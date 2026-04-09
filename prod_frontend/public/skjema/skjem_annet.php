<!-- ANNET TYPE DOKUMENT -->
<form id="AnnetSkjema">
  <div class="row g-3">

    <!-- (valgfritt, men fint om API forventer form_id slik som artikkel) -->
    <input type="hidden" name="form_id" value="4">

    <!-- 1 - FILNAVN -->
    <div class="col-md-2">
      <div class="input-group input-group-lg">
        <div class="form-floating">
          <input type="text" class="form-control" id="filnavn" placeholder="" aria-label="Felt for filnavn" name="filnavn">
          <label for="filnavn">Filnavn</label>
        </div>
      </div>
    </div>

    <!-- 2 - SKANNJOBB-ID -->
    <div class="col-md-3">
      <div class="input-group input-group-lg">
        <div class="form-floating">
          <input type="text" class="form-control" id="skannjobb_id" placeholder="" aria-label="Felt for skannjobb-ID" name="skannjobb_id">
          <label for="skannjobb_id">Skannjobb-ID</label>
        </div>
      </div>
    </div>

    <div class="col-md-5"></div>

    <!-- 3 - TITTEL -->
    <div class="col-md-10">
      <div class="input-group input-group-lg">
        <div class="form-floating">
          <input type="text" class="form-control" id="tittel" placeholder="" aria-label="Felt for tittel på dokument" name="tittel">
          <label for="tittel">Tittel på dokument*</label>
        </div>
      </div>
    </div>

    <!-- 4 - FORFATTER(E) -->
    <div class="col-md-5">
      <div class="input-group input-group-lg">
        <div class="form-floating">
          <input type="text" class="form-control" id="forfatter" placeholder="" aria-label="Felt for forfattere av materiellet" name="forfatter">
          <label for="forfatter">Forfatter(e)</label>
        </div>
      </div>
    </div>

    <!-- 5 - UTGITT -->
    <div class="col-md-1">
      <div class="input-group input-group-lg">
        <div class="form-floating">
          <input type="text" class="form-control" id="utgitt" placeholder="" aria-label="Felt for når materiellet er utgitt" name="utgitt">
          <label for="utgitt">Utgitt</label>
        </div>
      </div>
    </div>

    <!-- 7 - SIDEANGIVELSE(R) -->
    <div class="col-md-2">
      <div class="input-group input-group-lg">
        <div class="form-floating">
          <input type="text" class="form-control" id="sideangivelse" placeholder="" aria-label="Felt for sideangivelser" name="sideangivelse">
          <label for="sideangivelse">Sideangivelse(r)</label>
        </div>
      </div>
    </div>

    <!-- 6 - TYPE DOKUMENT -->
    <div class="col-md-10">
      <div class="input-group input-group-lg">
        <div class="form-floating">
          <input type="text" class="form-control" id="type_dokument" placeholder="" aria-label="Felt for hva slags type dokumentet er" name="type_dokument">
          <label for="type_dokument">Type dokument (beskrivelse)</label>
        </div>
      </div>
    </div>

    <!-- Viktig: doktype_id = 4 (slik du hadde) -->
    <input type="hidden" readonly value="4" name="doktype_id">

    <div class="col-12">
      <button type="submit" class="btn btn-primary btn-lg" aria-label="Knapp for å sende inn skjemaet">
        Legg til annet type dokument til filoversikt
      </button>
    </div>

  </div>
</form>

<script>
function annetScript() {
    var success_1 = `<div class="alert alert-success light-mode alert-dismissible fade show" role="alert">
<svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="currentColor" class="bi bi-check-circle" viewBox="0 0 16 16">
<path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14m0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16"/>
<path d="m10.97 4.97-.02.022-3.473 4.425-2.093-2.094a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-1.071-1.05"/>
</svg>
&nbsp;&nbsp;Filen ved navn <strong>`;

    var success_2 = `</strong> ble lagt til i filoversikten!
<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
</div>`;

  console.log("annetScript(): kobler submit for #AnnetSkjema");

  const skjema = document.getElementById('AnnetSkjema');
  if (!skjema) {
    console.log("Fant ikke #AnnetSkjema");
    return;
  }

  // Unngå dobbel-binding
  if (skjema.dataset.bound === "1") return;
  skjema.dataset.bound = "1";

  // Token fra cookie 'data'
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

  function showModal(id, message) {
    const modalBody = document.getElementById(id + 'Body');
    if (modalBody) modalBody.textContent = message;
    const modalDiv = document.getElementById(id);
    if (modalDiv) {
      const modal = new bootstrap.Modal(modalDiv);
      modal.show();
    }
  }

  skjema.addEventListener('submit', async function(e) {
    console.log("SUBMIT trigget for AnnetSkjema");
    e.preventDefault();

    const formData = new FormData(skjema);
    const data = {};
    formData.forEach((value, key) => data[key] = value);
    data.token = token;

    try {
      const respons = await fetch('/proxy.php?endpoint=filoversikt/leggtil', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });

      let res = {};
      try { res = await respons.json(); } catch (e) {}

      console.log("HTTP status:", respons.status, "ok:", respons.ok, "res:", res);

      if (respons.ok) {
        var successMessage = success_1 + data.filnavn + success_2;
        document.querySelector('#successDiv').innerHTML = successMessage;

        //const successDiv = document.querySelector('#successDiv');
        //if (successDiv) {
        //  successDiv.innerHTML = 'Lagt til: <strong>' + (data.filnavn || '') + '</strong>';
        //}
        skjema.reset();
      } else {
        let feilmelding = res && res.detail;
        if (!feilmelding || typeof feilmelding !== 'string') {
          feilmelding = JSON.stringify(feilmelding) || 'Ukjent feil';
        }
        showModal('errorModal', 'Feil: ' + feilmelding);
      }
    } catch (err) {
      console.log("Fetch-feil:", err);
      showModal('errorModal', 'Teknisk feil: ' + err);
    }
  });
}
</script>
