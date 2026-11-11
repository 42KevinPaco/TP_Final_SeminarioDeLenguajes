"""Flask routes for the supermarket storefront.

Views stay thin: they validate request shape, call one service and render.
Guards rely on the server-side session, never on client-side state.
"""

import os
from functools import wraps

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)

from app.container import build_container
from app.models.pago import PagoCredito, PagoDebito, PagoEfectivo
from app.utils import imagenes, validators
from app.utils.config import IMAGENES_DIR, SECRET_KEY
from app.utils.exceptions import DatosInvalidosError, ErrorDeNegocio

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), 'ui'),
    static_folder=os.path.join(os.path.dirname(__file__), 'static'),
)
app.secret_key = SECRET_KEY

container = build_container()

ROL_ADMINISTRADOR = 'administrador'
ROL_CLIENTE = 'cliente'


# ---------------------------------------------------------------- guards
def requerir_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('id_usuario'):
            flash('Necesitás iniciar sesión para continuar', 'error')
            return redirect(url_for('login', next=request.path))
        if session.get('rol') != ROL_ADMINISTRADOR:
            flash('No tenés permisos para acceder a esa sección', 'error')
            return redirect(url_for('catalogo'))
        return f(*args, **kwargs)

    return decorated_function


def requerir_cliente(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('id_usuario'):
            flash('Necesitás iniciar sesión para continuar', 'error')
            return redirect(url_for('login', next=request.path))
        if session.get('rol') != ROL_CLIENTE:
            flash('El administrador no tiene acceso al área de clientes', 'error')
            return redirect(url_for('admin_usuarios'))
        return f(*args, **kwargs)

    return decorated_function


def requerir_cliente_api(f):
    """JSON variant of the customer guard: fetch() callers never get a redirect."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('id_usuario'):
            return jsonify({'ok': False, 'mensaje': 'Necesitás iniciar sesión para continuar'}), 401
        if session.get('rol') != ROL_CLIENTE:
            return jsonify({'ok': False, 'mensaje': 'El administrador no tiene carrito'}), 403
        return f(*args, **kwargs)

    return decorated_function


@app.context_processor
def inyectar_cantidad_carrito():
    """Expose the cart counter to every template (badge in header and catalog)."""
    cantidad = 0
    if session.get('id_usuario') and session.get('rol') == ROL_CLIENTE:
        cantidad = container.carrito_service.contar_unidades(session['id_usuario'])
    return {'cantidad_carrito': cantidad}


def _destino_por_rol() -> str:
    if session.get('rol') == ROL_ADMINISTRADOR:
        return url_for('admin_usuarios')
    return url_for('cliente_dashboard')


def _destino_seguro(valor: str | None) -> str | None:
    """Only accept local paths, never an absolute URL (open redirect guard)."""
    if not valor or not valor.startswith('/') or valor.startswith('//'):
        return None
    return valor


# ---------------------------------------------------------------- public
@app.route('/')
@app.route('/catalogo')
def catalogo():
    productos = container.catalogo_service.listar_disponibles()
    return render_template('pages/public/catalogo/catalogo.html', productos=productos)


@app.route('/productos')
def productos_publico():
    productos = container.catalogo_service.listar_disponibles()
    return render_template('pages/public/catalogo/catalogo.html', productos=productos)


# ---------------------------------------------------------------- auth
@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('id_usuario'):
        return redirect(_destino_por_rol())

    form_data = request.form if request.method == 'POST' else {}

    if request.method == 'POST':
        try:
            usuario = container.auth_service.autenticar(
                request.form.get('nombre_usuario', ''),
                request.form.get('contrasena', ''),
            )
        except ErrorDeNegocio as error:
            flash(str(error), 'error')
            return render_template('pages/auth/login/login.html', form_data=form_data), 401

        session.clear()
        session['id_usuario'] = usuario.id_usuario
        session['nombre_usuario'] = usuario.nombre_usuario
        session['nombre'] = usuario.nombre
        session['apellido'] = usuario.apellido
        session['rol'] = usuario.rol
        return redirect(_destino_seguro(request.args.get('next')) or _destino_por_rol())

    return render_template('pages/auth/login/login.html', form_data=form_data)


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if session.get('id_usuario'):
        return redirect(_destino_por_rol())

    form_data = request.form if request.method == 'POST' else {}

    if request.method == 'POST':
        try:
            container.auth_service.registrar_cliente(
                nombre_usuario=request.form.get('nombre_usuario', ''),
                contrasena=request.form.get('contrasena', ''),
                nombre=request.form.get('nombre', ''),
                apellido=request.form.get('apellido', ''),
                email=request.form.get('email', ''),
                domicilio=request.form.get('domicilio', ''),
                telefono=request.form.get('telefono', ''),
            )
        except ErrorDeNegocio as error:
            flash(str(error), 'error')
            return render_template('pages/auth/registro/registro.html', form_data=form_data), 400

        flash('Registro exitoso. Ya podés iniciar sesión.', 'success')
        return redirect(url_for('login'))

    return render_template('pages/auth/registro/registro.html', form_data=form_data)


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    flash('Cerraste sesión correctamente', 'info')
    return redirect(url_for('catalogo'))


# ---------------------------------------------------------------- cliente
@app.route('/cliente/dashboard')
@requerir_cliente
def cliente_dashboard():
    usuario = container.auth_service.obtener_usuario(session['id_usuario'])
    return render_template('pages/cliente/dashboard/dashboard.html', usuario=usuario)


@app.route('/cliente/carrito')
@requerir_cliente
def cliente_carrito():
    carrito = container.carrito_service.obtener_carrito(session['id_usuario'])
    return render_template('pages/cliente/carrito/carrito.html', carrito=carrito, items=carrito.items)


def _carrito_json(carrito) -> dict:
    return {
        'ok': True,
        'cantidad_total': carrito.cantidad_items,
        'total': carrito.calcular_total(),
        'items': [
            {
                'id_producto': item.producto.id_producto,
                'nombre': item.producto.nombre,
                'cantidad': item.cantidad,
                'precio_unitario': item.precio_unitario,
                'subtotal': item.subtotal,
            }
            for item in carrito.items
        ],
    }


def _datos_carrito():
    return request.get_json(silent=True) or request.form


@app.route('/carrito/agregar', methods=['POST'])
@requerir_cliente_api
def carrito_agregar():
    datos = _datos_carrito()
    try:
        id_producto = validators.validar_entero_positivo(datos.get('id_producto'), 'producto')
        carrito = container.carrito_service.agregar(
            session['id_usuario'],
            id_producto,
            datos.get('cantidad', 1),
        )
    except (ErrorDeNegocio, ValueError) as error:
        return jsonify({'ok': False, 'mensaje': str(error)}), 400
    return jsonify(_carrito_json(carrito))


@app.route('/carrito/actualizar', methods=['POST'])
@requerir_cliente_api
def carrito_actualizar():
    datos = _datos_carrito()
    try:
        id_producto = validators.validar_entero_positivo(datos.get('id_producto'), 'producto')
        carrito = container.carrito_service.actualizar_cantidad(
            session['id_usuario'],
            id_producto,
            datos.get('cantidad'),
        )
    except (ErrorDeNegocio, ValueError) as error:
        return jsonify({'ok': False, 'mensaje': str(error)}), 400
    return jsonify(_carrito_json(carrito))


@app.route('/carrito/eliminar', methods=['POST'])
@requerir_cliente_api
def carrito_eliminar():
    datos = _datos_carrito()
    try:
        id_producto = validators.validar_entero_positivo(datos.get('id_producto'), 'producto')
        carrito = container.carrito_service.eliminar(session['id_usuario'], id_producto)
    except (ErrorDeNegocio, ValueError) as error:
        return jsonify({'ok': False, 'mensaje': str(error)}), 400
    return jsonify(_carrito_json(carrito))


def _construir_pago(formulario, importe: float):
    """Build the polymorphic payment object the purchase service expects."""
    metodo = (formulario.get('metodoPago') or '').strip()
    if metodo == 'efectivo':
        return PagoEfectivo(
            id_pago=0,
            importe=importe,
            monto_recibido=validators.validar_numero_positivo(
                formulario.get('monto_recibido'), 'monto recibido'
            ),
        )
    if metodo in ('debito', 'credito'):
        datos_tarjeta = {
            'id_pago': 0,
            'importe': importe,
            'numero_tarjeta': formulario.get('numeroTarjeta', ''),
            'titular': formulario.get('titular', ''),
            'vencimiento': formulario.get('vencimiento', ''),
            'cvv': formulario.get('cvv', ''),
        }
        if metodo == 'debito':
            return PagoDebito(**datos_tarjeta)
        return PagoCredito(
            cuotas=validators.validar_entero_positivo(formulario.get('cuotas', 1), 'cuotas'),
            **datos_tarjeta,
        )
    raise DatosInvalidosError('Elegí un método de pago')


def _render_compra(sucursales, status: int = 200):
    borrador = container.compra_service.preparar(session['id_usuario'])
    detalles = borrador.detalles if borrador is not None else []
    total = borrador.total if borrador is not None else 0.0
    return (
        render_template(
            'pages/cliente/compra/compra.html',
            sucursales=sucursales,
            detalles=detalles,
            total=total,
            form_data=request.form,
        ),
        status,
    )


@app.route('/cliente/compra', methods=['GET', 'POST'])
@requerir_cliente
def cliente_compra():
    sucursales = container.sucursal_service.listar()

    if request.method == 'POST':
        try:
            borrador = container.compra_service.preparar(session['id_usuario'])
            if borrador is None:
                raise DatosInvalidosError('Tu carrito está vacío')
            id_sucursal = validators.validar_entero_positivo(request.form.get('sucursal'), 'sucursal')
            pago = _construir_pago(request.form, borrador.total)
            compra = container.compra_service.confirmar(session['id_usuario'], id_sucursal, pago)
        except (ErrorDeNegocio, ValueError) as error:
            flash(str(error), 'error')
            return _render_compra(sucursales, status=400)

        flash(f'Compra #{compra.id_compra} confirmada. Total: $ {compra.total:.2f}', 'success')
        return redirect(url_for('cliente_dashboard'))

    if container.compra_service.preparar(session['id_usuario']) is None:
        flash('Tu carrito está vacío', 'info')
        return redirect(url_for('cliente_carrito'))
    return _render_compra(sucursales)


@app.route('/cliente/sucursales-cercanas')
@requerir_cliente
def cliente_sucursales_cercanas():
    sucursales = container.sucursal_service.listar_por_cercania()
    return render_template(
        'pages/cliente/sucursales-cercanas/sucursales-cercanas.html',
        sucursales=sucursales,
    )


# ---------------------------------------------------------------- admin
@app.route('/admin/usuarios')
@requerir_admin
def admin_usuarios():
    usuarios = container.auth_service.listar_usuarios()
    return render_template('pages/admin/usuarios/usuarios.html', usuarios=usuarios)


@app.route('/admin/productos')
@requerir_admin
def admin_productos():
    productos = container.producto_service.listar()
    return render_template('pages/admin/productos/productos.html', productos=productos)


@app.route('/admin/sucursales')
@requerir_admin
def admin_sucursales():
    sucursales = container.sucursal_service.listar()
    productos_por_id = {p.id_producto: p for p in container.producto_service.listar()}
    sucursales_por_id = {s.id_sucursal: s for s in sucursales}
    filas_stock = [
        {
            'stock': stock,
            'producto': productos_por_id.get(stock.id_producto),
            'sucursal': sucursales_por_id.get(stock.id_sucursal),
        }
        for stock in container.stock_service.listar()
    ]
    return render_template(
        'pages/admin/sucursales/sucursales.html',
        sucursales=sucursales,
        filas_stock=filas_stock,
    )


# ------------------------------------------------------------ admin: producto
@app.route('/imagenes/<nombre>')
def imagen_producto(nombre):
    """Serve one uploaded product image (guards path traversal)."""
    return send_from_directory(IMAGENES_DIR, imagenes._nombre_seguro(nombre))


@app.route('/admin/productos/nuevo', methods=['GET', 'POST'])
@requerir_admin
def admin_producto_nuevo():
    if request.method == 'POST':
        try:
            producto = container.producto_service.crear(
                nombre=request.form.get('nombre', ''),
                descripcion=request.form.get('descripcion', ''),
                precio=request.form.get('precio', ''),
                marca=request.form.get('marca', ''),
                imagen=imagenes.guardar_imagen(request.files.get('imagen')),
            )
        except ErrorDeNegocio as error:
            flash(str(error), 'error')
            return (
                render_template(
                    'pages/admin/producto-form/producto-form.html',
                    producto=None,
                    form_data=request.form,
                ),
                400,
            )
        flash(f'Producto "{producto.nombre}" creado correctamente', 'success')
        return redirect(url_for('admin_productos'))
    return render_template(
        'pages/admin/producto-form/producto-form.html',
        producto=None,
        form_data={},
    )


@app.route('/admin/productos/<int:id_producto>/modificar', methods=['GET', 'POST'])
@requerir_admin
def admin_producto_modificar(id_producto):
    try:
        actual = container.producto_service.obtener(id_producto)
    except ErrorDeNegocio as error:
        flash(str(error), 'error')
        return redirect(url_for('admin_productos'))

    if request.method == 'POST':
        try:
            nueva_imagen = imagenes.guardar_imagen(request.files.get('imagen'))
            container.producto_service.actualizar(
                id_producto,
                nombre=request.form.get('nombre', ''),
                descripcion=request.form.get('descripcion', ''),
                precio=request.form.get('precio', ''),
                marca=request.form.get('marca', ''),
                imagen=nueva_imagen or None,
            )
        except ErrorDeNegocio as error:
            flash(str(error), 'error')
            return (
                render_template(
                    'pages/admin/producto-form/producto-form.html',
                    producto=actual,
                    form_data=request.form,
                ),
                400,
            )
        # Replace the old file only when a new image was actually uploaded.
        if nueva_imagen and actual.imagen and nueva_imagen != actual.imagen:
            imagenes.eliminar_imagen(actual.imagen)
        flash('Producto actualizado correctamente', 'success')
        return redirect(url_for('admin_productos'))

    return render_template(
        'pages/admin/producto-form/producto-form.html',
        producto=actual,
        form_data={},
    )


@app.route('/admin/productos/<int:id_producto>/eliminar', methods=['POST'])
@requerir_admin
def admin_producto_eliminar(id_producto):
    try:
        producto = container.producto_service.obtener(id_producto)
        container.producto_service.eliminar(id_producto)
        # Cascade: a product without stock rows never shows stale rows.
        container.stock_service.eliminar_de_producto(id_producto)
        imagenes.eliminar_imagen(producto.imagen)
    except ErrorDeNegocio as error:
        flash(str(error), 'error')
        return redirect(url_for('admin_productos'))
    flash('Producto eliminado correctamente', 'success')
    return redirect(url_for('admin_productos'))


# ------------------------------------------------------------ admin: sucursal
@app.route('/admin/sucursales/nueva', methods=['GET', 'POST'])
@requerir_admin
def admin_sucursal_nueva():
    if request.method == 'POST':
        try:
            sucursal = container.sucursal_service.crear(
                nombre=request.form.get('nombre', ''),
                direccion=request.form.get('direccion', ''),
                latitud=request.form.get('latitud', ''),
                longitud=request.form.get('longitud', ''),
            )
        except ErrorDeNegocio as error:
            flash(str(error), 'error')
            return (
                render_template(
                    'pages/admin/sucursal-form/sucursal-form.html',
                    sucursal=None,
                    form_data=request.form,
                ),
                400,
            )
        flash(f'Sucursal "{sucursal.nombre}" creada correctamente', 'success')
        return redirect(url_for('admin_sucursales'))
    return render_template(
        'pages/admin/sucursal-form/sucursal-form.html',
        sucursal=None,
        form_data={},
    )


@app.route('/admin/sucursales/<int:id_sucursal>/modificar', methods=['GET', 'POST'])
@requerir_admin
def admin_sucursal_modificar(id_sucursal):
    if request.method == 'POST':
        try:
            container.sucursal_service.actualizar(
                id_sucursal,
                nombre=request.form.get('nombre', ''),
                direccion=request.form.get('direccion', ''),
                latitud=request.form.get('latitud', ''),
                longitud=request.form.get('longitud', ''),
            )
        except ErrorDeNegocio as error:
            flash(str(error), 'error')
            return (
                render_template(
                    'pages/admin/sucursal-form/sucursal-form.html',
                    sucursal=container.sucursal_service.obtener(id_sucursal),
                    form_data=request.form,
                ),
                400,
            )
        flash('Sucursal actualizada correctamente', 'success')
        return redirect(url_for('admin_sucursales'))

    try:
        sucursal = container.sucursal_service.obtener(id_sucursal)
    except ErrorDeNegocio as error:
        flash(str(error), 'error')
        return redirect(url_for('admin_sucursales'))
    return render_template(
        'pages/admin/sucursal-form/sucursal-form.html',
        sucursal=sucursal,
        form_data={},
    )


@app.route('/admin/sucursales/<int:id_sucursal>/eliminar', methods=['POST'])
@requerir_admin
def admin_sucursal_eliminar(id_sucursal):
    try:
        container.sucursal_service.eliminar(id_sucursal)
        # Cascade: a branch without stock rows never shows stale rows.
        container.stock_service.eliminar_de_sucursal(id_sucursal)
    except ErrorDeNegocio as error:
        flash(str(error), 'error')
        return redirect(url_for('admin_sucursales'))
    flash('Sucursal eliminada correctamente', 'success')
    return redirect(url_for('admin_sucursales'))


# ------------------------------------------------------------ admin: stock
@app.route('/admin/stock/asignar', methods=['GET', 'POST'])
@requerir_admin
def admin_stock_asignar():
    if request.method == 'POST':
        try:
            id_producto = validators.validar_entero_positivo(
                request.form.get('id_producto'), 'producto'
            )
            id_sucursal = validators.validar_entero_positivo(
                request.form.get('id_sucursal'), 'sucursal'
            )
            container.stock_service.asignar(
                id_producto,
                id_sucursal,
                request.form.get('cantidad', ''),
            )
        except ErrorDeNegocio as error:
            flash(str(error), 'error')
            return _render_stock_form(status=400)
        flash('Stock asignado correctamente', 'success')
        return redirect(url_for('admin_sucursales'))
    return _render_stock_form()


def _render_stock_form(status: int = 200):
    return (
        render_template(
            'pages/admin/stock-form/stock-form.html',
            productos=container.producto_service.listar(),
            sucursales=container.sucursal_service.listar(),
            form_data=request.form,
        ),
        status,
    )


@app.route('/admin/stock/<int:id_stock>/actualizar', methods=['POST'])
@requerir_admin
def admin_stock_actualizar(id_stock):
    try:
        container.stock_service.actualizar_cantidad(id_stock, request.form.get('cantidad'))
    except ErrorDeNegocio as error:
        flash(str(error), 'error')
        return redirect(url_for('admin_sucursales'))
    flash('Stock actualizado correctamente', 'success')
    return redirect(url_for('admin_sucursales'))
