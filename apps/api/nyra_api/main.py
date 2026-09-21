"""Nyra Service Tool API application factory."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import __version__
from .config import settings
from .routers import audit, health, incidents, kb, meta, people, teams
from .services.state_machine import TransitionError

logging.basicConfig(level=settings().log_level, format="%(asctime)s %(levelname)s %(name)s :: %(message)s")

DESCRIPTION = """
Nyra Service Tool - open, AI-native ITSM / ITIL 4 service management platform (prototype, Alpha 0.1).

Day-1 surface: reference data, people + caller context, incidents (queue, create, transition, comment), knowledge
search and feedback, audit trail and notification proof-of-send. See docs/SCOPE.md for what is deliberately not built yet.
""".strip()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Nyra Service Tool API",
        version=__version__,
        description=DESCRIPTION,
        contact={"name": "Nyra Service Tool"},
        license_info={"name": "Apache-2.0 (pending)"},
        openapi_tags=[
            {"name": "system", "description": "health and readiness"},
            {"name": "reference data", "description": "tenant, taxonomy, teams, services, SLA policies, views"},
            {"name": "people", "description": "people, caller context bundle"},
            {"name": "teams", "description": "assignment groups and distribution lists"},
            {"name": "incidents", "description": "the incident golden path"},
            {"name": "knowledge", "description": "knowledge articles"},
            {"name": "audit & notifications", "description": "audit trail, templates, audiences, proof of send"},
        ],
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(TransitionError)
    async def transition_error_handler(_: Request, exc: TransitionError) -> JSONResponse:  # pragma: no cover
        return JSONResponse(status_code=422, content={"detail": str(exc), "missing": exc.missing})

    @app.get("/", include_in_schema=False)
    def root() -> dict:
        return {"service": "nyra-api", "version": __version__, "docs": "/docs", "health": "/health"}

    app.include_router(health.router)
    app.include_router(meta.router)
    app.include_router(people.router)
    app.include_router(teams.router)
    app.include_router(incidents.router)
    app.include_router(kb.router)
    app.include_router(audit.router)
    return app


app = create_app()
