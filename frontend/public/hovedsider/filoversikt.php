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
    var target = $(this).data('target');
    if (!target) {
        return;
    }

    event.preventDefault(); // hindre normal lenke-oppførsel

    $.post('/scripts/set_target.php', { target: target }, function () {
        // Last HELE siden på nytt via index.php
        window.location.href = '/'; 
        // f.eks. main_project_path = '/index.php' eller '/';
    });
});
</script>

</body>
</html>
