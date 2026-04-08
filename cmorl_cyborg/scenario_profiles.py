from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml


@dataclass(frozen=True)
class ScenarioAssetProfile:
    scenario_name: str
    profile_name: str
    mission_critical_hosts: frozenset[str]
    operational_hosts: frozenset[str]
    enterprise_hosts: frozenset[str]
    defender_hosts: frozenset[str]
    user_hosts: frozenset[str]
    security_weights: dict[str, float]
    business_weights: dict[str, float]
    high_disruption_actions: frozenset[str]
    low_disturbance_actions: frozenset[str]
    observation_actions: frozenset[str]
    decoy_action_prefix: str
    action_costs: dict[str, float]
    decoy_cost: float
    default_action_cost: float
    action_disturbance_weights: dict[str, float]
    decoy_action_disturbance: float
    default_action_disturbance: float
    security_critical_impact_penalty: float
    security_recovery_bonus: float
    business_critical_impact_penalty: float
    default_security_weight: float
    default_business_weight: float
    fallback_target_business_weight: float

    @property
    def focus_hosts(self) -> tuple[str, ...]:
        for hosts in (
            self.mission_critical_hosts,
            self.operational_hosts,
            self.enterprise_hosts,
            self.defender_hosts,
            self.user_hosts,
        ):
            if hosts:
                return tuple(sorted(hosts))
        weighted_hosts = set(self.security_weights) | set(self.business_weights)
        return tuple(sorted(weighted_hosts))

    @property
    def primary_focus_host(self) -> str | None:
        hosts = self.focus_hosts
        return hosts[0] if hosts else None


PROFILE_DIR = Path(__file__).resolve().parent / "profiles"


def _profile_path_for(scenario_name: str, scenario_profile: str | None = None) -> Path:
    profile_ref = (scenario_profile or "").strip()
    if profile_ref:
        profile_path = Path(profile_ref)
        if profile_path.suffix:
            return profile_path if profile_path.is_absolute() else Path.cwd() / profile_path
        return PROFILE_DIR / f"{profile_ref}.yaml"
    return PROFILE_DIR / f"{scenario_name}.yaml"


def _as_frozenset(payload: dict, key: str) -> frozenset[str]:
    return frozenset(str(item) for item in payload.get(key, []))


def _as_float_map(payload: dict, key: str) -> dict[str, float]:
    return {str(k): float(v) for k, v in dict(payload.get(key, {})).items()}


@lru_cache(maxsize=32)
def _load_profile_cached(profile_path: str) -> ScenarioAssetProfile:
    path = Path(profile_path)
    if not path.exists():
        raise ValueError(f"Scenario profile file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"Scenario profile must be a mapping: {path}")
    scenario_name = str(payload.get("scenario_name") or path.stem)
    profile_name = str(payload.get("profile_name") or path.stem)
    return ScenarioAssetProfile(
        scenario_name=scenario_name,
        profile_name=profile_name,
        mission_critical_hosts=_as_frozenset(payload, "mission_critical_hosts"),
        operational_hosts=_as_frozenset(payload, "operational_hosts"),
        enterprise_hosts=_as_frozenset(payload, "enterprise_hosts"),
        defender_hosts=_as_frozenset(payload, "defender_hosts"),
        user_hosts=_as_frozenset(payload, "user_hosts"),
        security_weights=_as_float_map(payload, "security_weights"),
        business_weights=_as_float_map(payload, "business_weights"),
        high_disruption_actions=_as_frozenset(payload, "high_disruption_actions"),
        low_disturbance_actions=_as_frozenset(payload, "low_disturbance_actions"),
        observation_actions=_as_frozenset(payload, "observation_actions"),
        decoy_action_prefix=str(payload.get("decoy_action_prefix", "Decoy")),
        action_costs=_as_float_map(payload, "action_costs"),
        decoy_cost=float(payload.get("decoy_cost", 0.20)),
        default_action_cost=float(payload.get("default_action_cost", 0.10)),
        action_disturbance_weights=_as_float_map(payload, "action_disturbance_weights"),
        decoy_action_disturbance=float(payload.get("decoy_action_disturbance", 0.20)),
        default_action_disturbance=float(payload.get("default_action_disturbance", 0.10)),
        security_critical_impact_penalty=float(
            payload.get("security_critical_impact_penalty", 6.0)
        ),
        security_recovery_bonus=float(payload.get("security_recovery_bonus", 1.0)),
        business_critical_impact_penalty=float(
            payload.get("business_critical_impact_penalty", 1.25)
        ),
        default_security_weight=float(payload.get("default_security_weight", 0.10)),
        default_business_weight=float(payload.get("default_business_weight", 0.05)),
        fallback_target_business_weight=float(
            payload.get("fallback_target_business_weight", 0.20)
        ),
    )


def load_scenario_profile(
    scenario_name: str = "Scenario2",
    scenario_profile: str | None = None,
) -> ScenarioAssetProfile:
    path = _profile_path_for(scenario_name, scenario_profile)
    return _load_profile_cached(str(path.resolve()))
