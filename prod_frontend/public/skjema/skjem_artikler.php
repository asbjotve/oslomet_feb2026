<!-- FILNAVN -->
<form id="ArtiklerSkjema">
<div id="hell">
        <div class="row g-3">

                <input type="hidden" name="form_id" value="2">


                <!-- FILNAVN -->
                <div class="col-md-3">
                        <div class="form-floating">
                                <input type="text" class="form-control" id="filnavn" placeholder="" name="filnavn">
                                <label for="filnavn">Filnavn</label>
                        </div>
                </div>

                <!--SKANNJOBB_ID -->
                <div class="col-md-3">
                        <div class="form-floating">
                                <input type="text" class="form-control" id="skannjobb_id" placeholder="" name="skannjobb_id">
                                <label for="skannjobb_id" class="form-label">Skannjobb-ID</label>
                        </div>
                </div>

                <!-- SIDEANGIVELSE -->
                <div class="col-md-6">
                        <div class="form-floating">
                                <input type="text" class="form-control" id="sideangivelse" placeholder="" name="sideangivelse">
                                <label for="sideangivelse">Sideangivelse(r)</label>
                        </div>
                </div>

                <!--ARTIKKELTITTEL -->
                <div class="col-md-6">
                        <div class="form-floating">
                                <input type="text" class="form-control" id="artikkel_tittel" placeholder="" name="artikkel_tittel">
                                <label for="artikkel_tittel">Artikkeltittel</label>
                        </div>
                </div>

                <!-- FORFATTER(E) -->
                <div class="col-md-6">
                        <div class="form-floating">
                                <input type="text" class="form-control" id="forfatter" placeholder="" name="forfatter">
                                <label for="forfatter" class="form-label">Forfatter(e)</label>
                        </div>
                        <span id="passwordHelpInline" class="form-text">
                                Skrives i formen Etternavn, Fornavn ; Etternavn, Fornavn og så videre.
                        </span>
                </div>

                <!-- ISSN -->
                <div class="col-md-2">
                        <div class="form-floating">
                                <input type="text" class="form-control" id="issn" placeholder="" name="issn">
                                <label for="issn" class="form-label">ISSN</label>
                        </div>
                </div>

                <!-- TIDSSKRIFT -->
                <div class="col-md-10">
                        <div class="form-floating">
                                <input type="text" class="form-control" id="tidsskrift" placeholder="" name="tidsskrift">
                                <label for="tidsskrift" class="form-label">Tidsskrift</label>
                        </div>
                </div>

                <!-- ÅRGANG/VOLUME -->
                <div class="col-md-2">
                        <div class="form-floating">
                                <input type="text" class="form-control" id="argang" placeholder="" name="argang_volume">
                                <label for="argang" class="form-label">Årgang</label>
                        </div>
                </div>

                <!-- HEFTE/ISSUE -->
                <div class="col-md-5">
                        <div class="form-floating">
                                <input type="text" class="form-control" id="hefte_issue" placeholder="" name="hefte_issue">
                                <label for="hefte_issue" class="form-label">Hefte/nummer</label>
                        </div>
                </div>

                <!-- UTGITT -->
                <div class="col-md-5">
                        <div class="form-floating">
                                <input type="text" class="form-control" id="utgitt" placeholder="" name="utgitt">
                                <label for="utgitt" class="form-label">Utgitt</label>
                        </div>
                </div>

                <!-- MEKRNAD -->
                <div class="col-md-12">
                        <div class="form-floating">
                                <input type="text" class="form-control" id="merknad" placeholder="" name="merknad">
                                <label for="merknad" class="form-label">Merknad/kommentar</label>
                        </div>
                </div>

                <div class="col-12">
                        <button type="submit" class="btn btn-primary btn-lg">Legg til artikkel i filoversikt</button>
                </div>

        </div>
</div>

<input type="hidden" readonly value="2" name="doktype_id">

</form>

<script>
function artiklerScript() {

    var success_1 = `<div class="alert alert-success light-mode alert-dismissible fade show" role="alert">
<svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="currentColor" class="bi bi-check-circle" viewBox="0 0 16 16">
<path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14m0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16"/>
<path d="m10.97 4.97-.02.022-3.473 4.425-2.093-2.094a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-1.071-1.05"/>
</svg>
&nbsp;&nbsp;Filen ved navn <strong>`;

    var success_2 = `</strong> ble lagt til i filoversikten!
<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
</div>`;

  // Hent token fra cookie
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

  // Modal helper
  function showModal(id, message) {
    var modalBody = document.getElementById(id + 'Body') ||
                    document.getElementById('errorModalBody') ||
                    document.getElementById('suksessBody');
    if (modalBody) {
      modalBody.innerHTML = message;
    }
    const modalDiv = document.getElementById(id);
    if (modalDiv) {
      const modal = bootstrap.Modal.getOrCreateInstance(modalDiv);
      modal.show();
    }
  }

  const skjema = document.getElementById('ArtiklerSkjema');
  if (!skjema) return;

  skjema.addEventListener('submit', function(e) {
    e.preventDefault();
    const formData = new FormData(skjema);
    const skjemaData = {};
    formData.forEach((value, key) => {
      skjemaData[key] = value;
    });

    // Legg til token!
    skjemaData.token = token;

    sendData(skjemaData);
  });

 async function sendData(data) {
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
        skjema.reset();
        document.querySelectorAll('#ArtiklerSkjema input, #ArtiklerSkjema textarea, #ArtiklerSkjema select').forEach(el => {
          el.readOnly = false; el.disabled = false;
        });
      } else {
        let feilmelding = res && res.detail;
        if (!feilmelding || typeof feilmelding !== 'string') {
          feilmelding = JSON.stringify(feilmelding) || 'Ukjent feil';
        }
        showModal('errorModal', 'Feil: ' + feilmelding);
      }
    } catch (err) {
      showModal('errorModal', 'Teknisk feil: ' + err);
    }
  }

}

// Kjør denne ETTER du har lagt inn HTML for skjema og modalene
// artiklerScript();
</script>
