import sqlite3
from datetime import datetime
from fastapi import HTTPException

# 📊 GÉNÉRATION DYNAMIQUE DU CALENDRIER MOIS PAR MOIS SUR LE CRÉDIT EFFECTIF
def charger_calendrier_recouvrement(client_id: str, db_path: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Récupérer les informations de l'agriculteur et son épargne réelle
    cursor.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
    client = cursor.fetchone()
    if not client:
        conn.close()
        raise HTTPException(status_code=404, detail="Agriculteur introuvable.")
        
    # 2. Vérifier si l'échéancier existe déjà pour ce client
    cursor.execute("SELECT * FROM remboursements WHERE client_id = ? ORDER BY num_echeance ASC", (client_id,))
    ech_existants = cursor.fetchall()
    
    if len(ech_existants) == 0:
        # 🧮 CALCULS FINANCIERS PROPORTIONNELS EN DIRECT
        total_brut = client["total_epargne"]
        nombre_tranches = Math.floor(total_brut / 20000) if hasattr(client, 'total_epargne') else int(total_brut // 20000)
        
        # Déduction automatique des frais d'encadrement terrain (5 000 CFA par mois)
        frais_formation = nombre_tranches * 5000
        epargne_nette = total_brut - frais_formation
        
        # Droit au Crédit Effectif Alloué (Ratio Prudentiel : 15% Apport / 85% Levier)
        if epargneNette > 0:
            credit_effectif = int((epargne_nette / 0.15) * 0.85)
        else:
            credit_effectif = 0
            
        # Paramètres financiers COBAC (12% annuel lissé sur 12 mois)
        duree_totale = 12
        mois_grace = 2
        mois_remboursement_effectif = duree_totale - mois_grace
        
        # Calcul du coût des intérêts sur le crédit effectif alloué
        total_interets = int(credit_effectif * 0.01 * duree_totale)
        
        # Calcul de la traite mensuelle dynamique proportionnelle
        if credit_effectif > 0:
            traite_mensuelle_dynamique = int((credit_effectif + total_interets) / mois_remboursement_effectif)
        else:
            traite_mensuelle_dynamique = 0
            
        # Enregistrement du calendrier mois par mois
        date_depart = datetime.strptime(client["date_octroi"] or datetime.now().strftime("%Y-%m-%d"), "%Y-%m-%d")
        
        for mois in range(1, 13):
            annee_echeance = date_depart.year + (date_depart.month + mois - 1) // 12
            mois_echeance = (date_depart.month + mois - 1) % 12 + 1
            date_echeance_str = f"{annee_echeance}-{mois_echeance:02d}-{date_depart.day:02d}"
            
            # Application de la grâce : Mois 1 et Mois 2 = 0 CFA
            montant_du = 0 if mois <= 2 else traite_mensuelle_dynamique
            statut_initial = "Période de grâce" if mois <= 2 else "En attente"
            
            cursor.execute("""
                INSERT INTO remboursements (client_id, num_echeance, date_theorique, montant_theorique, montant_paye, statut)
                VALUES (?, ?, ?, ?, 0, ?)
            """, (client_id, mois, date_echeance_str, montant_du, statut_initial))
            
        conn.commit()
        cursor.execute("SELECT * FROM remboursements WHERE client_id = ? ORDER BY num_echeance ASC", (client_id,))
        ech_existants = cursor.fetchall()

    liste_echeances = list()
    for row in ech_existants:
        liste_echeances.append({
            "num_echeance": row["num_echeance"],
            "date_theorique": row["date_theorique"],
            "montant_theorique": row["montant_theorique"],
            "montant_paye": row["montant_paye"],
            "date_paiement": row["date_paiement"],
            "transaction_ref": row["transaction_ref"],
            "statut": row["statut"]
        })
    conn.close()
    return {"client_name": client["full_name"], "filiere": client["filiere"], "echeances": liste_echeances}

# 💸 ENCAISSEMENT D'UNE TRAITE PAR TRANSFERT ORANGE MONEY (Inchangé)
def encaisser_traite_orange(client_id: str, num_echeance: int, amount: int, transaction_ref: str, db_path: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    date_paiement_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    try:
        cursor.execute("""
            UPDATE remboursements 
            SET montant_paye = ?, date_paiement = ?, transaction_ref = ?, statut = 'Payé'
            WHERE client_id = ? AND num_echeance = ?
        """, (amount, date_paiement_str, transaction_ref.upper(), client_id, num_echeance))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Cette référence Orange Money a déjà été validée pour une autre traite.")
    conn.close()
    return {"status": "success"}