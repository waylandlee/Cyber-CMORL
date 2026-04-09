from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from cmorl_minicage.buffer import load_policy_buffer
from cmorl_minicage.utils import ensure_dir, load_json, save_json

from . import export_tight_feasible_set_reevaluated as reevaluate_mod
from .evaluate_constraints import write_aggregated_constraint_metrics
from .paper_plots import plot_fair_compare_table_b

DEFAULT_PILOT_SEEDS = (19,)
DEFAULT_FULL_SEEDS = (7, 11, 19)
DEFAULT_CONSTRAINT_TOLERANCE = -1.5
DEFAULT_CONSTRAINED_UPDATES = 5
DEFAULT_BARRIER_COEF = 20.0
DEFAULT_BETA_MIN = 1.001
DEFAULT_BETA_MAX = 1.006
DEFAULT_SELECTED_EVAL_EPISODES = 40
DEFAULT_REEVALUATED_EVAL_EPISODES = 3

BASE_METHOD_NAME = "ours_stage2_fair"
TIGHTER_METHOD_NAME = "ours_stage2_fair_tighter"
TIGHTER_DISPLAY_NAME = "Ours Stage2 Tighter"


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


def _train_seed_root(seed: int) -> Path:
    return _resolve_repo_path(
        f"cmorl_cyborg/outputs/fair_compare_tuning/{TIGHTER_METHOD_NAME}/seed_{seed:04d}"
    )


def _eval_input_buffer_path(seed: int) -> Path:
    return _resolve_repo_path(
        f"cmorl_cyborg/outputs/fair_compare_eval_inputs/{TIGHTER_METHOD_NAME}/seed_{seed:04d}/solution_buffer.json"
    )


def _tight_metrics_path(seed: int) -> Path:
    return _resolve_repo_path(
        f"cmorl_cyborg/outputs/fair_compare_eval/tight/{TIGHTER_METHOD_NAME}/seed_{seed:04d}/constraint_metrics.json"
    )


def _seed_summary_path(seed: int) -> Path:
    return _resolve_repo_path(
        f"cmorl_cyborg/outputs/fair_compare_eval/reevaluated_tight_feasible_set_summary/{TIGHTER_METHOD_NAME}/seed_{seed:04d}.json"
    )


def _runner_root() -> Path:
    return ensure_dir(
        _resolve_repo_path("cmorl_cyborg/outputs/fair_compare_tighter_runner")
    )


def _generated_config_root() -> Path:
    return ensure_dir(_runner_root() / "generated_configs")


def _thresholds_tight_path() -> Path:
    return _resolve_repo_path("cmorl_cyborg/outputs/fair_compare_eval/thresholds_tight.json")


def _aggregated_root() -> Path:
    return ensure_dir(_resolve_repo_path("cmorl_cyborg/outputs/fair_compare_eval/aggregated"))


def _latest_run_artifact(seed_root: Path, filename: str) -> Path | None:
    run_paths = sorted(
        seed_root.glob(f"run_*/{filename}"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not run_paths:
        return None
    return run_paths[0].resolve()


class ProgressTracker:
    def __init__(self, total_steps: int) -> None:
        self.total_steps = max(int(total_steps), 1)
        self.completed_steps = 0
        self.pipeline_start = time.monotonic()
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

    def _append_log(self, message: str) -> None:
        line = f"[{_timestamp()}] {message}"
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")

    def _format_seconds(self, seconds: float) -> str:
        total = max(int(seconds), 0)
        hours, remainder = divmod(total, 3600)
        minutes, secs = divmod(remainder, 60)
        if hours > 0:
            return f"{hours:d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"

    def _bar(self) -> str:
        width = 28
        filled = int(width * self.completed_steps / self.total_steps)
        return "#" * filled + "-" * (width - filled)

    def _write_status(
        self,
        status: str,
        *,
        label: str | None,
        step_elapsed: float | None = None,
        error: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        payload: dict[str, Any] = {
            "status": status,
            "pid": os.getpid(),
            "updated_at": _timestamp(),
            "pipeline_started_at": self.pipeline_started_at,
            "pipeline_elapsed_seconds": round(time.monotonic() - self.pipeline_start, 1),
            "total_steps": self.total_steps,
            "completed_steps": self.completed_steps,
            "percent_complete": round(100.0 * self.completed_steps / self.total_steps, 1),
            "current_step": label,
            "current_step_started_at": self.current_step_started_at if label else None,
            "step_elapsed_seconds": None if step_elapsed is None else round(step_elapsed, 1),
            "current_command": self.current_command,
            "current_subprocess_pid": self.current_subprocess_pid,
            "log_path": str(self.log_path.resolve()),
            "last_error": error if error is not None else self.last_error,
        }
        if extra:
            payload.update(extra)
        save_json(self.status_path, payload)

    def _print(self, status: str, label: str, *, step_elapsed: float | None = None) -> None:
        total_elapsed = self._format_seconds(time.monotonic() - self.pipeline_start)
        percent = 100.0 * self.completed_steps / self.total_steps
        message = (
            f"[{self._bar()}] {self.completed_steps:02d}/{self.total_steps:02d} "
            f"{percent:5.1f}% | {status:<5} | {label} | total {total_elapsed}"
        )
        if step_elapsed is not None:
            message += f" | step {self._format_seconds(step_elapsed)}"
        print(message, flush=True)
        self._append_log(message)

    def start_step(self, label: str) -> float:
        step_start = time.monotonic()
        self.current_label = label
        self.current_step_started_at = _timestamp()
        self.current_step_start_monotonic = step_start
        self.current_command = None
        self.current_subprocess_pid = None
        self.last_error = None
        self._print("START", label)
        self._write_status("START", label=label, step_elapsed=0.0)
        return step_start

    def heartbeat(self, label: str, step_start: float) -> None:
        self._print("RUN", label, step_elapsed=time.monotonic() - step_start)
        self._write_status("RUN", label=label, step_elapsed=time.monotonic() - step_start)

    def finish_step(self, label: str, step_start: float, *, skipped: bool = False) -> None:
        self.completed_steps += 1
        state = "SKIP" if skipped else "DONE"
        self._print(state, label, step_elapsed=time.monotonic() - step_start)
        self._write_status(state, label=label, step_elapsed=time.monotonic() - step_start)
        self.current_label = None
        self.current_step_started_at = None
        self.current_step_start_monotonic = None
        self.current_command = None
        self.current_subprocess_pid = None
        self.last_error = None

    def attach_command(self, label: str, cmd: list[str]) -> None:
        if self.current_label != label:
            return
        self.current_command = list(cmd)
        self._append_log("$ " + " ".join(cmd))
        self._write_status("START", label=label, step_elapsed=0.0)

    def attach_subprocess(self, label: str, pid: int) -> None:
        if self.current_label != label:
            return
        self.current_subprocess_pid = pid
        self._append_log(f"SUBPROCESS PID {pid} | {label}")
        self._write_status("RUN", label=label, step_elapsed=0.0)

    def fail_step(self, label: str | None, error: BaseException | str) -> None:
        active_label = label or self.current_label or "unknown_step"
        active_start = self.current_step_start_monotonic
        step_elapsed = None if active_start is None else (time.monotonic() - active_start)
        self.last_error = str(error)
        self._print("FAIL", active_label, step_elapsed=step_elapsed)
        self._append_log(f"ERROR | {active_label} | {self.last_error}")
        self._write_status("FAIL", label=active_label, step_elapsed=step_elapsed, error=self.last_error)

    def log_exception_traceback(self, exc: BaseException) -> None:
        self._append_log(traceback.format_exc().rstrip() or repr(exc))

    def finalize(self, *, success: bool, extra: dict[str, Any] | None = None) -> None:
        final_status = "COMPLETE" if success else "FAILED"
        if success:
            self.completed_steps = self.total_steps
        self.current_label = None
        self.current_step_started_at = None
        self.current_step_start_monotonic = None
        self.current_command = None
        self.current_subprocess_pid = None
        self._append_log(f"RUNNER {final_status}")
        self._write_status(final_status, label=None, extra=extra)


def _run_module(
    module: str,
    args: list[str],
    *,
    progress: ProgressTracker,
    label: str,
) -> None:
    cmd = [sys.executable, "-m", module, *args]
    progress.attach_command(label, cmd)
    with progress.log_path.open("a", encoding="utf-8") as log_handle:
        process = subprocess.Popen(
            cmd,
            cwd=_repo_root(),
            stdout=log_handle,
            stderr=subprocess.STDOUT,
        )
        progress.attach_subprocess(label, process.pid)
        step_start = time.monotonic()
        next_heartbeat = step_start + 30.0
        while True:
            return_code = process.poll()
            if return_code is not None:
                if return_code != 0:
                    raise subprocess.CalledProcessError(return_code, cmd)
                return
            if time.monotonic() >= next_heartbeat:
                progress.heartbeat(label, step_start)
                next_heartbeat += 30.0
            time.sleep(1.0)


def _materialize_stage2_config(
    *,
    seed: int,
    constraint_tolerance: float,
    constrained_updates: int,
    barrier_coef: float,
    beta_min: float,
    beta_max: float,
) -> Path:
    base_config_path = _resolve_repo_path(
        f"cmorl_cyborg/configs/paper/fair_compare/stage2_fair_constrained_seed_{seed:04d}.yaml"
    )
    payload = _load_yaml(base_config_path)
    payload["constraint_tolerance"] = float(constraint_tolerance)
    payload["constrained_updates"] = int(constrained_updates)
    payload["output_dir"] = f"cmorl_cyborg/outputs/fair_compare_tuning/{TIGHTER_METHOD_NAME}/seed_{seed:04d}"
    ipo = dict(payload.get("ipo", {}) or {})
    ipo["barrier_coef"] = float(barrier_coef)
    ipo["beta_min"] = float(beta_min)
    ipo["beta_max"] = float(beta_max)
    payload["ipo"] = ipo
    config_path = _generated_config_root() / f"stage2_fair_tighter_seed_{seed:04d}.yaml"
    return _write_yaml(config_path, payload)


def _materialize_eval_config(
    *,
    seed: int,
    buffer_path: Path,
    eval_episodes: int,
) -> Path:
    payload = {
        "method_name": TIGHTER_METHOD_NAME,
        "input_kind": "buffer",
        "input_path": str(buffer_path.resolve()),
        "selection_source": "pareto",
        "selection_policy": "objective",
        "thresholds_path": str(_thresholds_tight_path().resolve()),
        "output_path": str(_tight_metrics_path(seed).resolve()),
        "eval_episodes": int(eval_episodes),
    }
    config_path = _generated_config_root() / f"evaluate_tight_seed_{seed:04d}.yaml"
    return _write_yaml(config_path, payload)


class _CandidateLogger:
    def __init__(self, progress: ProgressTracker) -> None:
        self.progress = progress

    def start(self, label: str) -> None:
        self.progress._append_log(f"REEVAL START {label}")

    def done(self, label: str) -> None:
        self.progress._append_log(f"REEVAL DONE {label}")


def _run_training_for_seed(
    *,
    seed: int,
    constraint_tolerance: float,
    constrained_updates: int,
    barrier_coef: float,
    beta_min: float,
    beta_max: float,
    progress: ProgressTracker,
) -> Path:
    seed_root = _train_seed_root(seed)
    existing = _latest_run_artifact(seed_root, "solution_buffer.json")
    label = f"train tighter_ours seed_{seed:04d}"
    if existing is not None:
        step_start = progress.start_step(label)
        progress.finish_step(label, step_start, skipped=True)
        return existing

    config_path = _materialize_stage2_config(
        seed=seed,
        constraint_tolerance=constraint_tolerance,
        constrained_updates=constrained_updates,
        barrier_coef=barrier_coef,
        beta_min=beta_min,
        beta_max=beta_max,
    )
    step_start = progress.start_step(label)
    _run_module(
        "cmorl_cyborg.train_stage2",
        ["--config", str(config_path), "--output-dir", str(seed_root)],
        progress=progress,
        label=label,
    )
    progress.finish_step(label, step_start)
    created = _latest_run_artifact(seed_root, "solution_buffer.json")
    if created is None:
        raise FileNotFoundError(f"Missing solution_buffer.json under {seed_root}")
    return created


def _copy_eval_input_for_seed(*, seed: int, train_buffer_path: Path, progress: ProgressTracker) -> Path:
    target_path = _eval_input_buffer_path(seed)
    label = f"copy eval_input seed_{seed:04d}"
    step_start = progress.start_step(label)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(train_buffer_path, target_path)
    progress.finish_step(label, step_start)
    return target_path.resolve()


def _run_tight_eval_for_seed(
    *,
    seed: int,
    input_buffer_path: Path,
    selected_eval_episodes: int,
    progress: ProgressTracker,
) -> Path:
    output_path = _tight_metrics_path(seed)
    label = f"tight eval seed_{seed:04d}"
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
    _run_module(
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
    progress: ProgressTracker,
) -> dict[str, Any]:
    reevaluate_mod.DISPLAY_NAMES[TIGHTER_METHOD_NAME] = TIGHTER_DISPLAY_NAME
    reevaluate_mod.COLORS[TIGHTER_METHOD_NAME] = "#72b7b2"
    label = f"reevaluate set seed_{seed:04d}"
    step_start = progress.start_step(label)
    summary = reevaluate_mod._seed_summary(
        method_name=TIGHTER_METHOD_NAME,
        constraint_metrics_path=constraint_metrics_path,
        eval_episodes=int(reevaluated_eval_episodes),
        logger=_CandidateLogger(progress),
    )
    save_json(_seed_summary_path(seed), summary)
    progress.finish_step(label, step_start)
    return summary


def _aggregate_selected_policy(
    *,
    metrics_paths: list[Path],
    progress: ProgressTracker,
) -> Path:
    label = "aggregate tighter selected-policy tight metrics"
    step_start = progress.start_step(label)
    aggregate_path = _aggregated_root() / f"{TIGHTER_METHOD_NAME}_tight.json"
    write_aggregated_constraint_metrics(
        [str(path.resolve()) for path in metrics_paths],
        aggregate_path,
        method_name=TIGHTER_METHOD_NAME,
    )
    progress.finish_step(label, step_start)
    return aggregate_path.resolve()


def _plot_selected_policy_compare(
    *,
    new_aggregate_path: Path,
    progress: ProgressTracker,
) -> Path:
    label = "plot tighter selected-policy compare"
    step_start = progress.start_step(label)
    output_path = _aggregated_root() / "fair_compare_table_b_tight_with_tighter_ours.png"
    baseline_paths = [
        _aggregated_root() / "ours_stage2_fair_tight.json",
        new_aggregate_path,
        _aggregated_root() / "no_constraint_stage2_fair_tight.json",
        _aggregated_root() / "coverage_combo_fair_tight.json",
        _aggregated_root() / "coverage_more_parents_fair_tight.json",
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
    progress: ProgressTracker,
) -> dict[str, Path]:
    reevaluate_mod.DISPLAY_NAMES[TIGHTER_METHOD_NAME] = TIGHTER_DISPLAY_NAME
    reevaluate_mod.COLORS[TIGHTER_METHOD_NAME] = "#72b7b2"
    label = "aggregate tighter reevaluated set metrics"
    step_start = progress.start_step(label)
    new_row = reevaluate_mod._aggregate_method_rows(TIGHTER_METHOD_NAME, seed_rows)

    baseline_payload = load_json(
        _aggregated_root() / "reevaluated_tight_feasible_set_summary.json"
    )
    baseline_rows = list(baseline_payload.get("methods", []))
    filtered_rows = [
        row for row in baseline_rows if str(row.get("method_name")) != TIGHTER_METHOD_NAME
    ]
    combined_rows = []
    for method_name in (
        BASE_METHOD_NAME,
        TIGHTER_METHOD_NAME,
        "no_constraint_stage2_fair",
        "coverage_combo_fair",
        "coverage_more_parents_fair",
    ):
        if method_name == TIGHTER_METHOD_NAME:
            combined_rows.append(new_row)
            continue
        match = next((row for row in filtered_rows if str(row.get("method_name")) == method_name), None)
        if match is not None:
            combined_rows.append(match)

    csv_path = _aggregated_root() / "reevaluated_tight_feasible_set_summary_with_tighter_ours.csv"
    json_path = _aggregated_root() / "reevaluated_tight_feasible_set_summary_with_tighter_ours.json"
    figure_path = _aggregated_root() / "reevaluated_tight_feasible_set_quality_with_tighter_ours.png"

    reevaluate_mod._write_aggregate_csv(csv_path, combined_rows)
    save_json(
        json_path,
        {
            "methods": combined_rows,
            "eval_episodes": int(reevaluated_eval_episodes),
            "thresholds": load_json(_thresholds_tight_path()),
            "baseline_summary_path": str(
                (_aggregated_root() / "reevaluated_tight_feasible_set_summary.json").resolve()
            ),
            "new_method_name": TIGHTER_METHOD_NAME,
        },
    )
    reevaluate_mod._plot_reevaluated_tight_feasible_set(combined_rows, figure_path)
    progress.finish_step(label, step_start)
    return {
        "csv": csv_path.resolve(),
        "json": json_path.resolve(),
        "figure": figure_path.resolve(),
    }


def _candidate_count_from_buffer(buffer_path: Path) -> int:
    payload = load_policy_buffer(buffer_path)
    return int(len(payload.get("pareto_front", [])))


def run_tighter_ours_fair_compare(
    *,
    pilot_seeds: tuple[int, ...],
    full_seeds: tuple[int, ...],
    constraint_tolerance: float,
    constrained_updates: int,
    barrier_coef: float,
    beta_min: float,
    beta_max: float,
    selected_eval_episodes: int,
    reevaluated_eval_episodes: int,
    force_full: bool,
) -> dict[str, Any]:
    full_seed_order = tuple(dict.fromkeys(int(seed) for seed in full_seeds))
    pilot_seed_order = tuple(dict.fromkeys(int(seed) for seed in pilot_seeds))
    planned_train_eval_seeds = full_seed_order if force_full else tuple(
        dict.fromkeys((*pilot_seed_order, *full_seed_order))
    )
    total_steps = len(planned_train_eval_seeds) * 4 + 3
    progress = ProgressTracker(total_steps=total_steps)

    manifest: dict[str, Any] = {
        "method_name": TIGHTER_METHOD_NAME,
        "display_name": TIGHTER_DISPLAY_NAME,
        "pilot_seeds": list(pilot_seed_order),
        "full_seeds": list(full_seed_order),
        "force_full": bool(force_full),
        "constraint_tolerance": float(constraint_tolerance),
        "constrained_updates": int(constrained_updates),
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
    decision = "pilot"
    try:
        for seed in pilot_seed_order:
            train_buffer = _run_training_for_seed(
                seed=seed,
                constraint_tolerance=constraint_tolerance,
                constrained_updates=constrained_updates,
                barrier_coef=barrier_coef,
                beta_min=beta_min,
                beta_max=beta_max,
                progress=progress,
            )
            eval_input = _copy_eval_input_for_seed(
                seed=seed,
                train_buffer_path=train_buffer,
                progress=progress,
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
            manifest["per_seed"][f"seed_{seed:04d}"] = {
                "train_buffer": str(train_buffer),
                "eval_input_buffer": str(eval_input),
                "tight_metrics": str(metrics_path),
                "reevaluated_seed_summary": str(_seed_summary_path(seed).resolve()),
                "pareto_candidate_count": _candidate_count_from_buffer(eval_input),
                "reevaluated_feasible_candidate_count": int(
                    seed_summary["reevaluated_feasible_candidate_count"]
                ),
                "closest_candidate_margin": float(seed_summary["closest_candidate_margin"]),
            }
            successful_seeds.append(seed)
            metrics_paths.append(metrics_path)
            seed_rows.append(seed_summary)
            save_json(_runner_root() / "run_manifest.json", manifest)

        pilot_has_feasible = any(
            int(row["reevaluated_feasible_candidate_count"]) > 0 for row in seed_rows
        )
        decision = "expand_to_full" if (force_full or pilot_has_feasible) else "stop_after_pilot"

        if decision == "expand_to_full":
            remaining_seeds = [seed for seed in full_seed_order if seed not in successful_seeds]
            for seed in remaining_seeds:
                train_buffer = _run_training_for_seed(
                    seed=seed,
                    constraint_tolerance=constraint_tolerance,
                    constrained_updates=constrained_updates,
                    barrier_coef=barrier_coef,
                    beta_min=beta_min,
                    beta_max=beta_max,
                    progress=progress,
                )
                eval_input = _copy_eval_input_for_seed(
                    seed=seed,
                    train_buffer_path=train_buffer,
                    progress=progress,
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
                manifest["per_seed"][f"seed_{seed:04d}"] = {
                    "train_buffer": str(train_buffer),
                    "eval_input_buffer": str(eval_input),
                    "tight_metrics": str(metrics_path),
                    "reevaluated_seed_summary": str(_seed_summary_path(seed).resolve()),
                    "pareto_candidate_count": _candidate_count_from_buffer(eval_input),
                    "reevaluated_feasible_candidate_count": int(
                        seed_summary["reevaluated_feasible_candidate_count"]
                    ),
                    "closest_candidate_margin": float(seed_summary["closest_candidate_margin"]),
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
            "method_name": TIGHTER_METHOD_NAME,
            "display_name": TIGHTER_DISPLAY_NAME,
            "decision": decision,
            "completed_seeds": successful_seeds,
            "pilot_has_reevaluated_feasible_candidate": any(
                int(row["reevaluated_feasible_candidate_count"]) > 0
                for row in seed_rows[: len(pilot_seed_order)]
            ),
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
                "decision": decision,
                "completed_seeds": successful_seeds,
                "run_manifest_path": str((_runner_root() / "run_manifest.json").resolve()),
            },
        )
        raise


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Pilot-first tighter fair-compare rerun for Ours Stage2. "
            "Runs seed 19 first, then expands to 7/11 only if the pilot "
            "produces at least one reevaluated tight-feasible candidate."
        )
    )
    parser.add_argument("--pilot-seeds", nargs="+", type=int, default=list(DEFAULT_PILOT_SEEDS))
    parser.add_argument("--full-seeds", nargs="+", type=int, default=list(DEFAULT_FULL_SEEDS))
    parser.add_argument("--force-full", action="store_true")
    parser.add_argument("--constraint-tolerance", type=float, default=DEFAULT_CONSTRAINT_TOLERANCE)
    parser.add_argument("--constrained-updates", type=int, default=DEFAULT_CONSTRAINED_UPDATES)
    parser.add_argument("--barrier-coef", type=float, default=DEFAULT_BARRIER_COEF)
    parser.add_argument("--beta-min", type=float, default=DEFAULT_BETA_MIN)
    parser.add_argument("--beta-max", type=float, default=DEFAULT_BETA_MAX)
    parser.add_argument("--selected-eval-episodes", type=int, default=DEFAULT_SELECTED_EVAL_EPISODES)
    parser.add_argument("--reevaluated-eval-episodes", type=int, default=DEFAULT_REEVALUATED_EVAL_EPISODES)
    args = parser.parse_args()

    outputs = run_tighter_ours_fair_compare(
        pilot_seeds=tuple(int(seed) for seed in args.pilot_seeds),
        full_seeds=tuple(int(seed) for seed in args.full_seeds),
        constraint_tolerance=float(args.constraint_tolerance),
        constrained_updates=int(args.constrained_updates),
        barrier_coef=float(args.barrier_coef),
        beta_min=float(args.beta_min),
        beta_max=float(args.beta_max),
        selected_eval_episodes=int(args.selected_eval_episodes),
        reevaluated_eval_episodes=int(args.reevaluated_eval_episodes),
        force_full=bool(args.force_full),
    )
    for key, value in outputs.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
