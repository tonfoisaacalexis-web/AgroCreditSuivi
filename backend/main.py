import os
import sqlite3
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Importation directe nettoyée
from mdp import AGENCES_AUTORISEES
import remboursement

app = FastAPI(title="AgroCrédit Suivi - Édition Recouvrement")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
FRONTEND_DIR = os.path.join(PARENT_DIR, "frontend")
DB_PATH = os.path.join(CURRENT_DIR, "agrocredit.db")

def initialiser_base_de_donnees():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            filiere TEXT NOT NULL,
            total_epargne INTEGER DEFAULT 0,
            garantie_type TEXT NOT NULL,
            garantie_details TEXT NOT NULL,
            banque_nom TEXT,
            agence_nom TEXT,
            localite TEXT,
            arrondissement TEXT,
            departement TEXT,
            region TEXT,
            date_octroi TEXT
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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS remboursements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT NOT NULL,
            num_echeance INTEGER NOT NULL,
            date_theorique TEXT NOT NULL,
            montant_theorique INTEGER NOT NULL,
            montant_paye INTEGER DEFAULT 0,
            date_paiement TEXT,
            transaction_ref TEXT UNIQUE,
            statut TEXT DEFAULT 'En attente'
        )
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

class DemandeConnexion(BaseModel):
    code_securite: str

class SaisieRemboursement(BaseModel):
    client_id: str
    num_echeance: int
    amount: int
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

# 🔥 RENDRE LA ROUTE DU SERVEUR COMPATIBLE AVEC VOTRE NOUVEAU FICHIER ECHEANCE.HTML
@app.get("/recouvrement", response_class=HTMLResponse)
def lire_espace_remboursement():
    with open(os.path.join(FRONTEND_DIR, "echeance.html"), "r", encoding="utf-8") as f:
        return f.read()
        # 🔥 AJOUTEZ CETTE ROUTE TRÈS COURTE DANS VOTRE MAIN.PY :
@app.get("/recu", response_class=HTMLResponse)
def lire_page_recu():
    with open(os.path.join(FRONTEND_DIR, "recu.html"), "r", encoding="utf-8") as f:
        return f.read()

@app.post("/api/admin/login")
def verifier_code_agence(demande: DemandeConnexion):
    code = demande.code_securite.strip()
    if code not in AGENCES_AUTORISEES:
        raise HTTPException(status_code=401, detail="Code d'agence invalide.")
    return {"status": "success", **AGENCES_AUTORISEES[code]}

@app.post("/api/register")
def inscrire_client(client: ClientRegister):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM clients WHERE LOWER(email) = ? AND LOWER(agence_nom) = ?", (client.email.strip().lower(), client.agence_nom.strip().lower()))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Agriculteur déjà enregistré.")
    date_actuelle = datetime.now().strftime("%Y-%m-%d")
    try:
        cursor.execute("""
            INSERT INTO clients (full_name, email, filiere, total_epargne, garantie_type, garantie_details, banque_nom, agence_nom, localite, arrondissement, departement, region, date_octroi)
            VALUES (?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (client.full_name.strip(), client.email.strip().lower(), client.filiere, client.garantie_type, client.garantie_details.strip(), client.banque_nom, client.agence_nom, client.localite, client.arrondissement, client.departement, client.region, date_actuelle))
        conn.commit()
        nouvel_id = cursor.lastrowid
    except Exception:
        conn.close()
        raise HTTPException(status_code=500, detail="Erreur SQLite.")
    conn.close()
    return {"status": "success", "id": nouvel_id}

@app.post("/api/save/orange")
def enregistrer_epargne(depot: DépôtOrangeMoney):
    if depot.amount < 20000:
        raise HTTPException(status_code=400, detail="Minimum 20 000 CFA.")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT total_epargne FROM clients WHERE id = ?", (depot.user_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Agriculteur introuvable.")
    nouveau_solde = row[0] + int(depot.amount)
    try:
        cursor.execute("INSERT INTO transactions (user_id, amount, transaction_ref) VALUES (?, ?, ?)", (depot.user_id, int(depot.amount), depot.transaction_ref.upper()))
        cursor.execute("UPDATE clients SET total_epargne = ? WHERE id = ?", (nouveau_solde, depot.user_id))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Référence déjà utilisée.")
    conn.close()
    return {"status": "success"}

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
            "id": str(row["id"]), "full_name": row["full_name"], "email": row["email"], "filiere": row["filiere"], "total_epargne": row["total_epargne"], "garantie_type": row["garantie_type"], "garantie_details": row["garantie_details"]
        })
    conn.close()
    return {"clients": comptes}

@app.get("/api/recouvrement/echéancier/{client_id}")
def API_obtenir_calendrier(client_id: str):
    return remboursement.charger_calendrier_recouvrement(client_id, DB_PATH)

# 🔥 Ligne 121 nettoyée et sécurisée ici
@app.post("/api/recouvrement/payer")
def API_encaisser_traite(saisie: SaisieRemboursement):
    return remboursement.encaisser_traite_orange(saisie.client_id, int(saisie.num_echeance), int(saisie.amount), transaction_ref=saisie.transaction_ref, db_path=DB_PATH)

# 🔥 REMPLACEZ TOUTE LA DERNIÈRE FONCTION DANS main.py PAR CELLE-CI :
@app.get("/api/admin/evaluation/{client_id}")
def evaluer_projet_bancable(client_id: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Client introuvable.")
        
    # 🧮 CALCUL DYNAMIQUE ET PROPORTIONNEL DU CRÉDIT LEVIER REEL
    total_brut = row["total_epargne"]
    nombre_tranches = int(total_brut // 20000)
    frais_formation = nombre_tranches * 5000
    epargne_nette = total_brut - frais_formation
    
    # Prise en compte du droit au crédit effectif selon le ratio prudentiel 15% / 85%
    if epargne_nette > 0:
        credit_sollicite = int((epargne_nette / 0.15) * 0.85)
    else:
        credit_sollicite = 0
        
    duree_totale = 12
    mois_grace = 2
    mois_remboursement_effectif = duree_totale - mois_grace
    total_interets = int(credit_sollicite * 0.01 * duree_totale)
    
    if credit_sollicite > 0:
        mensualite_globale = int((credit_sollicite + total_interets) / mois_remboursement_effectif)
    else:
        mensualite_globale = 0
        
    return {
        "client_name": row["full_name"],
        "speculation": row["filiere"],
        "cycle_exploitation": "Selon filière",
        "budget_total_projet": int(credit_sollicite + epargne_nette),
        "apport_epargne_nette": epargne_nette,
        "credit_sollicite_banque": credit_sollicite,  # 👈 DEVIENT PROPORTIONNEL ET DYNAMIQUE
        "chiffre_affaires_prev": int(credit_sollicite * 1.4),
        "charges_exploitation_prev": int(credit_sollicite * 0.35),
        "benefice_net_prev": int(credit_sollicite * 0.05),
        "garantie_type": row["garantie_type"],
        "garantie_details": row["garantie_details"],
        "statut_projet": "BANCABLE & SÉCURISÉ",
        "duree_mois": duree_totale,
        "differe_mois": mois_grace,
        "mensualite": mensualite_globale,
        "total_interets": total_interets,
        "taux_annuel": "12%",
        "banque_nom": row["banque_nom"],
        "agence_nom": row["agence_nom"],
        "localite": row["localite"]
    }