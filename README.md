# Refeed Raptor

A local RAG lab: a RAPTOR summary tree, a small refeed loop, and a System-1 decision model. No cloud model, no API key.

- Public overview: `docs/index.html`
- Design intent: `INTENT.md`
- First corpus: `lab/demos/raptor-reserve/`
- Metrics reference: `mds/metrics.md`

## Quick start

The environment is a pixi workspace named `rptr`.

```bash
pixi install
pixi shell
```

The corpus is already generated. To rebuild it:

```bash
cd lab/demos/raptor-reserve
python tools/build_corpus.py
```

## Status

The corpus and eval set are in place. The app, the Docker stack, and the replay player are next.

## License

The corpus is CC BY 4.0. The code license is separate.
