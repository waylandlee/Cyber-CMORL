from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any

import numpy as np

from cmorl_minicage.utils import ensure_dir, load_json, save_json

from .evaluate_constraints import evaluate_constraints, write_aggregated_constraint_metrics
from .paper_plots import plot_fair_compare_table_b


os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-cmorl-cyborg")

SEEDS = (7, 11, 19)
OURS_METHOD_NAME = "ours_stage2"
ORIGINAL_METHOD_NAME = "original_stage2_table_b"
OURS_DISPLAY_NAME = "AdaCS-DCS (Ours)"
ORIGINAL_DISPLAY_NAME = "Original Stage2"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _resolve_repo_path(raw_path: str | Path) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return (_repo_root() / path).resolve()


def _analysis_root() -> Path:
    return ensure_dir(_resolve_repo_path("cmorl_cyborg/outputs/original_vs_ours_compare"))


def _paper_table_b_root() -> Path:
    return ensure_dir(_analysis_root() / "paper_table_b")


def _tight_candidate_root() -> Path:
    return ensure_dir(_analysis_root() / "tight_candidate")


def _ours_table_b_metrics_path(seed: int) -> Path:
    return _resolve_repo_path(
        f"cmorl_cyborg/outputs/paper_table_b/ours_stage2/seed_{seed:04d}/constraint_metrics.json"
    )


def _ours_buffer_path(seed: int) -> Path:
    table_b_summary = load_json(
        _resolve_repo_path("cmorl_cyborg/outputs/paper_table_b/table_b_summary.json")
    )
    for record in table_b_summary.get("per_run_records", []):
        if str(record.get("method_name")) != "ours_stage2":
            continue
        if int(record.get("seed", -1)) != int(seed):
            continue
        return Path(str(record["input_path"])).resolve()
    raise ValueError(f"Could not find ours_stage2 seed {seed} in paper_table_b summary")


def _original_buffer_path(seed: int) -> Path:
    return _resolve_repo_path(
        f"cmorl_cyborg/outputs/fair_compare_eval_inputs/original_stage2_fair/seed_{seed:04d}/solution_buffer.json"
    )


def _original_table_b_metrics_path(seed: int) -> Path:
    return _paper_table_b_root() / "original_stage2" / f"seed_{seed:04d}" / "constraint_metrics.json"


def _table_b_thresholds_path() -> Path:
    return _resolve_repo_path("cmorl_cyborg/outputs/paper_table_b/shared_thresholds.json")


def _tight_summary_path(method_name: str, seed: int) -> Path:
    return _resolve_repo_path(
        f"cmorl_cyborg/outputs/fair_compare_eval/reevaluated_tight_feasible_set_summary/{method_name}/seed_{seed:04d}.json"
    )


def _import_matplotlib():
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError("matplotlib is required for original-vs-ours comparison plots.") from exc
    return plt


def _maybe_evaluate_original_seed(seed: int, *, refresh: bool, eval_episodes: int) -> Path:
    output_path = _original_table_b_metrics_path(seed)
    if output_path.exists() and not refresh:
        return output_path.resolve()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = evaluate_constraints(
        method_name=ORIGINAL_METHOD_NAME,
        input_kind="buffer",
        input_path=str(_original_buffer_path(seed).resolve()),
        selection_source="pareto",
        selection_policy="objective",
        thresholds_path=str(_table_b_thresholds_path().resolve()),
        eval_episodes=int(eval_episodes),
    )
    save_json(output_path, payload)
    return output_path.resolve()


def _aggregate_table_b(metrics_paths: list[Path], *, method_name: str, output_name: str) -> Path:
    output_path = _paper_table_b_root() / "aggregated" / output_name
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return write_aggregated_constraint_metrics(
        [str(path.resolve()) for path in metrics_paths],
        output_path,
        method_name=method_name,
    ).resolve()


def _method_style(method_name: str) -> dict[str, str]:
    if method_name == OURS_METHOD_NAME:
        return {"label": OURS_DISPLAY_NAME, "color": "#4c78a8", "marker": "o"}
    return {"label": ORIGINAL_DISPLAY_NAME, "color": "#9d755d", "marker": "s"}


def _annotate_seed_points(axis, rows: list[dict[str, Any]]) -> None:
    for row in rows:
        axis.annotate(
            f"{int(row['seed'])}",
            (float(row["x"]), float(row["y"])),
            xytext=(4, 4),
            textcoords="offset points",
            fontsize=8,
            alpha=0.85,
        )


def _plot_selected_policy_pairwise(rows: list[dict[str, Any]], thresholds: dict[str, float]) -> Path:
    plt = _import_matplotlib()
    output_path = _paper_table_b_root() / "original_vs_ours_table_b_selected_pairwise_2d.png"

    panels = [
        ("business_return", "cost_return", "Business Return", "Cost Return"),
        ("security_return", "business_return", "Security Return", "Business Return"),
        ("security_return", "cost_return", "Security Return", "Cost Return"),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(16.5, 5.2))
    for axis, (x_key, y_key, x_label, y_label) in zip(axes, panels):
        for method_name in (OURS_METHOD_NAME, ORIGINAL_METHOD_NAME):
            subset = [row for row in rows if row["method_name"] == method_name]
            style = _method_style(method_name)
            points = [
                {
                    "seed": row["seed"],
                    "x": float(row[x_key]),
                    "y": float(row[y_key]),
                }
                for row in subset
            ]
            axis.scatter(
                [row["x"] for row in points],
                [row["y"] for row in points],
                s=90,
                alpha=0.85,
                c=style["color"],
                marker=style["marker"],
                edgecolors="black",
                linewidths=0.8,
                label=style["label"],
            )
            _annotate_seed_points(axis, points)
            axis.scatter(
                [np.mean([row["x"] for row in points])],
                [np.mean([row["y"] for row in points])],
                s=170,
                c=style["color"],
                marker="X",
                edgecolors="black",
                linewidths=1.0,
            )
        if x_key == "business_return" and y_key == "cost_return":
            axis.axvline(float(thresholds["d_business"]), color="black", linestyle="--", linewidth=1.1)
            axis.axhline(float(thresholds["d_cost"]), color="black", linestyle="--", linewidth=1.1)
        axis.set_xlabel(x_label)
        axis.set_ylabel(y_label)
        axis.grid(alpha=0.25)

    axes[0].set_title("Selected Policy: Business-Cost Plane")
    axes[1].set_title("Selected Policy: Security-Business Plane")
    axes[2].set_title("Selected Policy: Security-Cost Plane")
    handles, labels = axes[0].get_legend_handles_labels()
    unique: dict[str, Any] = {}
    for handle, label in zip(handles, labels):
        unique.setdefault(label, handle)
    fig.legend(
        list(unique.values()),
        list(unique.keys()),
        loc="upper center",
        bbox_to_anchor=(0.5, 1.01),
        ncol=2,
        frameon=True,
    )
    fig.suptitle("Original Stage2 vs AdaCS-DCS under Paper Table B Protocol", y=1.08)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return output_path.resolve()


def _plot_tight_candidate_pairwise(rows: list[dict[str, Any]], thresholds: dict[str, float]) -> Path:
    plt = _import_matplotlib()
    output_path = _tight_candidate_root() / "original_vs_ours_tight_candidate_pairwise_2d.png"

    panels = [
        ("business_return", "cost_return", "Reevaluated Business Return", "Reevaluated Cost Return"),
        ("security_return", "business_return", "Reevaluated Security Return", "Reevaluated Business Return"),
        ("security_return", "cost_return", "Reevaluated Security Return", "Reevaluated Cost Return"),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(16.5, 5.2))
    for axis, (x_key, y_key, x_label, y_label) in zip(axes, panels):
        for method_name in ("ours_stage2_fair", "original_stage2_fair"):
            subset = [row for row in rows if row["method_name"] == method_name]
            style = _method_style(OURS_METHOD_NAME if method_name == "ours_stage2_fair" else ORIGINAL_METHOD_NAME)
            infeasible = [row for row in subset if not row["is_feasible"]]
            feasible = [row for row in subset if row["is_feasible"]]
            axis.scatter(
                [row[x_key] for row in infeasible],
                [row[y_key] for row in infeasible],
                s=28,
                alpha=0.35,
                c=style["color"],
                marker=style["marker"],
                edgecolors="none",
                label=f"{style['label']} (infeasible)",
            )
            if feasible:
                axis.scatter(
                    [row[x_key] for row in feasible],
                    [row[y_key] for row in feasible],
                    s=90,
                    alpha=0.95,
                    c=style["color"],
                    marker=style["marker"],
                    edgecolors="black",
                    linewidths=0.8,
                    label=f"{style['label']} (feasible)",
                )
        if x_key == "business_return" and y_key == "cost_return":
            axis.axvline(float(thresholds["d_business"]), color="black", linestyle="--", linewidth=1.1)
            axis.axhline(float(thresholds["d_cost"]), color="black", linestyle="--", linewidth=1.1)
        axis.set_xlabel(x_label)
        axis.set_ylabel(y_label)
        axis.grid(alpha=0.25)

    axes[0].set_title("Tight Candidate Set: Business-Cost")
    axes[1].set_title("Tight Candidate Set: Security-Business")
    axes[2].set_title("Tight Candidate Set: Security-Cost")
    handles, labels = axes[0].get_legend_handles_labels()
    unique: dict[str, Any] = {}
    for handle, label in zip(handles, labels):
        unique.setdefault(label, handle)
    fig.legend(
        list(unique.values()),
        list(unique.keys()),
        loc="upper center",
        bbox_to_anchor=(0.5, 1.01),
        ncol=4,
        frameon=True,
    )
    fig.suptitle("Original Stage2 vs AdaCS-DCS: Reevaluated Tight Candidate Set", y=1.08)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return output_path.resolve()


def _collect_selected_rows(
    *,
    ours_metrics_paths: list[Path],
    original_metrics_paths: list[Path],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for seed, path in zip(SEEDS, ours_metrics_paths):
        payload = load_json(path)
        rows.append(
            {
                "method_name": OURS_METHOD_NAME,
                "display_name": OURS_DISPLAY_NAME,
                "seed": seed,
                "selected_policy_id": payload.get("selected_policy_id"),
                "security_return": float(payload["security_return"]),
                "business_return": float(payload["business_return"]),
                "cost_return": float(payload["cost_return"]),
                "feasible_rate": float(payload["feasible_rate"]),
                "mean_violation": float(payload["mean_violation"]),
            }
        )
    for seed, path in zip(SEEDS, original_metrics_paths):
        payload = load_json(path)
        rows.append(
            {
                "method_name": ORIGINAL_METHOD_NAME,
                "display_name": ORIGINAL_DISPLAY_NAME,
                "seed": seed,
                "selected_policy_id": payload.get("selected_policy_id"),
                "security_return": float(payload["security_return"]),
                "business_return": float(payload["business_return"]),
                "cost_return": float(payload["cost_return"]),
                "feasible_rate": float(payload["feasible_rate"]),
                "mean_violation": float(payload["mean_violation"]),
            }
        )
    return rows


def _collect_tight_candidate_rows() -> tuple[list[dict[str, Any]], dict[str, float]]:
    rows: list[dict[str, Any]] = []
    thresholds: dict[str, float] | None = None
    for method_name in ("ours_stage2_fair", "original_stage2_fair"):
        for seed in SEEDS:
            payload = load_json(_tight_summary_path(method_name, seed))
            if thresholds is None:
                thresholds = {
                    "d_business": float(payload["tight_thresholds"]["d_business"]),
                    "d_cost": float(payload["tight_thresholds"]["d_cost"]),
                }
            for candidate in payload.get("candidate_rows", []):
                rows.append(
                    {
                        "method_name": method_name,
                        "seed": seed,
                        "policy_id": candidate["policy_id"],
                        "security_return": float(candidate["reevaluated_security_return"]),
                        "business_return": float(candidate["reevaluated_business_return"]),
                        "cost_return": float(candidate["reevaluated_cost_return"]),
                        "is_feasible": bool(candidate["is_reevaluated_feasible"]),
                    }
                )
    if thresholds is None:
        raise ValueError("Could not load tight thresholds.")
    return rows, thresholds


def _write_summary(
    *,
    ours_agg_path: Path,
    original_agg_path: Path,
    selected_rows: list[dict[str, Any]],
    selected_plot_path: Path,
    tight_plot_path: Path,
    table_b_bar_path: Path,
) -> Path:
    ours_payload = load_json(ours_agg_path)
    original_payload = load_json(original_agg_path)
    summary_path = _analysis_root() / "original_vs_ours_summary.json"
    summary = {
        "seeds": list(SEEDS),
        "paper_table_b_thresholds_path": str(_table_b_thresholds_path().resolve()),
        "ours_aggregated_metrics_path": str(ours_agg_path),
        "original_aggregated_metrics_path": str(original_agg_path),
        "table_b_bar_path": str(table_b_bar_path),
        "selected_policy_pairwise_2d_path": str(selected_plot_path),
        "tight_candidate_pairwise_2d_path": str(tight_plot_path),
        "selected_policy_rows": selected_rows,
        "table_b_delta_original_minus_ours": {
            key: float(original_payload.get(key, 0.0)) - float(ours_payload.get(key, 0.0))
            for key in (
                "security_return",
                "business_return",
                "cost_return",
                "feasible_rate",
                "mean_violation",
                "final_critical_compromised_hosts",
                "critical_impact_count",
                "high_disruption_action_rate",
            )
        },
    }
    save_json(summary_path, summary)
    return summary_path.resolve()


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Compare Original Stage2 (crowding + fixed beta) against AdaCS-DCS, "
            "generate 2D figures, and refresh a Table-B-style deployment comparison."
        )
    )
    parser.add_argument("--refresh-original-table-b", action="store_true")
    parser.add_argument("--eval-episodes", type=int, default=5)
    args = parser.parse_args()

    original_metrics_paths = [
        _maybe_evaluate_original_seed(
            seed,
            refresh=bool(args.refresh_original_table_b),
            eval_episodes=int(args.eval_episodes),
        )
        for seed in SEEDS
    ]
    ours_metrics_paths = [_ours_table_b_metrics_path(seed) for seed in SEEDS]

    original_agg_path = _aggregate_table_b(
        original_metrics_paths,
        method_name=ORIGINAL_METHOD_NAME,
        output_name="original_stage2_3seed.json",
    )
    ours_agg_path = _aggregate_table_b(
        ours_metrics_paths,
        method_name=OURS_METHOD_NAME,
        output_name="ours_stage2_3seed.json",
    )

    table_b_bar_path = _paper_table_b_root() / "original_vs_ours_table_b_bar_3seed.png"
    plot_fair_compare_table_b(
        aggregated_paths=[str(original_agg_path), str(ours_agg_path)],
        output_path=table_b_bar_path,
        title="Deployment Comparison under Paper Table B Protocol: AdaCS-DCS vs Original Stage2",
        label_map={
            OURS_METHOD_NAME: OURS_DISPLAY_NAME,
            ORIGINAL_METHOD_NAME: ORIGINAL_DISPLAY_NAME,
        },
    )

    selected_rows = _collect_selected_rows(
        ours_metrics_paths=ours_metrics_paths,
        original_metrics_paths=original_metrics_paths,
    )
    selected_plot_path = _plot_selected_policy_pairwise(
        selected_rows,
        thresholds=load_json(_table_b_thresholds_path()),
    )

    tight_rows, tight_thresholds = _collect_tight_candidate_rows()
    tight_plot_path = _plot_tight_candidate_pairwise(tight_rows, tight_thresholds)

    summary_path = _write_summary(
        ours_agg_path=ours_agg_path,
        original_agg_path=original_agg_path,
        selected_rows=selected_rows,
        selected_plot_path=selected_plot_path,
        tight_plot_path=tight_plot_path,
        table_b_bar_path=table_b_bar_path.resolve(),
    )

    print(original_agg_path)
    print(ours_agg_path)
    print(table_b_bar_path.resolve())
    print(selected_plot_path)
    print(tight_plot_path)
    print(summary_path)


if __name__ == "__main__":
    main()
