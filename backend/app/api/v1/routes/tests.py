"""Rotas de ensaios laboratoriais e assinatura de laudos."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.deps import (
    CurrentUser,
    DbSession,
    SignatureToken,
    require_roles,
    require_signature,
)
from app.core.context import RequestContext
from app.models.electronic_signature import ElectronicSignature
from app.models.enums import SignatureAction, TestStatus, UserRole
from app.models.user import User
from app.schemas.common import Page
from app.schemas.test import (
    LabTestCreate,
    LabTestCreateResponse,
    LabTestOut,
    LabTestResultIn,
    LabTestResultOut,
    TestHistoryOut,
    TestResultResponse,
)
from app.services import signature_service, test_service

router = APIRouter(prefix="/tests", tags=["Ensaios e Assinatura de Laudos"])

CREATE_ROLES = (UserRole.ADMIN, UserRole.FISCAL, UserRole.TECNICO)
SIGN_ROLES = (UserRole.ADMIN, UserRole.TECNICO)


@router.post(
    "",
    response_model=LabTestCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Programar ensaio (assinado)",
    responses={
        409: {
            "description": (
                "Amostra descartada ou aprovada. Amostra aprovada exige "
                "reabertura assinada para EM_TESTE antes de um novo ensaio."
            )
        }
    },
)
async def create_test(
    payload: LabTestCreate,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    token: SignatureToken,
    _role: User = Depends(require_roles(*CREATE_ROLES)),
) -> LabTestCreateResponse:
    signature: ElectronicSignature = await signature_service.consume(
        db,
        token=token,
        user=user,
        entity_type="LabTest",
        entity_id=str(payload.id),
        action=SignatureAction.CREATE,
        context=RequestContext.from_request(request),
    )
    test, audit_id = await test_service.create_test(
        db,
        payload=payload,
        actor=user,
        signature=signature,
        context=RequestContext.from_request(request),
    )
    return LabTestCreateResponse(
        test=LabTestOut.model_validate(test),
        audit_log_id=audit_id,
        signature_id=signature.id,
    )


@router.get("", response_model=Page[LabTestOut], summary="Listar ensaios")
async def list_tests(
    db: DbSession,
    user: CurrentUser,
    sample_id: UUID | None = Query(None),
    test_status: TestStatus | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
) -> Page[LabTestOut]:
    items, total = await test_service.list_tests(
        db, sample_id=sample_id, status=test_status, page=page, size=size
    )
    return Page[LabTestOut].build(
        [LabTestOut.model_validate(item) for item in items], total, page, size
    )


@router.get("/{test_id}", response_model=LabTestOut, summary="Detalhar ensaio")
async def get_test(test_id: UUID, db: DbSession, user: CurrentUser) -> LabTestOut:
    test = await test_service.get_test(db, test_id)
    return LabTestOut.model_validate(test)


@router.get(
    "/{test_id}/history",
    response_model=TestHistoryOut,
    summary="Versões assinadas do resultado (imutáveis)",
)
async def test_history(
    test_id: UUID, db: DbSession, user: CurrentUser
) -> TestHistoryOut:
    versions = await test_service.list_result_versions(db, test_id)
    return TestHistoryOut(
        test_id=test_id,
        versions=[LabTestResultOut.model_validate(item) for item in versions],
    )


@router.patch(
    "/{test_id}/result",
    response_model=TestResultResponse,
    summary="Lançar resultado e assinar laudo (assinatura eletrônica)",
    description=(
        "Grava o resultado em versão imutável, consome a assinatura eletrônica "
        "e registra auditoria na mesma transação. Resultado reprovado dispara "
        "abertura automática de CAPA e retorna alerta crítico."
    ),
    responses={
        401: {"description": "Assinatura ausente, expirada ou já utilizada"},
        409: {"description": "Resultado já assinado (exige emenda)"},
    },
)
async def record_result(
    test_id: UUID,
    payload: LabTestResultIn,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    signature: ElectronicSignature = Depends(
        require_signature(
            entity_type="LabTest",
            action=SignatureAction.UPDATE,
            id_param="test_id",
        )
    ),
    _role: User = Depends(require_roles(*SIGN_ROLES)),
) -> TestResultResponse:
    test, result_version, capa, alert, audit_id = await test_service.record_result(
        db,
        test_id=test_id,
        payload=payload,
        actor=user,
        signature=signature,
        context=RequestContext.from_request(request),
    )
    return TestResultResponse(
        test=LabTestOut.model_validate(test),
        result_version=LabTestResultOut.model_validate(result_version),
        alert=alert,
        capa_id=capa.id if capa else None,
        audit_log_id=audit_id,
        signature_id=signature.id,
        signature_manifest_hash=signature.manifest_hash,
    )
