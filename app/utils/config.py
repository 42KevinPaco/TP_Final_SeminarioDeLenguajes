"""Runtime configuration.

The secret key is read from the environment; the development fallback exists
only so the UI can run locally. No credential is ever committed.
"""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("DATA_DIR", PROJECT_ROOT / "data"))

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-secret-do-not-use-in-production")

# Default location used to sort branches by distance when the client has no
# stored coordinates (Buenos Aires downtown).
DEFAULT_LATITUD = float(os.environ.get("DEFAULT_LATITUD", -34.6037))
DEFAULT_LONGITUD = float(os.environ.get("DEFAULT_LONGITUD", -58.3816))
