from __future__ import annotations

import argparse
import itertools
from pathlib import Path
from typing import Sequence

import numpy as np

from cmorl_minicage.algorithms.assignment import assign_policy
from cmorl_minicage.algorithms.selection import nondominated_filter
from cmorl_minicage.buffer import load_policy_buffer
from cmorl_minicage.config import DEFAULT_EVALUATE_CONFIG, load_evaluate_config
from cmorl_minicage.utils import save_json, simplex_grid


def _prepare_hv_points(points: np.ndarray, reference_point: Sequence[float]) -> np.ndarray:
    reference = np.asarray(reference_point, dtype=np.float32)
    pts = np.asarray(points, dtype=np.float32)
    if pts.size == 0:
        return np.zeros((0, len(reference)), dtype=np.float32)
    pts = pts[np.all(pts > reference, axis=1)]
    if len(pts) == 0:
        return np.zeros((0, len(reference)), dtype=np.float32)
    pts = np.unique(pts, axis=0)

    keep = np.ones(len(pts), dtype=bool)
    for i in range(len(pts)):
        if not keep[i]:
            continue
        for j in range(len(pts)):
            if i == j:
                continue
            dominates = np.all(pts[j] >= pts[i]) and np.any(pts[j] > pts[i])
            if dominates:
                keep[i] = False
                break
    return pts[keep]


def _hypervolume_exact(points: np.ndarray, reference_point: Sequence[float]) -> float:
    reference = np.asarray(reference_point, dtype=np.float32)
    pts = _prepare_hv_points(points, reference)
    if len(pts) == 0:
        return 0.0

    volume = 0.0
    indices = range(len(pts))
    for subset_size in range(1, len(pts) + 1):
        sign = 1.0 if subset_size % 2 == 1 else -1.0
        for subset in itertools.combinations(indices, subset_size):
            upper = np.min(pts[list(subset)], axis=0)
            edge_lengths = upper - reference
            if np.any(edge_lengths <= 0):
                continue
            volume += sign * float(np.prod(edge_lengths))
    return volume


def _hypervolume_monte_carlo(
    points: np.ndarray, reference_point: Sequence[float], num_samples: int
) -> float:
    reference = np.asarray(reference_point, dtype=np.float32)
    pts = _prepare_hv_points(points, reference)
    if len(pts) == 0:
        return 0.0

    upper_bound = np.max(pts, axis=0)
    edge_lengths = upper_bound - reference
    if np.any(edge_lengths <= 0):
        return 0.0

    rng = np.random.default_rng(0)
    samples = rng.uniform(reference, upper_bound, size=(num_samples, pts.shape[1]))
    dominated = np.any(np.all(pts[:, None, :] >= samples[None, :, :], axis=2), axis=0)
    box_volume = float(np.prod(edge_lengths))
    return box_volume * float(np.mean(dominated))


def hypervolume(
    points: np.ndarray,
    reference_point: Sequence[float],
    *,
    max_exact_points: int = 18,
    mc_samples: int = 50000,
) -> tuple[float, str]:
    pts = np.asarray(points, dtype=np.float32)
    if len(pts) <= max_exact_points:
        return _hypervolume_exact(pts, reference_point), "exact_inclusion_exclusion"
    return _hypervolume_monte_carlo(pts, reference_point, mc_samples), "monte_carlo"


def resolve_reference_point(
    points: np.ndarray,
    *,
    obj_dim: int,
    reference_strategy: str,
    reference_margin: float,
    reference_point: Sequence[float] | None,
) -> np.ndarray:
    strategy = reference_strategy.lower()
    if reference_point:
        explicit = np.asarray(reference_point, dtype=np.float32)
        if explicit.shape != (obj_dim,):
            raise ValueError(
                f"reference_point must have length {obj_dim}, got {explicit.shape}"
            )
        return explicit

    if len(points) == 0:
        return np.full(obj_dim, -reference_margin, dtype=np.float32)

    point_min = points.min(axis=0)
    point_range = np.maximum(points.max(axis=0) - point_min, 1.0)

    if strategy == "data_min_margin":
        return (point_min - reference_margin).astype(np.float32)
    if strategy == "data_min_range":
        return (point_min - (reference_margin * point_range)).astype(np.float32)
    raise ValueError(f"Unsupported reference strategy: {reference_strategy}")


def expected_utility(records: Sequence[dict], preferences: Sequence[Sequence[float]]) -> float:
    if not preferences:
        return 0.0
    utilities = []
    for preference in preferences:
        assigned = assign_policy(preference, records)
        utilities.append(float(assigned["utility"]))
    return float(np.mean(utilities))


def sparsity(records: Sequence[dict]) -> float:
    if len(records) <= 1:
        return 0.0
    points = np.asarray([record["objective_vector"] for record in records], dtype=np.float32)
    total = 0.0
    for objective_idx in range(points.shape[1]):
        ordered = np.sort(points[:, objective_idx])
        diffs = np.diff(ordered)
        total += float(np.sum(diffs**2))
    return total / max(len(records) - 1, 1)


def evaluate_policy_buffer(
    buffer_path: str | Path,
    preference_step: float | None = None,
    *,
    reference_strategy: str = "data_min_margin",
    reference_margin: float = 1.0,
    reference_point: Sequence[float] | None = None,
    hv_max_exact_points: int = 18,
    hv_mc_samples: int = 50000,
) -> dict:
    payload = load_policy_buffer(buffer_path)
    records = payload["records"]
    pareto_records = nondominated_filter(records)
    if not records:
        raise ValueError("buffer contains no records")

    obj_dim = len(records[0]["objective_vector"])
    if preference_step is None:
        if obj_dim == 2:
            preference_step = 0.01
        elif obj_dim in (3, 4):
            preference_step = 0.1
        elif obj_dim in (6, 9):
            preference_step = 0.5
        else:
            preference_step = 0.1

    preferences = simplex_grid(preference_step, obj_dim)
    points = np.asarray([record["objective_vector"] for record in pareto_records], dtype=np.float32)
    reference = resolve_reference_point(
        points,
        obj_dim=obj_dim,
        reference_strategy=reference_strategy,
        reference_margin=reference_margin,
        reference_point=reference_point,
    )

    assignments = [assign_policy(pref, pareto_records) for pref in preferences]
    assignment_counts: dict[str, int] = {}
    assignment_utility_sum: dict[str, float] = {}
    for assigned in assignments:
        policy_id = assigned["policy_id"]
        assignment_counts[policy_id] = assignment_counts.get(policy_id, 0) + 1
        assignment_utility_sum[policy_id] = assignment_utility_sum.get(policy_id, 0.0) + float(
            assigned["utility"]
        )

    hv_value, hv_method = hypervolume(
        points,
        reference,
        max_exact_points=hv_max_exact_points,
        mc_samples=hv_mc_samples,
    )
    assignment_summary = {
        "num_preferences": len(preferences),
        "unique_assigned_policies": len(assignment_counts),
        "coverage_ratio": (
            float(len(assignment_counts) / len(pareto_records)) if pareto_records else 0.0
        ),
        "max_assignment_count": max(assignment_counts.values(), default=0),
        "mean_assignment_count": (
            float(np.mean(list(assignment_counts.values()))) if assignment_counts else 0.0
        ),
        "mean_assigned_utility": (
            float(np.mean([entry["utility"] for entry in assignments])) if assignments else 0.0
        ),
        "per_policy_mean_utility": {
            policy_id: assignment_utility_sum[policy_id] / assignment_counts[policy_id]
            for policy_id in assignment_counts
        },
    }
    metrics = {
        "num_records": len(records),
        "num_pareto_records": len(pareto_records),
        "hypervolume": hv_value,
        "hypervolume_method": hv_method,
        "expected_utility": expected_utility(pareto_records, preferences),
        "sparsity": sparsity(pareto_records),
        "reference_point": reference.tolist(),
        "reference_strategy": reference_strategy,
        "reference_margin": reference_margin,
        "preference_step": preference_step,
        "obj_dim": obj_dim,
    }
    return {
        "schema_version": payload.get("schema_version"),
        "metadata": payload.get("metadata", {}),
        "metrics": metrics,
        "pareto_front": pareto_records,
        "assignments": assignments,
        "assignment_counts": assignment_counts,
        "assignment_summary": assignment_summary,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate C-MORL MiniCAGE policy buffer.")
    parser.add_argument("--config", default=str(DEFAULT_EVALUATE_CONFIG))
    parser.add_argument("--buffer-path", default=None)
    parser.add_argument("--preference-step", type=float, default=None)
    parser.add_argument("--output-path", default=None)
    args = parser.parse_args()

    config = load_evaluate_config(args.config)
    if args.buffer_path is not None:
        config.buffer_path = args.buffer_path
    if args.output_path is not None:
        config.output_path = args.output_path
    if args.preference_step is not None:
        config.preference_step = args.preference_step
    if not config.buffer_path:
        raise ValueError("buffer_path must be set via config file or --buffer-path")

    result = evaluate_policy_buffer(
        config.buffer_path,
        config.preference_step,
        reference_strategy=config.reference_strategy,
        reference_margin=config.reference_margin,
        reference_point=config.reference_point,
        hv_max_exact_points=config.hv_max_exact_points,
        hv_mc_samples=config.hv_mc_samples,
    )
    output_path = (
        Path(config.output_path)
        if config.output_path
        else Path(config.buffer_path).with_name("metrics.json")
    )
    save_json(output_path, result)
    print(f"Saved evaluation to {output_path}")


if __name__ == "__main__":
    main()
