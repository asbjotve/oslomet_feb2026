<?php
// Starter sesjon, hvis en sesjon ikke allerede er startet
if ( session_status() == PHP_SESSION_NONE ) {
    session_start();
}

require_once __DIR__ . '/../path.php';
include $path_inc . '/credentials/db_connection.php';

//######################################################################
// Funksjon for å hente data fra databasen og lagre som JSON i en fil
//######################################################################
function fetchDataAndSaveToFile($conn, $sql, $file_path) {
    $result = $conn->query($sql);

    // Sjekk om spørringen returnerte noen resultater
    if ($result->num_rows > 0) {
        $data = array();

        // Hent hver rad som en assosiativ array og legg til under fieldData
        while ($row = $result->fetch_assoc()) {
            // Erstatt null-verdier med tomme strenger
            foreach ($row as $key => $value) {
                if (is_null($value)) {
                    $row[$key] = "";
                }
            }
            $data[] = array('fieldData' => $row);
        }

        // Bygg opp responsstrukturen
        $response = array('response' => array('status' => 'success', 'data' => $data));

        // Konverter resultatene til JSON-format med pretty print
        $json_data = json_encode($response, JSON_PRETTY_PRINT);

        // Lagre JSON-dataene i en .txt-fil
        if (file_put_contents($file_path, $json_data)) {
            //echo "Data successfully written to " . $file_path;
        } else {
            //echo "Failed to write data to " . $file_path;
        }
    } else {
        //echo json_encode(array('status' => 'error', 'message' => 'No records found.'));
    }
}

//######################################################################
// Legg data i MySQL
//######################################################################
// Forbered og bind
$stmt = $conn->prepare("INSERT INTO filoversikt_data (filnavn, boktittel, artikkel_tittel, tittel, kapittelnummer, kapittelforfatter, kapitteltittel, utgitt, forlag, forfatter, merknad, isbn, issn, kommentar, mangler_i_fil, skannjobb_id, type_dokument, tidsskrift, argang_volume, hefte_issue, fil_bestar_av, alternativ_sideangivelse, mange_sideangivelser, doktype_id, lagt_til_av_id, lagt_til_av_navn, sideangivelse) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)");

        $filnavn = isset( $formData[ 'filnavn' ] ) ? $formData[ 'filnavn' ] : "";
        $boktittel = isset( $formData[ 'boktittel' ] ) ? $formData[ 'boktittel' ] : "";
        $artikkel_tittel = isset( $formData[ 'artikkel_tittel' ] ) ? $formData[ 'artikkel_tittel' ] : "";
        $tittel = isset( $formData[ 'tittel' ] ) ? $formData[ 'tittel' ] : "";
        if ($formData ['doktype_id'] == '3'){
                        $sideangivelse = isset( $formData[ 'page_numbers' ] ) ? $formData[ 'page_numbers' ] : "";
                } else {
                        $sideangivelse = isset( $formData[ 'sideangivelse' ] ) ? $formData[ 'sideangivelse' ] : "";
                }
        $kapittelnummer = isset( $formData[ 'kapittelnummer' ] ) ? $formData[ 'kapittelnummer' ] : "";
        $kapittelforfatter = isset( $formData[ 'kapittelforfatter' ] ) ? $formData[ 'kapittelforfatter' ] : "";
        $kapitteltittel = isset( $formData[ 'kapitteltittel' ] ) ? $formData[ 'kapitteltittel' ] : "";
        $utgitt = isset( $formData[ 'utgitt' ] ) ? $formData[ 'utgitt' ] : "";
        $forlag = isset( $formData[ 'forlag' ] ) ? $formData[ 'forlag' ] : "";
        $forfatter = isset( $formData[ 'forfatter' ] ) ? $formData[ 'forfatter' ] : "";
        $merknad = isset( $formData[ 'merknad' ] ) ? $formData[ 'merknad' ] : "";
        $isbn = isset( $formData[ 'isbn' ] ) ? $formData[ 'isbn' ] : "";
        $issn = isset( $formData[ 'issn' ] ) ? $formData[ 'issn' ] : "";
        $kommentar = isset( $formData[ 'kommentar' ] ) ? $formData[ 'kommentar' ] : "";
        $mangler_i_fil = isset( $formData[ 'mangler_i_fil' ] ) ? $formData[ 'mangler_i_fil' ] : "";
        $skannjobb_id = isset( $formData[ 'skannjobb_id' ] ) ? $formData[ 'skannjobb_id' ] : "";
        $type_dokument = isset( $formData[ 'type_dokument' ] ) ? $formData[ 'type_dokument' ] : "";
        $tidsskrift = isset( $formData[ 'tidsskrift' ] ) ? $formData[ 'tidsskrift' ] : "";
        $argang_volume = isset( $formData[ 'argang_volume' ] ) ? $formData[ 'argang_volume' ] : "";
        $hefte_issue = isset( $formData[ 'hefte_issue' ] ) ? $formData[ 'hefte_issue' ] : "";
        $fil_bestar_av = isset( $formData[ 'fil_bestar_av' ] ) ? $formData[ 'fil_bestar_av' ] : "";
        $alternativ_sideangivelse = isset( $formData[ 'alt_side' ] ) ? $formData[ 'alt_side' ] : "";
        $mange_sideangivelser = isset( $formData[ 'mange_sideangivelser' ] ) ? $formData[ 'mange_sideangivelser' ] : 0;
        $doktype_id = isset( $formData[ 'doktype_id' ] ) ? $formData[ 'doktype_id' ] : "";
        $brukerID = isset( $formData[ 'user_id' ] ) ? $formData[ 'user_id' ] : "";
        $bruker_navn = isset( $formData[ 'brukernavn' ] ) ? $formData[ 'brukernavn' ] : "";

if ($stmt === false) {
    error_log('mysqli prepare error: ' . $conn->error);
}

$stmt->bind_param("sssssssssssssssssssssssssss", $filnavn, $boktittel, $artikkel_tittel, $tittel, $kapittelnummer, $kapittelforfatter, $kapitteltittel, $utgitt, $forlag, $forfatter, $merknad, $isbn, $issn,  $kommentar, $mangler_i_fil, $skannjobb_id, $type_dokument, $tidsskrift, $argang_volume, $hefte_issue, $fil_bestar_av, $alternativ_sideangivelse, $mange_sideangivelser, $doktype_id, $brukerID, $bruker_navn, $sideangivelse);

$success = $stmt->execute();

if ($success === false) {
    error_log('mysqli execute error: ' . $stmt->error);
}

//######################################################################
// Produserer JSON-filene
//######################################################################
switch ($formData['doktype_id']) {
    case '1':
        $sql = "SELECT * FROM filoversikt_data WHERE doktype_id='1'";
        $file_path = $path_inc . '/json/bokutdrag.txt'; // Endre denne banen til ønsket filplassering
        fetchDataAndSaveToFile($conn, $sql, $file_path);
        break;

            case '2':
        $sql = "SELECT * FROM filoversikt_data WHERE doktype_id='2'";
        $file_path = $path_inc . '/json/artikler.txt'; // Endre denne banen til ønsket filplassering
        fetchDataAndSaveToFile($conn, $sql, $file_path);
        break;

            case '3':
        $sql = "SELECT * FROM filoversikt_data WHERE doktype_id='3'";
        $file_path = $path_inc . '/json/sammensatt.txt'; // Endre denne banen til ønsket filplassering
        fetchDataAndSaveToFile($conn, $sql, $file_path);
        break;

            case '4':
        $sql = "SELECT * FROM filoversikt_data WHERE doktype_id='4'";
        $file_path = $path_inc . '/json/annet.txt'; // Endre denne banen til ønsket filplassering
        fetchDataAndSaveToFile($conn, $sql, $file_path);
        break;

    default:
        echo json_encode(array('status' => 'error', 'message' => 'Invalid doktype_id.'));
        break;
}

        $sql = "SELECT * FROM filoversikt_data";
        $file_path = $path_inc . '/json/samlet_fil_utdrag.txt'; // Endre denne banen til ønsket filplassering
        fetchDataAndSaveToFile($conn, $sql, $file_path);

        $sql = "SELECT 
                  boktittel, 
                  forfatter, 
                  forlag, 
                  isbn, 
                  merknad, 
                  utgitt 
                FROM 
                  filoversikt_data 
                WHERE 
                  doktype_id = 1 AND 
                  isbn IS NOT NULL 
                GROUP BY isbn";
        $file_path = $path_inc . '/json/json_bok_unik.txt'; // Endre denne banen til ønsket filplassering
        fetchDataAndSaveToFile($conn, $sql, $file_path);


$stmt->close();
$conn->close();

$success = array();
$success[] = 'suksess';
?>
