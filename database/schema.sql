-- ============================================================================
-- EXAM SCHEDULING PLATFORM - DATABASE SCHEMA
-- ============================================================================
-- This schema is designed for a university with:
-- - 7 departments
-- - 200+ training programs (formations)
-- - 13,000+ students
-- - 130,000+ course enrollments
--
-- The design follows 3NF (Third Normal Form) to minimize data redundancy
-- while maintaining query performance through strategic indexing.
-- ============================================================================

-- Enable UUID extension for generating unique identifiers
-- UUIDs are better than auto-increment IDs for distributed systems
-- and prevent ID enumeration attacks
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- CORE ACADEMIC STRUCTURE
-- ============================================================================

-- DEPARTMENTS TABLE
-- Represents the 7 major academic departments of the faculty
-- Examples: Computer Science, Mathematics, Physics, etc.
CREATE TABLE departments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Department name must be unique (can't have two "Computer Science" depts)
    name VARCHAR(100) NOT NULL UNIQUE,
    
    -- Short code for quick identification (e.g., "CS", "MATH", "PHY")
    code VARCHAR(10) NOT NULL UNIQUE,
    
    -- Contact info for the department
    email VARCHAR(255),
    phone VARCHAR(20),
    
    -- Building/location information
    building VARCHAR(100),
    
    -- Soft delete: instead of deleting, we mark as inactive
    -- This preserves historical data integrity
    is_active BOOLEAN DEFAULT true,
    
    -- Audit timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- FORMATIONS TABLE (Training Programs)
-- A formation is a specific study program like "L3 Computer Science" or "M1 Data Science"
-- Each department offers multiple formations
CREATE TABLE formations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Link to parent department
    department_id UUID NOT NULL REFERENCES departments(id) ON DELETE RESTRICT,
    
    -- Formation name (e.g., "Licence Informatique", "Master Data Science")
    name VARCHAR(150) NOT NULL,
    
    -- Short code (e.g., "L3-INFO", "M1-DS")
    code VARCHAR(20) NOT NULL UNIQUE,
    
    -- Academic level: L1, L2, L3, M1, M2, D (Doctorate)
    level VARCHAR(10) NOT NULL CHECK (level IN ('L1', 'L2', 'L3', 'M1', 'M2', 'D')),
    
    -- Number of modules in this formation (6-9 as per requirements)
    -- This is denormalized for performance (could be computed from modules table)
    module_count INTEGER DEFAULT 0 CHECK (module_count >= 0),
    
    -- Academic year this formation is for (e.g., "2024-2025")
    academic_year VARCHAR(9) NOT NULL,
    
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- A department can't have duplicate formation names in the same year
    UNIQUE(department_id, name, academic_year)
);

-- PROFESSORS TABLE
-- Faculty members who teach modules and supervise exams
CREATE TABLE professors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Link to their primary department
    department_id UUID NOT NULL REFERENCES departments(id) ON DELETE RESTRICT,
    
    -- Personal information
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    
    -- Professional email (university domain)
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(20),
    
    -- Academic title: Professor, Associate Prof, Assistant Prof, Lecturer
    title VARCHAR(50) DEFAULT 'Lecturer',
    
    -- Their area of expertise (for matching with modules)
    specialization VARCHAR(200),
    
    -- Maximum exams they can supervise per day (default: 3 as per requirements)
    max_exams_per_day INTEGER DEFAULT 3 CHECK (max_exams_per_day > 0),
    
    -- Track how many supervisions they've been assigned (for fair distribution)
    -- This is denormalized and updated by triggers
    supervision_count INTEGER DEFAULT 0,
    
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- STUDENTS TABLE
-- All enrolled students in the faculty
CREATE TABLE students (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Link to their current formation
    formation_id UUID NOT NULL REFERENCES formations(id) ON DELETE RESTRICT,
    
    -- Student identification number (matricule)
    student_number VARCHAR(20) NOT NULL UNIQUE,
    
    -- Personal information
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE,
    
    -- Academic year of first enrollment (e.g., 2022)
    enrollment_year INTEGER NOT NULL,
    
    -- Current promotion/cohort (e.g., "2024")
    promotion VARCHAR(10),
    
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- MODULES TABLE
-- Individual courses/subjects within formations
CREATE TABLE modules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Link to parent formation
    formation_id UUID NOT NULL REFERENCES formations(id) ON DELETE RESTRICT,
    
    -- Module name (e.g., "Database Systems", "Algorithms")
    name VARCHAR(150) NOT NULL,
    
    -- Module code (e.g., "BDA-401", "ALGO-201")
    code VARCHAR(20) NOT NULL UNIQUE,
    
    -- ECTS credits (usually 2-6)
    credits INTEGER NOT NULL CHECK (credits > 0 AND credits <= 10),
    
    -- Optional prerequisite module
    prerequisite_id UUID REFERENCES modules(id) ON DELETE SET NULL,
    
    -- Exam duration in minutes (typical: 60, 90, 120, 180)
    exam_duration_minutes INTEGER DEFAULT 120 CHECK (exam_duration_minutes > 0),
    
    -- Whether this module requires special equipment (computers, lab, etc.)
    requires_computer BOOLEAN DEFAULT false,
    requires_lab BOOLEAN DEFAULT false,
    
    -- Semester: 1 (Fall) or 2 (Spring)
    semester INTEGER CHECK (semester IN (1, 2)),
    
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- EXAM INFRASTRUCTURE
-- ============================================================================

-- EXAM ROOMS TABLE
-- All available rooms for exams: amphitheaters, classrooms, labs
CREATE TABLE exam_rooms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Room identification
    name VARCHAR(100) NOT NULL,          -- e.g., "Amphi A", "Room 101"
    building VARCHAR(100) NOT NULL,       -- e.g., "Main Building", "Science Block"
    floor INTEGER DEFAULT 0,
    
    -- Room type determines capacity limits
    -- 'amphi': large amphitheater (100-500 students)
    -- 'classroom': standard room (30-50 students, but 20 max for exams)
    -- 'lab': computer lab with special equipment
    room_type VARCHAR(20) NOT NULL CHECK (room_type IN ('amphi', 'classroom', 'lab')),
    
    -- Total physical capacity
    total_capacity INTEGER NOT NULL CHECK (total_capacity > 0),
    
    -- Exam capacity (reduced for spacing - usually 50% of total, max 20 for small rooms)
    -- This is the actual number of students that can take an exam here
    exam_capacity INTEGER NOT NULL CHECK (exam_capacity > 0),
    
    -- Equipment availability
    has_computers BOOLEAN DEFAULT false,
    has_projector BOOLEAN DEFAULT true,
    has_video_surveillance BOOLEAN DEFAULT false,
    is_accessible BOOLEAN DEFAULT true,  -- Wheelchair accessible
    
    -- Availability status
    is_available BOOLEAN DEFAULT true,
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Ensure exam capacity doesn't exceed total capacity
    CONSTRAINT valid_exam_capacity CHECK (exam_capacity <= total_capacity),
    
    -- Unique room names within a building
    UNIQUE(building, name)
);

-- ============================================================================
-- ENROLLMENT AND SCHEDULING
-- ============================================================================

-- ENROLLMENTS TABLE
-- Tracks which students are enrolled in which modules
-- This is the junction table for the many-to-many relationship
CREATE TABLE enrollments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    module_id UUID NOT NULL REFERENCES modules(id) ON DELETE CASCADE,
    
    -- Academic year for this enrollment
    academic_year VARCHAR(9) NOT NULL,
    
    -- Enrollment status
    status VARCHAR(20) DEFAULT 'enrolled' CHECK (status IN ('enrolled', 'dropped', 'completed')),
    
    -- Grade (NULL if not yet graded, 0-20 scale typical in French system)
    grade DECIMAL(4,2) CHECK (grade IS NULL OR (grade >= 0 AND grade <= 20)),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- A student can only be enrolled once per module per year
    UNIQUE(student_id, module_id, academic_year)
);

-- EXAM SESSIONS TABLE
-- Represents an exam period (e.g., "Session Normale Janvier 2025", "Session Rattrapage")
CREATE TABLE exam_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Session name (e.g., "Session Normale S1", "Session Rattrapage S1")
    name VARCHAR(100) NOT NULL,
    
    -- Session type
    session_type VARCHAR(20) NOT NULL CHECK (session_type IN ('normal', 'rattrapage', 'special')),
    
    -- Date range for this exam session
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    
    -- Academic year
    academic_year VARCHAR(9) NOT NULL,
    
    -- Status of the session
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'in_progress', 'completed')),
    
    -- Validation tracking
    validated_by UUID REFERENCES professors(id),
    validated_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Valid date range
    CONSTRAINT valid_date_range CHECK (end_date >= start_date),
    
    -- Unique session per type per year
    UNIQUE(name, academic_year)
);

-- EXAMS TABLE
-- Individual scheduled exams - the core of our scheduling system
CREATE TABLE exams (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Which module is being examined
    module_id UUID NOT NULL REFERENCES modules(id) ON DELETE RESTRICT,
    
    -- Which exam session this belongs to
    session_id UUID NOT NULL REFERENCES exam_sessions(id) ON DELETE CASCADE,
    
    -- Assigned room (can be NULL initially before scheduling)
    room_id UUID REFERENCES exam_rooms(id) ON DELETE SET NULL,
    
    -- Scheduled date and time
    scheduled_date DATE,
    start_time TIME,
    
    -- Duration in minutes (copied from module, but can be overridden)
    duration_minutes INTEGER NOT NULL CHECK (duration_minutes > 0),
    
    -- Scheduling status
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'scheduled', 'in_progress', 'completed', 'cancelled')),
    
    -- Number of students expected (for room allocation)
    expected_students INTEGER DEFAULT 0,
    
    -- Special requirements
    requires_computer BOOLEAN DEFAULT false,
    requires_lab BOOLEAN DEFAULT false,
    
    -- Notes for invigilators
    notes TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- One exam per module per session
    UNIQUE(module_id, session_id)
);

-- EXAM SUPERVISORS TABLE (Junction table)
-- Tracks which professors supervise which exams
-- Multiple professors can supervise one exam (for large amphitheaters)
CREATE TABLE exam_supervisors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    exam_id UUID NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
    professor_id UUID NOT NULL REFERENCES professors(id) ON DELETE CASCADE,
    
    -- Role in this exam
    role VARCHAR(20) DEFAULT 'supervisor' CHECK (role IN ('responsible', 'supervisor', 'assistant')),
    
    -- Is this their department's exam? (for priority scheduling)
    is_department_exam BOOLEAN DEFAULT false,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- A professor can only be assigned once per exam
    UNIQUE(exam_id, professor_id)
);

-- ============================================================================
-- USER AUTHENTICATION & AUTHORIZATION
-- ============================================================================

-- USERS TABLE
-- For authentication - links to either professors or students
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Email for login
    email VARCHAR(255) NOT NULL UNIQUE,
    
    -- Password hash (we'll use bcrypt)
    password_hash VARCHAR(255) NOT NULL,
    
    -- Role-based access control
    role VARCHAR(30) NOT NULL CHECK (role IN (
        'admin',           -- Full system access
        'vice_dean',       -- Strategic view, validation
        'dean',            -- Final approval
        'dept_head',       -- Department-level access
        'professor',       -- View and supervise
        'student'          -- View personal schedule only
    )),
    
    -- Link to professor or student record
    professor_id UUID REFERENCES professors(id) ON DELETE SET NULL,
    student_id UUID REFERENCES students(id) ON DELETE SET NULL,
    
    -- For department heads, which department they manage
    department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
    
    -- Account status
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Must be linked to either professor or student (or neither for admin)
    CONSTRAINT valid_user_link CHECK (
        (professor_id IS NULL AND student_id IS NULL) OR  -- Admin/Dean
        (professor_id IS NOT NULL AND student_id IS NULL) OR  -- Professor
        (professor_id IS NULL AND student_id IS NOT NULL)  -- Student
    )
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE OPTIMIZATION
-- ============================================================================

-- Indexes are crucial for our 130k+ enrollments dataset
-- They speed up queries but slow down inserts, so we're strategic

-- Department lookups
CREATE INDEX idx_departments_code ON departments(code);

-- Formation lookups by department and level
CREATE INDEX idx_formations_department ON formations(department_id);
CREATE INDEX idx_formations_level ON formations(level);
CREATE INDEX idx_formations_year ON formations(academic_year);

-- Student lookups
CREATE INDEX idx_students_formation ON students(formation_id);
CREATE INDEX idx_students_number ON students(student_number);
CREATE INDEX idx_students_promotion ON students(promotion);

-- Professor lookups
CREATE INDEX idx_professors_department ON professors(department_id);
CREATE INDEX idx_professors_supervision_count ON professors(supervision_count);

-- Module lookups
CREATE INDEX idx_modules_formation ON modules(formation_id);
CREATE INDEX idx_modules_semester ON modules(semester);

-- Enrollment lookups (most critical for performance)
CREATE INDEX idx_enrollments_student ON enrollments(student_id);
CREATE INDEX idx_enrollments_module ON enrollments(module_id);
CREATE INDEX idx_enrollments_year ON enrollments(academic_year);
CREATE INDEX idx_enrollments_student_year ON enrollments(student_id, academic_year);

-- Exam lookups
CREATE INDEX idx_exams_session ON exams(session_id);
CREATE INDEX idx_exams_module ON exams(module_id);
CREATE INDEX idx_exams_room ON exams(room_id);
CREATE INDEX idx_exams_date ON exams(scheduled_date);
CREATE INDEX idx_exams_status ON exams(status);

-- Partial index for only scheduled exams (used in conflict detection)
CREATE INDEX idx_exams_scheduled ON exams(scheduled_date, start_time) 
    WHERE status = 'scheduled';

-- Supervisor lookups
CREATE INDEX idx_supervisors_exam ON exam_supervisors(exam_id);
CREATE INDEX idx_supervisors_professor ON exam_supervisors(professor_id);

-- Room lookups
CREATE INDEX idx_rooms_type ON exam_rooms(room_type);
CREATE INDEX idx_rooms_capacity ON exam_rooms(exam_capacity);
CREATE INDEX idx_rooms_building ON exam_rooms(building);

-- ============================================================================
-- TRIGGERS FOR DATA INTEGRITY
-- ============================================================================

-- Function to update the updated_at timestamp automatically
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply the timestamp trigger to all tables with updated_at
CREATE TRIGGER update_departments_timestamp BEFORE UPDATE ON departments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
    
CREATE TRIGGER update_formations_timestamp BEFORE UPDATE ON formations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
    
CREATE TRIGGER update_professors_timestamp BEFORE UPDATE ON professors
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
    
CREATE TRIGGER update_students_timestamp BEFORE UPDATE ON students
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
    
CREATE TRIGGER update_modules_timestamp BEFORE UPDATE ON modules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
    
CREATE TRIGGER update_exam_rooms_timestamp BEFORE UPDATE ON exam_rooms
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
    
CREATE TRIGGER update_enrollments_timestamp BEFORE UPDATE ON enrollments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
    
CREATE TRIGGER update_exam_sessions_timestamp BEFORE UPDATE ON exam_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
    
CREATE TRIGGER update_exams_timestamp BEFORE UPDATE ON exams
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
    
CREATE TRIGGER update_users_timestamp BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Function to update formation module count when modules change
CREATE OR REPLACE FUNCTION update_formation_module_count()
RETURNS TRIGGER AS $$
BEGIN
    -- Update the count for the affected formation(s)
    IF TG_OP = 'DELETE' THEN
        UPDATE formations SET module_count = (
            SELECT COUNT(*) FROM modules WHERE formation_id = OLD.formation_id AND is_active = true
        ) WHERE id = OLD.formation_id;
        RETURN OLD;
    ELSE
        UPDATE formations SET module_count = (
            SELECT COUNT(*) FROM modules WHERE formation_id = NEW.formation_id AND is_active = true
        ) WHERE id = NEW.formation_id;
        
        -- If formation_id changed, update the old formation too
        IF TG_OP = 'UPDATE' AND OLD.formation_id != NEW.formation_id THEN
            UPDATE formations SET module_count = (
                SELECT COUNT(*) FROM modules WHERE formation_id = OLD.formation_id AND is_active = true
            ) WHERE id = OLD.formation_id;
        END IF;
        
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_module_count_on_change
    AFTER INSERT OR UPDATE OR DELETE ON modules
    FOR EACH ROW EXECUTE FUNCTION update_formation_module_count();

-- Function to update professor supervision count
CREATE OR REPLACE FUNCTION update_professor_supervision_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        UPDATE professors SET supervision_count = supervision_count - 1
        WHERE id = OLD.professor_id;
        RETURN OLD;
    ELSIF TG_OP = 'INSERT' THEN
        UPDATE professors SET supervision_count = supervision_count + 1
        WHERE id = NEW.professor_id;
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_supervision_count
    AFTER INSERT OR DELETE ON exam_supervisors
    FOR EACH ROW EXECUTE FUNCTION update_professor_supervision_count();

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- View: Complete exam information with all related data
CREATE OR REPLACE VIEW exam_details AS
SELECT 
    e.id AS exam_id,
    e.scheduled_date,
    e.start_time,
    e.duration_minutes,
    e.status AS exam_status,
    e.expected_students,
    m.id AS module_id,
    m.name AS module_name,
    m.code AS module_code,
    f.id AS formation_id,
    f.name AS formation_name,
    f.level AS formation_level,
    d.id AS department_id,
    d.name AS department_name,
    d.code AS department_code,
    r.id AS room_id,
    r.name AS room_name,
    r.building AS room_building,
    r.exam_capacity,
    es.id AS session_id,
    es.name AS session_name
FROM exams e
JOIN modules m ON e.module_id = m.id
JOIN formations f ON m.formation_id = f.id
JOIN departments d ON f.department_id = d.id
LEFT JOIN exam_rooms r ON e.room_id = r.id
JOIN exam_sessions es ON e.session_id = es.id;

-- View: Student schedule with their enrolled exams
CREATE OR REPLACE VIEW student_exam_schedule AS
SELECT 
    s.id AS student_id,
    s.student_number,
    s.first_name,
    s.last_name,
    s.formation_id,
    e.id AS exam_id,
    e.scheduled_date,
    e.start_time,
    e.duration_minutes,
    m.name AS module_name,
    m.code AS module_code,
    r.name AS room_name,
    r.building AS room_building
FROM students s
JOIN enrollments enr ON s.id = enr.student_id
JOIN modules m ON enr.module_id = m.id
JOIN exams e ON m.id = e.module_id
LEFT JOIN exam_rooms r ON e.room_id = r.id
WHERE enr.status = 'enrolled' AND e.status = 'scheduled';

-- View: Professor supervision schedule
CREATE OR REPLACE VIEW professor_supervision_schedule AS
SELECT 
    p.id AS professor_id,
    p.first_name,
    p.last_name,
    p.department_id,
    es.exam_id,
    es.role,
    es.is_department_exam,
    e.scheduled_date,
    e.start_time,
    e.duration_minutes,
    m.name AS module_name,
    r.name AS room_name,
    r.building AS room_building
FROM professors p
JOIN exam_supervisors es ON p.id = es.professor_id
JOIN exams e ON es.exam_id = e.id
JOIN modules m ON e.module_id = m.id
LEFT JOIN exam_rooms r ON e.room_id = r.id
WHERE e.status = 'scheduled';

-- View: Department statistics
CREATE OR REPLACE VIEW department_stats AS
SELECT 
    d.id AS department_id,
    d.name AS department_name,
    d.code AS department_code,
    COUNT(DISTINCT f.id) AS formation_count,
    COUNT(DISTINCT s.id) AS student_count,
    COUNT(DISTINCT p.id) AS professor_count,
    COUNT(DISTINCT m.id) AS module_count
FROM departments d
LEFT JOIN formations f ON d.id = f.department_id AND f.is_active = true
LEFT JOIN students s ON f.id = s.formation_id AND s.is_active = true
LEFT JOIN professors p ON d.id = p.department_id AND p.is_active = true
LEFT JOIN modules m ON f.id = m.formation_id AND m.is_active = true
WHERE d.is_active = true
GROUP BY d.id, d.name, d.code;

-- View: Room utilization
CREATE OR REPLACE VIEW room_utilization AS
SELECT 
    r.id AS room_id,
    r.name AS room_name,
    r.building,
    r.room_type,
    r.exam_capacity,
    COUNT(e.id) AS scheduled_exams,
    SUM(e.expected_students) AS total_students_served,
    ROUND(AVG(e.expected_students::DECIMAL / r.exam_capacity * 100), 2) AS avg_utilization_percent
FROM exam_rooms r
LEFT JOIN exams e ON r.id = e.room_id AND e.status = 'scheduled'
WHERE r.is_active = true
GROUP BY r.id, r.name, r.building, r.room_type, r.exam_capacity;

COMMENT ON SCHEMA public IS 'Exam Scheduling Platform - University Exam Management System';
