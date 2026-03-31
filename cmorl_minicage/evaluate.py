from __future__ import annotations

import argparse
import itertools
from pathlib import Path
from typing import Sequence

import numpy as np
import torch

from cmorl_minicage.algorithms.assignment import assign_policy
from cmorl_minicage.algorithms.selection import nondominated_filter
from cmorl_minicage.buffer import load_policy_buffer
from cmorl_minicage.config import DEFAULT_EVALUATE_CONFIG, load_evaluate_config
from cmorl_minicage.env import MiniCageMORLEnv
from cmorl_minicage.models import ActorCritic
from cmorl_minicage.utils import save_json, simplex_grid


def _repo_root_from_path(path: str | Path) -> Path:
    path = Path(path).resolve()
    for candidate in (path, *path.parents):
        if (candidate / "cmorl_minicage").exists():
            return candidate
    raise ValueError(f"Could not infer repository root from {path}")


def _prepare_hv_points(points: np.ndarray, reference_point: Sequence[float]) -> np.ndarray:
    reference = np.asarray(reference_point, dtype=np.float32)
    pts = np.asarray(points, dtype=np.float32)
    if pts.size == 0:
        return np.zeros((0, len(reference)), dtype=np.float32)
    pts = pts[np.all(pts > reference, axis=1)]
    if len(pts) == 0:
        return np.zeros((0, len(reference)), dtype=np.float32)
    pts = np.unique(pts, axis=0)

    keep = np.ones(len(pts), dtype=bool)
    for i in range(len(pts)):
        if not keep[i]:
            continue
        for j in range(len(pts)):
            if i == j:
                continue
            dominates = np.all(pts[j] >= pts[i]) and np.any(pts[j] > pts[i])
            if dominates:
                keep[i] = False
                break
    return pts[keep]


def _hypervolume_exact(points: np.ndarray, reference_point: Sequence[float]) -> float:
    reference = np.asarray(reference_point, dtype=np.float32)
    pts = _prepare_hv_points(points, reference)
    if len(pts) == 0:
        return 0.0

    volume = 0.0
    indices = range(len(pts))
    for subset_size in range(1, len(pts) + 1):
        sign = 1.0 if subset_size % 2 == 1 else -1.0
        for subset in itertools.combinations(indices, subset_size):
            upper = np.min(pts[list(subset)], axis=0)
            edge_lengths = upper - reference
            if np.any(edge_lengths <= 0):
                continue
            volume += sign * float(np.prod(edge_lengths))
    return volume


def _hypervolume_monte_carlo(
    points: np.ndarray, reference_point: Sequence[float], num_samples: int
) -> float:
    reference = np.asarray(reference_point, dtype=np.float32)
    pts = _prepare_hv_points(points, reference)
    if len(pts) == 0:
        return 0.0

    upper_bound = np.max(pts, axis=0)
    edge_lengths = upper_bound - reference
    if np.any(edge_lengths <= 0):
        return 0.0

    rng = np.random.default_rng(0)
    samples = rng.uniform(reference, upper_bound, size=(num_samples, pts.shape[1]))
    dominated = np.any(np.all(pts[:, None, :] >= samples[None, :, :], axis=2), axis=0)
    box_volume = float(np.prod(edge_lengths))
    return box_volume * float(np.mean(dominated))


def hypervolume(
    points: np.ndarray,
    reference_point: Sequence[float],
    *,
    max_exact_points: int = 18,
    mc_samples: int = 50000,
) -> tuple[float, str]:
    pts = np.asarray(points, dtype=np.float32)
    if len(pts) <= max_exact_points:
        return _hypervolume_exact(pts, reference_point), "exact_inclusion_exclusion"
    return _hypervolume_monte_carlo(pts, reference_point, mc_samples), "monte_carlo"


def resolve_reference_point(
    points: np.ndarray,
    *,
    obj_dim: int,
    reference_strategy: str,
    reference_margin: float,
    reference_point: Sequence[float] | None,
) -> np.ndarray:
    strategy = reference_strategy.lower()
    if reference_point:
        explicit = np.asarray(reference_point, dtype=np.float32)
        if explicit.shape != (obj_dim,):
            raise ValueError(
                f"reference_point must have length {obj_dim}, got {explicit.shape}"
            )
        return explicit

    if len(points) == 0:
        return np.full(obj_dim, -reference_margin, dtype=np.float32)

    point_min = points.min(axis=0)
    point_range = np.maximum(points.max(axis=0) - point_min, 1.0)

    if strategy == "data_min_margin":
        return (point_min - reference_margin).astype(np.float32)
    if strategy == "data_min_range":
        return (point_min - (reference_margin * point_range)).astype(np.float32)
    raise ValueError(f"Unsupported reference strategy: {reference_strategy}")


def expected_utility(records: Sequence[dict], preferences: Sequence[Sequence[float]]) -> float:
    if not preferences:
        return 0.0
    utilities = []
    for preference in preferences:
        assigned = assign_policy(preference, records)
        utilities.append(float(assigned["utility"]))
    return float(np.mean(utilities))


def sparsity(records: Sequence[dict]) -> float:
    if len(records) <= 1:
        return 0.0
    points = np.asarray([record["objective_vector"] for record in records], dtype=np.float32)
    total = 0.0
    for objective_idx in range(points.shape[1]):
        ordered = np.sort(points[:, objective_idx])
        diffs = np.diff(ordered)
        total += float(np.sum(diffs**2))
    return total / max(len(records) - 1, 1)


def _resolve_checkpoint_path(buffer_path: str | Path, checkpoint_path: str | Path) -> Path:
    checkpoint = Path(checkpoint_path)
    if checkpoint.is_absolute():
        return checkpoint
    return (_repo_root_from_path(buffer_path) / checkpoint).resolve()


def _sleep_actions(env: MiniCageMORLEnv) -> np.ndarray:
    return np.zeros(env.num_envs, dtype=np.int32)


def _random_valid_actions(env: MiniCageMORLEnv) -> np.ndarray:
    blue_mask = env.sim.get_mask(env.sim.state, env.sim.current_decoys)["Blue"]
    actions = np.zeros(env.num_envs, dtype=np.int32)
    for idx in range(env.num_envs):
        valid_actions = np.flatnonzero(blue_mask[idx] > 0)
        actions[idx] = int(np.random.choice(valid_actions))
    return actions


def _semantic_metrics_for_record(
    record: dict,
    metadata: dict,
    buffer_path: str | Path,
    *,
    eval_batches: int,
) -> dict[str, float]:
    env_config = metadata.get("env", {})
    model_config = metadata.get("model", {})
    env = MiniCageMORLEnv(
        num_envs=int(env_config.get("num_envs", 8)),
        red_policy=env_config.get("red_policy", "bline"),
        remove_bugs=bool(env_config.get("remove_bugs", True)),
        max_steps=int(env_config.get("max_episode_steps", 100)),
        seed=int(env_config.get("seed", 7)),
    )
    baseline_kind = record.get("notes", {}).get("baseline_kind")
    actor_critic = None
    if record.get("source") != "baseline_heuristic":
        actor_critic = ActorCritic(
            obs_dim=env.obs_dim,
            action_dim=env.action_dim,
            obj_dim=int(model_config.get("obj_dim", 3)),
            hidden_sizes=(int(model_config.get("hidden_size", 128)), int(model_config.get("hidden_size", 128))),
        ).to(torch.device("cpu"))
        checkpoint = torch.load(
            _resolve_checkpoint_path(buffer_path, record["checkpoint_path"]),
            map_location="cpu",
            weights_only=True,
        )
        actor_critic.load_state_dict(checkpoint)
        actor_critic.eval()

    totals: dict[str, list[float]] = {
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

    base_seed = int(env_config.get("seed", 7))
    with torch.no_grad():
        for batch_idx in range(max(eval_batches, 1)):
            env.seed = base_seed + batch_idx
            obs, _ = env.reset()
            done = np.zeros(env.num_envs, dtype=bool)
            episode_totals = {
                "critical_impact_count": np.zeros(env.num_envs, dtype=np.float32),
                "recovered_hosts": np.zeros(env.num_envs, dtype=np.float32),
                "analyse_count": np.zeros(env.num_envs, dtype=np.float32),
                "remove_count": np.zeros(env.num_envs, dtype=np.float32),
                "restore_count": np.zeros(env.num_envs, dtype=np.float32),
                "high_disruption_action_count": np.zeros(env.num_envs, dtype=np.float32),
                "total_action_count": np.zeros(env.num_envs, dtype=np.float32),
            }
            final_compromised_hosts = np.zeros(env.num_envs, dtype=np.float32)
            final_critical_compromised_hosts = np.zeros(env.num_envs, dtype=np.float32)

            while not np.all(done):
                if actor_critic is None:
                    if baseline_kind == "sleep":
                        actions = _sleep_actions(env).reshape(env.num_envs, 1)
                    elif baseline_kind == "random_valid":
                        actions = _random_valid_actions(env).reshape(env.num_envs, 1)
                    else:
                        raise ValueError(f"Unsupported baseline_kind: {baseline_kind}")
                else:
                    obs_tensor = torch.as_tensor(obs, dtype=torch.float32, device=torch.device("cpu"))
                    actions = actor_critic.act(obs_tensor).actions.cpu().numpy().reshape(env.num_envs, 1)
                obs, _, done, _, info = env.step(actions)
                semantic_info = info["semantic_info"]
                final_compromised_hosts = np.asarray(
                    semantic_info["final_compromised_hosts"], dtype=np.float32
                )
                final_critical_compromised_hosts = np.asarray(
                    semantic_info["final_critical_compromised_hosts"], dtype=np.float32
                )
                for key in episode_totals:
                    episode_totals[key] += np.asarray(semantic_info[key], dtype=np.float32)

            totals["final_compromised_hosts"].extend(final_compromised_hosts.tolist())
            totals["final_critical_compromised_hosts"].extend(
                final_critical_compromised_hosts.tolist()
            )
            for key in episode_totals:
                totals[key].extend(episode_totals[key].tolist())

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


def _assignment_weighted_semantic_metrics(
    assignment_counts: dict[str, int],
    per_policy_semantics: dict[str, dict[str, float]],
) -> dict[str, float]:
    if not assignment_counts or not per_policy_semantics:
        return {}
    weighted_metrics: dict[str, float] = {}
    total_weight = float(sum(assignment_counts.values()))
    metric_keys = [
        "final_compromised_hosts",
        "final_critical_compromised_hosts",
        "critical_impact_count",
        "recovered_hosts",
        "analyse_count",
        "remove_count",
        "restore_count",
        "high_disruption_action_rate",
    ]
    for key in metric_keys:
        weighted_metrics[key] = float(
            sum(
                assignment_counts[policy_id] * per_policy_semantics[policy_id][key]
                for policy_id in assignment_counts
                if policy_id in per_policy_semantics
            )
            / total_weight
        )
    return weighted_metrics


def evaluate_policy_buffer(
    buffer_path: str | Path,
    preference_step: float | None = None,
    *,
    reference_strategy: str = "data_min_margin",
    reference_margin: float = 1.0,
    reference_point: Sequence[float] | None = None,
    hv_max_exact_points: int = 18,
    hv_mc_samples: int = 50000,
    semantic_eval_batches: int | None = None,
) -> dict:
    payload = load_policy_buffer(buffer_path)
    records = payload["records"]
    pareto_records = nondominated_filter(records)
    if not records:
        raise ValueError("buffer contains no records")

    obj_dim = len(records[0]["objective_vector"])
    if preference_step is None:
        if obj_dim == 2:
            preference_step = 0.01
        elif obj_dim in (3, 4):
            preference_step = 0.1
        elif obj_dim in (6, 9):
            preference_step = 0.5
        else:
            preference_step = 0.1

    preferences = simplex_grid(preference_step, obj_dim)
    points = np.asarray([record["objective_vector"] for record in pareto_records], dtype=np.float32)
    reference = resolve_reference_point(
        points,
        obj_dim=obj_dim,
        reference_strategy=reference_strategy,
        reference_margin=reference_margin,
        reference_point=reference_point,
    )

    assignments = [assign_policy(pref, pareto_records) for pref in preferences]
    assignment_counts: dict[str, int] = {}
    assignment_utility_sum: dict[str, float] = {}
    for assigned in assignments:
        policy_id = assigned["policy_id"]
        assignment_counts[policy_id] = assignment_counts.get(policy_id, 0) + 1
        assignment_utility_sum[policy_id] = assignment_utility_sum.get(policy_id, 0.0) + float(
            assigned["utility"]
        )

    hv_value, hv_method = hypervolume(
        points,
        reference,
        max_exact_points=hv_max_exact_points,
        mc_samples=hv_mc_samples,
    )
    assignment_summary = {
        "num_preferences": len(preferences),
        "unique_assigned_policies": len(assignment_counts),
        "coverage_ratio": (
            float(len(assignment_counts) / len(pareto_records)) if pareto_records else 0.0
        ),
        "max_assignment_count": max(assignment_counts.values(), default=0),
        "mean_assignment_count": (
            float(np.mean(list(assignment_counts.values()))) if assignment_counts else 0.0
        ),
        "mean_assigned_utility": (
            float(np.mean([entry["utility"] for entry in assignments])) if assignments else 0.0
        ),
        "per_policy_mean_utility": {
            policy_id: assignment_utility_sum[policy_id] / assignment_counts[policy_id]
            for policy_id in assignment_counts
        },
    }
    if semantic_eval_batches is None:
        semantic_eval_batches = int(payload.get("metadata", {}).get("evaluation", {}).get("eval_episodes", 1))
    policy_lookup = {record["policy_id"]: record for record in records}
    assigned_policy_ids = sorted(assignment_counts)
    per_policy_semantic_metrics = {
        policy_id: _semantic_metrics_for_record(
            policy_lookup[policy_id],
            payload.get("metadata", {}),
            buffer_path,
            eval_batches=semantic_eval_batches,
        )
        for policy_id in assigned_policy_ids
        if policy_id in policy_lookup
    }
    semantic_metrics = _assignment_weighted_semantic_metrics(
        assignment_counts,
        per_policy_semantic_metrics,
    )
    metrics = {
        "num_records": len(records),
        "num_pareto_records": len(pareto_records),
        "hypervolume": hv_value,
        "hypervolume_method": hv_method,
        "expected_utility": expected_utility(pareto_records, preferences),
        "sparsity": sparsity(pareto_records),
        "reference_point": reference.tolist(),
        "reference_strategy": reference_strategy,
        "reference_margin": reference_margin,
        "preference_step": preference_step,
        "obj_dim": obj_dim,
        "semantic_eval_batches": semantic_eval_batches,
    }
    return {
        "schema_version": payload.get("schema_version"),
        "metadata": payload.get("metadata", {}),
        "metrics": metrics,
        "pareto_front": pareto_records,
        "assignments": assignments,
        "assignment_counts": assignment_counts,
        "assignment_summary": assignment_summary,
        "semantic_metrics": semantic_metrics,
        "semantic_policy_metrics": per_policy_semantic_metrics,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate C-MORL MiniCAGE policy buffer.")
    parser.add_argument("--config", default=str(DEFAULT_EVALUATE_CONFIG))
    parser.add_argument("--buffer-path", default=None)
    parser.add_argument("--preference-step", type=float, default=None)
    parser.add_argument("--output-path", default=None)
    args = parser.parse_args()

    config = load_evaluate_config(args.config)
    if args.buffer_path is not None:
        config.buffer_path = args.buffer_path
    if args.output_path is not None:
        config.output_path = args.output_path
    if args.preference_step is not None:
        config.preference_step = args.preference_step
    if not config.buffer_path:
        raise ValueError("buffer_path must be set via config file or --buffer-path")

    result = evaluate_policy_buffer(
        config.buffer_path,
        config.preference_step,
        reference_strategy=config.reference_strategy,
        reference_margin=config.reference_margin,
        reference_point=config.reference_point,
        hv_max_exact_points=config.hv_max_exact_points,
        hv_mc_samples=config.hv_mc_samples,
    )
    output_path = (
        Path(config.output_path)
        if config.output_path
        else Path(config.buffer_path).with_name("metrics.json")
    )
    save_json(output_path, result)
    print(f"Saved evaluation to {output_path}")


if __name__ == "__main__":
    main()
