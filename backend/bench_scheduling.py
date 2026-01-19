"""
Script de Benchmark - Mesure des performances de planification
================================================================
Ce script mesure le temps d'exécution de l'algorithme de planification
automatique. C'est utile pour valider l'objectif de < 45 secondes.

Usage:
    cd backend
    python bench_scheduling.py
"""

import asyncio
import time
from sqlalchemy import select

from app.core.database import async_session_maker
from app.models import ExamSession


async def benchmark():
    """
    Lance un benchmark complet de la planification :
    1. Efface le planning existant
    2. Initialise les examens depuis les modules
    3. Lance la planification automatique
    4. Affecte les surveillants
    
    Affiche les temps d'exécution pour chaque étape.
    """
    async with async_session_maker() as db:
        # Chercher la session d'examen
        result = await db.execute(
            select(ExamSession).where(ExamSession.name == "Session Principale S1 2026")
        )
        session = result.scalar_one_or_none()
        
        if not session:
            print("Erreur : Session non trouvée. Lancez d'abord populate_full_data.py")
            return

        print(f"\n{'='*60}")
        print(f"BENCHMARK - Session : {session.name}")
        print(f"{'='*60}\n")
        
        # Import des fonctions de planification
        from app.routers.scheduling import (
            clear_session_schedule,
            prepare_session_for_scheduling,
            schedule_entire_session,
            assign_exam_supervisors
        )
        
        # Utilisateur fictif pour les tests (doit avoir le rôle admin)
        fake_user = {"role": "admin"}
        
        # ---------------------------------------------------------------
        # ÉTAPE 0 : Réinitialisation
        # ---------------------------------------------------------------
        await clear_session_schedule(session.id, db=db, current_user=fake_user)
        print("Session réinitialisée.")

        # ---------------------------------------------------------------
        # ÉTAPE 1 : Préparation (création des examens depuis les modules)
        # ---------------------------------------------------------------
        start = time.time()
        await prepare_session_for_scheduling(session.id, db=db, current_user=fake_user)
        prep_time = time.time() - start
        print(f"Préparation : {prep_time:.2f} secondes")
        
        # ---------------------------------------------------------------
        # ÉTAPE 2 : Planification automatique (l'étape critique)
        # ---------------------------------------------------------------
        start = time.time()
        res = await schedule_entire_session(session.id, db=db, current_user=fake_user)
        schedule_time = time.time() - start
        
        print(f"\nPLANIFICATION : {schedule_time:.2f} secondes")
        print(f"  - Examens planifiés : {res.scheduled_count}")
        print(f"  - Examens échoués   : {res.failed_count}")
        
        # Vérifier l'objectif
        if schedule_time < 45:
            print(f"  ✓ Objectif atteint (< 45s)")
        else:
            print(f"  ✗ Objectif non atteint (> 45s)")
        
        # ---------------------------------------------------------------
        # ÉTAPE 3 : Affectation des surveillants
        # ---------------------------------------------------------------
        start = time.time()
        sup_res = await assign_exam_supervisors(session.id, db=db, current_user=fake_user)
        assign_time = time.time() - start
        
        print(f"\nAffectation surveillants : {assign_time:.2f} secondes")
        print(f"  - Surveillances créées : {sup_res['assignments_made']}")
        print(f"  - Professeurs impliqués : {sup_res['professors_used']}")
        
        # ---------------------------------------------------------------
        # RÉSUMÉ
        # ---------------------------------------------------------------
        total = prep_time + schedule_time + assign_time
        print(f"\n{'='*60}")
        print(f"TEMPS TOTAL : {total:.2f} secondes")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(benchmark())
