"""Suíte de Testes da Fase 5: Painéis Gerenciais, BI e Controle Metrológico (Sprint 5.1).

Valida:
1. Agregação analítica de Turnaround Time (TAT) por etapa e global.
2. Estratificação de backlog de amostras por faixa de envelhecimento.
3. Indicadores de conformidade analítica e eficácia de CAPAs (ISO 17025 §8.7 e §8.8).
4. Cartas de Controle de Shewhart / Levey-Jennings com limites +-2s e +-3s (ISO 17025 §7.7).
5. Avaliação multiregra de Westgard (1_3s, 2_2s, R_4s, 4_1s, 10_x) para controle estatístico.
6. Requisito de autenticação segura para acesso aos endpoints analíticos.
"""

from __future__ import annotations

from typing import Any

import pytest
from httpx import AsyncClient

from app.services.analytics_service import _evaluate_westgard

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
async def test_analytics_requires_authentication(client: AsyncClient) -> None:
    """Garante que os endpoints de BI não podem ser acessados anonimamente."""
    res_op = await client.get(f"{API}/analytics/operational")
    assert res_op.status_code == 401

    res_qc = await client.get(f"{API}/analytics/quality-control")
    assert res_qc.status_code == 401


@pytest.mark.asyncio
async def test_operational_analytics_payload(
    client: AsyncClient, users: dict[str, Any]
) -> None:
    """Valida a estrutura completa e integridade do payload de métricas operacionais."""
    adm_token = (
        await login(client, "admin", users["admin"]["password"])
    )["access_token"]

    res = await client.get(
        f"{API}/analytics/operational",
        headers=auth(adm_token),
    )
    assert res.status_code == 200, res.text
    data = res.json()

    # Valida blocos estruturais
    assert "turnaround_time" in data
    assert "sample_backlog" in data
    assert "test_conformity" in data
    assert "capa_metrics" in data
    assert "analysts_workload" in data
    assert "equipment_status_summary" in data

    # Valida TAT
    tat = data["turnaround_time"]
    assert tat["global_avg_hours"] >= 0.0
    assert tat["receipt_to_testing_avg_hours"] >= 0.0
    assert tat["testing_to_review_avg_hours"] >= 0.0
    assert tat["review_to_report_avg_hours"] >= 0.0

    # Valida Backlog
    backlog = data["sample_backlog"]
    assert backlog["age_0_to_5_days"] >= 0
    assert backlog["age_6_to_15_days"] >= 0
    assert backlog["age_above_15_days"] >= 0
    assert backlog["total_active"] >= 0

    # Valida Conformidade
    conf = data["test_conformity"]
    assert conf["total_tests"] >= 0
    assert 0.0 <= conf["conformity_rate_pct"] <= 100.0

    # Valida CAPA
    capa = data["capa_metrics"]
    assert capa["total_capas"] >= 0
    assert 0.0 <= capa["effectiveness_rate_pct"] <= 100.0


@pytest.mark.asyncio
async def test_quality_control_chart_payload(
    client: AsyncClient, users: dict[str, Any]
) -> None:
    """Valida os parâmetros da Carta de Controle de Shewhart e limites estatísticos."""
    tec_token = (
        await login(client, "tecnico", users["tecnico"]["password"])
    )["access_token"]

    res = await client.get(
        f"{API}/analytics/quality-control",
        headers=auth(tec_token),
    )
    assert res.status_code == 200, res.text
    data = res.json()

    # Valida parâmetros da carta
    assert "method_name" in data
    assert "mean" in data
    assert "standard_deviation" in data
    assert data["standard_deviation"] > 0
    assert data["warning_limit_upper"] > data["mean"]
    assert data["warning_limit_lower"] < data["mean"]
    assert data["action_limit_upper"] > data["warning_limit_upper"]
    assert data["action_limit_lower"] < data["warning_limit_lower"]

    # Valida pontos de controle
    assert len(data["data_points"]) >= 8
    for pt in data["data_points"]:
        assert "run_number" in pt
        assert "measured_at" in pt
        assert "value" in pt
        assert "operator_name" in pt


def test_westgard_rules_engine() -> None:
    """Valida a detecção matemática exata das violações de regras multiregra de Westgard."""
    mean = 100.0
    std_dev = 1.0

    # 1. Violação 1_3s (ponto excede 3 desvios padrão)
    vals_1_3s = [100.1, 99.9, 103.5, 100.0]  # ponto 3 = 103.5 > 103.0
    pt_viols, viols = _evaluate_westgard(vals_1_3s, mean, std_dev)
    assert pt_viols[2] == "1_3s"
    assert any(v.rule_code == "1_3s" for v in viols)

    # 2. Violação 2_2s (dois pontos consecutivos excedem 2s no mesmo lado)
    vals_2_2s = [100.0, 102.2, 102.3, 100.0]
    pt_viols, viols = _evaluate_westgard(vals_2_2s, mean, std_dev)
    assert pt_viols[2] == "2_2s"
    assert any(v.rule_code == "2_2s" for v in viols)

    # 3. Violação R_4s (um ponto > +2s e o seguinte < -2s -> diferença >= 4s)
    vals_r_4s = [100.0, 102.2, 97.8, 100.0]
    pt_viols, viols = _evaluate_westgard(vals_r_4s, mean, std_dev)
    assert pt_viols[2] == "R_4s"
    assert any(v.rule_code == "R_4s" for v in viols)

    # 4. Violação 4_1s (quatro pontos consecutivos além de 1s no mesmo lado)
    vals_4_1s = [101.2, 101.4, 101.3, 101.5]
    pt_viols, viols = _evaluate_westgard(vals_4_1s, mean, std_dev)
    assert pt_viols[3] == "4_1s"
    assert any(v.rule_code == "4_1s" for v in viols)

    # 5. Violação 10_x (dez pontos consecutivos no mesmo lado da média)
    vals_10_x = [100.2] * 10
    pt_viols, viols = _evaluate_westgard(vals_10_x, mean, std_dev)
    assert pt_viols[9] == "10_x"
    assert any(v.rule_code == "10_x" for v in viols)
