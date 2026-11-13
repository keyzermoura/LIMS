"""Rotas de Gestão de Evidências e Anexos de Bancada (Sprint 3.3 / ALCOA+)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, File, Request, Response, UploadFile

from app.api.deps import CurrentUser, DbSession
from app.core.context import RequestContext
from app.schemas.test_attachment import TestAttachmentOut
from app.services import attachment_service

attachments_router = APIRouter(prefix="/attachments", tags=["Evidências e Anexos de Bancada"])


@attachments_router.post(
    "/tests/{test_id}",
    response_model=TestAttachmentOut,
    summary="Fazer upload de evidência bruta de bancada para o ensaio",
)
async def upload_test_attachment(
    test_id: UUID,
    request: Request,
    response: Response,
    db: DbSession,
    user: CurrentUser,
    file: UploadFile = File(...),
) -> TestAttachmentOut:
    context = RequestContext.from_request(request)
    file_bytes = await file.read()
    attachment, audit_seq = await attachment_service.upload_attachment(
        db,
        test_id=test_id,
        filename=file.filename or "evidence.bin",
        file_bytes=file_bytes,
        content_type=file.content_type or "application/octet-stream",
        actor=user,
        context=context,
    )
    response.headers["X-Audit-Sequence"] = str(audit_seq)
    return TestAttachmentOut.model_validate(attachment)


@attachments_router.get(
    "/tests/{test_id}",
    response_model=list[TestAttachmentOut],
    summary="Listar evidências anexadas ao ensaio",
)
async def list_test_attachments(
    test_id: UUID,
    db: DbSession,
    _: CurrentUser,
) -> list[TestAttachmentOut]:
    attachments = await attachment_service.list_attachments_for_test(db, test_id)
    return [TestAttachmentOut.model_validate(a) for a in attachments]


@attachments_router.get(
    "/{attachment_id}/download",
    summary="Baixar evidência bruta de bancada",
)
async def download_test_attachment(
    attachment_id: UUID,
    db: DbSession,
    _: CurrentUser,
) -> Response:
    attachment = await attachment_service.get_attachment(db, attachment_id)
    return Response(
        content=attachment.file_data,
        media_type=attachment.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{attachment.filename}"',
            "X-SHA256-Checksum": attachment.sha256_hash,
        },
    )
