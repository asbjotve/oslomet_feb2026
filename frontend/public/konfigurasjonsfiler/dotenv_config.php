<?php
// Setter innstillinger for miljøvariabler
require_once '/var/www/dev.oslomet.plexcity.net/vendor/autoload.php';
$dotenv = Dotenv\Dotenv::createImmutable('/var/www/dev.oslomet.plexcity.net', '.env.oslomet');
$dotenv->load();
?>
