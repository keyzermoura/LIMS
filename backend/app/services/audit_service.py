"""Serviço de auditoria: cadeia de hashes append-only + verificação.

Garantias:
  1. Numeração sequencial sem lacunas (serializada por advisory lock).
  2. `hash` encadeia o registro anterior — qualquer alteração quebra a cadeia.
  3. `hmac` com chave externa ao banco — detecta recálculo malicioso.
  4. Trigger no PostgreSQL bloqueia UPDATE/DELETE/TRUNCATE.

O `append` participa da MESMA transação da alteração de negócio. Se a
transação falhar, não existe evento "fantasma"; se o evento falhar, a
alteração não é persistida.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Select, func, or_, select, text
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.context import RequestContext
from app.core.security import hmac_sha256, sha256_hex
from app.core.serialization import CANONICALIZATION_VERSION, canonical_json, jsonable
from app.db.dialect import is_postgres
from app.models.audit_log import AuditLog
from app.models.base import utcnow
from app.models.enums import AuditAction
from app.models.user import User

GENESIS_HASH = "0" * 64
AUDIT_LOCK_KEY = 728341  # chave arbitrária e estável do advisory lock

# Campos que nunca podem ser auditados em claro.
_SENSITIVE_FIELDS = {"hashed_password"}


# --------------------------------------------------------------------------
# Snapshots
# --------------------------------------------------------------------------
def snapshot(instance: Any, *, include: set[str] | None = None) -> dict[str, Any]:
    """Extrai os valores de coluna de uma entidade de forma serializável."""
    if instance is None:
        return {}
    mapper = sa_inspect(instance).mapper
    data: dict[str, Any] = {}
    for attr in mapper.column_attrs:
        key = "metadata" if attr.key == "attributes" else attr.key
        if key in _SENSITIVE_FIELDS:
            continue
        if include is not None and key not in include:
            continue
        data[key] = jsonable(getattr(instance, attr.key))
    return data


def diff(old: dict[str, Any] | None, new: dict[str, Any] | None) -> dict[str, Any]:
    """Somente os campos alterados — mantém a trilha legível para o auditor."""
    old = old or {}
    new = new or {}
    changes: dict[str, Any] = {}
    for key in sorted(set(old) | set(new)):
        if old.get(key) != new.get(key):
            changes[key] = {"de": old.get(key), "para": new.get(key)}
    return changes


def filtered_query(
    *,
    entity_type: str | None = None,
    entity_id: str | None = None,
    actor_id: UUID | None = None,
    action: AuditAction | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    search: str | None = None,
) -> Select[Any]:
    """Consulta base compartilhada entre a tela e a exportação da trilha.

    Manter os filtros em um único lugar garante que o arquivo exportado
    contenha exatamente o mesmo recorte exibido ao auditor.
    """
    stmt = select(AuditLog)
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    if entity_id:
        stmt = stmt.where(AuditLog.entity_id == entity_id)
    if actor_id:
        stmt = stmt.where(AuditLog.actor_id == actor_id)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if date_from:
        stmt = stmt.where(AuditLog.occurred_at >= date_from)
    if date_to:
        stmt = stmt.where(AuditLog.occurred_at <= date_to)
    if search:
        term = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                AuditLog.actor_username.ilike(term),
                AuditLog.entity_id.ilike(term),
                AuditLog.reason.ilike(term),
            )
        )
    return stmt


# --------------------------------------------------------------------------
# Append
# --------------------------------------------------------------------------
async def append(
    db: AsyncSession,
    *,
    action: AuditAction,
    entity_type: str,
    entity_id: str | UUID,
    actor: User | None = None,
    actor_username: str | None = None,
    old_value: dict[str, Any] | None = None,
    new_value: dict[str, Any] | None = None,
    reason: str | None = None,
    context: RequestContext | None = None,
    signature_id: UUID | None = None,
    occurred_at: datetime | None = None,
) -> AuditLog:
    # Serializa a geração da cadeia dentro da transação corrente. O SQLite
    # (somente testes) serializa escritas por natureza e não tem advisory lock.
    if is_postgres(db):
        await db.execute(
            text("SELECT pg_advisory_xact_lock(:key)"), {"key": AUDIT_LOCK_KEY}
        )

    last = (
        await db.execute(
            select(AuditLog.sequence, AuditLog.hash)
            .order_by(AuditLog.sequence.desc())
            .limit(1)
        )
    ).first()
    sequence = (last.sequence if last else 0) + 1
    prev_hash = last.hash if last else GENESIS_HASH

    timestamp = occurred_at or utcnow()
    payload: dict[str, Any] = {
        "v": CANONICALIZATION_VERSION,
        "seq": sequence,
        "at": jsonable(timestamp),
        "action": action.value,
        "entity": {"type": entity_type, "id": str(entity_id)},
        "actor": {
            "id": str(actor.id) if actor else None,
            "username": actor.username if actor else (actor_username or "SYSTEM"),
            "role": actor.role.value if actor else None,
        },
        "old": jsonable(old_value),
        "new": jsonable(new_value),
        "reason": reason,
        "signature_id": str(signature_id) if signature_id else None,
        "request_id": context.request_id if context else None,
        "ip": context.ip_address if context else None,
    }

    digest = sha256_hex(f"{sequence}:{prev_hash}:{canonical_json(payload)}")
    mac = hmac_sha256(settings.AUDIT_HMAC_KEY.get_secret_value(), digest)

    record = AuditLog(
        sequence=sequence,
        occurred_at=timestamp,
        actor_id=actor.id if actor else None,
        actor_username=payload["actor"]["username"],
        actor_role=payload["actor"]["role"],
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        old_value=jsonable(old_value),
        new_value=jsonable(new_value),
        reason=reason,
        payload=payload,
        ip_address=context.ip_address if context else None,
        user_agent=context.user_agent if context else None,
        request_id=context.request_id if context else None,
        signature_id=signature_id,
        prev_hash=prev_hash,
        hash=digest,
        hmac=mac,
    )
    db.add(record)
    await db.flush()
    return record


# --------------------------------------------------------------------------
# Verificação
# --------------------------------------------------------------------------
async def verify_chain(db: AsyncSession, *, from_sequence: int = 1) -> dict[str, Any]:
    if from_sequence < 1:
        from_sequence = 1

    if from_sequence == 1:
        expected_prev = GENESIS_HASH
        expected_seq = 1
    else:
        anchor = await db.scalar(
            select(AuditLog.hash).where(AuditLog.sequence == from_sequence - 1)
        )
        if anchor is None:
            return {
                "ok": False,
                "checked": 0,
                "from_sequence": from_sequence,
                "last_sequence": None,
                "head_hash": None,
                "issues": [
                    {
                        "sequence": from_sequence - 1,
                        "type": "ANCHOR_NOT_FOUND",
                        "detail": "Registro âncora inexistente.",
                    }
                ],
            }
        expected_prev = anchor
        expected_seq = from_sequence

    key = settings.AUDIT_HMAC_KEY.get_secret_value()
    issues: list[dict[str, Any]] = []
    checked = 0
    last_sequence: int | None = None
    head_hash = expected_prev

    rows = (
        await db.execute(
            select(
                AuditLog.sequence,
                AuditLog.payload,
                AuditLog.prev_hash,
                AuditLog.hash,
                AuditLog.hmac,
            )
            .where(AuditLog.sequence >= from_sequence)
            .order_by(AuditLog.sequence.asc())
        )
    ).all()

    for row in rows:
        checked += 1
        if row.sequence != expected_seq:
            issues.append(
                {
                    "sequence": row.sequence,
                    "type": "SEQUENCE_GAP",
                    "detail": f"Esperado {expected_seq}, encontrado {row.sequence}.",
                }
            )
        if row.prev_hash != expected_prev:
            issues.append(
                {
                    "sequence": row.sequence,
                    "type": "PREV_HASH_MISMATCH",
                    "detail": "Encadeamento com o registro anterior foi rompido.",
                }
            )
        recomputed = sha256_hex(
            f"{row.sequence}:{row.prev_hash}:{canonical_json(row.payload)}"
        )
        if recomputed != row.hash:
            issues.append(
                {
                    "sequence": row.sequence,
                    "type": "HASH_MISMATCH",
                    "detail": "Conteúdo do registro não corresponde ao hash gravado.",
                }
            )
        if hmac_sha256(key, row.hash) != row.hmac:
            issues.append(
                {
                    "sequence": row.sequence,
                    "type": "HMAC_MISMATCH",
                    "detail": "Registro não foi autenticado com a chave de integridade.",
                }
            )
        expected_prev = row.hash
        expected_seq = row.sequence + 1
        last_sequence = row.sequence
        head_hash = row.hash

    total = await db.scalar(select(func.count()).select_from(AuditLog)) or 0

    return {
        "ok": not issues,
        "checked": checked,
        "total_records": total,
        "from_sequence": from_sequence,
        "last_sequence": last_sequence,
        "head_hash": head_hash,
        "canonicalization": CANONICALIZATION_VERSION,
        "issues": issues[:200],
    }
