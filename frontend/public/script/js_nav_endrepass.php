<?php
echo '<script>';
echo 'document.title = "OsloMet - Filregistrering";';
echo 'var debugMode = false;';
echo 'function debugLog() {';
echo '    if (debugMode) {';
echo '        console.log.apply(console, arguments);';
echo '    }';
echo '}';
echo '$(document).ready(function () {';
require 'js_nav_endrepass_sidehandtering.txt';
echo '});';
require 'js_nav_endrepass_brukermeny.txt';
require 'js_nav_endrepass_brukerhandtering.txt';
echo '</script>'
?>
