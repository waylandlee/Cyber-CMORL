from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from cmorl_minicage.utils import load_json, save_json

from . import export_tight_feasible_set_reevaluated as reevaluate_mod
from . import strong_tightplus_ours_fair_compare_runner as base
from .evaluate_constraints import write_aggregated_constraint_metrics
from .paper_plots import plot_fair_compare_table_b


DEFAULT_SEEDS = (7, 11, 19)
DEFAULT_SELECTED_EVAL_EPISODES = 40
DEFAULT_REEVALUATED_EVAL_EPISODES = 3

BASELINE_METHOD_NAME = "no_constraint_stage2_fair"
METHOD_NAME = "no_constraint_stage2_fair_rerun"
DISPLAY_NAME = "No-Constraint Stage2 Rerun"
RUNNER_DIRNAME = "fair_compare_no_constraint_rerun_runner"
COMPARE_PLOT_NAME = "fair_compare_table_b_tight_no_constraint_rerun_vs_baseline.png"
SUMMARY_CSV_NAME = "reevaluated_tight_feasible_set_summary_with_no_constraint_rerun.csv"
SUMMARY_JSON_NAME = "reevaluated_tight_feasible_set_summary_with_no_constraint_rerun.json"
SUMMARY_FIGURE_NAME = "reevaluated_tight_feasible_set_quality_with_no_constraint_rerun.png"
DIFF_JSON_NAME = "no_constraint_stage2_fair_rerun_diff.json"
DIFF_CSV_NAME = "no_constraint_stage2_fair_rerun_diff.csv"


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


def _train_seed_root(seed: int) -> Path:
    return _resolve_repo_path(
        f"cmorl_cyborg/outputs/fair_compare_rerun/{METHOD_NAME}/seed_{seed:04d}"
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


def _aggregated_root() -> Path:
    return base._aggregated_root()


def _baseline_selected_aggregate_path() -> Path:
    return _aggregated_root() / "no_constraint_stage2_fair_tight.json"


def _baseline_reevaluated_aggregate_path() -> Path:
    return _aggregated_root() / "reevaluated_tight_feasible_set_summary.json"


def _baseline_seed_summary_path(seed: int) -> Path:
    return _resolve_repo_path(
        f"cmorl_cyborg/outputs/fair_compare_eval/reevaluated_tight_feasible_set_summary/{BASELINE_METHOD_NAME}/seed_{seed:04d}.json"
    )


def _baseline_constraint_metrics_path(seed: int) -> Path:
    return _resolve_repo_path(
        f"cmorl_cyborg/outputs/fair_compare_eval/tight/{BASELINE_METHOD_NAME}/seed_{seed:04d}/constraint_metrics.json"
    )


def _load_yaml(path: str | Path) -> dict[str, Any]:
    return base._load_yaml(path)


def _write_yaml(path: str | Path, payload: dict[str, Any]) -> Path:
    return base._write_yaml(path, payload)


def _materialize_stage2_config(seed: int) -> Path:
    base_config_path = _resolve_repo_path(
        f"cmorl_cyborg/configs/paper/fair_compare/stage2_fair_unconstrained_seed_{seed:04d}.yaml"
    )
    payload = _load_yaml(base_config_path)
    payload["output_dir"] = f"cmorl_cyborg/outputs/fair_compare_rerun/{METHOD_NAME}/seed_{seed:04d}"
    config_path = _generated_config_root() / f"stage2_fair_unconstrained_rerun_seed_{seed:04d}.yaml"
    return _write_yaml(config_path, payload)


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
    return _write_yaml(config_path, payload)


def _run_training_for_seed(*, seed: int, progress: base.ProgressTracker) -> Path:
    seed_root = _train_seed_root(seed)
    existing = base._latest_run_artifact(seed_root, "solution_buffer.json")
    label = f"train no_constraint_rerun seed_{seed:04d}"
    if existing is not None:
        step_start = progress.start_step(label)
        progress.finish_step(label, step_start, skipped=True)
        return existing

    config_path = _materialize_stage2_config(seed)
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
    label = f"copy eval_input rerun seed_{seed:04d}"
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
    label = f"tight eval rerun seed_{seed:04d}"
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
    reevaluate_mod.DISPLAY_NAMES[METHOD_NAME] = DISPLAY_NAME
    reevaluate_mod.COLORS[METHOD_NAME] = "#9c755f"
    label = f"reevaluate rerun seed_{seed:04d}"
    step_start = progress.start_step(label)
    summary = reevaluate_mod._seed_summary(
        method_name=METHOD_NAME,
        constraint_metrics_path=constraint_metrics_path,
        eval_episodes=int(reevaluated_eval_episodes),
        logger=base._CandidateLogger(progress),
    )
    save_json(_seed_summary_path(seed), summary)
    progress.finish_step(label, step_start)
    return summary


def _aggregate_selected_policy(*, metrics_paths: list[Path], progress: base.ProgressTracker) -> Path:
    label = "aggregate no_constraint rerun selected-policy tight metrics"
    step_start = progress.start_step(label)
    aggregate_path = _aggregated_root() / f"{METHOD_NAME}_tight.json"
    write_aggregated_constraint_metrics(
        [str(path.resolve()) for path in metrics_paths],
        aggregate_path,
        method_name=METHOD_NAME,
    )
    progress.finish_step(label, step_start)
    return aggregate_path.resolve()


def _plot_selected_policy_compare(*, new_aggregate_path: Path, progress: base.ProgressTracker) -> Path:
    label = "plot no_constraint rerun selected-policy compare"
    step_start = progress.start_step(label)
    output_path = _aggregated_root() / COMPARE_PLOT_NAME
    plot_fair_compare_table_b(
        aggregated_paths=[
            str(_baseline_selected_aggregate_path().resolve()),
            str(new_aggregate_path.resolve()),
        ],
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
    reevaluate_mod.DISPLAY_NAMES[METHOD_NAME] = DISPLAY_NAME
    reevaluate_mod.COLORS[METHOD_NAME] = "#9c755f"
    label = "aggregate no_constraint rerun reevaluated set metrics"
    step_start = progress.start_step(label)
    new_row = reevaluate_mod._aggregate_method_rows(METHOD_NAME, seed_rows)

    baseline_payload = load_json(_baseline_reevaluated_aggregate_path())
    baseline_rows = list(baseline_payload.get("methods", []))
    baseline_row = next(
        row for row in baseline_rows if str(row.get("method_name")) == BASELINE_METHOD_NAME
    )
    combined_rows = [baseline_row, new_row]

    csv_path = _aggregated_root() / SUMMARY_CSV_NAME
    json_path = _aggregated_root() / SUMMARY_JSON_NAME
    figure_path = _aggregated_root() / SUMMARY_FIGURE_NAME

    reevaluate_mod._write_aggregate_csv(csv_path, combined_rows)
    save_json(
        json_path,
        {
            "methods": combined_rows,
            "eval_episodes": int(reevaluated_eval_episodes),
            "thresholds": load_json(base._thresholds_tight_path()),
            "baseline_summary_path": str(_baseline_reevaluated_aggregate_path().resolve()),
            "new_method_name": METHOD_NAME,
            "baseline_method_name": BASELINE_METHOD_NAME,
        },
    )
    reevaluate_mod._plot_reevaluated_tight_feasible_set(combined_rows, figure_path)
    progress.finish_step(label, step_start)
    return {"csv": csv_path.resolve(), "json": json_path.resolve(), "figure": figure_path.resolve()}


def _diff_dict(current: dict[str, Any], baseline: dict[str, Any], keys: list[str]) -> dict[str, float | None]:
    out: dict[str, float | None] = {}
    for key in keys:
        current_value = current.get(key)
        baseline_value = baseline.get(key)
        if current_value is None or baseline_value is None:
            out[key] = None
        else:
            out[key] = float(current_value) - float(baseline_value)
    return out


def _write_compare_summary(
    *,
    completed_seeds: list[int],
    rerun_selected_aggregate_path: Path,
    rerun_reevaluated_json_path: Path,
) -> dict[str, Any]:
    baseline_selected = load_json(_baseline_selected_aggregate_path())
    rerun_selected = load_json(rerun_selected_aggregate_path)
    baseline_reevaluated_payload = load_json(_baseline_reevaluated_aggregate_path())
    baseline_reevaluated = next(
        row
        for row in baseline_reevaluated_payload.get("methods", [])
        if str(row.get("method_name")) == BASELINE_METHOD_NAME
    )
    rerun_reevaluated_payload = load_json(rerun_reevaluated_json_path)
    rerun_reevaluated = next(
        row
        for row in rerun_reevaluated_payload.get("methods", [])
        if str(row.get("method_name")) == METHOD_NAME
    )

    selected_keys = [
        "security_return",
        "business_return",
        "cost_return",
        "feasible_rate",
        "mean_violation",
        "final_critical_compromised_hosts",
        "critical_impact_count",
        "high_disruption_action_rate",
    ]
    reevaluated_keys = [
        "reevaluated_feasible_candidate_count",
        "reevaluated_feasible_pareto_ratio",
        "best_reevaluated_feasible_security_return",
        "num_runs_with_reevaluated_feasible_candidate",
        "closest_candidate_margin",
    ]

    per_seed: dict[str, Any] = {}
    for seed in completed_seeds:
        baseline_seed = load_json(_baseline_seed_summary_path(seed))
        rerun_seed = load_json(_seed_summary_path(seed))
        baseline_tight = load_json(_baseline_constraint_metrics_path(seed))
        rerun_tight = load_json(_tight_metrics_path(seed))
        per_seed[f"seed_{seed:04d}"] = {
            "reevaluated_baseline": {
                "feasible_candidate_count": int(baseline_seed["reevaluated_feasible_candidate_count"]),
                "closest_candidate_margin": float(baseline_seed["closest_candidate_margin"]),
                "closest_candidate_policy_id": str(baseline_seed["closest_candidate_policy_id"]),
            },
            "reevaluated_rerun": {
                "feasible_candidate_count": int(rerun_seed["reevaluated_feasible_candidate_count"]),
                "closest_candidate_margin": float(rerun_seed["closest_candidate_margin"]),
                "closest_candidate_policy_id": str(rerun_seed["closest_candidate_policy_id"]),
            },
            "reevaluated_delta": {
                "feasible_candidate_count": int(rerun_seed["reevaluated_feasible_candidate_count"])
                - int(baseline_seed["reevaluated_feasible_candidate_count"]),
                "closest_candidate_margin": float(rerun_seed["closest_candidate_margin"])
                - float(baseline_seed["closest_candidate_margin"]),
            },
            "selected_policy_baseline": {
                "security_return": float(baseline_tight["security_return"]),
                "business_return": float(baseline_tight["business_return"]),
                "cost_return": float(baseline_tight["cost_return"]),
                "feasible_rate": float(baseline_tight["feasible_rate"]),
                "mean_violation": float(baseline_tight["mean_violation"]),
                "selected_policy_id": str(baseline_tight["selected_policy_id"]),
            },
            "selected_policy_rerun": {
                "security_return": float(rerun_tight["security_return"]),
                "business_return": float(rerun_tight["business_return"]),
                "cost_return": float(rerun_tight["cost_return"]),
                "feasible_rate": float(rerun_tight["feasible_rate"]),
                "mean_violation": float(rerun_tight["mean_violation"]),
                "selected_policy_id": str(rerun_tight["selected_policy_id"]),
            },
            "selected_policy_delta": {
                "security_return": float(rerun_tight["security_return"]) - float(baseline_tight["security_return"]),
                "business_return": float(rerun_tight["business_return"]) - float(baseline_tight["business_return"]),
                "cost_return": float(rerun_tight["cost_return"]) - float(baseline_tight["cost_return"]),
                "feasible_rate": float(rerun_tight["feasible_rate"]) - float(baseline_tight["feasible_rate"]),
                "mean_violation": float(rerun_tight["mean_violation"]) - float(baseline_tight["mean_violation"]),
            },
        }

    compare_summary = {
        "baseline_method_name": BASELINE_METHOD_NAME,
        "rerun_method_name": METHOD_NAME,
        "completed_seeds": completed_seeds,
        "selected_policy_compare": {
            "baseline": {key: baseline_selected.get(key) for key in selected_keys},
            "rerun": {key: rerun_selected.get(key) for key in selected_keys},
            "delta": _diff_dict(rerun_selected, baseline_selected, selected_keys),
        },
        "reevaluated_set_compare": {
            "baseline": {key: baseline_reevaluated.get(key) for key in reevaluated_keys},
            "rerun": {key: rerun_reevaluated.get(key) for key in reevaluated_keys},
            "delta": _diff_dict(rerun_reevaluated, baseline_reevaluated, reevaluated_keys),
        },
        "per_seed": per_seed,
    }
    save_json(_runner_root() / DIFF_JSON_NAME, compare_summary)
    return compare_summary


def run_no_constraint_stage2_fair_rerun(
    *,
    seeds: tuple[int, ...],
    selected_eval_episodes: int,
    reevaluated_eval_episodes: int,
) -> dict[str, Any]:
    base.RUNNER_DIRNAME = RUNNER_DIRNAME
    seed_order = tuple(dict.fromkeys(int(seed) for seed in seeds))
    total_steps = len(seed_order) * 4 + 4
    progress = base.ProgressTracker(total_steps=total_steps)

    manifest: dict[str, Any] = {
        "method_name": METHOD_NAME,
        "display_name": DISPLAY_NAME,
        "baseline_method_name": BASELINE_METHOD_NAME,
        "seeds": list(seed_order),
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
            train_buffer = _run_training_for_seed(seed=seed, progress=progress)
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
            baseline_seed_summary = load_json(_baseline_seed_summary_path(seed))
            manifest["per_seed"][f"seed_{seed:04d}"] = {
                "train_buffer": str(train_buffer),
                "eval_input_buffer": str(eval_input),
                "tight_metrics": str(metrics_path),
                "reevaluated_seed_summary": str(_seed_summary_path(seed).resolve()),
                "baseline_closest_candidate_margin": float(
                    baseline_seed_summary["closest_candidate_margin"]
                ),
                "rerun_closest_candidate_margin": float(seed_summary["closest_candidate_margin"]),
                "margin_delta_vs_baseline": float(seed_summary["closest_candidate_margin"])
                - float(baseline_seed_summary["closest_candidate_margin"]),
                "baseline_reevaluated_feasible_candidate_count": int(
                    baseline_seed_summary["reevaluated_feasible_candidate_count"]
                ),
                "rerun_reevaluated_feasible_candidate_count": int(
                    seed_summary["reevaluated_feasible_candidate_count"]
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
        compare_summary = _write_compare_summary(
            completed_seeds=successful_seeds,
            rerun_selected_aggregate_path=selected_aggregate_path,
            rerun_reevaluated_json_path=reevaluated_outputs["json"],
        )

        final_summary = {
            "method_name": METHOD_NAME,
            "display_name": DISPLAY_NAME,
            "baseline_method_name": BASELINE_METHOD_NAME,
            "completed_seeds": successful_seeds,
            "selected_policy_aggregate_path": str(selected_aggregate_path),
            "selected_policy_compare_plot": str(selected_compare_plot),
            "reevaluated_compare_csv": str(reevaluated_outputs["csv"]),
            "reevaluated_compare_json": str(reevaluated_outputs["json"]),
            "reevaluated_compare_figure": str(reevaluated_outputs["figure"]),
            "diff_json_path": str((_runner_root() / DIFF_JSON_NAME).resolve()),
            "runner_log": str(progress.log_path.resolve()),
            "runner_status": str(progress.status_path.resolve()),
            "run_manifest_path": str((_runner_root() / "run_manifest.json").resolve()),
            "selected_policy_delta": compare_summary["selected_policy_compare"]["delta"],
            "reevaluated_set_delta": compare_summary["reevaluated_set_compare"]["delta"],
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
            "Rerun no_constraint_stage2_fair on the same matched fair-compare seeds and "
            "compare the new run against the existing baseline."
        )
    )
    parser.add_argument("--seeds", nargs="+", type=int, default=list(DEFAULT_SEEDS))
    parser.add_argument("--selected-eval-episodes", type=int, default=DEFAULT_SELECTED_EVAL_EPISODES)
    parser.add_argument("--reevaluated-eval-episodes", type=int, default=DEFAULT_REEVALUATED_EVAL_EPISODES)
    args = parser.parse_args()

    outputs = run_no_constraint_stage2_fair_rerun(
        seeds=tuple(int(seed) for seed in args.seeds),
        selected_eval_episodes=int(args.selected_eval_episodes),
        reevaluated_eval_episodes=int(args.reevaluated_eval_episodes),
    )
    for key, value in outputs.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
