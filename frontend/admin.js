const serverUrl = ""; 

function validerCodeBanque() {
    const inputCode = document.getElementById("agency-password-field").value;
    if (inputCode === "Ambam2026") {
        document.getElementById("auth-container").style.display = "none";
        document.getElementById("protected-content").style.display = "block";
        initialiserVariablesAgence();
        chargerClients();
    } else {
        alert("❌ Code incorrect.");
        document.getElementById("agency-password-field").value = "";
    }
}

function initialiserVariablesAgence() {
    if(!localStorage.getItem("cfg_banque")) {
        localStorage.setItem("cfg_banque", "La Régionale");
        localStorage.setItem("cfg_agence", "Ambam");
        localStorage.setItem("cfg_localite", "Ambam");
        localStorage.setItem("cfg_arrondissement", "Ambam");
        localStorage.setItem("cfg_departement", "Vallée-du-Ntem");
        localStorage.setItem("cfg_region", "Sud");
    }
    document.getElementById("title-banque").innerText = localStorage.getItem("cfg_banque");
    document.getElementById("subtitle-agence").innerText = "Agence de " + localStorage.getItem("cfg_agence") + " — Département de la " + localStorage.getItem("cfg_departement") + " (" + localStorage.getItem("cfg_region") + ")";
}

async function chargerClients() {
    const tbody = document.getElementById('table-clients-body');
    const banque = localStorage.getItem("cfg_banque") || "La Régionale";
    const agence = localStorage.getItem("cfg_agence") || "Ambam";
    try {
        const response = await fetch(`${serverUrl}/api/admin/clients?banque=${encodeURIComponent(banque)}&agence=${encodeURIComponent(agence)}`);
        const data = await response.json();
        if (data.clients && data.clients.length > 0) {
            tbody.innerHTML = "";
            data.clients.forEach(client => {
                const nombreDeMois = Math.floor(client.total_epargne / 20000);
                const fraisFormation = nombreDeMois * 5000;
                const epargneNette = client.total_epargne - fraisFormation;
                const droitCredit = epargneNette > 0 ? Math.floor((epargneNette / 0.15) * 0.85) : 0;
                tbody.innerHTML += `<tr><td>#0${client.id}</td><td><strong>${client.full_name}</strong><br><small>${client.email}</small></td><td>${client.filiere}</td><td>${client.total_epargne.toLocaleString('fr-FR')} CFA</td><td><span class="badge-frais">-${fraisFormation.toLocaleString('fr-FR')} CFA</span></td><td style="font-weight:bold;color:#166534;background-color:#f0fdf4;">${droitCredit.toLocaleString('fr-FR')} CFA</td><td><button onclick="analyserProjet('${client.id}')" class="btn-eval">📊 Évaluer</button></td></tr>`;
            });
        } else {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: #94a3b8; padding:20px 0;">Aucun agriculteur enregistré pour l\'agence de ' + agence + '.</td></tr>';
        }
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: #b91c1c; padding:20px 0;">⚠️ Erreur de liaison base de données.</td></tr>';
    }
}

async function enregistrerAgriculteur() {
    const nameInput = document.getElementById('reg-name');
    const emailInput = document.getElementById('reg-email');
    const filiereInput = document.getElementById('reg-filiere');
    const garantieTypeInput = document.getElementById('reg-garantie-type');
    const garantieDetailsInput = document.getElementById('reg-garantie-details');
    if (nameInput.value.trim() === "" || emailInput.value.trim() === "" || garantieDetailsInput.value.trim() === "") {
        alert("⚠️ Remplissez tous les champs."); return;
    }
    try {
        await fetch(serverUrl + "/api/register", {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                full_name: nameInput.value.trim(), email: emailInput.value.trim(), filiere: filiereInput.value, garantie_type: garantieTypeInput.value, garantie_details: garantieDetailsInput.value.trim(),
                banque_nom: localStorage.getItem("cfg_banque") || "La Régionale", agence_nom: localStorage.getItem("cfg_agence") || "Ambam", localite: localStorage.getItem("cfg_localite") || "Ambam", arrondissement: localStorage.getItem("cfg_arrondissement") || "Ambam", departement: localStorage.getItem("cfg_departement") || "Vallée-du-Ntem", region: localStorage.getItem("cfg_region") || "Sud"
            })
        });
        alert("✅ Agriculteur inscrit !"); nameInput.value = ""; emailInput.value = ""; garantieDetailsInput.value = ""; chargerClients();
    } catch (e) { alert("❌ Erreur de connexion."); }
}

async function analyserProjet(clientId) {
    const contentBox = document.getElementById('evaluation-content');
    contentBox.innerHTML = "<p>Calcul de l'échéancier...</p>";
    try {
        const response = await fetch(serverUrl + "/api/admin/evaluation/" + clientId);
        const data = await response.json();
        contentBox.innerHTML = `<div style="background:white;padding:15px;border-radius:8px;border:1px solid #e2e8f0;border-top:4px solid #2563eb;line-height:1.6;"><h4 style="margin:0 0 10px 0;text-transform:uppercase;">📊 DOSSIER BANCABLE — ${data.banque_nom}</h4><p style="font-size:11px;color:#64748b;">Agence de ${data.agence_nom}</p><hr style="border:0;border-top:1px solid #e2e8f0;margin:8px 0;"><p><strong>Nom :</strong> ${data.client_name}</p><p><strong>Spéculation :</strong> ${data.speculation}</p><hr style="border:0;border-top:1px solid #e2e8f0;margin:8px 0;"><p><strong>Garantie :</strong> ${data.garantie_type}</p><p style="font-size:11px;background:#f8fafc;padding:6px;border-radius:4px;">📝 ${data.garantie_details}</p><hr style="border:0;border-top:1px solid #e2e8f0;margin:8px 0;"><p>Financement : Épargne Nette (15%) : <strong>150 000 CFA</strong> | Crédit Sollicité (85%) : <strong style="color:#166534;">850 000 CFA</strong></p><hr style="border:0;border-top:1px solid #e2e8f0;margin:8px 0;"><p style="font-weight:bold;color:#2563eb;">📅 ÉCHÉANCIER RECALCULÉ :</p><div style="background:#f0fdf4;padding:10px;border-radius:6px;border:1px solid #bbf7d0;font-size:11px;"><p>Durée : <strong>12 mois</strong></p><p style="color:#c2410c;font-weight:bold;">⚠️ Période de grâce : Mois 1 & Mois 2 (0 CFA)</p><p style="font-size:12px;color:#166534;font-weight:bold;">👉 Traite (Mois 3 à 12) : ${data.mensualite.toLocaleString('fr-FR')} CFA / mois</p><p style="color:#64748b;font-size:10px;">Intérêts COBAC : ${data.total_interets.toLocaleString()} CFA</p></div><hr style="border:0;border-top:1px solid #e2e8f0;margin:8px 0;"><p>Chiffre d'Affaires prévisionnel : <strong>${data.chiffre_affaires_prev.toLocaleString()} CFA</strong></p><p>Bénéfice Net Campagne : <strong style="color:#2563eb;">+${data.benefice_net_prev.toLocaleString()} CFA</strong></p><div style="margin-top:15px;background:#dcfce7;color:#15803d;padding:8px;text-align:center;font-weight:bold;border-radius:6px;font-size:11px;">🎯 EVALUATION : ${data.statut_projet}</div></div>`;
    } catch (error) { contentBox.innerHTML = "<p>⚠️ Échec du calcul.</p>"; }
}

function exporterVersExcel() {
    const table = document.querySelector("table");
    if (!table || table.rows.length <= 2) { alert("⚠️ Aucun compte à exporter."); return; }
    let html = table.outerHTML.replace(/<button[^>]*>([\s\S]*?)<\/button>/gi, "Dossier");
    const blob = new Blob([`<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://w3.org"><head><meta charset="utf-8"></head><body>${html}</body></html>`], { type: "application/vnd.ms-excel" });
    const url = URL.createObjectURL(blob); const a = document.createElement("a"); a.href = url; a.download = `Portefeuille_${localStorage.getItem("cfg_banque")}_${localStorage.getItem("cfg_agence")}.xls`; document.body.appendChild(a); a.click(); document.body.removeChild(a);
}