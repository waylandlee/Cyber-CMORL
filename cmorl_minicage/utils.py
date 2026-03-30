from __future__ import annotations

import json
import math
import random
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import torch


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def ensure_dir(path: str | Path) -> Path:
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _json_default(value):
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    raise TypeError(f"Unsupported JSON value: {type(value)!r}")


def save_json(path: str | Path, payload) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False, default=_json_default)


def load_json(path: str | Path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def simplex_grid(step: float, dimensions: int) -> list[list[float]]:
    if dimensions <= 0:
        raise ValueError("dimensions must be positive")
    denominator = round(1.0 / step)
    if not math.isclose(step * denominator, 1.0, rel_tol=1e-9, abs_tol=1e-9):
        raise ValueError("step must divide 1.0 exactly for simplex_grid")

    points: list[list[float]] = []

    def recurse(prefix: list[int], remaining: int, dims_left: int) -> None:
        if dims_left == 1:
            point = prefix + [remaining]
            points.append([entry / denominator for entry in point])
            return
        for value in range(remaining + 1):
            recurse(prefix + [value], remaining - value, dims_left - 1)

    recurse([], denominator, dimensions)
    return points


def sample_preferences(
    *,
    num_policies: int,
    dimensions: int,
    strategy: str,
    seed: int,
    step: float = 0.5,
    dirichlet_alpha: float = 1.0,
) -> list[list[float]]:
    if num_policies <= 0:
        return []
    if dimensions <= 0:
        raise ValueError("dimensions must be positive")

    strategy = strategy.lower()
    if strategy == "grid":
        points = simplex_grid(step, dimensions)
        if len(points) < num_policies:
            raise ValueError("Not enough simplex-grid preferences for requested num_policies")
        return points[:num_policies]

    rng = np.random.default_rng(seed)
    alpha = np.full(dimensions, dirichlet_alpha, dtype=np.float64)

    if strategy == "dirichlet":
        return rng.dirichlet(alpha, size=num_policies).astype(np.float32).tolist()

    if strategy == "dirichlet_extremes":
        preferences: list[list[float]] = []
        for index in range(min(num_policies, dimensions)):
            extreme = np.zeros(dimensions, dtype=np.float32)
            extreme[index] = 1.0
            preferences.append(extreme.tolist())
        remaining = num_policies - len(preferences)
        if remaining > 0:
            sampled = rng.dirichlet(alpha, size=remaining).astype(np.float32).tolist()
            preferences.extend(sampled)
        return preferences

    raise ValueError(f"Unsupported preference sampling strategy: {strategy}")


def pareto_payload(records: Sequence[dict]) -> list[dict]:
    serialised: list[dict] = []
    for record in records:
        entry = dict(record)
        vector = np.asarray(entry["objective_vector"], dtype=np.float32)
        entry["objective_vector"] = vector.tolist()
        serialised.append(entry)
    return serialised


def preference_payload(preferences: Iterable[Sequence[float]]) -> list[list[float]]:
    return [list(map(float, preference)) for preference in preferences]
