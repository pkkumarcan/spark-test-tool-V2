"""Resilience utilities: retry, circuit breaker, exponential backoff."""

from __future__ import annotations

import asyncio
import functools
import logging
import time
from collections.abc import Callable
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)


class CircuitState(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Circuit breaker pattern — stops calling a function after repeated failures."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        name: str = "default",
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.name = name
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = 0.0

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if time.time() - self._last_failure_time >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
        return self._state

    def record_success(self) -> None:
        self._failure_count = 0
        self._state = CircuitState.CLOSED

    def record_failure(self) -> None:
        self._failure_count += 1
        self._last_failure_time = time.time()
        if self._failure_count >= self.failure_threshold:
            self._state = CircuitState.OPEN
            logger.warning(f"Circuit breaker '{self.name}' opened after {self._failure_count} failures")

    def allow_request(self) -> bool:
        state = self.state
        if state == CircuitState.CLOSED:
            return True
        if state == CircuitState.HALF_OPEN:
            return True
        return False

    def reset(self) -> None:
        self._state = CircuitState.CLOSED
        self._failure_count = 0


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    on_retry: Callable[[int, Exception], None] | None = None,
) -> Callable:
    """Decorator that retries a function on failure with exponential backoff.

    Works for both sync and async functions.
    """

    def decorator(fn: Callable) -> Callable:
        if asyncio.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                last_exc: Exception | None = None
                for attempt in range(1, max_attempts + 1):
                    try:
                        return await fn(*args, **kwargs)
                    except exceptions as e:
                        last_exc = e
                        if attempt < max_attempts:
                            wait = delay * (backoff_factor ** (attempt - 1))
                            if on_retry:
                                on_retry(attempt, e)
                            logger.warning(f"Retry {attempt}/{max_attempts} for {fn.__name__}: {e} (wait {wait:.1f}s)")
                            await asyncio.sleep(wait)
                raise last_exc  # type: ignore[misc]
            return async_wrapper
        else:
            @functools.wraps(fn)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                last_exc: Exception | None = None
                for attempt in range(1, max_attempts + 1):
                    try:
                        return fn(*args, **kwargs)
                    except exceptions as e:
                        last_exc = e
                        if attempt < max_attempts:
                            wait = delay * (backoff_factor ** (attempt - 1))
                            if on_retry:
                                on_retry(attempt, e)
                            logger.warning(f"Retry {attempt}/{max_attempts} for {fn.__name__}: {e} (wait {wait:.1f}s)")
                            time.sleep(wait)
                raise last_exc  # type: ignore[misc]
            return sync_wrapper

    return decorator


def circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: float = 30.0,
    name: str | None = None,
) -> Callable:
    """Decorator that wraps a function with a circuit breaker."""

    breaker = CircuitBreaker(
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        name=name or "default",
    )

    def decorator(fn: Callable) -> Callable:
        if asyncio.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                if not breaker.allow_request():
                    raise ConnectionError(f"Circuit breaker '{breaker.name}' is open")
                try:
                    result = await fn(*args, **kwargs)
                    breaker.record_success()
                    return result
                except Exception:
                    breaker.record_failure()
                    raise
            return async_wrapper
        else:
            @functools.wraps(fn)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                if not breaker.allow_request():
                    raise ConnectionError(f"Circuit breaker '{breaker.name}' is open")
                try:
                    result = fn(*args, **kwargs)
                    breaker.record_success()
                    return result
                except Exception:
                    breaker.record_failure()
                    raise
            return sync_wrapper

    return decorator
