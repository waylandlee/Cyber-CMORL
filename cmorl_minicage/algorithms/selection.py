from __future__ import annotations

from typing import Sequence

import numpy as np


def _objective_array(records: Sequence[dict]) -> np.ndarray:
    return np.asarray([record["objective_vector"] for record in records], dtype=np.float32)


def nondominated_filter(records: Sequence[dict]) -> list[dict]:
    if not records:
        return []
    points = _objective_array(records)
    keep = np.ones(len(records), dtype=bool)
    for i in range(len(records)):
        if not keep[i]:
            continue
        for j in range(len(records)):
            if i == j:
                continue
            dominates = np.all(points[j] >= points[i]) and np.any(points[j] > points[i])
            if dominates:
                keep[i] = False
                break
    return [dict(records[i]) for i in range(len(records)) if keep[i]]


def crowding_distance(records: Sequence[dict]) -> np.ndarray:
    if not records:
        return np.zeros(0, dtype=np.float32)
    points = _objective_array(records)
    num_points, num_objectives = points.shape
    if num_points <= 2:
        return np.full(num_points, np.inf, dtype=np.float32)

    distances = np.zeros(num_points, dtype=np.float32)
    for objective_idx in range(num_objectives):
        order = np.argsort(points[:, objective_idx])
        distances[order[0]] = np.inf
        distances[order[-1]] = np.inf
        min_value = points[order[0], objective_idx]
        max_value = points[order[-1], objective_idx]
        scale = max(max_value - min_value, 1e-8)
        for rank in range(1, num_points - 1):
            left = points[order[rank - 1], objective_idx]
            right = points[order[rank + 1], objective_idx]
            distances[order[rank]] += (right - left) / scale
    return distances


def select_top_n_by_crowding(records: Sequence[dict], top_n: int) -> list[dict]:
    pareto = nondominated_filter(records)
    if top_n <= 0 or not pareto:
        return []

    distances = crowding_distance(pareto)
    points = _objective_array(pareto)
    selected_indices: list[int] = []

    for objective_idx in range(points.shape[1]):
        extreme = int(np.argmax(points[:, objective_idx]))
        if extreme not in selected_indices:
            selected_indices.append(extreme)

    remaining = [index for index in range(len(pareto)) if index not in selected_indices]
    remaining.sort(key=lambda index: distances[index], reverse=True)
    for index in remaining:
        if len(selected_indices) >= top_n:
            break
        selected_indices.append(index)

    return [dict(pareto[index]) for index in selected_indices[:top_n]]
