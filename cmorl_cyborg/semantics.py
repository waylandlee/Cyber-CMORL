from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .scenario_profiles import ScenarioAssetProfile, load_scenario_profile
from .topology import role_group_for_host, role_group_for_subnet, subnet_for_host

DEFAULT_CRITICAL_HOST = "Op_Server0"
DEFAULT_CRITICAL_PATH_HOSTS = frozenset(
    ("Enterprise0", "Enterprise1", "Enterprise2", DEFAULT_CRITICAL_HOST)
)


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


def _serialise_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _serialise_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_serialise_value(item) for item in value]
    item_method = getattr(value, "item", None)
    if callable(item_method):
        try:
            return item_method()
        except Exception:
            pass
    return str(value)


def action_params_payload(action: Any) -> dict[str, Any]:
    if action is None or not hasattr(action, "get_params"):
        return {}
    try:
        params = action.get_params()
    except Exception:
        return {}
    if not isinstance(params, dict):
        return {"value": _serialise_value(params)}
    return {str(key): _serialise_value(value) for key, value in params.items()}


def action_target_hostname(action: Any) -> str | None:
    params = action_params_payload(action)
    for key in ("hostname", "target_hostname", "host", "target_host"):
        value = params.get(key)
        if isinstance(value, str):
            return value
    return None


def action_target_subnet(
    action: Any,
    scenario_name: str = "Scenario2",
    scenario_profile: str | None = None,
) -> str | None:
    params = action_params_payload(action)
    for key in ("subnet", "target_subnet"):
        value = params.get(key)
        if isinstance(value, str):
            return value
    return subnet_for_host(
        action_target_hostname(action),
        scenario_name=scenario_name,
        scenario_profile=scenario_profile,
    )


def _action_targets_user_subnet(
    action: Any,
    scenario_name: str = "Scenario2",
    scenario_profile: str | None = None,
) -> bool:
    target_subnet = action_target_subnet(
        action,
        scenario_name=scenario_name,
        scenario_profile=scenario_profile,
    )
    if isinstance(target_subnet, str) and target_subnet.lower() == "user":
        return True
    target_hostname = action_target_hostname(action)
    target_role_group = role_group_for_host(
        target_hostname,
        scenario_name=scenario_name,
        scenario_profile=scenario_profile,
    )
    return bool(target_role_group == "user")


def serialize_action(
    action: Any,
    scenario_name: str = "Scenario2",
    scenario_profile: str | None = None,
    subnet_aliases: dict[str, str] | None = None,
) -> dict[str, Any]:
    params = action_params_payload(action)
    target_hostname = action_target_hostname(action)
    target_subnet = action_target_subnet(
        action,
        scenario_name=scenario_name,
        scenario_profile=scenario_profile,
    )
    if (
        subnet_aliases
        and isinstance(target_subnet, str)
        and target_subnet in subnet_aliases
    ):
        target_subnet = subnet_aliases[target_subnet]
    target_role_group = role_group_for_host(
        target_hostname,
        scenario_name=scenario_name,
        scenario_profile=scenario_profile,
    )
    if target_role_group is None:
        target_role_group = role_group_for_subnet(target_subnet)
    return {
        "name": action_name(action),
        "params": params,
        "target_hostname": target_hostname,
        "target_subnet": target_subnet,
        "target_role_group": target_role_group,
        "raw": None if action is None else str(action),
    }


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


def snapshot_payload(snapshot: SemanticSnapshot) -> dict[str, Any]:
    return {
        "compromised_hosts": sorted(snapshot.compromised_hosts),
        "critical_compromised_hosts": sorted(snapshot.critical_compromised_hosts),
        "operational_compromised_hosts": sorted(snapshot.operational_compromised_hosts),
        "enterprise_compromised_hosts": sorted(snapshot.enterprise_compromised_hosts),
        "defender_compromised_hosts": sorted(snapshot.defender_compromised_hosts),
        "user_compromised_hosts": sorted(snapshot.user_compromised_hosts),
        "compromised_host_count": int(len(snapshot.compromised_hosts)),
        "critical_compromised_host_count": int(len(snapshot.critical_compromised_hosts)),
        "weighted_security_exposure": float(snapshot.weighted_security_exposure),
        "weighted_business_exposure": float(snapshot.weighted_business_exposure),
    }


def snapshot_transition(
    previous: SemanticSnapshot,
    current: SemanticSnapshot,
) -> dict[str, Any]:
    return {
        "state_before": snapshot_payload(previous),
        "state_after": snapshot_payload(current),
        "newly_compromised_hosts": sorted(current.compromised_hosts - previous.compromised_hosts),
        "recovered_hosts": sorted(previous.compromised_hosts - current.compromised_hosts),
        "critical_compromised_hosts": sorted(current.critical_compromised_hosts),
        "weighted_security_exposure": float(current.weighted_security_exposure),
        "weighted_business_exposure": float(current.weighted_business_exposure),
    }


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
    critical_present = float(DEFAULT_CRITICAL_HOST in current.critical_compromised_hosts)
    previous_critical_present = bool(DEFAULT_CRITICAL_HOST in previous.critical_compromised_hosts)
    critical_hit_event = float(critical_present > 0.0 and not previous_critical_present)
    user_target = _action_targets_user_subnet(
        blue_action,
        scenario_name=scenario_name,
        scenario_profile=scenario_profile,
    )
    enterprise_foothold_present = bool(previous.enterprise_compromised_hosts)
    return {
        "final_compromised_hosts": float(len(current.compromised_hosts)),
        "final_critical_compromised_hosts": float(len(current.critical_compromised_hosts)),
        "persistent_critical_breach_rate": float(len(current.critical_compromised_hosts)),
        "critical_impact_count": float(len(new_critical)),
        "recovered_hosts": float(len(recovered)),
        "analyse_count": 1.0 if action == "Analyse" else 0.0,
        "remove_count": 1.0 if action == "Remove" else 0.0,
        "restore_count": 1.0 if action == "Restore" else 0.0,
        "high_disruption_action_count": 1.0
        if high_disruption_action(blue_action, scenario_name, scenario_profile)
        else 0.0,
        "total_action_count": 1.0,
        "enterprise_foothold_present": 1.0 if enterprise_foothold_present else 0.0,
        "critical_present": critical_present,
        "critical_hit_event": critical_hit_event,
        "critical_dwell_flag": critical_present,
        "critical_path_compromise_count": float(
            len(current.compromised_hosts & DEFAULT_CRITICAL_PATH_HOSTS)
        ),
        "sleep_during_critical_breach": 1.0
        if action == "Sleep" and previous_critical_present
        else 0.0,
        "user_action_during_critical_breach": 1.0
        if user_target and previous_critical_present
        else 0.0,
        "user_action_after_enterprise_foothold": 1.0
        if user_target and enterprise_foothold_present
        else 0.0,
    }
