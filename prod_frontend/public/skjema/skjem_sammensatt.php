<div class="bg-secondary">
  <label for="add_file_name" class="form-label mt-3">
    Legg til filnavn ved å enten droppe filer, eller ved å skrive inn manuelt
    (filnavn skilles med komma, hvis flere filer)
  </label>
  <div class="d-flex justify-content-between">
    <div id="drop_zone" class="border border-light flex-fill me-3 d-flex justify-content-center align-items-center" style="height: 200px; width:220px;">
        Dropp filer her
    </div>
    <div class="col-md-10">
      <div class="input-group input-group-lg">
        <div class="form-floating">
          <input type="text" class="form-control" id="add_file_name" placeholder="" aria-label="Felt hvor man legger inn filnavn som skal legges til i filen" name="add_file_name" autocomplete="off">
          <label for="add_file_name">filnavn</label>
        </div>
      </div>
    </div>
  </div>
  <button id="add_file_name_button" class="btn btn-info mb-1">Legg til filnavn</button>
</div>

<form id="SammensattSkjema">
  <div class="row g-3">
    <div class="col-md-4">
      <div class="input-group input-group-lg">
        <div class="form-floating">
          <input type="text" class="form-control" id="filnavn" placeholder="" aria-label="Felt for filnavn til den sammensatte filen" name="filnavn">
          <label for="filnavn">Filnavn på sammensatt fil</label>
        </div>
      </div>
    </div>
    <span>Velg filnavn du har lagt til, og deretter gå gjennom og endre/legg til sideangivelse der det er nødvendig</span>
    <div class="col-md-7">
      <div class="form-floating">
        <div class="input-group input-group-lg">
          <select id="file_select" class="form-select" size="10" aria-label="Size 3 select example"></select>
        </div>
      </div>
      <div class="d-flex justify-content-between mt-2">
        <button type="button" id="move_up" class="btn btn-secondary">Flytt opp</button>
        <button type="button" id="move_down" class="btn btn-secondary">Flytt ned</button>
      </div>
    </div>
    <div class="col-md-4">
      <div class="input-group input-group-lg">
        <div class="form-floating">
          <input type="text" class="form-control" id="page_number" placeholder="" aria-label="Felt for sideangivelse">
          <label for="page_number">Sideangivelse(r)</label>
        </div>
      </div>
    </div>
  </div>
  <div class="row g-3 mt-3">
    <div class="col-md-12">
      <div class="form-floating">
        <input type="hidden" class="form-control" id="fil_bestar_av" placeholder="" aria-label="Liste over filnavn" readonly name="fil_bestar_av">
      </div>
    </div>
    <div class="col-md-12 mt-3">
      <div class="form-floating">
        <input type="hidden" class="form-control" id="sideangivelse" placeholder="" aria-label="Liste over sideangivelser" readonly name="sideangivelse">
      </div>
    </div>
  </div>
<input type="hidden" id="mange_sideangivelser" value="0" name="mange_sideangivelser">
<input type="hidden" readonly value="3" name="doktype_id">
<button type="submit" class="btn btn-primary btn-lg" aria-label="Knapp for å sende inn skjemaet">Legg til nytt bokutdrag i filoversikt</button>
</form>

<div id="respons" class="mt-2"></div>

<script>
// Sett denne variabelen fra PHP/server eller hardkod hvis du skal teste lokalt
// Eksempel: var json_bokutdrag_nc = "/din/path/filoversikt.json";
</script>

<script>
function sammensattScript(){
document.getElementById('drop_zone').addEventListener('drop', handleFileDrop, false);
document.getElementById('drop_zone').addEventListener('dragover', handleDragOver, false);
document.getElementById('file_select').addEventListener('change', handleFileSelectChange, false);
document.getElementById('move_up').addEventListener('click', moveUp, false);
document.getElementById('move_down').addEventListener('click', moveDown, false);
document.getElementById('page_number').addEventListener('input', handlePageNumberInput, false);
document.getElementById('add_file_name_button').addEventListener('click', addFileNameManually, false);

let fileDataMap = {};

function addFileNameManually() {
  const inputField = document.getElementById('add_file_name');
  const rawValue = inputField.value.trim();
  if (rawValue) {
    // Split på komma og fjern ekstra mellomrom
    const fileNames = rawValue.split(',').map(f => f.trim()).filter(f => f.length > 0);
    const fileSelect = document.getElementById('file_select');
    fileNames.forEach(fileName => {
      let existsInSelect = false;
      for (let i = 0; i < fileSelect.options.length; i++) {
        if (fileSelect.options[i].value === fileName) {
          existsInSelect = true;
          break;
        }
      }
      if (!existsInSelect) {
        const option = document.createElement('option');
        option.value = fileName;
        option.text = fileName;
        fileSelect.appendChild(option);
        fetchPageNumbers([fileName]).then(() => {
          updateFileList();
          updatePageList();
        });
      }
    });
  } else {
    alert('Vennligst skriv inn et filnavn.');
  }
  inputField.value = '';
}

function handleDragOver(event) {
  event.stopPropagation();
  event.preventDefault();
  event.dataTransfer.dropEffect = 'copy';
}

function handleFileDrop(event) {
  event.stopPropagation();
  event.preventDefault();

  const files = event.dataTransfer.files;
  const fileNames = [];

  for (let i = 0; i < files.length; i++) {
    const fileName = files[i].name.split('.').slice(0, -1).join('.');
    if (!fileDataMap.hasOwnProperty(fileName)) { // Sjekk om filen allerede finnes
      fileNames.push(fileName);
    }
  }

  if (fileNames.length > 0) {
    updateFileSelect(fileNames, true); // Legg til nye filer uten å tømme eksisterende
    fetchPageNumbers(fileNames);
  }
}

function updateFileSelect(fileNames, append = false) {
  const fileSelect = document.getElementById('file_select');
  if (!append) {
    fileSelect.innerHTML = '';
  }

  fileNames.forEach(fileName => {
    const option = document.createElement('option');
    option.value = fileName;
    option.text = fileName;
    fileSelect.appendChild(option);
  });

  updateFileList();
  updatePageList();
}

function fetchPageNumbers(fileNames) {
  // Du må definere json_bokutdrag_nc i egen <script> før denne koden
  if (typeof json_bokutdrag_nc === 'undefined') return Promise.resolve();
  return fetch(json_bokutdrag_nc)
    .then(response => response.json())
    .then(data => {
      const records = data.response.data;
      fileNames.forEach(fileName => {
        const record = records.find(item => item.fieldData.filnavn === fileName);
        if (record) {
          if (!fileDataMap[fileName]) {
            fileDataMap[fileName] = [];
          }
          fileDataMap[fileName].push(record.fieldData.sideangivelse);
        } else {
          fileDataMap[fileName] = [];
        }
      });
      updatePageList();
    })
    .catch(error => console.error('Error fetching page numbers:', error));
}

function handleFileSelectChange(event) {
  const selectedFileName = event.target.value;
  const pageNumberInput = document.getElementById('page_number');
  pageNumberInput.value = (fileDataMap[selectedFileName] || []).join(', ');
}

function handlePageNumberInput(event) {
  const selectedFileName = document.getElementById('file_select').value;
  const newPageNumber = event.target.value;

  // Fjern alle tilfeller av mer enn ett komma på rad
  const cleanedPageNumber = newPageNumber.replace(/,+\s*/g, ", ").replace(/,\s*$/, "");

  if (selectedFileName) {
    if (!fileDataMap[selectedFileName]) {
      fileDataMap[selectedFileName] = [];
    }
    fileDataMap[selectedFileName] = [cleanedPageNumber];
    updatePageList();
    const allPageNumbers = document.getElementById('sideangivelse').value;
    updateUniquePageRangesResult(allPageNumbers);
  }
}

function moveUp() {
  const fileSelect = document.getElementById('file_select');
  const selectedIndex = fileSelect.selectedIndex;

  if (selectedIndex > 0) {
    const option = fileSelect.options[selectedIndex];
    const previousOption = fileSelect.options[selectedIndex - 1];
    fileSelect.remove(selectedIndex);
    fileSelect.add(option, previousOption);
    fileSelect.selectedIndex = selectedIndex - 1;
    updateFileList();
    updatePageList();
  }
}

function moveDown() {
  const fileSelect = document.getElementById('file_select');
  const selectedIndex = fileSelect.selectedIndex;

  if (selectedIndex < fileSelect.options.length - 1) {
    const option = fileSelect.options[selectedIndex];
    const nextOption = fileSelect.options[selectedIndex + 1];
    fileSelect.remove(selectedIndex);
    fileSelect.add(option, nextOption.nextSibling);
    fileSelect.selectedIndex = selectedIndex + 1;
    updateFileList();
    updatePageList();
  }
}

function updateFileList() {
  const fileSelect = document.getElementById('file_select');
  const fileList = [];

  for (let i = 0; i < fileSelect.options.length; i++) {
    fileList.push(fileSelect.options[i].text);
  }

  document.getElementById('fil_bestar_av').value = fileList.join(', ');
}

function updatePageList() {
  const fileSelect = document.getElementById('file_select');
  const pageList = [];

  for (let i = 0; i < fileSelect.options.length; i++) {
    const fileName = fileSelect.options[i].value;
    const pageNumbersList = fileDataMap[fileName] || [];
    const pageNumbers = pageNumbersList.join(', ');
    if (pageNumbers) {
      pageList.push(pageNumbers);
    }
  }
  document.getElementById('sideangivelse').value = pageList.join(', ');

  const allPageNumbers = document.getElementById('sideangivelse').value;
  updateUniquePageRangesResult(allPageNumbers);
}

function sortPageNumbers(pageNumbers) {
  let pages = pageNumbers.split(',').map(s => s.trim());
  pages.sort((a, b) => {
    let aFirstPage = parseInt(a.split('-')[0]);
    let bFirstPage = parseInt(b.split('-')[0]);
    return aFirstPage - bFirstPage;
  });
  return pages.join(', ');
}

function hasMoreThanTwoUniquePageRanges(pageNumbers) {
  let pages = pageNumbers.split(',').map(s => s.trim()).sort((a, b) => {
    let aFirstPage = parseInt(a.split('-')[0]);
    let bFirstPage = parseInt(b.split('-')[0]);
    return aFirstPage - bFirstPage;
  });

  let uniquePageRanges = [];
  let previousEndPage = -1;

  for (let pageRange of pages) {
    let [startPage, endPage] = pageRange.split('-').map(Number);
    if (startPage > previousEndPage + 1) {
      uniquePageRanges.push(pageRange);
    }
    previousEndPage = Math.max(endPage, previousEndPage);
  }

  return uniquePageRanges.length > 2 ? 1 : 0;
}

function updateUniquePageRangesResult(pageNumbers) {
  const sortedNumbers = sortPageNumbers(pageNumbers);
  const result = hasMoreThanTwoUniquePageRanges(sortedNumbers);
  document.getElementById('mange_sideangivelser').value = result;
}
}
document.addEventListener('DOMContentLoaded', sammensattScript);
</script>

<script>
(function() {
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}
const brukerCookie = getCookie('data');
let token = null;
if (brukerCookie) {
    try {
        const parsed = JSON.parse(decodeURIComponent(brukerCookie));
        token = parsed.token;
    } catch (e) { token = null; }
}

    var leggtilfil_success_1 = `<div class="alert alert-success light-mode alert-dismissible fade show" role="alert">
<svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="currentColor" class="bi bi-check-circle" viewBox="0 0 16 16">
<path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14m0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16"/>
<path d="m10.97 4.97-.02.022-3.473 4.425-2.093-2.094a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-1.071-1.05"/>
</svg>
&nbsp;&nbsp;Filen ved navn <strong>`;

    var leggtilfil_success_2 = `</strong> ble lagt til i filoversikten!
<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
</div>`;

function handleSkjema() {
    const skjema = document.getElementById('SammensattSkjema');
    if (!skjema) return;

    skjema.addEventListener('submit', function(e) {
        e.preventDefault();
        const responsDiv = document.getElementById('respons');
        responsDiv.textContent = '';
        const formData = new FormData(skjema);
        const skjemaData = {};
        formData.forEach((value, key) => {
            skjemaData[key] = value;
        });
        skjemaData.token = token;
        // Debug:
        console.log("Sender data:", skjemaData);

        sendData(skjemaData, skjema, responsDiv);
    });
}

async function sendData(data, skjema, responsDiv) {
    responsDiv.textContent = 'Sender data...';
    responsDiv.classList.remove('text-danger');
    try {
        const respons = await fetch('/proxy.php?endpoint=filoversikt/leggtil', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        let res;
        try {
            res = await respons.json();
        } catch (e) { res = {}; }
        if (respons.ok) {
            responsDiv.textContent = '';
            var successMessage = leggtilfil_success_1 + `${data.filnavn}` + leggtilfil_success_2;
            document.querySelector('#successDiv').innerHTML = successMessage;
            
            // ======= EKSTRA NULLSTILLING ETTER SUKSESS =======
            skjema.reset();

            // Tøm dynamiske felter og JS-data
            const fileSelect = document.getElementById('file_select');
            if (fileSelect) fileSelect.innerHTML = '';

            const filBestarAv = document.getElementById('fil_bestar_av');
            if (filBestarAv) filBestarAv.value = '';

            const sideangivelse = document.getElementById('sideangivelse');
            if (sideangivelse) sideangivelse.value = '';

            const mangeSideangivelser = document.getElementById('mange_sideangivelser');
            if (mangeSideangivelser) mangeSideangivelser.value = '0';

            const addFileName = document.getElementById('add_file_name');
            if (addFileName) addFileName.value = '';

            const pageNumber = document.getElementById('page_number');
            if (pageNumber) pageNumber.value = '';

            // Nullstill fileDataMap hvis det finnes og er globalt tilgjengelig
            if (typeof fileDataMap !== "undefined" && fileDataMap) {
                for (let key in fileDataMap) delete fileDataMap[key];
            }
            // Oppdater visning hvis du har slike funksjoner
            if (typeof updateFileList === "function") updateFileList();
            if (typeof updatePageList === "function") updatePageList();
            // ======= SLUTT EKSTRA NULLSTILLING =======
        } else {
            let feilmelding = res && res.detail;
            if (typeof feilmelding !== 'string') {
                feilmelding = JSON.stringify(feilmelding) || 'Ukjent feil';
            }
            document.querySelector('#hello .modal-body').innerHTML = 'Feil: ' + feilmelding;
            var myModal = new bootstrap.Modal(document.getElementById('hello'), {});
            myModal.show();
        }
    } catch (err) {
        responsDiv.textContent = 'Teknisk feil: ' + err;
        responsDiv.classList.add('text-danger');
    }
}

// Aktiver straks DOM er klar:
if (document.readyState === "loading") {
    document.addEventListener('DOMContentLoaded', handleSkjema);
} else {
    handleSkjema();
}
})();
</script>
