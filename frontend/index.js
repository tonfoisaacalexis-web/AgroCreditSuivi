let totalEpargne = 0;
const serverUrl = ""; // Utilise automatiquement l'adresse actuelle du serveur

// 1. Charger automatiquement le conseil agropastoral actif depuis Python
async function chargerConseilAgro() {
    const tipsBox = document.getElementById('agro-tips-box');
    try {
        const response = await fetch(serverUrl + "/api/tips/elevage");
        const data = await response.json();
        
        tipsBox.innerHTML = `
            <div class="tip-box">
                <strong style="display: block; margin-bottom: 5px;">` + data.title + `</strong>
                ` + data.content + `
            </div>
        `;
    } catch (error) {
        tipsBox.innerHTML = '<p style="font-size: 12px; color: #b91c1c; font-weight: bold;">⚠️ Le moteur en ligne ne répond pas. Vérifiez le statut Render.</p>';
    }
}

// 🔥 REMPLACEZ LA FONCTION effectuerVersement DANS index.js PAR CETTE VERSION DYNAMIQUE :
async function effectuerVersement() {
    const amountInput = document.getElementById('saving-amount');
    const refInput = document.getElementById('transaction-ref');
    const errorBox = document.getElementById('error-message');
    
    // Ajoutez temporairement une invite de texte pour demander l'ID PostgreSQL ou créez un champ input id="client-id" dans index.html
    const prodUserId = prompt("Veuillez saisir votre Identifiant Unique d'Agriculteur (Ex: 1, 2, 3...) :"); 
    
    const amount = parseInt(amountInput.value);
    const ref = refInput.value.trim();

    if (!prodUserId) {
        alert("⚠️ Action requise : Vous devez renseigner votre ID pour valider le versement.");
        return;
    }

    if (isNaN(amount) || amount < 20000) {
        errorBox.innerText = "⚠️ Règle AgroCrédit : Le montant minimum d'épargne mensuel réglementaire est de 20 000 CFA.";
        errorBox.style.display = "block";
        return;
    }

    if (ref === "") {
        errorBox.innerText = "⚠️ Référence requise : Entrez le code SMS Orange Money.";
        errorBox.style.display = "block";
        return;
    }

    try {
        errorBox.style.display = "none";

        const response = await fetch(serverUrl + "/api/save/orange", {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                user_id: prodUserId.trim(), // Transmission de l'ID PostgreSQL dynamique lue en base
                amount: amount, 
                transaction_ref: ref 
            })
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.detail || "Erreur de validation du serveur.");
        }

        alert("✅ Succès ! Dépôt Orange Money validé et synchronisé à vie dans la base PostgreSQL Supabase.");
        amountInput.value = "";
        refInput.value = "";

    } catch (error) {
        errorBox.innerText = "❌ Échec : " + error.message;
        errorBox.style.display = "block";
    }
}

window.onload = chargerConseilAgro;