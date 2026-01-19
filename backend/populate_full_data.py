#!/usr/bin/env python3
# ==============================================================================
# SCRIPT DE PEUPLEMENT - DONNÉES RÉALISTES ALGÉRIENNES
# ==============================================================================
# Ce script génère des données réalistes pour une université algérienne.
# Il utilise de vrais prénoms et noms de famille arabes/berbères.
# ==============================================================================

import asyncio
import random
import uuid
from datetime import date, datetime, timezone

from app.core.database import async_session_maker, init_db
from app.models import (
    Department, Formation, Professor, Student, Module,
    ExamRoom, Enrollment, ExamSession, User
)
from sqlalchemy import select, func
from app.core.security import get_password_hash

# ==============================================================================
# DONNÉES RÉALISTES ALGÉRIENNES
# ==============================================================================

# Prénoms masculins algériens (arabes et berbères)
PRENOMS_MASCULINS = [
    "Mohamed", "Ahmed", "Youssef", "Amine", "Karim", "Omar", "Ali", "Bilal",
    "Sofiane", "Riad", "Nadir", "Hamza", "Mehdi", "Walid", "Farouk", "Anis",
    "Zakaria", "Ayoub", "Mourad", "Samir", "Rachid", "Nabil", "Yacine", "Khaled",
    "Ismail", "Redouane", "Abdelkader", "Noureddine", "Djamel", "Lotfi", "Hakim",
    "Abderrahmane", "Salim", "Nacer", "Toufik", "Malik", "Massine", "Rayan",
    "Adel", "Fares", "Idriss", "Ghiles", "Akram", "Zaki", "Amar", "Mustapha",
    "Lyes", "Rafik", "Hichem", "Said", "Brahim", "Tarek", "Mounir", "Farid"
]

# Prénoms féminins algériens (arabes et berbères)
PRENOMS_FEMININS = [
    "Fatima", "Amina", "Meriem", "Khadija", "Sara", "Nour", "Yasmine", "Lina",
    "Imane", "Ikram", "Asma", "Rania", "Nesrine", "Samira", "Houda", "Dalia",
    "Chaima", "Sihem", "Lamia", "Amel", "Souad", "Djamila", "Malika", "Hafsa",
    "Zineb", "Leila", "Wafa", "Amira", "Hanane", "Salima", "Karima", "Nabila",
    "Faiza", "Safia", "Naima", "Aicha", "Wassila", "Louiza", "Tassadit", "Dyhia",
    "Lynda", "Melissa", "Ryma", "Katia", "Lydia", "Sabrina", "Kahina", "Tinhinan"
]

# Noms de famille algériens (arabes et berbères)
NOMS_FAMILLE = [
    "Benali", "Boudiaf", "Kaci", "Hadj", "Amrani", "Belkacem", "Zerhouni",
    "Messaoudi", "Boumediene", "Mammeri", "Ait Ahmed", "Benaissa", "Hammoudi",
    "Khellaf", "Benslimane", "Mebarki", "Ouali", "Berkane", "Saidi", "Mekki",
    "Ferhat", "Dahlab", "Boukhalfa", "Brahimi", "Cherif", "Djebbar", "Fellah",
    "Grine", "Hamidi", "Ibrahimi", "Ait Kaci", "Larbi", "Mansouri", "Nait Rabah",
    "Oukaci", "Boudjerda", "Rahmani", "Slimani", "Taleb", "Yahiaoui", "Zidane",
    "Amirouche", "Benamara", "Chibane", "Derdour", "Fekhar", "Guellati", "Hadef",
    "Ighil", "Kerboua", "Laouari", "Mazouz", "Nezar", "Ouahab", "Rabhi", "Selmi",
    "Tounsi", "Yahi", "Zeghdoud", "Ait Ouali", "Belhadi", "Chikhi", "Dib",
    "Ferhati", "Guendouz", "Haddadi", "Idir", "Khaldi", "Laoubi", "Medjdoub"
]

# Titres de modules réalistes par département
MODULES_PAR_DOMAINE = {
    "Informatique": [
        "Algorithmique et Structures de Données", "Programmation Orientée Objet",
        "Bases de Données", "Systèmes d'Exploitation", "Réseaux Informatiques",
        "Intelligence Artificielle", "Génie Logiciel", "Sécurité Informatique",
        "Développement Web", "Architecture des Ordinateurs", "Compilation",
        "Analyse Numérique", "Théorie des Graphes", "Machine Learning"
    ],
    "Mathématiques": [
        "Analyse 1", "Analyse 2", "Algèbre 1", "Algèbre 2", "Probabilités",
        "Statistiques", "Analyse Numérique", "Topologie", "Analyse Complexe",
        "Équations Différentielles", "Recherche Opérationnelle"
    ],
    "Physique": [
        "Mécanique du Point", "Thermodynamique", "Électromagnétisme",
        "Optique Géométrique", "Mécanique Quantique", "Physique des Solides",
        "Électronique Analogique", "Électronique Numérique", "Ondes et Vibrations"
    ],
    "Chimie": [
        "Chimie Générale", "Chimie Organique 1", "Chimie Organique 2",
        "Chimie Analytique", "Chimie Physique", "Biochimie", "Electrochimie"
    ],
    "Sciences Naturelles": [
        "Biologie Cellulaire", "Génétique", "Écologie", "Microbiologie",
        "Biologie Moléculaire", "Physiologie Animale", "Physiologie Végétale"
    ],
    "Langues": [
        "Anglais Scientifique 1", "Anglais Scientifique 2", "Français",
        "Technique d'Expression", "Communication Scientifique"
    ],
    "Économie": [
        "Microéconomie", "Macroéconomie", "Comptabilité", "Gestion Financière",
        "Management", "Marketing", "Économie Monétaire", "Commerce International"
    ]
}

# Départements d'une faculté de sciences
DEPARTEMENTS = [
    ("Informatique", "INFO", "Bâtiment A"),
    ("Mathématiques", "MATH", "Bâtiment B"),
    ("Physique", "PHYS", "Bâtiment C"),
    ("Chimie", "CHIM", "Bâtiment C"),
    ("Sciences Naturelles", "SNV", "Bâtiment D"),
    ("Langues Étrangères", "LANG", "Bâtiment E"),
    ("Sciences Économiques", "ECO", "Bâtiment F")
]

# ==============================================================================
# FONCTIONS UTILITAIRES
# ==============================================================================

def generer_prenom():
    """Génère un prénom aléatoire (50% masculin, 50% féminin)."""
    if random.random() < 0.5:
        return random.choice(PRENOMS_MASCULINS)
    return random.choice(PRENOMS_FEMININS)

def generer_nom():
    """Génère un nom de famille aléatoire."""
    return random.choice(NOMS_FAMILLE)

def generer_email(prenom: str, nom: str, domaine: str = "univ-alger.dz") -> str:
    """Génère une adresse email réaliste."""
    prenom_clean = prenom.lower().replace(" ", "").replace("'", "")
    nom_clean = nom.lower().replace(" ", "").replace("'", "")
    random_suffix = random.randint(1, 99)
    return f"{prenom_clean}.{nom_clean}{random_suffix}@{domaine}"

def generer_numero_etudiant(annee: int, index: int) -> str:
    """Génère un numéro d'étudiant au format algérien."""
    return f"{annee}{index:06d}"

# ==============================================================================
# FONCTION PRINCIPALE DE PEUPLEMENT
# ==============================================================================

async def populate_realistic_data(target_students: int = 13000):
    """
    Peuple la base de données avec des données réalistes algériennes.
    
    Cette fonction crée :
    - 7 départements
    - 35 formations (5 par département)
    - 175 professeurs (25 par département)
    - 307 modules
    - 40 salles d'examen
    - 13,000 étudiants avec noms algériens
    - ~100,000 inscriptions
    - 1 session d'examen
    - 1 utilisateur admin
    """
    await init_db()
    
    async with async_session_maker() as db:
        print("=" * 60)
        print("🇩🇿 PEUPLEMENT AVEC DONNÉES RÉALISTES ALGÉRIENNES")
        print("=" * 60)
        
        # ---------------------------------------------------------------------
        # 1. DÉPARTEMENTS
        # ---------------------------------------------------------------------
        print("\n📚 Création des départements...")
        
        existing_depts = (await db.execute(select(func.count(Department.id)))).scalar()
        if existing_depts > 0:
            print(f"   → {existing_depts} départements existants, on passe...")
            departments = (await db.execute(select(Department))).scalars().all()
        else:
            departments = []
            for nom, code, batiment in DEPARTEMENTS:
                dept = Department(
                    name=nom,
                    code=code,
                    email=f"{code.lower()}@univ-alger.dz",
                    phone=f"021-{random.randint(10,99)}-{random.randint(10,99)}-{random.randint(10,99)}",
                    building=batiment,
                    is_active=True
                )
                db.add(dept)
                departments.append(dept)
            await db.commit()
            print(f"   ✓ {len(departments)} départements créés")
        
        # ---------------------------------------------------------------------
        # 2. FORMATIONS (5 par département = 35 total)
        # ---------------------------------------------------------------------
        print("\n🎓 Création des formations...")
        
        existing_formations = (await db.execute(select(func.count(Formation.id)))).scalar()
        if existing_formations > 0:
            print(f"   → {existing_formations} formations existantes, on passe...")
            formations = (await db.execute(select(Formation))).scalars().all()
        else:
            formations = []
            niveaux = [
                ("L1", 1), ("L2", 2), ("L3", 3), ("M1", 4), ("M2", 5)
            ]
            for dept in departments:
                for niveau, year in niveaux:
                    fmt = Formation(
                        department_id=dept.id,
                        name=f"{niveau} {dept.name}",
                        code=f"{dept.code}-{niveau}",
                        level=niveau,
                        module_count=random.randint(6, 10),
                        academic_year="2025-2026",
                        is_active=True
                    )
                    db.add(fmt)
                    formations.append(fmt)
            await db.commit()
            print(f"   ✓ {len(formations)} formations créées")
        
        # ---------------------------------------------------------------------
        # 3. PROFESSEURS (25 par département = 175 total)
        # ---------------------------------------------------------------------
        print("\n👨‍🏫 Création des professeurs...")
        
        existing_profs = (await db.execute(select(func.count(Professor.id)))).scalar()
        if existing_profs > 0:
            print(f"   → {existing_profs} professeurs existants, on passe...")
            professors = (await db.execute(select(Professor))).scalars().all()
        else:
            professors = []
            grades = ["Maître Assistant A", "Maître Assistant B", "Maître de Conférences A", 
                     "Maître de Conférences B", "Professeur"]
            
            noms_utilises = set()  # Éviter les doublons d'email
            
            for dept in departments:
                for _ in range(25):
                    prenom = generer_prenom()
                    nom = generer_nom()
                    
                    # Éviter les doublons d'email
                    email = generer_email(prenom, nom, "univ-alger.dz")
                    while email in noms_utilises:
                        prenom = generer_prenom()
                        nom = generer_nom()
                        email = generer_email(prenom, nom, "univ-alger.dz")
                    noms_utilises.add(email)
                    
                    prof = Professor(
                        department_id=dept.id,
                        first_name=prenom,
                        last_name=nom,
                        email=email,
                        phone=f"05{random.randint(5,7)}{random.randint(1000000,9999999)}",
                        grade=random.choice(grades),
                        specialization=dept.name,
                        max_surveillance_hours=random.randint(15, 30),
                        current_surveillance_hours=0,
                        is_active=True
                    )
                    db.add(prof)
                    professors.append(prof)
            await db.commit()
            print(f"   ✓ {len(professors)} professeurs créés")
        
        # ---------------------------------------------------------------------
        # 4. MODULES (8-10 par formation ≈ 307 total)
        # ---------------------------------------------------------------------
        print("\n📖 Création des modules...")
        
        existing_modules = (await db.execute(select(func.count(Module.id)))).scalar()
        if existing_modules > 0:
            print(f"   → {existing_modules} modules existants, on passe...")
            modules = (await db.execute(select(Module))).scalars().all()
        else:
            modules = []
            
            # Mapper les départements aux domaines de modules
            dept_domain_map = {
                "Informatique": "Informatique",
                "Mathématiques": "Mathématiques",
                "Physique": "Physique",
                "Chimie": "Chimie",
                "Sciences Naturelles": "Sciences Naturelles",
                "Langues Étrangères": "Langues",
                "Sciences Économiques": "Économie"
            }
            
            for fmt in formations:
                dept = next((d for d in departments if d.id == fmt.department_id), None)
                if not dept:
                    continue
                    
                domain = dept_domain_map.get(dept.name, "Informatique")
                available_modules = MODULES_PAR_DOMAINE.get(domain, MODULES_PAR_DOMAINE["Informatique"])
                
                # Sélectionner des modules aléatoires
                num_modules = min(fmt.module_count, len(available_modules))
                selected_modules = random.sample(available_modules, num_modules)
                
                for i, mod_name in enumerate(selected_modules):
                    # Professeur responsable aléatoire du département
                    dept_profs = [p for p in professors if p.department_id == dept.id]
                    
                    module = Module(
                        formation_id=fmt.id,
                        professor_id=random.choice(dept_profs).id if dept_profs else professors[0].id,
                        name=f"{mod_name}",
                        code=f"{fmt.code}-M{i+1:02d}",
                        credits=random.choice([3, 4, 5, 6]),
                        coefficient=random.choice([2, 3, 4]),
                        semester=1 if "L1" in fmt.code or "M1" in fmt.code else 2,
                        exam_duration_minutes=random.choice([90, 120, 180]),
                        requires_computer=(domain == "Informatique" and random.random() < 0.3),
                        requires_lab=(domain in ["Physique", "Chimie"] and random.random() < 0.4),
                        is_active=True
                    )
                    db.add(module)
                    modules.append(module)
            
            await db.commit()
            print(f"   ✓ {len(modules)} modules créés")
        
        # ---------------------------------------------------------------------
        # 5. SALLES D'EXAMEN (40 salles)
        # ---------------------------------------------------------------------
        print("\n🏫 Création des salles d'examen...")
        
        existing_rooms = (await db.execute(select(func.count(ExamRoom.id)))).scalar()
        if existing_rooms > 0:
            print(f"   → {existing_rooms} salles existantes, on passe...")
        else:
            room_configs = [
                # (préfixe, type, capacité, nombre, has_computers)
                ("Amphi", "amphitheater", 300, 4, False),
                ("Amphi", "amphitheater", 200, 4, False),
                ("Salle", "classroom", 100, 8, False),
                ("Salle", "classroom", 60, 10, False),
                ("Salle Info", "lab", 40, 8, True),
                ("Labo", "lab", 30, 6, True),
            ]
            
            room_count = 0
            for prefix, rtype, capacity, count, has_computers in room_configs:
                for i in range(count):
                    room = ExamRoom(
                        name=f"{prefix} {room_count + 1:02d}",
                        building=f"Bâtiment {chr(65 + (room_count % 5))}",
                        floor=random.randint(0, 3),
                        room_type=rtype,
                        total_capacity=capacity,
                        exam_capacity=int(capacity * 0.7),  # 70% pour espacement
                        has_computers=has_computers,
                        has_projector=True,
                        has_video_surveillance=random.random() < 0.6,
                        is_accessible=(room_count % 5 == 0),
                        is_available=True,
                        is_active=True
                    )
                    db.add(room)
                    room_count += 1
            
            await db.commit()
            print(f"   ✓ {room_count} salles créées")
        
        # ---------------------------------------------------------------------
        # 6. ÉTUDIANTS (13,000 avec noms algériens)
        # ---------------------------------------------------------------------
        print(f"\n👨‍🎓 Création de {target_students} étudiants avec noms algériens...")
        
        existing_students = (await db.execute(select(func.count(Student.id)))).scalar()
        students_to_create = target_students - existing_students
        
        if students_to_create <= 0:
            print(f"   → {existing_students} étudiants existants, on passe...")
        else:
            print(f"   → {existing_students} existants, création de {students_to_create} nouveaux...")
            
            formation_ids = [f.id for f in formations]
            emails_utilises = set()
            
            batch_size = 100
            for batch_start in range(0, students_to_create, batch_size):
                batch_end = min(batch_start + batch_size, students_to_create)
                
                for i in range(batch_start, batch_end):
                    prenom = generer_prenom()
                    nom = generer_nom()
                    
                    # Génération email unique
                    email = generer_email(prenom, nom, "etu.univ-alger.dz")
                    attempts = 0
                    while email in emails_utilises and attempts < 10:
                        # Ajouter un suffixe si doublon
                        email = generer_email(prenom, nom, "etu.univ-alger.dz")
                        attempts += 1
                    emails_utilises.add(email)
                    
                    student = Student(
                        formation_id=random.choice(formation_ids),
                        student_number=generer_numero_etudiant(2025, existing_students + i + 1),
                        first_name=prenom,
                        last_name=nom,
                        email=email,
                        enrollment_year=random.choice([2021, 2022, 2023, 2024, 2025])
                    )
                    db.add(student)
                
                await db.commit()
                progress = ((batch_end) / students_to_create) * 100
                print(f"   → Progression: {batch_end}/{students_to_create} ({progress:.1f}%)")
            
            print(f"   ✓ {students_to_create} étudiants créés avec noms algériens")
        
        # ---------------------------------------------------------------------
        # 7. INSCRIPTIONS (chaque étudiant inscrit aux modules de sa formation)
        # ---------------------------------------------------------------------
        print("\n📝 Création des inscriptions...")
        
        existing_enrollments = (await db.execute(select(func.count(Enrollment.id)))).scalar()
        if existing_enrollments > 0:
            print(f"   → {existing_enrollments} inscriptions existantes, on passe...")
        else:
            # Récupérer tous les étudiants et modules
            all_students = (await db.execute(select(Student.id, Student.formation_id))).all()
            
            # Mapper formation -> modules
            module_by_formation = {}
            for mod in modules:
                if mod.formation_id not in module_by_formation:
                    module_by_formation[mod.formation_id] = []
                module_by_formation[mod.formation_id].append(mod.id)
            
            total_enrollments = 0
            batch_size = 500
            enrollment_batch = []
            
            for student_id, formation_id in all_students:
                formation_modules = module_by_formation.get(formation_id, [])
                for module_id in formation_modules:
                    enrollment = Enrollment(
                        student_id=student_id,
                        module_id=module_id,
                        academic_year="2025-2026",
                        status="enrolled"
                    )
                    enrollment_batch.append(enrollment)
                    total_enrollments += 1
                    
                    if len(enrollment_batch) >= batch_size:
                        db.add_all(enrollment_batch)
                        await db.commit()
                        print(f"   → Inscriptions créées: {total_enrollments}")
                        enrollment_batch = []
            
            # Commit final
            if enrollment_batch:
                db.add_all(enrollment_batch)
                await db.commit()
            
            print(f"   ✓ {total_enrollments} inscriptions créées")
        
        # ---------------------------------------------------------------------
        # 8. SESSION D'EXAMEN (Janvier 2026)
        # ---------------------------------------------------------------------
        print("\n📅 Création de la session d'examen...")
        
        existing_sessions = (await db.execute(select(func.count(ExamSession.id)))).scalar()
        if existing_sessions > 0:
            print(f"   → Session existante, on passe...")
        else:
            session = ExamSession(
                name="Session Principale S1 2026",
                session_type="main",
                start_date=date(2026, 1, 20),
                end_date=date(2026, 2, 8),  # ~3 semaines pour 307 examens
                academic_year="2025-2026",
                status="planned"
            )
            db.add(session)
            await db.commit()
            print("   ✓ Session d'examen créée (20 Jan - 8 Fév 2026)")
        
        # ---------------------------------------------------------------------
        # 9. UTILISATEUR ADMIN
        # ---------------------------------------------------------------------
        print("\n👤 Création de l'utilisateur admin...")
        
        existing_users = (await db.execute(select(func.count(User.id)))).scalar()
        if existing_users > 0:
            print(f"   → Utilisateur existant, on passe...")
        else:
            admin = User(
                email="admin@univ-alger.dz",
                password_hash=get_password_hash("admin123"),
                role="admin",
                is_active=True
            )
            db.add(admin)
            await db.commit()
            print("   ✓ Admin créé (admin@univ-alger.dz / admin123)")
        
        # ---------------------------------------------------------------------
        # 10. UTILISATEURS DE DÉMO (Pour la soutenance)
        # ---------------------------------------------------------------------
        print("\n👥 Création des utilisateurs de démo pour la soutenance...")
        
        # 1. Chef de Département Informatique
        dept_info = next((d for d in departments if d.code == "INFO"), None)
        if dept_info:
            dept_head_email = "head_info@univ-alger.dz"
            if not (await db.execute(select(User).filter_by(email=dept_head_email))).scalar():
                head_user = User(
                    email=dept_head_email,
                    password_hash=get_password_hash("head123"),
                    role="dept_head",
                    department_id=dept_info.id,
                    is_active=True
                )
                db.add(head_user)
                print("   ✓ Chef de Dept créé (head_info@univ-alger.dz / head123)")

        # 2. Professeur Informatique
        # On prend le premier prof du dept info
        if departments:
            dept_info = next((d for d in departments if d.code == "INFO"), None)
            if dept_info:
                # Chercher un prof de ce département
                prof = (await db.execute(select(Professor).filter_by(department_id=dept_info.id).limit(1))).scalar_one_or_none()
                if prof:
                    prof_email = "prof_info@univ-alger.dz" # On utilise un email générique pour la démo, ou celui du prof
                    # Pour la démo, on crée un user avec cet email spécifique lié à ce prof
                    if not (await db.execute(select(User).filter_by(email=prof_email))).scalar():
                        prof_user = User(
                            email=prof_email,
                            password_hash=get_password_hash("prof123"),
                            role="professor",
                            professor_id=prof.id,
                            department_id=dept_info.id,
                            is_active=True
                        )
                        db.add(prof_user)
                        print("   ✓ Professeur créé (prof_info@univ-alger.dz / prof123)")

        # 3. Étudiant Informatique
        if formations:
            # Chercher une formation info
            fmt_info = next((f for f in formations if "INFO" in f.code or "Informatique" in f.name), None)
            if fmt_info:
                student = (await db.execute(select(Student).filter_by(formation_id=fmt_info.id).limit(1))).scalar_one_or_none()
                if student:
                    student_email = "etu_info@univ-alger.dz"
                    if not (await db.execute(select(User).filter_by(email=student_email))).scalar():
                        student_user = User(
                            email=student_email,
                            password_hash=get_password_hash("etu123"),
                            role="student",
                            student_id=student.id,
                            department_id=fmt_info.department_id,
                            is_active=True
                        )
                        db.add(student_user)
                        print("   ✓ Étudiant créé (etu_info@univ-alger.dz / etu123)")
        
        await db.commit()
        
        # ---------------------------------------------------------------------
        # RÉSUMÉ FINAL
        # ---------------------------------------------------------------------
        print("\n" + "=" * 60)
        print("✅ PEUPLEMENT TERMINÉ !")
        print("=" * 60)
        
        # Compter les enregistrements
        counts = {
            "Départements": (await db.execute(select(func.count(Department.id)))).scalar(),
            "Formations": (await db.execute(select(func.count(Formation.id)))).scalar(),
            "Professeurs": (await db.execute(select(func.count(Professor.id)))).scalar(),
            "Modules": (await db.execute(select(func.count(Module.id)))).scalar(),
            "Salles": (await db.execute(select(func.count(ExamRoom.id)))).scalar(),
            "Étudiants": (await db.execute(select(func.count(Student.id)))).scalar(),
            "Inscriptions": (await db.execute(select(func.count(Enrollment.id)))).scalar(),
            "Sessions": (await db.execute(select(func.count(ExamSession.id)))).scalar(),
        }
        
        for table, count in counts.items():
            print(f"   {table}: {count:,}")
        
        print("\n🇩🇿 Données algériennes réalistes générées avec succès !")


if __name__ == "__main__":
    asyncio.run(populate_realistic_data(target_students=13000))
