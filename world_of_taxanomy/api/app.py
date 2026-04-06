"""FastAPI application factory."""

from fastapi import FastAPI

from world_of_taxanomy.api.routers import systems, nodes, search, equivalences


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="WorldOfTaxanomy",
        description=(
            "Unified global industry classification knowledge graph. "
            "Federation model connecting NAICS, ISIC, NACE, and more."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Register routers
    app.include_router(systems.router)
    app.include_router(nodes.router)
    app.include_router(search.router)
    app.include_router(equivalences.router)

    @app.get("/", tags=["root"])
    async def root():
        return {
            "name": "WorldOfTaxanomy",
            "version": "0.1.0",
            "docs": "/docs",
            "api": "/api/v1",
        }

    return app
