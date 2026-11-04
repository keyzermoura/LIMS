"""Engine assíncrona e sessão por requisição."""

from __future__ import annotations

import re
from collections.abc import AsyncIterator
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from starlette.concurrency import run_in_threadpool

from app.core.config import settings

# SQLite (usado apenas em testes/importações locais) não aceita as opções de
# pool do PostgreSQL. Produção continua usando o pool dimensionado.
_IS_SQLITE = settings.DATABASE_URL.startswith("sqlite")

_ENGINE_OPTIONS: dict[str, object] = {
    "echo": settings.DB_ECHO,
    "pool_pre_ping": True,
}
if not _IS_SQLITE:
    _ENGINE_OPTIONS.update(
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_recycle=settings.DB_POOL_RECYCLE_SECONDS,
    )

engine = create_async_engine(settings.DATABASE_URL, **_ENGINE_OPTIONS)

SessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """Dependency do FastAPI.

    O commit é responsabilidade do serviço (unidade de trabalho atômica:
    alteração de negócio + evento de auditoria + assinatura). Se nada for
    commitado, o contexto descarta a transação.
    """
    async with SessionFactory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


SQL_DIR = Path(__file__).parent / "sql"


async def init_db() -> None:
    """Cria o schema (dev/test) e instala as proteções de imutabilidade.

    Em produção o schema é criado por migração versionada (Alembic); os
    triggers abaixo são idempotentes e podem rodar a cada deploy.
    """
    from app.models import Base  # import tardio: registra todos os modelos

    if settings.AUTO_CREATE_SCHEMA:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    await apply_sql_file(SQL_DIR / "001_immutability.sql")
    await apply_sql_file(SQL_DIR / "002_indexes.sql")


async def apply_sql_file(path: Path) -> None:
    """Executa um arquivo .sql dividido por `-- @@statement`.

    O driver asyncpg não aceita múltiplos comandos em um prepared statement,
    por isso cada bloco é executado isoladamente.
    """
    # Leitura de arquivo em thread para não bloquear o event loop.
    script = await run_in_threadpool(path.read_text, encoding="utf-8")
    async with engine.begin() as conn:
        for statement in split_sql_script(script):
            await conn.execute(text(statement))


def split_sql_script(script: str) -> list[str]:
    """Divide um script nos statements separados pela linha delimitadora.

    O delimitador só é reconhecido quando ocupa a linha inteira — assim
    comentários que citam o texto do delimitador não quebram o arquivo.
    Comentários de cabeçalho são descartados.
    """
    statements: list[str] = []
    for chunk in re.split(r"(?m)^[ \t]*--[ \t]*@@statement[ \t]*$", script):
        lines = chunk.splitlines()
        while lines and (not lines[0].strip() or lines[0].lstrip().startswith("--")):
            lines.pop(0)
        statement = "\n".join(lines).strip()
        if statement:
            statements.append(statement)
    return statements



async def healthcheck() -> bool:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:  # pragma: no cover - depende de infraestrutura
        return False
