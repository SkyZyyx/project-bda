# ==============================================================================
# PYDANTIC SCHEMAS FOR API DATA VALIDATION
# ==============================================================================
# Pydantic schemas define the shape of data going in and out of our API.
# They provide automatic validation, serialization, and documentation.
#
# Naming convention:
# - Base: Shared fields between create and response
# - Create: Fields needed to create a new record
# - Update: Fields that can be updated (all optional)
# - Response: Fields returned by the API (includes id, timestamps)
# ==============================================================================

from datetime import datetime, date, time
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr, ConfigDict


# ==============================================================================
# DEPARTMENT SCHEMAS
# ==============================================================================

class DepartmentBase(BaseModel):
    """Base fields shared between create and response."""
    name: str = Field(..., min_length=2, max_length=100, description="Department name")
    code: str = Field(..., min_length=2, max_length=10, description="Short code (e.g., INFO)")
    email: Optional[str] = Field(None, description="Department email")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    building: Optional[str] = Field(None, max_length=100, description="Building location")


class DepartmentCreate(DepartmentBase):
    """Schema for creating a new department."""
    pass


class DepartmentUpdate(BaseModel):
    """Schema for updating a department. All fields are optional."""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    code: Optional[str] = Field(None, min_length=2, max_length=10)
    email: Optional[str] = None
    phone: Optional[str] = None
    building: Optional[str] = None
    is_active: Optional[bool] = None


class DepartmentResponse(DepartmentBase):
    """Schema for department API responses."""
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    # This allows Pydantic to read data from SQLAlchemy models
    model_config = ConfigDict(from_attributes=True)


class DepartmentWithStats(DepartmentResponse):
    """Department with computed statistics."""
    formation_count: int = 0
    student_count: int = 0
    professor_count: int = 0


# ==============================================================================
# FORMATION SCHEMAS
# ==============================================================================

class FormationBase(BaseModel):
    """Base formation fields."""
    name: str = Field(..., min_length=2, max_length=150)
    code: str = Field(..., min_length=2, max_length=20)
    level: str = Field(..., pattern="^(L1|L2|L3|M1|M2|D)$", description="Academic level")
    academic_year: str = Field(..., pattern="^\\d{4}-\\d{4}$", description="Format: 2024-2025")


class FormationCreate(FormationBase):
    """Schema for creating a formation."""
    department_id: UUID


class FormationUpdate(BaseModel):
    """Schema for updating a formation."""
    name: Optional[str] = None
    code: Optional[str] = None
    level: Optional[str] = None
    academic_year: Optional[str] = None
    is_active: Optional[bool] = None


class FormationResponse(FormationBase):
    """Formation response schema."""
    id: UUID
    department_id: UUID
    module_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class FormationWithDepartment(FormationResponse):
    """Formation with department details."""
    department: DepartmentResponse


# ==============================================================================
# PROFESSOR SCHEMAS
# ==============================================================================

class ProfessorBase(BaseModel):
    """Base professor fields."""
    first_name: str = Field(..., min_length=2, max_length=100)
    last_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: Optional[str] = None
    title: str = Field(default="Lecturer", max_length=50)
    specialization: Optional[str] = None
    max_exams_per_day: int = Field(default=3, ge=1, le=10)


class ProfessorCreate(ProfessorBase):
    """Schema for creating a professor."""
    department_id: UUID


class ProfessorUpdate(BaseModel):
    """Schema for updating a professor."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    specialization: Optional[str] = None
    max_exams_per_day: Optional[int] = None
    is_active: Optional[bool] = None


class ProfessorResponse(ProfessorBase):
    """Professor response schema."""
    id: UUID
    department_id: UUID
    supervision_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ProfessorWithWorkload(ProfessorResponse):
    """Professor with workload statistics."""
    department_name: str
    scheduled_supervisions: int = 0


# ==============================================================================
# STUDENT SCHEMAS
# ==============================================================================

class StudentBase(BaseModel):
    """Base student fields."""
    student_number: str = Field(..., min_length=5, max_length=20, description="Matricule")
    first_name: str = Field(..., min_length=2, max_length=100)
    last_name: str = Field(..., min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    enrollment_year: int = Field(..., ge=2000, le=2100)
    promotion: Optional[str] = None


class StudentCreate(StudentBase):
    """Schema for creating a student."""
    formation_id: UUID


class StudentUpdate(BaseModel):
    """Schema for updating a student."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    formation_id: Optional[UUID] = None
    promotion: Optional[str] = None
    is_active: Optional[bool] = None


class StudentResponse(StudentBase):
    """Student response schema."""
    id: UUID
    formation_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class StudentWithFormation(StudentResponse):
    """Student with formation details."""
    formation_name: str
    department_name: str


# ==============================================================================
# MODULE SCHEMAS
# ==============================================================================

class ModuleBase(BaseModel):
    """Base module fields."""
    name: str = Field(..., min_length=2, max_length=150)
    code: str = Field(..., min_length=2, max_length=20)
    credits: int = Field(..., ge=1, le=10)
    exam_duration_minutes: int = Field(default=120, ge=30, le=300)
    requires_computer: bool = False
    requires_lab: bool = False
    semester: Optional[int] = Field(None, ge=1, le=2)


class ModuleCreate(ModuleBase):
    """Schema for creating a module."""
    formation_id: UUID
    prerequisite_id: Optional[UUID] = None


class ModuleUpdate(BaseModel):
    """Schema for updating a module."""
    name: Optional[str] = None
    code: Optional[str] = None
    credits: Optional[int] = None
    exam_duration_minutes: Optional[int] = None
    requires_computer: Optional[bool] = None
    requires_lab: Optional[bool] = None
    semester: Optional[int] = None
    is_active: Optional[bool] = None


class ModuleResponse(ModuleBase):
    """Module response schema."""
    id: UUID
    formation_id: UUID
    prerequisite_id: Optional[UUID]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ModuleWithEnrollmentCount(ModuleResponse):
    """Module with enrollment statistics."""
    enrolled_students: int = 0


# ==============================================================================
# EXAM ROOM SCHEMAS
# ==============================================================================

class ExamRoomBase(BaseModel):
    """Base exam room fields."""
    name: str = Field(..., min_length=2, max_length=100)
    building: str = Field(..., min_length=2, max_length=100)
    floor: int = Field(default=0, ge=-5, le=50)
    room_type: str = Field(..., pattern="^(amphi|classroom|lab|salle)$")
    total_capacity: int = Field(..., ge=1, le=1000)
    exam_capacity: int = Field(..., ge=1, le=500)
    has_computers: bool = False
    has_projector: bool = True
    has_video_surveillance: bool = False
    is_accessible: bool = True


class ExamRoomCreate(ExamRoomBase):
    """Schema for creating an exam room."""
    pass


class ExamRoomUpdate(BaseModel):
    """Schema for updating an exam room."""
    name: Optional[str] = None
    building: Optional[str] = None
    floor: Optional[int] = None
    total_capacity: Optional[int] = None
    exam_capacity: Optional[int] = None
    has_computers: Optional[bool] = None
    has_projector: Optional[bool] = None
    is_available: Optional[bool] = None
    is_active: Optional[bool] = None


class ExamRoomResponse(ExamRoomBase):
    """Exam room response schema."""
    id: UUID
    is_available: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ExamRoomWithUtilization(ExamRoomResponse):
    """Room with utilization statistics."""
    scheduled_exams: int = 0
    utilization_percent: float = 0.0


# ==============================================================================
# EXAM SESSION SCHEMAS
# ==============================================================================

class ExamSessionBase(BaseModel):
    """Base exam session fields."""
    name: str = Field(..., min_length=2, max_length=100)
    session_type: str = Field(..., pattern="^(normal|rattrapage|special)$")
    start_date: date
    end_date: date
    academic_year: str = Field(..., pattern="^\\d{4}-\\d{4}$")


class ExamSessionCreate(ExamSessionBase):
    """Schema for creating an exam session."""
    pass


class ExamSessionUpdate(BaseModel):
    """Schema for updating an exam session."""
    name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None


class ExamSessionResponse(ExamSessionBase):
    """Exam session response schema."""
    id: UUID
    status: str
    validated_by: Optional[UUID]
    validated_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ExamSessionWithStats(ExamSessionResponse):
    """Session with statistics."""
    total_exams: int = 0
    scheduled_exams: int = 0
    pending_exams: int = 0
    conflict_count: int = 0


# ==============================================================================
# EXAM SCHEMAS
# ==============================================================================

class ExamBase(BaseModel):
    """Base exam fields."""
    duration_minutes: int = Field(..., ge=30, le=300)
    requires_computer: bool = False
    requires_lab: bool = False
    notes: Optional[str] = None


class ExamCreate(ExamBase):
    """Schema for creating an exam."""
    module_id: UUID
    session_id: UUID


class ExamSchedule(BaseModel):
    """Schema for scheduling an exam."""
    scheduled_date: date
    start_time: time
    room_id: UUID


class ExamUpdate(BaseModel):
    """Schema for updating an exam."""
    scheduled_date: Optional[date] = None
    start_time: Optional[time] = None
    room_id: Optional[UUID] = None
    duration_minutes: Optional[int] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class ExamResponse(ExamBase):
    """Exam response schema."""
    id: UUID
    module_id: UUID
    session_id: UUID
    room_id: Optional[UUID]
    scheduled_date: Optional[date]
    start_time: Optional[time]
    status: str
    expected_students: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ExamDetail(ExamResponse):
    """Exam with full details."""
    module_name: str
    module_code: str
    formation_name: str
    department_name: str
    room_name: Optional[str] = None
    room_building: Optional[str] = None


class ExamSupervisorResponse(BaseModel):
    """Supervisor assignment response."""
    id: UUID
    exam_id: UUID
    professor_id: UUID
    professor_name: str
    role: str
    is_department_exam: bool
    
    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# CONFLICT SCHEMAS
# ==============================================================================

class StudentConflict(BaseModel):
    """Student conflict information."""
    student_id: UUID
    student_name: str
    conflict_date: date
    exam_count: int
    exam_list: str


class ProfessorConflict(BaseModel):
    """Professor conflict information."""
    professor_id: UUID
    professor_name: str
    conflict_date: date
    exam_count: int
    max_allowed: int
    exam_list: str


class RoomConflict(BaseModel):
    """Room conflict information."""
    room_id: UUID
    room_name: str
    building: str
    conflict_date: date
    exam1_name: str
    exam1_time: str
    exam2_name: str
    exam2_time: str


class ConflictSummary(BaseModel):
    """Summary of all conflicts."""
    conflict_type: str
    conflict_count: int
    severity: str


# ==============================================================================
# SCHEDULING SCHEMAS
# ==============================================================================

class AvailableSlot(BaseModel):
    """An available time slot for an exam."""
    slot_date: date
    slot_time: time
    room_id: UUID
    room_name: str
    room_capacity: int
    score: int  # Higher score = better slot


class ScheduleResult(BaseModel):
    """Result of automatic scheduling."""
    success: bool
    message: str
    scheduled_date: Optional[date] = None
    scheduled_time: Optional[time] = None
    room_name: Optional[str] = None


class SessionScheduleResult(BaseModel):
    """Result of scheduling an entire session."""
    total_exams: int
    scheduled_count: int
    failed_count: int
    execution_time_ms: int


# ==============================================================================
# STATISTICS SCHEMAS
# ==============================================================================

class SessionStats(BaseModel):
    """Statistics for an exam session."""
    total_exams: int
    scheduled_exams: int
    pending_exams: int
    total_rooms_used: int
    total_professors_assigned: int
    avg_room_utilization: Optional[float]
    conflict_count: int
    departments_covered: int


class DepartmentStats(BaseModel):
    """Statistics for a department."""
    department_name: str
    total_exams: int
    scheduled_exams: int
    total_students: int
    professors_supervising: int
    student_conflicts: int
    formations_count: int


class ProfessorWorkloadStats(BaseModel):
    """Professor workload for fair distribution analysis."""
    professor_id: UUID
    professor_name: str
    department_name: str
    supervision_count: int
    dept_exams_count: int
    other_exams_count: int
    deviation_from_mean: float


# ==============================================================================
# DASHBOARD SCHEMAS
# ==============================================================================

class DashboardOverview(BaseModel):
    """Overview data for the main dashboard."""
    total_departments: int
    total_formations: int
    total_students: int
    total_professors: int
    total_modules: int
    total_exam_rooms: int
    active_sessions: List[ExamSessionWithStats]


class DepartmentDashboard(BaseModel):
    """Department-specific dashboard data."""
    department: DepartmentWithStats
    formations: List[FormationResponse]
    upcoming_exams: List[ExamDetail]
    conflict_summary: List[ConflictSummary]


# ==============================================================================
# AUTHENTICATION SCHEMAS
# ==============================================================================

class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Data stored in JWT token."""
    sub: str  # User ID
    email: str
    role: str


class UserLogin(BaseModel):
    """User login request."""
    email: EmailStr
    password: str


class UserCreate(BaseModel):
    """Create a new user."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: str
    professor_id: Optional[UUID] = None
    student_id: Optional[UUID] = None
    department_id: Optional[UUID] = None


class UserResponse(BaseModel):
    """User response (no password)."""
    id: UUID
    email: str
    role: str
    professor_id: Optional[UUID]
    student_id: Optional[UUID]
    department_id: Optional[UUID]
    is_active: bool
    last_login: Optional[datetime]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# PAGINATION SCHEMAS
# ==============================================================================

class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)


class PaginatedResponse(BaseModel):
    """Generic paginated response."""
    items: List
    total: int
    page: int
    size: int
    pages: int
