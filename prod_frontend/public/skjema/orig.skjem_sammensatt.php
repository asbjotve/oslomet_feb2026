<div class="bg-secondary">
  <label for="add_file_name" class="form-label mt-3">Legg til filnavn ved å enten droppe filer, eller ved å skrive inn manuelt (filnavn skilles med komma, hvis flere filer)</label>
  <div class="d-flex justify-content-between">
    <div id="drop_zone" class="border border-light flex-fill me-3 d-flex justify-content-center align-items-center" style="height: 200px; width:100px;">Dropp filer her</div>
    <div class="col-md-10">
      <div class="input-group input-group-lg">
        <div class="form-floating">
          <input type="text" class="form-control" id="add_file_name" placeholder="" aria-label="Felt hvor man legger inn filnavn som skal legges til i filen" name="add_file_name">
          <label for="add_file_name">filnavn</label>
        </div>
      </div>
    </div>
  </div>
  <button id="add_file_name_button" class="btn btn-info mb-1">Legg til filnavn</button>
</div>

<form action="ajax_handler.php" method="post" id="sammensattForm">
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
        <input type="hidden" class="form-control" id="fil_bestar_av" placeholder="" aria-label="Liste over filnavn" readonly name="fil_bestar_av"></textarea>
      </div>
    </div>
    <div class="col-md-12 mt-3">
      <div class="form-floating">
        <input type="hidden" class="form-control" id="sideangivelse" placeholder="" aria-label="Liste over sideangivelser" readonly name="sideangivelse"></textarea>
      </div>
    </div>
  </div>
<input type="hidden" id="mange_sideangivelser" value="0" name="mange_sideangivelser">
<input type="hidden" readonly value="3" name="doktype_id">
<button type="submit" class="btn btn-primary btn-lg" aria-label="Knapp for å sende inn skjemaet">Legg til nytt bokutdrag i filoversikt</button>
</form>
