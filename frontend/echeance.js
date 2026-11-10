const serverUrl = "";

async function chargerCalendrierRecouvrement() {
    const clientId = document.getElementById("search-client-id").value.trim();
    const tbody = document.getElementById("table-remboursements-body");
    const banner = document.getElementById("client-info-banner");
    if (clientId === "") { alert("⚠️ Saisissez l'ID."); return; }

    try {
        const evalResponse = await fetch("/api/admin/evaluation/" + clientId);
        if (!evalResponse.ok) { throw new Error("Données d'octroi introuvables."); }
        const evalData = await evalResponse.json();

        const response = await fetch("/api/recouvrement/echéancier/" + clientId);
        if (!response.ok) { throw new Error("Agriculteur introuvable."); }
        const data = await response.json();
        
        document.getElementById("txt-client-name").innerText = data.client_name;
        document.getElementById("txt-client-filiere").innerText = data.filiere;
        
        // Liaison dynamique avec le vrai crédit accordé calculé par le serveur
        document.getElementById("lbl-credit-total").innerText = evalData.credit_sollicite_banque.toLocaleString('fr-FR') + " CFA";
        
        if (data.echeances.length > 0) {
            // Lecture rigoureuse du premier mois (Index 0) et du dernier mois (Index 11)
            document.getElementById("lbl-date-debut").innerText = new Date(data.echeances[0].date_theorique).toLocaleDateString('fr-FR');
            document.getElementById("lbl-date-fin").innerText = new Date(data.echeances[data.echeances.length - 1].date_theorique).toLocaleDateString('fr-FR');
        }
        document.getElementById("lbl-taux-credit").innerText = evalData.taux_annuel;
        banner.style.display = "block";
        tbody.innerHTML = "";
        const dateDuJour = new Date();

        data.echeances.forEach(ech => {
            let badgeClass = "status-wait"; let statutAffiche = ech.statut; let boutonAction = "-";
            const dateLimite = new Date(ech.date_theorique);
            if (ech.statut === "En attente" && dateLimite < dateDuJour) {
                badgeClass = "status-late"; statutAffiche = "Impayé / Retard";
            } else if (ech.statut === "Période de grâce") { badgeClass = "status-grace";
            } else if (ech.statut === "Payé") {
                badgeClass = "status-paid";
                const nomPropre = data.client_name.replace(/'/g, "\\'");
                boutonAction = `<button onclick="imprimerRecuTraite('${nomPropre}', '${ech.num_echeance}', '${ech.date_theorique}', '${ech.montant_paye}', '${ech.date_paiement}', '${ech.transaction_ref}')" class="btn-pay">🖨️ Reçu</button>`;
            }
            tbody.innerHTML += `<tr><td><strong>Mois ${ech.num_echeance}</strong></td><td>${new Date(ech.date_theorique).toLocaleDateString('fr-FR')}</td><td style="font-weight:bold;">${ech.montant_theorique.toLocaleString('fr-FR')} CFA</td><td style="color:#16a34a; font-weight:bold;">${ech.montant_paye > 0 ? ech.montant_paye.toLocaleString('fr-FR') + ' CFA' : '-'}</td><td>${ech.date_paiement || '-'}</td><td style="font-family:monospace; font-weight:bold;">${ech.transaction_ref || '-'}</td><td><span class="status-badge ${badgeClass}">${statutAffiche}</span></td><td>${boutonAction}</td></tr>`;
        });
    } catch (error) { banner.style.display = "none"; tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: #b91c1c; font-weight: bold;">❌ ${error.message}</td></tr>`; }
}

async function validerPaiementTraite() {
    const clientId = document.getElementById("search-client-id").value.trim();
    const numEcheance = document.getElementById("pay-num-echeance").value;
    const amount = document.getElementById("pay-amount").value.trim();
    const txRef = document.getElementById("pay-tx-ref").value.trim();
    if (clientId === "" || amount === "" || txRef === "") { alert("⚠️ Remplissez tous les champs."); return; }
    try {
        const response = await fetch("/api/recouvrement/payer", {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ client_id: clientId, num_echeance: parseInt(numEcheance), amount: parseInt(amount), transaction_ref: txRef })
        });
        if (!response.ok) { throw new Error("Échec d'enregistrement."); }
        alert("✅ Échéance enregistrée !");
        document.getElementById("pay-amount").value = ""; document.getElementById("pay-tx-ref").value = "";
        chargerCalendrierRecouvrement();
    } catch (error) { alert("❌ Erreur : " + error.message); }
}

function imprimerRecuTraite(nom, num, dateLim, montant, datePaye, ref) {
    const url = `/recu?nom=${encodeURIComponent(nom)}&num=${num}&montant=${montant}&date=${encodeURIComponent(datePaye)}&ref=${encodeURIComponent(ref)}`;
    window.open(url, '_blank');
}