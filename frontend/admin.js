const serverUrl = ""; // Adresse relative universelle pour éviter les conflits d'URLs

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

        const result = await response.json();

        if (response.ok) {
            alert("✅ Succès ! L'agriculteur a été enregistré dans le programme.");
            nameInput.value = "";
            emailInput.value = "";
            garantieDetailsInput.value = "";
            chargerClients();
        } else {
            alert("❌ Échec : " + (result.detail || "Erreur de validation du serveur."));
        }
    } catch (error) {
        alert("❌ Erreur de connexion avec le serveur.");
    }
}

// 3. Générer le canevas d'évaluation de projet de levier avec les 2 mois de différé de grâce
async function analyserProjet(clientId) {
    const contentBox = document.getElementById('evaluation-content');
    contentBox.innerHTML = "<p style='font-style:italic;'>Analyse des indicateurs de viabilité et calcul de l'échéancier...</p>";

    try {
        const response = await fetch(serverUrl + "/api/admin/evaluation/" + clientId);
        const data = await response.json();

        contentBox.innerHTML = `
            <div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0; border-top: 4px solid #2563eb; line-height: 1.5;">
                <h4 style="margin:0 0 10px 0; color:#1e293b; font-size:13px; text-transform: uppercase;">📊 DOSSIER TECHNIQUE BANCABLE</h4>
                <p style="margin:4px 0;"><strong>Nom :</strong> ${data.client_name}</p>
                <p style="margin:4px 0;"><strong>Spéculation :</strong> ${data.speculation} (${data.cycle_exploitation})</p>
                <hr style="border:0; border-top:1px solid #e2e8f0; margin:10px 0;">
                
                <p style="margin:4px 0; font-weight:bold; color:#c2410c;">🔒 COUVERTURE DES RISQUES :</p>
                <p style="margin:2px 0;">Garantie : <span class="badge" style="background-color:#eff6ff; color:#1d4ed8;">${data.garantie_type}</span></p>
                <p style="margin:4px 0; font-size:11px; background:#f8fafc; padding:6px; border-radius:4px; border:1px solid #f1f5f9; color:#475569;">📝 ${data.garantie_details}</p>
                
                <hr style="border:0; border-top:1px solid #e2e8f0; margin:10px 0;">
                <p style="margin:4px 0; font-weight:bold; color:#1e293b;">💰 Plan de Financement (1M CFA) :</p>
                <p style="margin:2px 0;">Nantissement Épargne (15%) : <strong>${data.apport_epargne_nette.toLocaleString()} CFA</strong></p>
                <p style="margin:2px 0;">Crédit Levier Sollicité (85%) : <strong style="color:#166534;">${data.credit_sollicite_banque.toLocaleString()} CFA</strong></p>
                
                <hr style="border:0; border-top:1px solid #e2e8f0; margin:10px 0;">
                <p style="margin:4px 0; font-weight:bold; color:#2563eb;">📅 ÉCHÉANCIER DE REMBOURSEMENT LOGIQUE :</p>
                <div style="background:#f0fdf4; padding:10px; border-radius:6px; border:1px solid #bbf7d0; margin-bottom:10px; font-size:11px;">
                    <p style="margin:2px 0;">Durée totale du contrat : <strong>${data.duree_mois} mois</strong></p>
                    <p style="margin:2px 0; color:#c2410c; font-weight:bold;">⚠️ Période de grâce (Différé total) : Mois 1 et Mois 2 (0 CFA)</p>
                    <p style="margin:4px 0; font-size:13px; color:#166534; font-weight:bold;">👉 Traite (Mois 3 à Mois 12) : ${data.mensualite.toLocaleString('fr-FR')} CFA / mois</p>
                    <p style="margin:2px 0; color:#64748b; font-size:10px;">Coût total du crédit (intérêts) : ${data.total_interets.toLocaleString()} CFA (Taux : ${data.taux_annuel})</p>
                </div>

                <hr style="border:0; border-top:1px solid #e2e8f0; margin:10px 0;">
                <p style="margin:4px 0; font-weight:bold; color:#1e293b;">📈 Rentabilité de la Campagne :</p>
                <p style="margin:2px 0;">Chiffre d'Affaires prévisionnel : <strong>${data.chiffre_affaires_prev.toLocaleString()} CFA</strong></p>
                <p style="margin:2px 0;">Bénéfice Net d'Exploitation : <strong style="color:#2563eb;">+${data.benefice_net_prev.toLocaleString()} CFA</strong></p>
                <p style="margin:2px 0; color:#16a34a; font-size:10px; font-style:italic;">*Le bénéfice couvre amplement les traites de la banque.</p>

                <div style="margin-top:15px; background:#dcfce7; color:#15803d; padding:8px; text-align:center; font-weight:bold; border-radius:6px; font-size:11px;">
                    🎯 EVALUATION : ${data.statut_projet}
                </div>
            </div>
        `;
    } catch (error) {
        contentBox.innerHTML = "<p style='color:#b91c1c;'>⚠️ Échec du calcul de l'échéancier prévisionnel.</p>";
        // 🔥 DANS admin.html, AJOUTEZ CE BOUTON JUSTE EN DESSOUS DU BLOC EVALUATION VERT :
<button onclick="window.print()" style="margin-top: 15px; width: 100%; background-color: #1e293b; color: white; padding: 10px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 12px; display: flex; align-items: center; justify-content: center; gap: 8px;">
    🖨️ Imprimer l'Attestation Officielle (PDF)
</button>
    }
}

window.onload = chargerClients;