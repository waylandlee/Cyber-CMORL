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


DISPLAY_NAMES = {
    "ours_stage2_fair": "Ours Stage2",
    "no_constraint_stage2_fair": "No-Constraint Stage2",
    "coverage_combo_fair": "Coverage Combo",
    "coverage_more_parents_fair": "Coverage More Parents",
}

METHOD_ORDER = [
    "ours_stage2_fair",
    "no_constraint_stage2_fair",
    "coverage_combo_fair",
    "coverage_more_parents_fair",
]

COLORS = {
    "ours_stage2_fair": "#4c78a8",
    "no_constraint_stage2_fair": "#e45756",
    "coverage_combo_fair": "#54a24b",
    "coverage_more_parents_fair": "#f58518",
}


def _load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _import_matplotlib():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def _mean_std(values: list[float]) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    if len(values) == 1:
        return float(values[0]), 0.0
    return float(mean(values)), float(pstdev(values))


def _tight_root() -> Path:
    return (
        Path(__file__).resolve().parent
        / "outputs"
        / "fair_compare_eval"
        / "tight"
    )


def _aggregated_root() -> Path:
    return (
        Path(__file__).resolve().parent
        / "outputs"
        / "fair_compare_eval"
        / "aggregated"
    )


def _summary_root() -> Path:
    return (
        Path(__file__).resolve().parent
        / "outputs"
        / "fair_compare_eval"
        / "tight_feasible_set_summary"
    )


def _compute_seed_summary(
    method_name: str,
    constraint_metrics_path: Path,
) -> dict[str, Any]:
    constraint_payload = _load_json(constraint_metrics_path)
    thresholds = dict(constraint_payload.get("thresholds", {}))
    input_path = Path(str(constraint_payload["input_path"])).resolve()
    buffer_payload = _load_json(input_path)
    pareto_front = list(buffer_payload.get("pareto_front", []))
    records = list(buffer_payload.get("records", []))

    business_threshold = float(thresholds["d_business"])
    cost_threshold = float(thresholds["d_cost"])

    feasible_pareto = [
        record
        for record in pareto_front
        if float(record["objective_vector"][1]) >= business_threshold
        and float(record["objective_vector"][2]) >= cost_threshold
    ]
    feasible_records = [
        record
        for record in records
        if float(record["objective_vector"][1]) >= business_threshold
        and float(record["objective_vector"][2]) >= cost_threshold
    ]

    best_feasible_security = (
        max(float(record["objective_vector"][0]) for record in feasible_pareto)
        if feasible_pareto
        else None
    )
    mean_feasible_security = (
        float(mean(float(record["objective_vector"][0]) for record in feasible_pareto))
        if feasible_pareto
        else None
    )

    seed_name = constraint_metrics_path.parent.name
    seed_value = int(seed_name.split("_")[-1])
    return {
        "method_name": method_name,
        "display_name": DISPLAY_NAMES.get(method_name, method_name),
        "seed": seed_value,
        "seed_label": seed_name,
        "constraint_metrics_path": str(constraint_metrics_path.resolve()),
        "input_path": str(input_path),
        "tight_thresholds": thresholds,
        "num_records": len(records),
        "pareto_candidate_count": len(pareto_front),
        "feasible_candidate_count": len(feasible_pareto),
        "feasible_record_count": len(feasible_records),
        "feasible_pareto_ratio": (
            float(len(feasible_pareto) / len(pareto_front)) if pareto_front else 0.0
        ),
        "best_feasible_security_return": best_feasible_security,
        "mean_feasible_security_return": mean_feasible_security,
        "selected_policy_id": constraint_payload.get("selected_policy_id"),
        "selected_security_return": float(constraint_payload.get("security_return", 0.0)),
        "selected_feasible_rate": float(constraint_payload.get("feasible_rate", 0.0)),
        "selected_mean_violation": float(constraint_payload.get("mean_violation", 0.0)),
    }


def _discover_seed_summaries() -> dict[str, list[dict[str, Any]]]:
    summaries: dict[str, list[dict[str, Any]]] = {}
    tight_root = _tight_root()
    for method_name in METHOD_ORDER:
        method_dir = tight_root / method_name
        if not method_dir.exists():
            continue
        method_rows: list[dict[str, Any]] = []
        for metrics_path in sorted(method_dir.glob("seed_*/constraint_metrics.json")):
            method_rows.append(_compute_seed_summary(method_name, metrics_path))
        if method_rows:
            summaries[method_name] = method_rows
    return summaries


def _aggregate_method_rows(
    method_name: str,
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    feasible_counts = [float(row["feasible_candidate_count"]) for row in rows]
    feasible_ratios = [float(row["feasible_pareto_ratio"]) for row in rows]
    best_security_values = [
        float(row["best_feasible_security_return"])
        for row in rows
        if row["best_feasible_security_return"] is not None
    ]

    count_mean, count_std = _mean_std(feasible_counts)
    ratio_mean, ratio_std = _mean_std(feasible_ratios)
    if best_security_values:
        best_sec_mean, best_sec_std = _mean_std(best_security_values)
    else:
        best_sec_mean, best_sec_std = math.nan, math.nan

    return {
        "method_name": method_name,
        "display_name": DISPLAY_NAMES.get(method_name, method_name),
        "num_runs": len(rows),
        "feasible_candidate_count": count_mean,
        "feasible_candidate_count_std": count_std,
        "feasible_pareto_ratio": ratio_mean,
        "feasible_pareto_ratio_std": ratio_std,
        "best_feasible_security_return": best_sec_mean,
        "best_feasible_security_return_std": best_sec_std,
        "num_runs_with_feasible_candidate": sum(
            1 for row in rows if int(row["feasible_candidate_count"]) > 0
        ),
        "source_seed_summaries": [
            str((_summary_root() / method_name / f"seed_{int(row['seed']):04d}.json").resolve())
            for row in rows
        ],
    }


def _write_aggregate_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "method_name",
        "display_name",
        "num_runs",
        "num_runs_with_feasible_candidate",
        "feasible_candidate_count",
        "feasible_candidate_count_std",
        "feasible_pareto_ratio",
        "feasible_pareto_ratio_std",
        "best_feasible_security_return",
        "best_feasible_security_return_std",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fieldnames})


def _plot_tight_feasible_set(
    aggregate_rows: list[dict[str, Any]],
    seed_rows: dict[str, list[dict[str, Any]]],
    output_path: Path,
) -> None:
    plt = _import_matplotlib()

    labels = [row["display_name"] for row in aggregate_rows]
    methods = [row["method_name"] for row in aggregate_rows]
    x = list(range(len(aggregate_rows)))
    colors = [COLORS.get(method, "#4c78a8") for method in methods]

    fig, axes = plt.subplots(1, 3, figsize=(17, 4.6))
    fig.suptitle("Tight Feasible Set Quality", fontsize=15, y=1.02)

    count_means = [row["feasible_candidate_count"] for row in aggregate_rows]
    count_stds = [row["feasible_candidate_count_std"] for row in aggregate_rows]
    axes[0].bar(x, count_means, yerr=count_stds, color=colors, alpha=0.9, capsize=4)
    axes[0].set_title("Feasible Candidate Count")
    axes[0].set_ylabel("Count")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(labels, rotation=12, ha="right")
    axes[0].grid(True, axis="y", alpha=0.22)

    ratio_means = [row["feasible_pareto_ratio"] for row in aggregate_rows]
    ratio_stds = [row["feasible_pareto_ratio_std"] for row in aggregate_rows]
    axes[1].bar(x, ratio_means, yerr=ratio_stds, color=colors, alpha=0.9, capsize=4)
    axes[1].set_title("Feasible Pareto Ratio")
    axes[1].set_ylabel("Ratio")
    axes[1].set_ylim(0.0, max(0.25, max(ratio_means + ratio_stds) * 1.25))
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(labels, rotation=12, ha="right")
    axes[1].grid(True, axis="y", alpha=0.22)

    axes[2].set_title("Best Feasible Security Return")
    axes[2].set_ylabel("Security Return")
    axes[2].set_xticks(x)
    axes[2].set_xticklabels(labels, rotation=12, ha="right")
    axes[2].grid(True, axis="y", alpha=0.22)

    all_valid_security: list[float] = []
    for method_name in methods:
        for row in seed_rows[method_name]:
            value = row["best_feasible_security_return"]
            if value is not None:
                all_valid_security.append(float(value))
    ymin = min(all_valid_security) * 1.08 if all_valid_security else -1.0
    ymax = max(all_valid_security) * 0.92 if all_valid_security else 1.0
    if ymin == ymax:
        ymin -= 1.0
        ymax += 1.0
    axes[2].set_ylim(ymin, ymax)

    for idx, method_name in enumerate(methods):
        valid_rows = [
            row for row in seed_rows[method_name] if row["best_feasible_security_return"] is not None
        ]
        if not valid_rows:
            axes[2].text(
                idx,
                ymax - (0.06 * (ymax - ymin)),
                "none",
                ha="center",
                va="top",
                fontsize=10,
                color="#b22222",
            )
            continue
        jitter_offsets = [-0.08, 0.0, 0.08]
        for j, row in enumerate(valid_rows):
            axes[2].scatter(
                idx + jitter_offsets[j % len(jitter_offsets)],
                float(row["best_feasible_security_return"]),
                color=colors[idx],
                s=48,
                zorder=3,
                edgecolors="black",
                linewidths=0.5,
            )
        mean_value = aggregate_rows[idx]["best_feasible_security_return"]
        axes[2].hlines(
            mean_value,
            idx - 0.18,
            idx + 0.18,
            colors="black",
            linewidth=2.0,
            zorder=4,
        )

    fig.text(
        0.5,
        -0.02,
        "Tight thresholds: business >= -125 and cost >= -22. Counts and ratios are computed over Pareto candidates; security panel shows seed-level best feasible candidates.",
        ha="center",
        fontsize=10,
        color="#444444",
    )
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def export_tight_feasible_set() -> dict[str, str]:
    seed_rows = _discover_seed_summaries()
    if not seed_rows:
        raise ValueError("No tight constraint metrics were found.")

    summary_root = _summary_root()
    aggregate_rows: list[dict[str, Any]] = []
    for method_name in METHOD_ORDER:
        rows = seed_rows.get(method_name, [])
        if not rows:
            continue
        for row in rows:
            seed_path = summary_root / method_name / f"seed_{int(row['seed']):04d}.json"
            _save_json(seed_path, row)
        aggregate_rows.append(_aggregate_method_rows(method_name, rows))

    aggregate_dir = _aggregated_root()
    csv_path = aggregate_dir / "tight_feasible_set_summary.csv"
    json_path = aggregate_dir / "tight_feasible_set_summary.json"
    figure_path = aggregate_dir / "tight_feasible_set_quality.png"

    _write_aggregate_csv(csv_path, aggregate_rows)
    _save_json(
        json_path,
        {
            "methods": aggregate_rows,
            "thresholds": _load_json(
                Path(__file__).resolve().parent
                / "outputs"
                / "fair_compare_eval"
                / "thresholds_tight.json"
            ),
        },
    )
    _plot_tight_feasible_set(aggregate_rows, seed_rows, figure_path)
    return {
        "aggregate_csv": str(csv_path),
        "aggregate_json": str(json_path),
        "figure": str(figure_path),
        "seed_summary_root": str(summary_root),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export tight feasible set summaries and plot Tight Feasible Set Quality."
    )
    parser.parse_args()
    outputs = export_tight_feasible_set()
    for key, value in outputs.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
