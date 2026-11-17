"""Testes automatizados das funcionalidades do Roadmap v1.1.0:

1. Lookup de amostras por código de barras / accession / lote (H3.3)
2. Emissão e manifesto agregado em lote de laudos periciais (Batch Official Reports)
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.context import RequestContext
from app.core.errors import NotFoundError
from app.models.device_sample import DeviceSample
from app.models.enums import (
    CoordinationReviewStatus,
    SampleStatus,
    SignatureAction,
    SignatureMeaning,
    UserRole,
)
from app.models.enums import TestOutcome as DomainOutcome
from app.models.enums import TestStatus as DomainTestStatus
from app.models.lab_test import LabTest
from app.models.user import User
from app.schemas.official_report import OfficialReportBatchIn, OfficialReportBatchItemIn
from app.services import report_service, sample_service, signature_service
from app.services.auth_service import hash_password


@pytest.mark.asyncio
async def test_sample_lookup_by_barcode_accession_and_serial(
    db_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with db_factory() as db:
        user = User(
            id=uuid4(),
            username=f"tecnico_{uuid4().hex[:6]}",
            email=f"tecnico_{uuid4().hex[:6]}@lims.gov.br",
            full_name="Tecnico Recebedor",
            role=UserRole.TECNICO,
            hashed_password=hash_password("Tecnico@Lims2026"),
            is_active=True,
        )
        db.add(user)
        await db.flush()

        unique_acc = f"BARCODE-{uuid4().hex[:8].upper()}"
        unique_serial = f"SN-{uuid4().hex[:6].upper()}"
        unique_lot = f"LOT-{uuid4().hex[:6].upper()}"

        sample = DeviceSample(
            id=uuid4(),
            accession_number=unique_acc,
            serial_number=unique_serial,
            lot_number=unique_lot,
            manufacturer="B. Braun Melsungen AG",
            commercial_name="Cateter de Balão Coronário PTCA",
            model="SeQuent Please",
            status=SampleStatus.RECEBIDO,
            received_by_id=user.id,
        )
        db.add(sample)
        await db.commit()

        # Busca por accession
        found_acc = await sample_service.get_sample_by_barcode(db, unique_acc)
        assert found_acc.id == sample.id

        # Busca por serial
        found_sn = await sample_service.get_sample_by_barcode(db, unique_serial)
        assert found_sn.id == sample.id

        # Busca por lote
        found_lot = await sample_service.get_sample_by_barcode(db, unique_lot)
        assert found_lot.id == sample.id

        # Busca inexistente levanta NotFoundError
        with pytest.raises(NotFoundError):
            await sample_service.get_sample_by_barcode(db, "INEXISTENTE-999")


@pytest.mark.asyncio
async def test_batch_official_reports_generation(
    db_factory: async_sessionmaker[AsyncSession],
    users: dict[str, Any],
) -> None:
    async with db_factory() as db:
        issuer = User(
            id=uuid4(),
            username=f"fiscal_batch_{uuid4().hex[:6]}",
            email=f"fiscal_batch_{uuid4().hex[:6]}@lims.gov.br",
            full_name="Fiscal Auditor Lote",
            role=UserRole.FISCAL,
            hashed_password=hash_password("Fiscal@Lims2026"),
            is_active=True,
        )
        db.add(issuer)
        await db.flush()

        sample1 = DeviceSample(
            id=uuid4(),
            accession_number=f"LIMS-BATCH-1-{uuid4().hex[:6]}",
            manufacturer="Fabricante 1",
            commercial_name="Bomba de Seringa Alaris",
            status=SampleStatus.EM_TESTE,
            received_by_id=issuer.id,
        )
        sample2 = DeviceSample(
            id=uuid4(),
            accession_number=f"LIMS-BATCH-2-{uuid4().hex[:6]}",
            manufacturer="Fabricante 2",
            commercial_name="Desfibrilador Externo HeartStart",
            status=SampleStatus.EM_TESTE,
            received_by_id=issuer.id,
        )
        db.add_all([sample1, sample2])
        await db.flush()

        test1 = LabTest(
            id=uuid4(),
            device_sample_id=sample1.id,
            name="Teste de Oclusão",
            unit="ml/h",
            status=DomainTestStatus.CONCLUIDO,
            review_status=CoordinationReviewStatus.APROVADO,
            result_value=12.0,
            outcome=DomainOutcome.APROVADO,
            tested_by_id=issuer.id,
        )
        test2 = LabTest(
            id=uuid4(),
            device_sample_id=sample2.id,
            name="Descarga de Energia",
            unit="J",
            status=DomainTestStatus.CONCLUIDO,
            review_status=CoordinationReviewStatus.APROVADO,
            result_value=200.0,
            outcome=DomainOutcome.APROVADO,
            tested_by_id=issuer.id,
        )
        db.add_all([test1, test2])
        await db.commit()

        context = RequestContext(
            ip_address="127.0.0.1",
            user_agent="pytest/batch",
            request_id="test-batch-001",
        )

        _, token = await signature_service.issue(
            db,
            user=issuer,
            password="Fiscal@Lims2026",
            meaning=SignatureMeaning.RESPONSABILIDADE_TECNICA,
            reason="Homologação e assinatura pericial de laudo oficial em lote",
            entity_type="BatchReport",
            entity_id="batch-001",
            action=SignatureAction.CLOSE,
            context=context,
        )

        batch_payload = OfficialReportBatchIn(
            items=[
                OfficialReportBatchItemIn(
                    device_sample_id=sample1.id,
                    test_ids=[test1.id],
                    title="Laudo Pericial Lote 1",
                    conclusion=DomainOutcome.APROVADO,
                    summary="Amostra 1 aprovada nos ensaios mecânicos.",
                ),
                OfficialReportBatchItemIn(
                    device_sample_id=sample2.id,
                    test_ids=[test2.id],
                    title="Laudo Pericial Lote 2",
                    conclusion=DomainOutcome.APROVADO,
                    summary="Amostra 2 aprovada nos ensaios elétricos.",
                ),
            ],
            batch_reason="Emissão em lote para fiscalização pós-mercado",
        )

        batch_out, audit_seq = await report_service.generate_batch_official_reports(
            db,
            payload=batch_payload,
            issuer=issuer,
            signature_token=token,
            context=context,
        )

        assert batch_out.total_requested == 2
        assert batch_out.total_issued == 2
        assert len(batch_out.reports) == 2
        assert batch_out.batch_manifest_hash is not None
        assert len(batch_out.batch_manifest_hash) == 64
        assert batch_out.reports[0].report_number != batch_out.reports[1].report_number
