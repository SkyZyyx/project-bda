# ==============================================================================
# EXAMS ROUTER
# ==============================================================================
# Handles CRUD operations for exams and exam sessions.
# This is the core of the scheduling functionality.
# ==============================================================================

from typing import List, Optional
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text, or_

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models import Exam, ExamSession, ExamRoom, Module, Formation, Department
from app.schemas import (
    ExamCreate,
    ExamUpdate,
    ExamResponse,
    ExamDetail,
    ExamSessionCreate,
    ExamSessionUpdate,
    ExamSessionResponse,
    ExamRoomResponse,
    ConflictSummary
)

router = APIRouter()


# ==============================================================================
# EXAM SESSION ENDPOINTS
# ==============================================================================

@router.get("/sessions", response_model=List[ExamSessionResponse])
async def get_exam_sessions(
    db: AsyncSession = Depends(get_db),
    academic_year: str = Query(None, description="Filter by academic year"),
    status_filter: str = Query(None, alias="status", description="Filter by status"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all exam sessions with optional filters.
    """
    query = select(ExamSession)
    
    if academic_year:
        query = query.where(ExamSession.academic_year == academic_year)
    
    if status_filter:
        query = query.where(ExamSession.status == status_filter)
    
    query = query.order_by(ExamSession.start_date.desc())
    
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/sessions", response_model=ExamSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_exam_session(
    session_data: ExamSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["admin", "vice_dean"]))
):
    """
    Create a new exam session (admin/vice_dean only).
    
    An exam session defines a period during which exams can be scheduled,
    like "Session Normale S1" or "Session Rattrapage".
    """
    # Validate date range
    if session_data.end_date < session_data.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date must be after start date"
        )
    
    new_session = ExamSession(**session_data.model_dump())
    
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    
    return new_session


@router.get("/sessions/{session_id}", response_model=ExamSessionResponse)
async def get_exam_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific exam session.
    """
    result = await db.execute(
        select(ExamSession).where(ExamSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Exam session not found")
    
    return session


@router.put("/sessions/{session_id}", response_model=ExamSessionResponse)
async def update_exam_session(
    session_id: UUID,
    session_data: ExamSessionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["admin", "vice_dean"]))
):
    """
    Update an exam session.
    """
    result = await db.execute(
        select(ExamSession).where(ExamSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Exam session not found")
    
    update_data = session_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(session, field, value)
    
    await db.commit()
    await db.refresh(session)
    
    return session


# ==============================================================================
# EXAM ENDPOINTS
# ==============================================================================

@router.get("/", response_model=List[ExamDetail])
async def get_exams(
    db: AsyncSession = Depends(get_db),
    session_id: Optional[UUID] = Query(None),
    department_id: Optional[UUID] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    search: Optional[str] = Query(None),
    student_id: Optional[UUID] = Query(None),
    professor_id: Optional[UUID] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all exams with optional filters.
    
    Returns detailed exam information including module, formation,
    department, and room details.
    """
    # Build the query with joins
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
    )
    
    # Apply filters
    if session_id:
        query = query.where(Exam.session_id == session_id)
    
    if department_id:
        query = query.where(Department.id == department_id)
    
    if status_filter:
        query = query.where(Exam.status == status_filter)
    
    if date_from:
        query = query.where(Exam.scheduled_date >= date_from)
    
    if date_to:
        query = query.where(Exam.scheduled_date <= date_to)
    
    if search:
        query = query.where(or_(
            Module.name.ilike(f"%{search}%"),
            Module.code.ilike(f"%{search}%")
        ))
    
    if student_id:
        from app.models import Enrollment
        query = query.join(Enrollment, (Enrollment.module_id == Exam.module_id)).where(Enrollment.student_id == student_id)
        
    if professor_id:
        from app.models import ExamSupervisor
        query = query.join(ExamSupervisor, (ExamSupervisor.exam_id == Exam.id)).where(ExamSupervisor.professor_id == professor_id)
    
    query = query.order_by(Exam.scheduled_date, Exam.start_time)
    
    result = await db.execute(query)
    rows = result.all()
    
    # Build response
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


@router.get("/{exam_id}", response_model=ExamDetail)
async def get_exam(
    exam_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific exam with full details.
    """
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
        .where(Exam.id == exam_id)
    )
    
    result = await db.execute(query)
    row = result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    exam = row[0]
    return ExamDetail(
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
    )


@router.put("/{exam_id}", response_model=ExamResponse)
async def update_exam(
    exam_id: UUID,
    exam_data: ExamUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["admin", "vice_dean", "dept_head"]))
):
    """
    Update an exam (schedule, room, status, etc.).
    """
    result = await db.execute(
        select(Exam).where(Exam.id == exam_id)
    )
    exam = result.scalar_one_or_none()
    
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    update_data = exam_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(exam, field, value)
    
    # If we're setting a schedule, update status to 'scheduled'
    if exam_data.scheduled_date and exam_data.start_time and exam_data.room_id:
        exam.status = "scheduled"
    
    await db.commit()
    await db.refresh(exam)
    
    return exam


# ==============================================================================
# ROOM ENDPOINTS
# ==============================================================================

@router.get("/rooms/", response_model=List[ExamRoomResponse])
async def get_exam_rooms(
    db: AsyncSession = Depends(get_db),
    room_type: str = Query(None, description="Filter by room type (amphi, classroom, lab)"),
    min_capacity: int = Query(None, description="Minimum exam capacity"),
    has_computers: bool = Query(None, description="Filter by computer availability"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all exam rooms with optional filters.
    """
    query = select(ExamRoom).where(ExamRoom.is_active == True)
    
    if room_type:
        query = query.where(ExamRoom.room_type == room_type)
    
    if min_capacity:
        query = query.where(ExamRoom.exam_capacity >= min_capacity)
    
    if has_computers is not None:
        query = query.where(ExamRoom.has_computers == has_computers)
    
    query = query.order_by(ExamRoom.building, ExamRoom.name)
    
    result = await db.execute(query)
    return result.scalars().all()


# ==============================================================================
# CONFLICT DETECTION ENDPOINTS
# ==============================================================================

@router.get("/sessions/{session_id}/conflicts", response_model=List[ConflictSummary])
async def get_session_conflicts(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get a summary of all conflicts in an exam session.
    
    This calls the PL/pgSQL function get_conflicts_summary to detect:
    - Students with multiple exams on the same day
    - Professors exceeding daily exam limits
    - Room double-bookings
    - Capacity violations
    """
    # Verify session exists
    session_result = await db.execute(
        select(ExamSession).where(ExamSession.id == session_id)
    )
    if not session_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Exam session not found")
    
    # Call the stored procedure
    result = await db.execute(
        text("SELECT * FROM get_conflicts_summary(:session_id)"),
        {"session_id": str(session_id)}
    )
    
    conflicts = []
    for row in result:
        conflicts.append(ConflictSummary(
            conflict_type=row.conflict_type,
            conflict_count=row.conflict_count,
            severity=row.severity
        ))
    
    return conflicts
