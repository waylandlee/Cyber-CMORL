from __future__ import annotations

from typing import Sequence

import numpy as np

from cmorl_minicage.algorithms.selection import crowding_distance, nondominated_filter


def _objective_array(records: Sequence[dict]) -> np.ndarray:
    return np.asarray([record["objective_vector"] for record in records], dtype=np.float32)


def _normalize_nonnegative(values: np.ndarray) -> np.ndarray:
    if values.size == 0:
        return np.zeros(0, dtype=np.float32)
    values = np.asarray(values, dtype=np.float32)
    vmin = float(np.min(values))
    vmax = float(np.max(values))
    if np.isclose(vmax, vmin):
        return np.zeros_like(values, dtype=np.float32)
    return (values - vmin) / (vmax - vmin)


def _utility_matrix(
    records: Sequence[dict], preferences: Sequence[Sequence[float]]
) -> np.ndarray:
    if not records or not preferences:
        return np.zeros((len(records), len(preferences)), dtype=np.float32)
    points = _objective_array(records)
    weights = np.asarray(preferences, dtype=np.float32)
    return (points @ weights.T).astype(np.float32)


def compute_crowding_score(records: Sequence[dict]) -> np.ndarray:
    distances = crowding_distance(records)
    if distances.size == 0:
        return np.zeros(0, dtype=np.float32)
    scores = np.zeros_like(distances, dtype=np.float32)
    finite_mask = np.isfinite(distances)
    if np.any(finite_mask):
        scores[finite_mask] = _normalize_nonnegative(distances[finite_mask])
    scores[~finite_mask] = 1.0
    return scores


def compute_expansion_potential(records: Sequence[dict]) -> tuple[np.ndarray, np.ndarray]:
    if not records:
        return np.zeros(0, dtype=np.float32), np.zeros((0, 0), dtype=np.float32)
    points = _objective_array(records)
    point_max = points.max(axis=0)
    point_min = points.min(axis=0)
    point_range = np.maximum(point_max - point_min, 1.0)
    target_expansion = (point_max[None, :] - points) / point_range[None, :]
    expansion = np.max(target_expansion, axis=1)
    return expansion.astype(np.float32), target_expansion.astype(np.float32)


def compute_constraint_risk(records: Sequence[dict]) -> np.ndarray:
    if not records:
        return np.zeros(0, dtype=np.float32)
    points = _objective_array(records)
    point_min = points.min(axis=0)
    point_max = points.max(axis=0)
    point_range = np.maximum(point_max - point_min, 1.0)
    normalized = (points - point_min[None, :]) / point_range[None, :]
    risk = np.std(normalized, axis=1)
    return _normalize_nonnegative(risk).astype(np.float32)


def compute_utility_coverage_gain(
    records: Sequence[dict],
    preferences: Sequence[Sequence[float]],
    tolerance: float,
) -> np.ndarray:
    if not records or not preferences:
        return np.zeros(len(records), dtype=np.float32)
    utilities = _utility_matrix(records, preferences)
    best = np.max(utilities, axis=0, keepdims=True)
    covered = utilities >= (best - float(tolerance))
    coverage_gain = covered.mean(axis=1)
    return coverage_gain.astype(np.float32)


def _covered_preferences_mask(
    utilities: np.ndarray,
    tolerance: float,
    selected_indices: Sequence[int],
) -> np.ndarray:
    if utilities.size == 0:
        return np.zeros(0, dtype=bool)
    best = np.max(utilities, axis=0, keepdims=True)
    covered = utilities >= (best - float(tolerance))
    if not selected_indices:
        return np.zeros(covered.shape[1], dtype=bool)
    selected_mask = covered[np.asarray(selected_indices, dtype=np.int32)]
    return np.any(selected_mask, axis=0)


def compute_selection_components(
    records: Sequence[dict],
    preferences: Sequence[Sequence[float]],
    tolerance: float,
) -> dict[str, dict[str, float | list[float]]]:
    if not records:
        return {}
    crowding = compute_crowding_score(records)
    expansion, target_expansion = compute_expansion_potential(records)
    risk = compute_constraint_risk(records)
    coverage = compute_utility_coverage_gain(records, preferences, tolerance)

    components: dict[str, dict[str, float | list[float]]] = {}
    for index, record in enumerate(records):
        components[record["policy_id"]] = {
            "crowding_score": float(crowding[index]),
            "expansion_potential": float(expansion[index]),
            "target_expansion_by_objective": target_expansion[index].astype(np.float32).tolist(),
            "constraint_risk": float(risk[index]),
            "low_risk_score": float(1.0 - risk[index]),
            "utility_coverage_gain": float(coverage[index]),
        }
    return components


def compute_selection_score(
    component: dict[str, float | list[float]],
    weights: dict[str, float],
) -> float:
    return float(
        weights.get("crowding", 0.0) * float(component["crowding_score"])
        + weights.get("expansion", 0.0) * float(component["expansion_potential"])
        + weights.get("low_risk", 0.0) * float(component["low_risk_score"])
        + weights.get("coverage", 0.0) * float(component["utility_coverage_gain"])
        + weights.get("semantic_low_risk", 0.0)
        * float(component.get("semantic_low_risk_score", 0.0))
    )


def select_top_n_adaptive(
    records: Sequence[dict],
    top_n: int,
    preferences: Sequence[Sequence[float]],
    weights: dict[str, float],
    tolerance: float,
    *,
    coverage_mode: str = "static",
    keep_extremes: bool = True,
    pareto_only: bool = True,
    component_overrides: dict[str, dict[str, float | list[float] | dict[str, float]]] | None = None,
) -> tuple[list[dict], dict[str, float], dict[str, dict[str, float | list[float]]]]:
    candidates = (
        nondominated_filter(records) if pareto_only else [dict(record) for record in records]
    )
    if top_n <= 0 or not candidates:
        return [], {}, {}

    components = compute_selection_components(candidates, preferences, tolerance)
    component_overrides = component_overrides or {}
    for policy_id, override in component_overrides.items():
        if policy_id not in components:
            continue
        components[policy_id].update(dict(override))
    scores = {
        record["policy_id"]: compute_selection_score(components[record["policy_id"]], weights)
        for record in candidates
    }

    selected_indices: list[int] = []
    points = _objective_array(candidates)
    if keep_extremes and len(candidates) > 0:
        for objective_idx in range(points.shape[1]):
            extreme = int(np.argmax(points[:, objective_idx]))
            if extreme not in selected_indices:
                selected_indices.append(extreme)

    selected_ids = {candidates[index]["policy_id"] for index in selected_indices}
    if coverage_mode != "marginal":
        remaining = [record for record in candidates if record["policy_id"] not in selected_ids]
        remaining.sort(
            key=lambda record: (
                -scores[record["policy_id"]],
                -float(components[record["policy_id"]]["utility_coverage_gain"]),
                -float(components[record["policy_id"]]["crowding_score"]),
                record["policy_id"],
            )
        )

        for record in remaining:
            if len(selected_indices) >= top_n:
                break
            selected_indices.append(
                next(
                    i
                    for i, candidate in enumerate(candidates)
                    if candidate["policy_id"] == record["policy_id"]
                )
            )
    else:
        utilities = _utility_matrix(candidates, preferences)
        while len(selected_indices) < min(top_n, len(candidates)):
            covered_preferences = _covered_preferences_mask(
                utilities, tolerance, selected_indices
            )
            remaining_indices = [
                index for index in range(len(candidates)) if index not in selected_indices
            ]
            if not remaining_indices:
                break
            best_index = None
            best_key = None
            for index in remaining_indices:
                best = np.max(utilities, axis=0, keepdims=True)
                candidate_covered = utilities[index] >= (
                    best[0] - float(tolerance)
                )
                marginal_gain = float(
                    np.mean(candidate_covered & (~covered_preferences))
                )
                components[candidates[index]["policy_id"]]["utility_coverage_gain"] = marginal_gain
                scores[candidates[index]["policy_id"]] = compute_selection_score(
                    components[candidates[index]["policy_id"]], weights
                )
                key = (
                    -scores[candidates[index]["policy_id"]],
                    -marginal_gain,
                    -float(components[candidates[index]["policy_id"]]["crowding_score"]),
                    candidates[index]["policy_id"],
                )
                if best_key is None or key < best_key:
                    best_key = key
                    best_index = index
            if best_index is None:
                break
            selected_indices.append(best_index)

    selected = [dict(candidates[index]) for index in selected_indices[:top_n]]
    selected_scores = {record["policy_id"]: scores[record["policy_id"]] for record in selected}
    selected_components = {
        record["policy_id"]: dict(components[record["policy_id"]]) for record in selected
    }
    return selected, selected_scores, selected_components
