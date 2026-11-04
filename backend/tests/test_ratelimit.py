"""Testes da janela deslizante de rate limiting (sem HTTP)."""

from __future__ import annotations

import pytest

from app.core.ratelimit import SlidingWindowLimiter


def test_allows_up_to_the_limit() -> None:
    limiter = SlidingWindowLimiter()

    for expected_remaining in (2, 1, 0):
        decision = limiter.hit("login:127.0.0.1", limit=3, window_seconds=60, now=0)
        assert decision.allowed is True
        assert decision.remaining == expected_remaining

    blocked = limiter.hit("login:127.0.0.1", limit=3, window_seconds=60, now=0)
    assert blocked.allowed is False
    assert blocked.retry_after == 60


def test_window_slides_and_releases_the_oldest_event() -> None:
    limiter = SlidingWindowLimiter()
    limiter.hit("k", limit=1, window_seconds=60, now=0)
    assert limiter.hit("k", limit=1, window_seconds=60, now=59).allowed is False

    # Em now=60 a requisição de now=0 saiu da janela.
    assert limiter.hit("k", limit=1, window_seconds=60, now=60).allowed is True


def test_retry_after_is_rounded_up() -> None:
    limiter = SlidingWindowLimiter()
    limiter.hit("k", limit=1, window_seconds=60, now=0)
    decision = limiter.hit("k", limit=1, window_seconds=60, now=10.5)
    assert decision.allowed is False
    assert decision.retry_after == 50  # 60 - 10.5 = 49.5 -> 50


def test_keys_are_independent() -> None:
    limiter = SlidingWindowLimiter()
    assert limiter.hit("a", limit=1, window_seconds=60, now=0).allowed
    assert limiter.hit("b", limit=1, window_seconds=60, now=0).allowed
    assert limiter.hit("a", limit=1, window_seconds=60, now=0).allowed is False


def test_reset_clears_counters() -> None:
    limiter = SlidingWindowLimiter()
    limiter.hit("k", limit=1, window_seconds=60, now=0)
    assert limiter.hit("k", limit=1, window_seconds=60, now=0).allowed is False

    limiter.reset()
    assert limiter.hit("k", limit=1, window_seconds=60, now=0).allowed is True


@pytest.mark.parametrize("limit", [0, -1])
def test_non_positive_limit_disables_the_limiter(limit: int) -> None:
    limiter = SlidingWindowLimiter()
    for _ in range(10):
        assert limiter.hit("k", limit=limit, window_seconds=60, now=0).allowed
