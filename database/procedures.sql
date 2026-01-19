-- ============================================================================
-- EXAM SCHEDULING PLATFORM - STORED PROCEDURES
-- ============================================================================
-- These procedures handle the core business logic:
-- 1. Conflict detection (students, professors, rooms)
-- 2. Schedule optimization
-- 3. Statistics and KPIs
-- ============================================================================

-- ============================================================================
-- CONFLICT DETECTION PROCEDURES
-- ============================================================================

-- TYPE: Conflict information structure
-- This custom type holds details about any detected conflict
DROP TYPE IF EXISTS conflict_info CASCADE;
CREATE TYPE conflict_info AS (
    conflict_type VARCHAR(50),      -- 'student', 'professor', 'room'
    entity_id UUID,                  -- ID of the conflicting entity
    entity_name VARCHAR(200),        -- Human-readable name
    exam1_id UUID,                   -- First conflicting exam
    exam2_id UUID,                   -- Second conflicting exam
    conflict_date DATE,              -- Date of conflict
    conflict_time TIME,              -- Time of conflict
    details TEXT                     -- Additional details
);

-- ----------------------------------------------------------------------------
-- FUNCTION: Detect student conflicts
-- A student cannot have more than one exam on the same day
-- Returns all students who have multiple exams scheduled for the same day
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION detect_student_conflicts(p_session_id UUID)
RETURNS TABLE (
    student_id UUID,
    student_name TEXT,
    conflict_date DATE,
    exam_count INTEGER,
    exam_list TEXT
) AS $$
BEGIN
    -- We find students with more than 1 exam on the same day
    -- The constraint says "maximum 1 exam per day" for students
    RETURN QUERY
    SELECT 
        s.id,
        s.first_name || ' ' || s.last_name AS student_name,
        e.scheduled_date,
        COUNT(e.id)::INTEGER AS exam_count,
        STRING_AGG(m.name || ' (' || e.start_time::TEXT || ')', ', ' ORDER BY e.start_time) AS exam_list
    FROM students s
    -- Join through enrollments to find which exams the student is taking
    JOIN enrollments enr ON s.id = enr.student_id
    JOIN modules m ON enr.module_id = m.id
    JOIN exams e ON m.id = e.module_id
    WHERE 
        e.session_id = p_session_id
        AND e.status = 'scheduled'
        AND e.scheduled_date IS NOT NULL
        AND enr.status = 'enrolled'
    GROUP BY s.id, s.first_name, s.last_name, e.scheduled_date
    -- Only return students with MORE than 1 exam per day (conflict!)
    HAVING COUNT(e.id) > 1
    ORDER BY e.scheduled_date, student_name;
END;
$$ LANGUAGE plpgsql;

-- ----------------------------------------------------------------------------
-- FUNCTION: Detect professor conflicts
-- A professor cannot supervise more than 3 exams per day
-- Also detects time overlaps (same professor in two places at once)
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION detect_professor_conflicts(p_session_id UUID)
RETURNS TABLE (
    professor_id UUID,
    professor_name TEXT,
    conflict_date DATE,
    exam_count INTEGER,
    max_allowed INTEGER,
    exam_list TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        p.first_name || ' ' || p.last_name AS prof_name,
        e.scheduled_date,
        COUNT(e.id)::INTEGER AS exams_that_day,
        p.max_exams_per_day,
        STRING_AGG(
            m.name || ' (' || e.start_time::TEXT || '-' || 
            (e.start_time + (e.duration_minutes || ' minutes')::INTERVAL)::TIME::TEXT || ')', 
            ', ' ORDER BY e.start_time
        ) AS exam_list
    FROM professors p
    JOIN exam_supervisors es ON p.id = es.professor_id
    JOIN exams e ON es.exam_id = e.id
    JOIN modules m ON e.module_id = m.id
    WHERE 
        e.session_id = p_session_id
        AND e.status = 'scheduled'
        AND e.scheduled_date IS NOT NULL
    GROUP BY p.id, p.first_name, p.last_name, e.scheduled_date, p.max_exams_per_day
    -- Conflict: more exams than allowed
    HAVING COUNT(e.id) > p.max_exams_per_day
    ORDER BY e.scheduled_date, prof_name;
END;
$$ LANGUAGE plpgsql;

-- ----------------------------------------------------------------------------
-- FUNCTION: Detect professor time overlaps
-- A professor cannot be in two exams at the exact same time
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION detect_professor_time_overlaps(p_session_id UUID)
RETURNS TABLE (
    professor_id UUID,
    professor_name TEXT,
    conflict_date DATE,
    exam1_name TEXT,
    exam1_time TEXT,
    exam2_name TEXT,
    exam2_time TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH professor_exams AS (
        SELECT 
            p.id AS prof_id,
            p.first_name || ' ' || p.last_name AS prof_name,
            e.id AS exam_id,
            m.name AS module_name,
            e.scheduled_date,
            e.start_time,
            e.start_time + (e.duration_minutes || ' minutes')::INTERVAL AS end_time
        FROM professors p
        JOIN exam_supervisors es ON p.id = es.professor_id
        JOIN exams e ON es.exam_id = e.id
        JOIN modules m ON e.module_id = m.id
        WHERE 
            e.session_id = p_session_id
            AND e.status = 'scheduled'
    )
    -- Self-join to find overlapping exams for the same professor
    SELECT 
        pe1.prof_id,
        pe1.prof_name,
        pe1.scheduled_date,
        pe1.module_name,
        pe1.start_time::TEXT || '-' || pe1.end_time::TIME::TEXT,
        pe2.module_name,
        pe2.start_time::TEXT || '-' || pe2.end_time::TIME::TEXT
    FROM professor_exams pe1
    JOIN professor_exams pe2 ON 
        pe1.prof_id = pe2.prof_id
        AND pe1.scheduled_date = pe2.scheduled_date
        AND pe1.exam_id < pe2.exam_id  -- Avoid duplicate pairs
        -- Time overlap condition: exam1 starts before exam2 ends AND exam2 starts before exam1 ends
        AND pe1.start_time < pe2.end_time
        AND pe2.start_time < pe1.end_time
    ORDER BY pe1.scheduled_date, pe1.prof_name, pe1.start_time;
END;
$$ LANGUAGE plpgsql;

-- ----------------------------------------------------------------------------
-- FUNCTION: Detect room conflicts
-- A room cannot host more than one exam at the same time
-- Also checks if room capacity is exceeded
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION detect_room_conflicts(p_session_id UUID)
RETURNS TABLE (
    room_id UUID,
    room_name TEXT,
    building TEXT,
    conflict_date DATE,
    exam1_name TEXT,
    exam1_time TEXT,
    exam2_name TEXT,
    exam2_time TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH room_exams AS (
        SELECT 
            r.id AS room_id,
            r.name AS room_name,
            r.building,
            e.id AS exam_id,
            m.name AS module_name,
            e.scheduled_date,
            e.start_time,
            e.start_time + (e.duration_minutes || ' minutes')::INTERVAL AS end_time
        FROM exam_rooms r
        JOIN exams e ON r.id = e.room_id
        JOIN modules m ON e.module_id = m.id
        WHERE 
            e.session_id = p_session_id
            AND e.status = 'scheduled'
    )
    SELECT 
        re1.room_id,
        re1.room_name,
        re1.building,
        re1.scheduled_date,
        re1.module_name,
        re1.start_time::TEXT || '-' || re1.end_time::TIME::TEXT,
        re2.module_name,
        re2.start_time::TEXT || '-' || re2.end_time::TIME::TEXT
    FROM room_exams re1
    JOIN room_exams re2 ON 
        re1.room_id = re2.room_id
        AND re1.scheduled_date = re2.scheduled_date
        AND re1.exam_id < re2.exam_id
        AND re1.start_time < re2.end_time
        AND re2.start_time < re1.end_time
    ORDER BY re1.scheduled_date, re1.room_name, re1.start_time;
END;
$$ LANGUAGE plpgsql;

-- ----------------------------------------------------------------------------
-- FUNCTION: Detect room capacity violations
-- Room cannot have more students than its exam capacity
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION detect_capacity_violations(p_session_id UUID)
RETURNS TABLE (
    exam_id UUID,
    module_name TEXT,
    room_name TEXT,
    expected_students INTEGER,
    room_capacity INTEGER,
    overflow INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.id,
        m.name,
        r.name,
        e.expected_students,
        r.exam_capacity,
        e.expected_students - r.exam_capacity
    FROM exams e
    JOIN modules m ON e.module_id = m.id
    JOIN exam_rooms r ON e.room_id = r.id
    WHERE 
        e.session_id = p_session_id
        AND e.status = 'scheduled'
        AND e.expected_students > r.exam_capacity
    ORDER BY (e.expected_students - r.exam_capacity) DESC;
END;
$$ LANGUAGE plpgsql;

-- ----------------------------------------------------------------------------
-- FUNCTION: Get all conflicts summary
-- Returns a complete summary of all conflicts in a session
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION get_conflicts_summary(p_session_id UUID)
RETURNS TABLE (
    conflict_type TEXT,
    conflict_count BIGINT,
    severity TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 'Student - Multiple exams same day'::TEXT, 
           COUNT(*)::BIGINT,
           CASE WHEN COUNT(*) > 0 THEN 'HIGH' ELSE 'OK' END::TEXT
    FROM detect_student_conflicts(p_session_id)
    
    UNION ALL
    
    SELECT 'Professor - Too many exams per day'::TEXT, 
           COUNT(*)::BIGINT,
           CASE WHEN COUNT(*) > 0 THEN 'MEDIUM' ELSE 'OK' END::TEXT
    FROM detect_professor_conflicts(p_session_id)
    
    UNION ALL
    
    SELECT 'Professor - Time overlap'::TEXT, 
           COUNT(*)::BIGINT,
           CASE WHEN COUNT(*) > 0 THEN 'HIGH' ELSE 'OK' END::TEXT
    FROM detect_professor_time_overlaps(p_session_id)
    
    UNION ALL
    
    SELECT 'Room - Double booking'::TEXT, 
           COUNT(*)::BIGINT,
           CASE WHEN COUNT(*) > 0 THEN 'HIGH' ELSE 'OK' END::TEXT
    FROM detect_room_conflicts(p_session_id)
    
    UNION ALL
    
    SELECT 'Room - Capacity exceeded'::TEXT, 
           COUNT(*)::BIGINT,
           CASE WHEN COUNT(*) > 0 THEN 'MEDIUM' ELSE 'OK' END::TEXT
    FROM detect_capacity_violations(p_session_id);
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- SCHEDULING OPTIMIZATION PROCEDURES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- FUNCTION: Get available time slots for an exam
-- Returns all possible (date, time, room) combinations where an exam could be scheduled
-- without causing any conflicts
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION get_available_slots(
    p_session_id UUID,
    p_module_id UUID,
    p_duration_minutes INTEGER DEFAULT 120
)
RETURNS TABLE (
    slot_date DATE,
    slot_time TIME,
    room_id UUID,
    room_name TEXT,
    room_capacity INTEGER,
    score INTEGER  -- Higher score = better slot
) AS $$
DECLARE
    v_expected_students INTEGER;
    v_start_date DATE;
    v_end_date DATE;
    v_requires_computer BOOLEAN;
    v_requires_lab BOOLEAN;
BEGIN
    -- Get exam requirements
    SELECT 
        (SELECT COUNT(*) FROM enrollments enr WHERE enr.module_id = p_module_id AND enr.status = 'enrolled'),
        m.requires_computer,
        m.requires_lab
    INTO v_expected_students, v_requires_computer, v_requires_lab
    FROM modules m
    WHERE m.id = p_module_id;
    
    -- Get session date range
    SELECT start_date, end_date INTO v_start_date, v_end_date
    FROM exam_sessions WHERE id = p_session_id;
    
    -- Generate all possible slots
    RETURN QUERY
    WITH 
    -- Generate all dates in the session
    all_dates AS (
        SELECT generate_series(v_start_date, v_end_date, '1 day'::INTERVAL)::DATE AS exam_date
    ),
    -- Standard exam time slots (8:00, 10:30, 14:00, 16:30)
    time_slots AS (
        SELECT unnest(ARRAY['08:00', '10:30', '14:00', '16:30']::TIME[]) AS exam_time
    ),
    -- All possible date/time combinations
    all_slots AS (
        SELECT d.exam_date, t.exam_time
        FROM all_dates d
        CROSS JOIN time_slots t
        -- Exclude weekends
        WHERE EXTRACT(DOW FROM d.exam_date) NOT IN (0, 6)
    ),
    -- Rooms that meet the requirements
    suitable_rooms AS (
        SELECT r.id, r.name, r.exam_capacity
        FROM exam_rooms r
        WHERE 
            r.is_active = true
            AND r.is_available = true
            AND r.exam_capacity >= v_expected_students
            AND (NOT v_requires_computer OR r.has_computers = true)
            AND (NOT v_requires_lab OR r.room_type = 'lab')
    ),
    -- Existing exams (to check for conflicts)
    existing_exams AS (
        SELECT 
            e.scheduled_date,
            e.start_time,
            e.start_time + (e.duration_minutes || ' minutes')::INTERVAL AS end_time,
            e.room_id
        FROM exams e
        WHERE e.session_id = p_session_id AND e.status = 'scheduled'
    ),
    -- Rooms occupied at each slot
    occupied_rooms AS (
        SELECT DISTINCT ee.scheduled_date, ts.exam_time, ee.room_id
        FROM existing_exams ee
        CROSS JOIN time_slots ts
        WHERE 
            ts.exam_time < ee.end_time
            AND (ts.exam_time + (p_duration_minutes || ' minutes')::INTERVAL) > ee.start_time
    ),
    -- Students taking this module and their exam days
    student_exam_days AS (
        SELECT DISTINCT enr.student_id, e.scheduled_date
        FROM enrollments enr
        JOIN enrollments enr2 ON enr.student_id = enr2.student_id
        JOIN modules m ON enr2.module_id = m.id
        JOIN exams e ON m.id = e.module_id
        WHERE 
            enr.module_id = p_module_id
            AND e.session_id = p_session_id
            AND e.status = 'scheduled'
    ),
    -- Days where students already have exams
    blocked_days AS (
        SELECT DISTINCT scheduled_date FROM student_exam_days
    )
    -- Final available slots
    SELECT 
        s.exam_date,
        s.exam_time,
        r.id,
        r.name,
        r.exam_capacity,
        -- Scoring: prefer morning slots, smaller rooms (less waste), early dates
        (CASE WHEN s.exam_time = '08:00' THEN 10 
              WHEN s.exam_time = '10:30' THEN 8
              WHEN s.exam_time = '14:00' THEN 6
              ELSE 4 END) +
        (10 - LEAST(10, r.exam_capacity - v_expected_students)) +  -- Prefer right-sized rooms
        (v_end_date - s.exam_date)::INTEGER / 2  -- Slight preference for earlier dates
        AS score
    FROM all_slots s
    CROSS JOIN suitable_rooms r
    -- Room must not be occupied
    LEFT JOIN occupied_rooms occ ON 
        s.exam_date = occ.scheduled_date 
        AND s.exam_time = occ.exam_time 
        AND r.id = occ.room_id
    -- Day must not have student conflicts
    LEFT JOIN blocked_days bd ON s.exam_date = bd.scheduled_date
    WHERE 
        occ.room_id IS NULL  -- Room is free
        AND bd.scheduled_date IS NULL  -- No student has exam that day
    ORDER BY score DESC, s.exam_date, s.exam_time;
END;
$$ LANGUAGE plpgsql;

-- ----------------------------------------------------------------------------
-- FUNCTION: Auto-schedule a single exam
-- Automatically assigns the best available slot to an exam
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION auto_schedule_exam(
    p_exam_id UUID
)
RETURNS TABLE (
    success BOOLEAN,
    message TEXT,
    scheduled_date DATE,
    scheduled_time TIME,
    room_name TEXT
) AS $$
DECLARE
    v_module_id UUID;
    v_session_id UUID;
    v_duration INTEGER;
    v_slot RECORD;
BEGIN
    -- Get exam details
    SELECT module_id, session_id, duration_minutes 
    INTO v_module_id, v_session_id, v_duration
    FROM exams WHERE id = p_exam_id;
    
    IF NOT FOUND THEN
        RETURN QUERY SELECT false, 'Exam not found'::TEXT, NULL::DATE, NULL::TIME, NULL::TEXT;
        RETURN;
    END IF;
    
    -- Get the best available slot
    SELECT * INTO v_slot
    FROM get_available_slots(v_session_id, v_module_id, v_duration)
    LIMIT 1;
    
    IF NOT FOUND THEN
        RETURN QUERY SELECT false, 'No available slots found'::TEXT, NULL::DATE, NULL::TIME, NULL::TEXT;
        RETURN;
    END IF;
    
    -- Update the exam with the selected slot
    UPDATE exams
    SET 
        scheduled_date = v_slot.slot_date,
        start_time = v_slot.slot_time,
        room_id = v_slot.room_id,
        status = 'scheduled',
        expected_students = (
            SELECT COUNT(*) FROM enrollments 
            WHERE module_id = v_module_id AND status = 'enrolled'
        )
    WHERE id = p_exam_id;
    
    RETURN QUERY SELECT 
        true, 
        'Exam scheduled successfully'::TEXT, 
        v_slot.slot_date,
        v_slot.slot_time,
        v_slot.room_name;
END;
$$ LANGUAGE plpgsql;

-- ----------------------------------------------------------------------------
-- FUNCTION: Auto-schedule all pending exams in a session
-- Uses a greedy algorithm: schedules exams with most students first
-- (they have the most constraints)
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION auto_schedule_session(p_session_id UUID)
RETURNS TABLE (
    total_exams INTEGER,
    scheduled_count INTEGER,
    failed_count INTEGER,
    execution_time_ms INTEGER
) AS $$
DECLARE
    v_start_time TIMESTAMPTZ;
    v_exam RECORD;
    v_total INTEGER := 0;
    v_scheduled INTEGER := 0;
    v_failed INTEGER := 0;
    v_result RECORD;
BEGIN
    v_start_time := clock_timestamp();
    
    -- Process exams in order of student count (most constrained first)
    -- This greedy approach helps avoid getting stuck
    FOR v_exam IN
        SELECT e.id, m.name,
               (SELECT COUNT(*) FROM enrollments enr 
                WHERE enr.module_id = e.module_id AND enr.status = 'enrolled') as student_count
        FROM exams e
        JOIN modules m ON e.module_id = m.id
        WHERE e.session_id = p_session_id AND e.status = 'pending'
        ORDER BY student_count DESC
    LOOP
        v_total := v_total + 1;
        
        -- Try to schedule this exam
        SELECT * INTO v_result FROM auto_schedule_exam(v_exam.id);
        
        IF v_result.success THEN
            v_scheduled := v_scheduled + 1;
        ELSE
            v_failed := v_failed + 1;
            -- Log the failure
            RAISE NOTICE 'Failed to schedule exam %: %', v_exam.name, v_result.message;
        END IF;
    END LOOP;
    
    RETURN QUERY SELECT 
        v_total,
        v_scheduled,
        v_failed,
        (EXTRACT(EPOCH FROM (clock_timestamp() - v_start_time)) * 1000)::INTEGER;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- SUPERVISOR ASSIGNMENT PROCEDURES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- FUNCTION: Assign supervisors to exams
-- Ensures fair distribution and priority for department exams
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION assign_supervisors(p_session_id UUID)
RETURNS TABLE (
    assignments_made INTEGER,
    professors_used INTEGER,
    avg_supervisions DECIMAL
) AS $$
DECLARE
    v_exam RECORD;
    v_professor RECORD;
    v_assignments INTEGER := 0;
    v_professors_used INTEGER := 0;
BEGIN
    -- For each scheduled exam that needs supervisors
    FOR v_exam IN
        SELECT 
            e.id AS exam_id,
            e.scheduled_date,
            e.start_time,
            e.duration_minutes,
            d.id AS dept_id,
            r.exam_capacity,
            -- Calculate number of supervisors needed (1 per 30 students)
            GREATEST(1, CEIL(e.expected_students / 30.0)::INTEGER) AS supervisors_needed
        FROM exams e
        JOIN modules m ON e.module_id = m.id
        JOIN formations f ON m.formation_id = f.id
        JOIN departments d ON f.department_id = d.id
        LEFT JOIN exam_rooms r ON e.room_id = r.id
        WHERE 
            e.session_id = p_session_id
            AND e.status = 'scheduled'
            AND NOT EXISTS (
                SELECT 1 FROM exam_supervisors es WHERE es.exam_id = e.id
            )
        ORDER BY e.scheduled_date, e.start_time
    LOOP
        -- Find available professors, prioritizing:
        -- 1. Same department (is_department_exam = true)
        -- 2. Lowest current supervision count (fair distribution)
        -- 3. Not exceeding daily limit
        FOR v_professor IN
            SELECT 
                p.id AS prof_id,
                p.department_id = v_exam.dept_id AS is_dept_exam,
                p.supervision_count,
                -- Count exams already supervising that day
                (SELECT COUNT(*) FROM exam_supervisors es
                 JOIN exams e ON es.exam_id = e.id
                 WHERE es.professor_id = p.id 
                   AND e.scheduled_date = v_exam.scheduled_date) AS exams_that_day
            FROM professors p
            WHERE 
                p.is_active = true
                -- Not already supervising at this time
                AND NOT EXISTS (
                    SELECT 1 FROM exam_supervisors es
                    JOIN exams e ON es.exam_id = e.id
                    WHERE es.professor_id = p.id
                      AND e.scheduled_date = v_exam.scheduled_date
                      AND e.start_time < (v_exam.start_time + (v_exam.duration_minutes || ' minutes')::INTERVAL)
                      AND (e.start_time + (e.duration_minutes || ' minutes')::INTERVAL) > v_exam.start_time
                )
            -- Apply daily limit
            HAVING (SELECT COUNT(*) FROM exam_supervisors es
                    JOIN exams e ON es.exam_id = e.id
                    WHERE es.professor_id = p.id 
                      AND e.scheduled_date = v_exam.scheduled_date) < p.max_exams_per_day
            ORDER BY 
                p.department_id = v_exam.dept_id DESC,  -- Same dept first
                p.supervision_count ASC  -- Fewest supervisions first
            LIMIT v_exam.supervisors_needed
        LOOP
            -- Create the assignment
            INSERT INTO exam_supervisors (exam_id, professor_id, role, is_department_exam)
            VALUES (
                v_exam.exam_id,
                v_professor.prof_id,
                CASE WHEN v_assignments = 0 THEN 'responsible' ELSE 'supervisor' END,
                v_professor.is_dept_exam
            );
            
            v_assignments := v_assignments + 1;
        END LOOP;
    END LOOP;
    
    -- Calculate statistics
    SELECT 
        COUNT(DISTINCT professor_id),
        ROUND(AVG(supervision_count), 2)
    INTO v_professors_used, avg_supervisions
    FROM professors
    WHERE supervision_count > 0;
    
    RETURN QUERY SELECT v_assignments, COALESCE(v_professors_used, 0), COALESCE(avg_supervisions, 0.0);
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- STATISTICS AND KPI PROCEDURES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- FUNCTION: Get session statistics
-- Returns KPIs for a specific exam session
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION get_session_stats(p_session_id UUID)
RETURNS TABLE (
    total_exams INTEGER,
    scheduled_exams INTEGER,
    pending_exams INTEGER,
    total_rooms_used INTEGER,
    total_professors_assigned INTEGER,
    avg_room_utilization DECIMAL,
    conflict_count INTEGER,
    departments_covered INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        (SELECT COUNT(*)::INTEGER FROM exams WHERE session_id = p_session_id),
        (SELECT COUNT(*)::INTEGER FROM exams WHERE session_id = p_session_id AND status = 'scheduled'),
        (SELECT COUNT(*)::INTEGER FROM exams WHERE session_id = p_session_id AND status = 'pending'),
        (SELECT COUNT(DISTINCT room_id)::INTEGER FROM exams WHERE session_id = p_session_id AND status = 'scheduled'),
        (SELECT COUNT(DISTINCT es.professor_id)::INTEGER 
         FROM exam_supervisors es 
         JOIN exams e ON es.exam_id = e.id 
         WHERE e.session_id = p_session_id),
        (SELECT ROUND(AVG(e.expected_students::DECIMAL / NULLIF(r.exam_capacity, 0) * 100), 2)
         FROM exams e 
         JOIN exam_rooms r ON e.room_id = r.id 
         WHERE e.session_id = p_session_id AND e.status = 'scheduled'),
        (SELECT COALESCE(SUM(conflict_count), 0)::INTEGER FROM get_conflicts_summary(p_session_id)),
        (SELECT COUNT(DISTINCT d.id)::INTEGER 
         FROM exams e
         JOIN modules m ON e.module_id = m.id
         JOIN formations f ON m.formation_id = f.id
         JOIN departments d ON f.department_id = d.id
         WHERE e.session_id = p_session_id);
END;
$$ LANGUAGE plpgsql;

-- ----------------------------------------------------------------------------
-- FUNCTION: Get department-level statistics
-- Returns stats for a specific department in a session
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION get_department_stats(
    p_session_id UUID,
    p_department_id UUID
)
RETURNS TABLE (
    department_name TEXT,
    total_exams INTEGER,
    scheduled_exams INTEGER,
    total_students INTEGER,
    professors_supervising INTEGER,
    student_conflicts INTEGER,
    formations_count INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        d.name,
        (SELECT COUNT(*)::INTEGER 
         FROM exams e
         JOIN modules m ON e.module_id = m.id
         JOIN formations f ON m.formation_id = f.id
         WHERE e.session_id = p_session_id AND f.department_id = p_department_id),
        (SELECT COUNT(*)::INTEGER 
         FROM exams e
         JOIN modules m ON e.module_id = m.id
         JOIN formations f ON m.formation_id = f.id
         WHERE e.session_id = p_session_id AND f.department_id = p_department_id AND e.status = 'scheduled'),
        (SELECT COUNT(DISTINCT s.id)::INTEGER
         FROM students s
         JOIN formations f ON s.formation_id = f.id
         WHERE f.department_id = p_department_id AND s.is_active = true),
        (SELECT COUNT(DISTINCT es.professor_id)::INTEGER
         FROM exam_supervisors es
         JOIN exams e ON es.exam_id = e.id
         JOIN modules m ON e.module_id = m.id
         JOIN formations f ON m.formation_id = f.id
         WHERE e.session_id = p_session_id AND f.department_id = p_department_id),
        (SELECT COUNT(*)::INTEGER FROM detect_student_conflicts(p_session_id) sc
         WHERE sc.student_id IN (
             SELECT s.id FROM students s
             JOIN formations f ON s.formation_id = f.id
             WHERE f.department_id = p_department_id
         )),
        (SELECT COUNT(DISTINCT f.id)::INTEGER
         FROM formations f
         WHERE f.department_id = p_department_id AND f.is_active = true)
    FROM departments d
    WHERE d.id = p_department_id;
END;
$$ LANGUAGE plpgsql;

-- ----------------------------------------------------------------------------
-- FUNCTION: Get professor workload statistics
-- For ensuring fair distribution of supervisions
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION get_professor_workload_stats(p_session_id UUID)
RETURNS TABLE (
    professor_id UUID,
    professor_name TEXT,
    department_name TEXT,
    supervision_count INTEGER,
    dept_exams_count INTEGER,
    other_exams_count INTEGER,
    deviation_from_mean DECIMAL
) AS $$
DECLARE
    v_mean DECIMAL;
BEGIN
    -- Calculate mean supervisions
    SELECT AVG(supervision_count) INTO v_mean
    FROM professors WHERE is_active = true;
    
    RETURN QUERY
    SELECT 
        p.id,
        p.first_name || ' ' || p.last_name,
        d.name,
        p.supervision_count,
        (SELECT COUNT(*)::INTEGER FROM exam_supervisors es
         JOIN exams e ON es.exam_id = e.id
         WHERE es.professor_id = p.id 
           AND e.session_id = p_session_id 
           AND es.is_department_exam = true),
        (SELECT COUNT(*)::INTEGER FROM exam_supervisors es
         JOIN exams e ON es.exam_id = e.id
         WHERE es.professor_id = p.id 
           AND e.session_id = p_session_id 
           AND es.is_department_exam = false),
        ROUND(p.supervision_count - v_mean, 2)
    FROM professors p
    JOIN departments d ON p.department_id = d.id
    WHERE p.is_active = true
    ORDER BY p.supervision_count DESC;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- UTILITY PROCEDURES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- FUNCTION: Reset and prepare a new exam session
-- Creates exam entries for all modules in active formations
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION prepare_exam_session(
    p_session_id UUID
)
RETURNS INTEGER AS $$
DECLARE
    v_count INTEGER := 0;
BEGIN
    -- Create an exam entry for each active module
    INSERT INTO exams (module_id, session_id, duration_minutes, requires_computer, requires_lab, expected_students)
    SELECT 
        m.id,
        p_session_id,
        m.exam_duration_minutes,
        m.requires_computer,
        m.requires_lab,
        (SELECT COUNT(*) FROM enrollments enr WHERE enr.module_id = m.id AND enr.status = 'enrolled')
    FROM modules m
    JOIN formations f ON m.formation_id = f.id
    WHERE 
        m.is_active = true 
        AND f.is_active = true
        -- Don't create duplicate exams
        AND NOT EXISTS (
            SELECT 1 FROM exams e WHERE e.module_id = m.id AND e.session_id = p_session_id
        );
    
    GET DIAGNOSTICS v_count = ROW_COUNT;
    RETURN v_count;
END;
$$ LANGUAGE plpgsql;

-- ----------------------------------------------------------------------------
-- FUNCTION: Clear schedule for a session (for re-scheduling)
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION clear_session_schedule(p_session_id UUID)
RETURNS INTEGER AS $$
DECLARE
    v_count INTEGER;
BEGIN
    -- Remove supervisor assignments
    DELETE FROM exam_supervisors
    WHERE exam_id IN (SELECT id FROM exams WHERE session_id = p_session_id);
    
    -- Reset exam schedules
    UPDATE exams
    SET 
        scheduled_date = NULL,
        start_time = NULL,
        room_id = NULL,
        status = 'pending'
    WHERE session_id = p_session_id;
    
    GET DIAGNOSTICS v_count = ROW_COUNT;
    RETURN v_count;
END;
$$ LANGUAGE plpgsql;
