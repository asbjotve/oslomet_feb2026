<?php
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);

session_start();

$main_path          = "/var/www/dev.oslomet.plexcity.net/public/";
$oversikt_url       = $main_path . "hovedsider/filoversikt.php";
$datainput_url      = $main_path . "hovedsider/datainput.php";
$datainput_edit_url = $main_path . "hovedsider/datainput_edit.php";
$referansesjekk_url = $main_path . "hovedsider/referansesjekk.php";
$admin_url          = $main_path . "hovedsider/admin.php";
$loggut_url         = $main_path . "hovedsider/loggut.php";

// Hovedside
$target = $_SESSION['target'] ?? 'oversikt';

// Underside: fra GET hvis satt, ellers fra session
if (isset($_GET['sub'])) {
    $subpage = $_GET['sub'];
    $_SESSION['sub'] = $subpage;
} else {
    $subpage = $_SESSION['sub'] ?? null;
}

// Del verdien med hovedsidene
$current_subpage = $subpage;

// Velg hovedside
switch ($target) {
    case 'oversikt':
        include $oversikt_url;
        break;
    case 'datainput':
        include $datainput_url;
        break;
    case 'datainput_edit':
        include $datainput_edit_url;
        break;
    case 'referansesjekk':
        include $referansesjekk_url;
        break;
    case 'admin':
        include $admin_url;
        break;
    case 'loggut':
        include $loggut_url;
        break;
    default:
        include $oversikt_url;
        break;
}
?>
