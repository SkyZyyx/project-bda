# ==============================================================================
# SCHEDULING ROUTER
# ==============================================================================
# Handles automatic exam scheduling and optimization.
# This is the core algorithm of the platform.
# ==============================================================================

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models import ExamSession, Exam, Module
from app.schemas import (
    AvailableSlot,
    ScheduleResult,
    SessionScheduleResult,
    SessionStats,
)

router = APIRouter()


@router.get("/available-slots/{exam_id}", response_model=List[AvailableSlot])
async def get_available_slots(
    exam_id: UUID,
    db: AsyncSession = Depends(get_db),
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
    module_students: dict = None,
    students_per_day: dict = None,
    rooms_busy_at_slot: dict = None,
):
    """
    Get available time slots for a specific exam.
    Supports in-memory checks for bulk processing.
    """
    # Get exam details including required relations
    result = await db.execute(select(Exam).where(Exam.id == exam_id))
    exam = result.scalar_one_or_none()

    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    # Get Session
    session_result = await db.execute(
        select(ExamSession).where(ExamSession.id == exam.session_id)
    )
    session = session_result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get Students for this exam (via Module Enrollments)
    from app.models import Enrollment

    students_res = await db.execute(
        select(Enrollment.student_id).where(Enrollment.module_id == exam.module_id)
    )
    student_ids = [r[0] for r in students_res.all()]

    # Get Rooms compatible with capacity and requirements
    from app.models import ExamRoom

    rooms_query = (
        select(ExamRoom)
        .where(
            ExamRoom.exam_capacity >= len(student_ids),
            ExamRoom.is_active == True,
            ExamRoom.is_available == True,
        )
        .order_by(ExamRoom.exam_capacity)
    )  # Use smallest fitting room first

    if exam.requires_computer:
        rooms_query = rooms_query.where(ExamRoom.has_computers == True)
    if exam.requires_lab:
        rooms_query = rooms_query.where(ExamRoom.room_type == "lab")

    rooms_res = await db.execute(rooms_query)
    rooms = rooms_res.scalars().all()

    # Define Time Slots (Simple fixed slots logic)
    from datetime import timedelta, datetime, time

    date_cursor = session.start_date
    delta = timedelta(days=1)

    available_slots = []

    # Pre-fetch all existing exams in this session to check conflicts
    existing_exams_res = await db.execute(
        select(Exam).where(
            Exam.session_id == session.id,
            Exam.status == "scheduled",
            Exam.id != exam_id,
        )
    )
    existing_exams = existing_exams_res.scalars().all()

    # Standard start times
    start_times = [time(8, 30), time(11, 0), time(13, 30), time(16, 0)]

    # Iterate days
    while date_cursor <= session.end_date:
        if date_cursor.weekday() == 4:  # Skip Friday
            date_cursor += delta
            continue

        # Performance optimization: Use in-memory check for "1 exam per day"
        # provided by the batch processor
        if students_per_day and exam.module_id in module_students:
            mod_stds = module_students[exam.module_id]
            day_busy = students_per_day.get(date_cursor, set())
            if not mod_stds.isdisjoint(day_busy):
                date_cursor += delta
                continue

        for t in start_times:
            if len(available_slots) >= limit:
                break

            for room in rooms:
                # Room check in memory
                room_free = True
                room_busy = rooms_busy_at_slot.get((date_cursor, t), set())
                if room.id in room_busy:
                    room_free = False

                if not room_free:
                    continue

                available_slots.append(
                    AvailableSlot(
                        slot_date=date_cursor,
                        slot_time=t,
                        room_id=room.id,
                        room_name=room.name,
                        room_capacity=room.exam_capacity,
                        score=100 - (len(available_slots)),
                    )
                )
                if len(available_slots) >= limit:
                    break

        date_cursor += delta

    return available_slots


@router.post("/schedule-exam/{exam_id}", response_model=ScheduleResult)
async def schedule_single_exam(
    exam_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["admin", "vice_dean"])),
):
    """
    Schedule a single exam using Python logic (Greedy).
    """
    # Get available slots
    slots = await get_available_slots(
        exam_id, db=db, limit=1, current_user=current_user
    )

    if not slots:
        return ScheduleResult(success=False, message="No available slots found")

    best_slot = slots[0]

    # Update Exam
    stmt = select(Exam).where(Exam.id == exam_id)
    result = await db.execute(stmt)
    exam = result.scalar_one()

    exam.scheduled_date = best_slot.slot_date
    exam.start_time = best_slot.slot_time
    exam.room_id = best_slot.room_id
    exam.status = "scheduled"

    await db.commit()

    return ScheduleResult(
        success=True,
        message="Scheduled successfully",
        scheduled_date=best_slot.slot_date,
        scheduled_time=best_slot.slot_time,
        room_name=best_slot.room_name,
    )


@router.post("/schedule-session/{session_id}", response_model=SessionScheduleResult)
async def schedule_entire_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["admin", "vice_dean"])),
):
    """
    Auto-schedule entire session - VERSION ULTRA-OPTIMISÉE.

    OPTIMISATION MAJEURE : Toutes les données chargées en 6 requêtes au début,
    puis planification 100% en mémoire sans aucune requête SQL dans la boucle.

    Avant : ~1500 requêtes SQL (5 par examen × 307 examens)
    Après : ~6 requêtes SQL total !
    """
    from app.models import ExamSession, Exam, Enrollment, ExamRoom
    from collections import defaultdict
    from datetime import timedelta, time
    import time as time_sys

    start_ts = time_sys.time()

    # ========================================================================
    # PHASE 1 : CHARGEMENT BATCH DE TOUTES LES DONNÉES (6 requêtes seulement)
    # ========================================================================

    # 1. Session
    result = await db.execute(select(ExamSession).where(ExamSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 2. Toutes les inscriptions (module_id -> set of student_ids)
    enroll_res = await db.execute(select(Enrollment.student_id, Enrollment.module_id))
    module_students = defaultdict(set)
    for sid, mid in enroll_res.all():
        module_students[mid].add(sid)

    # 3. Toutes les salles actives
    rooms_res = await db.execute(
        select(ExamRoom)
        .where(ExamRoom.is_active == True, ExamRoom.is_available == True)
        .order_by(ExamRoom.exam_capacity)
    )
    all_rooms = rooms_res.scalars().all()

    # Pré-indexer les salles par capacité pour accès O(1)
    rooms_by_capacity = sorted(all_rooms, key=lambda r: r.exam_capacity)
    computer_rooms = [r for r in rooms_by_capacity if r.has_computers]
    lab_rooms = [r for r in rooms_by_capacity if r.room_type == "lab"]

    # 4. Examens en attente (triés par nombre d'étudiants décroissant = hardest first)
    exams_res = await db.execute(
        select(Exam)
        .where(Exam.session_id == session_id, Exam.status == "pending")
        .order_by(Exam.expected_students.desc())
    )
    pending_exams = exams_res.scalars().all()

    # 5. Examens déjà planifiés (pour pré-remplir les contraintes)
    existing_res = await db.execute(
        select(Exam).where(Exam.session_id == session_id, Exam.status == "scheduled")
    )
    existing_exams = existing_res.scalars().all()

    # ========================================================================
    # PHASE 2 : CONSTRUCTION DES STRUCTURES EN MÉMOIRE
    # ========================================================================

    # Tracking structures pour l'algorithme greedy
    students_per_day = defaultdict(set)  # date -> set(student_ids)
    rooms_busy_at_slot = defaultdict(set)  # (date, time) -> set(room_ids)

    # Remplir avec les examens existants
    for ex in existing_exams:
        if ex.scheduled_date and ex.module_id in module_students:
            students_per_day[ex.scheduled_date].update(module_students[ex.module_id])
            if ex.start_time and ex.room_id:
                rooms_busy_at_slot[(ex.scheduled_date, ex.start_time)].add(ex.room_id)

    # Générer tous les créneaux possibles
    start_times = [time(8, 30), time(11, 0), time(13, 30), time(16, 0)]
    all_slots = []
    date_cursor = session.start_date
    delta = timedelta(days=1)

    while date_cursor <= session.end_date:
        if date_cursor.weekday() != 4:  # Skip Friday (Algeria constraint)
            for t in start_times:
                all_slots.append((date_cursor, t))
        date_cursor += delta

    # ========================================================================
    # PHASE 3 : PLANIFICATION 100% EN MÉMOIRE (ZÉRO REQUÊTE SQL)
    # ========================================================================

    scheduled_count = 0
    failed_count = 0

    for exam in pending_exams:
        # Déterminer les salles compatibles
        student_count = len(module_students.get(exam.module_id, set()))
        if student_count == 0:
            student_count = exam.expected_students or 50  # Fallback

        # Sélectionner le pool de salles selon les contraintes
        if exam.requires_lab:
            candidate_rooms = [r for r in lab_rooms if r.exam_capacity >= student_count]
        elif exam.requires_computer:
            candidate_rooms = [
                r for r in computer_rooms if r.exam_capacity >= student_count
            ]
        else:
            candidate_rooms = [
                r for r in rooms_by_capacity if r.exam_capacity >= student_count
            ]

        if not candidate_rooms:
            failed_count += 1
            continue

        # Étudiants de cet examen
        exam_students = module_students.get(exam.module_id, set())

        # Chercher le premier créneau disponible
        slot_found = False
        for slot_date, slot_time in all_slots:
            # Vérifier contrainte étudiants (1 exam/jour/étudiant)
            if not exam_students.isdisjoint(students_per_day[slot_date]):
                continue

            # Chercher une salle libre
            busy_rooms = rooms_busy_at_slot[(slot_date, slot_time)]
            for room in candidate_rooms:
                if room.id not in busy_rooms:
                    # SLOT TROUVÉ !
                    exam.scheduled_date = slot_date
                    exam.start_time = slot_time
                    exam.room_id = room.id
                    exam.status = "scheduled"

                    # Mise à jour des structures en mémoire
                    students_per_day[slot_date].update(exam_students)
                    rooms_busy_at_slot[(slot_date, slot_time)].add(room.id)

                    scheduled_count += 1
                    slot_found = True
                    break

            if slot_found:
                break

        if not slot_found:
            failed_count += 1

    # ========================================================================
    # PHASE 4 : COMMIT UNIQUE FINAL
    # ========================================================================
    await db.commit()
    exec_time = int((time_sys.time() - start_ts) * 1000)

    return SessionScheduleResult(
        total_exams=len(pending_exams),
        scheduled_count=scheduled_count,
        failed_count=failed_count,
        execution_time_ms=exec_time,
    )


@router.post("/prepare-session/{session_id}")
async def prepare_session_for_scheduling(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["admin", "vice_dean"])),
):
    """
    Prépare la session d'examen - VERSION OPTIMISÉE.

    OPTIMISATION : Chargement batch des données, création en mémoire.
    Avant : ~600 requêtes (2 par module × 307 modules)
    Après : ~4 requêtes totales !
    """
    from app.models import Module, Formation, Enrollment
    from sqlalchemy import func

    # 1. Vérifier la session
    result = await db.execute(select(ExamSession).where(ExamSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 2. Charger tous les modules actifs pour cette année académique
    modules_res = await db.execute(
        select(Module)
        .join(Formation)
        .where(
            Formation.academic_year == session.academic_year, Module.is_active == True
        )
    )
    modules = modules_res.scalars().all()

    # 3. Charger tous les examens existants pour cette session (batch)
    existing_res = await db.execute(
        select(Exam.module_id).where(Exam.session_id == session.id)
    )
    existing_module_ids = {row[0] for row in existing_res.all()}

    # 4. Compter les étudiants par module EN UNE SEULE REQUÊTE
    enrollment_counts = await db.execute(
        select(Enrollment.module_id, func.count(Enrollment.id).label("count")).group_by(
            Enrollment.module_id
        )
    )
    student_counts = {row[0]: row[1] for row in enrollment_counts.all()}

    # 5. Créer les examens en mémoire (aucune requête dans la boucle!)
    new_exams = []
    for module in modules:
        # Skip si l'examen existe déjà
        if module.id in existing_module_ids:
            continue

        std_count = student_counts.get(module.id, 0)

        new_exam = Exam(
            module_id=module.id,
            session_id=session.id,
            duration_minutes=module.exam_duration_minutes,
            status="pending",
            expected_students=std_count,
            requires_computer=module.requires_computer,
            requires_lab=module.requires_lab,
        )
        new_exams.append(new_exam)

    # 6. Bulk add (SQLAlchemy optimise l'insertion)
    db.add_all(new_exams)
    await db.commit()

    return {
        "message": f"Created {len(new_exams)} exam entries",
        "exams_created": len(new_exams),
    }


@router.post("/clear-session/{session_id}")
async def clear_session_schedule(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["admin"])),
):
    """
    Python implementation of clear session - OPTIMIZED VERSION.
    Uses bulk UPDATE instead of looping through exams one by one.
    """
    from sqlalchemy import update, delete
    from app.models import ExamSupervisor
    import time

    start_time = time.time()

    # OPTIMIZED: Bulk update all scheduled exams to pending in ONE query
    result = await db.execute(
        update(Exam)
        .where(Exam.session_id == session_id, Exam.status == "scheduled")
        .values(status="pending", scheduled_date=None, start_time=None, room_id=None)
        .execution_options(synchronize_session=False)
    )
    count = result.rowcount

    # Delete supervisors for this session's exams (optimized)
    exam_ids_result = await db.execute(
        select(Exam.id).where(Exam.session_id == session_id)
    )
    exam_ids = [row[0] for row in exam_ids_result.all()]

    if exam_ids:
        await db.execute(
            delete(ExamSupervisor).where(ExamSupervisor.exam_id.in_(exam_ids))
        )

    await db.commit()

    elapsed_ms = int((time.time() - start_time) * 1000)

    return {
        "message": f"Cleared schedule for {count} exams in {elapsed_ms}ms",
        "exams_cleared": count,
        "execution_time_ms": elapsed_ms,
    }


@router.post("/assign-supervisors/{session_id}")
async def assign_exam_supervisors(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["admin", "vice_dean"])),
):
    """
    Automatically assign supervisors to exams (Python Implementation).
    """
    # 1. Verify Session
    result = await db.execute(select(ExamSession).where(ExamSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 2. Get Scheduled Exams
    exams_res = await db.execute(
        select(Exam).where(Exam.session_id == session_id, Exam.status == "scheduled")
    )
    exams = exams_res.scalars().all()

    if not exams:
        return {"message": "No scheduled exams found to assign supervisors to."}

    # 3. Get All Professors
    from app.models import Professor, ExamSupervisor, Module, Formation

    profs_res = await db.execute(select(Professor).where(Professor.is_active == True))
    professors = profs_res.scalars().all()
    prof_dict = {p.id: p for p in professors}

    # 4. Get Existing Assignments (to check conflicts/load)
    # We will track assignments in memory for this transaction
    assignments_res = await db.execute(
        select(ExamSupervisor).where(ExamSupervisor.exam_id.in_([e.id for e in exams]))
    )
    existing_assignments = assignments_res.scalars().all()

    # Map: ProfID -> List of (Date, Time) busy
    prof_busy = {p.id: set() for p in professors}
    prof_load = {p.id: 0 for p in professors}

    # Fill with existing
    for sup in existing_assignments:
        # Find exam connected to this supervision
        # Since we didn't eager load, we look up in 'exams' list
        ex = next((e for e in exams if e.id == sup.exam_id), None)
        if ex:
            prof_busy[sup.professor_id].add((ex.scheduled_date, ex.start_time))
            prof_load[sup.professor_id] += 1

    new_assignments = 0

    # 5. Greedy Assignment
    import random

    for exam in exams:
        # Determine required supervisors
        # Rule: 1 supervisor per 25 students, min 2.
        count_needed = max(2, (exam.expected_students // 25) + 1)

        # Check current supervisors
        current_sups = [s for s in existing_assignments if s.exam_id == exam.id]
        if len(current_sups) >= count_needed:
            continue

        needed = count_needed - len(current_sups)

        # Get Exam Department
        mod_res = await db.execute(
            select(Module, Formation.department_id)
            .join(Formation, Module.formation_id == Formation.id)
            .where(Module.id == exam.module_id)
        )
        mod_info = mod_res.first()
        exam_dept_id = mod_info[1] if mod_info else None

        # Find Candidates
        candidates = []
        for pid, prof in prof_dict.items():
            # 1. Check Slot Availability (Simultaneous exams)
            if (exam.scheduled_date, exam.start_time) in prof_busy[pid]:
                continue

            # 2. Check Daily Limit (Max 3 exams per day)
            day_count = len([d for d, t in prof_busy[pid] if d == exam.scheduled_date])
            if day_count >= (prof.max_exams_per_day or 3):
                continue

            # 3. Avoid duplicates for same exam
            if any(s.professor_id == pid for s in current_sups):
                continue

            # SCORE CALCULATION (Priorities & Balance)
            score = 0

            # Priority A: Same Dept Preference (+20 points)
            if prof.department_id == exam_dept_id:
                score += 20

            # Priority B: Load Balancing (Extreme penalty for high load)
            # We want to encourage "All teachers same number of invigilations"
            score -= prof_load[pid] * 5

            # Priority C: Small random factor for natural distribution
            score += random.random()

            candidates.append((score, pid))

        # Sort candidates by score descending
        candidates.sort(key=lambda x: x[0], reverse=True)

        # Pick top 'needed' candidates
        for i in range(min(len(candidates), needed)):
            best_pid = candidates[i][1]

            # Create Assignment
            role = "responsible" if i == 0 and len(current_sups) == 0 else "supervisor"

            new_sup = ExamSupervisor(
                exam_id=exam.id,
                professor_id=best_pid,
                role=role,
                is_department_exam=(prof_dict[best_pid].department_id == exam_dept_id),
            )
            db.add(new_sup)

            # Update local tracking
            prof_busy[best_pid].add((exam.scheduled_date, exam.start_time))
            prof_load[best_pid] += 1
            new_assignments += 1

    await db.commit()

    return {
        "message": f"Assigned {new_assignments} supervisors",
        "assignments_made": new_assignments,
        "professors_used": len([p for p in prof_load if prof_load[p] > 0]),
        "avg_supervisions": sum(prof_load.values()) / len(professors)
        if professors
        else 0,
    }


@router.get("/session-stats/{session_id}", response_model=SessionStats)
async def get_session_statistics(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Python implementation of session stats"""
    result = await db.execute(select(ExamSession).where(ExamSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Aggegrate queries
    from sqlalchemy import func
    from app.models import ExamSupervisor, Department, Formation, Module

    total = await db.scalar(
        select(func.count(Exam.id)).where(Exam.session_id == session_id)
    )
    scheduled = await db.scalar(
        select(func.count(Exam.id)).where(
            Exam.session_id == session_id, Exam.status == "scheduled"
        )
    )
    pending = (total or 0) - (scheduled or 0)

    # Rooms used
    rooms = await db.scalar(
        select(func.count(func.distinct(Exam.room_id))).where(
            Exam.session_id == session_id, Exam.room_id != None
        )
    )

    # Professors Assigned
    profs = await db.scalar(
        select(func.count(func.distinct(ExamSupervisor.professor_id)))
        .join(Exam, ExamSupervisor.exam_id == Exam.id)
        .where(Exam.session_id == session_id)
    )

    # Departments Involved
    depts = await db.scalar(
        select(func.count(func.distinct(Department.id)))
        .join(Formation, Department.id == Formation.department_id)
        .join(Module, Formation.id == Module.formation_id)
        .join(Exam, Module.id == Exam.module_id)
        .where(Exam.session_id == session_id)
    )

    return SessionStats(
        total_exams=total or 0,
        scheduled_exams=scheduled or 0,
        pending_exams=pending or 0,
        total_rooms_used=rooms or 0,
        total_professors_assigned=profs or 0,
        avg_room_utilization=0.0,  # Complex calc left as 0
        conflict_count=0,
        departments_covered=depts or 0,
    )


@router.get("/conflicts")
async def get_schedule_conflicts(
    db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    """
    Comprehensive conflict detection (Python Implementation).
    Checks for Room overlaps, Capacity issues, Student overlaps, and Professor overlaps.
    """
    from app.models import (
        Exam,
        Module,
        ExamRoom,
        ExamSupervisor,
        Professor,
        Enrollment,
        Student,
    )
    from sqlalchemy import and_

    # 1. Fetch all scheduled exams with details
    query = (
        select(
            Exam,
            Module.name.label("module_name"),
            ExamRoom.name.label("room_name"),
            ExamRoom.exam_capacity.label("room_capacity"),
        )
        .join(Module, Exam.module_id == Module.id)
        .join(ExamRoom, Exam.room_id == ExamRoom.id)
        .where(Exam.status == "scheduled")
    )
    res = await db.execute(query)
    exams_rows = res.all()

    conflicts = []

    def times_overlap(start1, dur1, start2, dur2):
        if not start1 or not start2:
            return False
        m1 = start1.hour * 60 + start1.minute
        m2 = start2.hour * 60 + start2.minute
        return max(m1, m2) < min(m1 + dur1, m2 + dur2)

    # --- ROOM OVERLAP & CAPACITY ---
    for i, row1 in enumerate(exams_rows):
        e1, m1_name, r1_name, r1_cap = row1

        # Capacity Check
        if e1.expected_students > r1_cap:
            conflicts.append(
                {
                    "type": "Capacity",
                    "severity": "High",
                    "item": f"{r1_name}",
                    "detail": f"Exam {m1_name} ({e1.expected_students} students) exceeds room capacity ({r1_cap}).",
                }
            )

        # Room Overlap Check
        for j, row2 in enumerate(exams_rows):
            if i >= j:
                continue
            e2, m2_name, r2_name, r2_cap = row2

            if e1.room_id == e2.room_id and e1.scheduled_date == e2.scheduled_date:
                if times_overlap(
                    e1.start_time,
                    e1.duration_minutes,
                    e2.start_time,
                    e2.duration_minutes,
                ):
                    conflicts.append(
                        {
                            "type": "Room Overlap",
                            "severity": "Critical",
                            "item": f"{r1_name}",
                            "detail": f"Conflict between {m1_name} and {m2_name} at {e1.start_time}.",
                        }
                    )

    # --- PROFESSOR OVERLAP ---
    # Fetch all supervisions for these exams
    sup_query = (
        select(
            ExamSupervisor,
            Professor.first_name,
            Professor.last_name,
            Exam.scheduled_date,
            Exam.start_time,
            Exam.duration_minutes,
            Module.name,
        )
        .join(Professor, ExamSupervisor.professor_id == Professor.id)
        .join(Exam, ExamSupervisor.exam_id == Exam.id)
        .join(Module, Exam.module_id == Module.id)
        .where(Exam.status == "scheduled")
    )
    sup_res = await db.execute(sup_query)
    sups = sup_res.all()

    for i, s1 in enumerate(sups):
        for j, s2 in enumerate(sups):
            if i >= j:
                continue
            if s1.ExamSupervisor.professor_id == s2.ExamSupervisor.professor_id:
                if s1.scheduled_date == s2.scheduled_date:
                    if times_overlap(
                        s1.start_time,
                        s1.duration_minutes,
                        s2.start_time,
                        s2.duration_minutes,
                    ):
                        conflicts.append(
                            {
                                "type": "Professor Overlap",
                                "severity": "Critical",
                                "item": f"{s1.first_name} {s1.last_name}",
                                "detail": f"Assigned to {s1.name} and {s2.name} simultaneously.",
                            }
                        )

    # --- STUDENT OVERLAP ---
    from collections import defaultdict

    # 1. Map Modules to Dates/Times
    mod_timing = {}
    for row in exams_rows:
        e, name, _, _ = row
        mod_timing[e.module_id] = (
            e.scheduled_date,
            e.start_time,
            e.duration_minutes,
            name,
        )

    # 2. Get All Enrollments for active students
    enr_query = (
        select(
            Enrollment.student_id,
            Enrollment.module_id,
            Student.first_name,
            Student.last_name,
        )
        .join(Student, Enrollment.student_id == Student.id)
        .where(Student.is_active == True)
    )
    enr_res = await db.execute(enr_query)
    enrollments = enr_res.all()

    # 3. Track Student Busy times
    student_busy = defaultdict(list)
    for enr in enrollments:
        if enr.module_id in mod_timing:
            timing = mod_timing[enr.module_id]
            student_busy[enr.student_id].append((timing, enr.first_name, enr.last_name))

    # 4. Find Overlaps per student
    # To keep performance manageable, we only report the first 50 unique student conflicts
    count = 0
    for sid, busy_list in student_busy.items():
        if len(busy_list) < 2:
            continue
        found_for_student = False
        for i, (t1, fname, lname) in enumerate(busy_list):
            for j, (t2, _, _) in enumerate(busy_list):
                if i >= j:
                    continue
                # t = (date, start, dur, name)
                if t1[0] == t2[0]:  # Same day
                    if times_overlap(t1[1], t1[2], t2[1], t2[2]):
                        conflicts.append(
                            {
                                "type": "Student Overlap",
                                "severity": "Critical",
                                "item": f"{fname} {lname}",
                                "detail": f"Double exam: {t1[3]} and {t2[3]} on {t1[0]}.",
                            }
                        )
                        found_for_student = True
                        count += 1
                        break
            if found_for_student:
                break
        if count >= 50:
            break

    return conflicts
