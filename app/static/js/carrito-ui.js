// Client-side cart helpers.
// Authentication is decided by the server session; this module only reads the
// flag rendered by the layout. The cart itself lives in the CSV store, so a
// page refresh never empties it: only a confirmed purchase does.
function agregarAlCarrito(idProducto) {
    if (!window.USUARIO_AUTENTICADO) {
        alert('Necesitás iniciar sesión para agregar al carrito');
        window.location.href = '/login';
        return;
    }

    const inputCantidad = document.getElementById('cantidad-' + idProducto);
    const cantidad = inputCantidad ? Number(inputCantidad.value) : 1;

    enviarCarrito(
        '/carrito/agregar',
        { id_producto: idProducto, cantidad: cantidad },
        function (datos) {
            actualizarContadores(datos.cantidad_total);
            if (inputCantidad) inputCantidad.value = 1;
        }
    );
}

function actualizarCantidad(idProducto, cantidad) {
    enviarCarrito(
        '/carrito/actualizar',
        { id_producto: idProducto, cantidad: cantidad },
        function (datos) {
            actualizarContadores(datos.cantidad_total);
            actualizarFila(idProducto, datos);
            actualizarTotalCarrito(datos.total);
        },
        function () {
            window.location.reload();
        }
    );
}

function eliminarDelCarrito(idProducto) {
    enviarCarrito(
        '/carrito/eliminar',
        { id_producto: idProducto },
        function (datos) {
            actualizarContadores(datos.cantidad_total);
            actualizarTotalCarrito(datos.total);
            const fila = buscarFila(idProducto);
            if (fila) fila.remove();
            if ((datos.items || []).length === 0) {
                window.location.reload();
            }
        }
    );
}

function enviarCarrito(url, cuerpo, alExito, alError) {
    fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(cuerpo),
    })
        .then(function (respuesta) {
            return respuesta.json().then(function (datos) {
                return { ok: respuesta.ok, datos: datos };
            });
        })
        .then(function (resultado) {
            if (!resultado.datos || resultado.datos.ok !== true) {
                const mensaje = (resultado.datos && resultado.datos.mensaje)
                    || 'No se pudo actualizar el carrito';
                alert(mensaje);
                if (alError) alError(resultado.datos);
                return;
            }
            alExito(resultado.datos);
        })
        .catch(function () {
            alert('No se pudo conectar con el servidor');
            if (alError) alError(null);
        });
}

function actualizarContadores(cantidad) {
    document.querySelectorAll('.js-carrito-contador').forEach(function (nodo) {
        nodo.textContent = String(cantidad);
        nodo.dataset.cantidad = String(cantidad);
    });
}

function actualizarTotalCarrito(total) {
    const nodo = document.getElementById('total-carrito');
    if (nodo) nodo.textContent = formatearPrecio(total);
}

function buscarFila(idProducto) {
    return document.querySelector(
        '[data-item-carrito][data-id-producto="' + idProducto + '"]'
    );
}

function actualizarFila(idProducto, datos) {
    const fila = buscarFila(idProducto);
    if (!fila) return;
    const item = (datos.items || []).find(function (linea) {
        return linea.id_producto === idProducto;
    });
    if (!item) return;
    const celdaSubtotal = fila.querySelector('[data-subtotal]');
    if (celdaSubtotal) celdaSubtotal.textContent = formatearPrecio(item.subtotal);
}

function formatearPrecio(valor) {
    return '$ ' + Number(valor).toFixed(2);
}
