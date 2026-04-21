from __future__ import annotations

import argparse
import copy
import csv
from pathlib import Path
from typing import Any

import numpy as np

from cmorl_minicage.algorithms.selection import nondominated_filter
from cmorl_minicage.buffer import load_policy_buffer, save_policy_buffer
from cmorl_minicage.evaluate import evaluate_policy_buffer, resolve_reference_point
from cmorl_minicage.utils import load_json, save_json

from . import assignment_diagnostics as assignment_diag_mod
from . import evaluate_constraints as constraint_eval_mod
from . import support_shell_diagnostics as support_shell_mod
from . import strong_tightplus_ours_fair_compare_runner as base

DEFAULT_SEED = 7
DEFAULT_PARENT_BUFFER_PATH = (
    "cmorl_cyborg/outputs/paper_table_a/ours_stage2/seed_0007/run_ddb937f9/solution_buffer.json"
)
DEFAULT_PARENT_ASSIGNMENT_SUMMARY_PATH = (
    "cmorl_cyborg/outputs/assignment_diag/tight_strict_seed0007/assignment_diag_summary.json"
)
DEFAULT_PARENT_SUPPORT_SHELL_SUMMARY_PATH = (
    "cmorl_cyborg/outputs/support_shell_diag/tight_strict_seed0007/support_shell_summary.json"
)
DEFAULT_THRESHOLDS_PATH = "cmorl_cyborg/outputs/fair_compare_eval/thresholds_tight.json"
DEFAULT_BASE_CONFIG_PATH = "cmorl_cyborg/configs/paper/stage2_main_seed_0007.yaml"
DEFAULT_SELECTED_POLICY_EVAL_EPISODES = 40
DEFAULT_ASSIGNMENT_EVAL_EPISODES = 5
DEFAULT_PREFERENCE_STEP = 0.1

SELECTION_PROFILES: dict[str, dict[str, Any]] = {
    "repair": {
        "method_name": "ours_stage2_support_repair",
        "display_name": "Ours Stage2 Support Repair",
        "runner_dirname": "support_aware_repair_runner",
        "train_output_dir": "cmorl_cyborg/outputs/support_aware_repair/seed_{seed:04d}",
        "selection_patch": None,
    },
    "adaptive_reweight": {
        "method_name": "ours_stage2_support_reweight",
        "display_name": "Ours Stage2 Support Reweight",
        "runner_dirname": "support_aware_reweight_runner",
        "train_output_dir": "cmorl_cyborg/outputs/support_aware_reweight/seed_{seed:04d}",
        "selection_patch": {
            "mode": "adaptive",
            "coverage_mode": "static",
            "keep_extremes": True,
            "semantic_eval_episodes": 5,
            "semantic_score_mode": "support_aware",
            "score_weights": {
                "crowding": 0.20,
                "expansion": 0.20,
                "coverage": 0.15,
                "low_risk": 0.15,
                "semantic_low_risk": 0.30,
            },
            "semantic_support_score_weights": {
                "mean_violation": 0.40,
                "high_disruption": 0.30,
                "business": 0.20,
                "cost": 0.10,
            },
        },
    },
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _resolve_repo_path(raw_path: str | Path) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return (_repo_root() / path).resolve()


def _profile_settings(selection_profile: str) -> dict[str, Any]:
    if selection_profile not in SELECTION_PROFILES:
        raise ValueError(f"Unsupported selection_profile: {selection_profile}")
    return dict(SELECTION_PROFILES[selection_profile])


def _runner_root(selection_profile: str) -> Path:
    settings = _profile_settings(selection_profile)
    return base.ensure_dir(
        _resolve_repo_path(f"cmorl_cyborg/outputs/{settings['runner_dirname']}")
    )


def _generated_config_root(selection_profile: str) -> Path:
    return base.ensure_dir(_runner_root(selection_profile) / "generated_configs")


def _refinement_input_root(selection_profile: str) -> Path:
    return base.ensure_dir(_runner_root(selection_profile) / "refinement_inputs")


def _train_seed_root(selection_profile: str, seed: int) -> Path:
    settings = _profile_settings(selection_profile)
    return _resolve_repo_path(settings["train_output_dir"].format(seed=int(seed)))


def _assignment_output_root(selection_profile: str) -> Path:
    settings = _profile_settings(selection_profile)
    return _resolve_repo_path(f"cmorl_cyborg/outputs/assignment_diag/{settings['method_name']}")


def _support_shell_output_root(selection_profile: str) -> Path:
    settings = _profile_settings(selection_profile)
    return _resolve_repo_path(
        f"cmorl_cyborg/outputs/support_shell_diag/{settings['method_name']}"
    )


def _tight_metrics_root(selection_profile: str) -> Path:
    settings = _profile_settings(selection_profile)
    return base.ensure_dir(
        _resolve_repo_path(
            f"cmorl_cyborg/outputs/support_selected_tight_metrics/{settings['method_name']}"
        )
    )


def _summary_root(selection_profile: str) -> Path:
    settings = _profile_settings(selection_profile)
    return base.ensure_dir(
        _resolve_repo_path(
            f"cmorl_cyborg/outputs/support_experiment_summary/{settings['method_name']}"
        )
    )


def _refinement_input_buffer_path(selection_profile: str, seed: int) -> Path:
    return _refinement_input_root(selection_profile) / f"seed_{seed:04d}" / "solution_buffer.json"


def _selected_policy_metrics_path(selection_profile: str, seed: int) -> Path:
    return _tight_metrics_root(selection_profile) / f"seed_{seed:04d}.json"


def _csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _latest_solution_buffer(seed_root: Path) -> Path | None:
    return base._latest_run_artifact(seed_root, "solution_buffer.json")


def _materialize_stage2_config(
    *,
    selection_profile: str,
    seed: int,
    stage1_buffer_path: Path,
    base_config_path: Path,
    thresholds_path: Path,
) -> Path:
    settings = _profile_settings(selection_profile)
    payload = base._load_yaml(base_config_path)
    payload["seed"] = int(seed)
    payload["stage1_buffer"] = str(stage1_buffer_path.resolve())
    payload["output_dir"] = str(_train_seed_root(selection_profile, seed))
    selection_payload = dict(payload.get("selection", {}) or {})
    if settings["selection_patch"] is not None:
        for key, value in settings["selection_patch"].items():
            selection_payload[key] = copy.deepcopy(value)
        selection_payload["semantic_thresholds_path"] = str(thresholds_path.resolve())
    payload["selection"] = selection_payload
    config_path = (
        _generated_config_root(selection_profile)
        / f"{settings['method_name']}_seed_{seed:04d}.yaml"
    )
    return base._write_yaml(config_path, payload)


def _support_shell_selection_rows(
    *,
    support_shell_summary_path: Path,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    summary = load_json(support_shell_summary_path)
    candidates_path = support_shell_summary_path.parent / "support_shell_candidates.csv"
    rows = _csv_rows(candidates_path)
    if not rows:
        raise ValueError(f"No support-shell candidates found: {candidates_path}")
    return summary, rows


def _build_support_refinement_buffer(
    *,
    selection_profile: str,
    seed: int,
    parent_buffer_path: Path,
    support_shell_summary_path: Path,
    progress: base.ProgressTracker,
) -> Path:
    output_path = _refinement_input_buffer_path(selection_profile, seed)
    label = f"build support refinement seed_{seed:04d}"
    if output_path.exists():
        step_start = progress.start_step(label)
        progress.finish_step(label, step_start, skipped=True)
        return output_path.resolve()

    step_start = progress.start_step(label)
    summary, shell_rows = _support_shell_selection_rows(
        support_shell_summary_path=support_shell_summary_path
    )
    target_shell = str(summary.get("recommended_repair_shell", ""))
    if not target_shell:
        raise ValueError(
            f"Support-shell summary does not expose a non-empty repair shell: {support_shell_summary_path}"
        )

    candidate_rows = [
        row for row in shell_rows if str(row.get(f"passed_{target_shell}", "")).lower() == "true"
    ]
    candidate_rows.sort(
        key=lambda row: (
            float(row["mean_violation"]),
            float(row["high_disruption_action_rate"]),
            -float(row["business_return"]),
            -float(row["cost_return"]),
            -float(row.get("strict_margin", "-inf")),
            str(row["policy_id"]),
        )
    )
    payload = load_policy_buffer(parent_buffer_path)
    record_by_id = {str(record["policy_id"]): record for record in payload.get("records", [])}

    selected_ids: list[str] = []
    seen: set[str] = set()

    def _add(policy_id: str) -> None:
        if policy_id and policy_id not in seen:
            selected_ids.append(policy_id)
            seen.add(policy_id)

    for row in candidate_rows:
        _add(str(row["policy_id"]))

    best_business = max(
        shell_rows,
        key=lambda row: (float(row["business_return"]), str(row["policy_id"])),
    )
    best_cost = max(
        shell_rows,
        key=lambda row: (float(row["cost_return"]), str(row["policy_id"])),
    )
    _add(str(best_business["policy_id"]))
    _add(str(best_cost["policy_id"]))

    selected_records = [
        copy.deepcopy(record_by_id[policy_id])
        for policy_id in selected_ids
        if policy_id in record_by_id
    ]
    if not selected_records:
        raise ValueError(
            f"Failed to select any support-aware refinement records from {parent_buffer_path}"
        )

    metadata = dict(payload.get("metadata", {}))
    metadata["support_aware_refinement"] = {
        "enabled": True,
        "selection_profile": selection_profile,
        "seed": int(seed),
        "parent_buffer_path": str(parent_buffer_path.resolve()),
        "support_shell_summary_path": str(support_shell_summary_path.resolve()),
        "target_shell": target_shell,
        "selected_policy_ids": list(selected_ids),
        "selected_record_count": len(selected_records),
        "selection_rule": (
            "all policies from nearest non-empty support shell ranked by "
            "mean_violation, high_disruption, business, cost, plus business/cost anchors"
        ),
    }
    filtered_pareto = nondominated_filter(selected_records)
    save_policy_buffer(
        output_path,
        metadata=metadata,
        records=selected_records,
        pareto_front=filtered_pareto,
    )
    progress.finish_step(label, step_start)
    return output_path.resolve()


def _run_training(
    *,
    selection_profile: str,
    seed: int,
    stage1_buffer_path: Path,
    base_config_path: Path,
    thresholds_path: Path,
    progress: base.ProgressTracker,
) -> Path:
    seed_root = _train_seed_root(selection_profile, seed)
    existing = _latest_solution_buffer(seed_root)
    label = f"train {selection_profile} seed_{seed:04d}"
    if existing is not None:
        step_start = progress.start_step(label)
        progress.finish_step(label, step_start, skipped=True)
        return existing.resolve()
    config_path = _materialize_stage2_config(
        selection_profile=selection_profile,
        seed=seed,
        stage1_buffer_path=stage1_buffer_path,
        base_config_path=base_config_path,
        thresholds_path=thresholds_path,
    )
    step_start = progress.start_step(label)
    base._run_module(
        "cmorl_cyborg.train_stage2",
        ["--config", str(config_path), "--output-dir", str(seed_root)],
        progress=progress,
        label=label,
    )
    progress.finish_step(label, step_start)
    created = _latest_solution_buffer(seed_root)
    if created is None:
        raise FileNotFoundError(f"Missing solution_buffer.json under {seed_root}")
    return created.resolve()


def _run_assignment_summary(
    *,
    selection_profile: str,
    seed: int,
    buffer_path: Path,
    thresholds_path: Path,
    progress: base.ProgressTracker,
) -> Path:
    settings = _profile_settings(selection_profile)
    label = f"assignment diagnostics {selection_profile} seed_{seed:04d}"
    step_start = progress.start_step(label)
    config = assignment_diag_mod.load_assignment_diagnostics_config(
        assignment_diag_mod.DEFAULT_ASSIGNMENT_DIAGNOSTICS_CONFIG
    )
    config.buffer_path = str(buffer_path.resolve())
    config.thresholds_path = str(thresholds_path.resolve())
    config.output_dir = str(_assignment_output_root(selection_profile))
    config.strict_level_output_dir = str(
        _resolve_repo_path(
            f"cmorl_cyborg/outputs/strict_level_diag/{settings['method_name']}"
        )
    )
    config.run_label = f"seed_{seed:04d}"
    outputs = assignment_diag_mod.run_assignment_diagnostics(config, config_anchor=buffer_path)
    progress.finish_step(label, step_start)
    return Path(outputs["summary_path"]).resolve()


def _run_support_shell_summary(
    *,
    selection_profile: str,
    seed: int,
    assignment_summary_path: Path,
    progress: base.ProgressTracker,
) -> Path:
    label = f"support shell {selection_profile} seed_{seed:04d}"
    step_start = progress.start_step(label)
    config = support_shell_mod.load_support_shell_diagnostics_config(
        support_shell_mod.DEFAULT_SUPPORT_SHELL_DIAGNOSTICS_CONFIG
    )
    config.assignment_summary_path = str(assignment_summary_path.resolve())
    config.output_dir = str(_support_shell_output_root(selection_profile))
    config.run_label = f"seed_{seed:04d}"
    outputs = support_shell_mod.run_support_shell_diagnostics(
        config, config_anchor=assignment_summary_path
    )
    progress.finish_step(label, step_start)
    return Path(outputs["summary_path"]).resolve()


def _run_selected_policy_tight_eval(
    *,
    selection_profile: str,
    seed: int,
    buffer_path: Path,
    thresholds_path: Path,
    progress: base.ProgressTracker,
) -> Path:
    label = f"selected policy tight eval {selection_profile} seed_{seed:04d}"
    output_path = _selected_policy_metrics_path(selection_profile, seed)
    if output_path.exists():
        step_start = progress.start_step(label)
        progress.finish_step(label, step_start, skipped=True)
        return output_path.resolve()
    step_start = progress.start_step(label)
    payload = constraint_eval_mod.evaluate_constraints(
        method_name=_profile_settings(selection_profile)["method_name"],
        input_kind="buffer",
        input_path=str(buffer_path.resolve()),
        selection_source="pareto",
        selection_policy="objective",
        thresholds_path=str(thresholds_path.resolve()),
        eval_episodes=int(DEFAULT_SELECTED_POLICY_EVAL_EPISODES),
    )
    save_json(output_path, payload)
    progress.finish_step(label, step_start)
    return output_path.resolve()


def _shared_set_quality(
    *,
    parent_buffer_path: Path,
    child_buffer_path: Path,
) -> tuple[dict[str, Any], dict[str, Any], list[float]]:
    parent_payload = load_policy_buffer(parent_buffer_path)
    child_payload = load_policy_buffer(child_buffer_path)
    points = np.asarray(
        [
            record["objective_vector"]
            for record in list(parent_payload.get("pareto_front", []))
            + list(child_payload.get("pareto_front", []))
        ],
        dtype=np.float32,
    )
    reference_point = resolve_reference_point(
        points,
        obj_dim=int(points.shape[1]),
        reference_strategy="data_min_margin",
        reference_margin=1.0,
        reference_point=None,
    ).astype(np.float32).tolist()
    parent_eval = evaluate_policy_buffer(
        parent_buffer_path,
        DEFAULT_PREFERENCE_STEP,
        reference_strategy="data_min_margin",
        reference_margin=1.0,
        reference_point=reference_point,
    )
    child_eval = evaluate_policy_buffer(
        child_buffer_path,
        DEFAULT_PREFERENCE_STEP,
        reference_strategy="data_min_margin",
        reference_margin=1.0,
        reference_point=reference_point,
    )
    return parent_eval, child_eval, reference_point


def _closest_candidate(candidate_cache_path: str | Path) -> dict[str, Any]:
    rows = []
    with Path(candidate_cache_path).open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                rows.append(load_json(stripped) if stripped.startswith("{") else {})
    if not rows:
        rows = [json.loads(line) for line in Path(candidate_cache_path).read_text().splitlines() if line.strip()]
    return max(rows, key=lambda row: (float(row["strict_margin"]), str(row["policy_id"])))


def _closest_candidate_from_summary(assignment_summary_path: Path) -> dict[str, Any]:
    summary = load_json(assignment_summary_path)
    cache_path = Path(summary["candidate_semantics_path"]).resolve()
    rows = [
        load_json(line)
        if False
        else json.loads(line)
        for line in cache_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return max(rows, key=lambda row: (float(row["strict_margin"]), str(row["policy_id"])))


def _higher_shell_gain(
    *,
    comparison_summary: dict[str, Any],
    child_summary: dict[str, Any],
) -> bool:
    comparison_counts = dict(comparison_summary.get("pass_counts_by_shell", {}))
    child_counts = dict(child_summary.get("pass_counts_by_shell", {}))
    comparison_highest = -1
    for idx, shell_name in enumerate(SHELL_ORDER := ("S0", "S1", "S2", "STRICT")):
        if int(comparison_counts.get(shell_name, 0)) > 0:
            comparison_highest = idx
    higher_shells = SHELL_ORDER[max(comparison_highest + 1, 0) :]
    return any(int(child_counts.get(shell_name, 0)) > int(comparison_counts.get(shell_name, 0)) for shell_name in higher_shells)


def _strict_margin_improved(parent_margin: float, child_margin: float) -> bool:
    return bool(
        (child_margin - parent_margin) >= 1.0
        or abs(child_margin) <= (0.8 * abs(parent_margin))
    )


def run_support_aware_tight_experiment(
    *,
    selection_profile: str,
    seed: int,
    parent_buffer_path: str | Path,
    parent_assignment_summary_path: str | Path,
    comparison_buffer_path: str | Path | None,
    comparison_assignment_summary_path: str | Path | None,
    comparison_support_shell_summary_path: str | Path | None,
    support_shell_summary_path: str | Path,
    thresholds_path: str | Path,
    base_config_path: str | Path,
    stage1_buffer_path: str | Path | None = None,
) -> dict[str, Any]:
    settings = _profile_settings(selection_profile)
    base.RUNNER_DIRNAME = settings["runner_dirname"]
    progress = base.ProgressTracker(total_steps=6 if stage1_buffer_path is None else 5)
    parent_buffer_path = _resolve_repo_path(parent_buffer_path)
    parent_assignment_summary_path = _resolve_repo_path(parent_assignment_summary_path)
    support_shell_summary_path = _resolve_repo_path(support_shell_summary_path)
    thresholds_path = _resolve_repo_path(thresholds_path)
    base_config_path = _resolve_repo_path(base_config_path)
    comparison_buffer_path = (
        _resolve_repo_path(comparison_buffer_path)
        if comparison_buffer_path is not None
        else parent_buffer_path
    )
    comparison_assignment_summary_path = (
        _resolve_repo_path(comparison_assignment_summary_path)
        if comparison_assignment_summary_path is not None
        else parent_assignment_summary_path
    )
    comparison_support_shell_summary_path = (
        _resolve_repo_path(comparison_support_shell_summary_path)
        if comparison_support_shell_summary_path is not None
        else support_shell_summary_path
    )

    manifest: dict[str, Any] = {
        "selection_profile": selection_profile,
        "method_name": settings["method_name"],
        "display_name": settings["display_name"],
        "seed": int(seed),
        "parent_buffer_path": str(parent_buffer_path.resolve()),
        "parent_assignment_summary_path": str(parent_assignment_summary_path.resolve()),
        "comparison_buffer_path": str(comparison_buffer_path.resolve()),
        "comparison_assignment_summary_path": str(comparison_assignment_summary_path.resolve()),
        "comparison_support_shell_summary_path": str(
            comparison_support_shell_summary_path.resolve()
        ),
        "support_shell_summary_path": str(support_shell_summary_path.resolve()),
        "thresholds_path": str(thresholds_path.resolve()),
        "base_config_path": str(base_config_path.resolve()),
        "runner_log": str(progress.log_path.resolve()),
        "runner_status": str(progress.status_path.resolve()),
    }
    save_json(_runner_root(selection_profile) / "run_manifest.json", manifest)

    try:
        if stage1_buffer_path is None:
            refinement_input = _build_support_refinement_buffer(
                selection_profile=selection_profile,
                seed=seed,
                parent_buffer_path=parent_buffer_path,
                support_shell_summary_path=support_shell_summary_path,
                progress=progress,
            )
        else:
            label = f"reuse stage1 buffer {selection_profile} seed_{seed:04d}"
            step_start = progress.start_step(label)
            refinement_input = _resolve_repo_path(stage1_buffer_path)
            progress.finish_step(label, step_start, skipped=True)

        train_buffer = _run_training(
            selection_profile=selection_profile,
            seed=seed,
            stage1_buffer_path=refinement_input,
            base_config_path=base_config_path,
            thresholds_path=thresholds_path,
            progress=progress,
        )
        assignment_summary_path = _run_assignment_summary(
            selection_profile=selection_profile,
            seed=seed,
            buffer_path=train_buffer,
            thresholds_path=thresholds_path,
            progress=progress,
        )
        support_shell_summary_path_child = _run_support_shell_summary(
            selection_profile=selection_profile,
            seed=seed,
            assignment_summary_path=assignment_summary_path,
            progress=progress,
        )
        tight_metrics_path = _run_selected_policy_tight_eval(
            selection_profile=selection_profile,
            seed=seed,
            buffer_path=train_buffer,
            thresholds_path=thresholds_path,
            progress=progress,
        )

        label = f"set quality compare {selection_profile} seed_{seed:04d}"
        step_start = progress.start_step(label)
        parent_set_quality, child_set_quality, reference_point = _shared_set_quality(
            parent_buffer_path=comparison_buffer_path,
            child_buffer_path=train_buffer,
        )
        progress.finish_step(label, step_start)

        comparison_support_summary = load_json(comparison_support_shell_summary_path)
        child_support_summary = load_json(support_shell_summary_path_child)
        comparison_assignment_summary = load_json(comparison_assignment_summary_path)
        child_assignment_summary = load_json(assignment_summary_path)
        comparison_closest = _closest_candidate_from_summary(comparison_assignment_summary_path)
        child_closest = _closest_candidate_from_summary(assignment_summary_path)

        comparison_margin = float(comparison_closest["strict_margin"])
        child_margin = float(child_closest["strict_margin"])
        hv_parent = float(parent_set_quality["hypervolume"])
        hv_child = float(child_set_quality["hypervolume"])
        eu_parent = float(parent_set_quality["expected_utility"])
        eu_child = float(child_set_quality["expected_utility"])
        higher_shell_gain = _higher_shell_gain(
            comparison_summary=comparison_support_summary,
            child_summary=child_support_summary,
        )
        strict_margin_improved = _strict_margin_improved(comparison_margin, child_margin)
        mean_violation_improved = float(child_closest["mean_violation"]) < float(
            comparison_closest["mean_violation"]
        )
        high_disruption_improved = float(child_closest["high_disruption_action_rate"]) < float(
            comparison_closest["high_disruption_action_rate"]
        )
        set_quality_ok = bool(hv_child >= 0.95 * hv_parent and eu_child >= 0.95 * eu_parent)
        should_run_adaptive_reweight = bool(
            selection_profile == "repair"
            and higher_shell_gain
            and strict_margin_improved
            and int(child_assignment_summary["strict_candidate_count"]) == 0
        )

        summary_dir = _summary_root(selection_profile)
        summary_dir.mkdir(parents=True, exist_ok=True)
        parent_set_quality_path = summary_dir / f"seed_{seed:04d}_parent_set_quality.json"
        child_set_quality_path = summary_dir / f"seed_{seed:04d}_child_set_quality.json"
        save_json(parent_set_quality_path, parent_set_quality)
        save_json(child_set_quality_path, child_set_quality)

        final_summary = {
            "selection_profile": selection_profile,
            "method_name": settings["method_name"],
            "display_name": settings["display_name"],
            "seed": int(seed),
            "refinement_input_buffer": str(refinement_input.resolve()),
            "train_buffer": str(train_buffer.resolve()),
            "assignment_summary_path": str(assignment_summary_path.resolve()),
            "support_shell_summary_path": str(support_shell_summary_path_child.resolve()),
            "selected_policy_tight_metrics_path": str(tight_metrics_path.resolve()),
            "parent_set_quality_path": str(parent_set_quality_path.resolve()),
            "child_set_quality_path": str(child_set_quality_path.resolve()),
            "shared_reference_point": reference_point,
            "comparison": {
                "comparison_buffer_path": str(comparison_buffer_path.resolve()),
                "comparison_assignment_summary_path": str(
                    comparison_assignment_summary_path.resolve()
                ),
                "comparison_support_shell_summary_path": str(
                    comparison_support_shell_summary_path.resolve()
                ),
                "comparison_strict_candidate_count": int(
                    comparison_assignment_summary["strict_candidate_count"]
                ),
                "comparison_closest_strict_margin": comparison_margin,
                "comparison_closest_mean_violation": float(
                    comparison_closest["mean_violation"]
                ),
                "comparison_closest_high_disruption_action_rate": float(
                    comparison_closest["high_disruption_action_rate"]
                ),
                "comparison_hypervolume": hv_parent,
                "comparison_expected_utility": eu_parent,
            },
            "child": {
                "strict_candidate_count": int(child_assignment_summary["strict_candidate_count"]),
                "closest_strict_margin": child_margin,
                "closest_mean_violation": float(child_closest["mean_violation"]),
                "closest_high_disruption_action_rate": float(
                    child_closest["high_disruption_action_rate"]
                ),
                "hypervolume": hv_child,
                "expected_utility": eu_child,
            },
            "acceptance": {
                "higher_shell_gain": bool(higher_shell_gain),
                "strict_margin_improved": bool(strict_margin_improved),
                "mean_violation_or_high_disruption_improved": bool(
                    mean_violation_improved or high_disruption_improved
                ),
                "set_quality_ok": bool(set_quality_ok),
                "continue_to_adaptive_reweight": bool(should_run_adaptive_reweight),
            },
            "runner_log": str(progress.log_path.resolve()),
            "runner_status": str(progress.status_path.resolve()),
        }
        final_summary_path = summary_dir / f"seed_{seed:04d}_final_summary.json"
        save_json(final_summary_path, final_summary)
        save_json(_runner_root(selection_profile) / "run_manifest.json", {**manifest, **final_summary})
        progress.finalize(success=True, extra={"final_summary_path": str(final_summary_path.resolve())})
        return final_summary
    except BaseException as exc:
        progress.fail_step(progress.current_label, exc)
        progress.log_exception_traceback(exc)
        progress.finalize(success=False, extra={"run_manifest_path": str((_runner_root(selection_profile) / "run_manifest.json").resolve())})
        raise


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run support-aware tight-feasible repair or adaptive reweight experiments."
    )
    parser.add_argument(
        "--selection-profile",
        choices=tuple(SELECTION_PROFILES.keys()),
        default="repair",
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--parent-buffer-path", default=DEFAULT_PARENT_BUFFER_PATH)
    parser.add_argument(
        "--parent-assignment-summary-path",
        default=DEFAULT_PARENT_ASSIGNMENT_SUMMARY_PATH,
    )
    parser.add_argument("--comparison-buffer-path", default=None)
    parser.add_argument("--comparison-assignment-summary-path", default=None)
    parser.add_argument("--comparison-support-shell-summary-path", default=None)
    parser.add_argument(
        "--support-shell-summary-path",
        default=DEFAULT_PARENT_SUPPORT_SHELL_SUMMARY_PATH,
    )
    parser.add_argument("--thresholds-path", default=DEFAULT_THRESHOLDS_PATH)
    parser.add_argument("--base-config-path", default=DEFAULT_BASE_CONFIG_PATH)
    parser.add_argument("--stage1-buffer-path", default=None)
    args = parser.parse_args()

    outputs = run_support_aware_tight_experiment(
        selection_profile=str(args.selection_profile),
        seed=int(args.seed),
        parent_buffer_path=args.parent_buffer_path,
        parent_assignment_summary_path=args.parent_assignment_summary_path,
        comparison_buffer_path=args.comparison_buffer_path,
        comparison_assignment_summary_path=args.comparison_assignment_summary_path,
        comparison_support_shell_summary_path=args.comparison_support_shell_summary_path,
        support_shell_summary_path=args.support_shell_summary_path,
        thresholds_path=args.thresholds_path,
        base_config_path=args.base_config_path,
        stage1_buffer_path=args.stage1_buffer_path,
    )
    for key, value in outputs.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
