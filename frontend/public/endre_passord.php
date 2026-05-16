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

  <meta charset="UTF-8">
  <title>Bytt passord</title>
  <style>
    body { font-family: Arial, sans-serif; }
    form { max-width: 320px; margin: 2rem auto; }
    input[type="password"], input[type="submit"] { width: 100%; padding: 10px; margin: 8px 0; }
    .error { color: red; }
    .success { color: green; }
  </style>
</head>
<body>
  <form id="changePasswordForm">
    <h2>Bytt passord</h2>
    <label for="oldPassword">Gammelt passord:</label>
    <input type="password" id="oldPassword" name="oldPassword" required autocomplete="current-password">
    
    <label for="newPassword">Nytt passord:</label>
    <input type="password" id="newPassword" name="newPassword" required autocomplete="new-password">
    
    <label for="repeatPassword">Gjenta nytt passord:</label>
    <input type="password" id="repeatPassword" name="repeatPassword" required autocomplete="new-password">
    
    <input type="submit" value="Bytt passord">
    <div id="message"></div>
  </form>

  <script>
    // Funksjon for å hente cookie-verdi
    function getCookie(name) {
      const value = `; ${document.cookie}`;
      const parts = value.split(`; ${name}=`);
      if (parts.length === 2) return parts.pop().split(';').shift();
      return null;
    }

    document.getElementById('changePasswordForm').addEventListener('submit', async function(e) {
      e.preventDefault();
      const oldPassword = document.getElementById('oldPassword').value;
      const newPassword = document.getElementById('newPassword').value;
      const repeatPassword = document.getElementById('repeatPassword').value;
      const messageDiv = document.getElementById('message');
      messageDiv.textContent = '';
      messageDiv.className = '';

      // Klientside validering
      if (newPassword !== repeatPassword) {
        messageDiv.textContent = 'Nytt passord og gjentatt passord er ikke like!';
        messageDiv.className = 'error';
        return;
      }

// Hent token fra cookie
const dataCookie = getCookie('data');
let token = null;
if (dataCookie) {
  try {
    // Cookie-verdien er URL-enkodet, så vi må dekode den først
    const decoded = decodeURIComponent(dataCookie);
    const json = JSON.parse(decoded);
    token = json.token;
  } catch (e) {
    token = null;
  }
}

if (!token) {
  messageDiv.textContent = 'Bruker ikke autentisert (token mangler).';
  messageDiv.className = 'error';
  return;
}

      // Send til API via proxy.php (eller direkte til ditt endepunkt)
      fetch('proxy.php?endpoint=api/change_password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'change_password',
          oldPassword: oldPassword,
          newPassword: newPassword,
          token: token
        })
      })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          messageDiv.textContent = 'Passordet ble endret!';
          messageDiv.className = 'success';
          document.getElementById('changePasswordForm').reset();
        } else {
          messageDiv.textContent = data.message || 'Noe gikk galt!';
          messageDiv.className = 'error';
        }
      })
      .catch(() => {
        messageDiv.textContent = 'En feil oppstod under kommunikasjon med serveren.';
        messageDiv.className = 'error';
      });
    });
  </script>
</body>
</html>
