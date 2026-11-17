"""Rotas REST para Cadeia Física de Armazenamento, Retenção e Descarte (H2.3 & H2.4)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.deps import CurrentUser, DbSession, require_roles
from app.core.context import RequestContext
from app.models.enums import RetentionStatus, StorageLocationType, UserRole
from app.schemas.storage_and_disposal import (
    SampleDisposalCreate,
    SampleDisposalOut,
    SampleRetentionCreate,
    SampleRetentionOut,
    SampleRetentionUpdate,
    SampleStorageMovementCreate,
    SampleStorageMovementOut,
    StorageDashboardSummary,
    StorageLocationCreate,
    StorageLocationOut,
    StorageLocationUpdate,
)
from app.services import storage_disposal_service

router = APIRouter(prefix="/storage", tags=["Cadeia Física, Contraprova e Descarte"])


# ---------------------------------------------------------------------------
# Dashboard / Resumo
# ---------------------------------------------------------------------------


@router.get(
    "/summary",
    response_model=StorageDashboardSummary,
    summary="Resumo de conformidade e contadores de armazenamento e descarte",
)
async def get_storage_summary(
    db: DbSession,
    user: CurrentUser,
) -> StorageDashboardSummary:
    return await storage_disposal_service.get_storage_summary(db)


# ---------------------------------------------------------------------------
# Locais Físicos de Armazenamento (StorageLocation)
# ---------------------------------------------------------------------------


@router.post(
    "/locations",
    response_model=StorageLocationOut,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar novo local físico de custódia (Freezer, Câmara, etc.)",
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.TECNICO, UserRole.CUSTODIANTE))],
)
async def create_storage_location(
    payload: StorageLocationCreate,
    request: Request,
    db: DbSession,
    user: CurrentUser,
) -> StorageLocationOut:
    location = await storage_disposal_service.create_location(
        db,
        payload=payload,
        actor=user,
        context=RequestContext.from_request(request),
    )
    occupancy = await storage_disposal_service.get_location_occupancy(db, location.id)
    out = StorageLocationOut.model_validate(location)
    out.current_occupancy = occupancy
    return out


@router.get(
    "/locations",
    response_model=list[StorageLocationOut],
    summary="Listar locais físicos de custódia",
)
async def list_storage_locations(
    db: DbSession,
    user: CurrentUser,
    is_active: bool | None = Query(None, description="Filtrar por ativo/inativo"),
    location_type: StorageLocationType | None = Query(None, description="Filtrar por tipo"),
) -> list[StorageLocationOut]:
    locations = await storage_disposal_service.list_locations(
        db, is_active=is_active, location_type=location_type
    )
    result: list[StorageLocationOut] = []
    for loc in locations:
        occupancy = await storage_disposal_service.get_location_occupancy(db, loc.id)
        out = StorageLocationOut.model_validate(loc)
        out.current_occupancy = occupancy
        result.append(out)
    return result


@router.get(
    "/locations/{location_id}",
    response_model=StorageLocationOut,
    summary="Detalhes do local físico de custódia",
)
async def get_storage_location(
    location_id: UUID,
    db: DbSession,
    user: CurrentUser,
) -> StorageLocationOut:
    location = await storage_disposal_service.get_location(db, location_id)
    occupancy = await storage_disposal_service.get_location_occupancy(db, location.id)
    out = StorageLocationOut.model_validate(location)
    out.current_occupancy = occupancy
    return out


@router.patch(
    "/locations/{location_id}",
    response_model=StorageLocationOut,
    summary="Atualizar limites térmicos, capacidade ou status do local",
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.TECNICO, UserRole.CUSTODIANTE))],
)
async def update_storage_location(
    location_id: UUID,
    payload: StorageLocationUpdate,
    request: Request,
    db: DbSession,
    user: CurrentUser,
) -> StorageLocationOut:
    location = await storage_disposal_service.update_location(
        db,
        location_id=location_id,
        payload=payload,
        actor=user,
        context=RequestContext.from_request(request),
    )
    occupancy = await storage_disposal_service.get_location_occupancy(db, location.id)
    out = StorageLocationOut.model_validate(location)
    out.current_occupancy = occupancy
    return out


# ---------------------------------------------------------------------------
# Movimentações Físicas (SampleStorageMovement)
# ---------------------------------------------------------------------------


@router.post(
    "/movements",
    response_model=SampleStorageMovementOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar movimentação física de amostra entre locais de custódia",
    dependencies=[
        Depends(
            require_roles(UserRole.ADMIN, UserRole.TECNICO, UserRole.CUSTODIANTE, UserRole.FISCAL)
        )
    ],
)
async def create_sample_movement(
    payload: SampleStorageMovementCreate,
    request: Request,
    db: DbSession,
    user: CurrentUser,
) -> SampleStorageMovementOut:
    movement = await storage_disposal_service.move_sample(
        db,
        payload=payload,
        actor=user,
        context=RequestContext.from_request(request),
    )
    return SampleStorageMovementOut.model_validate(movement)


@router.get(
    "/movements",
    response_model=list[SampleStorageMovementOut],
    summary="Histórico de transferências físicas de custódia",
)
async def list_sample_movements(
    db: DbSession,
    user: CurrentUser,
    sample_id: UUID | None = Query(None, description="Filtrar por ID da amostra"),
) -> list[SampleStorageMovementOut]:
    movements = await storage_disposal_service.list_sample_movements(db, sample_id=sample_id)
    return [SampleStorageMovementOut.model_validate(m) for m in movements]


# ---------------------------------------------------------------------------
# Contraprova Pericial (SampleRetention - ISO 17025 §7.4)
# ---------------------------------------------------------------------------


@router.post(
    "/retentions",
    response_model=SampleRetentionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Instituir guarda de contraprova pericial sob lacre inviolável",
    dependencies=[
        Depends(
            require_roles(UserRole.ADMIN, UserRole.TECNICO, UserRole.CUSTODIANTE, UserRole.FISCAL)
        )
    ],
)
async def create_sample_retention(
    payload: SampleRetentionCreate,
    request: Request,
    db: DbSession,
    user: CurrentUser,
) -> SampleRetentionOut:
    retention = await storage_disposal_service.retain_sample(
        db,
        payload=payload,
        actor=user,
        context=RequestContext.from_request(request),
    )
    return SampleRetentionOut.model_validate(retention)


@router.get(
    "/retentions",
    response_model=list[SampleRetentionOut],
    summary="Listar contraprovas periciais sob guarda legal",
)
async def list_sample_retentions(
    db: DbSession,
    user: CurrentUser,
    status_filter: RetentionStatus | None = Query(
        None, alias="status", description="Filtrar por status"
    ),
    location_id: UUID | None = Query(None, description="Filtrar por local físico"),
) -> list[SampleRetentionOut]:
    retentions = await storage_disposal_service.list_retentions(
        db, status_filter=status_filter, location_id=location_id
    )
    return [SampleRetentionOut.model_validate(r) for r in retentions]


@router.get(
    "/retentions/{retention_id}",
    response_model=SampleRetentionOut,
    summary="Detalhes da contraprova pericial",
)
async def get_sample_retention(
    retention_id: UUID,
    db: DbSession,
    user: CurrentUser,
) -> SampleRetentionOut:
    retention = await storage_disposal_service.get_retention(db, retention_id)
    return SampleRetentionOut.model_validate(retention)


@router.patch(
    "/retentions/{retention_id}",
    response_model=SampleRetentionOut,
    summary="Atualizar contraprova (extensão de prazo de guarda legal ou atualização de lacre)",
    dependencies=[
        Depends(
            require_roles(UserRole.ADMIN, UserRole.TECNICO, UserRole.CUSTODIANTE, UserRole.FISCAL)
        )
    ],
)
async def update_sample_retention(
    retention_id: UUID,
    payload: SampleRetentionUpdate,
    request: Request,
    db: DbSession,
    user: CurrentUser,
) -> SampleRetentionOut:
    retention = await storage_disposal_service.update_retention(
        db,
        retention_id=retention_id,
        payload=payload,
        actor=user,
        context=RequestContext.from_request(request),
    )
    return SampleRetentionOut.model_validate(retention)


# ---------------------------------------------------------------------------
# Descarte Irreversível com Dupla Assinatura (21 CFR Part 11)
# ---------------------------------------------------------------------------


@router.post(
    "/disposal",
    response_model=SampleDisposalOut,
    status_code=status.HTTP_201_CREATED,
    summary="Lavrar Termo de Descarte com Dupla Assinatura Eletrônica (21 CFR Part 11)",
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.TECNICO, UserRole.CUSTODIANTE))],
)
async def dispose_sample_endpoint(
    payload: SampleDisposalCreate,
    request: Request,
    db: DbSession,
    user: CurrentUser,
) -> SampleDisposalOut:
    disposal = await storage_disposal_service.dispose_sample(
        db,
        payload=payload,
        actor=user,
        context=RequestContext.from_request(request),
    )
    return SampleDisposalOut.model_validate(disposal)


@router.get(
    "/disposals",
    response_model=list[SampleDisposalOut],
    summary="Listar termos e manifestos de descarte executados",
)
async def list_sample_disposals(
    db: DbSession,
    user: CurrentUser,
    sample_id: UUID | None = Query(None, description="Filtrar por ID da amostra"),
) -> list[SampleDisposalOut]:
    disposals = await storage_disposal_service.list_disposals(db, sample_id=sample_id)
    return [SampleDisposalOut.model_validate(d) for d in disposals]
