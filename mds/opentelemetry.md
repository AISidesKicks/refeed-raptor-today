# OpenTelemetry and Phoenix

The lab shows its own trace in the UI and in the API. That is enough for a demo, but it is not a standard format, so the trace cannot be opened in a tracing tool. The lab also exports every run to OpenTelemetry, and Arize Phoenix collects it.

## The setup

One variable turns it on:

```bash
RPTR_OTLP_ENDPOINT=http://127.0.0.1:6006/v1/traces pixi run serve
```

Without the variable the module `src/rptr/tracing.py` does nothing. No socket, no thread, no dependency at runtime. The app never needs a collector.

The collector is the `rptr-phoenix` container from `docker/compose.yaml`:

```bash
pixi run phoenix-up      # start it
pixi run phoenix-stop    # stop it
```

It listens on 6006 for the UI and for OTLP over HTTP, and on 4317 for OTLP over gRPC. The lab uses the HTTP path because it needs no gRPC package.

## What is exported

One parent span per run, and one child span per step of the run trace.

```
raptor.answer            the whole run
  rptr.retrieve          the top 20 passages
  rptr.relevance         the per passage probabilities
  rptr.sufficient        the sufficiency decision and the band
  rptr.action            the chosen action
  rptr.rewrite           the new queries
  rptr.write             the answer and the latency
  rptr.cite              inline citations or a sources footer
  rptr.grounded          the groundedness decision
```

The parent span carries the question, the place, the number of refeeds, the answer length, the citation count, the total latency, and the warning if there was one. A run that could not answer gets an error status.

The trace id is copied into the API result, so a run in the UI can be matched with a run in the collector:

```json
{"answer": "...", "trace_id": "759c431e3e60ff44846fca33a0cf97ce"}
```

The UI shows the first 12 characters under the answer, next to the refeed count and the latency.

## The code

The module is small on purpose:

```python
@contextmanager
def span(name: str, **attributes: Any) -> Iterator[Span | None]:
    if not enabled():
        yield None
        return
    tracer = _setup()
    with tracer.start_as_current_span(name) as active:
        ...
```

The pipeline wraps the run in one span and exports the trace list as child spans:

```python
with tracing.span("raptor.answer", **{"rptr.place": place.id}) as span:
    result = _answer_question(router, conn, place, question, config)
    tracing.record_steps(span, result.get("trace", []))
    tracing.finish(span, result)
    result["trace_id"] = tracing.trace_id(span)
```

The exporter is a `BatchSpanProcessor`, so the spans leave the process in the background and never block an answer. The provider is shut down at exit.

## The tests

The tests never open a socket. They swap the exporter:

```python
exporter = InMemorySpanExporter()
tracing.use_exporter(exporter)
result = answer_question(FakeRouter(), conn, place, "Which ranger approved it?")
assert "raptor.answer" in [span.name for span in exporter.get_finished_spans()]
```

That is the same trick the pipeline tests use for the router. The decision logic stays testable without a model.

## Why this and not the Phoenix SDK

The Phoenix python package would pull in a large dependency tree and would want to own the tracing setup. The OpenTelemetry SDK is the standard, the exporter is one HTTP POST, and the collector can be anything: Phoenix, Jaeger, or a plain OTLP endpoint in the cloud. The lab keeps the data local, so the default is a local container, but the endpoint is a variable.

## What is not exported yet

The spans carry the decision data, not the text of the passages. That is deliberate: a passage can be long, and a trace tool is not a corpus viewer. The passages stay in SQLite, and the trace keeps the ids.

Read next: [the refeed loop](refeed.md), [llama.cpp as the local router](llamacpp.md).
