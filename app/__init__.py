"""MotoShop Backend application package.

Exposes the FastAPI ``app`` instance so that WSGI servers (e.g.
``gunicorn app:app`` on Render) can import it directly from the package.
"""
from .main import app

__all__ = ["app"]

