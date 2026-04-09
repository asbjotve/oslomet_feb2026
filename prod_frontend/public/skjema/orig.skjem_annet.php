        <form action="ajax_handler.php" method="post" id="annetForm" >
<div class="row g-3">

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
        <label for"skannjobb_id">Skannjobb-ID</label>
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
        <label for="forfattere">Forfatter(e)</label>
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
        <input type="text" class="form-control" id="type_dokument" placeholder="" aria-label="Felt for hva slags type dokumentet er (f.eks. 'offentlig dokument')" name="type_dokument">
        <label for="type_dokument">Type dokuemtn (beskrivelse)</label>
      </div>
    </div>
  </div>

<input type="hidden" readonly value="4" name="doktype_id">

                        <div class="col-12">
                        <button type="submit" class="btn btn-primary btn-lg" aria-label="Knapp for å sende inn skjemaet">Legg til annet type dokument til filoversikt</button>
                </div>

</div>
                </form>
