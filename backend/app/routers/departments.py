# ==============================================================================
# DEPARTMENTS ROUTER
# ==============================================================================
# Handles CRUD operations for departments and department statistics.
# Departments are the top-level organizational unit in the university.
# ==============================================================================

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models import Department, Formation, Student, Professor
from app.schemas import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    DepartmentWithStats
)

router = APIRouter()


@router.get("/", response_model=List[DepartmentWithStats])
async def get_departments(
    db: AsyncSession = Depends(get_db),
    include_inactive: bool = Query(False, description="Include inactive departments"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all departments with their statistics.
    
    Returns a list of departments including:
    - Basic department info (name, code, email, etc.)
    - Number of formations
    - Number of students
    - Number of professors
    
    This is used for the main dashboard and department selection.
    """
    # Base query
    query = select(Department)
    
    if not include_inactive:
        query = query.where(Department.is_active == True)
    
    result = await db.execute(query.order_by(Department.name))
    departments = result.scalars().all()
    
    # Get statistics for each department
    # We use subqueries to count related entities efficiently
    departments_with_stats = []
    
    for dept in departments:
        # Count formations
        form_count = await db.execute(
            select(func.count(Formation.id))
            .where(Formation.department_id == dept.id)
            .where(Formation.is_active == True)
        )
        
        # Count students (through formations)
        student_count = await db.execute(
            select(func.count(Student.id))
            .join(Formation, Student.formation_id == Formation.id)
            .where(Formation.department_id == dept.id)
            .where(Student.is_active == True)
        )
        
        # Count professors
        prof_count = await db.execute(
            select(func.count(Professor.id))
            .where(Professor.department_id == dept.id)
            .where(Professor.is_active == True)
        )
        
        # Build response with stats
        dept_dict = {
            "id": dept.id,
            "name": dept.name,
            "code": dept.code,
            "email": dept.email,
            "phone": dept.phone,
            "building": dept.building,
            "is_active": dept.is_active,
            "created_at": dept.created_at,
            "updated_at": dept.updated_at,
            "formation_count": form_count.scalar() or 0,
            "student_count": student_count.scalar() or 0,
            "professor_count": prof_count.scalar() or 0
        }
        
        departments_with_stats.append(DepartmentWithStats(**dept_dict))
    
    return departments_with_stats


@router.get("/{department_id}", response_model=DepartmentWithStats)
async def get_department(
    department_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific department by ID with its statistics.
    
    Returns detailed information about a single department,
    including all computed statistics.
    """
    result = await db.execute(
        select(Department).where(Department.id == department_id)
    )
    dept = result.scalar_one_or_none()
    
    if not dept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    
    # Get statistics
    form_count = (await db.execute(
        select(func.count(Formation.id))
        .where(Formation.department_id == dept.id)
        .where(Formation.is_active == True)
    )).scalar() or 0
    
    student_count = (await db.execute(
        select(func.count(Student.id))
        .join(Formation, Student.formation_id == Formation.id)
        .where(Formation.department_id == dept.id)
        .where(Student.is_active == True)
    )).scalar() or 0
    
    prof_count = (await db.execute(
        select(func.count(Professor.id))
        .where(Professor.department_id == dept.id)
        .where(Professor.is_active == True)
    )).scalar() or 0
    
    return DepartmentWithStats(
        id=dept.id,
        name=dept.name,
        code=dept.code,
        email=dept.email,
        phone=dept.phone,
        building=dept.building,
        is_active=dept.is_active,
        created_at=dept.created_at,
        updated_at=dept.updated_at,
        formation_count=form_count,
        student_count=student_count,
        professor_count=prof_count
    )


@router.post("/", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    department_data: DepartmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["admin", "dean"]))
):
    """
    Create a new department (admin/dean only).
    
    Creates a new academic department. The department code must be unique.
    """
    # Check if code already exists
    existing = await db.execute(
        select(Department).where(Department.code == department_data.code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department code already exists"
        )
    
    # Create new department
    new_department = Department(**department_data.model_dump())
    
    db.add(new_department)
    await db.commit()
    await db.refresh(new_department)
    
    return new_department


@router.put("/{department_id}", response_model=DepartmentResponse)
async def update_department(
    department_id: UUID,
    department_data: DepartmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["admin", "dean"]))
):
    """
    Update a department (admin/dean only).
    
    Updates the specified department. Only provided fields are updated.
    """
    result = await db.execute(
        select(Department).where(Department.id == department_id)
    )
    department = result.scalar_one_or_none()
    
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    
    # Update only provided fields
    update_data = department_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(department, field, value)
    
    await db.commit()
    await db.refresh(department)
    
    return department


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(
    department_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["admin"]))
):
    """
    Delete (deactivate) a department (admin only).
    
    This performs a soft delete by setting is_active to False.
    The department data is preserved for historical records.
    """
    result = await db.execute(
        select(Department).where(Department.id == department_id)
    )
    department = result.scalar_one_or_none()
    
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    
    # Soft delete
    department.is_active = False
    await db.commit()
    
    return None


@router.get("/{department_id}/formations", response_model=List)
async def get_department_formations(
    department_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all formations in a department.
    
    Returns a list of all active formations belonging to the specified department.
    """
    # Verify department exists
    dept_result = await db.execute(
        select(Department).where(Department.id == department_id)
    )
    if not dept_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Department not found")
    
    # Get formations
    result = await db.execute(
        select(Formation)
        .where(Formation.department_id == department_id)
        .where(Formation.is_active == True)
        .order_by(Formation.level, Formation.name)
    )
    
    formations = result.scalars().all()
    
    return formations


@router.get("/{department_id}/professors", response_model=List)
async def get_department_professors(
    department_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all professors in a department.
    
    Returns a list of all active professors belonging to the specified department.
    """
    # Verify department exists
    dept_result = await db.execute(
        select(Department).where(Department.id == department_id)
    )
    if not dept_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Department not found")
    
    # Get professors
    result = await db.execute(
        select(Professor)
        .where(Professor.department_id == department_id)
        .where(Professor.is_active == True)
        .order_by(Professor.last_name, Professor.first_name)
    )
    
    professors = result.scalars().all()
    
    return professors
