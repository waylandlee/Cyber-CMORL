from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from .compat import repo_root
from .scenario_profiles import ScenarioAssetProfile, load_scenario_profile


def resolve_scenario_topology_path(scenario_name: str = "Scenario2") -> Path:
    return (
        repo_root()
        / "Debugged_CybORG"
        / "CybORG"
        / "CybORG"
        / "Shared"
        / "Scenarios"
        / f"{scenario_name}.yaml"
    )


def _role_group_for_host_from_profile(
    hostname: str,
    profile: ScenarioAssetProfile,
) -> str | None:
    if hostname in profile.mission_critical_hosts:
        return "mission_critical"
    if hostname in profile.operational_hosts:
        return "operational"
    if hostname in profile.enterprise_hosts:
        return "enterprise"
    if hostname in profile.defender_hosts:
        return "defender"
    if hostname in profile.user_hosts:
        return "user"
    return None


def role_group_for_host(
    hostname: str | None,
    scenario_name: str = "Scenario2",
    scenario_profile: str | None = None,
) -> str | None:
    if not hostname:
        return None
    profile = load_scenario_profile(scenario_name, scenario_profile)
    return _role_group_for_host_from_profile(hostname, profile)


def role_group_for_subnet(subnet_name: str | None) -> str | None:
    if subnet_name is None:
        return None
    normalized = str(subnet_name).strip().lower()
    return {
        "operational": "operational",
        "enterprise": "enterprise",
        "user": "user",
    }.get(normalized)


@lru_cache(maxsize=16)
def _scenario_payload(scenario_name: str) -> dict[str, Any]:
    path = resolve_scenario_topology_path(scenario_name)
    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"Scenario topology payload must be a mapping: {path}")
    return payload


@lru_cache(maxsize=32)
def topology_snapshot(
    scenario_name: str = "Scenario2",
    scenario_profile: str | None = None,
) -> dict[str, Any]:
    payload = _scenario_payload(scenario_name)
    profile = load_scenario_profile(scenario_name, scenario_profile)

    subnets_payload = dict(payload.get("Subnets", {}))
    hosts_payload = dict(payload.get("Hosts", {}))

    host_to_subnet: dict[str, str] = {}
    subnets: list[dict[str, Any]] = []
    for subnet_name, subnet_payload in subnets_payload.items():
        hosts = [str(hostname) for hostname in subnet_payload.get("Hosts", [])]
        for hostname in hosts:
            host_to_subnet[hostname] = str(subnet_name)
        subnets.append(
            {
                "name": str(subnet_name),
                "hosts": hosts,
                "size": int(subnet_payload.get("Size", len(hosts))),
            }
        )

    hosts: dict[str, dict[str, Any]] = {}
    for hostname, host_payload in hosts_payload.items():
        image = host_payload.get("image")
        hosts[str(hostname)] = {
            "hostname": str(hostname),
            "subnet": host_to_subnet.get(str(hostname)),
            "role_group": _role_group_for_host_from_profile(str(hostname), profile),
            "image": str(image) if image is not None else None,
            "is_critical": str(hostname) in profile.mission_critical_hosts,
            "security_weight": float(
                profile.security_weights.get(str(hostname), profile.default_security_weight)
            ),
            "business_weight": float(
                profile.business_weights.get(str(hostname), profile.default_business_weight)
            ),
        }

    return {
        "scenario_name": scenario_name,
        "scenario_profile": profile.profile_name,
        "subnets": subnets,
        "hosts": hosts,
        "host_to_subnet": host_to_subnet,
    }


def subnet_for_host(
    hostname: str | None,
    scenario_name: str = "Scenario2",
    scenario_profile: str | None = None,
) -> str | None:
    if not hostname:
        return None
    snapshot = topology_snapshot(scenario_name, scenario_profile)
    return snapshot["host_to_subnet"].get(str(hostname))
