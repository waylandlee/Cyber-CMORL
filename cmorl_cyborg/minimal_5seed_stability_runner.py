from __future__ import annotations

import argparse
import os
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

from cmorl_minicage.utils import ensure_dir, save_json

from .week2_formal_runner import (
    _resolve_repo_path,
    _run_stage1,
    _run_stage2,
    _run_weighted_sum,
)

DEFAULT_BASE_SEEDS = (7, 11, 19)
DEFAULT_EXTRA_SEEDS = (23, 29)
DEFAULT_METHODS = ("stage1_only", "weighted_sum", "ours_stage2")


class StabilityProgressTracker:
    def __init__(self, total_steps: int, *, output_dir: Path, dry_run: bool = False) -> None:
        self.total_steps = max(int(total_steps), 1)
        self.completed_steps = 0
        self.pipeline_start = time.monotonic()
        self.pipeline_started_at = self._timestamp()
        self.dry_run = dry_run
        self.output_dir = ensure_dir(output_dir)
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

    def _timestamp(self) -> str:
        return datetime.now().astimezone().isoformat(timespec="seconds")

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

    def _append_log(self, message: str) -> None:
        line = f"[{self._timestamp()}] {message}"
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(line)
            handle.write("\n")

    def _write_status(
        self,
        status: str,
        *,
        label: str | None,
        step_elapsed: float | None = None,
        error: str | None = None,
    ) -> None:
        payload: dict[str, Any] = {
            "status": status,
            "dry_run": self.dry_run,
            "pid": os.getpid(),
            "updated_at": self._timestamp(),
            "pipeline_started_at": self.pipeline_started_at,
            "pipeline_elapsed_seconds": round(time.monotonic() - self.pipeline_start, 1),
            "total_steps": self.total_steps,
            "completed_steps": self.completed_steps,
            "percent_complete": round(100.0 * self.completed_steps / self.total_steps, 1),
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
        active_start = self.current_step_start_monotonic
        step_elapsed = None if active_start is None else (time.monotonic() - active_start)
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


def _artifact_for_method(method_name: str, seed: int) -> Path:
    if method_name == "stage1_only":
        return _resolve_repo_path(
            f"cmorl_cyborg/outputs/paper_appendix/stage1_only/seed_{seed:04d}"
        )
    if method_name == "weighted_sum":
        return _resolve_repo_path(
            f"cmorl_cyborg/outputs/paper_table_a/weighted_sum/seed_{seed:04d}"
        )
    if method_name == "ours_stage2":
        return _resolve_repo_path(
            f"cmorl_cyborg/outputs/paper_table_a/ours_stage2/seed_{seed:04d}"
        )
    if method_name == "no_constraint_stage2":
        return _resolve_repo_path(
            f"cmorl_cyborg/outputs/paper_appendix/no_constraint_stage2/seed_{seed:04d}"
        )
    raise ValueError(f"Unsupported method: {method_name}")


def run_minimal_5seed_stability(
    *,
    extra_seeds: tuple[int, ...],
    methods: tuple[str, ...],
    include_existing: bool,
    dry_run: bool,
) -> dict[str, Any]:
    seeds = tuple(DEFAULT_BASE_SEEDS + extra_seeds) if include_existing else tuple(extra_seeds)
    total_steps = 0
    for _seed in seeds:
        if "stage1_only" in methods or "ours_stage2" in methods or "no_constraint_stage2" in methods:
            total_steps += 1
        if "weighted_sum" in methods:
            total_steps += 1
        if "ours_stage2" in methods:
            total_steps += 1
        if "no_constraint_stage2" in methods:
            total_steps += 1

    output_dir = ensure_dir(
        _resolve_repo_path("cmorl_cyborg/outputs/paper_5seed_runner")
    )
    tracker = StabilityProgressTracker(total_steps, output_dir=output_dir, dry_run=dry_run)
    manifest: dict[str, Any] = {
        "base_seeds": list(DEFAULT_BASE_SEEDS),
        "extra_seeds": list(extra_seeds),
        "resolved_seeds": list(seeds),
        "methods": list(methods),
        "dry_run": dry_run,
        "started_at": tracker.pipeline_started_at,
        "log_path": str(tracker.log_path.resolve()),
        "status_path": str(tracker.status_path.resolve()),
        "per_seed": {},
    }

    try:
        for seed in seeds:
            seed_key = f"seed_{seed:04d}"
            seed_summary: dict[str, Any] = {}
            stage1_buffer: Path | None = None

            if (
                "stage1_only" in methods
                or "ours_stage2" in methods
                or "no_constraint_stage2" in methods
            ):
                stage1_buffer = _run_stage1(seed, dry_run=dry_run, progress=tracker)
                seed_summary["stage1_only_buffer"] = str(stage1_buffer)

            if "weighted_sum" in methods:
                weighted_sum_buffer = _run_weighted_sum(seed, dry_run=dry_run, progress=tracker)
                seed_summary["weighted_sum_buffer"] = str(weighted_sum_buffer)

            if "ours_stage2" in methods:
                if stage1_buffer is None:
                    raise RuntimeError("stage1 buffer is required for ours_stage2")
                ours_buffer = _run_stage2(
                    seed,
                    constrained=True,
                    stage1_buffer=stage1_buffer,
                    dry_run=dry_run,
                    progress=tracker,
                )
                seed_summary["ours_stage2_buffer"] = str(ours_buffer)

            if "no_constraint_stage2" in methods:
                if stage1_buffer is None:
                    raise RuntimeError("stage1 buffer is required for no_constraint_stage2")
                no_constraint_buffer = _run_stage2(
                    seed,
                    constrained=False,
                    stage1_buffer=stage1_buffer,
                    dry_run=dry_run,
                    progress=tracker,
                )
                seed_summary["no_constraint_stage2_buffer"] = str(no_constraint_buffer)

            manifest["per_seed"][seed_key] = seed_summary
            save_json(output_dir / "run_manifest.json", manifest)

        manifest["finished_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
        manifest["artifacts_by_method"] = {
            method: [str(_artifact_for_method(method, seed)) for seed in seeds]
            for method in methods
        }
        save_json(output_dir / "run_manifest.json", manifest)
        tracker.finalize(success=True)
        return manifest
    except BaseException as exc:
        tracker.fail_step(tracker.current_label, exc)
        tracker.log_exception_traceback(exc)
        tracker.finalize(success=False)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run the minimal 5-seed stability extension for the formal CybORG line "
            "and continuously write progress/status logs."
        )
    )
    parser.add_argument(
        "--extra-seeds",
        nargs="+",
        type=int,
        default=list(DEFAULT_EXTRA_SEEDS),
        help="New seeds to add on top of the default 3-seed protocol.",
    )
    parser.add_argument(
        "--methods",
        nargs="+",
        default=list(DEFAULT_METHODS),
        choices=["stage1_only", "weighted_sum", "ours_stage2", "no_constraint_stage2"],
        help="Methods to include in the stability extension.",
    )
    parser.add_argument(
        "--extra-only",
        action="store_true",
        help="Run only the new seeds instead of replaying the original 3-seed set.",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    manifest = run_minimal_5seed_stability(
        extra_seeds=tuple(args.extra_seeds),
        methods=tuple(args.methods),
        include_existing=not args.extra_only,
        dry_run=args.dry_run,
    )
    print(str(_resolve_repo_path("cmorl_cyborg/outputs/paper_5seed_runner/run_manifest.json")))
    print("Methods:", ", ".join(manifest["methods"]))
    print("Seeds:", ", ".join(f"{seed:04d}" for seed in manifest["resolved_seeds"]))


if __name__ == "__main__":
    main()
