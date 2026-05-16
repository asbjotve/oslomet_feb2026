<script>
// Åpner modal, hvis CTRL+F tastes
window.addEventListener("keydown", function(e) {
    if (e.ctrlKey && e.key === 'f') {
        e.preventDefault();
        $('#filterModal').modal('show');
    }
});

// Definerer globale variabler
var data = [];           // Hoveddataen hentet fra serveren
var filteredData = [];   // Filtrert data basert på brukerens søk
var current_page = 1;    // Gjeldende side som vises
var rows_per_page = 20;  // Antall rader som skal vises per side
//var buttonContainer = document.getElementById("button-container");
var hiddenColumns = [];
var navover_artikler_json = json_artikler_path;
// buttonContainer.innerHTML += '<button onclick="toggleColumns([4, 5, 6, 7, 8])">Toggle kolonner</button>';
//buttonContainer.innerHTML += '<button class="btn btn-primary" onclick="toggleCommentColumn()">Toggle kommentar kolonne</button>';

// Funksjon som kjører når dokumentet er klart
$(document).ready(function() {
  $.ajax({
    url: navover_artikler_json,
    method: 'GET',
    cache: false, //forhindrer at det lastes inn cached data, altså laster alltid inn nyeste datao
    success: function(response) {
      var responseData = JSON.parse(response).response.data;

      // Sorterer dataene basert på artikkeltittel
      responseData.sort(function(a, b) {
        var x = a.fieldData.artikkel_tittel ? a.fieldData.artikkel_tittel.toLowerCase().trim() : '';
        var y = b.fieldData.artikkel_tittel ? b.fieldData.artikkel_tittel.toLowerCase().trim() : '';
        return x.localeCompare(y, undefined, {numeric: true, sensitivity: 'base'});
      });

      // Lagrer de sorterte dataene
      data = responseData;
      filteredData = responseData.slice();
      changePage(1);
    },
    error: function(jqXHR, textStatus, errorThrown) {
    }
  });
toggleColumns([4, 5, 6, 7, 8, 9]);
});

// Funksjon for å skjule eller vise flere kolonner
function toggleColumns(columnIndices) {
  // Går gjennom hver kolonneindeks i listen
  for (var i = 0; i < columnIndices.length; i++) {
    // Kaller toggleColumn funksjonen for hver kolonneindeks
    // Dette vil skjule kolonnen hvis den er synlig, eller vise den hvis den er skjult
    toggleColumn(columnIndices[i]);
  }
}

// Funksjon for å skjule eller vise en kolonne
function toggleColumn(columnIndex) {
  var table = document.getElementById("data-table");
  var columnCells = table.querySelectorAll('tr td:nth-child(' + (columnIndex + 1) + '), tr th:nth-child(' + (columnIndex + 1) + ')');
  for (var i = 0; i < columnCells.length; i++) {
    if (columnCells[i].style.display === 'none') {
      columnCells[i].style.display = '';
      // Fjerner kolonnen fra listen over skjulte kolonner
      var index = hiddenColumns.indexOf(columnIndex);
      if (index > -1) {
        hiddenColumns.splice(index, 1);
      }
    } else {
      columnCells[i].style.display = 'none';
      // Legger til kolonnen i listen over skjulte kolonner
      hiddenColumns.push(columnIndex);
    }
  }
}

// Funksjon som kjører når brukeren klikker på Apply Filter-knappen
$('#applyFilter').on('click', function() {
  var searchText = $('#searchText').val().toLowerCase(); // Henter søketeksten
  var selectedColumn = $('#selectColumn').val();         // Henter valgt kolonne
  var useRegex = $('#regexSearch').prop('checked');      // Sjekker om regex skal brukes

  // Filtrerer dataen basert på søketeksten og den valgte kolonnen
  if (useRegex) {
    var regex = new RegExp(searchText, 'i');
    filteredData = data.filter(function(row) {
      return regex.test(row.fieldData[selectedColumn].toLowerCase());
    });
  } else {
    filteredData = data.filter(function(row) {
      return row.fieldData[selectedColumn].toLowerCase().indexOf(searchText) !== -1;
    });
  }

  // Oppdaterer tabellen med den filtrerte dataen
  changePage(1);
  // Lukker modalen
  $('#filterModal').modal('hide');
});

// Funksjon som kjører når brukeren klikker på Reset Filter-knappen
$('#resetFilter').on('click', function() {
  // Nullstiller filteredData til den opprinnelige dataen
  filteredData = data.slice();
  // Oppdaterer tabellen
  changePage(1);
});

// Funksjon for å oppdatere tabellen basert på den gjeldende siden
function changePage(page) {
  // Få referanser til elementene vi trenger
  var btn_next = document.getElementById("btn_next");
  var btn_prev = document.getElementById("btn_prev");
  var btn_first = document.getElementById("btn_first");
  var btn_last = document.getElementById("btn_last");
  var listing_table = document.getElementById("data-table").getElementsByTagName('tbody')[0];
  var page_span = document.getElementById("page");
  var pagination_buttons = document.getElementById("pagination_buttons");

  // Validerer siden
  if (page < 1) page = 1;
  if (page > numPages()) page = numPages();

  // Tømmer tabellen
  listing_table.innerHTML = "";

  // Legger til rader i tabellen basert på den gjeldende siden av den filtrerte dataen
  for (var i = (page-1) * rows_per_page; i < (page * rows_per_page) && i < filteredData.length; i++) {
    if (filteredData[i]) {
        var row = '<tr class="table-dark">';
    // Legger til en celle for hver kolonne, men endrer 'display' stilen hvis kolonnen er skjult
    row += '<td style="' + (hiddenColumns.indexOf(0) > -1 ? 'display: none;' : '') + '">' + filteredData[i].fieldData.filnavn + '</td>';
    row += '<td style="' + (hiddenColumns.indexOf(1) > -1 ? 'display: none;' : '') + '">' + filteredData[i].fieldData.sideangivelse + '</td>';
    row += '<td style="' + (hiddenColumns.indexOf(2) > -1 ? 'display: none;' : '') + '">' + filteredData[i].fieldData.artikkel_tittel + '</td>';
    row += '<td style="' + (hiddenColumns.indexOf(3) > -1 ? 'display: none;' : '') + '">' + filteredData[i].fieldData.forfatter + '</td>';
    row += '<td style="' + (hiddenColumns.indexOf(4) > -1 ? 'display: none;' : '') + '">' + filteredData[i].fieldData.tidsskrift + '</td>';
    row += '<td style="' + (hiddenColumns.indexOf(5) > -1 ? 'display: none;' : '') + '">' + filteredData[i].fieldData.issn + '</td>';
    row += '<td style="' + (hiddenColumns.indexOf(6) > -1 ? 'display: none;' : '') + '">' + filteredData[i].fieldData.utgitt + '</td>';
    row += '<td style="' + (hiddenColumns.indexOf(7) > -1 ? 'display: none;' : '') + '">' + filteredData[i].fieldData.argang_volume + '</td>';
    row += '<td style="' + (hiddenColumns.indexOf(8) > -1 ? 'display: none;' : '') + '">' + filteredData[i].fieldData.hefte_issue + '</td>';
    row += '<td style="' + (hiddenColumns.indexOf(9) > -1 ? 'display: none;' : '') + '">' + filteredData[i].fieldData.merknad + '</td>';
    row += '</tr>';
    listing_table.innerHTML += row;
  }
 }
/*
  for (var i = (page-1) * rows_per_page; i < (page * rows_per_page) && i < filteredData.length; i++) {
    var row = '<tr class="table-dark">';
    row += '<td style="' + (hiddenColumns.indexOf(0) > -1 ? 'display: none;' : '') + '">' + filteredData[i].fieldData.filnavn + '</td>';
    row += '<td style="' + (hiddenColumns.indexOf(1) > -1 ? 'display: none;' : '') + '">' + filteredData[i].fieldData.sideangivelse + '</td>';
    row += '<td style="' + (hiddenColumns.indexOf(2) > -1 ? 'display: none;' : '') + '">' + filteredData[i].fieldData.kapittelnummer + '</td>';
    row += '<td style="' + (hiddenColumns.indexOf(3) > -1 ? 'display: none;' : '') + '">' + filteredData[i].fieldData.kapitelltittel + '</td>';
    row += '<td style="' + (hiddenColumns.indexOf(4) > -1 ? 'display: none;' : '') + '">' + filteredData[i].fieldData.kapittelforfatter + '</td>';
    row += '<td style="' + (hiddenColumns.indexOf(5) > -1 ? 'display: none;' : '') + '">' + filteredData[i].fieldData.boktittel + '</td>';
    row += '<td style="' + (hiddenColumns.indexOf(6) > -1 ? 'display: none;' : '') + '">' + filteredData[i].fieldData.utgitt + '</td>';
    row += '<td style="' + (hiddenColumns.indexOf(7) > -1 ? 'display: none;' : '') + '">' + filteredData[i].fieldData.forlag + '</td>';
    row += '<td style="' + (hiddenColumns.indexOf(8) > -1 ? 'display: none;' : '') + '">' + filteredData[i].fieldData.forfatter + '</td>';
    row += '</tr>';
    listing_table.innerHTML += row;
  }
*/

  // Oppdaterer sidenavigasjonen
  page_span.innerHTML = page + "/" + numPages() + " (Totalt " + filteredData.length + " poster)";

  // Viser eller skjuler forrige og neste knapper avhengig av gjeldende side
  if (page == numPages()) {
    btn_next.style.visibility = "hidden";
    btn_last.style.visibility = "hidden";
  } else {
    btn_next.style.visibility = "visible";
    btn_last.style.visibility = "visible";
  }

  // Beregner start- og sluttsiden for pagineringsknappene
  var startPage = Math.max(page - 5, 1);
  var endPage = Math.min(page + 5, numPages());

  // Genererer pagineringsknappene
  pagination_buttons.innerHTML = "";
  for (var i = startPage; i <= endPage; i++) {
    // Bestemmer hvilken klasse som skal brukes basert på om knappen representerer den gjeldende siden
    var buttonClass = i === page ? 'btn_page_current' : 'btn_page';
    // Legger til en knapp for denne siden
    pagination_buttons.innerHTML += "<button class='btn btn-primary me-2 mb-3 " + buttonClass + "' onclick='changePage(" + i + ")'>" + i + "</button>";
  }
}

// Funksjon for å beregne antall sider basert på den filtrerte dataen
function numPages() {
  return Math.ceil(filteredData.length / rows_per_page);
}

// Funksjon for å gå til forrige side
function prevPage() {
  if (current_page > 1) {
    current_page--;
    changePage(current_page);
  }
}

// Funksjon for å gå til neste side
function nextPage() {
  if (current_page < numPages()) {
    current_page++;
    changePage(current_page);
  }
}

// Variabel for å holde styr på sorteringstilstanden for hver kolonne
var columnSort = {};

// Funksjon for å sortere dataen basert på en angitt kolonne
function sortData(column) {
  var sortFunction;

  // Hvis kolonnen ikke har blitt sortert før, eller hvis den ble sortert synkende sist, sorterer vi stigende
  if (!columnSort[column] || columnSort[column] === 'desc') {
    sortFunction = function(a, b) {
      var x = a.fieldData[column].toLowerCase().trim();
      var y = b.fieldData[column].toLowerCase().trim();
      return x.localeCompare(y, 'nb', {numeric: true, sensitivity: 'base'});
    };
    columnSort[column] = 'asc';  // Oppdaterer sorteringstilstanden for denne kolonnen
  } else {
    // Hvis kolonnen ble sortert stigende sist, sorterer vi synkende
    sortFunction = function(a, b) {
      var x = a.fieldData[column].toLowerCase().trim();
      var y = b.fieldData[column].toLowerCase().trim();
      return y.localeCompare(x, 'nb', {numeric: true, sensitivity: 'base'});
    };
    columnSort[column] = 'desc';  // Oppdaterer sorteringstilstanden for denne kolonnen
  }

  data.sort(sortFunction);

  // Oppdater filteredData til den sorterte dataen
  filteredData = data.slice();
}

// Funksjon for å sortere tabellen
function sortTable(n) {
  var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
  table = document.getElementById("data-table");
  switching = true;
  dir = "asc";

  // Bestem kolonnenavnet basert på indeksen n
  var columnName;
  switch (n) {
    case 0:
      columnName = 'filnavn';
      break;
    case 1:
      columnName = 'sideangivelse';
      break;
    case 2:
      columnName = 'artikkel_tittel';
      break;
    case 3:
      columnName = 'forfatter';
      break;
    case 7:
      columnName = 'argang_volume';
      break;
    default:
      return;  // Ugyldig kolonneindeks
  }

  // Sorter dataen basert på den angitte kolonnen
  sortData(columnName);

  // Oppdater tabellen
  changePage(current_page);
}

function toggleKommentarColumn() {
  // Anta at kommentarkolonnen er kolonneindeks 9
  var columnIndex = 9;
  toggleColumn(columnIndex);
}

</script>
