from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from cmorl_minicage.utils import save_json

from .evaluate_constraints import evaluate_constraints, write_aggregated_constraint_metrics


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_METHODS = (
    "ours_stage2_v2_4",
    "stage1_only_4obj",
    "no_constraint_stage2_4obj",
    "weighted_sum_4obj",
)
DEFAULT_SEEDS = (7, 11, 19)
DEFAULT_EVAL_EPISODES = 5
DEFAULT_TABLE_A_SUMMARY_PATH = (
    REPO_ROOT / "cmorl_cyborg" / "outputs" / "paper_4obj" / "table_a" / "table_a_summary.json"
)
DEFAULT_TABLE_B_SUMMARY_PATH = (
    REPO_ROOT / "cmorl_cyborg" / "outputs" / "paper_4obj" / "table_b" / "table_b_summary.json"
)
DEFAULT_SHARED_THRESHOLDS_PATH = (
    REPO_ROOT / "cmorl_cyborg" / "outputs" / "paper_4obj" / "table_b" / "shared_thresholds.json"
)
DEFAULT_OUTPUT_DIR = (
    REPO_ROOT / "cmorl_cyborg" / "outputs" / "paper_4obj" / "attacker_shift_meander"
)

DISPLAY_NAMES = {
    "ours_stage2_v2_4": "Constraint-Aware Stage-2",
    "stage1_only_4obj": "Stage-1 Policy Archive",
    "no_constraint_stage2_4obj": "Unconstrained Stage-2",
    "weighted_sum_4obj": "Weighted-Sum",
}


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
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "\\begin{tabular}{@{}lccccccc@{}}",
        "\\toprule",
        " & ".join(columns) + " \\\\",
        "\\midrule",
    ]
    for row in rows:
        lines.append(" & ".join(str(row[column]) for column in columns) + " \\\\")
    lines.extend(["\\bottomrule", "\\end{tabular}"])
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
        eval_red_policy: str | None = None,
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
                "eval_red_policy": eval_red_policy,
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
        eval_red_policy: str | None = None,
        current_method: str | None = None,
        current_seed: int | None = None,
        last_error: str | None = None,
    ) -> None:
        self._write_status(
            status=status,
            current_step=current_step,
            completed_steps=completed_steps,
            total_steps=total_steps,
            eval_red_policy=eval_red_policy,
            current_method=current_method,
            current_seed=current_seed,
            last_error=last_error,
        )


def _resolve_artifact_path(raw_path: str | Path) -> Path:
    resolved_path = Path(str(raw_path))
    if not resolved_path.is_absolute():
        resolved_path = (REPO_ROOT / resolved_path).resolve()
    return resolved_path


def _artifact_lookup(
    table_a_summary_path: str | Path,
    table_b_summary_path: str | Path | None = None,
) -> dict[str, dict[int, Path]]:
    payload = _load_json(table_a_summary_path)
    lookup: dict[str, dict[int, Path]] = {}
    for row in payload.get("per_run", []):
        method_name = str(row.get("method_name", ""))
        seed = int(row.get("seed", -1))
        artifact_path = row.get("artifact_path")
        if not method_name or seed < 0 or not artifact_path:
            continue
        lookup.setdefault(method_name, {})[seed] = _resolve_artifact_path(artifact_path)
    if table_b_summary_path is not None and Path(table_b_summary_path).exists():
        table_b_payload = _load_json(table_b_summary_path)
        for row in table_b_payload.get("per_run_records", []):
            if str(row.get("input_kind", "")) != "buffer":
                continue
            method_name = str(row.get("method_name", ""))
            seed = int(row.get("seed", -1))
            input_path = row.get("input_path")
            if not method_name or seed < 0 or not input_path:
                continue
            lookup.setdefault(method_name, {}).setdefault(seed, _resolve_artifact_path(input_path))
    if not lookup:
        raise ValueError(
            f"Missing paper_4obj buffer artifact rows in {table_a_summary_path}"
        )
    return lookup


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


def export_attacker_shift_summary_4obj(
    *,
    red_policy: str = "meander",
    methods: tuple[str, ...] = DEFAULT_METHODS,
    seeds: tuple[int, ...] = DEFAULT_SEEDS,
    eval_episodes: int = DEFAULT_EVAL_EPISODES,
    table_a_summary_path: str | Path = DEFAULT_TABLE_A_SUMMARY_PATH,
    table_b_summary_path: str | Path = DEFAULT_TABLE_B_SUMMARY_PATH,
    shared_thresholds_path: str | Path = DEFAULT_SHARED_THRESHOLDS_PATH,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, str]:
    output_dir = Path(output_dir)
    tmp_dir = output_dir / "tmp_inputs"
    per_seed_dir = output_dir / "per_seed"
    aggregated_dir = output_dir / "aggregated"
    output_dir.mkdir(parents=True, exist_ok=True)

    artifact_lookup = _artifact_lookup(table_a_summary_path, table_b_summary_path)
    shared_thresholds_path = Path(shared_thresholds_path).resolve()
    logger = ShiftLogger(output_dir)

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
                eval_red_policy=red_policy,
                current_method=method_name,
                current_seed=seed,
            )

            source_path = artifact_lookup.get(method_name, {}).get(seed)
            if source_path is None:
                logger.log(f"SKIP missing artifact for {step_name}")
                completed_steps += 1
                continue

            shifted_input = _override_red_policy(
                source_path,
                red_policy=red_policy,
                output_path=tmp_dir / method_name / f"seed_{seed:04d}" / "solution_buffer.json",
            )
            result = evaluate_constraints(
                method_name=method_name,
                input_kind="buffer",
                input_path=str(shifted_input),
                selection_source="pareto",
                selection_policy="objective",
                thresholds_path=str(shared_thresholds_path),
                eval_episodes=int(eval_episodes),
                semantic_metric_weights={
                    "high_disruption_action_rate": 0.50,
                    "final_critical_compromised_hosts": 0.30,
                    "critical_impact_count": 0.20,
                },
                security_margin=120.0,
                feasible_rate_tolerance=0.10,
                mean_violation_tolerance=0.50,
            )
            result["train_red_policy"] = "bline"
            result["eval_red_policy"] = red_policy
            result["source_buffer_path"] = str(source_path)
            result["shifted_input_path"] = str(shifted_input)

            metric_path = per_seed_dir / method_name / f"seed_{seed:04d}.json"
            save_json(metric_path, result)
            method_metric_paths.append(str(metric_path))
            per_seed_rows.append(
                {
                    "method_name": method_name,
                    "display_name": DISPLAY_NAMES.get(method_name, method_name),
                    "seed": int(seed),
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
                eval_red_policy=red_policy,
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
            aggregated_paths.append(str(aggregate_path.resolve()))

    summary_json = output_dir / "attacker_shift_summary.json"
    summary_csv = output_dir / "attacker_shift_summary.csv"
    summary_tex = output_dir / "attacker_shift_summary.tex"

    aggregate_rows = [_load_json(path) for path in aggregated_paths]
    aggregate_rows.sort(key=lambda row: methods.index(str(row["method_name"])))
    flat_rows = [
        {
            "display_name": row.get("display_name", row["method_name"]),
            "security_return": f"{float(row['security_return']):.4f}",
            "business_return": f"{float(row['business_return']):.4f}",
            "cost_return": f"{float(row['cost_return']):.4f}",
            "feasible_rate": f"{float(row['feasible_rate']):.4f}",
            "mean_violation": f"{float(row['mean_violation']):.4f}",
            "final_critical_compromised_hosts": f"{float(row['final_critical_compromised_hosts']):.4f}",
            "critical_impact_count": f"{float(row['critical_impact_count']):.4f}",
            "high_disruption_action_rate": f"{float(row['high_disruption_action_rate']):.4f}",
        }
        for row in aggregate_rows
    ]
    _write_csv(
        summary_csv,
        [
            "display_name",
            "security_return",
            "business_return",
            "cost_return",
            "feasible_rate",
            "mean_violation",
            "final_critical_compromised_hosts",
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
            "final_critical_compromised_hosts",
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
            "eval_episodes": int(eval_episodes),
            "table_a_summary_path": str(Path(table_a_summary_path).resolve()),
            "table_b_summary_path": str(Path(table_b_summary_path).resolve()),
            "shared_thresholds_path": str(shared_thresholds_path),
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
        eval_red_policy=red_policy,
    )

    return {
        "summary_json": str(summary_json.resolve()),
        "summary_csv": str(summary_csv.resolve()),
        "summary_tex": str(summary_tex.resolve()),
        "status_path": str((output_dir / "status.json").resolve()),
        "log_path": str((output_dir / "runner.log").resolve()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run held-out attacker shift evaluation for the paper_4obj method set."
    )
    parser.add_argument("--red-policy", default="meander")
    parser.add_argument("--methods", nargs="+", default=list(DEFAULT_METHODS))
    parser.add_argument("--seeds", nargs="+", type=int, default=list(DEFAULT_SEEDS))
    parser.add_argument("--eval-episodes", type=int, default=DEFAULT_EVAL_EPISODES)
    parser.add_argument("--table-a-summary-path", default=str(DEFAULT_TABLE_A_SUMMARY_PATH))
    parser.add_argument("--table-b-summary-path", default=str(DEFAULT_TABLE_B_SUMMARY_PATH))
    parser.add_argument("--shared-thresholds-path", default=str(DEFAULT_SHARED_THRESHOLDS_PATH))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    outputs = export_attacker_shift_summary_4obj(
        red_policy=str(args.red_policy),
        methods=tuple(str(method) for method in args.methods),
        seeds=tuple(int(seed) for seed in args.seeds),
        eval_episodes=int(args.eval_episodes),
        table_a_summary_path=args.table_a_summary_path,
        table_b_summary_path=args.table_b_summary_path,
        shared_thresholds_path=args.shared_thresholds_path,
        output_dir=args.output_dir,
    )
    print(json.dumps(outputs, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
