# ==============================================================================
# DASHBOARD ROUTER
# ==============================================================================
# Provides aggregated data for the various dashboard views.
# Different users see different dashboards based on their roles.
# ==============================================================================

from typing import List, Optional
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models import (
    Department, Formation, Student, Professor, Module,
    ExamRoom, ExamSession, Exam
)
from app.schemas import (
    DashboardOverview,
    DepartmentStats,
    ProfessorWorkloadStats,
    ExamSessionWithStats,
    ExamDetail
)

router = APIRouter()


@router.get("/overview", response_model=DashboardOverview)
async def get_dashboard_overview(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get the main dashboard overview.
    
    Returns global statistics about the university:
    - Total counts for departments, formations, students, etc.
    - Active exam sessions with their statistics
    
    This is the first view users see when they log in.
    """
    # Get total counts
    dept_count = (await db.execute(
        select(func.count(Department.id)).where(Department.is_active == True)
    )).scalar() or 0
    
    form_count = (await db.execute(
        select(func.count(Formation.id)).where(Formation.is_active == True)
    )).scalar() or 0
    
    student_count = (await db.execute(
        select(func.count(Student.id)).where(Student.is_active == True)
    )).scalar() or 0
    
    prof_count = (await db.execute(
        select(func.count(Professor.id)).where(Professor.is_active == True)
    )).scalar() or 0
    
    module_count = (await db.execute(
        select(func.count(Module.id)).where(Module.is_active == True)
    )).scalar() or 0
    
    room_count = (await db.execute(
        select(func.count(ExamRoom.id)).where(ExamRoom.is_active == True)
    )).scalar() or 0
    
    # Get active sessions
    sessions_result = await db.execute(
        select(ExamSession)
        .where(ExamSession.status.in_(["draft", "published", "in_progress"]))
        .order_by(ExamSession.start_date)
    )
    sessions = sessions_result.scalars().all()
    
    # Batch load stats for all active sessions to avoid N+1 problem
    session_ids = [s.id for s in sessions]
    exam_stats = {}
    if session_ids:
        stats_q = await db.execute(
            select(
                Exam.session_id,
                func.count(Exam.id).label("total"),
                func.sum(text("CASE WHEN status = 'scheduled' THEN 1 ELSE 0 END")).label("scheduled"),
                func.sum(text("CASE WHEN status = 'pending' THEN 1 ELSE 0 END")).label("pending")
            )
            .where(Exam.session_id.in_(session_ids))
            .group_by(Exam.session_id)
        )
        exam_stats = {row.session_id: row for row in stats_q.all()}

    active_sessions = []
    for session in sessions:
        stats = exam_stats.get(session.id)
        
        active_sessions.append(ExamSessionWithStats(
            id=session.id,
            name=session.name,
            session_type=session.session_type,
            start_date=session.start_date,
            end_date=session.end_date,
            academic_year=session.academic_year,
            status=session.status,
            validated_by=session.validated_by,
            validated_at=session.validated_at,
            created_at=session.created_at,
            updated_at=session.updated_at,
            total_exams=stats.total if stats else 0,
            scheduled_exams=int(stats.scheduled or 0) if stats else 0,
            pending_exams=int(stats.pending or 0) if stats else 0,
            conflict_count=0 # Conflicts are retrieved separately via specialized endpoint
        ))
    
    return DashboardOverview(
        total_departments=dept_count,
        total_formations=form_count,
        total_students=student_count,
        total_professors=prof_count,
        total_modules=module_count,
        total_exam_rooms=room_count,
        active_sessions=active_sessions
    )


@router.get("/department/{department_id}", response_model=DepartmentStats)
async def get_department_dashboard(
    department_id: UUID,
    session_id: UUID = Query(None, description="Exam session for statistics"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get dashboard data for a specific department.
    
    Returns department-level statistics including:
    - Formation and student counts
    - Exam statistics (if session_id provided)
    - Conflict information
    
    Used by department heads to monitor their area.
    """
    # Verify department exists
    dept_result = await db.execute(
        select(Department).where(Department.id == department_id)
    )
    dept = dept_result.scalar_one_or_none()
    
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    
    # If session provided, calculate detailed stats
    if session_id:
        # Get exams for this dept/session
        exams_q = await db.execute(
            select(Exam)
            .join(Module, Exam.module_id == Module.id)
            .join(Formation, Module.formation_id == Formation.id)
            .where(Formation.department_id == department_id)
            .where(Exam.session_id == session_id)
        )
        exams = exams_q.scalars().all()
        
        # Get unique students in these exams
        student_count = (await db.execute(
            select(func.count(func.distinct(Student.id)))
            .join(Enrollment, Student.id == Enrollment.student_id)
            .join(Formation, Student.formation_id == Formation.id)
            .where(Formation.department_id == department_id)
        )).scalar() or 0

        # Get unique professors supervising these exams
        from app.models import ExamSupervisor
        prof_count_q = await db.execute(
            select(func.count(func.distinct(ExamSupervisor.professor_id)))
            .join(Exam, ExamSupervisor.exam_id == Exam.id)
            .where(Exam.session_id == session_id)
            .where(ExamSupervisor.is_department_exam == True)
        )
        
        scheduled = len([e for e in exams if e.status == 'scheduled'])
        
        return DepartmentStats(
            department_name=dept.name,
            total_exams=len(exams),
            scheduled_exams=scheduled,
            total_students=student_count,
            professors_supervising=prof_count_q.scalar() or 0,
            student_conflicts=0, # Conflict detection via separate endpoint
            formations_count=(await db.execute(select(func.count(Formation.id)).where(Formation.department_id == department_id))).scalar() or 0
        )
    
    # Basic stats without session
    student_count = (await db.execute(
        select(func.count(Student.id))
        .join(Formation, Student.formation_id == Formation.id)
        .where(Formation.department_id == department_id)
        .where(Student.is_active == True)
    )).scalar() or 0
    
    formation_count = (await db.execute(
        select(func.count(Formation.id))
        .where(Formation.department_id == department_id)
        .where(Formation.is_active == True)
    )).scalar() or 0
    
    return DepartmentStats(
        department_name=dept.name,
        total_exams=0,
        scheduled_exams=0,
        total_students=student_count,
        professors_supervising=0,
        student_conflicts=0,
        formations_count=formation_count
    )


@router.get("/professor-workload", response_model=List[ProfessorWorkloadStats])
async def get_professor_workload(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["admin", "vice_dean", "dean"]))
):
    """
    Get professor workload statistics for fair distribution analysis.
    
    Returns for each professor:
    - Total supervisions
    - Department vs other exams
    - Deviation from average (for identifying imbalances)
    
    Used by administrators to ensure fair workload distribution.
    """
    from app.models import ExamSupervisor
    # Get all supervisors for the session
    query = (
        select(
            Professor.id,
            Professor.first_name,
            Professor.last_name,
            Department.name.label("dept_name"),
            func.count(ExamSupervisor.id).label("total_sups"),
            func.sum(text("CASE WHEN is_department_exam = 1 THEN 1 ELSE 0 END")).label("dept_sups")
        )
        .join(Professor, ExamSupervisor.professor_id == Professor.id)
        .join(Department, Professor.department_id == Department.id)
        .join(Exam, ExamSupervisor.exam_id == Exam.id)
        .where(Exam.session_id == session_id)
        .group_by(Professor.id)
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    # Calculate Mean for deviation
    total_supervisions = sum(row.total_sups for row in rows)
    mean = total_supervisions / len(rows) if rows else 0
    
    workload = []
    for row in rows:
        workload.append(ProfessorWorkloadStats(
            professor_id=row.id,
            professor_name=f"{row.first_name} {row.last_name}",
            department_name=row.dept_name,
            supervision_count=row.total_sups,
            dept_exams_count=int(row.dept_sups or 0),
            other_exams_count=int(row.total_sups - (row.dept_sups or 0)),
            deviation_from_mean=float(row.total_sups - mean)
        ))
    
    return workload


@router.get("/room-utilization")
async def get_room_utilization(
    session_id: UUID = Query(None, description="Filter by exam session"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get room utilization statistics.
    
    Shows how efficiently rooms are being used:
    - Number of exams per room
    - Average fill rate
    - Underutilized rooms
    
    Helps identify capacity planning opportunities.
    """
    # Use the view we created
    if session_id:
        result = await db.execute(
            text("""
                SELECT 
                    r.id as room_id,
                    r.name as room_name,
                    r.building,
                    r.room_type,
                    r.exam_capacity,
                    COUNT(e.id) as scheduled_exams,
                    COALESCE(SUM(e.expected_students), 0) as total_students,
                    ROUND(
                        COALESCE(AVG(e.expected_students * 1.0 / NULLIF(r.exam_capacity, 0) * 100), 0),
                        2
                    ) as avg_utilization
                FROM exam_rooms r
                LEFT JOIN exams e ON r.id = e.room_id 
                    AND e.session_id = :session_id 
                    AND e.status = 'scheduled'
                WHERE r.is_active = true
                GROUP BY r.id, r.name, r.building, r.room_type, r.exam_capacity
                ORDER BY scheduled_exams DESC, r.building, r.name
            """),
            {"session_id": str(session_id)}
        )
    else:
        result = await db.execute(text("SELECT * FROM room_utilization"))
    
    rooms = []
    for row in result:
        rooms.append({
            "room_id": str(row.room_id),
            "room_name": row.room_name,
            "building": row.building,
            "room_type": row.room_type,
            "exam_capacity": row.exam_capacity,
            "scheduled_exams": row.scheduled_exams,
            "total_students": row.total_students if hasattr(row, 'total_students') else 0,
            "avg_utilization_percent": float(row.avg_utilization) if hasattr(row, 'avg_utilization') else 0
        })
    
    return rooms


@router.get("/upcoming-exams", response_model=List[ExamDetail])
async def get_upcoming_exams(
    department_id: UUID = Query(None, description="Filter by department"),
    limit: int = Query(10, ge=1, le=50, description="Number of exams to return"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get upcoming scheduled exams.
    
    Returns the next N exams that are scheduled to happen,
    optionally filtered by department.
    
    Useful for quick overview and preparation.
    """
    today = date.today()
    
    query = (
        select(
            Exam,
            Module.name.label("module_name"),
            Module.code.label("module_code"),
            Formation.name.label("formation_name"),
            Department.name.label("department_name"),
            ExamRoom.name.label("room_name"),
            ExamRoom.building.label("room_building")
        )
        .join(Module, Exam.module_id == Module.id)
        .join(Formation, Module.formation_id == Formation.id)
        .join(Department, Formation.department_id == Department.id)
        .outerjoin(ExamRoom, Exam.room_id == ExamRoom.id)
        .where(Exam.status == "scheduled")
        .where(Exam.scheduled_date >= today)
    )
    
    if department_id:
        query = query.where(Department.id == department_id)
    
    query = query.order_by(Exam.scheduled_date, Exam.start_time).limit(limit)
    
    result = await db.execute(query)
    rows = result.all()
    
    exams = []
    for row in rows:
        exam = row[0]
        exams.append(ExamDetail(
            id=exam.id,
            module_id=exam.module_id,
            session_id=exam.session_id,
            room_id=exam.room_id,
            scheduled_date=exam.scheduled_date,
            start_time=exam.start_time,
            duration_minutes=exam.duration_minutes,
            status=exam.status,
            expected_students=exam.expected_students,
            requires_computer=exam.requires_computer,
            requires_lab=exam.requires_lab,
            notes=exam.notes,
            created_at=exam.created_at,
            updated_at=exam.updated_at,
            module_name=row.module_name,
            module_code=row.module_code,
            formation_name=row.formation_name,
            department_name=row.department_name,
            room_name=row.room_name,
            room_building=row.room_building
        ))
    
    return exams


@router.get("/my-schedule")
async def get_my_schedule(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get the current user's personal exam schedule.
    
    For students: Shows their exams based on enrollments
    For professors: Shows their supervision assignments
    
    This is the personalized view for individual users.
    """
    user_role = current_user.get("role")
    user_id = current_user.get("id")
    
    if user_role == "student":
        # Get student's exams via Enrollment
        query = (
            select(
                Exam.scheduled_date,
                Exam.start_time,
                Exam.duration_minutes,
                Module.name.label("module_name"),
                Module.code.label("module_code"),
                ExamRoom.name.label("room_name"),
                ExamRoom.building.label("room_building")
            )
            .join(Enrollment, Exam.module_id == Enrollment.module_id)
            .join(Module, Exam.module_id == Module.id)
            .outerjoin(ExamRoom, Exam.room_id == ExamRoom.id)
            .where(Enrollment.student_id == current_user["student_id"])
            .where(Exam.status == "scheduled")
            .order_by(Exam.scheduled_date, Exam.start_time)
        )
        result = await db.execute(query)
        schedule = [dict(row._mapping) for row in result.all()]
        return schedule

    elif user_role in ["professor", "dept_head"]:
        # Get professor's supervisions
        from app.models import ExamSupervisor
        query = (
            select(
                Exam.scheduled_date,
                Exam.start_time,
                Exam.duration_minutes,
                Module.name.label("module_name"),
                Module.code.label("module_code"),
                ExamRoom.name.label("room_name"),
                ExamRoom.building.label("room_building"),
                ExamSupervisor.role
            )
            .join(ExamSupervisor, Exam.id == ExamSupervisor.exam_id)
            .join(Module, Exam.module_id == Module.id)
            .outerjoin(ExamRoom, Exam.room_id == ExamRoom.id)
            .where(ExamSupervisor.professor_id == current_user["professor_id"])
            .where(Exam.status == "scheduled")
            .order_by(Exam.scheduled_date, Exam.start_time)
        )
        result = await db.execute(query)
        schedule = [dict(row._mapping) for row in result.all()]
        return schedule
