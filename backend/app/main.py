from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    clients,
    events,
    facts,
    health,
    operators,
    pending_forwards,
    profile,
    uploads,
    whatsapp_webhook,
)


def create_app() -> FastAPI:
    app = FastAPI(
        title="FollowRoom Backend",
        version="0.0.1",
        description="Phase 1 foundation API",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(operators.router)
    app.include_router(clients.router)
    app.include_router(events.router)
    app.include_router(facts.router)
    app.include_router(profile.router)
    app.include_router(uploads.router)
    app.include_router(whatsapp_webhook.router)
    app.include_router(pending_forwards.router)
    return app


app = create_app()
