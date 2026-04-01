from __future__ import annotations

import argparse
import copy
import csv
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from cmorl_minicage.buffer import load_policy_buffer
from cmorl_minicage.config import (
    DEFAULT_EVALUATE_CONFIG,
    load_evaluate_config,
    load_stage1_config,
    load_stage2_config,
    save_config_template,
)
from cmorl_minicage.evaluate import evaluate_policy_buffer, resolve_reference_point
from cmorl_minicage.train_stage1 import train_stage1
from cmorl_minicage.train_stage2 import train_stage2
from cmorl_minicage.utils import ensure_dir, save_json


SUMMARY_METRICS = [
    "hypervolume",
    "expected_utility",
    "sparsity",
    "num_pareto_records",
    "coverage_ratio",
    "unique_assigned_policies",
    "final_compromised_hosts",
    "final_critical_compromised_hosts",
    "critical_impact_count",
    "recovered_hosts",
    "analyse_count",
    "remove_count",
    "restore_count",
    "high_disruption_action_rate",
]

HIGHER_IS_BETTER = {
    "hypervolume",
    "expected_utility",
    "num_pareto_records",
    "coverage_ratio",
    "unique_assigned_policies",
    "recovered_hosts",
    "analyse_count",
    "remove_count",
    "restore_count",
}


def _extract_summary_row(result: dict[str, Any]) -> dict[str, float]:
    metrics = result.get("metrics", {})
    assignment_summary = result.get("assignment_summary", {})
    semantic_metrics = result.get("semantic_metrics", {})
    return {
        "hypervolume": float(metrics["hypervolume"]),
        "expected_utility": float(metrics["expected_utility"]),
        "sparsity": float(metrics["sparsity"]),
        "num_pareto_records": float(metrics["num_pareto_records"]),
        "coverage_ratio": float(assignment_summary.get("coverage_ratio", 0.0)),
        "unique_assigned_policies": float(assignment_summary.get("unique_assigned_policies", 0.0)),
        "final_compromised_hosts": float(semantic_metrics.get("final_compromised_hosts", 0.0)),
        "final_critical_compromised_hosts": float(
            semantic_metrics.get("final_critical_compromised_hosts", 0.0)
        ),
        "critical_impact_count": float(semantic_metrics.get("critical_impact_count", 0.0)),
        "recovered_hosts": float(semantic_metrics.get("recovered_hosts", 0.0)),
        "analyse_count": float(semantic_metrics.get("analyse_count", 0.0)),
        "remove_count": float(semantic_metrics.get("remove_count", 0.0)),
        "restore_count": float(semantic_metrics.get("restore_count", 0.0)),
        "high_disruption_action_rate": float(
            semantic_metrics.get("high_disruption_action_rate", 0.0)
        ),
    }


def _combine_reference_point(
    buffer_paths: Sequence[str | Path],
    *,
    reference_strategy: str,
    reference_margin: float,
    reference_point: Sequence[float] | None,
) -> list[float]:
    all_points: list[list[float]] = []
    obj_dim = 0
    for buffer_path in buffer_paths:
        payload = load_policy_buffer(buffer_path)
        pareto_front = payload.get("pareto_front", [])
        if not pareto_front:
            continue
        obj_dim = len(pareto_front[0]["objective_vector"])
        all_points.extend(record["objective_vector"] for record in pareto_front)
    if not all_points:
        raise ValueError("Could not build shared reference point from empty Pareto fronts")
    points = np.asarray(all_points, dtype=np.float32)
    resolved = resolve_reference_point(
        points,
        obj_dim=obj_dim,
        reference_strategy=reference_strategy,
        reference_margin=reference_margin,
        reference_point=reference_point,
    )
    return resolved.tolist()


def _evaluate_with_reference(
    *,
    buffer_path: str | Path,
    evaluate_config,
    reference_point: Sequence[float],
) -> dict[str, Any]:
    return evaluate_policy_buffer(
        buffer_path,
        evaluate_config.preference_step,
        reference_strategy=evaluate_config.reference_strategy,
        reference_margin=evaluate_config.reference_margin,
        reference_point=reference_point,
        hv_max_exact_points=evaluate_config.hv_max_exact_points,
        hv_mc_samples=evaluate_config.hv_mc_samples,
    )


def _aggregate_rows(rows: Sequence[dict[str, float]]) -> dict[str, dict[str, float]]:
    if not rows:
        return {}
    aggregate: dict[str, dict[str, float]] = {}
    for metric_name in SUMMARY_METRICS:
        values = np.asarray([row[metric_name] for row in rows], dtype=np.float64)
        aggregate[metric_name] = {
            "mean": float(np.mean(values)),
            "std": float(np.std(values)),
            "min": float(np.min(values)),
            "max": float(np.max(values)),
        }
    return aggregate


def _delta_row(stage1_row: dict[str, float], stage2_row: dict[str, float]) -> dict[str, float]:
    return {
        metric_name: float(stage2_row[metric_name] - stage1_row[metric_name])
        for metric_name in SUMMARY_METRICS
    }


def _win_counts(stage1_rows: Sequence[dict[str, float]], stage2_rows: Sequence[dict[str, float]]) -> dict[str, dict[str, int]]:
    wins: dict[str, dict[str, int]] = {}
    for metric_name in SUMMARY_METRICS:
        stage2_better = 0
        stage1_better = 0
        ties = 0
        for stage1_row, stage2_row in zip(stage1_rows, stage2_rows):
            left = stage1_row[metric_name]
            right = stage2_row[metric_name]
            if np.isclose(left, right):
                ties += 1
                continue
            if metric_name in HIGHER_IS_BETTER:
                if right > left:
                    stage2_better += 1
                else:
                    stage1_better += 1
            else:
                if right < left:
                    stage2_better += 1
                else:
                    stage1_better += 1
        wins[metric_name] = {
            "stage2_better": stage2_better,
            "stage1_better": stage1_better,
            "ties": ties,
        }
    return wins


def _write_csv(
    path: str | Path,
    *,
    seeds: Sequence[int],
    stage1_rows: Sequence[dict[str, float]],
    stage2_rows: Sequence[dict[str, float]],
    delta_rows: Sequence[dict[str, float]],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["seed"]
    for prefix in ("stage1", "stage2", "delta"):
        fieldnames.extend(f"{prefix}_{metric_name}" for metric_name in SUMMARY_METRICS)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for seed, stage1_row, stage2_row, delta_row in zip(seeds, stage1_rows, stage2_rows, delta_rows):
            row = {"seed": int(seed)}
            row.update({f"stage1_{key}": value for key, value in stage1_row.items()})
            row.update({f"stage2_{key}": value for key, value in stage2_row.items()})
            row.update({f"delta_{key}": value for key, value in delta_row.items()})
            writer.writerow(row)


def _prepare_stage1_config(base_config, *, seed: int, output_dir: Path):
    config = copy.deepcopy(base_config)
    config.seed = int(seed)
    config.env.seed = int(seed)
    config.output_dir = str(output_dir)
    return config


def _prepare_stage2_config(base_config, *, seed: int, output_dir: Path, stage1_buffer: str | Path):
    config = copy.deepcopy(base_config)
    config.seed = int(seed)
    config.env.seed = int(seed)
    config.output_dir = str(output_dir)
    config.stage1_buffer = str(stage1_buffer)
    return config


def run_multiseed_validation(
    *,
    stage1_config_path: str | Path,
    stage2_config_path: str | Path,
    evaluate_config_path: str | Path,
    seeds: Sequence[int],
    output_dir: str | Path,
    skip_existing: bool = False,
) -> Path:
    if skip_existing:
        raise ValueError("skip_existing is not implemented yet")
    stage1_base = load_stage1_config(stage1_config_path)
    stage2_base = load_stage2_config(stage2_config_path)
    evaluate_config = load_evaluate_config(evaluate_config_path)
    root_dir = ensure_dir(output_dir)

    stage1_rows: list[dict[str, float]] = []
    stage2_rows: list[dict[str, float]] = []
    delta_rows: list[dict[str, float]] = []
    per_seed_results: list[dict[str, Any]] = []

    for seed in seeds:
        seed_dir = ensure_dir(root_dir / f"seed_{int(seed):04d}")
        compare_dir = ensure_dir(seed_dir / "compare")
        final_summary_path = seed_dir / "seed_summary.json"

        stage1_config = _prepare_stage1_config(
            stage1_base,
            seed=int(seed),
            output_dir=seed_dir / "stage1",
        )
        stage2_config = _prepare_stage2_config(
            stage2_base,
            seed=int(seed),
            output_dir=seed_dir / "stage2",
            stage1_buffer="",
        )
        save_config_template(seed_dir / "stage1_config.yaml", stage1_config)
        stage1_buffer = train_stage1(stage1_config)

        stage2_config.stage1_buffer = str(stage1_buffer)
        save_config_template(seed_dir / "stage2_config.yaml", stage2_config)
        stage2_buffer = train_stage2(stage2_config)

        reference_point = _combine_reference_point(
            [stage1_buffer, stage2_buffer],
            reference_strategy=evaluate_config.reference_strategy,
            reference_margin=evaluate_config.reference_margin,
            reference_point=evaluate_config.reference_point,
        )
        stage1_result = _evaluate_with_reference(
            buffer_path=stage1_buffer,
            evaluate_config=evaluate_config,
            reference_point=reference_point,
        )
        stage2_result = _evaluate_with_reference(
            buffer_path=stage2_buffer,
            evaluate_config=evaluate_config,
            reference_point=reference_point,
        )
        save_json(compare_dir / "stage1_metrics_shared_ref.json", stage1_result)
        save_json(compare_dir / "stage2_metrics_shared_ref.json", stage2_result)

        stage1_row = _extract_summary_row(stage1_result)
        stage2_row = _extract_summary_row(stage2_result)
        delta = _delta_row(stage1_row, stage2_row)
        stage1_rows.append(stage1_row)
        stage2_rows.append(stage2_row)
        delta_rows.append(delta)

        seed_summary = {
            "seed": int(seed),
            "reference_point": reference_point,
            "stage1_buffer": str(stage1_buffer),
            "stage2_buffer": str(stage2_buffer),
            "stage1": stage1_row,
            "stage2": stage2_row,
            "delta_stage2_minus_stage1": delta,
        }
        save_json(final_summary_path, seed_summary)
        per_seed_results.append(seed_summary)

    summary = {
        "stage1_config": str(Path(stage1_config_path)),
        "stage2_config": str(Path(stage2_config_path)),
        "evaluate_config": str(Path(evaluate_config_path)),
        "seeds": [int(seed) for seed in seeds],
        "num_seeds": len(seeds),
        "stage1_aggregate": _aggregate_rows(stage1_rows),
        "stage2_aggregate": _aggregate_rows(stage2_rows),
        "delta_stage2_minus_stage1_aggregate": _aggregate_rows(delta_rows),
        "win_counts": _win_counts(stage1_rows, stage2_rows),
        "per_seed": per_seed_results,
    }
    save_json(root_dir / "multiseed_summary.json", summary)
    _write_csv(
        root_dir / "multiseed_summary.csv",
        seeds=seeds,
        stage1_rows=stage1_rows,
        stage2_rows=stage2_rows,
        delta_rows=delta_rows,
    )
    return root_dir / "multiseed_summary.json"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run multi-seed Stage-1/Stage-2 validation and aggregate shared-reference metrics."
    )
    parser.add_argument("--stage1-config", required=True)
    parser.add_argument("--stage2-config", required=True)
    parser.add_argument("--evaluate-config", default=str(DEFAULT_EVALUATE_CONFIG))
    parser.add_argument("--seeds", nargs="+", type=int, required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Reserved for future resume support. Currently unsupported.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if args.skip_existing:
        raise ValueError("--skip-existing is not implemented yet")
    summary_path = run_multiseed_validation(
        stage1_config_path=args.stage1_config,
        stage2_config_path=args.stage2_config,
        evaluate_config_path=args.evaluate_config,
        seeds=args.seeds,
        output_dir=args.output_dir,
        skip_existing=args.skip_existing,
    )
    print(summary_path)


if __name__ == "__main__":
    main()
