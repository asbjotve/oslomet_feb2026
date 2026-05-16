<?php
// Starter sesjon, hvis en sesjon ikke allerede er startet
if (session_status() == PHP_SESSION_NONE) {
        session_start();
}

$modal_warning_time = 5 * 60 * 1000;

switch ($lastet_side) {
    case 'filoversikt':
        // Brukes kun til php-include
        $js_nav = $_ENV['SERVER_PATH'] . $_ENV['BASE_URL'] . $_ENV['SCRIPT_M'] . "/" . $_ENV['NAV_FO_JS'];
        $script_tab_bok = $_ENV['SERVER_PATH'] . $_ENV['BASE_URL'] . $_ENV['SCRIPT_M'] . "/" . $_ENV['FO_BOK_JS'];
        $script_tab_art = $_ENV['SERVER_PATH'] . $_ENV['BASE_URL'] . $_ENV['SCRIPT_M'] . "/" . $_ENV['FO_ARTIKLER_JS'];
        $script_tab_annet = $_ENV['SERVER_PATH'] . $_ENV['BASE_URL'] . $_ENV['SCRIPT_M'] . "/" . $_ENV['FO_ANNET_JS'];
        $script_tab_sammensatt = $_ENV['SERVER_PATH'] . $_ENV['BASE_URL'] . $_ENV['SCRIPT_M'] . "/" . $_ENV['FO_SAMMENSATT_JS'];
        $modals = $_ENV['SERVER_PATH'] . $_ENV['BASE_URL'] . $_ENV['NAVIGERING_M'] . "/" . $_ENV['MODALS'] ;


        // Brukes i javascript-kode
        $bokutdrag_p = $_ENV['BASE_URL'] . $_ENV['TABELLER_M'] . "/" . $_ENV['TB_BOK'];
        $artikler_p = $_ENV['BASE_URL'] . $_ENV['TABELLER_M'] . "/" . $_ENV['TB_ARTIKLER'];
        $annet_p = $_ENV['BASE_URL'] . $_ENV['TABELLER_M'] . "/" . $_ENV['TB_ANNET'];
        $sammensatt_p = $_ENV['BASE_URL'] . $_ENV['TABELLER_M'] . "/" . $_ENV['TB_SAMMENSATT'];

        $json_bokutdrag_p = $_ENV['BASE_URL'] . $_ENV['JSON_M'] . "/" . $_ENV['BOK_JSON'] ;
        $json_artikler_p = $_ENV['BASE_URL'] . $_ENV['JSON_M'] . "/" . $_ENV['ARTIKLER_JSON'] ;
        $json_annet_p = $_ENV['BASE_URL'] . $_ENV['JSON_M'] . "/" . $_ENV['ANNET_JSON'] ;
        $json_sammensatt_p = $_ENV['BASE_URL'] . $_ENV['JSON_M'] . "/" . $_ENV['SAMMENSATT_JSON'] ;
        $hold_innlogget_p = $_ENV['BASE_URL'] . $_ENV['CREDENTIALS_M'] . "/" . $_ENV['HOLD_INNLOGGET'];

        $brukermeny_p = $_ENV['BASE_URL'] . $_ENV['NAVIGERING_M'] . "/" . $_ENV['BRUKERMENY'] ;
        $bruker_id_var = isset($_SESSION['user']['bruker_id']) ? $_SESSION['user']['bruker_id'] : '' ;
        $rolle_id_sjekk = isset($_SESSION['user']['rolle_id']) ? $_SESSION['user']['rolle_id'] : '4';
        $logg_ut_p = $_ENV['BASE_URL'] . $_ENV['CREDENTIALS_M'] . "/" . $_ENV['LOGGUT_C'] ;
        $logg_inn_p = $_ENV['BASE_URL'] . $_ENV['CREDENTIALS_M'] . "/" . $_ENV['LOGGINN_C'];
        $main_project_p = $_ENV['BASE_URL'];
        $set_session_p = $_ENV['BASE_URL'] . $_ENV['SCRIPT_M'] . "/" . $_ENV['SET_SESSION'] ;



        echo '<script>';
        echo 'const MODAL_WARNING_TIME = ' . $modal_warning_time . ';';
        echo 'const bokutdrag_path ="' . $bokutdrag_p .'";';
        echo 'const artikler_path = "' . $artikler_p . '";';
        echo 'const annet_path = "' . $annet_p . '";';
        echo 'const sammensatt_path = "' . $sammensatt_p . '";';

        echo 'const main_project_path = "' . $main_project_p . '";';
        echo 'const setsession_path = "' . $set_session_p . '";';
        //echo 'const logg_ut_script_path = "' . $logg_ut_p . '";';
        echo 'const logg_ut_path = "' . $logg_ut_p . '";' ;
        echo 'const logg_inn_script_path = "' . $logg_inn_p . '";';
        echo 'const json_bokutdrag_path = "' . $json_bokutdrag_p . '";';
        echo 'const json_artikler_path ="' . $json_artikler_p . '";';
        echo 'const json_annet_path = "' . $json_annet_p . '";';
        echo 'const json_sammensatt_path = "' . $json_sammensatt_p . '";';
        echo 'const brukermeny_path = "' . $brukermeny_p . '";';
        echo 'var bruker_id_variable = "' . $bruker_id_var . '";';
        echo 'var hold_innlogget_cookie = "' . $hold_innlogget_p . '";' ;
        echo 'var rolle_id_sjekk = "' . $rolle_id_sjekk . '";';
        echo '</script>';

        break;
    case 'datainput':
        // Brukes ikke i javascript-koden
        $js_nav_datainput_path = $_ENV['SERVER_PATH'] . $_ENV['BASE_URL'] . $_ENV['SCRIPT_M'] . "/" . $_ENV['NAV_DI_JS'];
        $datainput_modal_path = $_ENV['SERVER_PATH'] . $_ENV['BASE_URL'] . $_ENV['NAVIGERING_M'] . "/" . $_ENV['MODALS'];

        $bokutdrag_json_php = $_ENV['SERVER_PATH'] . $_ENV['BASE_URL'] . $_ENV['JSON_M'] . "/" . $_ENV['BOK_JSON'];
        $artikler_json_php = $_ENV['SERVER_PATH'] . $_ENV['BASE_URL'] . $_ENV['JSON_M'] . "/" . $_ENV['ARTIKLER_JSON'];
        $annet_json_php = $_ENV['SERVER_PATH'] . $_ENV['BASE_URL'] . $_ENV['JSON_M'] . "/" . $_ENV['ANNET_JSON'];
        $sammensatt_json_php = $_ENV['SERVER_PATH'] . $_ENV['BASE_URL'] . $_ENV['JSON_M'] . "/" . $_ENV['SAMMENSATT_JSON'];
        $ureg_bok_json_php = $_ENV['SERVER_PATH'] . $_ENV['BASE_URL'] . $_ENV['JSON_M'] . "/" . $_ENV['UREG_FILER_JSON'] ;
        $alle_reg_json_php = $_ENV['SERVER_PATH'] . $_ENV['BASE_URL'] . $_ENV['JSON_M'] . "/" . $_ENV['ALLE_JSON'] ;
        $unik_bok_isbn_php = $_ENV['SERVER_PATH'] . $_ENV['BASE_URL'] . $_ENV['JSON_M'] . "/" . $_ENV['UNIK_ISBN_JSON'] ;

        // Brukes i javascript-kode
        $bokutdrag_p = $_ENV['BASE_URL'] . $_ENV['SKJEMA_M'] . "/" . $_ENV['SK_BOK'] ;
        $artikler_p = $_ENV['BASE_URL'] . $_ENV['SKJEMA_M'] . "/" . $_ENV['SK_ARTIKLER'] ;
        $annet_p = $_ENV['BASE_URL'] . $_ENV['SKJEMA_M'] . "/" . $_ENV['SK_ANNET'] ;
        $sammensatt_p = $_ENV['BASE_URL'] . $_ENV['SKJEMA_M'] . "/" . $_ENV['SK_SAMMENSATT'] ;
        $js_skjema_sammensatt = $_ENV['SERVER_PATH'] . $_ENV['BASE_URL'] . $_ENV['SCRIPT_M'] . "/" . $_ENV['JS_DI_SAMMENSATT'];

        $ureg_bok_json = $_ENV['BASE_URL'] . $_ENV['JSON_M'] . "/" . $_ENV['UREG_FILER_JSON'] ;
        $unik_isbn_bok_p = $_ENV['BASE_URL'] . $_ENV['JSON_M'] . "/" . $_ENV['UNIK_ISBN_JSON'] ;
        $bokutdrag_json = $_ENV['BASE_URL'] . $_ENV['JSON_M'] . "/" . $_ENV['BOK_JSON'];
        $artikler_json = $_ENV['BASE_URL'] . $_ENV['JSON_M'] . "/" . $_ENV['ARTIKLER_JSON'];
        $hold_innlogget_p = $_ENV['BASE_URL'] . $_ENV['CREDENTIALS_M'] . "/" . $_ENV['HOLD_INNLOGGET'];

        $set_session_p = $_ENV['BASE_URL'] . $_ENV['SCRIPT_M'] . "/" . $_ENV['SET_SESSION'] ;
        $bruker_id_var = isset($_SESSION['user']['bruker_id']) ? $_SESSION['user']['bruker_id'] : '' ;
        $brukernavn_var = isset($_SESSION['user']['name']) ? $_SESSION['user']['name'] : '' ;
        $main_project_p = $_ENV['BASE_URL'] ;
        $logg_ut_p = $_ENV['BASE_URL'] . $_ENV['CREDENTIALS_M'] . "/" . $_ENV['LOGGUT_C'] ;
        $rolle_id_sjekk = isset($_SESSION['user']['rolle_id']) ? $_SESSION['user']['rolle_id'] : '4' ;
        $brukermeny_p = $_ENV['BASE_URL'] . $_ENV['NAVIGERING_M'] . "/" . $_ENV['BRUKERMENY'] ;
        $json_bokutdrag_p = $_ENV['BASE_URL'] . $_ENV['JSON_M'] . "/" . $_ENV['BOK_JSON'] ;
        $token = isset($_SESSION['user']['token']) ? $_SESSION['user']['token'] : '' ;
$refsjekk_p = "/" . "js_referansesjekk.php" ;

        echo '<script>';
        echo 'const MODAL_WARNING_TIME = ' . $modal_warning_time . ';';
        echo 'const bokutdrag_path = "' . $bokutdrag_p . '";';
        echo 'const artikler_path = "' . $artikler_p . '";';
        echo 'const annet_path = "' . $annet_p . '";';
        echo 'const sammensatt_path = "' . $sammensatt_p . '";';
        echo 'const ureg_bok = "' . $ureg_bok_json . '";';
        echo 'const json_bok_unik_isbn = "' . $unik_isbn_bok_p . '";';
        echo 'const main_project_path = "' . $main_project_p . '";';
        echo 'const setsession_path = "' . $set_session_p . '";';
        echo 'const logg_ut_path = "' . $logg_ut_p . '";' ;
        echo 'var bruker_id_variable = "' . $bruker_id_var . '";' ;
        echo 'const brukermeny_path = "' . $brukermeny_p . '";';
        echo 'var rolle_id_sjekk = "' . $rolle_id_sjekk . '";' ;
        echo 'var token = "' . $token . '";' ;
        echo 'var user_id = "' . $bruker_id_var . '";' ;
        echo 'var brukernavn = "' . $brukernavn_var . '";' ;
        echo 'var hold_innlogget_cookie = "' . $hold_innlogget_p . '";' ;
        echo 'const json_bokutdrag = "' . $json_bokutdrag_p . '";' ;
        echo 'const json_bokutdrag_nc = "' . $json_bokutdrag_p . '?nocache=" + new Date().getTime();';
        echo 'const refsjekk_path = "' . $refsjekk_p . '";' ;
        echo '</script>';
break;
    case 'referansesjekk':
        // Brukes ikke i javascript-koden
        $js_nav_datainput_path = $_ENV['SERVER_PATH'] . $_ENV['BASE_URL'] . $_ENV['SCRIPT_M'] . "/" . $_ENV['NAV_DI_JS'];
        $datainput_modal_path = $_ENV['SERVER_PATH'] . $_ENV['BASE_URL'] . $_ENV['NAVIGERING_M'] . "/" . $_ENV['MODALS'];

        // Brukes i javascript-kode
        $hold_innlogget_p = $_ENV['BASE_URL'] . $_ENV['CREDENTIALS_M'] . "/" . $_ENV['HOLD_INNLOGGET'];

        $set_session_p = $_ENV['BASE_URL'] . $_ENV['SCRIPT_M'] . "/" . $_ENV['SET_SESSION'] ;
        $bruker_id_var = isset($_SESSION['user']['bruker_id']) ? $_SESSION['user']['bruker_id'] : '' ;
        $brukernavn_var = isset($_SESSION['user']['name']) ? $_SESSION['user']['name'] : '' ;
        $main_project_p = $_ENV['BASE_URL'] ;
        $logg_ut_p = $_ENV['BASE_URL'] . $_ENV['CREDENTIALS_M'] . "/" . $_ENV['LOGGUT_C'] ;
        $rolle_id_sjekk = isset($_SESSION['user']['rolle_id']) ? $_SESSION['user']['rolle_id'] : '4' ;
        $brukermeny_p = $_ENV['BASE_URL'] . $_ENV['NAVIGERING_M'] . "/" . $_ENV['BRUKERMENY'] ;
        $json_bokutdrag_p = $_ENV['BASE_URL'] . $_ENV['JSON_M'] . "/" . $_ENV['BOK_JSON'] ;
        $token = isset($_SESSION['user']['token']) ? $_SESSION['user']['token'] : '' ;
	$js_nav_referansesjekk_path = $_ENV['SERVER_PATH'] . $_ENV['BASE_URL'] . $_ENV['SCRIPT_M'] . "/" . $_ENV['NAV_RS_JS'];
        $refsjekk_p = $_ENV['BASE_URL'] . $_ENV['ANDRE_SIDER_M'] . "/" . $_ENV['AS_REFSJEKK'];

        echo '<script>';
        echo 'const MODAL_WARNING_TIME = ' . $modal_warning_time . ';';
        echo 'const main_project_path = "' . $main_project_p . '";';
        echo 'const setsession_path = "' . $set_session_p . '";';
        echo 'const logg_ut_path = "' . $logg_ut_p . '";' ;
        echo 'var bruker_id_variable = "' . $bruker_id_var . '";' ;
        echo 'const brukermeny_path = "' . $brukermeny_p . '";';
        echo 'var brukernavn = "' . $brukernavn_var . '";' ;
        echo 'var hold_innlogget_cookie = "' . $hold_innlogget_p . '";' ;
        echo 'const refsjekk_path = "' . $refsjekk_p . '";' ;
        echo '</script>';
break;
    case 'endrepass':
        // Brukes ikke i javascript-koden
        $js_nav_datainput_path = $_ENV['SERVER_PATH'] . $_ENV['BASE_URL'] . $_ENV['SCRIPT_M'] . "/" . $_ENV['NAV_DI_JS'];
        $datainput_modal_path = $_ENV['SERVER_PATH'] . $_ENV['BASE_URL'] . $_ENV['NAVIGERING_M'] . "/" . $_ENV['MODALS'];

        // Brukes i javascript-kode
        $hold_innlogget_p = $_ENV['BASE_URL'] . $_ENV['CREDENTIALS_M'] . "/" . $_ENV['HOLD_INNLOGGET'];

        $set_session_p = $_ENV['BASE_URL'] . $_ENV['SCRIPT_M'] . "/" . $_ENV['SET_SESSION'] ;
        $bruker_id_var = isset($_SESSION['user']['bruker_id']) ? $_SESSION['user']['bruker_id'] : '' ;
        $brukernavn_var = isset($_SESSION['user']['name']) ? $_SESSION['user']['name'] : '' ;
        $main_project_p = $_ENV['BASE_URL'] ;
        $logg_ut_p = $_ENV['BASE_URL'] . $_ENV['CREDENTIALS_M'] . "/" . $_ENV['LOGGUT_C'] ;
        $rolle_id_sjekk = isset($_SESSION['user']['rolle_id']) ? $_SESSION['user']['rolle_id'] : '4' ;
        $brukermeny_p = $_ENV['BASE_URL'] . $_ENV['NAVIGERING_M'] . "/" . $_ENV['BRUKERMENY'] ;
        $json_bokutdrag_p = $_ENV['BASE_URL'] . $_ENV['JSON_M'] . "/" . $_ENV['BOK_JSON'] ;
        $token = isset($_SESSION['user']['token']) ? $_SESSION['user']['token'] : '' ;
        $js_nav_referansesjekk_path = $_ENV['SERVER_PATH'] . $_ENV['BASE_URL'] . $_ENV['SCRIPT_M'] . "/" . $_ENV['NAV_RS_JS'];
        $ENDREPASS_p = $_ENV['BASE_URL'] . $_ENV['ANDRE_SIDER_M'] . "/" . $_ENV['AS_ENDREPASS'];

        echo '<script>';
        echo 'const MODAL_WARNING_TIME = ' . $modal_warning_time . ';';
        echo 'const main_project_path = "' . $main_project_p . '";';
        echo 'const setsession_path = "' . $set_session_p . '";';
        echo 'const logg_ut_path = "' . $logg_ut_p . '";' ;
        echo 'var bruker_id_variable = "' . $bruker_id_var . '";' ;
        echo 'const brukermeny_path = "' . $brukermeny_p . '";';
        echo 'var brukernavn = "' . $brukernavn_var . '";' ;
        echo 'var hold_innlogget_cookie = "' . $hold_innlogget_p . '";' ;
        echo 'const endrepass_path = "' . $refsjekk_p . '";' ;
        echo '</script>';
break;
    case 'lagring_data':
        $bokutdrag_json_php = $_ENV['SERVER_PATH'] . $_ENV['BASE_URL'] . $_ENV['JSON_M'] . "/" . $_ENV['BOK_JSON'];
        $artikler_json_php = $_ENV['SERVER_PATH'] . $_ENV['BASE_URL'] . $_ENV['JSON_M'] . "/" . $_ENV['ARTIKLER_JSON'];
        $annet_json_php = $_ENV['SERVER_PATH'] . $_ENV['BASE_URL'] . $_ENV['JSON_M'] . "/" . $_ENV['ANNET_JSON'];
        $sammensatt_json_php = $_ENV['SERVER_PATH'] . $_ENV['BASE_URL'] . $_ENV['JSON_M'] . "/" . $_ENV['SAMMENSATT_JSON'];
        $ureg_bok_json_php = $_ENV['SERVER_PATH'] . $_ENV['BASE_URL'] . $_ENV['JSON_M'] . "/" . $_ENV['UREG_FILER_JSON'] ;
        $alle_reg_json_php = $_ENV['SERVER_PATH'] . $_ENV['BASE_URL'] . $_ENV['JSON_M'] . "/" . $_ENV['ALLE_JSON'] ;
        $unik_bok_isbn_php = $_ENV['SERVER_PATH'] . $_ENV['BASE_URL'] . $_ENV['JSON_M'] . "/" . $_ENV['UNIK_ISBN_JSON'] ;
        $endre_passord = $_ENV['SERVER_PATH'] . $_ENV['BASE_URL'] . $_ENV['SCRIPT_M'] . "/" . $_ENV['C_PASSORD'];
        $lagre_json = $_ENV['SERVER_PATH']. $_ENV['BASE_URL']. $_ENV['SCRIPT_M'] . "/" . $_ENV['LAGRE_JSON'];
        $lagre_mysql = $_ENV['SERVER_PATH'] . $_ENV['BASE_URL'] . $_ENV['SCRIPT_M'] . "/" . $_ENV['LAGRE_MYSQL'];
        $db_servername = $_ENV['DB_SERVERNAME'];
        $db_username = $_ENV['DB_USERNAME'];
        $db_password = $_ENV['DB_PASSWORD'];
        $db_name = $_ENV['DB_NAME'];
break;
    case 'tab':
        $script_tab_bok = $_ENV['SERVER_PATH'] . $_ENV['BASE_URL'] . $_ENV['SCRIPT_M'] . "/" . $_ENV['FO_BOK_JS'];
        $script_tab_art = $_ENV['SERVER_PATH'] . $_ENV['BASE_URL'] . $_ENV['SCRIPT_M'] . "/" . $_ENV['FO_ARTIKLER_JS'];
        $script_tab_annet = $_ENV['SERVER_PATH'] . $_ENV['BASE_URL'] . $_ENV['SCRIPT_M'] . "/" . $_ENV['FO_ANNET_JS'];
        $script_tab_sammensatt = $_ENV['SERVER_PATH'] . $_ENV['BASE_URL'] . $_ENV['SCRIPT_M'] . "/" . $_ENV['FO_SAMMENSATT_JS'];
break;
    default:
        $json_samlet_fil = $_ENV['SERVER_PATH'] . $_ENV['BASE_URL'] . $_ENV['JSON_M'] . "/" . $_ENV['ALLE_JSON'];
        $lagre_json = $_ENV['SERVER_PATH']. $_ENV['BASE_URL']. $_ENV['SCRIPT_M'] . "/" . $_ENV['LAGRE_JSON'];
        $lagre_mysql = $_ENV['SERVER_PATH'] . $_ENV['BASE_URL'] . $_ENV['SCRIPT_M'] . "/" . $_ENV['LAGRE_MYSQL'];
        $endre_passord = $_ENV['SERVER_PATH'] . $_ENV['BASE_URL'] . $_ENV['SCRIPT_M'] . "/" . $_ENV['C_PASSORD'];
        $token_expiry = $_ENV['TOKEN_EXPIRY'];
        $cookie_path = $_ENV['BASE_URL'];
        $db_servername = $_ENV['DB_SERVERNAME'];
        $db_username = $_ENV['DB_USERNAME'];
        $db_password = $_ENV['DB_PASSWORD'];
        $db_name = $_ENV['DB_NAME'];
        break;
}
