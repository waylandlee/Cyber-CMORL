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


def _build_cyborg_env_from_metadata(metadata: dict[str, object]) -> CybORGMORLEnv:
    env_config = dict(metadata.get("env", {})) if isinstance(metadata, dict) else {}
    model_config = dict(metadata.get("model", {})) if isinstance(metadata, dict) else {}
    shield_config = dict(metadata.get("shield", {})) if isinstance(metadata, dict) else {}
    return CybORGMORLEnv(
        num_envs=int(env_config.get("num_envs", 8)),
        red_policy=str(env_config.get("red_policy", "bline")),
        remove_bugs=bool(env_config.get("remove_bugs", True)),
        max_steps=int(env_config.get("max_episode_steps", 100)),
        seed=int(env_config.get("seed", 7)),
        scenario_name=str(env_config.get("scenario_name", "Scenario2")),
        scenario_profile=str(env_config.get("scenario_profile", "")),
        gym_wrapper_name=str(env_config.get("gym_wrapper_name", "ChallengeWrapper")),
        blue_agent_name=str(env_config.get("blue_agent_name", "Blue")),
        red_agent_name=str(env_config.get("red_agent_name", "Red")),
        obs_mode=str(env_config.get("obs_mode", "vector")),
        state_mode=str(env_config.get("state_mode", "true")),
        obj_dim=int(model_config.get("obj_dim", 3)),
        critical_host_safety_mode=str(
            model_config.get("critical_host_safety_mode", "v2_legacy")
        ),
        shield_mode=str(shield_config.get("mode", "disabled")),
    )


base._build_env_from_metadata = _build_cyborg_env_from_metadata
compute_shared_thresholds = base.compute_shared_thresholds
evaluate_constraints = base.evaluate_constraints

_AGGREGATE_FIELDS = (
    "security_return",
    "business_return",
    "cost_return",
    "critical_host_safety_return",
    "critical_host_safety_cvar_alpha",
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
        raw_values = [
            payload.get(field_name)
            for payload in payloads
            if payload.get(field_name) is not None
        ]
        if not raw_values:
            aggregated[field_name] = None
            aggregated[f"{field_name}_std"] = None
            continue
        values = np.asarray([float(value) for value in raw_values], dtype=np.float64)
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
    parser.add_argument(
        "--selection-policy",
        choices=(
            "objective",
            "semantic_aware",
            "semantic_balanced",
            "critical_safe_balanced",
        ),
        default=None,
    )
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
