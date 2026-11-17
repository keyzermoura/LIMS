"""Testes automatizados do Horizonte 2 — Sprint 7.2: Desvios Analíticos OOS/OOT e Intertravamento (H2.2)."""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.context import RequestContext
from app.core.errors import ValidationDomainError
from app.models.base import utcnow
from app.models.device_sample import DeviceSample
from app.models.enums import (
    CoordinationReviewStatus,
    DeviationType,
    OOSInvestigationStatus,
    SampleStatus,
    TestOutcome,
    TestStatus,
)
from app.models.lab_test import LabTest
from app.models.oos_investigation import OOSInvestigation
from app.models.test_execution import TestExecution
from app.models.user import User
from app.schemas.official_report import OfficialReportGenerateIn
from app.schemas.oos_investigation import (
    OOSInvestigationCreate,
)
from app.services import oos_service, report_service

API = "/api/v1"


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def login(client: AsyncClient, username: str, password: str) -> dict[str, Any]:
    res = await client.post(
        f"{API}/auth/login",
        data={"username": username, "password": password},
    )
    assert res.status_code == 200, res.text
    return res.json()


@pytest.mark.asyncio
async def test_oos_two_phase_investigation_and_capa_link(
    db_factory: async_sessionmaker[AsyncSession],
    client: AsyncClient,
    users: dict[str, dict[str, Any]],
) -> None:
    """Valida o ciclo completo de investigação OOS em duas fases e criação automática de CAPA."""
    login_data = await login(client, "tecnico", "Tecnico@Lims2026")
    token = login_data["access_token"]

    async with db_factory() as db:
        user_tecnico = await db.get(User, UUID(users["tecnico"]["id"]))
        assert user_tecnico is not None

        sample = DeviceSample(
            id=uuid4(),
            accession_number=f"AMO-OOS-{uuid4().hex[:4].upper()}",
            commercial_name="Cateter Guia Hidrofílico",
            manufacturer="Inova Med Ltda",
            status=SampleStatus.EM_TESTE,
            received_at=utcnow(),
            received_by_id=user_tecnico.id,
        )
        db.add(sample)

        test = LabTest(
            id=uuid4(),
            device_sample_id=sample.id,
            name="Teor de Revestimento Hidrofílico",
            unit="mg/cm2",
            lower_limit=10.0,
            upper_limit=25.0,
            result_value=7.5,  # Abaixo de 10.0 -> Fora de Especificação (OOS)
            outcome=TestOutcome.REPROVADO,
            status=TestStatus.PENDENTE,
            review_status=CoordinationReviewStatus.PENDENTE,
            tested_by_id=user_tecnico.id,
        )
        db.add(test)

        execution = TestExecution(
            id=uuid4(),
            lab_test_id=test.id,
            executed_by_id=user_tecnico.id,
            started_at=utcnow(),
            raw_data={"absorbance": 0.12},
        )
        db.add(execution)
        await db.commit()

        context = RequestContext(
            ip_address="127.0.0.1",
            user_agent="pytest",
            request_id="test-req-oos-1",
        )

        # 1. Abertura formal da investigação OOS
        create_payload = OOSInvestigationCreate(
            lab_test_id=test.id,
            execution_id=execution.id,
            deviation_type=DeviationType.OOS,
            initial_result=7.5,
            specification_min=10.0,
            specification_max=25.0,
        )
        inv = await oos_service.create_investigation(
            db, payload=create_payload, actor=user_tecnico, context=context
        )
        assert inv.investigation_number.startswith("OOS-")
        assert inv.status == OOSInvestigationStatus.PHASE_I_PENDING
        assert inv.initial_result == 7.5
        inv_id = inv.id

    # 2. Execução da Fase I via API REST (Investigação Laboratorial Imediata)
    phase1_payload = {
        "calculation_verified": True,
        "instrument_verified": True,
        "reagent_verified": True,
        "analyst_interviewed": True,
        "sample_integrity_verified": True,
        "checklist_notes": "Diluições conferidas, espectrofotômetro calibrado e padrões PA válidos.",
        "phase_1_conclusion": "Nenhum erro de laboratório identificado. Encaminhado para re-ensaio Fase II.",
        "phase_2_required": True,
    }
    res_p1 = await client.put(
        f"{API}/oos/{inv_id}/phase1",
        json=phase1_payload,
        headers=auth(token),
    )
    assert res_p1.status_code == 200, res_p1.text
    p1_data = res_p1.json()
    assert p1_data["status"] == "PHASE_II_REQUIRED"
    assert p1_data["phase_2_required"] is True

    # 3. Execução da Fase II via API REST (Re-ensaio e Determinação de Causa Raiz)
    phase2_payload = {
        "phase_2_plan": "Re-ensaio em triplicata por analista sênior com novo preparo.",
        "retest_results": [
            {
                "retest_number": 1,
                "analyst_name": "Especialista Metrologia",
                "result_value": 7.4,
                "outcome": "REPROVADO",
                "retest_date": "2026-11-17",
            },
            {
                "retest_number": 2,
                "analyst_name": "Especialista Metrologia",
                "result_value": 7.6,
                "outcome": "REPROVADO",
                "retest_date": "2026-11-17",
            },
        ],
        "root_cause_category": "SAMPLE_ANOMALY",
        "root_cause_description": "Espessura da camada polimérica insuficiente por falha na extrusão do fabricante.",
        "confirmed_status": "CONFIRMED_PRODUCT_FAILURE",
        "auto_create_capa": True,
    }
    res_p2 = await client.put(
        f"{API}/oos/{inv_id}/phase2",
        json=phase2_payload,
        headers=auth(token),
    )
    assert res_p2.status_code == 200, res_p2.text
    p2_data = res_p2.json()
    assert p2_data["status"] == "CONFIRMED_PRODUCT_FAILURE"
    assert p2_data["capa_action_id"] is not None  # CAPA gerada automaticamente

    # 4. Encerramento formal via API REST (Coordenação/Fiscal)
    login_admin = await login(client, "admin", "Admin@Lims2026")
    admin_token = login_admin["access_token"]

    close_payload = {
        "final_disposition": "Investigação concluída. Lote interditado sanitariamente e CAPA instaurada.",
    }
    res_close = await client.post(
        f"{API}/oos/{inv_id}/close",
        json=close_payload,
        headers=auth(admin_token),
    )
    assert res_close.status_code == 200, res_close.text
    close_data = res_close.json()
    assert close_data["status"] == "CLOSED"
    assert close_data["final_disposition"] is not None


@pytest.mark.asyncio
async def test_report_service_blocks_when_open_oos_exists(
    db_factory: async_sessionmaker[AsyncSession],
    users: dict[str, dict[str, Any]],
) -> None:
    """Valida o intertravamento regulamentar ISO 17025 §7.10: bloqueia laudo com OOS em aberto."""
    async with db_factory() as db:
        user_tecnico = await db.get(User, UUID(users["tecnico"]["id"]))
        assert user_tecnico is not None

        sample = DeviceSample(
            id=uuid4(),
            accession_number=f"AMO-INTERLOCK-{uuid4().hex[:4].upper()}",
            commercial_name="Prótese Valvar Biológica",
            manufacturer="Biomedical SA",
            status=SampleStatus.EM_TESTE,
            received_at=utcnow(),
            received_by_id=user_tecnico.id,
        )
        db.add(sample)

        test = LabTest(
            id=uuid4(),
            device_sample_id=sample.id,
            name="Ensaio de Fadiga Hidrodinâmica",
            unit="ciclos",
            lower_limit=1000000.0,
            result_value=1200000.0,
            outcome=TestOutcome.APROVADO,
            status=TestStatus.CONCLUIDO,
            review_status=CoordinationReviewStatus.APROVADO,
            tested_by_id=user_tecnico.id,
        )
        db.add(test)

        # Cria investigação OOS pendente para este ensaio
        oos = OOSInvestigation(
            investigation_number=f"OOS-2026-{uuid4().hex[:4].upper()}",
            lab_test_id=test.id,
            deviation_type=DeviationType.OOS,
            status=OOSInvestigationStatus.PHASE_I_PENDING,
            initial_result=950000.0,
            detected_by_id=user_tecnico.id,
            detected_at=utcnow(),
            phase_1_checklist={},
            phase_2_required=False,
            phase_2_retest_results=[],
        )
        db.add(oos)
        await db.commit()

        context = RequestContext(
            ip_address="127.0.0.1",
            user_agent="pytest",
            request_id="test-req-interlock-1",
        )

        # Tentativa de gerar laudo oficial com ensaio em OOS aberta deve lançar ValidationDomainError
        report_in = OfficialReportGenerateIn(
            device_sample_id=sample.id,
            test_ids=[test.id],
            notes="Tentativa de emissão de laudo",
        )

        with pytest.raises(ValidationDomainError) as exc_info:
            await report_service.generate_official_report(
                db,
                payload=report_in,
                issuer=user_tecnico,
                context=context,
            )

        assert "investigação de desvio analítico OOS pendente" in str(exc_info.value)
        assert "ISO/IEC 17025 §7.10" in str(exc_info.value)
