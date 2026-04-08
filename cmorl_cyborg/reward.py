from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .scenario_profiles import load_scenario_profile
from .semantics import (
    SemanticSnapshot,
    action_disturbance_weight,
    action_name,
    action_target_hostname,
    host_business_weight,
)


@dataclass
class RewardTerms:
    security: float
    business: float
    cost: float

    def as_array(self) -> np.ndarray:
        return np.asarray(
            [self.security, self.business, self.cost],
            dtype=np.float32,
        )


def action_operation_cost(
    action: Any,
    *,
    scenario_name: str = "Scenario2",
    scenario_profile: str | None = None,
) -> float:
    profile = load_scenario_profile(scenario_name, scenario_profile)
    name = action_name(action)
    if name.startswith(profile.decoy_action_prefix):
        return float(profile.decoy_cost)
    return float(profile.action_costs.get(name, profile.default_action_cost))


def project_reward_terms(
    *,
    previous: SemanticSnapshot,
    current: SemanticSnapshot,
    raw_reward: float,
    blue_action: Any,
    scenario_name: str = "Scenario2",
    scenario_profile: str | None = None,
) -> RewardTerms:
    profile = load_scenario_profile(scenario_name, scenario_profile)
    recovered = len(previous.compromised_hosts - current.compromised_hosts)
    new_critical = len(current.critical_compromised_hosts - previous.critical_compromised_hosts)
    target_hostname = action_target_hostname(blue_action)
    target_business_weight = (
        host_business_weight(target_hostname, scenario_name, scenario_profile)
        if target_hostname is not None
        else float(profile.fallback_target_business_weight)
    )
    action_disturbance = action_disturbance_weight(
        blue_action,
        scenario_name,
        scenario_profile,
    )

    security = (
        float(raw_reward)
        - float(current.weighted_security_exposure)
        - float(profile.security_critical_impact_penalty) * new_critical
        + float(profile.security_recovery_bonus) * recovered
    )
    business = -(
        float(current.weighted_business_exposure)
        + (action_disturbance * target_business_weight)
        + (float(profile.business_critical_impact_penalty) * new_critical)
    )
    cost = -float(
        action_operation_cost(
            blue_action,
            scenario_name=scenario_name,
            scenario_profile=scenario_profile,
        )
    )
    return RewardTerms(security=security, business=business, cost=cost)
