from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_ROOT = (
    REPO_ROOT
    / "cmorl_cyborg"
    / "outputs"
    / "fair_compare_eval"
    / "reevaluated_tight_feasible_set_summary"
)
DEFAULT_OUTPUT_ROOT = (
    REPO_ROOT
    / "cmorl_cyborg"
    / "outputs"
    / "paper_appendix"
    / "ours_vs_no_constraint_distribution"
)

METHODS = {
    "ours_stage2_fair": {
        "label": "Ours Stage2",
        "color": "#4c78a8",
        "marker": "o",
    },
    "no_constraint_stage2_fair": {
        "label": "No-Constraint Stage2",
        "color": "#e45756",
        "marker": "^",
    },
}
SEEDS = (7, 11, 19)


def _load_seed_payload(method_name: str, seed: int, input_root: Path) -> dict:
    path = input_root / method_name / f"seed_{seed:04d}.json"
    return json.loads(path.read_text())


def _collect_rows(input_root: Path) -> tuple[list[dict], dict[str, float]]:
    rows: list[dict] = []
    thresholds: dict[str, float] | None = None
    for method_name, spec in METHODS.items():
        for seed in SEEDS:
            payload = _load_seed_payload(method_name, seed, input_root)
            if thresholds is None:
                thresholds = {
                    "d_business": float(payload["tight_thresholds"]["d_business"]),
                    "d_cost": float(payload["tight_thresholds"]["d_cost"]),
                }
            for candidate in payload["candidate_rows"]:
                rows.append(
                    {
                        "method_name": method_name,
                        "display_name": spec["label"],
                        "seed": seed,
                        "policy_id": candidate["policy_id"],
                        "security_return": float(candidate["reevaluated_security_return"]),
                        "business_return": float(candidate["reevaluated_business_return"]),
                        "cost_return": float(candidate["reevaluated_cost_return"]),
                        "feasible_rate": float(candidate["reevaluated_feasible_rate"]),
                        "mean_violation": float(candidate["reevaluated_mean_violation"]),
                        "is_feasible": bool(candidate["is_reevaluated_feasible"]),
                        "margin": float(candidate["reevaluated_margin"]),
                    }
                )
    if thresholds is None:
        raise ValueError("No thresholds found.")
    return rows, thresholds


def _write_csv(rows: list[dict], output_path: Path) -> None:
    header = [
        "method_name",
        "display_name",
        "seed",
        "policy_id",
        "security_return",
        "business_return",
        "cost_return",
        "feasible_rate",
        "mean_violation",
        "is_feasible",
        "margin",
    ]
    lines = [",".join(header)]
    for row in rows:
        values = [str(row[key]) for key in header]
        lines.append(",".join(values))
    output_path.write_text("\n".join(lines) + "\n")


def _plot_overlay(rows: list[dict], thresholds: dict[str, float], output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8.5, 6.5))
    for method_name, spec in METHODS.items():
        subset = [row for row in rows if row["method_name"] == method_name]
        infeasible = [row for row in subset if not row["is_feasible"]]
        feasible = [row for row in subset if row["is_feasible"]]
        ax.scatter(
            [row["business_return"] for row in infeasible],
            [row["cost_return"] for row in infeasible],
            s=42,
            alpha=0.45,
            c=spec["color"],
            marker=spec["marker"],
            edgecolors="none",
            label=f"{spec['label']} (infeasible)",
        )
        if feasible:
            ax.scatter(
                [row["business_return"] for row in feasible],
                [row["cost_return"] for row in feasible],
                s=90,
                alpha=0.95,
                c=spec["color"],
                marker=spec["marker"],
                edgecolors="black",
                linewidths=0.8,
                label=f"{spec['label']} (feasible)",
            )
    ax.axvline(thresholds["d_business"], color="black", linestyle="--", linewidth=1.2)
    ax.axhline(thresholds["d_cost"], color="black", linestyle="--", linewidth=1.2)
    ax.text(
        thresholds["d_business"] + 0.5,
        thresholds["d_cost"] + 0.2,
        "Tight feasible region",
        fontsize=10,
        ha="left",
        va="bottom",
    )
    ax.set_xlabel("Reevaluated business return")
    ax.set_ylabel("Reevaluated cost return")
    ax.set_title("Ours vs No-Constraint Stage2 on Tight Business-Cost Plane")
    ax.grid(alpha=0.25)
    ax.legend(frameon=True, fontsize=9, loc="lower right")
    fig.tight_layout()
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def _plot_by_seed(rows: list[dict], thresholds: dict[str, float], output_path: Path) -> None:
    fig, axes = plt.subplots(1, len(SEEDS), figsize=(16.5, 5.4), sharex=True, sharey=True)
    if len(SEEDS) == 1:
        axes = [axes]
    for ax, seed in zip(axes, SEEDS):
        seed_rows = [row for row in rows if row["seed"] == seed]
        for method_name, spec in METHODS.items():
            subset = [row for row in seed_rows if row["method_name"] == method_name]
            infeasible = [row for row in subset if not row["is_feasible"]]
            feasible = [row for row in subset if row["is_feasible"]]
            ax.scatter(
                [row["business_return"] for row in infeasible],
                [row["cost_return"] for row in infeasible],
                s=42,
                alpha=0.45,
                c=spec["color"],
                marker=spec["marker"],
                edgecolors="none",
            )
            if feasible:
                ax.scatter(
                    [row["business_return"] for row in feasible],
                    [row["cost_return"] for row in feasible],
                    s=90,
                    alpha=0.95,
                    c=spec["color"],
                    marker=spec["marker"],
                    edgecolors="black",
                    linewidths=0.8,
                )
        ax.axvline(thresholds["d_business"], color="black", linestyle="--", linewidth=1.1)
        ax.axhline(thresholds["d_cost"], color="black", linestyle="--", linewidth=1.1)
        ax.set_title(f"Seed {seed}")
        ax.grid(alpha=0.25)
    axes[0].set_ylabel("Reevaluated cost return")
    for ax in axes:
        ax.set_xlabel("Reevaluated business return")
    handles = []
    labels = []
    for method_name, spec in METHODS.items():
        handles.append(
            plt.Line2D(
                [0],
                [0],
                marker=spec["marker"],
                color="w",
                markerfacecolor=spec["color"],
                markeredgecolor="black",
                markersize=8,
                linewidth=0,
            )
        )
        labels.append(spec["label"])
    fig.legend(handles, labels, loc="upper center", ncol=2, frameon=True)
    fig.suptitle("Per-seed Tight Business-Cost Candidate Distribution", y=1.03)
    fig.tight_layout()
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Plot reevaluated tight business-cost distributions for ours and no-constraint Stage2."
    )
    parser.add_argument("--input-root", type=Path, default=DEFAULT_INPUT_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    args = parser.parse_args()

    rows, thresholds = _collect_rows(args.input_root.resolve())
    args.output_root.mkdir(parents=True, exist_ok=True)

    csv_path = args.output_root / "ours_vs_no_constraint_reevaluated_points.csv"
    overlay_path = args.output_root / "ours_vs_no_constraint_business_cost_overlay.png"
    by_seed_path = args.output_root / "ours_vs_no_constraint_business_cost_by_seed.png"

    _write_csv(rows, csv_path)
    _plot_overlay(rows, thresholds, overlay_path)
    _plot_by_seed(rows, thresholds, by_seed_path)

    print(csv_path)
    print(overlay_path)
    print(by_seed_path)


if __name__ == "__main__":
    main()
