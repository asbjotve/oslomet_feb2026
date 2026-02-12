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

        <style>
                .menu-padding {
                padding-right: 30px;}
        </style>

<style>
.light-mode {
    background-color: green;
    color: white;
    border-color: black;
}

.nav-link.ajax-link.active::before {
  content: "";
  display: inline-block;
  width: 1.7em;
  height: 1.7em;
  margin-right: 6px;
  vertical-align: middle; /* eller baseline */
  /* margin-top: 1px;  Prøv deg frem! */
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' fill='currentColor' viewBox='0 0 17 17'><path fill-rule='evenodd' d='M10.146 4.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1 0 .708l-3 3a.5.5 0 0 1-.708-.708L12.293 8H2.5a.5.5 0 0 1 0-1h9.793l-2.147-2.146a.5.5 0 0 1 0-.708z'/></svg>");
  background-size: contain;
  background-repeat: no-repeat;
}

</style>

    </head>
    <body id="bootstrap-overrided">

<li><a class="dropdown-item ajax-link" data-target="datainput">Gå til oversikt over filer</a></li>
<a class="nav-link ajax-link">Artikler</a>


<div id="content">
</div>
<script>
$(document).on('click', 'a.ajax-link', function (event) {
    var $link  = $(this);
    var target = $link.data('target');   // undefined hvis ikke satt
    var href   = $link.attr('href');     // kan være undefined/empty

    // 1) Har data-target => bruk eksisterende set_target + full side-reload
    if (typeof target !== 'undefined' && target !== '') {
        event.preventDefault();

        $.post('/scripts/set_target.php', { target: target })
            .done(function () {
                // Last HELE siden på nytt via index.php (root)
                window.location.href = '/';
            })
            .fail(function (xhr, status, error) {
                console.error('Feil ved set_target:', error);
            });

        return;
    }

    // 2) Ingen data-target, men har href => last inn i #content via AJAX
    if (href && href !== '#') {
        event.preventDefault();

        $.ajax({
            url: href,
            type: 'GET',
            success: function (html) {
                // Sett hele responsen inn i content-diven
                $('#content').html(html);
            },
            error: function (xhr, status, error) {
                console.error('Feil ved lasting av innhold:', error);
                $('#content').html('<p>Kunne ikke laste innhold. Prøv igjen senere.</p>');
            }
        });

        return;
    }

    // 3) Hvis verken data-target eller href gir mening, gjør ingenting spesielt
    // (lenken kan oppføre seg normalt, eller du kan event.preventDefault() her også)
});
</script>
</body>
</html>
