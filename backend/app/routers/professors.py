# ==============================================================================
# PROFESSORS ROUTER
# ==============================================================================
# Handles operations related to professors and their workloads.
# ==============================================================================

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models import Professor, Department, ExamSupervisor
from app.schemas import (
    ProfessorResponse, 
    ProfessorWithWorkload, 
    ProfessorCreate, 
    ProfessorUpdate
)

router = APIRouter()


@router.get("/", response_model=List[ProfessorWithWorkload])
async def get_professors(
    db: AsyncSession = Depends(get_db),
    dept_id: Optional[UUID] = Query(None, alias="department_id"),
    search: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all professors with optional filters and workload stats.
    """
    query = select(
        Professor, 
        Department.name.label("department_name")
    ).join(Department, Professor.department_id == Department.id)
    
    if dept_id:
        query = query.where(Professor.department_id == dept_id)
    
    if search:
        query = query.where(or_(
            Professor.first_name.ilike(f"%{search}%"),
            Professor.last_name.ilike(f"%{search}%"),
            Professor.email.ilike(f"%{search}%"),
            Professor.specialization.ilike(f"%{search}%")
        ))
    
    query = query.order_by(Professor.last_name, Professor.first_name)
    
    result = await db.execute(query)
    rows = result.all()
    
    professors = []
    for row in rows:
        prof = row[0]
        # Count all-time supervisions for this professor
        count_res = await db.execute(
            select(func.count(ExamSupervisor.id)).where(ExamSupervisor.professor_id == prof.id)
        )
        count = count_res.scalar() or 0
        
        professors.append(ProfessorWithWorkload(
            id=prof.id,
            department_id=prof.department_id,
            first_name=prof.first_name,
            last_name=prof.last_name,
            email=prof.email,
            phone=prof.phone,
            title=prof.title,
            specialization=prof.specialization,
            max_exams_per_day=prof.max_exams_per_day,
            supervision_count=prof.supervision_count,
            is_active=prof.is_active,
            created_at=prof.created_at,
            updated_at=prof.updated_at,
            department_name=row.department_name,
            scheduled_supervisions=count
        ))
        
    return professors


@router.get("/{prof_id}", response_model=ProfessorWithWorkload)
async def get_professor(
    prof_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get details for a specific professor.
    """
    query = select(
        Professor, 
        Department.name.label("department_name")
    ).join(Department, Professor.department_id == Department.id).where(Professor.id == prof_id)
    
    result = await db.execute(query)
    row = result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Professor not found")
    
    prof = row[0]
    count_res = await db.execute(
        select(func.count(ExamSupervisor.id)).where(ExamSupervisor.professor_id == prof.id)
    )
    count = count_res.scalar() or 0
    
    return ProfessorWithWorkload(
        id=prof.id,
        department_id=prof.department_id,
        first_name=prof.first_name,
        last_name=prof.last_name,
        email=prof.email,
        phone=prof.phone,
        title=prof.title,
        specialization=prof.specialization,
        max_exams_per_day=prof.max_exams_per_day,
        supervision_count=prof.supervision_count,
        is_active=prof.is_active,
        created_at=prof.created_at,
        updated_at=prof.updated_at,
        department_name=row.department_name,
        scheduled_supervisions=count
    )


@router.post("/", response_model=ProfessorResponse, status_code=status.HTTP_201_CREATED)
async def create_professor(
    prof_data: ProfessorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["admin", "vice_dean"]))
):
    """
    Create a new professor (Admin/Vice Dean only).
    """
    # Check if email already exists
    existing = await db.execute(select(Professor).where(Professor.email == prof_data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Professor with this email already exists")
    
    new_prof = Professor(**prof_data.model_dump())
    db.add(new_prof)
    await db.commit()
    await db.refresh(new_prof)
    return new_prof


@router.put("/{prof_id}", response_model=ProfessorResponse)
async def update_professor(
    prof_id: UUID,
    prof_data: ProfessorUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["admin", "vice_dean"]))
):
    """
    Update a professor's information.
    """
    result = await db.execute(select(Professor).where(Professor.id == prof_id))
    prof = result.scalar_one_or_none()
    
    if not prof:
        raise HTTPException(status_code=404, detail="Professor not found")
    
    update_data = prof_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(prof, key, value)
    
    await db.commit()
    await db.refresh(prof)
    return prof
