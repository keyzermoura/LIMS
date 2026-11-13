"""Rotas de Gestão de Competência e Qualificação de Analistas (ISO/IEC 17025 §6.2 / Sprint 4.1)."""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.context import RequestContext
from app.models.enums import QualificationStatus, UserRole
from app.models.user import User
from app.schemas.qualification import (
    AnalystQualificationGrantIn,
    AnalystQualificationOut,
    AnalystQualificationRevokeIn,
    QualificationCheckOut,
    TrainingRecordCreate,
    TrainingRecordOut,
)
from app.services import qualification_service

router = APIRouter(prefix="/qualifications", tags=["Competência & Qualificação (Fase 4)"])


def _to_qualification_out(qual: Any) -> AnalystQualificationOut:
    return AnalystQualificationOut(
        id=qual.id,
        user_id=qual.user_id,
        method_id=qual.method_id,
        status=qual.status,
        granted_at=qual.granted_at,
        expires_at=qual.expires_at,
        authorized_by_id=qual.authorized_by_id,
        signature_id=qual.signature_id,
        scope=qual.scope,
        notes=qual.notes,
        is_active=qual.is_active,
        version=qual.version,
        created_at=qual.created_at,
        user_name=qual.user.full_name if qual.user else None,
        method_code=qual.method.code if qual.method else None,
        method_name=qual.method.name if qual.method else None,
        trainings=[TrainingRecordOut.model_validate(t) for t in (qual.trainings or [])],
    )


@router.get("", response_model=list[AnalystQualificationOut])
async def list_qualifications(
    user_id: UUID | None = None,
    method_id: UUID | None = None,
    status_filter: QualificationStatus | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AnalystQualificationOut]:
    """Lista as habilitações técnicas e qualificações da equipe analítica."""
    quals = await qualification_service.list_analyst_qualifications(
        db, user_id=user_id, method_id=method_id, status=status_filter
    )
    return [_to_qualification_out(q) for q in quals]


@router.get("/check", response_model=QualificationCheckOut)
async def check_qualification(
    user_id: UUID,
    method_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> QualificationCheckOut:
    """Verifica em tempo de execução se um analista está formalmente habilitado e vigente para o método."""
    return await qualification_service.check_analyst_qualification(
        db, user_id=user_id, method_id=method_id
    )


@router.post("/grant", response_model=AnalystQualificationOut, status_code=status.HTTP_201_CREATED)
async def grant_qualification(
    payload: AnalystQualificationGrantIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_signature_token: Annotated[str | None, Header(alias="X-Signature-Token")] = None,
) -> AnalystQualificationOut:
    """Concede ou renova habilitação técnica a um analista com assinatura eletrônica e auditoria Part 11."""
    qual, _ = await qualification_service.grant_analyst_qualification(
        db,
        payload=payload,
        authorizer=current_user,
        signature_token=x_signature_token,
    )
    return _to_qualification_out(qual)


@router.post("/{qualification_id}/revoke", response_model=AnalystQualificationOut)
async def revoke_qualification(
    qualification_id: UUID,
    payload: AnalystQualificationRevokeIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_signature_token: Annotated[str | None, Header(alias="X-Signature-Token")] = None,
) -> AnalystQualificationOut:
    """Suspende ou revoga a qualificação analítica de um operador com justificativa obrigatória."""
    qual, _ = await qualification_service.revoke_or_suspend_qualification(
        db,
        qualification_id=qualification_id,
        payload=payload,
        authorizer=current_user,
        signature_token=x_signature_token,
    )
    return _to_qualification_out(qual)


@router.post("/trainings", response_model=TrainingRecordOut, status_code=status.HTTP_201_CREATED)
async def record_training(
    user_id: UUID,
    payload: TrainingRecordCreate,
    qualification_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TrainingRecordOut:
    """Registra treinamento técnico ou comprovação de horas práticas de bancada."""
    tr, _ = await qualification_service.record_training(
        db,
        user_id=user_id,
        payload=payload,
        qualification_id=qualification_id,
        actor=current_user,
    )
    return TrainingRecordOut.model_validate(tr)
