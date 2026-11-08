// 🔥 L'adresse de l'API principale doit s'arrêter juste après .com :
const serverUrl = "https://agrocreditsuivi.onrender.com/admin";

// 1. Charger la liste des clients depuis le serveur Render
async function chargerClients() {
    const tbody = document.getElementById('table-clients-body');
    try {
        const response = await fetch(serverUrl + "/api/admin/clients");
        const data = await response.json();

        if (data.clients && data.clients.length > 0) {
            tbody.innerHTML = "";
            data.clients.forEach(client => {
                const nombreDeMois = Math.floor(client.total_epargne / 20000);
                const fraisFormation = nombreDeMois * 5000;
                const epargneNette = client.total_epargne - fraisFormation;
                const droitCredit = epargneNette > 0 ? Math.floor((epargneNette / 0.15) * 0.85) : 0;

                tbody.innerHTML += `
                    <tr>
                        <td>#0${client.id}</td>
                        <td><strong>${client.full_name}</strong><br><small style="color:#64748b;">${client.email}</small></td>
                        <td>${client.filiere}</td>
                        <td style="font-weight: bold;">${client.total_epargne.toLocaleString('fr-FR')} CFA</td>
                        <td><span class="badge-frais">-${fraisFormation.toLocaleString('fr-FR')} CFA</span></td>
                        <td style="font-weight: bold; color: #166534; background-color: #f0fdf4;">${droitCredit.toLocaleString('fr-FR')} CFA</td>
                        <td><button onclick="analyserProjet('${client.id}')" class="btn-eval">📊 Évaluer</button></td>
                    </tr>
                `;
            });
        } else {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: #94a3b8;">Aucun client enregistré.</td></tr>';
        }
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: #b91c1c; font-weight: bold;">⚠️ Erreur de connexion au serveur.</td></tr>';
    }
}

// 2. Transmettre l'inscription d'un nouvel agriculteur avec ses garanties d'octroi
async function enregistrerAgriculteur() {
    const nameInput = document.getElementById('reg-name');
    const emailInput = document.getElementById('reg-email');
    const filiereInput = document.getElementById('reg-filiere');
    const garantieTypeInput = document.getElementById('reg-garantie-type');
    const garantieDetailsInput = document.getElementById('reg-garantie-details');

    if (nameInput.value.trim() === "" || emailInput.value.trim() === "" || garantieDetailsInput.value.trim() === "") {
        alert("⚠️ Erreur : Veuillez remplir toutes les informations, y compris le volet des garanties.");
        return;
    }

    try {
        const response = await fetch(serverUrl + "/api/register", {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                full_name: nameInput.value.trim(),
                email: emailInput.value.trim(),
                filiere: filiereInput.value,
                garantie_type: garantieTypeInput.value,
                garantie_details: garantieDetailsInput.value.trim()
            })
        });

        if (response.ok) {
            alert("✅ Succès ! L'agriculteur et ses garanties d'octroi ont été enregistrés.");
            nameInput.value = "";
            emailInput.value = "";
            garantieDetailsInput.value = "";
            chargerClients();
        } else {
            alert("❌ Échec de l'enregistrement.");
        }
    } catch (error) {
        alert("❌ Erreur de connexion avec le serveur.");
    }
}

// 3. Générer le canevas d'évaluation de projet de levier pour la banque
async function analyserProjet(clientId) {
    const contentBox = document.getElementById('evaluation-content');
    contentBox.innerHTML = "<p style='font-style:italic;'>Analyse des risques en cours...</p>";

    try {
        const response = await fetch(serverUrl + "/api/admin/evaluation/" + clientId);
        const data = await response.json();

        contentBox.innerHTML = `
            <div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0; border-top: 4px solid #2563eb; line-height: 1.6;">
                <h4 style="margin:0 0 10px 0; color:#1e293b; font-size:13px; text-transform: uppercase;">📊 DOSSIER TECHNIQUE BANCABLE</h4>
                <p style="margin:4px 0;"><strong>Nom :</strong> ${data.client_name}</p>
                <p style="margin:4px 0;"><strong>Spéculation :</strong> ${data.speculation}</p>
                <p style="margin:4px 0;"><strong>Cycle :</strong> ${data.cycle_exploitation}</p>
                <hr style="border:0; border-top:1px solid #e2e8f0; margin:10px 0;">
                <p style="margin:4px 0; font-weight:bold; color:#c2410c;">🔒 COUVERTURE DES RISQUES / GARANTIES :</p>
                <p style="margin:2px 0;">Type : <span class="badge" style="background-color:#eff6ff; color:#1d4ed8;">${data.garantie_type}</span></p>
                <p style="margin:4px 0; font-size:11px; background:#f8fafc; padding:6px; border-radius:4px; border:1px solid #f1f5f9; color:#334155;">📝 ${data.garantie_details}</p>
                <hr style="border:0; border-top:1px solid #e2e8f0; margin:10px 0;">
                <p style="margin:4px 0; font-weight:bold; color:#1e293b;">💰 Plan de Financement :</p>
                <p style="margin:2px 0;">Garantie Épargne Nette (15%) : <strong>150 000 CFA</strong></p>
                <p style="margin:2px 0;">Crédit Sollicité (85%) : <strong style="color:#166534;">850 000 CFA</strong></p>
                <hr style="border:0; border-top:1px solid #e2e8f0; margin:10px 0;">
                <p style="margin:4px 0; font-weight:bold; color:#1e293b;">📈 Prévisions d'Exploitation :</p>
                <p style="margin:2px 0;">Chiffre d'Affaires : <strong>${data.chiffre_affaires_prev.toLocaleString()} CFA</strong></p>
                <p style="margin:2px 0;">Bénéfice Net Estimé : <strong style="color:#2563eb;">+${data.benefice_net_prev.toLocaleString()} CFA</strong></p>
                <div style="margin-top:15px; background:#dcfce7; color:#15803d; padding:8px; text-align:center; font-weight:bold; border-radius:6px; font-size:11px;">
                    🎯 EVALUATION : ${data.statut_projet}
                </div>
            </div>
        `;
    } catch (error) {
        contentBox.innerHTML = "<p style='color:#b91c1c;'>⚠️ Échec de la génération du rapport.</p>";
    }
}

window.onload = chargerClients;