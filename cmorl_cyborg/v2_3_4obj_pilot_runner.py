from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from cmorl_minicage.utils import load_json, save_json

import cmorl_cyborg.v2_2_4obj_pilot_runner as v2_2
import cmorl_cyborg.v2_4obj_pilot_runner as base


DEFAULT_SEED = 11
METHOD_NAME = "ours_stage2_fair_critical_safe_v2_3_4obj"
BASELINE_METHOD_NAME = "ours_stage2_fair"
RUNNER_DIRNAME = "fair_compare_critical_safe_v2_3_4obj_runner"
DEFAULT_STAGE1_CONFIG = (
    Path(__file__).resolve().parent
    / "configs"
    / "paper"
    / "fair_compare_semantic"
    / "stage1_fair_critical_safe_v2_3_4obj_seed_0011.yaml"
)
DEFAULT_STAGE2_CONFIG = (
    Path(__file__).resolve().parent
    / "configs"
    / "paper"
    / "fair_compare_semantic"
    / "stage2_fair_critical_safe_v2_3_4obj_seed_0011.yaml"
)
DEFAULT_THRESHOLDS_PATH = v2_2.DEFAULT_THRESHOLDS_PATH
DEFAULT_CONSTRAINT_EVAL_EPISODES = v2_2.DEFAULT_CONSTRAINT_EVAL_EPISODES
DEFAULT_REPLAY_EVAL_EPISODES = v2_2.DEFAULT_REPLAY_EVAL_EPISODES
DEFAULT_AUDIT_EVAL_EPISODES = v2_2.DEFAULT_AUDIT_EVAL_EPISODES
DEFAULT_AUDIT_SHORTLIST_K = v2_2.DEFAULT_AUDIT_SHORTLIST_K

REFERENCE_V2_2_RUNNER_DIRNAME = "fair_compare_critical_safe_v2_2_4obj_runner"


def _runner_root() -> Path:
    return Path(
        base._resolve_repo_path(f"cmorl_cyborg/outputs/{RUNNER_DIRNAME}")
    ).resolve()


def _pilot_summary_path(seed: int) -> Path:
    return _runner_root() / f"seed_{seed:04d}_pilot_summary.json"


def _final_summary_path(seed: int) -> Path:
    return _runner_root() / f"seed_{seed:04d}_final_summary.json"


def _reference_v2_2_final_summary_path(seed: int) -> Path:
    return Path(
        base._resolve_repo_path(
            f"cmorl_cyborg/outputs/{REFERENCE_V2_2_RUNNER_DIRNAME}/seed_{seed:04d}_final_summary.json"
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


def _mechanism_verification(seed: int, final_summary: dict[str, Any]) -> dict[str, Any]:
    selected_risk_summary = _load_json_if_exists(final_summary.get("selected_risk_summary_path"))
    current_step_rates = dict(
        (selected_risk_summary or {}).get("critical_action_family_step_rates", {}) or {}
    )
    current_env_run_rates = dict(
        (selected_risk_summary or {}).get("critical_action_family_env_run_rates", {}) or {}
    )
    reference_summary_path = _reference_v2_2_final_summary_path(seed)
    reference_final_summary = _load_json_if_exists(reference_summary_path)
    reference_selected_risk_summary = _load_json_if_exists(
        None
        if reference_final_summary is None
        else reference_final_summary.get("selected_risk_summary_path")
    )
    reference_step_rates = dict(
        (reference_selected_risk_summary or {}).get(
            "critical_action_family_step_rates",
            {},
        )
        or {}
    )
    reference_env_run_rates = dict(
        (reference_selected_risk_summary or {}).get(
            "critical_action_family_env_run_rates",
            {},
        )
        or {}
    )
    current_restore_remove = _rate_sum(current_step_rates, "restore", "remove")
    reference_restore_remove = _rate_sum(reference_step_rates, "restore", "remove")
    current_decoy = (
        None if "decoy" not in current_step_rates else float(current_step_rates["decoy"])
    )
    reference_decoy = (
        None if "decoy" not in reference_step_rates else float(reference_step_rates["decoy"])
    )
    decoy_step_rate_decreased = (
        None
        if current_decoy is None or reference_decoy is None
        else bool(current_decoy < reference_decoy)
    )
    restore_remove_step_rate_increased = (
        None
        if current_restore_remove is None or reference_restore_remove is None
        else bool(current_restore_remove > reference_restore_remove)
    )
    mechanism_hypothesis_triggered = (
        None
        if decoy_step_rate_decreased is None
        or restore_remove_step_rate_increased is None
        else bool(decoy_step_rate_decreased and restore_remove_step_rate_increased)
    )
    return {
        "reference_v2_2_final_summary_path": (
            None
            if reference_final_summary is None
            else str(reference_summary_path)
        ),
        "current_selected_policy_id": str(final_summary.get("selected_policy_id", "")),
        "current_critical_action_family_step_rates": current_step_rates,
        "current_critical_action_family_env_run_rates": current_env_run_rates,
        "current_restore_remove_step_rate": current_restore_remove,
        "current_decoy_step_rate": current_decoy,
        "reference_v2_2_selected_policy_id": (
            None
            if reference_final_summary is None
            else str(reference_final_summary.get("selected_policy_id", ""))
        ),
        "reference_v2_2_critical_action_family_step_rates": reference_step_rates,
        "reference_v2_2_critical_action_family_env_run_rates": reference_env_run_rates,
        "reference_v2_2_restore_remove_step_rate": reference_restore_remove,
        "reference_v2_2_decoy_step_rate": reference_decoy,
        "decoy_step_rate_decreased_vs_v2_2": decoy_step_rate_decreased,
        "restore_remove_step_rate_increased_vs_v2_2": restore_remove_step_rate_increased,
        "mechanism_hypothesis_triggered_vs_v2_2": mechanism_hypothesis_triggered,
    }


def _augment_saved_summaries(seed: int, final_summary: dict[str, Any]) -> dict[str, Any]:
    mechanism_verification = _mechanism_verification(seed, final_summary)
    pilot_summary_path = _pilot_summary_path(seed)
    final_summary_path = _final_summary_path(seed)
    pilot_summary = dict(load_json(pilot_summary_path))
    materialized_final_summary = dict(load_json(final_summary_path))
    pilot_summary["mechanism_verification"] = dict(mechanism_verification)
    materialized_final_summary["mechanism_verification"] = dict(mechanism_verification)
    save_json(pilot_summary_path, pilot_summary)
    save_json(final_summary_path, materialized_final_summary)
    return materialized_final_summary


def finalize_v2_3_4obj_pilot(
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


def run_v2_3_4obj_pilot(
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
        description="Run the V2.3 recovery-priority shield Critical-First pilot."
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
        summary = finalize_v2_3_4obj_pilot(
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
        summary = run_v2_3_4obj_pilot(
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
