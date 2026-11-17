"""Testes automatizados do Horizonte 2 — Sprint 7.4: CEP Real e Regras de Westgard (H2.5)."""

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
    QCStatus,
    SampleStatus,
    TestOutcome,
    TestStatus,
)
from app.models.lab_test import LabTest
from app.models.test_method import TestMethod
from app.models.user import User
from app.schemas.official_report import OfficialReportGenerateIn
from app.schemas.qc_spc import QCRunCreate, QCRunResolve
from app.services import qc_spc_service, report_service

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


def test_westgard_rules_evaluation_unit() -> None:
    """Valida individualmente cada uma das 6 regras clássicas de Westgard."""
    # 1. Conforme
    status, viol = qc_spc_service.evaluate_westgard_rules([0.5, -0.2], 0.8)
    assert status == QCStatus.CONFORMING
    assert viol == []

    # 2. Regra 1_2s (Warning)
    status, viol = qc_spc_service.evaluate_westgard_rules([0.5], 2.2)
    assert status == QCStatus.WARNING
    assert "1_2s" in viol

    # 3. Regra 1_3s (Rejeição Randômica)
    status, viol = qc_spc_service.evaluate_westgard_rules([0.5], 3.2)
    assert status == QCStatus.REJECTED
    assert "1_3s" in viol

    # 4. Regra 2_2s (Rejeição Sistemática)
    status, viol = qc_spc_service.evaluate_westgard_rules([2.3], 2.1)
    assert status == QCStatus.REJECTED
    assert "2_2s" in viol

    # 5. Regra R_4s (Rejeição Randômica)
    status, viol = qc_spc_service.evaluate_westgard_rules([2.2], -2.1)
    assert status == QCStatus.REJECTED
    assert "R_4s" in viol

    # 6. Regra 4_1s (Rejeição Sistemática / Deslocamento)
    status, viol = qc_spc_service.evaluate_westgard_rules([1.2, 1.4, 1.3], 1.1)
    assert status == QCStatus.REJECTED
    assert "4_1s" in viol

    # 7. Regra 10_x (Rejeição por Viés / Drift)
    series_9 = [0.3] * 9
    status, viol = qc_spc_service.evaluate_westgard_rules(series_9, 0.4)
    assert status == QCStatus.REJECTED
    assert "10_x" in viol


@pytest.mark.asyncio
async def test_qc_run_creation_and_levey_jennings_chart_api(
    db_factory: async_sessionmaker[AsyncSession],
    client: AsyncClient,
    users: dict[str, dict[str, Any]],
) -> None:
    """Valida registro de corridas CQI e recuperação de dados da carta Levey-Jennings via API."""
    login_tecnico = await login(client, "tecnico", "Tecnico@Lims2026")
    headers = auth(login_tecnico["access_token"])

    # Cria método analítico no banco
    async with db_factory() as db:
        user_tecnico = await db.get(User, UUID(users["tecnico"]["id"]))
        assert user_tecnico is not None

        method = TestMethod(
            id=uuid4(),
            code=f"MET-SPC-{uuid4().hex[:4].upper()}",
            name="Determinação de Teor por HPLC-UV",
            category="Cromatografia Líquida",
            standard="USP 43-NF 38",
            is_active=True,
            attributes={"target_mean": 100.0, "target_sd": 2.0},
        )
        db.add(method)
        await db.commit()
        method_id = method.id

    # 1. Ponto 1: Conforme (100.5 -> z = +0.25)
    run1 = {
        "method_id": str(method_id),
        "target_mean": 100.0,
        "target_sd": 2.0,
        "measured_value": 100.5,
    }
    res1 = await client.post(f"{API}/spc/runs", json=run1, headers=headers)
    assert res1.status_code == 201
    assert res1.json()["status"] == QCStatus.CONFORMING.value

    # 2. Ponto 2: Rejeição 1_3s (106.5 -> z = +3.25)
    run2 = {
        "method_id": str(method_id),
        "target_mean": 100.0,
        "target_sd": 2.0,
        "measured_value": 106.5,
    }
    res2 = await client.post(f"{API}/spc/runs", json=run2, headers=headers)
    assert res2.status_code == 201
    data2 = res2.json()
    assert data2["status"] == QCStatus.REJECTED.value
    assert "1_3s" in data2["violation_rules"]
    assert data2["is_active_violation"] is True
    run2_id = data2["id"]

    # 3. Consulta da Carta de Levey-Jennings
    res_chart = await client.get(f"{API}/spc/methods/{method_id}/chart", headers=headers)
    assert res_chart.status_code == 200
    chart = res_chart.json()
    assert chart["total_runs"] == 2
    assert chart["active_rejections"] == 1
    assert chart["plus_3s"] == 106.0

    # 4. Solução da Violação com Parecer Corretivo
    resolve_payload = {
        "corrective_notes": "Recalibração do detector UV realizada e linha purgada com fase móvel nova.",
    }
    res_resolve = await client.post(
        f"{API}/spc/runs/{run2_id}/resolve", json=resolve_payload, headers=headers
    )
    assert res_resolve.status_code == 200
    assert res_resolve.json()["is_active_violation"] is False


@pytest.mark.asyncio
async def test_report_generation_interlocked_by_active_westgard_violation(
    db_factory: async_sessionmaker[AsyncSession],
    client: AsyncClient,
    users: dict[str, dict[str, Any]],
) -> None:
    """Garante que violação ativa de Westgard no método bloqueia a emissão de laudo oficial (ISO 17025 §7.7.1)."""
    async with db_factory() as db:
        user_tecnico = await db.get(User, UUID(users["tecnico"]["id"]))
        assert user_tecnico is not None

        method = TestMethod(
            id=uuid4(),
            code=f"MET-ILK-{uuid4().hex[:4].upper()}",
            name="Ensaio de Fluorescência de Lote",
            category="Espectroscopia",
            standard="ISO 10993-5",
            is_active=True,
            attributes={},
        )
        db.add(method)

        sample = DeviceSample(
            id=uuid4(),
            accession_number=f"AMO-SPC-{uuid4().hex[:4].upper()}",
            commercial_name="Fio Guia Hidrofílico",
            manufacturer="MedTech Brasil",
            status=SampleStatus.EM_TESTE,
            received_at=utcnow(),
            received_by_id=user_tecnico.id,
        )
        db.add(sample)

        test = LabTest(
            id=uuid4(),
            device_sample_id=sample.id,
            method_id=method.id,
            name="Ensaio de Fluorescência Residual",
            unit="RFU",
            status=TestStatus.CONCLUIDO,
            outcome=TestOutcome.APROVADO,
            result_value=12.5,
            review_status=CoordinationReviewStatus.APROVADO,
            assigned_to_id=user_tecnico.id,
            tested_by_id=user_tecnico.id,
            tested_at=utcnow(),
        )
        db.add(test)
        await db.commit()

        # 1. Registra corrida CQI Rejeitada (z = 3.5 > 3.0)
        cqi_payload = QCRunCreate(
            method_id=method.id,
            target_mean=50.0,
            target_sd=2.0,
            measured_value=57.0,  # z = +3.5 -> 1_3s ALARM
        )
        cqi_run = await qc_spc_service.record_qc_run(
            db,
            payload=cqi_payload,
            actor=user_tecnico,
            context=RequestContext(
                ip_address="127.0.0.1", user_agent="pytest", request_id="req-spc-1"
            ),
        )
        assert cqi_run.is_active_violation is True

        # 2. Tenta emitir laudo oficial -> BLOQUEIO POR WESTGARD (ISO 17025 §7.7.1)
        report_in = OfficialReportGenerateIn(
            device_sample_id=sample.id,
            test_ids=[test.id],
            notes="Tentativa de emissão sob violação ativa de CQI",
        )
        with pytest.raises(ValidationDomainError) as exc_info:
            await report_service.generate_official_report(
                db,
                payload=report_in,
                issuer=user_tecnico,
                signature_token=None,
                context=RequestContext(
                    ip_address="127.0.0.1", user_agent="pytest", request_id="req-spc-2"
                ),
            )
        assert "CEP/Westgard" in str(exc_info.value)
        assert "ISO/IEC 17025 §7.7.1" in str(exc_info.value)

        # 3. Soluciona a violação
        await qc_spc_service.resolve_qc_violation(
            db,
            run_id=cqi_run.id,
            payload=QCRunResolve(
                corrective_notes="Investigação concluída. Pipetador descalibrado substituído e lote re-validado."
            ),
            actor=user_tecnico,
            context=RequestContext(
                ip_address="127.0.0.1", user_agent="pytest", request_id="req-spc-3"
            ),
        )

        # 4. Agora a checagem de intertravamento do método deve retornar livre (False)
        is_blocked, block_msg = await qc_spc_service.check_method_has_active_violation(
            db, method.id
        )
        assert is_blocked is False
        assert block_msg is None
