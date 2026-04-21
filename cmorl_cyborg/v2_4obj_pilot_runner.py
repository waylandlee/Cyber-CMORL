from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from cmorl_minicage.buffer import load_policy_buffer
from cmorl_minicage.utils import ensure_dir, load_json, save_json

from .config import (
    DEFAULT_CONSTRAINT_EVALUATE_CONFIG,
    load_constraint_evaluate_config,
    load_stage1_config,
    load_stage2_config,
)
from .evaluate_constraints import evaluate_constraints
from .export_candidate_semantic_audit import export_candidate_semantic_audit
from .export_figure2_attack_defense_trace import (
    Figure2ReplayCandidate,
    export_candidate_trace,
    resolve_artifact_path,
)
from .train_stage1 import train_stage1
from .train_stage2 import train_stage2


DEFAULT_SEED = 11
METHOD_NAME = "ours_stage2_fair_critical_safe_v2_1_4obj"
BASELINE_METHOD_NAME = "ours_stage2_fair"
RUNNER_DIRNAME = "fair_compare_critical_safe_v2_1_4obj_runner"
DEFAULT_STAGE1_CONFIG = (
    Path(__file__).resolve().parent
    / "configs"
    / "paper"
    / "fair_compare_semantic"
    / "stage1_fair_critical_safe_v2_1_4obj_seed_0011.yaml"
)
DEFAULT_STAGE2_CONFIG = (
    Path(__file__).resolve().parent
    / "configs"
    / "paper"
    / "fair_compare_semantic"
    / "stage2_fair_critical_safe_v2_1_4obj_seed_0011.yaml"
)
DEFAULT_THRESHOLDS_PATH = "cmorl_cyborg/outputs/fair_compare_eval/thresholds_tight.json"
DEFAULT_BASELINE_CONSTRAINT_METRICS_PATH = (
    "cmorl_cyborg/outputs/fair_compare_eval/tight/ours_stage2_fair/seed_0011/constraint_metrics.json"
)
DEFAULT_CONSTRAINT_EVAL_EPISODES = 8
DEFAULT_REPLAY_EVAL_EPISODES = 20
ANALYSIS_DIRNAME = "critical_safe_v2_1_4obj_analysis"
SELECTION_MODE_STAGE2_GATE_AWARE = "stage2_gate_aware"
SELECTION_FALLBACK_REASON_NO_STAGE2_CHILD_PASSED_GATE = (
    "no_stage2_child_passed_gate"
)
PILOT_BUSINESS_GUARDRAIL_LIMIT = 8.0
PILOT_COST_GUARDRAIL_LIMIT = 4.0
PILOT_EVER_CRITICAL_BREACH_LIMIT = 0.90
PILOT_FIRST_HIT_DELAY_MIN = 10.0
PILOT_DWELL_IMPROVEMENT_MIN = 5.0
CONSTRAINT_METRIC_FIELDS = (
    "security_return",
    "business_return",
    "cost_return",
    "critical_host_safety_return",
    "critical_host_safety_cvar_alpha",
    "feasible_rate",
    "mean_violation",
    "final_compromised_hosts",
    "final_critical_compromised_hosts",
    "persistent_critical_breach_rate",
    "critical_impact_count",
    "recovered_hosts",
    "analyse_count",
    "remove_count",
    "restore_count",
    "high_disruption_action_rate",
    "ever_critical_breach_rate",
    "mean_first_critical_hit_step",
    "critical_hit_latency_score",
    "mean_critical_dwell_steps",
    "mean_critical_path_compromise_count",
    "sleep_during_critical_breach_rate",
    "user_action_during_critical_breach_rate",
    "user_action_after_enterprise_foothold_rate",
)


def _timestamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _resolve_repo_path(raw_path: str | Path) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return (_repo_root() / path).resolve()


def _load_yaml(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"Config must be a mapping: {path}")
    return payload


def _write_yaml(path: str | Path, payload: dict[str, Any]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(payload, handle, sort_keys=False, allow_unicode=True)
    return path


def _analysis_dirname_from_runner_dirname(runner_dirname: str) -> str:
    normalized = str(runner_dirname)
    if normalized.startswith("fair_compare_"):
        normalized = normalized[len("fair_compare_") :]
    if normalized.endswith("_runner"):
        normalized = normalized[: -len("_runner")]
    return f"{normalized}_analysis"


def _configure_experiment(
    *,
    method_name: str | None = None,
    baseline_method_name: str | None = None,
    runner_dirname: str | None = None,
) -> None:
    global METHOD_NAME, BASELINE_METHOD_NAME, RUNNER_DIRNAME, ANALYSIS_DIRNAME
    METHOD_NAME = str(method_name or METHOD_NAME)
    BASELINE_METHOD_NAME = str(baseline_method_name or BASELINE_METHOD_NAME)
    RUNNER_DIRNAME = str(runner_dirname or RUNNER_DIRNAME)
    ANALYSIS_DIRNAME = _analysis_dirname_from_runner_dirname(RUNNER_DIRNAME)


def _runner_root() -> Path:
    return ensure_dir(_resolve_repo_path(f"cmorl_cyborg/outputs/{RUNNER_DIRNAME}"))


def _generated_config_root() -> Path:
    return ensure_dir(_runner_root() / "generated_configs")


def _stage1_output_root(seed: int) -> Path:
    return _resolve_repo_path(
        f"cmorl_cyborg/outputs/fair_compare_semantic/{METHOD_NAME}/stage1/seed_{seed:04d}"
    )


def _stage2_output_root(seed: int) -> Path:
    return _resolve_repo_path(
        f"cmorl_cyborg/outputs/fair_compare_semantic/{METHOD_NAME}/stage2/seed_{seed:04d}"
    )


def _selected_constraint_metrics_path(seed: int) -> Path:
    return _resolve_repo_path(
        f"cmorl_cyborg/outputs/fair_compare_eval/tight/{METHOD_NAME}/seed_{seed:04d}/constraint_metrics.json"
    )


def _baseline_constraint_metrics_output_path(seed: int) -> Path:
    return _runner_root() / f"seed_{seed:04d}_baseline_constraint_metrics.json"


def _baseline_localized_buffer_output_path(seed: int) -> Path:
    return _runner_root() / f"seed_{seed:04d}_baseline_buffer_localized.json"


def _analysis_root(kind: str, seed: int) -> Path:
    return ensure_dir(
        _resolve_repo_path(
            f"cmorl_cyborg/outputs/paper_appendix/{ANALYSIS_DIRNAME}/{kind}/seed_{seed:04d}"
        )
    )


def _pilot_summary_path(seed: int) -> Path:
    return _runner_root() / f"seed_{seed:04d}_pilot_summary.json"


def _final_summary_path(seed: int) -> Path:
    return _runner_root() / f"seed_{seed:04d}_final_summary.json"


def _selected_constraint_metrics_output_path(seed: int) -> Path:
    return _runner_root() / f"seed_{seed:04d}_selected_constraint_metrics.json"


def _selection_diagnostics_output_path(seed: int) -> Path:
    return _runner_root() / f"seed_{seed:04d}_selection_diagnostics.json"


def _latest_buffer_path(output_root: Path) -> Path:
    buffer_paths = sorted(
        (
            path
            for path in output_root.glob("run_*/solution_buffer.json")
            if path.is_file()
        ),
        key=lambda path: path.stat().st_mtime,
    )
    if not buffer_paths:
        raise FileNotFoundError(f"Could not find solution_buffer.json under {output_root}")
    return buffer_paths[-1].resolve()


def _resolve_existing_stage1_buffer(
    seed: int,
    stage1_buffer_path: str | Path | None = None,
) -> Path:
    if stage1_buffer_path is not None:
        return Path(stage1_buffer_path).resolve()
    return _latest_buffer_path(_stage1_output_root(seed))


def _resolve_existing_stage2_buffer(
    seed: int,
    stage2_buffer_path: str | Path | None = None,
) -> Path:
    if stage2_buffer_path is not None:
        return Path(stage2_buffer_path).resolve()
    return _latest_buffer_path(_stage2_output_root(seed))


def _resolve_checkpoint_for_local_eval(
    raw_path: str | Path,
    *,
    anchor_path: str | Path,
) -> Path:
    resolved = resolve_artifact_path(raw_path, anchor_path=anchor_path)
    if resolved.exists():
        return resolved

    path = Path(raw_path)
    candidates: list[Path] = []
    if path.is_absolute():
        candidates.append(path)
    else:
        anchor = Path(anchor_path)
        probe = anchor if anchor.is_dir() else anchor.parent
        for parent in (probe, *probe.parents):
            if parent.name == "CybORG_plus_plus":
                candidates.append((parent.parent / path).resolve())

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return resolved


def _localize_buffer_for_eval(
    *,
    buffer_path: str | Path,
    output_path: str | Path,
) -> Path:
    source_path = Path(buffer_path).resolve()
    payload = load_policy_buffer(source_path)
    localized = json.loads(json.dumps(payload))
    for section in ("records", "pareto_front"):
        for record in localized.get(section, []):
            checkpoint_path = record.get("checkpoint_path")
            if not checkpoint_path:
                continue
            record["checkpoint_path"] = str(
                _resolve_checkpoint_for_local_eval(
                    checkpoint_path,
                    anchor_path=source_path,
                )
            )
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_json(output_path, localized)
    return output_path.resolve()


def _materialize_stage1_config(*, seed: int, template_path: str | Path) -> Path:
    payload = _load_yaml(template_path)
    payload["seed"] = int(seed)
    payload["output_dir"] = str(_stage1_output_root(seed))
    env_payload = dict(payload.get("env", {}) or {})
    env_payload["seed"] = int(seed)
    payload["env"] = env_payload
    config_path = _generated_config_root() / f"{METHOD_NAME}_stage1_seed_{seed:04d}.yaml"
    return _write_yaml(config_path, payload)


def _materialize_stage2_config(
    *,
    seed: int,
    stage1_buffer_path: str | Path,
    template_path: str | Path,
) -> Path:
    payload = _load_yaml(template_path)
    payload["seed"] = int(seed)
    payload["stage1_buffer"] = str(Path(stage1_buffer_path).resolve())
    payload["output_dir"] = str(_stage2_output_root(seed))
    env_payload = dict(payload.get("env", {}) or {})
    env_payload["seed"] = int(seed)
    payload["env"] = env_payload
    config_path = _generated_config_root() / f"{METHOD_NAME}_stage2_seed_{seed:04d}.yaml"
    return _write_yaml(config_path, payload)


def _record_lookup(buffer_path: str | Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    payload = load_policy_buffer(buffer_path)
    lookup: dict[str, dict[str, Any]] = {}
    for record in list(payload.get("records", [])) + list(payload.get("pareto_front", [])):
        policy_id = str(record.get("policy_id", ""))
        if policy_id and policy_id not in lookup:
            lookup[policy_id] = record
    return payload, lookup


def _objective_vector_signature(raw_vector: Any) -> tuple[float, ...] | None:
    if raw_vector is None:
        return None
    try:
        values = tuple(float(value) for value in raw_vector)
    except TypeError:
        return None
    return values or None


def _objective_vectors_match(
    candidate_vector: Any,
    selected_vector: tuple[float, ...] | None,
    *,
    atol: float = 1e-6,
) -> bool:
    candidate_signature = _objective_vector_signature(candidate_vector)
    if candidate_signature is None or selected_vector is None:
        return False
    if len(candidate_signature) != len(selected_vector):
        return False
    return all(
        abs(float(candidate_value) - float(selected_value)) <= float(atol)
        for candidate_value, selected_value in zip(
            candidate_signature, selected_vector
        )
    )


def _resolve_record_for_replay(
    records: dict[str, dict[str, Any]],
    *,
    selected_policy_id: str,
    selected_objective_vector: Any = None,
    record_label: str,
) -> dict[str, Any]:
    if selected_policy_id in records:
        return records[selected_policy_id]

    objective_signature = _objective_vector_signature(selected_objective_vector)
    if objective_signature is not None:
        matching_records = [
            record
            for record in records.values()
            if _objective_vectors_match(
                record.get("objective_vector"),
                objective_signature,
            )
        ]
        if len(matching_records) == 1:
            return matching_records[0]

    if len(records) == 1:
        return next(iter(records.values()))

    raise KeyError(
        f"Could not find {record_label}: policy_id={selected_policy_id}, "
        f"objective_vector={list(objective_signature) if objective_signature is not None else None}, "
        f"available_policy_ids={sorted(records)}"
    )


def _aggregate_tail_reject_reason_counts(round_summaries: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for round_summary in list(round_summaries or []):
        reason_counts = dict(round_summary.get("tail_reject_reason_counts", {}) or {})
        for reason, value in reason_counts.items():
            counts[str(reason)] = int(counts.get(str(reason), 0)) + int(value)
    return counts


def _constraint_summary_view(
    constraint_metrics: dict[str, Any],
    audit_summary: dict[str, Any],
) -> dict[str, float]:
    return {
        "business_return": float(constraint_metrics["business_return"]),
        "cost_return": float(constraint_metrics["cost_return"]),
        "env_run_feasible_rate": float(constraint_metrics["feasible_rate"]),
        "ever_critical_breach_rate": float(constraint_metrics["ever_critical_breach_rate"]),
        "persistent_critical_breach_rate": float(
            constraint_metrics["persistent_critical_breach_rate"]
        ),
        "mean_first_critical_hit_step": float(
            constraint_metrics["mean_first_critical_hit_step"]
        ),
        "critical_hit_latency_score": float(
            constraint_metrics["critical_hit_latency_score"]
        ),
        "mean_critical_dwell_steps": float(
            constraint_metrics["mean_critical_dwell_steps"]
        ),
        "high_confidence_env_run_rate": float(audit_summary["high_confidence_env_run_rate"]),
        "critical_host_safety_return": float(
            constraint_metrics.get("critical_host_safety_return", 0.0) or 0.0
        ),
        "critical_host_safety_cvar_alpha": float(
            constraint_metrics.get("critical_host_safety_cvar_alpha", 0.0) or 0.0
        ),
    }


def _return_regression(*, baseline_value: float, candidate_value: float) -> float:
    return max(0.0, float(baseline_value) - float(candidate_value))


def _pilot_gate_decision(
    *,
    candidate_policy_id: str,
    candidate_summary: dict[str, Any],
    baseline_summary: dict[str, Any],
) -> dict[str, Any]:
    persistent_drop = float(
        baseline_summary["persistent_critical_breach_rate"]
        - candidate_summary["persistent_critical_breach_rate"]
    )
    ever_drop = float(
        baseline_summary["ever_critical_breach_rate"]
        - candidate_summary["ever_critical_breach_rate"]
    )
    first_hit_delay = float(
        candidate_summary["mean_first_critical_hit_step"]
        - baseline_summary["mean_first_critical_hit_step"]
    )
    latency_improvement = float(
        candidate_summary["critical_hit_latency_score"]
        - baseline_summary["critical_hit_latency_score"]
    )
    business_regression = _return_regression(
        baseline_value=baseline_summary["business_return"],
        candidate_value=candidate_summary["business_return"],
    )
    cost_regression = _return_regression(
        baseline_value=baseline_summary["cost_return"],
        candidate_value=candidate_summary["cost_return"],
    )
    criteria = {
        "stage2_child_selected": bool(str(candidate_policy_id).startswith("stage2_ext_")),
        "persistent_critical_breach_ok": bool(
            candidate_summary["persistent_critical_breach_rate"]
            <= baseline_summary["persistent_critical_breach_rate"]
        ),
        "ever_critical_breach_ok": bool(
            candidate_summary["ever_critical_breach_rate"] < PILOT_EVER_CRITICAL_BREACH_LIMIT
        ),
        "first_hit_delay_ok": bool(
            candidate_summary["mean_first_critical_hit_step"]
            >= baseline_summary["mean_first_critical_hit_step"] + PILOT_FIRST_HIT_DELAY_MIN
        ),
        "critical_dwell_ok": bool(
            candidate_summary["mean_critical_dwell_steps"]
            <= baseline_summary["mean_critical_dwell_steps"] - PILOT_DWELL_IMPROVEMENT_MIN
        ),
        "business_guardrail_ok": bool(
            business_regression <= PILOT_BUSINESS_GUARDRAIL_LIMIT
        ),
        "cost_guardrail_ok": bool(cost_regression <= PILOT_COST_GUARDRAIL_LIMIT),
    }
    failure_reasons = [name for name, passed in criteria.items() if not passed]
    return {
        "persistent_drop": persistent_drop,
        "ever_drop": ever_drop,
        "first_hit_delay": first_hit_delay,
        "latency_improvement": latency_improvement,
        "business_regression": business_regression,
        "cost_regression": cost_regression,
        "criteria": criteria,
        "failure_reasons": failure_reasons,
        "pilot_passed": bool(all(criteria.values())),
    }


def _pilot_comparison(
    *,
    candidate_policy_id: str,
    candidate_summary: dict[str, float],
    baseline_summary: dict[str, float],
) -> dict[str, Any]:
    gate_decision = _pilot_gate_decision(
        candidate_policy_id=candidate_policy_id,
        candidate_summary=candidate_summary,
        baseline_summary=baseline_summary,
    )
    high_confidence_delta = float(
        candidate_summary["high_confidence_env_run_rate"]
        - baseline_summary["high_confidence_env_run_rate"]
    )
    return {
        "candidate": dict(candidate_summary),
        "baseline": dict(baseline_summary),
        "persistent_drop": gate_decision["persistent_drop"],
        "ever_drop": gate_decision["ever_drop"],
        "first_hit_delay": gate_decision["first_hit_delay"],
        "latency_improvement": gate_decision["latency_improvement"],
        "business_regression": gate_decision["business_regression"],
        "cost_regression": gate_decision["cost_regression"],
        "high_confidence_delta": high_confidence_delta,
        "selected_policy_id": str(candidate_policy_id),
        "criteria": dict(gate_decision["criteria"]),
        "failure_reasons": list(gate_decision["failure_reasons"]),
        "pilot_passed": bool(gate_decision["pilot_passed"]),
    }


def _selected_entry_from_constraint_metrics(
    constraint_metrics: dict[str, Any],
) -> dict[str, Any]:
    diagnostics = dict(constraint_metrics.get("selection_diagnostics", {}) or {})
    evaluated_candidates = list(diagnostics.get("evaluated_candidates", []) or [])
    selected_policy_id = str(constraint_metrics.get("selected_policy_id", ""))
    selected_objective_vector = constraint_metrics.get("selected_objective_vector")
    if selected_policy_id:
        for entry in evaluated_candidates:
            if str(entry.get("policy_id", "")) == selected_policy_id:
                return dict(entry)
    objective_signature = _objective_vector_signature(selected_objective_vector)
    if objective_signature is not None:
        for entry in evaluated_candidates:
            if _objective_vectors_match(
                entry.get("objective_vector"),
                objective_signature,
            ):
                return dict(entry)

    fallback_entry: dict[str, Any] = {
        "policy_id": selected_policy_id,
        "objective_vector": list(selected_objective_vector or []),
    }
    for field in CONSTRAINT_METRIC_FIELDS:
        if field in constraint_metrics:
            fallback_entry[field] = constraint_metrics[field]
    return fallback_entry


def _stage2_gate_sort_key(entry: dict[str, Any]) -> tuple[float, ... | str]:
    cvar = entry.get("critical_host_safety_cvar_alpha")
    cvar_value = float(cvar) if cvar is not None else float("-inf")
    return (
        float(entry["persistent_critical_breach_rate"]),
        -cvar_value,
        float(entry["mean_critical_dwell_steps"]),
        float(entry["ever_critical_breach_rate"]),
        -float(entry["critical_hit_latency_score"]),
        float(entry["mean_violation"]),
        str(entry["policy_id"]),
    )


def _build_gate_selection_diagnostics(
    *,
    raw_constraint_metrics: dict[str, Any],
    raw_selected_constraint_metrics_path: Path,
    baseline_constraint_metrics: dict[str, Any],
) -> dict[str, Any]:
    raw_selection_policy = str(
        raw_constraint_metrics.get("selection_policy")
        or raw_constraint_metrics.get("selection_diagnostics", {}).get("selection_policy")
        or "critical_safe_balanced"
    )
    raw_selected_entry = _selected_entry_from_constraint_metrics(raw_constraint_metrics)
    evaluated_candidates = list(
        raw_constraint_metrics.get("selection_diagnostics", {}).get(
            "evaluated_candidates", []
        )
        or []
    )
    stage2_candidates = [
        dict(entry)
        for entry in evaluated_candidates
        if str(entry.get("policy_id", "")).startswith("stage2_ext_")
    ]
    stage2_gate_results: list[dict[str, Any]] = []
    reject_reason_counts: dict[str, int] = {}
    gate_pass_candidates: list[dict[str, Any]] = []
    for candidate in stage2_candidates:
        gate_decision = _pilot_gate_decision(
            candidate_policy_id=str(candidate["policy_id"]),
            candidate_summary=candidate,
            baseline_summary=baseline_constraint_metrics,
        )
        candidate_result = {
            "policy_id": str(candidate["policy_id"]),
            "objective_vector": list(candidate.get("objective_vector", []) or []),
            "business_return": float(candidate["business_return"]),
            "cost_return": float(candidate["cost_return"]),
            "ever_critical_breach_rate": float(candidate["ever_critical_breach_rate"]),
            "persistent_critical_breach_rate": float(
                candidate["persistent_critical_breach_rate"]
            ),
            "critical_host_safety_cvar_alpha": (
                None
                if candidate.get("critical_host_safety_cvar_alpha") is None
                else float(candidate["critical_host_safety_cvar_alpha"])
            ),
            "mean_critical_dwell_steps": float(candidate["mean_critical_dwell_steps"]),
            "mean_first_critical_hit_step": float(candidate["mean_first_critical_hit_step"]),
            "critical_hit_latency_score": float(candidate["critical_hit_latency_score"]),
            "mean_violation": float(candidate["mean_violation"]),
            "business_regression": float(gate_decision["business_regression"]),
            "cost_regression": float(gate_decision["cost_regression"]),
            "persistent_drop": float(gate_decision["persistent_drop"]),
            "ever_drop": float(gate_decision["ever_drop"]),
            "first_hit_delay": float(gate_decision["first_hit_delay"]),
            "latency_improvement": float(gate_decision["latency_improvement"]),
            "criteria": dict(gate_decision["criteria"]),
            "failure_reasons": list(gate_decision["failure_reasons"]),
            "gate_passed": bool(gate_decision["pilot_passed"]),
        }
        stage2_gate_results.append(candidate_result)
        if candidate_result["gate_passed"]:
            gate_pass_candidates.append(candidate)
        else:
            for reason in candidate_result["failure_reasons"]:
                reject_reason_counts[reason] = int(reject_reason_counts.get(reason, 0)) + 1

    if gate_pass_candidates:
        final_selected_entry = min(gate_pass_candidates, key=_stage2_gate_sort_key)
        selection_fallback_used = False
        selection_fallback_reason = None
    else:
        final_selected_entry = raw_selected_entry
        selection_fallback_used = True
        selection_fallback_reason = SELECTION_FALLBACK_REASON_NO_STAGE2_CHILD_PASSED_GATE

    return {
        "selection_mode": SELECTION_MODE_STAGE2_GATE_AWARE,
        "raw_selected_policy_id": str(raw_constraint_metrics["selected_policy_id"]),
        "raw_selected_objective_vector": list(
            raw_constraint_metrics.get("selected_objective_vector", []) or []
        ),
        "raw_selection_policy": raw_selection_policy,
        "raw_selected_constraint_metrics_path": str(raw_selected_constraint_metrics_path),
        "raw_shortlist_policy_ids": list(
            raw_constraint_metrics.get("selection_diagnostics", {}).get(
                "shortlist_policy_ids", []
            )
            or []
        ),
        "selection_fallback_used": bool(selection_fallback_used),
        "selection_fallback_reason": selection_fallback_reason,
        "stage2_candidates_considered": [
            str(candidate["policy_id"]) for candidate in stage2_candidates
        ],
        "stage2_gate_pass_policy_ids": [
            str(candidate["policy_id"]) for candidate in gate_pass_candidates
        ],
        "stage2_gate_reject_reason_counts": dict(reject_reason_counts),
        "stage2_gate_results": stage2_gate_results,
        "selected_policy_id": str(final_selected_entry["policy_id"]),
        "selected_objective_vector": list(
            final_selected_entry.get("objective_vector", []) or []
        ),
        "baseline_policy_id": str(baseline_constraint_metrics.get("selected_policy_id", "")),
    }


def _materialize_selected_constraint_metrics(
    *,
    raw_constraint_metrics: dict[str, Any],
    selected_entry: dict[str, Any],
    selection_diagnostics: dict[str, Any],
) -> dict[str, Any]:
    selected_policy_id = str(selected_entry["policy_id"])
    metrics = json.loads(json.dumps(raw_constraint_metrics))
    raw_selected_policy_id = str(raw_constraint_metrics.get("selected_policy_id", ""))
    selection_changed = selected_policy_id != raw_selected_policy_id
    metrics["selected_policy_id"] = selected_policy_id
    metrics["selected_objective_vector"] = list(selected_entry.get("objective_vector", []) or [])
    metrics["selection_policy"] = SELECTION_MODE_STAGE2_GATE_AWARE
    metrics["selection_diagnostics"] = dict(selection_diagnostics)
    for field in CONSTRAINT_METRIC_FIELDS:
        if field in selected_entry:
            metrics[field] = selected_entry[field]
        elif selection_changed and field in metrics:
            metrics[field] = None
    return metrics


def _run_constraint_eval(
    *,
    method_name: str,
    input_path: str | Path,
    selection_policy: str,
    thresholds_path: str | Path,
    eval_episodes: int,
    output_path: str | Path,
) -> dict[str, Any]:
    defaults = load_constraint_evaluate_config(DEFAULT_CONSTRAINT_EVALUATE_CONFIG)
    metrics = evaluate_constraints(
        method_name=method_name,
        input_kind="buffer",
        input_path=str(Path(input_path).resolve()),
        selection_source="pareto",
        selection_policy=selection_policy,
        thresholds_path=str(_resolve_repo_path(thresholds_path)),
        eval_episodes=int(eval_episodes),
        semantic_metric_weights=dict(defaults.semantic_metric_weights),
        security_margin=float(defaults.security_margin),
        feasible_rate_tolerance=float(defaults.feasible_rate_tolerance),
        mean_violation_tolerance=float(defaults.mean_violation_tolerance),
    )
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_json(output_path, metrics)
    return metrics


def _export_replay_audit(
    *,
    method_name: str,
    seed: int,
    candidate: Figure2ReplayCandidate,
    buffer_path: str | Path,
    record: dict[str, Any],
    metadata: dict[str, Any],
    analysis_kind: str,
    replay_eval_episodes: int,
) -> dict[str, Any]:
    trace_root = _analysis_root(analysis_kind, seed) / "trace"
    audit_root = _analysis_root(analysis_kind, seed)
    trace_dir = export_candidate_trace(
        method_name=method_name,
        seed=int(seed),
        candidate=candidate,
        buffer_path=buffer_path,
        buffer_anchor_path=str(Path(buffer_path).resolve()),
        record=record,
        metadata=metadata,
        output_root=trace_root,
        eval_episodes=int(replay_eval_episodes),
    )
    audit_dir = audit_root / f"{candidate.candidate_label}__{candidate.policy_id}_semantic_audit_replay20"
    audit_result = export_candidate_semantic_audit(
        trace_dir=trace_dir,
        output_dir=audit_dir,
    )
    return {
        "trace_dir": str(trace_dir.resolve()),
        "analysis_dir": str(Path(audit_dir).resolve()),
        "summary_path": str((Path(audit_dir) / "risk_tier_summary.json").resolve()),
        "audit_result": audit_result,
        "summary": dict(audit_result["stage_a"]),
    }


def _resolve_baseline_buffer(seed: int) -> Path:
    default_metrics_path = _resolve_repo_path(
        f"cmorl_cyborg/outputs/fair_compare_eval/tight/{BASELINE_METHOD_NAME}/seed_{seed:04d}/constraint_metrics.json"
    )
    if not default_metrics_path.exists():
        default_metrics_path = _resolve_repo_path(DEFAULT_BASELINE_CONSTRAINT_METRICS_PATH)
    baseline_metrics = load_json(default_metrics_path)
    return resolve_artifact_path(
        str(baseline_metrics["input_path"]),
        anchor_path=default_metrics_path,
    )


def finalize_v2_4obj_pilot(
    *,
    seed: int = DEFAULT_SEED,
    stage1_config_path: str | Path = DEFAULT_STAGE1_CONFIG,
    stage2_config_path: str | Path = DEFAULT_STAGE2_CONFIG,
    stage1_buffer_path: str | Path | None = None,
    stage2_buffer_path: str | Path | None = None,
    thresholds_path: str | Path = DEFAULT_THRESHOLDS_PATH,
    constraint_eval_episodes: int = DEFAULT_CONSTRAINT_EVAL_EPISODES,
    replay_eval_episodes: int = DEFAULT_REPLAY_EVAL_EPISODES,
    method_name: str | None = None,
    baseline_method_name: str | None = None,
    runner_dirname: str | None = None,
) -> dict[str, Any]:
    _configure_experiment(
        method_name=method_name,
        baseline_method_name=baseline_method_name,
        runner_dirname=runner_dirname,
    )
    runner_root = _runner_root()
    runner_root.mkdir(parents=True, exist_ok=True)

    resolved_stage1_buffer = _resolve_existing_stage1_buffer(
        int(seed),
        stage1_buffer_path,
    )
    resolved_stage2_buffer = _resolve_existing_stage2_buffer(
        int(seed),
        stage2_buffer_path,
    )
    materialized_stage1 = _materialize_stage1_config(
        seed=int(seed),
        template_path=stage1_config_path,
    )
    materialized_stage2 = _materialize_stage2_config(
        seed=int(seed),
        stage1_buffer_path=resolved_stage1_buffer,
        template_path=stage2_config_path,
    )
    materialized_stage2_payload = _load_yaml(materialized_stage2)
    raw_selected_constraint_metrics_path = _selected_constraint_metrics_path(seed)

    raw_selected_constraint_metrics = _run_constraint_eval(
        method_name=METHOD_NAME,
        input_path=resolved_stage2_buffer,
        selection_policy="critical_safe_balanced",
        thresholds_path=thresholds_path,
        eval_episodes=int(constraint_eval_episodes),
        output_path=raw_selected_constraint_metrics_path,
    )

    stage2_payload, stage2_records = _record_lookup(resolved_stage2_buffer)
    stage2_round_summaries = list(
        stage2_payload.get("metadata", {}).get("round_summaries", []) or []
    )
    tail_reject_reason_counts = _aggregate_tail_reject_reason_counts(
        stage2_round_summaries
    )

    baseline_buffer_path = _localize_buffer_for_eval(
        buffer_path=_resolve_baseline_buffer(seed),
        output_path=_baseline_localized_buffer_output_path(seed),
    )
    baseline_constraint_metrics = _run_constraint_eval(
        method_name=f"{BASELINE_METHOD_NAME}_objective_baseline",
        input_path=baseline_buffer_path,
        selection_policy="objective",
        thresholds_path=thresholds_path,
        eval_episodes=int(constraint_eval_episodes),
        output_path=_baseline_constraint_metrics_output_path(seed),
    )
    baseline_payload, baseline_records = _record_lookup(baseline_buffer_path)
    baseline_policy_id = str(baseline_constraint_metrics["selected_policy_id"])
    baseline_record = _resolve_record_for_replay(
        baseline_records,
        selected_policy_id=baseline_policy_id,
        selected_objective_vector=baseline_constraint_metrics.get(
            "selected_objective_vector"
        ),
        record_label="baseline policy",
    )

    selection_diagnostics = _build_gate_selection_diagnostics(
        raw_constraint_metrics=raw_selected_constraint_metrics,
        raw_selected_constraint_metrics_path=raw_selected_constraint_metrics_path.resolve(),
        baseline_constraint_metrics=baseline_constraint_metrics,
    )
    save_json(_selection_diagnostics_output_path(seed), selection_diagnostics)
    selected_constraint_metrics = _materialize_selected_constraint_metrics(
        raw_constraint_metrics=raw_selected_constraint_metrics,
        selected_entry=_selected_entry_from_constraint_metrics(
            {
                **raw_selected_constraint_metrics,
                "selected_policy_id": selection_diagnostics["selected_policy_id"],
                "selected_objective_vector": selection_diagnostics["selected_objective_vector"],
            }
        ),
        selection_diagnostics=selection_diagnostics,
    )
    save_json(_selected_constraint_metrics_output_path(seed), selected_constraint_metrics)

    selected_policy_id = str(selected_constraint_metrics["selected_policy_id"])
    selected_record = _resolve_record_for_replay(
        stage2_records,
        selected_policy_id=selected_policy_id,
        selected_objective_vector=selected_constraint_metrics.get(
            "selected_objective_vector"
        ),
        record_label="selected V2 policy",
    )
    selected_tail_acceptance = dict(
        selected_record.get("notes", {}).get("tail_acceptance", {}) or {}
    )
    selected_candidate_label = "critical_safe_balanced_selected"
    selected_candidate_aliases = ("critical_safe_balanced_selected", "selected")
    if selected_policy_id != str(raw_selected_constraint_metrics["selected_policy_id"]):
        selected_candidate_label = "gate_selected"
        selected_candidate_aliases = ("gate_selected", "selected")
    selected_trace = _export_replay_audit(
        method_name=METHOD_NAME,
        seed=int(seed),
        candidate=Figure2ReplayCandidate(
            policy_id=selected_policy_id,
            candidate_label=selected_candidate_label,
            candidate_aliases=selected_candidate_aliases,
        ),
        buffer_path=resolved_stage2_buffer,
        record=selected_record,
        metadata=dict(stage2_payload.get("metadata", {})),
        analysis_kind="pilot",
        replay_eval_episodes=int(replay_eval_episodes),
    )
    baseline_trace = _export_replay_audit(
        method_name=BASELINE_METHOD_NAME,
        seed=int(seed),
        candidate=Figure2ReplayCandidate(
            policy_id=baseline_policy_id,
            candidate_label="objective_selected",
            candidate_aliases=("objective_selected", "selected"),
        ),
        buffer_path=baseline_buffer_path,
        record=baseline_record,
        metadata=dict(baseline_payload.get("metadata", {})),
        analysis_kind="baseline",
        replay_eval_episodes=int(replay_eval_episodes),
    )

    comparison = _pilot_comparison(
        candidate_policy_id=selected_policy_id,
        candidate_summary=_constraint_summary_view(
            selected_constraint_metrics,
            selected_trace["summary"],
        ),
        baseline_summary=_constraint_summary_view(
            baseline_constraint_metrics,
            baseline_trace["summary"],
        ),
    )

    pilot_summary = {
        "generated_at": _timestamp(),
        "seed": int(seed),
        "method_name": METHOD_NAME,
        "baseline_method_name": BASELINE_METHOD_NAME,
        "runner_dirname": RUNNER_DIRNAME,
        "stage1_config_path": str(materialized_stage1.resolve()),
        "stage2_config_path": str(materialized_stage2.resolve()),
        "stage1_buffer_path": str(Path(resolved_stage1_buffer).resolve()),
        "stage2_buffer_path": str(Path(resolved_stage2_buffer).resolve()),
        "selected_policy_id": selected_policy_id,
        "selected_objective_vector": list(
            map(float, selected_constraint_metrics.get("selected_objective_vector", []))
        ),
        "selected_constraint_metrics_path": str(
            _selected_constraint_metrics_output_path(seed).resolve()
        ),
        "selection_diagnostics_path": str(
            _selection_diagnostics_output_path(seed).resolve()
        ),
        "raw_selected_policy_id": str(raw_selected_constraint_metrics["selected_policy_id"]),
        "raw_selected_objective_vector": list(
            map(
                float,
                raw_selected_constraint_metrics.get("selected_objective_vector", []),
            )
        ),
        "raw_selection_policy": str(selection_diagnostics["raw_selection_policy"]),
        "raw_selected_constraint_metrics_path": str(
            raw_selected_constraint_metrics_path.resolve()
        ),
        "selection_mode": str(selection_diagnostics["selection_mode"]),
        "selection_fallback_used": bool(selection_diagnostics["selection_fallback_used"]),
        "selection_fallback_reason": selection_diagnostics["selection_fallback_reason"],
        "stage2_candidates_considered": list(
            selection_diagnostics["stage2_candidates_considered"]
        ),
        "stage2_gate_pass_policy_ids": list(
            selection_diagnostics["stage2_gate_pass_policy_ids"]
        ),
        "stage2_gate_reject_reason_counts": dict(
            selection_diagnostics["stage2_gate_reject_reason_counts"]
        ),
        "selected_trace_dir": selected_trace["trace_dir"],
        "selected_audit_dir": selected_trace["analysis_dir"],
        "selected_risk_summary_path": selected_trace["summary_path"],
        "baseline_policy_id": baseline_policy_id,
        "baseline_constraint_metrics_path": str(
            _baseline_constraint_metrics_output_path(seed).resolve()
        ),
        "baseline_trace_dir": baseline_trace["trace_dir"],
        "baseline_audit_dir": baseline_trace["analysis_dir"],
        "baseline_risk_summary_path": baseline_trace["summary_path"],
        "tail_acceptance_mode": str(
            materialized_stage2_payload.get("tail_acceptance", {}).get("mode", "disabled")
        ),
        "tail_eval_episodes": int(
            materialized_stage2_payload.get("tail_acceptance", {}).get(
                "tail_eval_episodes", 0
            )
        ),
        "tail_alpha": float(
            materialized_stage2_payload.get("tail_acceptance", {}).get(
                "tail_alpha", 0.0
            )
        ),
        "critical_host_safety_cvar_alpha": float(
            comparison["candidate"]["critical_host_safety_cvar_alpha"]
        ),
        "parent_tail_metrics": (
            None
            if not selected_tail_acceptance.get("parent_tail_metrics")
            else dict(selected_tail_acceptance["parent_tail_metrics"])
        ),
        "child_tail_metrics": (
            None
            if not selected_tail_acceptance.get("child_tail_metrics")
            else dict(selected_tail_acceptance["child_tail_metrics"])
        ),
        "tail_reject_reason_counts": dict(tail_reject_reason_counts),
        "baseline_ever_critical_breach_rate": float(
            comparison["baseline"]["ever_critical_breach_rate"]
        ),
        "candidate_ever_critical_breach_rate": float(
            comparison["candidate"]["ever_critical_breach_rate"]
        ),
        "candidate_persistent_critical_breach_rate": float(
            comparison["candidate"]["persistent_critical_breach_rate"]
        ),
        "candidate_critical_hit_latency_score": float(
            comparison["candidate"]["critical_hit_latency_score"]
        ),
        "candidate_mean_first_critical_hit_step": float(
            comparison["candidate"]["mean_first_critical_hit_step"]
        ),
        "candidate_mean_critical_dwell_steps": float(
            comparison["candidate"]["mean_critical_dwell_steps"]
        ),
        "candidate_critical_host_safety_cvar_alpha": float(
            comparison["candidate"]["critical_host_safety_cvar_alpha"]
        ),
        "business_regression": float(comparison["business_regression"]),
        "cost_regression": float(comparison["cost_regression"]),
        "pilot_passed": bool(comparison["pilot_passed"]),
        "failure_reasons": list(comparison["failure_reasons"]),
        "comparison": comparison,
    }
    save_json(_pilot_summary_path(seed), pilot_summary)

    final_summary = {
        "generated_at": _timestamp(),
        "seed": int(seed),
        "method_name": METHOD_NAME,
        "baseline_method_name": BASELINE_METHOD_NAME,
        "runner_dirname": RUNNER_DIRNAME,
        "pilot_passed": bool(comparison["pilot_passed"]),
        "failure_reasons": list(comparison["failure_reasons"]),
        "tail_acceptance_mode": pilot_summary["tail_acceptance_mode"],
        "tail_eval_episodes": pilot_summary["tail_eval_episodes"],
        "tail_alpha": pilot_summary["tail_alpha"],
        "critical_host_safety_cvar_alpha": pilot_summary["critical_host_safety_cvar_alpha"],
        "parent_tail_metrics": pilot_summary["parent_tail_metrics"],
        "child_tail_metrics": pilot_summary["child_tail_metrics"],
        "tail_reject_reason_counts": pilot_summary["tail_reject_reason_counts"],
        "pilot_summary_path": str(_pilot_summary_path(seed).resolve()),
        "selected_policy_id": selected_policy_id,
        "selected_objective_vector": list(pilot_summary["selected_objective_vector"]),
        "selected_constraint_metrics_path": pilot_summary["selected_constraint_metrics_path"],
        "selection_diagnostics_path": pilot_summary["selection_diagnostics_path"],
        "raw_selected_policy_id": pilot_summary["raw_selected_policy_id"],
        "raw_selected_objective_vector": list(pilot_summary["raw_selected_objective_vector"]),
        "raw_selection_policy": pilot_summary["raw_selection_policy"],
        "raw_selected_constraint_metrics_path": pilot_summary[
            "raw_selected_constraint_metrics_path"
        ],
        "selection_mode": pilot_summary["selection_mode"],
        "selection_fallback_used": pilot_summary["selection_fallback_used"],
        "selection_fallback_reason": pilot_summary["selection_fallback_reason"],
        "stage2_candidates_considered": list(
            pilot_summary["stage2_candidates_considered"]
        ),
        "stage2_gate_pass_policy_ids": list(
            pilot_summary["stage2_gate_pass_policy_ids"]
        ),
        "stage2_gate_reject_reason_counts": dict(
            pilot_summary["stage2_gate_reject_reason_counts"]
        ),
        "baseline_policy_id": baseline_policy_id,
        "selected_risk_summary_path": pilot_summary["selected_risk_summary_path"],
        "baseline_constraint_metrics_path": pilot_summary["baseline_constraint_metrics_path"],
        "baseline_risk_summary_path": pilot_summary["baseline_risk_summary_path"],
    }
    save_json(_final_summary_path(seed), final_summary)
    return final_summary


def run_v2_4obj_pilot(
    *,
    seed: int = DEFAULT_SEED,
    stage1_config_path: str | Path = DEFAULT_STAGE1_CONFIG,
    stage2_config_path: str | Path = DEFAULT_STAGE2_CONFIG,
    thresholds_path: str | Path = DEFAULT_THRESHOLDS_PATH,
    constraint_eval_episodes: int = DEFAULT_CONSTRAINT_EVAL_EPISODES,
    replay_eval_episodes: int = DEFAULT_REPLAY_EVAL_EPISODES,
    method_name: str | None = None,
    baseline_method_name: str | None = None,
    runner_dirname: str | None = None,
) -> dict[str, Any]:
    _configure_experiment(
        method_name=method_name,
        baseline_method_name=baseline_method_name,
        runner_dirname=runner_dirname,
    )
    runner_root = _runner_root()
    runner_root.mkdir(parents=True, exist_ok=True)

    materialized_stage1 = _materialize_stage1_config(
        seed=int(seed),
        template_path=stage1_config_path,
    )
    stage1_buffer_path = train_stage1(load_stage1_config(materialized_stage1))

    materialized_stage2 = _materialize_stage2_config(
        seed=int(seed),
        stage1_buffer_path=stage1_buffer_path,
        template_path=stage2_config_path,
    )
    stage2_buffer_path = train_stage2(load_stage2_config(materialized_stage2))

    return finalize_v2_4obj_pilot(
        seed=int(seed),
        stage1_config_path=materialized_stage1,
        stage2_config_path=materialized_stage2,
        stage1_buffer_path=stage1_buffer_path,
        stage2_buffer_path=stage2_buffer_path,
        thresholds_path=thresholds_path,
        constraint_eval_episodes=int(constraint_eval_episodes),
        replay_eval_episodes=int(replay_eval_episodes),
        method_name=METHOD_NAME,
        baseline_method_name=BASELINE_METHOD_NAME,
        runner_dirname=RUNNER_DIRNAME,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the V2.1 four-objective tail-aware Critical-First pilot."
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--stage1-config", default=str(DEFAULT_STAGE1_CONFIG))
    parser.add_argument("--stage2-config", default=str(DEFAULT_STAGE2_CONFIG))
    parser.add_argument("--method-name", default=METHOD_NAME)
    parser.add_argument("--baseline-method-name", default=BASELINE_METHOD_NAME)
    parser.add_argument("--runner-dirname", default=RUNNER_DIRNAME)
    parser.add_argument("--thresholds-path", default=DEFAULT_THRESHOLDS_PATH)
    parser.add_argument("--postprocess-only", action="store_true")
    parser.add_argument("--stage1-buffer", default=None)
    parser.add_argument("--stage2-buffer", default=None)
    parser.add_argument(
        "--constraint-eval-episodes",
        type=int,
        default=DEFAULT_CONSTRAINT_EVAL_EPISODES,
    )
    parser.add_argument(
        "--replay-eval-episodes",
        type=int,
        default=DEFAULT_REPLAY_EVAL_EPISODES,
    )
    args = parser.parse_args()

    if bool(args.postprocess_only):
        summary = finalize_v2_4obj_pilot(
            seed=int(args.seed),
            stage1_config_path=args.stage1_config,
            stage2_config_path=args.stage2_config,
            stage1_buffer_path=args.stage1_buffer,
            stage2_buffer_path=args.stage2_buffer,
            thresholds_path=args.thresholds_path,
            constraint_eval_episodes=int(args.constraint_eval_episodes),
            replay_eval_episodes=int(args.replay_eval_episodes),
            method_name=args.method_name,
            baseline_method_name=args.baseline_method_name,
            runner_dirname=args.runner_dirname,
        )
    else:
        summary = run_v2_4obj_pilot(
            seed=int(args.seed),
            stage1_config_path=args.stage1_config,
            stage2_config_path=args.stage2_config,
            thresholds_path=args.thresholds_path,
            constraint_eval_episodes=int(args.constraint_eval_episodes),
            replay_eval_episodes=int(args.replay_eval_episodes),
            method_name=args.method_name,
            baseline_method_name=args.baseline_method_name,
            runner_dirname=args.runner_dirname,
        )
    print(yaml.safe_dump(summary, sort_keys=False, allow_unicode=True), end="")


if __name__ == "__main__":
    main()
