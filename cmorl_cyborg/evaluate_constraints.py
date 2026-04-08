from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import cmorl_minicage.evaluate_constraints as base
import numpy as np

from .config import DEFAULT_CONSTRAINT_EVALUATE_CONFIG, load_constraint_evaluate_config
from .env import CybORGMORLEnv
from cmorl_minicage.utils import load_json, save_json

base.MiniCageMORLEnv = CybORGMORLEnv
compute_shared_thresholds = base.compute_shared_thresholds
evaluate_constraints = base.evaluate_constraints

_AGGREGATE_FIELDS = (
    "security_return",
    "business_return",
    "cost_return",
    "feasible_rate",
    "mean_violation",
    "final_compromised_hosts",
    "final_critical_compromised_hosts",
    "critical_impact_count",
    "recovered_hosts",
    "analyse_count",
    "remove_count",
    "restore_count",
    "high_disruption_action_rate",
)


def aggregate_constraint_metrics(
    metrics_paths: list[str | Path],
    *,
    method_name: str | None = None,
) -> dict[str, Any]:
    if not metrics_paths:
        raise ValueError("metrics_paths must not be empty")

    payloads = [load_json(path) for path in metrics_paths]
    thresholds = payloads[0].get("thresholds", {})
    for payload in payloads[1:]:
        other_thresholds = payload.get("thresholds", {})
        if thresholds and other_thresholds and other_thresholds != thresholds:
            raise ValueError("All constraint payloads must share the same thresholds")

    aggregated: dict[str, Any] = {
        "schema_version": payloads[0].get("schema_version", "0.1.0"),
        "method_name": method_name or payloads[0].get("method_name", "constraint_method"),
        "num_runs": len(payloads),
        "source_metrics_paths": [str(Path(path).resolve()) for path in metrics_paths],
        "selected_policy_ids": [payload.get("selected_policy_id", "") for payload in payloads],
        "thresholds": thresholds,
    }
    for field_name in _AGGREGATE_FIELDS:
        values = np.asarray(
            [float(payload.get(field_name, 0.0)) for payload in payloads],
            dtype=np.float64,
        )
        aggregated[field_name] = float(np.mean(values))
        aggregated[f"{field_name}_std"] = float(np.std(values))
    return aggregated


def write_aggregated_constraint_metrics(
    metrics_paths: list[str | Path],
    output_path: str | Path,
    *,
    method_name: str | None = None,
) -> Path:
    output_path = Path(output_path)
    payload = aggregate_constraint_metrics(metrics_paths, method_name=method_name)
    save_json(output_path, payload)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate constraint metrics on CybORG.")
    subparsers = parser.add_subparsers(dest="command", required=False)

    build_parser = subparsers.add_parser("build-thresholds")
    build_parser.add_argument("--buffer-paths", nargs="+", required=True)
    build_parser.add_argument("--output-path", required=True)

    aggregate_parser = subparsers.add_parser("aggregate")
    aggregate_parser.add_argument("--metrics-paths", nargs="+", required=True)
    aggregate_parser.add_argument("--method-name", default=None)
    aggregate_parser.add_argument("--output-path", required=True)

    parser.add_argument("--config", default=str(DEFAULT_CONSTRAINT_EVALUATE_CONFIG))
    parser.add_argument("--method-name", default=None)
    parser.add_argument("--input-kind", choices=("buffer", "single_policy"), default=None)
    parser.add_argument("--input-path", default=None)
    parser.add_argument("--selection-source", choices=("pareto", "records"), default=None)
    parser.add_argument("--selection-policy", choices=("objective", "semantic_aware", "semantic_balanced"), default=None)
    parser.add_argument("--thresholds-path", default=None)
    parser.add_argument("--output-path", default=None)
    args = parser.parse_args()

    if args.command == "build-thresholds":
        thresholds = compute_shared_thresholds(args.buffer_paths, args.output_path)
        print(thresholds)
        return

    if args.command == "aggregate":
        output_path = write_aggregated_constraint_metrics(
            args.metrics_paths,
            args.output_path,
            method_name=args.method_name,
        )
        print(output_path)
        return

    config = load_constraint_evaluate_config(args.config)
    if args.method_name is not None:
        config.method_name = args.method_name
    if args.input_kind is not None:
        config.input_kind = args.input_kind
    if args.input_path is not None:
        config.input_path = args.input_path
    if args.selection_source is not None:
        config.selection_source = args.selection_source
    if args.selection_policy is not None:
        config.selection_policy = args.selection_policy
    if args.thresholds_path is not None:
        config.thresholds_path = args.thresholds_path
    if not config.thresholds_path:
        raise ValueError("thresholds_path must be provided")
    if not config.input_path:
        raise ValueError("input_path must be provided")
    payload = evaluate_constraints(
        method_name=config.method_name,
        input_kind=config.input_kind,
        input_path=config.input_path,
        selection_source=config.selection_source,
        selection_policy=config.selection_policy,
        thresholds_path=config.thresholds_path,
        eval_episodes=config.eval_episodes,
        semantic_metric_weights=config.semantic_metric_weights,
        security_margin=config.security_margin,
        feasible_rate_tolerance=config.feasible_rate_tolerance,
        mean_violation_tolerance=config.mean_violation_tolerance,
    )
    output_path = Path(args.output_path or config.output_path or Path(config.input_path).resolve().parent / "constraint_metrics.json")
    save_json(output_path, payload)
    print(output_path)


if __name__ == "__main__":
    main()
