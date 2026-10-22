"""Optional OpenTelemetry export of the run trace to a local collector.

The lab has its own trace view in the UI and in the API. This module adds the
standard one: when `RPTR_OTLP_ENDPOINT` points at a collector, every run is
exported as OpenTelemetry spans. The default target is the local Phoenix
container from `docker/compose.yaml`:

    RPTR_OTLP_ENDPOINT=http://127.0.0.1:6006/v1/traces

Without the variable the module stays a no-op. The app never needs a running
collector, and the tests never open a socket.

The shape of the export:

- one parent span `raptor.answer` per run, with the question, the place, the
  number of refeeds, and the latency
- one child span per step of the run trace: retrieve, relevance, sufficient,
  action, rewrite, write, cite, grounded

The trace id is copied into the API result, so a run in the UI can be matched
with a run in the collector.
"""

from __future__ import annotations

import atexit
import json
import os
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Span, Status, StatusCode

TRACER_NAME = "rptr"
DEFAULT_ENDPOINT = "http://127.0.0.1:6006/v1/traces"
MAX_ATTRIBUTE_LENGTH = 800

_provider: TracerProvider | None = None
_tracer: trace.Tracer | None = None
_ready = False


def endpoint() -> str | None:
    """The OTLP endpoint, or None when tracing is off."""

    value = os.environ.get("RPTR_OTLP_ENDPOINT", "").strip()
    return value or None


def enabled() -> bool:
    """True when the run trace should be exported."""

    return endpoint() is not None


def _setup() -> trace.Tracer:
    """Build the tracer once, on the first traced call."""

    global _provider, _tracer, _ready
    if _ready:
        return _tracer or trace.get_tracer(TRACER_NAME)
    _ready = True

    target = endpoint()
    if not target:
        _tracer = trace.get_tracer(TRACER_NAME)
        return _tracer

    resource = Resource.create(
        {
            "service.name": os.environ.get("RPTR_SERVICE_NAME", "refeed-raptor"),
            "service.version": "0.1.0",
        }
    )
    provider = TracerProvider(resource=resource)
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=target)))
    atexit.register(provider.shutdown)
    _provider = provider
    _tracer = provider.get_tracer(TRACER_NAME)
    return _tracer


def use_exporter(exporter: Any) -> None:
    """Send the spans to a custom exporter. Used by the tests."""

    global _provider, _tracer, _ready
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor

    provider = TracerProvider(resource=Resource.create({"service.name": "rptr-test"}))
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    _provider = provider
    _tracer = provider.get_tracer(TRACER_NAME)
    _ready = True


def reset() -> None:
    """Drop the cached provider. Used by the tests."""

    global _provider, _tracer, _ready
    if _provider is not None:
        _provider.shutdown()
    _provider = None
    _tracer = None
    _ready = False


def set_attribute(span: Span | None, key: str, value: Any) -> None:
    """Set one attribute, keeping the value types OpenTelemetry accepts."""

    if span is None or value is None:
        return
    if isinstance(value, (bool, int, float)):
        span.set_attribute(key, value)
        return
    if isinstance(value, str):
        span.set_attribute(key, value[:MAX_ATTRIBUTE_LENGTH])
        return
    try:
        payload = json.dumps(value, default=str)
    except (TypeError, ValueError):
        payload = str(value)
    span.set_attribute(key, payload[:MAX_ATTRIBUTE_LENGTH])


@contextmanager
def span(name: str, **attributes: Any) -> Iterator[Span | None]:
    """Open a span when tracing is on, and do nothing when it is off."""

    if not enabled():
        yield None
        return
    tracer = _setup()
    with tracer.start_as_current_span(name) as active:
        for key, value in attributes.items():
            set_attribute(active, key, value)
        yield active


def record_steps(parent: Span | None, steps: list[dict[str, Any]]) -> None:
    """Export the run trace as child spans of the parent span."""

    if parent is None or not steps:
        return
    tracer = _setup()
    for step in steps:
        name = str(step.get("step", "step"))
        with tracer.start_as_current_span(f"rptr.{name}") as child:
            for key, value in step.items():
                if key == "step":
                    continue
                set_attribute(child, f"rptr.{key}", value)
            if step.get("rejected") or step.get("warning"):
                child.set_status(Status(StatusCode.ERROR, str(step.get("warning", ""))))


def finish(parent: Span | None, result: dict[str, Any]) -> None:
    """Copy the outcome of a run onto the parent span."""

    if parent is None:
        return
    set_attribute(parent, "rptr.refeeds", result.get("refeeds"))
    set_attribute(parent, "rptr.can_answer", result.get("can_answer"))
    set_attribute(parent, "rptr.answer_chars", len(str(result.get("answer", ""))))
    set_attribute(parent, "rptr.citations", len(result.get("citations", [])))
    set_attribute(parent, "rptr.total_ms", (result.get("timings") or {}).get("total_ms"))
    set_attribute(parent, "rptr.warning", result.get("warning"))
    if not result.get("can_answer"):
        parent.set_status(Status(StatusCode.ERROR, "no answer"))


def trace_id(span: Span | None) -> str | None:
    """The hex trace id of a span, so a run can be found in the collector."""

    if span is None:
        return None
    context = span.get_span_context()
    if not context.is_valid:
        return None
    return format(context.trace_id, "032x")
