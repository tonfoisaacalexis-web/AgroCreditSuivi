import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(title="AgroCrédit Suivi")

# Bases de données temporaires en mémoire locale
base_donnees_clients = [
    {"id": "1", "full_name": "Jean Du Terrain", "email": "jean@terrain.cm", "filiere": "Élevage", "total_epargne": 20000}
]
base_donnees_epargne = [
    {"user_id": "1", "amount": 20000, "transaction_ref": "699418222"}
]

class ClientRegister(BaseModel):
    full_name: str
    email: str
    filiere: str

class DépôtOrangeMoney(BaseModel):
    user_id: str
    amount: float
    transaction_ref: str

# Chemins des fichiers HTML
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
FRONTEND_DIR = os.path.join(PARENT_DIR, "frontend")

@app.get("/", response_class=HTMLResponse)
def lire_espace_client():
    with open(os.path.join(FRONTEND_DIR, "index.html"), "r", encoding="utf-8") as f:
        return f.read()

@app.get("/admin", response_class=HTMLResponse)
def lire_espace_banque():
    with open(os.path.join(FRONTEND_DIR, "admin.html"), "r", encoding="utf-8") as f:
        return f.read()

# 🚜 Route API : Charger le conseil agropastoral
@app.get("/api/tips/elevage")
def obtenir_conseil():
    return {
        "title": "🌡️ Gestion thermique du poulailler à Ambam",
        "content": "Pendant la saison des pluies dans la Vallée-du-Ntem, préchauffez le poulailler 24h avant l'arrivée des poussins. Utilisez des lampes chauffantes."
    }

# 👤 Route API : Inscrire un nouvel agriculteur
@app.post("/api/register")
def inscrire_client(client: ClientRegister):
    nouvel_id = str(len(base_donnees_clients) + 1)
    nouveau_client = {
        "id": nouvel_id,
        "full_name": client.full_name,
        "email": client.email,
        "filiere": client.filiere,
        "total_epargne": 0
    }
    base_donnees_clients.append(nouveau_client)
    return {"status": "success", "message": "Agriculteur inscrit avec succès", "client": nouveau_client}

# 💰 Route API : Enregistrer un versement Orange Money
# Dans backend/main.py, modifiez les routes de calcul ou d'affichage

# Nouvelle règle de validation : Minimum 20 000 FCFA / mois
@app.post("/api/save/orange")
def enregistrer_epargne(depot: DépôtOrangeMoney):
    # Changement du seuil minimal à 20 000 CFA selon vos nouvelles directives
    if depot.amount < 20000:
        raise HTTPException(status_code=400, detail="Le montant minimum d'épargne mensuel est de 20 000 CFA.")
    
    # ... (reste du code d'enregistrement inchangé)
    
    # Trouver le client et ajouter le montant
    client_trouve = False
    for client in base_donnees_clients:
        if client["id"] == depot.user_id:
            client["total_epargne"] += depot.amount
            client_trouve = True
            break
            
    if not client_trouve:
        raise HTTPException(status_code=404, detail="Agriculteur introuvable.")

    base_donnees_epargne.append({
        "user_id": depot.user_id,
        "amount": depot.amount,
        "transaction_ref": depot.transaction_ref.upper()
    })
    return {"status": "success"}

# 🏦 Route API : Permettre à la banque de lister tous les clients et leurs calculs de crédit
@app.get("/api/admin/clients")
def obtenir_tous_les_clients():
    return {"clients": base_donnees_clients}