"""Transferência de custódia — evento assinado e imutável."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.errors import ConflictError, ForbiddenError, NotFoundError, ValidationDomainError
from app.models.base import utcnow
from app.models.chain_of_custody import ChainOfCustody
from app.models.device_sample import DeviceSample
from app.models.electronic_signature import ElectronicSignature
from app.models.enums import AuditAction, AuditEntity, SampleStatus, UserRole
from app.models.user import User
from app.schemas.sample import CustodyTransferRequest
from app.services import audit_service, signature_service

# Quem pode assumir a guarda física de uma amostra.
CUSTODIAN_ROLES = {
    UserRole.ADMIN,
    UserRole.FISCAL,
    UserRole.TECNICO,
    UserRole.CUSTODIANTE,
}


async def transfer(
    db: AsyncSession,
    *,
    payload: CustodyTransferRequest,
    actor: User,
    signature: ElectronicSignature,
    context: RequestContext,
) -> tuple[ChainOfCustody, DeviceSample, int]:
    sample = await db.scalar(
        select(DeviceSample)
        .where(DeviceSample.id == payload.device_sample_id)
        .with_for_update()
    )
    if sample is None:
        raise NotFoundError("Amostra não encontrada.")

    if sample.status == SampleStatus.DESCARTADO:
        raise ConflictError("Amostra descartada não pode ser transferida.")

    if sample.version != payload.version:
        raise ConflictError(
            "A amostra foi alterada por outro usuário. Recarregue antes de prosseguir.",
            details={"current_version": sample.version},
        )

    # Apenas o custodiante atual (ou administração/fiscalização) transfere.
    if (
        sample.current_custodian_id is not None
        and sample.current_custodian_id != actor.id
        and actor.role not in (UserRole.ADMIN, UserRole.FISCAL)
    ):
        raise ForbiddenError(
            "Somente o custodiante atual pode transferir a guarda da amostra."
        )

    target = await db.get(User, payload.to_custodian_id)
    if target is None or not target.is_active:
        raise NotFoundError("Custodiante de destino não encontrado ou inativo.")
    if target.role not in CUSTODIAN_ROLES:
        raise ValidationDomainError(
            f"O perfil {target.role.value} não pode assumir custódia de amostras."
        )
    if target.id == sample.current_custodian_id:
        raise ValidationDomainError("O destino da transferência é o custodiante atual.")

    previous_custodian_id = sample.current_custodian_id
    previous_location = sample.current_location
    previous_custodian = (
        await db.get(User, previous_custodian_id) if previous_custodian_id else None
    )

    now = utcnow()
    event = ChainOfCustody(
        device_sample_id=sample.id,
        from_custodian_id=previous_custodian_id,
        from_custodian=previous_custodian,
        to_custodian_id=target.id,
        to_custodian=target,
        transferred_at=now,
        reason=payload.reason,
        location_from=previous_location,
        location_to=payload.storage_location,
        seal_number=payload.seal_number,
        signature_id=signature.id,
        notes=payload.notes,
    )
    db.add(event)
    await db.flush()

    sample.current_custodian_id = target.id
    sample.current_custodian = target
    sample.current_location = payload.storage_location
    sample.version += 1
    sample.updated_at = now
    await db.flush()

    await signature_service.bind_record(
        db,
        signature,
        {
            "custody_event": audit_service.snapshot(event),
            "sample": {
                "id": str(sample.id),
                "accession_number": sample.accession_number,
                "location": sample.current_location,
            },
        },
    )

    log = await audit_service.append(
        db,
        action=AuditAction.TRANSFER,
        entity_type=AuditEntity.DEVICE_SAMPLE.value,
        entity_id=sample.id,
        actor=actor,
        old_value={
            "current_custodian_id": str(previous_custodian_id)
            if previous_custodian_id
            else None,
            "current_location": previous_location,
        },
        new_value={
            "current_custodian_id": str(target.id),
            "current_location": payload.storage_location,
            "seal_number": payload.seal_number,
        },
        reason=payload.reason,
        context=context,
        signature_id=signature.id,
    )
    await db.commit()

    refreshed = await db.scalar(
        select(DeviceSample).where(DeviceSample.id == sample.id)
    )
    assert refreshed is not None
    return event, refreshed, log.id


async def history(db: AsyncSession, sample_id: UUID) -> list[ChainOfCustody]:
    sample = await db.get(DeviceSample, sample_id)
    if sample is None:
        raise NotFoundError("Amostra não encontrada.")
    rows = await db.execute(
        select(ChainOfCustody)
        .where(ChainOfCustody.device_sample_id == sample_id)
        .order_by(ChainOfCustody.transferred_at.asc())
    )
    return list(rows.scalars().all())
