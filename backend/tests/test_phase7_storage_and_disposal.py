"""Testes automatizados do Horizonte 2 — Sprint 7.3: Cadeia Física, Contraprova e Descarte (H2.3 & H2.4)."""

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
    RetentionStatus,
    RetentionType,
    SampleStatus,
    SignatureAction,
    SignatureMeaning,
    StorageLocationType,
)
from app.models.user import User

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
async def test_storage_location_management_and_constraints(
    client: AsyncClient,
    users: dict[str, dict[str, Any]],
) -> None:
    """Valida cadastro de locais de custódia e validações térmicas e de capacidade."""
    login_tecnico = await login(client, "tecnico", "Tecnico@Lims2026")
    headers_tecnico = auth(login_tecnico["access_token"])

    # 1. Rejeição de limites térmicos incoerentes (min > max)
    invalid_payload = {
        "code": "INV-FRZ-01",
        "name": "Freezer Incoerente",
        "location_type": StorageLocationType.ULTRA_FREEZER.value,
        "room": "Sala 101",
        "temperature_target_celsius": -80.0,
        "temperature_min_celsius": -70.0,
        "temperature_max_celsius": -86.0,  # min > max!
        "capacity_units": 50,
    }
    res_inv = await client.post(
        f"{API}/storage/locations", json=invalid_payload, headers=headers_tecnico
    )
    assert res_inv.status_code == 422

    # 2. Cadastro válido de Ultra Freezer -80ºC
    valid_freezer = {
        "code": f"FRZ-80-{uuid4().hex[:4].upper()}",
        "name": "Ultra Freezer Bio 01",
        "location_type": StorageLocationType.ULTRA_FREEZER.value,
        "room": "Criobiologia Central",
        "temperature_target_celsius": -80.0,
        "temperature_min_celsius": -86.0,
        "temperature_max_celsius": -70.0,
        "humidity_max_percent": 60.0,
        "capacity_units": 100,
        "metadata": {"rack_count": 4, "boxes_per_rack": 16},
    }
    res_frz = await client.post(
        f"{API}/storage/locations", json=valid_freezer, headers=headers_tecnico
    )
    assert res_frz.status_code == 201, res_frz.text
    frz_data = res_frz.json()
    assert frz_data["code"] == valid_freezer["code"]
    assert frz_data["current_occupancy"] == 0

    # 3. Listagem de locais
    res_list = await client.get(f"{API}/storage/locations", headers=headers_tecnico)
    assert res_list.status_code == 200
    locations = res_list.json()
    assert any(loc["code"] == valid_freezer["code"] for loc in locations)

    # 4. Dashboard de resumo
    res_summary = await client.get(f"{API}/storage/summary", headers=headers_tecnico)
    assert res_summary.status_code == 200
    summary = res_summary.json()
    assert summary["total_locations"] >= 1


@pytest.mark.asyncio
async def test_sample_movement_and_thermal_excursion_alert(
    db_factory: async_sessionmaker[AsyncSession],
    client: AsyncClient,
    users: dict[str, dict[str, Any]],
) -> None:
    """Valida movimentações físicas de amostra e registro de excursão térmica (ISO 17025 §7.4.3)."""
    login_tecnico = await login(client, "tecnico", "Tecnico@Lims2026")
    headers_tecnico = auth(login_tecnico["access_token"])

    # Cria local de armazenamento com limites estritos (2.0 a 8.0 °C)
    loc_payload = {
        "code": f"REF-28-{uuid4().hex[:4].upper()}",
        "name": "Geladeira de Imunoensaio",
        "location_type": StorageLocationType.REFRIGERATOR.value,
        "room": "Bancada Central",
        "temperature_target_celsius": 4.0,
        "temperature_min_celsius": 2.0,
        "temperature_max_celsius": 8.0,
        "capacity_units": 20,
    }
    res_loc = await client.post(
        f"{API}/storage/locations", json=loc_payload, headers=headers_tecnico
    )
    assert res_loc.status_code == 201
    loc_id = res_loc.json()["id"]

    # Cria amostra no banco
    async with db_factory() as db:
        user_tecnico = await db.get(User, UUID(users["tecnico"]["id"]))
        assert user_tecnico is not None

        sample = DeviceSample(
            id=uuid4(),
            accession_number=f"AMO-MOV-{uuid4().hex[:4].upper()}",
            commercial_name="Enxerto Vascular PTFE",
            manufacturer="CardioTech SA",
            status=SampleStatus.RECEBIDO,
            received_at=utcnow(),
            received_by_id=user_tecnico.id,
        )
        db.add(sample)
        await db.commit()
        sample_id = sample.id

    # Movimentação 1: Normal (4.5 °C)
    mov1_payload = {
        "sample_id": str(sample_id),
        "to_location_id": loc_id,
        "reason": "Entrada na câmara refrigerada após recepção e triagem",
        "temperature_at_movement": 4.5,
    }
    res_mov1 = await client.post(
        f"{API}/storage/movements", json=mov1_payload, headers=headers_tecnico
    )
    assert res_mov1.status_code == 201
    assert "EXCURSÃO TÉRMICA" not in (res_mov1.json()["notes"] or "")

    # Movimentação 2: Excursão Térmica detectada (12.5 °C - acima de 8.0 °C)
    mov2_payload = {
        "sample_id": str(sample_id),
        "to_location_id": loc_id,
        "reason": "Retorno de bancada para refrigerador",
        "temperature_at_movement": 12.5,
        "notes": "Amostra permaneceu na bancada por tempo prolongado.",
    }
    res_mov2 = await client.post(
        f"{API}/storage/movements", json=mov2_payload, headers=headers_tecnico
    )
    assert res_mov2.status_code == 201
    mov2_data = res_mov2.json()
    assert "ALERTA DE EXCURSÃO TÉRMICA" in mov2_data["notes"]


@pytest.mark.asyncio
async def test_retention_and_disposal_dual_signature_workflow(
    db_factory: async_sessionmaker[AsyncSession],
    client: AsyncClient,
    users: dict[str, dict[str, Any]],
) -> None:
    """Valida retenção de contraprova, bloqueio de descarte prematuro e termo de descarte 21 CFR Part 11."""
    login_tecnico = await login(client, "tecnico", "Tecnico@Lims2026")
    headers_tecnico = auth(login_tecnico["access_token"])

    login_fiscal = await login(client, "fiscal", "Fiscal@Lims2026")
    headers_fiscal = auth(login_fiscal["access_token"])

    # 1. Cadastra câmara fria
    loc_payload = {
        "code": f"CAM-RET-{uuid4().hex[:4].upper()}",
        "name": "Câmara de Contraprova Pericial",
        "location_type": StorageLocationType.COLD_CHAMBER.value,
        "room": "Área Restrita Pericial",
        "temperature_target_celsius": 5.0,
        "temperature_min_celsius": 2.0,
        "temperature_max_celsius": 8.0,
        "capacity_units": 500,
    }
    res_loc = await client.post(
        f"{API}/storage/locations", json=loc_payload, headers=headers_tecnico
    )
    assert res_loc.status_code == 201
    loc_id = res_loc.json()["id"]

    # 2. Cria amostra
    async with db_factory() as db:
        user_tecnico = await db.get(User, UUID(users["tecnico"]["id"]))
        user_fiscal = await db.get(User, UUID(users["fiscal"]["id"]))
        assert user_tecnico is not None and user_fiscal is not None

        sample = DeviceSample(
            id=uuid4(),
            accession_number=f"AMO-RET-{uuid4().hex[:4].upper()}",
            commercial_name="Válvula Cardíaca Biológica",
            manufacturer="BioValvular Brasil",
            status=SampleStatus.APROVADO,
            received_at=utcnow(),
            received_by_id=user_tecnico.id,
        )
        db.add(sample)
        await db.commit()
        sample_id = sample.id

    # 3. Guarda formal de contraprova com prazo legal de 1 ano
    retain_until = (date.today() + timedelta(days=365)).isoformat()
    seal_number = f"LACRE-INVIOLAVEL-{uuid4().hex[:6].upper()}"
    retention_payload = {
        "sample_id": str(sample_id),
        "storage_location_id": loc_id,
        "retention_type": RetentionType.CONTRAPROVA_PERICIAL.value,
        "retain_until": retain_until,
        "quantity_retained": 1.0,
        "unit": "un",
        "seal_number": seal_number,
        "notes": "Contraprova pericial retida conforme RDC 665/2022 Art. 45.",
    }
    res_ret = await client.post(
        f"{API}/storage/retentions", json=retention_payload, headers=headers_tecnico
    )
    assert res_ret.status_code == 201, res_ret.text
    ret_data = res_ret.json()
    assert ret_data["status"] == RetentionStatus.ACTIVE.value
    assert ret_data["seal_number"] == seal_number

    # 4. Emissão de assinatura eletrônica do Técnico (Executor)
    sign_tecnico_payload = {
        "password": "Tecnico@Lims2026",
        "meaning": SignatureMeaning.EXECUCAO_DESCARTE.value,
        "reason": "Execução de descarte com autoclave e neutralização conforme POP-LAB-044",
        "entity_type": "DeviceSample",
        "entity_id": str(sample_id),
        "action": SignatureAction.CLOSE.value,
    }
    res_sign_tec = await client.post(
        f"{API}/auth/sign", json=sign_tecnico_payload, headers=headers_tecnico
    )
    assert res_sign_tec.status_code == 200, res_sign_tec.text
    token_tecnico = res_sign_tec.json()["token"]

    # 5. Tentativa de auto-testemunho (mesmo usuário executor como testemunha -> Violação de Segregação)
    dual_self_payload = {
        "sample_id": str(sample_id),
        "disposal_method": "AUTOCLAVAGEM",
        "primary_esign_token": token_tecnico,
        "witness_id": users["tecnico"]["id"],
        "witness_esign_token": token_tecnico,
    }
    res_dual_self = await client.post(
        f"{API}/storage/disposal", json=dual_self_payload, headers=headers_tecnico
    )
    assert res_dual_self.status_code == 422
    assert "dois usuários distintos" in res_dual_self.json()["detail"]

    # 6. Emissão de assinatura da Fiscal (Testemunha)
    sign_fiscal_payload = {
        "password": "Fiscal@Lims2026",
        "meaning": SignatureMeaning.TESTEMUNHA_DESCARTE.value,
        "reason": "Testemunho formal e conferência da integridade do lacre antes do expurgo",
        "entity_type": "DeviceSample",
        "entity_id": str(sample_id),
        "action": SignatureAction.CLOSE.value,
    }
    res_sign_fisc = await client.post(
        f"{API}/auth/sign", json=sign_fiscal_payload, headers=headers_fiscal
    )
    assert res_sign_fisc.status_code == 200, res_sign_fisc.text
    token_fiscal = res_sign_fisc.json()["token"]

    # 7. Tentativa de descarte antes do vencimento legal da contraprova (sem override) -> Bloqueio
    disposal_blocked_payload = {
        "sample_id": str(sample_id),
        "disposal_method": "AUTOCLAVAGEM",
        "primary_esign_token": token_tecnico,
        "witness_id": users["fiscal"]["id"],
        "witness_esign_token": token_fiscal,
        "force_legal_override": False,
    }
    res_blocked = await client.post(
        f"{API}/storage/disposal", json=disposal_blocked_payload, headers=headers_tecnico
    )
    assert res_blocked.status_code == 422
    assert "BLOQUEIO REGULATÓRIO" in res_blocked.json()["detail"]

    # 8. Re-emissão de tokens para autorização legal de descarte com override expresso
    res_sign_tec2 = await client.post(
        f"{API}/auth/sign", json=sign_tecnico_payload, headers=headers_tecnico
    )
    res_sign_fisc2 = await client.post(
        f"{API}/auth/sign", json=sign_fiscal_payload, headers=headers_fiscal
    )
    token_tecnico2 = res_sign_tec2.json()["token"]
    token_fiscal2 = res_sign_fisc2.json()["token"]

    disposal_ok_payload = {
        "sample_id": str(sample_id),
        "disposal_method": "INCINERACAO",
        "primary_esign_token": token_tecnico2,
        "witness_id": users["fiscal"]["id"],
        "witness_esign_token": token_fiscal2,
        "environmental_license_number": "LO-IBAMA-2026-9812",
        "waste_company_name": "Ecológica Tratamento de Resíduos Perigosos S/A",
        "notes": "Determinação judicial de incineração com ata notarial.",
        "force_legal_override": True,
    }
    res_disposal = await client.post(
        f"{API}/storage/disposal", json=disposal_ok_payload, headers=headers_tecnico
    )
    assert res_disposal.status_code == 201, res_disposal.text
    disp_data = res_disposal.json()
    assert disp_data["disposal_manifest_number"].startswith("MAN-DESC-")
    assert disp_data["disposal_method"] == "INCINERACAO"

    # 9. Confere status da amostra no banco
    async with db_factory() as db:
        refreshed_sample = await db.get(DeviceSample, sample_id)
        assert refreshed_sample is not None
        assert refreshed_sample.status == SampleStatus.DESCARTADO
