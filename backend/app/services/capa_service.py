"""Serviço de CAPA (Ação Corretiva / Preventiva)."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.errors import ConflictError, ForbiddenError, NotFoundError, ValidationDomainError
from app.db.dialect import next_sequence
from app.models.base import utcnow
from app.models.capa_action import CapaAction
from app.models.device_sample import DeviceSample
from app.models.electronic_signature import ElectronicSignature
from app.models.enums import AuditAction, AuditEntity, CapaStatus, UserRole
from app.models.lab_test import LabTest
from app.models.user import User
from app.schemas.capa import CapaCreate, CapaUpdate
from app.services import audit_service, signature_service

FINAL_STATUSES = {CapaStatus.CONCLUIDA, CapaStatus.CANCELADA}
EDITOR_ROLES = {UserRole.ADMIN, UserRole.FISCAL}
# O responsável precisa conseguir editar a própria CAPA (rota exige WRITE_ROLES).
OWNER_ROLES = {UserRole.ADMIN, UserRole.FISCAL, UserRole.TECNICO}


async def create_capa(
    db: AsyncSession,
    *,
    payload: CapaCreate,
    actor: User,
    signature: ElectronicSignature,
    context: RequestContext,
) -> tuple[CapaAction, int]:
    if (
        payload.device_sample_id is not None
        and await db.get(DeviceSample, payload.device_sample_id) is None
    ):
        raise NotFoundError("Amostra de origem não encontrada.")

    if payload.lab_test_id is not None:
        lab_test = await db.get(LabTest, payload.lab_test_id)
        if lab_test is None:
            raise NotFoundError("Ensaio de origem não encontrado.")
        if (
            payload.device_sample_id is not None
            and lab_test.device_sample_id != payload.device_sample_id
        ):
            raise ValidationDomainError(
                "O ensaio informado não pertence à amostra de origem da CAPA."
            )

    owner = await db.get(User, payload.owner_id)
    if owner is None or not owner.is_active:
        raise NotFoundError("Responsável pela CAPA não encontrado ou inativo.")
    if owner.role not in OWNER_ROLES:
        raise ValidationDomainError(
            f"O perfil {owner.role.value} não pode ser responsável por uma CAPA."
        )

    if payload.due_date <= date.today():
        raise ValidationDomainError("O prazo da CAPA deve ser uma data futura.")

    if await db.get(CapaAction, payload.id) is not None:
        raise ConflictError("Já existe uma CAPA com o identificador informado.")

    sequence = await next_sequence(db, "capa_code_seq")
    capa = CapaAction(
        id=payload.id,
        code=f"CAPA-{utcnow().year}-{int(sequence):06d}",
        device_sample_id=payload.device_sample_id,
        lab_test_id=payload.lab_test_id,
        title=payload.title.strip(),
        root_cause=payload.root_cause.strip(),
        action_plan=payload.action_plan.strip(),
        owner_id=owner.id,
        owner=owner,
        status=CapaStatus.ABERTA,
        due_date=payload.due_date,
        auto_opened=False,
        created_by_id=actor.id,
        signature_id=signature.id,
    )
    db.add(capa)
    await db.flush()

    await signature_service.bind_record(
        db, signature, {"capa": audit_service.snapshot(capa)}
    )

    log = await audit_service.append(
        db,
        action=AuditAction.CREATE,
        entity_type=AuditEntity.CAPA_ACTION.value,
        entity_id=capa.id,
        actor=actor,
        new_value=audit_service.snapshot(capa),
        reason="Abertura manual de CAPA.",
        context=context,
        signature_id=signature.id,
    )
    await db.commit()

    refreshed = await db.scalar(select(CapaAction).where(CapaAction.id == capa.id))
    assert refreshed is not None
    return refreshed, log.id


async def update_capa(
    db: AsyncSession,
    *,
    capa_id: UUID,
    payload: CapaUpdate,
    actor: User,
    signature: ElectronicSignature,
    context: RequestContext,
) -> tuple[CapaAction, int]:
    capa = await db.scalar(
        select(CapaAction).where(CapaAction.id == capa_id).with_for_update()
    )
    if capa is None:
        raise NotFoundError("CAPA não encontrada.")

    if capa.version != payload.version:
        raise ConflictError(
            "A CAPA foi alterada por outro usuário. Recarregue antes de prosseguir.",
            details={"current_version": capa.version},
        )

    if capa.status in FINAL_STATUSES:
        raise ConflictError("CAPA concluída ou cancelada não pode ser editada.")

    if actor.role not in EDITOR_ROLES and capa.owner_id != actor.id:
        raise ForbiddenError("Somente o responsável pela CAPA (ou gestão) pode alterá-la.")

    old_values = audit_service.snapshot(capa)

    if payload.status == CapaStatus.CONCLUIDA:
        if not payload.effectiveness_check:
            raise ValidationDomainError(
                "Para concluir a CAPA, registre a verificação de eficácia."
            )
        capa.closed_at = utcnow()
        capa.closed_by_id = actor.id
    elif payload.status == CapaStatus.CANCELADA:
        capa.closed_at = utcnow()
        capa.closed_by_id = actor.id

    if payload.owner_id is not None:
        new_owner = await db.get(User, payload.owner_id)
        if new_owner is None or not new_owner.is_active:
            raise NotFoundError("Novo responsável não encontrado ou inativo.")
        if new_owner.role not in OWNER_ROLES:
            raise ValidationDomainError(
                f"O perfil {new_owner.role.value} não pode ser responsável por uma CAPA."
            )
        capa.owner_id = new_owner.id
        capa.owner = new_owner

    if (
        payload.due_date is not None
        and payload.due_date != capa.due_date
        and payload.due_date <= date.today()
    ):
        raise ValidationDomainError("O prazo da CAPA deve ser uma data futura.")

    capa.signature_id = signature.id

    changes = payload.model_dump(exclude_unset=True, exclude={"version"})
    for field, value in changes.items():
        if value is not None:
            setattr(capa, field, value)

    capa.version += 1
    capa.updated_at = utcnow()
    await db.flush()

    await signature_service.bind_record(
        db, signature, {"capa": audit_service.snapshot(capa), "changes": changes}
    )

    log = await audit_service.append(
        db,
        action=AuditAction.UPDATE,
        entity_type=AuditEntity.CAPA_ACTION.value,
        entity_id=capa.id,
        actor=actor,
        old_value=old_values,
        new_value=audit_service.snapshot(capa),
        reason="Atualização de CAPA.",
        context=context,
        signature_id=signature.id,
    )
    await db.commit()

    refreshed = await db.scalar(select(CapaAction).where(CapaAction.id == capa.id))
    assert refreshed is not None
    return refreshed, log.id


async def get_capa(db: AsyncSession, capa_id: UUID) -> CapaAction:
    capa = await db.scalar(select(CapaAction).where(CapaAction.id == capa_id))
    if capa is None:
        raise NotFoundError("CAPA não encontrada.")
    return capa


async def list_capas(
    db: AsyncSession,
    *,
    status: CapaStatus | None = None,
    sample_id: UUID | None = None,
    page: int = 1,
    size: int = 50,
) -> tuple[list[CapaAction], int]:
    stmt = select(CapaAction)
    if status is not None:
        stmt = stmt.where(CapaAction.status == status)
    if sample_id is not None:
        stmt = stmt.where(CapaAction.device_sample_id == sample_id)

    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    stmt = (
        stmt.order_by(CapaAction.opened_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all()), int(total)
