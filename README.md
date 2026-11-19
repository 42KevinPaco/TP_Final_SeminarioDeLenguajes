# TPFinal_SL — E-commerce de un supermercado

Trabajo final de Seminario de Lenguajes: front-end de una plataforma e-commerce de supermercado en Python (Flask), con persistencia en archivos CSV.

## Cómo ejecutarlo

```bash
python -m venv .venv
source .venv/bin/activate        # en Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py                   # http://127.0.0.1:8080
```

Tests (125 originales + 48 de regresión):

```bash
python -m unittest discover -s tests -t .
```

### Usuarios iniciales

| Rol | Usuario | Contraseña |
| --- | --- | --- |
| Administrador | `admin` | `Admin1234` (cambiala; se puede fijar con `ADMIN_PASSWORD` antes del primer arranque) |

Los clientes se registran desde `/registro`; el administrador también puede crearlos.

### Variables de entorno

| Variable | Para qué sirve | Por defecto |
| --- | --- | --- |
| `SECRET_KEY` | Firma de la sesión | aleatoria en cada arranque (las sesiones no sobreviven a un reinicio) |
| `FLASK_DEBUG` | `1` activa el depurador de Flask | apagado |
| `ADMIN_PASSWORD` | Clave del admin al sembrar datos | `Admin1234` |
| `DEFAULT_LATITUD` / `DEFAULT_LONGITUD` | Punto de referencia cuando el cliente no indicó su ubicación | Buenos Aires |
| `DATA_DIR` | Carpeta de los CSV | `data/` |

## Funcionalidades (según la consigna)

- **Login** con usuario y contraseña (hash scrypt), registro de clientes y perfil de administrador.
- **Consulta de productos**: el catálogo muestra todos los productos (también los agotados), con buscador y el stock total y por sucursal.
- **Sucursal más cercana**: el cliente comparte su ubicación (geolocalización del navegador o coordenadas a mano) y las sucursales se ordenan por distancia (Haversine). El checkout usa esa misma ubicación, muestra la distancia y deshabilita las sucursales que no pueden abastecer el carrito.
- **Compra** al contado (efectivo, con vuelto) o con tarjeta de débito/crédito (hasta 12 cuotas). La compra es todo o nada: el stock solo se descuenta si la compra se guarda. Historial en *Mis Compras*.
- **Administrador**: ABM completo de **usuarios**, **productos** (con imagen) y **sucursales**, y gestión del stock por sucursal.

## Arquitectura

```text
app/
├── models/       # Dominio: Usuario/Cliente/Administrador, Producto, Sucursal, Carrito, Compra, Pago (polimórfico)
├── repository/   # Interfaces + implementación CSV
├── services/     # Casos de uso (auth, catálogo, carrito, compra, stock, sucursales)
├── ui/           # Plantillas Jinja (componentes y páginas)
├── static/       # CSS y JS
├── utils/        # Config, validaciones, seguridad, geo, concurrencia
├── container.py  # Composición de dependencias
└── routes_frontend.py
data/             # CSV y carpeta de imágenes
tests/
```

## Decisiones y límites conocidos

- El carrito siempre cobra el **precio vigente** del producto.
- Seguridad: token CSRF en todos los POST (formularios y `fetch`), cierre de sesión solo por POST, depurador apagado por defecto.
- Los CSV se protegen con un lock dentro de un mismo proceso. Para varios procesos/servidores haría falta una base de datos real (el diseño con repositorios permite reemplazarlos sin tocar los servicios).
- Las tarjetas no se guardan: solo el método de pago de cada compra.
