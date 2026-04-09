<?php
session_start();
if (isset($_POST['target'])) {
    $_SESSION['target'] = $_POST['target'];
}

if (isset($_POST['role'])) {
    $_SESSION['role'] = $_POST['role'];
}
?>
