"""Compute assisted annotation agreement for the reproducibility benchmark."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any

from benchmark_helpers import (
    BENCHMARK_ROOT,
    RESULTS_DIR,
    markdown_table,
    read_json,
    write_json,
    write_text,
)


def run(
    *,
    benchmark_root: Path = BENCHMARK_ROOT,
    results_dir: Path = RESULTS_DIR,
) -> dict[str, Any]:
    payload = read_json(benchmark_root / "labels" / "annotation_rounds.json")
    annotator_a, annotator_b = payload["annotators"]
    fields = payload["fields"]
    items = payload["items"]
    field_results = {
        field: _agreement_for_field(items, annotator_a, annotator_b, field)
        for field in fields
    }
    summary = {
        "protocol": payload["protocol"],
        "unit": payload["unit"],
        "annotators": payload["annotators"],
        "item_count": len(items),
        "fields": field_results,
    }
    write_json(results_dir / "annotation_agreement.json", summary)
    write_text(results_dir / "annotation_agreement.md", render_agreement_markdown(summary))
    return summary


def _agreement_for_field(
    items: list[dict[str, Any]],
    annotator_a: str,
    annotator_b: str,
    field: str,
) -> dict[str, Any]:
    pairs = [
        (
            str(item["labels"][annotator_a][field]),
            str(item["labels"][annotator_b][field]),
            item["id"],
        )
        for item in items
    ]
    total = len(pairs)
    agreements = sum(1 for left, right, _ in pairs if left == right)
    labels_a = [left for left, _, _ in pairs]
    labels_b = [right for _, right, _ in pairs]
    labels_all = labels_a + labels_b
    return {
        "total": total,
        "agreements": agreements,
        "disagreements": total - agreements,
        "percent_agreement": _round_ratio(agreements, total),
        "cohen_kappa": _cohen_kappa(labels_a, labels_b),
        "krippendorff_alpha_nominal": _krippendorff_alpha_nominal(labels_a, labels_b),
        "labels": sorted(set(labels_all)),
        "disagreement_items": [
            {"sample": sample, annotator_a: left, annotator_b: right}
            for left, right, sample in pairs
            if left != right
        ],
    }


def _cohen_kappa(labels_a: list[str], labels_b: list[str]) -> float:
    total = len(labels_a)
    if total == 0:
        return 0.0
    observed = sum(1 for left, right in zip(labels_a, labels_b) if left == right) / total
    counts_a = Counter(labels_a)
    counts_b = Counter(labels_b)
    categories = set(counts_a) | set(counts_b)
    expected = sum(
        (counts_a[category] / total) * (counts_b[category] / total)
        for category in categories
    )
    if expected == 1.0:
        return 1.0 if observed == 1.0 else 0.0
    return round((observed - expected) / (1 - expected), 4)


def _krippendorff_alpha_nominal(labels_a: list[str], labels_b: list[str]) -> float:
    total = len(labels_a)
    if total == 0:
        return 0.0
    observed_disagreement = sum(
        1 for left, right in zip(labels_a, labels_b) if left != right
    ) / total
    pooled_counts = Counter(labels_a + labels_b)
    pooled_total = total * 2
    expected_disagreement = 1 - sum(
        (count / pooled_total) ** 2 for count in pooled_counts.values()
    )
    if expected_disagreement == 0.0:
        return 1.0 if observed_disagreement == 0.0 else 0.0
    return round(1 - (observed_disagreement / expected_disagreement), 4)


def _round_ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round((numerator / denominator) * 100, 2)


def render_agreement_markdown(summary: dict[str, Any]) -> str:
    rows = [
        [
            field,
            str(values["total"]),
            f"{values['percent_agreement']}%",
            str(values["cohen_kappa"]),
            str(values["krippendorff_alpha_nominal"]),
            str(values["disagreements"]),
        ]
        for field, values in summary["fields"].items()
    ]
    lines = [
        "# Annotation agreement",
        "",
        f"- Protocol: `{summary['protocol']}`",
        f"- Unit: `{summary['unit']}`",
        f"- Annotators: {', '.join(summary['annotators'])}",
        f"- Items: {summary['item_count']}",
        "",
        markdown_table(
            ["Field", "Items", "Agreement", "Cohen kappa", "Krippendorff alpha", "Disagreements"],
            rows,
        ),
        "",
        "## Disagreements",
        "",
    ]
    for field, values in summary["fields"].items():
        disagreements = values["disagreement_items"]
        if not disagreements:
            continue
        lines.append(f"### {field}")
        for item in disagreements:
            lines.append(f"- `{item['sample']}`: {item}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark-root", type=Path, default=BENCHMARK_ROOT)
    parser.add_argument("--results-dir", type=Path, default=RESULTS_DIR)
    args = parser.parse_args()
    payload = run(benchmark_root=args.benchmark_root, results_dir=args.results_dir)
    print(
        "Annotation agreement: "
        f"{payload['item_count']} items, "
        f"{len(payload['fields'])} fields."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



