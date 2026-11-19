"""Runtime configuration.

The secret key is read from the environment (`SECRET_KEY`). Without it a random
key is generated on every start: the app still runs locally, but sessions do
not survive a restart and nothing predictable is ever committed.
"""

import os
import secrets
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("DATA_DIR", PROJECT_ROOT / "data"))

# Uploaded product images live as binary files next to the CSV store.
IMAGENES_DIR = Path(os.environ.get("IMAGENES_DIR", DATA_DIR / "imagenes"))

SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

# Initial password of the seeded administrator (only used when no user exists yet).
ADMIN_PASSWORD_INICIAL = os.environ.get("ADMIN_PASSWORD", "Admin1234")

# The Flask debugger executes arbitrary code: only on when explicitly requested.
DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"

# Default location used to sort branches by distance when the client has no
# stored coordinates (Buenos Aires downtown).
DEFAULT_LATITUD = float(os.environ.get("DEFAULT_LATITUD", -34.6037))
DEFAULT_LONGITUD = float(os.environ.get("DEFAULT_LONGITUD", -58.3816))
