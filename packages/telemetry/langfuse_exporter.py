"""Langfuse as an OpenTelemetry span exporter.

Configure via environment variables:
  SPARK_LANGFUSE_URL   — Langfuse server URL
  SPARK_LANGFUSE_KEY   — Langfuse public key
  SPARK_LANGFUSE_SECRET — Langfuse secret key (for signing)
"""

from __future__ import annotations

import logging
import os
import time
from base64 import b64encode

import httpx
import httpx
from opentelemetry.sdk.trace import ReadableSpan, SpanProcessor

logger = logging.getLogger(__name__)


class LangfuseSpanProcessor(SpanProcessor):
    """Export finished spans to Langfuse via its OTLP-compatible endpoint."""

    def __init__(
        self,
        base_url: str,
        public_key: str,
        secret_key: str = "",
        flush_interval: float = 5.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.public_key = public_key
        self.secret_key = secret_key
        self.flush_interval = flush_interval
        self._buffer: list[dict] = []
        self._last_flush = time.time()

    def on_start(self, span: ReadableSpan, parent_context=None) -> None:
        pass

    def on_end(self, span: ReadableSpan) -> None:
        if span.name in ("__default__", ""):
            return

        trace_id = format(span.context.trace_id, "032x")
        span_id = format(span.context.span_id, "016x")

        attrs: dict[str, str] = {}
        if span.attributes:
            for key, value in span.attributes.items():
                attrs[key] = str(value)

        record: dict[str, object] = {
            "id": span_id,
            "traceId": trace_id,
            "name": span.name,
            "startTime": span.start_time / 1e9 if span.start_time else time.time(),
            "endTime": span.end_time / 1e9 if span.end_time else time.time(),
            "attributes": attrs,
        }

        status = span.status
        if status is not None:
            record["statusCode"] = "OK" if status.is_ok else "ERROR"
            if status.description:
                record["statusMessage"] = status.description

        self._buffer.append(record)

        if time.time() - self._last_flush >= self.flush_interval:
            self._flush()

    def _flush(self) -> None:
        if not self._buffer:
            return

        batch = self._buffer[:]
        self._buffer.clear()
        self._last_flush = time.time()

        try:
            auth = b64encode(f"{self.public_key}:".encode()).decode()
            headers = {
                "Authorization": f"Basic {auth}",
                "Content-Type": "application/json",
            }

            with httpx.Client(timeout=10.0) as client:
                for record in batch:
                    client.post(
                        f"{self.base_url}/api/v1/ingestion",
                        json={"batch": [record]},
                        headers=headers,
                    )
        except Exception as e:
            logger.warning(f"Langfuse export failed: {e}")

    def shutdown(self) -> None:
        self._flush()

    def force_flush(self, timeout_millis: float = 30000) -> bool:
        self._flush()
        return True


def init_langfuse_exporter() -> LangfuseSpanProcessor | None:
    """Create Langfuse processor if configured. Returns None otherwise."""
    base_url = os.getenv("SPARK_LANGFUSE_URL", "")
    public_key = os.getenv("SPARK_LANGFUSE_KEY", "")
    secret_key = os.getenv("SPARK_LANGFUSE_SECRET", "")

    if not base_url or not public_key:
        logger.info("Langfuse not configured — skipping exporter")
        return None

    processor = LangfuseSpanProcessor(
        base_url=base_url,
        public_key=public_key,
        secret_key=secret_key,
    )
    logger.info(f"Langfuse exporter initialized: {base_url}")
    return processor
