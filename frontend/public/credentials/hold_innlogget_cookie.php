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

$response = array('status' => 'error', 'message' => 'Ugyldig bruker eller token');

if(isset($_COOKIE['data'])) {
    $data_to_save = $_COOKIE['data'];
    $role_to_save = $_COOKIE['role'];
    $data = json_decode(urldecode($_COOKIE['data']), true);
    $username = $data['bruker_id']; // endret fra 'username' til 'name'
    $token = $data['token'];
}

    // Sjekk brukernavn og token mot databasen
    $query = "SELECT * FROM filoversikt_brukere WHERE bruker_id = ? AND token = ?";
    $stmt = $conn->prepare($query);
    $stmt->bind_param('ss', $username, $token);
    $stmt->execute();
    $result = $stmt->get_result();

    if ($result->num_rows > 0) {
        $token_exp = time() + $token_expiry;

        // Nettstedet bruker HTTPS, så vi setter secure flag på cookien
        $isSecure = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') || $_SERVER['SERVER_PORT'] == 443;

        setcookie("expiry", $token_exp, $token_exp, $cookie_path, "", $isSecure, false); // 1 time
        setcookie('data', $data_to_save, $token_exp, $cookie_path); // Setter en ny cookie med samme verdi
        setcookie('role', $role_to_save, $token_exp, $cookie_path);

// Oppdaterer dataene i mysql-tabellen
  $sql = "UPDATE filoversikt_brukere SET token_expiry = ? WHERE bruker_id = ?";
  $stmt = $conn->prepare($sql);
  $stmt->bind_param("ss", $token_exp, $username);
  $stmt->execute();

    // Oppdaterer responsen for suksess
    $response['status'] = 'success';
    $response['message'] = 'Bruker fortsatt innlogget';

}

header('Content-Type: application/json');
echo json_encode($response);
exit;

    $conn->close();
?>
