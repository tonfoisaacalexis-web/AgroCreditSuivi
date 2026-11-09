import os
import math
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="AgroCrédit Suivi")

# Récupération sécurisée des clés d'accès Supabase PostgreSQL configurées sur Render
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# En-têtes obligatoires pour interagir avec l'API REST sécurisée de Supabase
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

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

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
FRONTEND_DIR = os.path.join(PARENT_DIR, "frontend")

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

# 👤 INSCRIPTION : Insertion directe dans la table PostgreSQL
@app.post("/api/register")
def inscrire_client(client: ClientRegister):
    url = f"{SUPABASE_URL}/rest/v1/clients"
    donnees = {
        "full_name": client.full_name,
        "email": client.email,
        "filiere": client.filiere,
        "total_epargne": 0,
        "garantie_type": client.garantie_type,
        "garantie_details": client.garantie_details
    }
    response = requests.post(url, headers=HEADERS, json=donnees)
    if response.status_code != 201:
        raise HTTPException(status_code=500, detail="Échec de l'enregistrement dans Supabase.")
    return {"status": "success", "client": response.json()}

# 💰 VERSEMENT : Extraction de l'index [0] sécurisée pour corriger le crash Failed
@app.post("/api/save/orange")
def enregistrer_epargne(depot: DépôtOrangeMoney):
    if depot.amount < 20000:
        raise HTTPException(status_code=400, detail="L'épargne mensuelle doit être d'au moins 20 000 CFA.")
    
    try:
        user_id_num = int(depot.user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="L'identifiant de l'agriculteur doit être un nombre valide.")

    url_client = f"{SUPABASE_URL}/rest/v1/clients?id=eq.{user_id_num}"
    res_client = requests.get(url_client, headers=HEADERS)
    
    res_json = res_client.json()
    if res_client.status_code != 200 or not res_json or len(res_json) == 0:
        raise HTTPException(status_code=404, detail="Agriculteur introuvable dans la base PostgreSQL.")
    
    # Extraction sécurisée du dictionnaire dans le tableau JSON
    client_data = res_json[0]
    nouveau_solde = int(client_data["total_epargne"]) + depot.amount

    res_patch = requests.patch(url_client, headers=HEADERS, json={"total_epargne": nouveau_solde})
    if res_patch.status_code != 200 and res_patch.status_code != 204:
        raise HTTPException(status_code=500, detail="Échec de la mise à jour du solde d'épargne.")

    url_tx = f"{SUPABASE_URL}/rest/v1/transactions"
    requests.post(url_tx, headers=HEADERS, json={
        "user_id": str(user_id_num),
        "amount": depot.amount,
        "transaction_ref": depot.transaction_ref.upper()
    })
    return {"status": "success"}

# 🏦 PORTFEUILLE : Liste globale
@app.get("/api/admin/clients")
def obtenir_tous_les_clients():
    url = f"{SUPABASE_URL}/rest/v1/clients?select=*"
    response = requests.get(url, headers=HEADERS)
    return {"clients": response.json() if response.status_code == 200 else []}

# 📊 EVALUATION AUTOMATIQUE SÉCURISÉE
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
    url = f"{SUPABASE_URL}/rest/v1/clients?id=eq.{client_id}"
    res = requests.get(url, headers=HEADERS)
    
    res_json = res.json()
    if res.status_code != 200 or not res_json or len(res_json) == 0:
        raise HTTPException(status_code=404, detail="Client introuvable.")
    
    client_cible = res_json[0]
    modele = modeles_rentabilite.get(client_cible["filiere"], {"cycle": "Indéfini", "invest": 1000000, "ca": 1400000, "charges": 350000})
    
    credit_sollicite = 850000
    duree_totale = 12
    mois_differe = 2
    mois_remboursement_effectif = duree_totale - mois_differe
    total_interets = int(credit_sollicite * 0.01 * duree_totale)
    mensualite_globale = int((credit_sollicite + total_interets) / mois_remboursement_effectif)

    return {
        "client_name": client_cible["full_name"],
        "speculation": client_cible["filiere"],
        "cycle_exploitation": modele["cycle"],
        "budget_total_projet": 1000000,
        "apport_epargne_nette": 150000,
        "credit_sollicite_banque": credit_sollicite,
        "chiffre_affaires_prev": modele["ca"],
        "charges_exploitation_prev": modele["charges"],
        "benefice_net_prev": modele["ca"] - modele["charges"] - 1000000,
        "garantie_type": client_cible["garantie_type"],
        "garantie_details": client_cible["garantie_details"],
        "statut_projet": "BANCABLE & SÉCURISÉ",
        "duree_mois": duree_totale,
        "differe_mois": mois_differe,
        "mensualite": mensualite_globale,
        "total_interets": total_interets,
        "taux_annuel": "12%"
    }