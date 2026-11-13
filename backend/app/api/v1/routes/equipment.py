"""Rotas de Gestão de Equipamentos e Metrologia (Fase 2 / M2.1)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response, status

from app.api.deps import CurrentUser, DbSession, require_roles
from app.core.context import RequestContext
from app.models.enums import EquipmentCalibrationStatus, UserRole
from app.models.user import User
from app.schemas.equipment import (
    EquipmentCalibrationUpdate,
    EquipmentCreate,
    EquipmentOut,
    EquipmentUpdate,
)
from app.services import equipment_service

router = APIRouter(prefix="/equipment", tags=["Equipamentos e Metrologia"])

WRITE_ROLES = (UserRole.ADMIN, UserRole.FISCAL, UserRole.TECNICO)


@router.get(
    "",
    response_model=list[EquipmentOut],
    summary="Listar equipamentos do laboratório",
)
async def list_equipment(
    db: DbSession,
    _: CurrentUser,
    calibration_status: EquipmentCalibrationStatus | None = Query(
        default=None, description="Filtrar por status de calibração"
    ),
    active_only: bool = Query(default=True, description="Exibir apenas equipamentos ativos"),
) -> list[EquipmentOut]:
    equipment_list = await equipment_service.list_equipment(
        db, calibration_status=calibration_status, active_only=active_only
    )
    return [EquipmentOut.model_validate(e) for e in equipment_list]


@router.post(
    "",
    response_model=EquipmentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar novo instrumento ou equipamento",
)
async def create_equipment(
    payload: EquipmentCreate,
    db: DbSession,
    request: Request,
    response: Response,
    actor: User = Depends(require_roles(*WRITE_ROLES)),
) -> EquipmentOut:
    ctx = RequestContext.from_request(request)
    equipment, audit_id = await equipment_service.create_equipment(
        db, payload=payload, actor=actor, context=ctx
    )
    out = EquipmentOut.model_validate(equipment)
    await db.commit()
    response.headers["X-Audit-Log-Id"] = str(audit_id)
    return out


@router.get(
    "/{equipment_id}",
    response_model=EquipmentOut,
    summary="Consultar equipamento por identificador",
)
async def get_equipment(
    equipment_id: UUID,
    db: DbSession,
    _: CurrentUser,
) -> EquipmentOut:
    equipment = await equipment_service.get_equipment(db, equipment_id)
    return EquipmentOut.model_validate(equipment)


@router.put(
    "/{equipment_id}",
    response_model=EquipmentOut,
    summary="Atualizar cadastro de equipamento",
)
async def update_equipment(
    equipment_id: UUID,
    payload: EquipmentUpdate,
    db: DbSession,
    request: Request,
    response: Response,
    actor: User = Depends(require_roles(*WRITE_ROLES)),
) -> EquipmentOut:
    ctx = RequestContext.from_request(request)
    equipment, audit_id = await equipment_service.update_equipment(
        db, equipment_id=equipment_id, payload=payload, actor=actor, context=ctx
    )
    out = EquipmentOut.model_validate(equipment)
    await db.commit()
    response.headers["X-Audit-Log-Id"] = str(audit_id)
    return out


@router.post(
    "/{equipment_id}/calibration",
    response_model=EquipmentOut,
    summary="Registrar nova calibração periódica para o instrumento",
)
async def update_calibration(
    equipment_id: UUID,
    payload: EquipmentCalibrationUpdate,
    db: DbSession,
    request: Request,
    response: Response,
    actor: User = Depends(require_roles(*WRITE_ROLES)),
) -> EquipmentOut:
    ctx = RequestContext.from_request(request)
    equipment, audit_id = await equipment_service.update_calibration(
        db, equipment_id=equipment_id, payload=payload, actor=actor, context=ctx
    )
    out = EquipmentOut.model_validate(equipment)
    await db.commit()
    response.headers["X-Audit-Log-Id"] = str(audit_id)
    return out
