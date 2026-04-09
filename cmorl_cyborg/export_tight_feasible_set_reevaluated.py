from __future__ import annotations

import argparse
import csv
import json
import math
import os
import time
from datetime import datetime
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-cmorl-cyborg")

import cmorl_cyborg.evaluate_constraints as _cyborg_evaluate_constraints  # noqa: F401
from cmorl_minicage.buffer import load_policy_buffer
from cmorl_minicage.evaluate_constraints import (
    _evaluate_actor_critic_record,
    _resolve_path,
)


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


def _timestamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _load_json(path: str | Path) -> Any:
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


def _import_matplotlib():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def _aggregated_root() -> Path:
    return (
        Path(__file__).resolve().parent
        / "outputs"
        / "fair_compare_eval"
        / "aggregated"
    )


def _tight_eval_root() -> Path:
    return (
        Path(__file__).resolve().parent
        / "outputs"
        / "fair_compare_eval"
        / "tight"
    )


def _seed_summary_root() -> Path:
    return (
        Path(__file__).resolve().parent
        / "outputs"
        / "fair_compare_eval"
        / "reevaluated_tight_feasible_set_summary"
    )


def _runner_root() -> Path:
    return (
        Path(__file__).resolve().parent
        / "outputs"
        / "fair_compare_eval"
        / "reevaluated_tight_runner"
    )


def _workspace_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_checkpoint_path(buffer_path: Path, raw_path: str | Path | None) -> Path | None:
    if raw_path is None:
        return None
    first = _resolve_path(buffer_path, raw_path)
    if first.exists():
        return first
    raw = Path(raw_path)
    if raw.is_absolute():
        return first
    fallback = (_workspace_root() / raw).resolve()
    if fallback.exists():
        return fallback
    return first


class ReevaluationLogger:
    def __init__(self, *, total_steps: int) -> None:
        self.total_steps = max(int(total_steps), 1)
        self.completed_steps = 0
        self.output_dir = _runner_root()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.output_dir / "runner.log"
        self.status_path = self.output_dir / "status.json"
        self.current_step: str | None = None
        self.last_error: str | None = None
        self._append_log("RUNNER START")
        self._write_status("START", None)

    def _append_log(self, message: str) -> None:
        line = f"[{_timestamp()}] {message}"
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")

    def _write_status(self, status: str, current_step: str | None) -> None:
        _save_json(
            self.status_path,
            {
                "status": status,
                "updated_at": _timestamp(),
                "current_step": current_step,
                "completed_steps": self.completed_steps,
                "total_steps": self.total_steps,
                "last_error": self.last_error,
                "log_path": str(self.log_path.resolve()),
            },
        )

    def start(self, label: str) -> None:
        self.current_step = label
        self._append_log(f"START {label}")
        self._write_status("RUN", label)

    def done(self, label: str) -> None:
        self.completed_steps += 1
        self.current_step = None
        self._append_log(f"DONE {label}")
        self._write_status("RUN", None)

    def fail(self, label: str, exc: BaseException) -> None:
        self.last_error = str(exc)
        self._append_log(f"FAIL {label}: {self.last_error}")
        self._write_status("FAIL", label)

    def finalize(self) -> None:
        self._append_log("RUNNER COMPLETE")
        self._write_status("COMPLETE", None)


def _reevaluate_candidate(
    *,
    buffer_path: Path,
    metadata: dict[str, Any],
    record: dict[str, Any],
    thresholds: dict[str, float],
    eval_episodes: int,
) -> dict[str, Any]:
    baseline_kind = record.get("notes", {}).get("baseline_kind")
    checkpoint_path = _resolve_checkpoint_path(buffer_path, record.get("checkpoint_path"))
    metrics = _evaluate_actor_critic_record(
        checkpoint_path,
        metadata,
        thresholds,
        eval_episodes=eval_episodes,
        baseline_kind=baseline_kind,
    )
    business_return = float(metrics["business_return"])
    cost_return = float(metrics["cost_return"])
    margin = min(
        business_return - float(thresholds["d_business"]),
        cost_return - float(thresholds["d_cost"]),
    )
    return {
        "policy_id": str(record.get("policy_id", "")),
        "cached_objective_vector": list(record.get("objective_vector", [])),
        "reevaluated_security_return": float(metrics["security_return"]),
        "reevaluated_business_return": business_return,
        "reevaluated_cost_return": cost_return,
        "reevaluated_feasible_rate": float(metrics["feasible_rate"]),
        "reevaluated_mean_violation": float(metrics["mean_violation"]),
        "reevaluated_final_critical_compromised_hosts": float(
            metrics["final_critical_compromised_hosts"]
        ),
        "is_reevaluated_feasible": bool(
            business_return >= float(thresholds["d_business"])
            and cost_return >= float(thresholds["d_cost"])
        ),
        "reevaluated_margin": float(margin),
    }


def _seed_summary(
    *,
    method_name: str,
    constraint_metrics_path: Path,
    eval_episodes: int,
    logger: ReevaluationLogger,
) -> dict[str, Any]:
    constraint_payload = _load_json(constraint_metrics_path)
    thresholds = dict(constraint_payload["thresholds"])
    buffer_path = Path(str(constraint_payload["input_path"])).resolve()
    buffer_payload = load_policy_buffer(buffer_path)
    metadata = dict(buffer_payload.get("metadata", {}))
    pareto_front = list(buffer_payload.get("pareto_front", []))

    candidate_rows: list[dict[str, Any]] = []
    for record in pareto_front:
        label = (
            f"{method_name}:{constraint_metrics_path.parent.name}:"
            f"{record.get('policy_id', 'unknown')}"
        )
        logger.start(label)
        candidate_rows.append(
            _reevaluate_candidate(
                buffer_path=buffer_path,
                metadata=metadata,
                record=record,
                thresholds=thresholds,
                eval_episodes=eval_episodes,
            )
        )
        logger.done(label)

    feasible_rows = [row for row in candidate_rows if row["is_reevaluated_feasible"]]
    sorted_rows = sorted(candidate_rows, key=lambda row: row["reevaluated_margin"], reverse=True)

    seed_value = int(constraint_metrics_path.parent.name.split("_")[-1])
    return {
        "method_name": method_name,
        "display_name": DISPLAY_NAMES.get(method_name, method_name),
        "seed": seed_value,
        "seed_label": constraint_metrics_path.parent.name,
        "eval_episodes": int(eval_episodes),
        "constraint_metrics_path": str(constraint_metrics_path.resolve()),
        "buffer_path": str(buffer_path),
        "tight_thresholds": thresholds,
        "pareto_candidate_count": len(candidate_rows),
        "reevaluated_feasible_candidate_count": len(feasible_rows),
        "reevaluated_feasible_pareto_ratio": (
            float(len(feasible_rows) / len(candidate_rows)) if candidate_rows else 0.0
        ),
        "best_reevaluated_feasible_security_return": (
            max(float(row["reevaluated_security_return"]) for row in feasible_rows)
            if feasible_rows
            else None
        ),
        "closest_candidate_policy_id": (
            str(sorted_rows[0]["policy_id"]) if sorted_rows else None
        ),
        "closest_candidate_margin": (
            float(sorted_rows[0]["reevaluated_margin"]) if sorted_rows else None
        ),
        "closest_candidate_security_return": (
            float(sorted_rows[0]["reevaluated_security_return"]) if sorted_rows else None
        ),
        "closest_candidate_business_return": (
            float(sorted_rows[0]["reevaluated_business_return"]) if sorted_rows else None
        ),
        "closest_candidate_cost_return": (
            float(sorted_rows[0]["reevaluated_cost_return"]) if sorted_rows else None
        ),
        "candidate_rows": candidate_rows,
    }


def _aggregate_method_rows(method_name: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    feasible_counts = [float(row["reevaluated_feasible_candidate_count"]) for row in rows]
    feasible_ratios = [float(row["reevaluated_feasible_pareto_ratio"]) for row in rows]
    best_security_values = [
        float(row["best_reevaluated_feasible_security_return"])
        for row in rows
        if row["best_reevaluated_feasible_security_return"] is not None
    ]
    closest_margins = [
        float(row["closest_candidate_margin"])
        for row in rows
        if row["closest_candidate_margin"] is not None
    ]

    count_mean, count_std = _mean_std(feasible_counts)
    ratio_mean, ratio_std = _mean_std(feasible_ratios)
    margin_mean, margin_std = _mean_std(closest_margins)
    if best_security_values:
        best_sec_mean, best_sec_std = _mean_std(best_security_values)
    else:
        best_sec_mean, best_sec_std = math.nan, math.nan

    return {
        "method_name": method_name,
        "display_name": DISPLAY_NAMES.get(method_name, method_name),
        "num_runs": len(rows),
        "reevaluated_feasible_candidate_count": count_mean,
        "reevaluated_feasible_candidate_count_std": count_std,
        "reevaluated_feasible_pareto_ratio": ratio_mean,
        "reevaluated_feasible_pareto_ratio_std": ratio_std,
        "best_reevaluated_feasible_security_return": best_sec_mean,
        "best_reevaluated_feasible_security_return_std": best_sec_std,
        "num_runs_with_reevaluated_feasible_candidate": sum(
            1 for row in rows if int(row["reevaluated_feasible_candidate_count"]) > 0
        ),
        "closest_candidate_margin": margin_mean,
        "closest_candidate_margin_std": margin_std,
        "source_seed_summaries": [
            str((_seed_summary_root() / method_name / f"seed_{int(row['seed']):04d}.json").resolve())
            for row in rows
        ],
    }


def _write_aggregate_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "method_name",
        "display_name",
        "num_runs",
        "num_runs_with_reevaluated_feasible_candidate",
        "reevaluated_feasible_candidate_count",
        "reevaluated_feasible_candidate_count_std",
        "reevaluated_feasible_pareto_ratio",
        "reevaluated_feasible_pareto_ratio_std",
        "best_reevaluated_feasible_security_return",
        "best_reevaluated_feasible_security_return_std",
        "closest_candidate_margin",
        "closest_candidate_margin_std",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fieldnames})


def _plot_reevaluated_tight_feasible_set(
    aggregate_rows: list[dict[str, Any]],
    output_path: Path,
) -> None:
    plt = _import_matplotlib()
    labels = [row["display_name"] for row in aggregate_rows]
    methods = [row["method_name"] for row in aggregate_rows]
    x = list(range(len(aggregate_rows)))
    colors = [COLORS.get(method, "#4c78a8") for method in methods]

    fig, axes = plt.subplots(1, 3, figsize=(17, 4.8))
    fig.suptitle("Reevaluated Tight Feasible Set Quality", fontsize=15, y=1.02)

    count_means = [row["reevaluated_feasible_candidate_count"] for row in aggregate_rows]
    count_stds = [row["reevaluated_feasible_candidate_count_std"] for row in aggregate_rows]
    axes[0].bar(x, count_means, yerr=count_stds, color=colors, alpha=0.9, capsize=4)
    axes[0].set_title("Reevaluated Feasible Candidate Count")
    axes[0].set_ylabel("Count")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(labels, rotation=12, ha="right")
    axes[0].grid(True, axis="y", alpha=0.22)

    ratio_means = [row["reevaluated_feasible_pareto_ratio"] for row in aggregate_rows]
    ratio_stds = [row["reevaluated_feasible_pareto_ratio_std"] for row in aggregate_rows]
    axes[1].bar(x, ratio_means, yerr=ratio_stds, color=colors, alpha=0.9, capsize=4)
    axes[1].set_title("Reevaluated Feasible Pareto Ratio")
    axes[1].set_ylabel("Ratio")
    axes[1].set_ylim(0.0, max(0.25, max(ratio_means + ratio_stds) * 1.25))
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(labels, rotation=12, ha="right")
    axes[1].grid(True, axis="y", alpha=0.22)

    best_means = [row["best_reevaluated_feasible_security_return"] for row in aggregate_rows]
    best_stds = [row["best_reevaluated_feasible_security_return_std"] for row in aggregate_rows]
    axes[2].set_title("Best Reevaluated Feasible Security")
    axes[2].set_ylabel("Security Return")
    axes[2].set_xticks(x)
    axes[2].set_xticklabels(labels, rotation=12, ha="right")
    axes[2].grid(True, axis="y", alpha=0.22)
    for idx, mean_value in enumerate(best_means):
        if isinstance(mean_value, float) and math.isnan(mean_value):
            axes[2].text(idx, 0.5, "none", ha="center", va="center", color="#b22222")
            continue
        axes[2].bar(
            idx,
            mean_value,
            yerr=best_stds[idx],
            color=colors[idx],
            alpha=0.9,
            capsize=4,
        )

    fig.text(
        0.5,
        -0.02,
        "Thresholds use reevaluated candidate rollout means under tight protocol: business >= -125 and cost >= -22.",
        ha="center",
        fontsize=10,
        color="#444444",
    )
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def export_tight_feasible_set_reevaluated(
    *,
    eval_episodes: int = 3,
) -> dict[str, str]:
    seed_metric_paths: list[tuple[str, Path]] = []
    for method_name in METHOD_ORDER:
        method_root = _tight_eval_root() / method_name
        for metrics_path in sorted(method_root.glob("seed_*/constraint_metrics.json")):
            seed_metric_paths.append((method_name, metrics_path))

    total_steps = 0
    for _, metrics_path in seed_metric_paths:
        payload = _load_json(metrics_path)
        buffer_payload = load_policy_buffer(payload["input_path"])
        total_steps += len(buffer_payload.get("pareto_front", []))

    logger = ReevaluationLogger(total_steps=total_steps)
    seed_summary_root = _seed_summary_root()
    aggregate_rows: list[dict[str, Any]] = []
    method_seed_rows: dict[str, list[dict[str, Any]]] = {method_name: [] for method_name in METHOD_ORDER}

    try:
        for method_name, metrics_path in seed_metric_paths:
            summary = _seed_summary(
                method_name=method_name,
                constraint_metrics_path=metrics_path,
                eval_episodes=eval_episodes,
                logger=logger,
            )
            out_path = seed_summary_root / method_name / f"seed_{int(summary['seed']):04d}.json"
            _save_json(out_path, summary)
            method_seed_rows[method_name].append(summary)

        for method_name in METHOD_ORDER:
            rows = method_seed_rows.get(method_name, [])
            if rows:
                aggregate_rows.append(_aggregate_method_rows(method_name, rows))
        logger.finalize()
    except BaseException as exc:
        logger.fail(logger.current_step or "reevaluated_tight", exc)
        raise

    aggregate_dir = _aggregated_root()
    csv_path = aggregate_dir / "reevaluated_tight_feasible_set_summary.csv"
    json_path = aggregate_dir / "reevaluated_tight_feasible_set_summary.json"
    figure_path = aggregate_dir / "reevaluated_tight_feasible_set_quality.png"

    _write_aggregate_csv(csv_path, aggregate_rows)
    _save_json(
        json_path,
        {
            "methods": aggregate_rows,
            "eval_episodes": int(eval_episodes),
            "thresholds": _load_json(
                Path(__file__).resolve().parent
                / "outputs"
                / "fair_compare_eval"
                / "thresholds_tight.json"
            ),
        },
    )
    _plot_reevaluated_tight_feasible_set(aggregate_rows, figure_path)
    return {
        "aggregate_csv": str(csv_path),
        "aggregate_json": str(json_path),
        "figure": str(figure_path),
        "seed_summary_root": str(seed_summary_root),
        "runner_log": str(logger.log_path),
        "runner_status": str(logger.status_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Reevaluate every Pareto candidate under the tight protocol and "
            "export a reevaluated tight feasible-set figure."
        )
    )
    parser.add_argument("--eval-episodes", type=int, default=3)
    args = parser.parse_args()
    outputs = export_tight_feasible_set_reevaluated(eval_episodes=int(args.eval_episodes))
    for key, value in outputs.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
