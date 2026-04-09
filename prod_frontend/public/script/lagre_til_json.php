<?php
// Starter sesjon, hvis en sesjon ikke allerede er startet
if ( session_status() == PHP_SESSION_NONE ) {
    session_start();
}

require_once __DIR__ . '/../path.php';
$lastet_side = 'lagring_data';

// Muliggjør henting av variabler fra globale phpdotenv-variabler
include_once $path_inc . '/konfigurasjonsfiler/dotenv_config.php';

// Henter relevante variabler for php og javascript-kode
include_once $path_inc . '/konfigurasjonsfiler/php_variables.php';

$eksisterende_til_sletting = isset($formData['eksisterende_til_sletting']) ? $formData['eksisterende_til_sletting'] : '';

// Sletter verdi, hvis det er valgt verdi fra drop-down-felt
if ($eksisterende_til_sletting == '1' && $formData['doktype_id'] == '1') {
    // Les innholdet av JSON-filen
    $data = file_get_contents($ureg_bok_json_php);
    //$data = file_get_contents('/var/www/plexcity.net/filoversikt/json/json_ureg_bok.txt');

    // Parse innholdet til en PHP-objekt
    $array = json_decode($data, true);

    // Sjekk om JSON-dekoding var vellykket
    if (json_last_error() !== JSON_ERROR_NONE) {
        // Håndter JSON-dekodingsfeil
        echo 'Feil ved dekoding av JSON: ' . json_last_error_msg();
        exit;
    }

    // Finn indeksen til objektet du vil slette basert på attributtverdien
    foreach ($array['response']['data'] as $key => $item) {
        if (isset($item['fieldData']['filnavn']) && $item['fieldData']['filnavn'] === $formData['filnavn']) {
            unset($array['response']['data'][$key]);
        }
    }

    // Reindekser arrayen for å fjerne eventuelle hull i nøklene
    $array['response']['data'] = array_values($array['response']['data']);

    // Konverter det oppdaterte objektet tilbake til en JSON-streng
    $json = json_encode($array, JSON_PRETTY_PRINT);

    // Sjekk om JSON-koding var vellykket
    if (json_last_error() !== JSON_ERROR_NONE) {
        // Håndter JSON-kodingsfeil
        echo 'Feil ved koding av JSON: ' . json_last_error_msg();
        exit;
    }

    // Skriv den oppdaterte JSON-strengen tilbake til filen
    if (file_put_contents($ureg_bok_json_php, $json)) {
    //if (file_put_contents('/var/www/plexcity.net/filoversikt/json/json_ureg_bok.txt', $json)) {
        //echo 'Filen er oppdatert!';
    } else {
        //echo 'Det oppstod en feil under oppdatering av filen';
    }
}

// Setter korrekt verdig for feltet for sideangivelse (hvis doktype_id = 4 (dvs. sammensatt-fil), skal sideangivelse hentes fra page_numbers
if ($formData ['doktype_id'] == '3'){
$sideangivelse = isset( $formData[ 'page_numbers' ] ) ? $formData[ 'page_numbers' ] : "";
} else {
$sideangivelse = isset( $formData[ 'sideangivelse' ] ) ? $formData[ 'sideangivelse' ] : "";
}
/*################################################*/
switch ( $formData[ 'doktype_id' ] ) {
    case '1':
        $fil = $bokutdrag_json_php;
        //$fil = "/var/www/plexcity.net/filoversikt/json/bokutdrag.txt";
        $data_fil = array(
            'fieldData' => array(
                'filnavn' => isset( $formData[ 'filnavn' ] ) ? $formData[ 'filnavn' ] : "",
                'boktittel' => isset( $formData[ 'boktittel' ] ) ? $formData[ 'boktittel' ] : "",
                'sideangivelse' => isset( $formData[ 'sideangivelse' ] ) ? $formData[ 'sideangivelse' ] : "",
                'kapittelnummer' => isset( $formData[ 'kapittelnummer' ] ) ? $formData[ 'kapittelnummer' ] : "",
                'kapittelforfatter' => isset( $formData[ 'kapittelforfatter' ] ) ? $formData[ 'kapittelforfatter' ] : "",
                'kapitteltittel' => isset( $formData[ 'kapitteltittel' ] ) ? $formData[ 'kapitteltittel' ] : "",
                'utgitt' => isset( $formData[ 'utgitt' ] ) ? $formData[ 'utgitt' ] : "",
                'forlag' => isset( $formData[ 'forlag' ] ) ? $formData[ 'forlag' ] : "",
                'forfatter' => isset( $formData[ 'forfatter' ] ) ? $formData[ 'forfatter' ] : "",
                'merknad' => isset( $formData[ 'merknad' ] ) ? $formData[ 'merknad' ] : "",
                'isbn' => isset( $formData[ 'isbn' ] ) ? $formData[ 'isbn' ] : "",
                'kommentar' => isset( $formData[ 'kommentar' ] ) ? $formData[ 'kommentar' ] : "",
                'mangler_i_fil' => isset( $formData[ 'mangler_i_fil' ] ) ? $formData[ 'mangler_i_fil' ] : "",
                'skannjobb_id' => isset( $formData[ 'skannjobb_id' ] ) ? $formData[ 'skannjobb_id' ] : "",
                'lagt_til_av_id' => isset( $formData[ 'user_id' ] ) ? $formData[ 'user_id' ] : "",
                'lagt_til_av_navn' => isset( $formData[ 'brukernavn' ] ) ? $formData[ 'brukernavn' ] : ""
            )
        );
break;
case '2':
$fil = $artikler_json_php;
//$fil = "/var/www/plexcity.net/filoversikt/json/artikler.txt";
 $data_fil = array(
            'fieldData' => array(
                'filnavn' => isset( $formData[ 'filnavn' ] ) ? $formData[ 'filnavn' ] : "",
                'artikkel_tittel' => isset( $formData[ 'artikkel_tittel' ] ) ? $formData[ 'artikkel_tittel' ] : "",
                'tidsskrift' => isset( $formData[ 'tidsskrift' ] ) ? $formData[ 'tidsskrift' ] : "",
                'argang_volume' => isset( $formData[ 'argang_volume' ] ) ? $formData[ 'argang_volume' ] : "",
                'hefte_issue' => isset( $formData[ 'hefte_issue' ] ) ? $formData[ 'hefte_issue' ] : "",
                'issn' => isset( $formData[ 'issn' ] ) ? $formData[ 'issn' ] : "",
                'forfatter' => isset( $formData[ 'forfatter' ] ) ? $formData[ 'forfatter' ] : "",
                'utgitt' => isset( $formData[ 'utgitt' ] ) ? $formData[ 'utgitt' ] : "",
                'lagt_til_av_id' => isset( $formData[ 'user_id' ] ) ? $formData[ 'user_id' ] : "",
                'lagt_til_av_navn' => isset( $formData[ 'brukernavn' ] ) ? $formData[ 'brukernavn' ] : ""
)
);
break;
case '4':
$fil = $annet_json_php;
//$fil = "/var/www/plexcity.net/filoversikt/json/annet.txt";
$data_fil = array(
            'fieldData' => array(
                'filnavn' => isset( $formData[ 'filnavn' ] ) ? $formData[ 'filnavn' ] : "",
                'tittel' => isset( $formData[ 'tittel' ] ) ? $formData[ 'tittel' ] : "",
                'forfatter' => isset( $formData[ 'forfatter' ] ) ? $formData[ 'forfatter' ] : "",
                'utgitt' => isset( $formData[ 'utgitt' ] ) ? $formData[ 'utgitt' ] : "",
                'sideangivelse' => isset( $formData[ 'sideangivelse' ] ) ? $formData[ 'sideangivelse' ] : "",
                'skannjobb_id' => isset( $formData[ 'skannjobb_id' ] ) ? $formData[ 'skannjobb_id' ] : "",
                'type_dokument' => isset( $formData[ 'type_dokument' ] ) ? $formData[ 'type_dokument' ] : "",
                'lagt_til_av_id' => isset( $formData[ 'user_id' ] ) ? $formData[ 'user_id' ] : "",
                'lagt_til_av_navn' => isset( $formData[ 'brukernavn' ] ) ? $formData[ 'brukernavn' ] : ""
)
);
break;
case '3':
$FIL = $sammensatt_json_php;
//$fil = "/var/www/plexcity.net/filoversikt/json/sammensatt.txt";
$data_fil = array(
            'fieldData' => array(
                'filnavn' => isset( $formData[ 'filnavn' ] ) ? $formData[ 'filnavn' ] : "",
                'fil_bestar_av' => isset( $formData[ 'fil_bestar_av' ] ) ? $formData[ 'fil_bestar_av' ] : "",
                'sideangivelse' => $sideangivelse,
                'mange_sideangivelser' => isset( $formData[ 'mange_sideangivelser' ] ) ? $formData[ 'mange_sideangivelser' ] : "",
                'lagt_til_av_id' => isset( $formData[ 'user_id' ] ) ? $formData[ 'user_id' ] : "",
                'lagt_til_av_navn' => isset( $formData[ 'brukernavn' ] ) ? $formData[ 'brukernavn' ] : ""
)
);
break;
    default:
}


// Les innholdet av den eksisterende JSON-filen
$jsonString = file_get_contents( $fil );

// Konverter JSON-innholdet til en PHP-array
$dataArray = json_decode( $jsonString, true );

// Legg til nye data i PHP-arrayen
$dataArray[ 'response' ][ 'data' ][] = $data_fil;

// Konverter PHP-arrayen tilbake til JSON
$newJsonString = json_encode( $dataArray, JSON_PRETTY_PRINT );

// Skriv den oppdaterte JSON-strengen tilbake til filen
file_put_contents( $fil, $newJsonString );

/*################################################*/

// Samle data fra skjemaet
$data_hovedfil = array(
    'fieldData' => array(
        'filnavn' => isset( $formData[ 'filnavn' ] ) ? $formData[ 'filnavn' ] : "",
        'boktittel' => isset( $formData[ 'boktittel' ] ) ? $formData[ 'boktittel' ] : "",
        'artikkel_tittel' => isset( $formData[ 'artikkel_tittel' ] ) ? $formData[ 'artikkel_tittel' ] : "",
        'tittel' => isset( $formData[ 'tittel' ] ) ? $formData[ 'tittel' ] : "",
        'sideangivelse' => $sideangivelse,
        'kapittelnummer' => isset( $formData[ 'kapittelnummer' ] ) ? $formData[ 'kapittelnummer' ] : "",
        'kapittelforfatter' => isset( $formData[ 'kapittelforfatter' ] ) ? $formData[ 'kapittelforfatter' ] : "",
        'kapitteltittel' => isset( $formData[ 'kapitteltittel' ] ) ? $formData[ 'kapitteltittel' ] : "",
        'utgitt' => isset( $formData[ 'utgitt' ] ) ? $formData[ 'utgitt' ] : "",
        'forlag' => isset( $formData[ 'forlag' ] ) ? $formData[ 'forlag' ] : "",
        'forfatter' => isset( $formData[ 'forfatter' ] ) ? $formData[ 'forfatter' ] : "",
        'merknad' => isset( $formData[ 'merknad' ] ) ? $formData[ 'merknad' ] : "",
        'isbn' => isset( $formData[ 'isbn' ] ) ? $formData[ 'isbn' ] : "",
        'issn' => isset( $formData[ 'issn' ] ) ? $formData[ 'issn' ] : "",
        'kommentar' => isset( $formData[ 'kommentar' ] ) ? $formData[ 'kommentar' ] : "",
        'mangler_i_fil' => isset( $formData[ 'mangler_i_fil' ] ) ? $formData[ 'mangler_i_fil' ] : "",
        'skannjobb_id' => isset( $formData[ 'skannjobb_id' ] ) ? $formData[ 'skannjobb_id' ] : "",
        'type_dokument' => isset( $formData[ 'type_dokument' ] ) ? $formData[ 'type_dokument' ] : "",
        'tidsskrift' => isset( $formData[ 'tidsskrift' ] ) ? $formData[ 'tidsskrift' ] : "",
        'argang_volume' => isset( $formData[ 'argang_volume' ] ) ? $formData[ 'argang_volume' ] : "",
        'hefte_issue' => isset( $formData[ 'hefte_issue' ] ) ? $formData[ 'hefte_issue' ] : "",
        'fil_bestar_av' => isset( $formData[ 'fil_bestar_av' ] ) ? $formData[ 'fil_bestar_av' ] : "",
        'alternativ_sideangivelse' => isset( $formData[ 'alt_side' ] ) ? $formData[ 'alt_side' ] : "",
        'mange_sideangivelser' => isset( $formData[ 'mange_sideangivelser' ] ) ? $formData[ 'mange_sideangivelser' ] : "",
        'doktype_id' => isset( $formData[ 'doktype_id' ] ) ? $formData[ 'doktype_id' ] : "",
        'lagt_til_av_id' => isset( $formData[ 'user_id' ] ) ? $formData[ 'user_id' ] : "",
        'lagt_til_av_navn' => isset( $formData[ 'brukernavn' ] ) ? $formData[ 'brukernavn' ] : "",
 )
);

/*
####################################################################################################
LEGGER TIL DATA I SAMLET FIL
##################################################################################################*/
// Les innholdet av den eksisterende JSON-filen
$jsonString = file_get_contents( $alle_reg_json_php );
//$jsonString = file_get_contents( '/var/www/plexcity.net/filoversikt/json/samlet_fil_utdrag.txt' );

// Konverter JSON-innholdet til en PHP-array
$dataArray = json_decode( $jsonString, true );

// Legg til nye data i PHP-arrayen
$dataArray[ 'response' ][ 'data' ][] = $data_hovedfil;

// Konverter PHP-arrayen tilbake til JSON
$newJsonString = json_encode( $dataArray, JSON_PRETTY_PRINT );

// Skriv den oppdaterte JSON-strengen tilbake til filen
file_put_contents( $alle_reg_json_php, $newJsonString );
//file_put_contents( '/var/www/plexcity.net/filoversikt/json/samlet_fil_utdrag.txt', $newJsonString );

$filnavn = $formData[ 'filnavn' ];


if ($formData['doktype_id'] == '1') {
    // Sjekk om ISBN finnes i json_ureg_bok.txt og legg til hvis det ikke finnes
    $isbnExists = false;
    $data = file_get_contents($unik_bok_isbn_php); //variabel hentes fra php_variables.php
    //$data = file_get_contents('/var/www/plexcity.net/filoversikt/json/json_bok_unik.txt');
    $array = json_decode($data, true);

    // Sjekk om JSON-dekoding var vellykket
    if (json_last_error() !== JSON_ERROR_NONE) {
        // Håndter JSON-dekodingsfeil
        echo 'Feil ved dekoding av JSON: ' . json_last_error_msg();
        exit;
    }

    // Sjekk om ISBN allerede finnes
    foreach ($array['response']['data'] as $item) {
        if (isset($item['fieldData']['isbn']) && $item['fieldData']['isbn'] === $formData['isbn']) {
            $isbnExists = true;
            break;
        }
    }

    // Hvis ISBN ikke finnes, legg til ny post
    if (!$isbnExists) {
        $newEntry = array(
            'fieldData' => array(
                'boktittel' => isset($formData['boktittel']) ? $formData['boktittel'] : "",
                'forfatter' => isset($formData['forfatter']) ? $formData['forfatter'] : "",
                'forlag' => isset($formData['forlag']) ? $formData['forlag'] : "",
                'isbn' => isset($formData['isbn']) ? $formData['isbn'] : "",
                'merknad' => isset($formData['merknad']) ? $formData['merknad'] : "",
                'utgitt' => isset($formData['utgitt']) ? $formData['utgitt'] : ""
            )
        );

        // Legg til den nye posten i arrayen
        $array['response']['data'][] = $newEntry;

        // Konverter det oppdaterte objektet tilbake til en JSON-streng
        $json = json_encode($array, JSON_PRETTY_PRINT);

        // Sjekk om JSON-koding var vellykket
        if (json_last_error() !== JSON_ERROR_NONE) {
            // Håndter JSON-kodingsfeil
            echo 'Feil ved koding av JSON: ' . json_last_error_msg();
            exit;
        }

        // Skriv den oppdaterte JSON-strengen tilbake til filen
if (file_put_contents($unik_bok_isbn_php, $json)) {
        //if (file_put_contents('/var/www/plexcity.net/filoversikt/json/json_bok_unik.txt', $json)) {
            //echo 'Filen er oppdatert!';
        } else {
            //echo 'Det oppstod en feil under oppdatering av filen';
        }
    }
}

$success[] = 'suksess';

$_SESSION[ 'form_data' ] = '';
//$errors[] = "Ingen error generert, data lagt til!";

?>
