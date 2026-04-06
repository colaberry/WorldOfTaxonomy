"""Dependency injection for FastAPI routes.

Provides database connections from the pool stored in app.state.
"""

from fastapi import Request


async def get_conn(request: Request):
    """Yield a database connection from the app's pool."""
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        yield conn
