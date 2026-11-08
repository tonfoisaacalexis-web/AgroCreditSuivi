import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(title="AgroCrédit Suivi")

# Base de données temporaire en mémoire locale
base_donnees_epargne = []

class DépôtOrangeMoney(BaseModel):
    amount: float
    transaction_ref: str

# Définition des chemins vers vos fichiers HTML
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
FRONTEND_DIR = os.path.join(PARENT_DIR, "frontend")

# 🌐 1. ADRESSE CLIENT : Accessible sur http://127.0.0
@app.get("/", response_class=HTMLResponse)
def lire_espace_client():
    with open(os.path.join(FRONTEND_DIR, "index.html"), "r", encoding="utf-8") as f:
        return f.read()

# 🌐 2. ADRESSE BANQUE : Accessible sur http://127.0.0admin
@app.get("/admin", response_class=HTMLResponse)
def lire_espace_banque():
    with open(os.path.join(FRONTEND_DIR, "admin.html"), "r", encoding="utf-8") as f:
        return f.read()

# --- CONFIGURATION DES COMMUNICATIONS ---

@app.get("/api/tips/elevage")
def obtenir_conseil():
    return {
        "title": "🌡️ Gestion thermique du poulailler à Ambam",
        "content": "Pendant la saison des pluies dans la Vallée-du-Ntem, préchauffez le poulailler 24h avant l'arrivée des poussins. Utilisez des lampes chauffantes."
    }

@app.post("/api/save/orange")
def enregistrer_epargne(depot: DépôtOrangeMoney):
    if not (15000 <= depot.amount <= 30000):
        raise HTTPException(status_code=400, detail="L'épargne mensuelle doit être comprise entre 15 000 et 30 000 CFA.")
    
    nouvelle_transaction = {"amount": depot.amount, "transaction_ref": depot.transaction_ref.upper()}
    base_donnees_epargne.append(nouvelle_transaction)
    return {"status": "success"}

@app.get("/api/admin/transactions")
def obtenir_toutes_les_transactions():
    return {"transactions": base_donnees_epargne}