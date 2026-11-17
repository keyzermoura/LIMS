"""Rotas da API para Aquisição Direta de Instrumentos Analíticos (Fase 5 / Sprint 5.3).

Conforme ISO/IEC 17025:2017 §7.11 (Controle de Dados) e 21 CFR Part 11 (ALCOA+).
"""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Header, Query, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.api.deps import CurrentUser, DbSession, require_roles
from app.models.enums import InstrumentFileFormat, InstrumentImportStatus, UserRole
from app.models.user import User
from app.schemas.instrument_data import (
    InstrumentDataImportOut,
    InstrumentDataMapIn,
    InstrumentDataSummary,
)
from app.services import idempotency_service, instrument_parser_service, instrument_profiles

router = APIRouter(
    prefix="/instrument-data",
    tags=["Aquisição de Dados de Instrumentos (Fase 5)"],
)

WRITE_ROLES = (UserRole.ADMIN, UserRole.FISCAL, UserRole.TECNICO, UserRole.SERVICE)


class RawUploadIn(BaseModel):
    equipment_id: UUID
    file_name: str
    file_format: InstrumentFileFormat
    raw_content: str
    profile_id: str | None = None
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
    profile_id: Annotated[
        str | None,
        Form(description="Perfil declarativo de instrumento (H3.3)"),
    ] = None,
    test_execution_id: Annotated[
        UUID | None, Form(description="ID opcional da execução de ensaio")
    ] = None,
    idempotency_key: Annotated[
        str | None,
        Header(alias="Idempotency-Key", description="Chave de idempotência (RFC 7231 / H3.1)"),
    ] = None,
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
):
    """Ingere arquivo bruto multipart, valida calibração, calcula SHA-256 e extrai medições."""
    content_bytes = await file.read()
    raw_content = content_bytes.decode("utf-8", errors="replace")

    client_id = (
        current_user._service_client.client_id
        if hasattr(current_user, "_service_client")
        else str(current_user.id)
    )

    if idempotency_key:
        req_hash = idempotency_service.compute_payload_hash(
            {
                "equipment_id": str(equipment_id),
                "file_format": file_format.value,
                "raw_content": raw_content,
                "profile_id": profile_id,
                "test_execution_id": str(test_execution_id) if test_execution_id else None,
            }
        )
        is_replay, cached_status, cached_body = await idempotency_service.check_idempotency(
            db, client_id=client_id, key=idempotency_key, request_hash=req_hash
        )
        if is_replay and cached_body is not None:
            return JSONResponse(status_code=cached_status or 201, content=cached_body)

    record = await instrument_parser_service.upload_instrument_data(
        db,
        equipment_id=equipment_id,
        user_id=current_user.id,
        actor_username=current_user.username,
        file_name=file.filename or "instrument_data.raw",
        raw_content=raw_content,
        file_format=file_format,
        profile_id=profile_id,
        test_execution_id=test_execution_id,
    )
    out_model = InstrumentDataImportOut.model_validate(record)

    if idempotency_key:
        await idempotency_service.record_idempotency(
            db,
            client_id=client_id,
            key=idempotency_key,
            request_hash=req_hash,
            response_status=status.HTTP_201_CREATED,
            response_body=out_model.model_dump(mode="json"),
            ttl_seconds=idempotency_service.INSTRUMENT_IDEMPOTENCY_TTL_SECONDS,
            created_by_user_id=current_user.id,
        )

    return out_model


@router.post(
    "/upload-raw",
    response_model=InstrumentDataImportOut,
    status_code=status.HTTP_201_CREATED,
    summary="Ingestão de dados brutos de instrumento via JSON payload",
)
async def upload_raw_instrument_data(
    payload: RawUploadIn,
    db: DbSession,
    idempotency_key: Annotated[
        str | None,
        Header(alias="Idempotency-Key", description="Chave de idempotência (RFC 7231 / H3.1)"),
    ] = None,
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
):
    """Ingere conteúdo bruto de instrumento via corpo JSON estruturado."""
    client_id = (
        current_user._service_client.client_id
        if hasattr(current_user, "_service_client")
        else str(current_user.id)
    )

    if idempotency_key:
        req_hash = idempotency_service.compute_payload_hash(payload.model_dump(mode="json"))
        is_replay, cached_status, cached_body = await idempotency_service.check_idempotency(
            db, client_id=client_id, key=idempotency_key, request_hash=req_hash
        )
        if is_replay and cached_body is not None:
            return JSONResponse(status_code=cached_status or 201, content=cached_body)

    record = await instrument_parser_service.upload_instrument_data(
        db,
        equipment_id=payload.equipment_id,
        user_id=current_user.id,
        actor_username=current_user.username,
        file_name=payload.file_name,
        raw_content=payload.raw_content,
        file_format=payload.file_format,
        profile_id=payload.profile_id,
        test_execution_id=payload.test_execution_id,
    )
    out_model = InstrumentDataImportOut.model_validate(record)

    if idempotency_key:
        await idempotency_service.record_idempotency(
            db,
            client_id=client_id,
            key=idempotency_key,
            request_hash=req_hash,
            response_status=status.HTTP_201_CREATED,
            response_body=out_model.model_dump(mode="json"),
            ttl_seconds=idempotency_service.INSTRUMENT_IDEMPOTENCY_TTL_SECONDS,
            created_by_user_id=current_user.id,
        )

    return out_model


@router.get("/profiles", summary="Listar perfis declarativos de instrumentos (H3.3)")
async def list_profiles(
    _: CurrentUser,
) -> list[dict[str, Any]]:
    """Retorna os perfis declarativos de integração disponíveis para cromatógrafos e analisadores."""
    return [
        {
            "profile_id": p.profile_id,
            "name": p.name,
            "version": p.version,
            "instrument_category": p.instrument_category,
            "manufacturer": p.manufacturer,
            "model_regex": p.model_regex,
            "units": p.units,
        }
        for p in instrument_profiles.INSTRUMENT_PROFILES.values()
    ]


@router.get("", response_model=list[InstrumentDataImportOut])
async def list_instrument_imports(
    db: DbSession,
    _: CurrentUser,
    equipment_id: Annotated[UUID | None, Query(description="Filtrar por equipamento")] = None,
    test_execution_id: Annotated[
        UUID | None, Query(description="Filtrar por execução de ensaio")
    ] = None,
    import_status: Annotated[
        InstrumentImportStatus | None, Query(alias="status", description="Filtrar por status")
    ] = None,
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
