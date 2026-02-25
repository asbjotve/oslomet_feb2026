# Navigasjonslogikk: Hovedsider + Undersider (session-basert, uten query-URL)

Denne filen dokumenterer hvordan navigasjonen er satt opp **uten** at URL-en endres:

- URL er alltid f.eks. `https://dev.oslomet.plexcity.net/` (ingen `?sub=...`).
- **Hovedsider** styres av `$_SESSION['target']` (via `set_target.php`).
- **Undersider** (innhold inni en hovedside, f.eks. i en `#content`‑div) styres av `$_SESSION['sub']`.
- **Én felles JS‑handler** håndterer alle hopp/lenker som skal bytte både hovedside og underside.

Strukturen (for referanse):

```text
frontend/public/
├── hovedsider
│   ├── datainput.php
│   └── filoversikt.php
├── index.php
├── scripts
│   ├── set_target.php
│   └── tabeller
│       └── js_bokutdrag.php
└── undersider
    └── tab_hallo.php
```

## 1. Roller

### 1.1 `index.php`

- Innstegspunkt for hele applikasjonen.
- Bestemmer **hvilken hovedside** som skal vises, basert på `$_SESSION['target']`.
- Leser **underside‑nøkkelen** `sub` fra `$_SESSION['sub']` og eksponerer den som `$current_subpage` til hovedsidene.
- Inneholder ikke HTML-layout; hver hovedside (`filoversikt.php`, `datainput.php`, ...) er fortsatt en full HTML-side.

### 1.2 `scripts/set_target.php`

- Tar imot AJAX‑kall fra JavaScript.
- Setter:
  - `$_SESSION['target']` (hovedside)
  - `$_SESSION['sub']` (underside‑nøkkel)

Brukes av generiske lenker/knapper for å forberede neste sidevisning.

### 1.3 Hovedsider (f.eks. `hovedsider/filoversikt.php`)

- Fullverdige HTML‑sider (`<!DOCTYPE html>`, `<head>`, `<body>`).
- Representerer en “seksjon” (f.eks. Filoversikt, Datainput).
- Har gjerne et område (f.eks. `<div id="content">`) hvor undersider kan lastes inn.
- Har et **oppslagstabell** som sier hvilken fil som hører til hvilken `sub`‑verdi.

### 1.4 Undersider (f.eks. `undersider/tab_hallo.php`)

- Inneholder bare HTML/PHP for innholdet som skal inn i en eksisterende `<div>` i hovedsiden (typisk `#content`).
- Ingen egen `<html>`, `<head>`, `<body>`.

### 1.5 JavaScript

- Én felles handler `.goto-via-target` håndterer alle lenker/knapper som skal:
  - sette `target` (og ev. `sub`) i session, og
  - redirecte til root (`/`), uten query-parametre.

I tillegg har du en `a.ajax-link`‑handler for lokale AJAX‑innlastinger i `#content`.

## 2. `index.php`: Hovedside + Underside fra session

```php name=frontend/public/index.php
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

// Underside: kun fra session (ingen GET-parametre)
$subpage = $_SESSION['sub'] ?? null;

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
```

**Viktig:**

- Ingen `$_GET['sub']` – `sub` styres utelukkende via session.
- URL er alltid ren (f.eks. `/`).

## 3. `scripts/set_target.php`: Setter hovedside + underside i session

```php name=frontend/public/scripts/set_target.php
<?php
session_start();

if (isset($_POST['target'])) {
    $_SESSION['target'] = $_POST['target'];
}

if (isset($_POST['sub'])) {
    $_SESSION['sub'] = $_POST['sub'];
}
```

- Kalles fra JavaScript via `$.post(...)`.
- `target` sier hvilken hovedside som skal vises neste gang `/` lastes.
- `sub` er valgfri og brukes til å forhåndsvelge en underside.

## 4. Generisk JS‑handler `.goto-via-target` (session-basert, URL = `/`)

Denne handleren brukes for alle knapper/lenker som skal bytte både hovedside og ev. underside.

```html name=frontend/public/hovedsider/datainput.php
<script>
$(document).on('click', 'a.ajax-link', function (event) {
    var $link  = $(this);
    var target = $link.data('target');   // undefined hvis ikke satt
    var href   = $link.attr('href');     // kan være undefined/empty

    // 1) Har data-target => bruk set_target + full side-reload (bytte hovedside)
    if (typeof target !== 'undefined' && target !== '') {
        event.preventDefault();

        $.post('/scripts/set_target.php', { target: target })
            .done(function () {
                window.location.href = '/';
            })
            .fail(function (xhr, status, error) {
                console.error('Feil ved set_target:', error);
            });

        return;
    }

    // 2) Ingen data-target, men href => last inn i #content via AJAX
    if (href && href !== '#') {
        event.preventDefault();

        $.ajax({
            url: href,
            type: 'GET',
            success: function (html) {
                $('#content').html(html);
            },
            error: function (xhr, status, error) {
                console.error('Feil ved lasting av innhold:', error);
                $('#content').html('<p>Kunne ikke laste innhold. Prøv igjen senere.</p>');
            }
        });

        return;
    }
});

// Handler for goto-via-target (setter target + sub i session, redirecter til '/')
$(document).on('click', '.goto-via-target', function (event) {
    event.preventDefault();

    var $el    = $(this);
    var target = $el.data('target');  // f.eks. "oversikt"
    var sub    = $el.data('sub');     // f.eks. "bokutdrag"

    if (!target) {
        console.error('goto-via-target mangler data-target');
        return;
    }

    var postData = { target: target };
    if (sub) {
        postData.sub = sub;
    }

    $.post('/scripts/set_target.php', postData)
        .done(function () {
            // All navigasjon går til root; index.php leser target + sub fra session
            window.location.href = '/';
        })
        .fail(function (xhr, status, error) {
            console.error('Feil ved set_target:', error);
        });
});
</script>
```

Merk:

- Ingen `?sub=...` i `href` eller `data-href`.
- Ingen lesing av `sub` fra URL i PHP.

## 5. Hovedside: `hovedsider/filoversikt.php` med `$subpages`

`filoversikt.php` har sitt eget sett med undersider definert i `$subpages`.

```php name=frontend/public/hovedsider/filoversikt.php
<?php
// Oppslagstabell: sub-nøkkel => filsti
$subpages = [
    'bokutdrag' => __DIR__ . '/../undersider/tab_hallo.php',
    'artikler'  => __DIR__ . '/../undersider/filoversikt_artikler.php',
    // legg til flere her etter behov
];
?>
<!DOCTYPE html>
<html lang="en" data-bs-theme="dark">
    <head>
        <link rel="icon" href="https://plexcity.net:4588/filoversikt/favicon.ico" />
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Document Title</title>

        <script src="/dist/js/jquery.min.js"></script>
        <link rel="stylesheet" href="/dist/css/bootstrap.min.css">
        <script src="/dist/js/bootstrap.bundle.min.js"></script>

        <!-- CSS-stiler her -->
    </head>
    <body id="bootstrap-overrided">

<li><a class="dropdown-item ajax-link" data-target="datainput">Gå til oversikt over filer</a></li>
<a class="nav-link ajax-link" href="/undersider/tab_bokutdrag.php">Artikler</a>

<div id="content">
    <?php
    if (!empty($current_subpage) && isset($subpages[$current_subpage])) {
        include $subpages[$current_subpage];
    } else {
        echo "<p>Velg en tab for å vise detaljer.</p>";
    }
    ?>
</div>

<script>
$(document).on('click', 'a.ajax-link', function (event) {
    var $link  = $(this);
    var target = $link.data('target');   // undefined hvis ikke satt
    var href   = $link.attr('href');     // kan være undefined/empty

    // 1) Har data-target => bytt hovedside via set_target + full reload
    if (typeof target !== 'undefined' && target !== '') {
        event.preventDefault();

        $.post('/scripts/set_target.php', { target: target })
            .done(function () {
                window.location.href = '/';
            })
            .fail(function (xhr, status, error) {
                console.error('Feil ved set_target:', error);
            });

        return;
    }

    // 2) Ingen data-target, men href => last inn i #content via AJAX
    if (href && href !== '#') {
        event.preventDefault();

        $.ajax({
            url: href,
            type: 'GET',
            success: function (html) {
                $('#content').html(html);
            },
            error: function (xhr, status, error) {
                console.error('Feil ved lasting av innhold:', error);
                $('#content').html('<p>Kunne ikke laste innhold. Prøv igjen senere.</p>');
            }
        });

        return;
    }
});
</script>

<!-- goto-via-target-handler kan ligge her eller i en felles .js-fil -->

</body>
</html>
```

### Underside-eksempel: `undersider/tab_hallo.php`

```php name=frontend/public/undersider/tab_hallo.php
HALLO, DETTE ER EN TEST
```

## 6. Eksempel: Fra `datainput.php` → `filoversikt` + underside `bokutdrag` (uten query i URL)

I `hovedsider/datainput.php`:

```html name=frontend/public/hovedsider/datainput.php
<!-- Knapp -->
<button
  type="button"
  class="btn btn-primary goto-via-target"
  data-target="oversikt"
  data-sub="bokutdrag">
  Gå til filoversikt (bokutdrag)
</button>

<!-- Lenke -->
<a
  href="#"
  class="goto-via-target"
  data-target="oversikt"
  data-sub="bokutdrag">
  Gå til filoversikt (bokutdrag)
</a>
```

Flyt:

1. Klikk → JS leser `data-target="oversikt"`, `data-sub="bokutdrag"`.
2. JS: `POST /scripts/set_target.php` med `target=oversikt`, `sub=bokutdrag`.
3. JS: redirect til `/` (ingen query-parametere).
4. `index.php`:
   - Leser `$_SESSION['target'] = oversikt` → inkluderer `filoversikt.php`.
   - Leser `$_SESSION['sub'] = bokutdrag` → `$current_subpage = 'bokutdrag'`.
5. `filoversikt.php`:
   - Ser `$subpages['bokutdrag']` → inkluderer `undersider/tab_hallo.php` i `#content`.

URL i adressefeltet er hele tiden bare `https://dev.oslomet.plexcity.net/`.

## 7. Legge til nye undersider uten å endre URL

For ny underside under `filoversikt`:

1. Lag fila, f.eks.:

   ```text
   frontend/public/undersider/filoversikt_anno.php
   ```

2. Registrer den i `$subpages` i `filoversikt.php`:

   ```php
   $subpages = [
       'bokutdrag' => __DIR__ . '/../undersider/tab_hallo.php',
       'artikler'  => __DIR__ . '/../undersider/filoversikt_artikler.php',
       'anno'      => __DIR__ . '/../undersider/filoversikt_anno.php',
   ];
   ```

3. Lag lenke/knapp hvor som helst:

   ```html
   <a
     href="#"
     class="goto-via-target"
     data-target="oversikt"
     data-sub="anno">
     Gå til filoversikt (anno-visning)
   </a>
   ```

Ingen query‑parametre, ingen endring i `index.php` eller `set_target.php` nødvendig – kun:

- én linje i `$subpages` for `filoversikt.php`, og
- en ny `.goto-via-target`‑lenke/knapp.
