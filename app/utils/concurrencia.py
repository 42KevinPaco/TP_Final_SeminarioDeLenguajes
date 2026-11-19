"""Process-wide lock for the CSV store.

Every CSV table is read, modified in memory and rewritten as a whole, so two
requests writing at once could overwrite each other. Writes (and the purchase
use case that spans several tables) run under this re-entrant lock.
The lock protects the threads of one server process, which is how Flask's
development server runs; a multi-process deployment needs a real database.
"""

import threading
from functools import wraps

LOCK_ALMACEN = threading.RLock()


def bajo_lock(funcion):
    """Run a repository write operation while holding the store lock."""

    @wraps(funcion)
    def envuelta(*args, **kwargs):
        with LOCK_ALMACEN:
            return funcion(*args, **kwargs)

    return envuelta
