from __future__ import annotations

import argparse
import csv
import json
import math
import os
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-cmorl-cyborg")


METHOD_ORDER = [
    "ours_stage2",
    "lagrangian_ppo",
    "weighted_sum",
    "stage1_only",
    "no_constraint_stage2",
    "single_objective",
]

DISPLAY_NAMES = {
    "ours_stage2": "Ours Stage2",
    "lagrangian_ppo": "Lagrangian PPO",
    "weighted_sum": "Weighted-Sum",
    "stage1_only": "Stage1 Only",
    "no_constraint_stage2": "No-Constraint Stage2",
    "single_objective": "Single-Objective",
}


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _save_json(path: str | Path, payload: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _mean_std(values: list[float]) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    if len(values) == 1:
        return float(values[0]), 0.0
    return float(mean(values)), float(pstdev(values))


def _format_mean_std(mean_value: float, std_value: float) -> str:
    return f"{mean_value:.4f} $\\pm$ {std_value:.4f}"


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _write_tex(path: Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
    def tex_escape(value: Any, *, preserve_math: bool = False) -> str:
        text = str(value)
        if preserve_math:
            return text.replace("_", "\\_")
        return text.replace("\\", "\\textbackslash{}").replace("_", "\\_")

    path.parent.mkdir(parents=True, exist_ok=True)
    align = "l" + "c" * (len(columns) - 1)
    lines = [
        "\\begin{tabular}{" + align + "}",
        "\\hline",
        " & ".join(tex_escape(column) for column in columns) + " \\\\",
        "\\hline",
    ]
    for row in rows:
        lines.append(
            " & ".join(tex_escape(row[column], preserve_math=True) for column in columns) + " \\\\"
        )
    lines.extend(["\\hline", "\\end{tabular}"])
    path.write_text("\n".join(lines), encoding="utf-8")


def _import_matplotlib():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def _plot_semantics(summary_rows: list[dict[str, Any]], output_path: Path) -> None:
    plt = _import_matplotlib()
    fig, axes = plt.subplots(2, 2, figsize=(15, 8))
    fig.suptitle("Business/Cost Operational Semantics", fontsize=15, y=0.98)

    metric_specs = [
        ("avg_intervention_count", "Avg Intervention Count", "#4c78a8"),
        ("expensive_action_ratio", "Expensive Action Ratio", "#e45756"),
        ("service_recovery_actions", "Service Recovery Actions", "#54a24b"),
        ("critical_impact_count", "Critical Impact Count", "#f58518"),
    ]
    labels = [row["display_name"] for row in summary_rows]
    x = list(range(len(summary_rows)))

    for axis, (metric_key, title, color) in zip(axes.flatten(), metric_specs):
        means = [float(row["metrics"][metric_key]["mean"]) for row in summary_rows]
        stds = [float(row["metrics"][metric_key]["std"]) for row in summary_rows]
        axis.bar(x, means, yerr=stds, color=color, alpha=0.9, capsize=4)
        axis.set_title(title)
        axis.set_xticks(x)
        axis.set_xticklabels(labels, rotation=15, ha="right")
        axis.grid(True, axis="y", alpha=0.22)

    fig.tight_layout(rect=(0, 0, 1, 0.95))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def _method_rows(aggregated_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    aggregated = _load_json(aggregated_path)
    seed_rows = [_load_json(path) for path in aggregated.get("source_metrics_paths", [])]
    return aggregated, seed_rows


def export_business_cost_semantics(
    aggregated_dir: str | Path | None = None,
) -> dict[str, str]:
    if aggregated_dir is None:
        aggregated_dir = (
            Path(__file__).resolve().parent / "outputs" / "paper_table_b" / "aggregated"
        )
    aggregated_dir = Path(aggregated_dir).resolve()
    output_dir = (
        Path(__file__).resolve().parent / "outputs" / "paper_appendix" / "business_cost_semantics"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_rows: list[dict[str, Any]] = []
    csv_rows: list[dict[str, Any]] = []

    for method_name in METHOD_ORDER:
        aggregated_path = aggregated_dir / f"{method_name}.json"
        if not aggregated_path.exists():
            continue
        aggregated, seed_rows = _method_rows(aggregated_path)
        intervention_values = [
            float(seed.get("analyse_count", 0.0))
            + float(seed.get("remove_count", 0.0))
            + float(seed.get("restore_count", 0.0))
            for seed in seed_rows
        ]
        intervention_mean, intervention_std = _mean_std(intervention_values)
        expensive_mean = float(aggregated.get("high_disruption_action_rate", 0.0))
        expensive_std = float(aggregated.get("high_disruption_action_rate_std", 0.0))
        recovery_mean = float(aggregated.get("restore_count", 0.0))
        recovery_std = float(aggregated.get("restore_count_std", 0.0))
        impact_mean = float(aggregated.get("critical_impact_count", 0.0))
        impact_std = float(aggregated.get("critical_impact_count_std", 0.0))
        recovered_mean = float(aggregated.get("recovered_hosts", 0.0))
        recovered_std = float(aggregated.get("recovered_hosts_std", 0.0))

        summary_rows.append(
            {
                "method_name": method_name,
                "display_name": DISPLAY_NAMES.get(method_name, method_name),
                "num_runs": int(aggregated.get("num_runs", len(seed_rows))),
                "metrics": {
                    "avg_intervention_count": {
                        "mean": intervention_mean,
                        "std": intervention_std,
                    },
                    "expensive_action_ratio": {
                        "mean": expensive_mean,
                        "std": expensive_std,
                    },
                    "service_recovery_actions": {
                        "mean": recovery_mean,
                        "std": recovery_std,
                    },
                    "critical_impact_count": {
                        "mean": impact_mean,
                        "std": impact_std,
                    },
                    "recovered_hosts": {
                        "mean": recovered_mean,
                        "std": recovered_std,
                    },
                },
                "source_aggregated_path": str(aggregated_path),
            }
        )
        csv_rows.append(
            {
                "method_name": method_name,
                "display_name": DISPLAY_NAMES.get(method_name, method_name),
                "avg_intervention_count": _format_mean_std(intervention_mean, intervention_std),
                "expensive_action_ratio": _format_mean_std(expensive_mean, expensive_std),
                "service_recovery_actions": _format_mean_std(recovery_mean, recovery_std),
                "critical_impact_count": _format_mean_std(impact_mean, impact_std),
                "recovered_hosts": _format_mean_std(recovered_mean, recovered_std),
            }
        )

    csv_path = output_dir / "business_cost_semantics.csv"
    tex_path = output_dir / "business_cost_semantics.tex"
    json_path = output_dir / "business_cost_semantics.json"
    figure_path = output_dir / "business_cost_semantics.png"

    columns = [
        "display_name",
        "avg_intervention_count",
        "expensive_action_ratio",
        "service_recovery_actions",
        "critical_impact_count",
        "recovered_hosts",
    ]
    _write_csv(csv_path, ["method_name", *columns], csv_rows)
    _write_tex(tex_path, columns, csv_rows)
    _save_json(
        json_path,
        {
            "table_name": "Business and Cost Semantics",
            "rows": summary_rows,
        },
    )
    _plot_semantics(summary_rows, figure_path)

    return {
        "csv": str(csv_path),
        "tex": str(tex_path),
        "json": str(json_path),
        "figure": str(figure_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Export business/cost semantic summaries.")
    parser.add_argument("--aggregated-dir", default=None)
    args = parser.parse_args()
    outputs = export_business_cost_semantics(args.aggregated_dir)
    print(outputs)


if __name__ == "__main__":
    main()
