"""Fixtures dos testes de integração HTTP.

Por padrão cada teste recebe um banco SQLite em arquivo temporário, criado a
partir do metadata real. Definindo `LIMS_TEST_DATABASE_URL` (ex.:
`postgresql+asyncpg://lims@localhost:55432/lims_test`), a suíte roda contra
PostgreSQL de verdade: um schema exclusivo por teste, com os triggers e as
sequences de `app/db/sql/*.sql` instalados.

A dependência `get_db_session` do FastAPI é sobrescrita para apontar para esse
banco — o restante da aplicação (rotas, serviços, RBAC, assinatura e
auditoria) roda exatamente como em produção.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core import ratelimit
from app.core.security import hash_password
from app.db.database import get_db_session, split_sql_script
from app.main import app as fastapi_app
from app.models import Base
from app.models.base import utcnow
from app.models.enums import UserRole
from app.models.user import User

POSTGRES_URL = os.getenv("LIMS_TEST_DATABASE_URL")
SQL_DIR = Path(__file__).resolve().parents[1] / "app" / "db" / "sql"

# (username, full_name, role, password, registration_number)
DEMO_USERS: list[tuple[str, str, UserRole, str, str | None]] = [
    ("admin", "Ana Administradora", UserRole.ADMIN, "Admin@Lims2026", None),
    ("auditor", "Clara Auditora", UserRole.AUDITOR, "Auditor@Lims2026", "CQA-4412"),
    ("fiscal", "Marina Prado", UserRole.FISCAL, "Fiscal@Lims2026", "ANVISA-7781"),
    ("tecnico", "Rafael Nunes", UserRole.TECNICO, "Tecnico@Lims2026", "CRF-3391"),
    ("tecnico2", "Bruno Lima", UserRole.TECNICO, "Tecnico@Lims2026", "CRF-3392"),
    (
        "custodiante",
        "Helena Castro",
        UserRole.CUSTODIANTE,
        "Custodia@Lims2026",
        None,
    ),
]


async def _install_sql_files(engine: AsyncEngine) -> None:
    """Aplica triggers/indices/sequences no schema corrente da conexão."""
    for filename in ("001_immutability.sql", "002_indexes.sql"):
        script = (SQL_DIR / filename).read_text(encoding="utf-8")
        async with engine.begin() as conn:
            for statement in split_sql_script(script):
                await conn.execute(text(statement))


@pytest.fixture(scope="session")
def hashed_passwords() -> dict[str, str]:
    """Argon2 é caro: cada senha distinta é hasheada uma única vez."""
    return {password: hash_password(password) for _, _, _, password, _ in DEMO_USERS}


@pytest.fixture
async def db_factory(
    tmp_path: Path,
) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    if POSTGRES_URL:
        async for factory in _postgres_factory():
            yield factory
        return

    engine = create_async_engine(
        f"sqlite+aiosqlite:///{(tmp_path / 'lims-test.db').as_posix()}"
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    yield factory
    await engine.dispose()


async def _postgres_factory() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    schema = f"lims_test_{uuid4().hex[:16]}"
    admin = create_async_engine(POSTGRES_URL, poolclass=NullPool)
    async with admin.begin() as conn:
        await conn.execute(text(f'CREATE SCHEMA "{schema}"'))

    engine = create_async_engine(
        POSTGRES_URL,
        poolclass=NullPool,
        connect_args={"server_settings": {"search_path": schema}},
    )
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await _install_sql_files(engine)
        yield async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
    finally:
        await engine.dispose()
        async with admin.begin() as conn:
            await conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        await admin.dispose()


@pytest.fixture
async def client(
    db_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncClient]:
    async def override_db_session() -> AsyncIterator[AsyncSession]:
        async with db_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    # O rate limiter é por processo: zera a janela para que um teste não
    # consuma a cota do seguinte.
    ratelimit.limiter.reset()
    fastapi_app.dependency_overrides[get_db_session] = override_db_session
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as http_client:
        yield http_client
    fastapi_app.dependency_overrides.pop(get_db_session, None)


@pytest.fixture
async def users(
    db_factory: async_sessionmaker[AsyncSession],
    hashed_passwords: dict[str, str],
) -> dict[str, dict[str, Any]]:
    """Usuários de demonstração, retornados como dados simples (sem ORM)."""
    records: dict[str, dict[str, Any]] = {}
    async with db_factory() as db:
        for username, full_name, role, password, registration in DEMO_USERS:
            user = User(
                username=username,
                email=f"{username}@lims.local",
                full_name=full_name,
                role=role,
                hashed_password=hashed_passwords[password],
                registration_number=registration,
                password_changed_at=utcnow(),
            )
            db.add(user)
            await db.flush()
            records[username] = {
                "id": str(user.id),
                "role": role.value,
                "password": password,
                "full_name": full_name,
            }
        await db.commit()
    return records
