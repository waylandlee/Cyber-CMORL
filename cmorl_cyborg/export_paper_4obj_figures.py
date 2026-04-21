from __future__ import annotations

import json
import math
import os
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(REPO_ROOT / ".mplconfig"))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


OUTPUT_ROOT = REPO_ROOT / "paper" / "images"
PAPER_4OBJ_ROOT = REPO_ROOT / "cmorl_cyborg" / "outputs" / "paper_4obj"
APPENDIX_ROOT = (
    REPO_ROOT
    / "cmorl_cyborg"
    / "outputs"
    / "paper_appendix"
    / "critical_safe_v2_4_4obj_analysis"
    / "pilot"
)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _slug_to_display(method_name: str) -> str:
    mapping = {
        "ours_stage2_v2_4": "Constraint-Aware Stage-2",
        "stage1_only_4obj": "Stage-1 Policy Archive",
        "weighted_sum_4obj": "Weighted-Sum",
        "no_constraint_stage2_4obj": "Unconstrained Stage-2",
    }
    return mapping.get(method_name, method_name)


def _ensure_output_dir() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)


def _save_figure(fig: plt.Figure, filename: str) -> None:
    out_path = OUTPUT_ROOT / filename
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def build_semantic_risk_summary() -> None:
    aggregate = _load_json(
        PAPER_4OBJ_ROOT / "semantic_risk" / "semantic_risk_aggregate.json"
    )
    selected = aggregate["selected"]
    baseline = aggregate["baseline"]

    colors = {"Baseline": "#9b2226", "V2.4": "#0a9396"}
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.8))

    rate_metrics = [
        ("Ever\ncritical breach", "ever_critical_breach_rate"),
        ("Persistent\ncritical breach", "persistent_critical_breach_rate"),
        ("High-conf.\nruns", "high_confidence_env_run_rate"),
        ("Q2", "Q2_user_action_during_critical_breach"),
        ("Q4", "Q4_user_focus_after_enterprise_foothold"),
        ("Q5", "Q5_repeated_low_value_decoy_loop"),
    ]
    x = np.arange(len(rate_metrics))
    width = 0.38
    axes[0].bar(
        x - width / 2,
        [baseline[k] for _, k in rate_metrics],
        width=width,
        color=colors["Baseline"],
        label="Baseline",
    )
    axes[0].bar(
        x + width / 2,
        [selected[k] for _, k in rate_metrics],
        width=width,
        color=colors["V2.4"],
        label="V2.4",
    )
    axes[0].set_xticks(x)
    axes[0].set_xticklabels([label for label, _ in rate_metrics], fontsize=9)
    axes[0].set_ylim(0, 1.05)
    axes[0].set_ylabel("Rate")
    axes[0].set_title("Semantic Risk Rates")
    axes[0].grid(axis="y", alpha=0.25)
    axes[0].legend(frameon=False, loc="upper right")

    tier_labels = [
        "Tier 0\nSafe",
        "Tier 1\nNear-Miss",
        "Tier 2\nTransient",
        "Tier 3\nPersistent",
    ]
    tier_keys = [
        "Tier 0 Safe",
        "Tier 1 Near-Miss",
        "Tier 2 Transient Critical Breach",
        "Tier 3 Persistent Critical Breach",
    ]
    tier_x = np.arange(2)
    baseline_bottom = 0.0
    selected_bottom = 0.0
    tier_colors = ["#94d2bd", "#e9d8a6", "#ee9b00", "#bb3e03"]
    for label, key, color in zip(tier_labels, tier_keys, tier_colors):
        axes[1].bar(
            tier_x[0],
            baseline[key],
            bottom=baseline_bottom,
            color=color,
            width=0.5,
        )
        axes[1].bar(
            tier_x[1],
            selected[key],
            bottom=selected_bottom,
            color=color,
            width=0.5,
            label=label,
        )
        baseline_bottom += baseline[key]
        selected_bottom += selected[key]
    axes[1].set_xticks(tier_x)
    axes[1].set_xticklabels(["Baseline", "V2.4"])
    axes[1].set_ylim(0, 1.05)
    axes[1].set_ylabel("Fraction of env-runs")
    axes[1].set_title("Modeled Risk Tiers")
    axes[1].legend(frameon=False, fontsize=8, loc="upper right")

    behavior_labels = [
        "Restore\nshare",
        "Decoy\nshare",
        "Compromised-target\nfocus",
    ]
    behavior_keys = [
        "precritical_action_family_step_rates.restore",
        "precritical_action_family_step_rates.decoy",
        "precritical_compromised_target_focus_step_rate",
    ]
    bx = np.arange(len(behavior_labels))
    axes[2].bar(
        bx - width / 2,
        [baseline[k] for k in behavior_keys],
        width=width,
        color=colors["Baseline"],
        label="Baseline",
    )
    axes[2].bar(
        bx + width / 2,
        [selected[k] for k in behavior_keys],
        width=width,
        color=colors["V2.4"],
        label="V2.4",
    )
    axes[2].set_xticks(bx)
    axes[2].set_xticklabels(behavior_labels, fontsize=9)
    axes[2].set_ylim(0, 1.05)
    axes[2].set_ylabel("Rate")
    axes[2].set_title("Pre-Critical Response Structure")
    axes[2].grid(axis="y", alpha=0.25)

    fig.suptitle(
        "Semantic Safety of Selected Policies: Baseline vs. Four-Objective V2.4",
        fontsize=14,
    )
    _save_figure(fig, "semantic_risk_4obj_summary.png")


def _normalize(values: list[float]) -> list[float]:
    vmin, vmax = min(values), max(values)
    if math.isclose(vmin, vmax):
        return [0.5 for _ in values]
    return [(v - vmin) / (vmax - vmin) for v in values]


def build_candidate_set_parallel_coordinates() -> None:
    summary = _load_json(PAPER_4OBJ_ROOT / "table_a" / "table_a_summary.json")
    method_summary = summary["method_summary"]
    methods = [
        "ours_stage2_v2_4",
        "stage1_only_4obj",
        "weighted_sum_4obj",
    ]
    selected_rows = {
        row["method_name"]: row for row in method_summary if row["method_name"] in methods
    }

    metrics = [
        ("Hypervolume", lambda r: r["hypervolume"]["mean"]),
        ("Expected Utility", lambda r: r["expected_utility"]["mean"]),
        ("Coverage Ratio", lambda r: r["coverage_ratio"]["mean"]),
        ("Unique Assigned\nPolicies", lambda r: r["unique_assigned_policies"]["mean"]),
    ]

    metric_values = {
        label: [extractor(selected_rows[m]) for m in methods] for label, extractor in metrics
    }
    normalized = {label: _normalize(vals) for label, vals in metric_values.items()}

    fig, ax = plt.subplots(figsize=(10, 5.6))
    x = np.arange(len(metrics))
    colors = {
        "ours_stage2_v2_4": "#0a9396",
        "stage1_only_4obj": "#ee9b00",
        "weighted_sum_4obj": "#9b2226",
    }

    for idx, method in enumerate(methods):
        y = [normalized[label][idx] for label, _ in metrics]
        ax.plot(
            x,
            y,
            marker="o",
            linewidth=2.5,
            markersize=7,
            color=colors[method],
            label=_slug_to_display(method).replace("\n", " "),
        )

    ax.set_xticks(x)
    ax.set_xticklabels([label for label, _ in metrics], fontsize=10)
    ax.set_yticks(np.linspace(0, 1, 6))
    ax.set_yticklabels([f"{v:.1f}" for v in np.linspace(0, 1, 6)])
    ax.set_ylabel("Normalized across methods")
    ax.set_title("4D Candidate-Set Quality Comparison")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False, loc="lower left")

    for metric_idx, (label, _) in enumerate(metrics):
        values = metric_values[label]
        raw_text = "\n".join(
            f"{_slug_to_display(method).splitlines()[0]}: {values[i]:.3g}"
            for i, method in enumerate(methods)
        )
        ax.text(
            metric_idx,
            -0.18,
            raw_text,
            ha="center",
            va="top",
            fontsize=8,
            transform=ax.get_xaxis_transform(),
        )

    _save_figure(fig, "candidate_set_4obj_parallel_coordinates.png")


def _load_candidate_points() -> dict[str, list[dict]]:
    summary = _load_json(PAPER_4OBJ_ROOT / "table_a" / "table_a_summary.json")
    points_by_method: dict[str, list[dict]] = {}
    for method in summary["method_summary"]:
        points: list[dict] = []
        for run in method["runs"]:
            buffer_data = _load_json(Path(run["artifact_path"]))
            for record in buffer_data["pareto_front"]:
                obj = record["objective_vector"]
                points.append(
                    {
                        "seed": run["seed"],
                        "policy_id": record["policy_id"],
                        "security": obj[0],
                        "business": obj[1],
                        "cost": obj[2],
                        "critical_asset_safety": obj[3],
                    }
                )
        points_by_method[method["method_name"]] = points
    return points_by_method


def build_candidate_set_3d_projection() -> None:
    points_by_method = _load_candidate_points()
    methods = ["ours_stage2_v2_4", "stage1_only_4obj", "weighted_sum_4obj"]
    colors = {
        "ours_stage2_v2_4": "#0a9396",
        "stage1_only_4obj": "#ee9b00",
        "weighted_sum_4obj": "#9b2226",
    }
    markers = {
        "ours_stage2_v2_4": "o",
        "stage1_only_4obj": "^",
        "weighted_sum_4obj": "s",
    }

    all_safety = [
        point["critical_asset_safety"]
        for method in methods
        for point in points_by_method[method]
    ]
    safety_min = min(all_safety)
    safety_max = max(all_safety)
    norm = plt.Normalize(safety_min, safety_max)
    cmap = plt.cm.viridis

    fig = plt.figure(figsize=(16.6, 5.1))
    axes = [fig.add_subplot(1, 3, i + 1, projection="3d") for i in range(3)]
    scatter_ref = None

    for ax, method in zip(axes, methods):
        points = points_by_method[method]
        xs = [p["security"] for p in points]
        ys = [p["business"] for p in points]
        zs = [p["cost"] for p in points]
        cs = [p["critical_asset_safety"] for p in points]
        scatter_ref = ax.scatter(
            xs,
            ys,
            zs,
            c=cs,
            cmap=cmap,
            norm=norm,
            marker=markers[method],
            s=44,
            edgecolors=colors[method],
            linewidths=0.9,
            alpha=0.9,
        )
        ax.set_xlabel("Security\nEffectiveness", labelpad=8)
        ax.set_ylabel("Business\nContinuity", labelpad=8)
        ax.set_zlabel("")
        ax.view_init(elev=22, azim=-53)
        ax.grid(True, alpha=0.22)
        ax.text2D(
            0.5,
            -0.12,
            _slug_to_display(method),
            transform=ax.transAxes,
            ha="center",
            va="top",
            fontsize=10,
        )
        ax.text2D(
            1.10,
            0.50,
            "Defense Cost",
            transform=ax.transAxes,
            rotation=90,
            ha="left",
            va="center",
            fontsize=10,
        )

    fig.subplots_adjust(left=0.03, right=0.85, bottom=0.12, top=0.98, wspace=0.24)
    cax = fig.add_axes([0.89, 0.20, 0.016, 0.62])
    cbar = fig.colorbar(scatter_ref, cax=cax)
    cbar.set_label("Critical-Asset Safety", rotation=90, fontsize=11, labelpad=10)
    cbar.ax.tick_params(labelsize=9)

    _save_figure(fig, "candidate_set_4obj_3d_projection.png")


def build_candidate_set_pairwise_matrix() -> None:
    points_by_method = _load_candidate_points()
    methods = ["ours_stage2_v2_4", "stage1_only_4obj", "weighted_sum_4obj"]
    colors = {
        "ours_stage2_v2_4": "#0a9396",
        "stage1_only_4obj": "#ee9b00",
        "weighted_sum_4obj": "#9b2226",
    }
    markers = {
        "ours_stage2_v2_4": "o",
        "stage1_only_4obj": "^",
        "weighted_sum_4obj": "s",
    }

    dims = [
        ("security", "Security Effectiveness"),
        ("business", "Business Continuity"),
        ("cost", "Defense Cost"),
        ("critical_asset_safety", "Critical-Asset Safety"),
    ]
    pairs = [
        (0, 1),
        (0, 2),
        (0, 3),
        (1, 2),
        (1, 3),
        (2, 3),
    ]

    fig, axes = plt.subplots(2, 3, figsize=(12.8, 7.1))
    axes = axes.flatten()
    for ax, (i, j) in zip(axes, pairs):
        x_key, x_label = dims[i]
        y_key, y_label = dims[j]
        for method in methods:
            points = points_by_method[method]
            ax.scatter(
                [p[x_key] for p in points],
                [p[y_key] for p in points],
                s=28,
                alpha=0.75,
                color=colors[method],
                marker=markers[method],
                label=_slug_to_display(method).replace("\n", " "),
            )
        ax.set_xlabel(x_label, fontsize=9)
        ax.set_ylabel(y_label, fontsize=9)
        ax.grid(alpha=0.22)

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="lower center",
        ncol=3,
        frameon=False,
        bbox_to_anchor=(0.5, -0.01),
        fontsize=10,
    )
    fig.tight_layout(rect=[0, 0.06, 1, 1])

    _save_figure(fig, "candidate_set_4obj_pairwise_matrix.png")


def _extract_casebook_seed_summary(seed: str) -> dict:
    casebook = next(
        (APPENDIX_ROOT / f"seed_{seed}").rglob("critical_casebook.md")
    ).read_text()
    step5_match = re.search(r"step 5:.*new=(Enterprise[01])", casebook)
    step6_match = re.search(r"step 6: Blue `Restore` -> `(Enterprise[01])`", casebook)
    enterprise_step_match = re.search(r"enterprise_foothold_step=(\\d+|None)", casebook)
    response_step_match = re.search(r"first_relevant_blue_response=(\\d+|None)", casebook)
    initial_blue_match = re.search(r"step 0: Blue `([^`]+)`", casebook)
    top_actions = re.findall(r"- `Restore -> (Enterprise[01])`: `(\\d+)` containment steps", casebook)
    return {
        "seed": seed,
        "initial_blue": initial_blue_match.group(1) if initial_blue_match else "Blue Action",
        "enterprise_host": step5_match.group(1) if step5_match else "Enterprise0",
        "restored_host": step6_match.group(1) if step6_match else "Enterprise0",
        "enterprise_step": int(enterprise_step_match.group(1))
        if enterprise_step_match and enterprise_step_match.group(1) != "None"
        else 5,
        "response_step": int(response_step_match.group(1))
        if response_step_match and response_step_match.group(1) != "None"
        else 6,
        "top_actions": top_actions,
    }


def build_attack_defense_timeline() -> None:
    seeds = ["0007", "0011", "0019"]
    summaries = [_extract_casebook_seed_summary(seed) for seed in seeds]

    fig, ax = plt.subplots(figsize=(11, 4.8))
    y_positions = np.arange(len(summaries))[::-1]
    colors = {
        "recon": "#94d2bd",
        "foothold": "#ee9b00",
        "restore": "#0a9396",
        "safe": "#005f73",
    }

    for y, summary in zip(y_positions, summaries):
        ax.hlines(y, 0, 10, color="#c9d1d9", linewidth=6, alpha=0.55)
        ax.scatter(2, y, s=90, color=colors["recon"], zorder=3)
        ax.scatter(summary["enterprise_step"], y, s=140, color=colors["foothold"], zorder=3)
        ax.scatter(summary["response_step"], y, s=150, color=colors["restore"], zorder=3)
        ax.annotate(
            f"Enterprise foothold on {summary['enterprise_host']}",
            (summary["enterprise_step"], y),
            textcoords="offset points",
            xytext=(0, 14),
            ha="center",
            fontsize=9,
        )
        ax.annotate(
            f"Restore {summary['restored_host']}",
            (summary["response_step"], y),
            textcoords="offset points",
            xytext=(0, -24),
            ha="center",
            fontsize=9,
            color=colors["restore"],
        )
        ax.annotate(
            "No critical breach through episode end",
            (9.3, y),
            textcoords="offset points",
            xytext=(0, 8),
            ha="right",
            fontsize=9,
            color=colors["safe"],
        )
        ax.text(
            -0.35,
            y,
            f"Seed {summary['seed']}\nidle={summary['initial_blue']}",
            ha="right",
            va="center",
            fontsize=9,
        )

    ax.set_xlim(-0.8, 10.5)
    ax.set_ylim(-0.7, len(summaries) - 0.3)
    ax.set_yticks([])
    ax.set_xticks([0, 2, 5, 6, 10])
    ax.set_xticklabels(
        [
            "Step 0\nstart",
            "Step 2\nuser compromise",
            "Step 5\nenterprise foothold",
            "Step 6\ncontainment",
            "Step 10+\nno critical breach",
        ]
    )
    ax.set_title("Representative Attack-Defense Timelines for V2.4 Selected Policies")
    ax.spines["left"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)

    legend_handles = [
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=colors["recon"], markersize=10, label="Early attack progress"),
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=colors["foothold"], markersize=10, label="Enterprise foothold"),
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=colors["restore"], markersize=10, label="Blue restore containment"),
    ]
    ax.legend(handles=legend_handles, frameon=False, loc="upper left")

    _save_figure(fig, "attack_defense_case_study_timeline.png")


def main() -> None:
    _ensure_output_dir()
    build_semantic_risk_summary()
    build_candidate_set_parallel_coordinates()
    build_candidate_set_3d_projection()
    build_candidate_set_pairwise_matrix()
    build_attack_defense_timeline()


if __name__ == "__main__":
    main()
