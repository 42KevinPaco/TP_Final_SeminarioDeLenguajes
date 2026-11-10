// Pago UI - muestra solo los campos del método de pago elegido.
function mostrarFormularioTarjeta() {
    const selectMetodo = document.getElementById('metodoPago');
    if (!selectMetodo) return;

    const metodo = selectMetodo.value;
    const bloqueEfectivo = document.getElementById('form-efectivo');
    const bloqueTarjeta = document.getElementById('form-tarjeta');
    const bloqueCuotas = document.getElementById('form-cuotas');

    if (bloqueEfectivo) {
        bloqueEfectivo.style.display = metodo === 'efectivo' ? 'block' : 'none';
    }

    const esTarjeta = metodo === 'debito' || metodo === 'credito';
    if (bloqueTarjeta) {
        bloqueTarjeta.style.display = esTarjeta ? 'block' : 'none';
    }

    if (bloqueCuotas) {
        bloqueCuotas.style.display = metodo === 'credito' ? 'block' : 'none';
    }
}
