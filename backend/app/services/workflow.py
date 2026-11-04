"""Regras de transição de status da amostra."""

from __future__ import annotations

from app.core.errors import ValidationDomainError
from app.models.enums import SampleStatus

ALLOWED_TRANSITIONS: dict[SampleStatus, set[SampleStatus]] = {
    SampleStatus.RECEBIDO: {SampleStatus.EM_TESTE, SampleStatus.DESCARTADO},
    SampleStatus.EM_TESTE: {
        SampleStatus.APROVADO,
        SampleStatus.REPROVADO,
        SampleStatus.DESCARTADO,
    },
    SampleStatus.REPROVADO: {SampleStatus.DESCARTADO, SampleStatus.EM_TESTE},
    # APROVADO → EM_TESTE é a reabertura explícita para reteste (ex.: vigilância
    # pós-mercado). É sempre assinada e jamais ocorre por omissão: o serviço de
    # ensaios recusa programar um novo ensaio em amostra aprovada.
    SampleStatus.APROVADO: {SampleStatus.EM_TESTE, SampleStatus.DESCARTADO},
    SampleStatus.DESCARTADO: set(),
}

FINAL_STATUSES = {SampleStatus.DESCARTADO}


def ensure_transition(current: SampleStatus, target: SampleStatus) -> None:
    if current == target:
        raise ValidationDomainError(f"A amostra já está com status {target.value}.")
    if target not in ALLOWED_TRANSITIONS[current]:
        raise ValidationDomainError(
            f"Transição não permitida: {current.value} → {target.value}.",
            details={"allowed": sorted(s.value for s in ALLOWED_TRANSITIONS[current])},
        )
