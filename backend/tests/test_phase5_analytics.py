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
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

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
async def test_operational_analytics_payload(client: AsyncClient, users: dict[str, Any]) -> None:
    """Valida a estrutura completa e integridade do payload de métricas operacionais sem dados fabricados."""
    adm_token = (await login(client, "admin", users["admin"]["password"]))["access_token"]

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

    # Valida que em banco vazio ou sem dados suficientes, métricas são None (ALCOA+ / H0.6)
    tat = data["turnaround_time"]
    assert tat["data_quality"] in ("sufficient", "insufficient")
    if tat["samples_measured_count"] == 0:
        assert tat["global_avg_hours"] is None
        assert tat["receipt_to_testing_avg_hours"] is None
        assert tat["testing_to_review_avg_hours"] is None
        assert tat["review_to_report_avg_hours"] is None
        assert tat["data_quality"] == "insufficient"
    else:
        assert tat["global_avg_hours"] >= 0.0

    # Valida Backlog
    backlog = data["sample_backlog"]
    assert backlog["age_0_to_5_days"] >= 0
    assert backlog["age_6_to_15_days"] >= 0
    assert backlog["age_above_15_days"] >= 0
    assert backlog["total_active"] >= 0

    # Valida Conformidade
    conf = data["test_conformity"]
    assert conf["total_tests"] >= 0
    if conf["total_tests"] == 0:
        assert conf["conformity_rate_pct"] is None
        assert conf["data_quality"] == "insufficient"
    else:
        assert 0.0 <= conf["conformity_rate_pct"] <= 100.0

    # Valida CAPA
    capa = data["capa_metrics"]
    assert capa["total_capas"] >= 0
    if capa["total_capas"] == 0:
        assert capa["effectiveness_rate_pct"] is None
        assert capa["data_quality"] == "insufficient"
    else:
        assert 0.0 <= capa["effectiveness_rate_pct"] <= 100.0


@pytest.mark.asyncio
async def test_quality_control_chart_payload(client: AsyncClient, users: dict[str, Any]) -> None:
    """Valida os parâmetros da Carta de Controle de Shewhart sem dados sintéticos simulados."""
    tec_token = (await login(client, "tecnico", users["tecnico"]["password"]))["access_token"]

    res = await client.get(
        f"{API}/analytics/quality-control",
        headers=auth(tec_token),
    )
    assert res.status_code == 200, res.text
    data = res.json()

    # Valida parâmetros da carta
    assert "method_name" in data
    assert "data_points" in data
    assert "data_quality" in data
    # Em ambiente sem 20 pontos de ensaio reais, data_quality deve ser insufficient
    if len(data["data_points"]) < 20:
        assert data["data_quality"] == "insufficient"


@pytest.mark.asyncio
async def test_empty_database_returns_no_fabricated_metrics(
    db_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Trava de regressão (H0.6 / Risco 2): banco sem dados não inventa números."""
    from app.services import analytics_service

    async with db_factory() as db:
        result = await analytics_service.get_operational_analytics(db)
        assert result.turnaround_time.global_avg_hours is None
        assert result.turnaround_time.receipt_to_testing_avg_hours is None
        assert result.turnaround_time.testing_to_review_avg_hours is None
        assert result.turnaround_time.review_to_report_avg_hours is None
        assert result.turnaround_time.data_quality == "insufficient"
        assert result.test_conformity.conformity_rate_pct is None
        assert result.test_conformity.data_quality == "insufficient"
        assert result.capa_metrics.effectiveness_rate_pct is None
        assert result.capa_metrics.data_quality == "insufficient"

        qc = await analytics_service.get_quality_control_analytics(db)
        assert qc.data_quality == "insufficient"
        assert len(qc.data_points) == 0


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
