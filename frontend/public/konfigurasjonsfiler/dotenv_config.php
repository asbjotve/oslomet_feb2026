<?php
// Setter innstillinger for miljøvariabler
require_once '/var/www/app.oslomet.plexcityhub.net/vendor/autoload.php';
$dotenv = Dotenv\Dotenv::createImmutable('/var/www/app.oslomet.plexcityhub.net/env-files', '.oslomet_filoversikt_env');
$dotenv->load();
?>
