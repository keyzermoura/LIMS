"""Serviço de ensaios: criação, lançamento de resultado e CAPA automática."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.context import RequestContext
from app.core.errors import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationDomainError,
)
from app.db.dialect import next_sequence
from app.models.base import utcnow
from app.models.capa_action import CapaAction
from app.models.device_sample import DeviceSample
from app.models.electronic_signature import ElectronicSignature
from app.models.enums import (
    AuditAction,
    AuditEntity,
    CapaStatus,
    SampleStatus,
    TestOutcome,
    TestStatus,
    UserRole,
)
from app.models.lab_test import LabTest, LabTestResult
from app.models.user import User
from app.schemas.test import LabTestCreate, LabTestResultIn, TestAlert
from app.services import audit_service, sample_service, signature_service


async def create_test(
    db: AsyncSession,
    *,
    payload: LabTestCreate,
    actor: User,
    signature: ElectronicSignature,
    context: RequestContext,
) -> tuple[LabTest, int]:
    if await db.get(LabTest, payload.id) is not None:
        raise ConflictError("Já existe um ensaio com o identificador informado.")

    sample = await db.scalar(
        select(DeviceSample)
        .where(DeviceSample.id == payload.device_sample_id)
        .with_for_update()
    )
    if sample is None:
        raise NotFoundError("Amostra não encontrada.")
    if sample.status == SampleStatus.DESCARTADO:
        raise ConflictError("Não é possível programar ensaios para amostra descartada.")
    if sample.status == SampleStatus.APROVADO:
        # Reabrir uma decisão de conformidade exige ato assinado explícito:
        # sem isso, um novo ensaio pendente rebaixaria a amostra para EM_TESTE
        # silenciosamente, apagando a aprovação anterior.
        raise ConflictError(
            "Amostra aprovada: reabra o status para EM_TESTE (com assinatura "
            "eletrônica e justificativa) antes de programar um novo ensaio.",
            details={"status": sample.status.value},
        )

    # `tested_by` aqui significa "testador designado": é quem poderá assinar
    # o laudo. Só faz sentido quando o perfil tem competência para assinar
    # (TECNICO/ADMIN). Um FISCAL que apenas programa o ensaio sem escolher um
    # testador deve deixá-lo em aberto — caso contrário o laudo fica travado,
    # pois o fiscal não pode assiná-lo.
    assignee: User | None = None
    if payload.assigned_to_id is not None:
        candidate = await db.get(User, payload.assigned_to_id)
        if candidate is None or not candidate.is_active:
            raise NotFoundError("Testador designado não encontrado ou inativo.")
        if candidate.role not in (UserRole.TECNICO, UserRole.ADMIN):
            raise ValidationDomainError(
                "O testador designado deve ter perfil TECNICO ou ADMIN."
            )
        assignee = candidate
    elif actor.role in (UserRole.TECNICO, UserRole.ADMIN):
        assignee = actor

    test = LabTest(
        id=payload.id,
        device_sample_id=sample.id,
        name=payload.name.strip(),
        method=payload.method,
        parameters=payload.parameters,
        unit=payload.unit.strip(),
        lower_limit=payload.lower_limit,
        upper_limit=payload.upper_limit,
        acceptance_criteria=payload.acceptance_criteria,
        status=TestStatus.PENDENTE,
        assigned_to_id=assignee.id if assignee is not None else None,
        tested_by=assignee,
    )
    db.add(test)
    await db.flush()

    await sample_service.recompute_status(
        db,
        sample=sample,
        actor=actor,
        signature_id=None,
        context=context,
    )

    await signature_service.bind_record(
        db,
        signature,
        {
            "test": audit_service.snapshot(test),
            "sample_id": str(sample.id),
        },
    )

    log = await audit_service.append(
        db,
        action=AuditAction.CREATE,
        entity_type=AuditEntity.LAB_TEST.value,
        entity_id=test.id,
        actor=actor,
        new_value=audit_service.snapshot(test),
        reason=f"Programação de ensaio '{test.name}' para a amostra {sample.accession_number}.",
        context=context,
        signature_id=signature.id,
    )
    await db.commit()
    return test, log.id


async def record_result(
    db: AsyncSession,
    *,
    test_id: UUID,
    payload: LabTestResultIn,
    actor: User,
    signature: ElectronicSignature,
    context: RequestContext,
) -> tuple[LabTest, LabTestResult, CapaAction | None, TestAlert | None, int]:
    test = await db.scalar(
        select(LabTest).where(LabTest.id == test_id).with_for_update()
    )
    if test is None:
        raise NotFoundError("Ensaio não encontrado.")

    sample = await db.scalar(
        select(DeviceSample)
        .where(DeviceSample.id == test.device_sample_id)
        .with_for_update()
    )
    if sample is None:
        raise NotFoundError("Amostra do ensaio não encontrada.")
    if sample.status == SampleStatus.DESCARTADO:
        raise ConflictError("Amostra descartada: resultados não podem ser lançados.")

    if test.version != payload.version:
        raise ConflictError(
            "O ensaio foi alterado por outro usuário. Recarregue antes de prosseguir.",
            details={"current_version": test.version},
        )

    designated = test.tested_by
    designated_can_sign = designated is not None and designated.role in (
        UserRole.TECNICO,
        UserRole.ADMIN,
    )
    if (
        designated_can_sign
        and test.tested_by_id != actor.id
        and actor.role != UserRole.ADMIN
    ):
        raise ForbiddenError(
            "Apenas o testador responsável (ou administrador) pode assinar este laudo."
        )

    is_amendment = test.status == TestStatus.CONCLUIDO
    if is_amendment and not payload.amendment_reason:
        raise ConflictError(
            "Resultado já assinado é imutável. Para corrigir, informe "
            "'amendment_reason' — a correção gera nova versão auditada.",
            details={"current_result_version": test.result_version},
        )

    outcome = evaluate_outcome(
        result_value=payload.result_value,
        lower_limit=test.lower_limit,
        upper_limit=test.upper_limit,
        explicit=payload.outcome,
        result_text=payload.result_text,
    )

    old_values = audit_service.snapshot(test)
    now = utcnow()

    test.result_value = payload.result_value
    test.result_text = payload.result_text
    test.outcome = outcome
    test.notes = payload.notes
    test.status = TestStatus.CONCLUIDO
    test.tested_by_id = actor.id
    test.tested_by = actor
    test.tested_at = now
    test.signed_at = now
    test.signed_by_id = actor.id
    test.signed_by = actor
    test.signature_id = signature.id
    test.result_version += 1
    test.version += 1
    test.updated_at = now
    await db.flush()

    result_version = LabTestResult(
        lab_test_id=test.id,
        version=test.result_version,
        result_value=payload.result_value,
        result_text=payload.result_text,
        unit=test.unit,
        outcome=outcome,
        notes=payload.notes,
        is_amendment=is_amendment,
        amendment_reason=payload.amendment_reason,
        signed_by_id=actor.id,
        signed_by=actor,
        signed_at=now,
        signature_id=signature.id,
    )
    db.add(result_version)
    await db.flush()

    await signature_service.bind_record(
        db,
        signature,
        {
            "test": audit_service.snapshot(test),
            "result_version": audit_service.snapshot(result_version),
            "amendment": is_amendment,
            "amendment_reason": payload.amendment_reason,
        },
    )

    reason = payload.amendment_reason or (
        f"Lançamento e assinatura do resultado do ensaio '{test.name}'."
    )
    log = await audit_service.append(
        db,
        action=AuditAction.UPDATE,
        entity_type=AuditEntity.LAB_TEST.value,
        entity_id=test.id,
        actor=actor,
        old_value=old_values,
        new_value=audit_service.snapshot(test),
        reason=reason,
        context=context,
        signature_id=signature.id,
    )

    await sample_service.recompute_status(
        db,
        sample=sample,
        actor=actor,
        signature_id=None,
        context=context,
    )

    capa: CapaAction | None = None
    alert: TestAlert | None = None
    if outcome == TestOutcome.REPROVADO:
        capa, alert = await _handle_reproval(
            db,
            test=test,
            sample=sample,
            actor=actor,
            context=context,
            trigger_audit_id=log.id,
        )

    await db.commit()
    return test, result_version, capa, alert, log.id


def evaluate_outcome(
    *,
    result_value: Decimal | None,
    lower_limit: Decimal | None,
    upper_limit: Decimal | None,
    explicit: TestOutcome | None,
    result_text: str | None = None,
) -> TestOutcome:
    """Aplica o critério de aceitação de forma determinística.

    - Ensaios quantitativos (valor + limites) são avaliados pelo sistema.
    - Ensaios qualitativos podem declarar o desfecho, mas TODO desfecho —
      inclusive APROVADO — exige evidência registrada (valor ou texto);
      um laudo vazio não pode ser assinado.
    - Um valor fora dos limites NUNCA pode ser assinado como APROVADO,
      mesmo que o usuário declare o desfecho explicitamente.
    """
    numeric = _evaluate_numeric(result_value, lower_limit, upper_limit)
    evidence = result_text.strip() if result_text else ""

    if explicit is not None:
        if result_value is None and not evidence:
            raise ValidationDomainError(
                "Informe o resultado observado (valor ou texto) para "
                "sustentar o desfecho."
            )
        if (
            numeric == TestOutcome.REPROVADO
            and explicit == TestOutcome.APROVADO
        ):
            raise ValidationDomainError(
                "Resultado fora dos limites de aceitação não pode ser aprovado.",
                details={
                    "result_value": format(result_value, "f")
                    if result_value is not None
                    else None,
                    "lower_limit": format(lower_limit, "f")
                    if lower_limit is not None
                    else None,
                    "upper_limit": format(upper_limit, "f")
                    if upper_limit is not None
                    else None,
                },
            )
        return explicit

    if result_value is None:
        raise ValidationDomainError(
            "Informe o valor numérico do resultado ou declare o desfecho explicitamente."
        )
    if lower_limit is None and upper_limit is None:
        raise ValidationDomainError(
            "O ensaio não possui limites de tolerância; declare o desfecho explicitamente."
        )
    return numeric or TestOutcome.APROVADO


def _evaluate_numeric(
    result_value: Decimal | None,
    lower_limit: Decimal | None,
    upper_limit: Decimal | None,
) -> TestOutcome | None:
    """Retorna o desfecho calculado ou None quando não há base numérica."""
    if result_value is None or (lower_limit is None and upper_limit is None):
        return None
    if lower_limit is not None and result_value < lower_limit:
        return TestOutcome.REPROVADO
    if upper_limit is not None and result_value > upper_limit:
        return TestOutcome.REPROVADO
    return TestOutcome.APROVADO


async def _handle_reproval(
    db: AsyncSession,
    *,
    test: LabTest,
    sample: DeviceSample,
    actor: User,
    context: RequestContext,
    trigger_audit_id: int,
) -> tuple[CapaAction | None, TestAlert]:
    existing = await db.scalar(
        select(CapaAction).where(
            CapaAction.lab_test_id == test.id,
            CapaAction.status.in_([CapaStatus.ABERTA, CapaStatus.EM_ANDAMENTO]),
        )
    )
    if existing is not None:
        return existing, TestAlert(
            code="RESULTADO_REPROVADO",
            severity="CRITICAL",
            message=(
                f"Resultado reprovado. Já existe CAPA em aberto ({existing.code}) "
                "para este ensaio."
            ),
            capa_id=existing.id,
            capa_code=existing.code,
            capa_required=True,
        )

    if not settings.AUTO_OPEN_CAPA_ON_FAILURE:
        return None, TestAlert(
            code="RESULTADO_REPROVADO",
            severity="CRITICAL",
            message=(
                "Resultado reprovado. Abertura de CAPA é obrigatória e deve ser "
                "registrada manualmente."
            ),
            capa_required=True,
        )

    sequence = await next_sequence(db, "capa_code_seq")
    code = f"CAPA-{utcnow().year}-{int(sequence):06d}"

    owner = actor
    capa = CapaAction(
        code=code,
        device_sample_id=sample.id,
        lab_test_id=test.id,
        title=f"Desvio de conformidade — {test.name} reprovado",
        root_cause=(
            "Causa raiz a investigar. O ensaio apresentou resultado fora do "
            "limite de tolerância definido no protocolo."
        ),
        action_plan=(
            "1) Isolar o lote e revisar a cadeia de custódia; "
            "2) Analisar causas (produto, transporte, armazenamento); "
            "3) Definir ação corretiva e verificar eficácia em 30 dias."
        ),
        owner_id=owner.id,
        owner=owner,
        status=CapaStatus.ABERTA,
        due_date=date.today() + timedelta(days=30),
        auto_opened=True,
        created_by_id=actor.id,
        # Vincula a CAPA à assinatura do laudo que a motivou.
        signature_id=test.signature_id,
    )
    db.add(capa)
    await db.flush()

    await audit_service.append(
        db,
        action=AuditAction.CAPA_AUTO_OPEN,
        entity_type=AuditEntity.CAPA_ACTION.value,
        entity_id=capa.id,
        actor=actor,
        new_value={
            **audit_service.snapshot(capa),
            "trigger": {
                "lab_test_id": str(test.id),
                "result_version": test.result_version,
                "audit_log_id": trigger_audit_id,
                "signature_id": str(test.signature_id) if test.signature_id else None,
            },
        },
        reason=(
            f"Abertura automática de CAPA após resultado reprovado no ensaio "
            f"'{test.name}' da amostra {sample.accession_number}."
        ),
        context=context,
        signature_id=None,
    )

    return capa, TestAlert(
        code="RESULTADO_REPROVADO",
        severity="CRITICAL",
        message=(
            f"Resultado reprovado. CAPA {code} aberta automaticamente e "
            f"atribuída a {owner.full_name}."
        ),
        capa_id=capa.id,
        capa_code=capa.code,
        capa_required=True,
    )


async def get_test(db: AsyncSession, test_id: UUID) -> LabTest:
    test = await db.scalar(select(LabTest).where(LabTest.id == test_id))
    if test is None:
        raise NotFoundError("Ensaio não encontrado.")
    return test


async def list_tests(
    db: AsyncSession,
    *,
    sample_id: UUID | None = None,
    status: TestStatus | None = None,
    page: int = 1,
    size: int = 50,
) -> tuple[list[LabTest], int]:
    stmt = select(LabTest)
    if sample_id is not None:
        stmt = stmt.where(LabTest.device_sample_id == sample_id)
    if status is not None:
        stmt = stmt.where(LabTest.status == status)

    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    stmt = (
        stmt.order_by(LabTest.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all()), int(total)


async def list_result_versions(
    db: AsyncSession, test_id: UUID
) -> list[LabTestResult]:
    await get_test(db, test_id)
    rows = await db.execute(
        select(LabTestResult)
        .where(LabTestResult.lab_test_id == test_id)
        .order_by(LabTestResult.version.asc())
    )
    return list(rows.scalars().all())
