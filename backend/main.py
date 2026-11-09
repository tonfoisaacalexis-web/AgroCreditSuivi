import os
import sqlite3
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="AgroCrédit Suivi - Édition Universelle")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
FRONTEND_DIR = os.path.join(PARENT_DIR, "frontend")
DB_PATH = os.path.join(CURRENT_DIR, "agrocredit.db")

# 🐘 EVOLUTION DE LA BASE DE DONNÉES EN VERSION MULTI-AGENCES
def initialiser_base_de_donnees():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Table des clients avec traçabilité de l'institution et de l'agence
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            filiere TEXT NOT NULL,
            total_epargne INTEGER DEFAULT 0,
            garantie_type TEXT NOT NULL,
            garantie_details TEXT NOT NULL,
            banque_nom TEXT DEFAULT 'La Régionale',
            agence_nom TEXT DEFAULT 'Ambam',
            localite TEXT DEFAULT 'Ambam',
            arrondissement TEXT DEFAULT 'Ambam',
            departement TEXT DEFAULT 'Vallée-du-Ntem',
            region TEXT DEFAULT 'Sud'
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            amount INTEGER NOT NULL,
            transaction_ref TEXT NOT NULL UNIQUE
        )
    """)
    
    # Insertion du profil de test originel lié par défaut à Ambam
    cursor.execute("SELECT COUNT(*) FROM clients")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO clients (full_name, email, filiere, total_epargne, garantie_type, garantie_details, banque_nom, agence_nom, localite, arrondissement, departement, region)
            VALUES ('Jean Du Terrain', 'jean@terrain.cm', 'Poulet de chair', 40000, 'Caution Fonctionnaire', 'Aval de M. Ndong, Enseignant au Lycée (Matricule X-123)', 'La Régionale', 'Ambam', 'Ambam', 'Ambam', 'Vallée-du-Ntem', 'Sud')
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
    banque_nom: str
    agence_nom: str
    localite: str
    arrondissement: str
    departement: str
    region: str

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

# 👤 INSCRIPTION : Liaison explicite avec la banque et l'agence émettrice
@app.post("/api/register")
def inscrire_client(client: ClientRegister):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Sécurité anti-doublon par e-mail au sein d'une même agence
    cursor.execute("SELECT id FROM clients WHERE LOWER(email) = ? AND LOWER(agence_nom) = ?", (client.email.strip().lower(), client.agence_nom.strip().lower()))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Cet agriculteur est déjà enregistré dans cette agence.")
        
    try:
        cursor.execute("""
            INSERT INTO clients (full_name, email, filiere, total_epargne, garantie_type, garantie_details, banque_nom, agence_nom, localite, arrondissement, departement, region)
            VALUES (?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (client.full_name.strip(), client.email.strip().lower(), client.filiere, client.garantie_type, client.garantie_details.strip(), client.banque_nom, client.agence_nom, client.localite, client.arrondissement, client.departement, client.region))
        conn.commit()
        nouvel_id = cursor.lastrowid
    except Exception:
        conn.close()
        raise HTTPException(status_code=500, detail="Erreur d'écriture SQLite.")
    conn.close()
    return {"status": "success", "id": nouvel_id}

@app.post("/api/save/orange")
def enregistrer_epargne(depot: DépôtOrangeMoney):
    if depot.amount < 20000:
        raise HTTPException(status_code=400, detail="L'épargne mensuelle doit être d'au moins 20 000 CFA.")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT total_epargne FROM clients WHERE id = ?", (depot.user_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Agriculteur introuvable.")
    nouveau_solde = row[0] + int(depot.amount)
    try:
        cursor.execute("INSERT INTO transactions (user_id, amount, transaction_ref) VALUES (?, ?, ?)",
                       (depot.user_id, int(depot.amount), depot.transaction_ref.upper()))
        cursor.execute("UPDATE clients SET total_epargne = ? WHERE id = ?", (nouveau_solde, depot.user_id))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Référence Orange Money déjà utilisée.")
    except Exception:
        conn.close()
        raise HTTPException(status_code=500, detail="Erreur système.")
    conn.close()
    return {"status": "success"}

# 🏦 PORTFEUILLE FILTRÉ : Renvoie exclusivement les clients de la banque et de l'agence sélectionnée
@app.get("/api/admin/clients")
def obtenir_tous_les_clients(banque: str = "La Régionale", agence: str = "Ambam"):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clients WHERE banque_nom = ? AND agence_nom = ?", (banque, agence))
    rows = cursor.fetchall()
    comptes = list()
    for row in rows:
        comptes.append({
            "id": str(row["id"]),
            "full_name": row["full_name"],
            "email": row["email"],
            "filiere": row["filiere"],
            "total_epargne": row["total_epargne"],
            "garantie_type": row["garantie_type"],
            "garantie_details": row["garantie_details"]
        })
    conn.close()
    return {"clients": comptes}

# 📊 EVALUATION FINANCIÈRE RECALCULÉE AVEC LES 2 MOIS DE GRÂCE COBAC
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
        raise HTTPException(status_code=404, detail="Client introuvable.")
        
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
        "taux_annuel": "12%",
        "banque_nom": row["banque_nom"],
        "agence_nom": row["agence_nom"],
        "localite": row["localite"]
    }