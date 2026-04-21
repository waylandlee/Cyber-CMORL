from __future__ import annotations

import argparse
import csv
import json
import os
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any, Iterable

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-cmorl-cyborg")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from cmorl_minicage.buffer import load_policy_buffer
from cmorl_minicage.shield import (
    ACTION_FAMILY_ANALYSE,
    ACTION_FAMILY_DECOY,
    ACTION_FAMILY_OTHER,
    ACTION_FAMILY_REMOVE,
    ACTION_FAMILY_RESTORE,
    action_family_from_name,
)
from cmorl_minicage.utils import ensure_dir, save_json

from .export_figure2_attack_defense_trace import (
    Figure2ReplayCandidate,
    export_candidate_trace,
    resolve_artifact_path,
)


DEFAULT_CRITICAL_HOST = "Op_Server0"
DEFAULT_CRITICAL_PATH_HOSTS = ("Enterprise0", "Enterprise1", "Enterprise2", "Op_Server0")
HIGH_CONFIDENCE_RULES = {
    "Q1_sleep_during_critical_breach",
    "Q2_user_action_during_critical_breach",
    "Q3_missed_immediate_response_to_critical_hit",
}
MEDIUM_CONFIDENCE_RULES = {
    "Q4_user_focus_after_enterprise_foothold",
    "Q5_repeated_low_value_decoy_loop",
}
SUMMARY_FILES = (
    "env_run_risk_table.csv",
    "risk_tier_summary.json",
    "questionable_defense_actions.csv",
    "critical_casebook.md",
    "semantic_risk_summary.md",
    "critical_path_heatmap.png",
)
CRITICAL_ACTION_FAMILIES = (
    ACTION_FAMILY_RESTORE,
    ACTION_FAMILY_REMOVE,
    ACTION_FAMILY_ANALYSE,
    ACTION_FAMILY_DECOY,
    ACTION_FAMILY_OTHER,
)
PRECRITICAL_ACTION_FAMILIES = CRITICAL_ACTION_FAMILIES


@dataclass
class EnvRunAudit:
    key: tuple[str, int]
    method_name: str
    seed: int
    policy_id: str
    candidate_label: str
    episode_id: str
    env_idx: int
    env_seed: int
    step_count: int
    return_vector: list[float]
    final_state: dict[str, Any]
    rows: list[dict[str, Any]]
    risk_row: dict[str, Any]
    questionable_events: list[dict[str, Any]]


def _load_json(path: str | Path) -> dict[str, Any] | list[Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _format_float(value: float | None, digits: int = 4) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.{digits}f}"


def _mean_or_none(values: Iterable[float | None]) -> float | None:
    cleaned = [float(value) for value in values if value is not None]
    if not cleaned:
        return None
    return float(mean(cleaned))


def _format_list(values: Iterable[str]) -> str:
    return ", ".join(str(value) for value in values) if values else "-"


def _json_list_field(values: Iterable[str]) -> str:
    return json.dumps(list(values), ensure_ascii=False)


def _response_context_field(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def _trace_manifest(trace_dir: Path) -> dict[str, Any]:
    return dict(_load_json(trace_dir / "trace_manifest.json"))


def _episode_summary_lookup(trace_dir: Path) -> dict[tuple[str, int], dict[str, Any]]:
    payload = list(_load_json(trace_dir / "episode_summaries.json"))
    lookup: dict[tuple[str, int], dict[str, Any]] = {}
    for episode in payload:
        episode_id = str(episode["episode_id"])
        for env_summary in episode.get("env_summaries", []):
            lookup[(episode_id, int(env_summary["env_idx"]))] = {
                "episode_id": episode_id,
                "episode_seed": int(episode["episode_seed"]),
                "env_idx": int(env_summary["env_idx"]),
                "env_seed": int(env_summary["env_seed"]),
                "step_count": int(env_summary["step_count"]),
                "return_vector": list(env_summary["return_vector"]),
                "final_state": dict(env_summary["final_state"]),
            }
    return lookup


def _trace_rows_by_env_run(trace_dir: Path) -> dict[tuple[str, int], list[dict[str, Any]]]:
    rows_by_key: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for episode_path in sorted(trace_dir.glob("episode_*.jsonl")):
        with episode_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                key = (str(row["episode_id"]), int(row["env_idx"]))
                rows_by_key[key].append(row)
    for rows in rows_by_key.values():
        rows.sort(key=lambda row: int(row["step_idx"]))
    return rows_by_key


def _blue_target_hostname(row: dict[str, Any]) -> str | None:
    target = row.get("blue_action", {}).get("target_hostname")
    return None if not target else str(target)


def _blue_target_subnet(row: dict[str, Any]) -> str | None:
    target = row.get("blue_action", {}).get("target_subnet")
    return None if not target else str(target)


def _blue_action_family(row: dict[str, Any]) -> str:
    family = action_family_from_name(row.get("blue_action", {}).get("name"))
    if family in {ACTION_FAMILY_RESTORE, ACTION_FAMILY_REMOVE, ACTION_FAMILY_ANALYSE, ACTION_FAMILY_DECOY}:
        return family
    return ACTION_FAMILY_OTHER


def _red_target_hostname(row: dict[str, Any]) -> str | None:
    target = row.get("red_action", {}).get("target_hostname")
    return None if not target else str(target)


def _compromised_hosts(state: dict[str, Any]) -> list[str]:
    return list(state.get("compromised_hosts", []))


def _critical_hosts(state: dict[str, Any]) -> list[str]:
    return list(state.get("critical_compromised_hosts", []))


def _critical_present(state: dict[str, Any], critical_host: str) -> bool:
    return critical_host in set(_critical_hosts(state))


def _critical_present_for_action_family(row: dict[str, Any], critical_host: str) -> bool:
    semantic_payload = dict(row.get("semantic_info", {}) or {})
    if "critical_present" in semantic_payload:
        return bool(float(semantic_payload.get("critical_present", 0.0)))
    return _critical_present(row.get("state_before", {}), critical_host) or _critical_present(
        row.get("state_after", {}),
        critical_host,
    )


def _enterprise_foothold_present(row: dict[str, Any], enterprise_hosts: set[str]) -> bool:
    semantic_payload = dict(row.get("semantic_info", {}) or {})
    if "enterprise_foothold_present" in semantic_payload:
        return bool(float(semantic_payload.get("enterprise_foothold_present", 0.0)))
    state_before_hosts = set(_compromised_hosts(row.get("state_before", {})))
    state_after_hosts = set(_compromised_hosts(row.get("state_after", {})))
    return bool((state_before_hosts | state_after_hosts) & enterprise_hosts)


def _precritical_present_for_action_family(
    row: dict[str, Any],
    *,
    critical_host: str,
    enterprise_hosts: set[str],
) -> bool:
    return _enterprise_foothold_present(
        row,
        enterprise_hosts,
    ) and not _critical_present_for_action_family(row, critical_host)


def _precritical_compromised_target_focus(row: dict[str, Any]) -> bool:
    target_hostname = _blue_target_hostname(row)
    target_subnet = _blue_target_subnet(row)
    if target_hostname is None:
        return False
    normalized_subnet = None if target_subnet is None else str(target_subnet).lower()
    if normalized_subnet not in {"enterprise", "operational"}:
        return False
    return target_hostname in set(_compromised_hosts(row.get("state_before", {})))


def _critical_path_compromise_count(state: dict[str, Any], critical_path_hosts: set[str]) -> int:
    return len(set(_compromised_hosts(state)) & critical_path_hosts)


def _first_step_matching(rows: list[dict[str, Any]], predicate) -> int | None:
    for row in rows:
        if predicate(row):
            return int(row["step_idx"])
    return None


def _first_relevant_response_step(
    rows: list[dict[str, Any]],
    *,
    activation_step: int | None,
    critical_path_hosts: set[str],
) -> int | None:
    if activation_step is None:
        return None
    for row in rows:
        step_idx = int(row["step_idx"])
        if step_idx <= activation_step:
            continue
        if _blue_target_hostname(row) in critical_path_hosts:
            return step_idx
    return None


def _risk_tier(*, ever_critical_breach: bool, final_critical_breach: bool, enterprise_foothold_step: int | None) -> str:
    if final_critical_breach:
        return "Tier 3 Persistent Critical Breach"
    if ever_critical_breach:
        return "Tier 2 Transient Critical Breach"
    if enterprise_foothold_step is not None:
        return "Tier 1 Near-Miss"
    return "Tier 0 Safe"


def _response_context(
    *,
    enterprise_foothold_step: int | None,
    first_critical_hit_step: int | None,
    blue_response_after_enterprise: int | None,
    blue_response_after_critical: int | None,
    window_start: int | None = None,
    window_end: int | None = None,
) -> str:
    return _response_context_field(
        {
            "enterprise_foothold_step": enterprise_foothold_step,
            "first_critical_hit_step": first_critical_hit_step,
            "blue_first_relevant_response_after_enterprise": blue_response_after_enterprise,
            "blue_first_relevant_response_after_critical": blue_response_after_critical,
            "window_start": window_start,
            "window_end": window_end,
        }
    )


def _event_row(
    *,
    run: dict[str, Any],
    row: dict[str, Any],
    rule_id: str,
    severity: str,
    response_context: str,
) -> dict[str, Any]:
    return {
        "method_name": str(run["method_name"]),
        "seed": int(run["seed"]),
        "policy_id": str(run["policy_id"]),
        "candidate_label": str(run["candidate_label"]),
        "episode_id": str(run["episode_id"]),
        "env_idx": int(run["env_idx"]),
        "env_seed": int(run["env_seed"]),
        "step_idx": int(row["step_idx"]),
        "rule_id": rule_id,
        "severity": severity,
        "blue_action_name": str(row["blue_action"].get("name", "")),
        "blue_target_hostname": str(row["blue_action"].get("target_hostname") or ""),
        "blue_target_subnet": str(row["blue_action"].get("target_subnet") or ""),
        "red_action_name": str(row["red_action"].get("name", "")),
        "red_target_hostname": str(row["red_action"].get("target_hostname") or ""),
        "critical_state_before": _json_list_field(_critical_hosts(row["state_before"])),
        "critical_state_after": _json_list_field(_critical_hosts(row["state_after"])),
        "compromised_hosts_before": _json_list_field(_compromised_hosts(row["state_before"])),
        "compromised_hosts_after": _json_list_field(_compromised_hosts(row["state_after"])),
        "response_context": response_context,
    }


def _evaluate_questionable_rules(
    *,
    run_metadata: dict[str, Any],
    rows: list[dict[str, Any]],
    critical_host: str,
    enterprise_hosts: set[str],
    critical_path_hosts: set[str],
    enterprise_foothold_step: int | None,
    first_critical_hit_step: int | None,
    blue_response_after_enterprise: int | None,
    blue_response_after_critical: int | None,
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []

    for row in rows:
        if (
            str(row["blue_action"].get("name", "")) == "Sleep"
            and _critical_present(row["state_before"], critical_host)
        ):
            events.append(
                _event_row(
                    run=run_metadata,
                    row=row,
                    rule_id="Q1_sleep_during_critical_breach",
                    severity="high",
                    response_context=_response_context(
                        enterprise_foothold_step=enterprise_foothold_step,
                        first_critical_hit_step=first_critical_hit_step,
                        blue_response_after_enterprise=blue_response_after_enterprise,
                        blue_response_after_critical=blue_response_after_critical,
                    ),
                )
            )
        if (
            _blue_target_subnet(row) == "User"
            and _critical_present(row["state_before"], critical_host)
        ):
            events.append(
                _event_row(
                    run=run_metadata,
                    row=row,
                    rule_id="Q2_user_action_during_critical_breach",
                    severity="high",
                    response_context=_response_context(
                        enterprise_foothold_step=enterprise_foothold_step,
                        first_critical_hit_step=first_critical_hit_step,
                        blue_response_after_enterprise=blue_response_after_enterprise,
                        blue_response_after_critical=blue_response_after_critical,
                    ),
                )
            )

    if first_critical_hit_step is not None:
        response_exists = any(
            _blue_target_hostname(row) in critical_path_hosts
            for row in rows
            if first_critical_hit_step < int(row["step_idx"]) <= first_critical_hit_step + 3
        )
        if not response_exists:
            anchor_row = next(
                row for row in rows if int(row["step_idx"]) == first_critical_hit_step
            )
            events.append(
                _event_row(
                    run=run_metadata,
                    row=anchor_row,
                    rule_id="Q3_missed_immediate_response_to_critical_hit",
                    severity="high",
                    response_context=_response_context(
                        enterprise_foothold_step=enterprise_foothold_step,
                        first_critical_hit_step=first_critical_hit_step,
                        blue_response_after_enterprise=blue_response_after_enterprise,
                        blue_response_after_critical=blue_response_after_critical,
                        window_start=first_critical_hit_step + 1,
                        window_end=first_critical_hit_step + 3,
                    ),
                )
            )

    if enterprise_foothold_step is not None:
        rows_by_step = {int(row["step_idx"]): row for row in rows}
        max_step = max(rows_by_step) if rows_by_step else -1
        for window_start in range(enterprise_foothold_step + 1, max_step - 1):
            window_steps = [window_start, window_start + 1, window_start + 2]
            if any(step not in rows_by_step for step in window_steps):
                continue
            window_rows = [rows_by_step[step] for step in window_steps]
            if all(_blue_target_subnet(row) == "User" for row in window_rows) and not any(
                _blue_target_hostname(row) in critical_path_hosts for row in window_rows
            ):
                events.append(
                    _event_row(
                        run=run_metadata,
                        row=window_rows[0],
                        rule_id="Q4_user_focus_after_enterprise_foothold",
                        severity="medium",
                        response_context=_response_context(
                            enterprise_foothold_step=enterprise_foothold_step,
                            first_critical_hit_step=first_critical_hit_step,
                            blue_response_after_enterprise=blue_response_after_enterprise,
                            blue_response_after_critical=blue_response_after_critical,
                            window_start=window_start,
                            window_end=window_start + 2,
                        ),
                    )
                )

        emitted_loops: set[tuple[str, str]] = set()
        for window_start in range(enterprise_foothold_step + 1, max_step - 8):
            window_rows = [
                rows_by_step[step]
                for step in range(window_start, window_start + 10)
                if step in rows_by_step
            ]
            if len(window_rows) < 10:
                continue
            decoy_counter: Counter[tuple[str, str]] = Counter()
            start_count = _critical_path_compromise_count(window_rows[0]["state_before"], critical_path_hosts)
            min_window_count = min(
                _critical_path_compromise_count(row["state_after"], critical_path_hosts)
                for row in window_rows
            )
            if min_window_count < start_count:
                continue
            for row in window_rows:
                blue_action_name = str(row["blue_action"].get("name", ""))
                blue_target = _blue_target_hostname(row)
                if not blue_action_name.startswith("Decoy"):
                    continue
                if _blue_target_subnet(row) != "User" or not blue_target:
                    continue
                decoy_counter[(blue_action_name, blue_target)] += 1
            for (blue_action_name, blue_target), count in sorted(decoy_counter.items()):
                if count < 3 or (blue_action_name, blue_target) in emitted_loops:
                    continue
                anchor_row = next(
                    row
                    for row in window_rows
                    if str(row["blue_action"].get("name", "")) == blue_action_name
                    and _blue_target_hostname(row) == blue_target
                )
                events.append(
                    _event_row(
                        run=run_metadata,
                        row=anchor_row,
                        rule_id="Q5_repeated_low_value_decoy_loop",
                        severity="medium",
                        response_context=_response_context(
                            enterprise_foothold_step=enterprise_foothold_step,
                            first_critical_hit_step=first_critical_hit_step,
                            blue_response_after_enterprise=blue_response_after_enterprise,
                            blue_response_after_critical=blue_response_after_critical,
                            window_start=window_start,
                            window_end=window_start + 9,
                        ),
                    )
                )
                emitted_loops.add((blue_action_name, blue_target))
    return events


def _build_env_run_audit(
    *,
    manifest: dict[str, Any],
    env_summary: dict[str, Any],
    rows: list[dict[str, Any]],
    critical_host: str,
    enterprise_hosts: set[str],
    critical_path_hosts: set[str],
) -> EnvRunAudit:
    enterprise_foothold_step = _first_step_matching(
        rows,
        lambda row: bool(set(_compromised_hosts(row["state_after"])) & enterprise_hosts),
    )
    first_critical_hit_step = _first_step_matching(
        rows,
        lambda row: _critical_present(row["state_after"], critical_host),
    )
    ever_critical_breach = first_critical_hit_step is not None
    final_critical_breach = _critical_present(env_summary["final_state"], critical_host)
    critical_dwell_steps = sum(
        1 for row in rows if _critical_present(row["state_after"], critical_host)
    )
    op_server0_impact_count = sum(
        1
        for row in rows
        if str(row["red_action"].get("name", "")) == "Impact"
        and _red_target_hostname(row) == critical_host
    )
    max_compromised_host_count = max(
        int(row["state_after"].get("compromised_host_count", 0)) for row in rows
    ) if rows else 0
    blue_response_after_enterprise = _first_relevant_response_step(
        rows,
        activation_step=enterprise_foothold_step,
        critical_path_hosts=critical_path_hosts,
    )
    blue_response_after_critical = _first_relevant_response_step(
        rows,
        activation_step=first_critical_hit_step,
        critical_path_hosts=critical_path_hosts,
    )
    blue_first_relevant_response_step = (
        blue_response_after_enterprise
        if blue_response_after_enterprise is not None
        else blue_response_after_critical
    )
    security_return = float(env_summary["return_vector"][0])
    business_return = float(env_summary["return_vector"][1])
    cost_return = float(env_summary["return_vector"][2])
    critical_host_safety_return = (
        float(env_summary["return_vector"][3])
        if len(env_summary["return_vector"]) > 3
        else None
    )
    shield_active_step_count = sum(
        int(bool(row.get("shield_active_flag", False))) for row in rows
    )
    shield_fallback_step_count = sum(
        int(bool(row.get("shield_fallback_flag", False))) for row in rows
    )
    mean_shield_blocked_probability_mass = _mean_or_none(
        float(row.get("shield_blocked_probability_mass", 0.0)) for row in rows
    )
    thresholds = manifest["tight_thresholds"]
    risk_row = {
        "method_name": str(manifest["method_name"]),
        "seed": int(manifest["seed"]),
        "policy_id": str(manifest["policy_id"]),
        "candidate_label": str(manifest["candidate_label"]),
        "episode_id": str(env_summary["episode_id"]),
        "env_idx": int(env_summary["env_idx"]),
        "env_seed": int(env_summary["env_seed"]),
        "step_count": int(env_summary["step_count"]),
        "security_return": security_return,
        "business_return": business_return,
        "cost_return": cost_return,
        "critical_host_safety_return": critical_host_safety_return,
        "business_violation_flag": bool(business_return < float(thresholds["d_business"])),
        "cost_violation_flag": bool(cost_return < float(thresholds["d_cost"])),
        "env_run_feasible_flag": bool(
            business_return >= float(thresholds["d_business"])
            and cost_return >= float(thresholds["d_cost"])
        ),
        "enterprise_foothold_step": enterprise_foothold_step,
        "first_critical_hit_step": first_critical_hit_step,
        "ever_critical_breach": bool(ever_critical_breach),
        "final_critical_breach": bool(final_critical_breach),
        "critical_dwell_steps": int(critical_dwell_steps),
        "op_server0_impact_count": int(op_server0_impact_count),
        "max_compromised_host_count": int(max_compromised_host_count),
        "blue_first_relevant_response_step": blue_first_relevant_response_step,
        "response_delay_after_enterprise": (
            None
            if enterprise_foothold_step is None or blue_response_after_enterprise is None
            else int(blue_response_after_enterprise - enterprise_foothold_step)
        ),
        "response_delay_after_critical": (
            None
            if first_critical_hit_step is None or blue_response_after_critical is None
            else int(blue_response_after_critical - first_critical_hit_step)
        ),
        "shield_active_step_count": int(shield_active_step_count),
        "shield_active_step_rate": float(
            shield_active_step_count / max(len(rows), 1)
        ),
        "shield_fallback_step_count": int(shield_fallback_step_count),
        "shield_fallback_step_rate": float(
            shield_fallback_step_count / max(len(rows), 1)
        ),
        "mean_shield_blocked_probability_mass": (
            None
            if mean_shield_blocked_probability_mass is None
            else float(mean_shield_blocked_probability_mass)
        ),
        "no_post_critical_response": bool(
            first_critical_hit_step is not None and blue_response_after_critical is None
        ),
    }
    risk_row["risk_tier"] = _risk_tier(
        ever_critical_breach=bool(risk_row["ever_critical_breach"]),
        final_critical_breach=bool(risk_row["final_critical_breach"]),
        enterprise_foothold_step=enterprise_foothold_step,
    )
    run_metadata = {
        "method_name": manifest["method_name"],
        "seed": manifest["seed"],
        "policy_id": manifest["policy_id"],
        "candidate_label": manifest["candidate_label"],
        "episode_id": env_summary["episode_id"],
        "env_idx": env_summary["env_idx"],
        "env_seed": env_summary["env_seed"],
    }
    questionable_events = _evaluate_questionable_rules(
        run_metadata=run_metadata,
        rows=rows,
        critical_host=critical_host,
        enterprise_hosts=enterprise_hosts,
        critical_path_hosts=critical_path_hosts,
        enterprise_foothold_step=enterprise_foothold_step,
        first_critical_hit_step=first_critical_hit_step,
        blue_response_after_enterprise=blue_response_after_enterprise,
        blue_response_after_critical=blue_response_after_critical,
    )
    return EnvRunAudit(
        key=(str(env_summary["episode_id"]), int(env_summary["env_idx"])),
        method_name=str(manifest["method_name"]),
        seed=int(manifest["seed"]),
        policy_id=str(manifest["policy_id"]),
        candidate_label=str(manifest["candidate_label"]),
        episode_id=str(env_summary["episode_id"]),
        env_idx=int(env_summary["env_idx"]),
        env_seed=int(env_summary["env_seed"]),
        step_count=int(env_summary["step_count"]),
        return_vector=list(env_summary["return_vector"]),
        final_state=dict(env_summary["final_state"]),
        rows=list(rows),
        risk_row=risk_row,
        questionable_events=questionable_events,
    )


def _tier_sort_key(tier: str) -> tuple[int, str]:
    ordering = {
        "Tier 0 Safe": 0,
        "Tier 1 Near-Miss": 1,
        "Tier 2 Transient Critical Breach": 2,
        "Tier 3 Persistent Critical Breach": 3,
    }
    return (ordering.get(tier, 99), tier)


def _risk_label(summary: dict[str, Any]) -> str:
    ever_rate = float(summary["ever_critical_breach_rate"])
    persistent_rate = float(summary["persistent_critical_breach_rate"])
    high_conf_env_rate = float(summary["high_confidence_env_run_rate"])
    if ever_rate > 0.50 or persistent_rate > 0.25 or high_conf_env_rate >= 0.05:
        return "Red"
    if ever_rate <= 0.25 and persistent_rate <= 0.10 and int(summary["high_confidence_event_count"]) == 0:
        return "Green"
    return "Amber"


def _critical_action_family_metrics(
    env_runs: list[EnvRunAudit],
    *,
    critical_host: str,
) -> tuple[dict[str, float], dict[str, float]]:
    critical_step_counter: Counter[str] = Counter()
    critical_env_counter: Counter[str] = Counter()
    critical_step_total = 0
    critical_env_total = 0

    for run in env_runs:
        run_families: set[str] = set()
        for row in run.rows:
            if not _critical_present_for_action_family(row, critical_host):
                continue
            family = _blue_action_family(row)
            critical_step_counter[family] += 1
            critical_step_total += 1
            run_families.add(family)
        if run_families:
            critical_env_total += 1
            for family in run_families:
                critical_env_counter[family] += 1

    step_rates = {
        family: float(critical_step_counter.get(family, 0) / max(critical_step_total, 1))
        for family in CRITICAL_ACTION_FAMILIES
    }
    env_run_rates = {
        family: float(critical_env_counter.get(family, 0) / max(critical_env_total, 1))
        for family in CRITICAL_ACTION_FAMILIES
    }
    return step_rates, env_run_rates


def _precritical_action_family_metrics(
    env_runs: list[EnvRunAudit],
    *,
    critical_host: str,
    enterprise_hosts: set[str],
) -> tuple[dict[str, float], dict[str, float], float, float]:
    precritical_step_counter: Counter[str] = Counter()
    precritical_env_counter: Counter[str] = Counter()
    precritical_step_total = 0
    precritical_env_total = 0
    compromised_target_focus_step_count = 0
    compromised_target_focus_env_count = 0

    for run in env_runs:
        run_families: set[str] = set()
        run_has_focus = False
        run_has_precritical = False
        for row in run.rows:
            if not _precritical_present_for_action_family(
                row,
                critical_host=critical_host,
                enterprise_hosts=enterprise_hosts,
            ):
                continue
            run_has_precritical = True
            family = _blue_action_family(row)
            precritical_step_counter[family] += 1
            precritical_step_total += 1
            run_families.add(family)
            if _precritical_compromised_target_focus(row):
                compromised_target_focus_step_count += 1
                run_has_focus = True
        if run_has_precritical:
            precritical_env_total += 1
            for family in run_families:
                precritical_env_counter[family] += 1
            if run_has_focus:
                compromised_target_focus_env_count += 1

    step_rates = {
        family: float(
            precritical_step_counter.get(family, 0)
            / max(precritical_step_total, 1)
        )
        for family in PRECRITICAL_ACTION_FAMILIES
    }
    env_run_rates = {
        family: float(
            precritical_env_counter.get(family, 0)
            / max(precritical_env_total, 1)
        )
        for family in PRECRITICAL_ACTION_FAMILIES
    }
    return (
        step_rates,
        env_run_rates,
        float(compromised_target_focus_step_count / max(precritical_step_total, 1)),
        float(compromised_target_focus_env_count / max(precritical_env_total, 1)),
    )


def _build_summary(
    *,
    manifest: dict[str, Any],
    trace_dir: Path,
    env_runs: list[EnvRunAudit],
    env_run_rows: list[dict[str, Any]],
    questionable_events: list[dict[str, Any]],
    critical_host: str,
    critical_path_hosts: list[str],
) -> dict[str, Any]:
    total_env_runs = len(env_run_rows)
    total_trace_steps = int(sum(int(run.step_count) for run in env_runs))
    enterprise_hosts = {
        str(host) for host in critical_path_hosts if str(host) != str(critical_host)
    }
    tier_counts = Counter(str(row["risk_tier"]) for row in env_run_rows)
    high_conf_events = [row for row in questionable_events if row["rule_id"] in HIGH_CONFIDENCE_RULES]
    medium_conf_events = [row for row in questionable_events if row["rule_id"] in MEDIUM_CONFIDENCE_RULES]
    high_conf_env_runs = {
        (row["episode_id"], int(row["env_idx"])) for row in high_conf_events
    }
    medium_conf_env_runs = {
        (row["episode_id"], int(row["env_idx"])) for row in medium_conf_events
    }
    rule_counts = Counter(str(row["rule_id"]) for row in questionable_events)
    rule_env_counts: dict[str, int] = {}
    for rule_id in rule_counts:
        rule_env_counts[rule_id] = len(
            {(row["episode_id"], int(row["env_idx"])) for row in questionable_events if row["rule_id"] == rule_id}
        )
    question_rule_env_rates = {
        rule_id: float(rule_env_counts[rule_id] / max(total_env_runs, 1))
        for rule_id in sorted(rule_env_counts)
    }
    question_rule_step_rates = {
        rule_id: float(rule_counts[rule_id] / max(total_trace_steps, 1))
        for rule_id in sorted(rule_counts)
    }
    shield_active_step_count = int(
        sum(int(row.get("shield_active_step_count", 0)) for row in env_run_rows)
    )
    shield_fallback_step_count = int(
        sum(int(row.get("shield_fallback_step_count", 0)) for row in env_run_rows)
    )
    critical_action_family_step_rates, critical_action_family_env_run_rates = (
        _critical_action_family_metrics(
            env_runs,
            critical_host=critical_host,
        )
    )
    (
        precritical_action_family_step_rates,
        precritical_action_family_env_run_rates,
        precritical_compromised_target_focus_step_rate,
        precritical_compromised_target_focus_env_run_rate,
    ) = _precritical_action_family_metrics(
        env_runs,
        critical_host=critical_host,
        enterprise_hosts=enterprise_hosts,
    )

    summary = {
        "method_name": str(manifest["method_name"]),
        "seed": int(manifest["seed"]),
        "policy_id": str(manifest["policy_id"]),
        "candidate_label": str(manifest["candidate_label"]),
        "trace_eval_episodes": int(manifest.get("eval_episodes", 0)),
        "trace_dir": str(trace_dir.resolve()),
        "critical_host": critical_host,
        "critical_path_hosts": list(critical_path_hosts),
        "tight_thresholds": dict(manifest["tight_thresholds"]),
        "total_env_runs": int(total_env_runs),
        "total_trace_steps": int(total_trace_steps),
        "env_run_feasible_rate": float(mean(float(row["env_run_feasible_flag"]) for row in env_run_rows)) if env_run_rows else 0.0,
        "mean_security_return": float(mean(float(row["security_return"]) for row in env_run_rows)) if env_run_rows else 0.0,
        "mean_business_return": float(mean(float(row["business_return"]) for row in env_run_rows)) if env_run_rows else 0.0,
        "mean_cost_return": float(mean(float(row["cost_return"]) for row in env_run_rows)) if env_run_rows else 0.0,
        "mean_critical_host_safety_return": _mean_or_none(
            row.get("critical_host_safety_return") for row in env_run_rows
        ),
        "business_violation_rate": float(mean(float(row["business_violation_flag"]) for row in env_run_rows)) if env_run_rows else 0.0,
        "cost_violation_rate": float(mean(float(row["cost_violation_flag"]) for row in env_run_rows)) if env_run_rows else 0.0,
        "ever_critical_breach_rate": float(mean(float(row["ever_critical_breach"]) for row in env_run_rows)) if env_run_rows else 0.0,
        "persistent_critical_breach_rate": float(mean(float(row["final_critical_breach"]) for row in env_run_rows)) if env_run_rows else 0.0,
        "mean_critical_dwell_steps": float(mean(float(row["critical_dwell_steps"]) for row in env_run_rows)) if env_run_rows else 0.0,
        "mean_op_server0_impact_count": float(mean(float(row["op_server0_impact_count"]) for row in env_run_rows)) if env_run_rows else 0.0,
        "high_confidence_event_count": int(len(high_conf_events)),
        "high_confidence_env_run_count": int(len(high_conf_env_runs)),
        "high_confidence_env_run_rate": float(len(high_conf_env_runs) / max(total_env_runs, 1)),
        "medium_confidence_event_count": int(len(medium_conf_events)),
        "medium_confidence_env_run_count": int(len(medium_conf_env_runs)),
        "medium_confidence_env_run_rate": float(len(medium_conf_env_runs) / max(total_env_runs, 1)),
        "tier_counts": {tier: int(tier_counts.get(tier, 0)) for tier in sorted(tier_counts, key=_tier_sort_key)},
        "tier_rates": {
            tier: float(tier_counts.get(tier, 0) / max(total_env_runs, 1))
            for tier in sorted(tier_counts, key=_tier_sort_key)
        },
        "tier1_near_miss_rate": 0.0,
        "tier2_transient_critical_breach_rate": 0.0,
        "tier3_persistent_critical_breach_rate": 0.0,
        "questionable_rule_counts": {rule_id: int(rule_counts[rule_id]) for rule_id in sorted(rule_counts)},
        "questionable_rule_env_run_counts": {
            rule_id: int(rule_env_counts[rule_id]) for rule_id in sorted(rule_env_counts)
        },
        "questionable_rule_env_run_rates": dict(question_rule_env_rates),
        "questionable_rule_step_rates": dict(question_rule_step_rates),
        "critical_action_family_step_rates": dict(critical_action_family_step_rates),
        "critical_action_family_env_run_rates": dict(critical_action_family_env_run_rates),
        "precritical_action_family_step_rates": dict(
            precritical_action_family_step_rates
        ),
        "precritical_action_family_env_run_rates": dict(
            precritical_action_family_env_run_rates
        ),
        "precritical_compromised_target_focus_step_rate": float(
            precritical_compromised_target_focus_step_rate
        ),
        "precritical_compromised_target_focus_env_run_rate": float(
            precritical_compromised_target_focus_env_run_rate
        ),
        "shield_active_step_rate": float(
            shield_active_step_count / max(total_trace_steps, 1)
        ),
        "shield_fallback_step_rate": float(
            shield_fallback_step_count / max(total_trace_steps, 1)
        ),
        "mean_shield_blocked_probability_mass": _mean_or_none(
            row.get("mean_shield_blocked_probability_mass") for row in env_run_rows
        ),
    }
    for tier_name in (
        "Tier 0 Safe",
        "Tier 1 Near-Miss",
        "Tier 2 Transient Critical Breach",
        "Tier 3 Persistent Critical Breach",
    ):
        summary["tier_counts"].setdefault(tier_name, 0)
        summary["tier_rates"].setdefault(tier_name, 0.0)
    summary["tier1_near_miss_rate"] = float(summary["tier_rates"]["Tier 1 Near-Miss"])
    summary["tier2_transient_critical_breach_rate"] = float(
        summary["tier_rates"]["Tier 2 Transient Critical Breach"]
    )
    summary["tier3_persistent_critical_breach_rate"] = float(
        summary["tier_rates"]["Tier 3 Persistent Critical Breach"]
    )
    summary["risk_label"] = _risk_label(summary)
    return summary


def _critical_path_heatmap_arrays(
    env_runs: list[EnvRunAudit],
    critical_path_hosts: list[str],
) -> tuple[np.ndarray, np.ndarray]:
    max_step = max((int(row["step_idx"]) for run in env_runs for row in run.rows), default=-1)
    step_count = max_step + 1
    compromise = np.zeros((len(critical_path_hosts), step_count), dtype=np.float32)
    defense = np.zeros((len(critical_path_hosts), step_count), dtype=np.float32)
    samples_by_step = np.zeros((step_count,), dtype=np.float32)
    host_to_index = {hostname: idx for idx, hostname in enumerate(critical_path_hosts)}

    for run in env_runs:
        for row in run.rows:
            step_idx = int(row["step_idx"])
            samples_by_step[step_idx] += 1.0
            for host in _compromised_hosts(row["state_after"]):
                idx = host_to_index.get(str(host))
                if idx is not None:
                    compromise[idx, step_idx] += 1.0
            blue_target = _blue_target_hostname(row)
            if blue_target in host_to_index:
                defense[host_to_index[str(blue_target)], step_idx] += 1.0

    for step_idx in range(step_count):
        denom = max(samples_by_step[step_idx], 1.0)
        compromise[:, step_idx] /= denom
        defense[:, step_idx] /= denom
    return compromise, defense


def _plot_critical_path_heatmap(
    *,
    env_runs: list[EnvRunAudit],
    critical_path_hosts: list[str],
    output_path: Path,
    title: str,
) -> None:
    compromise, defense = _critical_path_heatmap_arrays(env_runs, critical_path_hosts)
    fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
    comp_ax, def_ax = axes
    comp_image = comp_ax.imshow(
        compromise,
        aspect="auto",
        interpolation="nearest",
        cmap="Reds",
        vmin=0.0,
        vmax=1.0,
    )
    def_image = def_ax.imshow(
        defense,
        aspect="auto",
        interpolation="nearest",
        cmap="Blues",
        vmin=0.0,
        vmax=max(float(np.max(defense)), 0.05),
    )
    comp_ax.set_title("Critical-path compromised rate")
    def_ax.set_title("Blue relevant-target rate")
    for ax in axes:
        ax.set_yticks(range(len(critical_path_hosts)))
        ax.set_yticklabels(critical_path_hosts)
        ax.set_ylabel("host")
    def_ax.set_xlabel("step_idx")
    fig.suptitle(title)
    fig.colorbar(comp_image, ax=comp_ax, shrink=0.8, label="rate")
    fig.colorbar(def_image, ax=def_ax, shrink=0.8, label="rate")
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def _first_compromised_enterprise_host(rows: list[dict[str, Any]], enterprise_hosts: list[str]) -> str | None:
    enterprise_set = set(enterprise_hosts)
    for row in rows:
        compromised = set(_compromised_hosts(row["state_after"]))
        for host in enterprise_hosts:
            if host in enterprise_set and host in compromised:
                return host
    return None


def _first_opserver0_impact_step(rows: list[dict[str, Any]], critical_host: str) -> int | None:
    for row in rows:
        if (
            str(row["red_action"].get("name", "")) == "Impact"
            and _red_target_hostname(row) == critical_host
        ):
            return int(row["step_idx"])
    return None


def _select_case_steps(run: EnvRunAudit, anchor_steps: list[int | None], *, max_steps: int = 12) -> list[int]:
    step_universe = [int(row["step_idx"]) for row in run.rows]
    if not step_universe:
        return []
    candidates: list[int] = [0]
    for anchor in anchor_steps:
        if anchor is None:
            continue
        for step in (anchor - 1, anchor, anchor + 1):
            if step in step_universe and step not in candidates:
                candidates.append(step)
            if len(candidates) >= max_steps - 1:
                break
        if len(candidates) >= max_steps - 1:
            break
    final_step = max(step_universe)
    if final_step not in candidates:
        candidates.append(final_step)
    if len(candidates) < 8:
        for step in step_universe:
            if step not in candidates:
                candidates.append(step)
            if len(candidates) >= min(8, len(step_universe)):
                break
    candidates = sorted(candidates)
    return candidates[:max_steps]


def _case_conclusion(run: EnvRunAudit, rule_events: list[dict[str, Any]], enterprise_hosts: list[str], critical_host: str) -> list[str]:
    row = run.risk_row
    earliest_enterprise_host = _first_compromised_enterprise_host(run.rows, enterprise_hosts)
    first_impact_step = _first_opserver0_impact_step(run.rows, critical_host)
    response_delay = row.get("response_delay_after_critical")
    questionable_rules = [event["rule_id"] for event in rule_events[:2]]
    lines = []
    if row["final_critical_breach"]:
        lines.append(
            f"最终 `Op_Server0` 仍处于 critical compromised 状态，说明该 env-run 属于持久打穿而不是短暂失守。"
        )
    elif row["ever_critical_breach"]:
        lines.append(
            f"曾经发生 critical breach，但最终没有维持到结束，属于短暂打穿后部分恢复。"
        )
    else:
        lines.append("没有发生 critical breach，但红方已经沿关键路径形成显著推进。")
    if first_impact_step is not None:
        lines.append(
            f"红方真正完成突破的关键节点是 step {first_impact_step} 对 `{critical_host}` 的 `Impact`。"
        )
    elif earliest_enterprise_host is not None:
        lines.append(
            f"红方的关键推进节点是首先在 `{earliest_enterprise_host}` 建立 foothold。"
        )
    if response_delay is None and row["ever_critical_breach"]:
        lines.append("critical hit 之后没有观察到蓝方对关键路径主机的直接响应。")
    elif response_delay is not None:
        lines.append(f"critical hit 后蓝方首次 relevant response 的延迟为 `{response_delay}` step。")
    if questionable_rules:
        lines.append(f"蓝方最可疑的动作规则是：`{questionable_rules[0]}`" + (f"，以及 `{questionable_rules[1]}`。" if len(questionable_rules) > 1 else "。"))
    return lines


def _overall_critical_action_summary(
    env_runs: list[EnvRunAudit],
    *,
    critical_host: str,
) -> tuple[list[tuple[str, int]], list[tuple[str, int]], list[tuple[str, int]]]:
    family_counter: Counter[str] = Counter()
    recovery_counter: Counter[str] = Counter()
    no_recovery_counter: Counter[str] = Counter()

    for run in env_runs:
        for row in run.rows:
            if not _critical_present_for_action_family(row, critical_host):
                continue
            family = _blue_action_family(row)
            family_counter[family] += 1
            action_name = str(row.get("blue_action", {}).get("name", ""))
            target_hostname = str(row.get("blue_action", {}).get("target_hostname") or "-")
            action_signature = f"{action_name} -> {target_hostname}"
            if row.get("recovered_hosts"):
                recovery_counter[action_signature] += 1
            else:
                no_recovery_counter[action_signature] += 1
    return (
        family_counter.most_common(5),
        recovery_counter.most_common(5),
        no_recovery_counter.most_common(5),
    )


def _overall_precritical_action_summary(
    env_runs: list[EnvRunAudit],
    *,
    critical_host: str,
    enterprise_hosts: set[str],
) -> tuple[list[tuple[str, int]], list[tuple[str, int]], list[tuple[str, int]]]:
    family_counter: Counter[str] = Counter()
    containment_counter: Counter[str] = Counter()
    no_containment_counter: Counter[str] = Counter()

    for run in env_runs:
        for row in run.rows:
            if not _precritical_present_for_action_family(
                row,
                critical_host=critical_host,
                enterprise_hosts=enterprise_hosts,
            ):
                continue
            family = _blue_action_family(row)
            family_counter[family] += 1
            action_name = str(row.get("blue_action", {}).get("name", ""))
            target_hostname = str(
                row.get("blue_action", {}).get("target_hostname") or "-"
            )
            action_signature = f"{action_name} -> {target_hostname}"
            if (
                family in {
                    ACTION_FAMILY_RESTORE,
                    ACTION_FAMILY_REMOVE,
                    ACTION_FAMILY_ANALYSE,
                }
                and _precritical_compromised_target_focus(row)
            ):
                containment_counter[action_signature] += 1
            else:
                no_containment_counter[action_signature] += 1
    return (
        family_counter.most_common(5),
        containment_counter.most_common(5),
        no_containment_counter.most_common(5),
    )


def _write_casebook(
    path: Path,
    env_runs: list[EnvRunAudit],
    *,
    critical_host: str,
    enterprise_hosts: list[str],
) -> None:
    by_key = {run.key: run for run in env_runs}

    def choose_unique(title: str, candidates: list[EnvRunAudit], used: set[tuple[str, int]]) -> tuple[str, EnvRunAudit | None]:
        for candidate in candidates:
            if candidate.key not in used:
                used.add(candidate.key)
                return title, candidate
        return title, candidates[0] if candidates else None

    earliest_critical = sorted(
        [run for run in env_runs if run.risk_row["ever_critical_breach"]],
        key=lambda run: (
            int(run.risk_row["first_critical_hit_step"]),
            run.env_seed,
        ),
    )
    worst_business = sorted(env_runs, key=lambda run: (float(run.risk_row["business_return"]), run.env_seed))
    worst_security = sorted(env_runs, key=lambda run: (float(run.risk_row["security_return"]), run.env_seed))
    max_dwell = sorted(
        env_runs,
        key=lambda run: (-int(run.risk_row["critical_dwell_steps"]), run.env_seed),
    )
    tier0_best = sorted(
        [run for run in env_runs if run.risk_row["risk_tier"] == "Tier 0 Safe"],
        key=lambda run: (-float(run.risk_row["security_return"]), run.env_seed),
    )

    used: set[tuple[str, int]] = set()
    case_specs = [
        choose_unique("Earliest Critical Breach", earliest_critical, used),
        choose_unique("Worst Business Return", worst_business, used),
        choose_unique("Worst Security Return", worst_security, used),
        choose_unique("Max Critical Dwell", max_dwell, used),
        choose_unique("Best Tier 0 Safe Sample", tier0_best, used),
    ]

    lines = ["# Critical Casebook", ""]
    for title, run in case_specs:
        lines.append(f"## {title}")
        lines.append("")
        if run is None:
            lines.append("No matching env-run was available for this case.")
            lines.append("")
            continue
        rule_events = sorted(run.questionable_events, key=lambda event: int(event["step_idx"]))
        lines.append(
            f"- Basic info: `episode_id={run.episode_id}` `env_idx={run.env_idx}` `env_seed={run.env_seed}` `risk_tier={run.risk_row['risk_tier']}`"
        )
        lines.append(
            f"- Returns: `security={_format_float(run.risk_row['security_return'])}` `business={_format_float(run.risk_row['business_return'])}` `cost={_format_float(run.risk_row['cost_return'])}`"
        )
        lines.append(
            f"- Key times: `enterprise_foothold_step={run.risk_row['enterprise_foothold_step']}` `first_critical_hit_step={run.risk_row['first_critical_hit_step']}` `first_relevant_blue_response={run.risk_row['blue_first_relevant_response_step']}`"
        )
        lines.append("")
        lines.append("Key sequence:")
        selected_steps = _select_case_steps(
            run,
            [
                run.risk_row["enterprise_foothold_step"],
                run.risk_row["first_critical_hit_step"],
                run.risk_row["blue_first_relevant_response_step"],
                _first_opserver0_impact_step(run.rows, critical_host),
            ],
        )
        rows_by_step = {int(row["step_idx"]): row for row in run.rows}
        for step_idx in selected_steps:
            row = rows_by_step[step_idx]
            lines.append(
                "- "
                + f"step {step_idx}: Blue `{row['blue_action']['name']}` -> `{row['blue_action'].get('target_hostname') or row['blue_action'].get('target_subnet') or '-'}`; "
                + f"Red `{row['red_action']['name']}` -> `{row['red_action'].get('target_hostname') or row['red_action'].get('target_subnet') or '-'}`; "
                + f"new={_format_list(row.get('newly_compromised_hosts', []))}; "
                + f"recovered={_format_list(row.get('recovered_hosts', []))}; "
                + f"critical_after={_format_list(_critical_hosts(row['state_after']))}"
            )
        lines.append("")
        lines.append("Conclusion:")
        for conclusion_line in _case_conclusion(run, rule_events, enterprise_hosts, critical_host):
            lines.append(f"- {conclusion_line}")
        lines.append("")
    top_action_families, recovery_counts, no_recovery_actions = _overall_critical_action_summary(
        env_runs,
        critical_host=critical_host,
    )
    (
        precritical_action_families,
        precritical_containment_counts,
        precritical_no_containment_actions,
    ) = _overall_precritical_action_summary(
        env_runs,
        critical_host=critical_host,
        enterprise_hosts=set(enterprise_hosts),
    )
    lines.extend(
        [
            "## Critical-Step Action Summary",
            "",
            "### Critical-step top action families",
            "",
        ]
    )
    if top_action_families:
        for family, count in top_action_families:
            lines.append(f"- `{family}`: `{count}` critical-present steps")
    else:
        lines.append("- No critical-present steps were observed.")
    lines.extend(
        [
            "",
            "### Critical-step recovery counts",
            "",
        ]
    )
    if recovery_counts:
        for action_signature, count in recovery_counts:
            lines.append(f"- `{action_signature}`: `{count}` recovery steps")
    else:
        lines.append("- No recovery steps were observed while `critical_present=1`.")
    lines.extend(
        [
            "",
            "### Critical-step no-recovery top actions",
            "",
        ]
    )
    if no_recovery_actions:
        for action_signature, count in no_recovery_actions:
            lines.append(f"- `{action_signature}`: `{count}` no-recovery steps")
    else:
        lines.append("- All critical-present steps included a recovery event.")
    lines.extend(
        [
            "",
            "## Pre-critical containment summary",
            "",
            "### Pre-critical top action families",
            "",
        ]
    )
    if precritical_action_families:
        for family, count in precritical_action_families:
            lines.append(f"- `{family}`: `{count}` pre-critical steps")
    else:
        lines.append("- No pre-critical containment window was observed.")
    lines.extend(
        [
            "",
            "### Pre-critical compromised-target recovery counts",
            "",
        ]
    )
    if precritical_containment_counts:
        for action_signature, count in precritical_containment_counts:
            lines.append(f"- `{action_signature}`: `{count}` containment steps")
    else:
        lines.append(
            "- No compromised-target recovery actions were observed while `enterprise_foothold_present=1 && critical_present=0`."
        )
    lines.extend(
        [
            "",
            "### Pre-critical no-containment top actions",
            "",
        ]
    )
    if precritical_no_containment_actions:
        for action_signature, count in precritical_no_containment_actions:
            lines.append(f"- `{action_signature}`: `{count}` no-containment steps")
    else:
        lines.append("- All pre-critical steps focused on compromised Enterprise/Operational targets.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_semantic_summary(
    path: Path,
    *,
    summary: dict[str, Any],
    comparison: dict[str, Any] | None = None,
) -> None:
    lines = [
        f"# Semantic Risk Summary: {summary['policy_id']}",
        "",
        f"- Candidate: `{summary['candidate_label']}` / `{summary['policy_id']}`",
        f"- Trace dir: `{summary['trace_dir']}`",
        f"- Tight thresholds: `business >= {summary['tight_thresholds']['d_business']}` `cost >= {summary['tight_thresholds']['d_cost']}`",
        f"- Audit verdict: `{summary['risk_label']}`",
        "",
        "## Core Metrics",
        "",
        f"- Mean returns: `security={_format_float(summary['mean_security_return'])}` `business={_format_float(summary['mean_business_return'])}` `cost={_format_float(summary['mean_cost_return'])}`",
    ]
    if summary.get("mean_critical_host_safety_return") is not None:
        lines.append(
            f"- Mean `critical_host_safety`: `{_format_float(summary['mean_critical_host_safety_return'])}`"
        )
    lines.extend(
        [
            f"- Env-run feasible rate: `{_format_float(summary['env_run_feasible_rate'])}`",
            f"- Per-env violation rate: `business={_format_float(summary['business_violation_rate'])}` `cost={_format_float(summary['cost_violation_rate'])}`",
            f"- Critical breach: `ever={_format_float(summary['ever_critical_breach_rate'])}` `persistent={_format_float(summary['persistent_critical_breach_rate'])}`",
            f"- Mean critical dwell steps: `{_format_float(summary['mean_critical_dwell_steps'])}`",
            f"- Mean `{summary['critical_host']}` impact count: `{_format_float(summary['mean_op_server0_impact_count'])}`",
            "",
            "## Risk Tiers",
            "",
        ]
    )
    for tier_name in (
        "Tier 0 Safe",
        "Tier 1 Near-Miss",
        "Tier 2 Transient Critical Breach",
        "Tier 3 Persistent Critical Breach",
    ):
        lines.append(
            f"- `{tier_name}`: count=`{summary['tier_counts'][tier_name]}` rate=`{_format_float(summary['tier_rates'][tier_name])}`"
        )
    lines.extend(
        [
            "",
            "## Questionable Defense Actions",
            "",
            f"- High-confidence events: `count={summary['high_confidence_event_count']}` `env_run_rate={_format_float(summary['high_confidence_env_run_rate'])}`",
            f"- Medium-confidence events: `count={summary['medium_confidence_event_count']}` `env_run_rate={_format_float(summary['medium_confidence_env_run_rate'])}`",
        ]
    )
    if summary["questionable_rule_counts"]:
        for rule_id, count in sorted(summary["questionable_rule_counts"].items()):
            env_count = summary["questionable_rule_env_run_counts"].get(rule_id, 0)
            lines.append(f"- `{rule_id}`: `events={count}` `env_runs={env_count}`")
    else:
        lines.append("- No questionable defense actions were detected under the configured rules.")

    lines.extend(
        [
            "",
            "## Critical Action Families",
            "",
        ]
    )
    for family in CRITICAL_ACTION_FAMILIES:
        lines.append(
            f"- `{family}`: `step_rate={_format_float(summary['critical_action_family_step_rates'].get(family, 0.0))}` "
            + f"`env_run_rate={_format_float(summary['critical_action_family_env_run_rates'].get(family, 0.0))}`"
        )
    lines.extend(
        [
            "",
            "## Pre-Critical Containment",
            "",
        ]
    )
    for family in PRECRITICAL_ACTION_FAMILIES:
        lines.append(
            f"- `{family}`: `step_rate={_format_float(summary['precritical_action_family_step_rates'].get(family, 0.0))}` "
            + f"`env_run_rate={_format_float(summary['precritical_action_family_env_run_rates'].get(family, 0.0))}`"
        )
    lines.append(
        f"- `compromised_target_focus`: `step_rate={_format_float(summary['precritical_compromised_target_focus_step_rate'])}` "
        + f"`env_run_rate={_format_float(summary['precritical_compromised_target_focus_env_run_rate'])}`"
    )

    if comparison is not None:
        current_label = f"{int(summary.get('trace_eval_episodes', 0))}-episode audit"
        comparison_label = f"{int(comparison.get('trace_eval_episodes', 0))}-episode confirmatory audit"
        lines.extend(
            [
                "",
                "## Audit Comparison",
                "",
                "| Audit | env-runs | feasible_rate | ever_critical | persistent_critical | high_conf_env_rate | verdict |",
                "| --- | --- | --- | --- | --- | --- | --- |",
                f"| {current_label} | "
                + " | ".join(
                    [
                        str(summary["total_env_runs"]),
                        _format_float(summary["env_run_feasible_rate"]),
                        _format_float(summary["ever_critical_breach_rate"]),
                        _format_float(summary["persistent_critical_breach_rate"]),
                        _format_float(summary["high_confidence_env_run_rate"]),
                        str(summary["risk_label"]),
                    ]
                )
                + " |",
                f"| {comparison_label} | "
                + " | ".join(
                    [
                        str(comparison["total_env_runs"]),
                        _format_float(comparison["env_run_feasible_rate"]),
                        _format_float(comparison["ever_critical_breach_rate"]),
                        _format_float(comparison["persistent_critical_breach_rate"]),
                        _format_float(comparison["high_confidence_env_run_rate"]),
                        str(comparison["risk_label"]),
                    ]
                )
                + " |",
            ]
        )
        if summary["risk_label"] == "Red" and comparison["risk_label"] == "Red":
            lines.extend(
                [
                    "",
                    "## Final Diagnosis",
                    "",
                    "- `constraint-feasible but semantically fragile`",
                ]
            )
    path.write_text("\n".join(lines), encoding="utf-8")


def _assert_summary_invariants(
    *,
    env_run_rows: list[dict[str, Any]],
    questionable_events: list[dict[str, Any]],
    summary: dict[str, Any],
    expected_policy_id: str,
) -> None:
    if summary["total_env_runs"] != len(env_run_rows):
        raise AssertionError("Summary total_env_runs does not match env_run_risk_table row count")
    if sum(int(count) for count in summary["tier_counts"].values()) != len(env_run_rows):
        raise AssertionError("Tier counts do not add up to total env runs")
    recalculated_ever_rate = mean(float(row["ever_critical_breach"]) for row in env_run_rows) if env_run_rows else 0.0
    if not np.isclose(float(summary["ever_critical_breach_rate"]), float(recalculated_ever_rate)):
        raise AssertionError("ever_critical_breach_rate mismatch")
    if any(str(row["policy_id"]) != expected_policy_id for row in questionable_events):
        raise AssertionError("questionable_defense_actions.csv contains unexpected policy ids")


def _audit_trace_dir(
    *,
    trace_dir: str | Path,
    output_dir: str | Path,
    critical_host: str,
    critical_path_hosts: list[str],
) -> dict[str, Any]:
    trace_dir = Path(trace_dir)
    output_dir = ensure_dir(output_dir)
    manifest = _trace_manifest(trace_dir)
    if str(manifest["policy_id"]) == "":
        raise ValueError("Missing policy_id in trace manifest")
    episode_lookup = _episode_summary_lookup(trace_dir)
    rows_by_key = _trace_rows_by_env_run(trace_dir)
    enterprise_hosts = set(host for host in critical_path_hosts if host != critical_host)
    critical_path_host_set = set(critical_path_hosts)

    env_runs: list[EnvRunAudit] = []
    env_run_rows: list[dict[str, Any]] = []
    questionable_events: list[dict[str, Any]] = []
    for key in sorted(rows_by_key, key=lambda item: (item[0], item[1])):
        if key not in episode_lookup:
            raise KeyError(f"Missing episode summary for env-run {key!r}")
        run = _build_env_run_audit(
            manifest=manifest,
            env_summary=episode_lookup[key],
            rows=rows_by_key[key],
            critical_host=critical_host,
            enterprise_hosts=enterprise_hosts,
            critical_path_hosts=critical_path_host_set,
        )
        env_runs.append(run)
        env_run_rows.append(run.risk_row)
        questionable_events.extend(run.questionable_events)

    summary = _build_summary(
        manifest=manifest,
        trace_dir=trace_dir,
        env_runs=env_runs,
        env_run_rows=env_run_rows,
        questionable_events=questionable_events,
        critical_host=critical_host,
        critical_path_hosts=critical_path_hosts,
    )
    _assert_summary_invariants(
        env_run_rows=env_run_rows,
        questionable_events=questionable_events,
        summary=summary,
        expected_policy_id=str(manifest["policy_id"]),
    )

    _write_csv(output_dir / "env_run_risk_table.csv", env_run_rows)
    save_json(output_dir / "risk_tier_summary.json", summary)
    _write_csv(output_dir / "questionable_defense_actions.csv", questionable_events)
    _write_casebook(
        output_dir / "critical_casebook.md",
        env_runs,
        critical_host=critical_host,
        enterprise_hosts=[host for host in critical_path_hosts if host != critical_host],
    )
    _plot_critical_path_heatmap(
        env_runs=env_runs,
        critical_path_hosts=critical_path_hosts,
        output_path=output_dir / "critical_path_heatmap.png",
        title=f"{manifest['policy_id']} critical-path audit heatmap",
    )
    _write_semantic_summary(
        output_dir / "semantic_risk_summary.md",
        summary=summary,
        comparison=None,
    )
    return summary


def _confirmatory_replay_trace(
    *,
    source_trace_dir: str | Path,
    output_dir: str | Path,
    eval_episodes: int,
) -> Path:
    source_trace_dir = Path(source_trace_dir)
    output_dir = ensure_dir(output_dir)
    manifest = _trace_manifest(source_trace_dir)
    buffer_anchor = resolve_artifact_path(
        str(manifest["buffer_path"]),
        anchor_path=str(manifest.get("buffer_anchor_path", manifest["buffer_path"])),
    )
    payload = load_policy_buffer(buffer_anchor)
    metadata = dict(payload.get("metadata", {}))
    record_lookup = {
        str(record.get("policy_id", "")): record
        for record in list(payload.get("records", [])) + list(payload.get("pareto_front", []))
    }
    policy_id = str(manifest["policy_id"])
    if policy_id not in record_lookup:
        raise KeyError(f"Could not find {policy_id} in {buffer_anchor}")
    candidate = Figure2ReplayCandidate(
        policy_id=policy_id,
        candidate_label=str(manifest["candidate_label"]),
        candidate_aliases=tuple(str(alias) for alias in manifest.get("candidate_aliases", [manifest["candidate_label"]])),
    )
    replay_root = ensure_dir(output_dir / "replay_trace")
    return export_candidate_trace(
        method_name=str(manifest["method_name"]),
        seed=int(manifest["seed"]),
        candidate=candidate,
        buffer_path=buffer_anchor,
        buffer_anchor_path=str(manifest.get("buffer_anchor_path", manifest["buffer_path"])),
        record=record_lookup[policy_id],
        metadata=metadata,
        output_root=replay_root,
        eval_episodes=eval_episodes,
    )


def export_candidate_semantic_audit(
    *,
    trace_dir: str | Path,
    output_dir: str | Path,
    critical_host: str = DEFAULT_CRITICAL_HOST,
    critical_path_hosts: Iterable[str] = DEFAULT_CRITICAL_PATH_HOSTS,
    confirmatory_eval_episodes: int = 0,
    confirmatory_output_dir: str | Path | None = None,
) -> dict[str, Any]:
    critical_path_hosts = [str(host) for host in critical_path_hosts]
    summary = _audit_trace_dir(
        trace_dir=trace_dir,
        output_dir=output_dir,
        critical_host=str(critical_host),
        critical_path_hosts=critical_path_hosts,
    )
    if confirmatory_eval_episodes > 0 and confirmatory_output_dir is not None:
        confirmatory_output_dir = ensure_dir(confirmatory_output_dir)
        replay_trace_dir = _confirmatory_replay_trace(
            source_trace_dir=trace_dir,
            output_dir=confirmatory_output_dir,
            eval_episodes=int(confirmatory_eval_episodes),
        )
        confirmatory_summary = _audit_trace_dir(
            trace_dir=replay_trace_dir,
            output_dir=confirmatory_output_dir,
            critical_host=str(critical_host),
            critical_path_hosts=critical_path_hosts,
        )
        _write_semantic_summary(
            Path(output_dir) / "semantic_risk_summary.md",
            summary=summary,
            comparison=confirmatory_summary,
        )
        _write_semantic_summary(
            Path(confirmatory_output_dir) / "semantic_risk_summary.md",
            summary=confirmatory_summary,
            comparison=summary,
        )
        return {
            "stage_a": summary,
            "stage_b": confirmatory_summary,
            "stage_b_trace_dir": str(replay_trace_dir),
        }
    return {"stage_a": summary}


def _parse_host_list(raw_value: str) -> list[str]:
    return [segment.strip() for segment in raw_value.split(",") if segment.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export semantic tail-risk audit artifacts for a single Figure 2 candidate trace."
    )
    parser.add_argument("--trace-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--critical-host", default=DEFAULT_CRITICAL_HOST)
    parser.add_argument(
        "--critical-path-hosts",
        default=",".join(DEFAULT_CRITICAL_PATH_HOSTS),
        help="Comma-separated hostnames for the critical path.",
    )
    parser.add_argument(
        "--confirmatory-eval-episodes",
        type=int,
        default=0,
        help="When >0, replay the same candidate for this many eval episodes and audit the replay output.",
    )
    parser.add_argument(
        "--confirmatory-output-dir",
        default=None,
        help="Output directory for confirmatory replay trace + audit artifacts.",
    )
    args = parser.parse_args()

    result = export_candidate_semantic_audit(
        trace_dir=args.trace_dir,
        output_dir=args.output_dir,
        critical_host=args.critical_host,
        critical_path_hosts=_parse_host_list(args.critical_path_hosts),
        confirmatory_eval_episodes=int(args.confirmatory_eval_episodes),
        confirmatory_output_dir=args.confirmatory_output_dir,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
