<!DOCTYPE html>
<html lang="no">
<head>
    <meta charset="UTF-8">
    <title>Hent referansedata</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
      body { margin-top: 40px; }
      #resultatTabell th, #resultatTabell td { font-size: 0.95rem; }
      #resultatTabell th { cursor: pointer; }
      .table-responsive { width: 100%; }
      #resultatTabell { width: 100% !important; min-width: 1200px; }
    </style>
</head>
<body>
<div class="container-fluid px-4">
    <h2 class="mb-4">Hent referansedata</h2>
    <form id="referanseForm" class="row g-3 mb-4">
        <div class="col-auto">
            <input type="text" class="form-control" id="aarsemInput" placeholder="Eks: 2025AUTUMN" required>
        </div>
        <div class="col-auto">
            <button type="submit" class="btn btn-primary mb-3">Hent data</button>
        </div>
    </form>
    <div id="feilmelding" class="alert alert-danger d-none"></div>
    <div id="tabellContainer" class="w-100"></div>
</div>

<!-- Modal for detaljvisning -->
<div class="modal fade" id="detaljModal" tabindex="-1" aria-labelledby="detaljModalLabel" aria-hidden="true">
  <div class="modal-dialog modal-lg modal-dialog-scrollable">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title" id="detaljModalLabel">Detaljer for pensumliste</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Lukk"></button>
      </div>
      <div class="modal-body" id="detaljModalBody">
        <div id="detaljTabellContainer"></div>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Lukk</button>
      </div>
    </div>
  </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
<!-- Tablesort JS og Number-plugin -->
<script src="https://unpkg.com/tablesort@5.3.0/dist/tablesort.min.js"></script>
<script src="https://unpkg.com/tablesort@5.3.0/dist/sorts/tablesort.number.min.js"></script>
<script>
let detaljModal = null;

document.getElementById('referanseForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    document.getElementById('feilmelding').classList.add('d-none');
    const aarsem = document.getElementById('aarsemInput').value.trim();
    if (!aarsem) return;

    // Oppdatert fetch-url:
    let url = `/proxy.php?endpoint=kopinor/statistikk?aarsem=${encodeURIComponent(aarsem)}`;

    try {
        const resp = await fetch(url);
        if (!resp.ok) throw new Error("Feil ved henting av data");
        const data = await resp.json();
        if (!Array.isArray(data) || data.length === 0) {
            document.getElementById('tabellContainer').innerHTML = `<div class="alert alert-warning">Ingen data funnet.</div>`;
            return;
        }

        // Tallkolonner som skal sorteres som tall
        const tallKolonner = [
            "antall_referanser_rapporteres",
            "antall_skal_bolkes",
            "antall_bolketantall_declined",
            "antall_annen_status"
        ];

        // Lag tabell med detaljknapp på hver rad
        let thead = `<thead><tr>`;
        Object.keys(data[0]).forEach(key => {
            if (tallKolonner.includes(key)) {
                thead += `<th data-sort-method="number">${key}</th>`;
            } else {
                thead += `<th>${key}</th>`;
            }
        });
        thead += `<th>Detaljer</th></tr></thead>`;

        let tbody = '<tbody>';
        data.forEach(rad => {
            tbody += '<tr>';
            Object.entries(rad).forEach(([key, verdi]) => {
                if (tallKolonner.includes(key)) {
                    const tallverdi = verdi !== null && verdi !== "" ? Number(verdi) : "";
                    tbody += `<td data-sort="${tallverdi}">${tallverdi}</td>`;
                } else {
                    tbody += `<td>${verdi !== null ? verdi : ''}</td>`;
                }
            });
            tbody += `<td><button class="btn btn-sm btn-outline-primary vis-detaljer-knapp" data-pensumliste-id="${rad.pensumliste_id}">Vis detaljer</button></td>`;
            tbody += '</tr>';
        });
        tbody += '</tbody>';

        document.getElementById('tabellContainer').innerHTML = `
            <div class="table-responsive w-100">
                <table class="table table-striped table-bordered" id="resultatTabell" style="width: 100%;">
                    ${thead}
                    ${tbody}
                </table>
            </div>
        `;
        // Aktiver sortering
        new Tablesort(document.getElementById('resultatTabell'));

        leggTilDetaljKnappEvent();
    } catch (err) {
        document.getElementById('feilmelding').classList.remove('d-none');
        document.getElementById('feilmelding').textContent = "Klarte ikke å hente data fra serveren.";
        document.getElementById('tabellContainer').innerHTML = "";
    }
});

function leggTilDetaljKnappEvent() {
    document.querySelectorAll('.vis-detaljer-knapp').forEach(knapp => {
        knapp.addEventListener('click', async function() {
            const pensumlisteId = this.dataset.pensumlisteId;
            if (!pensumlisteId) return;
            let url = `/proxy.php?endpoint=kopinor/referanseoversikt&pensumliste_id=${encodeURIComponent(pensumlisteId)}`;
            document.getElementById('detaljTabellContainer').innerHTML = '<div>Laster detaljer...</div>';
            if (!detaljModal) {
                detaljModal = new bootstrap.Modal(document.getElementById('detaljModal'));
            }
            detaljModal.show();

            try {
                const resp = await fetch(url);
                if (!resp.ok) throw new Error("Feil ved henting av detaljer");
                const data = await resp.json();
                if (!Array.isArray(data) || data.length === 0) {
                    document.getElementById('detaljTabellContainer').innerHTML = `<div class="alert alert-warning">Ingen detaljer funnet.</div>`;
                    return;
                }

                const tallKolonner = [
                    "antall_referanser_rapporteres",
                    "antall_skal_bolkes",
                    "antall_bolketantall_declined",
                    "antall_annen_status"
                ];

                let thead = `<thead><tr>`;
                Object.keys(data[0]).forEach(key => {
                    if (tallKolonner.includes(key)) {
                        thead += `<th data-sort-method="number">${key}</th>`;
                    } else {
                        thead += `<th>${key}</th>`;
                    }
                });
                thead += `</tr></thead>`;

                let tbody = '<tbody>';
                data.forEach(rad => {
                    tbody += '<tr>';
                    Object.entries(rad).forEach(([key, verdi]) => {
                        if (tallKolonner.includes(key)) {
                            const tallverdi = verdi !== null && verdi !== "" ? Number(verdi) : "";
                            tbody += `<td data-sort="${tallverdi}">${tallverdi}</td>`;
                        } else {
                            tbody += `<td>${verdi !== null ? verdi : ''}</td>`;
                        }
                    });
                    tbody += '</tr>';
                });
                tbody += '</tbody>';

                document.getElementById('detaljTabellContainer').innerHTML = `
                    <div class="table-responsive w-100">
                        <table class="table table-striped table-bordered" style="width: 100%;">
                            ${thead}
                            ${tbody}
                        </table>
                    </div>
                `;
            } catch (err) {
                document.getElementById('detaljTabellContainer').innerHTML = `<div class="alert alert-danger">Klarte ikke å hente detaljer fra serveren.</div>`;
            }
        });
    });
}
</script>
</body>
</html>
