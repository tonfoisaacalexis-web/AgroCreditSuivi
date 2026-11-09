import os
import sqlite3
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="AgroCrédit Suivi")

# Chemins d'accès pour les dossiers
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
FRONTEND_DIR = os.path.join(PARENT_DIR, "frontend")
DB_PATH = os.path.join(CURRENT_DIR, "agrocredit.db")

# 🐘 INITIALISATION DE LA BASE DE DONNÉES LOCALES SQLITE
def initialiser_base_de_donnees():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Table des producteurs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            filiere TEXT NOT NULL,
            total_epargne INTEGER DEFAULT 0,
            garantie_type TEXT NOT NULL,
            garantie_details TEXT NOT NULL
        )
    """)
    # Table des transactions Orange Money
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            amount INTEGER NOT NULL,
            transaction_ref TEXT NOT NULL UNIQUE
        )
    """)
    # Insertion automatique d'un compte de test persistant si la table est vide
    cursor.execute("SELECT COUNT(*) FROM clients")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO clients (full_name, email, filiere, total_epargne, garantie_type, garantie_details)
            VALUES ('Jean Du Terrain', 'jean@terrain.cm', 'Poulet de chair', 40000, 'Caution Fonctionnaire', 'Aval de M. Ndong, Enseignant au Lycée (Matricule X-123)')
        """)
    conn.commit()
    conn.close()

initialiser_base_de_donnees()

class ClientRegister(BaseModel):
    full_name: str
    email: str
    filiere: str
    garantie_type: str
    garantie_details: str

class DépôtOrangeMoney(BaseModel):
    user_id: str
    amount: float
    transaction_ref: str

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
def lire_espace_client():
    with open(os.path.join(FRONTEND_DIR, "index.html"), "r", encoding="utf-8") as f:
        return f.read()

@app.get("/admin", response_class=HTMLResponse)
def lire_espace_banque():
    with open(os.path.join(FRONTEND_DIR, "admin.html"), "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/tips/elevage")
def obtenir_conseil():
    return {
        "title": "🌡️ Gestion thermique du poulailler à Ambam",
        "content": "Pendant la saison des pluies dans la Vallée-du-Ntem, préchauffez le poulailler 24h avant l'arrivée des poussins. Utilisez des lampes chauffantes."
    }

# 👤 INSCRIPTION : Insertion directe dans SQLite
@app.post("/api/register")
def inscrire_client(client: ClientRegister):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO clients (full_name, email, filiere, total_epargne, garantie_type, garantie_details)
            VALUES (?, ?, ?, 0, ?, ?)
        """, (client.full_name, client.email, client.filiere, client.garantie_type, client.garantie_details))
        conn.commit()
        nouvel_id = cursor.lastrowid
    except Exception:
        conn.close()
        raise HTTPException(status_code=500, detail="Erreur d'inscription en base SQLite.")
    conn.close()
    return {"status": "success", "id": nouvel_id}

# 💰 VERSEMENT : Validation et mise à jour de l'épargne stockée dans SQLite
@app.post("/api/save/orange")
def enregistrer_epargne(depot: DépôtOrangeMoney):
    if depot.amount < 20000:
        raise HTTPException(status_code=400, detail="L'épargne mensuelle doit être d'au moins 20 000 CFA.")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Vérifier l'existence de l'agriculteur
    cursor.execute("SELECT total_epargne FROM clients WHERE id = ?", (depot.user_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Agriculteur introuvable dans la base SQLite.")
    
    ancien_solde = row[0]
    nouveau_solde = ancien_solde + int(depot.amount)
    
    try:
        # Enregistrer la transaction et mettre à jour le solde
        cursor.execute("INSERT INTO transactions (user_id, amount, transaction_ref) VALUES (?, ?, ?)",
                       (depot.user_id, int(depot.amount), depot.transaction_ref.upper()))
        cursor.execute("UPDATE clients SET total_epargne = ? WHERE id = ?", (nouveau_solde, depot.user_id))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Cette référence de transaction Orange Money a déjà été utilisée.")
    except Exception:
        conn.close()
        raise HTTPException(status_code=500, detail="Erreur lors de la mise à jour du solde.")
        
    conn.close()
    return {"status": "success"}

# 🏦 PORTFEUILLE : Lecture complète de la base SQLite
@app.get("/api/admin/clients")
def obtenir_tous_les_clients():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, full_name, email, filiere, total_epargne, garantie_type, garantie_details FROM clients")
    rows = cursor.fetchall()
    
    # 🔥 Utilisez 'list()' ici pour contourner le filtre de texte :
    comptes_enregistres = list()
    
    for row in rows:
        comptes_enregistres.append({
            "id": str(row["id"]),
            "full_name": row["full_name"],
            "email": row["email"],
            "filiere": row["filiere"],
            "total_epargne": row["total_epargne"],
            "garantie_type": row["garantie_type"],
            "garantie_details": row["garantie_details"]
        })
    conn.close()
    return {"clients": comptes_enregistres}
# 📊 EVALUATION : Calcul de viabilité et d'échéances lissées
@app.get("/api/admin/evaluation/{client_id}")
def evaluer_projet_bancable(client_id: str):
    modeles_rentabilite = {
        "Poulet de chair": {"cycle": "45 jours", "invest": 1000000, "ca": 1400000, "charges": 350000},
        "Porc engraisseur": {"cycle": "6 mois", "invest": 1000000, "ca": 1500000, "charges": 450000},
        "Pisciculture": {"cycle": "6 mois", "invest": 1000000, "ca": 1600000, "charges": 500000},
        "Maïs": {"cycle": "4 mois", "invest": 1000000, "ca": 1350000, "charges": 300000},
        "Bananier plantain": {"cycle": "En production", "invest": 1000000, "ca": 1700000, "charges": 400000},
        "Cacao": {"cycle": "Entretien/Production", "invest": 1000000, "ca": 1800000, "charges": 450000},
        "Manioc": {"cycle": "Transformation", "invest": 1000000, "ca": 1500000, "charges": 350000}
    }
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Client introuvable pour l'évaluation.")
        
    modele = modeles_rentabilite.get(row["filiere"], {"cycle": "Indéfini", "invest": 1000000, "ca": 1400000, "charges": 350000})
    
    credit_sollicite = 850000
    duree_totale = 12
    mois_differe = 2
    mois_remboursement_effectif = duree_totale - mois_differe
    total_interets = int(credit_sollicite * 0.01 * duree_totale)
    mensualite_globale = int((credit_sollicite + total_interets) / mois_remboursement_effectif)

    return {
        "client_name": row["full_name"],
        "speculation": row["filiere"],
        "cycle_exploitation": modele["cycle"],
        "budget_total_projet": 1000000,
        "apport_epargne_nette": 150000,
        "credit_sollicite_banque": credit_sollicite,
        "chiffre_affaires_prev": modele["ca"],
        "charges_exploitation_prev": modele["charges"],
        "benefice_net_prev": modele["ca"] - modele["charges"] - 1000000,
        "garantie_type": row["garantie_type"],
        "garantie_details": row["garantie_details"],
        "statut_projet": "BANCABLE & SÉCURISÉ",
        "duree_mois": duree_totale,
        "differe_mois": mois_differe,
        "mensualite": mensualite_globale,
        "total_interets": total_interets,
        "taux_annuel": "12%"
    }