<?php
// Starter sesjon, hvis en sesjon ikke allerede er startet
if ( session_status() == PHP_SESSION_NONE ) {
        session_start();
}

if ( $_SERVER[ "REQUEST_METHOD" ] == "POST" ) {

        // Angir hvilken switch, altså hvilet sett med variabler
        // fra php_variables, som skal lastes inn
        $lastet_side = 'lagring_data';

        // Angir hva som er hovedpath, f.eks. /var/www/plexcity.net/filoversikt/
        // Variabelen settes ved installasjon av filoversikt-nettstedet
        require_once __DIR__ . '/../path.php';

        // Laster inn phpdotenv
        include $path_inc . '/konfigurasjonsfiler/dotenv_config.php';

        // Laster inn php_variables.php
        include $path_inc . '/konfigurasjonsfiler/php_variables.php';

        if ( isset( $_POST[ 'skjema_type' ] ) && $_POST[ 'skjema_type' ] == 'endre_passord' ) {
                $success = array();
                $errors = array();

                include $endre_passord; //Definert i php_variables

        } else {
                $success = array();
                $errors = array();

                // Linje midlertidig de-aktivert - scriptet trengs å endres på
                //include '/var/www/plexcity.net/filoversikt/credentials/skjema_sjekk_innlogging.php';

                $uten_isbn_legg_til = isset( $_POST[ 'uten_isbn_legg_til' ] ) ? ( int )$_POST[ 'uten_isbn_legg_til' ] : 0;

                if ( $uten_isbn_legg_til === 1 ) {
                        $success = array();
                        $errors = array();
                        if ( empty( $errors ) ) {
                                // Lagrer verdier fra sesjonsvariabel i en variabel
                                $formData = $_SESSION[ 'form_data' ];

                                $filnavn_ureg_sjekk = isset( $formData[ 'filnavn' ] ) ? $formData[ 'filnavn' ] : "";

                                //include $lagre_json; //Erstatter linjen nedenfor
                                include $lagre_mysql; //Erstatter linjen nedenfor

                                // Sjekker om filnavnet finnes i JSON-filen og sletter objektet hvis det eksisterer
                                $filepath_json = "/var/www/plexcity.net/filoversikt/json/json_ureg_bok.txt";

                                if ( !empty( $filnavn ) && file_exists( $filepath_json ) ) {
                                        $json = file_get_contents( $filepath_json );
                                        $data = json_decode( $json );

                                        $filnavn = trim( $filnavn ); // Fjerner eventuelle ekstra mellomrom rundt filnavnet

                                        foreach ( $data as $key => $item ) {
                                                if ( $item->filnavn === $filnavn ) {
                                                        unset( $data[ $key ] ); // Sletter objektet som inneholder filnavnet
                                                        break;
                                                }
                                        }

                                        // Lagrer de oppdaterte dataene til JSON-filen
                                        file_put_contents( $filepath_json, json_encode( $data ) );

                                        //$success[] = "Objektet med filnavnet '$filnavn' ble slettet fra JSON-filen.";
                                } else {
                                        //$errors[] = "Filnavnet '$filnavn' ble ikke funnet i JSON-filen.";
                                }
                                //include '/var/www/plexcity.net/filoversikt/script/lagre_til_json.php';
                                //include '/var/www/plexcity.net/filoversikt/script/lagre_til_mysql.php';
                        }
                } else {
                        // Lagrer dataene som ble sendt i en sesjonsvariabell
                        $_SESSION[ 'form_data' ] = $_POST;

                        // Lagre verdier fra sesjonsvariabel i en variabel
                        $formData = $_SESSION[ 'form_data' ];

                        // Bruk htmlspecialchars på hver verdi
                        foreach ( $formData as $key => $value ) {
                                $formData[ $key ] = htmlspecialchars( $value, ENT_NOQUOTES, 'UTF-8' );
                        }

                        $filnavn = $formData[ 'filnavn' ]; // Brukes for å sjekke om filnavnet eksisterer fra før
                        $filnavn_felt = $filnavn; // Brukes til å sjekke format på filnavnet og om filnavn faktisk er satt

                        if ( empty( $filnavn_felt ) ) {
                                $errors[] = "- Feltet for FILNAVN kan ikke være tomt";
                        } elseif ( !preg_match( "/^(19|20)\d\d_(0[1-9]|1[012])_(0[1-9]|[12][0-9]|3[01])_(([01][0-9]|2[0-3])[0-5][0-9])$/", $filnavn_felt ) ) {
                                $errors[] = "- Feil filformat for FILNAVN: Det skal være skrevet i formatet ÅÅÅÅ_MM_DD_HHTT (HHTT = klokkeslett)";
                        } else {

                                $filepath = $alle_reg_json_php; //Erstatter linjen nedenfor
                                //$filepath = '/var/www/plexcity.net/filoversikt/json/samlet_fil_utdrag.txt';

                                // sjekk om filnavnet finnes i den valgte filen
                                if ( $filepath !== '' ) {
                                        $json = file_get_contents( $filepath );
                                        $data = json_decode( $json );

                                        foreach ( $data->response->data as $item ) {
                                                if ( $item->fieldData->filnavn === $filnavn ) {
                                                        $errors[] = "- FILNAVNet er allerede registrert i systemet, vennligst skriv inn et nytt";
                                                        break;
                                                }
                                        }
                                }
                        }

                        $doktype_id = isset( $formData[ 'doktype_id' ] ) ? $formData[ 'doktype_id' ] : '';
                        $boktittel = isset( $formData[ 'boktittel' ] ) ? $formData[ 'boktittel' ] : '';

                        $artikkel_tittel = isset( $formData[ 'artikkel_tittel' ] ) ? $formData[ 'artikkel_tittel' ] : '';
                        $isbn = isset( $formData[ 'isbn' ] ) ? $formData[ 'isbn' ] : '';

                        if ( $doktype_id == '1' ) {
                                // sjekk om boktittel er tomt, generer feilmelding hvis tomt.
                                if ( empty( $boktittel ) ) {
                                        $errors[] = "- Feltet for BOKTITTEL kan ikke være tomt";
                                }
                        } else if ( $doktype_id == '2' ) {
                                // sjekk om boktittel er tomt, generer feilmelding hvis tomt.
                                if ( empty( $artikkel_tittel ) ) {
                                        $errors[] = "- Feltet for TITTEL kan ikke være tomt";
                                }
                        }

                        // Her inkluderes fil for tilleggelse av data, hvis ingen feil er påvist
                        if ( empty( $errors ) ) {
                                if ( empty( $isbn ) && $doktype_id == '1' ) {
                                        $errors[] = "1";
                                } else {
                                        include $lagre_mysql;

                                        // Fortsett med sletting av objekt fra JSON-filen
                                        $filepath_json = "/var/www/plexcity.net/filoversikt/json/json_ureg_bok.txt";

                                        if ( !empty( $filnavn ) && file_exists( $filepath_json ) ) {
                                                $json = file_get_contents( $filepath_json );
                                                $data = json_decode( $json, true );

                                                $filnavn = trim( $filnavn ); // Fjerner eventuelle ekstra mellomrom rundt filnavnet

                                                $found = false;
                                                foreach ( $data as $key => $item ) {
                                                        if ( $item[ 'filnavn' ] === $filnavn ) {
                                                                unset( $data[ $key ] ); // Sletter objektet som inneholder filnavnet
                                                                $found = true;
                                                                break;
                                                        }
                                                }

                                                if ( $found ) {
                                                        // Lagrer de oppdaterte dataene til JSON-filen uten numeriske indekser
                                                        $data = array_values( $data ); // Fjerner numeriske indekser
                                                        file_put_contents( $filepath_json, json_encode( $data, JSON_PRETTY_PRINT ) );
                                                        //$success[] = "Objektet med filnavnet '$filnavn' ble slettet fra JSON-filen.";
                                                } else {
                                                        //$errors[] = "Filnavnet '$filnavn' ble ikke funnet i JSON-filen.";
                                                }
                                        } else {
                                                //$errors[] = "Feil ved å lese JSON-filen eller filnavn er tomt.";
                                        }


                                }
                        }

                }
        }
        // Forbereder JSON-respns med eventuelle feil og suksessmeldinger
        header( 'Content-Type: application/json' );
        echo json_encode( [ 'errors' => $errors, 'success' => $success, 'filnavn' => $filnavn ] );
        exit;
}
?>
