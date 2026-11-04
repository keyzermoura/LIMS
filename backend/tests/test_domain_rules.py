"""Regras de negócio puras: desfecho de ensaio e transições de status."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.core.errors import ValidationDomainError
from app.models.enums import SampleStatus
from app.models.enums import TestOutcome as Outcome
from app.services.test_service import evaluate_outcome
from app.services.workflow import ensure_transition


def test_numeric_result_within_limits_is_approved():
    assert (
        evaluate_outcome(
            result_value=Decimal("32"),
            lower_limit=Decimal("10"),
            upper_limit=Decimal("50"),
            explicit=None,
        )
        == Outcome.APROVADO
    )


def test_numeric_result_above_limit_is_rejected():
    assert (
        evaluate_outcome(
            result_value=Decimal("6.2"),
            lower_limit=Decimal("4.5"),
            upper_limit=Decimal("5.5"),
            explicit=None,
        )
        == Outcome.REPROVADO
    )


def test_one_sided_limit_is_supported():
    assert (
        evaluate_outcome(
            result_value=Decimal("2.0"),
            lower_limit=None,
            upper_limit=Decimal("1.0"),
            explicit=None,
        )
        == Outcome.REPROVADO
    )


def test_qualitative_result_requires_explicit_outcome():
    with pytest.raises(ValidationDomainError):
        evaluate_outcome(
            result_value=None,
            lower_limit=None,
            upper_limit=None,
            explicit=None,
            result_text="Sem trincas visíveis.",
        )


def test_result_without_any_value_is_rejected():
    with pytest.raises(ValidationDomainError):
        evaluate_outcome(
            result_value=None,
            lower_limit=Decimal("0"),
            upper_limit=Decimal("1"),
            explicit=None,
        )


def test_out_of_range_result_cannot_be_explicitly_approved():
    """Um valor fora dos limites nunca pode ser assinado como APROVADO."""
    with pytest.raises(ValidationDomainError) as exc:
        evaluate_outcome(
            result_value=Decimal("6.2"),
            lower_limit=Decimal("4.5"),
            upper_limit=Decimal("5.5"),
            explicit=Outcome.APROVADO,
            result_text="Aparentemente conforme.",
        )
    assert "fora dos limites" in str(exc.value)


def test_explicit_approval_is_allowed_when_numeric_result_is_in_range():
    assert (
        evaluate_outcome(
            result_value=Decimal("5.0"),
            lower_limit=Decimal("4.5"),
            upper_limit=Decimal("5.5"),
            explicit=Outcome.APROVADO,
        )
        == Outcome.APROVADO
    )


def test_conservative_override_of_numeric_result_is_allowed():
    """Reprovar um valor dentro da faixa é permitido (ex.: evidência adicional)."""
    assert (
        evaluate_outcome(
            result_value=Decimal("5.0"),
            lower_limit=Decimal("4.5"),
            upper_limit=Decimal("5.5"),
            explicit=Outcome.REPROVADO,
            result_text="Desvio visual identificado no lote.",
        )
        == Outcome.REPROVADO
    )


def test_qualitative_outcome_requires_textual_evidence():
    with pytest.raises(ValidationDomainError):
        evaluate_outcome(
            result_value=None,
            lower_limit=None,
            upper_limit=None,
            explicit=Outcome.REPROVADO,
            result_text=None,
        )

    assert (
        evaluate_outcome(
            result_value=None,
            lower_limit=None,
            upper_limit=None,
            explicit=Outcome.REPROVADO,
            result_text="Trinca visível na carcaça.",
        )
        == Outcome.REPROVADO
    )


def test_qualitative_approval_also_requires_evidence():
    """Nenhum desfecho pode ser assinado sem evidência registrada."""
    with pytest.raises(ValidationDomainError):
        evaluate_outcome(
            result_value=None,
            lower_limit=None,
            upper_limit=None,
            explicit=Outcome.APROVADO,
            result_text=None,
        )

    with pytest.raises(ValidationDomainError):
        evaluate_outcome(
            result_value=None,
            lower_limit=None,
            upper_limit=None,
            explicit=Outcome.APROVADO,
            result_text="   ",
        )

    assert (
        evaluate_outcome(
            result_value=None,
            lower_limit=None,
            upper_limit=None,
            explicit=Outcome.APROVADO,
            result_text="Sem trincas ou deformações visíveis.",
        )
        == Outcome.APROVADO
    )


def test_allowed_sample_transition():
    ensure_transition(SampleStatus.RECEBIDO, SampleStatus.EM_TESTE)
    ensure_transition(SampleStatus.EM_TESTE, SampleStatus.APROVADO)
    # Reabertura explícita para reteste.
    ensure_transition(SampleStatus.APROVADO, SampleStatus.EM_TESTE)


def test_forbidden_sample_transition():
    with pytest.raises(ValidationDomainError):
        ensure_transition(SampleStatus.DESCARTADO, SampleStatus.EM_TESTE)


class _EmptyRows:
    def all(self):
        return []


class _SampleSession:
    """Sessão mínima: devolve a amostra e nenhum ensaio."""

    def __init__(self, sample):
        self._sample = sample

    async def scalar(self, _statement):
        return self._sample

    async def execute(self, _statement):
        return _EmptyRows()


@pytest.mark.asyncio
async def test_manual_approval_requires_all_tests_approved():
    """Aprovar manualmente sem laudos aprovados deve falhar com erro de domínio.

    Regressão: o serviço referenciava `ValidationDomainError` sem importá-lo,
    transformando a recusa em um `NameError` (HTTP 500).
    """
    from types import SimpleNamespace
    from uuid import uuid4

    from app.models.device_sample import DeviceSample
    from app.schemas.sample import SampleStatusUpdate
    from app.services.sample_service import update_status

    sample = DeviceSample(id=uuid4(), status=SampleStatus.EM_TESTE, version=3)
    payload = SampleStatusUpdate(
        status=SampleStatus.APROVADO,
        reason="Aprovação manual após revisão documental.",
        version=3,
    )

    with pytest.raises(ValidationDomainError) as exc:
        await update_status(
            _SampleSession(sample),
            sample_id=sample.id,
            payload=payload,
            actor=SimpleNamespace(),
            signature=SimpleNamespace(),
            context=SimpleNamespace(),
        )

    assert "todos os ensaios" in str(exc.value)
    assert sample.status == SampleStatus.EM_TESTE


class _CreateTestSession:
    """Sessão mínima: nenhum ensaio existente, amostra informada."""

    def __init__(self, sample):
        self._sample = sample

    async def get(self, _model, _pk):
        return None

    async def scalar(self, _statement):
        return self._sample


@pytest.mark.asyncio
async def test_cannot_schedule_test_on_approved_sample():
    """Aprovação não pode ser rebaixada por um novo ensaio pendente."""
    from types import SimpleNamespace
    from uuid import uuid4

    from app.core.errors import ConflictError
    from app.models.device_sample import DeviceSample
    from app.schemas.test import LabTestCreate
    from app.services.test_service import create_test

    sample = DeviceSample(id=uuid4(), status=SampleStatus.APROVADO, version=4)
    payload = LabTestCreate(
        id=uuid4(),
        device_sample_id=sample.id,
        name="Reteste de esterilidade",
        unit="UFC",
    )

    with pytest.raises(ConflictError) as exc:
        await create_test(
            _CreateTestSession(sample),
            payload=payload,
            actor=SimpleNamespace(),
            signature=SimpleNamespace(),
            context=SimpleNamespace(),
        )

    assert "reabra" in exc.value.message.lower()
