"""Demonstração Completa Ponta a Ponta do LIMS (End-to-End Demonstration).

Cobre o ciclo de vida laboratorial completo em conformidade regulatória:
1. Autenticação RBAC e emissão de tokens de sessão (Fiscal e Técnico).
2. Recepção e cadastramento de amostra de dispositivo médico com assinatura 21 CFR Part 11.
3. Fracionamento em sub-alíquotas rastreáveis com código de barras/DataMatrix (P4.2).
4. Lookup de amostras e sub-alíquotas por código de barras / lote (H3.3).
5. Entrada de lote de reagente/padrão analítico com controle de validade e saldo (P3.1 / ISO 17025 §6.4).
6. Planejamento de ensaio técnico analítico com limites normativos e assinatura eletrônica.
7. Execução de bancada ALCOA+ com registro de leituras brutas e consumo obrigatório de reagente rastreado (P3.1).
8. Formalização e assinatura técnica do laudo de ensaio pelo analista executor.
9. Revisão técnica colegiada independente (4-Eyes Principle / ISO/IEC 17025) com aprovação formal.
10. Emissão de Laudo Pericial Oficial imutável com hash SHA-256 e assinatura eletrônica 21 CFR Part 11.
11. Verificação pública em tempo real da autenticidade do laudo via QR Code / token regulatório.
"""

from __future__ import annotations

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
    reason: str = "Assinatura técnica eletrônica em conformidade 21 CFR Part 11.",
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


@pytest.mark.anyio
async def test_complete_lims_laboratory_lifecycle_e2e(
    client: AsyncClient,
    users: dict[str, dict[str, Any]],
) -> None:
    # =========================================================================
    # ETAPA 1: Autenticação de Usuários (Fiscal Sanitário e Analista de Bancada)
    # =========================================================================
    fiscal_pass = users["fiscal"]["password"]
    tecnico_pass = users["tecnico"]["password"]

    fiscal_auth = await login(client, "fiscal", fiscal_pass)
    tecnico_auth = await login(client, "tecnico", tecnico_pass)

    assert fiscal_auth["user"]["role"] == "FISCAL"
    assert tecnico_auth["user"]["role"] == "TECNICO"

    fiscal_headers = auth(fiscal_auth["access_token"])
    tecnico_headers = auth(tecnico_auth["access_token"])

    # =========================================================================
    # ETAPA 2: Recepção e Cadastro de Amostra com Assinatura 21 CFR Part 11
    # =========================================================================
    sample_id = str(uuid4())
    sig_sample = await issue_signature(
        client,
        fiscal_auth["access_token"],
        fiscal_pass,
        entity_type="DeviceSample",
        entity_id=sample_id,
        action="CREATE",
        meaning="AUTORIA",
        reason="Apreensão e cadastramento fiscal de dispositivo médico de alta criticidade.",
    )

    sample_payload = {
        "id": sample_id,
        "serial_number": "SN-PTCA-2026-VAL01",
        "lot_number": "LOT-PTCA-2026-B01",
        "manufacturer": "CardioVascular Tech Inc.",
        "commercial_name": "Cateter de Balão para Angioplastia Coronária PTCA",
        "model": "Apex-Glide RX 3.0x15mm",
        "registration_number": "80123450099",
        "description": "Dispositivo estéril para dilatação mecânica em angioplastia transluminal coronária.",
        "storage_location": "Almoxarifado Geral - Armário de Quarentena A-01",
    }

    create_sample_res = await client.post(
        f"{API}/samples",
        headers=signed(fiscal_auth["access_token"], sig_sample["token"]),
        json=sample_payload,
    )
    assert create_sample_res.status_code == 201, create_sample_res.text
    sample = create_sample_res.json()["sample"]
    accession_number = sample["accession_number"]
    assert accession_number.startswith("LIMS-")
    assert sample["status"] == "RECEBIDO"

    # =========================================================================
    # ETAPA 3: Fracionamento em Sub-Alíquota Rastreável com Código de Barras (P4.2)
    # =========================================================================
    aliquot_payload = {
        "aliquot_code": "ALQ-PTCA-2026-001",
        "volume_or_mass": 1.0,
        "unit": "unidade",
        "storage_location": "Bancada Metrológica de Alta Pressão 02",
        "notes": "Alíquota destinada ao ensaio de pressão nominal de ruptura (RBP).",
    }
    aliquot_res = await client.post(
        f"{API}/samples/{sample_id}/aliquots",
        headers=fiscal_headers,
        json=aliquot_payload,
    )
    assert aliquot_res.status_code == 201, aliquot_res.text
    aliquot = aliquot_res.json()
    assert aliquot["aliquot_code"] == "ALQ-PTCA-2026-001"

    # Listagem de alíquotas da amostra
    list_aliq_res = await client.get(
        f"{API}/samples/{sample_id}/aliquots",
        headers=fiscal_headers,
    )
    assert list_aliq_res.status_code == 200
    aliquots = list_aliq_res.json()
    assert len(aliquots) == 1
    assert aliquots[0]["aliquot_code"] == "ALQ-PTCA-2026-001"

    # =========================================================================
    # ETAPA 4: Validação do Lookup de Amostras por Código / Lote (H3.3)
    # =========================================================================
    lookup_acc = await client.get(
        f"{API}/samples/lookup/barcode/{accession_number}",
        headers=fiscal_headers,
    )
    assert lookup_acc.status_code == 200
    assert lookup_acc.json()["id"] == sample_id

    lookup_serial = await client.get(
        f"{API}/samples/lookup/barcode/SN-PTCA-2026-VAL01",
        headers=fiscal_headers,
    )
    assert lookup_serial.status_code == 200
    assert lookup_serial.json()["id"] == sample_id

    # =========================================================================
    # ETAPA 5: Entrada de Reagente / Padrão Analítico e Lote Físico (P3.1 / ISO 17025)
    # =========================================================================
    from datetime import date, timedelta
    today = date.today()

    reagent_payload = {
        "code": "CRM-SALINA-01",
        "name": "Solução Fisiológica Salina 0.9% Padrão Analítico",
        "reagent_type": "PRIMARY_STANDARD_CRM",
        "grade": "PA",
    }
    reagent_res = await client.post(
        f"{API}/reagents",
        headers=fiscal_headers,
        json=reagent_payload,
    )
    assert reagent_res.status_code == 201, reagent_res.text
    reagent = reagent_res.json()
    reagent_id = reagent["id"]

    batch_payload = {
        "lot_number": "LOT-SALINA-2026-01",
        "manufacturer": "Merck KGaA",
        "initial_quantity": 1000.0,
        "unit": "mL",
        "certificate_number": "CERT-CRM-2026-9921",
        "expiration_date": (today + timedelta(days=365)).isoformat(),
    }
    batch_res = await client.post(
        f"{API}/reagents/{reagent_id}/batches",
        headers=fiscal_headers,
        json=batch_payload,
    )
    assert batch_res.status_code == 201, batch_res.text
    reagent_batch = batch_res.json()
    batch_id = reagent_batch["id"]

    # =========================================================================
    # ETAPA 6: Planejamento do Ensaio Técnico Analítico (LabTest)
    # =========================================================================
    test_id = str(uuid4())
    sig_test = await issue_signature(
        client,
        fiscal_auth["access_token"],
        fiscal_pass,
        entity_type="LabTest",
        entity_id=test_id,
        action="CREATE",
        meaning="AUTORIA",
        reason="Planejamento analítico do ensaio de ruptura sob pressão hidrostática.",
    )

    test_payload = {
        "id": test_id,
        "device_sample_id": sample_id,
        "name": "Pressão Nominal de Ruptura (Rated Burst Pressure - RBP)",
        "method": "Ensaio Hidrostático Conforme Norma ISO 10555-4",
        "parameters": {"temperatura_banho": "37 °C", "taxa_pressurizacao": "1 atm/s"},
        "unit": "atm",
        "lower_limit": 14.0,
        "upper_limit": 25.0,
        "acceptance_criteria": "O balão deve suportar pressão hidrostática mínima de 14.0 atm sem ruptura.",
        "assigned_to_id": users["tecnico"]["id"],
    }
    test_res = await client.post(
        f"{API}/tests",
        headers=signed(fiscal_auth["access_token"], sig_test["token"]),
        json=test_payload,
    )
    assert test_res.status_code == 201, test_res.text
    planned_test = test_res.json()["test"]
    assert planned_test["status"] == "PENDENTE"

    # =========================================================================
    # ETAPA 7: Execução de Bancada ALCOA+ com Consumo de Insumo (P3.1)
    # =========================================================================
    start_exec_res = await client.post(
        f"{API}/tests/{test_id}/executions",
        headers=tecnico_headers,
        json={
            "temperature_celsius": 22.5,
            "humidity_percent": 53.0,
            "pressure_hpa": 1012.8,
            "notes": "Início da pressurização hidrostática na bancada metrológica.",
        },
    )
    assert start_exec_res.status_code == 201, start_exec_res.text
    execution = start_exec_res.json()
    execution_id = execution["id"]
    assert execution["status"] == "EM_ANDAMENTO"

    # Consumo obrigatório do reagente/padrão analítico rastreado (P3.1)
    consume_payload = {
        "batch_id": batch_id,
        "quantity_used": 50.0,
        "unit": "mL",
    }
    consume_res = await client.post(
        f"{API}/reagents/executions/{execution_id}/consume",
        headers=tecnico_headers,
        json=consume_payload,
    )
    assert consume_res.status_code == 201, consume_res.text
    usage = consume_res.json()
    assert float(usage["quantity_used"]) == 50.0
    assert usage["unit"] == "mL"

    # Registro de dados brutos ALCOA+ (curva de pressurização)
    readings_payload = {
        "raw_data": {
            "pressurizacao_etapas_atm": [4.0, 8.0, 12.0, 14.0, 16.0, 18.2],
            "tempo_estabilizacao_s": 30,
            "ruptura_detectada": False,
        },
        "notes": "Pressurização progressiva com solução salina mantida a 37 °C.",
    }
    reading_res = await client.post(
        f"{API}/executions/{execution_id}/readings",
        headers=tecnico_headers,
        json=readings_payload,
    )
    assert reading_res.status_code == 200

    # Conclusão da Execução na Bancada
    complete_exec_res = await client.post(
        f"{API}/executions/{execution_id}/complete",
        headers=tecnico_headers,
        json={
            "result_value": 18.2,
            "result_text": "Balão suportou até 18.2 atm sem ruptura mecânica ou vazamento.",
            "outcome": "APROVADO",
            "notes": "Resultado em conformidade com especificação ISO 10555-4 (limite 14.0 atm).",
        },
    )
    assert complete_exec_res.status_code == 200, complete_exec_res.text
    exec_done = complete_exec_res.json()
    assert exec_done["status"] == "CONCLUIDA"
    assert exec_done["outcome"] == "APROVADO"

    # =========================================================================
    # ETAPA 8: Formalização e Assinatura Técnica do Ensaio pelo Analista
    # =========================================================================
    sig_result = await issue_signature(
        client,
        tecnico_auth["access_token"],
        tecnico_pass,
        entity_type="LabTest",
        entity_id=test_id,
        action="UPDATE",
        meaning="RESPONSABILIDADE_TECNICA",
        reason="Emissão técnica dos resultados obtidos na bancada de ensaios.",
    )
    update_test_res = await client.patch(
        f"{API}/tests/{test_id}/result",
        headers=signed(tecnico_auth["access_token"], sig_result["token"]),
        json={
            "result_value": 18.2,
            "result_text": "Pressão máxima suportada de 18.2 atm sem ruptura.",
            "outcome": "APROVADO",
            "notes": "Ensaio analítico concluído com êxito.",
            "version": 1,
        },
    )
    assert update_test_res.status_code == 200, update_test_res.text
    completed_test = update_test_res.json()["test"]
    assert completed_test["status"] == "CONCLUIDO"
    assert completed_test["outcome"] == "APROVADO"

    # =========================================================================
    # ETAPA 9: Revisão Técnica Colegiada (4-Eyes Principle / ISO/IEC 17025)
    # =========================================================================
    # Submissão à coordenação
    submit_res = await client.post(
        f"{API}/reviews/tests/{test_id}/submit",
        headers=tecnico_headers,
        json={"notes": "Ensaio concluído e assinado, aguardando revisão colegiada."},
    )
    assert submit_res.status_code == 200
    assert submit_res.json()["review_status"] == "PENDENTE"

    # Parecer técnico emitido pelo Fiscal Revisor independente
    sig_reviewer = await issue_signature(
        client,
        fiscal_auth["access_token"],
        fiscal_pass,
        entity_type="LabTest",
        entity_id=test_id,
        action="UPDATE",
        meaning="APROVACAO",
        reason="Homologação técnica independente dos dados brutos e cálculos metrológicos.",
    )
    decide_res = await client.post(
        f"{API}/reviews/tests/{test_id}/decide",
        headers=signed(fiscal_auth["access_token"], sig_reviewer["token"]),
        json={
            "status": "APROVADO",
            "notes": "Verificação documental e analítica integral. Critérios atendidos plenamente.",
        },
    )
    assert decide_res.status_code == 200, decide_res.text
    assert decide_res.json()["status"] == "APROVADO"

    # =========================================================================
    # ETAPA 10: Emissão do Laudo Pericial Oficial (21 CFR Part 11)
    # =========================================================================
    sig_official_report = await issue_signature(
        client,
        fiscal_auth["access_token"],
        fiscal_pass,
        entity_type="DeviceSample",
        entity_id=sample_id,
        action="CLOSE",
        meaning="RESPONSABILIDADE_TECNICA",
        reason="Emissão formal de Laudo Pericial Oficial Conclusivo de Fiscalização Sanitária.",
    )

    report_payload = {
        "device_sample_id": sample_id,
        "test_ids": [test_id],
        "title": "Laudo Pericial Oficial de Conformidade Mecânica e Estanqueidade",
        "conclusion": "APROVADO",
        "summary": "O lote de cateteres de balão atende com folga aos critérios de pressão nominal de ruptura (RBP >= 14 atm) da norma ISO 10555-4.",
    }
    report_res = await client.post(
        f"{API}/reports/official",
        headers=signed(fiscal_auth["access_token"], sig_official_report["token"]),
        json=report_payload,
    )
    assert report_res.status_code == 200, report_res.text
    official_report = report_res.json()

    assert official_report["report_number"].startswith("LDO-")
    assert len(official_report["sha256_hash"]) == 64
    assert len(official_report["auth_token"]) >= 20
    assert official_report["conclusion"] == "APROVADO"

    report_auth_token = official_report["auth_token"]
    expected_sha256 = official_report["sha256_hash"]
    expected_report_num = official_report["report_number"]

    # =========================================================================
    # ETAPA 11: Validação Pública em Tempo Real via QR Code / auth_token
    # =========================================================================
    # Endpoint público sem nenhum header de autorização (anônimo, simulando cidadão/fiscal externo)
    public_res = await client.get(f"{API}/reports/verify/{report_auth_token}")
    assert public_res.status_code == 200, public_res.text
    validation = public_res.json()

    assert validation["is_valid"] is True
    assert validation["report_number"] == expected_report_num
    assert validation["sha256_hash"] == expected_sha256
    assert validation["sample_acc_number"] == accession_number
    assert validation["sample_commercial_name"] == "Cateter de Balão para Angioplastia Coronária PTCA"
    assert validation["sample_serial_number"] == "SN-PTCA-2026-VAL01"
    assert validation["sample_lot_number"] == "LOT-PTCA-2026-B01"
    assert validation["conclusion"] == "APROVADO"
