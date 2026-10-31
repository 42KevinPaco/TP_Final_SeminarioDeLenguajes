// Guardianes UI - Solo diseño
function actualizarNavbar() {
    const usuario = sessionStorage.getItem('usuario');
    const tipoUsuario = sessionStorage.getItem('tipo_usuario');
    
    // Ocultar elementos para invitados
    document.querySelectorAll('[data-guest-only]').forEach(el => {
        el.style.display = usuario ? 'none' : 'block';
    });
    
    // Mostrar elementos para autenticados
    document.querySelectorAll('[data-auth-only]').forEach(el => {
        el.style.display = usuario ? 'block' : 'none';
    });
    
    // Mostrar elementos solo para cliente
    document.querySelectorAll('[data-cliente-only]').forEach(el => {
        el.style.display = (usuario && tipoUsuario === 'cliente') ? 'block' : 'none';
    });
    
    // Mostrar elementos solo para admin
    document.querySelectorAll('[data-admin-only]').forEach(el => {
        el.style.display = (usuario && tipoUsuario === 'admin') ? 'block' : 'none';
    });
}

function cerrarSesionUI() {
    sessionStorage.removeItem('usuario');
    sessionStorage.removeItem('tipo_usuario');
    alert('Sesión cerrada (simulado)');
    window.location.href = '/login';
}

// Ejecutar al cargar la página
document.addEventListener('DOMContentLoaded', actualizarNavbar);
