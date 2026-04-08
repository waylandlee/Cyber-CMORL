from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from cmorl_minicage.utils import ensure_dir, save_json

from .paper_plots import plot_paper_tables

SEEDS = (7, 11, 19)


class ProgressTracker:
    def __init__(self, total_steps: int, *, dry_run: bool = False) -> None:
        self.total_steps = max(int(total_steps), 1)
        self.completed_steps = 0
        self.pipeline_start = time.monotonic()
        self.pipeline_started_at = self._timestamp()
        self.dry_run = dry_run
        self.output_dir = ensure_dir(_resolve_repo_path("cmorl_cyborg/outputs/paper_week2_runner"))
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

    def _timestamp(self) -> str:
        return datetime.now().astimezone().isoformat(timespec="seconds")

    def _append_log(self, message: str) -> None:
        timestamped = f"[{self._timestamp()}] {message}"
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(timestamped)
            handle.write("\n")

    def _write_status(
        self,
        status: str,
        *,
        label: str | None,
        step_elapsed: float | None = None,
        error: str | None = None,
    ) -> None:
        percent = 100.0 * self.completed_steps / self.total_steps
        payload: dict[str, Any] = {
            "status": status,
            "dry_run": self.dry_run,
            "pid": os.getpid(),
            "updated_at": self._timestamp(),
            "pipeline_started_at": self.pipeline_started_at,
            "pipeline_elapsed_seconds": round(time.monotonic() - self.pipeline_start, 1),
            "total_steps": self.total_steps,
            "completed_steps": self.completed_steps,
            "percent_complete": round(percent, 1),
            "current_step": label,
            "current_step_started_at": self.current_step_started_at if label is not None else None,
            "step_elapsed_seconds": None if step_elapsed is None else round(step_elapsed, 1),
            "current_command": self.current_command,
            "current_subprocess_pid": self.current_subprocess_pid,
            "log_path": str(self.log_path.resolve()),
            "last_error": error if error is not None else self.last_error,
        }
        save_json(self.status_path, payload)

    def _print(self, status: str, label: str, *, step_elapsed: float | None = None) -> None:
        pipeline_elapsed = self._format_seconds(time.monotonic() - self.pipeline_start)
        percent = 100.0 * self.completed_steps / self.total_steps
        message = (
            f"[{self._bar()}] {self.completed_steps:02d}/{self.total_steps:02d} "
            f"{percent:5.1f}% | {status:<5} | {label} | total {pipeline_elapsed}"
        )
        if step_elapsed is not None:
            message += f" | step {self._format_seconds(step_elapsed)}"
        print(message, file=sys.stderr, flush=True)
        self._append_log(message)

    def start_step(self, label: str) -> float:
        step_start = time.monotonic()
        self.current_label = label
        self.current_step_started_at = self._timestamp()
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
        status = "SKIP" if skipped else "DONE"
        self._print(status, label, step_elapsed=time.monotonic() - step_start)
        self._write_status(status, label=label, step_elapsed=time.monotonic() - step_start)
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
        active_step_start = self.current_step_start_monotonic
        step_elapsed = None if active_step_start is None else (time.monotonic() - active_step_start)
        self.last_error = str(error)
        self._print("FAIL", active_label, step_elapsed=step_elapsed)
        self._append_log(f"ERROR | {active_label} | {self.last_error}")
        self._write_status("FAIL", label=active_label, step_elapsed=step_elapsed, error=self.last_error)

    def log_exception_traceback(self, exc: BaseException) -> None:
        self._append_log(traceback.format_exc().rstrip() or repr(exc))

    def finalize(self, *, success: bool) -> None:
        final_status = "COMPLETE" if success else "FAILED"
        self.current_label = None
        self.current_step_started_at = None
        self.current_step_start_monotonic = None
        self.current_command = None
        self.current_subprocess_pid = None
        self._append_log(f"RUNNER {final_status}")
        self._write_status(final_status, label=None)


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


def _set_seed(config: dict[str, Any], seed: int) -> dict[str, Any]:
    payload = dict(config)
    payload["seed"] = seed
    env = dict(payload.get("env", {}) or {})
    env["seed"] = seed
    payload["env"] = env
    return payload


def _run_module(
    module: str,
    args: list[str],
    *,
    dry_run: bool = False,
    progress: ProgressTracker | None = None,
    label: str | None = None,
) -> None:
    cmd = [sys.executable, "-m", module, *args]
    print("$", " ".join(cmd))
    if progress is not None and label is not None:
        progress.attach_command(label, cmd)
    if dry_run:
        return
    runner_log_path = progress.log_path if progress is not None else None
    with (runner_log_path.open("a", encoding="utf-8") if runner_log_path is not None else open(os.devnull, "w", encoding="utf-8")) as log_handle:
        process = subprocess.Popen(
            cmd,
            cwd=_repo_root(),
            stdout=log_handle,
            stderr=subprocess.STDOUT,
        )
        if progress is not None and label is not None:
            progress.attach_subprocess(label, process.pid)
        step_start = time.monotonic()
        next_heartbeat = step_start + 30.0
        while True:
            return_code = process.poll()
            if return_code is not None:
                if return_code != 0:
                    raise subprocess.CalledProcessError(return_code, cmd)
                return
            if progress is not None and label is not None and time.monotonic() >= next_heartbeat:
                progress.heartbeat(label, step_start)
                next_heartbeat += 30.0
            time.sleep(1.0)


def _run_dirs(seed_root: Path) -> list[Path]:
    return sorted(
        (path for path in seed_root.glob("run_*") if path.is_dir()),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )


def _single_run_dir(seed_root: Path) -> Path | None:
    run_dirs = _run_dirs(seed_root)
    if not run_dirs:
        return None
    return run_dirs[0]


def _artifact_in_seed_dir(seed_root: Path, relative_path: str) -> Path | None:
    for run_dir in _run_dirs(seed_root):
        artifact_path = run_dir / relative_path
        if artifact_path.exists():
            return artifact_path
    return None


def _require_artifact(seed_root: Path, relative_path: str) -> Path:
    artifact_path = _artifact_in_seed_dir(seed_root, relative_path)
    if artifact_path is None:
        raise FileNotFoundError(f"Missing {relative_path} under {seed_root}")
    return artifact_path.resolve()


def _expected_artifact_path(seed_root: Path, relative_path: str) -> Path:
    return (seed_root / "run_PENDING" / relative_path).resolve()


def _stage1_seed_dir(seed: int) -> Path:
    return _resolve_repo_path(f"cmorl_cyborg/outputs/paper_appendix/stage1_only/seed_{seed:04d}")


def _ours_seed_dir(seed: int) -> Path:
    return _resolve_repo_path(f"cmorl_cyborg/outputs/paper_table_a/ours_stage2/seed_{seed:04d}")


def _weighted_sum_seed_dir(seed: int) -> Path:
    return _resolve_repo_path(f"cmorl_cyborg/outputs/paper_table_a/weighted_sum/seed_{seed:04d}")


def _pref_cond_seed_dir(seed: int) -> Path:
    return _resolve_repo_path(
        f"cmorl_cyborg/outputs/paper_table_a/preference_conditioned_ppo/seed_{seed:04d}"
    )


def _pcn_seed_dir(seed: int) -> Path:
    return _resolve_repo_path(f"cmorl_cyborg/outputs/paper_appendix/pcn/seed_{seed:04d}")


def _no_constraint_seed_dir(seed: int) -> Path:
    return _resolve_repo_path(
        f"cmorl_cyborg/outputs/paper_appendix/no_constraint_stage2/seed_{seed:04d}"
    )


def _single_objective_seed_dir(seed: int) -> Path:
    return _resolve_repo_path(f"cmorl_cyborg/outputs/paper_table_b/single_objective/seed_{seed:04d}")


def _lagrangian_seed_dir(seed: int) -> Path:
    return _resolve_repo_path(f"cmorl_cyborg/outputs/paper_table_b/lagrangian_ppo/seed_{seed:04d}")


def _tmp_config_dir() -> Path:
    return ensure_dir(_resolve_repo_path("cmorl_cyborg/outputs/paper_week2_runner/tmp_configs"))


def _materialize_config(base_config_path: str | Path, *, seed: int, updates: dict[str, Any]) -> Path:
    payload = _set_seed(_load_yaml(base_config_path), seed)
    payload.update(updates)
    config_name = f"{Path(base_config_path).stem}_seed_{seed:04d}.yaml"
    return _write_yaml(_tmp_config_dir() / config_name, payload)


def _run_stage1(
    seed: int,
    *,
    dry_run: bool = False,
    progress: ProgressTracker | None = None,
) -> Path:
    output_dir = _stage1_seed_dir(seed)
    label = f"stage1_only seed_{seed:04d}"
    existing = _artifact_in_seed_dir(output_dir, "solution_buffer.json")
    if existing is not None:
        if progress is not None:
            step_start = progress.start_step(label)
            progress.finish_step(label, step_start, skipped=True)
        return existing.resolve()
    config_path = _materialize_config(
        _resolve_repo_path("cmorl_cyborg/configs/paper/stage1_only_main.yaml"),
        seed=seed,
        updates={},
    )
    step_start = progress.start_step(label) if progress is not None else None
    _run_module(
        "cmorl_cyborg.train_stage1",
        ["--config", str(config_path), "--output-dir", str(output_dir)],
        dry_run=dry_run,
        progress=progress,
        label=label,
    )
    if progress is not None and step_start is not None:
        progress.finish_step(label, step_start)
    if dry_run:
        return _expected_artifact_path(output_dir, "solution_buffer.json")
    return _require_artifact(output_dir, "solution_buffer.json")


def _run_stage2(
    seed: int,
    *,
    constrained: bool,
    stage1_buffer: Path,
    dry_run: bool = False,
    progress: ProgressTracker | None = None,
) -> Path:
    output_dir = _ours_seed_dir(seed) if constrained else _no_constraint_seed_dir(seed)
    mode_name = "ours_stage2" if constrained else "no_constraint_stage2"
    label = f"{mode_name} seed_{seed:04d}"
    existing = _artifact_in_seed_dir(output_dir, "solution_buffer.json")
    if existing is not None:
        if progress is not None:
            step_start = progress.start_step(label)
            progress.finish_step(label, step_start, skipped=True)
        return existing.resolve()
    base_name = "stage2_main.yaml" if constrained else "stage2_no_constraint_main.yaml"
    config_path = _materialize_config(
        _resolve_repo_path(f"cmorl_cyborg/configs/paper/{base_name}"),
        seed=seed,
        updates={"stage1_buffer": str(stage1_buffer)},
    )
    step_start = progress.start_step(label) if progress is not None else None
    _run_module(
        "cmorl_cyborg.train_stage2",
        ["--config", str(config_path), "--output-dir", str(output_dir)],
        dry_run=dry_run,
        progress=progress,
        label=label,
    )
    if progress is not None and step_start is not None:
        progress.finish_step(label, step_start)
    if dry_run:
        return _expected_artifact_path(output_dir, "solution_buffer.json")
    return _require_artifact(output_dir, "solution_buffer.json")


def _run_weighted_sum(
    seed: int,
    *,
    dry_run: bool = False,
    progress: ProgressTracker | None = None,
) -> Path:
    output_dir = _weighted_sum_seed_dir(seed)
    label = f"weighted_sum seed_{seed:04d}"
    existing = _artifact_in_seed_dir(output_dir, "solution_buffer.json")
    if existing is not None:
        if progress is not None:
            step_start = progress.start_step(label)
            progress.finish_step(label, step_start, skipped=True)
        return existing.resolve()
    config_path = _materialize_config(
        _resolve_repo_path("cmorl_cyborg/configs/paper/weighted_sum_main.yaml"),
        seed=seed,
        updates={},
    )
    step_start = progress.start_step(label) if progress is not None else None
    _run_module(
        "cmorl_cyborg.baselines",
        [
            "weighted-sum",
            "--stage1-config",
            str(config_path),
            "--evaluate-config",
            str(_resolve_repo_path("cmorl_cyborg/configs/paper/evaluate_main_table_a.yaml")),
            "--output-dir",
            str(output_dir),
        ],
        dry_run=dry_run,
        progress=progress,
        label=label,
    )
    if progress is not None and step_start is not None:
        progress.finish_step(label, step_start)
    if dry_run:
        return _expected_artifact_path(output_dir, "solution_buffer.json")
    return _require_artifact(output_dir, "solution_buffer.json")


def _run_pref_cond(
    seed: int,
    *,
    dry_run: bool = False,
    progress: ProgressTracker | None = None,
) -> Path:
    output_dir = _pref_cond_seed_dir(seed)
    label = f"preference_conditioned_ppo seed_{seed:04d}"
    existing = _artifact_in_seed_dir(output_dir, "conditioned_run_metadata.json")
    if existing is not None:
        if progress is not None:
            step_start = progress.start_step(label)
            progress.finish_step(label, step_start, skipped=True)
        return existing.resolve()
    config_path = _materialize_config(
        _resolve_repo_path("cmorl_cyborg/configs/paper/pref_cond_ppo.yaml"),
        seed=seed,
        updates={},
    )
    step_start = progress.start_step(label) if progress is not None else None
    _run_module(
        "cmorl_cyborg.train_pref_conditioned_ppo",
        ["--config", str(config_path), "--output-dir", str(output_dir)],
        dry_run=dry_run,
        progress=progress,
        label=label,
    )
    if progress is not None and step_start is not None:
        progress.finish_step(label, step_start)
    if dry_run:
        return _expected_artifact_path(output_dir, "conditioned_run_metadata.json")
    return _require_artifact(output_dir, "conditioned_run_metadata.json")


def _run_single_objective(
    seed: int,
    *,
    dry_run: bool = False,
    progress: ProgressTracker | None = None,
) -> Path:
    output_dir = _single_objective_seed_dir(seed)
    label = f"single_objective seed_{seed:04d}"
    existing = _artifact_in_seed_dir(output_dir, "solution_buffer.json")
    if existing is not None:
        if progress is not None:
            step_start = progress.start_step(label)
            progress.finish_step(label, step_start, skipped=True)
        return existing.resolve()
    config_path = _materialize_config(
        _resolve_repo_path("cmorl_cyborg/configs/paper/single_objective_main.yaml"),
        seed=seed,
        updates={},
    )
    step_start = progress.start_step(label) if progress is not None else None
    _run_module(
        "cmorl_cyborg.baselines",
        [
            "single-objective",
            "--stage1-config",
            str(config_path),
            "--evaluate-config",
            str(_resolve_repo_path("cmorl_cyborg/configs/paper/evaluate_main_table_a.yaml")),
            "--output-dir",
            str(output_dir),
        ],
        dry_run=dry_run,
        progress=progress,
        label=label,
    )
    if progress is not None and step_start is not None:
        progress.finish_step(label, step_start)
    if dry_run:
        return _expected_artifact_path(output_dir, "solution_buffer.json")
    return _require_artifact(output_dir, "solution_buffer.json")


def _run_pcn(
    seed: int,
    *,
    archive_sources: list[Path],
    dry_run: bool = False,
    progress: ProgressTracker | None = None,
) -> Path:
    output_dir = _pcn_seed_dir(seed)
    label = f"pcn seed_{seed:04d}"
    existing = _artifact_in_seed_dir(output_dir, "conditioned_run_metadata.json")
    if existing is not None:
        if progress is not None:
            step_start = progress.start_step(label)
            progress.finish_step(label, step_start, skipped=True)
        return existing.resolve()
    config_path = _materialize_config(
        _resolve_repo_path("cmorl_cyborg/configs/paper/pcn.yaml"),
        seed=seed,
        updates={"archive_sources": [str(path) for path in archive_sources]},
    )
    step_start = progress.start_step(label) if progress is not None else None
    _run_module(
        "cmorl_cyborg.train_pcn",
        ["--config", str(config_path), "--output-dir", str(output_dir)],
        dry_run=dry_run,
        progress=progress,
        label=label,
    )
    if progress is not None and step_start is not None:
        progress.finish_step(label, step_start)
    if dry_run:
        return _expected_artifact_path(output_dir, "conditioned_run_metadata.json")
    return _require_artifact(output_dir, "conditioned_run_metadata.json")


def _build_shared_thresholds(
    stage1_buffers: list[Path],
    *,
    dry_run: bool = False,
    progress: ProgressTracker | None = None,
) -> Path:
    thresholds_path = _resolve_repo_path("cmorl_cyborg/outputs/paper_table_b/shared_thresholds.json")
    label = "shared_thresholds"
    if thresholds_path.exists() and not dry_run:
        if progress is not None:
            step_start = progress.start_step(label)
            progress.finish_step(label, step_start, skipped=True)
        return thresholds_path.resolve()
    step_start = progress.start_step(label) if progress is not None else None
    _run_module(
        "cmorl_cyborg.evaluate_constraints",
        [
            "build-thresholds",
            "--buffer-paths",
            *[str(path) for path in stage1_buffers],
            "--output-path",
            str(thresholds_path),
        ],
        dry_run=dry_run,
        progress=progress,
        label=label,
    )
    if progress is not None and step_start is not None:
        progress.finish_step(label, step_start)
    return thresholds_path.resolve()


def _run_lagrangian(
    seed: int,
    *,
    thresholds_path: Path,
    stage1_buffer: Path,
    dry_run: bool = False,
    progress: ProgressTracker | None = None,
) -> Path:
    output_dir = _lagrangian_seed_dir(seed)
    label = f"lagrangian_ppo seed_{seed:04d}"
    existing = _artifact_in_seed_dir(output_dir, "run_metadata.json")
    if existing is not None:
        if progress is not None:
            step_start = progress.start_step(label)
            progress.finish_step(label, step_start, skipped=True)
        return existing.resolve()
    config_path = _materialize_config(
        _resolve_repo_path("cmorl_cyborg/configs/paper/lagrangian_ppo.yaml"),
        seed=seed,
        updates={
            "stage1_buffer": str(stage1_buffer),
            "thresholds_path": str(thresholds_path),
        },
    )
    step_start = progress.start_step(label) if progress is not None else None
    _run_module(
        "cmorl_cyborg.train_lagrangian_ppo",
        ["--config", str(config_path), "--output-dir", str(output_dir)],
        dry_run=dry_run,
        progress=progress,
        label=label,
    )
    if progress is not None and step_start is not None:
        progress.finish_step(label, step_start)
    if dry_run:
        return _expected_artifact_path(output_dir, "run_metadata.json")
    return _require_artifact(output_dir, "run_metadata.json")


def _run_summary_step(
    module: str,
    config_path: Path,
    *,
    label: str,
    dry_run: bool,
    progress: ProgressTracker | None,
) -> None:
    step_start = progress.start_step(label) if progress is not None else None
    _run_module(
        module,
        ["--config", str(config_path)],
        dry_run=dry_run,
        progress=progress,
        label=label,
    )
    if progress is not None and step_start is not None:
        progress.finish_step(label, step_start)


def _generate_tables_and_plots(
    *,
    dry_run: bool = False,
    progress: ProgressTracker | None = None,
) -> dict[str, str]:
    compare_config = _resolve_repo_path("cmorl_cyborg/configs/paper/compare_suite_main.yaml")
    table_b_config = _resolve_repo_path("cmorl_cyborg/configs/paper/table_b_suite_main.yaml")
    export_config = _resolve_repo_path("cmorl_cyborg/configs/paper/export_tables_main.yaml")
    compare_summary = _resolve_repo_path("cmorl_cyborg/outputs/paper_table_a/table_a_summary.json")
    table_b_summary = _resolve_repo_path("cmorl_cyborg/outputs/paper_table_b/table_b_summary.json")
    export_summary = _resolve_repo_path("cmorl_cyborg/outputs/paper_table_a/tables/export_summary.json")

    _run_summary_step(
        "cmorl_cyborg.main_table_a",
        compare_config,
        label="main_table_a",
        dry_run=dry_run,
        progress=progress,
    )
    _run_summary_step(
        "cmorl_cyborg.main_table_b",
        table_b_config,
        label="main_table_b",
        dry_run=dry_run,
        progress=progress,
    )
    _run_summary_step(
        "cmorl_cyborg.export_tables",
        export_config,
        label="export_tables",
        dry_run=dry_run,
        progress=progress,
    )

    plot_outputs: dict[str, str] = {}
    if not dry_run:
        plot_outputs = plot_paper_tables(
            compare_summary_path=compare_summary,
            table_b_summary_path=table_b_summary,
        )
    summary = {
        "compare_summary_path": str(compare_summary.resolve()),
        "table_b_summary_path": str(table_b_summary.resolve()),
        "export_summary_path": str(export_summary.resolve()),
        "plot_outputs": plot_outputs,
    }
    summary_path = _resolve_repo_path("cmorl_cyborg/outputs/paper_week2_runner/runner_summary.json")
    save_json(summary_path, summary)
    return {"runner_summary_path": str(summary_path.resolve()), **plot_outputs}


def run_week2_formal(*, include_pcn: bool = True, dry_run: bool = False) -> dict[str, Any]:
    per_seed_steps = 7 if include_pcn else 6
    total_steps = len(SEEDS) + 1 + len(SEEDS) * per_seed_steps + 3
    progress = ProgressTracker(total_steps, dry_run=dry_run)
    try:
        stage1_buffers = [_run_stage1(seed, dry_run=dry_run, progress=progress) for seed in SEEDS]
        thresholds_path = _build_shared_thresholds(
            stage1_buffers,
            dry_run=dry_run,
            progress=progress,
        )

        run_summary: dict[str, Any] = {
            "stage1_buffers": [str(path) for path in stage1_buffers],
            "shared_thresholds_path": str(thresholds_path),
            "per_seed": {},
        }
        for seed, stage1_buffer in zip(SEEDS, stage1_buffers):
            weighted_sum_buffer = _run_weighted_sum(seed, dry_run=dry_run, progress=progress)
            seed_summary: dict[str, Any] = {
                "stage1_buffer": str(stage1_buffer),
                "weighted_sum_buffer": str(weighted_sum_buffer),
                "ours_stage2_buffer": str(
                    _run_stage2(
                        seed,
                        constrained=True,
                        stage1_buffer=stage1_buffer,
                        dry_run=dry_run,
                        progress=progress,
                    )
                ),
                "preference_conditioned_ppo": str(
                    _run_pref_cond(seed, dry_run=dry_run, progress=progress)
                ),
                "no_constraint_stage2_buffer": str(
                    _run_stage2(
                        seed,
                        constrained=False,
                        stage1_buffer=stage1_buffer,
                        dry_run=dry_run,
                        progress=progress,
                    )
                ),
                "single_objective_buffer": str(
                    _run_single_objective(seed, dry_run=dry_run, progress=progress)
                ),
                "lagrangian_ppo": str(
                    _run_lagrangian(
                        seed,
                        thresholds_path=thresholds_path,
                        stage1_buffer=stage1_buffer,
                        dry_run=dry_run,
                        progress=progress,
                    )
                ),
            }
            if include_pcn:
                seed_summary["pcn"] = str(
                    _run_pcn(
                        seed,
                        archive_sources=[weighted_sum_buffer],
                        dry_run=dry_run,
                        progress=progress,
                    )
                )
            run_summary["per_seed"][f"seed_{seed:04d}"] = seed_summary

        run_summary["tables_and_plots"] = _generate_tables_and_plots(
            dry_run=dry_run,
            progress=progress,
        )
        summary_path = _resolve_repo_path(
            "cmorl_cyborg/outputs/paper_week2_runner/formal_run_manifest.json"
        )
        save_json(summary_path, run_summary)
        progress.finalize(success=True)
        return run_summary
    except BaseException as exc:
        progress.fail_step(progress.current_label, exc)
        progress.log_exception_traceback(exc)
        progress.finalize(success=False)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the formal Week-2 Scenario2 3-seed pipeline for cmorl_cyborg."
    )
    parser.add_argument("--skip-pcn", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    summary = run_week2_formal(include_pcn=not args.skip_pcn, dry_run=args.dry_run)
    print(summary["tables_and_plots"]["runner_summary_path"])


if __name__ == "__main__":
    main()
