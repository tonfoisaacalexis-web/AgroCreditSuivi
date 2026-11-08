from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="AgroCrédit Suivi")

# Autoriser la communication locale avec le fichier HTML
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base de données temporaire en mémoire locale
base_donnees_epargne = []

# Modèle de validation pour la transaction Orange Money
class DépôtOrangeMoney(BaseModel):
    amount: float
    transaction_ref: str

@app.get("/")
def home():
    return {"status": "Opérationnel", "service": "AgroCrédit Suivi local"}

# 🚜 Route pour envoyer le conseil agropastoral
@app.get("/api/tips/elevage")
def obtenir_conseil():
    return {
        "title": "🌡️ Gestion thermique du poulailler à Ambam",
        "content": "Pendant la saison des pluies dans la Vallée-du-Ntem, préchauffez le poulailler 24h avant l'arrivée des poussins. Utilisez des lampes chauffantes pour maintenir une température stable de 32°C à 35°C la première semaine."
    }

# 💰 Route pour enregistrer le versement Orange Money
@app.post("/api/save/orange")
def enregistrer_epargne(depot: DépôtOrangeMoney):
    # Application stricte de votre règle (15 000 à 30 000 CFA)
    if not (15000 <= depot.amount <= 30000):
        raise HTTPException(status_code=400, detail="L'épargne mensuelle doit être comprise entre 15 000 et 30 000 CFA.")
    
    # Vérification si la référence SMS existe déjà
    for transaction in base_donnees_epargne:
        if transaction["transaction_ref"] == depot.transaction_ref.upper():
            raise HTTPException(status_code=400, detail="Cette référence de transaction Orange Money a déjà été utilisée.")
    
    # Sauvegarde locale
    nouvelle_transaction = {
        "amount": depot.amount,
        "transaction_ref": depot.transaction_ref.upper()
    }
    base_donnees_epargne.append(nouvelle_transaction)
    
    return {"status": "success", "message": "Dépôt enregistré avec succès en local"}