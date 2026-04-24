"""Render paper-friendly summaries from ICSE benchmark result JSON."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from paper_helpers import RESULTS_DIR, markdown_table, read_json, write_json, write_text


def run(*, results_dir: Path = RESULTS_DIR) -> dict[str, Any]:
    compile_data = read_json(results_dir / "compile_matrix.json")
    roundtrip_data = read_json(results_dir / "roundtrip_fidelity.json")
    assertion_data = read_json(results_dir / "assertion_eval.json")
    annotation_data = _read_optional_json(results_dir / "annotation_agreement.json")
    summary = build_summary(compile_data, roundtrip_data, assertion_data, annotation_data)
    write_json(results_dir / "summary.json", summary)
    write_text(
        results_dir / "tables.md",
        render_tables(compile_data, roundtrip_data, assertion_data, annotation_data),
    )
    write_text(results_dir / "numbers.md", render_numbers(summary))
    return summary


def build_summary(
    compile_data: dict[str, Any],
    roundtrip_data: dict[str, Any],
    assertion_data: dict[str, Any],
    annotation_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    summary = {
        "compile": compile_data["summary"],
        "roundtrip": roundtrip_data["summary"],
        "assertions": assertion_data["summary"],
    }
    if annotation_data is not None:
        summary["annotation_agreement"] = {
            "item_count": annotation_data["item_count"],
            "fields": annotation_data["fields"],
        }
    return summary


def render_tables(
    compile_data: dict[str, Any],
    roundtrip_data: dict[str, Any],
    assertion_data: dict[str, Any],
    annotation_data: dict[str, Any] | None = None,
) -> str:
    compile_rows = [
        [
            target,
            str(
                sum(
                    1
                    for record in compile_data["results"]
                    if record["target"] == target and record["ok"]
                )
            ),
            str(sum(1 for record in compile_data["results"] if record["target"] == target)),
        ]
        for target in compile_data["targets"]
    ]
    compiled_success = [
        record for record in roundtrip_data["compiled"] if record["ok"]
    ]
    roundtrip_rows = [
        [
            source_type,
            str(sum(1 for record in compiled_success if record["source_type"] == source_type)),
            _mean_percent(
                record["exact_match_ratio"]
                for record in compiled_success
                if record["source_type"] == source_type
            ),
        ]
        for source_type in sorted({record["source_type"] for record in roundtrip_data["compiled"]})
    ]
    assertion_rows = [
        [
            assertion_type,
            str(values["total"]),
            str(values["caught"]),
            f"{values['catch_rate']}%",
        ]
        for assertion_type, values in assertion_data["summary"]["per_assertion"].items()
    ]
    annotation_section: list[str] = []
    if annotation_data is not None:
        annotation_rows = [
            [
                field,
                str(values["total"]),
                f"{values['percent_agreement']}%",
                str(values["cohen_kappa"]),
                str(values["krippendorff_alpha_nominal"]),
            ]
            for field, values in annotation_data["fields"].items()
        ]
        annotation_section = [
            "",
            "## Annotation agreement",
            markdown_table(
                ["Field", "Items", "Agreement", "Cohen kappa", "Krippendorff alpha"],
                annotation_rows,
            ),
        ]
    sections = [
        "# ICSE paper tables",
        "",
        "## Target coverage",
        markdown_table(["Target", "Succeeded", "Total"], compile_rows),
        "",
        "## Round-trip fidelity",
        markdown_table(["Source type", "Imported", "Average field fidelity"], roundtrip_rows),
        "",
        "## Assertion effectiveness",
        markdown_table(["Assertion", "Targeted samples", "Caught", "Catch rate"], assertion_rows),
        *annotation_section,
        "",
    ]
    return "\n".join(sections)


def render_numbers(summary: dict[str, Any]) -> str:
    compile_summary = summary["compile"]
    roundtrip_summary = summary["roundtrip"]
    assertion_summary = summary["assertions"]
    annotation_summary = summary.get("annotation_agreement")
    lines = [
        "# ICSE paper numbers",
        "",
        (
            f"- The compile matrix contains {compile_summary['total']} contract-target "
            f"pairs across {compile_summary['contract_count']} contracts and "
            f"{compile_summary['target_count']} representative targets; "
            f"{compile_summary['ok']} compiled successfully "
            f"({compile_summary['compile_success_rate']}%)."
        ),
        (
            f"- Compiled round-trip import succeeded for "
            f"{roundtrip_summary['compiled_ok']} of {roundtrip_summary['compiled_total']} "
            f"attempted artifacts ({roundtrip_summary['compiled_import_success_rate']}%)."
        ),
        (
            f"- Successful compiled round trips had an average core-field fidelity of "
            f"{roundtrip_summary['compiled_average_field_fidelity']}%."
        ),
        (
            f"- Handwritten artifact import succeeded for "
            f"{roundtrip_summary['handwritten_ok']} of {roundtrip_summary['handwritten_total']} "
            f"artifacts ({roundtrip_summary['handwritten_import_success_rate']}%)."
        ),
        (
            f"- All {assertion_summary['valid_passed']} of {assertion_summary['valid_total']} "
            f"valid outputs passed offline acceptance tests "
            f"({assertion_summary['valid_pass_rate']}%)."
        ),
        (
            f"- The targeted defect suite caught "
            f"{assertion_summary['isolated_defects_caught']} of "
            f"{assertion_summary['isolated_defect_total']} labeled defects "
            f"({assertion_summary['targeted_defect_catch_rate']}%)."
        ),
    ]
    if annotation_summary is not None:
        expected_ok = annotation_summary["fields"]["expected_ok"]
        targeted = annotation_summary["fields"]["targeted_assertion"]
        lines.extend(
            [
                (
                    f"- Assisted annotation agreement covered "
                    f"{annotation_summary['item_count']} output samples; "
                    f"`expected_ok` agreement was {expected_ok['percent_agreement']}% "
                    f"(Cohen's kappa {expected_ok['cohen_kappa']})."
                ),
                (
                    f"- `targeted_assertion` agreement was "
                    f"{targeted['percent_agreement']}% "
                    f"(Cohen's kappa {targeted['cohen_kappa']})."
                ),
            ]
        )
    lines.append("")
    return "\n".join(lines)


def _mean_percent(values: Any) -> str:
    collected = list(values)
    if not collected:
        return "0.0%"
    return f"{round(sum(collected) / len(collected) * 100, 2)}%"


def _read_optional_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    return read_json(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=RESULTS_DIR)
    args = parser.parse_args()
    run(results_dir=args.results_dir)
    print(f"Rendered tables and numbers into {args.results_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
