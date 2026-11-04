"""Ponto de entrada da API LIMS.

Execução local:
    uvicorn app.main:app --reload
Documentação:
    http://localhost:8000/docs
"""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.db.database import engine, healthcheck, init_db

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
)
logger = logging.getLogger("lims")

OPENAPI_DESCRIPTION = """
Sistema LIMS para **Fiscalização Pós-Mercado de Dispositivos Médicos**.

### Conformidade
* **21 CFR Part 11** — assinatura eletrônica em duas etapas, manifestos
  auditáveis, controle de acesso e trilha append-only.
* **Anvisa RDC 665/2022** — rastreabilidade, cadeia de custódia e retenção
  de registros.
* **ALCOA+** — atribuível, legível, contemporâneo, original, exato.

### Assinatura eletrônica
1. `POST /auth/sign` com senha + significado + motivo → token de uso único.
2. Requisição de negócio com header `X-Signature-Token`.

A trilha de auditoria é encadeada por SHA-256 + HMAC e protegida por
triggers no PostgreSQL (`UPDATE`, `DELETE` e `TRUNCATE` bloqueados).
"""

TAGS_METADATA = [
    {"name": "Autenticação e Assinatura", "description": "JWT, reautenticação e assinatura eletrônica."},
    {"name": "Amostras e Cadeia de Custódia", "description": "Entrada, QR Code, timeline e transferências."},
    {"name": "Ensaios e Assinatura de Laudos", "description": "Resultados imutáveis e CAPA automática."},
    {"name": "CAPA", "description": "Ações corretivas e preventivas."},
    {"name": "Trilha de Auditoria", "description": "Consulta e verificação de integridade."},
    {"name": "Usuários", "description": "Gestão de usuários e custodiantes."},
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Iniciando %s v%s (%s)", settings.PROJECT_NAME, settings.VERSION, settings.ENVIRONMENT
    )
    try:
        await init_db()
        logger.info("Schema e proteções de imutabilidade aplicados.")
    except Exception:
        # A API sobe mesmo com banco indisponível; /health reporta o estado.
        logger.exception("Falha ao inicializar o banco de dados.")
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=OPENAPI_DESCRIPTION,
    openapi_tags=TAGS_METADATA,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={"name": "Qualidade / Assuntos Regulatórios"},
    license_info={"name": "Uso interno — dados regulados"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Signature-Token", "X-Request-ID"],
    expose_headers=["X-Request-ID", "X-Process-Time"],
    max_age=600,
)

register_exception_handlers(app)


@app.middleware("http")
async def security_context(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or uuid4().hex
    request.state.request_id = request_id
    started = time.perf_counter()

    response = await call_next(request)

    elapsed_ms = (time.perf_counter() - started) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{elapsed_ms:.1f}ms"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    # Dados regulados não devem ser cacheados por proxies/navegador.
    response.headers["Cache-Control"] = "no-store"
    if settings.ENVIRONMENT == "prod":
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )

    logger.info(
        "%s %s -> %s (%.1fms) request_id=%s",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
        request_id,
    )
    return response


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["Operação"], summary="Liveness e readiness")
async def health() -> dict[str, object]:
    db_ok = await healthcheck()
    return {
        "status": "ok" if db_ok else "degraded",
        "database": "up" if db_ok else "down",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get(
    "/api/v1/meta",
    tags=["Operação"],
    summary="Parâmetros de conformidade expostos ao front-end",
)
async def metadata() -> dict[str, object]:
    return {
        "project": settings.PROJECT_NAME,
        "esignature_ttl_seconds": settings.ESIGNATURE_TTL_SECONDS,
        "session_idle_timeout_minutes": settings.SESSION_IDLE_TIMEOUT_MINUTES,
        "access_token_expire_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        "auto_open_capa_on_failure": settings.AUTO_OPEN_CAPA_ON_FAILURE,
        "password_min_length": settings.PASSWORD_MIN_LENGTH,
    }


app.include_router(api_router, prefix=settings.API_V1_PREFIX)


__all__ = ["app"]
