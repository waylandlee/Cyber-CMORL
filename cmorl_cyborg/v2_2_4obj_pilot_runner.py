from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from cmorl_minicage.utils import load_json, save_json

from .export_figure2_attack_defense_trace import Figure2ReplayCandidate
from .train_stage1 import train_stage1
from .train_stage2 import train_stage2
from .config import load_stage1_config, load_stage2_config
import cmorl_cyborg.v2_4obj_pilot_runner as base


DEFAULT_SEED = 11
METHOD_NAME = "ours_stage2_fair_critical_safe_v2_2_4obj"
BASELINE_METHOD_NAME = "ours_stage2_fair"
RUNNER_DIRNAME = "fair_compare_critical_safe_v2_2_4obj_runner"
DEFAULT_STAGE1_CONFIG = (
    Path(__file__).resolve().parent
    / "configs"
    / "paper"
    / "fair_compare_semantic"
    / "stage1_fair_critical_safe_v2_2_4obj_seed_0011.yaml"
)
DEFAULT_STAGE2_CONFIG = (
    Path(__file__).resolve().parent
    / "configs"
    / "paper"
    / "fair_compare_semantic"
    / "stage2_fair_critical_safe_v2_2_4obj_seed_0011.yaml"
)
DEFAULT_THRESHOLDS_PATH = base.DEFAULT_THRESHOLDS_PATH
DEFAULT_CONSTRAINT_EVAL_EPISODES = base.DEFAULT_CONSTRAINT_EVAL_EPISODES
DEFAULT_REPLAY_EVAL_EPISODES = base.DEFAULT_REPLAY_EVAL_EPISODES
DEFAULT_AUDIT_EVAL_EPISODES = 10
DEFAULT_AUDIT_SHORTLIST_K = 3

SELECTION_MODE_STAGE2_GATE_AUDIT_SHIELDED = "stage2_gate_audit_shielded"
SELECTION_FALLBACK_REASON_NO_STAGE2_CHILD_PASSED_GATE = (
    base.SELECTION_FALLBACK_REASON_NO_STAGE2_CHILD_PASSED_GATE
)
SELECTION_FALLBACK_REASON_NO_CANDIDATE_PASSED_AUDIT_GATE = (
    "no_candidate_passed_audit_gate"
)


def _timestamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _runner_root() -> Path:
    return base._runner_root()


def _pilot_summary_path(seed: int) -> Path:
    return base._pilot_summary_path(seed)


def _final_summary_path(seed: int) -> Path:
    return base._final_summary_path(seed)


def _selected_constraint_metrics_output_path(seed: int) -> Path:
    return base._selected_constraint_metrics_output_path(seed)


def _selection_diagnostics_output_path(seed: int) -> Path:
    return base._selection_diagnostics_output_path(seed)


def _audit_selection_diagnostics_output_path(seed: int) -> Path:
    return _runner_root() / f"seed_{seed:04d}_audit_selection_diagnostics.json"


def _rule_env_run_rate(summary: dict[str, Any], rule_id: str) -> float:
    return float(
        dict(summary.get("questionable_rule_env_run_rates", {}) or {}).get(rule_id, 0.0)
    )


def _comparison_summary_view(
    constraint_metrics: dict[str, Any],
    audit_summary: dict[str, Any],
) -> dict[str, float]:
    return {
        "business_return": float(constraint_metrics["business_return"]),
        "cost_return": float(constraint_metrics["cost_return"]),
        "ever_critical_breach_rate": float(audit_summary["ever_critical_breach_rate"]),
        "persistent_critical_breach_rate": float(
            audit_summary["persistent_critical_breach_rate"]
        ),
        "mean_first_critical_hit_step": float(
            constraint_metrics["mean_first_critical_hit_step"]
        ),
        "critical_hit_latency_score": float(
            constraint_metrics["critical_hit_latency_score"]
        ),
        "mean_critical_dwell_steps": float(audit_summary["mean_critical_dwell_steps"]),
        "high_confidence_env_run_rate": float(audit_summary["high_confidence_env_run_rate"]),
        "q2_user_action_during_critical_breach_env_run_rate": _rule_env_run_rate(
            audit_summary,
            "Q2_user_action_during_critical_breach",
        ),
        "q3_missed_immediate_response_to_critical_hit_env_run_rate": _rule_env_run_rate(
            audit_summary,
            "Q3_missed_immediate_response_to_critical_hit",
        ),
        "q4_user_focus_after_enterprise_foothold_env_run_rate": _rule_env_run_rate(
            audit_summary,
            "Q4_user_focus_after_enterprise_foothold",
        ),
        "q5_repeated_low_value_decoy_loop_env_run_rate": _rule_env_run_rate(
            audit_summary,
            "Q5_repeated_low_value_decoy_loop",
        ),
        "critical_host_safety_return": float(
            constraint_metrics.get("critical_host_safety_return", 0.0) or 0.0
        ),
        "critical_host_safety_cvar_alpha": float(
            constraint_metrics.get("critical_host_safety_cvar_alpha", 0.0) or 0.0
        ),
    }


def _resolve_entry_by_policy_id(
    evaluated_candidates: list[dict[str, Any]],
    policy_id: str,
) -> dict[str, Any]:
    for entry in evaluated_candidates:
        if str(entry.get("policy_id", "")) == str(policy_id):
            return dict(entry)
    raise KeyError(f"Could not resolve evaluated candidate for policy_id={policy_id}")


def _audit_gate_decision(
    *,
    candidate_entry: dict[str, Any],
    short_audit_summary: dict[str, Any],
    baseline_constraint_metrics: dict[str, Any],
    baseline_audit_summary: dict[str, Any],
) -> dict[str, Any]:
    candidate_summary = _comparison_summary_view(
        candidate_entry,
        short_audit_summary,
    )
    baseline_summary = _comparison_summary_view(
        baseline_constraint_metrics,
        baseline_audit_summary,
    )
    business_regression = base._return_regression(
        baseline_value=baseline_summary["business_return"],
        candidate_value=candidate_summary["business_return"],
    )
    cost_regression = base._return_regression(
        baseline_value=baseline_summary["cost_return"],
        candidate_value=candidate_summary["cost_return"],
    )
    q2_limit = max(
        0.0,
        min(
            baseline_summary["q2_user_action_during_critical_breach_env_run_rate"] - 0.10,
            0.60,
        ),
    )
    high_conf_limit = min(baseline_summary["high_confidence_env_run_rate"], 0.70)
    criteria = {
        "persistent_critical_breach_ok": bool(
            candidate_summary["persistent_critical_breach_rate"]
            <= baseline_summary["persistent_critical_breach_rate"]
        ),
        "ever_critical_breach_ok": bool(
            candidate_summary["ever_critical_breach_rate"] <= 0.80
        ),
        "critical_dwell_ok": bool(
            candidate_summary["mean_critical_dwell_steps"]
            <= baseline_summary["mean_critical_dwell_steps"] - 5.0
        ),
        "high_confidence_env_run_rate_ok": bool(
            candidate_summary["high_confidence_env_run_rate"] <= high_conf_limit
        ),
        "q2_user_action_during_critical_breach_ok": bool(
            candidate_summary["q2_user_action_during_critical_breach_env_run_rate"]
            <= q2_limit
        ),
        "q3_missed_immediate_response_to_critical_hit_ok": bool(
            candidate_summary["q3_missed_immediate_response_to_critical_hit_env_run_rate"]
            <= baseline_summary["q3_missed_immediate_response_to_critical_hit_env_run_rate"]
            + 0.02
        ),
        "q4_user_focus_after_enterprise_foothold_ok": bool(
            candidate_summary["q4_user_focus_after_enterprise_foothold_env_run_rate"]
            <= baseline_summary["q4_user_focus_after_enterprise_foothold_env_run_rate"]
        ),
        "q5_repeated_low_value_decoy_loop_ok": bool(
            candidate_summary["q5_repeated_low_value_decoy_loop_env_run_rate"]
            <= baseline_summary["q5_repeated_low_value_decoy_loop_env_run_rate"]
        ),
        "business_guardrail_ok": bool(business_regression <= 8.0),
        "cost_guardrail_ok": bool(cost_regression <= 4.0),
    }
    failure_reasons = [name for name, passed in criteria.items() if not passed]
    return {
        "candidate_summary": candidate_summary,
        "baseline_summary": baseline_summary,
        "business_regression": float(business_regression),
        "cost_regression": float(cost_regression),
        "criteria": criteria,
        "failure_reasons": failure_reasons,
        "audit_gate_passed": bool(all(criteria.values())),
    }


def _audit_sort_key(entry: dict[str, Any]) -> tuple[float | str, ...]:
    cvar = entry.get("critical_host_safety_cvar_alpha")
    cvar_value = float(cvar) if cvar is not None else float("-inf")
    return (
        float(entry["persistent_critical_breach_rate"]),
        float(entry["q2_user_action_during_critical_breach_env_run_rate"]),
        float(entry["high_confidence_env_run_rate"]),
        float(entry["q4_user_focus_after_enterprise_foothold_env_run_rate"]),
        float(entry["mean_critical_dwell_steps"]),
        -cvar_value,
        float(entry["business_regression"]),
        float(entry["cost_regression"]),
        str(entry["policy_id"]),
    )


def _final_candidate_label(
    *,
    raw_selected_policy_id: str,
    gate_selected_policy_id: str,
    final_selected_policy_id: str,
    audit_gate_passed: bool,
) -> str:
    if audit_gate_passed and final_selected_policy_id.startswith("stage2_ext_"):
        return "audit_selected"
    if final_selected_policy_id == gate_selected_policy_id and gate_selected_policy_id != raw_selected_policy_id:
        return "gate_selected"
    return "critical_safe_balanced_selected"


def _combined_selection_diagnostics(
    *,
    gate_selection: dict[str, Any],
    audit_selection: dict[str, Any],
) -> dict[str, Any]:
    payload = dict(gate_selection)
    payload.update(
        {
            "selection_mode": SELECTION_MODE_STAGE2_GATE_AUDIT_SHIELDED,
            "audit_selection_mode": SELECTION_MODE_STAGE2_GATE_AUDIT_SHIELDED,
            "audit_shortlist_policy_ids": list(
                audit_selection.get("audit_shortlist_policy_ids", [])
            ),
            "audit_gate_pass_policy_ids": list(
                audit_selection.get("audit_gate_pass_policy_ids", [])
            ),
            "audit_gate_reject_reason_counts": dict(
                audit_selection.get("audit_gate_reject_reason_counts", {})
            ),
            "selected_short_audit_summary_path": audit_selection.get(
                "selected_short_audit_summary_path"
            ),
            "gate_selected_policy_id": str(audit_selection["gate_selected_policy_id"]),
            "final_selected_policy_id": str(audit_selection["final_selected_policy_id"]),
            "selection_fallback_reason": audit_selection.get("selection_fallback_reason"),
            "selection_fallback_used": bool(
                audit_selection.get("selection_fallback_reason") is not None
            ),
        }
    )
    payload["selected_policy_id"] = str(audit_selection["final_selected_policy_id"])
    payload["selected_objective_vector"] = list(
        audit_selection.get("final_selected_objective_vector", []) or []
    )
    return payload


def _audit_selection(
    *,
    seed: int,
    method_name: str,
    stage2_buffer_path: Path,
    stage2_payload: dict[str, Any],
    stage2_records: dict[str, dict[str, Any]],
    raw_selected_entry: dict[str, Any],
    gate_selection_diagnostics: dict[str, Any],
    baseline_constraint_metrics: dict[str, Any],
    baseline_trace: dict[str, Any],
    shortlist_k: int,
    audit_eval_episodes: int,
) -> dict[str, Any]:
    evaluated_candidates = list(
        gate_selection_diagnostics.get("stage2_gate_results", []) or []
    )
    evaluated_candidate_lookup = {
        str(entry["policy_id"]): _resolve_entry_by_policy_id(
            list(
                gate_selection_diagnostics.get("stage2_gate_results", [])
                or []
            ),
            str(entry["policy_id"]),
        )
        for entry in evaluated_candidates
    }
    raw_evaluated_candidates = list(
        gate_selection_diagnostics.get("stage2_candidates_considered", []) or []
    )
    gate_pass_policy_ids = list(
        gate_selection_diagnostics.get("stage2_gate_pass_policy_ids", []) or []
    )
    raw_eval_entries = list(
        gate_selection_diagnostics.get("raw_selection_diagnostics", {}).get(
            "evaluated_candidates",
            [],
        )
        or []
    )
    raw_eval_lookup = {
        str(entry["policy_id"]): dict(entry) for entry in raw_eval_entries
    }
    gate_pass_entries = [
        raw_eval_lookup[policy_id]
        for policy_id in gate_pass_policy_ids
        if policy_id in raw_eval_lookup
    ]
    shortlist_entries: list[dict[str, Any]]
    pre_audit_fallback_reason = None
    if gate_pass_entries:
        shortlist_entries = sorted(
            gate_pass_entries,
            key=base._stage2_gate_sort_key,
        )[: max(int(shortlist_k), 1)]
    else:
        shortlist_entries = [dict(raw_selected_entry)]
        pre_audit_fallback_reason = (
            SELECTION_FALLBACK_REASON_NO_STAGE2_CHILD_PASSED_GATE
        )

    audit_results: list[dict[str, Any]] = []
    reject_reason_counts: dict[str, int] = {}
    audit_pass_entries: list[dict[str, Any]] = []
    baseline_audit_summary = dict(baseline_trace["summary"])
    stage2_metadata = dict(stage2_payload.get("metadata", {}))
    for shortlist_entry in shortlist_entries:
        policy_id = str(shortlist_entry["policy_id"])
        record = base._resolve_record_for_replay(
            stage2_records,
            selected_policy_id=policy_id,
            selected_objective_vector=shortlist_entry.get("objective_vector"),
            record_label="short-audit candidate",
        )
        short_audit = base._export_replay_audit(
            method_name=method_name,
            seed=int(seed),
            candidate=Figure2ReplayCandidate(
                policy_id=policy_id,
                candidate_label="audit_shortlist",
                candidate_aliases=("audit_shortlist", "selected"),
            ),
            buffer_path=stage2_buffer_path,
            record=record,
            metadata=stage2_metadata,
            analysis_kind="audit_shortlist",
            replay_eval_episodes=int(audit_eval_episodes),
        )
        decision = _audit_gate_decision(
            candidate_entry=shortlist_entry,
            short_audit_summary=short_audit["summary"],
            baseline_constraint_metrics=baseline_constraint_metrics,
            baseline_audit_summary=baseline_audit_summary,
        )
        result = {
            "policy_id": policy_id,
            "objective_vector": list(shortlist_entry.get("objective_vector", []) or []),
            "critical_host_safety_cvar_alpha": shortlist_entry.get(
                "critical_host_safety_cvar_alpha"
            ),
            "business_regression": float(decision["business_regression"]),
            "cost_regression": float(decision["cost_regression"]),
            "criteria": dict(decision["criteria"]),
            "failure_reasons": list(decision["failure_reasons"]),
            "audit_gate_passed": bool(decision["audit_gate_passed"]),
            "short_audit_trace_dir": str(short_audit["trace_dir"]),
            "short_audit_dir": str(short_audit["analysis_dir"]),
            "short_audit_summary_path": str(short_audit["summary_path"]),
            **decision["candidate_summary"],
        }
        audit_results.append(result)
        if result["audit_gate_passed"]:
            audit_pass_entries.append(result)
        else:
            for reason in result["failure_reasons"]:
                reject_reason_counts[reason] = int(reject_reason_counts.get(reason, 0)) + 1

    gate_selected_policy_id = str(gate_selection_diagnostics["selected_policy_id"])
    gate_selected_entry = _resolve_entry_by_policy_id(
        raw_eval_entries,
        gate_selected_policy_id,
    )
    if audit_pass_entries:
        final_selected_entry = min(audit_pass_entries, key=_audit_sort_key)
        selection_fallback_reason = pre_audit_fallback_reason
        audit_gate_passed = True
    else:
        final_selected_entry = dict(gate_selected_entry)
        matching_short = next(
            (
                entry
                for entry in audit_results
                if str(entry["policy_id"]) == str(final_selected_entry["policy_id"])
            ),
            None,
        )
        if matching_short is not None:
            final_selected_entry = dict(matching_short)
        selection_fallback_reason = (
            SELECTION_FALLBACK_REASON_NO_CANDIDATE_PASSED_AUDIT_GATE
        )
        audit_gate_passed = False

    selected_short_audit = next(
        (
            entry
            for entry in audit_results
            if str(entry["policy_id"]) == str(final_selected_entry["policy_id"])
        ),
        None,
    )
    return {
        "audit_selection_mode": SELECTION_MODE_STAGE2_GATE_AUDIT_SHIELDED,
        "raw_selected_policy_id": str(raw_selected_entry["policy_id"]),
        "gate_selected_policy_id": gate_selected_policy_id,
        "final_selected_policy_id": str(final_selected_entry["policy_id"]),
        "final_selected_objective_vector": list(
            final_selected_entry.get("objective_vector", []) or []
        ),
        "audit_shortlist_policy_ids": [
            str(entry["policy_id"]) for entry in shortlist_entries
        ],
        "audit_gate_pass_policy_ids": [
            str(entry["policy_id"]) for entry in audit_pass_entries
        ],
        "audit_gate_reject_reason_counts": dict(reject_reason_counts),
        "audit_results": audit_results,
        "selected_short_audit_summary_path": (
            None
            if selected_short_audit is None
            else str(selected_short_audit["short_audit_summary_path"])
        ),
        "selection_fallback_reason": selection_fallback_reason,
        "pre_audit_selection_fallback_reason": pre_audit_fallback_reason,
        "audit_gate_passed": bool(audit_gate_passed),
    }


def _pilot_gate_decision_v2_2(
    *,
    candidate_policy_id: str,
    candidate_summary: dict[str, float],
    baseline_summary: dict[str, float],
    audit_gate_passed: bool,
) -> dict[str, Any]:
    business_regression = base._return_regression(
        baseline_value=baseline_summary["business_return"],
        candidate_value=candidate_summary["business_return"],
    )
    cost_regression = base._return_regression(
        baseline_value=baseline_summary["cost_return"],
        candidate_value=candidate_summary["cost_return"],
    )
    first_hit_delay = float(
        candidate_summary["mean_first_critical_hit_step"]
        - baseline_summary["mean_first_critical_hit_step"]
    )
    latency_improvement = float(
        candidate_summary["critical_hit_latency_score"]
        - baseline_summary["critical_hit_latency_score"]
    )
    criteria = {
        "audit_gate_passed": bool(audit_gate_passed),
        "stage2_child_selected": bool(str(candidate_policy_id).startswith("stage2_ext_")),
        "ever_critical_breach_ok": bool(
            candidate_summary["ever_critical_breach_rate"] <= 0.80
        ),
        "persistent_critical_breach_ok": bool(
            candidate_summary["persistent_critical_breach_rate"] <= 0.60
        ),
        "latency_or_delay_ok": bool(
            first_hit_delay >= 10.0 or latency_improvement >= 0.10
        ),
        "critical_dwell_ok": bool(
            candidate_summary["mean_critical_dwell_steps"]
            <= baseline_summary["mean_critical_dwell_steps"] - 5.0
        ),
        "q2_user_action_during_critical_breach_ok": bool(
            candidate_summary["q2_user_action_during_critical_breach_env_run_rate"]
            <= 0.60
        ),
        "high_confidence_env_run_rate_ok": bool(
            candidate_summary["high_confidence_env_run_rate"] <= 0.70
        ),
        "business_guardrail_ok": bool(business_regression <= 8.0),
        "cost_guardrail_ok": bool(cost_regression <= 4.0),
    }
    failure_reasons = [name for name, passed in criteria.items() if not passed]
    return {
        "first_hit_delay": float(first_hit_delay),
        "latency_improvement": float(latency_improvement),
        "business_regression": float(business_regression),
        "cost_regression": float(cost_regression),
        "criteria": criteria,
        "failure_reasons": failure_reasons,
        "pilot_passed": bool(all(criteria.values())),
    }


def _pilot_comparison_v2_2(
    *,
    candidate_policy_id: str,
    candidate_summary: dict[str, float],
    baseline_summary: dict[str, float],
    audit_gate_passed: bool,
) -> dict[str, Any]:
    gate = _pilot_gate_decision_v2_2(
        candidate_policy_id=candidate_policy_id,
        candidate_summary=candidate_summary,
        baseline_summary=baseline_summary,
        audit_gate_passed=audit_gate_passed,
    )
    return {
        "candidate": dict(candidate_summary),
        "baseline": dict(baseline_summary),
        "first_hit_delay": float(gate["first_hit_delay"]),
        "latency_improvement": float(gate["latency_improvement"]),
        "business_regression": float(gate["business_regression"]),
        "cost_regression": float(gate["cost_regression"]),
        "selected_policy_id": str(candidate_policy_id),
        "criteria": dict(gate["criteria"]),
        "failure_reasons": list(gate["failure_reasons"]),
        "pilot_passed": bool(gate["pilot_passed"]),
    }


def finalize_v2_2_4obj_pilot(
    *,
    seed: int = DEFAULT_SEED,
    stage1_config_path: str | Path = DEFAULT_STAGE1_CONFIG,
    stage2_config_path: str | Path = DEFAULT_STAGE2_CONFIG,
    stage1_buffer_path: str | Path | None = None,
    stage2_buffer_path: str | Path | None = None,
    thresholds_path: str | Path = DEFAULT_THRESHOLDS_PATH,
    constraint_eval_episodes: int = DEFAULT_CONSTRAINT_EVAL_EPISODES,
    replay_eval_episodes: int = DEFAULT_REPLAY_EVAL_EPISODES,
    audit_eval_episodes: int = DEFAULT_AUDIT_EVAL_EPISODES,
    audit_shortlist_k: int = DEFAULT_AUDIT_SHORTLIST_K,
    method_name: str | None = None,
    baseline_method_name: str | None = None,
    runner_dirname: str | None = None,
) -> dict[str, Any]:
    resolved_method_name = str(method_name or METHOD_NAME)
    resolved_baseline_method_name = str(
        baseline_method_name or BASELINE_METHOD_NAME
    )
    resolved_runner_dirname = str(runner_dirname or RUNNER_DIRNAME)
    base._configure_experiment(
        method_name=resolved_method_name,
        baseline_method_name=resolved_baseline_method_name,
        runner_dirname=resolved_runner_dirname,
    )
    runner_root = _runner_root()
    runner_root.mkdir(parents=True, exist_ok=True)

    resolved_stage1_buffer = base._resolve_existing_stage1_buffer(
        int(seed),
        stage1_buffer_path,
    )
    resolved_stage2_buffer = base._resolve_existing_stage2_buffer(
        int(seed),
        stage2_buffer_path,
    )
    materialized_stage1 = base._materialize_stage1_config(
        seed=int(seed),
        template_path=stage1_config_path,
    )
    materialized_stage2 = base._materialize_stage2_config(
        seed=int(seed),
        stage1_buffer_path=resolved_stage1_buffer,
        template_path=stage2_config_path,
    )
    materialized_stage2_payload = base._load_yaml(materialized_stage2)
    raw_selected_constraint_metrics_path = base._selected_constraint_metrics_path(seed)

    raw_selected_constraint_metrics = base._run_constraint_eval(
        method_name=resolved_method_name,
        input_path=resolved_stage2_buffer,
        selection_policy="critical_safe_balanced",
        thresholds_path=thresholds_path,
        eval_episodes=int(constraint_eval_episodes),
        output_path=raw_selected_constraint_metrics_path,
    )
    stage2_payload, stage2_records = base._record_lookup(resolved_stage2_buffer)
    stage2_round_summaries = list(
        stage2_payload.get("metadata", {}).get("round_summaries", []) or []
    )
    tail_reject_reason_counts = base._aggregate_tail_reject_reason_counts(
        stage2_round_summaries
    )

    baseline_buffer_path = base._localize_buffer_for_eval(
        buffer_path=base._resolve_baseline_buffer(seed),
        output_path=base._baseline_localized_buffer_output_path(seed),
    )
    baseline_constraint_metrics = base._run_constraint_eval(
        method_name=f"{resolved_baseline_method_name}_objective_baseline",
        input_path=baseline_buffer_path,
        selection_policy="objective",
        thresholds_path=thresholds_path,
        eval_episodes=int(constraint_eval_episodes),
        output_path=base._baseline_constraint_metrics_output_path(seed),
    )
    baseline_payload, baseline_records = base._record_lookup(baseline_buffer_path)
    baseline_policy_id = str(baseline_constraint_metrics["selected_policy_id"])
    baseline_record = base._resolve_record_for_replay(
        baseline_records,
        selected_policy_id=baseline_policy_id,
        selected_objective_vector=baseline_constraint_metrics.get(
            "selected_objective_vector"
        ),
        record_label="baseline policy",
    )
    baseline_trace = base._export_replay_audit(
        method_name=resolved_baseline_method_name,
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

    gate_selection_diagnostics = base._build_gate_selection_diagnostics(
        raw_constraint_metrics=raw_selected_constraint_metrics,
        raw_selected_constraint_metrics_path=raw_selected_constraint_metrics_path.resolve(),
        baseline_constraint_metrics=baseline_constraint_metrics,
    )
    gate_selection_diagnostics["raw_selection_diagnostics"] = dict(
        raw_selected_constraint_metrics.get("selection_diagnostics", {}) or {}
    )
    save_json(_selection_diagnostics_output_path(seed), gate_selection_diagnostics)

    raw_selected_entry = base._selected_entry_from_constraint_metrics(
        raw_selected_constraint_metrics
    )
    audit_selection_diagnostics = _audit_selection(
        seed=int(seed),
        method_name=resolved_method_name,
        stage2_buffer_path=Path(resolved_stage2_buffer).resolve(),
        stage2_payload=stage2_payload,
        stage2_records=stage2_records,
        raw_selected_entry=raw_selected_entry,
        gate_selection_diagnostics=gate_selection_diagnostics,
        baseline_constraint_metrics=baseline_constraint_metrics,
        baseline_trace=baseline_trace,
        shortlist_k=int(audit_shortlist_k),
        audit_eval_episodes=int(audit_eval_episodes),
    )
    save_json(
        _audit_selection_diagnostics_output_path(seed),
        audit_selection_diagnostics,
    )

    combined_selection = _combined_selection_diagnostics(
        gate_selection=gate_selection_diagnostics,
        audit_selection=audit_selection_diagnostics,
    )
    final_selected_entry = _resolve_entry_by_policy_id(
        list(
            raw_selected_constraint_metrics.get("selection_diagnostics", {}).get(
                "evaluated_candidates",
                [],
            )
            or []
        ),
        str(audit_selection_diagnostics["final_selected_policy_id"]),
    )
    selected_constraint_metrics = base._materialize_selected_constraint_metrics(
        raw_constraint_metrics=raw_selected_constraint_metrics,
        selected_entry=final_selected_entry,
        selection_diagnostics=combined_selection,
    )
    selected_constraint_metrics["selection_policy"] = (
        SELECTION_MODE_STAGE2_GATE_AUDIT_SHIELDED
    )
    save_json(
        _selected_constraint_metrics_output_path(seed),
        selected_constraint_metrics,
    )

    selected_policy_id = str(selected_constraint_metrics["selected_policy_id"])
    selected_record = base._resolve_record_for_replay(
        stage2_records,
        selected_policy_id=selected_policy_id,
        selected_objective_vector=selected_constraint_metrics.get(
            "selected_objective_vector"
        ),
        record_label="selected V2.2 policy",
    )
    selected_tail_acceptance = dict(
        selected_record.get("notes", {}).get("tail_acceptance", {}) or {}
    )
    selected_trace = base._export_replay_audit(
        method_name=resolved_method_name,
        seed=int(seed),
        candidate=Figure2ReplayCandidate(
            policy_id=selected_policy_id,
            candidate_label=_final_candidate_label(
                raw_selected_policy_id=str(raw_selected_constraint_metrics["selected_policy_id"]),
                gate_selected_policy_id=str(audit_selection_diagnostics["gate_selected_policy_id"]),
                final_selected_policy_id=selected_policy_id,
                audit_gate_passed=bool(audit_selection_diagnostics["audit_gate_passed"]),
            ),
            candidate_aliases=("selected", "audit_selected"),
        ),
        buffer_path=resolved_stage2_buffer,
        record=selected_record,
        metadata=dict(stage2_payload.get("metadata", {})),
        analysis_kind="pilot",
        replay_eval_episodes=int(replay_eval_episodes),
    )

    comparison = _pilot_comparison_v2_2(
        candidate_policy_id=selected_policy_id,
        candidate_summary=_comparison_summary_view(
            selected_constraint_metrics,
            selected_trace["summary"],
        ),
        baseline_summary=_comparison_summary_view(
            baseline_constraint_metrics,
            baseline_trace["summary"],
        ),
        audit_gate_passed=bool(audit_selection_diagnostics["audit_gate_passed"]),
    )

    pilot_summary = {
        "generated_at": _timestamp(),
        "seed": int(seed),
        "method_name": resolved_method_name,
        "baseline_method_name": resolved_baseline_method_name,
        "runner_dirname": resolved_runner_dirname,
        "stage1_config_path": str(Path(materialized_stage1).resolve()),
        "stage2_config_path": str(Path(materialized_stage2).resolve()),
        "stage1_buffer_path": str(Path(resolved_stage1_buffer).resolve()),
        "stage2_buffer_path": str(Path(resolved_stage2_buffer).resolve()),
        "selection_mode": SELECTION_MODE_STAGE2_GATE_AUDIT_SHIELDED,
        "audit_selection_mode": SELECTION_MODE_STAGE2_GATE_AUDIT_SHIELDED,
        "selected_policy_id": selected_policy_id,
        "final_selected_policy_id": selected_policy_id,
        "selected_objective_vector": list(
            map(float, selected_constraint_metrics.get("selected_objective_vector", []))
        ),
        "selected_constraint_metrics_path": str(
            _selected_constraint_metrics_output_path(seed).resolve()
        ),
        "selection_diagnostics_path": str(
            _selection_diagnostics_output_path(seed).resolve()
        ),
        "audit_selection_diagnostics_path": str(
            _audit_selection_diagnostics_output_path(seed).resolve()
        ),
        "raw_selected_policy_id": str(raw_selected_constraint_metrics["selected_policy_id"]),
        "gate_selected_policy_id": str(audit_selection_diagnostics["gate_selected_policy_id"]),
        "raw_selection_policy": str(
            gate_selection_diagnostics.get("raw_selection_policy", "critical_safe_balanced")
        ),
        "raw_selected_constraint_metrics_path": str(
            raw_selected_constraint_metrics_path.resolve()
        ),
        "selection_fallback_reason": audit_selection_diagnostics.get(
            "selection_fallback_reason"
        ),
        "selection_fallback_used": bool(
            audit_selection_diagnostics.get("selection_fallback_reason") is not None
        ),
        "stage2_candidates_considered": list(
            gate_selection_diagnostics["stage2_candidates_considered"]
        ),
        "stage2_gate_pass_policy_ids": list(
            gate_selection_diagnostics["stage2_gate_pass_policy_ids"]
        ),
        "stage2_gate_reject_reason_counts": dict(
            gate_selection_diagnostics["stage2_gate_reject_reason_counts"]
        ),
        "audit_shortlist_policy_ids": list(
            audit_selection_diagnostics["audit_shortlist_policy_ids"]
        ),
        "audit_gate_pass_policy_ids": list(
            audit_selection_diagnostics["audit_gate_pass_policy_ids"]
        ),
        "audit_gate_reject_reason_counts": dict(
            audit_selection_diagnostics["audit_gate_reject_reason_counts"]
        ),
        "selected_short_audit_summary_path": audit_selection_diagnostics.get(
            "selected_short_audit_summary_path"
        ),
        "selected_trace_dir": selected_trace["trace_dir"],
        "selected_audit_dir": selected_trace["analysis_dir"],
        "selected_risk_summary_path": selected_trace["summary_path"],
        "baseline_policy_id": baseline_policy_id,
        "baseline_constraint_metrics_path": str(
            base._baseline_constraint_metrics_output_path(seed).resolve()
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
        "pilot_passed": bool(comparison["pilot_passed"]),
        "failure_reasons": list(comparison["failure_reasons"]),
        "comparison": comparison,
    }
    save_json(_pilot_summary_path(seed), pilot_summary)

    final_summary = {
        "generated_at": _timestamp(),
        "seed": int(seed),
        "method_name": resolved_method_name,
        "baseline_method_name": resolved_baseline_method_name,
        "runner_dirname": resolved_runner_dirname,
        "selection_mode": SELECTION_MODE_STAGE2_GATE_AUDIT_SHIELDED,
        "audit_selection_mode": SELECTION_MODE_STAGE2_GATE_AUDIT_SHIELDED,
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
        "raw_selected_policy_id": pilot_summary["raw_selected_policy_id"],
        "gate_selected_policy_id": pilot_summary["gate_selected_policy_id"],
        "final_selected_policy_id": selected_policy_id,
        "selected_objective_vector": list(pilot_summary["selected_objective_vector"]),
        "selected_constraint_metrics_path": pilot_summary["selected_constraint_metrics_path"],
        "selection_diagnostics_path": pilot_summary["selection_diagnostics_path"],
        "audit_selection_diagnostics_path": pilot_summary[
            "audit_selection_diagnostics_path"
        ],
        "selection_fallback_used": pilot_summary["selection_fallback_used"],
        "selection_fallback_reason": pilot_summary["selection_fallback_reason"],
        "audit_shortlist_policy_ids": list(pilot_summary["audit_shortlist_policy_ids"]),
        "audit_gate_pass_policy_ids": list(pilot_summary["audit_gate_pass_policy_ids"]),
        "audit_gate_reject_reason_counts": dict(
            pilot_summary["audit_gate_reject_reason_counts"]
        ),
        "selected_short_audit_summary_path": pilot_summary[
            "selected_short_audit_summary_path"
        ],
        "selected_risk_summary_path": pilot_summary["selected_risk_summary_path"],
        "baseline_constraint_metrics_path": pilot_summary["baseline_constraint_metrics_path"],
        "baseline_risk_summary_path": pilot_summary["baseline_risk_summary_path"],
    }
    save_json(_final_summary_path(seed), final_summary)
    return final_summary


def run_v2_2_4obj_pilot(
    *,
    seed: int = DEFAULT_SEED,
    stage1_config_path: str | Path = DEFAULT_STAGE1_CONFIG,
    stage2_config_path: str | Path = DEFAULT_STAGE2_CONFIG,
    thresholds_path: str | Path = DEFAULT_THRESHOLDS_PATH,
    constraint_eval_episodes: int = DEFAULT_CONSTRAINT_EVAL_EPISODES,
    replay_eval_episodes: int = DEFAULT_REPLAY_EVAL_EPISODES,
    audit_eval_episodes: int = DEFAULT_AUDIT_EVAL_EPISODES,
    audit_shortlist_k: int = DEFAULT_AUDIT_SHORTLIST_K,
    method_name: str | None = None,
    baseline_method_name: str | None = None,
    runner_dirname: str | None = None,
) -> dict[str, Any]:
    resolved_method_name = str(method_name or METHOD_NAME)
    resolved_baseline_method_name = str(
        baseline_method_name or BASELINE_METHOD_NAME
    )
    resolved_runner_dirname = str(runner_dirname or RUNNER_DIRNAME)
    base._configure_experiment(
        method_name=resolved_method_name,
        baseline_method_name=resolved_baseline_method_name,
        runner_dirname=resolved_runner_dirname,
    )
    runner_root = _runner_root()
    runner_root.mkdir(parents=True, exist_ok=True)

    materialized_stage1 = base._materialize_stage1_config(
        seed=int(seed),
        template_path=stage1_config_path,
    )
    stage1_buffer_path = train_stage1(load_stage1_config(materialized_stage1))

    materialized_stage2 = base._materialize_stage2_config(
        seed=int(seed),
        stage1_buffer_path=stage1_buffer_path,
        template_path=stage2_config_path,
    )
    stage2_buffer_path = train_stage2(load_stage2_config(materialized_stage2))

    return finalize_v2_2_4obj_pilot(
        seed=int(seed),
        stage1_config_path=materialized_stage1,
        stage2_config_path=materialized_stage2,
        stage1_buffer_path=stage1_buffer_path,
        stage2_buffer_path=stage2_buffer_path,
        thresholds_path=thresholds_path,
        constraint_eval_episodes=int(constraint_eval_episodes),
        replay_eval_episodes=int(replay_eval_episodes),
        audit_eval_episodes=int(audit_eval_episodes),
        audit_shortlist_k=int(audit_shortlist_k),
        method_name=resolved_method_name,
        baseline_method_name=resolved_baseline_method_name,
        runner_dirname=resolved_runner_dirname,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the V2.2 audit-aware shielded Critical-First pilot."
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
    parser.add_argument(
        "--audit-eval-episodes",
        type=int,
        default=DEFAULT_AUDIT_EVAL_EPISODES,
    )
    parser.add_argument(
        "--audit-shortlist-k",
        type=int,
        default=DEFAULT_AUDIT_SHORTLIST_K,
    )
    args = parser.parse_args()

    if bool(args.postprocess_only):
        summary = finalize_v2_2_4obj_pilot(
            seed=int(args.seed),
            stage1_config_path=args.stage1_config,
            stage2_config_path=args.stage2_config,
            stage1_buffer_path=args.stage1_buffer,
            stage2_buffer_path=args.stage2_buffer,
            thresholds_path=args.thresholds_path,
            constraint_eval_episodes=int(args.constraint_eval_episodes),
            replay_eval_episodes=int(args.replay_eval_episodes),
            audit_eval_episodes=int(args.audit_eval_episodes),
            audit_shortlist_k=int(args.audit_shortlist_k),
            method_name=args.method_name,
            baseline_method_name=args.baseline_method_name,
            runner_dirname=args.runner_dirname,
        )
    else:
        summary = run_v2_2_4obj_pilot(
            seed=int(args.seed),
            stage1_config_path=args.stage1_config,
            stage2_config_path=args.stage2_config,
            thresholds_path=args.thresholds_path,
            constraint_eval_episodes=int(args.constraint_eval_episodes),
            replay_eval_episodes=int(args.replay_eval_episodes),
            audit_eval_episodes=int(args.audit_eval_episodes),
            audit_shortlist_k=int(args.audit_shortlist_k),
            method_name=args.method_name,
            baseline_method_name=args.baseline_method_name,
            runner_dirname=args.runner_dirname,
        )
    print(yaml.safe_dump(summary, sort_keys=False, allow_unicode=True), end="")


if __name__ == "__main__":
    main()
