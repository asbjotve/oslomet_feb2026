<!-- <div id="myapp" class="container"> -->
  <h3 align="center">Artikler</h3><br />

<!-- Modal -->
<div class="modal fade" id="filterModal" tabindex="-1" aria-labelledby="filterModalLabel" aria-hidden="true">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title" id="filterModalLabel">Filter Table</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
      </div>
      <div class="modal-body">
        <div class="mb-3">
          <label for="searchText" class="form-label">Search Text</label>
          <input type="text" class="form-control" id="searchText">
        </div>
        <div class="mb-3">
          <label for="selectColumn" class="form-label">Select Column</label>
          <select class="form-select" id="selectColumn">
            <option value="filnavn">Filnavn</option>
            <option value="artikkel_tittel">Artikkeltittel</option>
            <option value="forfatter">Forfatter</option>
            <option value="tidsskrift">Tidsskrift</option>
            <option value="issn">ISSN</option>
          </select>
        </div>
<div class="form-check">
  <input class="form-check-input" type="checkbox" id="regexSearch">
  <label class="form-check-label" for="regexSearch">
    Use Regex
  </label>
</div>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
        <button type="button" class="btn btn-primary" id="applyFilter">Apply Filter</button>
      </div>
    </div>
  </div>
</div>


<div class="d-grid gap-2 d-md-block">
  <button class="btn btn-primary ajax_oppdater" type="button">Oppdater tabell</button>
  <button class="btn btn-primary" type="button" data-bs-toggle="modal" data-bs-target="#filterModal">Søk i tabell</button>
  <button class="btn btn-secondary" type="button" id="resetFilter">Nullstill søk</button>
</div>
<br>
<p class="d-inline-flex gap-1">
  <a href="" class="btn" role="button" data-bs-toggle="button" onclick="toggleColumns([4,5,6,7,8])">Vis/skjul kolonner</a>
  <a href="" class="btn" role="button" data-bs-toggle="button" onclick="toggleKommentarColumn()">Vis/skjul Merknad/Kommentar-kolonne</a>
</p>

<div class="table-responsive">
<table id="data-table" class="table table-striped table-hover table-bordered">
    <thead>
      <tr>
        <th id="filnavn" onclick="sortTable(0)">Filnavn</th>
        <th id="sideangivelse" onclick="sortTable(1)">Sideangivelse</th>
        <th id="artikkel_tittel" onclick="sortTable(2)">Artikkeltittel</th>
        <th id="art_forfatter">Forfatter</th>
        <th id="tidsskrift">Tidsskrift</th>
        <th id="issn">ISSN</th>
        <th id="utgitt">Utgitt</th>
        <th id="argang_volume" onclick="sortTable(7)">Volume/hefte</th>
        <th id="tidss_iss">Nummer/issue</th>
        <th id="merknad">Merknad/kommentar</th>

      </tr>
    </thead>
    <tbody></tbody>
  </table>
</div>
<div id="pagination_buttons"></div>
 <div id="pagination">
<button id="btn_first" onclick="changePage(1)" class="btn btn-primary">Første</button>
    <button id="btn_prev" onclick="prevPage()" class="btn btn-primary">Prev</button>
    <button id="btn_next" onclick="nextPage()" class="btn btn-primary">Next</button>
<button id="btn_last" onclick="changePage(numPages())" class="btn btn-primary">Siste</button>
    Page: <span id="page"></span>
  </div>

<?php include '/var/www/dev.oslomet.plexcity.net/public/scripts/tabeller/js_artikkelfiler.txt' ?>
