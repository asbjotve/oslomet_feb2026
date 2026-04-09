<!DOCTYPE html>
<html lang="no">
<head>
    <meta charset="UTF-8">
    <title>Hent referansedata</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
      body { margin-top: 40px; }
      .table-responsive { width: 100%; }
      .resultatTabell th, .resultatTabell td { font-size: 0.95rem; }
      .resultatTabell th { cursor: pointer; }
      .resultatTabell { width: 100% !important; min-width: 1200px; }
    </style>
</head>
<body>
<div class="container-fluid px-4">
    <h2 class="mb-4">Hent referansedata</h2>

    <form id="referanseForm" class="row g-3 mb-4 align-items-center">
        <div class="col-auto">
            <input type="text" class="form-control" id="aarsemInput" placeholder="Eks: 2025AUTUMN" required>
        </div>

        <div class="col-auto">
            <select class="form-select" id="fakultetSelect">
                <option value="SAM">SAM</option>
                <option value="TKD,LUI,HV">TKD, LUI, HV</option>
                <option value="ALLE" selected>Alle fakultet</option>
            </select>
        </div>

        <div class="col-auto">
            <button type="submit" class="btn btn-primary mb-3">Hent data</button>
        </div>
    </form>

    <div id="feilmelding" class="alert alert-danger d-none"></div>

    <!-- Tabs på hovedsiden -->
    <div id="hovedTabsContainer" class="d-none">
      <ul class="nav nav-tabs" id="hovedTabs" role="tablist"></ul>
      <div class="tab-content border border-top-0 p-3" id="hovedTabsContent"></div>
    </div>
</div>

<!-- Modal for detaljvisning -->
<div class="modal fade" id="detaljModal" tabindex="-1" aria-labelledby="detaljModalLabel" aria-hidden="true">
  <div class="modal-dialog modal-xl modal-dialog-scrollable">
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
<script src="https://unpkg.com/tablesort@5.3.0/dist/tablesort.min.js"></script>
<script src="https://unpkg.com/tablesort@5.3.0/dist/sorts/tablesort.number.min.js"></script>

<script>
let detaljModal = null;

// Global liste over kolonner som skal sorteres som tall (når de finnes i fanens keys)
const GLOBAL_TALLKOLONNER = [
  "total_referanser_rapporteringspliktig",
  "antall_bolket",
  "antall_skal_bolkes",
  "antall_declined",
  "antall_annen_status",
  "Liste skal låses",
  "antall_referanser_rapporteres"
];

function escapeHtml(s) {
  return String(s ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

async function fetchJson(url) {
  const resp = await fetch(url);
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}

function lagTabellFraArray(data, opts = {}) {
  const {
    columns = null,
    tallKolonner = [],
    tableId = null,
    includeDetaljer = false
  } = opts;

  if (!Array.isArray(data) || data.length === 0) {
    return `<div class="alert alert-warning mb-0">Ingen data funnet.</div>`;
  }

  const keys = (Array.isArray(columns) && columns.length > 0)
    ? columns
    : Object.keys(data[0]);

  let thead = `<thead><tr>`;
  keys.forEach(key => {
    if (tallKolonner.includes(key)) thead += `<th data-sort-method="number">${escapeHtml(key)}</th>`;
    else thead += `<th>${escapeHtml(key)}</th>`;
  });

  if (includeDetaljer) {
    thead += `<th>Detaljer</th>`;
  }
  thead += `</tr></thead>`;

  let tbody = `<tbody>`;
  data.forEach(rad => {
    tbody += `<tr>`;

    keys.forEach(key => {
      const verdi = rad?.[key];
      if (tallKolonner.includes(key)) {
        const tallverdi = verdi !== null && verdi !== "" && verdi !== undefined ? Number(verdi) : "";
        tbody += `<td data-sort="${tallverdi}">${tallverdi}</td>`;
      } else {
        tbody += `<td>${escapeHtml(verdi)}</td>`;
      }
    });

    if (includeDetaljer) {
      const pid = rad?.pensumliste_id;

      if (pid !== null && pid !== undefined && String(pid).trim() !== "") {
        tbody += `
          <td>
            <button class="btn btn-sm btn-outline-primary vis-detaljer-knapp"
                    data-pensumliste-id="${escapeHtml(pid)}">
              Vis detaljer
            </button>
          </td>
        `;
      } else {
        // Liten debug-hjelp: viser keys dersom pensumliste_id mangler
        tbody += `
          <td>
            <span class="text-muted">Mangler pensumliste_id</span>
            <div class="small text-muted">Keys: ${escapeHtml(Object.keys(rad || {}).join(', '))}</div>
          </td>
        `;
      }
    }

    tbody += `</tr>`;
  });
  tbody += `</tbody>`;

  const idAttr = tableId ? `id="${escapeHtml(tableId)}"` : '';
  return `
    <div class="table-responsive w-100">
      <table class="table table-striped table-bordered resultatTabell" ${idAttr} style="width: 100%;">
        ${thead}
        ${tbody}
      </table>
    </div>
  `;
}

function aktiverDetaljKnapperInnenfor(containerEl) {
  containerEl.querySelectorAll('.vis-detaljer-knapp').forEach(knapp => {
    knapp.addEventListener('click', async function() {
      const pensumlisteId = this.dataset.pensumlisteId;
      if (!pensumlisteId) return;

      if (!detaljModal) {
        detaljModal = new bootstrap.Modal(document.getElementById('detaljModal'));
      }

      document.getElementById('detaljTabellContainer').innerHTML = '<div>Laster detaljer...</div>';
      detaljModal.show();

      try {
        // Ditt eksisterende detalj-endepunkt
        const url = `/proxy.php?endpoint=kopinor/referanseoversikt&pensumliste_id=${encodeURIComponent(pensumlisteId)}`;
        const data = await fetchJson(url);

        const keys = (Array.isArray(data) && data.length > 0) ? Object.keys(data[0]) : [];
        const tallKolonner = GLOBAL_TALLKOLONNER.filter(k => keys.includes(k));

        document.getElementById('detaljTabellContainer').innerHTML = lagTabellFraArray(data, {
          columns: null,
          tallKolonner,
          tableId: `detaljTable-${pensumlisteId}`,
          includeDetaljer: false
        });

        const table = document.getElementById(`detaljTable-${pensumlisteId}`);
        if (table) new Tablesort(table);
      } catch (err) {
        document.getElementById('detaljTabellContainer').innerHTML =
          `<div class="alert alert-danger mb-0">Klarte ikke å hente detaljer fra serveren.</div>`;
      }
    });
  });
}

function buildTabsAndLazyLoad(tabs) {
  const tabsEl = document.getElementById('hovedTabs');
  const contentEl = document.getElementById('hovedTabsContent');

  tabsEl.innerHTML = '';
  contentEl.innerHTML = '';
  document.getElementById('hovedTabsContainer').classList.remove('d-none');

  const cache = new Map();

  async function loadTab(tab) {
    const cached = cache.get(tab.id);
    if (cached?.state === 'loaded') return;
    if (cached?.state === 'loading' && cached.promise) return cached.promise;

    const target = document.getElementById(`tabContent-${tab.id}`);
    if (target) target.innerHTML = 'Laster...';

    const p = (async () => {
      try {
        const data = await fetchJson(tab.url);

        const keys = (Array.isArray(tab.columns) && tab.columns.length > 0)
          ? tab.columns
          : (Array.isArray(data) && data.length > 0 ? Object.keys(data[0]) : []);

        const tallKolonner = GLOBAL_TALLKOLONNER.filter(k => keys.includes(k));

        if (target) {
          target.innerHTML = lagTabellFraArray(data, {
            columns: tab.columns,
            tallKolonner,
            tableId: `table-${tab.id}`,
            includeDetaljer: tab.includeDetaljer === true
          });

          const table = target.querySelector('table');
          if (table) new Tablesort(table);

          if (tab.includeDetaljer === true) {
            aktiverDetaljKnapperInnenfor(target);
          }
        }

        cache.set(tab.id, { state: 'loaded' });
      } catch (err) {
        if (target) {
          target.innerHTML = `<div class="alert alert-danger mb-0">Klarte ikke å hente data for "${escapeHtml(tab.title)}".</div>`;
        }
        cache.set(tab.id, { state: 'error' });
      }
    })();

    cache.set(tab.id, { state: 'loading', promise: p });
    return p;
  }

  // build DOM
  tabs.forEach((t, i) => {
    tabsEl.insertAdjacentHTML('beforeend', `
      <li class="nav-item" role="presentation">
        <button
          class="nav-link ${i === 0 ? 'active' : ''}"
          id="tab-${t.id}"
          data-bs-toggle="tab"
          data-bs-target="#pane-${t.id}"
          type="button"
          role="tab"
          aria-controls="pane-${t.id}"
          aria-selected="${i === 0 ? 'true' : 'false'}"
        >${escapeHtml(t.title)}</button>
      </li>
    `);

    contentEl.insertAdjacentHTML('beforeend', `
      <div
        class="tab-pane fade ${i === 0 ? 'show active' : ''}"
        id="pane-${t.id}"
        role="tabpanel"
        aria-labelledby="tab-${t.id}"
        tabindex="0"
      >
        <div id="tabContent-${t.id}">Ikke lastet enda.</div>
      </div>
    `);
  });

  // lazy load first
  loadTab(tabs[0]);

  // lazy load on tab show
  document.querySelectorAll('#hovedTabs button[data-bs-toggle="tab"]').forEach(btn => {
    btn.addEventListener('shown.bs.tab', async (event) => {
      const tabId = event.target.id.replace(/^tab-/, '');
      const tab = tabs.find(x => x.id === tabId);
      if (tab) await loadTab(tab);
    });
  });
}

document.getElementById('referanseForm').addEventListener('submit', async function(e) {
  e.preventDefault();

  const feilmeldingEl = document.getElementById('feilmelding');
  feilmeldingEl.classList.add('d-none');
  feilmeldingEl.textContent = '';

  const aarsem = document.getElementById('aarsemInput').value.trim();
  const fakultet = document.getElementById('fakultetSelect').value;
  if (!aarsem) return;

  const tabDefs = [
    {
      id: "statistikk",
      title: "Vis statistikk",
      url: `/proxy.php?endpoint=${encodeURIComponent(`kopinor/statistikk?aarsem=${encodeURIComponent(aarsem)}&fakultet=${encodeURIComponent(fakultet)}`)}`,
      columns: null,
      includeDetaljer: false
    },
    {
      id: "skal_rapporteres",
      title: "Skal rapporteres",
      url: `/proxy.php?endpoint=${encodeURIComponent(`kopinor/statistikk?aarsem=${encodeURIComponent(aarsem)}&fakultet=${encodeURIComponent(fakultet)}&variant=SKAL_BOLKES`)}`,
      columns: ["kurskode", "pensumliste_id", "aarsem", "antall_skal_bolkes"],
      includeDetaljer: true
    },
    {
      id: "fikses_declined",
      title: "Fikses / Declined referanser",
      url: `/proxy.php?endpoint=${encodeURIComponent(`kopinor/statistikk?aarsem=${encodeURIComponent(aarsem)}&fakultet=${encodeURIComponent(fakultet)}&variant=DECLINED`)}`,
      columns: ["kurskode", "pensumliste_id", "aarsem"],
      includeDetaljer: true
    },
    {
      id: "skal_lases",
      title: "Skal låses",
      url: `/proxy.php?endpoint=${encodeURIComponent(`kopinor/statistikk?aarsem=${encodeURIComponent(aarsem)}&fakultet=${encodeURIComponent(fakultet)}&variant=SKAL_LAASES`)}`,
      columns: ["kurskode", "pensumliste_id", "total_referanser_rapporteringspliktig", "antall_bolket"],
      includeDetaljer: false
    }
  ];

  buildTabsAndLazyLoad(tabDefs);
});
</script>
</body>
</html>
