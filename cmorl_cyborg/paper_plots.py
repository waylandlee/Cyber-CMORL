from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from cmorl_minicage.utils import ensure_dir, load_json

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-cmorl-cyborg")

TABLE_A_PANELS = [
    ("hypervolume", "Hypervolume", "#4c78a8", "max"),
    ("expected_utility", "Expected Utility", "#54a24b", "max"),
    ("sparsity", "Sparsity", "#f58518", "min"),
    ("num_pareto_records", "Pareto Count", "#e45756", "max"),
    ("coverage_ratio", "Coverage Ratio", "#72b7b2", "max"),
    ("unique_assigned_policies", "Assigned Policy Variety", "#b279a2", "max"),
]

TABLE_B_PANELS = [
    ("security_return", "Security Return", "#4c78a8", "max"),
    ("business_return", "Business Return", "#54a24b", "max"),
    ("cost_return", "Cost Return", "#9d755d", "max"),
    ("feasible_rate", "Feasible Rate", "#54a24b", "max"),
    ("mean_violation", "Mean Violation", "#e45756", "min"),
    (
        "final_critical_compromised_hosts",
        "Final Critical Compromised",
        "#f58518",
        "min",
    ),
    ("critical_impact_count", "Critical Impact Count", "#72b7b2", "min"),
    ("high_disruption_action_rate", "High Disruption Rate", "#b279a2", "min"),
]


def _import_matplotlib():
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError("matplotlib is required for paper plots.") from exc
    return plt


def _method_label(raw_label: str, label_map: dict[str, str] | None = None) -> str:
    mapped = raw_label
    if label_map is not None:
        mapped = label_map.get(raw_label, raw_label)
    return _display_label(mapped)


def _display_label(label: str) -> str:
    return (
        label.replace("Preference-Conditioned PPO", "Pref-Cond PPO")
        .replace("Ours Stage2", "Ours")
        .replace("_", "\n")
    )


def _best_index(values: Sequence[float], direction: str) -> int:
    if direction == "min":
        return int(np.argmin(values))
    return int(np.argmax(values))


def _annotation_text(mean: float, std: float) -> str:
    if abs(mean) >= 1000:
        return f"{mean:.1f}\n±{std:.1f}"
    if abs(mean) >= 100:
        return f"{mean:.2f}\n±{std:.2f}"
    return f"{mean:.3f}\n±{std:.3f}"


def _annotate_bars(axis, bars, means: Sequence[float], stds: Sequence[float]) -> None:
    ymin, ymax = axis.get_ylim()
    span = max(ymax - ymin, 1e-6)
    offset = span * 0.025
    for bar, mean, std in zip(bars, means, stds):
        y = bar.get_height()
        va = "bottom"
        text_y = y + offset
        if y < 0:
            va = "top"
            text_y = y - offset
        axis.text(
            bar.get_x() + bar.get_width() / 2.0,
            text_y,
            _annotation_text(float(mean), float(std)),
            ha="center",
            va=va,
            fontsize=7,
        )


def _method_summary_rows(compare_summary: dict[str, Any]) -> list[dict[str, Any]]:
    return list(compare_summary.get("method_summary", []))


def plot_main_table_a(
    compare_summary_path: str | Path,
    output_path: str | Path | None = None,
    title: str = "Formal CybORG Main Table A",
) -> Path:
    plt = _import_matplotlib()
    compare_summary = load_json(compare_summary_path)
    rows = _method_summary_rows(compare_summary)
    if not rows:
        raise ValueError("No method_summary rows found for main table A")

    labels = [_display_label(str(row.get("display_group", row["method_name"]))) for row in rows]
    x = np.arange(len(labels))

    fig, axes = plt.subplots(2, 3, figsize=(18, 9.5))
    fig.suptitle(title, fontsize=16, y=0.98)

    for axis, (metric_key, title, color, direction) in zip(axes.flatten(), TABLE_A_PANELS):
        means = [float(row.get(metric_key, {}).get("mean", 0.0)) for row in rows]
        stds = [float(row.get(metric_key, {}).get("std", 0.0)) for row in rows]
        bars = axis.bar(
            x,
            means,
            yerr=stds,
            color=color,
            alpha=0.92,
            error_kw={"elinewidth": 1.0, "capsize": 4},
        )
        best_idx = _best_index(means, direction)
        bars[best_idx].set_edgecolor("black")
        bars[best_idx].set_linewidth(1.4)
        axis.set_title(title)
        axis.set_xticks(x)
        axis.set_xticklabels(labels, rotation=0, fontsize=9)
        axis.grid(True, axis="y", alpha=0.22)
        _annotate_bars(axis, bars, means, stds)

    fig.tight_layout(rect=(0, 0, 1, 0.96))
    if output_path is None:
        output_path = Path(compare_summary_path).resolve().parent / "main_table_a_metrics.png"
    output_path = Path(output_path)
    ensure_dir(output_path.parent)
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output_path


def _load_table_b_rows(
    *,
    table_b_summary_path: str | Path | None = None,
    aggregated_paths: Sequence[str | Path] | None = None,
) -> list[dict[str, Any]]:
    if table_b_summary_path is not None:
        table_b_summary = load_json(table_b_summary_path)
        aggregated_paths = table_b_summary.get("aggregated_paths", [])
    if not aggregated_paths:
        raise ValueError("No aggregated_paths were provided for main table B")
    rows = [load_json(path) for path in aggregated_paths]
    return sorted(rows, key=lambda row: str(row.get("method_name", "")))


def plot_main_table_b(
    *,
    table_b_summary_path: str | Path | None = None,
    aggregated_paths: Sequence[str | Path] | None = None,
    output_path: str | Path | None = None,
    title: str = "Formal CybORG Main Table B",
    label_map: dict[str, str] | None = None,
) -> Path:
    plt = _import_matplotlib()
    rows = _load_table_b_rows(
        table_b_summary_path=table_b_summary_path,
        aggregated_paths=aggregated_paths,
    )
    labels = [
        _method_label(str(row.get("method_name", "method")), label_map=label_map)
        for row in rows
    ]
    x = np.arange(len(labels))

    fig, axes = plt.subplots(2, 4, figsize=(24, 9.5))
    fig.suptitle(title, fontsize=16, y=0.98)

    for axis, (metric_key, title, color, direction) in zip(axes.flatten(), TABLE_B_PANELS):
        means = [float(row.get(metric_key, 0.0)) for row in rows]
        stds = [float(row.get(f"{metric_key}_std", 0.0)) for row in rows]
        bars = axis.bar(
            x,
            means,
            yerr=stds,
            color=color,
            alpha=0.92,
            error_kw={"elinewidth": 1.0, "capsize": 4},
        )
        best_idx = _best_index(means, direction)
        bars[best_idx].set_edgecolor("black")
        bars[best_idx].set_linewidth(1.4)
        axis.set_title(title)
        axis.set_xticks(x)
        axis.set_xticklabels(labels, rotation=0, fontsize=9)
        axis.grid(True, axis="y", alpha=0.22)
        _annotate_bars(axis, bars, means, stds)

    for axis in axes.flatten()[len(TABLE_B_PANELS) :]:
        axis.axis("off")

    fig.tight_layout(rect=(0, 0, 1, 0.96))
    if output_path is None:
        if table_b_summary_path is None:
            raise ValueError("output_path is required when table_b_summary_path is not provided")
        output_path = Path(table_b_summary_path).resolve().parent / "main_table_b_bar_extended.png"
    output_path = Path(output_path)
    ensure_dir(output_path.parent)
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_fair_compare_table_b(
    *,
    aggregated_paths: Sequence[str | Path],
    output_path: str | Path | None = None,
    title: str = "Fair Comparison: Constrained vs Unconstrained Stage2",
    label_map: dict[str, str] | None = None,
) -> Path:
    plt = _import_matplotlib()
    rows = _load_table_b_rows(aggregated_paths=aggregated_paths)
    default_label_map = {
        "ours_stage2_fair": "Ours Stage2 Fair",
        "no_constraint_stage2_fair": "No-Constraint Stage2 Fair",
    }
    combined_label_map = dict(default_label_map)
    if label_map is not None:
        combined_label_map.update(label_map)
    labels = [
        _method_label(str(row.get("method_name", "method")), label_map=combined_label_map)
        for row in rows
    ]
    x = np.arange(len(labels))

    fig, axes = plt.subplots(2, 4, figsize=(24, 9.5))
    fig.suptitle(title, fontsize=16, y=0.98)

    for axis, (metric_key, title, color, direction) in zip(axes.flatten(), TABLE_B_PANELS):
        means = [float(row.get(metric_key, 0.0)) for row in rows]
        stds = [float(row.get(f"{metric_key}_std", 0.0)) for row in rows]
        bars = axis.bar(
            x,
            means,
            yerr=stds,
            color=color,
            alpha=0.92,
            error_kw={"elinewidth": 1.0, "capsize": 4},
        )
        best_idx = _best_index(means, direction)
        bars[best_idx].set_edgecolor("black")
        bars[best_idx].set_linewidth(1.4)
        axis.set_title(title)
        axis.set_xticks(x)
        axis.set_xticklabels(labels, rotation=0, fontsize=9)
        axis.grid(True, axis="y", alpha=0.22)
        _annotate_bars(axis, bars, means, stds)

    for axis in axes.flatten()[len(TABLE_B_PANELS) :]:
        axis.axis("off")

    fig.tight_layout(rect=(0, 0, 1, 0.96))
    if output_path is None:
        first_path = Path(aggregated_paths[0]).resolve()
        output_path = first_path.parent / "fair_compare_table_b.png"
    output_path = Path(output_path)
    ensure_dir(output_path.parent)
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_paper_tables(
    *,
    compare_summary_path: str | Path,
    table_b_summary_path: str | Path,
) -> dict[str, str]:
    table_a_path = plot_main_table_a(compare_summary_path)
    table_b_path = plot_main_table_b(table_b_summary_path=table_b_summary_path)
    return {
        "main_table_a_metrics": str(table_a_path.resolve()),
        "main_table_b_bar": str(table_b_path.resolve()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate paper-style Week-2 CybORG plots.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    table_a_parser = subparsers.add_parser("main-table-a")
    table_a_parser.add_argument("--compare-summary", required=True)
    table_a_parser.add_argument("--output-path", default=None)

    table_b_parser = subparsers.add_parser("main-table-b")
    table_b_parser.add_argument("--table-b-summary", required=True)
    table_b_parser.add_argument("--output-path", default=None)

    fair_parser = subparsers.add_parser("fair-compare-table-b")
    fair_parser.add_argument("--aggregated-paths", nargs="+", required=True)
    fair_parser.add_argument("--output-path", default=None)

    all_parser = subparsers.add_parser("all")
    all_parser.add_argument("--compare-summary", required=True)
    all_parser.add_argument("--table-b-summary", required=True)

    args = parser.parse_args()
    if args.command == "main-table-a":
        print(plot_main_table_a(args.compare_summary, args.output_path))
        return
    if args.command == "main-table-b":
        print(plot_main_table_b(table_b_summary_path=args.table_b_summary, output_path=args.output_path))
        return
    if args.command == "fair-compare-table-b":
        print(plot_fair_compare_table_b(aggregated_paths=args.aggregated_paths, output_path=args.output_path))
        return
    outputs = plot_paper_tables(
        compare_summary_path=args.compare_summary,
        table_b_summary_path=args.table_b_summary,
    )
    for _, output_path in outputs.items():
        print(output_path)


if __name__ == "__main__":
    main()
