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
<!-- KODE FJERNET, 19.03.2026 -->

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
