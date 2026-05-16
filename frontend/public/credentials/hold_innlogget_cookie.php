<?php
// Starter sesjon, hvis en sesjon ikke allerede er startet
if (session_status() == PHP_SESSION_NONE) {
    session_start();
}

/*
Disse variablene er definert via php_variables.php:
- $token_expiry
- $cookie_path
*/

// Angir hva som er hovedpath, f.eks. /var/www/plexcity.net/filoversikt/
// Variabelen settes ved installasjon av filoversikt-nettstedet
require_once __DIR__ . '/../path.php';

// Laster inn side med databasetilkobling - merk! phpdotenv blir lastet inn via denne siden.
include $path_inc . '/credentials/db_connection.php';

// Angir hvilken switch, altså hvilket sett med variabler
// fra php_variables, som skal lastes inn
$lastet_side = '';

// Laster inn php_variables.php
include_once $path_inc . '/konfigurasjonsfiler/php_variables.php';

$response = ['status' => 'error', 'message' => 'Ugyldig bruker eller token'];

/**
 * Returner JSON og avslutt
 */
function respond_and_exit(array $response): void {
    header('Content-Type: application/json');
    echo json_encode($response);
    exit;
}

// Må ha data-cookie
if (!isset($_COOKIE['data'])) {
    respond_and_exit($response);
}

$data_to_save = $_COOKIE['data'];
$role_to_save = $_COOKIE['role'] ?? '';

// Dekode cookie-data (JSON)
$data = json_decode($_COOKIE['data'], true);
if (!is_array($data) || !isset($data['bruker_id'], $data['token'])) {
    respond_and_exit($response);
}

$user_id = (int)$data['bruker_id'];
$token = (string)$data['token'];

if ($user_id <= 0 || $token === '') {
    respond_and_exit($response);
}

// Sjekk bruker_id og token mot databasen
$query = "SELECT bruker_id FROM filoversikt_brukere WHERE bruker_id = ? AND token = ? LIMIT 1";
$stmt = $conn->prepare($query);
$stmt->bind_param('is', $user_id, $token);
$stmt->execute();
$result = $stmt->get_result();

if ($result && $result->num_rows > 0) {
    $token_exp = time() + (int)$token_expiry;

    // Nettstedet bruker HTTPS, så vi setter secure flag på cookien
    $isSecure = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') || ($_SERVER['SERVER_PORT'] ?? null) == 443;

    // Cookie options (bruk samme i login/logout for konsistens)
    $cookieOptions = [
        'expires'  => $token_exp,
        'path'     => $cookie_path ?? '/',
        'secure'   => $isSecure,
        'httponly' => false,  // må være false hvis token leses i JS
        'samesite' => 'Lax',
    ];

    // Forny cookies
    setcookie("expiry", (string)$token_exp, $cookieOptions);
    setcookie("data", $data_to_save, $cookieOptions);
    setcookie("role", (string)$role_to_save, $cookieOptions);

    // Oppdater token_expiry i DB
    $sql = "UPDATE filoversikt_brukere SET token_expiry = ? WHERE bruker_id = ?";
    $stmt = $conn->prepare($sql);
    $stmt->bind_param("ii", $token_exp, $user_id);
    $stmt->execute();

    $response['status'] = 'success';
    $response['message'] = 'Bruker fortsatt innlogget';
}

$conn->close();
respond_and_exit($response);
?>
