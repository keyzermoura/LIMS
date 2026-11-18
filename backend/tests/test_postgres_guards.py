"""Garantias que só existem em PostgreSQL: triggers, sequences e advisory lock.

Estes testes são ignorados quando `LIMS_TEST_DATABASE_URL` não está definido.
Cada teste roda em um schema exclusivo, já com `app/db/sql/*.sql` aplicado.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.dialect import next_sequence
from app.models.audit_log import AuditLog
from app.models.enums import AuditAction
from app.services import audit_service

pytestmark = pytest.mark.skipif(
    not os.getenv("LIMS_TEST_DATABASE_URL"),
    reason="Requer PostgreSQL (defina LIMS_TEST_DATABASE_URL).",
)

API = "/api/v1"


async def login(client: AsyncClient, username: str, password: str) -> dict[str, Any]:
    response = await client.post(
        f"{API}/auth/login", data={"username": username, "password": password}
    )
    assert response.status_code == 200, response.text
    return response.json()


async def _append_event(factory: async_sessionmaker[AsyncSession], username: str) -> None:
    async with factory() as db:
        await audit_service.append(
            db,
            action=AuditAction.CREATE,
            entity_type="DeviceSample",
            entity_id=str(uuid4()),
            actor_username=username,
        )
        await db.commit()


async def _expect_guard(
    factory: async_sessionmaker[AsyncSession],
    statement: str,
    *,
    message: str,
    params: dict[str, Any] | None = None,
) -> None:
    async with factory() as db:
        with pytest.raises(DBAPIError, match=message):
            await db.execute(text(statement), params or {})
            await db.commit()
        await db.rollback()


async def test_audit_log_blocks_update_delete_and_truncate(
    db_factory: async_sessionmaker[AsyncSession],
) -> None:
    await _append_event(db_factory, "SYSTEM")

    await _expect_guard(
        db_factory,
        "UPDATE audit_logs SET reason = 'adulterado' WHERE sequence = 1",
        message="append-only",
    )
    await _expect_guard(
        db_factory,
        "DELETE FROM audit_logs WHERE sequence = 1",
        message="append-only",
    )
    await _expect_guard(
        db_factory,
        "TRUNCATE TABLE audit_logs",
        message="append-only",
    )

    async with db_factory() as db:
        assert await db.scalar(select(AuditLog.sequence)) == 1
        report = await audit_service.verify_chain(db)
        assert report["ok"] is True


async def test_electronic_signature_manifest_is_immutable(
    client: AsyncClient,
    users,
    db_factory: async_sessionmaker[AsyncSession],
) -> None:
    fiscal = await login(client, "fiscal", users["fiscal"]["password"])
    response = await client.post(
        f"{API}/auth/sign",
        headers={"Authorization": f"Bearer {fiscal['access_token']}"},
        json={
            "password": users["fiscal"]["password"],
            "meaning": "AUTORIA",
            "reason": "Assinatura criada para validar imutabilidade do manifesto.",
            "entity_type": "DeviceSample",
            "entity_id": str(uuid4()),
            "action": "CREATE",
        },
    )
    assert response.status_code == 200, response.text
    signature_id = response.json()["signature_id"]

    await _expect_guard(
        db_factory,
        "UPDATE electronic_signatures SET reason = 'outro motivo' WHERE id = :id",
        message="Manifesto de assinatura eletronica e imutavel",
        params={"id": signature_id},
    )
    await _expect_guard(
        db_factory,
        "DELETE FROM electronic_signatures WHERE id = :id",
        message="Assinaturas eletronicas nao podem ser removidas",
        params={"id": signature_id},
    )


async def test_native_sequences_are_monotonic(
    db_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with db_factory() as db:
        assert await next_sequence(db, "sample_accession_seq") == 1
        assert await next_sequence(db, "sample_accession_seq") == 2
        assert await next_sequence(db, "capa_code_seq") == 1
        assert await next_sequence(db, "official_report_seq") == 1
        assert await next_sequence(db, "official_report_seq") == 2
        await db.commit()


async def test_advisory_lock_serializes_the_hash_chain(
    db_factory: async_sessionmaker[AsyncSession],
) -> None:
    await asyncio.gather(*(_append_event(db_factory, f"WORKER-{index}") for index in range(8)))

    async with db_factory() as db:
        sequences = (await db.scalars(select(AuditLog.sequence).order_by(AuditLog.sequence))).all()
        assert list(sequences) == list(range(1, 9))
        report = await audit_service.verify_chain(db)
        assert report["ok"] is True
        assert report["checked"] == 8


async def _fetch_schema_triggers(db: AsyncSession) -> set[str]:
    """Retorna nomes de triggers não-internas pertencentes exclusivamente ao schema corrente."""
    rows = await db.scalars(
        text(
            "SELECT t.tgname "
            "FROM pg_trigger t "
            "JOIN pg_class c ON c.oid = t.tgrelid "
            "JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname = current_schema() "
            "AND NOT t.tgisinternal "
            "AND t.tgname LIKE 'trg_%'"
        )
    )
    return set(rows.all())


async def test_trigger_parity_phase5(
    db_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Valida paridade total de guardas DDL instaladas no schema isolado de teste."""
    expected_triggers = {
        "trg_audit_logs_append_only",
        "trg_audit_logs_no_truncate",
        "trg_lab_test_results_append_only",
        "trg_custody_append_only",
        "trg_esignature_guard",
        "trg_device_samples_no_delete",
        "trg_lab_tests_no_delete",
        "trg_capa_no_delete",
        "trg_official_reports_guard",
        "trg_test_executions_freeze",
        "trg_test_reviews_freeze",
        "trg_test_attachments_append_only",
        "trg_instrument_data_guard",
        "trg_training_records_append_only",
        "trg_custody_events_append_only",
        "trg_solicitations_no_delete",
        "trg_solicitation_items_no_delete",
        "trg_receipts_no_delete",
        "trg_receipt_items_no_delete",
        "trg_custody_objects_no_delete",
        "trg_receipt_decisions_no_delete",
        "trg_coordination_reviews_no_delete",
        "trg_analyst_qualifications_no_delete",
    }
    async with db_factory() as db:
        schema = await db.scalar(text("SELECT current_schema()"))
        assert isinstance(schema, str) and schema.startswith("lims_test_")
        triggers = await _fetch_schema_triggers(db)
        missing = expected_triggers - triggers
        assert not missing, f"Triggers ausentes no schema {schema}: {sorted(missing)}"


async def test_trigger_lookup_ignores_other_schemas_and_detects_missing_trigger(
    db_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Comprova que trigger em outro schema não mascara ausência no schema de teste."""
    extra_schema = f"lims_other_{uuid4().hex[:12]}"
    async with db_factory() as db:
        try:
            await db.execute(text(f'CREATE SCHEMA "{extra_schema}"'))
            await db.execute(text(f'CREATE TABLE "{extra_schema}".dummy_reports (id integer)'))
            await db.execute(
                text(
                    f'CREATE OR REPLACE FUNCTION "{extra_schema}".dummy_guard() RETURNS trigger '
                    "LANGUAGE plpgsql AS $$ BEGIN RETURN NEW; END; $$"
                )
            )
            await db.execute(
                text(
                    "CREATE TRIGGER trg_official_reports_guard "
                    f'BEFORE UPDATE ON "{extra_schema}".dummy_reports '
                    f'FOR EACH ROW EXECUTE FUNCTION "{extra_schema}".dummy_guard()'
                )
            )
            await db.execute(text("DROP TRIGGER trg_official_reports_guard ON official_reports"))

            other_triggers = set(
                (
                    await db.scalars(
                        text(
                            "SELECT t.tgname "
                            "FROM pg_trigger t "
                            "JOIN pg_class c ON c.oid = t.tgrelid "
                            "JOIN pg_namespace n ON n.oid = c.relnamespace "
                            "WHERE n.nspname = :schema AND NOT t.tgisinternal"
                        ),
                        {"schema": extra_schema},
                    )
                ).all()
            )
            assert "trg_official_reports_guard" in other_triggers

            triggers = await _fetch_schema_triggers(db)
            assert "trg_official_reports_guard" not in triggers
        finally:
            await db.rollback()
            await db.execute(text(f'DROP SCHEMA IF EXISTS "{extra_schema}" CASCADE'))
            await db.commit()
