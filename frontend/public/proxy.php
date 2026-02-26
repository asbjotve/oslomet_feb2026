<?php
if (!isset($_GET['endpoint'])) {
    http_response_code(400);
    echo json_encode(['error' => 'Missing endpoint']);
    exit;
}
$endpoint = $_GET['endpoint'];
unset($_GET['endpoint']);

require_once __DIR__ . '/path.php';

// Muliggjør henting av variabler fra globale phpdotenv-variabler
include $path_inc . '/konfigurasjonsfiler/dotenv_config.php';

$api_token = $_ENV['API_OSLOMET_TOKEN'] ?? getenv('API_OSLOMET_TOKEN') ?? null;

if (!$api_token) {
    throw new RuntimeException('OSLOMET_API_TOKEN mangler. Sjekk .env eller miljøvariabler.');
}

// Bygg query string uten endpoint
$query = http_build_query($_GET);

// Bygg API-URL
$apiUrl = "https://app.oslomet.plexcityhub.net/$endpoint";
if ($query && $_SERVER['REQUEST_METHOD'] === 'GET') {
    $apiUrl .= '?' . $query;
}

// Hent token fra cookie for brukerroller-endepunktet (både GET og POST)
if ($endpoint === 'brukerroller') {
    $cookieRaw = $_COOKIE['data'] ?? '';
    $cookie = json_decode($cookieRaw, true);
    $token = $cookie['token'] ?? '';
    error_log("Data-cookie: $cookieRaw");
    error_log("Token extracted: $token");
    if (!$token) {
        http_response_code(401);
        echo json_encode(['error' => 'Ingen token']);
        exit;
    }
    if ($_SERVER['REQUEST_METHOD'] === 'GET') {
        $apiUrl .= (strpos($apiUrl, '?') === false ? '?' : '&') . 'token=' . urlencode($token);
        error_log("GET url: $apiUrl");
    }
    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        $input = file_get_contents('php://input');
        $body = json_decode($input, true) ?: [];
        $body['token'] = $token;
        $postfields = json_encode($body);
        error_log("POST fields: $postfields");
    }
}

// Sett opp cURL
$ch = curl_init($apiUrl);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_HTTPHEADER, [
    "Authorization: Bearer " . trim($api_token),
    "Content-Type: application/json"
]);

// Håndter POST og videresend body
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    curl_setopt($ch, CURLOPT_POST, true);
    if (!isset($postfields)) {
        // Vanlige POST-endepunkt (uten brukerroller)
        $postfields = file_get_contents('php://input');
    }
    curl_setopt($ch, CURLOPT_POSTFIELDS, $postfields);
}

// Håndter PUT, DELETE osv om ønskelig
if ($_SERVER['REQUEST_METHOD'] === 'PUT') {
    curl_setopt($ch, CURLOPT_CUSTOMREQUEST, "PUT");
    curl_setopt($ch, CURLOPT_POSTFIELDS, file_get_contents('php://input'));
}
if ($_SERVER['REQUEST_METHOD'] === 'DELETE') {
    curl_setopt($ch, CURLOPT_CUSTOMREQUEST, "DELETE");
    curl_setopt($ch, CURLOPT_POSTFIELDS, file_get_contents('php://input'));
}

// Hent svar
$response = curl_exec($ch);
$httpcode = curl_getinfo($ch, CURLINFO_HTTP_CODE);

if ($response === false) {
    http_response_code(502);
    header('Content-Type: application/json');
    echo json_encode(['error' => 'Proxy error: ' . curl_error($ch)]);
    curl_close($ch);
    exit;
}

curl_close($ch);

http_response_code($httpcode);
header('Content-Type: application/json');
echo $response;
