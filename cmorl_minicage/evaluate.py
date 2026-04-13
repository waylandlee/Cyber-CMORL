from __future__ import annotations

import argparse
import itertools
from pathlib import Path
from typing import Sequence

import numpy as np
import torch

from cmorl_minicage.algorithms.assignment import (
    assign_policy,
    assign_policy_hybrid,
    assign_policy_strict,
)
from cmorl_minicage.algorithms.dual_archive import normalized_archive_sets
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


def _dedupe_by_policy_id(records: Sequence[dict]) -> list[dict]:
    by_id: dict[str, dict] = {}
    for record in records:
        by_id.setdefault(str(record["policy_id"]), dict(record))
    return list(by_id.values())


def _archive_sets(
    payload: dict,
    *,
    buffer_path: str | Path,
    semantic_eval_batches: int,
) -> dict[str, list[dict]]:
    metadata = payload.get("metadata", {})
    return normalized_archive_sets(
        payload,
        buffer_path=buffer_path,
        cons_thresholds=metadata.get("cons_thresholds", None),
        uc_thresholds=metadata.get("uc_thresholds", None),
        selector_penalty_weights=(
            metadata.get("selector_defaults", {}) or {}
        ).get("penalty_weights", None),
        semantic_eval_episodes=semantic_eval_batches,
    )


def _preference_grid(preference_step: float | None, obj_dim: int) -> tuple[list[list[float]], float]:
    if preference_step is None:
        if obj_dim == 2:
            preference_step = 0.01
        elif obj_dim in (3, 4):
            preference_step = 0.1
        elif obj_dim in (6, 9):
            preference_step = 0.5
        else:
            preference_step = 0.1
    return simplex_grid(float(preference_step), obj_dim), float(preference_step)


def _record_metric(record: dict, *keys: str, default: float = 0.0) -> float:
    for key in keys:
        value = record.get(key)
        if value is not None:
            return float(value)
    return float(default)


def _selected_objective_summary(assignments: Sequence[dict]) -> dict[str, float]:
    selected = [assignment for assignment in assignments if assignment.get("policy_id") is not None]
    if not selected:
        return {
            "selected_count": 0,
            "security_return": 0.0,
            "business_return": 0.0,
            "cost_return": 0.0,
            "mean_violation": 0.0,
            "final_critical_compromised": 0.0,
            "final_critical_compromised_hosts": 0.0,
            "critical_impact_count": 0.0,
            "high_disruption_rate": 0.0,
            "high_disruption_action_rate": 0.0,
            "selected_utility": 0.0,
            "selected_penalized_utility": 0.0,
        }
    vectors = [np.asarray(entry["objective_vector"], dtype=np.float32) for entry in selected]
    utilities = [
        float(entry["utility"])
        for entry in selected
        if entry.get("utility") is not None
    ]
    penalized = [
        float(entry["penalized_utility"])
        for entry in selected
        if entry.get("penalized_utility") is not None
    ]
    return {
        "selected_count": len(selected),
        "security_return": float(np.mean([vector[0] for vector in vectors])) if vectors and vectors[0].size >= 1 else 0.0,
        "business_return": float(np.mean([vector[1] for vector in vectors])) if vectors and vectors[0].size >= 2 else 0.0,
        "cost_return": float(np.mean([vector[2] for vector in vectors])) if vectors and vectors[0].size >= 3 else 0.0,
        "mean_violation": float(np.mean([_record_metric(entry, "mean_violation") for entry in selected])),
        "final_critical_compromised": float(
            np.mean(
                [
                    _record_metric(
                        entry,
                        "final_critical_compromised",
                        "final_critical_compromised_hosts",
                    )
                    for entry in selected
                ]
            )
        ),
        "final_critical_compromised_hosts": float(
            np.mean(
                [
                    _record_metric(
                        entry,
                        "final_critical_compromised_hosts",
                        "final_critical_compromised",
                    )
                    for entry in selected
                ]
            )
        ),
        "critical_impact_count": float(
            np.mean([_record_metric(entry, "critical_impact_count") for entry in selected])
        ),
        "high_disruption_rate": float(
            np.mean(
                [
                    _record_metric(
                        entry,
                        "high_disruption_rate",
                        "high_disruption_action_rate",
                    )
                    for entry in selected
                ]
            )
        ),
        "high_disruption_action_rate": float(
            np.mean(
                [
                    _record_metric(
                        entry,
                        "high_disruption_action_rate",
                        "high_disruption_rate",
                    )
                    for entry in selected
                ]
            )
        ),
        "selected_utility": float(np.mean(utilities)) if utilities else 0.0,
        "selected_penalized_utility": float(np.mean(penalized)) if penalized else 0.0,
    }


def _assignment_counts(assignments: Sequence[dict]) -> tuple[dict[str, int], dict[str, float]]:
    assignment_counts: dict[str, int] = {}
    assignment_utility_sum: dict[str, float] = {}
    for assigned in assignments:
        policy_id = assigned.get("policy_id")
        if policy_id is None:
            continue
        assignment_counts[policy_id] = assignment_counts.get(policy_id, 0) + 1
        assignment_utility_sum[policy_id] = assignment_utility_sum.get(policy_id, 0.0) + float(
            assigned.get("utility") or 0.0
        )
    return assignment_counts, assignment_utility_sum


def _semantic_payload_for_assignments(
    *,
    assignments: Sequence[dict],
    records: Sequence[dict],
    metadata: dict,
    buffer_path: str | Path,
    semantic_eval_batches: int,
) -> tuple[dict[str, float], dict[str, dict[str, float]]]:
    assignment_counts, _ = _assignment_counts(assignments)
    policy_lookup = {record["policy_id"]: record for record in records}
    per_policy_semantic_metrics = {
        policy_id: _semantic_metrics_for_record(
            policy_lookup[policy_id],
            metadata,
            buffer_path,
            eval_batches=semantic_eval_batches,
        )
        for policy_id in sorted(assignment_counts)
        if policy_id in policy_lookup
    }
    return (
        _assignment_weighted_semantic_metrics(assignment_counts, per_policy_semantic_metrics),
        per_policy_semantic_metrics,
    )


def _evaluate_union_mode(
    *,
    payload: dict,
    archive_sets: dict[str, list[dict]],
    buffer_path: str | Path,
    preferences: Sequence[Sequence[float]],
    preference_step: float,
    reference_strategy: str,
    reference_margin: float,
    reference_point: Sequence[float] | None,
    hv_max_exact_points: int,
    hv_mc_samples: int,
    semantic_eval_batches: int,
) -> dict:
    records = archive_sets["records"]
    pareto_records = nondominated_filter(archive_sets["union"])
    if archive_sets["union_front"]:
        pareto_records = nondominated_filter(archive_sets["union_front"])
    obj_dim = len(records[0]["objective_vector"])
    points = np.asarray([record["objective_vector"] for record in pareto_records], dtype=np.float32)
    reference = resolve_reference_point(
        points,
        obj_dim=obj_dim,
        reference_strategy=reference_strategy,
        reference_margin=reference_margin,
        reference_point=reference_point,
    )
    assignments = [assign_policy(pref, pareto_records, mode="plain", source_set="union") for pref in preferences]
    assignment_counts, assignment_utility_sum = _assignment_counts(assignments)
    hv_value, hv_method = hypervolume(
        points,
        reference,
        max_exact_points=hv_max_exact_points,
        mc_samples=hv_mc_samples,
    )
    assignment_summary = {
        "mode": "union",
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
    semantic_metrics, per_policy_semantic_metrics = _semantic_payload_for_assignments(
        assignments=assignments,
        records=records,
        metadata=payload.get("metadata", {}),
        buffer_path=buffer_path,
        semantic_eval_batches=semantic_eval_batches,
    )
    metrics = {
        "mode": "union",
        "num_records": len(records),
        "num_pareto_records": len(pareto_records),
        "num_cons_records": len(archive_sets["cons"]),
        "num_uc_records": len(archive_sets["uc"]),
        "num_union_records": len(archive_sets["union"]),
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
        "evaluation_mode": "union",
        "metrics": metrics,
        "pareto_front": pareto_records,
        "assignments": assignments,
        "assignment_counts": assignment_counts,
        "assignment_summary": assignment_summary,
        "semantic_metrics": semantic_metrics,
        "semantic_policy_metrics": per_policy_semantic_metrics,
    }


def _evaluate_deployment_mode(
    *,
    payload: dict,
    archive_sets: dict[str, list[dict]],
    buffer_path: str | Path,
    preferences: Sequence[Sequence[float]],
    preference_step: float,
    mode: str,
    penalty_weights: dict[str, float] | None,
    strict_require_tight: bool,
    semantic_eval_batches: int,
) -> dict:
    records = archive_sets["records"]
    cons_records = archive_sets["cons"]
    union_records = archive_sets["union"]
    if mode == "strict":
        assignments = [
            assign_policy_strict(
                pref,
                cons_records,
                require_tight=strict_require_tight,
                source_set="cons",
            )
            for pref in preferences
        ]
    elif mode == "hybrid":
        assignments = [
            assign_policy_hybrid(
                pref,
                cons_records,
                union_records,
                penalty_weights=penalty_weights,
                require_tight=strict_require_tight,
            )
            for pref in preferences
        ]
    else:
        raise ValueError(f"Unsupported deployment evaluation mode: {mode}")

    assignment_counts, assignment_utility_sum = _assignment_counts(assignments)
    selected_count = sum(1 for assignment in assignments if assignment.get("policy_id") is not None)
    strict_hit_count = sum(1 for assignment in assignments if assignment.get("strict_hit") is True)
    fallback_count = sum(1 for assignment in assignments if assignment.get("fallback_used") is True)
    miss_count = len(preferences) - selected_count
    selected_summary = _selected_objective_summary(assignments)
    semantic_metrics, per_policy_semantic_metrics = _semantic_payload_for_assignments(
        assignments=assignments,
        records=records,
        metadata=payload.get("metadata", {}),
        buffer_path=buffer_path,
        semantic_eval_batches=semantic_eval_batches,
    )
    deployment_summary = {
        "mode": mode,
        "num_preferences": len(preferences),
        "selected_count": selected_count,
        "strict_hit_count": strict_hit_count,
        "strict_miss_count": len(preferences) - strict_hit_count,
        "fallback_count": fallback_count,
        "miss_count": miss_count,
        "strict_hit_rate": float(strict_hit_count / len(preferences)) if preferences else 0.0,
        "hybrid_fallback_rate": float(fallback_count / len(preferences)) if preferences else 0.0,
        "selection_rate": float(selected_count / len(preferences)) if preferences else 0.0,
        "strict_require_tight": bool(strict_require_tight),
        **selected_summary,
    }
    assignment_summary = {
        "mode": mode,
        "num_preferences": len(preferences),
        "unique_assigned_policies": len(assignment_counts),
        "coverage_ratio": (
            float(len(assignment_counts) / len(cons_records if mode == "strict" else union_records))
            if (cons_records if mode == "strict" else union_records)
            else 0.0
        ),
        "max_assignment_count": max(assignment_counts.values(), default=0),
        "mean_assignment_count": (
            float(np.mean(list(assignment_counts.values()))) if assignment_counts else 0.0
        ),
        "mean_assigned_utility": deployment_summary["selected_utility"],
        "per_policy_mean_utility": {
            policy_id: assignment_utility_sum[policy_id] / assignment_counts[policy_id]
            for policy_id in assignment_counts
        },
    }
    metrics = {
        "mode": mode,
        "num_records": len(records),
        "num_cons_records": len(cons_records),
        "num_uc_records": len(archive_sets["uc"]),
        "num_union_records": len(union_records),
        "preference_step": preference_step,
        "obj_dim": len(records[0]["objective_vector"]),
        "semantic_eval_batches": semantic_eval_batches,
        **deployment_summary,
    }
    return {
        "schema_version": payload.get("schema_version"),
        "metadata": payload.get("metadata", {}),
        "evaluation_mode": mode,
        "metrics": metrics,
        "deployment_summary": deployment_summary,
        "assignments": assignments,
        "assignment_counts": assignment_counts,
        "assignment_summary": assignment_summary,
        "semantic_metrics": semantic_metrics,
        "semantic_policy_metrics": per_policy_semantic_metrics,
    }


def evaluate_policy_buffer(
    buffer_path: str | Path,
    preference_step: float | None = None,
    *,
    mode: str = "union",
    penalty_weights: dict[str, float] | None = None,
    strict_require_tight: bool = False,
    reference_strategy: str = "data_min_margin",
    reference_margin: float = 1.0,
    reference_point: Sequence[float] | None = None,
    hv_max_exact_points: int = 18,
    hv_mc_samples: int = 50000,
    semantic_eval_batches: int | None = None,
) -> dict:
    payload = load_policy_buffer(buffer_path)
    if semantic_eval_batches is None:
        semantic_eval_batches = int(payload.get("metadata", {}).get("evaluation", {}).get("eval_episodes", 1))
    archive_sets = _archive_sets(
        payload,
        buffer_path=buffer_path,
        semantic_eval_batches=semantic_eval_batches,
    )
    records = archive_sets["records"]
    if not records:
        raise ValueError("buffer contains no records")
    obj_dim = len(records[0]["objective_vector"])
    preferences, preference_step = _preference_grid(preference_step, obj_dim)
    mode = mode.lower()
    if mode == "union":
        return _evaluate_union_mode(
            payload=payload,
            archive_sets=archive_sets,
            buffer_path=buffer_path,
            preferences=preferences,
            preference_step=preference_step,
            reference_strategy=reference_strategy,
            reference_margin=reference_margin,
            reference_point=reference_point,
            hv_max_exact_points=hv_max_exact_points,
            hv_mc_samples=hv_mc_samples,
            semantic_eval_batches=semantic_eval_batches,
        )
    if mode in {"strict", "hybrid"}:
        return _evaluate_deployment_mode(
            payload=payload,
            archive_sets=archive_sets,
            buffer_path=buffer_path,
            preferences=preferences,
            preference_step=preference_step,
            mode=mode,
            penalty_weights=penalty_weights,
            strict_require_tight=strict_require_tight,
            semantic_eval_batches=semantic_eval_batches,
        )
    raise ValueError(f"Unsupported evaluation mode: {mode}")


def evaluate_policy_buffer_all_modes(
    buffer_path: str | Path,
    preference_step: float | None = None,
    *,
    penalty_weights: dict[str, float] | None = None,
    strict_require_tight: bool = False,
    reference_strategy: str = "data_min_margin",
    reference_margin: float = 1.0,
    reference_point: Sequence[float] | None = None,
    hv_max_exact_points: int = 18,
    hv_mc_samples: int = 50000,
    semantic_eval_batches: int | None = None,
) -> dict[str, dict]:
    return {
        mode: evaluate_policy_buffer(
            buffer_path,
            preference_step,
            mode=mode,
            penalty_weights=penalty_weights,
            strict_require_tight=strict_require_tight,
            reference_strategy=reference_strategy,
            reference_margin=reference_margin,
            reference_point=reference_point,
            hv_max_exact_points=hv_max_exact_points,
            hv_mc_samples=hv_mc_samples,
            semantic_eval_batches=semantic_eval_batches,
        )
        for mode in ("union", "strict", "hybrid")
    }


def archive_diagnostics_payload(
    buffer_path: str | Path,
    *,
    strict_payload: dict | None = None,
    hybrid_payload: dict | None = None,
) -> dict:
    payload = load_policy_buffer(buffer_path)
    semantic_eval_batches = int(
        payload.get("metadata", {}).get("evaluation", {}).get("eval_episodes", 1)
    )
    archive_sets = _archive_sets(
        payload,
        buffer_path=buffer_path,
        semantic_eval_batches=semantic_eval_batches,
    )
    records = archive_sets["records"]
    route_counts = {
        "from_original_to_cons": 0,
        "from_original_to_uc": 0,
        "from_adacs_to_cons": 0,
        "from_adacs_to_uc": 0,
        "from_unknown_to_cons": 0,
        "from_unknown_to_uc": 0,
    }
    for record in records:
        operator = record.get("operator_source")
        role = record.get("archive_role")
        if role not in {"cons", "uc"}:
            continue
        operator_key = "unknown"
        if operator == "original":
            operator_key = "original"
        elif operator == "adacs_dcs":
            operator_key = "adacs"
        key = f"from_{operator_key}_to_{role}"
        route_counts[key] = route_counts.get(key, 0) + 1

    strict_candidates = [
        record
        for record in archive_sets["cons"]
        if bool(record.get("tight_feasible_flag")) or bool(record.get("near_feasible_flag"))
    ]
    metadata = payload.get("metadata", {})
    shadow_keys = (
        "saved_route_preview_cons_accept_count",
        "shadow_route_preview_cons_accept_count",
        "saved_route_preview_near_feasible_count",
        "shadow_route_preview_near_feasible_count",
        "saved_route_fail_primary_counts",
        "shadow_route_fail_primary_counts",
        "saved_route_fail_component_counts",
        "shadow_route_fail_component_counts",
        "saved_final_critical_threshold_counts",
        "shadow_final_critical_threshold_counts",
        "saved_final_critical_value_summary",
        "shadow_final_critical_value_summary",
        "saved_objective_delta_vs_parent_summary",
        "shadow_objective_delta_vs_parent_summary",
        "saved_spread_gain_summary",
        "shadow_spread_gain_summary",
        "gap_direction_summary",
    )
    shadow_available = any(key in metadata for key in shadow_keys)
    strict_summary = (strict_payload or {}).get("deployment_summary", {})
    hybrid_summary = (hybrid_payload or {}).get("deployment_summary", {})
    diagnostics = {
        "buffer_path": str(buffer_path),
        "archive_mode": metadata.get("archive_mode", "single"),
        "archive_rule_version": metadata.get(
            "archive_rule_version", "legacy"
        ),
        "archive_seed_thresholds": metadata.get(
            "archive_seed_thresholds", {}
        ),
        "num_records": len(records),
        "num_cons_records": len(archive_sets["cons"]),
        "num_uc_records": len(archive_sets["uc"]),
        "num_union_records": len(archive_sets["union"]),
        "num_union_pareto_records": len(nondominated_filter(archive_sets["union"])),
        "strict_candidate_count": len(strict_candidates),
        "strict_hit_rate": float(strict_summary.get("strict_hit_rate", 0.0)),
        "hybrid_fallback_rate": float(hybrid_summary.get("hybrid_fallback_rate", 0.0)),
        "route_counts": route_counts,
        "cons_attempted_children": int(
            metadata.get("cons_attempted_children", 0)
        ),
        "cons_successful_children": int(
            metadata.get("cons_successful_children", 0)
        ),
        "cons_routed_children": int(
            metadata.get("cons_routed_children", 0)
        ),
        "cons_rejected_by_cost_gate": int(
            metadata.get("cons_rejected_by_cost_gate", 0)
        ),
        "cons_rejected_by_feasibility": int(
            metadata.get("cons_rejected_by_feasibility", 0)
        ),
        "cons_risk_mode": metadata.get("cons_risk_mode", "none"),
        "cons_cvar_alpha": float(metadata.get("cvar_alpha", 0.25)),
        "cons_cvar_metric": metadata.get(
            "cvar_metric", "final_critical_compromised_hosts"
        ),
        "cvar_metric_weights": metadata.get("cvar_metric_weights", {}),
        "cons_risk_objective_mode": metadata.get(
            "cons_risk_objective_mode", "none"
        ),
        "cons_risk_penalty_coef": float(
            metadata.get("cons_risk_penalty_coef", 0.0)
        ),
        "cons_cvar_estimate_mean": float(
            metadata.get("cons_cvar_estimate_mean", 0.0)
        ),
        "cons_cvar_estimate_tail": float(
            metadata.get("cons_cvar_estimate_tail", 0.0)
        ),
        "cons_risk_penalty_mean": float(
            metadata.get("cons_risk_penalty_mean", 0.0)
        ),
        "cons_rejected_by_risk_gate": int(
            metadata.get("cons_rejected_by_risk_gate", 0)
        ),
        "cons_risk_rollout_count": int(
            metadata.get("cons_risk_rollout_count", 0)
        ),
        "cons_tail_env_count": int(
            metadata.get("cons_tail_env_count", 0)
        ),
        "cons_tail_risk_mean": float(
            metadata.get("cons_tail_risk_mean", 0.0)
        ),
        "cons_tail_risk_max": float(
            metadata.get("cons_tail_risk_max", 0.0)
        ),
        "cons_episode_risk_mean": float(
            metadata.get("cons_episode_risk_mean", 0.0)
        ),
        "cons_episode_risk_tail": float(
            metadata.get("cons_episode_risk_tail", 0.0)
        ),
        "cons_child_failed_by_violation": int(
            metadata.get("cons_child_failed_by_violation", 0)
        ),
        "cons_child_failed_by_final_critical": int(
            metadata.get("cons_child_failed_by_final_critical", 0)
        ),
        "cons_child_failed_by_disruption": int(
            metadata.get("cons_child_failed_by_disruption", 0)
        ),
        "cons_child_failed_by_multiple": int(
            metadata.get("cons_child_failed_by_multiple", 0)
        ),
        "saved_vs_shadow_diagnostics": {
            "available": bool(shadow_available),
            "saved_route_preview_cons_accept_count": int(
                metadata.get("saved_route_preview_cons_accept_count", 0)
            ),
            "shadow_route_preview_cons_accept_count": int(
                metadata.get("shadow_route_preview_cons_accept_count", 0)
            ),
            "saved_route_preview_near_feasible_count": int(
                metadata.get("saved_route_preview_near_feasible_count", 0)
            ),
            "shadow_route_preview_near_feasible_count": int(
                metadata.get("shadow_route_preview_near_feasible_count", 0)
            ),
            "saved_route_fail_primary_counts": metadata.get(
                "saved_route_fail_primary_counts", {}
            ),
            "shadow_route_fail_primary_counts": metadata.get(
                "shadow_route_fail_primary_counts", {}
            ),
            "saved_route_fail_component_counts": metadata.get(
                "saved_route_fail_component_counts", {}
            ),
            "shadow_route_fail_component_counts": metadata.get(
                "shadow_route_fail_component_counts", {}
            ),
            "saved_final_critical_threshold_counts": metadata.get(
                "saved_final_critical_threshold_counts", {}
            ),
            "shadow_final_critical_threshold_counts": metadata.get(
                "shadow_final_critical_threshold_counts", {}
            ),
            "saved_final_critical_value_summary": metadata.get(
                "saved_final_critical_value_summary", {}
            ),
            "shadow_final_critical_value_summary": metadata.get(
                "shadow_final_critical_value_summary", {}
            ),
            "saved_objective_delta_vs_parent_summary": metadata.get(
                "saved_objective_delta_vs_parent_summary", {}
            ),
            "shadow_objective_delta_vs_parent_summary": metadata.get(
                "shadow_objective_delta_vs_parent_summary", {}
            ),
            "saved_spread_gain_summary": metadata.get(
                "saved_spread_gain_summary", {}
            ),
            "shadow_spread_gain_summary": metadata.get(
                "shadow_spread_gain_summary", {}
            ),
            "gap_direction_summary": metadata.get("gap_direction_summary", {}),
        },
    }
    diagnostics.update(route_counts)
    return diagnostics


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate C-MORL MiniCAGE policy buffer.")
    parser.add_argument("--config", default=str(DEFAULT_EVALUATE_CONFIG))
    parser.add_argument("--buffer-path", default=None)
    parser.add_argument("--preference-step", type=float, default=None)
    parser.add_argument("--output-path", default=None)
    parser.add_argument("--mode", choices=("union", "strict", "hybrid"), default=None)
    parser.add_argument("--strict-require-tight", action="store_true")
    args = parser.parse_args()

    config = load_evaluate_config(args.config)
    if args.buffer_path is not None:
        config.buffer_path = args.buffer_path
    if args.output_path is not None:
        config.output_path = args.output_path
    if args.preference_step is not None:
        config.preference_step = args.preference_step
    if args.mode is not None:
        config.selector_mode = args.mode
    if args.strict_require_tight:
        config.strict_require_tight = True
    if not config.buffer_path:
        raise ValueError("buffer_path must be set via config file or --buffer-path")

    results = evaluate_policy_buffer_all_modes(
        config.buffer_path,
        config.preference_step,
        penalty_weights=config.hybrid_penalty_weights,
        strict_require_tight=config.strict_require_tight,
        reference_strategy=config.reference_strategy,
        reference_margin=config.reference_margin,
        reference_point=config.reference_point,
        hv_max_exact_points=config.hv_max_exact_points,
        hv_mc_samples=config.hv_mc_samples,
    )
    output_path = Path(config.output_path) if config.output_path else Path(config.buffer_path).with_name("metrics.json")
    output_dir = output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    mode_paths = {
        "union": output_dir / "metrics_union.json",
        "strict": output_dir / "metrics_strict.json",
        "hybrid": output_dir / "metrics_hybrid.json",
    }
    for mode, result in results.items():
        save_json(mode_paths[mode], result)
    diagnostics = archive_diagnostics_payload(
        config.buffer_path,
        strict_payload=results["strict"],
        hybrid_payload=results["hybrid"],
    )
    diagnostics_path = output_dir / "archive_diagnostics.json"
    save_json(diagnostics_path, diagnostics)
    selected_mode = config.selector_mode if config.selector_mode in results else "union"
    save_json(output_path, results[selected_mode])
    if output_path.name != "metrics.json":
        save_json(output_dir / "metrics.json", results["union"])
    else:
        save_json(output_path, results["union"])
    print(f"Saved union evaluation to {mode_paths['union']}")
    print(f"Saved strict evaluation to {mode_paths['strict']}")
    print(f"Saved hybrid evaluation to {mode_paths['hybrid']}")
    print(f"Saved archive diagnostics to {diagnostics_path}")
    print(f"Saved selected evaluation ({selected_mode}) to {output_path}")


if __name__ == "__main__":
    main()
