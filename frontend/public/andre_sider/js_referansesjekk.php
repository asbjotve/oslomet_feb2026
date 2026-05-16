<script>
function injectCustomCSS() {
  const style = document.createElement('style');
  style.innerHTML = `
    #loadingSpinner {
        visibility: hidden;
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        z-index: 1000;
    }
    .table>tbody>tr.table-active>td {
        background: #007bff;
        color: #fff;
    }
    th.asc::after {
        content: " ▲";
    }
    th.desc::after {
        content: " ▼";
    }
    .table-container {
        width: 100%;
        overflow-x: auto;
    }
    .table-scrollable {
        max-height: 450px;
        overflow-y: auto;
    }
    thead th {
        position: sticky;
        top: 0;
        background: #fff;
        z-index: 10;
    }
    .table>tbody>tr.kode12>td {
        background-color: #71f93f;
        color: #000;
    }
    .table>tbody>tr.kode12.table-active>td {
        background: #007bff;
        color: #fff;
    }
  `;
  document.head.appendChild(style);
}

// Dynamisk referansesjekk-app uten statisk HTML.
// Forutsetter at jQuery og Bootstrap allerede er lastet inn på modersiden!

function createModal({id, title, label, inputId, saveButtonId}) {
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.id = id;
    modal.tabIndex = -1;
    modal.setAttribute('aria-labelledby', id + 'Label');
    modal.setAttribute('aria-hidden', 'true');
    modal.innerHTML = `
    <div class="modal-dialog"><div class="modal-content">
        <div class="modal-header"><h5 class="modal-title" id="${id}Label">${title}</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button></div>
        <div class="modal-body"><form>
            <div class="mb-3">
                <label for="${inputId}" class="form-label">${label}</label>
                <input type="text" class="form-control" id="${inputId}">
            </div>
        </form></div>
        <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Lukk</button>
            <button type="button" class="btn btn-primary" id="${saveButtonId}">Lagre endringer</button>
        </div>
    </div></div>`;
    document.body.appendChild(modal);
}

function createUI() {
    // Container
    const container = document.createElement('div');
    container.className = "container-fluid mt-2";
    container.innerHTML = `
      <div class="mb-4">
        <div class="input-group">
          <input type="text" id="inputField" class="form-control" placeholder="Skriv her..." aria-label="Input">
          <button class="btn btn-primary" type="button" id="referanseSjekkButton">Send</button>
        </div>
      </div>
      <div id="loadingSpinner" class="d-flex align-items-center" style="visibility:hidden">
        <strong>Henter data, vennligst vent...</strong>
        <div class="spinner-border ms-auto" role="status" aria-hidden="true"></div>
      </div>
      <div class="table-scrollable">
        <table class="table table-bordered table-striped table-hover w-100" id="firstTable">
          <thead><tr>
            <th>Tittel</th><th class="sortable" data-column-index="1">Forfatter</th>
            <th>Utgitt</th><th>Utgivelsessted</th><th>Forlag</th><th>M300</th>
            <th>Antall sider</th><th></th>
          </tr></thead>
          <tbody></tbody>
        </table>
      </div>
      <br />
      <div class="table-scrollable">
        <table class="table table-bordered table-striped table-hover w-100" id="secondTable">
          <thead><tr>
            <th>Referanse ID</th><th>Kapittel</th><th>Kapitteltittel</th>
            <th>Forfatter</th><th>Offentlig kommentar</th><th>Sideangivelse</th><th></th>
          </tr></thead>
          <tbody></tbody>
        </table>
      </div>
      <div id="statusDiv"><h2>Utdragene utgjør totalt xx sider av boken. Det er innenfor 15%.</h2></div>
    `;
    document.body.appendChild(container);

    // Modaler
    createModal({
        id: "editModal",
        title: "Rediger",
        label: "Sidetall",
        inputId: "antallsiderInput",
        saveButtonId: "saveChangesButton"
    });
    createModal({
        id: "editModalSidetall",
        title: "Rediger sideangivelse",
        label: "Sideangivelse (f.eks. 45-47, 89-90)",
        inputId: "sideangivelseInput",
        saveButtonId: "saveChangesButtonSidetall"
    });
}

const columnMapping = {
    0: 'id',
    1: 'title',
};

let tableData = [];
let selectedRowTable1 = null;
let selectedRowTable2 = null;
let inputPensumId = '';
let tableData2 = [];

function populateTable2(data) {
    const firstTableBody = document.getElementById('firstTable').querySelector('tbody');
    firstTableBody.innerHTML = '';

    data.forEach((item, index) => {
        const row = document.createElement('tr');

        const titleCell = document.createElement('td');
        titleCell.textContent = item.title;
        row.appendChild(titleCell);

        const forfatterCell = document.createElement('td');
        forfatterCell.textContent = item.author;
        row.appendChild(forfatterCell);

        const utgittCell = document.createElement('td');
        utgittCell.textContent = item.publication_date;
        row.appendChild(utgittCell);

        const utgittstedCell = document.createElement('td');
        utgittstedCell.textContent = item.place_of_publication;
        row.appendChild(utgittstedCell);

        const forlagCell = document.createElement('td');
        forlagCell.textContent = item.publisher;
        row.appendChild(forlagCell);

        const m300Cell = document.createElement('td');
        m300Cell.textContent = item.pages;
        row.appendChild(m300Cell);

        const antsiderCell = document.createElement('td');
        antsiderCell.textContent = item.sidetall;
        row.appendChild(antsiderCell);

        row.dataset.index = index;

        const buttonCell = document.createElement('td');
        const button = document.createElement('button');
        button.textContent = 'Fyll inn antall sider';
        button.className = 'btn btn-success';
        button.addEventListener('click', function(event) {
            event.stopPropagation();
            const rows = document.querySelectorAll('#firstTable tbody tr');
            rows.forEach(r => r.classList.remove('table-active'));
            row.classList.add('table-active');
            selectedRowTable1 = row;
            document.getElementById('antallsiderInput').value = item.sidetall;
            const modal = new bootstrap.Modal(document.getElementById('editModal'));
            modal.show();
        });
        buttonCell.appendChild(button);
        row.appendChild(buttonCell);

        row.addEventListener('click', function() {
            highlightRow(row, 'firstTable');
        });

        if (item.title && item.title.trim() === 'Kritisk og begeistret : barnehagelærernes fagpolitiske historie') {
            row.classList.add('kode12');
        }

        firstTableBody.appendChild(row);
    });
}

function populateSecondTable(data) {
    const secondTableBody = document.getElementById('secondTable').querySelector('tbody');
    secondTableBody.innerHTML = '';

    data.forEach((item, index) => {
        const row = document.createElement('tr');

        const idCell = document.createElement('td');
        idCell.textContent = item.id;
        row.appendChild(idCell);

        const chapterTitleCell = document.createElement('td');
        chapterTitleCell.textContent = item.chapter_title;
        row.appendChild(chapterTitleCell);

        const chapterCell = document.createElement('td');
        chapterCell.textContent = item.chapter;
        row.appendChild(chapterCell);

        const kapforfCell = document.createElement('td');
        kapforfCell.textContent = item.chapter_author;
        row.appendChild(kapforfCell);

        const publicnoteCell = document.createElement('td');
        publicnoteCell.textContent = item.public_note;
        row.appendChild(publicnoteCell);

        const sideangivelsefCell = document.createElement('td');
        sideangivelsefCell.textContent = item.formatted_pages || '';
        row.appendChild(sideangivelsefCell);

        row.dataset.index = index;

        const buttonCell = document.createElement('td');
        const button = document.createElement('button');
        button.textContent = 'Fyll inn sideangivelse(r)';
        button.className = 'btn btn-success';
        button.addEventListener('click', function(event) {
            event.stopPropagation();
            selectedRowTable2 = row;
            document.getElementById('sideangivelseInput').value = item.formatted_pages || '';
            const modal = new bootstrap.Modal(document.getElementById('editModalSidetall'));
            modal.show();
        });
        buttonCell.appendChild(button);
        row.appendChild(buttonCell);

        secondTableBody.appendChild(row);
    });
}

function sortTable2(columnKey, isAscending) {
    const sortedData = [...tableData].sort((a, b) => {
        const valueA = a[columnKey];
        const valueB = b[columnKey];

        if (typeof valueA === 'number' && typeof valueB === 'number') {
            return isAscending ? valueA - valueB : valueB - valueA;
        } else {
            return isAscending ? valueA.localeCompare(valueB, undefined, { sensitivity: 'base' }) : valueB.localeCompare(valueA, undefined, { sensitivity: 'base' });
        }
    });

    tableData = sortedData;
    populateTable2(tableData);
}

function highlightRow(row, tableId) {
    const rows = document.querySelectorAll(`#${tableId} tbody tr`);
    rows.forEach(r => r.classList.remove('table-active'));
    row.classList.add('table-active');
    if (tableId === 'firstTable') {
        selectedRowTable1 = row;
        const index = selectedRowTable1.dataset.index;
        const unik_bokid = tableData[index].unik_bok_id;
        const url = `/proxy.php/?endpoint=referansesjekk/hent_data&data=utdrag&pensumid=${inputPensumId}&bokid=${unik_bokid}`;
        fetch(url)
        .then(response => {
            if (response.ok) {
                return response.json();
            } else {
                throw new Error('API forespørsel feilet');
            }
        })
        .then(data => {
            const bok_array = [tableData[index]];
            const data_array = {
                array1: bok_array,
                array2: data
            };
            tableData2 = data;
            sendDataToAPI(data_array);
            populateSecondTable(data);
        })
        .catch(error => {
            console.error('Feil:', error);
        });
    } else {
        selectedRowTable2 = row;
    }
}

function sendDataToAPI(data_array) {
    fetch(`/proxy.php?endpoint=referansesjekk/kopieringssjekk`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data_array)
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        } else {
            throw new Error('API forespørsel feilet');
        }
    })
    .then(apiResponse => {
        const statusDiv = document.getElementById('statusDiv');
        statusDiv.innerHTML = apiResponse.status + '<br> - ' + apiResponse.ant_sid;
    })
    .catch(error => {
        console.error('Feil:', error);
    });
}

function beregnAntallSider(sidetallStreng) {
  if (!sidetallStreng) return 0;
  const sidetallArray = sidetallStreng.split(',');
  let totalSider = 0;
  sidetallArray.forEach(sidetall => {
    sidetall = sidetall.trim();
    const [start, slutt] = sidetall.split('-').map(Number);
    if (!isNaN(start) && !isNaN(slutt)) {
      totalSider += Math.abs(slutt - start) + 1;
    }
  });
  return totalSider;
}

function addListeners() {
    document.getElementById('referanseSjekkButton').addEventListener('click', function() {
        const inputField = document.getElementById('inputField');
        inputPensumId = inputField.value.trim();
        const loadingSpinner = document.getElementById('loadingSpinner');

        if (inputPensumId) {
            loadingSpinner.style.visibility = 'visible';

            const url = `/proxy.php?endpoint=referansesjekk/hent_data&data=bok&pensumid=${inputPensumId}`;
            fetch(url)
            .then(response => {
                if (response.ok) {
                    return response.json();
                } else {
                    throw new Error('API forespørsel feilet');
                }
            })
            .then(data => {
                tableData = data;
                populateTable2(tableData);
            })
            .catch(error => {
                console.error('Feil:', error);
            })
            .finally(() => {
                loadingSpinner.style.visibility = 'hidden';
            });
        }
    });

    // Sortering på forfatter-kolonnen
    document.querySelectorAll('#firstTable thead th.sortable').forEach((header) => {
        let isAscending = true;
        header.addEventListener('click', () => {
            const index = header.getAttribute('data-column-index');
            const columnKey = columnMapping[index];
            if (columnKey) {
                sortTable2(columnKey, isAscending);
                document.querySelectorAll('#firstTable thead th').forEach(th => {
                    th.classList.remove('asc', 'desc');
                });
                header.classList.add(isAscending ? 'asc' : 'desc');
                isAscending = !isAscending;
            } else {
                console.error(`No column key found for index: ${index}`);
            }
        });
    });

    document.getElementById('saveChangesButton').addEventListener('click', function() {
        if (selectedRowTable1) {
            const newValue = document.getElementById('antallsiderInput').value;
            selectedRowTable1.cells[6].textContent = newValue;
            const index = selectedRowTable1.dataset.index;
            tableData[index].sidetall = newValue;
            const bok_array = [tableData[index]];
            const data_array = {
                array1: bok_array,
                array2: tableData2
            };
            sendDataToAPI(data_array);
            const modalElement = document.getElementById('editModal');
            const modalInstance = bootstrap.Modal.getInstance(modalElement);
            modalInstance.hide();
        }
    });

    document.getElementById('saveChangesButtonSidetall').addEventListener('click', function() {
        if (selectedRowTable2) {
            const newValue = document.getElementById('sideangivelseInput').value.trim();
            const index = selectedRowTable2.dataset.index;
            tableData2[index].formatted_pages = newValue;
            selectedRowTable2.cells[5].textContent = newValue;

            const indexTable1 = selectedRowTable1?.dataset?.index;
            const bok_array = indexTable1 !== undefined ? [tableData[indexTable1]] : [];
            const data_array = {
                array1: bok_array,
                array2: tableData2
            };
            sendDataToAPI(data_array);

            const modalElement = document.getElementById('editModalSidetall');
            const modalInstance = bootstrap.Modal.getInstance(modalElement);
            modalInstance.hide();
        } else {
            console.error('Ingen rad valgt i tabell 2.');
        }
    });
}

// Kjør når DOM er klar: først bygg UI, så bind listeners!
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function() {
        injectCustomCSS();
        createUI();
        addListeners();
    });
} else {
    injectCustomCSS();
    createUI();
    addListeners();
}
</script>
