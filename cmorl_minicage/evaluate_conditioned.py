from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import os
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import torch

from cmorl_minicage.algorithms.assignment import assign_policy
from cmorl_minicage.algorithms.selection import nondominated_filter
from cmorl_minicage.config import (
    DEFAULT_CONDITIONED_EVALUATE_CONFIG,
    load_conditioned_evaluate_config,
)
from cmorl_minicage.env import MiniCageMORLEnv
from cmorl_minicage.evaluate import hypervolume, resolve_reference_point, sparsity
from cmorl_minicage.models import PCNPolicy, PreferenceConditionedActorCritic
from cmorl_minicage.utils import load_json, save_json, simplex_grid


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


def _semantic_metric_keys() -> list[str]:
    return [
        "final_compromised_hosts",
        "final_critical_compromised_hosts",
        "critical_impact_count",
        "recovered_hosts",
        "analyse_count",
        "remove_count",
        "restore_count",
        "high_disruption_action_rate",
    ]


def _aggregate_semantics(
    assignment_counts: dict[str, int],
    per_point_semantics: dict[str, dict[str, float]],
) -> dict[str, float]:
    if not assignment_counts or not per_point_semantics:
        return {}
    total = float(sum(assignment_counts.values()))
    return {
        key: float(
            sum(
                assignment_counts[point_id] * per_point_semantics[point_id][key]
                for point_id in assignment_counts
                if point_id in per_point_semantics
            )
            / total
        )
        for key in _semantic_metric_keys()
    }


def _preferences_from_step(step: float | None, obj_dim: int) -> list[list[float]]:
    if step is None:
        step = 0.1
    return simplex_grid(float(step), obj_dim)


def _load_conditioned_payload(path: str | Path) -> dict[str, Any]:
    payload = load_json(path)
    if isinstance(payload, list):
        return {
            "schema_version": "0.1.0",
            "metadata": {},
            "evaluated_points": payload,
        }
    if "evaluated_points" not in payload:
        raise ValueError(f"Expected evaluated_points payload: {path}")
    return payload


def _load_run_metadata(path: str | Path) -> dict[str, Any]:
    payload = load_json(path)
    if "checkpoint_path" not in payload:
        raise ValueError(f"Invalid conditioned run metadata: {path}")
    return payload


def _load_model_and_env_from_metadata(
    run_metadata_path: str | Path,
    metadata: dict[str, Any],
    *,
    device: torch.device,
) -> tuple[str, Any, MiniCageMORLEnv, Path, np.ndarray | None]:
    env = _build_env(metadata)
    hidden_size = int(metadata.get("model", {}).get("hidden_size", 128))
    checkpoint_path = _resolve_path(run_metadata_path, metadata["checkpoint_path"])
    model_kind = metadata.get("model_type", "preference_conditioned_ppo")

    if model_kind == "preference_conditioned_ppo":
        model = PreferenceConditionedActorCritic(
            obs_dim=env.obs_dim,
            preference_dim=env.obj_dim,
            action_dim=env.action_dim,
            hidden_sizes=(hidden_size, hidden_size),
        ).to(device)
        checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=True)
        model.load_state_dict(checkpoint)
        model.eval()
        return model_kind, model, env, checkpoint_path, None

    if model_kind == "pcn":
        command_library_path = _resolve_path(run_metadata_path, metadata["command_library_path"])
        command_payload = load_json(command_library_path)
        command_returns = np.asarray(command_payload.get("command_returns", []), dtype=np.float32)
        model = PCNPolicy(
            obs_dim=env.obs_dim,
            command_dim=env.obj_dim,
            action_dim=env.action_dim,
            hidden_sizes=(hidden_size, hidden_size),
        ).to(device)
        checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=True)
        model.load_state_dict(checkpoint)
        model.eval()
        return model_kind, model, env, checkpoint_path, command_returns

    raise ValueError(f"Unsupported conditioned model_type: {model_kind}")


def _build_env(metadata: dict[str, Any]) -> MiniCageMORLEnv:
    env_config = metadata.get("env", {})
    return MiniCageMORLEnv(
        num_envs=int(env_config.get("num_envs", 8)),
        red_policy=env_config.get("red_policy", "bline"),
        remove_bugs=bool(env_config.get("remove_bugs", True)),
        max_steps=int(env_config.get("max_episode_steps", 100)),
        seed=int(env_config.get("seed", 7)),
    )


def _semantic_summary(totals: dict[str, list[float]]) -> dict[str, float]:
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


def _empty_semantic_totals() -> dict[str, list[float]]:
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


def _evaluate_pref_conditioned_point(
    model: PreferenceConditionedActorCritic,
    env: MiniCageMORLEnv,
    preference: Sequence[float],
    *,
    eval_batches: int,
    seed_offset: int,
    device: torch.device,
) -> tuple[np.ndarray, dict[str, float]]:
    returns = np.zeros(env.obj_dim, dtype=np.float64)
    base_seed = int(env.seed)
    totals = _empty_semantic_totals()
    preference_vec = np.asarray(preference, dtype=np.float32)

    with torch.no_grad():
        for batch_idx in range(max(eval_batches, 1)):
            env.seed = base_seed + seed_offset + batch_idx
            obs, _ = env.reset()
            done = np.zeros(env.num_envs, dtype=bool)
            episode_returns = np.zeros((env.num_envs, env.obj_dim), dtype=np.float64)
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
            preference_batch = np.repeat(preference_vec[None, :], env.num_envs, axis=0)

            while not np.all(done):
                obs_tensor = torch.as_tensor(obs, dtype=torch.float32, device=device)
                preference_tensor = torch.as_tensor(
                    preference_batch, dtype=torch.float32, device=device
                )
                actions = (
                    model.act(obs_tensor, preference_tensor)
                    .actions.cpu()
                    .numpy()
                    .reshape(env.num_envs, 1)
                )
                obs, reward_vec, done, _, info = env.step(actions)
                episode_returns += reward_vec
                semantic_info = info["semantic_info"]
                final_compromised_hosts = np.asarray(
                    semantic_info["final_compromised_hosts"], dtype=np.float64
                )
                final_critical_compromised_hosts = np.asarray(
                    semantic_info["final_critical_compromised_hosts"], dtype=np.float64
                )
                for key in episode_semantics:
                    episode_semantics[key] += np.asarray(semantic_info[key], dtype=np.float64)

            returns += episode_returns.mean(axis=0)
            totals["final_compromised_hosts"].extend(final_compromised_hosts.tolist())
            totals["final_critical_compromised_hosts"].extend(
                final_critical_compromised_hosts.tolist()
            )
            for key in episode_semantics:
                totals[key].extend(episode_semantics[key].tolist())

    returns /= max(eval_batches, 1)
    return returns.astype(np.float32), _semantic_summary(totals)


def _evaluate_pcn_point(
    model: PCNPolicy,
    env: MiniCageMORLEnv,
    preference: Sequence[float],
    *,
    command_returns: np.ndarray,
    eval_batches: int,
    seed_offset: int,
    device: torch.device,
) -> tuple[np.ndarray, dict[str, float], list[float]]:
    if len(command_returns) == 0:
        raise ValueError("PCN command library is empty")
    preference_vec = np.asarray(preference, dtype=np.float32)
    utility = command_returns @ preference_vec
    desired_return = command_returns[int(np.argmax(utility))].astype(np.float32)

    returns = np.zeros(env.obj_dim, dtype=np.float64)
    base_seed = int(env.seed)
    totals = _empty_semantic_totals()
    max_horizon = max(int(env.max_steps), 1)

    with torch.no_grad():
        for batch_idx in range(max(eval_batches, 1)):
            env.seed = base_seed + seed_offset + batch_idx
            obs, _ = env.reset()
            done = np.zeros(env.num_envs, dtype=bool)
            episode_returns = np.zeros((env.num_envs, env.obj_dim), dtype=np.float64)
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

            step_idx = 0
            while not np.all(done):
                obs_tensor = torch.as_tensor(obs, dtype=torch.float32, device=device)
                desired_batch = torch.as_tensor(
                    np.repeat(desired_return[None, :], env.num_envs, axis=0),
                    dtype=torch.float32,
                    device=device,
                )
                horizon_value = max(max_horizon - step_idx, 1) / max_horizon
                horizon_batch = torch.full(
                    (env.num_envs, 1),
                    float(horizon_value),
                    dtype=torch.float32,
                    device=device,
                )
                actions = (
                    model.act(obs_tensor, desired_batch, horizon_batch)
                    .cpu()
                    .numpy()
                    .reshape(env.num_envs, 1)
                )
                obs, reward_vec, done, _, info = env.step(actions)
                episode_returns += reward_vec
                semantic_info = info["semantic_info"]
                final_compromised_hosts = np.asarray(
                    semantic_info["final_compromised_hosts"], dtype=np.float64
                )
                final_critical_compromised_hosts = np.asarray(
                    semantic_info["final_critical_compromised_hosts"], dtype=np.float64
                )
                for key in episode_semantics:
                    episode_semantics[key] += np.asarray(semantic_info[key], dtype=np.float64)
                step_idx += 1

            returns += episode_returns.mean(axis=0)
            totals["final_compromised_hosts"].extend(final_compromised_hosts.tolist())
            totals["final_critical_compromised_hosts"].extend(
                final_critical_compromised_hosts.tolist()
            )
            for key in episode_semantics:
                totals[key].extend(episode_semantics[key].tolist())

    returns /= max(eval_batches, 1)
    return returns.astype(np.float32), _semantic_summary(totals), desired_return.tolist()


def _evaluate_conditioned_preference_task(task: dict[str, Any]) -> dict[str, Any]:
    run_metadata_path = task["run_metadata_path"]
    metadata = task["metadata"]
    preference = task["preference"]
    pref_idx = int(task["pref_idx"])
    preference_step = float(task["preference_step"])
    eval_episodes = int(task["eval_episodes"])

    device = torch.device("cpu")
    model_kind, model, env, checkpoint_path, command_returns = _load_model_and_env_from_metadata(
        run_metadata_path,
        metadata,
        device=device,
    )

    if model_kind == "preference_conditioned_ppo":
        objective_vector, semantic_metrics = _evaluate_pref_conditioned_point(
            model,
            env,
            preference,
            eval_batches=eval_episodes,
            seed_offset=pref_idx * 1000,
            device=device,
        )
        return {
            "policy_id": f"evaluated_pref_{pref_idx:03d}",
            "checkpoint_path": str(checkpoint_path),
            "preference": list(map(float, preference)),
            "objective_vector": objective_vector.tolist(),
            "utility": float(np.dot(np.asarray(preference, dtype=np.float32), objective_vector)),
            "stage": "conditioned_eval",
            "source": model_kind,
            "semantic_metrics": semantic_metrics,
            "pref_idx": pref_idx,
            "preference_step": preference_step,
        }

    objective_vector, semantic_metrics, desired_return = _evaluate_pcn_point(
        model,
        env,
        preference,
        command_returns=command_returns if command_returns is not None else np.empty((0,)),
        eval_batches=eval_episodes,
        seed_offset=pref_idx * 1000,
        device=device,
    )
    return {
        "policy_id": f"evaluated_pref_{pref_idx:03d}",
        "checkpoint_path": str(checkpoint_path),
        "preference": list(map(float, preference)),
        "objective_vector": objective_vector.tolist(),
        "utility": float(np.dot(np.asarray(preference, dtype=np.float32), objective_vector)),
        "stage": "conditioned_eval",
        "source": model_kind,
        "desired_return": desired_return,
        "semantic_metrics": semantic_metrics,
        "pref_idx": pref_idx,
        "preference_step": preference_step,
    }


def evaluate_conditioned_points_payload(
    payload: dict[str, Any],
    *,
    preference_step: float | None,
    reference_strategy: str,
    reference_margin: float,
    reference_point: Sequence[float] | None,
    hv_max_exact_points: int,
    hv_mc_samples: int,
) -> dict[str, Any]:
    points = [dict(entry) for entry in payload.get("evaluated_points", [])]
    if not points:
        raise ValueError("conditioned payload contains no evaluated points")

    pareto_front = nondominated_filter(points)
    obj_dim = len(points[0]["objective_vector"])
    preferences = _preferences_from_step(preference_step, obj_dim)
    point_array = np.asarray(
        [record["objective_vector"] for record in pareto_front], dtype=np.float32
    )
    reference = resolve_reference_point(
        point_array,
        obj_dim=obj_dim,
        reference_strategy=reference_strategy,
        reference_margin=reference_margin,
        reference_point=reference_point,
    )

    assignments = [assign_policy(pref, pareto_front) for pref in preferences]
    assignment_counts: dict[str, int] = {}
    assignment_utility_sum: dict[str, float] = {}
    for assigned in assignments:
        point_id = assigned["policy_id"]
        assignment_counts[point_id] = assignment_counts.get(point_id, 0) + 1
        assignment_utility_sum[point_id] = assignment_utility_sum.get(point_id, 0.0) + float(
            assigned["utility"]
        )

    hv_value, hv_method = hypervolume(
        point_array,
        reference,
        max_exact_points=hv_max_exact_points,
        mc_samples=hv_mc_samples,
    )
    per_point_semantics = {
        entry["policy_id"]: dict(entry.get("semantic_metrics", {})) for entry in points
    }
    assignment_summary = {
        "num_preferences": len(preferences),
        "unique_assigned_policies": len(assignment_counts),
        "coverage_ratio": (
            float(len(assignment_counts) / len(pareto_front)) if pareto_front else 0.0
        ),
        "max_assignment_count": max(assignment_counts.values(), default=0),
        "mean_assignment_count": (
            float(np.mean(list(assignment_counts.values()))) if assignment_counts else 0.0
        ),
        "mean_assigned_utility": (
            float(np.mean([entry["utility"] for entry in assignments])) if assignments else 0.0
        ),
        "per_policy_mean_utility": {
            point_id: assignment_utility_sum[point_id] / assignment_counts[point_id]
            for point_id in assignment_counts
        },
    }
    metrics = {
        "num_records": len(points),
        "num_pareto_records": len(pareto_front),
        "hypervolume": hv_value,
        "hypervolume_method": hv_method,
        "expected_utility": float(
            np.mean([float(entry.get("utility", 0.0)) for entry in points])
        ),
        "sparsity": sparsity(pareto_front),
        "reference_point": reference.tolist(),
        "reference_strategy": reference_strategy,
        "reference_margin": reference_margin,
        "preference_step": preference_step,
        "obj_dim": obj_dim,
        "semantic_eval_batches": int(
            payload.get("metadata", {}).get("evaluation", {}).get("eval_episodes", 1)
        ),
    }
    return {
        "schema_version": payload.get("schema_version", "0.1.0"),
        "metadata": payload.get("metadata", {}),
        "metrics": metrics,
        "pareto_front": pareto_front,
        "assignments": assignments,
        "assignment_counts": assignment_counts,
        "assignment_summary": assignment_summary,
        "semantic_metrics": _aggregate_semantics(assignment_counts, per_point_semantics),
        "semantic_policy_metrics": per_point_semantics,
    }


def evaluate_conditioned_model(
    run_metadata_path: str | Path,
    *,
    preference_step: float | None,
    reference_strategy: str,
    reference_margin: float,
    reference_point: Sequence[float] | None,
    hv_max_exact_points: int,
    hv_mc_samples: int,
    eval_episodes: int,
    preference_eval_workers: int | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    metadata = _load_run_metadata(run_metadata_path)
    env = _build_env(metadata)
    preferences = _preferences_from_step(preference_step, env.obj_dim)
    model_kind = metadata.get("model_type", "preference_conditioned_ppo")
    seed = int(metadata.get("env", {}).get("seed", 0))
    preference_eval_workers = int(
        preference_eval_workers
        if preference_eval_workers is not None
        else os.environ.get("CMORL_CONDITIONED_PREF_WORKERS", "1")
    )
    preference_eval_workers = max(preference_eval_workers, 1)

    print(
        f"[conditioned-eval] START model={model_kind} seed={seed} "
        f"preferences={len(preferences)} eval_episodes={eval_episodes} "
        f"workers={preference_eval_workers}",
        flush=True,
    )

    evaluated_points: list[dict[str, Any]] = []
    if preference_eval_workers == 1 or len(preferences) <= 1:
        device = torch.device("cpu")
        resolved_kind, model, env, checkpoint_path, command_returns = _load_model_and_env_from_metadata(
            run_metadata_path,
            metadata,
            device=device,
        )
        if resolved_kind == "preference_conditioned_ppo":
            for pref_idx, preference in enumerate(preferences):
                objective_vector, semantic_metrics = _evaluate_pref_conditioned_point(
                    model,
                    env,
                    preference,
                    eval_batches=eval_episodes,
                    seed_offset=pref_idx * 1000,
                    device=device,
                )
                evaluated_points.append(
                    {
                        "policy_id": f"evaluated_pref_{pref_idx:03d}",
                        "checkpoint_path": str(checkpoint_path),
                        "preference": list(map(float, preference)),
                        "objective_vector": objective_vector.tolist(),
                        "utility": float(
                            np.dot(np.asarray(preference, dtype=np.float32), objective_vector)
                        ),
                        "stage": "conditioned_eval",
                        "source": resolved_kind,
                        "semantic_metrics": semantic_metrics,
                    }
                )
                print(
                    f"[conditioned-eval] RUN model={resolved_kind} seed={seed} "
                    f"{pref_idx + 1}/{len(preferences)}",
                    flush=True,
                )
        elif resolved_kind == "pcn":
            for pref_idx, preference in enumerate(preferences):
                objective_vector, semantic_metrics, desired_return = _evaluate_pcn_point(
                    model,
                    env,
                    preference,
                    command_returns=command_returns if command_returns is not None else np.empty((0,)),
                    eval_batches=eval_episodes,
                    seed_offset=pref_idx * 1000,
                    device=device,
                )
                evaluated_points.append(
                    {
                        "policy_id": f"evaluated_pref_{pref_idx:03d}",
                        "checkpoint_path": str(checkpoint_path),
                        "preference": list(map(float, preference)),
                        "objective_vector": objective_vector.tolist(),
                        "utility": float(
                            np.dot(np.asarray(preference, dtype=np.float32), objective_vector)
                        ),
                        "stage": "conditioned_eval",
                        "source": resolved_kind,
                        "desired_return": desired_return,
                        "semantic_metrics": semantic_metrics,
                    }
                )
                print(
                    f"[conditioned-eval] RUN model={resolved_kind} seed={seed} "
                    f"{pref_idx + 1}/{len(preferences)}",
                    flush=True,
                )
        else:
            raise ValueError(f"Unsupported conditioned model_type: {resolved_kind}")
    else:
        max_workers = min(preference_eval_workers, len(preferences))
        tasks = [
            {
                "run_metadata_path": str(run_metadata_path),
                "metadata": metadata,
                "preference": preference,
                "pref_idx": pref_idx,
                "preference_step": preference_step if preference_step is not None else 0.1,
                "eval_episodes": eval_episodes,
            }
            for pref_idx, preference in enumerate(preferences)
        ]
        completed = 0
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(_evaluate_conditioned_preference_task, task)
                for task in tasks
            ]
            for future in as_completed(futures):
                result = future.result()
                completed += 1
                pref_idx = int(result.pop("pref_idx"))
                result.pop("preference_step", None)
                evaluated_points.append((pref_idx, result))
                print(
                    f"[conditioned-eval] RUN model={model_kind} seed={seed} "
                    f"{completed}/{len(preferences)}",
                    flush=True,
                )
        evaluated_points = [
            entry for _, entry in sorted(evaluated_points, key=lambda item: item[0])
        ]

    points_payload = {
        "schema_version": metadata.get("schema_version", "0.1.0"),
        "metadata": metadata,
        "evaluated_points": evaluated_points,
    }
    metrics_payload = evaluate_conditioned_points_payload(
        points_payload,
        preference_step=preference_step,
        reference_strategy=reference_strategy,
        reference_margin=reference_margin,
        reference_point=reference_point,
        hv_max_exact_points=hv_max_exact_points,
        hv_mc_samples=hv_mc_samples,
    )
    print(
        f"[conditioned-eval] DONE model={model_kind} seed={seed} "
        f"pareto={len(metrics_payload.get('pareto_front', []))} "
        f"records={len(evaluated_points)}",
        flush=True,
    )
    return points_payload, metrics_payload


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate a conditioned policy family on a preference grid."
    )
    parser.add_argument("--config", default=str(DEFAULT_CONDITIONED_EVALUATE_CONFIG))
    parser.add_argument("--input-path", default=None)
    parser.add_argument("--input-kind", choices=("run_metadata", "evaluated_points"), default=None)
    parser.add_argument("--output-path", default=None)
    args = parser.parse_args()

    config = load_conditioned_evaluate_config(args.config)
    if args.input_path is not None:
        config.input_path = args.input_path
    if args.input_kind is not None:
        config.input_kind = args.input_kind
    if args.output_path is not None:
        config.output_path = args.output_path
    if not config.input_path:
        raise ValueError("input_path must be provided")

    if config.input_kind == "run_metadata":
        points_payload, metrics_payload = evaluate_conditioned_model(
            config.input_path,
            preference_step=config.preference_step,
            reference_strategy=config.reference_strategy,
            reference_margin=config.reference_margin,
            reference_point=config.reference_point,
            hv_max_exact_points=config.hv_max_exact_points,
            hv_mc_samples=config.hv_mc_samples,
            eval_episodes=config.eval_episodes,
        )
        base_dir = Path(config.output_path).parent if config.output_path else Path(config.input_path).resolve().parent
        evaluated_points_path = base_dir / "evaluated_points.json"
        pareto_front_path = base_dir / "pareto_front_conditioned.json"
        metrics_path = (
            Path(config.output_path) if config.output_path else base_dir / "metrics.json"
        )
        save_json(evaluated_points_path, points_payload)
        save_json(pareto_front_path, metrics_payload["pareto_front"])
        save_json(metrics_path, metrics_payload)
        print(f"Saved conditioned evaluation to {metrics_path}")
        return

    payload = _load_conditioned_payload(config.input_path)
    metrics_payload = evaluate_conditioned_points_payload(
        payload,
        preference_step=config.preference_step,
        reference_strategy=config.reference_strategy,
        reference_margin=config.reference_margin,
        reference_point=config.reference_point,
        hv_max_exact_points=config.hv_max_exact_points,
        hv_mc_samples=config.hv_mc_samples,
    )
    output_path = (
        Path(config.output_path)
        if config.output_path
        else Path(config.input_path).with_name("metrics.json")
    )
    save_json(output_path, metrics_payload)
    print(f"Saved conditioned metrics to {output_path}")


if __name__ == "__main__":
    main()
