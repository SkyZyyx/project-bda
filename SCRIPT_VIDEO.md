# 🎬 SCRIPT VIDÉO - Présentation du Projet BDA
## Plateforme d'Optimisation des Emplois du Temps d'Examens Universitaires

**Durée estimée** : 8-10 minutes

---

## 🎯 INTRODUCTION (1 minute)

**[Écran : Page de connexion de l'application]**

> "Bonjour, je vous présente aujourd'hui notre projet de Base de Données Avancées : une plateforme d'optimisation automatique des emplois du temps d'examens universitaires.

> Dans une faculté comme la nôtre, avec plus de 13 000 étudiants répartis sur 7 départements, l'élaboration manuelle des plannings d'examens pose de nombreux problèmes : chevauchements, surcharge des salles, conflits de surveillance...

> Notre solution propose une base de données PostgreSQL couplée à un algorithme d'optimisation capable de générer un planning complet en moins de 45 secondes."

---

## 📊 ARCHITECTURE ET BASE DE DONNÉES (2 minutes)

**[Écran : Schéma de la base de données ou code des modèles]**

> "Notre architecture repose sur trois couches :
> - Un **backend FastAPI** en Python qui expose une API REST
> - Un **frontend Streamlit** avec une interface moderne
> - Une base **PostgreSQL hébergée sur Neon** en région Europe pour minimiser la latence

> Notre schéma relationnel comprend 11 tables interconnectées :
> - **departments** et **formations** pour la structure académique
> - **professors** et **students** pour les acteurs (13 000 étudiants, 175 professeurs)
> - **modules** (284 modules) liés aux formations
> - **enrollments** qui lie les étudiants aux modules (105 000 inscriptions)
> - **exam_sessions**, **exams**, **exam_rooms** et **exam_supervisors** pour la gestion des examens
> - **users** avec différents rôles : admin, vice-doyen, chef de département, professeur, étudiant"

---

## 👥 RÔLES ET FONCTIONNALITÉS (2 minutes)

**[Écran : Dashboard avec différentes vues selon le rôle]**

> "Chaque acteur a des fonctionnalités adaptées à son rôle :

> **Le Vice-Doyen et le Doyen** ont une vue stratégique globale : occupation des amphis, taux de conflits par département, validation finale de l'emploi du temps, KPIs académiques.

> **L'Administrateur des examens** du service planification peut lancer la génération automatique, détecter les conflits, et optimiser les ressources.

> **Le Chef de département** valide les plannings de son département, consulte les statistiques et les conflits par formation.

> **Les Étudiants et Professeurs** peuvent consulter leur planning personnalisé, filtré par département ou formation."

**[Démontrer la connexion avec différents comptes]**

---

## ⚙️ ALGORITHME DE PLANIFICATION (2 minutes)

**[Écran : Code de l'algorithme ou console avec logs]**

> "L'algorithme de planification respecte plusieurs contraintes algériennes importantes :

> 1. **Pas d'examen le vendredi** - le jour de prière est exclu automatiquement
> 2. **Maximum 1 examen par jour par étudiant** - on évite la surcharge
> 3. **Maximum 3 surveillances par jour par professeur** - équilibrage de charge
> 4. **Respect des capacités des salles** - chaque salle a sa capacité d'examen définie
> 5. **Priorité au département** - un professeur surveille en priorité les examens de son département

> L'algorithme utilise une approche gloutonne optimisée : il trie les examens par nombre d'étudiants (les plus gros d'abord), puis cherche le premier créneau disponible en vérifiant toutes les contraintes en mémoire, sans requête SQL dans la boucle."

---

## 🚀 DÉMONSTRATION EN DIRECT (2 minutes)

**[Écran : Interface de planification]**

> "Passons à la démonstration. Je vais lancer la planification de notre session de 284 examens."

**[Cliquer sur "Lancer la planification"]**

> "Comme vous pouvez le voir, la préparation des examens prend moins d'une seconde.
> La planification automatique est en cours... Et voilà ! 
> **31 secondes** pour planifier 284 examens sans aucun conflit.
> L'objectif de moins de 45 secondes est atteint !"

**[Montrer le calendrier des examens]**

> "Le calendrier affiche tous les examens planifiés. On peut voir qu'aucun vendredi n'est utilisé, que les examens sont bien répartis sur la période."

---

## 📈 PERFORMANCES ET OPTIMISATIONS (1 minute)

**[Écran : Résultats du benchmark]**

> "Pour atteindre ces performances, nous avons appliqué plusieurs optimisations :

> 1. **Migration vers un serveur européen** (Frankfurt) pour réduire la latence depuis l'Algérie
> 2. **Pré-chargement batch** de toutes les données au début (une seule requête)
> 3. **Traitement 100% en mémoire** sans aller-retour à la base pendant le calcul
> 4. **Création groupée** des examens avec des insertions batch

> Le résultat : passage de 464 secondes à 50 secondes, soit une amélioration de **90%**."

---

## 🎯 CONCLUSION (30 secondes)

**[Écran : Dashboard principal avec KPIs]**

> "En résumé, notre plateforme permet de :
> - Gérer 13 000 étudiants et 284 examens
> - Générer un planning optimal en moins de 45 secondes
> - Respecter toutes les contraintes académiques algériennes
> - Offrir une interface adaptée à chaque rôle

> Merci pour votre attention. Je suis disponible pour vos questions."

---

## 📝 NOTES POUR LE PRÉSENTATEUR

### Comptes de démonstration
- **Admin** : admin@univ-alger.dz / admin123
- **Vice-Doyen** : vicedoyen@univ-alger.dz / vicedoyen123
- **Chef Département** : chef.info@univ-alger.dz / chef123

### Points clés à mentionner
- Base hébergée sur Neon (PostgreSQL cloud)
- 11 tables relationnelles
- Contrainte "pas de vendredi" dans le code
- Noms d'étudiants algériens réalistes (Meriem, Youssef, Benali, Mammeri...)

### En cas de question sur les capacités des salles
- Les amphithéâtres ont 300-500 places
- Les salles classiques 60-150 places
- Les salles informatiques 40-80 places
- L'algorithme vérifie `expected_students <= exam_capacity`
