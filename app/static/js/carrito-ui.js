// Carrito UI - Solo diseño
function agregarAlCarrito(idProducto) {
    const usuario = sessionStorage.getItem('usuario');
    
    if (!usuario) {
        alert('Necesitás iniciar sesión para agregar al carrito');
        window.location.href = '/login';
        return;
    }
    
    alert('Producto agregado al carrito (simulado)');
    // Contador visual simulado
}
