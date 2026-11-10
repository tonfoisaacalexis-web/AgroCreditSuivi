import sqlite3
from fastapi import HTTPException
from pydantic import BaseModel

class NouveauCours(BaseModel):
    cle: str
    titre: str
    description: str
    contenu: str

def initialiser_base_academie(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Table des cours dynamiques de l'Académie
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cours_academie (
            cle TEXT PRIMARY KEY,
            titre TEXT NOT NULL,
            description TEXT NOT NULL,
            contenu TEXT NOT NULL
        )
    """)
    
    # Insertion des 4 cours d'origine si la table est vierge
    cursor.execute("SELECT COUNT(*) FROM cours_academie")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
            INSERT INTO cours_academie (cle, titre, description, contenu)
            VALUES (?, ?, ?, ?)
        """, [
            ("poulet", "🌡️ Poulet de Chair : Chauffage", "Gestion de la température du poulailler en saison des pluies à Ambam.", "En saison des pluies à Ambam, préchauffez le bâtiment 24 heures avant l'arrivée des poussins. Maintenez 35°C en Semaine 1, puis descendez de 2°C par semaine. Utilisez des lampes chauffantes."),
            ("peste", "🐖 Porc : Prévention de la Peste", "Mesures d'étanchéité sanitaire et biosécurité des bâtiments d'engraissement.", "La peste porcine africaine est virulente dans le Sud. Interdiction totale d'accès aux personnes étrangères. Installez un bac de désinfection avec de la chaux vive à l'entrée de chaque loge."),
            ("pisciculture", "🐟 Pisciculture : Qualité de l'Eau", "Contrôle du pH et renouvellement de l'eau des étangs d'Olamze.", "Suivi de l'oxygénation : observez les poissons à l'aube. S'ils pipent en surface, l'eau manque d'oxygène. Changez 10% du volume d'eau tous les 15 jours."),
            ("mais", "🌽 Maïs : Calendrier des Semis", "Optimisation des rendements en fonction des précipitations du Sud.", "Semis : écartement strict de 75 cm entre les lignes et 25 cm entre les poquets. Apport de NPK (20-10-10) au 14ème jour après la levée. Premier sarclage impératif avant l'engrais.")
        ])
    conn.commit()
    conn.close()

def ajouter_nouveau_cours(cours: NouveauCours, db_path: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO cours_academie (cle, titre, description, contenu)
            VALUES (?, ?, ?, ?)
        """, (cours.cle.strip().lower(), cours.titre.strip(), cours.description.strip(), cours.contenu.strip()))
        conn.commit()
    except Exception:
        conn.close()
        raise HTTPException(status_code=500, detail="Erreur d'écriture SQLite Académie.")
    conn.close()
    return {"status": "success"}

def lister_tous_les_cours(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cours_academie")
    rows = cursor.fetchall()
    conn.close()
    
    cours_list = {}
    for row in rows:
        cours_list[row["cle"]] = {
            "titre": row["titre"],
            "description": row["description"],
            "contenu": row["contenu"]
        }
    return cours_list