"""Testes automatizados do Horizonte 2 — Sprint 7.1: Reagentes, Padrões Analíticos (CRMs) e Intertravamento (H2.1)."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.base import utcnow
from app.models.device_sample import DeviceSample
from app.models.enums import (
    CoordinationReviewStatus,
    ReagentBatchStatus,
    SampleStatus,
    TestOutcome,
    TestStatus,
)
from app.models.lab_test import LabTest
from app.models.reagent import ReagentBatch
from app.models.test_execution import TestExecution

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


async def create_sample_and_execution(
    db_factory: async_sessionmaker[AsyncSession],
    user_id: UUID,
) -> tuple[UUID, UUID]:
    """Cria amostra, ensaio e execução de teste para consumo em bancada."""
    sample_id = uuid4()
    test_id = uuid4()
    execution_id = uuid4()

    async with db_factory() as db:
        sample = DeviceSample(
            id=sample_id,
            accession_number=f"BR-2026-H2-{uuid4().hex[:4].upper()}",
            commercial_name="Stent Coronário Farmacoativo",
            manufacturer="Inova Med Ltda",
            lot_number="LOT-H2-990",
            serial_number="SN-H2-001",
            status=SampleStatus.EM_TESTE,
            received_by_id=user_id,
        )
        db.add(sample)

        test = LabTest(
            id=test_id,
            device_sample_id=sample_id,
            name="Ensaio de Teor de Sirolimus por HPLC",
            unit="mg/g",
            lower_limit=90.0,
            upper_limit=110.0,
            result_value=None,
            outcome=TestOutcome.APROVADO,
            status=TestStatus.PENDENTE,
            review_status=CoordinationReviewStatus.PENDENTE,
            tested_at=utcnow(),
        )
        db.add(test)

        execution = TestExecution(
            id=execution_id,
            lab_test_id=test_id,
            executed_by_id=user_id,
            started_at=utcnow(),
            raw_data={"parameters": {"flow_rate": "1.0 mL/min"}},
        )
        db.add(execution)
        await db.commit()

    return sample_id, execution_id


@pytest.mark.asyncio
async def test_reagents_and_crm_catalog_lifecycle(
    client: AsyncClient,
    users: dict[str, dict[str, Any]],
) -> None:
    """Valida o cadastro de reagentes químicos e padrões certificados (CRM) com metrologia."""
    login_data = await login(client, "admin", "Admin@Lims2026")
    token = login_data["access_token"]

    # 1. Cadastrar Padrão Primário Certificado (CRM)
    crm_payload = {
        "code": f"CRM-{uuid4().hex[:4].upper()}",
        "name": "Padrão Primário de Sirolimus USP",
        "chemical_formula": "C51H79NO13",
        "cas_number": "53123-88-9",
        "reagent_type": "PRIMARY_STANDARD_CRM",
        "grade": "USP",
        "storage_temperature_min": -25.0,
        "storage_temperature_max": -15.0,
        "hazard_classification": "Tóxico / Manuseio em Capela",
    }
    crm_res = await client.post(f"{API}/reagents", headers=auth(token), json=crm_payload)
    assert crm_res.status_code == 201, crm_res.text
    crm_data = crm_res.json()
    crm_id = crm_data["id"]
    assert crm_data["code"] == crm_payload["code"]
    assert crm_data["reagent_type"] == "PRIMARY_STANDARD_CRM"

    # 2. Entrada de Lote do CRM com Certificado e Incerteza
    today = date.today()
    batch_payload = {
        "lot_number": "LOT-USP-2026-X1",
        "manufacturer": "USP Reference Standards",
        "catalog_number": "USP-1614300",
        "expiration_date": (today + timedelta(days=365)).isoformat(),
        "initial_quantity": 250.0,
        "unit": "mg",
        "certificate_number": "CERT-USP-998877",
        "uncertainty_value": 0.008,
        "k_factor": 2.0,
        "notes": "Armazenado no ultrafreezer -20C da toxicologia",
    }
    batch_res = await client.post(
        f"{API}/reagents/{crm_id}/batches", headers=auth(token), json=batch_payload
    )
    assert batch_res.status_code == 201, batch_res.text
    batch_data = batch_res.json()
    assert batch_data["certificate_number"] == "CERT-USP-998877"
    assert batch_data["status"] == "AVAILABLE"
    assert batch_data["is_usable"] is True
    assert batch_data["is_expired"] is False


@pytest.mark.asyncio
async def test_reagent_interlock_blocks_expired_and_insufficient_stock(
    client: AsyncClient,
    users: dict[str, dict[str, Any]],
    db_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Garante o intertravamento regulamentar ISO 17025 §6.4: rejeita consumo de insumo vencido ou sem saldo."""
    login_data = await login(client, "admin", "Admin@Lims2026")
    token = login_data["access_token"]
    user_id = UUID(login_data["user"]["id"])

    _, execution_id = await create_sample_and_execution(db_factory, user_id)

    # 1. Cadastrar reagente comum
    reagent_res = await client.post(
        f"{API}/reagents",
        headers=auth(token),
        json={
            "code": f"SOLV-{uuid4().hex[:4].upper()}",
            "name": "Acetonitrila Grau HPLC",
            "reagent_type": "SOLVENT",
            "grade": "HPLC",
        },
    )
    assert reagent_res.status_code == 201
    reagent_id = reagent_res.json()["id"]

    today = date.today()

    # 2. Entrada de Lote VENCIDO
    expired_batch_res = await client.post(
        f"{API}/reagents/{reagent_id}/batches",
        headers=auth(token),
        json={
            "lot_number": "LOT-VENCIDO-99",
            "manufacturer": "Merck",
            "expiration_date": (today - timedelta(days=10)).isoformat(),
            "initial_quantity": 1000.0,
            "unit": "mL",
        },
    )
    assert expired_batch_res.status_code == 201
    expired_batch_id = expired_batch_res.json()["id"]
    assert expired_batch_res.json()["is_expired"] is True

    # 3. Tentativa de consumir lote VENCIDO deve ser bloqueada com 422
    consume_expired_res = await client.post(
        f"{API}/reagents/executions/{execution_id}/consume",
        headers=auth(token),
        json={
            "batch_id": expired_batch_id,
            "quantity_used": 50.0,
            "unit": "mL",
        },
    )
    assert consume_expired_res.status_code == 422, consume_expired_res.text
    assert "expirou" in consume_expired_res.json()["detail"].lower()
    assert "17025" in consume_expired_res.json()["detail"]

    # 4. Entrada de Lote VÁLIDO com saldo restrito (10 mL)
    valid_batch_res = await client.post(
        f"{API}/reagents/{reagent_id}/batches",
        headers=auth(token),
        json={
            "lot_number": "LOT-VALIDO-01",
            "manufacturer": "Merck",
            "expiration_date": (today + timedelta(days=180)).isoformat(),
            "initial_quantity": 10.0,
            "unit": "mL",
        },
    )
    assert valid_batch_res.status_code == 201
    valid_batch_id = valid_batch_res.json()["id"]

    # 5. Tentativa de consumir quantidade SUPERIOR ao saldo deve ser bloqueada com 422
    overflow_res = await client.post(
        f"{API}/reagents/executions/{execution_id}/consume",
        headers=auth(token),
        json={
            "batch_id": valid_batch_id,
            "quantity_used": 15.0,
            "unit": "mL",
        },
    )
    assert overflow_res.status_code == 422
    assert "insuficiente" in overflow_res.json()["detail"].lower()

    # 6. Consumo com sucesso de 4.0 mL
    good_consume_res = await client.post(
        f"{API}/reagents/executions/{execution_id}/consume",
        headers=auth(token),
        json={
            "batch_id": valid_batch_id,
            "quantity_used": 4.0,
            "unit": "mL",
        },
    )
    assert good_consume_res.status_code == 201
    usage_data = good_consume_res.json()
    assert usage_data["quantity_used"] == 4.0
    assert usage_data["batch_id"] == valid_batch_id

    # 7. Conferir baixa de saldo no banco (10.0 - 4.0 = 6.0)
    async with db_factory() as db:
        batch_db = await db.get(ReagentBatch, UUID(valid_batch_id))
        assert batch_db is not None
        assert batch_db.current_quantity == 6.0
        assert batch_db.status == ReagentBatchStatus.IN_USE
        assert batch_db.opened_at is not None
