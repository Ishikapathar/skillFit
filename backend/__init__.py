"""Backend package initializer.

Exposes the FastAPI `app` object so you can run:

    uvicorn backend:app --reload

instead of specifying the module path.
"""

from .backends import app  # noqa: F401
