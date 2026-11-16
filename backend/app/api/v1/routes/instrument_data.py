"""Rotas da API para Aquisição Direta de Instrumentos Analíticos (Fase 5 / Sprint 5.3).

Conforme ISO/IEC 17025:2017 §7.11 (Controle de Dados) e 21 CFR Part 11 (ALCOA+).
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from pydantic import BaseModel

from app.api.deps import CurrentUser, DbSession, require_roles
from app.models.enums import InstrumentFileFormat, InstrumentImportStatus, UserRole
from app.models.user import User
from app.schemas.instrument_data import (
    InstrumentDataImportOut,
    InstrumentDataMapIn,
    InstrumentDataSummary,
)
from app.services import instrument_parser_service

router = APIRouter(
    prefix="/instrument-data",
    tags=["Aquisição de Dados de Instrumentos (Fase 5)"],
)

WRITE_ROLES = (UserRole.ADMIN, UserRole.FISCAL, UserRole.TECNICO)


class RawUploadIn(BaseModel):
    equipment_id: UUID
    file_name: str
    file_format: InstrumentFileFormat
    raw_content: str
    test_execution_id: UUID | None = None


@router.post(
    "/upload",
    response_model=InstrumentDataImportOut,
    status_code=status.HTTP_201_CREATED,
    summary="Upload e ingestão de arquivo bruto de instrumento analítico (Multipart)",
)
async def upload_instrument_file(
    db: DbSession,
    equipment_id: Annotated[UUID, Form(description="ID do equipamento analítico emissor")],
    file_format: Annotated[InstrumentFileFormat, Form(description="Formato do arquivo")],
    file: UploadFile = File(...),
    test_execution_id: Annotated[UUID | None, Form(description="ID opcional da execução de ensaio")] = None,
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
) -> InstrumentDataImportOut:
    """Ingere arquivo bruto multipart, valida calibração, calcula SHA-256 e extrai medições."""
    content_bytes = await file.read()
    raw_content = content_bytes.decode("utf-8", errors="replace")
    record = await instrument_parser_service.upload_instrument_data(
        db,
        equipment_id=equipment_id,
        user_id=current_user.id,
        actor_username=current_user.username,
        file_name=file.filename or "instrument_data.raw",
        raw_content=raw_content,
        file_format=file_format,
        test_execution_id=test_execution_id,
    )
    return InstrumentDataImportOut.model_validate(record)


@router.post(
    "/upload-raw",
    response_model=InstrumentDataImportOut,
    status_code=status.HTTP_201_CREATED,
    summary="Ingestão de dados brutos de instrumento via JSON payload",
)
async def upload_raw_instrument_data(
    payload: RawUploadIn,
    db: DbSession,
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
) -> InstrumentDataImportOut:
    """Ingere conteúdo bruto de instrumento via corpo JSON estruturado."""
    record = await instrument_parser_service.upload_instrument_data(
        db,
        equipment_id=payload.equipment_id,
        user_id=current_user.id,
        actor_username=current_user.username,
        file_name=payload.file_name,
        raw_content=payload.raw_content,
        file_format=payload.file_format,
        test_execution_id=payload.test_execution_id,
    )
    return InstrumentDataImportOut.model_validate(record)


@router.get("", response_model=list[InstrumentDataImportOut])
async def list_instrument_imports(
    db: DbSession,
    _: CurrentUser,
    equipment_id: Annotated[UUID | None, Query(description="Filtrar por equipamento")] = None,
    test_execution_id: Annotated[UUID | None, Query(description="Filtrar por execução de ensaio")] = None,
    import_status: Annotated[InstrumentImportStatus | None, Query(alias="status", description="Filtrar por status")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[InstrumentDataImportOut]:
    """Lista importações de dados de instrumentos realizadas no laboratório."""
    items = await instrument_parser_service.list_instrument_imports(
        db,
        equipment_id=equipment_id,
        test_execution_id=test_execution_id,
        status=import_status,
        limit=limit,
    )
    return [InstrumentDataImportOut.model_validate(it) for it in items]


@router.get("/summary", response_model=InstrumentDataSummary)
async def get_instrument_imports_summary(
    db: DbSession,
    _: CurrentUser,
) -> InstrumentDataSummary:
    """Retorna o sumário de dados brutos importados e taxa de mapeamento."""
    all_imports = await instrument_parser_service.list_instrument_imports(db, limit=1000)
    total = len(all_imports)
    mapped = sum(1 for it in all_imports if it.status == InstrumentImportStatus.MAPPED)
    return InstrumentDataSummary(
        total_imports=total,
        mapped_imports=mapped,
        unmapped_imports=total - mapped,
    )


@router.get("/{import_id}", response_model=InstrumentDataImportOut)
async def get_instrument_import_detail(
    import_id: UUID,
    db: DbSession,
    _: CurrentUser,
) -> InstrumentDataImportOut:
    """Retorna os dados detalhados e o resumo de uma importação de instrumento."""
    record = await instrument_parser_service.get_instrument_import(db, import_id)
    return InstrumentDataImportOut.model_validate(record)


@router.post("/{import_id}/map-to-execution", response_model=InstrumentDataImportOut)
async def map_import_to_execution(
    import_id: UUID,
    payload: InstrumentDataMapIn,
    db: DbSession,
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
) -> InstrumentDataImportOut:
    """Mapeia os dados brutos de um instrumento diretamente nos resultados da execução."""
    record = await instrument_parser_service.map_import_to_execution(
        db,
        import_id=import_id,
        execution_id=payload.execution_id,
        actor_username=current_user.username,
    )
    return InstrumentDataImportOut.model_validate(record)
