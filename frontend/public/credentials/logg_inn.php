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

$token_exp = time() + $token_expiry;

// Hent data fra skjema
$form_username = $_POST['username'];
$form_password = $_POST['password'];

// Sjekk brukernavn og passord
$sql = "SELECT filoversikt_brukere.bruker_id AS bruker_id, brukernavn, passord, navn, token, token_expiry, filoversikt_b_roller.rolle_id, rolle, redirect_innlogging FROM filoversikt_brukere JOIN filoversikt_b_r ON filoversikt_b_r.bruker_id = filoversikt_brukere.bruker_id JOIN filoversikt_b_roller ON filoversikt_b_r.rolle_id = filoversikt_b_roller.rolle_id WHERE brukernavn = ?";
$stmt = $conn->prepare($sql);
$stmt->bind_param("s", $form_username);
$stmt->execute();
$result = $stmt->get_result();
$user = $result->fetch_assoc();

// Verifiser passord
if ($user && password_verify($form_password, $user['passord'])) {
  // Generer token
  $token = bin2hex(openssl_random_pseudo_bytes(16));

$data_cookie = ['name' => $user['navn'], 'bruker_id' => $user['bruker_id'], 'token' => $token];

  // Nettstedet bruker HTTPS, så vi setter secure flag på cookien
  $isSecure = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') || $_SERVER['SERVER_PORT'] == 443;

setcookie("data", json_encode($data_cookie), $token_exp, $cookie_path, "", $isSecure, false);
setcookie("expiry", $token_exp, $token_exp, $cookie_path, "", $isSecure, false); // 1 time
setcookie("role", $user['rolle_id'], $token_exp, $cookie_path, "", $isSecure, false);

  $sql = "UPDATE filoversikt_brukere SET token = ?, token_expiry = ? WHERE brukernavn = ?";
  $stmt = $conn->prepare($sql);
  $stmt->bind_param("sss", $token, $token_exp, $form_username);
  $stmt->execute();

  // Lagre bruker_id og token i en enkelt sesjonsvariabel
  $_SESSION['user'] = array('bruker_id' => $user['bruker_id'], 'token' => $token, 'rolle_id' => $user['rolle_id'], 'name' => $user['navn'], 'token_expiry' => $user['token_expiry']);

  echo "Login successful, token generated, role=" . $user['rolle_id'] . ", bruker=" . $user['navn'] . ", redirect=" . $user['redirect_innlogging'] . ", token_expiry=" . $token_expiry;
} else {
  echo "Invalid username or password.";
}

$conn->close();
?>
