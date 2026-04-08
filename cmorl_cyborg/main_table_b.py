from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

from .evaluate_constraints import (
    compute_shared_thresholds,
    evaluate_constraints,
    write_aggregated_constraint_metrics,
)
from cmorl_minicage.utils import load_json, save_json

_TABLE_B_COLUMNS = [
    "method_name",
    "num_runs",
    "security_return",
    "business_return",
    "cost_return",
    "feasible_rate",
    "mean_violation",
    "final_critical_compromised_hosts",
    "critical_impact_count",
    "high_disruption_action_rate",
]


def _repo_root_from_path(path: str | Path) -> Path:
    path = Path(path).resolve()
    for candidate in (path, *path.parents):
        if (candidate / "cmorl_cyborg").exists():
            return candidate
    raise ValueError(f"Could not infer repository root from {path}")


def _resolve_path(anchor: str | Path, raw_path: str | Path) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return (_repo_root_from_path(anchor) / path).resolve()


def _resolve_unique_glob(anchor: str | Path, pattern: str) -> Path:
    pattern_path = _resolve_path(anchor, pattern)
    if pattern_path.is_absolute():
        matches = sorted(Path("/").glob(str(pattern_path)[1:]))
    else:
        matches = sorted(Path(".").glob(str(pattern_path)))
    if len(matches) != 1:
        raise ValueError(
            f"Expected exactly one match for {pattern!r}, found {len(matches)}: {matches}"
        )
    return matches[0].resolve()


def _resolve_source_path(anchor: str | Path, entry: dict[str, Any], key: str) -> Path:
    raw_path = entry.get(key)
    raw_glob = entry.get(f"{key}_glob")
    if raw_path:
        return _resolve_path(anchor, raw_path)
    if raw_glob:
        return _resolve_unique_glob(anchor, raw_glob)
    raise ValueError(f"Entry must provide {key} or {key}_glob")


def _load_yaml_config(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"Config file must contain a mapping: {path}")
    return payload


def _write_csv(path: str | Path, rows: list[dict[str, Any]]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=_TABLE_B_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _write_tex(path: str | Path, rows: list[dict[str, Any]]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "\\begin{tabular}{" + "l" * len(_TABLE_B_COLUMNS) + "}",
        "\\hline",
        " & ".join(_TABLE_B_COLUMNS) + " \\\\",
        "\\hline",
    ]
    for row in rows:
        lines.append(" & ".join(str(row[column]) for column in _TABLE_B_COLUMNS) + " \\\\")
    lines.extend(["\\hline", "\\end{tabular}"])
    path.write_text("\n".join(lines), encoding="utf-8")


def _summary_row(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "method_name": payload.get("method_name", ""),
        "num_runs": int(payload.get("num_runs", 0)),
        "security_return": f"{float(payload.get('security_return', 0.0)):.4f}",
        "business_return": f"{float(payload.get('business_return', 0.0)):.4f}",
        "cost_return": f"{float(payload.get('cost_return', 0.0)):.4f}",
        "feasible_rate": f"{float(payload.get('feasible_rate', 0.0)):.4f}",
        "mean_violation": f"{float(payload.get('mean_violation', 0.0)):.4f}",
        "final_critical_compromised_hosts": (
            f"{float(payload.get('final_critical_compromised_hosts', 0.0)):.4f}"
        ),
        "critical_impact_count": f"{float(payload.get('critical_impact_count', 0.0)):.4f}",
        "high_disruption_action_rate": (
            f"{float(payload.get('high_disruption_action_rate', 0.0)):.4f}"
        ),
    }


def generate_main_table_b(config_path: str | Path) -> Path:
    config_path = Path(config_path).resolve()
    config = _load_yaml_config(config_path)
    entries = config.get("entries", [])
    if not entries:
        raise ValueError("entries must not be empty")

    output_dir = _resolve_path(config_path, config["output_dir"])
    table_output_dir = _resolve_path(
        config_path,
        config.get("table_output_dir", output_dir / "tables"),
    )
    shared_thresholds_path = _resolve_path(config_path, config["shared_thresholds_path"])

    threshold_sources = [
        str(_resolve_source_path(config_path, source, "path"))
        for source in config.get("threshold_buffer_sources", [])
    ]
    if not threshold_sources:
        raise ValueError("threshold_buffer_sources must not be empty")
    thresholds = compute_shared_thresholds(threshold_sources, shared_thresholds_path)

    per_run_paths: list[str] = []
    grouped_paths: dict[str, list[str]] = defaultdict(list)
    per_run_records: list[dict[str, Any]] = []
    for entry in entries:
        method_name = str(entry["method_name"])
        seed = int(entry["seed"])
        input_path = _resolve_source_path(config_path, entry, "input_path")
        result = evaluate_constraints(
            method_name=method_name,
            input_kind=str(entry.get("input_kind", "buffer")),
            input_path=input_path,
            selection_source=str(entry.get("selection_source", "pareto")),
            thresholds_path=shared_thresholds_path,
            eval_episodes=int(entry.get("eval_episodes", config.get("eval_episodes", 5))),
        )
        output_path = output_dir / method_name / f"seed_{seed:04d}" / "constraint_metrics.json"
        save_json(output_path, result)
        per_run_paths.append(str(output_path.resolve()))
        grouped_paths[method_name].append(str(output_path.resolve()))
        per_run_records.append(
            {
                "method_name": method_name,
                "seed": seed,
                "input_path": str(input_path),
                "output_path": str(output_path.resolve()),
            }
        )

    aggregated_dir = output_dir / "aggregated"
    aggregated_paths: list[str] = []
    table_rows: list[dict[str, Any]] = []
    for method_name in sorted(grouped_paths):
        aggregate_path = aggregated_dir / f"{method_name}.json"
        write_aggregated_constraint_metrics(
            grouped_paths[method_name],
            aggregate_path,
            method_name=method_name,
        )
        aggregated_paths.append(str(aggregate_path.resolve()))
        table_rows.append(_summary_row(load_json(aggregate_path)))

    _write_csv(table_output_dir / "table_b_constraints.csv", table_rows)
    _write_tex(table_output_dir / "table_b_constraints.tex", table_rows)

    summary = {
        "config_path": str(config_path),
        "shared_thresholds_path": str(shared_thresholds_path.resolve()),
        "shared_thresholds": thresholds,
        "threshold_buffer_paths": threshold_sources,
        "per_run_paths": per_run_paths,
        "aggregated_paths": aggregated_paths,
        "per_run_records": per_run_records,
        "table_b_csv_path": str((table_output_dir / "table_b_constraints.csv").resolve()),
        "table_b_tex_path": str((table_output_dir / "table_b_constraints.tex").resolve()),
    }
    summary_path = output_dir / "table_b_summary.json"
    save_json(summary_path, summary)
    return summary_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate the formal Scenario2 main-table-B artifacts."
    )
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    summary_path = generate_main_table_b(args.config)
    print(summary_path)


if __name__ == "__main__":
    main()
