<?php

// Angir hva som er hovedpath, f.eks. /var/www/plexcity.net/filoversikt/
// Variabelen settes ved installasjon av filoversikt-nettstedet
require_once __DIR__ . '/../path.php';

// Laster inn phpdotenv
require_once $path_inc . '/konfigurasjonsfiler/dotenv_config.php';

// Angir hvilken switch, altså hvilet sett med variabler
// fra php_variables, som skal lastes inn
$lastet_side = '';

// Laster inn php_variables.php
require_once $path_inc . '/konfigurasjonsfiler/php_variables.php';

/*
Variablene under blir hentet fra php_variables.php:
- db_servername
- $db_username
- $db_password
- $db_name
*/

// Opprett en ny tilkobling
$conn = new mysqli($db_servername, $db_username, $db_password, $db_name);

// Sjekk tilkoblingen
if ($conn->connect_error) {
    die("Tilkobling mislyktes: " . $conn->connect_error);
}
?>
