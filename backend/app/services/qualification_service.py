"""Serviço de Gestão de Competência e Qualificação de Analistas (ISO/IEC 17025 §6.2 / Sprint 4.1)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.context import RequestContext
from app.core.errors import NotFoundError, PermissionDeniedError, ValidationDomainError
from app.models.base import utcnow
from app.models.electronic_signature import ElectronicSignature
from app.models.enums import (
    AuditAction,
    AuditEntity,
    QualificationStatus,
    SignatureAction,
    UserRole,
)
from app.models.qualification import AnalystQualification, TrainingRecord
from app.models.test_method import TestMethod
from app.models.user import User
from app.schemas.qualification import (
    AnalystQualificationGrantIn,
    AnalystQualificationRevokeIn,
    QualificationCheckOut,
    TrainingRecordCreate,
)
from app.services import audit_service, signature_service
from app.services.audit_service import snapshot


async def check_analyst_qualification(
    db: AsyncSession,
    *,
    user_id: UUID,
    method_id: UUID,
) -> QualificationCheckOut:
    """Verifica em tempo de execução se o analista possui habilitação técnica vigente para o método."""
    user = await db.get(User, user_id)
    if user is None:
        raise NotFoundError("Usuário não encontrado.")

    method = await db.get(TestMethod, method_id)
    if method is None:
        raise NotFoundError("Método de ensaio não encontrado.")

    stmt = select(AnalystQualification).where(
        AnalystQualification.user_id == user_id,
        AnalystQualification.method_id == method_id,
    )
    qual = await db.scalar(stmt)

    if qual is None:
        return QualificationCheckOut(
            is_qualified=False,
            status=None,
            user_id=user_id,
            method_id=method_id,
            user_name=user.full_name,
            method_code=method.code,
            reason="Analista não possui registro formal de qualificação para este método.",
        )

    now = utcnow()
    if qual.status != QualificationStatus.QUALIFICADO:
        return QualificationCheckOut(
            is_qualified=False,
            status=qual.status,
            user_id=user_id,
            method_id=method_id,
            user_name=user.full_name,
            method_code=method.code,
            reason=f"Habilitação com status impeditivo: {qual.status.value}.",
        )

    if qual.expires_at and qual.expires_at < now:
        return QualificationCheckOut(
            is_qualified=False,
            status=QualificationStatus.EXPIRADO,
            user_id=user_id,
            method_id=method_id,
            user_name=user.full_name,
            method_code=method.code,
            reason=f"Qualificação expirada em {qual.expires_at.strftime('%d/%m/%Y')}.",
        )

    return QualificationCheckOut(
        is_qualified=True,
        status=qual.status,
        user_id=user_id,
        method_id=method_id,
        user_name=user.full_name,
        method_code=method.code,
        reason=None,
    )


async def grant_analyst_qualification(
    db: AsyncSession,
    *,
    payload: AnalystQualificationGrantIn,
    authorizer: User,
    signature_token: str | None = None,
    context: RequestContext | None = None,
) -> tuple[AnalystQualification, int]:
    """Concede ou renova habilitação técnica formal de um analista com assinatura eletrônica Part 11."""
    # Apenas Gerência Técnica / Inspetor / Admin podem autorizar
    if authorizer.role not in (UserRole.ADMIN, UserRole.FISCAL):
        raise PermissionDeniedError(
            "Apenas administradores ou fiscais/responsáveis técnicos podem conceder qualificações analíticas."
        )

    analyst = await db.get(User, payload.user_id)
    if analyst is None:
        raise NotFoundError("Analista não encontrado.")

    method = await db.get(TestMethod, payload.method_id)
    if method is None:
        raise NotFoundError("Método analítico não encontrado.")

    sig_record: ElectronicSignature | None = None
    if signature_token:
        request_ctx = context or RequestContext(
            ip_address="127.0.0.1", user_agent="LIMS-Internal", request_id="internal"
        )
        sig_record = await signature_service.consume(
            db,
            token=signature_token,
            user=authorizer,
            entity_type="User",
            entity_id=str(analyst.id),
            action=SignatureAction.UPDATE,
            context=request_ctx,
        )

    # Verifica se já existe qualificação para o par (user, method)
    stmt = (
        select(AnalystQualification)
        .options(selectinload(AnalystQualification.trainings))
        .where(
            AnalystQualification.user_id == analyst.id,
            AnalystQualification.method_id == method.id,
        )
    )
    existing = await db.scalar(stmt)

    now = utcnow()
    if existing:
        old_state = snapshot(existing)
        existing.status = payload.status
        existing.granted_at = now
        existing.expires_at = payload.expires_at
        existing.authorized_by_id = authorizer.id
        existing.scope = payload.scope
        existing.notes = payload.notes
        existing.signature_id = sig_record.id if sig_record else existing.signature_id
        existing.version += 1
        qual = existing
        action = AuditAction.UPDATE
    else:
        old_state = None
        qual = AnalystQualification(
            id=uuid4(),
            user_id=analyst.id,
            method_id=method.id,
            status=payload.status,
            granted_at=now,
            expires_at=payload.expires_at,
            authorized_by_id=authorizer.id,
            signature_id=sig_record.id if sig_record else None,
            scope=payload.scope,
            notes=payload.notes,
        )
        db.add(qual)
        action = AuditAction.CREATE

    # Registra treinamentos anexados na concessão
    for t_in in payload.trainings:
        tr = TrainingRecord(
            id=uuid4(),
            user_id=analyst.id,
            qualification_id=qual.id,
            title=t_in.title,
            provider=t_in.provider,
            completed_at=t_in.completed_at or now,
            hours=t_in.hours,
            certificate_code=t_in.certificate_code,
            notes=t_in.notes,
        )
        db.add(tr)

    audit_entry = await audit_service.append(
        db,
        action=action,
        entity_type=AuditEntity.ANALYST_QUALIFICATION.value,
        entity_id=qual.id,
        actor=authorizer,
        old_value=old_state,
        new_value=snapshot(qual),
        reason=f"Habilitação formal para o método {method.code} concedida ao analista {analyst.full_name}",
        context=context,
        signature_id=sig_record.id if sig_record else None,
    )

    await db.commit()
    await db.refresh(qual, ["user", "method", "authorized_by", "trainings"])
    return qual, audit_entry.sequence


async def revoke_or_suspend_qualification(
    db: AsyncSession,
    *,
    qualification_id: UUID,
    payload: AnalystQualificationRevokeIn,
    authorizer: User,
    signature_token: str | None = None,
    context: RequestContext | None = None,
) -> tuple[AnalystQualification, int]:
    """Suspende ou revoga a qualificação analítica de um operador com justificativa mandatória."""
    if authorizer.role not in (UserRole.ADMIN, UserRole.FISCAL):
        raise PermissionDeniedError("Apenas fiscais ou administradores podem suspender habilitações.")

    stmt = (
        select(AnalystQualification)
        .options(selectinload(AnalystQualification.user), selectinload(AnalystQualification.method))
        .where(AnalystQualification.id == qualification_id)
    )
    qual = await db.scalar(stmt)
    if qual is None:
        raise NotFoundError("Registro de qualificação não encontrado.")

    if payload.status not in (QualificationStatus.SUSPENSO, QualificationStatus.EXPIRADO):
        raise ValidationDomainError("O novo status deve ser SUSPENSO ou EXPIRADO.")

    sig_record: ElectronicSignature | None = None
    if signature_token:
        request_ctx = context or RequestContext(
            ip_address="127.0.0.1", user_agent="LIMS-Internal", request_id="internal"
        )
        sig_record = await signature_service.consume(
            db,
            token=signature_token,
            user=authorizer,
            entity_type="User",
            entity_id=str(qual.user_id),
            action=SignatureAction.UPDATE,
            context=request_ctx,
        )

    old_state = snapshot(qual)
    qual.status = payload.status
    qual.notes = f"{qual.notes or ''}\n[Revogação em {utcnow().isoformat()}]: {payload.reason}".strip()
    qual.version += 1

    audit_entry = await audit_service.append(
        db,
        action=AuditAction.UPDATE,
        entity_type=AuditEntity.ANALYST_QUALIFICATION.value,
        entity_id=qual.id,
        actor=authorizer,
        old_value=old_state,
        new_value=snapshot(qual),
        reason=f"Qualificação {qual.id} alterada para {payload.status.value}: {payload.reason}",
        context=context,
        signature_id=sig_record.id if sig_record else None,
    )

    await db.commit()
    await db.refresh(qual, ["user", "method", "authorized_by", "trainings"])
    return qual, audit_entry.sequence


async def list_analyst_qualifications(
    db: AsyncSession,
    *,
    user_id: UUID | None = None,
    method_id: UUID | None = None,
    status: QualificationStatus | None = None,
) -> list[AnalystQualification]:
    """Lista as qualificações da equipe técnica com opções de filtro metrológico."""
    stmt = (
        select(AnalystQualification)
        .options(
            selectinload(AnalystQualification.user),
            selectinload(AnalystQualification.method),
            selectinload(AnalystQualification.authorized_by),
            selectinload(AnalystQualification.trainings),
        )
        .order_by(AnalystQualification.granted_at.desc())
    )
    if user_id:
        stmt = stmt.where(AnalystQualification.user_id == user_id)
    if method_id:
        stmt = stmt.where(AnalystQualification.method_id == method_id)
    if status:
        stmt = stmt.where(AnalystQualification.status == status)

    return list((await db.scalars(stmt)).all())


async def record_training(
    db: AsyncSession,
    *,
    user_id: UUID,
    payload: TrainingRecordCreate,
    qualification_id: UUID | None = None,
    actor: User,
    context: RequestContext | None = None,
) -> tuple[TrainingRecord, int]:
    """Registra treinamento ou comprovação de horas práticas de bancada."""
    analyst = await db.get(User, user_id)
    if analyst is None:
        raise NotFoundError("Analista não encontrado.")

    if qualification_id:
        qual = await db.get(AnalystQualification, qualification_id)
        if qual is None:
            raise NotFoundError("Qualificação informada não existe.")

    now = utcnow()
    tr = TrainingRecord(
        id=uuid4(),
        user_id=analyst.id,
        qualification_id=qualification_id,
        title=payload.title,
        provider=payload.provider,
        completed_at=payload.completed_at or now,
        hours=payload.hours,
        certificate_code=payload.certificate_code,
        notes=payload.notes,
    )
    db.add(tr)

    audit_entry = await audit_service.append(
        db,
        action=AuditAction.CREATE,
        entity_type=AuditEntity.TRAINING_RECORD.value,
        entity_id=tr.id,
        actor=actor,
        old_value=None,
        new_value=snapshot(tr),
        reason=f"Treinamento registrado para o analista {analyst.full_name}: {payload.title}",
        context=context,
    )

    await db.commit()
    await db.refresh(tr, ["user", "qualification"])
    return tr, audit_entry.sequence
