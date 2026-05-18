from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health


def create_app() -> FastAPI:
    app = FastAPI(
        title="FollowRoom Backend",
        version="0.0.1",
        description="Phase 1 foundation API",
    )

    # CORS — tightened in later tasks once we know the frontend origin
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    return app


app = create_app()
