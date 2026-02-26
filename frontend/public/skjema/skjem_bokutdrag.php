        <form id="BokutdragSkjema">
<div class="row g-3">
  <!-- 1 - FILNAVN -->
  <div class="col-md-4">
    <div class="input-group input-group-lg">
      <button class="btn btn-primary" type="button" id="changeToDropdown" aria-label="Knapp for å få opp listse over uregistrerte filer">Hent uregistrerte filer</button>
<div class="form-floating">
        <input type="text" class="form-control" id="filnavn" placeholder="" aria-label="Felt for filnavn" name="filnavn" value="<?php echo isset($_SESSION['form_data']['filnavn']) ? $_SESSION['form_data']['filnavn'] : ''; ?>">
        <label for="filnavn">Filnavn</label>
      </div>
    </div>
  </div>

  <!-- 2 - SKANNJOBB-ID -->
  <div class="col-md-4">
    <div class="input-group input-group-lg">
      <button class="btn btn-secondary" type="button" id="button-skannjobb" disabled>Hent ID (hvis finnes)</button>
      <div class="form-floating">
        <input type="text" class="form-control" id="skannjobb_id" placeholder="" aria-label="Felt for skannjobb-ID" name="skannjobb_id" value="<?php echo isset($_SESSION['form_data']['skannjobb_id']) ? $_SESSION['form_data']['skannjobb_id'] : ''; ?>">
        <label for="skannjobb_id">Skannjobb-ID</label>
      </div>
    </div>
  </div>

  <!-- 3 - SIDEANGIVELSE(R) -->
  <div class="col-md-4">
    <div class="input-group input-group-lg">
      <div class="form-floating">
        <input type="text" class="form-control" id="sideangivelse" placeholder="" aria-label="Felt for sideangivelser" name="sideangivelse" value="<?php echo isset($_SESSION['form_data']['sideangivelse']) ? $_SESSION['form_data']['sideangivelse'] : ''; ?>">
        <label for="sideangivelse">Sideangivelse(r)</label>
      </div>
    </div>
  </div>

  <!-- 4 - BOKTITTEL -->
  <div class="col-md-7">
    <div class="input-group input-group-lg">
      <div class="form-floating">
        <input type="text" class="form-control" id="boktittel" placeholder="" aria-label="Felt for boktittel" name="boktittel" value="<?php echo isset($_SESSION['form_data']['boktittel']) ? $_SESSION['form_data']['boktittel'] : ''; ?>">
        <label for="boktittel">Boktittel*</label>
      </div>
    </div>
  </div>

  <!-- 5 - FORFATTER(E) -->
  <div class="col-md-5">
    <div class="input-group input-group-lg">
      <div class="form-floating">
        <input type="text" class="form-control" id="forfattere" placeholder="" aria-label="Felt for forfattere av boken" name="forfatter" value="<?php echo isset($_SESSION['form_data']['forfatter']) ? $_SESSION['form_data']['forfatter'] : ''; ?>">
        <label for="forfattere">Forfatter(e)</label>
      </div>
    </div>
  </div>

  <!-- 6 - ISBN -->
  <div class="col-md-5">
    <div class="input-group input-group-lg">
      <button class="btn btn-primary" type="button" id="button-sjekk-isbn" aria-label="Knapp for sjekk av ISBN-nummer">Sjekk ISBN</button>
      <button class="btn btn-secondary" type="button" id="button-rens-isbn" aria-label="Knapp for rens av bokdata">Rens bokdata</button>
      <div class="form-floating">
        <input type="text" class="form-control" id="isbn" placeholder="" aria-label="Felt for ISBN-nummer" name="isbn" value="<?php echo isset($_SESSION['form_data']['isbn']) ? $_SESSION['form_data']['isbn'] : ''; ?>">
        <label for="isbn">ISBN (uten bindestreker - kun sifferne)</label>
      </div>
    </div>
  </div>

  <!-- 7 - UTGITT -->
  <div class="col-md-2">
    <div class="input-group input-group-lg">
      <div class="form-floating">
        <input type="text" class="form-control" id="utgitt" placeholder="" aria-label="Felt for når boken er utgitt" name="utgitt" value="<?php echo isset($_SESSION['form_data']['utgitt']) ? $_SESSION['form_data']['utgitt'] : ''; ?>">
        <label for="utgitt">Utgitt</label>
      </div>
    </div>
  </div>

  <!-- 8 - FORLAG -->
  <div class="col-md-5">
    <div class="input-group input-group-lg">
      <div class="form-floating">
        <input type="text" class="form-control" id="forlag" placeholder="" aria-label="Felt for forlag" name="forlag" value="<?php echo isset($_SESSION['form_data']['forlag']) ? $_SESSION['form_data']['forlag'] : ''; ?>">
        <label for="forlag">Forlag</label>
      </div>
    </div>
  </div>

  <!-- 9 - KAPITTELNUMMER -->
  <div class="col-md-3">
    <div class="input-group input-group-lg">
      <div class="form-floating">
        <input type="text" class="form-control" id="kapittelnummer" placeholder="" aria-label="Felt for kapittel-nummer" name="kapittelnummer" value="<?php echo isset($_SESSION['form_data']['kapittelnummer']) ? $_SESSION['form_data']['kapittelnummer'] : ''; ?>">
        <label for="kapittelnummer">Kapittel (nummer)</label>
      </div>
    </div>
  </div>

  <!-- 10 - KAPITTELTITTEL -->
  <div class="col-md-9">
    <div class="input-group input-group-lg">
      <div class="form-floating">
        <input type="text" class="form-control" id="kapitteltittel" placeholder="" aria-label="Felt for kapittelets tittel" name="kapitteltittel" value="<?php echo isset($_SESSION['form_data']['kapitteltittel']) ? $_SESSION['form_data']['kapitteltittel'] : ''; ?>">
        <label for="kapitteltittel">Kapitteltittel</label>
      </div>
    </div>
  </div>

  <!-- 11 - KAPITTELFORFATTER(E) -->
  <div class="col-md-12">
    <div class="input-group input-group-lg">
      <div class="form-floating">
        <input type="text" class="form-control" id="kapittelforfatter" placeholder="" aria-label="Felt for kapittelets forfattere" name="kapittelforfatter" value ="<?php echo isset($_SESSION['form_data']['kapittelforfatter']) ? $_SESSION['form_data']['kapittelforfatter'] : ''; ?>">
        <label for="kapittelforfatter">Kapittelforfatter(e)</label>
      </div>
    </div>
  </div>

  <!-- 12 - UTGAVE -->
  <div class="col-md-12">
    <div class="input-group input-group-lg">
      <div class="form-floating">
        <input type="text" class="form-control" id ="utgave" placeholder="" aria-label="Felt for utgave-opplysninger" name="merknad" value="<?php echo isset($_SESSION['form_data']['merknad']) ? $_SESSION['form_data']['merknad'] : ''; ?>">
        <label for="utgave">Utgave (hvis 1. utgave, skrives det ikke inn)</label>
      </div>
        <button class="btn btn-primary" type="button" id="utgave_hjelp" aria-label="Knapp for visning av hjelp til utfylling av utgave">
<svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="currentColor" class="bi bi-question-circle" viewBox="0 0 16 16">
  <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14m0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16"/>
  <path d="M5.255 5.786a.237.237 0 0 0 .241.247h.825c.138 0 .248-.113.266-.25.09-.656.54-1.134 1.342-1.134.686 0 1.314.343 1.314 1.168 0 .635-.374.927-.965 1.371-.673.489-1.206 1.06-1.168 1.987l.003.217a.25.25 0 0 0 .25.246h.811a.25.25 0 0 0 .25-.25v-.105c0-.718.273-.927 1.01-1.486.609-.463 1.244-.977 1.244-2.056 0-1.511-1.276-2.241-2.673-2.241-1.267 0-2.655.59-2.75 2.286m1.557 5.763c0 .533.425.927 1.01.927.609 0 1.028-.394 1.028-.927 0-.552-.42-.94-1.029-.94-.584 0-1.009.388-1.009.94"/>
</svg>
</button>
    </div>
  </div>

          <!-- 13 - kOMMENTAR -->
  <div class="col-md-12">
    <div class="input-group input-group-lg">
      <div class="form-floating">
        <input type="text" class="form-control" id ="kommentar" placeholder="" aria-label="Felt for andre kommentarer eller opplysninger" name="kommentar" value="<?php echo isset($_SESSION['form_data']['kommentar']) ? $_SESSION['form_data']['kommentar'] : ''; ?>">
        <label for="kommentar">Kommentar</label>
      </div>
    </div>
  </div>

          <!-- 14 - MANGLER I/VED FIL -->
  <div class="col-md-12">
    <div class="input-group input-group-lg">
      <div class="form-floating">
        <input type="text" class="form-control" id ="mangler_i_fil" placeholder="" aria-label="Felt for opplysninger om mangler ved eller i fil" name="mangler_i_fil" value="<?php echo isset($_SESSION['form_data']['mangler_i_fil']) ? $_SESSION['form_data']['angler_i_fil'] : ''; ?>">
        <label for="mangler_i_fil">Mangler i eller ved fil</label>
      </div>
    </div>
  </div>

<input type="hidden" readonly value="1" name="doktype_id">
<div class="col-md-12">
                        <button type="submit" class="btn btn-primary btn-lg" aria-label="Knapp for å sende inn skjemaet">Legg til nytt bokutdrag i filoversikt</button>
                        <button type="button" class="btn btn-secondary btn-lg" aria-label="Knapp for å rense data i skjemaet (fjerne alle data)" id="rens_data">Tøm skjema</button>
        </div>
</div>
                </form>

    <div class="mt-2">
        <button type="button" id="fyllMedLagret" class="btn btn-outline-secondary btn-sm">Fyll ut med lagrede data</button>
    </div>
    <div id="respons" class="mt-3"></div>

<script>
function bokutdragScript() {

    var success_1 = `<div class="alert alert-success light-mode alert-dismissible fade show" role="alert">
<svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="currentColor" class="bi bi-check-circle" viewBox="0 0 16 16">
<path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14m0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16"/>
<path d="m10.97 4.97-.02.022-3.473 4.425-2.093-2.094a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-1.071-1.05"/>
</svg>
&nbsp;&nbsp;Filen ved navn <strong>`;

    var success_2 = `</strong> ble lagt til i filoversikten!
<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
</div>`;

  // === KONSTANTER OG INIT ===
  const LOCALSTORAGE_KEY = 'BokutdragSkjemaData';
  let lastIsbn = '';
  let found_isbn = false;
  const ureg_bok = '/json/ureg_bok.txt';
  const json_bok_unik_isbn = '/json/json_bok_unik.txt';

  // === MODAL-FUNKSJONER ===
  function showModal(id, message) {
    const modalBody = document.getElementById(id + 'Body');
    if (modalBody) modalBody.textContent = message;
    const modalDiv = document.getElementById(id);
    if (modalDiv) {
      const modal = new bootstrap.Modal(modalDiv);
      modal.show();
    }
  }

  // === COOKIE & TOKEN-HÅNDTERING ===
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

  // === INIT ===
  var skjema = document.getElementById('BokutdragSkjema');
  var fyllMedLagretBtn = document.getElementById('fyllMedLagret');
  var skjemaData = null;

  autofillSkjemaFraLagring();
  oppdaterFyllMedLagretKnapp();

  // === Autosave på alle felter ===
  if (skjema) {
    skjema.querySelectorAll('input, textarea, select').forEach(function(el) {
      el.addEventListener('input', autosaveSkjema);
    });
  }

  // === Skjemainnsending ===
  if (skjema) {
    skjema.addEventListener('submit', function(e) {
      e.preventDefault();
      const responsDiv = document.getElementById('respons');
      responsDiv.textContent = '';
      const filnavn = document.getElementById('filnavn').value;
      const isbn = document.getElementById('isbn').value;
      const boktittel = document.getElementById('boktittel').value.trim();

      // Filnavn-validering
      if (!filnavn) {
        showModal('filnavnModal', "Feltet for FILNAVN kan ikke være tomt.");
        return;
      }
      const filnavnRegex = /^(19|20)\d\d_(0[1-9]|1[0-2])_(0[1-9]|[12][0-9]|3[01])_([01][0-9]|2[0-3])[0-5][0-9]$/;
      if (!filnavnRegex.test(filnavn)) {
        showModal('filnavnModal', "Feil filformat for FILNAVN: Det skal være skrevet i formatet ÅÅÅÅ_MM_DD_HHTT (HHTT = klokkeslett, f.eks. 2024_09_02_1330)");
        return;
      }

// Før du samler inn FormData, åpne alle felter som er disabled
skjema.querySelectorAll('input:disabled, textarea:disabled, select:disabled').forEach(function(el) {
    el.disabled = false;
});

      const formData = new FormData(skjema);
      skjemaData = {};
      formData.forEach((value, key) => {
        skjemaData[key] = value;
      });
      skjemaData.token = token;

      // Ikke innlogget: lagre data og informer, men stopp innsending
      if (!token) {
        showModal('errorModal', 'Feil: Du må være innlogget for å kunne sende inn. Skjemadataene dine er lagret.');
        localStorage.setItem(LOCALSTORAGE_KEY, JSON.stringify(skjemaData));
        oppdaterFyllMedLagretKnapp();
        return;
      }

      if (!isbn) {
        const isbnModal = new bootstrap.Modal(document.getElementById('isbnModal'));
        isbnModal.show();
      } else {
        sendData(skjemaData);
      }
    });
  }

  // === FYLL SKJEMA FRA localStorage VED KNAPPETRYKK ===
  if (fyllMedLagretBtn) {
    fyllMedLagretBtn.addEventListener('click', function() {
      const lagret = localStorage.getItem(LOCALSTORAGE_KEY);
      if (!lagret) {
        alert("Ingen data lagret.");
        return;
      }
      try {
        const data = JSON.parse(lagret);
        Object.keys(data).forEach(key => {
          const felt = skjema.querySelector(`[name="${key}"]`);
          if (felt) felt.value = data[key];
        });
        localStorage.removeItem(LOCALSTORAGE_KEY);
        oppdaterFyllMedLagretKnapp();
      } catch (e) {
        alert("Kunne ikke lese lagrede data.");
      }
    });
  }

  // === AUTOSAVE-FUNKSJON ===
  function autosaveSkjema() {
    if (!skjema) return;
    const formData = new FormData(skjema);
    const skjemaData = {};
    formData.forEach((value, key) => {
      skjemaData[key] = value;
    });
    skjemaData.token = token;
    localStorage.setItem(LOCALSTORAGE_KEY, JSON.stringify(skjemaData));
    oppdaterFyllMedLagretKnapp();
  }

  // === AUTOFILL-FUNKSJON ===
  function autofillSkjemaFraLagring() {
    if (!skjema) return;
    const lagret = localStorage.getItem(LOCALSTORAGE_KEY);
    if (lagret) {
      try {
        const data = JSON.parse(lagret);
        Object.keys(data).forEach(key => {
          const felt = skjema.querySelector(`[name="${key}"]`);
          if (felt) felt.value = data[key];
        });
      } catch (e) { }
    }
  }

  // === SKJUL "FYLL MED LAGRET"-KNAPP HVIS INGEN DATA ===
  function oppdaterFyllMedLagretKnapp() {
    if (!fyllMedLagretBtn) return;
    if (!localStorage.getItem(LOCALSTORAGE_KEY)) {
      fyllMedLagretBtn.style.display = 'none';
    } else {
      fyllMedLagretBtn.style.display = '';
    }
  }

  // === SEND DATA (AJAX) MODAL-HÅNDTERING ===
  async function sendData(data) {
    const responsDiv = document.getElementById('respons');
    responsDiv.textContent = 'Sender data...';
    responsDiv.classList.remove('text-danger');
    try {
      const respons = await fetch('proxy.php?endpoint=filoversikt/leggtil', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      let res;
      try {
        res = await respons.json();
      } catch (e) { res = {}; }
      if (respons.ok) {
        var successMessage = success_1 + data.filnavn + success_2;
        document.querySelector('#successDiv').innerHTML = successMessage;
        responsDiv.textContent = 'Data lagret!';
        skjema.reset();
        document.querySelectorAll('#BokutdragSkjema input, #BokutdragSkjema textarea, #BokutdragSkjema select').forEach(el => {
          el.readOnly = false; el.disabled = false;
        });
        localStorage.removeItem(LOCALSTORAGE_KEY);
        oppdaterFyllMedLagretKnapp();
      } else {
        let feilmelding = res && res.detail;
        if (!feilmelding || typeof feilmelding !== 'string') {
          feilmelding = JSON.stringify(feilmelding) || 'Ukjent feil';
        }
        showModal('errorModal', 'Feil: ' + feilmelding);
        localStorage.setItem(LOCALSTORAGE_KEY, JSON.stringify(data));
        oppdaterFyllMedLagretKnapp();
      }
    } catch (err) {
      showModal('errorModal', 'Teknisk feil: ' + err);
      responsDiv.textContent = 'Teknisk feil: ' + err;
      responsDiv.classList.add('text-danger');
      localStorage.setItem(LOCALSTORAGE_KEY, JSON.stringify(data));
      oppdaterFyllMedLagretKnapp();
    }
  }

  // === AVANSERT: EKSTERNE FUNKSJONER (JQUERY) ===
  ChangeInputToDropdownOrDropdownToInput();
  isbnButtonEventListener();
  resetButtonEventListener();
  scanJobButtonEventListener();
  clearDataButtonEventListener();

  // === MODAL-BUTTONS ===
var bekreftUtenISBNBtn = document.getElementById('bekreftUtenISBN');
if (bekreftUtenISBNBtn) {
  bekreftUtenISBNBtn.addEventListener('click', function() {
    const isbnModal = bootstrap.Modal.getInstance(document.getElementById('isbnModal'));
    if (isbnModal) isbnModal.hide();
    sendData(skjemaData);
  });
}

  // === JQUERY-FUNKSJONER ===
  function ChangeInputToDropdownOrDropdownToInput() {
    $('#changeToDropdown, #changeToInput').off('click').on('click', function () {
      if (this.id === 'changeToInput') {
        $('#button-skannjobb').attr('disabled', true);
        $('#button-skannjobb').removeClass().addClass('btn btn-secondary');
        var dropdown = document.getElementById('filnavn');
        var inputField = document.createElement('input');
        inputField.id = 'filnavn';
        inputField.name = 'filnavn';
        inputField.type = 'text';
        inputField.classList.add('form-control');
        dropdown.parentNode.replaceChild(inputField, dropdown);
        this.id = 'changeToDropdown';
        this.className = 'btn btn-primary';
        $('#eksisterende_til_sletting').val(0);
      } else {
        $('#button-skannjobb').attr('disabled', false);
        $('#button-skannjobb').removeClass().addClass('btn btn-primary');
        var inputField = document.getElementById('filnavn');
        var dropdown = document.createElement('select');
        dropdown.id = 'filnavn';
        dropdown.name = 'filnavn';
        dropdown.classList.add('form-select');
        inputField.parentNode.replaceChild(dropdown, inputField);
        var button = document.getElementById('changeToDropdown');
        button.id = 'changeToInput';
        button.className = 'btn btn-secondary';
        var url = ureg_bok + "?_=" + new Date().getTime();
        fetch(url)
          .then(response => response.json())
          .then(data => {
            data.forEach(item => {
              var option = document.createElement('option');
              option.value = item.filnavn;
              option.text = item.filnavn;
              dropdown.add(option);
            });
          })
          .catch(error => console.error('Error:', error));
        $('#eksisterende_til_sletting').val(1);
      }
    });
  }

  function isbnButtonEventListener() {
    $('#button-sjekk-isbn').off('click').on('click', function () {
      var isbnNumber = $('#isbn').val();
      var url = json_bok_unik_isbn + "?_=" + new Date().getTime();
      fetch(url)
        .then(response => response.json())
        .then(data => {
          var matchingItem = data.response.data.find(item => item.fieldData.isbn === isbnNumber);
          if (matchingItem) {
            $('#boktittel').val(matchingItem.fieldData.boktittel).attr('readonly', true).attr('disabled', true);
            $('#forfattere').val(matchingItem.fieldData.forfatter).attr('readonly', true).attr('disabled', true);
            $('#utgitt').val(matchingItem.fieldData.utgitt).attr('readonly', true).attr('disabled', true);
            $('#forlag').val(matchingItem.fieldData.forlag).attr('readonly', true).attr('disabled', true);
            $('#utgave').val(matchingItem.fieldData.merknad).attr('readonly', true).attr('disabled', true);
            found_isbn = true;
            lastIsbn = isbnNumber;
          }
        })
        .catch(error => console.error('Error:', error));
    });
  }

  function resetButtonEventListener() {
    $('#button-rens-isbn').off('click').on('click', function () {
      var isbn = $('#isbn').val();
      if (found_isbn === true && isbn !== lastIsbn) {
        $('#boktittel').val('').attr('readonly', false).attr('disabled', false);
        $('#forfattere').val('').attr('readonly', false).attr('disabled', false);
        $('#utgitt').val('').attr('readonly', false).attr('disabled', false);
        $('#forlag').val('').attr('readonly', false).attr('disabled', false);
        $('#utgave').val('').attr('readonly', false).attr('disabled', false);
        lastIsbn = isbn;
      }
    });
  }

  function scanJobButtonEventListener() {
    $('#button-skannjobb').off('click').on('click', function () {
      var fileName = $('#filnavn').val();
      var url = ureg_bok + "?_=" + new Date().getTime();
      fetch(url)
        .then(response => response.json())
        .then(data => {
          var matchingItem = data.find(item => item.filnavn === fileName);
          if (matchingItem) {
            $('#skannjobb_id').val(matchingItem.skannjobb_id);
            $('#button-skannjobb').attr('disabled', true);
            $('#button-skannjobb').removeClass().addClass('btn btn-secondary');
          }
        })
        .catch(error => console.error('Error:', error));
    });
  }

  function clearDataButtonEventListener() {
    $('#rens_data').off('click').on('click', function () {
      $('#BokutdragSkjema').find('input, textarea, select').each(function() {
        if ($(this).attr('type') !== 'hidden') {
          $(this).val('');
        }
        $(this).attr('readonly', false).attr('disabled', false);
      });
      $('#button-skannjobb').attr('disabled', true);
      $('#button-skannjobb').removeClass().addClass('btn btn-secondary');
      $('#changeToInput').attr('id', 'changeToDropdown').removeClass('btn btn-secondary').addClass('btn btn-primary');
      if ($('#filnavn').is('select')) {
        $('#filnavn').replaceWith('<input type="text" class="form-control" id="filnavn" placeholder="" aria-label="Felt for filnavn" name="filnavn">');
      }
    });
  }
}
</script>
