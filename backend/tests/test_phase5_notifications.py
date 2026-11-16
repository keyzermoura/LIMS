"""Suíte de Testes da Fase 5: Central de Notificações e Alertas em Tempo Real (Sprint 5.2).

Valida:
1. Emissão e entrega de notificações com direcionamento individual e por perfil (RBAC).
2. Marcação individual e em lote de leitura (is_read, read_at).
3. Sumário em tempo real de contagem e distribuição por severidade (INFO, WARNING, CRITICAL).
4. Varredura proativa de desvios laboratoriais (calibração vencida/vencendo, competência, CAPA e TAT).
5. Idempotência na emissão periódica de alertas do sistema.
6. Proteção de autenticação em todos os endpoints de notificação.
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest
from httpx import AsyncClient

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
async def test_notifications_require_authentication(client: AsyncClient) -> None:
    """Garante que endpoints de notificação rejeitam acessos anônimos."""
    res_list = await client.get(f"{API}/notifications")
    assert res_list.status_code == 401

    res_sum = await client.get(f"{API}/notifications/summary")
    assert res_sum.status_code == 401

    res_read = await client.patch(f"{API}/notifications/{uuid4()}/read")
    assert res_read.status_code == 401


@pytest.mark.asyncio
async def test_notification_creation_and_rbac_delivery(
    client: AsyncClient, users: dict[str, Any]
) -> None:
    """Valida criação manual de alerta e entrega direcionada por perfil e individual."""
    tec_token = (
        await login(client, "tecnico", users["tecnico"]["password"])
    )["access_token"]
    fisc_token = (
        await login(client, "fiscal", users["fiscal"]["password"])
    )["access_token"]

    # 1. Cria notificação direcionada a TECNICO
    payload_tec = {
        "title": "Verificação de Balança Analítica",
        "message": "Realizar checagem de zero da balança BAL-01 antes do início dos ensaios.",
        "severity": "WARNING",
        "category": "CALIBRATION",
        "target_role": "TECNICO",
        "link_url": "/equipment",
    }
    res_create = await client.post(
        f"{API}/notifications",
        headers=auth(tec_token),
        json=payload_tec,
    )
    assert res_create.status_code == 201, res_create.text
    created = res_create.json()
    notif_id = created["id"]
    assert created["severity"] == "WARNING"
    assert created["is_read"] is False

    # 2. Técnico deve ver a notificação em sua lista
    res_list_tec = await client.get(
        f"{API}/notifications",
        headers=auth(tec_token),
    )
    assert res_list_tec.status_code == 200
    tec_items = res_list_tec.json()
    assert any(it["id"] == notif_id for it in tec_items)

    # 3. Fiscal não deve ver a notificação direcionada exclusivamente a técnicos
    res_list_fisc = await client.get(
        f"{API}/notifications",
        headers=auth(fisc_token),
    )
    assert res_list_fisc.status_code == 200
    fisc_items = res_list_fisc.json()
    assert not any(it["id"] == notif_id for it in fisc_items)

    # 4. Técnico marca como lida
    res_read = await client.patch(
        f"{API}/notifications/{notif_id}/read",
        headers=auth(tec_token),
    )
    assert res_read.status_code == 200
    updated = res_read.json()
    assert updated["is_read"] is True
    assert updated["read_at"] is not None


@pytest.mark.asyncio
async def test_notifications_summary_and_mark_all_read(
    client: AsyncClient, users: dict[str, Any]
) -> None:
    """Valida o cálculo do sumário de severidades e o comando de marcar todas como lidas."""
    adm_token = (
        await login(client, "admin", users["admin"]["password"])
    )["access_token"]

    # Emite 2 notificações com severidades distintas para ADMIN
    await client.post(
        f"{API}/notifications",
        headers=auth(adm_token),
        json={
            "title": "Alerta Crítico Teste",
            "message": "Parâmetro crítico fora da faixa.",
            "severity": "CRITICAL",
            "category": "SAMPLE_ISSUE",
            "target_role": "ADMIN",
        },
    )
    await client.post(
        f"{API}/notifications",
        headers=auth(adm_token),
        json={
            "title": "Informativo Teste",
            "message": "Novo procedimento operacional padrão publicado.",
            "severity": "INFO",
            "category": "SYSTEM",
            "target_role": "ADMIN",
        },
    )

    # Consulta sumário
    res_sum = await client.get(
        f"{API}/notifications/summary",
        headers=auth(adm_token),
    )
    assert res_sum.status_code == 200
    summary = res_sum.json()
    assert summary["unread_count"] >= 2
    assert summary["critical_count"] >= 1
    assert summary["info_count"] >= 1

    # Marca todas como lidas
    res_read_all = await client.post(
        f"{API}/notifications/read-all",
        headers=auth(adm_token),
    )
    assert res_read_all.status_code == 200
    assert res_read_all.json()["marked_count"] >= 2

    # Verifica que unread_count agora é 0
    res_sum_after = await client.get(
        f"{API}/notifications/summary",
        headers=auth(adm_token),
    )
    assert res_sum_after.json()["unread_count"] == 0


@pytest.mark.asyncio
async def test_proactive_system_alerts_sweep(
    client: AsyncClient, users: dict[str, Any]
) -> None:
    """Valida a varredura proativa de desvios laboratoriais e a garantia de idempotência."""
    tec_token = (
        await login(client, "tecnico", users["tecnico"]["password"])
    )["access_token"]

    # 1. Primeira execução da varredura
    res_sweep1 = await client.post(
        f"{API}/notifications/check-alerts",
        headers=auth(tec_token),
    )
    assert res_sweep1.status_code == 200
    data1 = res_sweep1.json()
    assert "alerts_generated" in data1
    assert "details" in data1

    # 2. Segunda execução imediata não deve duplicar alertas (idempotência 24h)
    res_sweep2 = await client.post(
        f"{API}/notifications/check-alerts",
        headers=auth(tec_token),
    )
    assert res_sweep2.status_code == 200
    data2 = res_sweep2.json()
    assert data2["alerts_generated"] == 0
