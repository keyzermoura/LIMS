"""Testes das migrações Alembic contra PostgreSQL real (upgrade/downgrade).

A suíte de integração usa `create_all` + scripts SQL; ela NÃO exercita as
migrações. Estes testes preenchem essa lacuna: cada teste cria um banco
descartável, executa o Alembic como em produção (processo separado, lendo
`DATABASE_URL`) e remove o banco ao final.

Só rodam com `LIMS_TEST_DATABASE_URL` apontando para um PostgreSQL cujo usuário
possa criar bancos (o serviço `postgres` do CI cumpre isso).
"""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import AsyncIterator
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool

POSTGRES_URL = os.getenv("LIMS_TEST_DATABASE_URL")
BACKEND_DIR = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(
    not POSTGRES_URL, reason="requer LIMS_TEST_DATABASE_URL (PostgreSQL real)"
)

PRE_PHASE1 = "0003_audit_export"
PHASE1 = "0004_fase1_solic_receb"
PHASE2 = "0005_fase2_execucao_lab"
PHASE3 = "0006_fase3_revisao_laudos"

PHASE1_TABLES = {
    "solicitations",
    "solicitation_items",
    "receipts",
    "receipt_items",
    "custody_objects",
    "custody_events",
    "checklist_templates",
    "checklist_criteria",
    "checklist_answers",
    "receipt_decisions",
    "coordination_reviews",
}
PHASE1_ENUMS = {
    "solicitation_status",
    "receipt_status",
    "presentation_status",
    "conference_status",
    "receipt_decision",
    "custody_object_status",
    "custody_event_type",
    "criterion_class",
    "checklist_result",
    "coordination_review_status",
}

PHASE2_TABLES = {
    "test_methods",
    "laboratory_equipment",
    "test_executions",
}
PHASE2_ENUMS = {
    "equipment_calibration_status",
    "execution_status",
}

PHASE3_TABLES = {
    "test_reviews",
    "official_reports",
    "test_attachments",
}


def _alembic(url: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=BACKEND_DIR,
        env={**os.environ, "DATABASE_URL": url},
        capture_output=True,
        text=True,
        timeout=240,
        check=False,
    )


def _ok(url: str, *args: str) -> str:
    result = _alembic(url, *args)
    assert result.returncode == 0, (
        f"alembic {' '.join(args)} falhou ({result.returncode})\n"
        f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
    )
    return result.stdout + result.stderr


@pytest.fixture
async def migration_url() -> AsyncIterator[str]:
    """Banco PostgreSQL descartável, isolado por teste."""
    assert POSTGRES_URL
    base = make_url(POSTGRES_URL)
    name = f"lims_mig_{uuid4().hex[:12]}"
    admin = create_async_engine(base, isolation_level="AUTOCOMMIT", poolclass=NullPool)
    async with admin.connect() as conn:
        await conn.execute(text(f'CREATE DATABASE "{name}"'))
    try:
        yield base.set(database=name).render_as_string(hide_password=False)
    finally:
        async with admin.connect() as conn:
            await conn.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
        await admin.dispose()


def _engine(url: str) -> AsyncEngine:
    return create_async_engine(url, poolclass=NullPool)


async def _scalars(url: str, sql: str, **params: object) -> list[object]:
    engine = _engine(url)
    try:
        async with engine.connect() as conn:
            return list((await conn.execute(text(sql), params)).scalars())
    finally:
        await engine.dispose()


async def _tables(url: str) -> set[str]:
    rows = await _scalars(
        url, "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
    )
    return {str(r) for r in rows}


async def _enum_counts(url: str) -> dict[str, int]:
    rows = await _scalars(
        url,
        "SELECT typname FROM pg_type t JOIN pg_namespace n ON n.oid = t.typnamespace "
        "WHERE t.typtype = 'e' AND n.nspname = 'public'",
    )
    counts: dict[str, int] = {}
    for r in rows:
        counts[str(r)] = counts.get(str(r), 0) + 1
    return counts


async def _insert_legacy_sample(url: str, *, serial: str | None, lot: str | None) -> None:
    """Insere usuário e amostra no schema pré-Fase 1 (colunas legadas)."""
    user_id, sample_id = uuid4(), uuid4()
    engine = _engine(url)
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO users (id, username, email, full_name, role, "
                    "hashed_password, is_active, password_changed_at) VALUES "
                    "(:id, :u, :e, 'Usuario Legado', 'TECNICO', 'x', true, now())"
                ),
                {"id": user_id, "u": f"legado_{uuid4().hex[:6]}", "e": f"{uuid4().hex[:6]}@x.org"},
            )
            await conn.execute(
                text(
                    "INSERT INTO device_samples (id, accession_number, serial_number, "
                    "lot_number, manufacturer, commercial_name, status, received_at, "
                    "received_by_id, version) VALUES (:id, :acc, :serial, :lot, 'Fab', "
                    "'Produto', 'RECEBIDO', now(), :uid, 1)"
                ),
                {
                    "id": sample_id,
                    "acc": f"LIMS-2026-{uuid4().hex[:6].upper()}",
                    "serial": serial,
                    "lot": lot,
                    "uid": user_id,
                },
            )
    finally:
        await engine.dispose()


async def test_upgrade_head_creates_schema_without_drift(migration_url: str) -> None:
    _ok(migration_url, "upgrade", "head")

    assert await _tables(migration_url) >= (PHASE1_TABLES | PHASE2_TABLES | PHASE3_TABLES)

    # Cada enum nativo deve existir exatamente uma vez (regressão: receipt_decision
    # é compartilhado por duas tabelas e já foi criado em duplicidade).
    counts = await _enum_counts(migration_url)
    for enum_name in (PHASE1_ENUMS | PHASE2_ENUMS):
        assert counts.get(enum_name) == 1, f"enum {enum_name}: {counts.get(enum_name)}"

    # Guardas de imutabilidade da migração 0002 continuam presentes.
    triggers = await _scalars(
        migration_url,
        "SELECT tgname FROM pg_trigger WHERE tgname = 'trg_audit_logs_append_only'",
    )
    assert triggers

    assert PHASE3 in _ok(migration_url, "current")
    # Paridade metadata x migrações: acusa índices, defaults ou tipos divergentes.
    _ok(migration_url, "check")


async def test_downgrade_is_reversible(migration_url: str) -> None:
    _ok(migration_url, "upgrade", "head")
    _ok(migration_url, "downgrade", PRE_PHASE1)

    tables = await _tables(migration_url)
    assert not ((PHASE1_TABLES | PHASE2_TABLES | PHASE3_TABLES) & tables)
    assert {"users", "device_samples", "audit_logs"} <= tables
    counts = await _enum_counts(migration_url)
    assert not ((PHASE1_ENUMS | PHASE2_ENUMS) & set(counts))

    nullable = await _scalars(
        migration_url,
        "SELECT is_nullable FROM information_schema.columns "
        "WHERE table_schema = 'public' AND table_name = 'device_samples' "
        "AND column_name IN ('lot_number', 'serial_number') ORDER BY column_name",
    )
    assert nullable == ["NO", "NO"]

    _ok(migration_url, "upgrade", "head")  # reaplicável após reversão


async def test_additive_migration_preserves_legacy_rows(migration_url: str) -> None:
    _ok(migration_url, "upgrade", PRE_PHASE1)
    await _insert_legacy_sample(migration_url, serial="SN-1", lot="L-1")

    _ok(migration_url, "upgrade", "head")
    rows = await _scalars(
        migration_url,
        "SELECT serial_number FROM device_samples WHERE solicitation_id IS NULL "
        "AND origin_custody_object_id IS NULL",
    )
    assert rows == ["SN-1"]

    _ok(migration_url, "downgrade", PRE_PHASE1)
    assert await _scalars(migration_url, "SELECT serial_number FROM device_samples") == ["SN-1"]


async def test_downgrade_refuses_when_it_would_lose_data(migration_url: str) -> None:
    _ok(migration_url, "upgrade", "head")
    # Série/lote opcionais só passam a existir após a Fase 1.
    await _insert_legacy_sample(migration_url, serial=None, lot=None)

    result = _alembic(migration_url, "downgrade", PRE_PHASE1)
    assert result.returncode != 0
    assert "sem serial_number/lot_number" in result.stdout + result.stderr

    # A falha é transacional: nada foi desfeito pela metade.
    assert await _tables(migration_url) >= PHASE1_TABLES
    current = _ok(migration_url, "current")
    assert PHASE1 in current or PHASE2 in current or PHASE3 in current
