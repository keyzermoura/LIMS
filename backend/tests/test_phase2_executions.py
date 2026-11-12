"""Suíte de Testes da Fase 2: Catálogo de Métodos, Metrologia e Execuções de Bancada (ALCOA+).

Valida:
1. Catálogo de Métodos de Ensaio e normas técnicas.
2. Controle Metrológico de Equipamentos, datas de validade e bloqueio de uso para calibração vencida.
3. Separação de Ensaio Planejado (LabTest) e Tentativas Reais de Bancada (TestExecution).
4. Interrupção e Repetição de Execuções sem sobrescrever dados históricos (ALCOA+).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest
from httpx import AsyncClient

API = "/api/v1"


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def signed(token: str, signature_token: str) -> dict[str, str]:
    return {**auth(token), "X-Signature-Token": signature_token}


async def login(client: AsyncClient, username: str, password: str) -> dict[str, Any]:
    res = await client.post(
        f"{API}/auth/login",
        data={"username": username, "password": password},
    )
    assert res.status_code == 200, res.text
    return res.json()


async def issue_signature(
    client: AsyncClient,
    access_token: str,
    password: str,
    *,
    entity_type: str,
    entity_id: str,
    action: str = "CREATE",
    meaning: str = "AUTORIA",
    reason: str = "Assinatura técnica eletrônica em conformidade Part 11.",
) -> dict[str, Any]:
    res = await client.post(
        f"{API}/auth/sign",
        headers=auth(access_token),
        json={
            "password": password,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "action": action,
            "meaning": meaning,
            "reason": reason,
        },
    )
    assert res.status_code == 200, res.text
    return res.json()


async def create_sample_fixture(
    client: AsyncClient, access_token: str, password: str
) -> dict[str, Any]:
    sample_id = str(uuid4())
    grant = await issue_signature(
        client,
        access_token,
        password,
        entity_type="DeviceSample",
        entity_id=sample_id,
        action="CREATE",
    )
    body = {
        "id": sample_id,
        "serial_number": f"SN-{uuid4().hex[:6].upper()}",
        "lot_number": "L-2026-F2",
        "manufacturer": "BioMed Test Corp",
        "commercial_name": "Bomba de Infusão Peristáltica",
        "model": "BIP-2000",
        "registration_number": "80000000002",
        "description": "Amostra para testes de fase 2.",
        "storage_location": "Bancada Metrológica 01",
    }
    res = await client.post(
        f"{API}/samples",
        headers=signed(access_token, grant["token"]),
        json=body,
    )
    assert res.status_code == 201, res.text
    return res.json()["sample"]


# ==============================================================================
# 1. Catálogo de Métodos de Ensaio
# ==============================================================================
@pytest.mark.anyio
async def test_method_catalog_crud_and_validation(
    client: AsyncClient, users: dict[str, dict[str, Any]]
) -> None:
    admin = await login(client, "admin", users["admin"]["password"])
    admin_auth = auth(admin["access_token"])

    # 1.1 Criar método válido
    method_data = {
        "code": "MET-TEST-RIGIDEZ",
        "name": "Rigidez Dielétrica e Isolamento",
        "standard": "ABNT NBR IEC 60601-1:2016",
        "category": "Segurança Elétrica",
        "default_unit": "mA",
        "default_lower_limit": "0.0",
        "default_upper_limit": "5.0",
        "default_acceptance_criteria": "Corrente não deve exceder 5 mA",
        "parameters_schema": {"tensao_v": 1500, "duracao_s": 60},
    }
    res = await client.post(f"{API}/catalog/methods", headers=admin_auth, json=method_data)
    assert res.status_code == 201, res.text
    created = res.json()
    assert created["code"] == "MET-TEST-RIGIDEZ"
    assert created["is_active"] is True
    method_id = created["id"]

    # 1.2 Tentar duplicar código (conflito 409)
    dup = await client.post(f"{API}/catalog/methods", headers=admin_auth, json=method_data)
    assert dup.status_code == 409

    # 1.3 Consultar por ID e listar
    get_res = await client.get(f"{API}/catalog/methods/{method_id}", headers=admin_auth)
    assert get_res.status_code == 200
    assert get_res.json()["name"] == method_data["name"]

    list_res = await client.get(f"{API}/catalog/methods", headers=admin_auth)
    assert list_res.status_code == 200
    codes = [m["code"] for m in list_res.json()]
    assert "MET-TEST-RIGIDEZ" in codes

    # 1.4 Seed de métodos padrão da SEFI
    seed_res = await client.post(f"{API}/catalog/methods/seed-standards", headers=admin_auth)
    assert seed_res.status_code == 200
    standards = seed_res.json()
    assert len(standards) >= 3
    assert any(m["code"] == "MET-ELETRO-01" for m in standards)


# ==============================================================================
# 2. Gestão de Equipamentos e Bloqueio Metrológico (ISO/IEC 17025)
# ==============================================================================
@pytest.mark.anyio
async def test_equipment_lifecycle_and_metrological_blocking(
    client: AsyncClient, users: dict[str, dict[str, Any]]
) -> None:
    admin = await login(client, "admin", users["admin"]["password"])
    tecnico = await login(client, "tecnico", users["tecnico"]["password"])
    admin_auth = auth(admin["access_token"])

    now = datetime.now(UTC)
    future_date = (now + timedelta(days=180)).isoformat()
    past_date = (now - timedelta(days=10)).isoformat()

    # 2.1 Cadastra equipamento com calibração válida
    valid_eq_payload = {
        "code": "EQ-CALIBRADO-01",
        "name": "Hipot Tester Digital",
        "equipment_type": "Gerador de Alta Tensão",
        "manufacturer": "Chroma",
        "model": "19052",
        "serial_number": "SN-HIPOT-001",
        "calibration_status": "CALIBRADO",
        "last_calibration_at": (now - timedelta(days=30)).isoformat(),
        "calibration_due_date": future_date,
        "certificate_number": "CAL-2026-999",
        "calibration_agency": "Laboratório RBC Calibrações",
    }
    res = await client.post(f"{API}/equipment", headers=admin_auth, json=valid_eq_payload)
    assert res.status_code == 201, res.text
    valid_eq = res.json()
    assert valid_eq["is_calibration_valid"] is True

    # 2.2 Cadastra equipamento com calibração vencida
    expired_eq_payload = {
        "code": "EQ-VENCIDO-01",
        "name": "Multímetro de Bancada Antigo",
        "equipment_type": "Multímetro 6.5 Dígitos",
        "calibration_status": "CALIBRADO",
        "last_calibration_at": (now - timedelta(days=400)).isoformat(),
        "calibration_due_date": past_date,
        "certificate_number": "CAL-2024-111",
        "calibration_agency": "Antiga Calibrações",
    }
    res = await client.post(f"{API}/equipment", headers=admin_auth, json=expired_eq_payload)
    assert res.status_code == 201
    expired_eq = res.json()
    # Deve ser automaticamente marcado como VENCIDO
    assert expired_eq["calibration_status"] == "VENCIDO"
    assert expired_eq["is_calibration_valid"] is False

    # 2.3 Prepara ensaio para testar o bloqueio na execução
    sample = await create_sample_fixture(client, admin["access_token"], users["admin"]["password"])
    test_id = str(uuid4())
    grant = await issue_signature(
        client,
        admin["access_token"],
        users["admin"]["password"],
        entity_type="LabTest",
        entity_id=test_id,
        action="CREATE",
    )
    test_res = await client.post(
        f"{API}/tests",
        headers=signed(admin["access_token"], grant["token"]),
        json={
            "id": test_id,
            "device_sample_id": sample["id"],
            "name": "Ensaio de Tensão Suportável",
            "unit": "mA",
            "lower_limit": 0.0,
            "upper_limit": 5.0,
        },
    )
    assert test_res.status_code == 201

    # 2.4 Tentar iniciar execução com o equipamento VENCIDO -> DEVE SER BLOQUEADO (422)
    tec_auth = auth(tecnico["access_token"])
    denied = await client.post(
        f"{API}/tests/{test_id}/executions",
        headers=tec_auth,
        json={"equipment_id": expired_eq["id"]},
    )
    assert denied.status_code == 422
    assert "calibração VENCIDA" in denied.json()["detail"] or "Bloqueio Metrológico" in denied.json()["detail"]

    # 2.5 Atualiza calibração do equipamento vencido
    calib_update = {
        "last_calibration_at": now.isoformat(),
        "calibration_due_date": (now + timedelta(days=365)).isoformat(),
        "certificate_number": "CAL-2026-RECALIBRADO",
        "calibration_agency": "Laboratório Acreditado Inmetro",
        "calibration_status": "CALIBRADO",
        "notes": "Instrumento aferido e calibrado com sucesso.",
    }
    calib_res = await client.post(
        f"{API}/equipment/{expired_eq['id']}/calibration",
        headers=admin_auth,
        json=calib_update,
    )
    assert calib_res.status_code == 200
    recalibrated = calib_res.json()
    assert recalibrated["calibration_status"] == "CALIBRADO"
    assert recalibrated["is_calibration_valid"] is True

    # 2.6 Agora o equipamento calibrado pode ser usado na bancada!
    start_res = await client.post(
        f"{API}/tests/{test_id}/executions",
        headers=tec_auth,
        json={"equipment_id": expired_eq["id"]},
    )
    assert start_res.status_code == 201
    assert start_res.json()["execution_number"] == 1


# ==============================================================================
# 3. Execução de Bancada ALCOA+: Leituras Brutas, Interrupção e Repetição
# ==============================================================================
@pytest.mark.anyio
async def test_execution_alcoa_raw_data_interrupt_and_repeat(
    client: AsyncClient, users: dict[str, dict[str, Any]]
) -> None:
    admin = await login(client, "admin", users["admin"]["password"])
    tecnico = await login(client, "tecnico", users["tecnico"]["password"])
    tec_auth = auth(tecnico["access_token"])

    # 3.1 Cria amostra e ensaio planejado
    sample = await create_sample_fixture(client, admin["access_token"], users["admin"]["password"])
    test_id = str(uuid4())
    grant = await issue_signature(
        client,
        admin["access_token"],
        users["admin"]["password"],
        entity_type="LabTest",
        entity_id=test_id,
        action="CREATE",
    )
    test_res = await client.post(
        f"{API}/tests",
        headers=signed(admin["access_token"], grant["token"]),
        json={
            "id": test_id,
            "device_sample_id": sample["id"],
            "name": "Elevação de Temperatura Contínua",
            "unit": "°C",
            "lower_limit": 20.0,
            "upper_limit": 65.0,
        },
    )
    assert test_res.status_code == 201

    # 3.2 Inicia Tentativa #1 com condições ambientais de bancada
    exec1_payload = {
        "temperature_celsius": 23.5,
        "humidity_percent": 55.0,
        "pressure_hpa": 1013.2,
        "notes": "Iniciando ensaio em bancada climatizada.",
    }
    exec1_res = await client.post(
        f"{API}/tests/{test_id}/executions",
        headers=tec_auth,
        json=exec1_payload,
    )
    assert exec1_res.status_code == 201, exec1_res.text
    exec1 = exec1_res.json()
    exec1_id = exec1["id"]
    assert exec1["execution_number"] == 1
    assert exec1["attempt_label"] == "Tentativa #1"
    assert exec1["status"] == "EM_ANDAMENTO"

    # 3.3 Tentar iniciar outra execução simultânea para o mesmo ensaio -> Conflito 409
    dup_exec = await client.post(
        f"{API}/tests/{test_id}/executions",
        headers=tec_auth,
        json={},
    )
    assert dup_exec.status_code == 409
    assert "em andamento" in dup_exec.json()["detail"]

    # 3.4 Registra leituras intermediárias na Tentativa #1
    readings_payload = {
        "raw_data": {
            "sensor_1_c": 35.2,
            "sensor_2_c": 38.4,
            "tempo_min": 15,
        },
        "notes": "Aquecimento preliminar estável.",
    }
    readings_res = await client.post(
        f"{API}/executions/{exec1_id}/readings",
        headers=tec_auth,
        json=readings_payload,
    )
    assert readings_res.status_code == 200
    assert readings_res.json()["raw_data"]["sensor_1_c"] == 35.2

    # 3.5 Simula incidente externo de bancada e interrompe Tentativa #1 (ALCOA+)
    interrupt_payload = {
        "reason": "Queda pontual de energia no laboratório interrompeu o ciclo térmico aos 20 minutos."
    }
    interrupt_res = await client.post(
        f"{API}/executions/{exec1_id}/interrupt",
        headers=tec_auth,
        json=interrupt_payload,
    )
    assert interrupt_res.status_code == 200
    exec1_interrupted = interrupt_res.json()
    assert exec1_interrupted["status"] == "INTERROMPIDA"
    assert exec1_interrupted["interruption_reason"] == interrupt_payload["reason"]
    assert exec1_interrupted["finished_at"] is not None

    # 3.6 Inicia Tentativa #2 (repetição do ensaio com novas condições)
    exec2_payload = {
        "temperature_celsius": 23.2,
        "humidity_percent": 54.5,
        "pressure_hpa": 1013.0,
        "notes": "Reiniciando ensaio após restabelecimento pleno da rede elétrica.",
    }
    exec2_res = await client.post(
        f"{API}/tests/{test_id}/executions",
        headers=tec_auth,
        json=exec2_payload,
    )
    assert exec2_res.status_code == 201
    exec2 = exec2_res.json()
    exec2_id = exec2["id"]
    assert exec2["execution_number"] == 2
    assert exec2["attempt_label"] == "Tentativa #2"
    assert exec2["status"] == "EM_ANDAMENTO"

    # 3.7 Conclui Tentativa #2 com sucesso
    complete_payload = {
        "raw_data": {
            "curva_temperatura": [24.0, 32.5, 41.2, 48.0, 52.3, 53.1],
            "ponto_estabilizacao_c": 53.1,
            "tempo_total_min": 120,
        },
        "result_value": 53.1,
        "result_text": "Temperatura máxima de 53.1 °C nos enrolamentos, dentro do limite de 65.0 °C.",
        "outcome": "APROVADO",
        "notes": "Ensaio concluído sem desvios com estabilização térmica comprovada.",
    }
    complete_res = await client.post(
        f"{API}/executions/{exec2_id}/complete",
        headers=tec_auth,
        json=complete_payload,
    )
    assert complete_res.status_code == 200
    exec2_done = complete_res.json()
    assert exec2_done["status"] == "CONCLUIDA"
    assert exec2_done["outcome"] == "APROVADO"
    assert float(exec2_done["result_value"]) == 53.1

    # 3.8 Auditoria / Rastreabilidade: ambas as execuções coexistem e estão preservadas
    history_res = await client.get(
        f"{API}/tests/{test_id}/executions",
        headers=tec_auth,
    )
    assert history_res.status_code == 200
    history = history_res.json()
    assert len(history) == 2
    assert history[0]["execution_number"] == 1
    assert history[0]["status"] == "INTERROMPIDA"
    assert history[0]["interruption_reason"] is not None
    assert history[1]["execution_number"] == 2
    assert history[1]["status"] == "CONCLUIDA"
    assert history[1]["outcome"] == "APROVADO"
