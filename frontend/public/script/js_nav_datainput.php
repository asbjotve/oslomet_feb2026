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
require 'js_nav_datainput_sidehandtering.txt';
//require 'js_nav_datainput_skjemahandtering.txt';
//require 'js_nav_datainput_bokutdrag.txt';
echo '});';
//require 'js_nav_datainput_sammensatt.txt';
require 'js_nav_datainput_brukermeny.txt';
require 'js_nav_datainput_brukerhandtering.txt';
echo '</script>'
?>
