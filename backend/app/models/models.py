# ==============================================================================
# SQLALCHEMY ORM MODELS
# ==============================================================================
# Ces modèles représentent nos tables de base de données en Python.
# SQLAlchemy ORM mappe les classes Python aux tables de la base de données,
# nous permettant de travailler avec les enregistrements comme objets Python.
# ==============================================================================

from datetime import datetime, date, time, timezone
from typing import Optional, List
from sqlalchemy import (
    Column, String, Integer, Boolean, ForeignKey, Text,
    DateTime, Date, Time, Numeric, CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base


# Fonction helper pour les timestamps avec timezone (requis par PostgreSQL TIMESTAMPTZ)
def utc_now():
    return datetime.now(timezone.utc)


# ==============================================================================
# DEPARTMENT MODEL
# ==============================================================================

class Department(Base):
    """
    Represents an academic department in the university.
    
    Each department contains:
    - Multiple formations (training programs)
    - Multiple professors
    - Basic contact information
    """
    __tablename__ = "departments"
    
    # Primary key using UUID for better security and distribution
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # Basic information
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    code: Mapped[str] = mapped_column(String(10), nullable=False, unique=True)
    email: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    building: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Soft delete flag
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    
    # Relationships - these allow easy navigation between related objects
    # For example: department.formations gives us all formations in the department
    formations: Mapped[List["Formation"]] = relationship(back_populates="department")
    professors: Mapped[List["Professor"]] = relationship(back_populates="department")


# ==============================================================================
# FORMATION MODEL
# ==============================================================================

class Formation(Base):
    """
    Represents a training program (formation) within a department.
    
    Examples: "Licence Informatique L3", "Master Data Science M1"
    
    A formation belongs to exactly one department and contains multiple modules.
    Students are enrolled in a specific formation.
    """
    __tablename__ = "formations"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Link to parent department
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="RESTRICT"),
        nullable=False
    )
    
    # Formation details
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    level: Mapped[str] = mapped_column(String(10), nullable=False)  # L1, L2, L3, M1, M2, D
    module_count: Mapped[int] = mapped_column(Integer, default=0)
    academic_year: Mapped[str] = mapped_column(String(9), nullable=False)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    
    # Relationships
    department: Mapped["Department"] = relationship(back_populates="formations")
    modules: Mapped[List["Module"]] = relationship(back_populates="formation")
    students: Mapped[List["Student"]] = relationship(back_populates="formation")
    
    # Table constraints
    __table_args__ = (
        CheckConstraint("level IN ('L1', 'L2', 'L3', 'M1', 'M2', 'D')", name="valid_level"),
        UniqueConstraint("department_id", "name", "academic_year", name="unique_formation_per_year"),
    )


# ==============================================================================
# PROFESSOR MODEL
# ==============================================================================

class Professor(Base):
    """
    Represents a faculty member who teaches and supervises exams.
    
    Professors belong to a department and can supervise exams.
    We track their supervision count for fair workload distribution.
    """
    __tablename__ = "professors"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="RESTRICT"),
        nullable=False
    )
    
    # Personal info
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    
    # Professional info
    title: Mapped[str] = mapped_column(String(50), default="Lecturer")
    specialization: Mapped[Optional[str]] = mapped_column(String(200))
    
    # Workload tracking
    max_exams_per_day: Mapped[int] = mapped_column(Integer, default=3)
    supervision_count: Mapped[int] = mapped_column(Integer, default=0)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    
    # Relationships
    department: Mapped["Department"] = relationship(back_populates="professors")
    supervisions: Mapped[List["ExamSupervisor"]] = relationship(back_populates="professor")


# ==============================================================================
# STUDENT MODEL
# ==============================================================================

class Student(Base):
    """
    Represents a student enrolled in the university.
    
    Students are assigned to a specific formation and can be enrolled
    in multiple modules within that formation.
    """
    __tablename__ = "students"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    formation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("formations.id", ondelete="RESTRICT"),
        nullable=False
    )
    
    # Identification
    student_number: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    
    # Personal info
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    
    # Academic info
    enrollment_year: Mapped[int] = mapped_column(Integer, nullable=False)
    promotion: Mapped[Optional[str]] = mapped_column(String(10))
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    
    # Relationships
    formation: Mapped["Formation"] = relationship(back_populates="students")
    enrollments: Mapped[List["Enrollment"]] = relationship(back_populates="student")


# ==============================================================================
# MODULE MODEL
# ==============================================================================

class Module(Base):
    """
    Represents a course/subject within a formation.
    
    Modules have exam configurations (duration, equipment requirements)
    and are what students enroll in and get examined on.
    """
    __tablename__ = "modules"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    formation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("formations.id", ondelete="RESTRICT"),
        nullable=False
    )
    
    # Module info
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    credits: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Exam configuration
    exam_duration_minutes: Mapped[int] = mapped_column(Integer, default=120)
    requires_computer: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_lab: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Optional prerequisite
    prerequisite_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("modules.id", ondelete="SET NULL")
    )
    
    semester: Mapped[Optional[int]] = mapped_column(Integer)  # 1 or 2
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    
    # Relationships
    formation: Mapped["Formation"] = relationship(back_populates="modules")
    enrollments: Mapped[List["Enrollment"]] = relationship(back_populates="module")
    exams: Mapped[List["Exam"]] = relationship(back_populates="module")


# ==============================================================================
# EXAM ROOM MODEL
# ==============================================================================

class ExamRoom(Base):
    """
    Represents a physical room where exams can be held.
    
    Rooms have different types (amphi, classroom, lab) with varying capacities.
    The exam_capacity is usually lower than total_capacity due to spacing requirements.
    """
    __tablename__ = "exam_rooms"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Location
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    building: Mapped[str] = mapped_column(String(100), nullable=False)
    floor: Mapped[int] = mapped_column(Integer, default=0)
    
    # Type and capacity
    room_type: Mapped[str] = mapped_column(String(20), nullable=False)  # amphi, classroom, lab
    total_capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    exam_capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Equipment
    has_computers: Mapped[bool] = mapped_column(Boolean, default=False)
    has_projector: Mapped[bool] = mapped_column(Boolean, default=True)
    has_video_surveillance: Mapped[bool] = mapped_column(Boolean, default=False)
    is_accessible: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Availability
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    
    # Relationships
    exams: Mapped[List["Exam"]] = relationship(back_populates="room")


# ==============================================================================
# ENROLLMENT MODEL
# ==============================================================================

class Enrollment(Base):
    """
    Junction table linking students to modules.
    
    This many-to-many relationship tracks which students are enrolled
    in which modules for a given academic year.
    """
    __tablename__ = "enrollments"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False
    )
    
    module_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("modules.id", ondelete="CASCADE"),
        nullable=False
    )
    
    academic_year: Mapped[str] = mapped_column(String(9), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="enrolled")  # enrolled, dropped, completed
    grade: Mapped[Optional[float]] = mapped_column(Numeric(4, 2))  # 0-20 scale
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    
    # Relationships
    student: Mapped["Student"] = relationship(back_populates="enrollments")
    module: Mapped["Module"] = relationship(back_populates="enrollments")
    
    __table_args__ = (
        UniqueConstraint("student_id", "module_id", "academic_year", name="unique_enrollment"),
    )


# ==============================================================================
# EXAM SESSION MODEL
# ==============================================================================

class ExamSession(Base):
    """
    Represents an exam period (e.g., "Session Normale S1", "Rattrapage").
    
    An exam session defines the date range when exams can be scheduled
    and groups related exams together.
    """
    __tablename__ = "exam_sessions"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    session_type: Mapped[str] = mapped_column(String(20), nullable=False)  # normal, rattrapage, special
    
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    academic_year: Mapped[str] = mapped_column(String(9), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft, published, in_progress, completed
    
    # Validation tracking
    validated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("professors.id")
    )
    validated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    
    # Relationships
    exams: Mapped[List["Exam"]] = relationship(back_populates="session")


# ==============================================================================
# EXAM MODEL
# ==============================================================================

class Exam(Base):
    """
    Represents a scheduled exam for a specific module.
    
    This is the core entity of the scheduling system. An exam:
    - Belongs to a module and session
    - Is assigned a room, date, and time (when scheduled)
    - Has supervisors (professors)
    """
    __tablename__ = "exams"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    module_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("modules.id", ondelete="RESTRICT"),
        nullable=False
    )
    
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("exam_sessions.id", ondelete="CASCADE"),
        nullable=False
    )
    
    room_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("exam_rooms.id", ondelete="SET NULL")
    )
    
    # Schedule (NULL before scheduling)
    scheduled_date: Mapped[Optional[date]] = mapped_column(Date)
    start_time: Mapped[Optional[time]] = mapped_column(Time)
    
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, scheduled, in_progress, completed, cancelled
    
    expected_students: Mapped[int] = mapped_column(Integer, default=0)
    
    # Requirements
    requires_computer: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_lab: Mapped[bool] = mapped_column(Boolean, default=False)
    
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    
    # Relationships
    module: Mapped["Module"] = relationship(back_populates="exams")
    session: Mapped["ExamSession"] = relationship(back_populates="exams")
    room: Mapped[Optional["ExamRoom"]] = relationship(back_populates="exams")
    supervisors: Mapped[List["ExamSupervisor"]] = relationship(back_populates="exam")


# ==============================================================================
# EXAM SUPERVISOR MODEL
# ==============================================================================

class ExamSupervisor(Base):
    """
    Junction table linking professors to exams as supervisors.
    
    Tracks which professors supervise which exams and their role
    (responsible, supervisor, assistant).
    """
    __tablename__ = "exam_supervisors"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    exam_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("exams.id", ondelete="CASCADE"),
        nullable=False
    )
    
    professor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("professors.id", ondelete="CASCADE"),
        nullable=False
    )
    
    role: Mapped[str] = mapped_column(String(20), default="supervisor")  # responsible, supervisor, assistant
    is_department_exam: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    
    # Relationships
    exam: Mapped["Exam"] = relationship(back_populates="supervisors")
    professor: Mapped["Professor"] = relationship(back_populates="supervisions")
    
    __table_args__ = (
        UniqueConstraint("exam_id", "professor_id", name="unique_supervisor"),
    )


# ==============================================================================
# USER MODEL
# ==============================================================================

class User(Base):
    """
    Represents an authenticated user of the system.
    
    Users have roles that determine their permissions:
    - admin: Full system access
    - vice_dean/dean: Strategic view, validation
    - dept_head: Department-level access
    - professor: View and supervise
    - student: View personal schedule only
    """
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    
    role: Mapped[str] = mapped_column(String(30), nullable=False)
    
    # Link to professor or student (optional)
    professor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("professors.id", ondelete="SET NULL")
    )
    
    student_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="SET NULL")
    )
    
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="SET NULL")
    )
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
