// Client-side cart helpers.
// Authentication is decided by the server session; this module only reads the
// flag rendered by the layout.
function agregarAlCarrito(idProducto) {
    if (!window.USUARIO_AUTENTICADO) {
        alert('Necesitás iniciar sesión para agregar al carrito');
        window.location.href = '/login';
        return;
    }

    // Cart persistence is not wired yet (pending cart service).
    window.location.href = '/cliente/carrito';
}
