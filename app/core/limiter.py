"""Shared slowapi Limiter instance.

Kept in its own module (rather than defined in app/main.py) so both
app/main.py (which registers it on app.state and its exception handler) and
individual routers (which apply @limiter.limit(...) to specific routes) can
import it without a circular import.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
