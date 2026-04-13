from __future__ import annotations

from typing import Sequence

import numpy as np


def _metric(record: dict, *names: str, default: float = 0.0) -> float:
    for name in names:
        value = record.get(name)
        if value is not None:
            return float(value)
    return float(default)


def _normalise_preference(preference: Sequence[float]) -> np.ndarray:
    return np.asarray(preference, dtype=np.float32)


def _miss_result(
    preference: Sequence[float],
    *,
    selector_mode: str,
    source_set: str,
    reason: str,
) -> dict:
    weights = _normalise_preference(preference)
    return {
        "policy_id": None,
        "preference": weights.tolist(),
        "utility": None,
        "penalized_utility": None,
        "selector_mode": selector_mode,
        "source_set": source_set,
        "strict_hit": False,
        "fallback_used": False,
        "selection_status": "miss",
        "miss_reason": reason,
        "score_breakdown": {},
    }


def _assign_plain(
    preference: Sequence[float],
    policy_set: Sequence[dict],
    *,
    source_set: str = "records",
) -> dict:
    if not policy_set:
        raise ValueError("policy_set must not be empty")
    weights = _normalise_preference(preference)
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
    assigned["penalized_utility"] = float(best_utility)
    assigned["selector_mode"] = "plain"
    assigned["source_set"] = source_set
    assigned["strict_hit"] = None
    assigned["fallback_used"] = False
    assigned["selection_status"] = "selected"
    assigned["score_breakdown"] = {
        "utility": float(best_utility),
        "penalty": 0.0,
        "penalized_utility": float(best_utility),
    }
    return assigned


def assign_policy_union(
    preference: Sequence[float],
    policy_set: Sequence[dict],
    *,
    source_set: str = "union",
) -> dict:
    return _assign_plain(preference, policy_set, source_set=source_set)


def _strict_candidates(
    policy_set: Sequence[dict],
    *,
    require_tight: bool = False,
) -> list[dict]:
    candidates = [
        record
        for record in policy_set
        if bool(record.get("tight_feasible_flag"))
        or (not require_tight and bool(record.get("near_feasible_flag")))
    ]
    return candidates


def assign_policy_strict(
    preference: Sequence[float],
    cons_policy_set: Sequence[dict],
    *,
    require_tight: bool = False,
    source_set: str = "cons",
) -> dict:
    candidates = _strict_candidates(cons_policy_set, require_tight=require_tight)
    if not candidates:
        return _miss_result(
            preference,
            selector_mode="strict",
            source_set=source_set,
            reason="no_tight_feasible_candidate" if require_tight else "no_strict_candidate",
        )
    assigned = _assign_plain(preference, candidates, source_set=source_set)
    assigned["selector_mode"] = "strict"
    assigned["strict_hit"] = True
    assigned["fallback_used"] = False
    return assigned


def assign_policy_hybrid(
    preference: Sequence[float],
    cons_policy_set: Sequence[dict],
    union_policy_set: Sequence[dict] | None = None,
    *,
    penalty_weights: dict[str, float] | None = None,
    require_tight: bool = False,
) -> dict:
    assigned = assign_policy_strict(
        preference,
        cons_policy_set,
        require_tight=require_tight,
        source_set="cons",
    )
    if assigned.get("policy_id") is not None:
        assigned["selector_mode"] = "hybrid"
        assigned["strict_hit"] = True
        assigned["fallback_used"] = False
        return assigned

    fallback_set = list(union_policy_set) if union_policy_set is not None else list(cons_policy_set)
    if not fallback_set:
        return _miss_result(
            preference,
            selector_mode="hybrid",
            source_set="union",
            reason="no_hybrid_fallback_candidate",
        )
    penalty_weights = dict(penalty_weights or {})
    weights = _normalise_preference(preference)
    best_record = None
    best_utility = -np.inf
    best_penalized_utility = -np.inf
    best_breakdown: dict[str, float] = {}
    for record in fallback_set:
        objectives = np.asarray(record["objective_vector"], dtype=np.float32)
        utility = float(np.dot(weights, objectives))
        violation_penalty = float(
            penalty_weights.get("mean_violation", penalty_weights.get("violation", 1.0))
        ) * _metric(record, "mean_violation")
        disruption_penalty = float(
            penalty_weights.get(
                "high_disruption_rate",
                penalty_weights.get("high_disruption", 1.0),
            )
        ) * _metric(record, "high_disruption_rate", "high_disruption_action_rate")
        critical_penalty = float(
            penalty_weights.get(
                "final_critical_compromised",
                penalty_weights.get("final_critical", 1.0),
            )
        ) * _metric(
            record,
            "final_critical_compromised",
            "final_critical_compromised_hosts",
        )
        penalty = violation_penalty + disruption_penalty + critical_penalty
        penalized_utility = utility - penalty
        if penalized_utility > best_penalized_utility:
            best_penalized_utility = penalized_utility
            best_utility = utility
            best_record = record
            best_breakdown = {
                "utility": float(utility),
                "mean_violation_penalty": float(violation_penalty),
                "high_disruption_penalty": float(disruption_penalty),
                "final_critical_penalty": float(critical_penalty),
                "penalty": float(penalty),
                "penalized_utility": float(penalized_utility),
            }
    assert best_record is not None
    assigned = dict(best_record)
    assigned["preference"] = weights.tolist()
    assigned["utility"] = float(best_utility)
    assigned["penalized_utility"] = float(best_penalized_utility)
    assigned["selector_mode"] = "hybrid"
    assigned["source_set"] = "union"
    assigned["strict_hit"] = False
    assigned["fallback_used"] = True
    assigned["selection_status"] = "selected"
    assigned["score_breakdown"] = best_breakdown
    return assigned


def assign_policy(
    preference: Sequence[float],
    policy_set: Sequence[dict],
    *,
    mode: str = "plain",
    penalty_weights: dict[str, float] | None = None,
    source_set: str = "records",
    strict_policy_set: Sequence[dict] | None = None,
    require_tight: bool = False,
) -> dict:
    if mode == "plain":
        return _assign_plain(preference, policy_set, source_set=source_set)
    if mode == "union":
        return assign_policy_union(preference, policy_set, source_set=source_set)
    if mode == "strict":
        return assign_policy_strict(
            preference,
            policy_set,
            require_tight=require_tight,
            source_set=source_set,
        )
    if mode == "hybrid":
        return assign_policy_hybrid(
            preference,
            strict_policy_set if strict_policy_set is not None else policy_set,
            policy_set,
            penalty_weights=penalty_weights,
            require_tight=require_tight,
        )
    raise ValueError(f"Unsupported selector mode: {mode}")
