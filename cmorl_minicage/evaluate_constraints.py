from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import torch

from cmorl_minicage.buffer import load_policy_buffer
from cmorl_minicage.config import (
    DEFAULT_CONSTRAINT_EVALUATE_CONFIG,
    load_constraint_evaluate_config,
)
from cmorl_minicage.env import MiniCageMORLEnv
from cmorl_minicage.models import ActorCritic
from cmorl_minicage.utils import load_json, save_json


def _repo_root_from_path(path: str | Path) -> Path:
    path = Path(path).resolve()
    for candidate in (path, *path.parents):
        if (candidate / "cmorl_minicage").exists():
            return candidate
    raise ValueError(f"Could not infer repository root from {path}")


def _resolve_path(anchor: str | Path, raw_path: str | Path) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return (_repo_root_from_path(anchor) / path).resolve()


def _load_thresholds(path: str | Path) -> dict[str, float]:
    payload = load_json(path)
    return {
        "d_business": float(payload["d_business"]),
        "d_cost": float(payload["d_cost"]),
    }


def compute_shared_thresholds(
    buffer_paths: list[str | Path], output_path: str | Path | None = None
) -> dict[str, float]:
    business_values: list[float] = []
    cost_values: list[float] = []
    for buffer_path in buffer_paths:
        payload = load_policy_buffer(buffer_path)
        pareto_front = payload.get("pareto_front", [])
        for record in pareto_front:
            vector = np.asarray(record["objective_vector"], dtype=np.float32)
            business_values.append(float(vector[1]))
            cost_values.append(float(vector[2]))
    if not business_values or not cost_values:
        raise ValueError("Could not compute shared thresholds from empty Pareto fronts")
    thresholds = {
        "d_business": float(np.quantile(np.asarray(business_values), 0.25)),
        "d_cost": float(np.quantile(np.asarray(cost_values), 0.25)),
    }
    if output_path is not None:
        save_json(output_path, thresholds)
    return thresholds


def _build_env_from_metadata(metadata: dict[str, Any]) -> MiniCageMORLEnv:
    env_config = metadata.get("env", {})
    return MiniCageMORLEnv(
        num_envs=int(env_config.get("num_envs", 8)),
        red_policy=env_config.get("red_policy", "bline"),
        remove_bugs=bool(env_config.get("remove_bugs", True)),
        max_steps=int(env_config.get("max_episode_steps", 100)),
        seed=int(env_config.get("seed", 7)),
    )


def _empty_semantics() -> dict[str, list[float]]:
    return {
        "final_compromised_hosts": [],
        "final_critical_compromised_hosts": [],
        "critical_impact_count": [],
        "recovered_hosts": [],
        "analyse_count": [],
        "remove_count": [],
        "restore_count": [],
        "high_disruption_action_count": [],
        "total_action_count": [],
    }


def _semantic_metrics(totals: dict[str, list[float]]) -> dict[str, float]:
    total_action_sum = max(float(np.sum(totals["total_action_count"])), 1.0)
    return {
        "final_compromised_hosts": float(np.mean(totals["final_compromised_hosts"])),
        "final_critical_compromised_hosts": float(
            np.mean(totals["final_critical_compromised_hosts"])
        ),
        "critical_impact_count": float(np.mean(totals["critical_impact_count"])),
        "recovered_hosts": float(np.mean(totals["recovered_hosts"])),
        "analyse_count": float(np.mean(totals["analyse_count"])),
        "remove_count": float(np.mean(totals["remove_count"])),
        "restore_count": float(np.mean(totals["restore_count"])),
        "high_disruption_action_rate": float(
            np.sum(totals["high_disruption_action_count"]) / total_action_sum
        ),
        "semantic_eval_episodes": int(len(totals["final_compromised_hosts"])),
    }


def _sleep_actions(env: MiniCageMORLEnv) -> np.ndarray:
    return np.zeros(env.num_envs, dtype=np.int32)


def _random_valid_actions(env: MiniCageMORLEnv) -> np.ndarray:
    blue_mask = env.sim.get_mask(env.sim.state, env.sim.current_decoys)["Blue"]
    actions = np.zeros(env.num_envs, dtype=np.int32)
    for idx in range(env.num_envs):
        valid_actions = np.flatnonzero(blue_mask[idx] > 0)
        actions[idx] = int(np.random.choice(valid_actions))
    return actions


def _select_record(
    records: list[dict[str, Any]],
    thresholds: dict[str, float],
) -> dict[str, Any]:
    if not records:
        raise ValueError("No candidate records available for constraint selection")

    def score(record: dict[str, Any]) -> tuple[int, float, float, float]:
        vector = np.asarray(record["objective_vector"], dtype=np.float32)
        business_violation = max(0.0, thresholds["d_business"] - float(vector[1]))
        cost_violation = max(0.0, thresholds["d_cost"] - float(vector[2]))
        total_violation = business_violation + cost_violation
        feasible = 1 if total_violation <= 1e-12 else 0
        return (feasible, -total_violation, float(vector[0]), float(vector[1] + vector[2]))

    return max(records, key=score)


def _normalize_metric(values: list[float]) -> list[float]:
    if not values:
        return []
    arr = np.asarray(values, dtype=np.float32)
    vmin = float(np.min(arr))
    vmax = float(np.max(arr))
    if np.isclose(vmax, vmin):
        return [0.0 for _ in values]
    return ((arr - vmin) / (vmax - vmin)).astype(np.float32).tolist()


def _select_record_semantic_aware(
    records: list[dict[str, Any]],
    metadata: dict[str, Any],
    buffer_anchor: str | Path,
    thresholds: dict[str, float],
    *,
    eval_episodes: int,
    semantic_metric_weights: dict[str, float],
) -> tuple[dict[str, Any], dict[str, Any]]:
    if not records:
        raise ValueError("No candidate records available for constraint selection")

    evaluated_candidates: list[dict[str, Any]] = []
    for record in records:
        baseline_kind = record.get("notes", {}).get("baseline_kind")
        metrics = _evaluate_actor_critic_record(
            (
                _resolve_path(buffer_anchor, record["checkpoint_path"])
                if record.get("checkpoint_path")
                else None
            ),
            metadata,
            thresholds,
            eval_episodes=eval_episodes,
            baseline_kind=baseline_kind,
        )
        evaluated_candidates.append(
            {
                "record": record,
                "metrics": metrics,
            }
        )

    weight_total = max(
        float(sum(float(weight) for weight in semantic_metric_weights.values())),
        1e-8,
    )
    normalized_by_metric: dict[str, list[float]] = {}
    for metric_name in semantic_metric_weights:
        normalized_by_metric[metric_name] = _normalize_metric(
            [float(entry["metrics"][metric_name]) for entry in evaluated_candidates]
        )

    for index, entry in enumerate(evaluated_candidates):
        semantic_risk = 0.0
        for metric_name, weight in semantic_metric_weights.items():
            semantic_risk += float(weight) * float(normalized_by_metric[metric_name][index])
        semantic_risk /= weight_total
        entry["semantic_risk"] = float(semantic_risk)

    selected_entry = max(
        evaluated_candidates,
        key=lambda entry: (
            float(entry["metrics"]["feasible_rate"]),
            -float(entry["metrics"]["mean_violation"]),
            -float(entry["semantic_risk"]),
            float(entry["metrics"]["security_return"]),
        ),
    )

    diagnostics = {
        "selection_policy": "semantic_aware",
        "semantic_metric_weights": {
            key: float(value) for key, value in semantic_metric_weights.items()
        },
        "evaluated_candidates": [
            {
                "policy_id": entry["record"]["policy_id"],
                "objective_vector": entry["record"]["objective_vector"],
                "semantic_risk": float(entry["semantic_risk"]),
                "feasible_rate": float(entry["metrics"]["feasible_rate"]),
                "mean_violation": float(entry["metrics"]["mean_violation"]),
                "security_return": float(entry["metrics"]["security_return"]),
                "final_critical_compromised_hosts": float(
                    entry["metrics"]["final_critical_compromised_hosts"]
                ),
                "critical_impact_count": float(entry["metrics"]["critical_impact_count"]),
                "high_disruption_action_rate": float(
                    entry["metrics"]["high_disruption_action_rate"]
                ),
            }
            for entry in sorted(
                evaluated_candidates,
                key=lambda entry: (
                    -float(entry["metrics"]["feasible_rate"]),
                    float(entry["metrics"]["mean_violation"]),
                    float(entry["semantic_risk"]),
                    -float(entry["metrics"]["security_return"]),
                    entry["record"]["policy_id"],
                ),
            )
        ],
    }
    return selected_entry["record"], diagnostics


def _select_record_semantic_balanced(
    records: list[dict[str, Any]],
    metadata: dict[str, Any],
    buffer_anchor: str | Path,
    thresholds: dict[str, float],
    *,
    eval_episodes: int,
    semantic_metric_weights: dict[str, float],
    security_margin: float,
    feasible_rate_tolerance: float,
    mean_violation_tolerance: float,
) -> tuple[dict[str, Any], dict[str, Any]]:
    selected, diagnostics = _select_record_semantic_aware(
        records,
        metadata,
        buffer_anchor,
        thresholds,
        eval_episodes=eval_episodes,
        semantic_metric_weights=semantic_metric_weights,
    )
    evaluated_candidates = list(diagnostics["evaluated_candidates"])
    best_feasible_rate = max(float(entry["feasible_rate"]) for entry in evaluated_candidates)
    min_mean_violation = min(float(entry["mean_violation"]) for entry in evaluated_candidates)

    shortlist = [
        entry
        for entry in evaluated_candidates
        if float(entry["feasible_rate"]) >= best_feasible_rate - float(feasible_rate_tolerance)
        and float(entry["mean_violation"]) <= min_mean_violation + float(mean_violation_tolerance)
    ]
    if not shortlist:
        shortlist = evaluated_candidates

    best_security = max(float(entry["security_return"]) for entry in shortlist)
    security_shortlist = [
        entry
        for entry in shortlist
        if float(entry["security_return"]) >= best_security - float(security_margin)
    ]
    if not security_shortlist:
        security_shortlist = shortlist

    selected_entry = max(
        security_shortlist,
        key=lambda entry: (
            float(entry["security_return"]),
            -float(entry["semantic_risk"]),
            float(entry["feasible_rate"]),
            -float(entry["mean_violation"]),
        ),
    )
    policy_id = str(selected_entry["policy_id"])
    selected_record = next(record for record in records if record["policy_id"] == policy_id)
    diagnostics.update(
        {
            "selection_policy": "semantic_balanced",
            "security_margin": float(security_margin),
            "feasible_rate_tolerance": float(feasible_rate_tolerance),
            "mean_violation_tolerance": float(mean_violation_tolerance),
            "shortlist_policy_ids": [entry["policy_id"] for entry in shortlist],
            "security_shortlist_policy_ids": [
                entry["policy_id"] for entry in security_shortlist
            ],
        }
    )
    return selected_record, diagnostics


def _evaluate_actor_critic_record(
    checkpoint_path: str | Path | None,
    metadata: dict[str, Any],
    thresholds: dict[str, float],
    *,
    eval_episodes: int,
    baseline_kind: str | None = None,
) -> dict[str, Any]:
    env = _build_env_from_metadata(metadata)
    model_config = metadata.get("model", {})
    actor_critic = None
    if checkpoint_path is not None:
        actor_critic = ActorCritic(
            obs_dim=env.obs_dim,
            action_dim=env.action_dim,
            obj_dim=int(model_config.get("obj_dim", 3)),
            hidden_sizes=(
                int(model_config.get("hidden_size", 128)),
                int(model_config.get("hidden_size", 128)),
            ),
        ).to(torch.device("cpu"))
        checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
        actor_critic.load_state_dict(checkpoint)
        actor_critic.eval()

    totals = _empty_semantics()
    episode_vectors: list[list[float]] = []
    base_seed = int(metadata.get("env", {}).get("seed", 7))
    with torch.no_grad():
        for episode_idx in range(max(eval_episodes, 1)):
            env.seed = base_seed + episode_idx
            obs, _ = env.reset()
            done = np.zeros(env.num_envs, dtype=bool)
            returns = np.zeros((env.num_envs, env.obj_dim), dtype=np.float64)
            episode_semantics = {
                "critical_impact_count": np.zeros(env.num_envs, dtype=np.float64),
                "recovered_hosts": np.zeros(env.num_envs, dtype=np.float64),
                "analyse_count": np.zeros(env.num_envs, dtype=np.float64),
                "remove_count": np.zeros(env.num_envs, dtype=np.float64),
                "restore_count": np.zeros(env.num_envs, dtype=np.float64),
                "high_disruption_action_count": np.zeros(env.num_envs, dtype=np.float64),
                "total_action_count": np.zeros(env.num_envs, dtype=np.float64),
            }
            final_compromised_hosts = np.zeros(env.num_envs, dtype=np.float64)
            final_critical_compromised_hosts = np.zeros(env.num_envs, dtype=np.float64)

            while not np.all(done):
                if actor_critic is None:
                    if baseline_kind == "random_valid":
                        actions = _random_valid_actions(env).reshape(env.num_envs, 1)
                    else:
                        actions = _sleep_actions(env).reshape(env.num_envs, 1)
                else:
                    obs_tensor = torch.as_tensor(obs, dtype=torch.float32)
                    actions = (
                        actor_critic.act(obs_tensor)
                        .actions.cpu()
                        .numpy()
                        .reshape(env.num_envs, 1)
                    )
                obs, reward_vec, done, _, info = env.step(actions)
                returns += reward_vec
                semantic_info = info["semantic_info"]
                final_compromised_hosts = np.asarray(
                    semantic_info["final_compromised_hosts"], dtype=np.float64
                )
                final_critical_compromised_hosts = np.asarray(
                    semantic_info["final_critical_compromised_hosts"], dtype=np.float64
                )
                for key in episode_semantics:
                    episode_semantics[key] += np.asarray(semantic_info[key], dtype=np.float64)

            episode_vectors.extend(returns.tolist())
            totals["final_compromised_hosts"].extend(final_compromised_hosts.tolist())
            totals["final_critical_compromised_hosts"].extend(
                final_critical_compromised_hosts.tolist()
            )
            for key in episode_semantics:
                totals[key].extend(episode_semantics[key].tolist())

    vectors = np.asarray(episode_vectors, dtype=np.float32)
    business_violation = np.maximum(0.0, thresholds["d_business"] - vectors[:, 1])
    cost_violation = np.maximum(0.0, thresholds["d_cost"] - vectors[:, 2])
    feasible = (business_violation <= 1e-12) & (cost_violation <= 1e-12)
    semantic_metrics = _semantic_metrics(totals)
    return {
        "security_return": float(np.mean(vectors[:, 0])),
        "business_return": float(np.mean(vectors[:, 1])),
        "cost_return": float(np.mean(vectors[:, 2])),
        "feasible_rate": float(np.mean(feasible.astype(np.float32))),
        "mean_violation": float(np.mean(business_violation + cost_violation)),
        "thresholds": thresholds,
        **semantic_metrics,
    }


def evaluate_constraints(
    *,
    method_name: str,
    input_kind: str,
    input_path: str | Path,
    selection_source: str,
    selection_policy: str,
    thresholds_path: str | Path,
    eval_episodes: int,
    semantic_metric_weights: dict[str, float] | None = None,
    security_margin: float = 120.0,
    feasible_rate_tolerance: float = 0.10,
    mean_violation_tolerance: float = 0.50,
) -> dict[str, Any]:
    thresholds = _load_thresholds(thresholds_path)

    if input_kind == "buffer":
        payload = load_policy_buffer(input_path)
        if selection_source == "pareto":
            candidates = list(payload.get("pareto_front", []))
        elif selection_source == "records":
            candidates = list(payload.get("records", []))
        else:
            raise ValueError(f"Unsupported selection_source: {selection_source}")
        selection_diagnostics = None
        if selection_policy == "semantic_aware":
            selected, selection_diagnostics = _select_record_semantic_aware(
                candidates,
                payload.get("metadata", {}),
                input_path,
                thresholds,
                eval_episodes=eval_episodes,
                semantic_metric_weights=semantic_metric_weights or {},
            )
        elif selection_policy == "semantic_balanced":
            selected, selection_diagnostics = _select_record_semantic_balanced(
                candidates,
                payload.get("metadata", {}),
                input_path,
                thresholds,
                eval_episodes=eval_episodes,
                semantic_metric_weights=semantic_metric_weights or {},
                security_margin=security_margin,
                feasible_rate_tolerance=feasible_rate_tolerance,
                mean_violation_tolerance=mean_violation_tolerance,
            )
        else:
            selected = _select_record(candidates, thresholds)
        baseline_kind = selected.get("notes", {}).get("baseline_kind")
        metrics = _evaluate_actor_critic_record(
            (
                _resolve_path(input_path, selected["checkpoint_path"])
                if selected.get("checkpoint_path")
                else None
            ),
            payload.get("metadata", {}),
            thresholds,
            eval_episodes=eval_episodes,
            baseline_kind=baseline_kind,
        )
        result = {
            "schema_version": payload.get("schema_version", "0.1.0"),
            "method_name": method_name or payload.get("metadata", {}).get("stage", "buffer"),
            "input_kind": input_kind,
            "input_path": str(input_path),
            "selection_source": selection_source,
            "selection_policy": selection_policy,
            "selected_policy_id": selected["policy_id"],
            "selected_objective_vector": selected["objective_vector"],
            **metrics,
        }
        if selection_diagnostics is not None:
            result["selection_diagnostics"] = selection_diagnostics
        return result

    if input_kind == "single_policy":
        metadata = load_json(input_path)
        checkpoint_path = _resolve_path(input_path, metadata["checkpoint_path"])
        metrics = _evaluate_actor_critic_record(
            checkpoint_path,
            metadata,
            thresholds,
            eval_episodes=eval_episodes,
        )
        return {
            "schema_version": metadata.get("schema_version", "0.1.0"),
            "method_name": method_name or metadata.get("method_name", "single_policy"),
            "input_kind": input_kind,
            "input_path": str(input_path),
            "selection_source": selection_source,
            "selection_policy": selection_policy,
            "selected_policy_id": metadata.get("policy_id", "single_policy"),
            "selected_objective_vector": metadata.get("final_objective_vector"),
            **metrics,
        }

    raise ValueError(f"Unsupported input_kind: {input_kind}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate constrained deployment metrics.")
    subparsers = parser.add_subparsers(dest="command", required=False)

    build_parser = subparsers.add_parser("build-thresholds")
    build_parser.add_argument("--buffer-paths", nargs="+", required=True)
    build_parser.add_argument("--output-path", required=True)

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
    if args.output_path is not None:
        config.output_path = args.output_path
    if not config.input_path:
        raise ValueError("input_path must be provided")
    if not config.thresholds_path:
        raise ValueError("thresholds_path must be provided")

    result = evaluate_constraints(
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
    output_path = (
        Path(config.output_path)
        if config.output_path
        else Path(config.input_path).with_name("constraint_metrics.json")
    )
    save_json(output_path, result)
    print(f"Saved constraint evaluation to {output_path}")


if __name__ == "__main__":
    main()
