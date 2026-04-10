from __future__ import annotations

import argparse
import subprocess
import time
from pathlib import Path
from typing import Any

from cmorl_minicage.utils import load_json, save_json

from . import export_tight_feasible_set_reevaluated as reevaluate_mod
from . import strong_tightplus_ours_fair_compare_runner as base
from .compare_suite import compare_suite
from .evaluate_constraints import write_aggregated_constraint_metrics
from .paper_plots import plot_fair_compare_table_b, plot_main_table_a


DEFAULT_SEEDS = (7, 11)
DEFAULT_SELECTED_EVAL_EPISODES = 40
DEFAULT_REEVALUATED_EVAL_EPISODES = 3
DEFAULT_TRAIN_POLL_SECONDS = 15

BASELINE_METHOD_NAME = "ours_stage2_fair"
METHOD_NAME = "original_stage2_fair"
DISPLAY_NAME = "Original Stage2"
RUNNER_DIRNAME = "fair_compare_original_stage2_runner"
SET_COMPARE_DIRNAME = "set_value_compare_original_vs_ours"
SELECTED_COMPARE_PLOT_NAME = "fair_compare_table_b_tight_with_original_stage2.png"
SET_COMPARE_PLOT_NAME = "set_value_compare_original_vs_ours.png"
REEVALUATED_SUMMARY_CSV_NAME = "reevaluated_tight_feasible_set_summary_with_original_stage2.csv"
REEVALUATED_SUMMARY_JSON_NAME = "reevaluated_tight_feasible_set_summary_with_original_stage2.json"
REEVALUATED_SUMMARY_FIGURE_NAME = "reevaluated_tight_feasible_set_quality_with_original_stage2.png"
DIFF_JSON_NAME = "original_stage2_fair_diff.json"


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


def _set_compare_root() -> Path:
    return base.ensure_dir(_resolve_repo_path(f"cmorl_cyborg/outputs/fair_compare_eval/{SET_COMPARE_DIRNAME}"))


def _stage2_config_path(seed: int) -> Path:
    return _resolve_repo_path(
        f"cmorl_cyborg/configs/paper/fair_compare_original/stage2_original_stage2_fair_seed_{seed:04d}.yaml"
    )


def _train_seed_root(seed: int) -> Path:
    return _resolve_repo_path(
        f"cmorl_cyborg/outputs/fair_compare/{METHOD_NAME}/seed_{seed:04d}"
    )


def _eval_input_buffer_path(seed: int) -> Path:
    return _resolve_repo_path(
        f"cmorl_cyborg/outputs/fair_compare_eval_inputs/{METHOD_NAME}/seed_{seed:04d}/solution_buffer.json"
    )


def _baseline_eval_input_buffer_path(seed: int) -> Path:
    return _resolve_repo_path(
        f"cmorl_cyborg/outputs/fair_compare_eval_inputs/{BASELINE_METHOD_NAME}/seed_{seed:04d}/solution_buffer.json"
    )


def _baseline_set_compare_buffer_path(seed: int) -> Path:
    config_path = _resolve_repo_path("cmorl_cyborg/configs/paper/compare_suite_main.yaml")
    payload = base._load_yaml(config_path)
    for entry in payload.get("entries", []):
        if str(entry.get("method_name")) != "ours_stage2":
            continue
        if int(entry.get("seed", -1)) != int(seed):
            continue
        raw_path = entry.get("artifact_path")
        if not raw_path:
            raise ValueError(f"Missing artifact_path for ours_stage2 seed {seed} in {config_path}")
        return _resolve_repo_path(raw_path)
    raise ValueError(f"Could not find ours_stage2 seed {seed} in {config_path}")


def _set_metrics_path(seed: int) -> Path:
    return _resolve_repo_path(
        f"cmorl_cyborg/outputs/fair_compare_eval/set_value/{METHOD_NAME}/seed_{seed:04d}/metrics.json"
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
    return _aggregated_root() / "ours_stage2_fair_tight.json"


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


def _write_yaml(path: str | Path, payload: dict[str, Any]) -> Path:
    return base._write_yaml(path, payload)


def _latest_run_dir(seed_root: Path) -> Path | None:
    run_dirs = sorted(
        seed_root.glob("run_*"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not run_dirs:
        return None
    return run_dirs[0].resolve()


def _running_train_pids_for_config(config_path: Path) -> list[int]:
    result = subprocess.run(
        ["ps", "-eo", "pid,args"],
        check=True,
        capture_output=True,
        text=True,
    )
    needle = str(config_path.resolve())
    pids: list[int] = []
    for line in result.stdout.splitlines()[1:]:
        stripped = line.strip()
        if not stripped:
            continue
        pid_str, _, args = stripped.partition(" ")
        if "cmorl_cyborg.train_stage2" not in args:
            continue
        if needle not in args:
            continue
        try:
            pids.append(int(pid_str))
        except ValueError:
            continue
    return pids


def _wait_for_external_training(
    *,
    seed: int,
    config_path: Path,
    seed_root: Path,
    poll_seconds: int,
    progress: base.ProgressTracker,
) -> Path | None:
    label = f"watch original_stage2 seed_{seed:04d}"
    step_start = progress.start_step(label)
    last_pids: list[int] = []
    while True:
        existing = base._latest_run_artifact(seed_root, "solution_buffer.json")
        if existing is not None:
            progress.finish_step(label, step_start)
            return existing.resolve()

        pids = _running_train_pids_for_config(config_path)
        if not pids:
            progress._append_log(
                f"WAIT ended without solution_buffer | seed={seed:04d} | latest_run={_latest_run_dir(seed_root)}"
            )
            progress.finish_step(label, step_start)
            return None

        if pids != last_pids:
            progress._append_log(
                f"WAIT external training | seed={seed:04d} | pids={pids} | latest_run={_latest_run_dir(seed_root)}"
            )
            last_pids = pids

        progress.heartbeat(label, step_start)
        time.sleep(max(int(poll_seconds), 1))


def _materialize_set_eval_config(*, seed: int, buffer_path: Path) -> Path:
    payload = {
        "buffer_path": str(buffer_path.resolve()),
        "output_path": str(_set_metrics_path(seed).resolve()),
        "preference_step": 0.1,
        "reference_strategy": "data_min_range",
        "reference_margin": 0.25,
        "reference_point": [],
        "hv_max_exact_points": 18,
        "hv_mc_samples": 100000,
    }
    config_path = _generated_config_root() / f"evaluate_set_seed_{seed:04d}.yaml"
    return _write_yaml(config_path, payload)


def _materialize_tight_eval_config(*, seed: int, buffer_path: Path, eval_episodes: int) -> Path:
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


def _materialize_set_compare_config(seeds: list[int]) -> Path:
    entries: list[dict[str, Any]] = []
    for seed in seeds:
        entries.append(
            {
                "method_name": BASELINE_METHOD_NAME,
                "artifact_kind": "buffer",
                "artifact_path": str(_baseline_set_compare_buffer_path(seed).resolve()),
                "display_group": "AdaCS-DCS (Ours)",
                "seed": int(seed),
            }
        )
        entries.append(
            {
                "method_name": METHOD_NAME,
                "artifact_kind": "buffer",
                "artifact_path": str(_eval_input_buffer_path(seed).resolve()),
                "display_group": "Original Stage2",
                "seed": int(seed),
            }
        )
    payload = {
        "output_dir": str(_set_compare_root().resolve()),
        "entries": entries,
        "preference_step": 0.1,
        "reference_strategy": "data_min_range",
        "reference_margin": 0.25,
        "reference_point": [],
        "hv_max_exact_points": 18,
        "hv_mc_samples": 100000,
    }
    config_path = _generated_config_root() / "compare_suite_original_vs_ours.yaml"
    return _write_yaml(config_path, payload)


def _run_training_for_seed(
    *,
    seed: int,
    poll_seconds: int,
    progress: base.ProgressTracker,
) -> Path:
    seed_root = _train_seed_root(seed)
    existing = base._latest_run_artifact(seed_root, "solution_buffer.json")
    label = f"train original_stage2 seed_{seed:04d}"
    if existing is not None:
        step_start = progress.start_step(label)
        progress.finish_step(label, step_start, skipped=True)
        return existing.resolve()

    config_path = _stage2_config_path(seed)
    if not config_path.exists():
        raise FileNotFoundError(f"Missing Stage-2 config: {config_path}")

    external_result = None
    if _running_train_pids_for_config(config_path):
        external_result = _wait_for_external_training(
            seed=seed,
            config_path=config_path,
            seed_root=seed_root,
            poll_seconds=poll_seconds,
            progress=progress,
        )
    if external_result is not None:
        return external_result

    step_start = progress.start_step(label)
    base._run_module(
        "cmorl_cyborg.train_stage2",
        ["--config", str(config_path)],
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
    label = f"copy eval_input original_stage2 seed_{seed:04d}"
    step_start = progress.start_step(label)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_bytes(train_buffer_path.read_bytes())
    progress.finish_step(label, step_start)
    return target_path.resolve()


def _run_set_eval_for_seed(*, seed: int, input_buffer_path: Path, progress: base.ProgressTracker) -> Path:
    output_path = _set_metrics_path(seed)
    label = f"set eval original_stage2 seed_{seed:04d}"
    if output_path.exists():
        step_start = progress.start_step(label)
        progress.finish_step(label, step_start, skipped=True)
        return output_path.resolve()

    config_path = _materialize_set_eval_config(seed=seed, buffer_path=input_buffer_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    step_start = progress.start_step(label)
    base._run_module(
        "cmorl_cyborg.evaluate",
        ["--config", str(config_path)],
        progress=progress,
        label=label,
    )
    progress.finish_step(label, step_start)
    return output_path.resolve()


def _run_tight_eval_for_seed(
    *,
    seed: int,
    input_buffer_path: Path,
    selected_eval_episodes: int,
    progress: base.ProgressTracker,
) -> Path:
    output_path = _tight_metrics_path(seed)
    label = f"tight eval original_stage2 seed_{seed:04d}"
    if output_path.exists():
        step_start = progress.start_step(label)
        progress.finish_step(label, step_start, skipped=True)
        return output_path.resolve()

    config_path = _materialize_tight_eval_config(
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
    output_path = _seed_summary_path(seed)
    label = f"reevaluate original_stage2 seed_{seed:04d}"
    if output_path.exists():
        step_start = progress.start_step(label)
        progress.finish_step(label, step_start, skipped=True)
        return load_json(output_path)

    step_start = progress.start_step(label)
    summary = reevaluate_mod._seed_summary(
        method_name=METHOD_NAME,
        constraint_metrics_path=constraint_metrics_path,
        eval_episodes=int(reevaluated_eval_episodes),
        logger=base._CandidateLogger(progress),
    )
    save_json(output_path, summary)
    progress.finish_step(label, step_start)
    return summary


def _aggregate_selected_policy(*, metrics_paths: list[Path], progress: base.ProgressTracker) -> Path:
    label = "aggregate original_stage2 selected-policy tight metrics"
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
    label = "plot original_stage2 selected-policy compare"
    step_start = progress.start_step(label)
    output_path = _aggregated_root() / SELECTED_COMPARE_PLOT_NAME
    plot_fair_compare_table_b(
        aggregated_paths=[
            str(_baseline_selected_aggregate_path().resolve()),
            str(new_aggregate_path.resolve()),
        ],
        output_path=output_path,
        title="Deployment Comparison under Tight Constraints: AdaCS-DCS vs Original Stage2",
        label_map={
            BASELINE_METHOD_NAME: "AdaCS-DCS (Ours)",
            METHOD_NAME: "Original Stage2",
        },
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
    label = "aggregate original_stage2 reevaluated set metrics"
    step_start = progress.start_step(label)
    new_row = reevaluate_mod._aggregate_method_rows(METHOD_NAME, seed_rows)

    baseline_payload = load_json(_baseline_reevaluated_aggregate_path())
    baseline_rows = list(baseline_payload.get("methods", []))
    baseline_row = next(
        row for row in baseline_rows if str(row.get("method_name")) == BASELINE_METHOD_NAME
    )
    combined_rows = [baseline_row, new_row]

    csv_path = _aggregated_root() / REEVALUATED_SUMMARY_CSV_NAME
    json_path = _aggregated_root() / REEVALUATED_SUMMARY_JSON_NAME
    figure_path = _aggregated_root() / REEVALUATED_SUMMARY_FIGURE_NAME

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


def _refresh_set_compare(*, completed_seeds: list[int], progress: base.ProgressTracker) -> dict[str, Path]:
    label = "refresh original_stage2 set-value compare"
    step_start = progress.start_step(label)
    config_path = _materialize_set_compare_config(completed_seeds)
    summary_path = compare_suite(config_path)
    figure_path = _set_compare_root() / SET_COMPARE_PLOT_NAME
    plot_main_table_a(
        summary_path,
        output_path=figure_path,
        title="Set Value Comparison: AdaCS-DCS vs Original Stage2",
    )
    progress.finish_step(label, step_start)
    return {
        "config": config_path.resolve(),
        "summary": Path(summary_path).resolve(),
        "figure": figure_path.resolve(),
    }


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


def _diff_nested_metric_dict(
    current: dict[str, Any],
    baseline: dict[str, Any],
    keys: list[str],
) -> dict[str, float | None]:
    out: dict[str, float | None] = {}
    for key in keys:
        current_metric = current.get(key, {})
        baseline_metric = baseline.get(key, {})
        current_mean = current_metric.get("mean")
        baseline_mean = baseline_metric.get("mean")
        if current_mean is None or baseline_mean is None:
            out[key] = None
        else:
            out[key] = float(current_mean) - float(baseline_mean)
    return out


def _write_compare_summary(
    *,
    completed_seeds: list[int],
    set_compare_summary_path: Path,
    selected_aggregate_path: Path,
    reevaluated_compare_json_path: Path,
) -> dict[str, Any]:
    set_compare_payload = load_json(set_compare_summary_path)
    method_rows = {
        str(row.get("method_name")): row for row in set_compare_payload.get("method_summary", [])
    }
    baseline_set = method_rows[BASELINE_METHOD_NAME]
    current_set = method_rows[METHOD_NAME]

    baseline_selected = load_json(_baseline_selected_aggregate_path())
    current_selected = load_json(selected_aggregate_path)
    baseline_reevaluated_payload = load_json(_baseline_reevaluated_aggregate_path())
    baseline_reevaluated = next(
        row
        for row in baseline_reevaluated_payload.get("methods", [])
        if str(row.get("method_name")) == BASELINE_METHOD_NAME
    )
    current_reevaluated_payload = load_json(reevaluated_compare_json_path)
    current_reevaluated = next(
        row
        for row in current_reevaluated_payload.get("methods", [])
        if str(row.get("method_name")) == METHOD_NAME
    )

    set_keys = [
        "hypervolume",
        "expected_utility",
        "sparsity",
        "num_pareto_records",
        "coverage_ratio",
        "unique_assigned_policies",
    ]
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
        per_seed[f"seed_{seed:04d}"] = {
            "set_metrics_path": str(_set_metrics_path(seed).resolve()),
            "tight_metrics_path": str(_tight_metrics_path(seed).resolve()),
            "reevaluated_seed_summary_path": str(_seed_summary_path(seed).resolve()),
            "baseline_tight_metrics_path": str(_baseline_constraint_metrics_path(seed).resolve()),
            "baseline_reevaluated_seed_summary_path": str(_baseline_seed_summary_path(seed).resolve()),
        }

    compare_summary = {
        "baseline_method_name": BASELINE_METHOD_NAME,
        "current_method_name": METHOD_NAME,
        "completed_seeds": completed_seeds,
        "set_value_compare": {
            "reference_point": set_compare_payload.get("reference_point"),
            "baseline": {key: baseline_set.get(key) for key in set_keys},
            "current": {key: current_set.get(key) for key in set_keys},
            "delta_mean": _diff_nested_metric_dict(current_set, baseline_set, set_keys),
        },
        "selected_policy_compare": {
            "baseline": {key: baseline_selected.get(key) for key in selected_keys},
            "current": {key: current_selected.get(key) for key in selected_keys},
            "delta": _diff_dict(current_selected, baseline_selected, selected_keys),
        },
        "reevaluated_set_compare": {
            "baseline": {key: baseline_reevaluated.get(key) for key in reevaluated_keys},
            "current": {key: current_reevaluated.get(key) for key in reevaluated_keys},
            "delta": _diff_dict(current_reevaluated, baseline_reevaluated, reevaluated_keys),
        },
        "per_seed": per_seed,
    }
    save_json(_runner_root() / DIFF_JSON_NAME, compare_summary)
    return compare_summary


def run_original_stage2_fair(
    *,
    seeds: tuple[int, ...],
    selected_eval_episodes: int,
    reevaluated_eval_episodes: int,
    train_poll_seconds: int,
) -> dict[str, Any]:
    base.RUNNER_DIRNAME = RUNNER_DIRNAME
    seed_order = tuple(dict.fromkeys(int(seed) for seed in seeds))
    total_steps = len(seed_order) * 9 + 1
    progress = base.ProgressTracker(total_steps=total_steps)

    manifest: dict[str, Any] = {
        "method_name": METHOD_NAME,
        "display_name": DISPLAY_NAME,
        "baseline_method_name": BASELINE_METHOD_NAME,
        "seeds": list(seed_order),
        "selected_eval_episodes": int(selected_eval_episodes),
        "reevaluated_eval_episodes": int(reevaluated_eval_episodes),
        "train_poll_seconds": int(train_poll_seconds),
        "runner_log": str(progress.log_path.resolve()),
        "runner_status": str(progress.status_path.resolve()),
        "started_at": progress.pipeline_started_at,
        "per_seed": {},
    }
    save_json(_runner_root() / "run_manifest.json", manifest)

    successful_seeds: list[int] = []
    tight_metrics_paths: list[Path] = []
    seed_rows: list[dict[str, Any]] = []
    latest_set_compare_outputs: dict[str, Path] | None = None
    latest_selected_aggregate_path: Path | None = None
    latest_selected_compare_plot: Path | None = None
    latest_reevaluated_outputs: dict[str, Path] | None = None

    try:
        for seed in seed_order:
            train_buffer = _run_training_for_seed(
                seed=seed,
                poll_seconds=train_poll_seconds,
                progress=progress,
            )
            eval_input = _copy_eval_input_for_seed(
                seed=seed,
                train_buffer_path=train_buffer,
                progress=progress,
            )
            set_metrics_path = _run_set_eval_for_seed(
                seed=seed,
                input_buffer_path=eval_input,
                progress=progress,
            )
            tight_metrics_path = _run_tight_eval_for_seed(
                seed=seed,
                input_buffer_path=eval_input,
                selected_eval_episodes=selected_eval_episodes,
                progress=progress,
            )
            seed_summary = _reevaluate_seed(
                seed=seed,
                constraint_metrics_path=tight_metrics_path,
                reevaluated_eval_episodes=reevaluated_eval_episodes,
                progress=progress,
            )

            successful_seeds.append(seed)
            tight_metrics_paths.append(tight_metrics_path)
            seed_rows.append(seed_summary)

            latest_set_compare_outputs = _refresh_set_compare(
                completed_seeds=successful_seeds,
                progress=progress,
            )
            latest_selected_aggregate_path = _aggregate_selected_policy(
                metrics_paths=tight_metrics_paths,
                progress=progress,
            )
            latest_selected_compare_plot = _plot_selected_policy_compare(
                new_aggregate_path=latest_selected_aggregate_path,
                progress=progress,
            )
            latest_reevaluated_outputs = _aggregate_reevaluated_compare(
                seed_rows=seed_rows,
                reevaluated_eval_episodes=reevaluated_eval_episodes,
                progress=progress,
            )

            manifest["per_seed"][f"seed_{seed:04d}"] = {
                "train_buffer": str(train_buffer),
                "eval_input_buffer": str(eval_input),
                "set_metrics": str(set_metrics_path),
                "tight_metrics": str(tight_metrics_path),
                "reevaluated_seed_summary": str(_seed_summary_path(seed).resolve()),
                "current_set_compare_summary": str(latest_set_compare_outputs["summary"]),
                "current_set_compare_figure": str(latest_set_compare_outputs["figure"]),
                "current_selected_policy_compare_plot": str(latest_selected_compare_plot),
                "current_reevaluated_compare_json": str(latest_reevaluated_outputs["json"]),
                "current_reevaluated_compare_figure": str(latest_reevaluated_outputs["figure"]),
            }
            save_json(_runner_root() / "run_manifest.json", manifest)

        if latest_set_compare_outputs is None or latest_selected_aggregate_path is None or latest_selected_compare_plot is None or latest_reevaluated_outputs is None:
            raise RuntimeError("Runner finished without generating comparison outputs")

        compare_summary = _write_compare_summary(
            completed_seeds=successful_seeds,
            set_compare_summary_path=latest_set_compare_outputs["summary"],
            selected_aggregate_path=latest_selected_aggregate_path,
            reevaluated_compare_json_path=latest_reevaluated_outputs["json"],
        )

        final_summary = {
            "method_name": METHOD_NAME,
            "display_name": DISPLAY_NAME,
            "baseline_method_name": BASELINE_METHOD_NAME,
            "completed_seeds": successful_seeds,
            "set_compare_config_path": str(latest_set_compare_outputs["config"]),
            "set_compare_summary_path": str(latest_set_compare_outputs["summary"]),
            "set_compare_figure": str(latest_set_compare_outputs["figure"]),
            "selected_policy_aggregate_path": str(latest_selected_aggregate_path),
            "selected_policy_compare_plot": str(latest_selected_compare_plot),
            "reevaluated_compare_csv": str(latest_reevaluated_outputs["csv"]),
            "reevaluated_compare_json": str(latest_reevaluated_outputs["json"]),
            "reevaluated_compare_figure": str(latest_reevaluated_outputs["figure"]),
            "diff_json_path": str((_runner_root() / DIFF_JSON_NAME).resolve()),
            "runner_log": str(progress.log_path.resolve()),
            "runner_status": str(progress.status_path.resolve()),
            "run_manifest_path": str((_runner_root() / "run_manifest.json").resolve()),
            "set_value_delta_mean": compare_summary["set_value_compare"]["delta_mean"],
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
            "Watch or run original_stage2_fair seeds, evaluate them, and compare "
            "the results against the existing AdaCS-DCS fair baseline."
        )
    )
    parser.add_argument("--seeds", nargs="+", type=int, default=list(DEFAULT_SEEDS))
    parser.add_argument("--selected-eval-episodes", type=int, default=DEFAULT_SELECTED_EVAL_EPISODES)
    parser.add_argument("--reevaluated-eval-episodes", type=int, default=DEFAULT_REEVALUATED_EVAL_EPISODES)
    parser.add_argument("--train-poll-seconds", type=int, default=DEFAULT_TRAIN_POLL_SECONDS)
    args = parser.parse_args()

    outputs = run_original_stage2_fair(
        seeds=tuple(int(seed) for seed in args.seeds),
        selected_eval_episodes=int(args.selected_eval_episodes),
        reevaluated_eval_episodes=int(args.reevaluated_eval_episodes),
        train_poll_seconds=int(args.train_poll_seconds),
    )
    for key, value in outputs.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
