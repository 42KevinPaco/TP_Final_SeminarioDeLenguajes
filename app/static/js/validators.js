// Validaciones HTML5 + JS - Solo diseño
function validarLogin() {
    let valido = true;
    
    const nombreUsuario = document.getElementById('nombreUsuario').value.trim();
    const contrasena = document.getElementById('contrasena').value.trim();
    
    document.getElementById('error-nombreUsuario').textContent = '';
    document.getElementById('error-contrasena').textContent = '';
    
    if (nombreUsuario === '') {
        document.getElementById('error-nombreUsuario').textContent = 'El nombre de usuario es requerido';
        valido = false;
    }
    
    if (contrasena === '') {
        document.getElementById('error-contrasena').textContent = 'La contraseña es requerida';
        valido = false;
    }
    
    return valido;
}

function validarRegistro() {
    let valido = true;
    
    // Limpiar errores
    const errores = document.querySelectorAll('.error-message');
    errores.forEach(e => e.textContent = '');
    
    // Usuario
    const nombreUsuario = document.getElementById('nombreUsuario').value.trim();
    const contrasena = document.getElementById('contrasena').value.trim();
    const nombre = document.getElementById('nombre').value.trim();
    const apellido = document.getElementById('apellido').value.trim();
    const email = document.getElementById('email').value.trim();
    const domicilio = document.getElementById('domicilio').value.trim();
    const telefono = document.getElementById('telefono').value.trim();
    
    if (nombreUsuario === '') {
        document.getElementById('error-nombreUsuario').textContent = 'El nombre de usuario es requerido';
        valido = false;
    }
    if (contrasena === '') {
        document.getElementById('error-contrasena').textContent = 'La contraseña es requerida';
        valido = false;
    }
    if (nombre === '') {
        document.getElementById('error-nombre').textContent = 'El nombre es requerido';
        valido = false;
    }
    if (apellido === '') {
        document.getElementById('error-apellido').textContent = 'El apellido es requerido';
        valido = false;
    }
    if (email === '') {
        document.getElementById('error-email').textContent = 'El email es requerido';
        valido = false;
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        document.getElementById('error-email').textContent = 'Email inválido';
        valido = false;
    }
    if (domicilio === '') {
        document.getElementById('error-domicilio').textContent = 'El domicilio es requerido';
        valido = false;
    }
    if (telefono === '') {
        document.getElementById('error-telefono').textContent = 'El teléfono es requerido';
        valido = false;
    } else if (!/^[0-9]{10}$/.test(telefono)) {
        document.getElementById('error-telefono').textContent = 'Teléfono inválido (10 dígitos)';
        valido = false;
    }
    
    return valido;
}
