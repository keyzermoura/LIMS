"""Testes automatizados do Horizonte 3 — Sprint 8.4: Conectores BI, Exportação por Cursor e UI (H3.4).

Conforme ESPECIFICACAO_CAMADA_INTEGRACAO_LIMS.md §6 e §10 (Gate G-D).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.device_sample import DeviceSample
from app.models.electronic_signature import ElectronicSignature
from app.models.enums import (
    SampleStatus,
    SignatureAction,
    SignatureMeaning,
    TestOutcome,
    TestStatus,
)
from app.models.lab_test import LabTest
from app.models.official_report import OfficialReport
from app.models.user import User
from app.services.integration_export_service import decode_cursor, encode_cursor

TestStatus.__test__ = False  # Evita pytest collection warning
TestOutcome.__test__ = False

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


def test_cursor_encoding_and_decoding() -> None:
    """Valida serialização e deserialização determinística do cursor base64 opaco."""
    now = datetime(2026, 11, 17, 15, 30, 0, tzinfo=UTC)
    uid = uuid4()

    cursor = encode_cursor(now, uid)
    assert isinstance(cursor, str)
    assert len(cursor) > 10

    decoded = decode_cursor(cursor)
    assert decoded is not None
    dt, parsed_uid = decoded
    assert dt == now
    assert parsed_uid == uid

    # Cursor inválido deve retornar None sem estourar exceção
    assert decode_cursor("cursor_invalido_sem_pipe") is None
    assert decode_cursor("") is None


@pytest.mark.asyncio
async def test_export_tests_cursor_pagination(
    db_factory: async_sessionmaker[AsyncSession],
    client: AsyncClient,
    users: dict[str, dict[str, Any]],
) -> None:
    """Valida paginação estável por cursor determinístico nos ensaios laboratoriais."""
    login_tecnico = await login(client, "tecnico", "Tecnico@Lims2026")
    tecnico_headers = auth(login_tecnico["access_token"])

    async with db_factory() as session:
        admin_user = (await session.execute(select(User).where(User.username == "admin"))).scalar_one()

        sample = DeviceSample(
            accession_number=f"ACC-BI-{uuid4().hex[:6]}",
            commercial_name="Cateter Guia 6F",
            manufacturer="MedTech Global",
            status=SampleStatus.EM_TESTE,
            received_by_id=admin_user.id,
        )
        session.add(sample)
        await session.flush()

        for i in range(3):
            test = LabTest(
                device_sample_id=sample.id,
                name=f"Ensaio BI HPLC #{i+1}",
                unit="%",
                status=TestStatus.CONCLUIDO,
                outcome=TestOutcome.APROVADO,
                result_value=Decimal(f"99.{i+1}"),
            )
            session.add(test)
        await session.commit()

    # 1. Página 1 com limit=2
    res_p1 = await client.get(
        f"{API}/integration/exports/tests?limit=2",
        headers=tecnico_headers,
    )
    assert res_p1.status_code == 200, res_p1.text
    p1 = res_p1.json()
    assert p1["count"] == 2
    assert p1["has_more"] is True
    assert p1["next_cursor"] is not None
    assert len(p1["items"]) == 2

    # 2. Página 2 usando cursor
    cursor = p1["next_cursor"]
    res_p2 = await client.get(
        f"{API}/integration/exports/tests?limit=2&cursor={cursor}",
        headers=tecnico_headers,
    )
    assert res_p2.status_code == 200, res_p2.text
    p2 = res_p2.json()
    assert len(p2["items"]) >= 1

    p1_ids = {item["id"] for item in p1["items"]}
    p2_ids = {item["id"] for item in p2["items"]}
    assert p1_ids.isdisjoint(p2_ids)


@pytest.mark.asyncio
async def test_export_reports_and_content_negotiation(
    db_factory: async_sessionmaker[AsyncSession],
    client: AsyncClient,
    users: dict[str, dict[str, Any]],
) -> None:
    """Valida exportação de laudos oficiais e negociação de conteúdo via Accept header."""
    login_fiscal = await login(client, "fiscal", "Fiscal@Lims2026")
    fiscal_headers = auth(login_fiscal["access_token"])
    fiscal_headers["Accept"] = "application/vnd.lims.v1+json"

    async with db_factory() as session:
        admin_user = (await session.execute(select(User).where(User.username == "admin"))).scalar_one()

        sample = DeviceSample(
            accession_number=f"ACC-REP-{uuid4().hex[:6]}",
            commercial_name="Stent Coronário",
            manufacturer="StentCorp Brasil",
            status=SampleStatus.APROVADO,
            received_by_id=admin_user.id,
        )
        session.add(sample)
        await session.flush()

        sig = ElectronicSignature(
            user_id=admin_user.id,
            username_snapshot=admin_user.username,
            full_name_snapshot=admin_user.full_name,
            role_snapshot=admin_user.role.value,
            entity_type="official_reports",
            entity_id=str(uuid4()),
            action=SignatureAction.CREATE,
            meaning=SignatureMeaning.APROVACAO,
            reason="Homologação pericial",
            manifest={"test": "ok"},
            manifest_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            token_jti=uuid4().hex,
            expires_at=datetime.now(UTC) + timedelta(minutes=15),
        )
        session.add(sig)
        await session.flush()

        report = OfficialReport(
            report_number=f"LAUDO-BI-{uuid4().hex[:6]}",
            device_sample_id=sample.id,
            issued_by_id=admin_user.id,
            signature_id=sig.id,
            auth_token=uuid4().hex,
            title="Laudo Pericial Oficial para Exportação BI",
            conclusion=TestOutcome.APROVADO,
            sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            is_latest=True,
            version=1,
        )
        session.add(report)
        await session.commit()

    res = await client.get(
        f"{API}/integration/exports/reports?limit=10",
        headers=fiscal_headers,
    )
    assert res.status_code == 200, res.text
    assert "application/vnd.lims.v1+json" in res.headers.get("content-type", "")

    data = res.json()
    assert len(data["items"]) >= 1
    found = any("LAUDO-BI" in rep["report_number"] for rep in data["items"])
    assert found is True


@pytest.mark.asyncio
async def test_export_samples_and_qc_metrics(
    client: AsyncClient,
    users: dict[str, dict[str, Any]],
) -> None:
    """Valida exportação de amostras e agregado de métricas analíticas de qualidade."""
    login_admin = await login(client, "admin", "Admin@Lims2026")
    admin_headers = auth(login_admin["access_token"])

    # 1. Exportação de amostras
    res_samples = await client.get(
        f"{API}/integration/exports/samples?limit=10",
        headers=admin_headers,
    )
    assert res_samples.status_code == 200, res_samples.text
    samples_data = res_samples.json()
    assert "items" in samples_data
    assert "count" in samples_data

    # 2. Resumo de métricas analíticas (QC metrics)
    res_metrics = await client.get(
        f"{API}/integration/exports/qc-metrics",
        headers=admin_headers,
    )
    assert res_metrics.status_code == 200, res_metrics.text
    metrics = res_metrics.json()
    assert "total_tests" in metrics
    assert "tests_by_status" in metrics
    assert "total_official_reports" in metrics
    assert "open_oos_count" in metrics
    assert "generated_at" in metrics


@pytest.mark.asyncio
async def test_service_client_m2m_export_access_with_scopes(
    client: AsyncClient,
    users: dict[str, dict[str, Any]],
) -> None:
    """Valida que uma credencial de serviço M2M com escopos autorizados acessa a exportação analítica."""
    login_admin = await login(client, "admin", "Admin@Lims2026")
    admin_headers = auth(login_admin["access_token"])

    # 1. Criar serviço M2M com escopos reports:read e tests:read
    res_client = await client.post(
        f"{API}/service-clients",
        json={
            "name": "Pipeline Data Lake Corporativo",
            "scopes": ["reports:read", "tests:read"],
            "expires_in_days": 30,
        },
        headers=admin_headers,
    )
    assert res_client.status_code == 201, res_client.text
    creds = res_client.json()

    # 2. Obter token M2M
    res_token = await client.post(
        f"{API}/auth/service-token",
        json={
            "client_id": creds["client_id"],
            "client_secret": creds["client_secret"],
        },
    )
    assert res_token.status_code == 200, res_token.text
    token_m2m = res_token.json()["access_token"]
    service_headers = auth(token_m2m)

    # 3. Acessar endpoints autorizados
    res_exp = await client.get(
        f"{API}/integration/exports/tests?limit=5",
        headers=service_headers,
    )
    assert res_exp.status_code == 200, res_exp.text

    # 4. Criar serviço M2M SEM os escopos de leitura analítica
    res_client_unauth = await client.post(
        f"{API}/service-clients",
        json={
            "name": "Serviço Balança Somente Escrita",
            "scopes": ["instrument:write"],
            "expires_in_days": 30,
        },
        headers=admin_headers,
    )
    assert res_client_unauth.status_code == 201, res_client_unauth.text
    creds_unauth = res_client_unauth.json()

    res_token_unauth = await client.post(
        f"{API}/auth/service-token",
        json={
            "client_id": creds_unauth["client_id"],
            "client_secret": creds_unauth["client_secret"],
        },
    )
    token_unauth = res_token_unauth.json()["access_token"]

    # Tentativa de acesso sem o escopo deve ser bloqueada com 403 Forbidden
    res_forbidden = await client.get(
        f"{API}/integration/exports/tests?limit=5",
        headers=auth(token_unauth),
    )
    assert res_forbidden.status_code == 403, res_forbidden.text
