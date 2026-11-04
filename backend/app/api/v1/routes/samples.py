"""Rotas de amostras: entrada, QR Code, timeline e status."""

from __future__ import annotations

import io
from uuid import UUID

import qrcode
from fastapi import APIRouter, Depends, Query, Request, Response, status
from fastapi.responses import StreamingResponse

from app.api.deps import (
    CurrentUser,
    DbSession,
    SignatureToken,
    require_roles,
    require_signature,
)
from app.core.config import settings
from app.core.context import RequestContext
from app.core.errors import ValidationDomainError
from app.core.security import TokenError, sign_qr_payload, verify_qr_payload
from app.models.device_sample import DeviceSample
from app.models.electronic_signature import ElectronicSignature
from app.models.enums import SampleStatus, SignatureAction, UserRole
from app.models.user import User
from app.schemas.common import Page
from app.schemas.sample import (
    CustodyOut,
    EventSignatureOut,
    SampleCreate,
    SampleCreateResponse,
    SampleOut,
    SampleQrOut,
    SampleStatusChangeOut,
    SampleStatusUpdate,
    SampleVerifyOut,
    TimelineEvent,
)
from app.services import custody_service, sample_service, signature_service

router = APIRouter(prefix="/samples", tags=["Amostras e Cadeia de Custódia"])

WRITE_ROLES = (UserRole.ADMIN, UserRole.FISCAL, UserRole.TECNICO)


@router.post(
    "",
    response_model=SampleCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar entrada de dispositivo médico",
    description=(
        "Gera o número de accession e o QR Code assinado (HMAC). "
        "Exige assinatura eletrônica vinculada ao `id` informado no corpo."
    ),
)
async def create_sample(
    payload: SampleCreate,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    token: SignatureToken,
    _role: User = Depends(require_roles(*WRITE_ROLES)),
) -> SampleCreateResponse:
    signature = await signature_service.consume(
        db,
        token=token,
        user=user,
        entity_type="DeviceSample",
        entity_id=str(payload.id),
        action=SignatureAction.CREATE,
        context=RequestContext.from_request(request),
    )
    sample, audit_id = await sample_service.create_sample(
        db,
        payload=payload,
        actor=user,
        signature=signature,
        context=RequestContext.from_request(request),
    )
    return SampleCreateResponse(
        sample=SampleOut.model_validate(sample),
        audit_log_id=audit_id,
        signature_id=signature.id,
        qr_code_url=f"{settings.API_V1_PREFIX}/samples/{sample.id}/qrcode.png",
    )


@router.get("", response_model=Page[SampleOut], summary="Listar amostras")
async def list_samples(
    db: DbSession,
    user: CurrentUser,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    sample_status: SampleStatus | None = Query(None, alias="status"),
    search: str | None = Query(None, max_length=120),
) -> Page[SampleOut]:
    items, total = await sample_service.list_samples(
        db, page=page, size=size, status=sample_status, search=search
    )
    return Page[SampleOut].build(
        [SampleOut.model_validate(item) for item in items], total, page, size
    )


@router.get(
    "/verify",
    response_model=SampleVerifyOut,
    summary="Validar QR Code de uma amostra",
)
async def verify_qr(token: str, db: DbSession, user: CurrentUser) -> SampleVerifyOut:
    try:
        claims = verify_qr_payload(token)
    except TokenError as exc:
        raise ValidationDomainError(str(exc)) from exc

    sample = await db.get(DeviceSample, UUID(claims["sub"]))
    if sample is None:
        raise ValidationDomainError("QR Code não corresponde a uma amostra existente.")

    return SampleVerifyOut(
        valid=sample.accession_number == claims["acc"],
        id=sample.id,
        accession_number=sample.accession_number,
        serial_number=sample.serial_number,
        lot_number=sample.lot_number,
        manufacturer=sample.manufacturer,
        commercial_name=sample.commercial_name,
        status=sample.status,
    )


@router.get("/{sample_id}", response_model=SampleOut, summary="Detalhar amostra")
async def get_sample(sample_id: UUID, db: DbSession, user: CurrentUser) -> SampleOut:
    sample = await sample_service.get_sample(db, sample_id)
    return SampleOut.model_validate(sample)


@router.get(
    "/{sample_id}/timeline",
    response_model=list[TimelineEvent],
    summary="Timeline de entrada e cadeia de custódia",
)
async def sample_timeline(
    sample_id: UUID, db: DbSession, user: CurrentUser
) -> list[TimelineEvent]:
    events = await sample_service.timeline(db, sample_id)
    return [TimelineEvent.model_validate(event) for event in events]


@router.get(
    "/{sample_id}/custody",
    response_model=list[CustodyOut],
    summary="Histórico de custódia",
)
async def custody_history(
    sample_id: UUID, db: DbSession, user: CurrentUser
) -> list[CustodyOut]:
    events = await custody_service.history(db, sample_id)
    return [CustodyOut.model_validate(event) for event in events]


@router.get(
    "/{sample_id}/signatures",
    response_model=list[EventSignatureOut],
    summary="Manifestos de assinatura vinculados à amostra",
)
async def sample_signatures(
    sample_id: UUID, db: DbSession, user: CurrentUser
) -> list[EventSignatureOut]:
    await sample_service.get_sample(db, sample_id)
    rows = await signature_service.consumed_signatures_for(
        db, "DeviceSample", str(sample_id)
    )
    return [
        EventSignatureOut(
            signature_id=row.id,
            signer_full_name=row.full_name_snapshot,
            signer_role=row.role_snapshot,
            meaning=row.meaning.value,
            reason=row.reason,
            signed_at=row.signed_at,
            manifest_hash=row.manifest_hash,
        )
        for row in rows
    ]


@router.get(
    "/{sample_id}/qrcode",
    response_model=SampleQrOut,
    summary="QR Code lógico assinado",
)
async def sample_qr(sample_id: UUID, db: DbSession, user: CurrentUser) -> SampleQrOut:
    sample = await sample_service.get_sample(db, sample_id)
    token = sign_qr_payload(sample.id, sample.accession_number)
    return SampleQrOut(
        token=token,
        accession_number=sample.accession_number,
        image_url=f"{settings.API_V1_PREFIX}/samples/{sample.id}/qrcode.png",
        verify_url=f"{settings.API_V1_PREFIX}/samples/verify?token={token}",
    )


@router.get(
    "/{sample_id}/qrcode.png",
    response_class=Response,
    summary="Imagem PNG do QR Code (para etiqueta)",
    responses={200: {"content": {"image/png": {}}}},
)
async def sample_qr_png(
    sample_id: UUID, db: DbSession, user: CurrentUser
) -> StreamingResponse:
    sample = await sample_service.get_sample(db, sample_id)
    token = sign_qr_payload(sample.id, sample.accession_number)

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(token)
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="image/png",
        headers={
            "Cache-Control": "no-store",
            "Content-Disposition": f'inline; filename="{sample.accession_number}.png"',
        },
    )


@router.patch(
    "/{sample_id}/status",
    response_model=SampleStatusChangeOut,
    summary="Alterar status da amostra (assinado)",
)
async def change_status(
    sample_id: UUID,
    payload: SampleStatusUpdate,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    signature: ElectronicSignature = Depends(
        require_signature(
            entity_type="DeviceSample",
            action=SignatureAction.UPDATE,
            id_param="sample_id",
        )
    ),
    _role: User = Depends(require_roles(*WRITE_ROLES)),
) -> SampleStatusChangeOut:
    sample, previous, audit_id = await sample_service.update_status(
        db,
        sample_id=sample_id,
        payload=payload,
        actor=user,
        signature=signature,
        context=RequestContext.from_request(request),
    )
    return SampleStatusChangeOut(
        sample=SampleOut.model_validate(sample),
        previous_status=previous,
        audit_log_id=audit_id,
    )
