"""Regras de transição de status da amostra."""

from __future__ import annotations

from app.core.errors import ValidationDomainError
from app.models.enums import (
    CustodyObjectStatus,
    ReceiptStatus,
    SampleStatus,
    SolicitationStatus,
)

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


ALLOWED_SOLICITATION_TRANSITIONS: dict[SolicitationStatus, set[SolicitationStatus]] = {
    SolicitationStatus.RASCUNHO: {SolicitationStatus.SUBMETIDA, SolicitationStatus.CANCELADA},
    SolicitationStatus.SUBMETIDA: {
        SolicitationStatus.RECEBIMENTO_REGISTRADO,
        SolicitationStatus.CANCELADA,
    },
    SolicitationStatus.RECEBIMENTO_REGISTRADO: {
        SolicitationStatus.EM_TRATAMENTO,
        SolicitationStatus.CANCELADA,
    },
    SolicitationStatus.EM_TRATAMENTO: {
        SolicitationStatus.CONCLUIDA,
        SolicitationStatus.CANCELADA,
    },
    SolicitationStatus.CONCLUIDA: set(),
    SolicitationStatus.CANCELADA: set(),
}


def ensure_solicitation_transition(
    current: SolicitationStatus, target: SolicitationStatus
) -> None:
    if current == target:
        raise ValidationDomainError(f"A solicitação já está com status {target.value}.")
    if target not in ALLOWED_SOLICITATION_TRANSITIONS[current]:
        raise ValidationDomainError(
            f"Transição não permitida para solicitação: {current.value} → {target.value}.",
            details={"allowed": sorted(s.value for s in ALLOWED_SOLICITATION_TRANSITIONS[current])},
        )


ALLOWED_RECEIPT_TRANSITIONS: dict[ReceiptStatus, set[ReceiptStatus]] = {
    ReceiptStatus.REGISTRADO: {ReceiptStatus.EM_CONFERENCIA, ReceiptStatus.CANCELADO},
    ReceiptStatus.EM_CONFERENCIA: {
        ReceiptStatus.PENDENTE,
        ReceiptStatus.CONCLUIDO,
        ReceiptStatus.CANCELADO,
    },
    ReceiptStatus.PENDENTE: {
        ReceiptStatus.EM_CONFERENCIA,
        ReceiptStatus.CONCLUIDO,
        ReceiptStatus.CANCELADO,
    },
    ReceiptStatus.CONCLUIDO: set(),
    ReceiptStatus.CANCELADO: set(),
}


def ensure_receipt_transition(current: ReceiptStatus, target: ReceiptStatus) -> None:
    if current == target:
        raise ValidationDomainError(f"O recebimento já está com status {target.value}.")
    if target not in ALLOWED_RECEIPT_TRANSITIONS[current]:
        raise ValidationDomainError(
            f"Transição não permitida para recebimento: {current.value} → {target.value}.",
            details={"allowed": sorted(s.value for s in ALLOWED_RECEIPT_TRANSITIONS[current])},
        )


ALLOWED_CUSTODY_OBJECT_TRANSITIONS: dict[CustodyObjectStatus, set[CustodyObjectStatus]] = {
    CustodyObjectStatus.SOB_GUARDA: {
        CustodyObjectStatus.EM_CONFERENCIA,
        CustodyObjectStatus.ACEITO,
        CustodyObjectStatus.RECUSADO,
        CustodyObjectStatus.DEVOLVIDO,
        CustodyObjectStatus.DESCARTADO,
    },
    CustodyObjectStatus.EM_CONFERENCIA: {
        CustodyObjectStatus.SOB_GUARDA,
        CustodyObjectStatus.ACEITO,
        CustodyObjectStatus.RECUSADO,
        CustodyObjectStatus.DEVOLVIDO,
        CustodyObjectStatus.DESCARTADO,
    },
    CustodyObjectStatus.ACEITO: set(),
    CustodyObjectStatus.RECUSADO: {
        CustodyObjectStatus.DEVOLVIDO,
        CustodyObjectStatus.DESCARTADO,
    },
    CustodyObjectStatus.DEVOLVIDO: set(),
    CustodyObjectStatus.DESCARTADO: set(),
}


def ensure_custody_object_transition(
    current: CustodyObjectStatus, target: CustodyObjectStatus
) -> None:
    if current == target:
        raise ValidationDomainError(f"O objeto de custódia já está com status {target.value}.")
    if target not in ALLOWED_CUSTODY_OBJECT_TRANSITIONS[current]:
        raise ValidationDomainError(
            f"Transição não permitida para objeto de custódia: {current.value} → {target.value}.",
            details={"allowed": sorted(s.value for s in ALLOWED_CUSTODY_OBJECT_TRANSITIONS[current])},
        )
