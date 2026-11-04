"""Compatibilidade entre PostgreSQL (produção) e SQLite (testes).

O PostgreSQL usa sequences nativas e advisory locks; o SQLite, usado apenas
em testes de integração, não implementa nenhum dos dois. Este módulo concentra
as duas diferenças para que os serviços de domínio não conheçam o dialeto.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Sequences criadas por `app/db/sql/001_immutability.sql`.
SEQUENCES = frozenset({"sample_accession_seq", "capa_code_seq"})

_SQLITE_COUNTERS_TABLE = "_sequence_counters"


def dialect_name(db: AsyncSession) -> str:
    return db.get_bind().dialect.name


def is_postgres(db: AsyncSession) -> bool:
    return dialect_name(db) == "postgresql"


async def next_sequence(db: AsyncSession, name: str) -> int:
    """Próximo valor da sequence informada.

    No PostgreSQL o valor vem da sequence nativa. No SQLite (testes) usamos
    uma tabela auxiliar com UPSERT atômico, preservando a mesma semântica de
    contador monotônico observada pelos serviços.
    """
    if name not in SEQUENCES:
        raise ValueError(f"Sequência desconhecida: {name}")

    if is_postgres(db):
        # `name` é validado contra a allowlist acima; não há interpolação livre.
        value = await db.scalar(text(f"SELECT nextval('{name}')"))
        return int(value or 0)

    await db.execute(
        text(
            f"CREATE TABLE IF NOT EXISTS {_SQLITE_COUNTERS_TABLE} "
            "(name VARCHAR(64) PRIMARY KEY, value INTEGER NOT NULL)"
        )
    )
    value = await db.scalar(
        text(
            f"INSERT INTO {_SQLITE_COUNTERS_TABLE} (name, value) VALUES (:name, 1) "
            "ON CONFLICT (name) DO UPDATE SET value = value + 1 "
            "RETURNING value"
        ),
        {"name": name},
    )
    return int(value or 0)
