# Plateforme d'Optimisation des Emplois du Temps d'Examens Universitaires

> Projet réalisé dans le cadre du module **Base de Données Avancées (BDA)**  
> Année universitaire 2025-2026

## Contexte du Projet

Dans une faculté de plus de **13 000 étudiants** répartis sur **7 départements** et plus de 
200 offres de formation, l'élaboration manuelle des emplois du temps d'examens génère 
fréquemment des conflits :
- Surcharge des amphithéâtres
- Salles limitées à 20 étudiants max (en période d'examen)
- Chevauchements étudiants/professeurs
- Contraintes d'équipements

Ce projet propose une solution automatisée basée sur une base de données relationnelle 
couplée à un algorithme d'optimisation.

## Technologies Utilisées

| Couche | Technologie |
|--------|-------------|
| **Frontend** | Streamlit + CSS personnalisé |
| **Backend** | FastAPI (Python) |
| **Base de données** | PostgreSQL via Neon (cloud) |
| **Authentification** | JWT |

## Structure du Projet

```
project-bda/
├── backend/                 # API FastAPI
│   ├── app/
│   │   ├── core/           # Config, connexion DB, sécurité
│   │   ├── models/         # Modèles SQLAlchemy
│   │   ├── routers/        # Endpoints API
│   │   ├── schemas/        # Schémas Pydantic
│   │   └── main.py         # Point d'entrée
│   ├── populate_full_data.py  # Script de peuplement massif
│   └── requirements.txt
│
├── frontend/               # Interface Streamlit
│   ├── utils/
│   │   ├── api.py          # Client API
│   │   └── styles.py       # CSS personnalisé
│   ├── app.py              # Application principale
│   └── requirements.txt
│
├── database/               # Scripts SQL
│   ├── schema.sql          # Schéma de la base
│   ├── procedures.sql      # Procédures PL/pgSQL
│   └── seed.sql            # Données de test
│
└── CHECKLIST.md            # Liste de vérification
```

## Installation et Lancement

### Prérequis
- Python 3.11+
- Compte Neon (PostgreSQL cloud)

### Étapes

```bash
# 1. Cloner et entrer dans le projet
cd project-bda

# 2. Créer l'environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Linux/Mac

# 3. Installer les dépendances
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt

# 4. Configurer les variables d'environnement
# Éditer backend/.env avec vos identifiants Neon

# 5. Peupler la base de données (si vide)
cd backend
python populate_full_data.py

# 6. Lancer les serveurs
# Terminal 1 - Backend
cd backend && uvicorn app.main:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend && streamlit run app.py
```

### Accès à l'Application

- **Interface Web** : (https://project-bda-v3c3zb5nqtxljq6zpyx4ff.streamlit.app/)
- **Documentation API** : (https://exam-scheduling-backend.onrender.com)

### Comptes Utilisateurs

| Rôle | Email | Mot de passe |
|------|-------|--------------|
| **Admin** (Service planification) | admin@univ-alger.dz | admin123 |
| **Vice-Doyen** | vicedoyen@univ-alger.dz | vicedoyen123 |
| **Doyen** | doyen@univ-alger.dz | doyen123 |
| **Chef Département** | chef.info@univ-alger.dz | chef123 |
| **Professeur** | professeur@univ-alger.dz | prof123 |
| **Étudiant** | etudiant@etu.univ-alger.dz | etu123 |

## Benchmark de Performance

Résultats obtenus sur la base de données cloud (Neon EU - Frankfurt) :

| Étape | Temps | Objectif |
|-------|-------|----------|
| Préparation (284 examens) | **0.96s** | ✓ |
| Planification automatique | **31.58s** | ✓ < 45s |
| Affectation surveillants | **17.38s** | ✓ |
| **TOTAL** | **49.93s** | ✓ |

- ✅ 284 examens planifiés sans conflits
- ✅ 0 examens échoués
- ✅ Serveur EU (Frankfurt) pour latence réduite depuis l'Algérie

## Fonctionnalités Principales

### Algorithme de Planification
- Génération automatique d'emploi du temps sans conflits
- **Exclusion des vendredis** (système algérien)
- Respect de la contrainte : max 1 examen par jour par étudiant
- Équilibrage de charge des surveillants (max 3 par jour)

### Détection de Conflits
- Conflits de salles (chevauchement horaire)
- Conflits de capacité (dépassement)
- Conflits étudiants (examens simultanés)
- Conflits professeurs (surveillances simultanées)

### Tableau de Bord
- Vue globale des KPIs (étudiants, examens, salles)
- Taux d'occupation des amphithéâtres
- Suivi des conflits par département

## Données de Test

Le script `populate_full_data.py` génère :
- 7 départements
- 35 formations (Licence + Master)
- 13 000 étudiants
- 175 professeurs
- ~300 modules
- ~100 000 inscriptions

## Contraintes Modélisées

| Contrainte | Implémentation |
|------------|----------------|
| Pas d'examen le vendredi | `weekday() == 4` exclu |
| Max 1 examen/jour/étudiant | Vérification mémoire |
| Max 3 examens/jour/prof | Limite dans l'algo |
| Capacité salles | Vérification avant affectation |
| Priorité département | Score pondéré (+20 pts) |

## Acteurs et Rôles

| Acteur | Fonctionnalités |
|--------|-----------------|
| **Vice-doyen** | Vue stratégique, validation finale |
| **Administrateur** | Génération EDT, résolution conflits |
| **Chef département** | Validation par département |
| **Étudiant/Prof** | Consultation planning personnalisé |

## Auteurs

Projet universitaire - Module BDA 2025-2026

## Licence

Projet académique - Libre d'utilisation
