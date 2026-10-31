from flask import Flask, render_template, session, redirect, url_for, request
from functools import wraps

import os
app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(__file__), 'ui'), 
            static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.secret_key = 'clave-simulada-solo-diseño'

def requerir_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def requerir_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario' not in session:
            return redirect(url_for('login'))
        if session.get('tipo_usuario') != 'admin':
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Rutas públicas
@app.route('/')
@app.route('/catalogo')
def catalogo():
    productos = [
        {'idProducto': 1, 'nombre': 'Leche Entera', 'descripcion': 'Leche entera pasteurizada 1L', 'precio': 150.00, 'marca': 'La Serenísima'},
        {'idProducto': 2, 'nombre': 'Pan Lactal', 'descripcion': 'Pan lactal blanco 500g', 'precio': 200.00, 'marca': 'Bimbo'},
        {'idProducto': 3, 'nombre': 'Arroz', 'descripcion': 'Arroz largo fino 1kg', 'precio': 120.00, 'marca': 'Gallo'}
    ]
    return render_template('pages/public/catalogo/catalogo.html', productos=productos)

@app.route('/productos')
def productos_publico():
    productos = [
        {'idProducto': 1, 'nombre': 'Leche Entera', 'descripcion': 'Leche entera pasteurizada 1L', 'precio': 150.00, 'marca': 'La Serenísima'},
        {'idProducto': 2, 'nombre': 'Pan Lactal', 'descripcion': 'Pan lactal blanco 500g', 'precio': 200.00, 'marca': 'Bimbo'},
        {'idProducto': 3, 'nombre': 'Arroz', 'descripcion': 'Arroz largo fino 1kg', 'precio': 120.00, 'marca': 'Gallo'}
    ]
    return render_template('pages/public/catalogo/catalogo.html', productos=productos)

# Autenticación
@app.route('/login')
def login():
    return render_template('pages/auth/login/login.html')

@app.route('/registro')
def registro():
    return render_template('pages/auth/registro/registro.html')

# Cliente - Requiere login
@app.route('/cliente/dashboard')

def cliente_dashboard():
    return render_template('pages/cliente/dashboard/dashboard.html')

@app.route('/cliente/carrito')

def cliente_carrito():
    return render_template('pages/cliente/carrito/carrito.html')

@app.route('/cliente/compra')

def cliente_compra():
    return render_template('pages/cliente/compra/compra.html')

@app.route('/cliente/sucursales-cercanas')

def cliente_sucursales_cercanas():
    return render_template('pages/cliente/sucursales-cercanas/sucursales-cercanas.html')

# Admin - Requiere login y rol admin
@app.route('/admin/usuarios')

def admin_usuarios():
    return render_template('pages/admin/usuarios/usuarios.html')

@app.route('/admin/productos')

def admin_productos():
    return render_template('pages/admin/productos/productos.html')

@app.route('/admin/sucursales')

def admin_sucursales():
    return render_template('pages/admin/sucursales/sucursales.html')

