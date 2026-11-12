"""Serviço de Recebimento, Conferência Física e Objetos de Custódia (Fase 1 / M1.1)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.context import RequestContext
from app.core.errors import ConflictError, NotFoundError, ValidationDomainError
from app.db.dialect import next_sequence
from app.models.base import utcnow
from app.models.chain_of_custody import ChainOfCustody
from app.models.device_sample import DeviceSample
from app.models.enums import (
    AuditAction,
    AuditEntity,
    ConferenceStatus,
    CustodyEventType,
    CustodyObjectStatus,
    PresentationStatus,
    ReceiptDecisionEnum,
    ReceiptStatus,
    SampleStatus,
    SolicitationStatus,
)
from app.models.receipt import CustodyEvent, CustodyObject, Receipt, ReceiptItem
from app.models.solicitation import Solicitation
from app.models.user import User
from app.schemas.receipt import (
    CustodyAcceptanceCreate,
    CustodyTransferCreate,
    ReceiptCreate,
    ReceiptItemConference,
)
from app.services import audit_service
from app.services.audit_service import snapshot
from app.services.workflow import (
    ensure_custody_object_transition,
)


async def create_receipt(
    db: AsyncSession,
    solicitation_id: UUID,
    *,
    payload: ReceiptCreate,
    actor: User,
    context: RequestContext | None = None,
) -> tuple[Receipt, int]:
    """Formaliza a chegada física de uma solicitação SUBMETIDA e gera os objetos de custódia iniciais."""
    solicitation = await db.get(Solicitation, solicitation_id)
    if solicitation is None:
        raise NotFoundError("Solicitação não encontrada.")

    existing_receipt = await db.scalar(
        select(Receipt.id).where(Receipt.solicitation_id == solicitation_id)
    )
    if existing_receipt is not None:
        raise ConflictError("Já existe um registro de recebimento para esta solicitação.")

    if solicitation.status != SolicitationStatus.SUBMETIDA:
        raise ValidationDomainError(
            f"O recebimento só pode ser criado para solicitações SUBMETIDAS. Status atual: {solicitation.status.value}"
        )

    sequence = await next_sequence(db, "receipt_number_seq")
    receipt_number = f"REC-{utcnow().year}-{int(sequence):05d}"
    arrived_at = payload.arrived_at or utcnow()

    receipt = Receipt(
        solicitation_id=solicitation_id,
        receipt_number=receipt_number,
        arrived_at=arrived_at,
        received_by_id=actor.id,
        arrival_location=payload.arrival_location,
        external_protocol=payload.external_protocol,
        delivery_method=payload.delivery_method,
        packaging_condition=payload.packaging_condition,
        notes=payload.notes,
        status=ReceiptStatus.REGISTRADO,
        version=1,
    )

    # Cria itens de recebimento para cada item declarado e os objetos de custódia iniciais
    for sol_item in solicitation.items:
        receipt_item = ReceiptItem(
            solicitation_item_id=sol_item.id,
            presentation_status=PresentationStatus.PRESENTED,
            presented_quantity=sol_item.declared_quantity,
            conference_status=ConferenceStatus.PENDENTE,
            version=1,
        )

        obj_sequence = await next_sequence(db, "custody_object_code_seq")
        object_code = f"OBJ-{utcnow().year}-{int(obj_sequence):05d}"

        custody_object = CustodyObject(
            object_code=object_code,
            grouping_description=f"Material recebido referente ao item {sol_item.item_number}: {sol_item.product_name}",
            represented_quantity=sol_item.declared_quantity,
            current_location=payload.arrival_location,
            status=CustodyObjectStatus.SOB_GUARDA,
            current_custodian_id=actor.id,
            version=1,
        )

        initial_event = CustodyEvent(
            event_type=CustodyEventType.INGRESSO,
            effective_at=arrived_at,
            to_custodian_id=actor.id,
            to_location=payload.arrival_location,
            reason="Ingresso físico no recebimento da solicitação",
            registered_by_id=actor.id,
        )
        custody_object.custody_events.append(initial_event)
        receipt_item.custody_objects.append(custody_object)
        receipt.items.append(receipt_item)

    # Atualiza status da solicitação
    old_sol_snapshot = snapshot(solicitation)
    solicitation.status = SolicitationStatus.RECEBIMENTO_REGISTRADO
    solicitation.version += 1
    new_sol_snapshot = snapshot(solicitation)
    new_receipt_snapshot = snapshot(receipt)

    db.add(receipt)
    await db.flush()

    # Trilha de auditoria
    await audit_service.append(
        db,
        action=AuditAction.STATUS_CHANGE,
        entity_type=AuditEntity.SOLICITATION.value,
        entity_id=solicitation.id,
        actor=actor,
        old_value=old_sol_snapshot,
        new_value=new_sol_snapshot,
        reason=f"Recebimento físico registrado ({receipt.receipt_number})",
        context=context,
    )

    audit_entry = await audit_service.append(
        db,
        action=AuditAction.CREATE,
        entity_type=AuditEntity.RECEIPT.value,
        entity_id=receipt.id,
        actor=actor,
        new_value=new_receipt_snapshot,
        reason="Registro de recebimento físico",
        context=context,
    )
    await db.commit()
    refreshed = await get_receipt(db, receipt.id)
    return refreshed, audit_entry.sequence


async def get_receipt(db: AsyncSession, receipt_id: UUID) -> Receipt:
    """Busca o recebimento pelo ID próprio ou levanta 404."""
    stmt = (
        select(Receipt)
        .options(
            selectinload(Receipt.items).selectinload(ReceiptItem.custody_objects),
            selectinload(Receipt.items).selectinload(ReceiptItem.solicitation_item),
            selectinload(Receipt.solicitation),
            selectinload(Receipt.received_by),
        )
        .where(Receipt.id == receipt_id)
    )
    receipt = await db.scalar(stmt)
    if receipt is None:
        raise NotFoundError("Recebimento não encontrado.")
    return receipt


async def get_receipt_by_solicitation(db: AsyncSession, solicitation_id: UUID) -> Receipt:
    """Busca o recebimento vinculado à solicitação ou levanta 404."""
    stmt = (
        select(Receipt)
        .options(
            selectinload(Receipt.items).selectinload(ReceiptItem.custody_objects),
            selectinload(Receipt.items).selectinload(ReceiptItem.solicitation_item),
            selectinload(Receipt.solicitation),
            selectinload(Receipt.received_by),
        )
        .where(Receipt.solicitation_id == solicitation_id)
    )
    receipt = await db.scalar(stmt)
    if receipt is None:
        raise NotFoundError("Recebimento para esta solicitação não encontrado.")
    return receipt


async def conference_item(
    db: AsyncSession,
    receipt_id: UUID,
    item_id: UUID,
    *,
    payload: ReceiptItemConference,
    actor: User,
    context: RequestContext | None = None,
) -> tuple[ReceiptItem, int]:
    """Registra conferência física de um item específico do recebimento."""
    receipt = await get_receipt(db, receipt_id)

    item: ReceiptItem | None = None
    for r_item in receipt.items:
        if r_item.id == item_id:
            item = r_item
            break

    if item is None:
        raise NotFoundError("Item do recebimento não encontrado.")

    if item.version != payload.version:
        raise ConflictError("O item foi modificado por outro processo. Atualize e tente novamente.")

    old_snapshot = snapshot(item)
    item.presentation_status = payload.presentation_status
    item.presented_quantity = payload.presented_quantity
    item.conference_status = payload.conference_status
    item.decision = payload.decision
    item.notes = payload.notes
    item.version += 1

    # Atualiza status global do recebimento se aplicável
    if receipt.status == ReceiptStatus.REGISTRADO:
        receipt.status = ReceiptStatus.EM_CONFERENCIA
        receipt.version += 1

    # Verifica se todos os itens foram conferidos
    all_concluded = all(i.conference_status != ConferenceStatus.PENDENTE for i in receipt.items)
    if all_concluded:
        any_non_conforming = any(
            i.conference_status in {ConferenceStatus.COM_RESSALVA, ConferenceStatus.NAO_CONFORME}
            for i in receipt.items
        )
        new_receipt_status = ReceiptStatus.PENDENTE if any_non_conforming else ReceiptStatus.CONCLUIDO
        if receipt.status != new_receipt_status:
            receipt.status = new_receipt_status
            receipt.version += 1

    new_item_snapshot = snapshot(item)
    await db.flush()

    audit_entry = await audit_service.append(
        db,
        action=AuditAction.UPDATE,
        entity_type=AuditEntity.RECEIPT.value,
        entity_id=receipt.id,
        actor=actor,
        old_value=old_snapshot,
        new_value=new_item_snapshot,
        reason=f"Conferência do item {item_id}: {payload.conference_status.value}",
        context=context,
    )
    await db.commit()
    refreshed_receipt = await get_receipt(db, receipt_id)
    refreshed_item = next(i for i in refreshed_receipt.items if i.id == item_id)
    return refreshed_item, audit_entry.sequence


async def get_custody_object(db: AsyncSession, custody_object_id: UUID) -> CustodyObject:
    """Busca o objeto de custódia pelo ID ou levanta 404."""
    stmt = (
        select(CustodyObject)
        .options(
            selectinload(CustodyObject.receipt_item).selectinload(ReceiptItem.solicitation_item),
            selectinload(CustodyObject.receipt_item).selectinload(ReceiptItem.receipt).selectinload(Receipt.solicitation),
            selectinload(CustodyObject.current_custodian),
            selectinload(CustodyObject.linked_device_sample),
        )
        .where(CustodyObject.id == custody_object_id)
    )
    obj = await db.scalar(stmt)
    if obj is None:
        raise NotFoundError("Objeto de custódia não encontrado.")
    return obj


async def get_custody_history(db: AsyncSession, custody_object_id: UUID) -> list[CustodyEvent]:
    """Retorna histórico cronológico append-only dos eventos de custódia do objeto."""
    await get_custody_object(db, custody_object_id)  # valida existência
    stmt = (
        select(CustodyEvent)
        .where(CustodyEvent.custody_object_id == custody_object_id)
        .order_by(CustodyEvent.effective_at.asc(), CustodyEvent.created_at.asc())
    )
    result = await db.scalars(stmt)
    return list(result.all())


async def transfer_custody(
    db: AsyncSession,
    custody_object_id: UUID,
    *,
    payload: CustodyTransferCreate,
    actor: User,
    context: RequestContext | None = None,
) -> tuple[CustodyObject, int]:
    """Transfere a guarda física de um objeto de custódia para outro custodiante/local."""
    obj = await get_custody_object(db, custody_object_id)

    if obj.status not in {CustodyObjectStatus.SOB_GUARDA, CustodyObjectStatus.EM_CONFERENCIA}:
        raise ValidationDomainError(
            f"Transferência não permitida para objeto no status {obj.status.value}."
        )

    if obj.version != payload.version:
        raise ConflictError("O objeto de custódia foi modificado por outro processo. Atualize e tente novamente.")

    new_custodian = await db.get(User, payload.to_custodian_id)
    if new_custodian is None:
        raise NotFoundError("Novo custodiante não encontrado.")

    old_snapshot = snapshot(obj)

    event = CustodyEvent(
        custody_object_id=obj.id,
        event_type=CustodyEventType.TRANSFERENCIA,
        effective_at=utcnow(),
        from_custodian_id=obj.current_custodian_id,
        to_custodian_id=payload.to_custodian_id,
        from_location=obj.current_location,
        to_location=payload.to_location or obj.current_location,
        reason=payload.reason,
        registered_by_id=actor.id,
    )
    db.add(event)

    obj.current_custodian_id = payload.to_custodian_id
    if payload.to_location:
        obj.current_location = payload.to_location
    obj.version += 1
    new_obj_snapshot = snapshot(obj)
    await db.flush()

    audit_entry = await audit_service.append(
        db,
        action=AuditAction.TRANSFER,
        entity_type=AuditEntity.CUSTODY_OBJECT.value,
        entity_id=obj.id,
        actor=actor,
        old_value=old_snapshot,
        new_value=new_obj_snapshot,
        reason=payload.reason,
        context=context,
    )
    await db.commit()
    refreshed = await get_custody_object(db, custody_object_id)
    return refreshed, audit_entry.sequence


async def accept_custody_object(
    db: AsyncSession,
    custody_object_id: UUID,
    *,
    payload: CustodyAcceptanceCreate,
    actor: User,
    context: RequestContext | None = None,
) -> tuple[DeviceSample | None, int]:
    """Formaliza o aceite técnico e cria atomicamente a DeviceSample correspondente."""
    obj = await get_custody_object(db, custody_object_id)

    if obj.status != CustodyObjectStatus.SOB_GUARDA:
        raise ValidationDomainError(
            f"O aceite só pode ser registrado para objetos com status SOB_GUARDA. Status atual: {obj.status.value}"
        )

    if obj.version != payload.version:
        raise ConflictError("O objeto foi modificado por outro processo. Atualize e tente novamente.")

    receipt_item = obj.receipt_item
    solicitation_item = receipt_item.solicitation_item
    solicitation = receipt_item.receipt.solicitation

    sample: DeviceSample | None = None

    if payload.decision == ReceiptDecisionEnum.ACCEPTED:
        ensure_custody_object_transition(obj.status, CustodyObjectStatus.ACEITO)

        sample_seq = await next_sequence(db, "sample_accession_seq")
        accession_number = f"LIMS-{utcnow().year}-{int(sample_seq):06d}"

        sample = DeviceSample(
            accession_number=accession_number,
            serial_number=solicitation_item.serial_number or f"SN-PEND-{accession_number}",
            lot_number=solicitation_item.lot_number or f"LOT-PEND-{accession_number}",
            manufacturer=solicitation_item.manufacturer or "Fabricante não informado",
            commercial_name=solicitation_item.product_name,
            model=solicitation_item.model,
            status=SampleStatus.RECEBIDO,
            received_at=utcnow(),
            received_by_id=actor.id,
            current_custodian_id=actor.id,
            current_location=payload.storage_location,
            solicitation_id=solicitation.id,
            origin_custody_object_id=obj.id,
            version=1,
        )
        db.add(sample)
        await db.flush()

        # Cria entrada na trilha legada de custódia para manter compatibilidade
        coc = ChainOfCustody(
            device_sample_id=sample.id,
            transferred_at=utcnow(),
            from_custodian_id=None,
            to_custodian_id=actor.id,
            location_from=None,
            location_to=payload.storage_location,
            reason="Ingresso via aceite técnico de objeto de custódia",
        )
        db.add(coc)

        # Encerramento do ciclo de custódia física pré-amostra
        event = CustodyEvent(
            custody_object_id=obj.id,
            event_type=CustodyEventType.ENCERRAMENTO,
            effective_at=utcnow(),
            from_custodian_id=obj.current_custodian_id,
            to_custodian_id=actor.id,
            from_location=obj.current_location,
            to_location=payload.storage_location,
            reason=f"Aceite técnico formalizado. Amostra operacional gerada: {sample.accession_number}.",
            registered_by_id=actor.id,
        )
        db.add(event)

        obj.status = CustodyObjectStatus.ACEITO
        obj.linked_device_sample_id = sample.id
        obj.version += 1
        new_sample_snapshot = snapshot(sample)
        new_obj_snapshot = snapshot(obj)
        await db.flush()

        await audit_service.append(
            db,
            action=AuditAction.CREATE,
            entity_type=AuditEntity.DEVICE_SAMPLE.value,
            entity_id=sample.id,
            actor=actor,
            new_value=new_sample_snapshot,
            reason=f"Amostra operacional gerada a partir do objeto {obj.object_code}",
            context=context,
        )

        audit_entry = await audit_service.append(
            db,
            action=AuditAction.STATUS_CHANGE,
            entity_type=AuditEntity.CUSTODY_OBJECT.value,
            entity_id=obj.id,
            actor=actor,
            new_value=new_obj_snapshot,
            reason=f"Objeto aceito tecnicamente. Amostra: {sample.accession_number}",
            context=context,
        )

    else:
        ensure_custody_object_transition(obj.status, CustodyObjectStatus.RECUSADO)

        event = CustodyEvent(
            custody_object_id=obj.id,
            event_type=CustodyEventType.ENCERRAMENTO,
            effective_at=utcnow(),
            from_custodian_id=obj.current_custodian_id,
            to_custodian_id=None,
            from_location=obj.current_location,
            to_location=None,
            reason=f"Recusa técnica: {payload.notes or 'Recusado na conferência técnica'}",
            registered_by_id=actor.id,
        )
        db.add(event)

        obj.status = CustodyObjectStatus.RECUSADO
        obj.version += 1
        new_obj_snapshot = snapshot(obj)
        await db.flush()

        audit_entry = await audit_service.append(
            db,
            action=AuditAction.STATUS_CHANGE,
            entity_type=AuditEntity.CUSTODY_OBJECT.value,
            entity_id=obj.id,
            actor=actor,
            new_value=new_obj_snapshot,
            reason=f"Objeto recusado tecnicamente: {payload.notes}",
            context=context,
        )

    await db.commit()
    refreshed_sample: DeviceSample | None = None
    if sample is not None:
        refreshed_sample = await db.get(DeviceSample, sample.id)
    return refreshed_sample, audit_entry.sequence
