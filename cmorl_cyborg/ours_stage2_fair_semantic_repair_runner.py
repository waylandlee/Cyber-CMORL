from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from typing import Any

from cmorl_minicage.buffer import load_policy_buffer
from cmorl_minicage.utils import ensure_dir, load_json, save_json

from . import export_tight_feasible_set_reevaluated as reevaluate_mod
from . import strong_tightplus_ours_fair_compare_runner as base
from .export_candidate_semantic_audit import (
    DEFAULT_CRITICAL_HOST,
    DEFAULT_CRITICAL_PATH_HOSTS,
    export_candidate_semantic_audit,
)
from .export_figure2_attack_defense_trace import (
    Figure2ReplayCandidate,
    _buffer_record_lookup,
    export_candidate_trace,
    resolve_artifact_path,
)

BASE_METHOD_NAME = "ours_stage2_fair"
CONTROL_METHOD_NAME = "no_constraint_stage2_fair"
RUNNER_DIRNAME = "fair_compare_semantic_repair_runner"
DEFAULT_SELECTION_SEEDS = (7, 11, 19)
DEFAULT_FULL_SEEDS = (7, 11, 19)
DEFAULT_PILOT_SEED = 11
DEFAULT_SELECTION_EVAL_EPISODES = 5
DEFAULT_TRACE_EVAL_EPISODES = 3
DEFAULT_CONFIRMATORY_EVAL_EPISODES = 20

PHASE1_SELECTION_METHODS = {
    "semantic_aware": {
        "method_name": "ours_stage2_fair_selection_semantic_aware",
        "display_name": "Ours Stage2 Fair Selection Only (Semantic Aware)",
        "color": "#ff9da6",
    },
    "semantic_balanced": {
        "method_name": "ours_stage2_fair_selection_semantic_balanced",
        "display_name": "Ours Stage2 Fair Selection Only (Semantic Balanced)",
        "color": "#9c755f",
    },
    "critical_safe_balanced": {
        "method_name": "ours_stage2_fair_selection_critical_safe_balanced",
        "display_name": "Ours Stage2 Fair Selection Only (Critical-Safe Balanced)",
        "color": "#e15759",
    },
}

PROFILE_SPECS = {
    "gate": {
        "method_name": "ours_stage2_fair_critical_safe_v1",
        "display_name": "Ours Stage2 Fair Critical-Safe V1",
        "template_config": "cmorl_cyborg/configs/paper/fair_compare_semantic/stage2_fair_critical_safe_v1_seed_0011.yaml",
        "color": "#4c78a8",
        "business_regression_limit": 8.0,
        "cost_regression_limit": 4.0,
        "mode_label": "critical-first gate + semantic_penalty",
    },
    "target": {
        "method_name": "ours_stage2_fair_semantic_target",
        "display_name": "Ours Stage2 Fair Semantic Target",
        "template_config": "cmorl_cyborg/configs/paper/fair_compare_semantic/stage2_fair_semantic_target_seed_0011.yaml",
        "color": "#72b7b2",
        "business_regression_limit": 8.0,
        "cost_regression_limit": 4.0,
        "mode_label": "deployability_target + semantic_penalty",
    },
}

SEMANTIC_METRIC_WEIGHTS = {
    "high_disruption_action_rate": 0.50,
    "final_critical_compromised_hosts": 0.30,
    "critical_impact_count": 0.20,
}

PHASE0_REPRESENTATIVE_BASELINES = {
    "ours_stage2_fair_objective_selected_seed_0011": {
        "seed": 11,
        "policy_id": "stage2_ext_016_obj_0",
        "summary_path": "cmorl_cyborg/outputs/paper_appendix/figure2_attack_defense_analysis/ours_stage2_fair/seed_0011/stage2_ext_016_obj_0_semantic_audit_replay20/risk_tier_summary.json",
    },
    "ours_stage2_fair_deployment_like_seed_0007": {
        "seed": 7,
        "policy_id": "stage1_pref_000_ckpt_191",
        "summary_path": "cmorl_cyborg/outputs/paper_appendix/figure2_attack_defense_analysis/ours_stage2_fair/seed_0007/stage1_pref_000_ckpt_191_deployment_like_semantic_audit_replay20/risk_tier_summary.json",
    },
    "no_constraint_stage2_fair_tight_feasible_seed_0019": {
        "seed": 19,
        "policy_id": "stage2_ext_023_obj_2",
        "summary_path": "cmorl_cyborg/outputs/paper_appendix/figure2_attack_defense_analysis/no_constraint_stage2_fair/seed_0019/stage2_ext_023_obj_2_semantic_audit_replay20/risk_tier_summary.json",
    },
}


def _timestamp() -> str:
    return base._timestamp()


def _repo_root() -> Path:
    return base._repo_root()


def _resolve_repo_path(raw_path: str | Path) -> Path:
    return base._resolve_repo_path(raw_path)


def _runner_root() -> Path:
    return ensure_dir(_resolve_repo_path(f"cmorl_cyborg/outputs/{RUNNER_DIRNAME}"))


def _generated_config_root() -> Path:
    return ensure_dir(_runner_root() / "generated_configs")


def _buffer_copy_root() -> Path:
    return ensure_dir(_runner_root() / "buffer_copies")


class ProgressTracker(base.ProgressTracker):
    def __init__(self, total_steps: int) -> None:
        self.total_steps = max(int(total_steps), 1)
        self.completed_steps = 0
        self.pipeline_start = base.time.monotonic()
        self.pipeline_started_at = _timestamp()
        self.output_dir = _runner_root()
        self.status_path = self.output_dir / "status.json"
        self.log_path = self.output_dir / "runner.log"
        self.current_label: str | None = None
        self.current_step_started_at: str | None = None
        self.current_step_start_monotonic: float | None = None
        self.current_command: list[str] | None = None
        self.current_subprocess_pid: int | None = None
        self.last_error: str | None = None
        self._append_log("RUNNER START")
        self._write_status("IDLE", label=None)


def _trace_root(*parts: str) -> Path:
    return ensure_dir(
        _resolve_repo_path("cmorl_cyborg/outputs/paper_appendix/semantic_repair_traces").joinpath(*parts)
    )


def _analysis_root(*parts: str) -> Path:
    return ensure_dir(
        _resolve_repo_path("cmorl_cyborg/outputs/paper_appendix/semantic_repair_analysis").joinpath(*parts)
    )


def _selection_method_name(selection_policy: str) -> str:
    return str(PHASE1_SELECTION_METHODS[selection_policy]["method_name"])


def _selection_display_name(selection_policy: str) -> str:
    return str(PHASE1_SELECTION_METHODS[selection_policy]["display_name"])


def _profile_method_name(profile_name: str) -> str:
    return str(PROFILE_SPECS[profile_name]["method_name"])


def _profile_display_name(profile_name: str) -> str:
    return str(PROFILE_SPECS[profile_name]["display_name"])


def _profile_template_path(profile_name: str) -> Path:
    return _resolve_repo_path(str(PROFILE_SPECS[profile_name]["template_config"]))


def _objective_tight_metrics_path(seed: int) -> Path:
    return _resolve_repo_path(
        f"cmorl_cyborg/outputs/fair_compare_eval/tight/{BASE_METHOD_NAME}/seed_{seed:04d}/constraint_metrics.json"
    )


def _objective_reevaluated_summary_path(seed: int) -> Path:
    return _resolve_repo_path(
        f"cmorl_cyborg/outputs/fair_compare_eval/reevaluated_tight_feasible_set_summary/{BASE_METHOD_NAME}/seed_{seed:04d}.json"
    )


def _fair_compare_base_config_path(seed: int) -> Path:
    return _resolve_repo_path(
        f"cmorl_cyborg/configs/paper/fair_compare/stage2_fair_constrained_seed_{seed:04d}.yaml"
    )


def _eval_input_buffer_path(method_name: str, seed: int) -> Path:
    return _resolve_repo_path(
        f"cmorl_cyborg/outputs/fair_compare_eval_inputs/{method_name}/seed_{seed:04d}/solution_buffer.json"
    )


def _tight_metrics_path(method_name: str, seed: int) -> Path:
    return _resolve_repo_path(
        f"cmorl_cyborg/outputs/fair_compare_eval/tight/{method_name}/seed_{seed:04d}/constraint_metrics.json"
    )


def _reevaluated_summary_path(method_name: str, seed: int) -> Path:
    return _resolve_repo_path(
        f"cmorl_cyborg/outputs/fair_compare_eval/reevaluated_tight_feasible_set_summary/{method_name}/seed_{seed:04d}.json"
    )


def _training_seed_root(method_name: str, seed: int) -> Path:
    return _resolve_repo_path(
        f"cmorl_cyborg/outputs/fair_compare_semantic/{method_name}/seed_{seed:04d}"
    )


def _phase_summary_path(phase_name: str) -> Path:
    return _runner_root() / f"{phase_name}.json"


def _baseline_objective_analysis_dir(seed: int, policy_id: str) -> Path:
    return _analysis_root(
        "phase0_objective_selected",
        f"seed_{seed:04d}",
        f"objective_selected__{policy_id}_semantic_audit",
    )


def _baseline_objective_replay_dir(seed: int, policy_id: str) -> Path:
    return _analysis_root(
        "phase0_objective_selected",
        f"seed_{seed:04d}",
        f"objective_selected__{policy_id}_semantic_audit_replay20",
    )


def _selection_analysis_dir(selection_policy: str, seed: int, policy_id: str) -> Path:
    return _analysis_root(
        "phase1_selection_only",
        selection_policy,
        f"seed_{seed:04d}",
        f"{selection_policy}__{policy_id}_semantic_audit",
    )


def _selection_replay_dir(selection_policy: str, seed: int, policy_id: str) -> Path:
    return _analysis_root(
        "phase1_selection_only",
        selection_policy,
        f"seed_{seed:04d}",
        f"{selection_policy}__{policy_id}_semantic_audit_replay20",
    )


def _profile_analysis_dir(
    phase_scope: str,
    seed: int,
    policy_id: str,
    candidate_label: str,
) -> Path:
    return _analysis_root(
        phase_scope,
        f"seed_{seed:04d}",
        f"{candidate_label}__{policy_id}_semantic_audit",
    )


def _profile_replay_dir(
    phase_scope: str,
    seed: int,
    policy_id: str,
    candidate_label: str,
) -> Path:
    return _analysis_root(
        phase_scope,
        f"seed_{seed:04d}",
        f"{candidate_label}__{policy_id}_semantic_audit_replay20",
    )


def _selection_trace_output_root(selection_policy: str) -> Path:
    return _trace_root("phase1_selection_only", selection_policy)


def _baseline_trace_output_root() -> Path:
    return _trace_root("phase0_objective_selected")


def _profile_trace_output_root(phase_scope: str) -> Path:
    return _trace_root(phase_scope)


def _load_yaml(path: str | Path) -> dict[str, Any]:
    return base._load_yaml(path)


def _write_yaml(path: str | Path, payload: dict[str, Any]) -> Path:
    return base._write_yaml(path, payload)


def _planned_steps(stop_after_phase: int) -> int:
    steps = 1  # phase 0
    if stop_after_phase >= 1:
        steps += len(DEFAULT_SELECTION_SEEDS)  # objective baseline audits
        steps += len(DEFAULT_SELECTION_SEEDS) * len(PHASE1_SELECTION_METHODS) * 3
    if stop_after_phase >= 2:
        steps += 5
    if stop_after_phase >= 3:
        steps += 5
    if stop_after_phase >= 4:
        steps += len(DEFAULT_FULL_SEEDS) * 5
    return steps + 2


def _summary_metrics(summary: dict[str, Any]) -> dict[str, float]:
    return {
        "business_return": float(summary["mean_business_return"]),
        "cost_return": float(summary["mean_cost_return"]),
        "env_run_feasible_rate": float(summary["env_run_feasible_rate"]),
        "ever_critical_breach_rate": float(summary["ever_critical_breach_rate"]),
        "persistent_critical_breach_rate": float(summary["persistent_critical_breach_rate"]),
        "mean_first_critical_hit_step": float(summary.get("mean_first_critical_hit_step", 0.0)),
        "critical_hit_latency_score": float(summary.get("critical_hit_latency_score", 0.0)),
        "mean_critical_dwell_steps": float(summary.get("mean_critical_dwell_steps", 0.0)),
        "high_confidence_env_run_rate": float(summary["high_confidence_env_run_rate"]),
    }


def _return_regression(*, baseline_value: float, candidate_value: float) -> float:
    return max(0.0, float(baseline_value) - float(candidate_value))


def _selection_only_comparison(
    candidate_summary: dict[str, Any],
    baseline_summary: dict[str, Any],
) -> dict[str, Any]:
    candidate = _summary_metrics(candidate_summary)
    baseline = _summary_metrics(baseline_summary)
    ever_drop = float(
        baseline["ever_critical_breach_rate"] - candidate["ever_critical_breach_rate"]
    )
    persistent_drop = float(
        baseline["persistent_critical_breach_rate"] - candidate["persistent_critical_breach_rate"]
    )
    first_hit_delay = float(
        candidate["mean_first_critical_hit_step"] - baseline["mean_first_critical_hit_step"]
    )
    latency_improvement = float(
        candidate["critical_hit_latency_score"] - baseline["critical_hit_latency_score"]
    )
    business_regression = _return_regression(
        baseline_value=baseline["business_return"],
        candidate_value=candidate["business_return"],
    )
    cost_regression = _return_regression(
        baseline_value=baseline["cost_return"],
        candidate_value=candidate["cost_return"],
    )
    return {
        "candidate": candidate,
        "baseline": baseline,
        "ever_drop": ever_drop,
        "persistent_drop": persistent_drop,
        "first_hit_delay": first_hit_delay,
        "latency_improvement": latency_improvement,
        "business_regression": business_regression,
        "cost_regression": cost_regression,
        "meets_phase1_rule": bool(
            persistent_drop >= 0.15
            and business_regression <= 5.0
            and cost_regression <= 2.0
        ),
    }


def _pilot_comparison(
    candidate_summary: dict[str, Any],
    baseline_summary: dict[str, Any],
    *,
    business_limit: float,
    cost_limit: float,
) -> dict[str, Any]:
    candidate = _summary_metrics(candidate_summary)
    baseline = _summary_metrics(baseline_summary)
    persistent_drop = float(
        baseline["persistent_critical_breach_rate"] - candidate["persistent_critical_breach_rate"]
    )
    ever_drop = float(
        baseline["ever_critical_breach_rate"] - candidate["ever_critical_breach_rate"]
    )
    first_hit_delay = float(
        candidate["mean_first_critical_hit_step"] - baseline["mean_first_critical_hit_step"]
    )
    latency_improvement = float(
        candidate["critical_hit_latency_score"] - baseline["critical_hit_latency_score"]
    )
    business_regression = _return_regression(
        baseline_value=baseline["business_return"],
        candidate_value=candidate["business_return"],
    )
    cost_regression = _return_regression(
        baseline_value=baseline["cost_return"],
        candidate_value=candidate["cost_return"],
    )
    high_conf_delta = float(
        candidate["high_confidence_env_run_rate"] - baseline["high_confidence_env_run_rate"]
    )
    criteria = {
        "ever_critical_breach_below_one": bool(candidate["ever_critical_breach_rate"] < 1.0),
        "persistent_critical_breach_ok": bool(
            candidate["persistent_critical_breach_rate"] <= 0.60
        ),
        "latency_or_delay_ok": bool(
            latency_improvement >= 0.10 or first_hit_delay >= 5.0
        ),
        "high_confidence_not_worse": bool(high_conf_delta <= 1e-9),
        "business_guardrail_ok": bool(business_regression <= business_limit),
        "cost_guardrail_ok": bool(cost_regression <= cost_limit),
    }
    failure_reasons = [name for name, passed in criteria.items() if not passed]
    return {
        "candidate": candidate,
        "baseline": baseline,
        "persistent_drop": persistent_drop,
        "ever_drop": ever_drop,
        "first_hit_delay": first_hit_delay,
        "latency_improvement": latency_improvement,
        "business_regression": business_regression,
        "cost_regression": cost_regression,
        "high_confidence_delta": high_conf_delta,
        "criteria": criteria,
        "failure_reasons": failure_reasons,
        "meets_phase2_rule": bool(all(criteria.values())),
    }


def _full_seed_comparison(
    candidate_summary: dict[str, Any],
    baseline_summary: dict[str, Any],
) -> dict[str, Any]:
    candidate = _summary_metrics(candidate_summary)
    baseline = _summary_metrics(baseline_summary)
    persistent_drop = float(
        baseline["persistent_critical_breach_rate"] - candidate["persistent_critical_breach_rate"]
    )
    business_regression = _return_regression(
        baseline_value=baseline["business_return"],
        candidate_value=candidate["business_return"],
    )
    cost_regression = _return_regression(
        baseline_value=baseline["cost_return"],
        candidate_value=candidate["cost_return"],
    )
    high_conf_delta = float(
        candidate["high_confidence_env_run_rate"] - baseline["high_confidence_env_run_rate"]
    )
    criteria = {
        "persistent_drop_ok": bool(persistent_drop >= 0.15),
        "high_confidence_not_worse": bool(high_conf_delta <= 1e-9),
        "business_guardrail_ok": bool(business_regression <= 8.0),
        "cost_guardrail_ok": bool(cost_regression <= 4.0),
    }
    return {
        "candidate": candidate,
        "baseline": baseline,
        "persistent_drop": persistent_drop,
        "business_regression": business_regression,
        "cost_regression": cost_regression,
        "high_confidence_delta": high_conf_delta,
        "criteria": criteria,
        "meets_seed_rule": bool(all(criteria.values())),
    }


def _full_phase_result(seed_results: dict[str, dict[str, Any]]) -> dict[str, Any]:
    ordered = [seed_results[key] for key in sorted(seed_results)]
    pass_count = sum(1 for item in ordered if bool(item["comparison"]["meets_seed_rule"]))
    guardrail_violations = [
        key
        for key, item in seed_results.items()
        if not bool(item["comparison"]["criteria"]["business_guardrail_ok"])
        or not bool(item["comparison"]["criteria"]["cost_guardrail_ok"])
    ]
    strong_seed = any(
        item["comparison"]["candidate"]["persistent_critical_breach_rate"] <= 0.50
        and item["comparison"]["candidate"]["ever_critical_breach_rate"] < 1.0
        for item in ordered
    )
    return {
        "seed_pass_count": int(pass_count),
        "guardrail_violating_seeds": guardrail_violations,
        "has_strong_seed": bool(strong_seed),
        "meets_phase4_rule": bool(
            pass_count >= 2 and not guardrail_violations and strong_seed
        ),
    }


def _load_risk_summary(summary_path: Path) -> dict[str, Any]:
    return dict(load_json(summary_path))


def _augment_trace_manifest(trace_dir: Path, updates: dict[str, Any]) -> None:
    manifest_path = trace_dir / "trace_manifest.json"
    payload = dict(load_json(manifest_path))
    payload.update(updates)
    save_json(manifest_path, payload)


def _objective_buffer_path(seed: int) -> Path:
    payload = dict(load_json(_objective_tight_metrics_path(seed)))
    return Path(str(payload["input_path"])).resolve()


def _normalized_objective_buffer_path(seed: int) -> Path:
    return _buffer_copy_root() / f"ours_stage2_fair_seed_{seed:04d}_normalized.json"


def _objective_metrics(seed: int) -> dict[str, Any]:
    return dict(load_json(_objective_tight_metrics_path(seed)))


def _record_from_buffer(buffer_path: Path, policy_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    buffer_payload = load_policy_buffer(buffer_path)
    lookup = _buffer_record_lookup(buffer_payload)
    if policy_id not in lookup:
        raise KeyError(f"Policy {policy_id} not found in {buffer_path}")
    return dict(lookup[policy_id]), dict(buffer_payload.get("metadata", {}))


def _normalize_buffer_paths(
    *,
    source_buffer_path: Path,
    output_path: Path,
    force: bool,
) -> Path:
    if output_path.exists() and not force:
        return output_path.resolve()

    buffer_payload = load_policy_buffer(source_buffer_path)
    normalized = dict(buffer_payload)
    metadata = dict(normalized.get("metadata", {}) or {})
    if metadata.get("stage1_buffer"):
        metadata["stage1_buffer"] = str(
            resolve_artifact_path(
                str(metadata["stage1_buffer"]),
                anchor_path=str(source_buffer_path),
            ).resolve()
        )
    normalized["metadata"] = metadata

    for key in ("records", "pareto_front"):
        entries = []
        for record in list(normalized.get(key, []) or []):
            item = dict(record)
            checkpoint_path = item.get("checkpoint_path")
            if checkpoint_path:
                item["checkpoint_path"] = str(
                    resolve_artifact_path(
                        str(checkpoint_path),
                        anchor_path=str(source_buffer_path),
                    ).resolve()
                )
            entries.append(item)
        normalized[key] = entries

    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_json(output_path, normalized)
    return output_path.resolve()


def _export_and_audit_candidate(
    *,
    method_name: str,
    seed: int,
    buffer_path: Path,
    policy_id: str,
    candidate_label: str,
    trace_root: Path,
    analysis_dir: Path,
    replay_dir: Path,
    trace_eval_episodes: int,
    confirmatory_eval_episodes: int,
    phase_name: str,
    selection_policy: str,
    force: bool,
    progress: base.ProgressTracker,
) -> dict[str, Any]:
    summary_path = replay_dir / "risk_tier_summary.json"
    cached_trace_dir = (
        Path(trace_root)
        / method_name
        / f"seed_{seed:04d}"
        / f"{candidate_label}__{policy_id}"
    )
    if summary_path.exists() and not force:
        stage_a_summary = _load_risk_summary(analysis_dir / "risk_tier_summary.json")
        stage_b_summary = _load_risk_summary(summary_path)
        return {
            "trace_dir": str(cached_trace_dir.resolve()),
            "stage_a": stage_a_summary,
            "stage_b": stage_b_summary,
            "analysis_dir": str(analysis_dir.resolve()),
            "replay_dir": str(replay_dir.resolve()),
        }

    record, metadata = _record_from_buffer(buffer_path, policy_id)
    trace_label = f"trace {phase_name} seed_{seed:04d} {policy_id}"
    trace_step = progress.start_step(trace_label)
    trace_dir = export_candidate_trace(
        method_name=method_name,
        seed=seed,
        candidate=Figure2ReplayCandidate(
            policy_id=policy_id,
            candidate_label=candidate_label,
            candidate_aliases=(candidate_label, selection_policy),
        ),
        buffer_path=buffer_path,
        buffer_anchor_path=buffer_path,
        record=record,
        metadata=metadata,
        output_root=trace_root,
        eval_episodes=int(trace_eval_episodes),
    )
    _augment_trace_manifest(
        trace_dir,
        {
            "experiment_context": "ours_stage2_fair semantic repair",
            "phase": phase_name,
            "selection_policy": selection_policy,
            "source_buffer_path": str(buffer_path.resolve()),
            "source_method_name": method_name,
        },
    )
    progress.finish_step(trace_label, trace_step)

    audit_label = f"audit {phase_name} seed_{seed:04d} {policy_id}"
    audit_step = progress.start_step(audit_label)
    audit_result = export_candidate_semantic_audit(
        trace_dir=trace_dir,
        output_dir=analysis_dir,
        critical_host=DEFAULT_CRITICAL_HOST,
        critical_path_hosts=DEFAULT_CRITICAL_PATH_HOSTS,
        confirmatory_eval_episodes=int(confirmatory_eval_episodes),
        confirmatory_output_dir=replay_dir,
    )
    progress.finish_step(audit_label, audit_step)
    return {
        "trace_dir": str(Path(trace_dir).resolve()),
        "stage_a": dict(audit_result["stage_a"]),
        "stage_b": dict(audit_result.get("stage_b", {})),
        "analysis_dir": str(Path(analysis_dir).resolve()),
        "replay_dir": str(Path(replay_dir).resolve()),
    }


def _reevaluated_summary_from_metrics(
    *,
    method_name: str,
    display_name: str,
    color: str,
    constraint_metrics_path: Path,
    eval_episodes: int,
    selected_policy_id: str,
    selection_policy: str,
    output_path: Path,
    progress: base.ProgressTracker,
    force: bool,
) -> dict[str, Any]:
    if output_path.exists() and not force:
        return dict(load_json(output_path))

    reevaluate_mod.DISPLAY_NAMES[method_name] = display_name
    reevaluate_mod.COLORS[method_name] = color
    label = f"reevaluate {method_name} {constraint_metrics_path.parent.name}"
    step_start = progress.start_step(label)
    summary = reevaluate_mod._seed_summary(
        method_name=method_name,
        constraint_metrics_path=constraint_metrics_path,
        eval_episodes=int(eval_episodes),
        logger=base._CandidateLogger(progress),
    )
    summary["selected_policy_id"] = str(selected_policy_id)
    summary["selected_selection_policy"] = str(selection_policy)
    summary["selected_candidate_row"] = next(
        (
            row
            for row in summary.get("candidate_rows", [])
            if str(row.get("policy_id")) == str(selected_policy_id)
        ),
        None,
    )
    save_json(output_path, summary)
    progress.finish_step(label, step_start)
    return dict(summary)


def _write_variant_summary_from_common(
    *,
    common_summary: dict[str, Any],
    method_name: str,
    display_name: str,
    selected_policy_id: str,
    selection_policy: str,
    output_path: Path,
) -> dict[str, Any]:
    payload = dict(common_summary)
    payload["method_name"] = method_name
    payload["display_name"] = display_name
    payload["selected_policy_id"] = str(selected_policy_id)
    payload["selected_selection_policy"] = str(selection_policy)
    payload["selected_candidate_row"] = next(
        (
            row
            for row in payload.get("candidate_rows", [])
            if str(row.get("policy_id")) == str(selected_policy_id)
        ),
        None,
    )
    save_json(output_path, payload)
    return payload


def _materialize_constraint_eval_config(
    *,
    method_name: str,
    buffer_path: Path,
    selection_policy: str,
    eval_episodes: int,
    output_path: Path,
    config_name: str,
) -> Path:
    payload = {
        "method_name": method_name,
        "input_kind": "buffer",
        "input_path": str(buffer_path.resolve()),
        "selection_source": "pareto",
        "selection_policy": selection_policy,
        "thresholds_path": str(base._thresholds_tight_path().resolve()),
        "output_path": str(output_path.resolve()),
        "eval_episodes": int(eval_episodes),
        "semantic_metric_weights": dict(SEMANTIC_METRIC_WEIGHTS),
    }
    return _write_yaml(_generated_config_root() / config_name, payload)


def _run_constraint_eval(
    *,
    method_name: str,
    buffer_path: Path,
    selection_policy: str,
    eval_episodes: int,
    output_path: Path,
    config_name: str,
    phase_label: str,
    progress: base.ProgressTracker,
    force: bool,
) -> dict[str, Any]:
    if output_path.exists() and not force:
        return dict(load_json(output_path))
    config_path = _materialize_constraint_eval_config(
        method_name=method_name,
        buffer_path=buffer_path,
        selection_policy=selection_policy,
        eval_episodes=eval_episodes,
        output_path=output_path,
        config_name=config_name,
    )
    label = f"tight eval {phase_label}"
    step_start = progress.start_step(label)
    base._run_module(
        "cmorl_cyborg.evaluate_constraints",
        ["--config", str(config_path)],
        progress=progress,
        label=label,
    )
    progress.finish_step(label, step_start)
    return dict(load_json(output_path))


def _copy_eval_input_for_method(
    *,
    method_name: str,
    seed: int,
    train_buffer_path: Path,
    progress: base.ProgressTracker,
    force: bool,
) -> Path:
    target_path = _eval_input_buffer_path(method_name, seed)
    label = f"copy eval_input {method_name} seed_{seed:04d}"
    if target_path.exists() and not force:
        step_start = progress.start_step(label)
        progress.finish_step(label, step_start, skipped=True)
        return target_path.resolve()
    step_start = progress.start_step(label)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(train_buffer_path, target_path)
    progress.finish_step(label, step_start)
    return target_path.resolve()


def _profile_config_path(profile_name: str, seed: int) -> Path:
    if seed == DEFAULT_PILOT_SEED:
        return _profile_template_path(profile_name)
    template_payload = _load_yaml(_profile_template_path(profile_name))
    base_seed_payload = _load_yaml(_fair_compare_base_config_path(seed))
    template_payload["seed"] = int(seed)
    template_payload["stage1_buffer"] = str(base_seed_payload["stage1_buffer"])
    template_payload["output_dir"] = (
        f"cmorl_cyborg/outputs/fair_compare_semantic/{_profile_method_name(profile_name)}/seed_{seed:04d}"
    )
    env_payload = dict(template_payload.get("env", {}) or {})
    env_payload["seed"] = int(seed)
    template_payload["env"] = env_payload
    return _write_yaml(
        _generated_config_root() / f"{_profile_method_name(profile_name)}_seed_{seed:04d}.yaml",
        template_payload,
    )


def _config_output_dir(config_path: Path) -> Path:
    payload = _load_yaml(config_path)
    return _resolve_repo_path(str(payload["output_dir"]))


def _train_profile_seed(
    *,
    profile_name: str,
    seed: int,
    progress: base.ProgressTracker,
    force: bool,
) -> Path:
    config_path = _profile_config_path(profile_name, seed)
    output_root = _config_output_dir(config_path)
    if force and output_root.exists():
        pass
    existing = base._latest_run_artifact(output_root, "solution_buffer.json")
    label = f"train {_profile_method_name(profile_name)} seed_{seed:04d}"
    if existing is not None and not force:
        step_start = progress.start_step(label)
        progress.finish_step(label, step_start, skipped=True)
        return existing.resolve()
    step_start = progress.start_step(label)
    base._run_module(
        "cmorl_cyborg.train_stage2",
        ["--config", str(config_path)],
        progress=progress,
        label=label,
    )
    progress.finish_step(label, step_start)
    created = base._latest_run_artifact(output_root, "solution_buffer.json")
    if created is None:
        raise FileNotFoundError(f"Missing solution_buffer.json under {output_root}")
    return created.resolve()


def _freeze_phase0_baselines(progress: base.ProgressTracker) -> dict[str, Any]:
    label = "phase0 freeze baselines"
    step_start = progress.start_step(label)
    per_seed: dict[str, Any] = {}
    for seed in DEFAULT_SELECTION_SEEDS:
        tight_metrics_path = _objective_tight_metrics_path(seed)
        reevaluated_path = _objective_reevaluated_summary_path(seed)
        tight_metrics = dict(load_json(tight_metrics_path))
        reevaluated_summary = dict(load_json(reevaluated_path))
        per_seed[f"seed_{seed:04d}"] = {
            "tight_metrics_path": str(tight_metrics_path.resolve()),
            "reevaluated_summary_path": str(reevaluated_path.resolve()),
            "selected_policy_id": str(tight_metrics["selected_policy_id"]),
            "closest_candidate_policy_id": str(reevaluated_summary["closest_candidate_policy_id"]),
        }
    representative: dict[str, Any] = {}
    for key, raw in PHASE0_REPRESENTATIVE_BASELINES.items():
        summary_path = _resolve_repo_path(str(raw["summary_path"]))
        representative[key] = {
            **raw,
            "summary_path": str(summary_path.resolve()),
            "exists": bool(summary_path.exists()),
        }
        if summary_path.exists():
            representative[key]["summary_metrics"] = _summary_metrics(
                dict(load_json(summary_path))
            )
    payload = {
        "phase": 0,
        "generated_at": _timestamp(),
        "objective_selected_baselines": per_seed,
        "representative_reference_points": representative,
    }
    save_json(_phase_summary_path("phase0_baselines"), payload)
    progress.finish_step(label, step_start)
    return payload


def _ensure_objective_baseline_audit(
    *,
    seed: int,
    progress: base.ProgressTracker,
    force: bool,
) -> dict[str, Any]:
    metrics = _objective_metrics(seed)
    policy_id = str(metrics["selected_policy_id"])
    analysis_dir = _baseline_objective_analysis_dir(seed, policy_id)
    replay_dir = _baseline_objective_replay_dir(seed, policy_id)
    stage_b_path = replay_dir / "risk_tier_summary.json"
    if stage_b_path.exists() and not force:
        return {
            "seed": seed,
            "policy_id": policy_id,
            "tight_metrics_path": str(_objective_tight_metrics_path(seed).resolve()),
            "reevaluated_summary_path": str(_objective_reevaluated_summary_path(seed).resolve()),
            "analysis_dir": str(analysis_dir.resolve()),
            "replay_dir": str(replay_dir.resolve()),
            "stage_a_summary": _load_risk_summary(analysis_dir / "risk_tier_summary.json"),
            "stage_b_summary": _load_risk_summary(stage_b_path),
        }

    exported = _export_and_audit_candidate(
        method_name=BASE_METHOD_NAME,
        seed=seed,
        buffer_path=_objective_buffer_path(seed),
        policy_id=policy_id,
        candidate_label="objective_selected",
        trace_root=_baseline_trace_output_root(),
        analysis_dir=analysis_dir,
        replay_dir=replay_dir,
        trace_eval_episodes=DEFAULT_TRACE_EVAL_EPISODES,
        confirmatory_eval_episodes=DEFAULT_CONFIRMATORY_EVAL_EPISODES,
        phase_name="phase0_objective_selected",
        selection_policy="objective",
        force=force,
        progress=progress,
    )
    return {
        "seed": seed,
        "policy_id": policy_id,
        "tight_metrics_path": str(_objective_tight_metrics_path(seed).resolve()),
        "reevaluated_summary_path": str(_objective_reevaluated_summary_path(seed).resolve()),
        "analysis_dir": str(analysis_dir.resolve()),
        "replay_dir": str(replay_dir.resolve()),
        "stage_a_summary": exported["stage_a"],
        "stage_b_summary": exported["stage_b"],
        "trace_dir": exported["trace_dir"],
    }


def _run_phase1_selection_only(
    *,
    selection_seeds: tuple[int, ...],
    baseline_audits: dict[int, dict[str, Any]],
    selection_eval_episodes: int,
    trace_eval_episodes: int,
    confirmatory_eval_episodes: int,
    progress: base.ProgressTracker,
    force: bool,
) -> dict[str, Any]:
    phase_payload: dict[str, Any] = {
        "phase": 1,
        "generated_at": _timestamp(),
        "seeds": {},
    }
    clear_help_seeds = 0

    for seed in selection_seeds:
        buffer_path = _normalize_buffer_paths(
            source_buffer_path=_objective_buffer_path(seed),
            output_path=_normalized_objective_buffer_path(seed),
            force=force,
        )
        baseline_summary = baseline_audits[seed]["stage_b_summary"]
        seed_payload: dict[str, Any] = {
            "baseline_policy_id": baseline_audits[seed]["policy_id"],
            "baseline_summary_metrics": _summary_metrics(baseline_summary),
            "variants": {},
        }
        common_reevaluated_summary: dict[str, Any] | None = None
        best_variant_name: str | None = None
        best_variant_score: tuple[float, float, float] | None = None
        seed_helpful = False

        for selection_policy in PHASE1_SELECTION_METHODS:
            method_name = _selection_method_name(selection_policy)
            metrics_path = _tight_metrics_path(method_name, seed)
            metrics_payload = _run_constraint_eval(
                method_name=method_name,
                buffer_path=buffer_path,
                selection_policy=selection_policy,
                eval_episodes=selection_eval_episodes,
                output_path=metrics_path,
                config_name=f"{method_name}_tight_seed_{seed:04d}.yaml",
                phase_label=f"phase1 {selection_policy} seed_{seed:04d}",
                progress=progress,
                force=force,
            )

            summary_path = _reevaluated_summary_path(method_name, seed)
            if common_reevaluated_summary is None or force:
                common_reevaluated_summary = _reevaluated_summary_from_metrics(
                    method_name=method_name,
                    display_name=_selection_display_name(selection_policy),
                    color=str(PHASE1_SELECTION_METHODS[selection_policy]["color"]),
                    constraint_metrics_path=metrics_path,
                    eval_episodes=trace_eval_episodes,
                    selected_policy_id=str(metrics_payload["selected_policy_id"]),
                    selection_policy=selection_policy,
                    output_path=summary_path,
                    progress=progress,
                    force=force,
                )
            else:
                _write_variant_summary_from_common(
                    common_summary=common_reevaluated_summary,
                    method_name=method_name,
                    display_name=_selection_display_name(selection_policy),
                    selected_policy_id=str(metrics_payload["selected_policy_id"]),
                    selection_policy=selection_policy,
                    output_path=summary_path,
                )

            policy_id = str(metrics_payload["selected_policy_id"])
            audit_result = _export_and_audit_candidate(
                method_name=BASE_METHOD_NAME,
                seed=seed,
                buffer_path=buffer_path,
                policy_id=policy_id,
                candidate_label=selection_policy,
                trace_root=_selection_trace_output_root(selection_policy),
                analysis_dir=_selection_analysis_dir(selection_policy, seed, policy_id),
                replay_dir=_selection_replay_dir(selection_policy, seed, policy_id),
                trace_eval_episodes=trace_eval_episodes,
                confirmatory_eval_episodes=confirmatory_eval_episodes,
                phase_name=f"phase1_{selection_policy}",
                selection_policy=selection_policy,
                force=force,
                progress=progress,
            )
            comparison = _selection_only_comparison(
                audit_result["stage_b"],
                baseline_summary,
            )
            seed_helpful = seed_helpful or bool(comparison["meets_phase1_rule"])
            variant_payload = {
                "selection_policy": selection_policy,
                "method_name": method_name,
                "tight_metrics_path": str(metrics_path.resolve()),
                "reevaluated_summary_path": str(summary_path.resolve()),
                "selected_policy_id": policy_id,
                "trace_dir": audit_result["trace_dir"],
                "analysis_dir": audit_result["analysis_dir"],
                "replay_dir": audit_result["replay_dir"],
                "comparison": comparison,
            }
            seed_payload["variants"][selection_policy] = variant_payload
            ranking = (
                float(comparison["ever_drop"]),
                float(comparison["persistent_drop"]),
                float(comparison["latency_improvement"]),
                -float(comparison["business_regression"]),
                -float(comparison["cost_regression"]),
            )
            if best_variant_score is None or ranking > best_variant_score:
                best_variant_name = selection_policy
                best_variant_score = ranking

        seed_payload["best_variant"] = best_variant_name
        seed_payload["selection_only_helpful"] = bool(seed_helpful)
        phase_payload["seeds"][f"seed_{seed:04d}"] = seed_payload
        clear_help_seeds += int(seed_helpful)

    phase_payload["selection_only_helpful_seed_count"] = int(clear_help_seeds)
    phase_payload["selection_only_has_clear_help"] = bool(clear_help_seeds >= 2)
    save_json(_phase_summary_path("phase1_selection_only_summary"), phase_payload)
    return phase_payload


def _run_profile_seed(
    *,
    profile_name: str,
    phase_scope: str,
    seed: int,
    baseline_summary: dict[str, Any],
    selection_eval_episodes: int,
    trace_eval_episodes: int,
    confirmatory_eval_episodes: int,
    progress: base.ProgressTracker,
    force: bool,
) -> dict[str, Any]:
    method_name = _profile_method_name(profile_name)
    selection_policy = "critical_safe_balanced"
    candidate_label = f"{selection_policy}_selected"
    train_buffer = _train_profile_seed(
        profile_name=profile_name,
        seed=seed,
        progress=progress,
        force=force,
    )
    eval_input = _copy_eval_input_for_method(
        method_name=method_name,
        seed=seed,
        train_buffer_path=train_buffer,
        progress=progress,
        force=force,
    )
    metrics_path = _tight_metrics_path(method_name, seed)
    metrics_payload = _run_constraint_eval(
        method_name=method_name,
        buffer_path=eval_input,
        selection_policy=selection_policy,
        eval_episodes=selection_eval_episodes,
        output_path=metrics_path,
        config_name=f"{method_name}_tight_seed_{seed:04d}.yaml",
        phase_label=f"{profile_name} {selection_policy} seed_{seed:04d}",
        progress=progress,
        force=force,
    )
    reevaluated_summary = _reevaluated_summary_from_metrics(
        method_name=method_name,
        display_name=_profile_display_name(profile_name),
        color=str(PROFILE_SPECS[profile_name]["color"]),
        constraint_metrics_path=metrics_path,
        eval_episodes=trace_eval_episodes,
        selected_policy_id=str(metrics_payload["selected_policy_id"]),
        selection_policy=selection_policy,
        output_path=_reevaluated_summary_path(method_name, seed),
        progress=progress,
        force=force,
    )
    policy_id = str(metrics_payload["selected_policy_id"])
    audit_result = _export_and_audit_candidate(
        method_name=method_name,
        seed=seed,
        buffer_path=eval_input,
        policy_id=policy_id,
        candidate_label=candidate_label,
        trace_root=_profile_trace_output_root(phase_scope),
        analysis_dir=_profile_analysis_dir(phase_scope, seed, policy_id, candidate_label),
        replay_dir=_profile_replay_dir(phase_scope, seed, policy_id, candidate_label),
        trace_eval_episodes=trace_eval_episodes,
        confirmatory_eval_episodes=confirmatory_eval_episodes,
        phase_name=phase_scope,
        selection_policy=selection_policy,
        force=force,
        progress=progress,
    )
    comparison = _pilot_comparison(
        audit_result["stage_b"],
        baseline_summary,
        business_limit=float(PROFILE_SPECS[profile_name]["business_regression_limit"]),
        cost_limit=float(PROFILE_SPECS[profile_name]["cost_regression_limit"]),
    )
    return {
        "profile_name": profile_name,
        "method_name": method_name,
        "seed": int(seed),
        "train_buffer_path": str(train_buffer),
        "eval_input_buffer_path": str(eval_input),
        "tight_metrics_path": str(metrics_path.resolve()),
        "reevaluated_summary_path": str(_reevaluated_summary_path(method_name, seed).resolve()),
        "selected_policy_id": policy_id,
        "trace_dir": audit_result["trace_dir"],
        "analysis_dir": audit_result["analysis_dir"],
        "replay_dir": audit_result["replay_dir"],
        "comparison": comparison,
        "reevaluated_summary": reevaluated_summary,
    }


def _run_phase4_full_rerun(
    *,
    winner_profile: str,
    full_seeds: tuple[int, ...],
    baseline_audits: dict[int, dict[str, Any]],
    selection_eval_episodes: int,
    trace_eval_episodes: int,
    confirmatory_eval_episodes: int,
    progress: base.ProgressTracker,
    force: bool,
) -> dict[str, Any]:
    seed_results: dict[str, dict[str, Any]] = {}
    for seed in full_seeds:
        seed_result = _run_profile_seed(
            profile_name=winner_profile,
            phase_scope=f"phase4_full_{winner_profile}",
            seed=seed,
            baseline_summary=baseline_audits[seed]["stage_b_summary"],
            selection_eval_episodes=selection_eval_episodes,
            trace_eval_episodes=trace_eval_episodes,
            confirmatory_eval_episodes=confirmatory_eval_episodes,
            progress=progress,
            force=force,
        )
        seed_result["comparison"] = _full_seed_comparison(
            _load_risk_summary(Path(seed_result["replay_dir"]) / "risk_tier_summary.json"),
            baseline_audits[seed]["stage_b_summary"],
        )
        seed_results[f"seed_{seed:04d}"] = seed_result

    aggregate = _full_phase_result(seed_results)
    payload = {
        "phase": 4,
        "winner_profile": winner_profile,
        "generated_at": _timestamp(),
        "seeds": seed_results,
        "aggregate": aggregate,
    }
    save_json(_phase_summary_path("phase4_full_summary"), payload)
    return payload


def _failure_reason_from_comparison(phase_payload: dict[str, Any]) -> str:
    comparison = dict(phase_payload.get("comparison", {}))
    criteria = dict(comparison.get("criteria", {}))
    if (
        comparison.get("persistent_drop", 0.0) >= 0.20
        and (
            not criteria.get("business_guardrail_ok", True)
            or not criteria.get("cost_guardrail_ok", True)
        )
    ):
        return "business_cost_constraint_conflict"
    return "three_dimensional_objective_insufficient"


def _write_final_report(
    *,
    phase0: dict[str, Any],
    phase1: dict[str, Any] | None,
    phase2: dict[str, Any] | None,
    phase3: dict[str, Any] | None,
    phase4: dict[str, Any] | None,
    final_summary: dict[str, Any],
) -> Path:
    lines = [
        "# Ours Stage2 Fair Semantic Repair Report",
        "",
        f"- Generated at: `{_timestamp()}`",
        f"- Final decision: `{final_summary['final_decision']}`",
        "",
        "## Q1. selection-only 能否明显缓解风险？",
    ]
    if phase1 is None:
        lines.append("- This phase was not executed.")
    else:
        lines.append(
            f"- Helpful seeds: `{phase1['selection_only_helpful_seed_count']}/3`"
        )
        lines.append(
            f"- Clear help: `{phase1['selection_only_has_clear_help']}`"
        )
    lines.extend(
        [
            "",
            "## Q2. `critical-first gate + semantic_penalty + critical_safe_balanced selection` 能否把风险降到可接受？",
        ]
    )
    if phase2 is None:
        lines.append("- Gate pilot was not executed.")
    else:
        lines.append(
            f"- Gate pilot passed: `{phase2['comparison']['meets_phase2_rule']}`"
        )
        lines.append(
            f"- Persistent drop: `{phase2['comparison']['persistent_drop']:.4f}`"
        )
        lines.append(
            f"- Ever drop: `{phase2['comparison']['ever_drop']:.4f}`"
        )
    lines.extend(
        [
            "",
            "## Q3. 如果不能，失败更像 business/cost 约束冲突，还是三维目标表达不足？",
        ]
    )
    if final_summary["final_decision"] == "stop_after_phase3_failure":
        lines.append(f"- Diagnosis: `{final_summary['failure_reason']}`")
    elif final_summary["final_decision"] == "full_rerun_failed":
        lines.append(f"- Diagnosis: `{final_summary['failure_reason']}`")
    else:
        lines.append("- The current winner was good enough to advance beyond pilot.")
    if phase4 is not None:
        lines.extend(
            [
                "",
                "## Phase 4",
                f"- Winner profile: `{phase4['winner_profile']}`",
                f"- Full rerun passed: `{phase4['aggregate']['meets_phase4_rule']}`",
                f"- Seed pass count: `{phase4['aggregate']['seed_pass_count']}`",
                f"- Has strong seed: `{phase4['aggregate']['has_strong_seed']}`",
            ]
        )
    report_path = _runner_root() / "final_report.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def run_ours_stage2_fair_semantic_repair(
    *,
    selection_seeds: tuple[int, ...] = DEFAULT_SELECTION_SEEDS,
    pilot_seed: int = DEFAULT_PILOT_SEED,
    full_seeds: tuple[int, ...] = DEFAULT_FULL_SEEDS,
    selection_eval_episodes: int = DEFAULT_SELECTION_EVAL_EPISODES,
    trace_eval_episodes: int = DEFAULT_TRACE_EVAL_EPISODES,
    confirmatory_eval_episodes: int = DEFAULT_CONFIRMATORY_EVAL_EPISODES,
    stop_after_phase: int = 2,
    force: bool = False,
) -> dict[str, Any]:
    progress = ProgressTracker(total_steps=_planned_steps(stop_after_phase))
    phase0: dict[str, Any] | None = None
    phase1: dict[str, Any] | None = None
    phase2: dict[str, Any] | None = None
    phase3: dict[str, Any] | None = None
    phase4: dict[str, Any] | None = None
    baseline_audits: dict[int, dict[str, Any]] = {}
    final_decision = "not_started"
    failure_reason = None

    try:
        phase0 = _freeze_phase0_baselines(progress)
        if stop_after_phase == 0:
            final_decision = "stop_after_phase0"
        else:
            baseline_seed_order = tuple(
                dict.fromkeys(
                    [*(int(seed) for seed in selection_seeds), int(pilot_seed), *(int(seed) for seed in full_seeds)]
                )
            )
            for seed in baseline_seed_order:
                baseline_audits[int(seed)] = _ensure_objective_baseline_audit(
                    seed=int(seed),
                    progress=progress,
                    force=force,
                )

            phase1 = _run_phase1_selection_only(
                selection_seeds=tuple(int(seed) for seed in selection_seeds),
                baseline_audits=baseline_audits,
                selection_eval_episodes=selection_eval_episodes,
                trace_eval_episodes=trace_eval_episodes,
                confirmatory_eval_episodes=confirmatory_eval_episodes,
                progress=progress,
                force=force,
            )
            if stop_after_phase == 1:
                final_decision = "stop_after_phase1"
            else:
                phase2 = _run_profile_seed(
                    profile_name="gate",
                    phase_scope="phase2_gate",
                    seed=int(pilot_seed),
                    baseline_summary=baseline_audits[int(pilot_seed)]["stage_b_summary"],
                    selection_eval_episodes=selection_eval_episodes,
                    trace_eval_episodes=trace_eval_episodes,
                    confirmatory_eval_episodes=confirmatory_eval_episodes,
                    progress=progress,
                    force=force,
                )
                save_json(_phase_summary_path("phase2_gate_summary"), phase2)
                if stop_after_phase == 2:
                    final_decision = "stop_after_phase2"
                elif bool(phase2["comparison"]["meets_phase2_rule"]):
                    if stop_after_phase >= 4:
                        phase4 = _run_phase4_full_rerun(
                            winner_profile="gate",
                            full_seeds=tuple(int(seed) for seed in full_seeds),
                            baseline_audits=baseline_audits,
                            selection_eval_episodes=selection_eval_episodes,
                            trace_eval_episodes=trace_eval_episodes,
                            confirmatory_eval_episodes=confirmatory_eval_episodes,
                            progress=progress,
                            force=force,
                        )
                        final_decision = (
                            "full_rerun_passed" if phase4["aggregate"]["meets_phase4_rule"] else "full_rerun_failed"
                        )
                        if not phase4["aggregate"]["meets_phase4_rule"]:
                            failure_reason = (
                                "business_cost_constraint_conflict"
                                if phase4["aggregate"]["guardrail_violating_seeds"]
                                else "three_dimensional_objective_insufficient"
                            )
                    else:
                        final_decision = "gate_pilot_passed"
                else:
                    if stop_after_phase == 2:
                        final_decision = "stop_after_phase2"
                    else:
                        phase3 = _run_profile_seed(
                            profile_name="target",
                            phase_scope="phase3_target",
                            seed=int(pilot_seed),
                            baseline_summary=baseline_audits[int(pilot_seed)]["stage_b_summary"],
                            selection_eval_episodes=selection_eval_episodes,
                            trace_eval_episodes=trace_eval_episodes,
                            confirmatory_eval_episodes=confirmatory_eval_episodes,
                            progress=progress,
                            force=force,
                        )
                        save_json(_phase_summary_path("phase3_target_summary"), phase3)
                        if stop_after_phase == 3:
                            final_decision = "stop_after_phase3"
                        elif bool(phase3["comparison"]["meets_phase2_rule"]):
                            if stop_after_phase >= 4:
                                phase4 = _run_phase4_full_rerun(
                                    winner_profile="target",
                                    full_seeds=tuple(int(seed) for seed in full_seeds),
                                    baseline_audits=baseline_audits,
                                    selection_eval_episodes=selection_eval_episodes,
                                    trace_eval_episodes=trace_eval_episodes,
                                    confirmatory_eval_episodes=confirmatory_eval_episodes,
                                    progress=progress,
                                    force=force,
                                )
                                final_decision = (
                                    "full_rerun_passed" if phase4["aggregate"]["meets_phase4_rule"] else "full_rerun_failed"
                                )
                                if not phase4["aggregate"]["meets_phase4_rule"]:
                                    failure_reason = (
                                        "business_cost_constraint_conflict"
                                        if phase4["aggregate"]["guardrail_violating_seeds"]
                                        else "three_dimensional_objective_insufficient"
                                    )
                            else:
                                final_decision = "target_pilot_passed"
                        else:
                            final_decision = "stop_after_phase3_failure"
                            failure_reason = _failure_reason_from_comparison(phase3)

        final_summary = {
            "generated_at": _timestamp(),
            "selection_seeds": list(selection_seeds),
            "pilot_seed": int(pilot_seed),
            "full_seeds": list(full_seeds),
            "selection_eval_episodes": int(selection_eval_episodes),
            "trace_eval_episodes": int(trace_eval_episodes),
            "confirmatory_eval_episodes": int(confirmatory_eval_episodes),
            "stop_after_phase": int(stop_after_phase),
            "force": bool(force),
            "final_decision": final_decision,
            "failure_reason": failure_reason,
            "phase0_path": str(_phase_summary_path("phase0_baselines").resolve()) if phase0 is not None else None,
            "phase1_path": str(_phase_summary_path("phase1_selection_only_summary").resolve()) if phase1 is not None else None,
            "phase2_path": str(_phase_summary_path("phase2_gate_summary").resolve()) if phase2 is not None else None,
            "phase3_path": str(_phase_summary_path("phase3_target_summary").resolve()) if phase3 is not None else None,
            "phase4_path": str(_phase_summary_path("phase4_full_summary").resolve()) if phase4 is not None else None,
            "runner_log": str(progress.log_path.resolve()),
            "runner_status": str(progress.status_path.resolve()),
        }
        report_path = _write_final_report(
            phase0=phase0 or {},
            phase1=phase1,
            phase2=phase2,
            phase3=phase3,
            phase4=phase4,
            final_summary=final_summary,
        )
        final_summary["final_report_path"] = str(report_path.resolve())
        save_json(_runner_root() / "final_summary.json", final_summary)
        progress.finalize(success=True, extra=final_summary)
        return final_summary
    except BaseException as exc:
        progress.fail_step(progress.current_label, exc)
        progress.log_exception_traceback(exc)
        progress.finalize(
            success=False,
            extra={
                "final_decision": final_decision,
                "failure_reason": failure_reason,
                "phase0_path": str(_phase_summary_path("phase0_baselines").resolve()) if phase0 is not None else None,
                "phase1_path": str(_phase_summary_path("phase1_selection_only_summary").resolve()) if phase1 is not None else None,
                "phase2_path": str(_phase_summary_path("phase2_gate_summary").resolve()) if phase2 is not None else None,
                "phase3_path": str(_phase_summary_path("phase3_target_summary").resolve()) if phase3 is not None else None,
                "phase4_path": str(_phase_summary_path("phase4_full_summary").resolve()) if phase4 is not None else None,
            },
        )
        raise


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the ours_stage2_fair semantic repair experiment plan."
    )
    parser.add_argument(
        "--selection-seeds",
        nargs="+",
        type=int,
        default=list(DEFAULT_SELECTION_SEEDS),
    )
    parser.add_argument("--pilot-seed", type=int, default=DEFAULT_PILOT_SEED)
    parser.add_argument("--full-seeds", nargs="+", type=int, default=list(DEFAULT_FULL_SEEDS))
    parser.add_argument("--selection-eval-episodes", type=int, default=DEFAULT_SELECTION_EVAL_EPISODES)
    parser.add_argument("--trace-eval-episodes", type=int, default=DEFAULT_TRACE_EVAL_EPISODES)
    parser.add_argument(
        "--confirmatory-eval-episodes",
        type=int,
        default=DEFAULT_CONFIRMATORY_EVAL_EPISODES,
    )
    parser.add_argument(
        "--stop-after-phase",
        type=int,
        choices=(0, 1, 2, 3, 4),
        default=2,
    )
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    summary = run_ours_stage2_fair_semantic_repair(
        selection_seeds=tuple(int(seed) for seed in args.selection_seeds),
        pilot_seed=int(args.pilot_seed),
        full_seeds=tuple(int(seed) for seed in args.full_seeds),
        selection_eval_episodes=int(args.selection_eval_episodes),
        trace_eval_episodes=int(args.trace_eval_episodes),
        confirmatory_eval_episodes=int(args.confirmatory_eval_episodes),
        stop_after_phase=int(args.stop_after_phase),
        force=bool(args.force),
    )
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
