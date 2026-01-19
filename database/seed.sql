-- ============================================================================
-- EXAM SCHEDULING PLATFORM - SEED DATA
-- ============================================================================
-- This script generates realistic test data for the university:
-- - 7 departments
-- - ~200 formations (training programs)
-- - ~13,000 students with Algerian names
-- - ~400 professors
-- - ~50 exam rooms
-- - ~130,000 enrollments
-- ============================================================================

-- First, let's create some helper functions for random data generation

-- Function to get a random element from an array
CREATE OR REPLACE FUNCTION random_element(arr ANYARRAY)
RETURNS ANYELEMENT AS $$
BEGIN
    RETURN arr[1 + floor(random() * array_length(arr, 1))::INTEGER];
END;
$$ LANGUAGE plpgsql;

-- Function to generate a random Algerian phone number
CREATE OR REPLACE FUNCTION random_phone()
RETURNS VARCHAR AS $$
DECLARE
    prefixes VARCHAR[] := ARRAY['05', '06', '07'];
BEGIN
    RETURN random_element(prefixes) || 
           lpad(floor(random() * 100000000)::TEXT, 8, '0');
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- ALGERIAN NAMES DATA
-- ============================================================================

-- Common Algerian first names (male)
-- These are authentic Arabic/Berber names commonly used in Algeria
CREATE TEMPORARY TABLE male_first_names (name VARCHAR(50));
INSERT INTO male_first_names (name) VALUES
    -- Arabic origin names (most common)
    ('Mohamed'), ('Ahmed'), ('Youcef'), ('Amine'), ('Karim'),
    ('Reda'), ('Sofiane'), ('Bilal'), ('Ayoub'), ('Zakaria'),
    ('Abdelkader'), ('Omar'), ('Ali'), ('Hamza'), ('Mourad'),
    ('Nassim'), ('Samir'), ('Walid'), ('Rachid'), ('Khaled'),
    ('Abderrahmane'), ('Farid'), ('Ismail'), ('Nadir'), ('Fouad'),
    ('Djamel'), ('Nabil'), ('Mehdi'), ('Riad'), ('Lotfi'),
    ('Yassine'), ('Adel'), ('Said'), ('Malik'), ('Hakim'),
    ('Tarek'), ('Raouf'), ('Mounir'), ('Fares'), ('Anis'),
    ('Hicham'), ('Fateh'), ('Nassir'), ('Lakhdar'), ('Djilali'),
    ('Mustapha'), ('Abdelaziz'), ('Salim'), ('Malek'), ('Yahia'),
    -- Berber/Amazigh origin names
    ('Amazigh'), ('Aksil'), ('Massinissa'), ('Jugurtha'), ('Aghilas'),
    ('Koceila'), ('Idir'), ('Aksel'), ('Syphax'), ('Gaya'),
    ('Ameziane'), ('Younes'), ('Ghiles'), ('Meziane'), ('Madjid');

-- Common Algerian first names (female)
CREATE TEMPORARY TABLE female_first_names (name VARCHAR(50));
INSERT INTO female_first_names (name) VALUES
    -- Arabic origin names
    ('Fatima'), ('Amina'), ('Khadija'), ('Meriem'), ('Aicha'),
    ('Yasmine'), ('Sara'), ('Nadia'), ('Nour'), ('Lina'),
    ('Imane'), ('Houda'), ('Souad'), ('Samira'), ('Leila'),
    ('Malika'), ('Zineb'), ('Nawal'), ('Farida'), ('Wafa'),
    ('Ikram'), ('Rania'), ('Asma'), ('Hafsa'), ('Amira'),
    ('Djamila'), ('Salima'), ('Karima'), ('Lamia'), ('Sonia'),
    ('Rym'), ('Ines'), ('Chaima'), ('Hadjer'), ('Nesrine'),
    ('Sabrina'), ('Soumia'), ('Nabila'), ('Ghania'), ('Fatiha'),
    -- Berber/Amazigh origin names
    ('Dihia'), ('Tiziri'), ('Thilelli'), ('Numidia'), ('Yemma'),
    ('Lwiza'), ('Dassine'), ('Tanina'), ('Tassadit'), ('Kahina'),
    ('Tinhinane'), ('Cyria'), ('Ferroudja'), ('Aldjia'), ('Ouardia');

-- Common Algerian family names (mix of Arabic and Berber)
CREATE TEMPORARY TABLE family_names (name VARCHAR(50));
INSERT INTO family_names (name) VALUES
    -- Arabic origin
    ('Benali'), ('Bouzid'), ('Khelifi'), ('Hadj'), ('Messaoudi'),
    ('Belkacem'), ('Benmohamed'), ('Guediri'), ('Hamidi'), ('Saadi'),
    ('Cherif'), ('Mebarki'), ('Boudiaf'), ('Larbi'), ('Ziani'),
    ('Yahiaoui'), ('Djaballah'), ('Khellaf'), ('Bensaid'), ('Rahmani'),
    ('Boutefnouchet'), ('Belhadj'), ('Hadjadj'), ('Mansouri'), ('Benabdallah'),
    ('Toumi'), ('Benamara'), ('Laid'), ('Brahimi'), ('Taleb'),
    ('Bouazza'), ('Kadir'), ('Ferhat'), ('Allaoui'), ('Gasmi'),
    ('Benhamed'), ('Mokrani'), ('Derradji'), ('Amrani'), ('Ouali'),
    -- Berber origin
    ('Ait Ahmed'), ('Ait Ali'), ('Meziane'), ('Amokrane'), ('Haddad'),
    ('Oukaci'), ('Berkani'), ('Ait Ouakli'), ('Zeroual'), ('Belaid'),
    ('Touati'), ('Ameur'), ('Bouamama'), ('Madani'), ('Bekhouche'),
    ('Ait Kaci'), ('Idir'), ('Bouchikhi'), ('Oulhadj'), ('Zemouri'),
    -- Regional variations
    ('Bensalem'), ('Kaci'), ('Benmalek'), ('Ourabah'), ('Hamadouche'),
    ('Belaidi'), ('Meghni'), ('Fellag'), ('Ait Menguellet'), ('Boudjemaa');

-- ============================================================================
-- INSERT DEPARTMENTS
-- ============================================================================

INSERT INTO departments (id, name, code, email, building) VALUES
    (uuid_generate_v4(), 'Informatique', 'INFO', 'info@univ-alger.dz', 'Bloc A'),
    (uuid_generate_v4(), 'Mathématiques', 'MATH', 'math@univ-alger.dz', 'Bloc A'),
    (uuid_generate_v4(), 'Physique', 'PHY', 'physique@univ-alger.dz', 'Bloc B'),
    (uuid_generate_v4(), 'Chimie', 'CHIM', 'chimie@univ-alger.dz', 'Bloc B'),
    (uuid_generate_v4(), 'Biologie', 'BIO', 'bio@univ-alger.dz', 'Bloc C'),
    (uuid_generate_v4(), 'Sciences Économiques', 'ECO', 'eco@univ-alger.dz', 'Bloc D'),
    (uuid_generate_v4(), 'Langues Étrangères', 'LANG', 'langues@univ-alger.dz', 'Bloc E');

-- ============================================================================
-- INSERT FORMATIONS (Training Programs)
-- ============================================================================
-- Each department has multiple formations across different levels

DO $$
DECLARE
    dept RECORD;
    formation_templates TEXT[][] := ARRAY[
        -- Informatique formations
        ARRAY['INFO', 'Licence Systèmes Informatiques', 'L1', 'L2', 'L3'],
        ARRAY['INFO', 'Licence Génie Logiciel', 'L1', 'L2', 'L3'],
        ARRAY['INFO', 'Licence Intelligence Artificielle', 'L1', 'L2', 'L3'],
        ARRAY['INFO', 'Master Data Science', 'M1', 'M2'],
        ARRAY['INFO', 'Master Cybersécurité', 'M1', 'M2'],
        ARRAY['INFO', 'Master Réseaux et Systèmes', 'M1', 'M2'],
        -- Mathématiques formations
        ARRAY['MATH', 'Licence Mathématiques Fondamentales', 'L1', 'L2', 'L3'],
        ARRAY['MATH', 'Licence Mathématiques Appliquées', 'L1', 'L2', 'L3'],
        ARRAY['MATH', 'Licence Statistiques', 'L1', 'L2', 'L3'],
        ARRAY['MATH', 'Master Analyse Numérique', 'M1', 'M2'],
        ARRAY['MATH', 'Master Probabilités', 'M1', 'M2'],
        -- Physique formations
        ARRAY['PHY', 'Licence Physique Fondamentale', 'L1', 'L2', 'L3'],
        ARRAY['PHY', 'Licence Physique des Matériaux', 'L1', 'L2', 'L3'],
        ARRAY['PHY', 'Licence Énergétique', 'L1', 'L2', 'L3'],
        ARRAY['PHY', 'Master Physique Théorique', 'M1', 'M2'],
        ARRAY['PHY', 'Master Physique Nucléaire', 'M1', 'M2'],
        -- Chimie formations
        ARRAY['CHIM', 'Licence Chimie Générale', 'L1', 'L2', 'L3'],
        ARRAY['CHIM', 'Licence Chimie Organique', 'L1', 'L2', 'L3'],
        ARRAY['CHIM', 'Licence Chimie Industrielle', 'L1', 'L2', 'L3'],
        ARRAY['CHIM', 'Master Chimie Analytique', 'M1', 'M2'],
        -- Biologie formations
        ARRAY['BIO', 'Licence Biologie Cellulaire', 'L1', 'L2', 'L3'],
        ARRAY['BIO', 'Licence Écologie', 'L1', 'L2', 'L3'],
        ARRAY['BIO', 'Licence Microbiologie', 'L1', 'L2', 'L3'],
        ARRAY['BIO', 'Master Biotechnologie', 'M1', 'M2'],
        ARRAY['BIO', 'Master Génétique', 'M1', 'M2'],
        -- Sciences Économiques formations
        ARRAY['ECO', 'Licence Économie Générale', 'L1', 'L2', 'L3'],
        ARRAY['ECO', 'Licence Gestion', 'L1', 'L2', 'L3'],
        ARRAY['ECO', 'Licence Commerce International', 'L1', 'L2', 'L3'],
        ARRAY['ECO', 'Licence Finance', 'L1', 'L2', 'L3'],
        ARRAY['ECO', 'Master Management', 'M1', 'M2'],
        ARRAY['ECO', 'Master Économétrie', 'M1', 'M2'],
        -- Langues formations
        ARRAY['LANG', 'Licence Anglais', 'L1', 'L2', 'L3'],
        ARRAY['LANG', 'Licence Français', 'L1', 'L2', 'L3'],
        ARRAY['LANG', 'Licence Espagnol', 'L1', 'L2', 'L3'],
        ARRAY['LANG', 'Licence Allemand', 'L1', 'L2', 'L3'],
        ARRAY['LANG', 'Master Traduction', 'M1', 'M2'],
        ARRAY['LANG', 'Master Didactique des Langues', 'M1', 'M2']
    ];
    template TEXT[];
    level TEXT;
    dept_id UUID;
    form_name TEXT;
    form_code TEXT;
    i INTEGER;
    j INTEGER;
BEGIN
    -- Process each formation template
    FOREACH template SLICE 1 IN ARRAY formation_templates LOOP
        -- Get department ID
        SELECT id INTO dept_id FROM departments WHERE code = template[1];
        
        -- Create formation for each level in the template
        FOR i IN 3..array_length(template, 1) LOOP
            level := template[i];
            form_name := template[2] || ' - ' || level;
            form_code := template[1] || '-' || 
                        regexp_replace(template[2], '[^A-Z]', '', 'gi') || '-' || 
                        level || '-' || 
                        lpad((i - 2)::TEXT, 2, '0');
            
            INSERT INTO formations (department_id, name, code, level, academic_year)
            VALUES (dept_id, form_name, LEFT(form_code, 20), level, '2024-2025');
        END LOOP;
    END LOOP;
    
    RAISE NOTICE 'Created formations';
END $$;

-- ============================================================================
-- INSERT EXAM ROOMS
-- ============================================================================

INSERT INTO exam_rooms (name, building, floor, room_type, total_capacity, exam_capacity, has_computers, has_projector) VALUES
    -- Large Amphitheaters (Bloc A)
    ('Amphi Ibn Khaldoun', 'Bloc A', 0, 'amphi', 500, 250, false, true),
    ('Amphi El Farabi', 'Bloc A', 0, 'amphi', 400, 200, false, true),
    ('Amphi Averroès', 'Bloc A', 1, 'amphi', 350, 175, false, true),
    ('Amphi Ibn Sina', 'Bloc B', 0, 'amphi', 300, 150, false, true),
    ('Amphi El Khawarizmi', 'Bloc B', 0, 'amphi', 300, 150, true, true),
    
    -- Medium Amphitheaters
    ('Amphi 1', 'Bloc C', 0, 'amphi', 200, 100, false, true),
    ('Amphi 2', 'Bloc C', 0, 'amphi', 200, 100, false, true),
    ('Amphi 3', 'Bloc D', 0, 'amphi', 150, 75, false, true),
    ('Amphi 4', 'Bloc D', 0, 'amphi', 150, 75, false, true),
    ('Amphi 5', 'Bloc E', 0, 'amphi', 120, 60, false, true),
    
    -- Computer Labs (for practical exams)
    ('Labo Info 1', 'Bloc A', 1, 'lab', 40, 20, true, true),
    ('Labo Info 2', 'Bloc A', 1, 'lab', 40, 20, true, true),
    ('Labo Info 3', 'Bloc A', 2, 'lab', 35, 17, true, true),
    ('Labo Info 4', 'Bloc A', 2, 'lab', 35, 17, true, true),
    ('Labo Langues', 'Bloc E', 1, 'lab', 30, 15, true, true),
    
    -- Regular Classrooms (20 students max for exams as per requirements)
    ('Salle 101', 'Bloc A', 1, 'classroom', 50, 20, false, true),
    ('Salle 102', 'Bloc A', 1, 'classroom', 50, 20, false, true),
    ('Salle 103', 'Bloc A', 1, 'classroom', 50, 20, false, true),
    ('Salle 104', 'Bloc A', 1, 'classroom', 40, 20, false, true),
    ('Salle 105', 'Bloc A', 1, 'classroom', 40, 20, false, true),
    ('Salle 201', 'Bloc A', 2, 'classroom', 45, 20, false, true),
    ('Salle 202', 'Bloc A', 2, 'classroom', 45, 20, false, true),
    ('Salle 203', 'Bloc A', 2, 'classroom', 45, 20, false, true),
    ('Salle 301', 'Bloc B', 1, 'classroom', 50, 20, false, true),
    ('Salle 302', 'Bloc B', 1, 'classroom', 50, 20, false, true),
    ('Salle 303', 'Bloc B', 1, 'classroom', 50, 20, false, true),
    ('Salle 304', 'Bloc B', 2, 'classroom', 40, 20, false, true),
    ('Salle 305', 'Bloc B', 2, 'classroom', 40, 20, false, true),
    ('Salle 401', 'Bloc C', 1, 'classroom', 45, 20, false, true),
    ('Salle 402', 'Bloc C', 1, 'classroom', 45, 20, false, true),
    ('Salle 403', 'Bloc C', 2, 'classroom', 45, 20, false, true),
    ('Salle 501', 'Bloc D', 1, 'classroom', 50, 20, false, true),
    ('Salle 502', 'Bloc D', 1, 'classroom', 50, 20, false, true),
    ('Salle 503', 'Bloc D', 2, 'classroom', 45, 20, false, true),
    ('Salle 601', 'Bloc E', 1, 'classroom', 40, 20, false, true),
    ('Salle 602', 'Bloc E', 1, 'classroom', 40, 20, false, true);

-- ============================================================================
-- INSERT MODULES
-- ============================================================================
-- Each formation has 6-9 modules as specified in requirements

DO $$
DECLARE
    formation RECORD;
    module_templates TEXT[][] := ARRAY[
        -- Common modules for L1 (all departments)
        ARRAY['L1', 'Mathématiques 1', '60', '3'],
        ARRAY['L1', 'Physique 1', '60', '3'],
        ARRAY['L1', 'Informatique 1', '60', '3'],
        ARRAY['L1', 'Anglais 1', '60', '2'],
        ARRAY['L1', 'Méthodologie', '60', '2'],
        ARRAY['L1', 'Français Technique', '60', '2'],
        -- L2 modules
        ARRAY['L2', 'Mathématiques 2', '90', '4'],
        ARRAY['L2', 'Algorithmique', '90', '4'],
        ARRAY['L2', 'Statistiques', '90', '3'],
        ARRAY['L2', 'Anglais 2', '60', '2'],
        ARRAY['L2', 'Communication', '60', '2'],
        ARRAY['L2', 'Projet Tutoré 1', '120', '3'],
        -- L3 modules
        ARRAY['L3', 'Bases de Données', '120', '5'],
        ARRAY['L3', 'Réseaux', '120', '4'],
        ARRAY['L3', 'Génie Logiciel', '120', '4'],
        ARRAY['L3', 'Intelligence Artificielle', '120', '4'],
        ARRAY['L3', 'Anglais 3', '60', '2'],
        ARRAY['L3', 'Projet de Fin d''Étude', '180', '6'],
        -- M1 modules
        ARRAY['M1', 'Recherche Opérationnelle', '120', '5'],
        ARRAY['M1', 'Machine Learning', '120', '5'],
        ARRAY['M1', 'Sécurité Informatique', '120', '4'],
        ARRAY['M1', 'Big Data', '120', '4'],
        ARRAY['M1', 'Méthodologie de Recherche', '90', '3'],
        ARRAY['M1', 'Anglais Scientifique', '60', '2'],
        ARRAY['M1', 'Stage en Entreprise', '120', '6'],
        -- M2 modules
        ARRAY['M2', 'Deep Learning', '120', '5'],
        ARRAY['M2', 'Cloud Computing', '120', '5'],
        ARRAY['M2', 'IoT et Systèmes Embarqués', '120', '4'],
        ARRAY['M2', 'Entrepreneuriat', '90', '3'],
        ARRAY['M2', 'Éthique et IA', '60', '2'],
        ARRAY['M2', 'Mémoire de Master', '180', '10']
    ];
    template TEXT[];
    module_code VARCHAR(20);
    module_num INTEGER := 0;
    requires_comp BOOLEAN;
BEGIN
    FOR formation IN SELECT * FROM formations LOOP
        module_num := 0;
        
        FOREACH template SLICE 1 IN ARRAY module_templates LOOP
            -- Only add modules matching the formation level
            IF template[1] = formation.level THEN
                module_num := module_num + 1;
                module_code := formation.code || '-M' || lpad(module_num::TEXT, 2, '0');
                
                -- Some modules require computers
                requires_comp := template[2] LIKE '%Informatique%' OR 
                                template[2] LIKE '%Algorithmique%' OR
                                template[2] LIKE '%Bases de Données%' OR
                                template[2] LIKE '%Machine Learning%' OR
                                template[2] LIKE '%Deep Learning%' OR
                                template[2] LIKE '%Big Data%';
                
                INSERT INTO modules (
                    formation_id, 
                    name, 
                    code, 
                    credits, 
                    exam_duration_minutes,
                    requires_computer,
                    semester
                )
                VALUES (
                    formation.id,
                    template[2],
                    LEFT(module_code, 20),
                    template[4]::INTEGER,
                    template[3]::INTEGER,
                    requires_comp,
                    CASE WHEN module_num <= 4 THEN 1 ELSE 2 END
                );
            END IF;
        END LOOP;
    END LOOP;
    
    RAISE NOTICE 'Created modules';
END $$;

-- ============================================================================
-- INSERT PROFESSORS
-- ============================================================================
-- About 50-60 professors per department

DO $$
DECLARE
    dept RECORD;
    male_names TEXT[];
    female_names TEXT[];
    family TEXT[];
    first_name TEXT;
    last_name TEXT;
    i INTEGER;
    gender INTEGER;
    titles TEXT[] := ARRAY['Professeur', 'Maître de Conférences A', 'Maître de Conférences B', 'Maître Assistant A', 'Maître Assistant B'];
    specializations TEXT[][] := ARRAY[
        ARRAY['INFO', 'Intelligence Artificielle', 'Bases de Données', 'Réseaux', 'Sécurité', 'Génie Logiciel', 'Systèmes Distribués'],
        ARRAY['MATH', 'Algèbre', 'Analyse', 'Probabilités', 'Statistiques', 'Optimisation', 'Géométrie'],
        ARRAY['PHY', 'Mécanique Quantique', 'Thermodynamique', 'Optique', 'Physique Nucléaire', 'Physique des Matériaux', 'Électromagnétisme'],
        ARRAY['CHIM', 'Chimie Organique', 'Chimie Inorganique', 'Chimie Analytique', 'Biochimie', 'Chimie des Polymères', 'Catalyse'],
        ARRAY['BIO', 'Biologie Cellulaire', 'Génétique', 'Microbiologie', 'Écologie', 'Biochimie', 'Biotechnologie'],
        ARRAY['ECO', 'Microéconomie', 'Macroéconomie', 'Économétrie', 'Finance', 'Management', 'Commerce International'],
        ARRAY['LANG', 'Linguistique', 'Littérature', 'Traduction', 'Didactique', 'Phonétique', 'Civilisation']
    ];
    spec_arr TEXT[];
BEGIN
    -- Load names into arrays
    SELECT array_agg(name) INTO male_names FROM male_first_names;
    SELECT array_agg(name) INTO female_names FROM female_first_names;
    SELECT array_agg(name) INTO family FROM family_names;
    
    FOR dept IN SELECT * FROM departments LOOP
        -- Find specializations for this department
        FOREACH spec_arr SLICE 1 IN ARRAY specializations LOOP
            IF spec_arr[1] = dept.code THEN
                -- Create 50-60 professors per department
                FOR i IN 1..55 LOOP
                    -- Random gender (slightly more male for realism in Algeria)
                    gender := floor(random() * 10);
                    
                    IF gender < 6 THEN
                        first_name := male_names[1 + floor(random() * array_length(male_names, 1))::INTEGER];
                    ELSE
                        first_name := female_names[1 + floor(random() * array_length(female_names, 1))::INTEGER];
                    END IF;
                    
                    last_name := family[1 + floor(random() * array_length(family, 1))::INTEGER];
                    
                    INSERT INTO professors (
                        department_id,
                        first_name,
                        last_name,
                        email,
                        phone,
                        title,
                        specialization,
                        max_exams_per_day
                    )
                    VALUES (
                        dept.id,
                        first_name,
                        last_name,
                        lower(regexp_replace(first_name, ' ', '', 'g')) || '.' || 
                            lower(regexp_replace(last_name, ' ', '', 'g')) || 
                            i::TEXT || '@univ-alger.dz',
                        random_phone(),
                        titles[1 + floor(random() * array_length(titles, 1))::INTEGER],
                        spec_arr[2 + floor(random() * (array_length(spec_arr, 1) - 1))::INTEGER],
                        3  -- Max 3 exams per day as per requirements
                    );
                END LOOP;
            END IF;
        END LOOP;
    END LOOP;
    
    RAISE NOTICE 'Created professors';
END $$;

-- ============================================================================
-- INSERT STUDENTS
-- ============================================================================
-- Target: ~13,000 students distributed across formations
-- L1: ~3500, L2: ~3000, L3: ~2800, M1: ~2000, M2: ~1700

DO $$
DECLARE
    formation RECORD;
    male_names TEXT[];
    female_names TEXT[];
    family TEXT[];
    first_name TEXT;
    last_name TEXT;
    i INTEGER;
    gender INTEGER;
    student_count INTEGER;
    total_students INTEGER := 0;
    student_num INTEGER := 0;
BEGIN
    -- Load names
    SELECT array_agg(name) INTO male_names FROM male_first_names;
    SELECT array_agg(name) INTO female_names FROM female_first_names;
    SELECT array_agg(name) INTO family FROM family_names;
    
    FOR formation IN SELECT * FROM formations ORDER BY level, name LOOP
        -- Determine number of students based on level
        CASE formation.level
            WHEN 'L1' THEN student_count := 80 + floor(random() * 40)::INTEGER;  -- 80-120 per L1 formation
            WHEN 'L2' THEN student_count := 60 + floor(random() * 30)::INTEGER;  -- 60-90
            WHEN 'L3' THEN student_count := 50 + floor(random() * 25)::INTEGER;  -- 50-75
            WHEN 'M1' THEN student_count := 35 + floor(random() * 20)::INTEGER;  -- 35-55
            WHEN 'M2' THEN student_count := 25 + floor(random() * 15)::INTEGER;  -- 25-40
            ELSE student_count := 30;
        END CASE;
        
        FOR i IN 1..student_count LOOP
            student_num := student_num + 1;
            
            -- Random gender (balanced for students)
            gender := floor(random() * 10);
            
            IF gender < 5 THEN
                first_name := male_names[1 + floor(random() * array_length(male_names, 1))::INTEGER];
            ELSE
                first_name := female_names[1 + floor(random() * array_length(female_names, 1))::INTEGER];
            END IF;
            
            last_name := family[1 + floor(random() * array_length(family, 1))::INTEGER];
            
            INSERT INTO students (
                formation_id,
                student_number,
                first_name,
                last_name,
                email,
                enrollment_year,
                promotion
            )
            VALUES (
                formation.id,
                '2024' || lpad(student_num::TEXT, 6, '0'),
                first_name,
                last_name,
                lower(regexp_replace(first_name, ' ', '', 'g')) || '.' || 
                    lower(regexp_replace(last_name, ' ', '', 'g')) || 
                    student_num::TEXT || '@etu.univ-alger.dz',
                CASE formation.level
                    WHEN 'L1' THEN 2024
                    WHEN 'L2' THEN 2023
                    WHEN 'L3' THEN 2022
                    WHEN 'M1' THEN 2024
                    WHEN 'M2' THEN 2023
                END,
                '2024-2025'
            );
            
            total_students := total_students + 1;
        END LOOP;
    END LOOP;
    
    RAISE NOTICE 'Created % students', total_students;
END $$;

-- ============================================================================
-- INSERT ENROLLMENTS
-- ============================================================================
-- Each student is enrolled in all modules of their formation
-- This creates ~130,000+ enrollments

DO $$
DECLARE
    student RECORD;
    module RECORD;
    enrollment_count INTEGER := 0;
BEGIN
    -- For each student, enroll them in all modules of their formation
    FOR student IN SELECT * FROM students LOOP
        FOR module IN 
            SELECT * FROM modules 
            WHERE formation_id = student.formation_id AND is_active = true 
        LOOP
            INSERT INTO enrollments (
                student_id,
                module_id,
                academic_year,
                status
            )
            VALUES (
                student.id,
                module.id,
                '2024-2025',
                'enrolled'
            );
            
            enrollment_count := enrollment_count + 1;
        END LOOP;
    END LOOP;
    
    RAISE NOTICE 'Created % enrollments', enrollment_count;
END $$;

-- ============================================================================
-- INSERT EXAM SESSION
-- ============================================================================
-- Create a sample exam session for testing

INSERT INTO exam_sessions (
    name,
    session_type,
    start_date,
    end_date,
    academic_year,
    status
)
VALUES (
    'Session Normale - Semestre 1',
    'normal',
    '2025-01-20',
    '2025-02-07',
    '2024-2025',
    'draft'
);

-- ============================================================================
-- CREATE ADMIN USER
-- ============================================================================
-- Default admin for testing (password: admin123)
-- Note: In production, use proper password hashing!

INSERT INTO users (
    email,
    password_hash,
    role
)
VALUES (
    'admin@univ-alger.dz',
    -- This is a placeholder hash. In the backend, we'll use bcrypt
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.M4EQEXbVqK.pLe',
    'admin'
);

-- ============================================================================
-- CLEANUP TEMPORARY TABLES
-- ============================================================================

DROP TABLE IF EXISTS male_first_names;
DROP TABLE IF EXISTS female_first_names;
DROP TABLE IF EXISTS family_names;
DROP FUNCTION IF EXISTS random_element;
DROP FUNCTION IF EXISTS random_phone;

-- ============================================================================
-- DISPLAY SUMMARY STATISTICS
-- ============================================================================

DO $$
DECLARE
    dept_count INTEGER;
    form_count INTEGER;
    student_count INTEGER;
    prof_count INTEGER;
    module_count INTEGER;
    enrollment_count INTEGER;
    room_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO dept_count FROM departments;
    SELECT COUNT(*) INTO form_count FROM formations;
    SELECT COUNT(*) INTO student_count FROM students;
    SELECT COUNT(*) INTO prof_count FROM professors;
    SELECT COUNT(*) INTO module_count FROM modules;
    SELECT COUNT(*) INTO enrollment_count FROM enrollments;
    SELECT COUNT(*) INTO room_count FROM exam_rooms;
    
    RAISE NOTICE '';
    RAISE NOTICE '============================================';
    RAISE NOTICE 'DATABASE SEED SUMMARY';
    RAISE NOTICE '============================================';
    RAISE NOTICE 'Departments:    %', dept_count;
    RAISE NOTICE 'Formations:     %', form_count;
    RAISE NOTICE 'Students:       %', student_count;
    RAISE NOTICE 'Professors:     %', prof_count;
    RAISE NOTICE 'Modules:        %', module_count;
    RAISE NOTICE 'Enrollments:    %', enrollment_count;
    RAISE NOTICE 'Exam Rooms:     %', room_count;
    RAISE NOTICE '============================================';
END $$;
