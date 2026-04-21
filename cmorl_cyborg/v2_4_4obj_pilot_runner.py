from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from cmorl_minicage.utils import load_json, save_json

import cmorl_cyborg.v2_2_4obj_pilot_runner as v2_2
import cmorl_cyborg.v2_4obj_pilot_runner as base


DEFAULT_SEED = 11
METHOD_NAME = "ours_stage2_fair_critical_safe_v2_4_4obj"
BASELINE_METHOD_NAME = "ours_stage2_fair"
RUNNER_DIRNAME = "fair_compare_critical_safe_v2_4_4obj_runner"
DEFAULT_STAGE1_CONFIG = (
    Path(__file__).resolve().parent
    / "configs"
    / "paper"
    / "fair_compare_semantic"
    / "stage1_fair_critical_safe_v2_4_4obj_seed_0011.yaml"
)
DEFAULT_STAGE2_CONFIG = (
    Path(__file__).resolve().parent
    / "configs"
    / "paper"
    / "fair_compare_semantic"
    / "stage2_fair_critical_safe_v2_4_4obj_seed_0011.yaml"
)
DEFAULT_THRESHOLDS_PATH = v2_2.DEFAULT_THRESHOLDS_PATH
DEFAULT_CONSTRAINT_EVAL_EPISODES = v2_2.DEFAULT_CONSTRAINT_EVAL_EPISODES
DEFAULT_REPLAY_EVAL_EPISODES = v2_2.DEFAULT_REPLAY_EVAL_EPISODES
DEFAULT_AUDIT_EVAL_EPISODES = v2_2.DEFAULT_AUDIT_EVAL_EPISODES
DEFAULT_AUDIT_SHORTLIST_K = v2_2.DEFAULT_AUDIT_SHORTLIST_K
DEFAULT_MULTI_SEEDS = (7, 11, 19)

REFERENCE_V2_3_RUNNER_DIRNAME = "fair_compare_critical_safe_v2_3_4obj_runner"
CONTAINMENT_STATUS_EVALUABLE = "evaluable"
CONTAINMENT_STATUS_NOT_EVALUABLE = "not_evaluable"


def _runner_root() -> Path:
    return Path(
        base._resolve_repo_path(f"cmorl_cyborg/outputs/{RUNNER_DIRNAME}")
    ).resolve()


def _pilot_summary_path(seed: int) -> Path:
    return _runner_root() / f"seed_{seed:04d}_pilot_summary.json"


def _final_summary_path(seed: int) -> Path:
    return _runner_root() / f"seed_{seed:04d}_final_summary.json"


def _reference_v2_3_final_summary_path(seed: int) -> Path:
    return Path(
        base._resolve_repo_path(
            f"cmorl_cyborg/outputs/{REFERENCE_V2_3_RUNNER_DIRNAME}/seed_{seed:04d}_final_summary.json"
        )
    ).resolve()


def _reference_v2_3_analysis_root(kind: str, seed: int) -> Path:
    return Path(
        base._resolve_repo_path(
            f"cmorl_cyborg/outputs/paper_appendix/critical_safe_v2_3_4obj_analysis/{kind}/seed_{seed:04d}"
        )
    ).resolve()


def _load_json_if_exists(path: str | Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    resolved = Path(path)
    if not resolved.exists():
        return None
    payload = load_json(resolved)
    if not isinstance(payload, dict):
        return None
    return dict(payload)


def _rate_sum(payload: dict[str, Any] | None, *keys: str) -> float | None:
    if payload is None:
        return None
    total = 0.0
    for key in keys:
        if key not in payload:
            return None
        total += float(payload[key])
    return float(total)


def _has_precritical_reference_metrics(summary: dict[str, Any] | None) -> bool:
    if summary is None:
        return False
    return all(
        key in summary
        for key in (
            "precritical_action_family_step_rates",
            "precritical_action_family_env_run_rates",
            "precritical_compromised_target_focus_step_rate",
            "precritical_compromised_target_focus_env_run_rate",
        )
    )


def _reference_v2_3_selected_trace_dir(seed: int) -> Path | None:
    reference_final_summary = _load_json_if_exists(_reference_v2_3_final_summary_path(seed))
    if reference_final_summary is None:
        return None
    policy_id = str(reference_final_summary.get("selected_policy_id", "")).strip()
    selected_risk_summary_path = reference_final_summary.get("selected_risk_summary_path")
    if not policy_id or not selected_risk_summary_path:
        return None

    audit_dirname = Path(str(selected_risk_summary_path)).resolve().parent.name
    candidate_label = audit_dirname.split("__", 1)[0]
    if not candidate_label:
        return None

    preferred_trace_dir = (
        _reference_v2_3_analysis_root("pilot", seed)
        / "trace"
        / "ours_stage2_fair_critical_safe_v2_3_4obj"
        / f"seed_{seed:04d}"
        / f"{candidate_label}__{policy_id}"
    )
    if preferred_trace_dir.exists():
        return preferred_trace_dir.resolve()

    trace_root = _reference_v2_3_analysis_root("pilot", seed) / "trace"
    if not trace_root.exists():
        return None
    matches = sorted(trace_root.glob(f"**/{candidate_label}__{policy_id}/trace_manifest.json"))
    if not matches:
        return None
    return matches[-1].parent.resolve()


def backfill_reference_v2_3_selected_audit(
    seed: int = DEFAULT_SEED,
) -> dict[str, Any]:
    reference_final_summary_path = _reference_v2_3_final_summary_path(int(seed))
    reference_final_summary = _load_json_if_exists(reference_final_summary_path)
    if reference_final_summary is None:
        return {
            "seed": int(seed),
            "reference_v2_3_final_summary_path": str(reference_final_summary_path),
            "reference_v2_3_available": False,
            "selected_trace_dir": None,
            "selected_audit_dir": None,
            "backfill_performed": False,
            "precritical_metrics_available": False,
        }

    selected_audit_dir = Path(
        str(reference_final_summary.get("selected_risk_summary_path", ""))
    ).resolve().parent
    trace_dir = _reference_v2_3_selected_trace_dir(int(seed))
    if trace_dir is None:
        return {
            "seed": int(seed),
            "reference_v2_3_final_summary_path": str(reference_final_summary_path),
            "reference_v2_3_available": True,
            "selected_trace_dir": None,
            "selected_audit_dir": str(selected_audit_dir),
            "backfill_performed": False,
            "precritical_metrics_available": _has_precritical_reference_metrics(
                _load_json_if_exists(reference_final_summary.get("selected_risk_summary_path"))
            ),
        }

    audit_result = base.export_candidate_semantic_audit(
        trace_dir=trace_dir,
        output_dir=selected_audit_dir,
    )
    stage_a_summary = dict(audit_result.get("stage_a", {}) or {})
    return {
        "seed": int(seed),
        "reference_v2_3_final_summary_path": str(reference_final_summary_path),
        "reference_v2_3_available": True,
        "selected_trace_dir": str(trace_dir),
        "selected_audit_dir": str(selected_audit_dir),
        "backfill_performed": True,
        "precritical_metrics_available": _has_precritical_reference_metrics(
            stage_a_summary
        ),
        "selected_risk_summary_path": str(selected_audit_dir / "risk_tier_summary.json"),
    }


def _containment_mechanism_verification(
    seed: int,
    final_summary: dict[str, Any],
) -> dict[str, Any]:
    selected_risk_summary = _load_json_if_exists(
        final_summary.get("selected_risk_summary_path")
    )
    current_precritical_step_rates = dict(
        (selected_risk_summary or {}).get("precritical_action_family_step_rates", {}) or {}
    )
    current_precritical_env_run_rates = dict(
        (selected_risk_summary or {}).get("precritical_action_family_env_run_rates", {}) or {}
    )
    current_precritical_recovery_step_rate = _rate_sum(
        current_precritical_step_rates,
        "restore",
        "remove",
        "analyse",
    )
    current_precritical_decoy_step_rate = (
        None
        if "decoy" not in current_precritical_step_rates
        else float(current_precritical_step_rates["decoy"])
    )
    current_precritical_focus_step_rate = (
        None
        if selected_risk_summary is None
        else float(
            selected_risk_summary.get(
                "precritical_compromised_target_focus_step_rate",
                0.0,
            )
        )
    )
    current_ever_critical_breach_rate = (
        None
        if selected_risk_summary is None
        else float(selected_risk_summary.get("ever_critical_breach_rate", 0.0))
    )
    current_tier0_safe_rate = (
        None
        if selected_risk_summary is None
        else float(
            dict(selected_risk_summary.get("tier_rates", {}) or {}).get(
                "Tier 0 Safe",
                0.0,
            )
        )
    )

    reference_summary_path = _reference_v2_3_final_summary_path(seed)
    reference_final_summary = _load_json_if_exists(reference_summary_path)
    reference_v2_3_available = reference_final_summary is not None
    reference_selected_risk_summary = _load_json_if_exists(
        None
        if reference_final_summary is None
        else reference_final_summary.get("selected_risk_summary_path")
    )
    reference_v2_3_precritical_metrics_available = _has_precritical_reference_metrics(
        reference_selected_risk_summary
    )
    reference_precritical_step_rates = dict(
        (reference_selected_risk_summary or {}).get(
            "precritical_action_family_step_rates",
            {},
        )
        or {}
    )
    reference_precritical_env_run_rates = dict(
        (reference_selected_risk_summary or {}).get(
            "precritical_action_family_env_run_rates",
            {},
        )
        or {}
    )
    reference_precritical_recovery_step_rate = _rate_sum(
        reference_precritical_step_rates,
        "restore",
        "remove",
        "analyse",
    )
    reference_precritical_decoy_step_rate = (
        None
        if "decoy" not in reference_precritical_step_rates
        else float(reference_precritical_step_rates["decoy"])
    )
    reference_precritical_focus_step_rate = (
        None
        if reference_selected_risk_summary is None
        else float(
            reference_selected_risk_summary.get(
                "precritical_compromised_target_focus_step_rate",
                0.0,
            )
        )
    )
    reference_ever_critical_breach_rate = (
        None
        if reference_selected_risk_summary is None
        else float(
            reference_selected_risk_summary.get("ever_critical_breach_rate", 0.0)
        )
    )
    reference_tier0_safe_rate = (
        None
        if reference_selected_risk_summary is None
        else float(
            dict(reference_selected_risk_summary.get("tier_rates", {}) or {}).get(
                "Tier 0 Safe",
                0.0,
            )
        )
    )

    precritical_decoy_decreased = (
        None
        if current_precritical_decoy_step_rate is None
        or reference_precritical_decoy_step_rate is None
        else bool(
            current_precritical_decoy_step_rate
            < reference_precritical_decoy_step_rate
        )
    )
    precritical_recovery_increased = (
        None
        if current_precritical_recovery_step_rate is None
        or reference_precritical_recovery_step_rate is None
        else bool(
            current_precritical_recovery_step_rate
            > reference_precritical_recovery_step_rate
        )
    )
    precritical_focus_increased = (
        None
        if current_precritical_focus_step_rate is None
        or reference_precritical_focus_step_rate is None
        else bool(
            current_precritical_focus_step_rate
            > reference_precritical_focus_step_rate
        )
    )
    ever_critical_decreased = (
        None
        if current_ever_critical_breach_rate is None
        or reference_ever_critical_breach_rate is None
        else bool(current_ever_critical_breach_rate < reference_ever_critical_breach_rate)
    )
    ever_critical_improvement = (
        None
        if current_ever_critical_breach_rate is None
        or reference_ever_critical_breach_rate is None
        else float(
            reference_ever_critical_breach_rate - current_ever_critical_breach_rate
        )
    )
    containment_hypothesis_triggered = (
        CONTAINMENT_STATUS_NOT_EVALUABLE
        if precritical_decoy_decreased is None
        or precritical_recovery_increased is None
        or precritical_focus_increased is None
        or ever_critical_decreased is None
        else bool(
            precritical_decoy_decreased
            and precritical_recovery_increased
            and precritical_focus_increased
            and ever_critical_decreased
        )
    )
    tier0_safe_positive = (
        None
        if current_tier0_safe_rate is None
        else bool(current_tier0_safe_rate > 0.0)
    )
    containment_hypothesis_evaluable = bool(
        containment_hypothesis_triggered != CONTAINMENT_STATUS_NOT_EVALUABLE
    )
    containment_hypothesis_status = (
        CONTAINMENT_STATUS_EVALUABLE
        if containment_hypothesis_evaluable
        else CONTAINMENT_STATUS_NOT_EVALUABLE
    )
    expansion_ready = (
        CONTAINMENT_STATUS_NOT_EVALUABLE
        if not containment_hypothesis_evaluable
        or tier0_safe_positive is None
        or ever_critical_improvement is None
        else bool(
            bool(final_summary.get("pilot_passed", False))
            and bool(containment_hypothesis_triggered)
            and (ever_critical_improvement >= 0.05 or tier0_safe_positive)
        )
    )

    return {
        "reference_v2_3_final_summary_path": (
            None if reference_final_summary is None else str(reference_summary_path)
        ),
        "reference_v2_3_available": reference_v2_3_available,
        "reference_v2_3_precritical_metrics_available": (
            reference_v2_3_precritical_metrics_available
        ),
        "containment_hypothesis_evaluable": containment_hypothesis_evaluable,
        "containment_hypothesis_status": containment_hypothesis_status,
        "current_selected_policy_id": str(final_summary.get("selected_policy_id", "")),
        "current_precritical_action_family_step_rates": current_precritical_step_rates,
        "current_precritical_action_family_env_run_rates": current_precritical_env_run_rates,
        "current_precritical_recovery_step_rate": current_precritical_recovery_step_rate,
        "current_precritical_decoy_step_rate": current_precritical_decoy_step_rate,
        "current_precritical_compromised_target_focus_step_rate": current_precritical_focus_step_rate,
        "current_ever_critical_breach_rate": current_ever_critical_breach_rate,
        "current_tier0_safe_rate": current_tier0_safe_rate,
        "reference_v2_3_selected_policy_id": (
            None
            if reference_final_summary is None
            else str(reference_final_summary.get("selected_policy_id", ""))
        ),
        "reference_v2_3_precritical_action_family_step_rates": reference_precritical_step_rates,
        "reference_v2_3_precritical_action_family_env_run_rates": reference_precritical_env_run_rates,
        "reference_v2_3_precritical_recovery_step_rate": reference_precritical_recovery_step_rate,
        "reference_v2_3_precritical_decoy_step_rate": reference_precritical_decoy_step_rate,
        "reference_v2_3_precritical_compromised_target_focus_step_rate": reference_precritical_focus_step_rate,
        "reference_v2_3_ever_critical_breach_rate": reference_ever_critical_breach_rate,
        "reference_v2_3_tier0_safe_rate": reference_tier0_safe_rate,
        "precritical_decoy_step_rate_decreased_vs_v2_3": precritical_decoy_decreased,
        "precritical_recovery_step_rate_increased_vs_v2_3": precritical_recovery_increased,
        "precritical_compromised_target_focus_increased_vs_v2_3": precritical_focus_increased,
        "ever_critical_breach_rate_decreased_vs_v2_3": ever_critical_decreased,
        "ever_critical_breach_rate_improvement_vs_v2_3": ever_critical_improvement,
        "tier0_safe_positive": tier0_safe_positive,
        "containment_hypothesis_triggered_vs_v2_3": containment_hypothesis_triggered,
        "eligible_for_seed_expansion": expansion_ready,
    }


def aggregate_v2_4_4obj_summaries(
    *,
    seeds: tuple[int, ...] = DEFAULT_MULTI_SEEDS,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    completed_rows: list[dict[str, Any]] = []

    metric_fields = (
        "business_return",
        "cost_return",
        "ever_critical_breach_rate",
        "persistent_critical_breach_rate",
        "mean_first_critical_hit_step",
        "mean_critical_dwell_steps",
        "high_confidence_env_run_rate",
        "q2_user_action_during_critical_breach_env_run_rate",
        "q3_missed_immediate_response_to_critical_hit_env_run_rate",
        "q4_user_focus_after_enterprise_foothold_env_run_rate",
        "q5_repeated_low_value_decoy_loop_env_run_rate",
        "tier0_safe_rate",
    )

    def _mean(values: list[float]) -> float | None:
        if not values:
            return None
        return float(sum(values) / len(values))

    for seed in [int(value) for value in seeds]:
        final_summary = _load_json_if_exists(_final_summary_path(seed))
        pilot_summary = _load_json_if_exists(_pilot_summary_path(seed))
        if final_summary is None or pilot_summary is None:
            rows.append(
                {
                    "seed": seed,
                    "available": False,
                    "pilot_passed": None,
                    "selected_policy_id": None,
                }
            )
            continue

        selected_risk_summary = _load_json_if_exists(
            final_summary.get("selected_risk_summary_path")
        ) or {}
        baseline_risk_summary = _load_json_if_exists(
            final_summary.get("baseline_risk_summary_path")
        ) or {}
        containment = dict(
            final_summary.get("containment_mechanism_verification", {}) or {}
        )
        comparison = dict(pilot_summary.get("comparison", {}) or {})
        candidate = dict(comparison.get("candidate", {}) or {})
        baseline = dict(comparison.get("baseline", {}) or {})

        row = {
            "seed": seed,
            "available": True,
            "pilot_passed": bool(final_summary.get("pilot_passed", False)),
            "selected_policy_id": str(final_summary.get("selected_policy_id", "")),
            "business_return": float(candidate.get("business_return", 0.0)),
            "cost_return": float(candidate.get("cost_return", 0.0)),
            "ever_critical_breach_rate": float(
                selected_risk_summary.get("ever_critical_breach_rate", 0.0)
            ),
            "persistent_critical_breach_rate": float(
                selected_risk_summary.get("persistent_critical_breach_rate", 0.0)
            ),
            "mean_first_critical_hit_step": float(
                candidate.get("mean_first_critical_hit_step", 0.0)
            ),
            "mean_critical_dwell_steps": float(
                selected_risk_summary.get("mean_critical_dwell_steps", 0.0)
            ),
            "high_confidence_env_run_rate": float(
                selected_risk_summary.get("high_confidence_env_run_rate", 0.0)
            ),
            "q2_user_action_during_critical_breach_env_run_rate": float(
                dict(
                    selected_risk_summary.get("questionable_rule_env_run_rates", {}) or {}
                ).get("Q2_user_action_during_critical_breach", 0.0)
            ),
            "q3_missed_immediate_response_to_critical_hit_env_run_rate": float(
                dict(
                    selected_risk_summary.get("questionable_rule_env_run_rates", {}) or {}
                ).get("Q3_missed_immediate_response_to_critical_hit", 0.0)
            ),
            "q4_user_focus_after_enterprise_foothold_env_run_rate": float(
                dict(
                    selected_risk_summary.get("questionable_rule_env_run_rates", {}) or {}
                ).get("Q4_user_focus_after_enterprise_foothold", 0.0)
            ),
            "q5_repeated_low_value_decoy_loop_env_run_rate": float(
                dict(
                    selected_risk_summary.get("questionable_rule_env_run_rates", {}) or {}
                ).get("Q5_repeated_low_value_decoy_loop", 0.0)
            ),
            "tier0_safe_rate": float(
                dict(selected_risk_summary.get("tier_rates", {}) or {}).get(
                    "Tier 0 Safe",
                    0.0,
                )
            ),
            "baseline_business_return": float(baseline.get("business_return", 0.0)),
            "baseline_cost_return": float(baseline.get("cost_return", 0.0)),
            "baseline_ever_critical_breach_rate": float(
                baseline_risk_summary.get("ever_critical_breach_rate", 0.0)
            ),
            "baseline_persistent_critical_breach_rate": float(
                baseline_risk_summary.get("persistent_critical_breach_rate", 0.0)
            ),
            "baseline_high_confidence_env_run_rate": float(
                baseline_risk_summary.get("high_confidence_env_run_rate", 0.0)
            ),
            "baseline_q2_user_action_during_critical_breach_env_run_rate": float(
                dict(
                    baseline_risk_summary.get("questionable_rule_env_run_rates", {}) or {}
                ).get("Q2_user_action_during_critical_breach", 0.0)
            ),
            "containment_reference_v2_3_available": containment.get(
                "reference_v2_3_available"
            ),
            "containment_reference_v2_3_precritical_metrics_available": containment.get(
                "reference_v2_3_precritical_metrics_available"
            ),
            "containment_hypothesis_evaluable": containment.get(
                "containment_hypothesis_evaluable"
            ),
            "containment_hypothesis_status": containment.get(
                "containment_hypothesis_status"
            ),
            "containment_hypothesis_triggered_vs_v2_3": containment.get(
                "containment_hypothesis_triggered_vs_v2_3"
            ),
            "eligible_for_seed_expansion": containment.get(
                "eligible_for_seed_expansion"
            ),
            "pilot_summary_path": str(_pilot_summary_path(seed)),
            "final_summary_path": str(_final_summary_path(seed)),
        }
        rows.append(row)
        completed_rows.append(row)

    candidate_means = {
        field: _mean([float(row[field]) for row in completed_rows if row.get(field) is not None])
        for field in metric_fields
    }
    baseline_means = {
        f"baseline_{field}": _mean(
            [
                float(row[f"baseline_{field}"])
                for row in completed_rows
                if row.get(f"baseline_{field}") is not None
            ]
        )
        for field in (
            "business_return",
            "cost_return",
            "ever_critical_breach_rate",
            "persistent_critical_breach_rate",
            "high_confidence_env_run_rate",
            "q2_user_action_during_critical_breach_env_run_rate",
        )
    }
    aggregated = {
        "method_name": METHOD_NAME,
        "runner_dirname": RUNNER_DIRNAME,
        "seeds": [int(value) for value in seeds],
        "num_completed": len(completed_rows),
        "num_pilot_passed": sum(
            1 for row in completed_rows if bool(row.get("pilot_passed", False))
        ),
        "pass_rate": (
            None
            if not completed_rows
            else float(
                sum(1 for row in completed_rows if bool(row.get("pilot_passed", False)))
                / len(completed_rows)
            )
        ),
        "persistent_non_regression_all": (
            None
            if not completed_rows
            else bool(
                all(
                    float(row["persistent_critical_breach_rate"])
                    <= float(row["baseline_persistent_critical_breach_rate"])
                    for row in completed_rows
                )
            )
        ),
        "candidate_metric_means": candidate_means,
        "baseline_metric_means": baseline_means,
        "seed_rows": rows,
    }
    output_path = _runner_root() / "three_seed_summary.json"
    save_json(output_path, aggregated)
    aggregated["summary_path"] = str(output_path.resolve())
    return aggregated


def _augment_saved_summaries(seed: int, final_summary: dict[str, Any]) -> dict[str, Any]:
    containment_mechanism_verification = _containment_mechanism_verification(
        seed,
        final_summary,
    )
    pilot_summary_path = _pilot_summary_path(seed)
    final_summary_path = _final_summary_path(seed)
    pilot_summary = dict(load_json(pilot_summary_path))
    materialized_final_summary = dict(load_json(final_summary_path))
    pilot_summary["containment_mechanism_verification"] = dict(
        containment_mechanism_verification
    )
    materialized_final_summary["containment_mechanism_verification"] = dict(
        containment_mechanism_verification
    )
    save_json(pilot_summary_path, pilot_summary)
    save_json(final_summary_path, materialized_final_summary)
    return materialized_final_summary


def finalize_v2_4_4obj_pilot(
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
    summary = v2_2.finalize_v2_2_4obj_pilot(
        seed=int(seed),
        stage1_config_path=stage1_config_path,
        stage2_config_path=stage2_config_path,
        stage1_buffer_path=stage1_buffer_path,
        stage2_buffer_path=stage2_buffer_path,
        thresholds_path=thresholds_path,
        constraint_eval_episodes=int(constraint_eval_episodes),
        replay_eval_episodes=int(replay_eval_episodes),
        audit_eval_episodes=int(audit_eval_episodes),
        audit_shortlist_k=int(audit_shortlist_k),
        method_name=method_name or METHOD_NAME,
        baseline_method_name=baseline_method_name or BASELINE_METHOD_NAME,
        runner_dirname=runner_dirname or RUNNER_DIRNAME,
    )
    return _augment_saved_summaries(int(seed), dict(summary))


def run_v2_4_4obj_pilot(
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
    summary = v2_2.run_v2_2_4obj_pilot(
        seed=int(seed),
        stage1_config_path=stage1_config_path,
        stage2_config_path=stage2_config_path,
        thresholds_path=thresholds_path,
        constraint_eval_episodes=int(constraint_eval_episodes),
        replay_eval_episodes=int(replay_eval_episodes),
        audit_eval_episodes=int(audit_eval_episodes),
        audit_shortlist_k=int(audit_shortlist_k),
        method_name=method_name or METHOD_NAME,
        baseline_method_name=baseline_method_name or BASELINE_METHOD_NAME,
        runner_dirname=runner_dirname or RUNNER_DIRNAME,
    )
    return _augment_saved_summaries(int(seed), dict(summary))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the V2.4 pre-critical containment Critical-First pilot."
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--seeds", nargs="+", type=int, default=None)
    parser.add_argument("--stage1-config", default=str(DEFAULT_STAGE1_CONFIG))
    parser.add_argument("--stage2-config", default=str(DEFAULT_STAGE2_CONFIG))
    parser.add_argument("--method-name", default=METHOD_NAME)
    parser.add_argument("--baseline-method-name", default=BASELINE_METHOD_NAME)
    parser.add_argument("--runner-dirname", default=RUNNER_DIRNAME)
    parser.add_argument("--thresholds-path", default=DEFAULT_THRESHOLDS_PATH)
    parser.add_argument("--postprocess-only", action="store_true")
    parser.add_argument("--aggregate-only", action="store_true")
    parser.add_argument("--backfill-reference-v2-3", action="store_true")
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

    if bool(args.aggregate_only):
        summary = aggregate_v2_4_4obj_summaries(
            seeds=tuple(args.seeds or DEFAULT_MULTI_SEEDS),
        )
    else:
        if bool(args.backfill_reference_v2_3):
            backfill_reference_v2_3_selected_audit(seed=int(args.seed))
        if bool(args.postprocess_only):
            summary = finalize_v2_4_4obj_pilot(
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
            summary = run_v2_4_4obj_pilot(
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
