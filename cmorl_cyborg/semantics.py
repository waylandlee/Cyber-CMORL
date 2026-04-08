from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .scenario_profiles import ScenarioAssetProfile, load_scenario_profile


@dataclass
class SemanticSnapshot:
    compromised_hosts: set[str]
    critical_compromised_hosts: set[str]
    operational_compromised_hosts: set[str]
    enterprise_compromised_hosts: set[str]
    defender_compromised_hosts: set[str]
    user_compromised_hosts: set[str]
    weighted_security_exposure: float
    weighted_business_exposure: float


def scenario_asset_profile(
    scenario_name: str = "Scenario2",
    scenario_profile: str | None = None,
) -> ScenarioAssetProfile:
    return load_scenario_profile(scenario_name, scenario_profile)


def is_critical_host(
    hostname: str,
    scenario_name: str = "Scenario2",
    scenario_profile: str | None = None,
) -> bool:
    profile = scenario_asset_profile(scenario_name, scenario_profile)
    return hostname in profile.mission_critical_hosts


def action_name(action: Any) -> str:
    if action is None:
        return "Sleep"
    return action.__class__.__name__


def action_target_hostname(action: Any) -> str | None:
    if action is None or not hasattr(action, "get_params"):
        return None
    params = action.get_params()
    for key in ("hostname", "target_hostname"):
        value = params.get(key)
        if isinstance(value, str):
            return value
    return None


def high_disruption_action(
    action: Any,
    scenario_name: str = "Scenario2",
    scenario_profile: str | None = None,
) -> bool:
    profile = scenario_asset_profile(scenario_name, scenario_profile)
    name = action_name(action)
    return (
        name in profile.high_disruption_actions
        or name.startswith(profile.decoy_action_prefix)
    )


def action_disturbance_weight(
    action: Any,
    scenario_name: str = "Scenario2",
    scenario_profile: str | None = None,
) -> float:
    profile = scenario_asset_profile(scenario_name, scenario_profile)
    name = action_name(action)
    if name in profile.low_disturbance_actions:
        return 0.0
    if name in profile.action_disturbance_weights:
        return float(profile.action_disturbance_weights[name])
    if name.startswith(profile.decoy_action_prefix):
        return float(profile.decoy_action_disturbance)
    return float(profile.default_action_disturbance)


def host_security_weight(
    hostname: str,
    scenario_name: str = "Scenario2",
    scenario_profile: str | None = None,
) -> float:
    profile = scenario_asset_profile(scenario_name, scenario_profile)
    return float(profile.security_weights.get(hostname, profile.default_security_weight))


def host_business_weight(
    hostname: str,
    scenario_name: str = "Scenario2",
    scenario_profile: str | None = None,
) -> float:
    profile = scenario_asset_profile(scenario_name, scenario_profile)
    return float(profile.business_weights.get(hostname, profile.default_business_weight))


def _host_compromised(host_state: dict[str, Any]) -> bool:
    for session in host_state.get("Sessions", []):
        if session.get("Agent") == "Red":
            return True
    return False


def snapshot_from_true_state(
    true_state: dict[str, Any],
    scenario_name: str = "Scenario2",
    scenario_profile: str | None = None,
) -> SemanticSnapshot:
    profile = scenario_asset_profile(scenario_name, scenario_profile)
    compromised: set[str] = set()
    critical: set[str] = set()
    operational: set[str] = set()
    enterprise: set[str] = set()
    defender: set[str] = set()
    user: set[str] = set()
    for hostname, host_state in true_state.items():
        if hostname == "success" or not isinstance(host_state, dict):
            continue
        if not _host_compromised(host_state):
            continue
        compromised.add(hostname)
        if hostname in profile.mission_critical_hosts:
            critical.add(hostname)
        if hostname in profile.operational_hosts:
            operational.add(hostname)
        if hostname in profile.enterprise_hosts:
            enterprise.add(hostname)
        if hostname in profile.defender_hosts:
            defender.add(hostname)
        if hostname in profile.user_hosts:
            user.add(hostname)
    return SemanticSnapshot(
        compromised_hosts=compromised,
        critical_compromised_hosts=critical,
        operational_compromised_hosts=operational,
        enterprise_compromised_hosts=enterprise,
        defender_compromised_hosts=defender,
        user_compromised_hosts=user,
        weighted_security_exposure=sum(
            host_security_weight(hostname, scenario_name, scenario_profile)
            for hostname in compromised
        ),
        weighted_business_exposure=sum(
            host_business_weight(hostname, scenario_name, scenario_profile)
            for hostname in compromised
        ),
    )


def semantic_step_info(
    previous: SemanticSnapshot,
    current: SemanticSnapshot,
    blue_action: Any,
    scenario_name: str = "Scenario2",
    scenario_profile: str | None = None,
) -> dict[str, float]:
    action = action_name(blue_action)
    recovered = previous.compromised_hosts - current.compromised_hosts
    new_critical = current.critical_compromised_hosts - previous.critical_compromised_hosts
    return {
        "final_compromised_hosts": float(len(current.compromised_hosts)),
        "final_critical_compromised_hosts": float(len(current.critical_compromised_hosts)),
        "critical_impact_count": float(len(new_critical)),
        "recovered_hosts": float(len(recovered)),
        "analyse_count": 1.0 if action == "Analyse" else 0.0,
        "remove_count": 1.0 if action == "Remove" else 0.0,
        "restore_count": 1.0 if action == "Restore" else 0.0,
        "high_disruption_action_count": 1.0
        if high_disruption_action(blue_action, scenario_name, scenario_profile)
        else 0.0,
        "total_action_count": 1.0,
    }
