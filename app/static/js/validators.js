// Validaciones de formularios - solo UI (sin lógica de negocio)
// Basado en los atributos del diagrama UML: Usuario, Cliente, Producto, Sucursal, ItemCarrito, Compra, Pago

// ---------- Utilidades ----------
function mostrarError(idCampo, mensaje) {
    const span = document.getElementById('error-' + idCampo);
    if (span) span.textContent = mensaje;
}

function limpiarError(idCampo) {
    const span = document.getElementById('error-' + idCampo);
    if (span) span.textContent = '';
}

function limpiarErrores(contenedor) {
    const scope = contenedor ? document.querySelector(contenedor) : document;
    scope.querySelectorAll('.error-message').forEach(function (el) {
        el.textContent = '';
    });
}

function esEnteroPositivo(valor) {
    const n = Number(valor);
    return Number.isInteger(n) && n >= 1;
}

function esNumeroPositivo(valor) {
    const n = Number(valor);
    return !isNaN(n) && n > 0;
}

function esEmailValido(valor) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(valor);
}

function esTelefonoValido(valor) {
    return /^[0-9]{10}$/.test(valor);
}

function esVencimientoValido(valor) {
    if (!/^(0[1-9]|1[0-2])\/[0-9]{2}$/.test(valor)) return false;
    const partes = valor.split('/');
    const mes = Number(partes[0]);
    const anio = 2000 + Number(partes[1]);
    const hoy = new Date();
    const vencimiento = new Date(anio, mes, 1);
    return vencimiento > hoy;
}

// ---------- Login (Usuario) ----------
function validarLogin() {
    let valido = true;
    limpiarErrores('#formLogin');

    const nombreUsuario = document.getElementById('nombreUsuario').value.trim();
    const contrasena = document.getElementById('contrasena').value.trim();

    if (nombreUsuario === '') {
        mostrarError('nombreUsuario', 'El nombre de usuario es requerido');
        valido = false;
    }
    if (contrasena === '') {
        mostrarError('contrasena', 'La contraseña es requerida');
        valido = false;
    } else if (contrasena.length < 4) {
        mostrarError('contrasena', 'La contraseña debe tener al menos 4 caracteres');
        valido = false;
    }
    return valido;
}

// ---------- Registro (Usuario + Cliente) ----------
function validarRegistro() {
    let valido = true;
    limpiarErrores('#formRegistro');

    const nombreUsuario = document.getElementById('nombreUsuario').value.trim();
    const contrasena = document.getElementById('contrasena').value.trim();
    const nombre = document.getElementById('nombre').value.trim();
    const apellido = document.getElementById('apellido').value.trim();
    const email = document.getElementById('email').value.trim();
    const domicilio = document.getElementById('domicilio').value.trim();
    const telefono = document.getElementById('telefono').value.trim();

    if (nombreUsuario === '') {
        mostrarError('nombreUsuario', 'El nombre de usuario es requerido');
        valido = false;
    }
    if (contrasena === '') {
        mostrarError('contrasena', 'La contraseña es requerida');
        valido = false;
    } else if (contrasena.length < 4) {
        mostrarError('contrasena', 'La contraseña debe tener al menos 4 caracteres');
        valido = false;
    }
    if (nombre === '') {
        mostrarError('nombre', 'El nombre es requerido');
        valido = false;
    }
    if (apellido === '') {
        mostrarError('apellido', 'El apellido es requerido');
        valido = false;
    }
    if (email === '') {
        mostrarError('email', 'El email es requerido');
        valido = false;
    } else if (!esEmailValido(email)) {
        mostrarError('email', 'Email inválido');
        valido = false;
    }
    if (domicilio === '') {
        mostrarError('domicilio', 'El domicilio es requerido');
        valido = false;
    }
    if (telefono === '') {
        mostrarError('telefono', 'El teléfono es requerido');
        valido = false;
    } else if (!esTelefonoValido(telefono)) {
        mostrarError('telefono', 'Teléfono inválido (10 dígitos)');
        valido = false;
    }
    return valido;
}

// ---------- Carrito (ItemCarrito) ----------
function validarCantidadCarrito(input) {
    if (!esEnteroPositivo(input.value)) {
        input.value = 1;
        alert('La cantidad debe ser un número entero mayor o igual a 1');
        return false;
    }
    return true;
}

function recalcularCarrito() {
    let total = 0;
    document.querySelectorAll('[data-item-carrito]').forEach(function (fila) {
        const precio = Number(fila.dataset.precio);
        const input = fila.querySelector('.input-cantidad');
        const cantidad = Number(input.value) || 0;
        const subtotal = precio * cantidad;
        const celdaSubtotal = fila.querySelector('[data-subtotal]');
        if (celdaSubtotal) {
            celdaSubtotal.textContent = '$ ' + subtotal.toFixed(2);
        }
        total += subtotal;
    });
    const totalGeneral = document.getElementById('total-carrito');
    if (totalGeneral) {
        totalGeneral.textContent = '$ ' + total.toFixed(2);
    }
}

// ---------- Compra (Compra + Pago) ----------
function validarCompra() {
    let valido = true;
    limpiarErrores('#formCompra');

    const sucursal = document.getElementById('sucursal');
    const metodoPago = document.getElementById('metodoPago');

    if (!sucursal.value) {
        mostrarError('sucursal', 'Debe seleccionar una sucursal');
        valido = false;
    }
    if (!metodoPago.value) {
        mostrarError('metodoPago', 'Debe seleccionar un método de pago');
        valido = false;
    }
    if (metodoPago.value === 'debito' || metodoPago.value === 'credito') {
        if (!validarTarjeta()) valido = false;
    }
    return valido;
}

// ---------- Pago con tarjeta (PagoDebito / PagoCredito) ----------
function validarTarjeta() {
    let valido = true;

    const numeroTarjeta = document.getElementById('numeroTarjeta').value.trim();
    const titular = document.getElementById('titular').value.trim();
    const vencimiento = document.getElementById('vencimiento').value.trim();
    const cvv = document.getElementById('cvv').value.trim();

    if (!/^[0-9]{16}$/.test(numeroTarjeta)) {
        mostrarError('numeroTarjeta', 'El número de tarjeta debe tener 16 dígitos');
        valido = false;
    }
    if (titular === '') {
        mostrarError('titular', 'El nombre del titular es requerido');
        valido = false;
    }
    if (vencimiento === '') {
        mostrarError('vencimiento', 'La fecha de vencimiento es requerida');
        valido = false;
    } else if (!esVencimientoValido(vencimiento)) {
        mostrarError('vencimiento', 'Formato MM/AA y fecha vigente');
        valido = false;
    }
    if (!/^[0-9]{3}$/.test(cvv)) {
        mostrarError('cvv', 'El CVV debe tener 3 dígitos');
        valido = false;
    }
    return valido;
}

// ---------- Administración (Producto / Sucursal / StockSucursal) ----------
function validarProducto() {
    let valido = true;
    limpiarErrores('#formProducto');

    const nombre = document.getElementById('nombre');
    const descripcion = document.getElementById('descripcion');
    const precio = document.getElementById('precio');
    const marca = document.getElementById('marca');

    if (!nombre || nombre.value.trim() === '') {
        mostrarError('nombre', 'El nombre del producto es requerido');
        valido = false;
    }
    if (!descripcion || descripcion.value.trim() === '') {
        mostrarError('descripcion', 'La descripción es requerida');
        valido = false;
    }
    if (!precio || !esNumeroPositivo(precio.value)) {
        mostrarError('precio', 'El precio debe ser un número mayor a 0');
        valido = false;
    }
    if (!marca || marca.value.trim() === '') {
        mostrarError('marca', 'La marca es requerida');
        valido = false;
    }
    return valido;
}

function validarSucursal() {
    let valido = true;
    limpiarErrores('#formSucursal');

    const nombre = document.getElementById('nombre');
    const direccion = document.getElementById('direccion');
    const latitud = document.getElementById('latitud');
    const longitud = document.getElementById('longitud');

    if (!nombre || nombre.value.trim() === '') {
        mostrarError('nombre', 'El nombre de la sucursal es requerido');
        valido = false;
    }
    if (!direccion || direccion.value.trim() === '') {
        mostrarError('direccion', 'La dirección es requerida');
        valido = false;
    }
    if (!latitud || isNaN(Number(latitud.value)) || latitud.value.trim() === '') {
        mostrarError('latitud', 'La latitud es requerida y debe ser numérica');
        valido = false;
    }
    if (!longitud || isNaN(Number(longitud.value)) || longitud.value.trim() === '') {
        mostrarError('longitud', 'La longitud es requerida y debe ser numérica');
        valido = false;
    }
    return valido;
}

function validarStock() {
    const cantidad = document.getElementById('cantidadDisponible');
    if (!cantidad || !esEnteroPositivo(cantidad.value)) {
        mostrarError('cantidadDisponible', 'La cantidad debe ser un entero mayor o igual a 1');
        return false;
    }
    return true;
}

// ---------- Inicialización ----------
document.addEventListener('DOMContentLoaded', function () {
    const inputsCantidad = document.querySelectorAll('.input-cantidad');
    inputsCantidad.forEach(function (input) {
        input.addEventListener('change', function () {
            if (validarCantidadCarrito(input)) recalcularCarrito();
        });
    });
    if (inputsCantidad.length > 0) recalcularCarrito();
});
