# Schemas module exports
from app.schemas.schemas import (
    # Department
    DepartmentCreate, DepartmentUpdate, DepartmentResponse, DepartmentWithStats,
    # Formation
    FormationCreate, FormationUpdate, FormationResponse, FormationWithDepartment,
    # Professor
    ProfessorCreate, ProfessorUpdate, ProfessorResponse, ProfessorWithWorkload,
    # Student
    StudentCreate, StudentUpdate, StudentResponse, StudentWithFormation,
    # Module
    ModuleCreate, ModuleUpdate, ModuleResponse, ModuleWithEnrollmentCount,
    # ExamRoom
    ExamRoomCreate, ExamRoomUpdate, ExamRoomResponse, ExamRoomWithUtilization,
    # ExamSession
    ExamSessionCreate, ExamSessionUpdate, ExamSessionResponse, ExamSessionWithStats,
    # Exam
    ExamCreate, ExamSchedule, ExamUpdate, ExamResponse, ExamDetail, ExamSupervisorResponse,
    # Conflicts
    StudentConflict, ProfessorConflict, RoomConflict, ConflictSummary,
    # Scheduling
    AvailableSlot, ScheduleResult, SessionScheduleResult,
    # Statistics
    SessionStats, DepartmentStats, ProfessorWorkloadStats,
    # Dashboard
    DashboardOverview, DepartmentDashboard,
    # Auth
    Token, TokenData, UserLogin, UserCreate, UserResponse,
    # Pagination
    PaginationParams, PaginatedResponse,
)

__all__ = [
    "DepartmentCreate", "DepartmentUpdate", "DepartmentResponse", "DepartmentWithStats",
    "FormationCreate", "FormationUpdate", "FormationResponse", "FormationWithDepartment",
    "ProfessorCreate", "ProfessorUpdate", "ProfessorResponse", "ProfessorWithWorkload",
    "StudentCreate", "StudentUpdate", "StudentResponse", "StudentWithFormation",
    "ModuleCreate", "ModuleUpdate", "ModuleResponse", "ModuleWithEnrollmentCount",
    "ExamRoomCreate", "ExamRoomUpdate", "ExamRoomResponse", "ExamRoomWithUtilization",
    "ExamSessionCreate", "ExamSessionUpdate", "ExamSessionResponse", "ExamSessionWithStats",
    "ExamCreate", "ExamSchedule", "ExamUpdate", "ExamResponse", "ExamDetail", "ExamSupervisorResponse",
    "StudentConflict", "ProfessorConflict", "RoomConflict", "ConflictSummary",
    "AvailableSlot", "ScheduleResult", "SessionScheduleResult",
    "SessionStats", "DepartmentStats", "ProfessorWorkloadStats",
    "DashboardOverview", "DepartmentDashboard",
    "Token", "TokenData", "UserLogin", "UserCreate", "UserResponse",
    "PaginationParams", "PaginatedResponse",
]
