<!-- LOGG INN MODAL -->
<div class="modal" tabindex="-1" id="logg_inn_modal">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h4 class="modal-title">Innlogging</h4>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
                <div id="warning_logg_inn"> </div>
                <form>
                    <div class="mb-3">
                        <label for="exampleInputPassword1" class="form-label">Brukernavn</label>
                        <input type="username" class="form-control" id="username" name="username">
                    </div>
                    <div class="mb-3">
                        <label for="exampleInputPassword1" class="form-label">Password</label>
                        <input type="password" class="form-control" id="password">
                    </div>
                    <button type="submit" class="btn btn-primary" id="submitButton">Logg inn</button>
                </form>
            </div>
        </div>
    </div>
</div>

<!-- ENDRE PASSORD MODAL -->
<div class="modal" tabindex="-1" id="endrePassordModal">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">
                    <svg xmlns="http://www.w3.org/2000/svg" width="25" height="25" fill="currentColor" class="bi bi-gear" viewBox="0 0 16 16">
                        <path d="M8 4.754a3.246 3.246 0 1 0 0 6.492 3.246 3.246 0 0 0 0-6.492M5.754 8a2.246 2.246 0 1 1 4.492 0 2.246 2.246 0 0 1-4.492 0"/>
                        <path d="M9.796 1.343c-.527-1.79-3.065-1.79-3.592 0l-.094.319a.873.873 0 0 1-1.255.52l-.292-.16c-1.64-.892-3.433.902-2.54 2.541l.159.292a.873.873 0 0 1-.52 1.255l-.319.094c-1.79.527-1.79 3.065 0 3.592l.319.094a.873.873 0 0 1 .52 1.255l-.16.292c-.892 1.64.901 3.434 2.541 2.54l.292-.159a.873.873 0 0 1 1.255.52l.094.319c.527 1.79 3.065 1.79 3.592 0l.094-.319a.873.873 0 0 1 1.255-.52l.292.16c1.64.893 3.434-.902 2.54-2.541l-.159-.292a.873.873 0 0 1 .52-1.255l.319-.094c1.79-.527 1.79-3.065 0-3.592l-.319-.094a.873.873 0 0 1-.52-1.255l.16-.292c.893-1.64-.902-3.433-2.541-2.54l-.292.159a.873.873 0 0 1-1.255-.52zm-2.633.283c.246-.835 1.428-.835 1.674 0l.094.319a1.873 1.873 0 0 0 2.693 1.115l.291-.16c.764-.415 1.6.42 1.184 1.185l-.159.292a1.873 1.873 0 0 0 1.116 2.692l.318.094c.835.246.835 1.428 0 1.674l-.319.094a1.873 1.873 0 0 0-1.115 2.693l.16.291c.415.764-.42 1.6-1.185 1.184l-.291-.159a1.873 1.873 0 0 0-2.693 1.116l-.094.318c-.246.835-1.428.835-1.674 0l-.094-.319a1.873 1.873 0 0 0-2.692-1.115l-.292.16c-.764.415-1.6-.42-1.184-1.185l.159-.291A1.873 1.873 0 0 0 1.945 8.93l-.319-.094c-.835-.246-.835-1.428 0-1.674l.319-.094A1.873 1.873 0 0 0 3.06 4.377l-.16-.292c-.415-.764.42-1.6 1.185-1.184l.292.159a1.873 1.873 0 0 0 2.692-1.115z"/>
                    </svg>
                    &nbsp;Endre passord</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
                <div id="warning_logg_inn"> </div>
                <form action="ajax_handler.php" method="post" class="g-3" id="endrePassordForm">
                    <div class="mb-3">
                        <label for="old_password" class="form-label">Gammelt passord:</label>
                        <input type="password" class="form-control" id="old_password" name="old_password" required>
                    </div>
                    <div class="mb-3">
                        <label for="new_password" class="form-label">Nytt passord:</label>
                        <input type="password" class="form-control" id="new_password" name="new_password" required>
                    </div>
                    <div class="mb-3">
                        <input type="hidden" value="endre_passord" name="skjema_type">
                        <input type="submit" class="btn btn-primary" value="Endre passord">
                    </div>
                </form>
            </div>
            <div class="modal-footer"> </div>
        </div>
    </div>
</div>

<!-- MODAL FOR ERRORS/FEIL -->
<div class="modal" tabindex="-1" id="errorModal">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header">
                <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="yellow" class="bi bi-exclamation-triangle-fill" viewBox="0 0 16 16">
                    <path d="M8.982 1.566a1.13 1.13 0 0 0-1.96 0L.165 13.233c-.457.778.091 1.767.98 1.767h13.713c.889 0 1.438-.99.98-1.767zM8 5c.535 0 .954.462.9.995l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 5.995A.905.905 0 0 1 8 5m.002 6a1 1 0 1 1 0 2 1 1 0 0 1 0-2"/>
                </svg>
                <h4 class="modal-title">&nbsp;&nbsp;Feil som må rettes</h4>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body" id="errorModalBody">
                <div class="form-check form-switch">
                    <input class="form-check-input" type="checkbox" role="switch" id="flexSwitchCheckDefault">
                    <label class="form-check-label" for="flexSwitchCheckDefault">Klikk her for å legge til fil, uten ISBN-nummer</label>
                </div>
                <p>Modal body text goes here.</p>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
            </div>
        </div>
    </div>
</div>

<!-- MODAL FOR SUKSESS-MELDINGER -->
<div class="modal" tabindex="-1" id="suksess">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="green" class="bi bi-check-circle" viewBox="0 0 16 16">
                    <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14m0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16"/>
                    <path d="m10.97 4.97-.02.022-3.473 4.425-2.093-2.094a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-1.071-1.05"/>
                </svg>
                <h5 class="modal-title">
                &nbsp; &>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
                <p>Modajghjgjgh</p>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                <button type="button" class="btn btn-primary">Save changes</button>
            </div>
        </div>
    </div>
</div>

<!-- MODAL HVIS TOMT ISBN-NUMMER -->
    <div class="modal fade" id="isbnModal" tabindex="-1" aria-labelledby="isbnModalLabel" aria-hidden="true">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="isbnModalLabel">Mangler ISBN-nummer</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Lukk"></button>
          </div>
          <div class="modal-body">
            Du har ikke fylt inn ISBN-nummer. Er du sikker på at du vil legge til posten uten ISBN?
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Avbryt</button>
            <button type="button" class="btn btn-primary" id="bekreftUtenISBN">Ja, legg til uten ISBN</button>
          </div>
        </div>
      </div>
    </div>

<!-- HOLD BRUKER INNLOGGET MODAL -->
<div class="modal" tabindex="-1" id="hold_innlogget">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h4 class="modal-title">Vil du holde deg innlogget?</h4>
            </div>
            <div class="modal-body">
<p>Du er i ferd med å bli automatisk logget ut, vil du likevel fortsette å være innlogget?</p>
<div id="nedtelling"></div>
                    <div class="text-center"><button type="button" class="btn btn-primary btn-lg" id="btn_hold_innlogget">Ja - hold meg innlogget</button></div>
            </div>
        </div>
    </div>
</div>

<!-- MODAL FOR ERROS (SPESIFIKT; UTLØPT TOKEN ELLER BRUKER IKKE INNLOGGET) -->
<div class="modal" tabindex="-1" id="utlogging">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Ikke innlogget</h5>
            </div>
            <div class="modal-body"> </div>
            <div class="modal-footer"> </div>
        </div>
    </div>
</div>
