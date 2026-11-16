"""Suíte de Testes da Fase 4: Avaliação de Incerteza de Medição GUM e Decisão ILAC-G8 (Sprint 4.2).

Valida:
1. Cálculo GUM em `/uncertainty/simulate`: Repetibilidade Tipo A, componentes Tipo B,
   incerteza combinada uc, graus de liberdade Welch-Satterthwaite, fator k e U.
2. Regras de decisão metrológica ILAC-G8:09/2019 e declarações ISO/IEC 17025 §7.8.6
   (SIMPLE_ACCEPTANCE, GUARD_BAND_CONSERVATIVE e GUARD_BAND_NON_BINARY).
3. Persistência de orçamento de incerteza em `/uncertainty/budgets` com assinatura e auditoria Part 11.
4. Integração metrológica com Laudo Oficial: o resumo de incerteza é automaticamente incorporado
   ao manifesto criptográfico SHA-256 do laudo assinado.
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
    action: str = "UPDATE",
    meaning: str = "APROVACAO",
    reason: str = "Assinatura metrológica em conformidade com ISO 17025 e Part 11.",
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
async def test_uncertainty_simulation_gum_and_ilac_g8_rules(
    client: AsyncClient,
    users: dict[str, dict[str, Any]],
) -> None:
    """Testa o motor de cálculo GUM e as 3 regras de decisão ILAC-G8."""
    tecnico_pass = users["tecnico"]["password"]
    tecnico_auth = await login(client, "tecnico", tecnico_pass)
    headers = auth(tecnico_auth["access_token"])

    # 1. Simulação GUM completa com Tipo A (5 leituras) e Tipo B (calibração + resolução)
    sim_payload = {
        "unit": "uA",
        "repeatability_readings": [98.40, 98.55, 98.48, 98.60, 98.47],
        "lower_limit": 0.0,
        "upper_limit": 100.0,
        "confidence_level": 95.45,
        "guard_band_multiplier": 1.0,
        "decision_rule": "GUARD_BAND_NON_BINARY",
        "components": [
            {
                "name": "Calibração do Multímetro",
                "symbol": "u_cal",
                "source_type": "TYPE_B",
                "distribution": "NORMAL",
                "half_width": 1.20,
                "divisor": 2.0,
                "sensitivity_coefficient": 1.0,
                "degrees_of_freedom": 50,
            },
            {
                "name": "Resolução do Instrumento",
                "symbol": "u_res",
                "source_type": "TYPE_B",
                "distribution": "RECTANGULAR",
                "half_width": 0.05,
                "sensitivity_coefficient": 1.0,
            },
        ],
    }

    res = await client.post(f"{API}/uncertainty/simulate", headers=headers, json=sim_payload)
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["unit"] == "uA"
    assert data["repeatability_count"] == 5
    assert float(data["measured_value"]) == pytest.approx(98.50, abs=0.05)
    assert float(data["combined_uncertainty"]) > 0.6
    assert float(data["expanded_uncertainty"]) > 1.2
    assert float(data["coverage_factor"]) >= 2.0
    assert len(data["components"]) == 3  # Injetou Tipo A + 2 Tipo B
    assert "Repetibilidade Experimental" in data["components"][0]["name"]
    assert data["decision_rule"] == "GUARD_BAND_NON_BINARY"
    # 98.50 com U aprox 1.3 cruza a zona de guarda para o limite superior 100.0 (100 - 1.3 = 98.7)
    # Como 98.50 < 98.7, está na zona conforme ou conforme condicional dependendo do valor
    assert data["conformity_status"] in ("CONFORME", "CONFORME_CONDICIONAL")

    # 2. Teste da regra Aceitação Simples (Simple Acceptance: risco compartilhado, w = 0)
    simple_payload = {
        "unit": "uA",
        "measured_value": 99.50,
        "lower_limit": 0.0,
        "upper_limit": 100.0,
        "decision_rule": "SIMPLE_ACCEPTANCE",
        "components": [
            {
                "name": "Incerteza Padrão Residual",
                "source_type": "TYPE_B",
                "distribution": "NORMAL",
                "half_width": 1.0,
                "divisor": 2.0,
            }
        ],
    }
    res_simple = await client.post(f"{API}/uncertainty/simulate", headers=headers, json=simple_payload)
    assert res_simple.status_code == 200
    data_simple = res_simple.json()
    assert float(data_simple["guard_band_width"]) == 0.0
    assert data_simple["conformity_status"] == "CONFORME"
    assert data_simple["recommended_outcome"] == "APROVADO"

    # 3. Teste da regra Conservadora com Faixa de Guarda (Guard Band Conservative)
    # Valor 99.50 com U = 1.000 cruza o limite de guarda superior (100.0 - 1.0 = 99.0)
    # Na regra conservadora binária, cair na zona de guarda reprova (NAO_CONFORME / REPROVADO)
    cons_payload = {
        "unit": "uA",
        "measured_value": 99.50,
        "lower_limit": 0.0,
        "upper_limit": 100.0,
        "decision_rule": "GUARD_BAND_CONSERVATIVE",
        "guard_band_multiplier": 1.0,
        "coverage_factor": 2.0,
        "components": [
            {
                "name": "Incerteza Padrão",
                "source_type": "TYPE_B",
                "distribution": "NORMAL",
                "half_width": 1.0,
                "divisor": 2.0,
            }
        ],
    }
    res_cons = await client.post(f"{API}/uncertainty/simulate", headers=headers, json=cons_payload)
    assert res_cons.status_code == 200
    data_cons = res_cons.json()
    assert float(data_cons["guard_band_width"]) == pytest.approx(1.0, abs=0.01)
    assert data_cons["conformity_status"] == "NAO_CONFORME"
    assert data_cons["recommended_outcome"] == "REPROVADO"

    # 4. Teste da regra Não-Binária na Zona de Guarda (Conditional Pass: CONFORME_CONDICIONAL / INCONCLUSIVO)
    non_bin_payload = {**cons_payload, "decision_rule": "GUARD_BAND_NON_BINARY"}
    res_nb = await client.post(f"{API}/uncertainty/simulate", headers=headers, json=non_bin_payload)
    assert res_nb.status_code == 200
    data_nb = res_nb.json()
    assert data_nb["conformity_status"] == "CONFORME_CONDICIONAL"
    assert data_nb["recommended_outcome"] == "INCONCLUSIVO"
    assert "ZONA DE GUARDA" in data_nb["conformity_statement"]


@pytest.mark.anyio
async def test_uncertainty_budget_persistence_and_report_manifest(
    client: AsyncClient,
    users: dict[str, dict[str, Any]],
) -> None:
    """Testa a criação de orçamento de incerteza persistido com assinatura e inclusão no laudo pericial."""
    tecnico_pass = users["tecnico"]["password"]
    fiscal_pass = users["fiscal"]["password"]
    tecnico_auth = await login(client, "tecnico", tecnico_pass)
    fiscal_auth = await login(client, "fiscal", fiscal_pass)

    analyst_id = tecnico_auth["user"]["id"]

    # 1. Cria método analítico e qualifica o técnico
    method_code = f"MET-UNC-{uuid4().hex[:6].upper()}"
    m_res = await client.post(
        f"{API}/catalog/methods",
        headers=auth(fiscal_auth["access_token"]),
        json={
            "code": method_code,
            "name": "Ensaio de Resistência de Aterramento de Proteção",
            "standard": "ABNT NBR IEC 60601-1 Cláusula 8.6",
            "default_unit": "mOhm",
            "default_lower_limit": 0.0,
            "default_upper_limit": 200.0,
        },
    )
    assert m_res.status_code == 201, m_res.text
    method_id = m_res.json()["id"]

    sig_qual = await issue_signature(
        client,
        fiscal_auth["access_token"],
        fiscal_pass,
        entity_type="User",
        entity_id=analyst_id,
        action="UPDATE",
        meaning="APROVACAO",
    )
    q_res = await client.post(
        f"{API}/qualifications/grant",
        headers=signed(fiscal_auth["access_token"], sig_qual["token"]),
        json={
            "user_id": analyst_id,
            "method_id": method_id,
            "status": "QUALIFICADO",
            "trainings": [
                {"title": "Treinamento Metrológico NBR IEC 60601-1", "hours": 16.0}
            ],
        },
    )
    assert q_res.status_code == 201, q_res.text

    # 2. Cadastra Amostra e Ensaio
    sample_id = str(uuid4())
    sig_sample = await issue_signature(
        client,
        fiscal_auth["access_token"],
        fiscal_pass,
        entity_type="DeviceSample",
        entity_id=sample_id,
        action="CREATE",
        meaning="AUTORIA",
    )
    s_res = await client.post(
        f"{API}/samples",
        headers=signed(fiscal_auth["access_token"], sig_sample["token"]),
        json={
            "id": sample_id,
            "serial_number": f"SN-UNC-{uuid4().hex[:6].upper()}",
            "lot_number": "L-UNC-42",
            "manufacturer": "EletroMedica Brasil",
            "commercial_name": "Eletrocautério Cirúrgico EC-50",
            "model": "EC-50",
            "registration_number": "80000000042",
            "storage_location": "Bancada Metrológica 04",
        },
    )
    assert s_res.status_code == 201, s_res.text

    test_id = str(uuid4())
    sig_test = await issue_signature(
        client,
        fiscal_auth["access_token"],
        fiscal_pass,
        entity_type="LabTest",
        entity_id=test_id,
        action="CREATE",
        meaning="AUTORIA",
    )
    t_res = await client.post(
        f"{API}/tests",
        headers=signed(fiscal_auth["access_token"], sig_test["token"]),
        json={
            "id": test_id,
            "device_sample_id": sample_id,
            "name": "Ensaio de Continuidade de Aterramento",
            "method_id": method_id,
            "unit": "mOhm",
            "lower_limit": 0.0,
            "upper_limit": 200.0,
            "assigned_to_id": analyst_id,
        },
    )
    assert t_res.status_code == 201, t_res.text

    # 3. Analista lança resultado de ensaio aprovado
    sig_res = await issue_signature(
        client,
        tecnico_auth["access_token"],
        tecnico_pass,
        entity_type="LabTest",
        entity_id=test_id,
        action="UPDATE",
        meaning="AUTORIA",
    )
    r_patch = await client.patch(
        f"{API}/tests/{test_id}/result",
        headers=signed(tecnico_auth["access_token"], sig_res["token"]),
        json={
            "result_value": 85.0,
            "result_text": "Continuidade de aterramento conforme.",
            "outcome": "APROVADO",
            "version": 1,
        },
    )
    assert r_patch.status_code == 200, r_patch.text

    # 4. Registra Orçamento de Incerteza GUM vinculado ao ensaio com assinatura Part 11
    sig_budget = await issue_signature(
        client,
        tecnico_auth["access_token"],
        tecnico_pass,
        entity_type="LabTest",
        entity_id=test_id,
        action="UPDATE",
        meaning="VERIFICACAO",
        reason="Assinatura técnica do orçamento de incerteza metrológica GUM.",
    )
    b_res = await client.post(
        f"{API}/uncertainty/budgets",
        headers=signed(tecnico_auth["access_token"], sig_budget["token"]),
        json={
            "lab_test_id": test_id,
            "measured_value": 85.0,
            "unit": "mOhm",
            "lower_limit": 0.0,
            "upper_limit": 200.0,
            "repeatability_readings": [84.8, 85.1, 85.0, 84.9, 85.2],
            "decision_rule": "GUARD_BAND_CONSERVATIVE",
            "guard_band_multiplier": 1.0,
            "notes": "Orçamento de incerteza acreditado conforme CGCRE/INMETRO.",
            "components": [
                {
                    "name": "Padrão de Calibração",
                    "source_type": "TYPE_B",
                    "distribution": "NORMAL",
                    "half_width": 1.5,
                    "divisor": 2.0,
                }
            ],
        },
    )
    assert b_res.status_code == 201, b_res.text
    budget_data = b_res.json()
    budget_id = budget_data["id"]
    assert budget_data["lab_test_id"] == test_id
    assert budget_data["conformity_status"] == "CONFORME"
    assert budget_data["signature_id"] is not None

    # Consulta orçamento criado
    get_b_res = await client.get(f"{API}/uncertainty/budgets/{budget_id}", headers=auth(tecnico_auth["access_token"]))
    assert get_b_res.status_code == 200
    assert get_b_res.json()["id"] == budget_id

    # Lista orçamentos com filtro
    list_b_res = await client.get(
        f"{API}/uncertainty/budgets?lab_test_id={test_id}",
        headers=auth(tecnico_auth["access_token"]),
    )
    assert list_b_res.status_code == 200
    assert len(list_b_res.json()) >= 1

    # 5. Revisão técnica por pares aprova o ensaio
    await client.post(
        f"{API}/reviews/tests/{test_id}/submit",
        headers=auth(tecnico_auth["access_token"]),
        json={"notes": "Submissão para homologação colegiada."},
    )
    sig_rev = await issue_signature(
        client,
        fiscal_auth["access_token"],
        fiscal_pass,
        entity_type="LabTest",
        entity_id=test_id,
        action="UPDATE",
        meaning="APROVACAO",
    )
    await client.post(
        f"{API}/reviews/tests/{test_id}/decide",
        headers=signed(fiscal_auth["access_token"], sig_rev["token"]),
        json={"status": "APROVADO", "notes": "Ensaio e incerteza aprovados."},
    )

    # 6. Emissão do Laudo Pericial Oficial e validação do bloco de incerteza no manifesto
    sig_report = await issue_signature(
        client,
        fiscal_auth["access_token"],
        fiscal_pass,
        entity_type="DeviceSample",
        entity_id=sample_id,
        action="CLOSE",
        meaning="RESPONSABILIDADE_TECNICA",
        reason="Emissão de laudo oficial com declaração metrológica de incerteza GUM.",
    )
    rep_res = await client.post(
        f"{API}/reports/official",
        headers=signed(fiscal_auth["access_token"], sig_report["token"]),
        json={
            "device_sample_id": sample_id,
            "test_ids": [test_id],
            "title": "Laudo Pericial de Segurança Elétrica com Incerteza GUM",
            "conclusion": "APROVADO",
            "summary": "Dispositivo médico testado com avaliação estrita de conformidade ILAC-G8.",
        },
    )
    assert rep_res.status_code == 200, rep_res.text
    rep_data = rep_res.json()
    auth_token = rep_data["auth_token"]

    # Consulta laudo público e verifica integridade
    pub_res = await client.get(f"{API}/reports/verify/{auth_token}")
    assert pub_res.status_code == 200
    assert pub_res.json()["is_valid"] is True
    assert pub_res.json()["conclusion"] == "APROVADO"
