from __future__ import annotations

import argparse
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from cmorl_minicage.utils import load_json, save_json

from . import export_tight_feasible_set_reevaluated as reevaluate_mod
from . import strong_tightplus_ours_fair_compare_runner as base

DEFAULT_SEEDS = (7, 11, 19)
DEFAULT_SELECTED_EVAL_EPISODES = 40
DEFAULT_REEVALUATED_EVAL_EPISODES = 3
DEFAULT_TRAIN_POLL_SECONDS = 15

VARIANT_SPECS: dict[str, dict[str, str]] = {
    "adaptive_fixed": {
        "method_name": "adaptive_fixed_stage2_fair",
        "display_name": "AdaCS Only",
        "runner_dirname": "fair_compare_adaptive_fixed_runner",
        "config_glob": "cmorl_cyborg/configs/paper/fair_compare_ablation/stage2_adaptive_fixed_fair_seed_{seed:04d}.yaml",
        "train_root": "cmorl_cyborg/outputs/fair_compare/adaptive_fixed_stage2_fair/seed_{seed:04d}",
        "color": "#54a24b",
    },
    "crowding_dynamic": {
        "method_name": "crowding_dynamic_stage2_fair",
        "display_name": "DCS Only",
        "runner_dirname": "fair_compare_crowding_dynamic_runner",
        "config_glob": "cmorl_cyborg/configs/paper/fair_compare_ablation/stage2_crowding_dynamic_fair_seed_{seed:04d}.yaml",
        "train_root": "cmorl_cyborg/outputs/fair_compare/crowding_dynamic_stage2_fair/seed_{seed:04d}",
        "color": "#f58518",
    },
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _resolve_repo_path(raw_path: str | Path) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return (_repo_root() / path).resolve()


def _spec(variant: str) -> dict[str, str]:
    try:
        return VARIANT_SPECS[variant]
    except KeyError as exc:
        raise ValueError(f"Unknown variant: {variant}") from exc


def _method_name(variant: str) -> str:
    return _spec(variant)["method_name"]


def _display_name(variant: str) -> str:
    return _spec(variant)["display_name"]


def _runner_root(variant: str) -> Path:
    return base.ensure_dir(
        _resolve_repo_path(f"cmorl_cyborg/outputs/{_spec(variant)['runner_dirname']}")
    )


def _generated_config_root(variant: str) -> Path:
    return base.ensure_dir(_runner_root(variant) / "generated_configs")


def _stage2_config_path(variant: str, seed: int) -> Path:
    return _resolve_repo_path(_spec(variant)["config_glob"].format(seed=seed))


def _train_seed_root(variant: str, seed: int) -> Path:
    return _resolve_repo_path(_spec(variant)["train_root"].format(seed=seed))


def _eval_input_buffer_path(method_name: str, seed: int) -> Path:
    return _resolve_repo_path(
        f"cmorl_cyborg/outputs/fair_compare_eval_inputs/{method_name}/seed_{seed:04d}/solution_buffer.json"
    )


def _set_metrics_path(method_name: str, seed: int) -> Path:
    return _resolve_repo_path(
        f"cmorl_cyborg/outputs/fair_compare_eval/set_value/{method_name}/seed_{seed:04d}/metrics.json"
    )


def _tight_metrics_path(method_name: str, seed: int) -> Path:
    return _resolve_repo_path(
        f"cmorl_cyborg/outputs/fair_compare_eval/tight/{method_name}/seed_{seed:04d}/constraint_metrics.json"
    )


def _seed_summary_path(method_name: str, seed: int) -> Path:
    return _resolve_repo_path(
        f"cmorl_cyborg/outputs/fair_compare_eval/reevaluated_tight_feasible_set_summary/{method_name}/seed_{seed:04d}.json"
    )


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
    variant: str,
    seed: int,
    config_path: Path,
    seed_root: Path,
    poll_seconds: int,
    progress: base.ProgressTracker,
) -> Path | None:
    label = f"watch {_method_name(variant)} seed_{seed:04d}"
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
                f"WAIT ended without solution_buffer | variant={variant} | seed={seed:04d} | latest_run={seed_root}"
            )
            progress.finish_step(label, step_start)
            return None

        if pids != last_pids:
            progress._append_log(
                f"WAIT external training | variant={variant} | seed={seed:04d} | pids={pids}"
            )
            last_pids = pids

        progress.heartbeat(label, step_start)
        time.sleep(max(int(poll_seconds), 1))


def _materialize_set_eval_config(*, variant: str, seed: int, buffer_path: Path) -> Path:
    payload = {
        "buffer_path": str(buffer_path.resolve()),
        "output_path": str(_set_metrics_path(_method_name(variant), seed).resolve()),
        "preference_step": 0.1,
        "reference_strategy": "data_min_range",
        "reference_margin": 0.25,
        "reference_point": [],
        "hv_max_exact_points": 18,
        "hv_mc_samples": 100000,
    }
    config_path = _generated_config_root(variant) / f"evaluate_set_seed_{seed:04d}.yaml"
    return base._write_yaml(config_path, payload)


def _materialize_tight_eval_config(
    *,
    variant: str,
    seed: int,
    buffer_path: Path,
    eval_episodes: int,
) -> Path:
    payload = {
        "method_name": _method_name(variant),
        "input_kind": "buffer",
        "input_path": str(buffer_path.resolve()),
        "selection_source": "pareto",
        "selection_policy": "objective",
        "thresholds_path": str(base._thresholds_tight_path().resolve()),
        "output_path": str(_tight_metrics_path(_method_name(variant), seed).resolve()),
        "eval_episodes": int(eval_episodes),
    }
    config_path = _generated_config_root(variant) / f"evaluate_tight_seed_{seed:04d}.yaml"
    return base._write_yaml(config_path, payload)


def _run_training_for_seed(
    *,
    variant: str,
    seed: int,
    poll_seconds: int,
    progress: base.ProgressTracker,
) -> Path:
    seed_root = _train_seed_root(variant, seed)
    existing = base._latest_run_artifact(seed_root, "solution_buffer.json")
    label = f"train {_method_name(variant)} seed_{seed:04d}"
    if existing is not None:
        step_start = progress.start_step(label)
        progress.finish_step(label, step_start, skipped=True)
        return existing.resolve()

    config_path = _stage2_config_path(variant, seed)
    if not config_path.exists():
        raise FileNotFoundError(f"Missing Stage-2 config: {config_path}")

    external_result = None
    if _running_train_pids_for_config(config_path):
        external_result = _wait_for_external_training(
            variant=variant,
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


def _copy_eval_input_for_seed(
    *,
    variant: str,
    seed: int,
    train_buffer_path: Path,
    progress: base.ProgressTracker,
) -> Path:
    target_path = _eval_input_buffer_path(_method_name(variant), seed)
    label = f"copy eval_input {_method_name(variant)} seed_{seed:04d}"
    step_start = progress.start_step(label)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(train_buffer_path, target_path)
    progress.finish_step(label, step_start)
    return target_path.resolve()


def _run_set_eval_for_seed(
    *,
    variant: str,
    seed: int,
    input_buffer_path: Path,
    progress: base.ProgressTracker,
) -> Path:
    output_path = _set_metrics_path(_method_name(variant), seed)
    label = f"set eval {_method_name(variant)} seed_{seed:04d}"
    if output_path.exists():
        step_start = progress.start_step(label)
        progress.finish_step(label, step_start, skipped=True)
        return output_path.resolve()

    config_path = _materialize_set_eval_config(
        variant=variant,
        seed=seed,
        buffer_path=input_buffer_path,
    )
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
    variant: str,
    seed: int,
    input_buffer_path: Path,
    selected_eval_episodes: int,
    progress: base.ProgressTracker,
) -> Path:
    output_path = _tight_metrics_path(_method_name(variant), seed)
    label = f"tight eval {_method_name(variant)} seed_{seed:04d}"
    if output_path.exists():
        step_start = progress.start_step(label)
        progress.finish_step(label, step_start, skipped=True)
        return output_path.resolve()

    config_path = _materialize_tight_eval_config(
        variant=variant,
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
    variant: str,
    seed: int,
    constraint_metrics_path: Path,
    reevaluated_eval_episodes: int,
    progress: base.ProgressTracker,
) -> dict[str, Any]:
    method_name = _method_name(variant)
    reevaluate_mod.DISPLAY_NAMES[method_name] = _display_name(variant)
    reevaluate_mod.COLORS[method_name] = _spec(variant)["color"]
    output_path = _seed_summary_path(method_name, seed)
    label = f"reevaluate {method_name} seed_{seed:04d}"
    if output_path.exists():
        step_start = progress.start_step(label)
        progress.finish_step(label, step_start, skipped=True)
        return load_json(output_path)

    step_start = progress.start_step(label)
    summary = reevaluate_mod._seed_summary(
        method_name=method_name,
        constraint_metrics_path=constraint_metrics_path,
        eval_episodes=int(reevaluated_eval_episodes),
        logger=base._CandidateLogger(progress),
    )
    save_json(output_path, summary)
    progress.finish_step(label, step_start)
    return summary


def _aggregate_selected_policy(
    *,
    variant: str,
    metrics_paths: list[Path],
    progress: base.ProgressTracker,
) -> Path:
    label = f"aggregate {_method_name(variant)} selected-policy tight metrics"
    step_start = progress.start_step(label)
    aggregate_path = base._aggregated_root() / f"{_method_name(variant)}_tight.json"
    base.write_aggregated_constraint_metrics(
        [str(path.resolve()) for path in metrics_paths],
        aggregate_path,
        method_name=_method_name(variant),
    )
    progress.finish_step(label, step_start)
    return aggregate_path.resolve()


def run_variant(
    *,
    variant: str,
    seeds: tuple[int, ...],
    selected_eval_episodes: int,
    reevaluated_eval_episodes: int,
    train_poll_seconds: int,
) -> dict[str, Any]:
    spec = _spec(variant)
    base.RUNNER_DIRNAME = spec["runner_dirname"]
    seed_order = tuple(dict.fromkeys(int(seed) for seed in seeds))
    total_steps = len(seed_order) * 5 + 1
    progress = base.ProgressTracker(total_steps=total_steps)
    method_name = spec["method_name"]

    manifest: dict[str, Any] = {
        "variant": variant,
        "method_name": method_name,
        "display_name": spec["display_name"],
        "seeds": list(seed_order),
        "selected_eval_episodes": int(selected_eval_episodes),
        "reevaluated_eval_episodes": int(reevaluated_eval_episodes),
        "train_poll_seconds": int(train_poll_seconds),
        "runner_log": str(progress.log_path.resolve()),
        "runner_status": str(progress.status_path.resolve()),
        "started_at": progress.pipeline_started_at,
        "per_seed": {},
    }
    save_json(_runner_root(variant) / "run_manifest.json", manifest)

    successful_seeds: list[int] = []
    tight_metrics_paths: list[Path] = []
    seed_rows: list[dict[str, Any]] = []

    try:
        for seed in seed_order:
            train_buffer = _run_training_for_seed(
                variant=variant,
                seed=seed,
                poll_seconds=train_poll_seconds,
                progress=progress,
            )
            eval_input = _copy_eval_input_for_seed(
                variant=variant,
                seed=seed,
                train_buffer_path=train_buffer,
                progress=progress,
            )
            set_metrics_path = _run_set_eval_for_seed(
                variant=variant,
                seed=seed,
                input_buffer_path=eval_input,
                progress=progress,
            )
            tight_metrics_path = _run_tight_eval_for_seed(
                variant=variant,
                seed=seed,
                input_buffer_path=eval_input,
                selected_eval_episodes=selected_eval_episodes,
                progress=progress,
            )
            seed_summary = _reevaluate_seed(
                variant=variant,
                seed=seed,
                constraint_metrics_path=tight_metrics_path,
                reevaluated_eval_episodes=reevaluated_eval_episodes,
                progress=progress,
            )

            successful_seeds.append(seed)
            tight_metrics_paths.append(tight_metrics_path)
            seed_rows.append(seed_summary)
            manifest["per_seed"][f"seed_{seed:04d}"] = {
                "train_buffer": str(train_buffer),
                "eval_input_buffer": str(eval_input),
                "set_metrics": str(set_metrics_path),
                "tight_metrics": str(tight_metrics_path),
                "reevaluated_seed_summary": str(_seed_summary_path(method_name, seed).resolve()),
            }
            save_json(_runner_root(variant) / "run_manifest.json", manifest)

        selected_aggregate_path = _aggregate_selected_policy(
            variant=variant,
            metrics_paths=tight_metrics_paths,
            progress=progress,
        )
        reevaluated_aggregate = reevaluate_mod._aggregate_method_rows(method_name, seed_rows)
        reevaluated_path = _runner_root(variant) / "reevaluated_aggregate.json"
        save_json(reevaluated_path, reevaluated_aggregate)

        final_summary = {
            "variant": variant,
            "method_name": method_name,
            "display_name": spec["display_name"],
            "completed_seeds": successful_seeds,
            "selected_policy_aggregate_path": str(selected_aggregate_path),
            "reevaluated_aggregate_path": str(reevaluated_path.resolve()),
            "runner_log": str(progress.log_path.resolve()),
            "runner_status": str(progress.status_path.resolve()),
            "run_manifest_path": str((_runner_root(variant) / "run_manifest.json").resolve()),
        }
        save_json(_runner_root(variant) / "final_summary.json", final_summary)
        progress.finalize(success=True, extra=final_summary)
        return final_summary
    except BaseException as exc:
        progress.fail_step(progress.current_label, exc)
        progress.log_exception_traceback(exc)
        progress.finalize(
            success=False,
            extra={
                "variant": variant,
                "completed_seeds": successful_seeds,
                "run_manifest_path": str((_runner_root(variant) / "run_manifest.json").resolve()),
            },
        )
        raise


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run one matched Stage-2 ablation variant and materialize its evaluation artifacts."
    )
    parser.add_argument(
        "--variant",
        required=True,
        choices=sorted(VARIANT_SPECS.keys()),
    )
    parser.add_argument("--seeds", nargs="+", type=int, default=list(DEFAULT_SEEDS))
    parser.add_argument("--selected-eval-episodes", type=int, default=DEFAULT_SELECTED_EVAL_EPISODES)
    parser.add_argument("--reevaluated-eval-episodes", type=int, default=DEFAULT_REEVALUATED_EVAL_EPISODES)
    parser.add_argument("--train-poll-seconds", type=int, default=DEFAULT_TRAIN_POLL_SECONDS)
    args = parser.parse_args()

    outputs = run_variant(
        variant=str(args.variant),
        seeds=tuple(int(seed) for seed in args.seeds),
        selected_eval_episodes=int(args.selected_eval_episodes),
        reevaluated_eval_episodes=int(args.reevaluated_eval_episodes),
        train_poll_seconds=int(args.train_poll_seconds),
    )
    for key, value in outputs.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
