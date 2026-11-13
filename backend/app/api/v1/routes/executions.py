"""Rotas de Execução de Ensaios e Gestão de Bancada (Fase 2 / M2.1)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response, status

from app.api.deps import CurrentUser, DbSession, require_roles
from app.core.context import RequestContext
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.test_execution import (
    TestExecutionComplete,
    TestExecutionInterrupt,
    TestExecutionOut,
    TestExecutionRecordData,
    TestExecutionStart,
)
from app.services import execution_service

test_executions_router = APIRouter(prefix="/tests/{test_id}/executions", tags=["Execução de Ensaios"])
executions_router = APIRouter(prefix="/executions", tags=["Execução de Ensaios"])

OPERATOR_ROLES = (UserRole.ADMIN, UserRole.TECNICO)


@test_executions_router.get(
    "",
    response_model=list[TestExecutionOut],
    summary="Listar histórico de execuções/tentativas de um ensaio",
)
async def list_executions(
    test_id: UUID,
    db: DbSession,
    _: CurrentUser,
) -> list[TestExecutionOut]:
    executions = await execution_service.list_executions_for_test(db, test_id)
    return [TestExecutionOut.model_validate(e) for e in executions]


@test_executions_router.post(
    "",
    response_model=TestExecutionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Iniciar nova tentativa de execução na bancada com validação metrológica",
)
async def start_execution(
    test_id: UUID,
    payload: TestExecutionStart,
    db: DbSession,
    request: Request,
    response: Response,
    actor: User = Depends(require_roles(*OPERATOR_ROLES)),
) -> TestExecutionOut:
    ctx = RequestContext.from_request(request)
    execution, audit_id = await execution_service.start_execution(
        db, test_id=test_id, payload=payload, actor=actor, context=ctx
    )
    out = TestExecutionOut.model_validate(execution)
    await db.commit()
    response.headers["X-Audit-Log-Id"] = str(audit_id)
    return out


@executions_router.get(
    "/{execution_id}",
    response_model=TestExecutionOut,
    summary="Consultar detalhes de uma execução específica",
)
async def get_execution(
    execution_id: UUID,
    db: DbSession,
    _: CurrentUser,
) -> TestExecutionOut:
    execution = await execution_service.get_execution(db, execution_id)
    return TestExecutionOut.model_validate(execution)


@executions_router.post(
    "/{execution_id}/readings",
    response_model=TestExecutionOut,
    summary="Registrar leituras intermediárias e condições de bancada durante a execução",
)
async def record_readings(
    execution_id: UUID,
    payload: TestExecutionRecordData,
    db: DbSession,
    request: Request,
    response: Response,
    actor: User = Depends(require_roles(*OPERATOR_ROLES)),
) -> TestExecutionOut:
    ctx = RequestContext.from_request(request)
    execution, audit_id = await execution_service.record_readings(
        db, execution_id=execution_id, payload=payload, actor=actor, context=ctx
    )
    out = TestExecutionOut.model_validate(execution)
    await db.commit()
    response.headers["X-Audit-Log-Id"] = str(audit_id)
    return out


@executions_router.post(
    "/{execution_id}/complete",
    response_model=TestExecutionOut,
    summary="Concluir execução na bancada e consolidar leituras brutas",
)
async def complete_execution(
    execution_id: UUID,
    payload: TestExecutionComplete,
    db: DbSession,
    request: Request,
    response: Response,
    actor: User = Depends(require_roles(*OPERATOR_ROLES)),
) -> TestExecutionOut:
    ctx = RequestContext.from_request(request)
    execution, audit_id = await execution_service.complete_execution(
        db, execution_id=execution_id, payload=payload, actor=actor, context=ctx
    )
    out = TestExecutionOut.model_validate(execution)
    await db.commit()
    response.headers["X-Audit-Log-Id"] = str(audit_id)
    return out


@executions_router.post(
    "/{execution_id}/interrupt",
    response_model=TestExecutionOut,
    summary="Interromper tentativa de ensaio preservando histórico (ALCOA+)",
)
async def interrupt_execution(
    execution_id: UUID,
    payload: TestExecutionInterrupt,
    db: DbSession,
    request: Request,
    response: Response,
    actor: User = Depends(require_roles(*OPERATOR_ROLES)),
) -> TestExecutionOut:
    ctx = RequestContext.from_request(request)
    execution, audit_id = await execution_service.interrupt_execution(
        db, execution_id=execution_id, payload=payload, actor=actor, context=ctx
    )
    out = TestExecutionOut.model_validate(execution)
    await db.commit()
    response.headers["X-Audit-Log-Id"] = str(audit_id)
    return out
