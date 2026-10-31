// Pago UI - Mostrar formulario de tarjeta condicionalmente
function mostrarFormularioTarjeta() {
    const metodoPago = document.getElementById('metodoPago').value;
    const formTarjeta = document.getElementById('form-tarjeta');
    
    if (metodoPago === 'debito' || metodoPago === 'credito') {
        formTarjeta.style.display = 'block';
    } else {
        formTarjeta.style.display = 'none';
    }
}
