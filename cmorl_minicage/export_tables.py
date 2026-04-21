from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from cmorl_minicage.config import load_export_tables_config
from cmorl_minicage.utils import load_json, save_json


def _format_mean_std(entry: dict[str, float]) -> str:
    return f"{entry['mean']:.4f} $\\pm$ {entry['std']:.4f}"


def _write_csv(path: str | Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _write_tex(path: str | Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "\\begin{tabular}{" + "l" * len(columns) + "}",
        "\\hline",
        " & ".join(columns) + " \\\\",
        "\\hline",
    ]
    for row in rows:
        lines.append(" & ".join(str(row[column]) for column in columns) + " \\\\")
    lines.extend(["\\hline", "\\end{tabular}"])
    path.write_text("\n".join(lines), encoding="utf-8")


def _table_a_rows(compare_summary: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for entry in compare_summary.get("method_summary", []):
        semantic = entry.get("semantic_metrics", {})
        rows.append(
            {
                "method_name": entry["method_name"],
                "display_group": entry["display_group"],
                "hypervolume": _format_mean_std(entry["hypervolume"]),
                "expected_utility": _format_mean_std(entry["expected_utility"]),
                "sparsity": _format_mean_std(entry["sparsity"]),
                "num_pareto_records": _format_mean_std(entry["num_pareto_records"]),
                "coverage_ratio": _format_mean_std(entry["coverage_ratio"]),
                "unique_assigned_policies": _format_mean_std(
                    entry["unique_assigned_policies"]
                ),
                "final_critical_compromised_hosts": _format_mean_std(
                    semantic.get(
                        "final_critical_compromised_hosts",
                        {"mean": 0.0, "std": 0.0},
                    )
                ),
                "critical_impact_count": _format_mean_std(
                    semantic.get("critical_impact_count", {"mean": 0.0, "std": 0.0})
                ),
                "high_disruption_action_rate": _format_mean_std(
                    semantic.get(
                        "high_disruption_action_rate",
                        {"mean": 0.0, "std": 0.0},
                    )
                ),
            }
        )
    return rows


def _table_b_rows(paths: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        payload = load_json(path)
        selected_policy_id = payload.get("selected_policy_id", "")
        if not selected_policy_id:
            selected_policy_ids = payload.get("selected_policy_ids", [])
            if isinstance(selected_policy_ids, list):
                unique_ids: list[str] = []
                for raw_policy_id in selected_policy_ids:
                    policy_id = str(raw_policy_id).strip()
                    if policy_id and policy_id not in unique_ids:
                        unique_ids.append(policy_id)
                selected_policy_id = "; ".join(unique_ids)
        rows.append(
            {
                "method_name": payload.get("method_name", Path(path).stem),
                "selected_policy_id": selected_policy_id,
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
        )
    return rows


def _appendix_rows(paths: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        payload = load_json(path)
        metrics = payload.get("metrics", payload)
        assignment_summary = payload.get("assignment_summary", {})
        rows.append(
            {
                "source_path": path,
                "hypervolume": float(metrics.get("hypervolume", 0.0)),
                "expected_utility": float(metrics.get("expected_utility", 0.0)),
                "sparsity": float(metrics.get("sparsity", 0.0)),
                "num_pareto_records": float(metrics.get("num_pareto_records", 0.0)),
                "coverage_ratio": float(assignment_summary.get("coverage_ratio", 0.0)),
                "unique_assigned_policies": float(
                    assignment_summary.get("unique_assigned_policies", 0.0)
                ),
            }
        )
    return rows


def export_tables(config_path: str | Path) -> Path:
    config = load_export_tables_config(config_path)
    if not config.compare_summary_path:
        raise ValueError("compare_summary_path must be provided")
    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    compare_summary = load_json(config.compare_summary_path)
    table_a_rows = _table_a_rows(compare_summary)
    table_a_columns = list(table_a_rows[0].keys()) if table_a_rows else ["method_name"]
    _write_csv(output_dir / "table_a_metrics.csv", table_a_columns, table_a_rows)
    _write_tex(output_dir / "table_a_metrics.tex", table_a_columns, table_a_rows)

    table_b_rows = _table_b_rows(config.constraint_metrics_paths)
    table_b_columns = list(table_b_rows[0].keys()) if table_b_rows else ["method_name"]
    _write_csv(output_dir / "table_b_constraints.csv", table_b_columns, table_b_rows)
    _write_tex(output_dir / "table_b_constraints.tex", table_b_columns, table_b_rows)

    appendix_rows = _appendix_rows(config.appendix_metrics_paths)
    appendix_columns = list(appendix_rows[0].keys()) if appendix_rows else ["source_path"]
    _write_csv(output_dir / "appendix_ablations.csv", appendix_columns, appendix_rows)

    summary = {
        "compare_summary_path": config.compare_summary_path,
        "constraint_metrics_paths": list(config.constraint_metrics_paths),
        "appendix_metrics_paths": list(config.appendix_metrics_paths),
        "table_a_row_count": len(table_a_rows),
        "table_b_row_count": len(table_b_rows),
        "appendix_row_count": len(appendix_rows),
    }
    summary_path = output_dir / "export_summary.json"
    save_json(summary_path, summary)
    return summary_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Export paper tables from summary artifacts.")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    summary_path = export_tables(args.config)
    print(summary_path)


if __name__ == "__main__":
    main()
