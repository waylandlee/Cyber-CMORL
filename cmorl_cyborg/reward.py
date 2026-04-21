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

CRITICAL_HOST_SAFETY_MODE_LEGACY = "v2_legacy"
CRITICAL_HOST_SAFETY_MODE_DENSE_PERSISTENT = "v2_1_dense_persistent"


@dataclass
class RewardTerms:
    security: float
    business: float
    cost: float
    critical_host_safety: float | None = None

    def as_array(self) -> np.ndarray:
        values = [self.security, self.business, self.cost]
        if self.critical_host_safety is not None:
            values.append(self.critical_host_safety)
        return np.asarray(values, dtype=np.float32)

    def with_critical_host_safety(self, value: float | None) -> "RewardTerms":
        return RewardTerms(
            security=float(self.security),
            business=float(self.business),
            cost=float(self.cost),
            critical_host_safety=None if value is None else float(value),
        )


def critical_host_safety_objective(
    *,
    ever_critical_breach: float,
    persistent_critical_breach: float,
    critical_hit_latency_score: float,
    dwell_ratio: float = 0.0,
    mode: str = CRITICAL_HOST_SAFETY_MODE_LEGACY,
) -> float:
    normalized_mode = str(mode).lower()
    if normalized_mode == CRITICAL_HOST_SAFETY_MODE_DENSE_PERSISTENT:
        return -(
            0.35 * float(ever_critical_breach)
            + 0.20 * float(persistent_critical_breach)
            + 0.15 * (1.0 - float(critical_hit_latency_score))
            + 0.30 * float(dwell_ratio)
        )
    return -(
        0.5 * float(ever_critical_breach)
        + 0.3 * float(persistent_critical_breach)
        + 0.2 * (1.0 - float(critical_hit_latency_score))
    )


def critical_host_safety_step_reward(
    *,
    critical_hit_event: float,
    critical_present: float,
    episode_done: bool,
    step_idx: int,
    max_episode_steps: int,
    mode: str = CRITICAL_HOST_SAFETY_MODE_LEGACY,
) -> float:
    normalized_mode = str(mode).lower()
    reward = 0.0
    if float(critical_hit_event) > 0.0:
        latency_score = float(step_idx) / float(max(int(max_episode_steps), 0) + 1)
        if normalized_mode == CRITICAL_HOST_SAFETY_MODE_DENSE_PERSISTENT:
            reward -= 0.35 + 0.15 * (1.0 - float(latency_score))
        else:
            reward += critical_host_safety_objective(
                ever_critical_breach=1.0,
                persistent_critical_breach=0.0,
                critical_hit_latency_score=latency_score,
                mode=normalized_mode,
            )
    if normalized_mode == CRITICAL_HOST_SAFETY_MODE_DENSE_PERSISTENT:
        reward -= (0.30 / float(max(int(max_episode_steps), 1))) * float(critical_present)
        if bool(episode_done) and float(critical_present) > 0.0:
            reward -= 0.20
    elif bool(episode_done) and float(critical_present) > 0.0:
        reward -= 0.3
    return float(reward)


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
