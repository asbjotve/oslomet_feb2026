<?php
session_start();
if (isset($_POST['target'])) {
    $_SESSION['target'] = $_POST['target'];
}
?>
