"""Rotas do Catálogo de Métodos de Ensaio (Fase 2 / M2.1)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response, status

from app.api.deps import CurrentUser, DbSession, require_roles
from app.core.context import RequestContext
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.test_method import (
    TestMethodCreate,
    TestMethodOut,
    TestMethodUpdate,
)
from app.services import method_service

router = APIRouter(prefix="/catalog/methods", tags=["Catálogo de Métodos"])

WRITE_ROLES = (UserRole.ADMIN, UserRole.FISCAL, UserRole.TECNICO)


@router.get(
    "",
    response_model=list[TestMethodOut],
    summary="Listar métodos de ensaio cadastrados no catálogo",
)
async def list_methods(
    db: DbSession,
    _: CurrentUser,
    category: str | None = Query(default=None, description="Filtrar por categoria técnica"),
    active_only: bool = Query(default=True, description="Exibir apenas métodos ativos"),
) -> list[TestMethodOut]:
    methods = await method_service.list_methods(db, category=category, active_only=active_only)
    return [TestMethodOut.model_validate(m) for m in methods]


@router.post(
    "",
    response_model=TestMethodOut,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar novo método no catálogo",
)
async def create_method(
    payload: TestMethodCreate,
    db: DbSession,
    request: Request,
    response: Response,
    actor: User = Depends(require_roles(*WRITE_ROLES)),
) -> TestMethodOut:
    ctx = RequestContext.from_request(request)
    method, audit_id = await method_service.create_method(
        db, payload=payload, actor=actor, context=ctx
    )
    await db.commit()
    response.headers["X-Audit-Log-Id"] = str(audit_id)
    return TestMethodOut.model_validate(method)


@router.post(
    "/seed-standards",
    response_model=list[TestMethodOut],
    summary="Inicializar catálogo com métodos normativos padrão da SEFI",
)
async def seed_standard_methods(
    db: DbSession,
    request: Request,
    actor: User = Depends(require_roles(UserRole.ADMIN)),
) -> list[TestMethodOut]:
    ctx = RequestContext.from_request(request)
    methods = await method_service.ensure_standard_methods(db, actor=actor, context=ctx)
    await db.commit()
    return [TestMethodOut.model_validate(m) for m in methods]


@router.get(
    "/{method_id}",
    response_model=TestMethodOut,
    summary="Consultar método por identificador",
)
async def get_method(
    method_id: UUID,
    db: DbSession,
    _: CurrentUser,
) -> TestMethodOut:
    method = await method_service.get_method(db, method_id)
    return TestMethodOut.model_validate(method)


@router.put(
    "/{method_id}",
    response_model=TestMethodOut,
    summary="Atualizar dados de um método no catálogo",
)
async def update_method(
    method_id: UUID,
    payload: TestMethodUpdate,
    db: DbSession,
    request: Request,
    response: Response,
    actor: User = Depends(require_roles(*WRITE_ROLES)),
) -> TestMethodOut:
    ctx = RequestContext.from_request(request)
    method, audit_id = await method_service.update_method(
        db, method_id=method_id, payload=payload, actor=actor, context=ctx
    )
    await db.commit()
    response.headers["X-Audit-Log-Id"] = str(audit_id)
    return TestMethodOut.model_validate(method)
