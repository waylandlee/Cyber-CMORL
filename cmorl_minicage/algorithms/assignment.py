from __future__ import annotations

from typing import Sequence

import numpy as np


def assign_policy(preference: Sequence[float], policy_set: Sequence[dict]) -> dict:
    if not policy_set:
        raise ValueError("policy_set must not be empty")
    weights = np.asarray(preference, dtype=np.float32)
    best_record = None
    best_utility = -np.inf
    for record in policy_set:
        objectives = np.asarray(record["objective_vector"], dtype=np.float32)
        utility = float(np.dot(weights, objectives))
        if utility > best_utility:
            best_utility = utility
            best_record = record
    assert best_record is not None
    assigned = dict(best_record)
    assigned["preference"] = weights.tolist()
    assigned["utility"] = float(best_utility)
    return assigned
