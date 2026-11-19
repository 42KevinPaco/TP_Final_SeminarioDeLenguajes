// Geolocalización: toma la posición real del navegador y recarga la página
// con ?lat=&lon= para que el servidor ordene las sucursales por distancia.
document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-geolocalizar]').forEach(function (boton) {
        boton.addEventListener('click', function () {
            const aviso = document.getElementById('error-ubicacion');
            if (aviso) aviso.textContent = '';
            if (!navigator.geolocation) {
                if (aviso) aviso.textContent = 'Tu navegador no permite obtener la ubicación. Ingresala a mano.';
                return;
            }
            navigator.geolocation.getCurrentPosition(
                function (posicion) {
                    const destino = boton.dataset.destino || window.location.pathname;
                    const parametros = new URLSearchParams({
                        lat: posicion.coords.latitude.toFixed(6),
                        lon: posicion.coords.longitude.toFixed(6),
                    });
                    window.location.href = destino + '?' + parametros.toString();
                },
                function () {
                    if (aviso) aviso.textContent = 'No pudimos obtener tu ubicación. Revisá los permisos o ingresala a mano.';
                }
            );
        });
    });
});
