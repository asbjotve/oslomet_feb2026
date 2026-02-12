<?php
session_start();

if (isset($_POST['target'])) {
    $_SESSION['target'] = $_POST['target'];
}

if (isset($_POST['sub'])) {
    $_SESSION['sub'] = $_POST['sub'];
}
