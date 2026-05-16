<?php
echo '<script>';
echo 'document.title = "OsloMet - Filoversikt";';

/*
echo '// Funksjon for å hente ut spesifikk cookie ved navn';
echo 'function getCookie(cname) {';
echo  'var name = cname + "=";';
echo  'var decodedCookie = decodeURIComponent(document.cookie);';
echo  'var ca = decodedCookie.split(';');';
echo  'for(var i = 0; i <ca.length; i++) {';
echo    'var c = ca[i];';
echo    'while (c.charAt(0) == \' \') {';
echo      'c = c.substring(1);';
echo    '}';
echo    'if (c.indexOf(name) == 0) {';
echo      'return c.substring(name.length, c.length);';
echo    '}';
echo  '}';
echo  'return "";';
echo '}';
*/

echo 'var debugMode = true;';
echo 'function debugLog() {';
echo '    if (debugMode) {';
echo '        console.log.apply(console, arguments);';
echo '    }';
echo '}';
echo '$(document).ready(function () {';
require 'js_nav_filoversikt_sidehandtering.txt';
//require 'js_nav_datainput_skjemahandtering.txt';
//require 'js_nav_datainput_bokutdrag.txt';
echo '});';
//require 'js_nav_datainput_sammensatt.txt';
require 'js_nav_filoversikt_brukermeny.txt';
require 'js_nav_filoversikt_brukerhandtering.txt';
//require 'js_nav_filoversikt_tabeller.txt';
echo '</script>'
?>
