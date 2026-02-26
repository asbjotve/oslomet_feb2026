<?php
// Starter sesjon, hvis en sesjon ikke allerede er startet
if (session_status() == PHP_SESSION_NONE) {
        session_start();
}

/*
Disse variablene er definert via php_variables.php:
- $token_expiry
- cookie_path
*/

// Angir hva som er hovedpath, f.eks. /var/www/plexcity.net/filoversikt/
// Variabelen settes ved installasjon av filoversikt-nettstedet
require_once __DIR__ . '/../path.php';

// Laster inn side med databasetilkobling - merk! phpdotenv blir lastet inn via denne siden.
include $path_inc . '/credentials/db_connection.php';

// Angir hvilken switch, altså hvilet sett med variabler
// fra php_variables, som skal lastes inn
$lastet_side = '';

// Laster inn php_variables.php
include_once $path_inc . '/konfigurasjonsfiler/php_variables.php';

$token_exp = time() - $token_expiry;

// Sjekk om 'data'-cookie er satt
if (!isset($_COOKIE['data'])) {
    // Hvis 'data'-cookie ikke er satt, avslutt scriptet
    die("No cookie found.");
}

// Dekoder 'data'-cookien fra JSON til et PHP-objekt
$data = json_decode($_COOKIE['data']);

// Hent bruker_id fra det dekodede objektet
$bruker_id = $data->bruker_id;

// Sett token til null i databasen
$sql = "UPDATE filoversikt_brukere SET token = NULL WHERE bruker_id = ?";
$stmt = $conn->prepare($sql);
$stmt->bind_param("i", $bruker_id);
$stmt->execute();

  // Nettstedet bruker HTTPS, så vi setter secure flag på cookien
  $isSecure = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') || $_SERVER['SERVER_PORT'] == 443;

// Sletter cookies
setcookie("data", "", $token_exp, $cookie_path, "", $isSecure, true);
setcookie("expiry", "", $token_exp, $cookie_path, "", $isSecure, true);
setcookie("role", "", $token_exp, $cookie_path, "", $isSecure, true);

// Fjern alle sesjonsvariabler
session_unset();

// Ødelegg sesjonen
session_destroy();

echo "Du har blitt logget ut";

$conn->close();
echo "Script completed.<br>";

session_unset();
session_destroy();

?>
