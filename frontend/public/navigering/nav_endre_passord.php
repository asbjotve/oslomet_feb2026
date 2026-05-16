<?php
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);

$lastet_side = "endrepass";

// Starter sesjon, hvis en sesjon ikke allerede er startet
if (session_status() == PHP_SESSION_NONE) {
        session_start();
}

require_once __DIR__ . '/../path.php';

// Muliggjør henting av variabler fra globale phpdotenv-variabler
include $path_inc . '/konfigurasjonsfiler/dotenv_config.php';

// Henter relevante variabler for php og javascript-kode
include $path_inc . '/konfigurasjonsfiler/php_variables.php';

?>


<!DOCTYPE html>
<html lang="en" data-bs-theme="dark">
    <head>
        <link rel="icon" href="https://plexcity.net:4588/filoversikt/favicon.ico" />
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Document Title</title>

        <script src="/dist/js/jquery.min.js"></script>
        <link rel="stylesheet" href="/dist/css/bootstrap.min.css">
        <script src="/dist/js/bootstrap.bundle.min.js"></script>

        <style>
                .menu-padding {
                padding-right: 30px;}
        </style>

<style>
.light-mode {
    background-color: green;
    color: white;
    border-color: black;
}

.nav-link.ajax-link.active::before {
  content: "";
  display: inline-block;
  width: 1.7em;
  height: 1.7em;
  margin-right: 6px;
  vertical-align: middle; /* eller baseline */
  /* margin-top: 1px;  Prøv deg frem! */
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' fill='currentColor' viewBox='0 0 17 17'><path fill-rule='evenodd' d='M10.146 4.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1 0 .708l-3 3a.5.5 0 0 1-.708-.708L12.293 8H2.5a.5.5 0 0 1 0-1h9.793l-2.147-2.146a.5.5 0 0 1 0-.708z'/></svg>");
  background-size: contain;
  background-repeat: no-repeat;
}
</style>

    </head>
    <body id="bootstrap-overrided">

<!-- NAVBAR -->
<nav class="navbar bg-warning navbar-expand-lg menu-padding" data-bs-theme="light">
  <div class="container-fluid">
    <span class="navbar-brand">
<svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="currentColor" class="bi bi-pencil" viewBox="0 0 16 16">
  <path d="M12.146.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1 0 .708l-10 10a.5.5 0 0 1-.168.11l-5 2a.5.5 0 0 1-.65-.65l2-5a.5.5 0 0 1 .11-.168zM11.207 2.5 13.5 4.793 14.793 3.5 12.5 1.207zm1.586 3L10.5 3.207 4 9.707V10h.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.5h.293zm-9.761 5.175-.106.106-1.528 3.821 3.821-1.528.106-.106A.5.5 0 0 1 5 12.5V12h-.5a.5.5 0 0 1-.5-.5V11h-.5a.5.5 0 0 1-.468-.325"/>
</svg>
Endre passord
</span>
    <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
      <span class="navbar-toggler-icon"></span>
    </button>
    <div class="collapse navbar-collapse" id="navbarNav">
      <ul class="navbar-nav">
        <li class="nav-item">
          <a class="nav-link ajax-link">Endre passord</a>
        </li>
      </ul>
<ul class="navbar-nav ms-auto menu-padding">
  <li class="nav-item dropdown">
    <a class="nav-link dropdown-toggle" href="#" id="navbarDropdown" role="button" data-bs-toggle="dropdown" aria-expanded="false">
      <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="currentColor" class="bi bi-person" viewBox="0 0 16 16">
        <path d="M8 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6m2-3a2 2 0 1 1-4 0 2 2 0 0 1 4 0m4 8c0 1-1 1-1 1H3s-1 0-1-1 1-4 6-4 6 3 6 4m-1-.004c-.001-.246-.154-.986-.832-1.664C11.516 10.68 10.289 10 8 10s-3.516.68-4.168 1.332"></path>
      </svg>
      <span id="username_txt_menu"></span>
    </a>
<div id="userMenu"></div>
  </li>
</ul>
    </div>
  </div>
</nav>
<br />
<!-- NAVBAR SLUTT -->

<!.. MODAL -->
<?php include $datainput_modal_path; ?>
<!-- MODAL SLUTT -->

<div id="successDiv">
</div>

<!-- INNHOLDS-DIV -->
<div id="content">
</div>


<!-- JAVASCRIPT SOM HÅNDTERER LENKER OG ANNET -->
<?php
include $js_nav_endrepassord_path;
?>

<script>
function getCookie(cname) {
  var name = cname + "=";
  var decodedCookie = decodeURIComponent(document.cookie);
  var ca = decodedCookie.split(';');
  for(var i = 0; i <ca.length; i++) {
    var c = ca[i];
    while (c.charAt(0) == ' ') {
      c = c.substring(1);
    }
    if (c.indexOf(name) == 0) {
      return c.substring(name.length, c.length);
    }
  }
  return "";
}
</script>

<script>
window.onload = function() {
// Hent cookien
var dataCookie = getCookie('data');

if (dataCookie) {
  try {
    // Parse JSON-strengen til et objekt
    var dataObject = JSON.parse(dataCookie);

    // Hent verdien av "name"
    var name = dataObject.name;

    // Sjekk om "name" attributtet finnes
    if (name) {
      document.getElementById("username_txt_menu").textContent = name;
    } else {
      document.getElementById("username_txt_menu").textContent = 'Ikke pålogget';
    }
  } catch (error) {
    console.error('Error parsing data cookie:', error);
    document.getElementById("username_txt_menu").textContent = 'Ikke pålogget';
  }
} else {
  document.getElementById("username_txt_menu").textContent = 'Ikke pålogget';
}
}
    </script>
    </body>
</html>
