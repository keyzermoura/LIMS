"""Serviço de Gestão de Evidências e Anexos de Bancada (Sprint 3.3 / ALCOA+ / ISO 17025)."""

from __future__ import annotations

import hashlib
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.context import RequestContext
from app.core.errors import NotFoundError, ValidationDomainError
from app.models.enums import AuditAction, AuditEntity
from app.models.lab_test import LabTest
from app.models.test_attachment import TestAttachment
from app.models.user import User
from app.services import audit_service
from app.services.audit_service import snapshot

MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB


async def upload_attachment(
    db: AsyncSession,
    test_id: UUID,
    *,
    filename: str,
    file_bytes: bytes,
    content_type: str = "application/octet-stream",
    actor: User,
    context: RequestContext | None = None,
) -> tuple[TestAttachment, int]:
    """Armazena evidência bruta vinculada ao ensaio com garantia de integridade SHA-256."""
    test = await db.get(LabTest, test_id)
    if test is None:
        raise NotFoundError("Ensaio laboratorial não encontrado.")

    if not filename or len(filename.strip()) == 0:
        raise ValidationDomainError("Nome do arquivo não pode ser vazio.")

    file_size = len(file_bytes)
    if file_size > MAX_FILE_SIZE:
        raise ValidationDomainError(
            f"Arquivo excede o tamanho máximo de {MAX_FILE_SIZE // (1024 * 1024)}MB."
        )

    sha256_hash = hashlib.sha256(file_bytes).hexdigest()

    attachment = TestAttachment(
        id=uuid4(),
        lab_test_id=test.id,
        filename=filename.strip(),
        file_size=file_size,
        content_type=content_type,
        sha256_hash=sha256_hash,
        file_data=file_bytes,
        uploaded_by_id=actor.id,
    )
    db.add(attachment)

    audit_entry = await audit_service.append(
        db,
        action=AuditAction.CREATE,
        entity_type=AuditEntity.TEST_ATTACHMENT.value,
        entity_id=attachment.id,
        actor=actor,
        old_value=None,
        new_value=snapshot(attachment),
        reason=f"Evidência de bancada '{attachment.filename}' anexada ao ensaio",
        context=context,
    )

    await db.commit()
    await db.refresh(attachment, ["uploaded_by"])
    return attachment, audit_entry.sequence


async def get_attachment(
    db: AsyncSession,
    attachment_id: UUID,
) -> TestAttachment:
    """Busca anexo pelo ID."""
    stmt = (
        select(TestAttachment)
        .options(selectinload(TestAttachment.uploaded_by))
        .where(TestAttachment.id == attachment_id)
    )
    attachment = await db.scalar(stmt)
    if attachment is None:
        raise NotFoundError("Anexo não encontrado.")
    return attachment


async def list_attachments_for_test(
    db: AsyncSession,
    test_id: UUID,
) -> list[TestAttachment]:
    """Lista anexos vinculados a um ensaio."""
    stmt = (
        select(TestAttachment)
        .options(selectinload(TestAttachment.uploaded_by))
        .where(TestAttachment.lab_test_id == test_id)
        .order_by(TestAttachment.created_at.desc())
    )
    res = await db.scalars(stmt)
    return list(res.all())
