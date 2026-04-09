<?php
// Starter sesjon/økt, dersom sesjon/økt ikke allerede er startet
if (session_status() == PHP_SESSION_NONE) {
    session_start();
}

$path_inc = "/var/www/dev.oslomet.plexcity.net/public/";
include_once $path_inc . 'konfigurasjonsfiler/dotenv_config.php';

/*
###################################################################
URL-VARIABLER
###################################################################
*/
$datainput_url = $_ENV['SERVER_PATH'] . $_ENV['BASE_URL'] . $_ENV['NAVIGERING_M'] . "/" . $_ENV['DATAINPUT'];
$admin_url = $_ENV['SERVER_PATH'] . $_ENV['BASE_URL'] . $_ENV['NAVIGERING_M'] . "/" . $_ENV['ADMIN'];
$oversikt_url = $_ENV['SERVER_PATH'] . $_ENV['BASE_URL'] . $_ENV['NAVIGERING_M'] . "/" . $_ENV['OVERSIKT'];
$datainput_edit_url = $_ENV['SERVER_PATH'] . $_ENV['BASE_URL'] . $_ENV['NAVIGERING_M'] . "/" . $_ENV['DATAINPUT_EDIT'];
$referansesjekk_url = $_ENV['SERVER_PATH'] . $_ENV['BASE_URL'] . $_ENV['NAVIGERING_M'] . "/" . $_ENV['REFERANSESJEKK'];

$target = $_SESSION['target'] ?? 'default';
switch($target) {
        case 'oversikt':
                include($oversikt_url);
                break;
        case 'datainput':
                include($datainput_url);
                break;
        case 'datainput_edit':
                include($datainput_edit_url);
                break;
        case 'referansesjekk':
                include($referansesjekk_url);
                break;
        case 'admin':
                include($admin_url);
                break;
        case 'loggut':
                include($loggut_url);
                break;
        default:
                include($oversikt_url);
                break;
}

?>
