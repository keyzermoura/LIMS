"""Testes de primitivas de segurança (não exigem banco de dados)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.core.errors import ValidationDomainError
from app.core.security import (
    TokenError,
    create_access_token,
    create_esign_token,
    decode_esign_token,
    decode_token,
    hash_password,
    sign_qr_payload,
    verify_password,
    verify_qr_payload,
)


def test_password_hash_roundtrip():
    password = "SenhaForte#2026"
    digest = hash_password(password)
    assert digest != password
    assert verify_password(password, digest)
    assert not verify_password("outra-senha", digest)


def test_password_policy_rejects_weak_password():
    with pytest.raises(ValidationDomainError):
        hash_password("123456")


def test_access_token_roundtrip_and_type_enforcement():
    user_id = uuid4()
    token = create_access_token(user_id, "TECNICO", password_version=123)
    claims = decode_token(token, expected_type="access")
    assert claims["sub"] == str(user_id)
    assert claims["role"] == "TECNICO"
    assert claims["pwdv"] == 123

    with pytest.raises(TokenError):
        decode_token(token, expected_type="refresh")


def test_esign_token_carries_intent():
    signature_id = uuid4()
    entity_id = str(uuid4())
    token = create_esign_token(
        signature_id=signature_id,
        user_id=uuid4(),
        entity_type="LabTest",
        entity_id=entity_id,
        action="UPDATE",
        meaning="RESPONSABILIDADE_TECNICA",
        jti="jti-de-teste",
    )
    claims = decode_esign_token(token)
    assert claims["sid"] == str(signature_id)
    assert claims["eid"] == entity_id
    assert claims["act"] == "UPDATE"
    assert claims["jti"] == "jti-de-teste"


def test_qr_payload_is_signed_and_tamper_evident():
    sample_id = uuid4()
    token = sign_qr_payload(sample_id, "LIMS-2026-000123")
    claims = verify_qr_payload(token)
    assert claims["sub"] == str(sample_id)
    assert claims["acc"] == "LIMS-2026-000123"

    tampered = token[:-3] + ("aaa" if not token.endswith("aaa") else "bbb")
    with pytest.raises(TokenError):
        verify_qr_payload(tampered)


def test_naive_and_aware_datetimes_serialize_consistently():
    from app.core.serialization import canonical_json

    aware = datetime(2026, 1, 1, tzinfo=UTC)
    assert canonical_json({"at": aware}) == '{"at":"2026-01-01T00:00:00+00:00"}'
