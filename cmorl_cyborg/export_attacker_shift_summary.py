from __future__ import annotations

import argparse
import csv
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from cmorl_minicage.utils import save_json

from .evaluate_constraints import write_aggregated_constraint_metrics
from cmorl_minicage.evaluate_constraints import evaluate_constraints as base_evaluate_constraints


DEFAULT_METHODS = ("ours_stage2", "weighted_sum", "stage1_only")
DEFAULT_SEEDS = (7, 11, 19, 23, 29)

ARTIFACT_ROOTS = {
    "ours_stage2": "cmorl_cyborg/outputs/paper_table_a/ours_stage2",
    "weighted_sum": "cmorl_cyborg/outputs/paper_table_a/weighted_sum",
    "stage1_only": "cmorl_cyborg/outputs/paper_appendix/stage1_only",
    "no_constraint_stage2": "cmorl_cyborg/outputs/paper_appendix/no_constraint_stage2",
}

DISPLAY_NAMES = {
    "ours_stage2": "Ours Stage2",
    "weighted_sum": "Weighted-Sum",
    "stage1_only": "Stage1 Only",
    "no_constraint_stage2": "No-Constraint Stage2",
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _timestamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _write_tex(path: Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
    def tex_escape(value: Any, *, preserve_math: bool = False) -> str:
        text = str(value)
        if preserve_math:
            return text.replace("_", "\\_")
        return text.replace("\\", "\\textbackslash{}").replace("_", "\\_")

    path.parent.mkdir(parents=True, exist_ok=True)
    align = "l" + "c" * (len(columns) - 1)
    lines = [
        "\\begin{tabular}{" + align + "}",
        "\\hline",
        " & ".join(tex_escape(column) for column in columns) + " \\\\",
        "\\hline",
    ]
    for row in rows:
        lines.append(
            " & ".join(tex_escape(row[column], preserve_math=True) for column in columns) + " \\\\"
        )
    lines.extend(["\\hline", "\\end{tabular}"])
    path.write_text("\n".join(lines), encoding="utf-8")


class ShiftLogger:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.log_path = output_dir / "runner.log"
        self.status_path = output_dir / "status.json"
        self._write_status(status="START", current_step=None, completed_steps=0, total_steps=0)
        self.log("RUNNER START")

    def log(self, message: str) -> None:
        line = f"[{_timestamp()}] {message}"
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")

    def _write_status(
        self,
        *,
        status: str,
        current_step: str | None,
        completed_steps: int,
        total_steps: int,
        red_policy: str | None = None,
        current_method: str | None = None,
        current_seed: int | None = None,
        last_error: str | None = None,
    ) -> None:
        save_json(
            self.status_path,
            {
                "status": status,
                "updated_at": _timestamp(),
                "current_step": current_step,
                "completed_steps": completed_steps,
                "total_steps": total_steps,
                "red_policy": red_policy,
                "current_method": current_method,
                "current_seed": current_seed,
                "last_error": last_error,
                "log_path": str(self.log_path),
            },
        )

    def update(
        self,
        *,
        status: str,
        current_step: str | None,
        completed_steps: int,
        total_steps: int,
        red_policy: str | None = None,
        current_method: str | None = None,
        current_seed: int | None = None,
        last_error: str | None = None,
    ) -> None:
        self._write_status(
            status=status,
            current_step=current_step,
            completed_steps=completed_steps,
            total_steps=total_steps,
            red_policy=red_policy,
            current_method=current_method,
            current_seed=current_seed,
            last_error=last_error,
        )


def _artifact_path(method_name: str, seed: int) -> Path:
    summary_path = _repo_root() / "cmorl_cyborg/outputs/paper_table_a/table_a_summary.json"
    if summary_path.exists():
        summary = _load_json(summary_path)
        for row in summary.get("per_run", []):
            if str(row.get("method_name")) == method_name and int(row.get("seed", -1)) == seed:
                artifact_path = row.get("artifact_path")
                if artifact_path:
                    return Path(str(artifact_path)).resolve()

    method_root = ARTIFACT_ROOTS[method_name]
    seed_dir = _repo_root() / method_root / f"seed_{seed:04d}"
    matches = sorted(seed_dir.glob("run_*/solution_buffer.json"))
    if len(matches) != 1:
        raise FileNotFoundError(
            f"Expected exactly one solution_buffer.json for {method_name} seed {seed}, got {matches}"
        )
    return matches[0]


def _override_red_policy(
    source_path: Path,
    *,
    red_policy: str,
    output_path: Path,
) -> Path:
    payload = _load_json(source_path)
    payload.setdefault("metadata", {}).setdefault("env", {})
    payload["metadata"]["env"]["red_policy"] = red_policy
    payload["metadata"]["env"]["seed"] = int(payload["metadata"]["env"].get("seed", 7))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_json(output_path, payload)
    return output_path


def export_attacker_shift_summary(
    *,
    red_policy: str = "meander",
    methods: tuple[str, ...] = DEFAULT_METHODS,
    seeds: tuple[int, ...] = DEFAULT_SEEDS,
    eval_episodes: int = 5,
) -> dict[str, str]:
    output_dir = _repo_root() / "cmorl_cyborg/outputs/paper_appendix/attacker_shift"
    tmp_dir = output_dir / "tmp_inputs"
    per_seed_dir = output_dir / "per_seed"
    aggregated_dir = output_dir / "aggregated"
    output_dir.mkdir(parents=True, exist_ok=True)
    logger = ShiftLogger(output_dir)

    thresholds_path = _repo_root() / "cmorl_cyborg/outputs/paper_table_b/shared_thresholds.json"
    total_steps = len(methods) * len(seeds)
    completed_steps = 0
    per_seed_rows: list[dict[str, Any]] = []
    aggregated_paths: list[str] = []

    for method_name in methods:
        method_metric_paths: list[str] = []
        for seed in seeds:
            step_name = f"{method_name}:seed_{seed:04d}:{red_policy}"
            logger.log(f"START {step_name}")
            logger.update(
                status="RUN",
                current_step=step_name,
                completed_steps=completed_steps,
                total_steps=total_steps,
                red_policy=red_policy,
                current_method=method_name,
                current_seed=seed,
            )

            try:
                source_path = _artifact_path(method_name, seed)
            except FileNotFoundError:
                logger.log(f"SKIP missing artifact for {step_name}")
                completed_steps += 1
                continue

            shifted_input = _override_red_policy(
                source_path,
                red_policy=red_policy,
                output_path=tmp_dir / method_name / f"seed_{seed:04d}" / "solution_buffer.json",
            )
            result = base_evaluate_constraints(
                method_name=method_name,
                input_kind="buffer",
                input_path=str(shifted_input),
                selection_source="pareto",
                selection_policy="objective",
                thresholds_path=str(thresholds_path),
                eval_episodes=eval_episodes,
                semantic_metric_weights={
                    "high_disruption_action_rate": 0.50,
                    "final_critical_compromised_hosts": 0.30,
                    "critical_impact_count": 0.20,
                },
                security_margin=120.0,
                feasible_rate_tolerance=0.10,
                mean_violation_tolerance=0.50,
            )
            result["eval_red_policy"] = red_policy
            result["train_red_policy"] = "bline"
            result["source_buffer_path"] = str(source_path)
            result["shifted_input_path"] = str(shifted_input)

            metric_path = per_seed_dir / method_name / f"seed_{seed:04d}.json"
            save_json(metric_path, result)
            method_metric_paths.append(str(metric_path))
            per_seed_rows.append(
                {
                    "method_name": method_name,
                    "display_name": DISPLAY_NAMES.get(method_name, method_name),
                    "seed": seed,
                    "train_red_policy": "bline",
                    "eval_red_policy": red_policy,
                    "security_return": float(result["security_return"]),
                    "business_return": float(result["business_return"]),
                    "cost_return": float(result["cost_return"]),
                    "feasible_rate": float(result["feasible_rate"]),
                    "mean_violation": float(result["mean_violation"]),
                    "final_critical_compromised_hosts": float(result["final_critical_compromised_hosts"]),
                    "critical_impact_count": float(result["critical_impact_count"]),
                    "high_disruption_action_rate": float(result["high_disruption_action_rate"]),
                }
            )
            completed_steps += 1
            logger.log(f"DONE {step_name}")
            logger.update(
                status="RUN",
                current_step=step_name,
                completed_steps=completed_steps,
                total_steps=total_steps,
                red_policy=red_policy,
                current_method=method_name,
                current_seed=seed,
            )

        if method_metric_paths:
            aggregate_path = aggregated_dir / f"{method_name}.json"
            write_aggregated_constraint_metrics(
                method_metric_paths,
                aggregate_path,
                method_name=method_name,
            )
            aggregate_payload = _load_json(aggregate_path)
            aggregate_payload["display_name"] = DISPLAY_NAMES.get(method_name, method_name)
            aggregate_payload["train_red_policy"] = "bline"
            aggregate_payload["eval_red_policy"] = red_policy
            save_json(aggregate_path, aggregate_payload)
            aggregated_paths.append(str(aggregate_path))

    summary_json = output_dir / "attacker_shift_summary.json"
    summary_csv = output_dir / "attacker_shift_summary.csv"
    summary_tex = output_dir / "attacker_shift_summary.tex"
    aggregate_rows = [_load_json(path) for path in aggregated_paths]
    aggregate_rows = sorted(aggregate_rows, key=lambda row: methods.index(row["method_name"]))
    flat_rows = [
        {
            "method_name": row["method_name"],
            "display_name": row.get("display_name", row["method_name"]),
            "num_runs": row["num_runs"],
            "train_red_policy": row["train_red_policy"],
            "eval_red_policy": row["eval_red_policy"],
            "security_return": row["security_return"],
            "business_return": row["business_return"],
            "cost_return": row["cost_return"],
            "feasible_rate": row["feasible_rate"],
            "mean_violation": row["mean_violation"],
            "critical_impact_count": row["critical_impact_count"],
            "high_disruption_action_rate": row["high_disruption_action_rate"],
        }
        for row in aggregate_rows
    ]
    _write_csv(
        summary_csv,
        [
            "method_name",
            "display_name",
            "num_runs",
            "train_red_policy",
            "eval_red_policy",
            "security_return",
            "business_return",
            "cost_return",
            "feasible_rate",
            "mean_violation",
            "critical_impact_count",
            "high_disruption_action_rate",
        ],
        flat_rows,
    )
    _write_tex(
        summary_tex,
        [
            "display_name",
            "security_return",
            "business_return",
            "cost_return",
            "feasible_rate",
            "mean_violation",
            "critical_impact_count",
        ],
        flat_rows,
    )
    save_json(
        summary_json,
        {
            "train_red_policy": "bline",
            "eval_red_policy": red_policy,
            "methods": list(methods),
            "seeds": list(seeds),
            "eval_episodes": eval_episodes,
            "aggregated_paths": aggregated_paths,
            "per_seed_rows": per_seed_rows,
        },
    )

    logger.log("RUNNER COMPLETE")
    logger.update(
        status="COMPLETE",
        current_step=None,
        completed_steps=completed_steps,
        total_steps=total_steps,
        red_policy=red_policy,
    )

    return {
        "summary_json": str(summary_json),
        "summary_csv": str(summary_csv),
        "summary_tex": str(summary_tex),
        "log_path": str(logger.log_path),
        "status_path": str(logger.status_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run minimal attacker-shift evaluation.")
    parser.add_argument("--red-policy", default="meander")
    parser.add_argument("--methods", nargs="+", default=list(DEFAULT_METHODS))
    parser.add_argument("--seeds", nargs="+", type=int, default=list(DEFAULT_SEEDS))
    parser.add_argument("--eval-episodes", type=int, default=5)
    args = parser.parse_args()
    outputs = export_attacker_shift_summary(
        red_policy=str(args.red_policy),
        methods=tuple(str(method) for method in args.methods),
        seeds=tuple(int(seed) for seed in args.seeds),
        eval_episodes=int(args.eval_episodes),
    )
    print(outputs)


if __name__ == "__main__":
    main()
