import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="AgroCrédit Suivi")

# Bases de données temporaires en mémoire locale
base_donnees_clients = [
    {"id": "1", "full_name": "Jean Du Terrain", "email": "jean@terrain.cm", "filiere": "Poulet de chair", "total_epargne": 20000, "garantie_type": "Caution Fonctionnaire", "garantie_details": "Aval de M. Ndong, Enseignant au Lycée (Matricule X-123)"}
]
base_donnees_epargne = [
    {"user_id": "1", "amount": 20000, "transaction_ref": "699418222"}
]

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

# Configuration des chemins vers le dossier frontend
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
FRONTEND_DIR = os.path.join(PARENT_DIR, "frontend")

# 📂 CONFIGURATION CRUCIALE : Autoriser FastAPI à servir le fichier style.css et les fichiers JS
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# 🌐 1. ADRESSE CLIENT : Accessible sur la racine du serveur
@app.get("/", response_class=HTMLResponse)
def lire_espace_client():
    with open(os.path.join(FRONTEND_DIR, "index.html"), "r", encoding="utf-8") as f:
        return f.read()

# 🌐 2. ADRESSE BANQUE : Accessible sur /admin
@app.get("/admin", response_class=HTMLResponse)
def lire_espace_banque():
    with open(os.path.join(FRONTEND_DIR, "admin.html"), "r", encoding="utf-8") as f:
        return f.read()

# --- ROUTES API ---

@app.get("/api/tips/elevage")
def obtenir_conseil():
    return {
        "title": "🌡️ Gestion thermique du poulailler à Ambam",
        "content": "Pendant la saison des pluies dans la Vallée-du-Ntem, préchauffez le poulailler 24h avant l'arrivée des poussins. Utilisez des lampes chauffantes."
    }

# 🔥 REMPLACEZ LA ROUTE POST /api/register PAR CETTE VERSION ULTRA-STABLE :
@app.post("/api/register")
def inscrire_client(client: ClientRegister):
    nouvel_id = str(len(base_donnees_clients) + 1)
    nouveau_client = {
        "id": nouvel_id,
        "full_name": client.full_name,
        "email": client.email,
        "filiere": client.filiere,
        "total_epargne": 0,
        "garantie_type": client.garantie_type,
        "garantie_details": client.garantie_details
    }
    base_donnees_clients.append(nouveau_client)
    return {"status": "success", "message": "Client enregistré", "client": nouveau_client}

@app.post("/api/save/orange")
def enregistrer_epargne(depot: DépôtOrangeMoney):
    if depot.amount < 20000:
        raise HTTPException(status_code=400, detail="L'épargne mensuelle doit être d'au moins 20 000 CFA.")
    
    for client in base_donnees_clients:
        if client["id"] == depot.user_id:
            client["total_epargne"] += depot.amount
            break

    base_donnees_epargne.append({
        "user_id": depot.user_id,
        "amount": depot.amount,
        "transaction_ref": depot.transaction_ref.upper()
    })
    return {"status": "success"}

@app.get("/api/admin/clients")
def obtenir_tous_les_clients():
    return {"clients": base_donnees_clients}

@app.get("/api/admin/evaluation/{client_id}")
def evaluer_projet_bancable(client_id: str):
    # Données techniques : investissement constant à 1 000 000 CFA (150k apport + 850k crédit)
    # Droit au crédit fixe à 850 000 CFA pour le levier visé en fin de cycle de 10 mois
    modeles_rentabilite = {
        "Poulet de chair": {"cycle": "45 jours", "invest": 1000000, "ca": 1400000, "charges": 350000, "duree_remboursement_mois": 3},
        "Porc engraisseur": {"cycle": "6 mois", "invest": 1000000, "ca": 1500000, "charges": 450000, "duree_remboursement_mois": 6},
        "Pisciculture": {"cycle": "6 mois", "invest": 1000000, "ca": 1600000, "charges": 500000, "duree_remboursement_mois": 6},
        "Maïs": {"cycle": "4 mois", "invest": 1000000, "ca": 1350000, "charges": 300000, "duree_remboursement_mois": 4},
        "Bananier plantain": {"cycle": "En production", "invest": 1000000, "ca": 1700000, "charges": 400000, "duree_remboursement_mois": 12},
        "Cacao": {"cycle": "Entretien/Production", "invest": 1000000, "ca": 1800000, "charges": 450000, "duree_remboursement_mois": 12},
        "Manioc": {"cycle": "Transformation", "invest": 1000000, "ca": 1500000, "charges": 350000, "duree_remboursement_mois": 6}
    }

    client_cible = next((c for c in base_donnees_clients if c["id"] == client_id), None)
    if not client_cible:
        raise HTTPException(status_code=404, detail="Client introuvable.")

    speculation = client_cible["filiere"]
    modele = modeles_rentabilite.get(speculation, {"cycle": "Indéfini", "invest": 1000000, "ca": 1300000, "charges": 400000, "duree_remboursement_mois": 6})
    
    # 📊 CALCULS AMORTISSEMENT CRÉDIT (850 000 CFA constant à terme)
    credit_sollicite = 850000
    taux_interet_mensuel = 0.01  # 1% par mois (12% par an)
    duree = modele["duree_remboursement_mois"]
    
    # Formule standard COBAC pour traite mensuelle constante (Amortissement lissé)
    mensualite_globale = math.floor((credit_sollicite * taux_interet_mensuel) / (1 - (1 + taux_interet_mensuel) ** (-duree)))
    total_interets = (mensualite_globale * duree) - credit_sollicite

    # Prévisions d'exploitation du projet
    benefice_brut_activite = modele["ca"] - modele["charges"] - modele["invest"]
    
    return {
        "client_name": client_cible["full_name"],
        "speculation": speculation,
        "cycle_exploitation": modele["cycle"],
        "budget_total_projet": modele["invest"],
        "apport_epargne_nette": 150000,
        "credit_sollicite_banque": credit_sollicite,
        "chiffre_affaires_prev": modele["ca"],
        "charges_exploitation_prev": modele["charges"],
        "benefice_net_prev": benefice_brut_activite,
        "garantie_type": client_cible["garantie_type"],
        "garantie_details": client_cible["garantie_details"],
        "statut_projet": "BANCABLE & SÉCURISÉ",
        # Variables de remboursement transmises
        "duree_mois": duree,
        "mensualite": mensualite_globale,
        "total_interets": total_interets,
        "taux_annuel": "12%"
    }