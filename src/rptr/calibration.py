"""Build the calibration page from a loop report.

The loop asks d1 one question: is the evidence enough? The answer comes with a
probability. A probability is only useful if it matches reality, so this module
compares the predicted probability with the outcome and draws the reliability
curve.

Correctness here is the citation hit: the answer cites a document that holds
the gold answer. It is a proxy, not a human grade, and the page says so.

Usage:

    python -m rptr.calibration \
        --input lab/demos/raptor-reserve/evals/modes.json \
        --output docs/calibration.html
"""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any

BIN_COUNT = 10
BAND_ORDER = ("low", "middle", "high")


def _load_rows(path: Path) -> tuple[str, list[dict[str, Any]]]:
    report = json.loads(path.read_text(encoding="utf-8"))
    place = report["places"][0]
    answers = place.get("answers", {})
    rows = [row for row in answers.get("results", []) if row.get("sufficiency")]
    return place.get("place_id", "place"), rows


def _sample(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sample: list[dict[str, Any]] = []
    for row in rows:
        decision = row["sufficiency"]
        probability = float(decision.get("probability") or 0.0)
        sample.append(
            {
                "id": row["id"],
                "type": row.get("type", "single"),
                "probability": probability,
                "confidence": float(decision.get("confidence") or 0.0),
                "band": decision.get("band") or "low",
                "source": decision.get("source") or "d1",
                "correct": 1.0 if row.get("citation_hit") else 0.0,
            }
        )
    return sample


def _bins(sample: list[dict[str, Any]]) -> list[dict[str, Any]]:
    bins: list[dict[str, Any]] = []
    for index in range(BIN_COUNT):
        low = index / BIN_COUNT
        high = (index + 1) / BIN_COUNT
        members = [
            item for item in sample if low <= item["probability"] < high or (index == 9 and item["probability"] == 1.0)
        ]
        predicted = sum(item["probability"] for item in members) / len(members) if members else 0.0
        observed = sum(item["correct"] for item in members) / len(members) if members else 0.0
        bins.append(
            {
                "label": f"{low:.1f}-{high:.1f}",
                "count": len(members),
                "predicted": predicted,
                "observed": observed,
                "gap": observed - predicted if members else 0.0,
            }
        )
    return bins


def _bands(sample: list[dict[str, Any]]) -> list[dict[str, Any]]:
    bands: list[dict[str, Any]] = []
    for band in BAND_ORDER:
        members = [item for item in sample if item["band"] == band]
        delegated = [item for item in members if item["source"] == "lfm"]
        bands.append(
            {
                "band": band,
                "count": len(members),
                "delegated": len(delegated),
                "accuracy": sum(item["correct"] for item in members) / len(members)
                if members
                else 0.0,
            }
        )
    return bands


def _brier(sample: list[dict[str, Any]]) -> float:
    if not sample:
        return 0.0
    return sum((item["probability"] - item["correct"]) ** 2 for item in sample) / len(sample)


def _svg_reliability(bins: list[dict[str, Any]]) -> str:
    width, height = 720, 420
    left, top, right, bottom = 70, 30, 30, 60
    plot_w = width - left - right
    plot_h = height - top - bottom

    def x(value: float) -> float:
        return left + value * plot_w

    def y(value: float) -> float:
        return top + (1.0 - value) * plot_h

    parts = [
        f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Reliability curve">',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#fffaf2"/>',
    ]
    # grid
    for tick in range(0, 11, 2):
        value = tick / 10
        parts.append(
            f'<line x1="{x(value):.1f}" y1="{y(0):.1f}" x2="{x(value):.1f}" y2="{y(1):.1f}" '
            'stroke="#e6dccd" stroke-width="1"/>'
        )
        parts.append(
            f'<line x1="{x(0):.1f}" y1="{y(value):.1f}" x2="{x(1):.1f}" y2="{y(value):.1f}" '
            'stroke="#e6dccd" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{x(value):.1f}" y="{y(0) + 22:.1f}" text-anchor="middle" '
            'font-size="12" fill="#6b6257">'
            f"{value:.1f}</text>"
        )
        parts.append(
            f'<text x="{x(0) - 12:.1f}" y="{y(value) + 4:.1f}" text-anchor="end" '
            'font-size="12" fill="#6b6257">'
            f"{value:.1f}</text>"
        )
    # diagonal
    parts.append(
        f'<line x1="{x(0):.1f}" y1="{y(0):.1f}" x2="{x(1):.1f}" y2="{y(1):.1f}" '
        'stroke="#6b6257" stroke-width="1.5" stroke-dasharray="6 5"/>'
    )
    # points
    for item in bins:
        if not item["count"]:
            continue
        radius = 5 + min(item["count"], 20) * 0.55
        parts.append(
            f'<circle cx="{x(item["predicted"]):.1f}" cy="{y(item["observed"]):.1f}" '
            f'r="{radius:.1f}" fill="#b43a1f" fill-opacity="0.35" stroke="#b43a1f" '
            'stroke-width="2"/>'
        )
        parts.append(
            f'<text x="{x(item["predicted"]):.1f}" y="{y(item["observed"]) - radius - 7:.1f}" '
            'text-anchor="middle" font-size="11" fill="#1f1b16">'
            f'{item["count"]}</text>'
        )
    # axis labels
    parts.append(
        f'<text x="{left + plot_w / 2:.1f}" y="{height - 14}" text-anchor="middle" '
        'font-size="13" fill="#1f1b16">Predicted probability (evidence is sufficient)</text>'
    )
    parts.append(
        f'<text x="18" y="{top + plot_h / 2:.1f}" text-anchor="middle" font-size="13" '
        'fill="#1f1b16" transform="rotate(-90 18 '
        f'{top + plot_h / 2:.1f})">Observed accuracy</text>'
    )
    parts.append("</svg>")
    return "".join(parts)


def _svg_histogram(bins: list[dict[str, Any]]) -> str:
    width, height = 720, 220
    left, top, right, bottom = 70, 20, 30, 46
    plot_w = width - left - right
    plot_h = height - top - bottom
    peak = max((item["count"] for item in bins), default=1) or 1
    slot = plot_w / len(bins)
    parts = [
        f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Probability histogram">',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#fffaf2"/>',
    ]
    for index, item in enumerate(bins):
        bar_h = (item["count"] / peak) * plot_h
        x = left + index * slot + slot * 0.18
        y = top + plot_h - bar_h
        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{slot * 0.64:.1f}" height="{bar_h:.1f}" '
            'fill="#b43a1f" fill-opacity="0.7"/>'
        )
        parts.append(
            f'<text x="{x + slot * 0.32:.1f}" y="{y - 6:.1f}" text-anchor="middle" '
            'font-size="11" fill="#1f1b16">'
            f'{item["count"]}</text>'
        )
        parts.append(
            f'<text x="{x + slot * 0.32:.1f}" y="{top + plot_h + 20:.1f}" text-anchor="middle" '
            'font-size="11" fill="#6b6257">'
            f'{item["label"]}</text>'
        )
    parts.append(
        f'<line x1="{left:.1f}" y1="{top + plot_h:.1f}" x2="{left + plot_w:.1f}" '
        f'y2="{top + plot_h:.1f}" stroke="#d9cfc0" stroke-width="1"/>'
    )
    parts.append(
        f'<text x="{left + plot_w / 2:.1f}" y="{height - 8}" text-anchor="middle" '
        'font-size="13" fill="#1f1b16">d1 probability, one bar per 0.1 band</text>'
    )
    parts.append("</svg>")
    return "".join(parts)


def _table(headers: list[str], rows: list[list[str]], numeric_from: int = 1) -> str:
    head = "".join(f"<th>{html.escape(item)}</th>" for item in headers)
    body = []
    for row in rows:
        cells = "".join(
            f'<td class="{"num" if index >= numeric_from else "txt"}">{cell}</td>'
            for index, cell in enumerate(row)
        )
        body.append(f"<tr>{cells}</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def build_page(place_id: str, rows: list[dict[str, Any]]) -> str:
    sample = _sample(rows)
    bins = _bins(sample)
    bands = _bands(sample)
    brier = _brier(sample)
    accuracy = sum(item["correct"] for item in sample) / len(sample) if sample else 0.0
    delegated = sum(1 for item in sample if item["source"] == "lfm")
    empty = len(sample) - sum(1 for item in bins if item["count"])
    mean_probability = sum(item["probability"] for item in sample) / len(sample) if sample else 0.0

    bin_rows = [
        [
            item["label"],
            str(item["count"]),
            f"{item['predicted']:.3f}" if item["count"] else "-",
            f"{item['observed']:.3f}" if item["count"] else "-",
            f"{item['gap']:+.3f}" if item["count"] else "-",
        ]
        for item in bins
    ]
    band_rows = [
        [
            item["band"],
            str(item["count"]),
            str(item["delegated"]),
            f"{item['accuracy']:.3f}" if item["count"] else "-",
        ]
        for item in bands
    ]

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Calibration - refeed.raptor.today</title>
<meta name="description" content="The reliability curve of the d1 sufficiency decision in the Refeed Raptor lab.">
<link rel="icon" href="./favicon.png" type="image/png">
<style>
  :root {{
    --paper: #f6f1e8;
    --ink: #1f1b16;
    --muted: #6b6257;
    --rust: #b43a1f;
    --line: #d9cfc0;
    --panel: #fffaf2;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: var(--paper);
    color: var(--ink);
    font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
    line-height: 1.6;
  }}
  .wrap {{ max-width: 860px; margin: 0 auto; padding: 32px 20px 64px; }}
  header {{ padding: 24px 0 8px; border-bottom: 1px solid var(--line); margin-bottom: 28px; }}
  .eyebrow {{ margin: 0; color: var(--muted); font-size: 12px; letter-spacing: .18em; text-transform: uppercase; }}
  h1 {{ margin: 6px 0 8px; font-size: clamp(30px, 5vw, 44px); line-height: 1.05; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }}
  h2 {{ margin: 34px 0 10px; font-size: 22px; }}
  p {{ margin: 0 0 14px; }}
  a {{ color: var(--rust); }}
  .lede {{ color: var(--muted); font-size: 18px; max-width: 64ch; }}
  .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin: 22px 0 8px; }}
  .stat {{ background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 14px 16px; }}
  .stat .value {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 28px; line-height: 1.1; }}
  .stat .label {{ color: var(--muted); font-size: 12px; letter-spacing: .08em; text-transform: uppercase; }}
  figure {{ margin: 18px 0 8px; background: var(--panel); border: 1px solid var(--line); border-radius: 12px; padding: 12px; }}
  figure svg {{ width: 100%; height: auto; display: block; }}
  figcaption {{ color: var(--muted); font-size: 13px; padding: 8px 4px 2px; }}
  table {{ width: 100%; border-collapse: collapse; margin: 12px 0 20px; font-size: 14px; }}
  th, td {{ text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--line); }}
  th {{ color: var(--muted); font-size: 12px; letter-spacing: .06em; text-transform: uppercase; }}
  td.num {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; text-align: right; }}
  .note {{ background: var(--panel); border-left: 3px solid var(--rust); padding: 12px 16px; margin: 18px 0; }}
  footer {{ margin-top: 42px; padding-top: 18px; border-top: 1px solid var(--line); color: var(--muted); font-size: 14px; }}
</style>
</head>
<body>
<div class="wrap">
<header>
  <p class="eyebrow">Refeed Raptor - a local RAG lab</p>
  <h1>Is the decision model calibrated?</h1>
  <p class="lede">The loop asks d1-3B one question: is the evidence enough? The model returns a probability, the loop trusts it in the high band and delegates in the low band. This page checks whether the probability means what it says.</p>
</header>

<section>
  <div class="stats">
    <div class="stat"><div class="value">{len(sample)}</div><div class="label">questions</div></div>
    <div class="stat"><div class="value">{accuracy:.3f}</div><div class="label">citation hit rate</div></div>
    <div class="stat"><div class="value">{brier:.3f}</div><div class="label">Brier score</div></div>
    <div class="stat"><div class="value">{delegated}</div><div class="label">delegated to LFM</div></div>
  </div>
  <p>Place <code>{html.escape(place_id)}</code>. Mean predicted probability {mean_probability:.3f}, observed accuracy {accuracy:.3f}. A perfectly calibrated model sits on the dashed diagonal: when it says 0.8, it is right eight times out of ten.</p>
</section>

<section>
  <h2>The reliability curve</h2>
  <figure>
    {_svg_reliability(bins)}
    <figcaption>Each circle is a 0.1 probability bin. The number in the circle is how many questions landed in that bin; the circle size follows the same count. The diagonal is perfect calibration.</figcaption>
  </figure>
  <p>The curve is the whole argument for a calibration band. A decision model that says 0.9 and is right half the time is not a small model with a cheap opinion, it is a random number with a latency cost. A model that says 0.9 and is right 0.9 of the time can gate a loop.</p>
</section>

<section>
  <h2>Where the questions land</h2>
  <figure>
    {_svg_histogram(bins)}
    <figcaption>Most questions sit high, which is what a 100-document corpus with 50 curated questions should look like.</figcaption>
  </figure>
  {_table(["Bin", "Questions", "Mean predicted", "Observed", "Gap"], bin_rows, numeric_from=1)}
</section>

<section>
  <h2>The bands</h2>
  <p>The loop keeps a d1 answer in the high band, delegates a low confidence answer to LFM2.5, and treats the middle band as its own. This table shows what each band was worth on this set.</p>
  {_table(["Band", "Questions", "Delegated", "Accuracy"], band_rows, numeric_from=1)}
  <p>{empty} of the ten probability bins are empty. A gap in the curve is not a failure; it is the corpus saying that the questions are either clearly answerable or clearly not.</p>
</section>

<section>
  <h2>What correctness means here</h2>
  <div class="note">
    <p><strong>Correct</strong> means the answer cites a document that holds the gold answer. That is a cheap automatic proxy, and it is not a faithfulness score. A sentence can be true and cite the wrong record, and a record can be right while the sentence around it is wrong. The recorded turns are checked by hand for exactly this reason.</p>
  </div>
  <p>The Brier score is the mean squared distance between the probability and the outcome. Lower is better. A model that always says 0.5 on a balanced set scores 0.25; this one scores {brier:.3f}.</p>
</section>

<section>
  <h2>Reproduce it</h2>
  <p>The input is the committed loop report:</p>
  <pre><code>pixi run eval -- --place raptor-reserve --modes --unknown \\
  --output lab/demos/raptor-reserve/evals/modes.json
pixi run calibrate</code></pre>
  <p>The report keeps every per-question row, including the probability, the band, and the citations, so each number on this page can be checked against the raw file.</p>
</section>

<footer>
  <p>Refeed Raptor - an educational lab about RAG, memory, and the cost of a second look.</p>
  <p><a href="./">The lab</a> - <a href="https://github.com/AISidesKicks/refeed-raptor-today">github.com/AISidesKicks/refeed-raptor-today</a></p>
</footer>
</div>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the calibration page.")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("lab/demos/raptor-reserve/evals/modes.json"),
        help="Loop report written by `eval --modes`.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/calibration.html"),
        help="Where to write the page.",
    )
    args = parser.parse_args()

    place_id, rows = _load_rows(args.input)
    if not rows:
        raise SystemExit(f"no sufficiency decisions in {args.input}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(build_page(place_id, rows), encoding="utf-8")

    sample = _sample(rows)
    bins = _bins(sample)
    print(
        f"{len(sample)} questions  accuracy "
        f"{sum(item['correct'] for item in sample) / len(sample):.3f}  "
        f"Brier {_brier(sample):.3f}"
    )
    for item in bins:
        if item["count"]:
            print(
                f"  {item['label']}  n={item['count']:<3} "
                f"pred {item['predicted']:.3f}  observed {item['observed']:.3f}"
            )
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
