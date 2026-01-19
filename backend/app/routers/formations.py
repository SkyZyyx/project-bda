# ==============================================================================
# FORMATIONS ROUTER
# ==============================================================================
# Handles CRUD operations for formations (training programs).
# Formations belong to departments and contain modules.
# ==============================================================================

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models import Formation, Department, Module, Student
from app.schemas import (
    FormationCreate,
    FormationUpdate,
    FormationResponse
)

router = APIRouter()


@router.get("/", response_model=List[FormationResponse])
async def get_formations(
    db: AsyncSession = Depends(get_db),
    department_id: UUID = Query(None, description="Filter by department"),
    level: str = Query(None, description="Filter by level (L1, L2, L3, M1, M2)"),
    academic_year: str = Query(None, description="Filter by academic year"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all formations with optional filters.
    
    Returns a list of formations that match the specified filters.
    If no filters are provided, returns all active formations.
    """
    query = select(Formation).where(Formation.is_active == True)
    
    # Apply filters
    if department_id:
        query = query.where(Formation.department_id == department_id)
    
    if level:
        query = query.where(Formation.level == level)
    
    if academic_year:
        query = query.where(Formation.academic_year == academic_year)
    
    query = query.order_by(Formation.level, Formation.name)
    
    result = await db.execute(query)
    formations = result.scalars().all()
    
    return formations


@router.get("/{formation_id}", response_model=FormationResponse)
async def get_formation(
    formation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific formation by ID.
    """
    result = await db.execute(
        select(Formation).where(Formation.id == formation_id)
    )
    formation = result.scalar_one_or_none()
    
    if not formation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Formation not found"
        )
    
    return formation


@router.post("/", response_model=FormationResponse, status_code=status.HTTP_201_CREATED)
async def create_formation(
    formation_data: FormationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["admin", "dean", "dept_head"]))
):
    """
    Create a new formation (admin/dean/dept_head only).
    
    Creates a new training program within a department.
    """
    # Verify department exists
    dept_result = await db.execute(
        select(Department).where(Department.id == formation_data.department_id)
    )
    if not dept_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department not found"
        )
    
    # Check if code already exists
    existing = await db.execute(
        select(Formation).where(Formation.code == formation_data.code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formation code already exists"
        )
    
    # Create formation
    new_formation = Formation(**formation_data.model_dump())
    
    db.add(new_formation)
    await db.commit()
    await db.refresh(new_formation)
    
    return new_formation


@router.put("/{formation_id}", response_model=FormationResponse)
async def update_formation(
    formation_id: UUID,
    formation_data: FormationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["admin", "dean", "dept_head"]))
):
    """
    Update a formation.
    """
    result = await db.execute(
        select(Formation).where(Formation.id == formation_id)
    )
    formation = result.scalar_one_or_none()
    
    if not formation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Formation not found"
        )
    
    update_data = formation_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(formation, field, value)
    
    await db.commit()
    await db.refresh(formation)
    
    return formation


@router.get("/{formation_id}/modules", response_model=List)
async def get_formation_modules(
    formation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all modules in a formation.
    """
    # Verify formation exists
    form_result = await db.execute(
        select(Formation).where(Formation.id == formation_id)
    )
    if not form_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Formation not found")
    
    result = await db.execute(
        select(Module)
        .where(Module.formation_id == formation_id)
        .where(Module.is_active == True)
        .order_by(Module.semester, Module.name)
    )
    
    return result.scalars().all()


@router.get("/{formation_id}/students", response_model=List)
async def get_formation_students(
    formation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all students in a formation.
    """
    # Verify formation exists
    form_result = await db.execute(
        select(Formation).where(Formation.id == formation_id)
    )
    if not form_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Formation not found")
    
    result = await db.execute(
        select(Student)
        .where(Student.formation_id == formation_id)
        .where(Student.is_active == True)
        .order_by(Student.last_name, Student.first_name)
    )
    
    return result.scalars().all()
