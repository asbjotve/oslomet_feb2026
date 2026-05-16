<?php

// sjekker om 'rolle'-cookie er satt og ikke er undefined
if (isset($_COOKIE['role']) && $_COOKIE['role'] !== 'undefined') {
    // bruker verdien i 'rolle'-cookie
    $role = $_COOKIE['role'];
} else {
    // setter $role til 4 hvis 'rolle'-cookie ikke er satt eller er undefined
    $role = 4;
}

    switch ($role) {
        case '1':
            $menu = '<ul class="dropdown-menu" aria-labelledby="navbarDropdown">
                        <li><a class="dropdown-item ajax-link" data-target="admin">Administrasjon</a></li>
                        <li><a class="dropdown-item ajax-link">Endre passord</a></li>
                        <li><hr class="dropdown-divider"></li>
                        <li><a class="dropdown-item ajax-link" data-target="oversikt">Gå til oversikt over filer</a></li>
                        <li><a class="dropdown-item ajax-link" data-target="datainput">Legg til data</a></li>
                        <li><a class="dropdown-item ajax-link" data-target="datainput_edit">Rediger eksisterende data</a></li>
                        <li><hr class="dropdown-divider"></li>
                        <li><a class="dropdown-item log-out-link" href="">Logg ut</a></li>
                    </ul>';
            break;
        case '2':
            $menu = '<ul class="dropdown-menu" aria-labelledby="navbarDropdown">
                        <li><a class="dropdown-item endrepassord" href="">Endre passord</a></li>
                        <li><hr class="dropdown-divider"></li>
                        <li><a class="dropdown-item ajax-link" data-target="oversikt">Gå til oversikt over filer</a></li>
                        <li><a class="dropdown-item ajax-link" data-target="datainput">Legg til data</a></li>
                        <li><a class="dropdown-item ajax-link" data-target="datainput_edit">Rediger eksisterende data</a></li>
                        <li><hr class="dropdown-divider"></li>
                        <li><a class="dropdown-item log-out-link" href="">Logg ut</a></li>
                    </ul>';
            break;
        case '3':
            $menu = '<ul class="dropdown-menu" aria-labelledby="navbarDropdown">
                        <li><a class="dropdown-item endrepassord" href="">Endre passord</a></li>
                        <li><hr class="dropdown-divider"></li>
                        <li><a class="dropdown-item ajax-link" data-target="oversikt">Gå til oversikt over filer</a></li>
                        <li><a class="dropdown-item ajax-link" data-target="datainput">Legg til data</a></li>
                        <li><hr class="dropdown-divider"></li>
			<li><a class="dropdown-item ajax-link" data-target="referansesjekk">Referansesjekk</a></li>
			<li><hr class="dropdown-divider"></li>
                        <li><a class="dropdown-item log-out-link" href="">Logg ut</a></li>
                    </ul>';
            break;
        default:
            $menu = '<ul class="dropdown-menu" aria-labelledby="navbarDropdown">
                        <li><a class="dropdown-item" href="" id="LoginLink">Logg inn</a></li>
                        <li><hr class="dropdown-divider"></li>
                        <li><a class="dropdown-item ajax-link" data-target="oversikt">Gå til oversikt over filer</a></li>
			<li><a class="dropdown-item ajax-link" data-target="referansesjekk">Referansesjekk</a></li>
                    </ul>';
            break;
    }

echo $menu;

?>
