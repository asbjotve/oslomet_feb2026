<?php
header('Content-Type: application/json');

if (!isset($_GET['endpoint'])) {
    http_response_code(400);
    echo json_encode(['error' => 'Missing endpoint']);
    exit;
}

$endpoint = $_GET['endpoint'];
unset($_GET['endpoint']);

$query = http_build_query($_GET);
$apiUrl = "https://mediadb.plexcityhub.net/$endpoint";
if ($query && $_SERVER['REQUEST_METHOD'] === 'GET') {
    $apiUrl .= '?' . $query;
}

$ch = curl_init($apiUrl);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

$headers = [];
if (function_exists('getallheaders')) {
    $clientHeaders = getallheaders();
} else {
    $clientHeaders = [];
    foreach ($_SERVER as $name => $value) {
        if (substr($name, 0, 5) == 'HTTP_') {
            $headerName = str_replace(' ', '-', ucwords(str_replace('_', ' ', strtolower(substr($name, 5)))));
            $clientHeaders[$headerName] = $value;
        }
    }
}
foreach ($clientHeaders as $name => $value) {
    $lower = strtolower($name);
    // Videresend bare Authorization og Cookie til API
    if ($lower === 'authorization' || $lower === 'cookie') {
        $headers[] = "$name: $value";
    }
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    // multipart/form-data: filer fra skjema
    if (!empty($_FILES) || (isset($_SERVER['CONTENT_TYPE']) && strpos($_SERVER['CONTENT_TYPE'], 'multipart/form-data') !== false)) {
        $fields = [];
        foreach ($_POST as $key => $value) {
            $fields[$key] = $value;
        }
        foreach ($_FILES as $key => $file) {
            if (is_array($file['tmp_name'])) {
                // Flere filer for samme key (f.eks. multiple="multiple")
                foreach ($file['tmp_name'] as $i => $tmpName) {
                    $fields[$key . "[$i]"] = new CURLFile($tmpName, $file['type'][$i], $file['name'][$i]);
                }
            } else {
                $fields[$key] = new CURLFile($file['tmp_name'], $file['type'], $file['name']);
            }
        }
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, $fields);
        // Ikke sett Content-Type: cURL gjør dette automatisk for multipart
    } else {
        // Vanlig JSON eller x-www-form-urlencoded
        curl_setopt($ch, CURLOPT_POST, true);
        $postfields = file_get_contents('php://input');
        curl_setopt($ch, CURLOPT_POSTFIELDS, $postfields);

        // Sørg for at Content-Type: application/json sendes til backend
        $hasContentType = false;
        foreach ($headers as $hdr) {
            if (stripos($hdr, 'content-type:') === 0) {
                $hasContentType = true;
                break;
            }
        }
        if (!$hasContentType) {
            $headers[] = 'Content-Type: application/json';
        }
    }
}

if ($_SERVER['REQUEST_METHOD'] === 'PUT') {
    curl_setopt($ch, CURLOPT_CUSTOMREQUEST, "PUT");
    curl_setopt($ch, CURLOPT_POSTFIELDS, file_get_contents('php://input'));
}
if ($_SERVER['REQUEST_METHOD'] === 'DELETE') {
    curl_setopt($ch, CURLOPT_CUSTOMREQUEST, "DELETE");
    curl_setopt($ch, CURLOPT_POSTFIELDS, file_get_contents('php://input'));
}

if (!empty($headers)) {
    curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
}

curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 10);
curl_setopt($ch, CURLOPT_TIMEOUT, 30);

$response = curl_exec($ch);
$httpcode = curl_getinfo($ch, CURLINFO_HTTP_CODE);

if ($response === false || trim($response) === "") {
    http_response_code(502);
    echo json_encode(['error' => 'Proxy error: ' . curl_error($ch)]);
    curl_close($ch);
    exit;
}

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

http_response_code($httpcode);
echo $response;

curl_close($ch);
?>
