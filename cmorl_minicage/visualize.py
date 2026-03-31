from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

import numpy as np

from cmorl_minicage.utils import ensure_dir, load_json

OBJECTIVE_LABELS = ("Security", "Business", "Cost")
COMPACT_MARKERS = ("o", "^", "s", "D", "P", "X", "v", "<", ">")
SEMANTIC_METRIC_PANELS = [
    ("final_compromised_hosts", "Final Compromised Hosts", "#4c78a8"),
    ("final_critical_compromised_hosts", "Final Critical Compromised", "#e45756"),
    ("critical_impact_count", "Critical Impact Count", "#f58518"),
    ("recovered_hosts", "Recovered Hosts", "#54a24b"),
    ("analyse_count", "Analyse Count", "#72b7b2"),
    ("remove_count", "Remove Count", "#b279a2"),
    ("restore_count", "Restore Count", "#ff9da6"),
    ("high_disruption_action_rate", "High Disruption Rate", "#9d755d"),
]
CORE_SECURITY_METRIC_PANELS = [
    ("final_compromised_hosts", "Final Compromised Hosts", "#4c78a8"),
    ("final_critical_compromised_hosts", "Final Critical Compromised", "#e45756"),
    ("critical_impact_count", "Critical Impact Count", "#f58518"),
]


def _import_matplotlib():
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError(
            "matplotlib is required for visualization. Install it in the active environment."
        ) from exc
    return plt


def _objective_array(records: Sequence[dict]) -> np.ndarray:
    if not records:
        return np.zeros((0, 0), dtype=np.float32)
    return np.asarray([record["objective_vector"] for record in records], dtype=np.float32)


def _label_from_path(path: str | Path) -> str:
    path = Path(path)
    if path.parent.name.startswith("run_"):
        return f"{path.parent.parent.name}:{path.parent.name}"
    return path.stem


def _repo_root_from_path(path: str | Path) -> Path:
    path = Path(path).resolve()
    for candidate in (path, *path.parents):
        if (candidate / "cmorl_minicage").exists():
            return candidate
    raise ValueError(f"Could not infer repository root from {path}")


def _resolve_repo_path(base_dir: Path, maybe_relative: str | Path) -> Path:
    candidate = Path(maybe_relative)
    if candidate.is_absolute():
        return candidate
    return (_repo_root_from_path(base_dir) / candidate).resolve()


def _load_stage1_pareto_from_stage2(payload: dict, run_dir: Path) -> list[dict]:
    metadata = payload.get("metadata", {})
    stage1_buffer = metadata.get("stage1_buffer")
    if not stage1_buffer:
        return []
    stage1_path = _resolve_repo_path(run_dir, stage1_buffer)
    if not stage1_path.exists():
        return []
    stage1_payload = load_json(stage1_path)
    return stage1_payload.get("pareto_front", [])


def _plot_stage_scatter_2d(plt, axis, points: np.ndarray, *, label: str, color: str, marker: str) -> None:
    if len(points) == 0:
        return
    axis.scatter(
        points[:, 0],
        points[:, 1],
        label=label,
        color=color,
        marker=marker,
        s=56,
        alpha=0.85,
        edgecolor="white",
        linewidth=0.4,
    )


def _plot_stage_scatter_3d(axis, points: np.ndarray, *, label: str, color: str, marker: str) -> None:
    if len(points) == 0:
        return
    axis.scatter(
        points[:, 0],
        points[:, 1],
        points[:, 2],
        label=label,
        color=color,
        marker=marker,
        s=66,
        alpha=0.88,
        depthshade=True,
        edgecolor="white",
        linewidth=0.35,
    )


def _objective_label(index: int) -> str:
    if index < len(OBJECTIVE_LABELS):
        return OBJECTIVE_LABELS[index]
    return f"Objective {index}"


def _plot_run_projections(
    plt,
    run_dir: Path,
    output_dir: Path,
    stage1_records: Sequence[dict],
    stage2_records: Sequence[dict],
) -> list[Path]:
    outputs: list[Path] = []
    stage1_points = _objective_array(stage1_records)
    stage2_points = _objective_array(stage2_records)
    all_points = np.vstack([arr for arr in (stage1_points, stage2_points) if len(arr) > 0])
    dims = all_points.shape[1]

    fig, axes = plt.subplots(1, dims, figsize=(5 * dims, 4.6))
    if dims == 1:
        axes = [axes]
    for axis, y_idx in zip(axes, range(dims)):
        x_idx = (y_idx + 1) % dims
        if len(stage1_points) > 0:
            axis.scatter(
                stage1_points[:, x_idx],
                stage1_points[:, y_idx],
                label="Stage-1 Pareto",
                color="#4c78a8",
                s=52,
                alpha=0.82,
                edgecolor="white",
                linewidth=0.35,
            )
        if len(stage2_points) > 0:
            axis.scatter(
                stage2_points[:, x_idx],
                stage2_points[:, y_idx],
                label="Stage-2 Pareto",
                color="#e45756",
                marker="^",
                s=62,
                alpha=0.86,
                edgecolor="white",
                linewidth=0.35,
            )
        axis.set_xlabel(_objective_label(x_idx))
        axis.set_ylabel(_objective_label(y_idx))
        axis.set_title(f"Projection ({x_idx}, {y_idx})")
        axis.grid(True, alpha=0.22)
    handles, labels = axes[0].get_legend_handles_labels()
    if handles:
        fig.legend(handles, labels, loc="upper center", ncol=2, frameon=False)
    fig.suptitle(f"Pareto Front Projections: {run_dir.name}")
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    out_path = output_dir / "pareto_projections.png"
    fig.savefig(out_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    outputs.append(out_path)
    return outputs


def _plot_run_overlay(
    plt,
    run_dir: Path,
    output_dir: Path,
    stage1_records: Sequence[dict],
    stage2_records: Sequence[dict],
) -> list[Path]:
    outputs: list[Path] = []
    stage1_points = _objective_array(stage1_records)
    stage2_points = _objective_array(stage2_records)
    if len(stage1_points) == 0 or len(stage2_points) == 0:
        return outputs

    dims = stage2_points.shape[1]
    pairs = [(0, 1)]
    if dims >= 3:
        pairs.extend([(0, 2), (1, 2)])

    fig, axes = plt.subplots(1, len(pairs), figsize=(5.2 * len(pairs), 4.5))
    if len(pairs) == 1:
        axes = [axes]
    for axis, (x_idx, y_idx) in zip(axes, pairs):
        _plot_stage_scatter_2d(
            plt,
            axis,
            stage1_points[:, [x_idx, y_idx]],
            label="Stage-1 Pareto",
            color="#4c78a8",
            marker="o",
        )
        _plot_stage_scatter_2d(
            plt,
            axis,
            stage2_points[:, [x_idx, y_idx]],
            label="Stage-2 Pareto",
            color="#e45756",
            marker="^",
        )
        axis.set_xlabel(_objective_label(x_idx))
        axis.set_ylabel(_objective_label(y_idx))
        axis.set_title(f"Stage-1 vs Stage-2 ({x_idx}, {y_idx})")
        axis.grid(True, alpha=0.22)
    handles, labels = axes[0].get_legend_handles_labels()
    if handles:
        fig.legend(handles, labels, loc="upper center", ncol=2, frameon=False)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    out_path = output_dir / "stage1_vs_stage2_overlay.png"
    fig.savefig(out_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    outputs.append(out_path)
    return outputs


def _plot_run_3d(
    plt,
    run_dir: Path,
    output_dir: Path,
    stage1_records: Sequence[dict],
    stage2_records: Sequence[dict],
) -> list[Path]:
    outputs: list[Path] = []
    stage1_points = _objective_array(stage1_records)
    stage2_points = _objective_array(stage2_records)
    all_points = np.vstack([arr for arr in (stage1_points, stage2_points) if len(arr) > 0])
    if all_points.shape[1] < 3:
        return outputs

    fig = plt.figure(figsize=(7.5, 6.2))
    axis = fig.add_subplot(111, projection="3d")
    _plot_stage_scatter_3d(
        axis,
        stage1_points[:, :3] if len(stage1_points) > 0 else stage1_points,
        label="Stage-1 Pareto",
        color="#4c78a8",
        marker="o",
    )
    _plot_stage_scatter_3d(
        axis,
        stage2_points[:, :3] if len(stage2_points) > 0 else stage2_points,
        label="Stage-2 Pareto",
        color="#e45756",
        marker="^",
    )
    axis.set_xlabel(_objective_label(0))
    axis.set_ylabel(_objective_label(1))
    axis.set_zlabel(_objective_label(2))
    axis.set_title(f"3D Pareto Scatter: {run_dir.name}")
    axis.view_init(elev=22, azim=38)
    axis.legend(frameon=False, loc="upper left")
    out_path = output_dir / "pareto_3d_scatter.png"
    fig.savefig(out_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    outputs.append(out_path)
    return outputs


def _plot_assignment_counts(plt, output_dir: Path, metrics_payload: dict) -> list[Path]:
    outputs: list[Path] = []
    assignment_counts = metrics_payload.get("assignment_counts", {})
    if not assignment_counts:
        return outputs
    items = sorted(assignment_counts.items(), key=lambda item: item[1], reverse=True)
    labels = [item[0] for item in items]
    counts = [item[1] for item in items]
    fig, axis = plt.subplots(figsize=(max(8, len(labels) * 0.8), 4.5))
    axis.bar(labels, counts, color="#54a24b")
    axis.set_title("Preference Assignment Counts")
    axis.set_ylabel("Assigned Preference Count")
    axis.set_xlabel("Policy ID")
    axis.tick_params(axis="x", rotation=45, labelsize=8)
    axis.grid(True, axis="y", alpha=0.25)
    fig.tight_layout()
    out_path = output_dir / "assignment_counts.png"
    fig.savefig(out_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    outputs.append(out_path)
    return outputs


def _plot_stage2_rounds(plt, output_dir: Path, rounds: Sequence[dict]) -> list[Path]:
    outputs: list[Path] = []
    if not rounds:
        return outputs
    round_ids = [entry["round_index"] for entry in rounds]
    before = [entry["pareto_size_before_round"] for entry in rounds]
    after = [entry["pareto_size_after_round"] for entry in rounds]
    generated = [
        sum(1 for result in entry["extension_results"] if result["generated_policy_id"])
        for entry in rounds
    ]
    terminated = [
        sum(
            1
            for result in entry["extension_results"]
            if result["terminated_due_to_constraints"]
        )
        for entry in rounds
    ]

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.6))
    axes[0].plot(round_ids, before, marker="o", label="Before Round", color="#4c78a8")
    axes[0].plot(round_ids, after, marker="o", label="After Round", color="#e45756")
    axes[0].set_title("Pareto Size by Round")
    axes[0].set_xlabel("Round")
    axes[0].set_ylabel("Pareto Size")
    axes[0].grid(True, alpha=0.25)
    axes[0].legend(frameon=False)

    width = 0.35
    axes[1].bar(np.asarray(round_ids) - width / 2, generated, width=width, label="Generated")
    axes[1].bar(
        np.asarray(round_ids) + width / 2,
        terminated,
        width=width,
        label="Constraint-Terminated",
    )
    axes[1].set_title("Extension Outcomes by Round")
    axes[1].set_xlabel("Round")
    axes[1].set_ylabel("Attempt Count")
    axes[1].grid(True, axis="y", alpha=0.25)
    axes[1].legend(frameon=False)

    fig.tight_layout()
    out_path = output_dir / "stage2_rounds.png"
    fig.savefig(out_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    outputs.append(out_path)
    return outputs


def plot_run(run_dir: str | Path, output_dir: str | Path | None = None) -> list[Path]:
    plt = _import_matplotlib()
    run_dir = Path(run_dir)
    if output_dir is None:
        output_dir = run_dir / "plots"
    output_dir = ensure_dir(output_dir)

    solution_path = run_dir / "solution_buffer.json"
    if not solution_path.exists():
        raise FileNotFoundError(f"Missing {solution_path}")

    payload = load_json(solution_path)
    pareto_records = payload.get("pareto_front", [])
    if not pareto_records:
        raise ValueError(f"No pareto_front found in {solution_path}")

    stage1_parent_records = _load_stage1_pareto_from_stage2(payload, run_dir)
    stage1_current_records = [record for record in pareto_records if record.get("stage") == "stage1"]
    stage2_current_records = [record for record in pareto_records if record.get("stage") == "stage2"]
    stage1_reference_records = stage1_parent_records or stage1_current_records

    outputs: list[Path] = []
    all_current = stage1_current_records + stage2_current_records
    current_plot_records = all_current if all_current else pareto_records
    outputs.extend(_plot_run_projections(plt, run_dir, output_dir, stage1_current_records, stage2_current_records or current_plot_records))
    outputs.extend(_plot_run_3d(plt, run_dir, output_dir, stage1_reference_records, stage2_current_records or stage1_current_records))
    outputs.extend(_plot_run_overlay(plt, run_dir, output_dir, stage1_reference_records, stage2_current_records))

    metrics_path = run_dir / "metrics.json"
    if metrics_path.exists():
        metrics_payload = load_json(metrics_path)
        outputs.extend(_plot_assignment_counts(plt, output_dir, metrics_payload))

    summary_path = run_dir / "stage2_summary.json"
    if summary_path.exists():
        rounds = load_json(summary_path)
        outputs.extend(_plot_stage2_rounds(plt, output_dir, rounds))

    if not outputs:
        raise ValueError(f"No plottable artifacts found in {run_dir}")
    return outputs


def plot_metrics_comparison(
    metrics_paths: Sequence[str | Path],
    labels: Sequence[str] | None = None,
    output_path: str | Path | None = None,
) -> Path:
    if not metrics_paths:
        raise ValueError("At least one metrics.json path is required")
    plt = _import_matplotlib()

    metric_names = [
        ("hypervolume", "Hypervolume"),
        ("expected_utility", "Expected Utility"),
        ("sparsity", "Sparsity"),
        ("num_pareto_records", "Pareto Count"),
        ("coverage_ratio", "Coverage Ratio"),
    ]

    resolved_paths = [Path(path) for path in metrics_paths]
    if labels is None:
        labels = [_label_from_path(path) for path in resolved_paths]
    if len(labels) != len(resolved_paths):
        raise ValueError("labels length must match metrics_paths length")

    rows = []
    for path in resolved_paths:
        payload = load_json(path)
        metrics = payload["metrics"]
        assignment_summary = payload.get("assignment_summary", {})
        rows.append(
            {
                "hypervolume": metrics["hypervolume"],
                "expected_utility": metrics["expected_utility"],
                "sparsity": metrics["sparsity"],
                "num_pareto_records": metrics["num_pareto_records"],
                "coverage_ratio": assignment_summary.get("coverage_ratio", 0.0),
            }
        )

    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    flat_axes = axes.flatten()
    x = np.arange(len(labels))
    for axis, (metric_key, title) in zip(flat_axes, metric_names):
        values = [row[metric_key] for row in rows]
        axis.bar(x, values, color="#4c78a8")
        axis.set_title(title)
        axis.set_xticks(x)
        axis.set_xticklabels(labels, rotation=35, ha="right")
        axis.grid(True, axis="y", alpha=0.25)
    flat_axes[-1].axis("off")
    fig.tight_layout()

    if output_path is None:
        output_path = Path("cmorl_minicage/outputs/plots/metrics_comparison.png")
    output_path = Path(output_path)
    ensure_dir(output_path.parent)
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_semantic_comparison(
    metrics_paths: Sequence[str | Path],
    labels: Sequence[str] | None = None,
    output_path: str | Path | None = None,
) -> Path:
    if not metrics_paths:
        raise ValueError("At least one metrics file is required")
    plt = _import_matplotlib()

    resolved_paths = [Path(path) for path in metrics_paths]
    if labels is None:
        labels = [_label_from_path(path) for path in resolved_paths]
    if len(labels) != len(resolved_paths):
        raise ValueError("labels length must match metrics_paths length")

    rows = []
    for path in resolved_paths:
        payload = load_json(path)
        semantic_metrics = payload.get("semantic_metrics")
        if not semantic_metrics:
            raise ValueError(f"Missing semantic_metrics in {path}")
        rows.append(semantic_metrics)

    cols = 4
    rows_count = int(np.ceil(len(SEMANTIC_METRIC_PANELS) / cols))
    fig, axes = plt.subplots(rows_count, cols, figsize=(18, 8.5))
    axes = np.asarray(axes).reshape(-1)
    x = np.arange(len(labels))

    for axis, (metric_key, title, color) in zip(axes, SEMANTIC_METRIC_PANELS):
        values = [row[metric_key] for row in rows]
        bars = axis.bar(x, values, color=color, alpha=0.92)
        best_idx = int(np.argmin(values)) if metric_key != "recovered_hosts" else int(np.argmax(values))
        bars[best_idx].set_edgecolor("black")
        bars[best_idx].set_linewidth(1.4)
        axis.set_title(title)
        axis.set_xticks(x)
        axis.set_xticklabels(labels, rotation=25, ha="right")
        axis.grid(True, axis="y", alpha=0.22)
        _style_bar_annotations(axis, values)

    for axis in axes[len(SEMANTIC_METRIC_PANELS):]:
        axis.axis("off")

    fig.suptitle("Cyber Semantics Comparison", fontsize=16, y=0.98)
    fig.tight_layout(rect=(0, 0, 1, 0.95))

    if output_path is None:
        output_path = Path("cmorl_minicage/outputs/plots/semantic_comparison.png")
    output_path = Path(output_path)
    ensure_dir(output_path.parent)
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_core_security_comparison(
    metrics_paths: Sequence[str | Path],
    labels: Sequence[str] | None = None,
    output_path: str | Path | None = None,
) -> Path:
    if not metrics_paths:
        raise ValueError("At least one metrics file is required")
    plt = _import_matplotlib()

    resolved_paths = [Path(path) for path in metrics_paths]
    if labels is None:
        labels = [_label_from_path(path) for path in resolved_paths]
    if len(labels) != len(resolved_paths):
        raise ValueError("labels length must match metrics_paths length")

    rows = []
    for path in resolved_paths:
        payload = load_json(path)
        semantic_metrics = payload.get("semantic_metrics")
        if not semantic_metrics:
            raise ValueError(f"Missing semantic_metrics in {path}")
        rows.append(semantic_metrics)

    fig, axes = plt.subplots(1, len(CORE_SECURITY_METRIC_PANELS), figsize=(14.5, 4.8))
    axes = np.asarray(axes).reshape(-1)
    x = np.arange(len(labels))

    for axis, (metric_key, title, color) in zip(axes, CORE_SECURITY_METRIC_PANELS):
        values = [row[metric_key] for row in rows]
        bars = axis.bar(x, values, color=color, alpha=0.92)
        best_idx = int(np.argmin(values))
        bars[best_idx].set_edgecolor("black")
        bars[best_idx].set_linewidth(1.4)
        axis.set_title(title)
        axis.set_xticks(x)
        axis.set_xticklabels(labels, rotation=20, ha="right")
        axis.grid(True, axis="y", alpha=0.22)
        _style_bar_annotations(axis, values)
        axis.set_ylabel("Lower is better")

    fig.suptitle("Core Cyber Security Outcomes", fontsize=16, y=0.98)
    fig.tight_layout(rect=(0, 0, 1, 0.93))

    if output_path is None:
        output_path = Path("cmorl_minicage/outputs/plots/core_security_comparison.png")
    output_path = Path(output_path)
    ensure_dir(output_path.parent)
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output_path


def _compact_method_style(label: str, default_marker: str) -> dict:
    lowered = label.lower()
    if "stage-1" in lowered or "stage1" in lowered:
        return {
            "marker": "o",
            "size": 105,
            "alpha": 0.38,
            "edgecolor": "#1f4e79",
            "linewidth": 1.2,
            "zorder": 2,
            "centroid_color": "#1f4e79",
        }
    if "stage-2" in lowered or "stage2" in lowered:
        return {
            "marker": "^",
            "size": 165,
            "alpha": 0.98,
            "edgecolor": "#111111",
            "linewidth": 1.15,
            "zorder": 4,
            "centroid_color": "#b22222",
        }
    if "weighted" in lowered:
        return {
            "marker": "s",
            "size": 120,
            "alpha": 0.75,
            "edgecolor": "#4a4a4a",
            "linewidth": 0.9,
            "zorder": 3,
            "centroid_color": "#4a4a4a",
        }
    return {
        "marker": default_marker,
        "size": 100,
        "alpha": 0.86,
        "edgecolor": "white",
        "linewidth": 0.45,
        "zorder": 3,
        "centroid_color": "#666666",
    }


def plot_compact_objective_map(
    buffer_paths: Sequence[str | Path],
    labels: Sequence[str] | None = None,
    output_path: str | Path | None = None,
) -> Path:
    if not buffer_paths:
        raise ValueError("At least one solution_buffer.json path is required")
    plt = _import_matplotlib()

    resolved_paths = [Path(path) for path in buffer_paths]
    if labels is None:
        labels = [_label_from_path(path) for path in resolved_paths]
    if len(labels) != len(resolved_paths):
        raise ValueError("labels length must match buffer_paths length")

    payloads = [load_json(path) for path in resolved_paths]
    pareto_sets = [payload.get("pareto_front", []) for payload in payloads]
    if any(not pareto for pareto in pareto_sets):
        raise ValueError("Every buffer_path must contain a non-empty pareto_front")

    all_points = np.vstack([_objective_array(records) for records in pareto_sets])
    mins = np.min(all_points, axis=0)
    maxs = np.max(all_points, axis=0)
    ranges = np.maximum(maxs - mins, 1e-6)

    fig, axis = plt.subplots(figsize=(10.4, 7.8))
    fig.patch.set_facecolor("#f7f8fb")
    axis.set_facecolor("#fbfcfe")
    background = np.linspace(0.0, 1.0, 256)
    background = np.outer(np.ones(256), background)
    axis.imshow(
        background,
        extent=(0.0, 1.0, 0.0, 1.0),
        origin="lower",
        cmap="Greys",
        alpha=0.06,
        zorder=0,
        aspect="auto",
    )
    last_scatter = None
    legend_handles = []

    for idx, (label, records) in enumerate(zip(labels, pareto_sets)):
        points = _objective_array(records)
        norm_points = (points - mins) / ranges
        style = _compact_method_style(label, COMPACT_MARKERS[idx % len(COMPACT_MARKERS)])
        order = np.argsort(norm_points[:, 0])
        axis.plot(
            norm_points[order, 0],
            norm_points[order, 1],
            color=style["centroid_color"],
            linewidth=1.25,
            alpha=0.28,
            zorder=max(style["zorder"] - 1, 1),
        )
        last_scatter = axis.scatter(
            norm_points[:, 0],
            norm_points[:, 1],
            c=norm_points[:, 2],
            cmap="viridis",
            vmin=0.0,
            vmax=1.0,
            marker=style["marker"],
            s=style["size"],
            alpha=style["alpha"],
            edgecolor=style["edgecolor"],
            linewidth=style["linewidth"],
            zorder=style["zorder"],
            label=label,
        )
        legend_handles.append(
            plt.Line2D(
                [0],
                [0],
                marker=style["marker"],
                color="none",
                markerfacecolor="white",
                markeredgecolor="#4b5563",
                markeredgewidth=max(float(style["linewidth"]) * 0.8, 0.6),
                markersize=7,
                linestyle="None",
                label=label,
            )
        )

    axis.set_xlabel(f"Normalized {_objective_label(0)}")
    axis.set_ylabel(f"Normalized {_objective_label(1)}")
    axis.set_title("Pareto Front Comparison in Normalized Objective Space", fontsize=14, pad=12)
    axis.grid(True, alpha=0.18, color="#94a3b8", linestyle="--", linewidth=0.8)
    axis.set_xlim(-0.03, 1.03)
    axis.set_ylim(-0.03, 1.03)
    axis.set_xticks(np.linspace(0.0, 1.0, 5))
    axis.set_yticks(np.linspace(0.0, 1.0, 5))
    for spine in axis.spines.values():
        spine.set_color("#cbd5e1")
        spine.set_linewidth(1.0)

    if last_scatter is not None:
        colorbar = fig.colorbar(last_scatter, ax=axis, pad=0.025, shrink=0.94)
        colorbar.set_label(f"Normalized {_objective_label(2)}")
        colorbar.outline.set_edgecolor("#cbd5e1")
        colorbar.outline.set_linewidth(0.8)

    legend = axis.legend(
        handles=legend_handles,
        frameon=True,
        fancybox=True,
        framealpha=0.9,
        loc="lower right",
    )
    legend.get_frame().set_edgecolor("#d8dee9")
    legend.get_frame().set_facecolor("white")
    fig.tight_layout()

    if output_path is None:
        output_path = Path("cmorl_minicage/outputs/plots/compact_objective_map.png")
    output_path = Path(output_path)
    ensure_dir(output_path.parent)
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_objective_3d_comparison(
    buffer_paths: Sequence[str | Path],
    labels: Sequence[str] | None = None,
    output_path: str | Path | None = None,
) -> Path:
    if not buffer_paths:
        raise ValueError("At least one solution_buffer.json path is required")
    plt = _import_matplotlib()

    resolved_paths = [Path(path) for path in buffer_paths]
    if labels is None:
        labels = [_label_from_path(path) for path in resolved_paths]
    if len(labels) != len(resolved_paths):
        raise ValueError("labels length must match buffer_paths length")

    payloads = [load_json(path) for path in resolved_paths]
    pareto_sets = [payload.get("pareto_front", []) for payload in payloads]
    if any(not pareto for pareto in pareto_sets):
        raise ValueError("Every buffer_path must contain a non-empty pareto_front")

    all_points = np.vstack([_objective_array(records) for records in pareto_sets])
    mins = np.min(all_points, axis=0)
    maxs = np.max(all_points, axis=0)
    ranges = np.maximum(maxs - mins, 1e-6)
    paper_colors = ["#4C78A8", "#F58518", "#54A24B", "#E45756", "#B279A2", "#9D755D"]

    fig = plt.figure(figsize=(10.6, 8.0))
    axis = fig.add_subplot(111, projection="3d")
    fig.patch.set_facecolor("white")
    try:
        axis.xaxis.pane.set_facecolor((1.0, 1.0, 1.0, 1.0))
        axis.yaxis.pane.set_facecolor((1.0, 1.0, 1.0, 1.0))
        axis.zaxis.pane.set_facecolor((1.0, 1.0, 1.0, 1.0))
        axis.xaxis.pane.set_edgecolor("#d1d5db")
        axis.yaxis.pane.set_edgecolor("#d1d5db")
        axis.zaxis.pane.set_edgecolor("#d1d5db")
    except Exception:
        pass
    legend_handles = []

    for idx, (label, records) in enumerate(zip(labels, pareto_sets)):
        points = _objective_array(records)
        norm_points = (points - mins) / ranges
        style = _compact_method_style(label, COMPACT_MARKERS[idx % len(COMPACT_MARKERS)])
        color = paper_colors[idx % len(paper_colors)]

        axis.scatter(
            norm_points[:, 0],
            norm_points[:, 1],
            norm_points[:, 2],
            marker="o",
            s=110,
            alpha=0.96,
            color=color,
            edgecolor="white",
            linewidth=0.7,
            depthshade=True,
            label=label,
            zorder=3 + idx,
        )

        legend_handles.append(
            plt.Line2D(
                [0],
                [0],
                marker="o",
                color="none",
                markerfacecolor=color,
                markeredgecolor="white",
                markeredgewidth=0.7,
                markersize=8,
                linestyle="None",
                label=label,
            )
        )

    axis.set_xlabel(f"Normalized {_objective_label(0)}", labelpad=10)
    axis.set_ylabel(f"Normalized {_objective_label(1)}", labelpad=10)
    axis.set_zlabel(f"Normalized {_objective_label(2)}", labelpad=8)
    axis.set_title("Three-Dimensional Pareto Front Comparison", pad=12, fontsize=14)
    axis.view_init(elev=20, azim=38)
    axis.set_xlim(-0.03, 1.03)
    axis.set_ylim(-0.03, 1.03)
    axis.set_zlim(-0.03, 1.03)
    axis.set_xticks(np.linspace(0.0, 1.0, 5))
    axis.set_yticks(np.linspace(0.0, 1.0, 5))
    axis.set_zticks(np.linspace(0.0, 1.0, 5))
    axis.grid(True, alpha=0.14, color="#cbd5e1")
    legend = axis.legend(handles=legend_handles, frameon=True, loc="upper left")
    legend.get_frame().set_facecolor("white")
    legend.get_frame().set_edgecolor("#d1d5db")
    legend.get_frame().set_alpha(0.96)
    fig.tight_layout()

    if output_path is None:
        output_path = Path("cmorl_minicage/outputs/plots/objective_3d_comparison.png")
    output_path = Path(output_path)
    ensure_dir(output_path.parent)
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_pairwise_objective_panels(
    buffer_paths: Sequence[str | Path],
    labels: Sequence[str] | None = None,
    output_path: str | Path | None = None,
) -> Path:
    if not buffer_paths:
        raise ValueError("At least one solution_buffer.json path is required")
    plt = _import_matplotlib()

    resolved_paths = [Path(path) for path in buffer_paths]
    if labels is None:
        labels = [_label_from_path(path) for path in resolved_paths]
    if len(labels) != len(resolved_paths):
        raise ValueError("labels length must match buffer_paths length")

    payloads = [load_json(path) for path in resolved_paths]
    pareto_sets = [payload.get("pareto_front", []) for payload in payloads]
    if any(not pareto for pareto in pareto_sets):
        raise ValueError("Every buffer_path must contain a non-empty pareto_front")

    all_points = np.vstack([_objective_array(records) for records in pareto_sets])
    mins = np.min(all_points, axis=0)
    maxs = np.max(all_points, axis=0)
    spans = np.maximum(maxs - mins, 1e-6)
    margins = 0.06 * spans
    paper_colors = ["#4C78A8", "#F58518", "#54A24B", "#E45756", "#B279A2", "#9D755D"]

    pairs = [(0, 1), (0, 2), (1, 2)]
    fig, axes = plt.subplots(1, len(pairs), figsize=(17.8, 5.4))
    fig.patch.set_facecolor("white")

    legend_handles = []
    for method_idx, (label, pareto_records) in enumerate(zip(labels, pareto_sets)):
        pareto_points = _objective_array(pareto_records)
        color = paper_colors[method_idx % len(paper_colors)]
        style = _compact_method_style(label, "o")
        legend_handles.append(
            plt.Line2D(
                [0],
                [0],
                marker="o",
                color="none",
                markerfacecolor=color,
                markeredgecolor="#222222",
                markeredgewidth=0.9,
                markersize=9,
                linestyle="None",
                label=label,
            )
        )
        for axis, (x_idx, y_idx) in zip(axes, pairs):
            axis.scatter(
                pareto_points[:, x_idx],
                pareto_points[:, y_idx],
                s=max(style["size"] * 1.02, 118),
                color=color,
                alpha=0.95,
                edgecolor="#222222",
                linewidth=1.0,
                marker="o",
                zorder=4 + method_idx,
            )

    for axis, (x_idx, y_idx) in zip(axes, pairs):
        axis.set_title(f"{_objective_label(x_idx)} vs {_objective_label(y_idx)}", fontsize=14, pad=8)
        axis.set_xlabel(f"{_objective_label(x_idx)} Return")
        axis.set_ylabel(f"{_objective_label(y_idx)} Return")
        axis.set_xlim(mins[x_idx] - margins[x_idx], maxs[x_idx] + margins[x_idx])
        axis.set_ylim(mins[y_idx] - margins[y_idx], maxs[y_idx] + margins[y_idx])
        axis.grid(True, alpha=0.22, color="#d1d5db", linestyle="-", linewidth=0.9)
        axis.set_facecolor("#fafafa")
        for spine in axis.spines.values():
            spine.set_color("#444444")
            spine.set_linewidth(1.0)

    fig.suptitle("Pareto Scatter Overview", fontsize=22, y=0.975)
    legend = axes[0].legend(
        handles=legend_handles,
        loc="lower right",
        frameon=True,
        fancybox=True,
        framealpha=0.96,
        borderpad=0.6,
        labelspacing=0.35,
        handletextpad=0.6,
    )
    legend.get_frame().set_facecolor("white")
    legend.get_frame().set_edgecolor("#d1d5db")
    fig.subplots_adjust(left=0.055, right=0.99, top=0.84, bottom=0.11, wspace=0.16)

    if output_path is None:
        output_path = Path("cmorl_minicage/outputs/plots/pairwise_objective_panels.png")
    output_path = Path(output_path)
    ensure_dir(output_path.parent)
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output_path


def _latest_run_dir(experiment_dir: Path) -> Path:
    runs = sorted(
        [path for path in experiment_dir.iterdir() if path.is_dir() and path.name.startswith("run_")],
        key=lambda path: path.stat().st_mtime,
    )
    if not runs:
        raise ValueError(f"No run directories found under {experiment_dir}")
    return runs[-1]


def _load_metric_row(label: str, metrics_path: Path) -> dict:
    payload = load_json(metrics_path)
    metrics = payload["metrics"]
    assignment_summary = payload.get("assignment_summary", {})
    return {
        "label": label,
        "metrics_path": str(metrics_path),
        "hypervolume": metrics["hypervolume"],
        "expected_utility": metrics["expected_utility"],
        "sparsity": metrics["sparsity"],
        "num_pareto_records": metrics["num_pareto_records"],
        "coverage_ratio": assignment_summary.get("coverage_ratio", 0.0),
        "unique_assigned_policies": assignment_summary.get("unique_assigned_policies", 0),
    }


def _style_bar_annotations(axis, values: Sequence[float]) -> None:
    for idx, value in enumerate(values):
        axis.text(
            idx,
            value,
            f"{value:.2f}" if abs(value) < 10000 else f"{value:.1e}",
            ha="center",
            va="bottom",
            fontsize=7,
            rotation=90,
        )


def plot_all_ablation_summary(
    outputs_root: str | Path | None = None,
    output_path: str | Path | None = None,
) -> Path:
    plt = _import_matplotlib()
    if outputs_root is None:
        outputs_root = Path("cmorl_minicage/outputs")
    outputs_root = Path(outputs_root)
    repo_root = _repo_root_from_path(outputs_root)

    ablation_roots = {
        "conservative": outputs_root / "ablation" / "stage2_conservative",
        "balanced": outputs_root / "ablation" / "stage2_balanced",
        "relaxed": outputs_root / "ablation" / "stage2_relaxed",
        "beta_1005": outputs_root / "ablation" / "local_search" / "stage2_beta_1005",
        "beta_1020": outputs_root / "ablation" / "local_search" / "stage2_beta_1020",
        "steps_1024": outputs_root / "ablation" / "local_search" / "stage2_steps_1024",
        "steps_1536": outputs_root / "ablation" / "local_search" / "stage2_steps_1536",
        "tol_025": outputs_root / "ablation" / "local_search" / "stage2_tol_025",
        "tol_075": outputs_root / "ablation" / "local_search" / "stage2_tol_075",
    }

    rows = []
    stage1_baseline_path = repo_root / "cmorl_minicage" / "outputs" / "p1_stage1_check" / "run_29deaae7" / "metrics_p1_stage1.json"
    if stage1_baseline_path.exists():
        rows.append(_load_metric_row("stage1_base", stage1_baseline_path))
    for label, experiment_dir in ablation_roots.items():
        latest = _latest_run_dir(experiment_dir)
        metrics_path = latest / "metrics.json"
        rows.append(_load_metric_row(label, metrics_path))

    labels = [row["label"] for row in rows]
    x = np.arange(len(labels))
    display_labels = [label.replace("_", "\n") for label in labels]

    fig, axes = plt.subplots(2, 3, figsize=(18, 9.5))
    fig.suptitle("C-MORL MiniCAGE Ablation Summary", fontsize=16, y=0.98)
    metric_panels = [
        ("hypervolume", "Hypervolume", "#4c78a8"),
        ("expected_utility", "Expected Utility", "#54a24b"),
        ("sparsity", "Sparsity", "#f58518"),
        ("num_pareto_records", "Pareto Count", "#e45756"),
        ("coverage_ratio", "Coverage Ratio", "#72b7b2"),
        ("unique_assigned_policies", "Assigned Policy Variety", "#b279a2"),
    ]

    for axis, (metric_key, title, color) in zip(axes.flatten(), metric_panels):
        values = [row[metric_key] for row in rows]
        bars = axis.bar(x, values, color=color, alpha=0.92)
        best_idx = int(np.argmax(values)) if metric_key != "sparsity" else int(np.argmin(values))
        bars[best_idx].set_edgecolor("black")
        bars[best_idx].set_linewidth(1.4)
        axis.set_title(title)
        axis.set_xticks(x)
        axis.set_xticklabels(display_labels, rotation=0, fontsize=9)
        axis.grid(True, axis="y", alpha=0.22)
        _style_bar_annotations(axis, values)

    fig.tight_layout(rect=(0, 0, 1, 0.96))

    if output_path is None:
        output_path = outputs_root / "plots" / "paper_style_ablation_summary.png"
    output_path = Path(output_path)
    ensure_dir(output_path.parent)
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Visualize C-MORL MiniCAGE experiment results.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Plot artifacts for a single run directory.")
    run_parser.add_argument("--run-dir", required=True)
    run_parser.add_argument("--output-dir", default=None)

    compare_parser = subparsers.add_parser(
        "compare", help="Plot metric comparison across multiple metrics.json files."
    )
    compare_parser.add_argument("--metrics", nargs="+", required=True)
    compare_parser.add_argument("--labels", nargs="*", default=None)
    compare_parser.add_argument("--output-path", default=None)

    semantic_parser = subparsers.add_parser(
        "compare-semantics", help="Plot semantic metric comparison across multiple metrics files."
    )
    semantic_parser.add_argument("--metrics", nargs="+", required=True)
    semantic_parser.add_argument("--labels", nargs="*", default=None)
    semantic_parser.add_argument("--output-path", default=None)

    core_security_parser = subparsers.add_parser(
        "compare-core-security",
        help="Plot only Final Compromised Hosts, Final Critical Compromised, and Critical Impact Count.",
    )
    core_security_parser.add_argument("--metrics", nargs="+", required=True)
    core_security_parser.add_argument("--labels", nargs="*", default=None)
    core_security_parser.add_argument("--output-path", default=None)

    compact_parser = subparsers.add_parser(
        "compare-compact-objectives",
        help="Plot Security/Business as 2D scatter and encode Cost as color using solution buffers.",
    )
    compact_parser.add_argument("--buffers", nargs="+", required=True)
    compact_parser.add_argument("--labels", nargs="*", default=None)
    compact_parser.add_argument("--output-path", default=None)

    objective_3d_parser = subparsers.add_parser(
        "compare-3d-objectives",
        help="Plot normalized 3D Pareto scatter across multiple solution buffers.",
    )
    objective_3d_parser.add_argument("--buffers", nargs="+", required=True)
    objective_3d_parser.add_argument("--labels", nargs="*", default=None)
    objective_3d_parser.add_argument("--output-path", default=None)

    pairwise_parser = subparsers.add_parser(
        "compare-pairwise-objectives",
        help="Plot three pairwise objective panels across multiple solution buffers.",
    )
    pairwise_parser.add_argument("--buffers", nargs="+", required=True)
    pairwise_parser.add_argument("--labels", nargs="*", default=None)
    pairwise_parser.add_argument("--output-path", default=None)

    ablation_parser = subparsers.add_parser(
        "all-ablation", help="Generate a paper-style summary figure for all ablation experiments."
    )
    ablation_parser.add_argument("--outputs-root", default="cmorl_minicage/outputs")
    ablation_parser.add_argument("--output-path", default=None)

    args = parser.parse_args()

    if args.command == "run":
        outputs = plot_run(args.run_dir, args.output_dir)
        for path in outputs:
            print(path)
        return

    if args.command == "compare":
        output_path = plot_metrics_comparison(args.metrics, args.labels, args.output_path)
        print(output_path)
        return

    if args.command == "compare-semantics":
        output_path = plot_semantic_comparison(args.metrics, args.labels, args.output_path)
        print(output_path)
        return

    if args.command == "compare-core-security":
        output_path = plot_core_security_comparison(args.metrics, args.labels, args.output_path)
        print(output_path)
        return

    if args.command == "compare-compact-objectives":
        output_path = plot_compact_objective_map(args.buffers, args.labels, args.output_path)
        print(output_path)
        return

    if args.command == "compare-3d-objectives":
        output_path = plot_objective_3d_comparison(args.buffers, args.labels, args.output_path)
        print(output_path)
        return

    if args.command == "compare-pairwise-objectives":
        output_path = plot_pairwise_objective_panels(args.buffers, args.labels, args.output_path)
        print(output_path)
        return

    output_path = plot_all_ablation_summary(args.outputs_root, args.output_path)
    print(output_path)


if __name__ == "__main__":
    main()
