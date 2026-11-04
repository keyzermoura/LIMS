"""Rate limiting em memória por janela deslizante.

Protege endpoints sensíveis (login e reautenticação para assinatura) contra
força bruta e abuso. O contador é **por processo**: em um deploy com múltiplos
workers cada um mantém a própria janela, então o limite efetivo é
`limite × workers`. Para um limite global exato, troque o backend por Redis
(o contrato de `SlidingWindowLimiter.hit` permanece o mesmo).

A janela deslizante guarda apenas os instantes das requisições aceitas, o que
evita o efeito de borda do algoritmo de janela fixa (rajada no fim de uma
janela seguida de outra rajada no início da próxima).
"""

from __future__ import annotations

import math
import threading
import time
from collections import deque
from dataclasses import dataclass

from app.core.errors import TooManyRequestsError


@dataclass(frozen=True, slots=True)
class RateLimitDecision:
    """Resultado de uma tentativa de consumo."""

    allowed: bool
    retry_after: int
    remaining: int


class SlidingWindowLimiter:
    """Contador de eventos por chave com janela deslizante."""

    def __init__(self) -> None:
        self._events: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def hit(
        self,
        key: str,
        *,
        limit: int,
        window_seconds: int,
        now: float | None = None,
    ) -> RateLimitDecision:
        """Registra uma tentativa e diz se ela pode prosseguir.

        ``limit <= 0`` desabilita o limite (útil para testes e ambientes
        controlados).
        """
        if limit <= 0 or window_seconds <= 0:
            return RateLimitDecision(allowed=True, retry_after=0, remaining=limit)

        current = time.monotonic() if now is None else now
        cutoff = current - window_seconds

        with self._lock:
            events = self._events.setdefault(key, deque())
            while events and events[0] <= cutoff:
                events.popleft()

            if len(events) >= limit:
                # Segundos até a requisição mais antiga sair da janela.
                retry_after = max(1, math.ceil(events[0] + window_seconds - current))
                return RateLimitDecision(
                    allowed=False, retry_after=retry_after, remaining=0
                )

            events.append(current)
            return RateLimitDecision(
                allowed=True, retry_after=0, remaining=limit - len(events)
            )

    def reset(self) -> None:
        """Zera todos os contadores (usado entre testes)."""
        with self._lock:
            self._events.clear()


# Limiter compartilhado pela API. Chaves distintas separam os escopos
# (`login:<ip>` e `sign:<user_id>`), permitindo usar uma única instância.
limiter = SlidingWindowLimiter()


def enforce(
    key: str,
    *,
    limit: int,
    window_seconds: int,
) -> None:
    """Consome uma tentativa ou levanta 429 com ``Retry-After``."""
    decision = limiter.hit(key, limit=limit, window_seconds=window_seconds)
    if not decision.allowed:
        raise TooManyRequestsError(
            "Muitas requisições. Aguarde antes de tentar novamente.",
            retry_after=decision.retry_after,
        )
