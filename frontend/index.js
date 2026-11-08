let totalEpargne = 0;
const serverUrl = "https://agrocreditsuivi.onrender.com";

// 1. Charger automatiquement le conseil agropastoral actif depuis Python
async function chargerConseilAgro() {
    const tipsBox = document.getElementById('agro-tips-box');
    try {
        const response = await fetch(serverUrl + "/api/tips/elevage");
        const data = await response.json();
        
        tipsBox.innerHTML = `
            <div class="tip-box">
                <strong style="display: block; margin-bottom: 5px;">${data.title}</strong>
                ${data.content}
            </div>
        `;
    } catch (error) {
        tipsBox.innerHTML = '<p style="font-size: 12px; color: #b91c1c; font-weight: bold;">⚠️ Le moteur en ligne ne répond pas. Vérifiez le statut Render.</p>';
    }
}

// 2. Envoyer la transaction Orange Money validée au serveur en ligne
async function effectuerVersement() {
    const amountInput = document.getElementById('saving-amount');
    const refInput = document.getElementById('transaction-ref');
    const errorBox = document.getElementById('error-message');
    
    const amount = parseInt(amountInput.value);
    const ref = refInput.value.trim();

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
        const testUserId = "1"; 

        const response = await fetch(serverUrl + "/api/save/orange", {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                user_id: testUserId,
                amount: amount, 
                transaction_ref: ref 
            })
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.detail || "Erreur de validation du serveur.");
        }

        totalEpargne += amount;
        
        const nombreDeMois = Math.floor(totalEpargne / 20000);
        const fraisFormation = nombreDeMois * 5000;
        const epargneNette = totalEpargne - fraisFormation;
        const droitCredit = epargneNette > 0 ? Math.floor((epargneNette / 0.15) * 0.85) : 0;

        document.getElementById('display-savings').innerText = totalEpargne.toLocaleString('fr-FR') + " CFA";
        document.getElementById('display-credit').innerText = droitCredit.toLocaleString('fr-FR') + " CFA";

        amountInput.value = "";
        refInput.value = "";

        alert("✅ Succès ! Dépôt Orange Money validé et enregistré sur le serveur Render.");

    } catch (error) {
        errorBox.innerText = "❌ Échec : " + error.message;
        errorBox.style.display = "block";
    }
}

window.onload = chargerConseilAgro;