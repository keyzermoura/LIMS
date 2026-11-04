"""Serviço de amostras: entrada, consulta, status e timeline."""

from __future__ import annotations

from datetime import UTC
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.errors import ConflictError, NotFoundError, ValidationDomainError
from app.db.dialect import next_sequence
from app.models.audit_log import AuditLog
from app.models.base import utcnow
from app.models.capa_action import CapaAction
from app.models.chain_of_custody import ChainOfCustody
from app.models.device_sample import DeviceSample
from app.models.electronic_signature import ElectronicSignature
from app.models.enums import (
    AuditAction,
    AuditEntity,
    SampleStatus,
    TestOutcome,
    TestStatus,
)
from app.models.lab_test import LabTest
from app.models.user import User
from app.schemas.sample import SampleCreate, SampleStatusUpdate
from app.services import audit_service, signature_service
from app.services.workflow import ensure_transition


async def create_sample(
    db: AsyncSession,
    *,
    payload: SampleCreate,
    actor: User,
    signature: ElectronicSignature,
    context: RequestContext,
) -> tuple[DeviceSample, int]:
    if await db.get(DeviceSample, payload.id) is not None:
        raise ConflictError("Já existe uma amostra com o identificador informado.")

    duplicate = await db.scalar(
        select(DeviceSample.id).where(
            DeviceSample.serial_number == payload.serial_number,
            DeviceSample.lot_number == payload.lot_number,
            DeviceSample.manufacturer == payload.manufacturer,
        )
    )
    if duplicate is not None:
        raise ConflictError(
            "Já existe uma amostra registrada para este fabricante/lote/número de série."
        )

    sequence = await next_sequence(db, "sample_accession_seq")
    accession = f"LIMS-{utcnow().year}-{int(sequence):06d}"

    received_at = payload.received_at or utcnow()
    if received_at.tzinfo is None:
        received_at = received_at.replace(tzinfo=UTC)

    sample = DeviceSample(
        id=payload.id,
        accession_number=accession,
        serial_number=payload.serial_number,
        lot_number=payload.lot_number,
        manufacturer=payload.manufacturer,
        commercial_name=payload.commercial_name,
        model=payload.model,
        registration_number=payload.registration_number,
        description=payload.description,
        status=SampleStatus.RECEBIDO,
        received_at=received_at,
        received_by_id=actor.id,
        received_by=actor,
        current_custodian_id=actor.id,
        current_custodian=actor,
        current_location=payload.storage_location,
        attributes=payload.attributes,
    )
    db.add(sample)
    await db.flush()

    receipt = ChainOfCustody(
        device_sample_id=sample.id,
        from_custodian_id=None,
        to_custodian_id=actor.id,
        to_custodian=actor,
        transferred_at=received_at,
        reason="Recebimento e entrada da amostra no LIMS.",
        location_to=payload.storage_location,
        signature_id=signature.id,
        notes=f"Accession {accession}",
    )
    db.add(receipt)
    await db.flush()

    await signature_service.bind_record(
        db,
        signature,
        {
            "sample": audit_service.snapshot(sample),
            "initial_custody": audit_service.snapshot(receipt),
        },
    )

    log = await audit_service.append(
        db,
        action=AuditAction.CREATE,
        entity_type=AuditEntity.DEVICE_SAMPLE.value,
        entity_id=sample.id,
        actor=actor,
        new_value=audit_service.snapshot(sample),
        reason="Registro de entrada de dispositivo médico recolhido no mercado.",
        context=context,
        signature_id=signature.id,
    )
    await db.commit()
    return sample, log.id


async def get_sample(db: AsyncSession, sample_id: UUID) -> DeviceSample:
    sample = await db.scalar(select(DeviceSample).where(DeviceSample.id == sample_id))
    if sample is None:
        raise NotFoundError("Amostra não encontrada.")
    return sample


async def list_samples(
    db: AsyncSession,
    *,
    page: int,
    size: int,
    status: SampleStatus | None = None,
    search: str | None = None,
) -> tuple[list[DeviceSample], int]:
    stmt = select(DeviceSample)
    if status is not None:
        stmt = stmt.where(DeviceSample.status == status)
    if search:
        term = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                DeviceSample.serial_number.ilike(term),
                DeviceSample.lot_number.ilike(term),
                DeviceSample.accession_number.ilike(term),
                DeviceSample.commercial_name.ilike(term),
                DeviceSample.manufacturer.ilike(term),
            )
        )

    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    stmt = (
        stmt.order_by(DeviceSample.received_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all()), int(total)


async def update_status(
    db: AsyncSession,
    *,
    sample_id: UUID,
    payload: SampleStatusUpdate,
    actor: User,
    signature: ElectronicSignature,
    context: RequestContext,
) -> tuple[DeviceSample, SampleStatus, int]:
    sample = await db.scalar(
        select(DeviceSample).where(DeviceSample.id == sample_id).with_for_update()
    )
    if sample is None:
        raise NotFoundError("Amostra não encontrada.")

    if sample.version != payload.version:
        raise ConflictError(
            "A amostra foi alterada por outro usuário. Recarregue antes de prosseguir.",
            details={"current_version": sample.version},
        )

    previous = sample.status
    ensure_transition(previous, payload.status)

    if payload.status == SampleStatus.APROVADO:
        rows = (
            await db.execute(
                select(LabTest.status, LabTest.outcome).where(
                    LabTest.device_sample_id == sample.id
                )
            )
        ).all()
        if not rows or not all(
            row.status == TestStatus.CONCLUIDO and row.outcome == TestOutcome.APROVADO
            for row in rows
        ):
            raise ValidationDomainError(
                "A amostra só pode ser aprovada quando todos os ensaios estiverem "
                "concluídos e aprovados.",
                details={"tests": len(rows)},
            )

    old_values = {"status": previous.value, "version": sample.version}
    sample.status = payload.status
    sample.version += 1
    sample.updated_at = utcnow()
    await db.flush()

    await signature_service.bind_record(
        db,
        signature,
        {
            "sample_id": str(sample.id),
            "accession_number": sample.accession_number,
            "from_status": previous.value,
            "to_status": payload.status.value,
            "reason": payload.reason,
        },
    )

    log = await audit_service.append(
        db,
        action=AuditAction.STATUS_CHANGE,
        entity_type=AuditEntity.DEVICE_SAMPLE.value,
        entity_id=sample.id,
        actor=actor,
        old_value=old_values,
        new_value={"status": payload.status.value, "version": sample.version},
        reason=payload.reason,
        context=context,
        signature_id=signature.id,
    )
    await db.commit()

    refreshed = await get_sample(db, sample_id)
    return refreshed, previous, log.id


async def timeline(db: AsyncSession, sample_id: UUID) -> list[dict[str, Any]]:
    sample = await get_sample(db, sample_id)
    events: list[dict[str, Any]] = []

    events.append(
        {
            "id": f"receipt-{sample.id}",
            "type": "RECEIPT",
            "occurred_at": sample.received_at,
            "title": "Entrada da amostra no LIMS",
            "description": (
                f"{sample.commercial_name} • lote {sample.lot_number} • "
                f"série {sample.serial_number}"
            ),
            "actor_name": sample.received_by.full_name if sample.received_by else None,
            "location": sample.current_location,
            "metadata": {
                "accession_number": sample.accession_number,
                "manufacturer": sample.manufacturer,
            },
        }
    )

    custody_rows = (
        await db.execute(
            select(ChainOfCustody)
            .where(ChainOfCustody.device_sample_id == sample_id)
            .order_by(ChainOfCustody.transferred_at.asc())
        )
    ).scalars()
    for event in custody_rows:
        events.append(
            {
                "id": str(event.id),
                "type": "CUSTODY",
                "occurred_at": event.transferred_at,
                "title": (
                    "Recebimento em custódia"
                    if event.from_custodian_id is None
                    else "Transferência de custódia"
                ),
                "description": event.reason,
                "actor_name": event.to_custodian.full_name
                if event.to_custodian
                else None,
                "location": event.location_to,
                "metadata": {
                    "from_custodian": event.from_custodian.full_name
                    if event.from_custodian
                    else None,
                    "to_custodian": event.to_custodian.full_name
                    if event.to_custodian
                    else None,
                    "seal_number": event.seal_number,
                    "signature_id": str(event.signature_id) if event.signature_id else None,
                },
            }
        )

    tests = list(
        (
            await db.execute(
                select(LabTest).where(LabTest.device_sample_id == sample_id)
            )
        ).scalars()
    )
    # A criação do ensaio é atribuída pelo evento de auditoria (fonte
    # autoritativa), pois `tested_by` passa a apontar para quem assinou o laudo.
    created_by: dict[str, str] = {}
    if tests:
        creation_logs = (
            await db.execute(
                select(AuditLog).where(
                    AuditLog.entity_type == AuditEntity.LAB_TEST.value,
                    AuditLog.action == AuditAction.CREATE,
                    AuditLog.entity_id.in_([str(test.id) for test in tests]),
                )
            )
        ).scalars()
        created_by = {log.entity_id: log.actor_username for log in creation_logs}
    for test in tests:
        events.append(
            {
                "id": f"test-created-{test.id}",
                "type": "TEST_CREATED",
                "occurred_at": test.created_at,
                "title": f"Ensaio programado: {test.name}",
                "description": test.acceptance_criteria,
                "actor_name": created_by.get(str(test.id)),
                "location": None,
                "metadata": {"test_id": str(test.id), "unit": test.unit},
            }
        )
        if test.signed_at is not None:
            events.append(
                {
                    "id": f"test-signed-{test.id}-{test.result_version}",
                    "type": "TEST_SIGNED",
                    "occurred_at": test.signed_at,
                    "title": f"Laudo assinado: {test.name}",
                    "description": (
                        f"Resultado {test.result_value} {test.unit} "
                        f"({test.outcome.value if test.outcome else 'sem desfecho'})"
                    ),
                    "actor_name": test.signed_by.full_name if test.signed_by else None,
                    "location": None,
                    "metadata": {
                        "test_id": str(test.id),
                        "outcome": test.outcome.value if test.outcome else None,
                        "signature_id": str(test.signature_id)
                        if test.signature_id
                        else None,
                    },
                }
            )

    capas = (
        await db.execute(
            select(CapaAction).where(CapaAction.device_sample_id == sample_id)
        )
    ).scalars()
    for capa in capas:
        events.append(
            {
                "id": f"capa-{capa.id}",
                "type": "CAPA_OPENED",
                "occurred_at": capa.opened_at,
                "title": f"CAPA aberta: {capa.code}",
                "description": capa.title,
                "actor_name": capa.owner.full_name if capa.owner else None,
                "location": None,
                "metadata": {
                    "capa_id": str(capa.id),
                    "status": capa.status.value,
                    "auto_opened": capa.auto_opened,
                },
            }
        )

    status_logs = (
        await db.execute(
            select(AuditLog)
            .where(
                AuditLog.entity_type == AuditEntity.DEVICE_SAMPLE.value,
                AuditLog.entity_id == str(sample_id),
                AuditLog.action == AuditAction.STATUS_CHANGE,
            )
            .order_by(AuditLog.sequence.asc())
        )
    ).scalars()
    for log in status_logs:
        new_value = log.new_value or {}
        events.append(
            {
                "id": f"audit-{log.sequence}",
                "type": "STATUS_CHANGE",
                "occurred_at": log.occurred_at,
                "title": f"Status alterado para {new_value.get('status', '—')}",
                "description": log.reason,
                "actor_name": log.actor_username,
                "location": None,
                "metadata": {
                    "audit_sequence": log.sequence,
                    "audit_hash": log.hash,
                },
            }
        )

    events.sort(key=lambda item: item["occurred_at"], reverse=True)
    return events


async def recompute_status(
    db: AsyncSession,
    *,
    sample: DeviceSample,
    actor: User,
    signature_id: UUID | None,
    context: RequestContext,
) -> tuple[SampleStatus, SampleStatus] | None:
    """Deriva o status da amostra a partir dos ensaios concluídos.

    Nunca sobrescreve amostra descartada. Retorna (anterior, novo) se mudou.
    """
    if sample.status == SampleStatus.DESCARTADO:
        return None

    rows = (
        await db.execute(
            select(LabTest.status, LabTest.outcome).where(
                LabTest.device_sample_id == sample.id
            )
        )
    ).all()

    # Um único ensaio reprovado reprova a amostra. A aprovação exige que
    # TODOS os ensaios estejam concluídos E aprovados: resultados
    # inconclusivos mantêm a amostra em teste (não podem aprovar por omissão).
    if any(row.outcome == TestOutcome.REPROVADO for row in rows):
        target = SampleStatus.REPROVADO
    elif rows and all(
        row.status == TestStatus.CONCLUIDO and row.outcome == TestOutcome.APROVADO
        for row in rows
    ):
        target = SampleStatus.APROVADO
    elif rows:
        target = SampleStatus.EM_TESTE
    else:
        return None

    if target == sample.status:
        return None

    previous = sample.status
    sample.status = target
    sample.updated_at = utcnow()
    sample.version += 1
    await db.flush()

    await audit_service.append(
        db,
        action=AuditAction.STATUS_CHANGE,
        entity_type=AuditEntity.DEVICE_SAMPLE.value,
        entity_id=sample.id,
        actor=actor,
        old_value={"status": previous.value},
        new_value={"status": target.value},
        reason="Transição automática derivada do resultado dos ensaios.",
        context=context,
        signature_id=signature_id,
    )
    return previous, target
