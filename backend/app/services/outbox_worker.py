"""Worker em background para despacho assíncrono do outbox transacional (Gate G-D).

Despacha eventos com idempotência, assinaturas HMAC-SHA256 e retentativas exponenciais.
Executa em background acoplado ao lifespan do FastAPI.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from app.core.config import settings
from app.services import outbox_service

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

logger = logging.getLogger(__name__)


async def start_outbox_worker(
    session_factory: async_sessionmaker[AsyncSession] | None = None,
) -> None:
    """Loop assíncrono que consome periodicamente eventos pendentes no outbox."""
    from app.db.database import SessionFactory

    factory = session_factory or SessionFactory
    poll_interval = settings.OUTBOX_POLL_INTERVAL_SECONDS
    batch_size = settings.OUTBOX_BATCH_SIZE
    logger.info(
        "Iniciando outbox background worker (intervalo: %.1fs, batch: %d).",
        poll_interval,
        batch_size,
    )

    while True:
        try:
            async with factory() as db:
                dispatched = await outbox_service.dispatch_pending_outbox(db, batch_size=batch_size)
                if dispatched > 0:
                    logger.debug("Outbox worker despachou %d eventos com sucesso.", dispatched)
        except asyncio.CancelledError:
            logger.info("Outbox worker recebeu sinal de cancelamento.")
            break
        except Exception:
            logger.exception("Erro inesperado durante ciclo do outbox worker.")

        try:
            await asyncio.sleep(poll_interval)
        except asyncio.CancelledError:
            logger.info("Outbox worker cancelado durante sleep.")
            break
