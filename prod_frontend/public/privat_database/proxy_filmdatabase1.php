<?php
// Robust proxy for API-kall med støtte for videresending av relevante headers og korrekt JSON-respons

header('Content-Type: application/json');

// Sjekk at endpoint er satt
if (!isset($_GET['endpoint'])) {
    http_response_code(400);
    echo json_encode(['error' => 'Missing endpoint']);
    exit;
}

$endpoint = $_GET['endpoint'];
unset($_GET['endpoint']);

// Bygg query string uten endpoint
$query = http_build_query($_GET);

// Bygg API-URL
$apiUrl = "https://mediadb.plexcityhub.net/$endpoint";
if ($query && $_SERVER['REQUEST_METHOD'] === 'GET') {
    $apiUrl .= '?' . $query;
}

// Sett opp cURL
$ch = curl_init($apiUrl);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

// Samle relevante headers fra klienten
$headers = [];

// Hent alle innkommende headers fra klienten
if (function_exists('getallheaders')) {
    $clientHeaders = getallheaders();
} else {
    // Fallback for f.eks. nginx/fpm
    $clientHeaders = [];
    foreach ($_SERVER as $name => $value) {
        if (substr($name, 0, 5) == 'HTTP_') {
            $headerName = str_replace(' ', '-', ucwords(str_replace('_', ' ', strtolower(substr($name, 5)))));
            $clientHeaders[$headerName] = $value;
        }
    }
}

// Videresend Authorization- og Cookie-header samt Content-Type
foreach ($clientHeaders as $name => $value) {
    $lower = strtolower($name);
    if ($lower === 'authorization' || $lower === 'cookie') {
        $headers[] = "$name: $value";
    }
}

// For POST, PUT, DELETE: innholdstype og body
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if ($endpoint === "token") {
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, http_build_query($_POST));
        // Ikke sett Content-Type for x-www-form-urlencoded (cURL gjør dette automatisk)
    } else {
        curl_setopt($ch, CURLOPT_POST, true);
        $postfields = file_get_contents('php://input');
        curl_setopt($ch, CURLOPT_POSTFIELDS, $postfields);
        $headers[] = "Content-Type: application/json";
    }
}
if ($_SERVER['REQUEST_METHOD'] === 'PUT') {
    curl_setopt($ch, CURLOPT_CUSTOMREQUEST, "PUT");
    curl_setopt($ch, CURLOPT_POSTFIELDS, file_get_contents('php://input'));
    $headers[] = "Content-Type: application/json";
}
if ($_SERVER['REQUEST_METHOD'] === 'DELETE') {
    curl_setopt($ch, CURLOPT_CUSTOMREQUEST, "DELETE");
    curl_setopt($ch, CURLOPT_POSTFIELDS, file_get_contents('php://input'));
    $headers[] = "Content-Type: application/json";
}

// Legg til headers hvis nødvendig
if (!empty($headers)) {
    curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
}

// Timeout for robusthet
curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 10);
curl_setopt($ch, CURLOPT_TIMEOUT, 30);

// Hent svar fra backend
$response = curl_exec($ch);
$httpcode = curl_getinfo($ch, CURLINFO_HTTP_CODE);

// Hvis feil fra cURL eller tom respons, returner JSON-feil
if ($response === false || trim($response) === "") {
    http_response_code(502);
    echo json_encode(['error' => 'Proxy error: ' . curl_error($ch)]);
    curl_close($ch);
    exit;
}

// Prøv å dekode JSON for å sikre at det er gyldig før vi sender det videre
$json_test = json_decode($response);

if (json_last_error() !== JSON_ERROR_NONE) {
    http_response_code($httpcode ?: 500);
    echo json_encode([
        'error' => 'Upstream did not return valid JSON',
        'response_snippet' => substr($response, 0, 512),
        'http_code' => $httpcode
    ]);
    curl_close($ch);
    exit;
}

// Returner backend-respons med riktig statuskode
http_response_code($httpcode);
echo $response;

curl_close($ch);
?>
