from __future__ import annotations

import argparse
import copy
from pathlib import Path
from typing import Any

from cmorl_minicage.algorithms.selection import nondominated_filter
from cmorl_minicage.buffer import load_policy_buffer, save_policy_buffer
from cmorl_minicage.utils import load_json, save_json

from . import strong_tightplus_ours_fair_compare_runner as base
from .paper_plots import plot_fair_compare_table_b


DEFAULT_SEEDS = (7, 11)
DEFAULT_PARENT_METHOD_NAME = "ours_stage2_fair_tightplus"
DEFAULT_KEEP_TOP_K = 8
DEFAULT_NUM_EXTENSION_POLICIES = 4
DEFAULT_EXTENSION_ROUNDS = 1
DEFAULT_CONSTRAINT_TOLERANCE = -0.25
DEFAULT_CONSTRAINED_UPDATES = 6
DEFAULT_MAX_CONSECUTIVE_CONSTRAINT_FAILURES = 2
DEFAULT_BARRIER_COEF = 42.0
DEFAULT_BETA_MIN = 1.003
DEFAULT_BETA_MAX = 1.012
DEFAULT_SELECTED_EVAL_EPISODES = 40
DEFAULT_REEVALUATED_EVAL_EPISODES = 3

METHOD_NAME = "ours_stage2_fair_tightplus_tail"
DISPLAY_NAME = "Ours Stage2 Tight+ Tail"
RUNNER_DIRNAME = "fair_compare_tightplus_tail_runner"
COMPARE_PLOT_NAME = "fair_compare_table_b_tight_with_tightplus_tail_ours.png"
SUMMARY_CSV_NAME = "reevaluated_tight_feasible_set_summary_with_tightplus_tail_ours.csv"
SUMMARY_JSON_NAME = "reevaluated_tight_feasible_set_summary_with_tightplus_tail_ours.json"
SUMMARY_FIGURE_NAME = "reevaluated_tight_feasible_set_quality_with_tightplus_tail_ours.png"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _resolve_repo_path(raw_path: str | Path) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return (_repo_root() / path).resolve()


def _runner_root() -> Path:
    return base.ensure_dir(_resolve_repo_path(f"cmorl_cyborg/outputs/{RUNNER_DIRNAME}"))


def _generated_config_root() -> Path:
    return base.ensure_dir(_runner_root() / "generated_configs")


def _refinement_input_root() -> Path:
    return base.ensure_dir(_runner_root() / "refinement_inputs")


def _train_seed_root(seed: int) -> Path:
    return _resolve_repo_path(
        f"cmorl_cyborg/outputs/fair_compare_tuning/{METHOD_NAME}/seed_{seed:04d}"
    )


def _eval_input_buffer_path(seed: int) -> Path:
    return _resolve_repo_path(
        f"cmorl_cyborg/outputs/fair_compare_eval_inputs/{METHOD_NAME}/seed_{seed:04d}/solution_buffer.json"
    )


def _tight_metrics_path(seed: int) -> Path:
    return _resolve_repo_path(
        f"cmorl_cyborg/outputs/fair_compare_eval/tight/{METHOD_NAME}/seed_{seed:04d}/constraint_metrics.json"
    )


def _seed_summary_path(seed: int) -> Path:
    return _resolve_repo_path(
        f"cmorl_cyborg/outputs/fair_compare_eval/reevaluated_tight_feasible_set_summary/{METHOD_NAME}/seed_{seed:04d}.json"
    )


def _parent_train_buffer_path(seed: int, parent_method_name: str) -> Path:
    root = _resolve_repo_path(
        f"cmorl_cyborg/outputs/fair_compare_tuning/{parent_method_name}/seed_{seed:04d}"
    )
    path = base._latest_run_artifact(root, "solution_buffer.json")
    if path is None:
        raise FileNotFoundError(
            f"Missing parent solution_buffer.json for {parent_method_name} seed {seed:04d}"
        )
    return path


def _parent_reevaluated_summary_path(seed: int, parent_method_name: str) -> Path:
    path = _resolve_repo_path(
        f"cmorl_cyborg/outputs/fair_compare_eval/reevaluated_tight_feasible_set_summary/{parent_method_name}/seed_{seed:04d}.json"
    )
    if not path.exists():
        raise FileNotFoundError(
            f"Missing reevaluated tight summary for {parent_method_name} seed {seed:04d}: {path}"
        )
    return path


def _parent_selected_aggregate_path(parent_method_name: str) -> Path:
    return _resolve_repo_path(
        f"cmorl_cyborg/outputs/fair_compare_eval/aggregated/{parent_method_name}_tight.json"
    )


def _parent_reevaluated_aggregate_path(parent_method_name: str) -> Path:
    if parent_method_name == "ours_stage2_fair_tightplus":
        return _resolve_repo_path(
            "cmorl_cyborg/outputs/fair_compare_eval/aggregated/"
            "reevaluated_tight_feasible_set_summary_with_tightplus_ours.json"
        )
    return _resolve_repo_path(
        "cmorl_cyborg/outputs/fair_compare_eval/aggregated/"
        f"reevaluated_tight_feasible_set_summary_with_{parent_method_name}.json"
    )


def _refinement_input_buffer_path(seed: int) -> Path:
    return _refinement_input_root() / f"seed_{seed:04d}" / "solution_buffer.json"


def _candidate_priority_rows(seed: int, parent_method_name: str) -> list[dict[str, Any]]:
    payload = load_json(_parent_reevaluated_summary_path(seed, parent_method_name))
    candidate_rows = list(payload.get("candidate_rows", []))
    if not candidate_rows:
        raise ValueError(f"No candidate rows found for {parent_method_name} seed {seed:04d}")
    return sorted(
        candidate_rows,
        key=lambda row: (
            float(row.get("reevaluated_margin", float("-inf"))),
            float(row.get("reevaluated_cost_return", float("-inf"))),
            float(row.get("reevaluated_business_return", float("-inf"))),
            float(row.get("reevaluated_security_return", float("-inf"))),
            str(row.get("policy_id", "")),
        ),
        reverse=True,
    )


def _select_refinement_policy_ids(
    *,
    seed: int,
    parent_method_name: str,
    keep_top_k: int,
) -> list[str]:
    rows = _candidate_priority_rows(seed, parent_method_name)
    selected_ids: list[str] = []
    seen: set[str] = set()

    def _add(policy_id: str) -> None:
        if policy_id and policy_id not in seen:
            selected_ids.append(policy_id)
            seen.add(policy_id)

    for row in rows[: max(int(keep_top_k), 1)]:
        _add(str(row["policy_id"]))

    for metric_name in (
        "reevaluated_cost_return",
        "reevaluated_business_return",
        "reevaluated_security_return",
    ):
        best_row = max(rows, key=lambda row: float(row.get(metric_name, float("-inf"))))
        _add(str(best_row["policy_id"]))

    return selected_ids


def _build_refinement_buffer(
    *,
    seed: int,
    parent_method_name: str,
    keep_top_k: int,
    progress: base.ProgressTracker,
) -> Path:
    output_path = _refinement_input_buffer_path(seed)
    label = f"build refinement input seed_{seed:04d}"
    if output_path.exists():
        step_start = progress.start_step(label)
        progress.finish_step(label, step_start, skipped=True)
        return output_path.resolve()

    step_start = progress.start_step(label)
    parent_buffer_path = _parent_train_buffer_path(seed, parent_method_name)
    parent_payload = load_policy_buffer(parent_buffer_path)
    all_records = list(parent_payload.get("records", []))
    record_by_id = {str(record["policy_id"]): record for record in all_records}

    selected_ids = _select_refinement_policy_ids(
        seed=seed,
        parent_method_name=parent_method_name,
        keep_top_k=keep_top_k,
    )
    selected_records = [
        copy.deepcopy(record_by_id[policy_id])
        for policy_id in selected_ids
        if policy_id in record_by_id
    ]
    if not selected_records:
        raise ValueError(f"Failed to select any refinement records for seed {seed:04d}")

    filtered_pareto = nondominated_filter(selected_records)
    metadata = dict(parent_payload.get("metadata", {}))
    metadata["refinement_tail"] = {
        "enabled": True,
        "parent_method_name": parent_method_name,
        "parent_buffer_path": str(parent_buffer_path.resolve()),
        "parent_reevaluated_summary_path": str(
            _parent_reevaluated_summary_path(seed, parent_method_name).resolve()
        ),
        "seed": int(seed),
        "keep_top_k": int(keep_top_k),
        "selected_policy_ids": [str(policy_id) for policy_id in selected_ids],
        "selected_record_count": len(selected_records),
        "selected_pareto_count": len(filtered_pareto),
        "selection_rule": (
            "top reevaluated tight-margin records plus best cost/business/security anchors"
        ),
    }
    save_policy_buffer(
        output_path,
        metadata=metadata,
        records=selected_records,
        pareto_front=filtered_pareto,
    )
    progress.finish_step(label, step_start)
    return output_path.resolve()


def _materialize_stage2_config(
    *,
    seed: int,
    stage1_buffer_path: Path,
    num_extension_policies: int,
    extension_rounds: int,
    constraint_tolerance: float,
    constrained_updates: int,
    max_consecutive_constraint_failures: int,
    barrier_coef: float,
    beta_min: float,
    beta_max: float,
) -> Path:
    base_config_path = _resolve_repo_path(
        f"cmorl_cyborg/configs/paper/fair_compare/stage2_fair_constrained_seed_{seed:04d}.yaml"
    )
    payload = base._load_yaml(base_config_path)
    payload["stage1_buffer"] = str(stage1_buffer_path.resolve())
    payload["num_extension_policies"] = int(num_extension_policies)
    payload["extension_rounds"] = int(extension_rounds)
    payload["constraint_tolerance"] = float(constraint_tolerance)
    payload["constrained_updates"] = int(constrained_updates)
    payload["max_consecutive_constraint_failures"] = int(
        max_consecutive_constraint_failures
    )
    payload["output_dir"] = f"cmorl_cyborg/outputs/fair_compare_tuning/{METHOD_NAME}/seed_{seed:04d}"
    payload["selection"] = {
        "mode": "adaptive",
        "coverage_mode": "static",
        "keep_extremes": True,
        "score_weights": {
            "crowding": 0.20,
            "expansion": 0.15,
            "low_risk": 0.45,
            "coverage": 0.20,
            "semantic_low_risk": 0.0,
        },
    }
    ipo = dict(payload.get("ipo", {}) or {})
    ipo["barrier_coef"] = float(barrier_coef)
    ipo["beta_min"] = float(beta_min)
    ipo["beta_max"] = float(beta_max)
    payload["ipo"] = ipo
    config_path = _generated_config_root() / f"stage2_fair_tightplus_tail_seed_{seed:04d}.yaml"
    return base._write_yaml(config_path, payload)


def _materialize_eval_config(*, seed: int, buffer_path: Path, eval_episodes: int) -> Path:
    payload = {
        "method_name": METHOD_NAME,
        "input_kind": "buffer",
        "input_path": str(buffer_path.resolve()),
        "selection_source": "pareto",
        "selection_policy": "objective",
        "thresholds_path": str(base._thresholds_tight_path().resolve()),
        "output_path": str(_tight_metrics_path(seed).resolve()),
        "eval_episodes": int(eval_episodes),
    }
    config_path = _generated_config_root() / f"evaluate_tight_seed_{seed:04d}.yaml"
    return base._write_yaml(config_path, payload)


def _run_training_for_seed(
    *,
    seed: int,
    stage1_buffer_path: Path,
    num_extension_policies: int,
    extension_rounds: int,
    constraint_tolerance: float,
    constrained_updates: int,
    max_consecutive_constraint_failures: int,
    barrier_coef: float,
    beta_min: float,
    beta_max: float,
    progress: base.ProgressTracker,
) -> Path:
    seed_root = _train_seed_root(seed)
    existing = base._latest_run_artifact(seed_root, "solution_buffer.json")
    label = f"train tightplus_tail seed_{seed:04d}"
    if existing is not None:
        step_start = progress.start_step(label)
        progress.finish_step(label, step_start, skipped=True)
        return existing

    config_path = _materialize_stage2_config(
        seed=seed,
        stage1_buffer_path=stage1_buffer_path,
        num_extension_policies=num_extension_policies,
        extension_rounds=extension_rounds,
        constraint_tolerance=constraint_tolerance,
        constrained_updates=constrained_updates,
        max_consecutive_constraint_failures=max_consecutive_constraint_failures,
        barrier_coef=barrier_coef,
        beta_min=beta_min,
        beta_max=beta_max,
    )
    step_start = progress.start_step(label)
    base._run_module(
        "cmorl_cyborg.train_stage2",
        ["--config", str(config_path), "--output-dir", str(seed_root)],
        progress=progress,
        label=label,
    )
    progress.finish_step(label, step_start)
    created = base._latest_run_artifact(seed_root, "solution_buffer.json")
    if created is None:
        raise FileNotFoundError(f"Missing solution_buffer.json under {seed_root}")
    return created.resolve()


def _copy_eval_input_for_seed(*, seed: int, train_buffer_path: Path, progress: base.ProgressTracker) -> Path:
    target_path = _eval_input_buffer_path(seed)
    label = f"copy eval_input tail seed_{seed:04d}"
    step_start = progress.start_step(label)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_bytes(train_buffer_path.read_bytes())
    progress.finish_step(label, step_start)
    return target_path.resolve()


def _run_tight_eval_for_seed(
    *,
    seed: int,
    input_buffer_path: Path,
    selected_eval_episodes: int,
    progress: base.ProgressTracker,
) -> Path:
    output_path = _tight_metrics_path(seed)
    label = f"tight eval tail seed_{seed:04d}"
    if output_path.exists():
        step_start = progress.start_step(label)
        progress.finish_step(label, step_start, skipped=True)
        return output_path.resolve()

    config_path = _materialize_eval_config(
        seed=seed,
        buffer_path=input_buffer_path,
        eval_episodes=selected_eval_episodes,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    step_start = progress.start_step(label)
    base._run_module(
        "cmorl_cyborg.evaluate_constraints",
        ["--config", str(config_path)],
        progress=progress,
        label=label,
    )
    progress.finish_step(label, step_start)
    return output_path.resolve()


def _reevaluate_seed(
    *,
    seed: int,
    constraint_metrics_path: Path,
    reevaluated_eval_episodes: int,
    progress: base.ProgressTracker,
) -> dict[str, Any]:
    base.reevaluate_mod.DISPLAY_NAMES[METHOD_NAME] = DISPLAY_NAME
    base.reevaluate_mod.COLORS[METHOD_NAME] = "#b279a2"
    label = f"reevaluate tail seed_{seed:04d}"
    step_start = progress.start_step(label)
    summary = base.reevaluate_mod._seed_summary(
        method_name=METHOD_NAME,
        constraint_metrics_path=constraint_metrics_path,
        eval_episodes=int(reevaluated_eval_episodes),
        logger=base._CandidateLogger(progress),
    )
    save_json(_seed_summary_path(seed), summary)
    progress.finish_step(label, step_start)
    return summary


def _aggregate_selected_policy(*, metrics_paths: list[Path], progress: base.ProgressTracker) -> Path:
    label = "aggregate tightplus-tail selected-policy tight metrics"
    step_start = progress.start_step(label)
    aggregate_path = base._aggregated_root() / f"{METHOD_NAME}_tight.json"
    base.write_aggregated_constraint_metrics(
        [str(path.resolve()) for path in metrics_paths],
        aggregate_path,
        method_name=METHOD_NAME,
    )
    progress.finish_step(label, step_start)
    return aggregate_path.resolve()


def _plot_selected_policy_compare(*, new_aggregate_path: Path, progress: base.ProgressTracker) -> Path:
    label = "plot tightplus-tail selected-policy compare"
    step_start = progress.start_step(label)
    output_path = base._aggregated_root() / COMPARE_PLOT_NAME
    baseline_paths = [
        base._aggregated_root() / "ours_stage2_fair_tight.json",
        base._aggregated_root() / "ours_stage2_fair_tighter_tight.json",
        _parent_selected_aggregate_path(DEFAULT_PARENT_METHOD_NAME),
        new_aggregate_path,
        base._aggregated_root() / "no_constraint_stage2_fair_tight.json",
        base._aggregated_root() / "coverage_combo_fair_tight.json",
        base._aggregated_root() / "coverage_more_parents_fair_tight.json",
    ]
    plot_fair_compare_table_b(
        aggregated_paths=[str(path.resolve()) for path in baseline_paths],
        output_path=output_path,
    )
    progress.finish_step(label, step_start)
    return output_path.resolve()


def _aggregate_reevaluated_compare(
    *,
    seed_rows: list[dict[str, Any]],
    reevaluated_eval_episodes: int,
    progress: base.ProgressTracker,
) -> dict[str, Path]:
    base.reevaluate_mod.DISPLAY_NAMES[METHOD_NAME] = DISPLAY_NAME
    base.reevaluate_mod.COLORS[METHOD_NAME] = "#b279a2"
    label = "aggregate tightplus-tail reevaluated set metrics"
    step_start = progress.start_step(label)
    new_row = base.reevaluate_mod._aggregate_method_rows(METHOD_NAME, seed_rows)

    baseline_payload = load_json(
        _parent_reevaluated_aggregate_path(DEFAULT_PARENT_METHOD_NAME)
    )
    baseline_rows = list(baseline_payload.get("methods", []))
    filtered_rows = [row for row in baseline_rows if str(row.get("method_name")) != METHOD_NAME]
    combined_rows = []
    for method_name in (
        base.BASE_METHOD_NAME,
        "ours_stage2_fair_tighter",
        DEFAULT_PARENT_METHOD_NAME,
        METHOD_NAME,
        "no_constraint_stage2_fair",
        "coverage_combo_fair",
        "coverage_more_parents_fair",
    ):
        if method_name == METHOD_NAME:
            combined_rows.append(new_row)
            continue
        match = next((row for row in filtered_rows if str(row.get("method_name")) == method_name), None)
        if match is not None:
            combined_rows.append(match)

    csv_path = base._aggregated_root() / SUMMARY_CSV_NAME
    json_path = base._aggregated_root() / SUMMARY_JSON_NAME
    figure_path = base._aggregated_root() / SUMMARY_FIGURE_NAME

    base.reevaluate_mod._write_aggregate_csv(csv_path, combined_rows)
    save_json(
        json_path,
        {
            "methods": combined_rows,
            "eval_episodes": int(reevaluated_eval_episodes),
            "thresholds": load_json(base._thresholds_tight_path()),
            "baseline_summary_path": str(
                _parent_reevaluated_aggregate_path(DEFAULT_PARENT_METHOD_NAME).resolve()
            ),
            "new_method_name": METHOD_NAME,
            "parent_method_name": DEFAULT_PARENT_METHOD_NAME,
        },
    )
    base.reevaluate_mod._plot_reevaluated_tight_feasible_set(combined_rows, figure_path)
    progress.finish_step(label, step_start)
    return {"csv": csv_path.resolve(), "json": json_path.resolve(), "figure": figure_path.resolve()}


def run_tightplus_refinement_tail(
    *,
    seeds: tuple[int, ...],
    parent_method_name: str,
    keep_top_k: int,
    num_extension_policies: int,
    extension_rounds: int,
    constraint_tolerance: float,
    constrained_updates: int,
    max_consecutive_constraint_failures: int,
    barrier_coef: float,
    beta_min: float,
    beta_max: float,
    selected_eval_episodes: int,
    reevaluated_eval_episodes: int,
) -> dict[str, Any]:
    base.RUNNER_DIRNAME = RUNNER_DIRNAME
    seed_order = tuple(dict.fromkeys(int(seed) for seed in seeds))
    total_steps = len(seed_order) * 5 + 3
    progress = base.ProgressTracker(total_steps=total_steps)

    manifest: dict[str, Any] = {
        "method_name": METHOD_NAME,
        "display_name": DISPLAY_NAME,
        "parent_method_name": parent_method_name,
        "seeds": list(seed_order),
        "keep_top_k": int(keep_top_k),
        "num_extension_policies": int(num_extension_policies),
        "extension_rounds": int(extension_rounds),
        "constraint_tolerance": float(constraint_tolerance),
        "constrained_updates": int(constrained_updates),
        "max_consecutive_constraint_failures": int(max_consecutive_constraint_failures),
        "barrier_coef": float(barrier_coef),
        "beta_min": float(beta_min),
        "beta_max": float(beta_max),
        "selected_eval_episodes": int(selected_eval_episodes),
        "reevaluated_eval_episodes": int(reevaluated_eval_episodes),
        "runner_log": str(progress.log_path.resolve()),
        "runner_status": str(progress.status_path.resolve()),
        "started_at": progress.pipeline_started_at,
        "per_seed": {},
    }
    save_json(_runner_root() / "run_manifest.json", manifest)

    successful_seeds: list[int] = []
    metrics_paths: list[Path] = []
    seed_rows: list[dict[str, Any]] = []
    try:
        for seed in seed_order:
            refinement_input = _build_refinement_buffer(
                seed=seed,
                parent_method_name=parent_method_name,
                keep_top_k=keep_top_k,
                progress=progress,
            )
            train_buffer = _run_training_for_seed(
                seed=seed,
                stage1_buffer_path=refinement_input,
                num_extension_policies=num_extension_policies,
                extension_rounds=extension_rounds,
                constraint_tolerance=constraint_tolerance,
                constrained_updates=constrained_updates,
                max_consecutive_constraint_failures=max_consecutive_constraint_failures,
                barrier_coef=barrier_coef,
                beta_min=beta_min,
                beta_max=beta_max,
                progress=progress,
            )
            eval_input = _copy_eval_input_for_seed(
                seed=seed, train_buffer_path=train_buffer, progress=progress
            )
            metrics_path = _run_tight_eval_for_seed(
                seed=seed,
                input_buffer_path=eval_input,
                selected_eval_episodes=selected_eval_episodes,
                progress=progress,
            )
            seed_summary = _reevaluate_seed(
                seed=seed,
                constraint_metrics_path=metrics_path,
                reevaluated_eval_episodes=reevaluated_eval_episodes,
                progress=progress,
            )
            parent_summary = load_json(_parent_reevaluated_summary_path(seed, parent_method_name))
            manifest["per_seed"][f"seed_{seed:04d}"] = {
                "refinement_input_buffer": str(refinement_input),
                "train_buffer": str(train_buffer),
                "eval_input_buffer": str(eval_input),
                "tight_metrics": str(metrics_path),
                "reevaluated_seed_summary": str(_seed_summary_path(seed).resolve()),
                "parent_closest_candidate_margin": float(parent_summary["closest_candidate_margin"]),
                "parent_reevaluated_feasible_candidate_count": int(
                    parent_summary["reevaluated_feasible_candidate_count"]
                ),
                "tail_pareto_candidate_count": int(base._candidate_count_from_buffer(eval_input)),
                "tail_reevaluated_feasible_candidate_count": int(
                    seed_summary["reevaluated_feasible_candidate_count"]
                ),
                "tail_closest_candidate_margin": float(seed_summary["closest_candidate_margin"]),
                "margin_delta_vs_parent": float(
                    seed_summary["closest_candidate_margin"] - parent_summary["closest_candidate_margin"]
                ),
            }
            successful_seeds.append(seed)
            metrics_paths.append(metrics_path)
            seed_rows.append(seed_summary)
            save_json(_runner_root() / "run_manifest.json", manifest)

        selected_aggregate_path = _aggregate_selected_policy(
            metrics_paths=metrics_paths,
            progress=progress,
        )
        selected_compare_plot = _plot_selected_policy_compare(
            new_aggregate_path=selected_aggregate_path,
            progress=progress,
        )
        reevaluated_outputs = _aggregate_reevaluated_compare(
            seed_rows=seed_rows,
            reevaluated_eval_episodes=reevaluated_eval_episodes,
            progress=progress,
        )

        final_summary = {
            "method_name": METHOD_NAME,
            "display_name": DISPLAY_NAME,
            "parent_method_name": parent_method_name,
            "completed_seeds": successful_seeds,
            "selected_policy_aggregate_path": str(selected_aggregate_path),
            "selected_policy_compare_plot": str(selected_compare_plot),
            "reevaluated_compare_csv": str(reevaluated_outputs["csv"]),
            "reevaluated_compare_json": str(reevaluated_outputs["json"]),
            "reevaluated_compare_figure": str(reevaluated_outputs["figure"]),
            "runner_log": str(progress.log_path.resolve()),
            "runner_status": str(progress.status_path.resolve()),
            "run_manifest_path": str((_runner_root() / "run_manifest.json").resolve()),
        }
        save_json(_runner_root() / "final_summary.json", final_summary)
        progress.finalize(success=True, extra=final_summary)
        return final_summary
    except BaseException as exc:
        progress.fail_step(progress.current_label, exc)
        progress.log_exception_traceback(exc)
        progress.finalize(
            success=False,
            extra={
                "completed_seeds": successful_seeds,
                "run_manifest_path": str((_runner_root() / "run_manifest.json").resolve()),
            },
        )
        raise


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run a targeted tightplus refinement tail for seeds 0007 and 0011. "
            "Starts from the tightplus buffer, keeps the candidates closest to the tight-feasible "
            "region, and performs one additional constrained Stage-2 tail round."
        )
    )
    parser.add_argument("--seeds", nargs="+", type=int, default=list(DEFAULT_SEEDS))
    parser.add_argument("--parent-method-name", default=DEFAULT_PARENT_METHOD_NAME)
    parser.add_argument("--keep-top-k", type=int, default=DEFAULT_KEEP_TOP_K)
    parser.add_argument("--num-extension-policies", type=int, default=DEFAULT_NUM_EXTENSION_POLICIES)
    parser.add_argument("--extension-rounds", type=int, default=DEFAULT_EXTENSION_ROUNDS)
    parser.add_argument("--constraint-tolerance", type=float, default=DEFAULT_CONSTRAINT_TOLERANCE)
    parser.add_argument("--constrained-updates", type=int, default=DEFAULT_CONSTRAINED_UPDATES)
    parser.add_argument(
        "--max-consecutive-constraint-failures",
        type=int,
        default=DEFAULT_MAX_CONSECUTIVE_CONSTRAINT_FAILURES,
    )
    parser.add_argument("--barrier-coef", type=float, default=DEFAULT_BARRIER_COEF)
    parser.add_argument("--beta-min", type=float, default=DEFAULT_BETA_MIN)
    parser.add_argument("--beta-max", type=float, default=DEFAULT_BETA_MAX)
    parser.add_argument("--selected-eval-episodes", type=int, default=DEFAULT_SELECTED_EVAL_EPISODES)
    parser.add_argument("--reevaluated-eval-episodes", type=int, default=DEFAULT_REEVALUATED_EVAL_EPISODES)
    args = parser.parse_args()

    outputs = run_tightplus_refinement_tail(
        seeds=tuple(int(seed) for seed in args.seeds),
        parent_method_name=str(args.parent_method_name),
        keep_top_k=int(args.keep_top_k),
        num_extension_policies=int(args.num_extension_policies),
        extension_rounds=int(args.extension_rounds),
        constraint_tolerance=float(args.constraint_tolerance),
        constrained_updates=int(args.constrained_updates),
        max_consecutive_constraint_failures=int(args.max_consecutive_constraint_failures),
        barrier_coef=float(args.barrier_coef),
        beta_min=float(args.beta_min),
        beta_max=float(args.beta_max),
        selected_eval_episodes=int(args.selected_eval_episodes),
        reevaluated_eval_episodes=int(args.reevaluated_eval_episodes),
    )
    for key, value in outputs.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
