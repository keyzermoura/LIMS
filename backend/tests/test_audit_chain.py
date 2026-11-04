"""Testes do encadeamento e da canonicalização da auditoria."""

from __future__ import annotations

from datetime import UTC

from app.core.security import hmac_sha256, sha256_hex
from app.core.serialization import canonical_json


def compute_hash(sequence: int, prev_hash: str, payload: dict) -> str:
    return sha256_hex(f"{sequence}:{prev_hash}:{canonical_json(payload)}")


def test_canonical_json_is_order_independent():
    first = {"b": 2, "a": 1, "nested": {"y": [1, 2], "x": None}}
    second = {"nested": {"x": None, "y": [1, 2]}, "a": 1, "b": 2}
    assert canonical_json(first) == canonical_json(second)


def test_hash_chain_detects_payload_tampering():
    genesis = "0" * 64
    payload_1 = {"seq": 1, "action": "CREATE", "new": {"status": "RECEBIDO"}}
    payload_2 = {"seq": 2, "action": "TRANSFER", "new": {"custodian": "Helena"}}

    hash_1 = compute_hash(1, genesis, payload_1)
    hash_2 = compute_hash(2, hash_1, payload_2)

    assert hash_2 == compute_hash(2, hash_1, payload_2)

    tampered = {**payload_2, "new": {"custodian": "Outro"}}
    assert compute_hash(2, hash_1, tampered) != hash_2


def test_hash_chain_detects_link_break():
    genesis = "0" * 64
    payload = {"seq": 1}
    hash_1 = compute_hash(1, genesis, payload)
    assert compute_hash(1, "1" * 64, payload) != hash_1


def test_hmac_requires_secret():
    digest = "a" * 64
    mac = hmac_sha256("chave-de-producao", digest)
    assert len(mac) == 64
    assert hmac_sha256("outra-chave", digest) != mac


def test_canonicalization_handles_domain_types():
    from datetime import datetime
    from decimal import Decimal
    from uuid import UUID

    payload = {
        "id": UUID("00000000-0000-0000-0000-000000000001"),
        "value": Decimal("6.20"),
        "at": datetime(2026, 10, 28, 12, 0, tzinfo=UTC),
    }
    result = canonical_json(payload)
    assert '"value":"6.20"' in result
    assert "2026-10-28T12:00:00+00:00" in result
