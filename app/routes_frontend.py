"""Flask routes for the supermarket storefront.

Views stay thin: they validate request shape, call one service and render.
Guards rely on the server-side session, never on client-side state.
"""

import os
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, session, url_for

from app.container import build_container
from app.utils.config import SECRET_KEY
from app.utils.exceptions import ErrorDeNegocio

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
    productos = container.producto_service.listar()
    return render_template('pages/public/catalogo/catalogo.html', productos=productos)


@app.route('/productos')
def productos_publico():
    productos = container.producto_service.listar()
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
    # Cart persistence belongs to the pending cart service; the page renders
    # an empty state until then.
    return render_template('pages/cliente/carrito/carrito.html', items=[])


@app.route('/cliente/compra')
@requerir_cliente
def cliente_compra():
    sucursales = container.sucursal_service.listar()
    return render_template(
        'pages/cliente/compra/compra.html',
        sucursales=sucursales,
        detalles=[],
        total=0.0,
    )


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
