"""Agregador da API v1."""

from fastapi import APIRouter

from app.api.v1.routes import audit, auth, capas, custody, samples, tests, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(samples.router)
api_router.include_router(custody.router)
api_router.include_router(tests.router)
api_router.include_router(capas.router)
api_router.include_router(audit.router)
api_router.include_router(users.router)

__all__ = ["api_router"]
