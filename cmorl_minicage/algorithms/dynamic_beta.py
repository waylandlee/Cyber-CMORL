from __future__ import annotations


def compute_dynamic_beta(
    component: dict[str, float | list[float]],
    objective_idx: int,
    round_idx: int,
    total_rounds: int,
    beta_min: float,
    beta_max: float,
    weights: dict[str, float],
) -> tuple[float, dict[str, float]]:
    crowding = float(component.get("crowding_score", 0.0))
    target_expansion_all = component.get("target_expansion_by_objective", [])
    if isinstance(target_expansion_all, list) and target_expansion_all:
        bounded_idx = min(max(objective_idx, 0), len(target_expansion_all) - 1)
        target_expansion = float(target_expansion_all[bounded_idx])
    else:
        target_expansion = float(component.get("expansion_potential", 0.0))
    low_risk = float(component.get("low_risk_score", 1.0))
    progress = float(round_idx / max(total_rounds - 1, 1))

    wc = float(weights.get("crowding", 0.0))
    we = float(weights.get("expansion", 0.0))
    wl = float(weights.get("low_risk", 0.0))
    wp = float(weights.get("progress", 0.0))
    total = wc + we + wl + wp
    if total <= 0.0:
        strictness = 0.0
    else:
        strictness = (
            wc * crowding + we * target_expansion + wl * low_risk + wp * progress
        ) / total

    dynamic_beta = float(beta_max - strictness * (beta_max - beta_min))
    dynamic_beta = max(min(dynamic_beta, beta_max), beta_min)
    return dynamic_beta, {
        "crowding": crowding,
        "target_expansion": target_expansion,
        "low_risk": low_risk,
        "progress": progress,
        "strictness": strictness,
    }
