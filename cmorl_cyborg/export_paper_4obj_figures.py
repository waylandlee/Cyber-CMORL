from __future__ import annotations

import json
import math
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(REPO_ROOT / ".mplconfig"))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


OUTPUT_ROOT = REPO_ROOT / "paper" / "images"
PAPER_4OBJ_ROOT = REPO_ROOT / "cmorl_cyborg" / "outputs" / "paper_4obj"
RQ3_ROOT = PAPER_4OBJ_ROOT / "rq3_symmetric"
RQ3_SEMANTIC_ROOT = RQ3_ROOT / "semantic_comparison"
RQ3_PHASE_ROOT = RQ3_ROOT / "phase_analysis"
RQ3_PAIRED_ROOT = RQ3_ROOT / "paired_casebooks"


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
        RQ3_SEMANTIC_ROOT / "semantic_comparison_aggregate.json"
    )
    left = aggregate["left"]
    right = aggregate["right"]
    left_label = aggregate["left_display_name"]
    right_label = aggregate["right_display_name"]

    colors = {right_label: "#9b2226", left_label: "#0a9396"}
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
        [right[k] for _, k in rate_metrics],
        width=width,
        color=colors[right_label],
        label=right_label,
    )
    axes[0].bar(
        x + width / 2,
        [left[k] for _, k in rate_metrics],
        width=width,
        color=colors[left_label],
        label=left_label,
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
            right[key],
            bottom=baseline_bottom,
            color=color,
            width=0.5,
        )
        axes[1].bar(
            tier_x[1],
            left[key],
            bottom=selected_bottom,
            color=color,
            width=0.5,
            label=label,
        )
        baseline_bottom += right[key]
        selected_bottom += left[key]
    axes[1].set_xticks(tier_x)
    axes[1].set_xticklabels([right_label, left_label])
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
        [right[k] for k in behavior_keys],
        width=width,
        color=colors[right_label],
        label=right_label,
    )
    axes[2].bar(
        bx + width / 2,
        [left[k] for k in behavior_keys],
        width=width,
        color=colors[left_label],
        label=left_label,
    )
    axes[2].set_xticks(bx)
    axes[2].set_xticklabels(behavior_labels, fontsize=9)
    axes[2].set_ylim(0, 1.05)
    axes[2].set_ylabel("Rate")
    axes[2].set_title("Pre-Critical Response Structure")
    axes[2].grid(axis="y", alpha=0.25)

    fig.suptitle(
        "Semantic Safety of Selected Policies: Constraint-Aware vs. Unconstrained Stage-2",
        fontsize=14,
    )
    _save_figure(fig, "semantic_risk_4obj_summary.png")


def build_phase_conditioned_action_summary() -> None:
    aggregate = _load_json(RQ3_PHASE_ROOT / "phase_comparison.json")
    methods = ["ours_stage2_v2_4", "no_constraint_stage2_4obj"]
    method_labels = [aggregate[method]["display_name"] for method in methods]
    method_colors = {
        methods[0]: "#0a9396",
        methods[1]: "#9b2226",
    }
    foothold_action_metrics = [
        ("Decoy", "action_rate.decoy"),
        ("Analyse", "action_rate.analyse"),
        ("Sleep", "action_rate.sleep"),
        ("Other", "action_rate.other"),
    ]
    foothold_target_metrics = [
        ("Critical-path\nhost", "target_rate.critical_path_host"),
        ("User\nhost", "target_rate.user_host"),
        ("No target /\nother", "target_rate.no_target_or_other"),
    ]

    def _panel_values(
        phase_key: str,
        metrics: list[tuple[str, str]],
    ) -> dict[str, list[float]]:
        values: dict[str, list[float]] = {}
        for method_name in methods:
            phase_payload = aggregate[method_name]["phases"][phase_key]
            values[method_name] = [
                float(phase_payload[metric_key]) for _, metric_key in metrics
            ]
        return values

    def _draw_grouped_bars(
        ax: plt.Axes,
        *,
        metrics: list[tuple[str, str]],
        values_by_method: dict[str, list[float]],
        ymax: float,
    ) -> None:
        x = np.arange(len(metrics), dtype=float)
        width = 0.34
        for method_offset, method_name in enumerate(methods):
            offsets = x + (method_offset - 0.5) * width
            values = values_by_method[method_name]
            bars = ax.bar(
                offsets,
                values,
                width=width,
                color=method_colors[method_name],
                label=aggregate[method_name]["display_name"],
            )
            ax.bar_label(
                bars,
                labels=[f"{value:.2f}" for value in values],
                padding=2,
                fontsize=8,
            )
        ax.set_xticks(x)
        ax.set_xticklabels([label for label, _ in metrics], fontsize=9)
        ax.set_ylim(0.0, ymax)
        ax.set_ylabel("Rate")
        ax.grid(axis="y", alpha=0.25)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    fig, axes = plt.subplots(1, 2, figsize=(11.8, 4.1))
    ax_action, ax_target = axes

    _draw_grouped_bars(
        ax_action,
        metrics=foothold_action_metrics,
        values_by_method=_panel_values("foothold", foothold_action_metrics),
        ymax=0.78,
    )
    _draw_grouped_bars(
        ax_target,
        metrics=foothold_target_metrics,
        values_by_method=_panel_values("foothold", foothold_target_metrics),
        ymax=0.82,
    )

    method_handles = [
        plt.Rectangle((0, 0), 1, 1, color=method_colors[method], label=label)
        for method, label in zip(methods, method_labels)
    ]
    fig.legend(
        handles=method_handles,
        frameon=False,
        loc="upper center",
        ncol=2,
        bbox_to_anchor=(0.5, 0.98),
    )
    fig.subplots_adjust(left=0.07, right=0.98, bottom=0.14, top=0.78, wspace=0.25)
    _save_figure(fig, "phase_conditioned_action_semantics.png")


def build_phase_conditioned_action_dumbbell() -> None:
    aggregate = _load_json(RQ3_PHASE_ROOT / "phase_comparison.json")
    methods = ["ours_stage2_v2_4", "no_constraint_stage2_4obj"]
    labels = {method: aggregate[method]["display_name"] for method in methods}
    colors = {
        methods[0]: "#0a9396",
        methods[1]: "#9b2226",
    }
    foothold = {
        method: aggregate[method]["phases"]["foothold"] for method in methods
    }
    metrics = [
        (
            "Foothold decoy share",
            float(foothold[methods[0]]["action_rate.decoy"]),
            float(foothold[methods[1]]["action_rate.decoy"]),
        ),
        (
            "Foothold monitoring /\nlow-disruption share",
            float(
                foothold[methods[0]]["action_rate.analyse"]
                + foothold[methods[0]]["action_rate.sleep"]
                + foothold[methods[0]]["action_rate.other"]
            ),
            float(
                foothold[methods[1]]["action_rate.analyse"]
                + foothold[methods[1]]["action_rate.sleep"]
                + foothold[methods[1]]["action_rate.other"]
            ),
        ),
        (
            "Foothold critical-path focus",
            float(foothold[methods[0]]["target_rate.critical_path_host"]),
            float(foothold[methods[1]]["target_rate.critical_path_host"]),
        ),
        (
            "Foothold user-host focus",
            float(foothold[methods[0]]["target_rate.user_host"]),
            float(foothold[methods[1]]["target_rate.user_host"]),
        ),
    ]
    precritical = {
        method: aggregate[method]["phases"]["precritical"] for method in methods
    }

    fig = plt.figure(figsize=(10.6, 5.6))
    gs = fig.add_gridspec(1, 2, width_ratios=[3.4, 1.5], wspace=0.16)
    ax = fig.add_subplot(gs[0, 0])
    ax_note = fig.add_subplot(gs[0, 1])

    y = np.arange(len(metrics), dtype=float)[::-1]
    for idx, (metric_label, left_value, right_value) in enumerate(metrics):
        y_pos = y[idx]
        ax.plot(
            [left_value, right_value],
            [y_pos, y_pos],
            color="#b0b8c0",
            linewidth=2.2,
            solid_capstyle="round",
            zorder=1,
        )
        ax.scatter(
            left_value,
            y_pos,
            s=130,
            color=colors[methods[0]],
            edgecolors="white",
            linewidth=1.0,
            zorder=3,
        )
        ax.scatter(
            right_value,
            y_pos,
            s=130,
            color=colors[methods[1]],
            edgecolors="white",
            linewidth=1.0,
            zorder=3,
        )
        ax.text(
            left_value - 0.035,
            y_pos + 0.12,
            f"{left_value:.2f}",
            ha="right",
            va="center",
            fontsize=9,
            color=colors[methods[0]],
        )
        ax.text(
            right_value + 0.035,
            y_pos - 0.12,
            f"{right_value:.2f}",
            ha="left",
            va="center",
            fontsize=9,
            color=colors[methods[1]],
        )

    ax.set_yticks(y)
    ax.set_yticklabels([label for label, _, _ in metrics], fontsize=10)
    ax.set_xlim(0.0, 1.05)
    ax.set_xticks(np.linspace(0.0, 1.0, 6))
    ax.set_xlabel("Rate")
    ax.set_title("Foothold-Phase Semantic Gaps")
    ax.grid(axis="x", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    legend_handles = [
        plt.Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            markerfacecolor=colors[method],
            markeredgecolor="white",
            markeredgewidth=1.0,
            markersize=10,
            label=labels[method],
        )
        for method in methods
    ]
    ax.legend(handles=legend_handles, frameon=False, loc="lower right")

    ax_note.axis("off")
    ax_note.text(
        0.02,
        0.95,
        "How to read this view\n\n"
        "Each row is one foothold-phase semantic indicator.\n"
        "The horizontal gap shows how far the two selected policies diverge.\n\n"
        f"Pre-critical convergence:\n"
        f"• Restore share = {precritical[methods[0]]['action_rate.restore']:.2f} vs {precritical[methods[1]]['action_rate.restore']:.2f}\n"
        f"• Critical-path focus = {precritical[methods[0]]['target_rate.critical_path_host']:.2f} vs {precritical[methods[1]]['target_rate.critical_path_host']:.2f}\n\n"
        "Critical-present is omitted because both selected policies have 0.00 mass there on the main three-seed replay.",
        transform=ax_note.transAxes,
        ha="left",
        va="top",
        fontsize=9.5,
        bbox={
            "boxstyle": "round,pad=0.45",
            "facecolor": "#f6f7f9",
            "edgecolor": "#d0d7de",
        },
    )

    fig.suptitle(
        "Selected-Policy Foothold Semantics: Dumbbell Comparison",
        fontsize=14,
        y=0.98,
    )
    fig.subplots_adjust(left=0.22, right=0.97, bottom=0.12, top=0.88)
    _save_figure(fig, "phase_conditioned_action_semantics_dumbbell.png")


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
    allowed_methods = {"ours_stage2_v2_4", "stage1_only_4obj", "weighted_sum_4obj"}
    for method in summary["method_summary"]:
        if method["method_name"] not in allowed_methods:
            continue
        points: list[dict] = []
        for run in method["runs"]:
            buffer_data = _load_json(Path(run["artifact_path"]))
            records = buffer_data.get("pareto_front")
            if records is None:
                records = buffer_data.get("records")
            if records is None:
                continue
            for record in records:
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


def _paired_seed_summary(seed: str) -> dict:
    return _load_json(RQ3_PAIRED_ROOT / f"seed_{seed}_summary.json")


def build_attack_defense_timeline() -> None:
    seed_summary = _paired_seed_summary("0011")
    summaries = [
        seed_summary["methods"]["ours_stage2_v2_4"],
        seed_summary["methods"]["no_constraint_stage2_4obj"],
    ]

    fig, ax = plt.subplots(figsize=(6.2, 5.4))
    y_positions = np.arange(len(summaries))[::-1]
    colors = {
        "recon": "#94d2bd",
        "foothold": "#ee9b00",
        "restore": "#0a9396",
        "critical": "#9b2226",
        "safe": "#005f73",
    }

    for y, summary in zip(y_positions, summaries):
        enterprise_step = summary.get("mode_enterprise_foothold_step")
        response_step = summary.get("mode_response_step")
        critical_step = summary.get("mode_first_critical_hit_step")
        line_end = max(
            [value for value in (enterprise_step, response_step, critical_step, 10) if value is not None]
        )
        ax.hlines(y, 0, line_end + 1, color="#c9d1d9", linewidth=6, alpha=0.55)
        ax.scatter(2, y, s=80, color=colors["recon"], zorder=3)
        if enterprise_step is not None:
            ax.scatter(enterprise_step, y, s=120, color=colors["foothold"], zorder=3)
            ax.annotate(
                f"Foothold\n{summary.get('mode_enterprise_host') or 'Enterprise host'}",
                (enterprise_step, y),
                textcoords="offset points",
                xytext=(0, 16),
                ha="center",
                fontsize=8,
                bbox={
                    "boxstyle": "round,pad=0.22",
                    "facecolor": "white",
                    "edgecolor": "#d0d7de",
                },
            )
        if response_step is not None:
            ax.scatter(response_step, y, s=130, color=colors["restore"], zorder=3)
            ax.annotate(
                f"{summary.get('mode_response_action_name') or 'Response'}\n{summary.get('mode_response_target') or 'critical-path host'}",
                (response_step, y),
                textcoords="offset points",
                xytext=(0, -30),
                ha="center",
                fontsize=8,
                color=colors["restore"],
                bbox={
                    "boxstyle": "round,pad=0.22",
                    "facecolor": "white",
                    "edgecolor": "#d0d7de",
                },
            )
        if critical_step is not None:
            ax.scatter(critical_step, y, s=130, color=colors["critical"], zorder=3)
        ax.annotate(
            summary["outcome_label"],
            ((critical_step if critical_step is not None else line_end), y),
            textcoords="offset points",
            xytext=(0, 11),
            ha="center",
            fontsize=8,
            color=colors["critical"] if critical_step is not None else colors["safe"],
        )
        ax.text(
            -0.58,
            y,
            f"{summary['display_name']}\npolicy={summary['policy_id']}",
            ha="right",
            va="center",
            fontsize=8.5,
        )

    ax.set_xlim(-1.0, 12.4)
    ax.set_ylim(-0.7, len(summaries) - 0.3)
    ax.set_yticks([])
    ax.set_xticks([0, 2, 5, 6, 9, 12])
    ax.set_xticklabels(
        [
            "0\nStart",
            "2\nUser",
            "5\nFoothold",
            "6\nResponse",
            "9\nCritical",
            "12+\nOutcome",
        ]
    )
    ax.tick_params(axis="x", labelsize=8)
    ax.set_title("Seed 0011 Paired Timeline", fontsize=11)
    ax.spines["left"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)

    legend_handles = [
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=colors["recon"], markersize=8, label="Early attack progress"),
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=colors["foothold"], markersize=8, label="Enterprise foothold"),
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=colors["restore"], markersize=8, label="Blue response"),
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=colors["critical"], markersize=8, label="Critical hit"),
    ]
    ax.legend(handles=legend_handles, frameon=False, loc="upper center", ncol=2, fontsize=8)

    fig.subplots_adjust(left=0.26, right=0.97, top=0.86, bottom=0.16)

    _save_figure(fig, "attack_defense_case_study_timeline.png")


def main() -> None:
    _ensure_output_dir()
    build_semantic_risk_summary()
    build_phase_conditioned_action_summary()
    build_phase_conditioned_action_dumbbell()
    build_candidate_set_parallel_coordinates()
    build_candidate_set_3d_projection()
    build_candidate_set_pairwise_matrix()
    build_attack_defense_timeline()


if __name__ == "__main__":
    main()
