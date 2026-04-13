from __future__ import annotations

import argparse
import copy
import uuid
from pathlib import Path

import numpy as np
import torch

from cmorl_minicage.algorithms.adaptive_selection import select_top_n_adaptive
from cmorl_minicage.algorithms.dual_archive import DualArchiveManager
from cmorl_minicage.buffer import (
    buffer_metadata,
    load_policy_buffer,
    policy_record,
    save_policy_buffer,
)
from cmorl_minicage.config import (
    DEFAULT_STAGE2_CONFIG,
    Stage2Config,
    load_stage2_config,
)
from cmorl_minicage.algorithms.dynamic_beta import compute_dynamic_beta
from cmorl_minicage.algorithms.ipo import IPOConfig, IPOTrainer
from cmorl_minicage.algorithms.selection import crowding_distance, nondominated_filter, select_top_n_by_crowding
from cmorl_minicage.env import MiniCageMORLEnv
from cmorl_minicage.models import ActorCritic
from cmorl_minicage.storage import ScalarRolloutStorage, VectorRolloutStorage
from cmorl_minicage.train_stage1 import collect_rollout, evaluate_policy
from cmorl_minicage.utils import ensure_dir, save_json, set_seed, simplex_grid


def _selection_preferences(config: Stage2Config, obj_dim: int) -> list[list[float]]:
    step = config.eval.preference_step
    if step is None:
        step = 0.5 if obj_dim == 2 else 0.1
    return simplex_grid(float(step), obj_dim)


def _selected_components_for_crowding(
    current_pareto: list[dict],
    extension_records: list[dict],
    current_crowding: np.ndarray,
) -> tuple[dict[str, float], dict[str, dict[str, float | list[float]]], dict[str, int]]:
    pareto_by_id = {record["policy_id"]: index for index, record in enumerate(current_pareto)}
    selected_scores: dict[str, float] = {}
    selected_components: dict[str, dict[str, float | list[float]]] = {}
    ranking_source: list[tuple[float, str]] = []
    for record in extension_records:
        index = pareto_by_id.get(record["policy_id"])
        crowding_value = float(current_crowding[index]) if index is not None else 0.0
        if not np.isfinite(crowding_value):
            crowding_value = 1.0
        selected_scores[record["policy_id"]] = crowding_value
        selected_components[record["policy_id"]] = {
            "crowding_score": crowding_value,
            "expansion_potential": 0.0,
            "target_expansion_by_objective": [],
            "constraint_risk": 0.0,
            "low_risk_score": 1.0,
            "utility_coverage_gain": 0.0,
        }
        ranking_source.append((crowding_value, record["policy_id"]))
    ranking_source.sort(key=lambda item: (-item[0], item[1]))
    selected_ranks = {
        policy_id: rank + 1 for rank, (_, policy_id) in enumerate(ranking_source)
    }
    return selected_scores, selected_components, selected_ranks


def _normalize_metric(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=np.float32)
    if values.size == 0:
        return np.zeros(0, dtype=np.float32)
    vmin = float(np.min(values))
    vmax = float(np.max(values))
    if np.isclose(vmax, vmin):
        return np.zeros_like(values, dtype=np.float32)
    return (values - vmin) / (vmax - vmin)


def _semantic_selection_metrics(
    env_config,
    model_config,
    checkpoint_path: str,
    *,
    eval_episodes: int,
) -> dict[str, float]:
    env = MiniCageMORLEnv(
        num_envs=env_config.num_envs,
        red_policy=env_config.red_policy,
        remove_bugs=env_config.remove_bugs,
        max_steps=env_config.max_episode_steps,
        seed=env_config.seed,
    )
    actor_critic = ActorCritic(
        obs_dim=env.obs_dim,
        action_dim=env.action_dim,
        obj_dim=env.obj_dim,
        hidden_sizes=(model_config.hidden_size, model_config.hidden_size),
    ).to(torch.device("cpu"))
    actor_critic.load_state_dict(
        torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    )
    actor_critic.eval()

    totals = {
        "final_critical_compromised_hosts": [],
        "critical_impact_count": [],
        "high_disruption_action_count": [],
        "total_action_count": [],
    }
    base_seed = int(env_config.seed)
    with torch.no_grad():
        for episode_idx in range(max(int(eval_episodes), 1)):
            env.seed = base_seed + episode_idx
            obs, _ = env.reset()
            done = np.zeros(env.num_envs, dtype=bool)
            episode_semantics = {
                "critical_impact_count": np.zeros(env.num_envs, dtype=np.float64),
                "high_disruption_action_count": np.zeros(env.num_envs, dtype=np.float64),
                "total_action_count": np.zeros(env.num_envs, dtype=np.float64),
            }
            final_critical = np.zeros(env.num_envs, dtype=np.float64)

            while not np.all(done):
                obs_tensor = torch.as_tensor(obs, dtype=torch.float32)
                actions = (
                    actor_critic.act(obs_tensor)
                    .actions.cpu()
                    .numpy()
                    .reshape(env.num_envs, 1)
                )
                obs, _, done, _, info = env.step(actions)
                semantic_info = info["semantic_info"]
                final_critical = np.asarray(
                    semantic_info["final_critical_compromised_hosts"],
                    dtype=np.float64,
                )
                for key in episode_semantics:
                    episode_semantics[key] += np.asarray(
                        semantic_info[key], dtype=np.float64
                    )

            totals["final_critical_compromised_hosts"].extend(final_critical.tolist())
            for key in episode_semantics:
                totals[key].extend(episode_semantics[key].tolist())

    total_action_sum = max(float(np.sum(totals["total_action_count"])), 1.0)
    return {
        "final_critical_compromised_hosts": float(
            np.mean(totals["final_critical_compromised_hosts"])
        ),
        "critical_impact_count": float(np.mean(totals["critical_impact_count"])),
        "high_disruption_action_rate": float(
            np.sum(totals["high_disruption_action_count"]) / total_action_sum
        ),
    }


def _semantic_component_overrides(
    records: list[dict],
    config: Stage2Config,
) -> dict[str, dict[str, float | dict[str, float]]]:
    if config.selection.semantic_eval_episodes <= 0 or not records:
        return {}

    metric_names = tuple(config.selection.semantic_metric_weights.keys())
    by_policy: dict[str, dict[str, float]] = {}
    for record in records:
        by_policy[record["policy_id"]] = _semantic_selection_metrics(
            config.env,
            config.model,
            record["checkpoint_path"],
            eval_episodes=config.selection.semantic_eval_episodes,
        )

    normalized_metrics: dict[str, np.ndarray] = {}
    for metric_name in metric_names:
        values = np.asarray(
            [by_policy[record["policy_id"]][metric_name] for record in records],
            dtype=np.float32,
        )
        normalized_metrics[metric_name] = _normalize_metric(values)

    overrides: dict[str, dict[str, float | dict[str, float]]] = {}
    total_weight = max(
        float(
            sum(
                float(weight)
                for weight in config.selection.semantic_metric_weights.values()
            )
        ),
        1e-8,
    )
    for index, record in enumerate(records):
        weighted_risk = 0.0
        for metric_name, weight in config.selection.semantic_metric_weights.items():
            weighted_risk += float(weight) * float(normalized_metrics[metric_name][index])
        semantic_risk = weighted_risk / total_weight
        overrides[record["policy_id"]] = {
            "semantic_risk": float(semantic_risk),
            "semantic_low_risk_score": float(1.0 - semantic_risk),
            "semantic_metrics": dict(by_policy[record["policy_id"]]),
        }
    return overrides


def _semantic_penalty(
    semantic_info: dict[str, np.ndarray | list[float]],
    weights: dict[str, float],
    coef: float,
) -> np.ndarray:
    if coef <= 0.0:
        first = next(iter(semantic_info.values()))
        return np.zeros(len(first), dtype=np.float32)
    penalty = None
    for metric_name, weight in weights.items():
        values = np.asarray(semantic_info.get(metric_name, 0.0), dtype=np.float32)
        term = float(weight) * values
        penalty = term if penalty is None else penalty + term
    if penalty is None:
        return np.zeros(0, dtype=np.float32)
    return np.asarray(coef * penalty, dtype=np.float32)


def _semantic_metric_values(
    semantic_info: dict[str, np.ndarray | list[float]],
    metric_name: str,
    num_envs: int,
) -> np.ndarray:
    values = semantic_info.get(metric_name)
    if values is None:
        return np.zeros(num_envs, dtype=np.float32)
    array = np.asarray(values, dtype=np.float32).reshape(-1)
    if array.size == 0:
        return np.zeros(num_envs, dtype=np.float32)
    if array.size == 1:
        return np.full(num_envs, float(array[0]), dtype=np.float32)
    if array.size >= num_envs:
        return np.asarray(array[:num_envs], dtype=np.float32)
    padded = np.zeros(num_envs, dtype=np.float32)
    padded[: array.size] = array
    return padded


def _rollout_cvar_penalty(
    *,
    risk_samples: np.ndarray | list[float],
    alpha: float,
    penalty_coef: float,
) -> tuple[float, float, float, int, np.ndarray]:
    samples = np.asarray(risk_samples, dtype=np.float32).reshape(-1)
    if samples.size == 0:
        return 0.0, 0.0, 0.0, 0, np.zeros(0, dtype=np.int64)
    alpha = min(max(float(alpha), 0.0), 1.0)
    effective_alpha = alpha if alpha > 0.0 else 1.0 / float(len(samples))
    worst_k = max(1, int(np.ceil(effective_alpha * len(samples))))
    ranked_indices = np.argsort(samples)[::-1][:worst_k]
    cvar_tail = float(np.mean(samples[ranked_indices]))
    cvar_mean = float(np.mean(samples))
    rollout_penalty = float(penalty_coef) * cvar_tail
    return cvar_mean, cvar_tail, rollout_penalty, worst_k, ranked_indices.astype(np.int64)


def _strict_aligned_risk_values(
    *,
    cumulative_objectives: np.ndarray,
    final_critical: np.ndarray,
    high_disruption_count: np.ndarray,
    total_action_count: np.ndarray,
    archive_seed_thresholds: dict[str, float],
    cons_thresholds: dict[str, float],
    metric_weights: dict[str, float],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    num_envs = cumulative_objectives.shape[0]
    mean_violation = np.zeros(num_envs, dtype=np.float32)
    business_threshold = archive_seed_thresholds.get("d_business")
    cost_threshold = archive_seed_thresholds.get("d_cost")
    if cumulative_objectives.shape[1] >= 2 and business_threshold is not None:
        mean_violation += np.maximum(
            0.0,
            float(business_threshold) - cumulative_objectives[:, 1],
        ).astype(np.float32)
    if cumulative_objectives.shape[1] >= 3 and cost_threshold is not None:
        mean_violation += np.maximum(
            0.0,
            float(cost_threshold) - cumulative_objectives[:, 2],
        ).astype(np.float32)
    action_denom = np.maximum(total_action_count, 1.0)
    high_disruption_rate = (high_disruption_count / action_denom).astype(np.float32)
    high_disruption_excess = np.maximum(
        0.0,
        high_disruption_rate - float(cons_thresholds.get("high_disruption", 1.0)),
    ).astype(np.float32)
    risk = (
        float(metric_weights.get("final_critical_compromised_hosts", 1.0)) * final_critical
        + float(metric_weights.get("mean_violation", 1.0)) * mean_violation
        + float(metric_weights.get("high_disruption_excess", 0.5)) * high_disruption_excess
    ).astype(np.float32)
    return risk, mean_violation, high_disruption_rate


def _strict_failure_buckets(
    results: list[dict],
    *,
    cons_thresholds: dict[str, float],
) -> dict[str, int]:
    buckets = {
        "cons_child_failed_by_violation": 0,
        "cons_child_failed_by_final_critical": 0,
        "cons_child_failed_by_disruption": 0,
        "cons_child_failed_by_multiple": 0,
    }
    for result in results:
        if result.get("archive_branch") != "cons":
            continue
        if result.get("generated_policy_id") is None:
            continue
        if result.get("route_decision") == "accepted_cons":
            continue
        violation_fail = float(result.get("mean_violation") or 0.0) > float(
            cons_thresholds.get("violation", 0.5)
        )
        final_critical_fail = float(
            result.get("final_critical_compromised_hosts") or 0.0
        ) > float(cons_thresholds.get("final_critical_near", 0.25))
        disruption_fail = float(
            result.get("high_disruption_action_rate")
            or result.get("high_disruption_rate")
            or 0.0
        ) > float(cons_thresholds.get("high_disruption", 1.0))
        fail_count = sum((violation_fail, final_critical_fail, disruption_fail))
        if fail_count <= 0:
            continue
        if fail_count > 1:
            buckets["cons_child_failed_by_multiple"] += 1
        elif violation_fail:
            buckets["cons_child_failed_by_violation"] += 1
        elif final_critical_fail:
            buckets["cons_child_failed_by_final_critical"] += 1
        elif disruption_fail:
            buckets["cons_child_failed_by_disruption"] += 1
    return buckets


def _summarize_cons_risk(
    results: list[dict],
    *,
    cons_risk_mode: str,
    cvar_alpha: float,
    cvar_metric: str,
) -> dict[str, float | int | str]:
    risk_results = [result for result in results if result.get("archive_branch") == "cons"]
    if not risk_results:
        return {
            "cons_risk_mode": cons_risk_mode,
            "cons_cvar_alpha": float(cvar_alpha),
            "cons_cvar_metric": cvar_metric,
            "cons_cvar_estimate_mean": 0.0,
            "cons_cvar_estimate_tail": 0.0,
            "cons_risk_penalty_mean": 0.0,
            "cons_rejected_by_risk_gate": 0,
            "cons_risk_rollout_count": 0,
            "cons_tail_env_count": 0,
            "cons_tail_risk_mean": 0.0,
            "cons_tail_risk_max": 0.0,
            "cons_episode_risk_mean": 0.0,
            "cons_episode_risk_tail": 0.0,
            "cons_risk_objective_mode": "none",
            "cons_risk_penalty_coef": 0.0,
        }
    return {
        "cons_risk_mode": cons_risk_mode,
        "cons_cvar_alpha": float(cvar_alpha),
        "cons_cvar_metric": cvar_metric,
        "cons_cvar_estimate_mean": float(
            np.mean([float(result.get("cons_cvar_estimate_mean", 0.0)) for result in risk_results])
        ),
        "cons_cvar_estimate_tail": float(
            np.mean([float(result.get("cons_cvar_estimate_tail", 0.0)) for result in risk_results])
        ),
        "cons_risk_penalty_mean": float(
            np.mean([float(result.get("cons_risk_penalty_mean", 0.0)) for result in risk_results])
        ),
        "cons_rejected_by_risk_gate": int(
            sum(int(result.get("cons_rejected_by_risk_gate", 0)) for result in risk_results)
        ),
        "cons_risk_rollout_count": int(
            sum(int(result.get("cons_risk_rollout_count", 0)) for result in risk_results)
        ),
        "cons_tail_env_count": int(
            sum(int(result.get("cons_tail_env_count", 0)) for result in risk_results)
        ),
        "cons_tail_risk_mean": float(
            np.mean([float(result.get("cons_tail_risk_mean", 0.0)) for result in risk_results])
        ),
        "cons_tail_risk_max": float(
            np.max([float(result.get("cons_tail_risk_max", 0.0)) for result in risk_results])
        ),
        "cons_episode_risk_mean": float(
            np.mean([float(result.get("cons_episode_risk_mean", 0.0)) for result in risk_results])
        ),
        "cons_episode_risk_tail": float(
            np.mean([float(result.get("cons_episode_risk_tail", 0.0)) for result in risk_results])
        ),
        "cons_risk_objective_mode": str(
            next(
                (
                    result.get("cons_risk_objective_mode")
                    for result in risk_results
                    if result.get("cons_risk_objective_mode")
                ),
                "none",
            )
        ),
        "cons_risk_penalty_coef": float(
            np.mean([float(result.get("cons_risk_penalty_coef", 0.0)) for result in risk_results])
        ),
    }


def _collect_rollout_stage2(
    env: MiniCageMORLEnv,
    actor_critic: ActorCritic,
    storage: VectorRolloutStorage,
    device: torch.device,
    *,
    semantic_penalty_coef: float,
    semantic_penalty_weights: dict[str, float],
    cons_risk_mode: str = "none",
    cvar_alpha: float = 0.25,
    cvar_metric: str = "final_critical_compromised_hosts",
    cvar_penalty_coef: float = 0.25,
    cvar_metric_weights: dict[str, float] | None = None,
    archive_seed_thresholds: dict[str, float] | None = None,
    cons_thresholds: dict[str, float] | None = None,
    cons_risk_objective_mode: str = "none",
    cons_risk_penalty_coef: float = 0.0,
) -> tuple[np.ndarray, torch.Tensor, ScalarRolloutStorage | None, dict[str, float | int | str]]:
    obs, _ = env.reset()
    obs_tensor = torch.as_tensor(obs, dtype=torch.float32, device=device)
    storage.reset()
    storage.obs[0].copy_(obs_tensor)
    episode_return = np.zeros((env.num_envs, env.obj_dim), dtype=np.float32)
    archive_seed_thresholds = dict(archive_seed_thresholds or {})
    cons_thresholds = dict(cons_thresholds or {})
    cvar_metric_weights = dict(cvar_metric_weights or {})
    risk_storage = None
    zero_preferences = None
    if cons_risk_mode == "strict_aligned_cvar":
        risk_storage = ScalarRolloutStorage(
            num_steps=storage.num_steps,
            num_envs=env.num_envs,
            obs_dim=env.obs_dim,
            preference_dim=1,
            device=device,
        )
        risk_storage.reset()
        risk_storage.obs[0].copy_(obs_tensor)
        risk_storage.preferences[0].zero_()
        zero_preferences = torch.zeros((env.num_envs, 1), dtype=torch.float32, device=device)
    cumulative_objectives = np.zeros((env.num_envs, env.obj_dim), dtype=np.float32)
    cumulative_high_disruption = np.zeros(env.num_envs, dtype=np.float32)
    cumulative_total_actions = np.zeros(env.num_envs, dtype=np.float32)
    last_risk_values = np.zeros(env.num_envs, dtype=np.float32)
    last_mean_violation = np.zeros(env.num_envs, dtype=np.float32)
    last_high_disruption_rate = np.zeros(env.num_envs, dtype=np.float32)
    completed_env_mask = np.zeros(env.num_envs, dtype=bool)
    per_env_risk_samples = np.zeros(env.num_envs, dtype=np.float32)
    completed_episode_count = 0
    proxy_sample_count = 0

    for _ in range(storage.num_steps):
        with torch.no_grad():
            policy_output = actor_critic.act(obs_tensor)
        actions = policy_output.actions.cpu().numpy().reshape(env.num_envs, 1)
        next_obs, reward_vec, done, _, info = env.step(actions)
        reward_vec = np.asarray(reward_vec, dtype=np.float32)
        raw_reward_vec = reward_vec.copy()
        semantic_info = info.get("semantic_info", {})
        cumulative_objectives += raw_reward_vec
        cumulative_high_disruption += _semantic_metric_values(
            semantic_info, "high_disruption_action_count", env.num_envs
        )
        cumulative_total_actions += _semantic_metric_values(
            semantic_info, "total_action_count", env.num_envs
        )
        penalty = _semantic_penalty(
            semantic_info,
            semantic_penalty_weights,
            semantic_penalty_coef,
        )
        if penalty.size:
            reward_vec = reward_vec - penalty[:, None]
        if cons_risk_mode == "cvar":
            last_risk_values = _semantic_metric_values(semantic_info, cvar_metric, env.num_envs)
            last_mean_violation = np.zeros(env.num_envs, dtype=np.float32)
            last_high_disruption_rate = np.zeros(env.num_envs, dtype=np.float32)
        elif cons_risk_mode == "strict_aligned_cvar":
            final_critical = _semantic_metric_values(
                semantic_info, "final_critical_compromised_hosts", env.num_envs
            )
            (
                last_risk_values,
                last_mean_violation,
                last_high_disruption_rate,
            ) = _strict_aligned_risk_values(
                cumulative_objectives=cumulative_objectives,
                final_critical=final_critical,
                high_disruption_count=cumulative_high_disruption,
                total_action_count=cumulative_total_actions,
                archive_seed_thresholds=archive_seed_thresholds,
                cons_thresholds=cons_thresholds,
                metric_weights=cvar_metric_weights,
            )
        next_obs_tensor = torch.as_tensor(next_obs, dtype=torch.float32, device=device)
        reward_tensor = torch.as_tensor(reward_vec, dtype=torch.float32, device=device)
        masks = torch.as_tensor(1.0 - done.astype(np.float32), dtype=torch.float32, device=device)
        storage.insert(
            obs=next_obs_tensor,
            actions=policy_output.actions,
            log_probs=policy_output.log_probs,
            values=policy_output.values,
            rewards=reward_tensor,
            masks=masks,
        )
        if risk_storage is not None and zero_preferences is not None:
            zero_values = torch.zeros(env.num_envs, dtype=torch.float32, device=device)
            zero_rewards = torch.zeros(env.num_envs, dtype=torch.float32, device=device)
            risk_storage.insert(
                obs=next_obs_tensor,
                preference=zero_preferences,
                actions=policy_output.actions,
                log_probs=policy_output.log_probs,
                values=zero_values,
                rewards=zero_rewards,
                masks=masks,
            )
        done_mask = np.asarray(done, dtype=bool)
        fresh_done = np.logical_and(done_mask, ~completed_env_mask)
        if np.any(fresh_done):
            per_env_risk_samples[fresh_done] = last_risk_values[fresh_done]
            completed_env_mask = np.logical_or(completed_env_mask, fresh_done)
            completed_episode_count += int(np.sum(fresh_done))
        obs_tensor = next_obs_tensor
        episode_return += reward_vec

    cvar_mean = 0.0
    cvar_tail = 0.0
    rollout_penalty = 0.0
    worst_k = 0
    tail_indices = np.zeros(0, dtype=np.int64)
    if cons_risk_mode in {"cvar", "strict_aligned_cvar"}:
        for env_index in range(env.num_envs):
            if not completed_env_mask[env_index]:
                per_env_risk_samples[env_index] = float(last_risk_values[env_index])
                proxy_sample_count += 1
        cvar_mean, cvar_tail, rollout_penalty, worst_k, tail_indices = _rollout_cvar_penalty(
            risk_samples=per_env_risk_samples,
            alpha=cvar_alpha,
            penalty_coef=cvar_penalty_coef,
        )
        if cons_risk_mode == "cvar" and rollout_penalty > 0.0:
            storage.rewards[: storage.num_steps] -= rollout_penalty
            episode_return -= rollout_penalty * float(storage.num_steps)
        if cons_risk_mode == "strict_aligned_cvar" and risk_storage is not None:
            per_step_risk = np.zeros((storage.num_steps, env.num_envs), dtype=np.float32)
            if tail_indices.size:
                per_step_risk[:, tail_indices] = (
                    per_env_risk_samples[tail_indices] / float(storage.num_steps)
                )[None, :]
            risk_storage.rewards[: storage.num_steps].copy_(
                torch.as_tensor(per_step_risk, dtype=torch.float32, device=device)
            )

    with torch.no_grad():
        next_value = actor_critic.get_value(obs_tensor)
    if risk_storage is not None:
        risk_next_value = torch.zeros(env.num_envs, dtype=torch.float32, device=device)
        risk_storage.compute_returns(risk_next_value, 1.0, 1.0)
    risk_summary = {
        "cons_risk_mode": cons_risk_mode,
        "cons_cvar_alpha": float(cvar_alpha),
        "cons_cvar_metric": cvar_metric,
        "cons_cvar_estimate_mean": float(cvar_mean),
        "cons_cvar_estimate_tail": float(cvar_tail),
        "cons_risk_penalty_mean": float(
            rollout_penalty if cons_risk_mode == "cvar" else float(cons_risk_penalty_coef) * cvar_tail
        ),
        "cons_rejected_by_risk_gate": 0,
        "cons_risk_rollout_count": 1 if cons_risk_mode in {"cvar", "strict_aligned_cvar"} else 0,
        "cons_cvar_worst_k": int(worst_k),
        "cons_cvar_sample_count": int(len(per_env_risk_samples)),
        "cons_cvar_completed_episode_count": int(completed_episode_count),
        "cons_cvar_proxy_sample_count": int(proxy_sample_count),
        "cons_tail_env_count": int(len(tail_indices)),
        "cons_tail_risk_mean": float(np.mean(per_env_risk_samples[tail_indices])) if len(tail_indices) else 0.0,
        "cons_tail_risk_max": float(np.max(per_env_risk_samples[tail_indices])) if len(tail_indices) else 0.0,
        "cons_episode_risk_mean": float(np.mean(per_env_risk_samples)) if per_env_risk_samples.size else 0.0,
        "cons_episode_risk_tail": float(cvar_tail),
        "cons_risk_objective_mode": cons_risk_objective_mode,
        "cons_risk_penalty_coef": float(cons_risk_penalty_coef),
        "cons_mean_violation_mean": float(np.mean(last_mean_violation)),
        "cons_high_disruption_rate_mean": float(np.mean(last_high_disruption_rate)),
    }
    return episode_return.mean(axis=0), next_value, risk_storage, risk_summary


def _operator_settings(operator_mode: str) -> tuple[str, str]:
    if operator_mode == "original":
        return "crowding", "fixed"
    if operator_mode == "adacs_dcs":
        return "adaptive", "dynamic"
    raise ValueError(f"Unsupported Stage-2 operator_mode: {operator_mode}")


def _selection_diagnostics_for_records(
    records: list[dict],
    selected_records: list[dict],
    *,
    selection_mode: str,
    config: Stage2Config,
    preferences: list[list[float]],
) -> tuple[dict[str, float], dict[str, dict[str, float | list[float]]], dict[str, int]]:
    if not selected_records:
        return {}, {}, {}
    if selection_mode == "adaptive":
        pareto_count = len(nondominated_filter(records))
        _, scores, components = select_top_n_adaptive(
            records,
            max(pareto_count, len(selected_records)),
            preferences,
            config.selection.score_weights,
            config.selection.utility_tolerance,
            coverage_mode=config.selection.coverage_mode,
            keep_extremes=config.selection.keep_extremes,
        )
        selected_ids = {record["policy_id"] for record in selected_records}
        ranking_source = [
            (float(score), policy_id)
            for policy_id, score in scores.items()
            if policy_id in selected_ids
        ]
        ranking_source.sort(key=lambda item: (-item[0], item[1]))
        ranks = {policy_id: rank + 1 for rank, (_, policy_id) in enumerate(ranking_source)}
        return (
            {policy_id: float(scores.get(policy_id, 0.0)) for policy_id in selected_ids},
            {policy_id: dict(components.get(policy_id, {})) for policy_id in selected_ids},
            ranks,
        )

    current_pareto = nondominated_filter(records)
    current_crowding = crowding_distance(current_pareto)
    return _selected_components_for_crowding(
        current_pareto,
        selected_records,
        current_crowding,
    )


def _record_objective_metrics(objectives: np.ndarray) -> dict[str, float | None]:
    return {
        "security_return": float(objectives[0]) if objectives.size >= 1 else None,
        "business_return": float(objectives[1]) if objectives.size >= 2 else None,
        "cost_return": float(objectives[2]) if objectives.size >= 3 else None,
    }


def _record_feasibility_metrics(
    *,
    last_constraint_margins: np.ndarray | None,
    extension_mode: str,
    constraint_tolerance: float,
    near_tolerance: float,
) -> dict[str, bool | float | None]:
    if extension_mode != "constrained" or last_constraint_margins is None:
        return {
            "feasible_flag": None,
            "near_feasible_flag": None,
            "tight_feasible_flag": None,
            "mean_violation": None,
        }
    margins = np.asarray(last_constraint_margins, dtype=np.float32)
    violations = np.maximum(0.0, float(constraint_tolerance) - margins)
    tight = bool(np.all(margins > float(constraint_tolerance)))
    near = bool(np.all(margins >= float(constraint_tolerance) - float(near_tolerance)))
    return {
        "feasible_flag": tight,
        "near_feasible_flag": near,
        "tight_feasible_flag": tight,
        "mean_violation": float(np.mean(violations)) if violations.size else 0.0,
    }


def _evaluate_policy_with_semantics(
    env: MiniCageMORLEnv,
    actor_critic: ActorCritic,
    device: torch.device,
    *,
    episodes: int = 3,
) -> tuple[np.ndarray, dict[str, float]]:
    returns = np.zeros(env.obj_dim, dtype=np.float64)
    final_critical_samples: list[float] = []
    critical_impact_samples: list[float] = []
    high_disruption_count = 0.0
    total_action_count = 0.0
    with torch.no_grad():
        for _ in range(max(int(episodes), 1)):
            obs, _ = env.reset()
            done = np.zeros(env.num_envs, dtype=bool)
            episode_critical_impact = np.zeros(env.num_envs, dtype=np.float64)
            episode_high_disruption = np.zeros(env.num_envs, dtype=np.float64)
            episode_action_count = np.zeros(env.num_envs, dtype=np.float64)
            final_critical = np.zeros(env.num_envs, dtype=np.float64)
            while not np.all(done):
                obs_tensor = torch.as_tensor(obs, dtype=torch.float32, device=device)
                actions = (
                    actor_critic.act(obs_tensor)
                    .actions.cpu()
                    .numpy()
                    .reshape(env.num_envs, 1)
                )
                obs, reward_vec, done, _, info = env.step(actions)
                returns += reward_vec.mean(axis=0)
                semantic_info = info.get("semantic_info", {}) if isinstance(info, dict) else {}
                final_critical = np.asarray(
                    semantic_info.get(
                        "final_critical_compromised_hosts",
                        np.zeros(env.num_envs, dtype=np.float64),
                    ),
                    dtype=np.float64,
                )
                episode_critical_impact += np.asarray(
                    semantic_info.get(
                        "critical_impact_count",
                        np.zeros(env.num_envs, dtype=np.float64),
                    ),
                    dtype=np.float64,
                )
                episode_high_disruption += np.asarray(
                    semantic_info.get(
                        "high_disruption_action_count",
                        np.zeros(env.num_envs, dtype=np.float64),
                    ),
                    dtype=np.float64,
                )
                episode_action_count += np.asarray(
                    semantic_info.get(
                        "total_action_count",
                        np.zeros(env.num_envs, dtype=np.float64),
                    ),
                    dtype=np.float64,
                )
            final_critical_samples.extend(final_critical.tolist())
            critical_impact_samples.extend(episode_critical_impact.tolist())
            high_disruption_count += float(np.sum(episode_high_disruption))
            total_action_count += float(np.sum(episode_action_count))
    returns /= max(int(episodes), 1)
    action_denom = max(total_action_count, 1.0)
    semantics = {
        "final_critical_compromised_hosts": float(np.mean(final_critical_samples))
        if final_critical_samples
        else 0.0,
        "critical_impact_count": float(np.mean(critical_impact_samples))
        if critical_impact_samples
        else 0.0,
        "high_disruption_action_rate": float(high_disruption_count / action_denom),
    }
    return returns.astype(np.float32), semantics


def _constraint_thresholds_for_objective(
    reference_objectives: np.ndarray,
    objective_idx: int,
    beta_value: float,
) -> tuple[list[int], np.ndarray]:
    reference = np.asarray(reference_objectives, dtype=np.float32)
    constraint_indices = [
        index for index in range(reference.size) if index != int(objective_idx)
    ]
    if not constraint_indices:
        return [], np.zeros(0, dtype=np.float32)
    thresholds = (float(beta_value) * reference[constraint_indices]).astype(np.float32)
    return constraint_indices, thresholds


def _strict_mean_violation(
    constraint_margins: np.ndarray | None,
) -> float | None:
    if constraint_margins is None:
        return None
    margins = np.asarray(constraint_margins, dtype=np.float32)
    if margins.size == 0:
        return 0.0
    return float(np.mean(np.maximum(0.0, -margins)))


def _record_metric(record: dict, *keys: str) -> float | None:
    for key in keys:
        value = record.get(key)
        if value is None:
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None


def _build_pre_save_cons_snapshot(
    *,
    base_record: dict,
    reference_objectives: np.ndarray,
    candidate_objectives: np.ndarray,
    candidate_constraint_margins: np.ndarray | None,
    objective_idx: int,
    beta_value: float,
    cons_thresholds: dict[str, float],
    cvar_metric_weights: dict[str, float],
    semantic_metrics: dict[str, float],
) -> dict[str, object]:
    constraint_indices, constraint_thresholds = _constraint_thresholds_for_objective(
        reference_objectives,
        objective_idx,
        beta_value,
    )
    margins = None
    if candidate_constraint_margins is not None:
        margins = np.asarray(candidate_constraint_margins, dtype=np.float32)
    parent_objectives = np.asarray(base_record["objective_vector"], dtype=np.float32)
    base_cost_return = float(parent_objectives[2]) if parent_objectives.size >= 3 else None
    cost_return = (
        float(candidate_objectives[2]) if np.asarray(candidate_objectives).size >= 3 else None
    )
    relative_cost_margin = None
    relative_cost_ok = False
    if base_cost_return is not None and cost_return is not None:
        relative_cost_margin = float(cost_return) - (
            float(base_cost_return)
            - float(cons_thresholds.get("cost_delta_tolerance", 3.0))
        )
        relative_cost_ok = bool(relative_cost_margin >= 0.0)

    mean_violation = _strict_mean_violation(margins)
    final_critical = semantic_metrics.get("final_critical_compromised_hosts")
    high_disruption = semantic_metrics.get("high_disruption_action_rate")
    high_disruption_excess = None
    if high_disruption is not None:
        high_disruption_excess = max(
            0.0,
            float(high_disruption) - float(cons_thresholds.get("high_disruption", 1.0)),
        )
    best_risk_seen = None
    if (
        final_critical is not None
        and mean_violation is not None
        and high_disruption_excess is not None
    ):
        best_risk_seen = float(
            float(cvar_metric_weights.get("final_critical_compromised_hosts", 1.0))
            * float(final_critical)
            + float(cvar_metric_weights.get("mean_violation", 1.0))
            * float(mean_violation)
            + float(cvar_metric_weights.get("high_disruption_excess", 0.5))
            * float(high_disruption_excess)
        )

    best_margin_seen = float(np.min(margins)) if margins is not None and margins.size else None
    parent_constraint_margins = None
    parent_min_margin = None
    if constraint_thresholds.size:
        parent_constraint_margins = (
            parent_objectives[constraint_indices] - constraint_thresholds
        ).astype(np.float32)
        parent_min_margin = float(np.min(parent_constraint_margins))
    best_min_margin_delta_vs_parent = None
    if best_margin_seen is not None and parent_min_margin is not None:
        best_min_margin_delta_vs_parent = float(best_margin_seen - parent_min_margin)

    parent_final_critical = _record_metric(
        base_record,
        "final_critical_compromised_hosts",
        "final_critical_compromised",
    )
    parent_mean_violation = _record_metric(base_record, "mean_violation")
    best_final_critical_delta_vs_parent = None
    if parent_final_critical is not None and final_critical is not None:
        best_final_critical_delta_vs_parent = float(
            float(final_critical) - float(parent_final_critical)
        )
    best_mean_violation_delta_vs_parent = None
    if parent_mean_violation is not None and mean_violation is not None:
        best_mean_violation_delta_vs_parent = float(
            float(mean_violation) - float(parent_mean_violation)
        )

    eligible = (
        mean_violation is not None
        and high_disruption is not None
        and final_critical is not None
        and base_cost_return is not None
        and cost_return is not None
    )
    disruption_ok = bool(
        high_disruption is not None
        and float(high_disruption)
        <= float(cons_thresholds.get("high_disruption", 1.0))
    )
    best_tight_feasible_flag = bool(
        eligible
        and float(mean_violation) <= 0.0
        and relative_cost_ok
        and float(final_critical) <= 0.0
        and disruption_ok
    )
    best_near_feasible_flag = bool(
        eligible
        and float(mean_violation) <= float(cons_thresholds.get("violation", 0.5))
        and relative_cost_ok
        and float(final_critical)
        <= float(cons_thresholds.get("final_critical_near", 0.25))
        and disruption_ok
    )

    return {
        "best_margin_seen": best_margin_seen,
        "best_risk_seen": best_risk_seen,
        "best_objective_vector": np.asarray(candidate_objectives, dtype=np.float32).tolist(),
        "best_security_return": (
            float(candidate_objectives[0]) if np.asarray(candidate_objectives).size >= 1 else None
        ),
        "best_business_return": (
            float(candidate_objectives[1]) if np.asarray(candidate_objectives).size >= 2 else None
        ),
        "best_cost_return": (
            float(candidate_objectives[2]) if np.asarray(candidate_objectives).size >= 3 else None
        ),
        "best_critical_impact_count": semantic_metrics.get("critical_impact_count"),
        "best_final_critical_compromised_hosts": (
            None if final_critical is None else float(final_critical)
        ),
        "best_high_disruption_action_rate": (
            None if high_disruption is None else float(high_disruption)
        ),
        "best_mean_violation": (
            None if mean_violation is None else float(mean_violation)
        ),
        "best_relative_cost_ok": bool(relative_cost_ok),
        "best_relative_cost_margin": (
            None if relative_cost_margin is None else float(relative_cost_margin)
        ),
        "best_seen_semantics": {
            "final_critical_compromised_hosts": (
                None if final_critical is None else float(final_critical)
            ),
            "mean_violation": (
                None if mean_violation is None else float(mean_violation)
            ),
            "high_disruption_action_rate": (
                None if high_disruption is None else float(high_disruption)
            ),
            "relative_cost_ok": bool(relative_cost_ok),
            "relative_cost_margin": (
                None if relative_cost_margin is None else float(relative_cost_margin)
            ),
            "strict_candidate_eligible": bool(eligible),
            "near_feasible_flag": bool(best_near_feasible_flag),
            "tight_feasible_flag": bool(best_tight_feasible_flag),
        },
        "best_near_feasible_flag": bool(best_near_feasible_flag),
        "best_tight_feasible_flag": bool(best_tight_feasible_flag),
        "best_min_margin_delta_vs_parent": best_min_margin_delta_vs_parent,
        "best_final_critical_delta_vs_parent": best_final_critical_delta_vs_parent,
        "best_mean_violation_delta_vs_parent": best_mean_violation_delta_vs_parent,
        "best_constraint_thresholds": constraint_thresholds.tolist(),
        "best_constraint_objective_indices": list(constraint_indices),
        "best_constraint_margins": (
            None if margins is None else margins.astype(np.float32).tolist()
        ),
    }


def _should_replace_best_snapshot(
    current_best: dict[str, object] | None,
    candidate_snapshot: dict[str, object],
) -> bool:
    if current_best is None:
        return True
    candidate_tight = bool(candidate_snapshot.get("best_tight_feasible_flag"))
    current_tight = bool(current_best.get("best_tight_feasible_flag"))
    if candidate_tight != current_tight:
        return candidate_tight
    candidate_near = bool(candidate_snapshot.get("best_near_feasible_flag"))
    current_near = bool(current_best.get("best_near_feasible_flag"))
    if candidate_near != current_near:
        return candidate_near
    candidate_margin = candidate_snapshot.get("best_margin_seen")
    current_margin = current_best.get("best_margin_seen")
    if candidate_margin is not None and (
        current_margin is None or float(candidate_margin) > float(current_margin) + 1e-6
    ):
        return True
    if (
        candidate_margin is not None
        and current_margin is not None
        and np.isclose(float(candidate_margin), float(current_margin), atol=1e-6)
    ):
        candidate_risk = candidate_snapshot.get("best_risk_seen")
        current_risk = current_best.get("best_risk_seen")
        if candidate_risk is not None and (
            current_risk is None or float(candidate_risk) < float(current_risk) - 1e-6
        ):
            return True
    return False


def _empty_route_fail_counts() -> dict[str, int]:
    return {
        "cost": 0,
        "violation": 0,
        "final_critical": 0,
        "disruption": 0,
        "missing_semantics": 0,
    }


FINAL_CRITICAL_THRESHOLD_FIELDS: tuple[tuple[str, float], ...] = (
    ("le_1_0", 1.0),
    ("le_0_9583", 23.0 / 24.0),
    ("le_0_5", 0.5),
    ("le_0_25", 0.25),
)

OBJECTIVE_DELTA_FIELDS: tuple[tuple[str, str, int], ...] = (
    ("security", "security_return", 0),
    ("business", "business_return", 1),
    ("cost", "cost_return", 2),
)


def _empty_scalar_summary() -> dict[str, float | int | None]:
    return {
        "count": 0,
        "min": None,
        "median": None,
        "mean": None,
        "max": None,
    }


def _scalar_summary(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return _empty_scalar_summary()
    data = np.asarray(values, dtype=np.float64)
    return {
        "count": int(data.size),
        "min": float(np.min(data)),
        "median": float(np.median(data)),
        "mean": float(np.mean(data)),
        "max": float(np.max(data)),
    }


def _empty_final_critical_threshold_counts() -> dict[str, int]:
    return {field: 0 for field, _ in FINAL_CRITICAL_THRESHOLD_FIELDS}


def _empty_objective_delta_summary() -> dict[str, dict[str, float | int | None]]:
    return {
        objective_name: _empty_scalar_summary()
        for objective_name, _, _ in OBJECTIVE_DELTA_FIELDS
    }


def _empty_gap_direction_summary() -> dict[str, object]:
    return {
        "num_pairs": 0,
        "mean_violation": {
            "worse_count": 0,
            "worse_rate": 0.0,
            "avg_worse_delta": 0.0,
            "avg_all_delta": 0.0,
        },
        "final_critical_compromised_hosts": {
            "worse_count": 0,
            "worse_rate": 0.0,
            "avg_worse_delta": 0.0,
            "avg_all_delta": 0.0,
        },
        "high_disruption_action_rate": {
            "worse_count": 0,
            "worse_rate": 0.0,
            "avg_worse_delta": 0.0,
            "avg_all_delta": 0.0,
        },
        "primary_worsened_metric_counts": {
            "final_critical_compromised_hosts": 0,
            "mean_violation": 0,
            "high_disruption_action_rate": 0,
        },
    }


def _empty_saved_shadow_diagnostics() -> dict[str, object]:
    return {
        "saved_route_preview_cons_accept_count": 0,
        "shadow_route_preview_cons_accept_count": 0,
        "saved_route_preview_near_feasible_count": 0,
        "shadow_route_preview_near_feasible_count": 0,
        "saved_route_fail_primary_counts": _empty_route_fail_counts(),
        "shadow_route_fail_primary_counts": _empty_route_fail_counts(),
        "saved_route_fail_component_counts": _empty_route_fail_counts(),
        "shadow_route_fail_component_counts": _empty_route_fail_counts(),
        "saved_final_critical_threshold_counts": _empty_final_critical_threshold_counts(),
        "shadow_final_critical_threshold_counts": _empty_final_critical_threshold_counts(),
        "saved_final_critical_value_summary": _empty_scalar_summary(),
        "shadow_final_critical_value_summary": _empty_scalar_summary(),
        "saved_objective_delta_vs_parent_summary": _empty_objective_delta_summary(),
        "shadow_objective_delta_vs_parent_summary": _empty_objective_delta_summary(),
        "saved_spread_gain_summary": _empty_scalar_summary(),
        "shadow_spread_gain_summary": _empty_scalar_summary(),
        "gap_direction_summary": _empty_gap_direction_summary(),
    }


def _build_shadow_preview_record(
    *,
    base_record: dict,
    best_snapshot: dict[str, object],
    policy_id: str,
    objective_idx: int,
    round_idx: int,
    operator_source: str,
) -> dict | None:
    objective_vector = best_snapshot.get("best_objective_vector")
    if objective_vector is None:
        return None
    return policy_record(
        policy_id=policy_id,
        checkpoint_path="",
        objective_vector=objective_vector,
        stage="stage2_shadow_preview",
        source="stage2_shadow_preview",
        parent_policy_id=base_record["policy_id"],
        target_objective=int(objective_idx),
        base_objective_vector=base_record["objective_vector"],
        update_index=round_idx,
        archive_role=None,
        operator_source=operator_source,
        security_return=best_snapshot.get("best_security_return"),
        business_return=best_snapshot.get("best_business_return"),
        cost_return=best_snapshot.get("best_cost_return"),
        mean_violation=best_snapshot.get("best_mean_violation"),
        critical_impact_count=best_snapshot.get("best_critical_impact_count"),
        final_critical_compromised=best_snapshot.get(
            "best_final_critical_compromised_hosts"
        ),
        high_disruption_rate=best_snapshot.get("best_high_disruption_action_rate"),
        notes={
            "shadow_preview": True,
            "shadow_snapshot_source": "best_pre_save_snapshot",
            "last_constraint_margins": best_snapshot.get("best_constraint_margins"),
            "constraint_thresholds": best_snapshot.get("best_constraint_thresholds"),
            "constraint_objective_indices": best_snapshot.get(
                "best_constraint_objective_indices"
            ),
            "best_margin_seen": best_snapshot.get("best_margin_seen"),
            "best_risk_seen": best_snapshot.get("best_risk_seen"),
            "best_seen_semantics": best_snapshot.get("best_seen_semantics"),
            "best_relative_cost_ok": best_snapshot.get("best_relative_cost_ok"),
            "best_relative_cost_margin": best_snapshot.get("best_relative_cost_margin"),
        },
    )


def _route_preview_payload(preview_result: dict | None) -> dict | None:
    if preview_result is None:
        return None
    record = dict(preview_result.get("record") or {})
    return {
        "route_decision": preview_result.get("route_decision"),
        "cons_reason": preview_result.get("cons_reason"),
        "uc_reason": preview_result.get("uc_reason"),
        "archive_role": preview_result.get("archive_role"),
        "strict_candidate_eligible": record.get("strict_candidate_eligible"),
        "relative_cost_ok": record.get("relative_cost_ok"),
        "relative_cost_margin": record.get("relative_cost_margin"),
        "security_return": record.get("security_return"),
        "business_return": record.get("business_return"),
        "cost_return": record.get("cost_return"),
        "near_feasible_flag": record.get("near_feasible_flag"),
        "tight_feasible_flag": record.get("tight_feasible_flag"),
        "mean_violation": record.get("mean_violation"),
        "final_critical_compromised_hosts": record.get(
            "final_critical_compromised_hosts"
        ),
        "high_disruption_action_rate": record.get("high_disruption_action_rate"),
        "delta_eu": record.get("delta_eu"),
        "delta_coverage": record.get("delta_coverage"),
        "spread_gain": record.get("spread_gain"),
        "route_fail_components_all": list(
            preview_result.get("route_fail_components_all") or []
        ),
        "route_fail_primary": preview_result.get("route_fail_primary"),
    }


def _saved_vs_shadow_semantic_gap(
    saved_preview: dict | None, shadow_preview: dict | None
) -> dict | None:
    if saved_preview is None or shadow_preview is None:
        return None

    def _delta(metric: str) -> float | None:
        saved_value = _record_metric(saved_preview, metric)
        shadow_value = _record_metric(shadow_preview, metric)
        if saved_value is None or shadow_value is None:
            return None
        return float(saved_value - shadow_value)

    return {
        "mean_violation_delta": _delta("mean_violation"),
        "final_critical_delta": _delta("final_critical_compromised_hosts"),
        "high_disruption_action_rate_delta": _delta("high_disruption_action_rate"),
    }


def _preview_objective_deltas(
    preview_payload: dict | None,
    *,
    parent_objectives: list[float] | np.ndarray | None,
) -> dict[str, float | None]:
    deltas = {
        objective_name: None for objective_name, _, _ in OBJECTIVE_DELTA_FIELDS
    }
    if preview_payload is None or parent_objectives is None:
        return deltas
    parent_values = np.asarray(parent_objectives, dtype=np.float32)
    for objective_name, preview_key, index in OBJECTIVE_DELTA_FIELDS:
        child_value = _record_metric(preview_payload, preview_key)
        if child_value is None or parent_values.size <= index:
            continue
        deltas[objective_name] = float(child_value - float(parent_values[index]))
    return deltas


def _primary_worsened_metric(
    gap_payload: dict[str, float | None] | None,
    *,
    cons_thresholds: dict[str, float],
) -> str | None:
    if gap_payload is None:
        return None

    thresholds = {
        "final_critical_compromised_hosts": max(
            float(cons_thresholds.get("final_critical_near", 0.25)), 1e-6
        ),
        "mean_violation": max(float(cons_thresholds.get("violation", 0.5)), 1e-6),
        "high_disruption_action_rate": max(
            float(cons_thresholds.get("high_disruption", 1.0)), 1e-6
        ),
    }
    normalized_positive = {
        "final_critical_compromised_hosts": max(
            0.0, float(gap_payload.get("final_critical_delta") or 0.0)
        )
        / thresholds["final_critical_compromised_hosts"],
        "mean_violation": max(
            0.0, float(gap_payload.get("mean_violation_delta") or 0.0)
        )
        / thresholds["mean_violation"],
        "high_disruption_action_rate": max(
            0.0, float(gap_payload.get("high_disruption_action_rate_delta") or 0.0)
        )
        / thresholds["high_disruption_action_rate"],
    }
    positive_metrics = [
        metric for metric, score in normalized_positive.items() if float(score) > 0.0
    ]
    if not positive_metrics:
        return None
    tie_break_order = {
        "final_critical_compromised_hosts": 0,
        "mean_violation": 1,
        "high_disruption_action_rate": 2,
    }
    return sorted(
        positive_metrics,
        key=lambda metric: (
            -float(normalized_positive.get(metric, 0.0)),
            tie_break_order.get(metric, 99),
        ),
    )[0]


def _aggregate_saved_shadow_diagnostics(
    results: list[dict],
    *,
    cons_thresholds: dict[str, float],
) -> dict[str, object]:
    aggregate = _empty_saved_shadow_diagnostics()
    metric_delta_keys = {
        "mean_violation": "mean_violation_delta",
        "final_critical_compromised_hosts": "final_critical_delta",
        "high_disruption_action_rate": "high_disruption_action_rate_delta",
    }
    all_deltas: dict[str, list[float]] = {metric: [] for metric in metric_delta_keys}
    worse_deltas: dict[str, list[float]] = {metric: [] for metric in metric_delta_keys}
    final_critical_values: dict[str, list[float]] = {"saved": [], "shadow": []}
    spread_gain_values: dict[str, list[float]] = {"saved": [], "shadow": []}
    objective_delta_values: dict[str, dict[str, list[float]]] = {
        "saved": {
            objective_name: [] for objective_name, _, _ in OBJECTIVE_DELTA_FIELDS
        },
        "shadow": {
            objective_name: [] for objective_name, _, _ in OBJECTIVE_DELTA_FIELDS
        },
    }

    for result in results:
        if result.get("archive_branch") != "cons":
            continue

        for prefix in ("saved", "shadow"):
            preview = result.get(f"{prefix}_route_preview")
            if preview is None:
                continue
            if preview.get("archive_role") == "cons":
                aggregate[f"{prefix}_route_preview_cons_accept_count"] += 1
            if bool(preview.get("near_feasible_flag")) or bool(
                preview.get("tight_feasible_flag")
            ):
                aggregate[f"{prefix}_route_preview_near_feasible_count"] += 1
            for component in preview.get("route_fail_components_all") or []:
                counts = aggregate[f"{prefix}_route_fail_component_counts"]
                if component in counts:
                    counts[component] += 1
            primary = preview.get("route_fail_primary")
            primary_counts = aggregate[f"{prefix}_route_fail_primary_counts"]
            if primary in primary_counts:
                primary_counts[primary] += 1
            final_critical_value = _record_metric(
                preview, "final_critical_compromised_hosts"
            )
            if final_critical_value is not None:
                final_critical_values[prefix].append(float(final_critical_value))
                threshold_counts = aggregate[
                    f"{prefix}_final_critical_threshold_counts"
                ]
                for field, threshold in FINAL_CRITICAL_THRESHOLD_FIELDS:
                    if float(final_critical_value) <= float(threshold) + 1e-9:
                        threshold_counts[field] += 1
            spread_gain = _record_metric(preview, "spread_gain")
            if spread_gain is not None:
                spread_gain_values[prefix].append(float(spread_gain))
            for objective_name, _, _ in OBJECTIVE_DELTA_FIELDS:
                objective_delta = result.get(f"{prefix}_{objective_name}_delta_vs_parent")
                if objective_delta is None:
                    continue
                objective_delta_values[prefix][objective_name].append(
                    float(objective_delta)
                )

        gap_payload = result.get("saved_vs_shadow_semantic_gap")
        if gap_payload is None:
            continue
        aggregate["gap_direction_summary"]["num_pairs"] += 1
        for metric, delta_key in metric_delta_keys.items():
            delta = gap_payload.get(delta_key)
            if delta is None:
                continue
            delta_value = float(delta)
            all_deltas[metric].append(delta_value)
            if delta_value > 0.0:
                worse_deltas[metric].append(delta_value)

        primary_metric = _primary_worsened_metric(
            gap_payload, cons_thresholds=cons_thresholds
        )
        if primary_metric is not None:
            aggregate["gap_direction_summary"]["primary_worsened_metric_counts"][
                primary_metric
            ] += 1

    num_pairs = int(aggregate["gap_direction_summary"]["num_pairs"])
    for metric in metric_delta_keys:
        metric_summary = aggregate["gap_direction_summary"][metric]
        metric_summary["worse_count"] = len(worse_deltas[metric])
        metric_summary["worse_rate"] = (
            float(len(worse_deltas[metric]) / num_pairs) if num_pairs > 0 else 0.0
        )
        metric_summary["avg_worse_delta"] = (
            float(np.mean(worse_deltas[metric])) if worse_deltas[metric] else 0.0
        )
        metric_summary["avg_all_delta"] = (
            float(np.mean(all_deltas[metric])) if all_deltas[metric] else 0.0
        )

    for prefix in ("saved", "shadow"):
        aggregate[f"{prefix}_final_critical_value_summary"] = _scalar_summary(
            final_critical_values[prefix]
        )
        aggregate[f"{prefix}_spread_gain_summary"] = _scalar_summary(
            spread_gain_values[prefix]
        )
        aggregate[f"{prefix}_objective_delta_vs_parent_summary"] = {
            objective_name: _scalar_summary(values)
            for objective_name, values in objective_delta_values[prefix].items()
        }

    return aggregate


def _aggregate_cons_progress(results: list[dict]) -> dict[str, int]:
    aggregate = {
        "best_near_feasible_children": 0,
        "strict_candidate_count": 0,
        "cons_margin_improved_attempts": 0,
        "cons_final_critical_improved_attempts": 0,
        "cons_mean_violation_improved_attempts": 0,
    }
    for result in results:
        if result.get("archive_branch") != "cons":
            continue
        if bool(result.get("best_near_feasible_flag")):
            aggregate["best_near_feasible_children"] += 1
        if bool(result.get("strict_candidate_eligible")):
            aggregate["strict_candidate_count"] += 1
        min_margin_delta = result.get("best_min_margin_delta_vs_parent")
        if min_margin_delta is not None and float(min_margin_delta) > 0.0:
            aggregate["cons_margin_improved_attempts"] += 1
        final_critical_delta = result.get("best_final_critical_delta_vs_parent")
        if final_critical_delta is not None and float(final_critical_delta) < 0.0:
            aggregate["cons_final_critical_improved_attempts"] += 1
        mean_violation_delta = result.get("best_mean_violation_delta_vs_parent")
        if mean_violation_delta is not None and float(mean_violation_delta) < 0.0:
            aggregate["cons_mean_violation_improved_attempts"] += 1
    return aggregate


def _run_stage2_extension_for_parent(
    *,
    env: MiniCageMORLEnv,
    device: torch.device,
    config: Stage2Config,
    ipo_config: IPOConfig,
    num_updates: int,
    run_dir: Path,
    base_record: dict,
    archive_seed_thresholds: dict[str, float],
    objective_idx: int,
    round_idx: int,
    policy_counter: int,
    selection_component: dict[str, float | list[float]],
    selection_score: float,
    selection_rank: int,
    archive_branch: str,
    operator_source: str,
    beta_mode: str,
) -> tuple[dict | None, dict]:
    actor_critic = ActorCritic(
        obs_dim=env.obs_dim,
        action_dim=env.action_dim,
        obj_dim=env.obj_dim,
        hidden_sizes=(config.model.hidden_size, config.model.hidden_size),
    ).to(device)
    actor_critic.load_state_dict(
        torch.load(
            base_record["checkpoint_path"],
            map_location=device,
            weights_only=True,
        )
    )
    trainer = IPOTrainer(actor_critic, ipo_config)
    storage = VectorRolloutStorage(
        num_steps=config.rollout.num_steps,
        num_envs=config.env.num_envs,
        obs_dim=env.obs_dim,
        obj_dim=env.obj_dim,
        device=device,
    )
    current_reference = np.asarray(base_record["objective_vector"], dtype=np.float32)
    best_feasible_state = None
    best_feasible_objectives = None
    best_feasible_constraint_margins = None
    best_feasible_constraint_thresholds = None
    best_feasible_constraint_objective_indices: list[int] = []
    best_feasible_semantics: dict[str, float] | None = None
    best_pre_save_snapshot: dict[str, object] | None = None
    successful_updates = 0
    terminated_due_to_constraints = False
    consecutive_constraint_failures = 0
    last_constraint_margins = None
    last_constraint_thresholds = None
    last_constraint_objective_indices: list[int] = []
    last_trainer_stats: dict[str, float] = {}
    cons_risk_rollout_summaries: list[dict[str, float | int | str]] = []

    if beta_mode == "dynamic":
        beta_value, beta_components = compute_dynamic_beta(
            selection_component,
            objective_idx,
            round_idx,
            config.extension_rounds,
            config.ipo.beta_min,
            config.ipo.beta_max,
            config.ipo.schedule_weights,
        )
    else:
        beta_value = float(config.ipo.beta)
        beta_components = {
            "crowding": float(selection_component.get("crowding_score", 0.0)),
            "target_expansion": float(selection_component.get("expansion_potential", 0.0)),
            "low_risk": float(selection_component.get("low_risk_score", 1.0)),
            "progress": float(round_idx / max(config.extension_rounds - 1, 1)),
            "strictness": 0.0,
        }

    for _ in range(config.constrained_updates):
        for _ in range(num_updates):
            _, next_value, risk_storage, rollout_risk_summary = _collect_rollout_stage2(
                env,
                actor_critic,
                storage,
                device,
                semantic_penalty_coef=float(config.semantic_penalty_coef),
                semantic_penalty_weights=dict(config.semantic_penalty_weights),
                cons_risk_mode=(
                    config.cons_risk_mode if archive_branch == "cons" else "none"
                ),
                cvar_alpha=float(config.cvar_alpha),
                cvar_metric=str(config.cvar_metric),
                cvar_penalty_coef=float(config.cvar_penalty_coef),
                cvar_metric_weights=dict(config.cvar_metric_weights),
                archive_seed_thresholds=dict(archive_seed_thresholds),
                cons_thresholds=dict(config.cons_thresholds),
                cons_risk_objective_mode=str(config.cons_risk_objective_mode),
                cons_risk_penalty_coef=float(config.cons_risk_penalty_coef),
            )
            if archive_branch == "cons":
                cons_risk_rollout_summaries.append(rollout_risk_summary)
            storage.compute_returns(next_value, ipo_config.gamma, ipo_config.gae_lambda)
            last_trainer_stats = trainer.update(
                storage,
                objective_idx,
                current_reference,
                beta_override=beta_value,
                use_barrier=(config.extension_mode == "constrained"),
                risk_storage=(
                    risk_storage
                    if archive_branch == "cons"
                    and config.cons_risk_mode == "strict_aligned_cvar"
                    else None
                ),
                risk_objective_mode=(
                    str(config.cons_risk_objective_mode)
                    if archive_branch == "cons"
                    and config.cons_risk_mode == "strict_aligned_cvar"
                    else "none"
                ),
                risk_penalty_coef=(
                    float(config.cons_risk_penalty_coef)
                    if archive_branch == "cons"
                    and config.cons_risk_mode == "strict_aligned_cvar"
                    else 0.0
                ),
            )
        candidate_semantics: dict[str, float] = {}
        if archive_branch == "cons":
            candidate_objectives, candidate_semantics = _evaluate_policy_with_semantics(
                env,
                actor_critic,
                device,
                episodes=config.eval.eval_episodes,
            )
        else:
            candidate_objectives = evaluate_policy(
                env,
                actor_critic,
                device,
                episodes=config.eval.eval_episodes,
            )
        if config.extension_mode == "constrained":
            reference_before_eval = np.asarray(current_reference, dtype=np.float32).copy()
            candidate_margins = candidate_objectives - (beta_value * reference_before_eval)
            constraint_margins = np.delete(candidate_margins, objective_idx)
            last_constraint_margins = constraint_margins.astype(np.float32)
            (
                last_constraint_objective_indices,
                last_constraint_thresholds,
            ) = _constraint_thresholds_for_objective(
                reference_before_eval,
                objective_idx,
                beta_value,
            )
            if archive_branch == "cons":
                snapshot = _build_pre_save_cons_snapshot(
                    base_record=base_record,
                    reference_objectives=reference_before_eval,
                    candidate_objectives=candidate_objectives,
                    candidate_constraint_margins=last_constraint_margins,
                    objective_idx=objective_idx,
                    beta_value=beta_value,
                    cons_thresholds=dict(config.cons_thresholds),
                    cvar_metric_weights=dict(config.cvar_metric_weights),
                    semantic_metrics=dict(candidate_semantics),
                )
                if _should_replace_best_snapshot(best_pre_save_snapshot, snapshot):
                    best_pre_save_snapshot = dict(snapshot)
            is_feasible = bool(np.all(constraint_margins > config.constraint_tolerance))
            if not is_feasible:
                consecutive_constraint_failures += 1
                if consecutive_constraint_failures >= max(
                    int(config.max_consecutive_constraint_failures), 1
                ):
                    terminated_due_to_constraints = True
                    break
                continue
            consecutive_constraint_failures = 0
        else:
            last_constraint_margins = None

        successful_updates += 1
        current_reference = candidate_objectives
        best_feasible_objectives = candidate_objectives.copy()
        best_feasible_state = copy.deepcopy(actor_critic.state_dict())
        best_feasible_constraint_margins = (
            None if last_constraint_margins is None else last_constraint_margins.copy()
        )
        best_feasible_constraint_thresholds = (
            None
            if last_constraint_thresholds is None
            else np.asarray(last_constraint_thresholds, dtype=np.float32).copy()
        )
        best_feasible_constraint_objective_indices = list(
            last_constraint_objective_indices
        )
        if archive_branch == "cons":
            best_feasible_semantics = dict(candidate_semantics)

    cons_risk_summary = _summarize_cons_risk(
        [{"archive_branch": archive_branch, **summary} for summary in cons_risk_rollout_summaries],
        cons_risk_mode=(config.cons_risk_mode if archive_branch == "cons" else "none"),
        cvar_alpha=float(config.cvar_alpha),
        cvar_metric=str(config.cvar_metric),
    )

    result = {
        "parent_policy_id": base_record["policy_id"],
        "parent_id": base_record["policy_id"],
        "parent_objectives": np.asarray(
            base_record["objective_vector"], dtype=np.float32
        ).tolist(),
        "archive_branch": archive_branch,
        "target_objective": int(objective_idx),
        "objective_idx": int(objective_idx),
        "generated_policy_id": None,
        "successful_constrained_updates": successful_updates,
        "terminated_due_to_constraints": terminated_due_to_constraints,
        "selection_score": selection_score,
        "selection_rank": selection_rank,
        "dynamic_beta": beta_value,
        "beta_components": beta_components,
        "operator_source": operator_source,
        "beta_mode": beta_mode,
        "max_consecutive_constraint_failures": int(
            config.max_consecutive_constraint_failures
        ),
        "consecutive_constraint_failures": int(consecutive_constraint_failures),
        "constraint_thresholds": (
            None
            if last_constraint_thresholds is None
            else np.asarray(last_constraint_thresholds, dtype=np.float32).tolist()
        ),
        "constraint_objective_indices": list(last_constraint_objective_indices),
        "last_constraint_margins": (
            None if last_constraint_margins is None else last_constraint_margins.tolist()
        ),
        "failure_stage": None,
        "termination_reason": None,
        "best_margin_seen": None,
        "best_risk_seen": None,
        "best_seen_semantics": None,
        "best_near_feasible_flag": False,
        "best_tight_feasible_flag": False,
        "best_min_margin_delta_vs_parent": None,
        "best_final_critical_delta_vs_parent": None,
        "best_mean_violation_delta_vs_parent": None,
        "saved_route_preview": None,
        "shadow_route_preview": None,
        "saved_vs_shadow_semantic_gap": None,
        "saved_security_delta_vs_parent": None,
        "saved_business_delta_vs_parent": None,
        "saved_cost_delta_vs_parent": None,
        "shadow_security_delta_vs_parent": None,
        "shadow_business_delta_vs_parent": None,
        "shadow_cost_delta_vs_parent": None,
        "ipo_stats": last_trainer_stats,
        **cons_risk_summary,
    }
    if best_pre_save_snapshot is not None:
        result.update(best_pre_save_snapshot)
    if best_feasible_state is None or best_feasible_objectives is None:
        if archive_branch == "cons":
            if terminated_due_to_constraints:
                result["failure_stage"] = "constraint_margin_fail"
                result["termination_reason"] = (
                    "max_consecutive_constraint_failures_reached"
                )
            else:
                result["failure_stage"] = "no_best_feasible_checkpoint"
                result["termination_reason"] = "no_best_feasible_checkpoint"
        return None, result

    checkpoint_path = run_dir / f"policy_stage2_{policy_counter:03d}.pt"
    torch.save(best_feasible_state, checkpoint_path)
    policy_id = f"stage2_ext_{policy_counter:03d}_obj_{objective_idx}"
    objectives = np.asarray(best_feasible_objectives, dtype=np.float32)
    feasibility = _record_feasibility_metrics(
        last_constraint_margins=best_feasible_constraint_margins,
        extension_mode=config.extension_mode,
        constraint_tolerance=config.constraint_tolerance,
        near_tolerance=float(config.cons_thresholds.get("violation", 0.5)),
    )
    record = policy_record(
        policy_id=policy_id,
        checkpoint_path=str(checkpoint_path.resolve()),
        objective_vector=objectives.tolist(),
        stage="stage2",
        source="stage2",
        parent_policy_id=base_record["policy_id"],
        target_objective=int(objective_idx),
        base_objective_vector=base_record["objective_vector"],
        update_index=round_idx,
        archive_role=None,
        operator_source=operator_source,
        **_record_objective_metrics(objectives),
        critical_impact_count=(
            None
            if best_feasible_semantics is None
            else best_feasible_semantics.get("critical_impact_count")
        ),
        final_critical_compromised=(
            None
            if best_feasible_semantics is None
            else best_feasible_semantics.get("final_critical_compromised_hosts")
        ),
        high_disruption_rate=(
            None
            if best_feasible_semantics is None
            else best_feasible_semantics.get("high_disruption_action_rate")
        ),
        **feasibility,
        notes={
            "extension_round": round_idx,
            "selection_score": selection_score,
            "selection_rank": selection_rank,
            "crowding_score": float(selection_component.get("crowding_score", 0.0)),
            "expansion_potential": float(
                selection_component.get("expansion_potential", 0.0)
            ),
            "constraint_risk": float(selection_component.get("constraint_risk", 0.0)),
            "utility_coverage_gain": float(
                selection_component.get("utility_coverage_gain", 0.0)
            ),
            "dynamic_beta": beta_value,
            "beta_mode": beta_mode,
            "archive_branch": archive_branch,
            "operator_source": operator_source,
            "extension_mode": config.extension_mode,
            "beta_components": beta_components,
            "successful_constrained_updates": successful_updates,
            "terminated_due_to_constraints": terminated_due_to_constraints,
            "constraint_tolerance": config.constraint_tolerance,
            "constraint_thresholds": (
                None
                if best_feasible_constraint_thresholds is None
                else best_feasible_constraint_thresholds.tolist()
            ),
            "constraint_objective_indices": list(
                best_feasible_constraint_objective_indices
            ),
            "max_consecutive_constraint_failures": int(
                config.max_consecutive_constraint_failures
            ),
            "consecutive_constraint_failures": int(consecutive_constraint_failures),
            "last_constraint_margins": (
                best_feasible_constraint_margins.tolist()
                if best_feasible_constraint_margins is not None
                else None
            ),
            "objective_improvement": float(
                objectives[objective_idx]
                - np.asarray(base_record["objective_vector"], dtype=np.float32)[objective_idx]
            ),
            "ipo_stats": last_trainer_stats,
            "cons_risk_summary": cons_risk_summary,
        },
    )
    result.update(
        {
            "generated_policy_id": policy_id,
            "objective_improvement": record["notes"]["objective_improvement"],
            "feasible_flag": record.get("feasible_flag"),
            "near_feasible_flag": record.get("near_feasible_flag"),
            "tight_feasible_flag": record.get("tight_feasible_flag"),
            "mean_violation": record.get("mean_violation"),
        }
    )
    return record, result


def _train_stage2_dual(config: Stage2Config) -> Path:
    if not config.stage1_buffer:
        raise ValueError("stage1_buffer must be provided")
    set_seed(config.seed)
    payload = load_policy_buffer(config.stage1_buffer)
    records: list[dict] = list(payload["records"])
    run_dir = ensure_dir(Path(config.output_dir) / f"run_{uuid.uuid4().hex[:8]}")
    device = torch.device("cpu")

    env = MiniCageMORLEnv(
        num_envs=config.env.num_envs,
        red_policy=config.env.red_policy,
        remove_bugs=config.env.remove_bugs,
        max_steps=config.env.max_episode_steps,
        seed=config.env.seed,
    )
    ipo_config = IPOConfig(
        clip_param=config.ipo.clip_param,
        ppo_epochs=config.ipo.ppo_epochs,
        num_mini_batch=config.ipo.num_mini_batch,
        value_loss_coef=config.ipo.value_loss_coef,
        entropy_coef=config.ipo.entropy_coef,
        learning_rate=config.ipo.learning_rate,
        max_grad_norm=config.ipo.max_grad_norm,
        barrier_coef=config.ipo.barrier_coef,
        beta=config.ipo.beta,
        gamma=config.ipo.gamma,
        gae_lambda=config.ipo.gae_lambda,
        eps=config.ipo.eps,
    )
    preferences = _selection_preferences(config, env.obj_dim)
    manager = DualArchiveManager(
        cons_thresholds=dict(config.cons_thresholds),
        uc_thresholds=dict(config.uc_thresholds),
        selector_penalty_weights=dict(config.selector_penalty_weights),
        preferences=preferences,
        utility_tolerance=config.selection.utility_tolerance,
        seed_uc_size=config.num_uc_parents,
        route_mode=config.route_mode,
        metadata=payload.get("metadata", {}),
        buffer_path=config.stage1_buffer,
        semantic_eval_episodes=config.eval.eval_episodes,
        archive_seed_thresholds=payload.get("metadata", {}).get(
            "archive_seed_thresholds", {}
        ),
    )
    manager.seed_from_stage1(records)

    policy_counter = 0
    round_summaries: list[dict] = []
    diagnostics = {
        "archive_mode": "dual",
        "selection_mode": {
            "cons": _operator_settings(config.cons_operator_mode)[0],
            "uc": _operator_settings(config.uc_operator_mode)[0],
        },
        "beta_schedule_mode": {
            "cons": _operator_settings(config.cons_operator_mode)[1],
            "uc": _operator_settings(config.uc_operator_mode)[1],
        },
        "selection_preferences": preferences,
        "archive_rule_version": manager.archive_rule_version,
        "archive_seed_thresholds": dict(manager.archive_seed_thresholds),
        "cons_attempted_children": 0,
        "cons_successful_children": 0,
        "cons_routed_children": 0,
        "cons_rejected_by_cost_gate": 0,
        "cons_rejected_by_feasibility": 0,
        "cons_risk_mode": config.cons_risk_mode,
        "cons_cvar_alpha": float(config.cvar_alpha),
        "cons_cvar_metric": str(config.cvar_metric),
        "cons_cvar_estimate_mean": 0.0,
        "cons_cvar_estimate_tail": 0.0,
        "cons_risk_penalty_mean": 0.0,
        "cons_rejected_by_risk_gate": 0,
        "cons_risk_rollout_count": 0,
        "cons_tail_env_count": 0,
        "cons_tail_risk_mean": 0.0,
        "cons_tail_risk_max": 0.0,
        "cons_episode_risk_mean": 0.0,
        "cons_episode_risk_tail": 0.0,
        "cons_risk_objective_mode": str(config.cons_risk_objective_mode),
        "cons_risk_penalty_coef": float(config.cons_risk_penalty_coef),
        "cons_child_failed_by_violation": 0,
        "cons_child_failed_by_final_critical": 0,
        "cons_child_failed_by_disruption": 0,
        "cons_child_failed_by_multiple": 0,
        "best_near_feasible_children": 0,
        "strict_candidate_count": 0,
        "cons_margin_improved_attempts": 0,
        "cons_final_critical_improved_attempts": 0,
        "cons_mean_violation_improved_attempts": 0,
        "round_diagnostics": [],
        **_empty_saved_shadow_diagnostics(),
    }
    num_updates = max(
        config.total_timesteps_per_update
        // (config.rollout.num_steps * config.env.num_envs),
        1,
    )

    for round_idx in range(config.extension_rounds):
        manager.refresh_union_front()
        cons_parents = manager.select_cons_parents(config.num_cons_parents)
        uc_parents = manager.select_uc_parents(config.num_uc_parents)
        round_summary = {
            "round_index": round_idx,
            "archive_mode": "dual",
            "num_records_before_round": len(records),
            "cons_size_before_round": len(manager.cons_records),
            "uc_size_before_round": len(manager.uc_records),
            "union_front_size_before_round": len(manager.union_front),
            "cons_parent_ids": [record["policy_id"] for record in cons_parents],
            "uc_parent_ids": [record["policy_id"] for record in uc_parents],
            "cons_generated_policy_ids": [],
            "uc_generated_policy_ids": [],
            "discarded_policy_ids": [],
            "cons_attempted_children": 0,
            "cons_successful_children": 0,
            "cons_routed_children": 0,
            "cons_rejected_by_cost_gate": 0,
            "cons_rejected_by_feasibility": 0,
            "cons_risk_mode": config.cons_risk_mode,
            "cons_cvar_alpha": float(config.cvar_alpha),
            "cons_cvar_metric": str(config.cvar_metric),
            "cons_cvar_estimate_mean": 0.0,
            "cons_cvar_estimate_tail": 0.0,
            "cons_risk_penalty_mean": 0.0,
            "cons_rejected_by_risk_gate": 0,
            "cons_risk_rollout_count": 0,
            "cons_tail_env_count": 0,
            "cons_tail_risk_mean": 0.0,
            "cons_tail_risk_max": 0.0,
            "cons_episode_risk_mean": 0.0,
            "cons_episode_risk_tail": 0.0,
            "cons_risk_objective_mode": str(config.cons_risk_objective_mode),
            "cons_risk_penalty_coef": float(config.cons_risk_penalty_coef),
            "cons_child_failed_by_violation": 0,
            "cons_child_failed_by_final_critical": 0,
            "cons_child_failed_by_disruption": 0,
            "cons_child_failed_by_multiple": 0,
            "best_near_feasible_children": 0,
            "strict_candidate_count": 0,
            "cons_margin_improved_attempts": 0,
            "cons_final_critical_improved_attempts": 0,
            "cons_mean_violation_improved_attempts": 0,
            "extension_results": [],
            **_empty_saved_shadow_diagnostics(),
        }
        branch_diagnostics: dict[str, dict] = {}
        branches = (
            ("cons", cons_parents, config.cons_operator_mode, manager.cons_records),
            ("uc", uc_parents, config.uc_operator_mode, manager.uc_records),
        )
        for branch_name, parents, operator_mode, archive_records in branches:
            selection_mode, beta_mode = _operator_settings(operator_mode)
            selected_scores, selected_components, selected_ranks = (
                _selection_diagnostics_for_records(
                    archive_records or manager.union_records,
                    parents,
                    selection_mode=selection_mode,
                    config=config,
                    preferences=preferences,
                )
            )
            branch_diagnostics[branch_name] = {
                "operator_mode": operator_mode,
                "selection_mode": selection_mode,
                "beta_schedule_mode": beta_mode,
                "selected_policy_ids": [record["policy_id"] for record in parents],
                "selected_policy_scores": dict(selected_scores),
                "selected_policy_components": {
                    policy_id: dict(components)
                    for policy_id, components in selected_components.items()
                },
            }
            for base_record in parents:
                selection_component = dict(
                    selected_components.get(
                        base_record["policy_id"],
                        {
                            "crowding_score": 0.0,
                            "expansion_potential": 0.0,
                            "target_expansion_by_objective": [],
                            "constraint_risk": 0.0,
                            "low_risk_score": 1.0,
                            "utility_coverage_gain": 0.0,
                        },
                    )
                )
                selection_score = float(selected_scores.get(base_record["policy_id"], 0.0))
                selection_rank = int(selected_ranks.get(base_record["policy_id"], 0))
                for objective_idx in range(env.obj_dim):
                    if branch_name == "cons":
                        round_summary["cons_attempted_children"] += 1
                        diagnostics["cons_attempted_children"] += 1
                    record, result = _run_stage2_extension_for_parent(
                        env=env,
                        device=device,
                        config=config,
                        ipo_config=ipo_config,
                        num_updates=num_updates,
                        run_dir=run_dir,
                        base_record=base_record,
                        archive_seed_thresholds=dict(manager.archive_seed_thresholds),
                        objective_idx=objective_idx,
                        round_idx=round_idx,
                        policy_counter=policy_counter,
                        selection_component=selection_component,
                        selection_score=selection_score,
                        selection_rank=selection_rank,
                        archive_branch=branch_name,
                        operator_source=operator_mode,
                        beta_mode=beta_mode,
                    )
                    if record is not None:
                        if branch_name == "cons":
                            saved_preview_result = manager.preview_route(record)
                            result["saved_route_preview"] = _route_preview_payload(
                                saved_preview_result
                            )
                            for (
                                objective_name,
                                objective_delta,
                            ) in _preview_objective_deltas(
                                result["saved_route_preview"],
                                parent_objectives=result.get("parent_objectives"),
                            ).items():
                                result[
                                    f"saved_{objective_name}_delta_vs_parent"
                                ] = objective_delta
                            shadow_record = _build_shadow_preview_record(
                                base_record=base_record,
                                best_snapshot=result,
                                policy_id=f"{record['policy_id']}__shadow_preview",
                                objective_idx=objective_idx,
                                round_idx=round_idx,
                                operator_source=operator_mode,
                            )
                            if shadow_record is not None:
                                shadow_preview_result = manager.preview_route(
                                    shadow_record
                                )
                                result["shadow_route_preview"] = _route_preview_payload(
                                    shadow_preview_result
                                )
                                for (
                                    objective_name,
                                    objective_delta,
                                ) in _preview_objective_deltas(
                                    result["shadow_route_preview"],
                                    parent_objectives=result.get("parent_objectives"),
                                ).items():
                                    result[
                                        f"shadow_{objective_name}_delta_vs_parent"
                                    ] = objective_delta
                                result["saved_vs_shadow_semantic_gap"] = (
                                    _saved_vs_shadow_semantic_gap(
                                        result["saved_route_preview"],
                                        result["shadow_route_preview"],
                                    )
                                )
                            route_result = manager.insert_preview(saved_preview_result)
                        else:
                            route_result = manager.route_and_insert(record)
                        annotated = route_result["record"]
                        if branch_name == "cons":
                            round_summary["cons_successful_children"] += 1
                            diagnostics["cons_successful_children"] += 1
                            if route_result["route_decision"] == "accepted_cons":
                                round_summary["cons_routed_children"] += 1
                                diagnostics["cons_routed_children"] += 1
                            elif route_result["route_decision"] == "rejected_cost_gate":
                                round_summary["cons_rejected_by_cost_gate"] += 1
                                diagnostics["cons_rejected_by_cost_gate"] += 1
                            elif route_result["route_decision"] == "rejected_feasibility":
                                round_summary["cons_rejected_by_feasibility"] += 1
                                diagnostics["cons_rejected_by_feasibility"] += 1
                        if route_result["accepted"]:
                            records.append(annotated)
                            role_key = f"{annotated['archive_role']}_generated_policy_ids"
                            round_summary[role_key].append(annotated["policy_id"])
                        else:
                            round_summary["discarded_policy_ids"].append(record["policy_id"])
                        result.update(manager.child_diagnostics(annotated))
                        result["route_decision"] = route_result["route_decision"]
                        result["cons_reason"] = route_result.get("cons_reason")
                        result["uc_reason"] = route_result.get("uc_reason")
                        if branch_name == "cons":
                            if route_result["route_decision"] == "accepted_cons":
                                result["failure_stage"] = "accepted_cons"
                                result["termination_reason"] = "accepted_cons"
                            else:
                                result["failure_stage"] = "route_rejected_after_save"
                                result["termination_reason"] = route_result[
                                    "route_decision"
                                ]
                        policy_counter += 1
                    round_summary["extension_results"].append(result)

        round_summary.update(
            _summarize_cons_risk(
                round_summary["extension_results"],
                cons_risk_mode=str(config.cons_risk_mode),
                cvar_alpha=float(config.cvar_alpha),
                cvar_metric=str(config.cvar_metric),
            )
        )
        round_summary.update(
            _strict_failure_buckets(
                round_summary["extension_results"],
                cons_thresholds=dict(config.cons_thresholds),
            )
        )
        round_summary.update(_aggregate_cons_progress(round_summary["extension_results"]))
        round_summary.update(
            _aggregate_saved_shadow_diagnostics(
                round_summary["extension_results"],
                cons_thresholds=dict(config.cons_thresholds),
            )
        )
        manager.refresh_union_front()
        round_summary.update(
            {
                "num_records_after_round": len(records),
                "cons_size_after_round": len(manager.cons_records),
                "uc_size_after_round": len(manager.uc_records),
                "union_front_size_after_round": len(manager.union_front),
                "branch_diagnostics": branch_diagnostics,
            }
        )
        round_summaries.append(round_summary)
        diagnostics["round_diagnostics"].append(
            {
                "round_index": round_idx,
                "archive_mode": "dual",
                "cons_parent_ids": round_summary["cons_parent_ids"],
                "uc_parent_ids": round_summary["uc_parent_ids"],
                "cons_generated_policy_ids": round_summary["cons_generated_policy_ids"],
                "uc_generated_policy_ids": round_summary["uc_generated_policy_ids"],
                "discarded_policy_ids": round_summary["discarded_policy_ids"],
                "branch_diagnostics": branch_diagnostics,
                "child_routes": [
                    {
                        key: result.get(key)
                        for key in (
                            "generated_policy_id",
                            "archive_role",
                            "operator_source",
                            "delta_eu",
                            "delta_coverage",
                            "spread_gain",
                            "tight_feasible_flag",
                            "high_disruption_rate",
                            "high_disruption_action_rate",
                            "mean_violation",
                            "final_critical_compromised_hosts",
                            "strict_candidate_eligible",
                            "relative_cost_ok",
                            "route_decision",
                            "cons_reason",
                            "uc_reason",
                            "failure_stage",
                            "termination_reason",
                            "saved_route_preview",
                            "shadow_route_preview",
                            "saved_vs_shadow_semantic_gap",
                            "saved_security_delta_vs_parent",
                            "saved_business_delta_vs_parent",
                            "saved_cost_delta_vs_parent",
                            "shadow_security_delta_vs_parent",
                            "shadow_business_delta_vs_parent",
                            "shadow_cost_delta_vs_parent",
                        )
                    }
                    for result in round_summary["extension_results"]
                    if result.get("generated_policy_id") is not None
                ],
                "cons_pre_save_attempts": [
                    {
                        key: result.get(key)
                        for key in (
                            "parent_id",
                            "objective_idx",
                            "generated_policy_id",
                            "failure_stage",
                            "termination_reason",
                            "parent_objectives",
                            "constraint_thresholds",
                            "constraint_objective_indices",
                            "last_constraint_margins",
                            "best_margin_seen",
                            "best_risk_seen",
                            "best_seen_semantics",
                            "best_near_feasible_flag",
                            "best_tight_feasible_flag",
                            "best_min_margin_delta_vs_parent",
                            "best_final_critical_delta_vs_parent",
                            "best_mean_violation_delta_vs_parent",
                            "route_decision",
                        )
                    }
                    for result in round_summary["extension_results"]
                    if result.get("archive_branch") == "cons"
                ],
                "cons_attempted_children": round_summary["cons_attempted_children"],
                "cons_successful_children": round_summary["cons_successful_children"],
                "cons_routed_children": round_summary["cons_routed_children"],
                "cons_rejected_by_cost_gate": round_summary["cons_rejected_by_cost_gate"],
                "cons_rejected_by_feasibility": round_summary["cons_rejected_by_feasibility"],
                "cons_risk_mode": round_summary["cons_risk_mode"],
                "cons_cvar_alpha": round_summary["cons_cvar_alpha"],
                "cons_cvar_metric": round_summary["cons_cvar_metric"],
                "cons_cvar_estimate_mean": round_summary["cons_cvar_estimate_mean"],
                "cons_cvar_estimate_tail": round_summary["cons_cvar_estimate_tail"],
                "cons_risk_penalty_mean": round_summary["cons_risk_penalty_mean"],
                "cons_rejected_by_risk_gate": round_summary["cons_rejected_by_risk_gate"],
                "cons_risk_rollout_count": round_summary["cons_risk_rollout_count"],
                "cons_tail_env_count": round_summary["cons_tail_env_count"],
                "cons_tail_risk_mean": round_summary["cons_tail_risk_mean"],
                "cons_tail_risk_max": round_summary["cons_tail_risk_max"],
                "cons_episode_risk_mean": round_summary["cons_episode_risk_mean"],
                "cons_episode_risk_tail": round_summary["cons_episode_risk_tail"],
                "cons_risk_objective_mode": round_summary["cons_risk_objective_mode"],
                "cons_risk_penalty_coef": round_summary["cons_risk_penalty_coef"],
                "cons_child_failed_by_violation": round_summary["cons_child_failed_by_violation"],
                "cons_child_failed_by_final_critical": round_summary["cons_child_failed_by_final_critical"],
                "cons_child_failed_by_disruption": round_summary["cons_child_failed_by_disruption"],
                "cons_child_failed_by_multiple": round_summary["cons_child_failed_by_multiple"],
                "best_near_feasible_children": round_summary["best_near_feasible_children"],
                "strict_candidate_count": round_summary["strict_candidate_count"],
                "cons_margin_improved_attempts": round_summary["cons_margin_improved_attempts"],
                "cons_final_critical_improved_attempts": round_summary["cons_final_critical_improved_attempts"],
                "cons_mean_violation_improved_attempts": round_summary["cons_mean_violation_improved_attempts"],
                "saved_route_preview_cons_accept_count": round_summary[
                    "saved_route_preview_cons_accept_count"
                ],
                "shadow_route_preview_cons_accept_count": round_summary[
                    "shadow_route_preview_cons_accept_count"
                ],
                "saved_route_preview_near_feasible_count": round_summary[
                    "saved_route_preview_near_feasible_count"
                ],
                "shadow_route_preview_near_feasible_count": round_summary[
                    "shadow_route_preview_near_feasible_count"
                ],
                "saved_route_fail_primary_counts": round_summary[
                    "saved_route_fail_primary_counts"
                ],
                "shadow_route_fail_primary_counts": round_summary[
                    "shadow_route_fail_primary_counts"
                ],
                "saved_route_fail_component_counts": round_summary[
                    "saved_route_fail_component_counts"
                ],
                "shadow_route_fail_component_counts": round_summary[
                    "shadow_route_fail_component_counts"
                ],
                "saved_final_critical_threshold_counts": round_summary[
                    "saved_final_critical_threshold_counts"
                ],
                "shadow_final_critical_threshold_counts": round_summary[
                    "shadow_final_critical_threshold_counts"
                ],
                "saved_final_critical_value_summary": round_summary[
                    "saved_final_critical_value_summary"
                ],
                "shadow_final_critical_value_summary": round_summary[
                    "shadow_final_critical_value_summary"
                ],
                "saved_objective_delta_vs_parent_summary": round_summary[
                    "saved_objective_delta_vs_parent_summary"
                ],
                "shadow_objective_delta_vs_parent_summary": round_summary[
                    "shadow_objective_delta_vs_parent_summary"
                ],
                "saved_spread_gain_summary": round_summary[
                    "saved_spread_gain_summary"
                ],
                "shadow_spread_gain_summary": round_summary[
                    "shadow_spread_gain_summary"
                ],
                "gap_direction_summary": round_summary["gap_direction_summary"],
            }
        )

    union_front = manager.refresh_union_front()
    diagnostics.update(
        _summarize_cons_risk(
            [result for summary in round_summaries for result in summary["extension_results"]],
            cons_risk_mode=str(config.cons_risk_mode),
            cvar_alpha=float(config.cvar_alpha),
            cvar_metric=str(config.cvar_metric),
        )
    )
    diagnostics.update(
        _strict_failure_buckets(
            [result for summary in round_summaries for result in summary["extension_results"]],
            cons_thresholds=dict(config.cons_thresholds),
        )
    )
    diagnostics.update(
        _aggregate_cons_progress(
            [result for summary in round_summaries for result in summary["extension_results"]]
        )
    )
    diagnostics.update(
        _aggregate_saved_shadow_diagnostics(
            [result for summary in round_summaries for result in summary["extension_results"]],
            cons_thresholds=dict(config.cons_thresholds),
        )
    )
    buffer_path = run_dir / "solution_buffer.json"
    save_policy_buffer(
        buffer_path,
        metadata=buffer_metadata(
            stage="stage2",
            env_config=config.env,
            model_config=config.model,
            rollout_config=config.rollout,
            optimizer_config=ipo_config,
            eval_config=config.eval,
            extra={
                "seed": config.seed,
                "stage1_buffer": config.stage1_buffer,
                "archive_mode": "dual",
                "num_extension_policies": config.num_extension_policies,
                "num_cons_parents": config.num_cons_parents,
                "num_uc_parents": config.num_uc_parents,
                "route_mode": config.route_mode,
                "cons_operator_mode": config.cons_operator_mode,
                "uc_operator_mode": config.uc_operator_mode,
                "cons_risk_mode": config.cons_risk_mode,
                "cvar_alpha": float(config.cvar_alpha),
                "cvar_metric": str(config.cvar_metric),
                "cvar_penalty_coef": float(config.cvar_penalty_coef),
                "cvar_metric_weights": dict(config.cvar_metric_weights),
                "cons_risk_objective_mode": str(config.cons_risk_objective_mode),
                "cons_risk_penalty_coef": float(config.cons_risk_penalty_coef),
                "cons_thresholds": dict(config.cons_thresholds),
                "uc_thresholds": dict(config.uc_thresholds),
                "archive_rule_version": manager.archive_rule_version,
                "archive_seed_thresholds": dict(manager.archive_seed_thresholds),
                "cons_policy_ids": [
                    record["policy_id"] for record in manager.cons_records
                ],
                "uc_policy_ids": [record["policy_id"] for record in manager.uc_records],
                "selector_defaults": {
                    "mode": config.selector_mode_default,
                    "penalty_weights": dict(config.selector_penalty_weights),
                },
                "extension_rounds": config.extension_rounds,
                "constrained_updates": config.constrained_updates,
                "max_consecutive_constraint_failures": config.max_consecutive_constraint_failures,
                "constraint_tolerance": config.constraint_tolerance,
                "total_timesteps_per_update": config.total_timesteps_per_update,
                "cons_attempted_children": diagnostics["cons_attempted_children"],
                "cons_successful_children": diagnostics["cons_successful_children"],
                "cons_routed_children": diagnostics["cons_routed_children"],
                "cons_rejected_by_cost_gate": diagnostics["cons_rejected_by_cost_gate"],
                "cons_rejected_by_feasibility": diagnostics["cons_rejected_by_feasibility"],
                "cons_cvar_estimate_mean": diagnostics["cons_cvar_estimate_mean"],
                "cons_cvar_estimate_tail": diagnostics["cons_cvar_estimate_tail"],
                "cons_risk_penalty_mean": diagnostics["cons_risk_penalty_mean"],
                "cons_rejected_by_risk_gate": diagnostics["cons_rejected_by_risk_gate"],
                "cons_risk_rollout_count": diagnostics["cons_risk_rollout_count"],
                "cons_tail_env_count": diagnostics["cons_tail_env_count"],
                "cons_tail_risk_mean": diagnostics["cons_tail_risk_mean"],
                "cons_tail_risk_max": diagnostics["cons_tail_risk_max"],
                "cons_episode_risk_mean": diagnostics["cons_episode_risk_mean"],
                "cons_episode_risk_tail": diagnostics["cons_episode_risk_tail"],
                "cons_risk_objective_mode": diagnostics["cons_risk_objective_mode"],
                "cons_risk_penalty_coef": diagnostics["cons_risk_penalty_coef"],
                "cons_child_failed_by_violation": diagnostics["cons_child_failed_by_violation"],
                "cons_child_failed_by_final_critical": diagnostics["cons_child_failed_by_final_critical"],
                "cons_child_failed_by_disruption": diagnostics["cons_child_failed_by_disruption"],
                "cons_child_failed_by_multiple": diagnostics["cons_child_failed_by_multiple"],
                "best_near_feasible_children": diagnostics["best_near_feasible_children"],
                "strict_candidate_count": diagnostics["strict_candidate_count"],
                "cons_margin_improved_attempts": diagnostics["cons_margin_improved_attempts"],
                "cons_final_critical_improved_attempts": diagnostics["cons_final_critical_improved_attempts"],
                "cons_mean_violation_improved_attempts": diagnostics["cons_mean_violation_improved_attempts"],
                "saved_route_preview_cons_accept_count": diagnostics[
                    "saved_route_preview_cons_accept_count"
                ],
                "shadow_route_preview_cons_accept_count": diagnostics[
                    "shadow_route_preview_cons_accept_count"
                ],
                "saved_route_preview_near_feasible_count": diagnostics[
                    "saved_route_preview_near_feasible_count"
                ],
                "shadow_route_preview_near_feasible_count": diagnostics[
                    "shadow_route_preview_near_feasible_count"
                ],
                "saved_route_fail_primary_counts": diagnostics[
                    "saved_route_fail_primary_counts"
                ],
                "shadow_route_fail_primary_counts": diagnostics[
                    "shadow_route_fail_primary_counts"
                ],
                "saved_route_fail_component_counts": diagnostics[
                    "saved_route_fail_component_counts"
                ],
                "shadow_route_fail_component_counts": diagnostics[
                    "shadow_route_fail_component_counts"
                ],
                "saved_final_critical_threshold_counts": diagnostics[
                    "saved_final_critical_threshold_counts"
                ],
                "shadow_final_critical_threshold_counts": diagnostics[
                    "shadow_final_critical_threshold_counts"
                ],
                "saved_final_critical_value_summary": diagnostics[
                    "saved_final_critical_value_summary"
                ],
                "shadow_final_critical_value_summary": diagnostics[
                    "shadow_final_critical_value_summary"
                ],
                "saved_objective_delta_vs_parent_summary": diagnostics[
                    "saved_objective_delta_vs_parent_summary"
                ],
                "shadow_objective_delta_vs_parent_summary": diagnostics[
                    "shadow_objective_delta_vs_parent_summary"
                ],
                "saved_spread_gain_summary": diagnostics[
                    "saved_spread_gain_summary"
                ],
                "shadow_spread_gain_summary": diagnostics[
                    "shadow_spread_gain_summary"
                ],
                "gap_direction_summary": diagnostics["gap_direction_summary"],
                "round_summaries": round_summaries,
                "parent_buffer_metadata": payload.get("metadata", {}),
            },
        ),
        records=records,
        pareto_front=union_front,
        cons_records=manager.cons_records,
        uc_records=manager.uc_records,
        union_front=union_front,
    )
    save_json(run_dir / "pareto_front_stage2.json", union_front)
    save_json(run_dir / "stage2_summary.json", round_summaries)
    save_json(run_dir / "method_diagnostics.json", diagnostics)
    return buffer_path


def train_stage2(config: Stage2Config) -> Path:
    if config.archive_mode == "dual":
        return _train_stage2_dual(config)
    if config.archive_mode != "single":
        raise ValueError(f"Unsupported archive_mode: {config.archive_mode}")
    if not config.stage1_buffer:
        raise ValueError("stage1_buffer must be provided")
    set_seed(config.seed)
    payload = load_policy_buffer(config.stage1_buffer)
    records: list[dict] = list(payload["records"])
    run_dir = ensure_dir(Path(config.output_dir) / f"run_{uuid.uuid4().hex[:8]}")
    device = torch.device("cpu")

    env = MiniCageMORLEnv(
        num_envs=config.env.num_envs,
        red_policy=config.env.red_policy,
        remove_bugs=config.env.remove_bugs,
        max_steps=config.env.max_episode_steps,
        seed=config.env.seed,
    )

    ipo_config = IPOConfig(
        clip_param=config.ipo.clip_param,
        ppo_epochs=config.ipo.ppo_epochs,
        num_mini_batch=config.ipo.num_mini_batch,
        value_loss_coef=config.ipo.value_loss_coef,
        entropy_coef=config.ipo.entropy_coef,
        learning_rate=config.ipo.learning_rate,
        max_grad_norm=config.ipo.max_grad_norm,
        barrier_coef=config.ipo.barrier_coef,
        beta=config.ipo.beta,
        gamma=config.ipo.gamma,
        gae_lambda=config.ipo.gae_lambda,
        eps=config.ipo.eps,
    )
    policy_counter = 0
    round_summaries: list[dict] = []
    diagnostics = {
        "selection_mode": config.selection.mode,
        "beta_schedule_mode": config.ipo.beta_mode,
        "selection_preferences": _selection_preferences(config, env.obj_dim),
        "round_diagnostics": [],
    }
    num_updates = max(
        config.total_timesteps_per_update
        // (config.rollout.num_steps * config.env.num_envs),
        1,
    )

    for round_idx in range(config.extension_rounds):
        current_pareto = nondominated_filter(records)
        current_crowding = crowding_distance(current_pareto)
        if config.selection.mode == "adaptive":
            semantic_component_overrides = _semantic_component_overrides(
                current_pareto, config
            )
            extension_records, selected_scores, selected_components = select_top_n_adaptive(
                records,
                config.num_extension_policies,
                diagnostics["selection_preferences"],
                config.selection.score_weights,
                config.selection.utility_tolerance,
                coverage_mode=config.selection.coverage_mode,
                keep_extremes=config.selection.keep_extremes,
                component_overrides=semantic_component_overrides,
            )
            ranking_source = [
                (float(selected_scores[record["policy_id"]]), record["policy_id"])
                for record in extension_records
            ]
            ranking_source.sort(key=lambda item: (-item[0], item[1]))
            selected_ranks = {
                policy_id: rank + 1 for rank, (_, policy_id) in enumerate(ranking_source)
            }
        else:
            extension_records = select_top_n_by_crowding(
                records, config.num_extension_policies
            )
            selected_scores, selected_components, selected_ranks = (
                _selected_components_for_crowding(
                    current_pareto, extension_records, current_crowding
                )
            )
        round_summary = {
            "round_index": round_idx,
            "num_records_before_round": len(records),
            "pareto_size_before_round": len(current_pareto),
            "selection_mode": config.selection.mode,
            "beta_schedule_mode": config.ipo.beta_mode,
            "selected_policy_ids": [record["policy_id"] for record in extension_records],
            "selected_policy_crowding": {
                record["policy_id"]: float(current_crowding[index])
                for index, record in enumerate(current_pareto)
                if record["policy_id"] in {entry["policy_id"] for entry in extension_records}
            },
            "selected_policy_scores": {
                policy_id: float(score) for policy_id, score in selected_scores.items()
            },
            "selected_policy_components": {
                policy_id: dict(components)
                for policy_id, components in selected_components.items()
            },
            "extension_results": [],
        }
        for base_record in extension_records:
            selection_component = dict(
                selected_components.get(
                    base_record["policy_id"],
                    {
                        "crowding_score": 0.0,
                        "expansion_potential": 0.0,
                        "target_expansion_by_objective": [],
                        "constraint_risk": 0.0,
                        "low_risk_score": 1.0,
                        "utility_coverage_gain": 0.0,
                    },
                )
            )
            selection_score = float(selected_scores.get(base_record["policy_id"], 0.0))
            selection_rank = int(selected_ranks.get(base_record["policy_id"], 0))
            for objective_idx in range(env.obj_dim):
                actor_critic = ActorCritic(
                    obs_dim=env.obs_dim,
                    action_dim=env.action_dim,
                    obj_dim=env.obj_dim,
                    hidden_sizes=(config.model.hidden_size, config.model.hidden_size),
                ).to(device)
                actor_critic.load_state_dict(
                    torch.load(
                        base_record["checkpoint_path"],
                        map_location=device,
                        weights_only=True,
                    )
                )
                trainer = IPOTrainer(actor_critic, ipo_config)
                storage = VectorRolloutStorage(
                    num_steps=config.rollout.num_steps,
                    num_envs=config.env.num_envs,
                    obs_dim=env.obs_dim,
                    obj_dim=env.obj_dim,
                    device=device,
                )
                current_reference = np.asarray(
                    base_record["objective_vector"], dtype=np.float32
                )
                best_feasible_state = None
                best_feasible_objectives = None
                successful_updates = 0
                terminated_due_to_constraints = False
                consecutive_constraint_failures = 0
                last_constraint_margins = None
                last_trainer_stats: dict[str, float] = {}
                if config.ipo.beta_mode == "dynamic":
                    beta_value, beta_components = compute_dynamic_beta(
                        selection_component,
                        objective_idx,
                        round_idx,
                        config.extension_rounds,
                        config.ipo.beta_min,
                        config.ipo.beta_max,
                        config.ipo.schedule_weights,
                    )
                else:
                    beta_value = float(config.ipo.beta)
                    beta_components = {
                        "crowding": float(selection_component.get("crowding_score", 0.0)),
                        "target_expansion": float(
                            selection_component.get("expansion_potential", 0.0)
                        ),
                        "low_risk": float(
                            selection_component.get("low_risk_score", 1.0)
                        ),
                        "progress": float(
                            round_idx / max(config.extension_rounds - 1, 1)
                        ),
                        "strictness": 0.0,
                    }

                for _ in range(config.constrained_updates):
                    for _ in range(num_updates):
                        _, next_value, _, _ = _collect_rollout_stage2(
                            env,
                            actor_critic,
                            storage,
                            device,
                            semantic_penalty_coef=float(config.semantic_penalty_coef),
                            semantic_penalty_weights=dict(config.semantic_penalty_weights),
                        )
                        storage.compute_returns(
                            next_value, ipo_config.gamma, ipo_config.gae_lambda
                        )
                        last_trainer_stats = trainer.update(
                            storage,
                            objective_idx,
                            current_reference,
                            beta_override=beta_value,
                            use_barrier=(config.extension_mode == "constrained"),
                        )
                    candidate_objectives = evaluate_policy(
                        env,
                        actor_critic,
                        device,
                        episodes=config.eval.eval_episodes,
                    )
                    if config.extension_mode == "constrained":
                        candidate_margins = candidate_objectives - (
                            beta_value * current_reference
                        )
                        constraint_margins = np.delete(candidate_margins, objective_idx)
                        last_constraint_margins = constraint_margins.astype(np.float32)
                        is_feasible = bool(
                            np.all(constraint_margins > config.constraint_tolerance)
                        )
                        if not is_feasible:
                            consecutive_constraint_failures += 1
                            if (
                                consecutive_constraint_failures
                                >= max(int(config.max_consecutive_constraint_failures), 1)
                            ):
                                terminated_due_to_constraints = True
                                break
                            continue
                        consecutive_constraint_failures = 0
                    else:
                        last_constraint_margins = None

                    successful_updates += 1
                    current_reference = candidate_objectives
                    best_feasible_objectives = candidate_objectives.copy()
                    best_feasible_state = copy.deepcopy(actor_critic.state_dict())

                if best_feasible_state is None or best_feasible_objectives is None:
                    round_summary["extension_results"].append(
                        {
                            "parent_policy_id": base_record["policy_id"],
                            "target_objective": int(objective_idx),
                            "generated_policy_id": None,
                            "successful_constrained_updates": successful_updates,
                            "terminated_due_to_constraints": terminated_due_to_constraints,
                            "selection_score": selection_score,
                            "selection_rank": selection_rank,
                            "dynamic_beta": beta_value,
                            "beta_components": beta_components,
                            "max_consecutive_constraint_failures": int(
                                config.max_consecutive_constraint_failures
                            ),
                            "consecutive_constraint_failures": int(
                                consecutive_constraint_failures
                            ),
                            "last_constraint_margins": (
                                None
                                if last_constraint_margins is None
                                else last_constraint_margins.tolist()
                            ),
                            "ipo_stats": last_trainer_stats,
                        }
                    )
                    continue

                checkpoint_path = run_dir / f"policy_stage2_{policy_counter:03d}.pt"
                torch.save(best_feasible_state, checkpoint_path)
                policy_id = f"stage2_ext_{policy_counter:03d}_obj_{objective_idx}"
                record = policy_record(
                    policy_id=policy_id,
                    checkpoint_path=str(checkpoint_path.resolve()),
                    objective_vector=best_feasible_objectives.tolist(),
                    stage="stage2",
                    source="stage2",
                    parent_policy_id=base_record["policy_id"],
                    target_objective=int(objective_idx),
                    base_objective_vector=base_record["objective_vector"],
                    update_index=round_idx,
                    notes={
                        "extension_round": round_idx,
                        "selection_score": selection_score,
                        "selection_rank": selection_rank,
                        "crowding_score": float(
                            selection_component.get("crowding_score", 0.0)
                        ),
                        "expansion_potential": float(
                            selection_component.get("expansion_potential", 0.0)
                        ),
                        "constraint_risk": float(
                            selection_component.get("constraint_risk", 0.0)
                        ),
                        "utility_coverage_gain": float(
                            selection_component.get("utility_coverage_gain", 0.0)
                        ),
                        "dynamic_beta": beta_value,
                        "beta_mode": config.ipo.beta_mode,
                        "extension_mode": config.extension_mode,
                        "beta_components": beta_components,
                        "successful_constrained_updates": successful_updates,
                        "terminated_due_to_constraints": terminated_due_to_constraints,
                        "constraint_tolerance": config.constraint_tolerance,
                        "max_consecutive_constraint_failures": int(
                            config.max_consecutive_constraint_failures
                        ),
                        "consecutive_constraint_failures": int(
                            consecutive_constraint_failures
                        ),
                        "last_constraint_margins": (
                            last_constraint_margins.tolist()
                            if last_constraint_margins is not None
                            else None
                        ),
                        "objective_improvement": float(
                            best_feasible_objectives[objective_idx]
                            - np.asarray(base_record["objective_vector"], dtype=np.float32)[objective_idx]
                        ),
                        "ipo_stats": last_trainer_stats,
                    },
                )
                pareto_after_append = nondominated_filter(records + [record])
                record.setdefault("notes", {})
                record["notes"].update(
                    {
                        "pareto_size_after_save": len(pareto_after_append),
                        "is_nondominated_after_save": any(
                            entry["policy_id"] == policy_id for entry in pareto_after_append
                        ),
                    }
                )
                records.append(record)
                round_summary["extension_results"].append(
                    {
                        "parent_policy_id": base_record["policy_id"],
                        "target_objective": int(objective_idx),
                        "generated_policy_id": policy_id,
                        "successful_constrained_updates": successful_updates,
                        "terminated_due_to_constraints": terminated_due_to_constraints,
                        "selection_score": selection_score,
                        "selection_rank": selection_rank,
                        "dynamic_beta": beta_value,
                        "beta_components": beta_components,
                        "last_constraint_margins": (
                            None
                            if last_constraint_margins is None
                            else last_constraint_margins.tolist()
                        ),
                        "objective_improvement": record["notes"]["objective_improvement"],
                        "ipo_stats": last_trainer_stats,
                    }
                )
                policy_counter += 1
        round_summary["num_records_after_round"] = len(records)
        round_summary["pareto_size_after_round"] = len(nondominated_filter(records))
        round_summaries.append(round_summary)
        diagnostics["round_diagnostics"].append(
            {
                "round_index": round_idx,
                "selection_mode": config.selection.mode,
                "beta_schedule_mode": config.ipo.beta_mode,
                "selected_policy_scores": round_summary["selected_policy_scores"],
                "selected_policy_components": round_summary["selected_policy_components"],
            }
        )

    pareto_front = nondominated_filter(records)
    buffer_path = run_dir / "solution_buffer.json"
    save_policy_buffer(
        buffer_path,
        metadata=buffer_metadata(
            stage="stage2",
            env_config=config.env,
            model_config=config.model,
            rollout_config=config.rollout,
            optimizer_config=ipo_config,
            eval_config=config.eval,
            extra={
                "seed": config.seed,
                "stage1_buffer": config.stage1_buffer,
                "num_extension_policies": config.num_extension_policies,
                "extension_rounds": config.extension_rounds,
                "constrained_updates": config.constrained_updates,
                "max_consecutive_constraint_failures": config.max_consecutive_constraint_failures,
                "constraint_tolerance": config.constraint_tolerance,
                "total_timesteps_per_update": config.total_timesteps_per_update,
                "selection_mode": config.selection.mode,
                "selection_weights": dict(config.selection.score_weights),
                "selection_utility_tolerance": config.selection.utility_tolerance,
                "selection_keep_extremes": config.selection.keep_extremes,
                "extension_mode": config.extension_mode,
                "beta_mode": config.ipo.beta_mode,
                "beta_min": config.ipo.beta_min,
                "beta_max": config.ipo.beta_max,
                "beta_schedule_weights": dict(config.ipo.schedule_weights),
                "round_summaries": round_summaries,
                "parent_buffer_metadata": payload.get("metadata", {}),
            },
        ),
        records=records,
        pareto_front=pareto_front,
    )
    save_json(run_dir / "pareto_front_stage2.json", pareto_front)
    save_json(run_dir / "stage2_summary.json", round_summaries)
    save_json(run_dir / "method_diagnostics.json", diagnostics)
    return buffer_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage-2 C-MORL Pareto extension on MiniCAGE.")
    parser.add_argument("--config", default=str(DEFAULT_STAGE2_CONFIG))
    parser.add_argument("--stage1-buffer", default=None)
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()

    config = load_stage2_config(args.config)
    if args.stage1_buffer is not None:
        config.stage1_buffer = args.stage1_buffer
    if args.output_dir is not None:
        config.output_dir = args.output_dir
    buffer_path = train_stage2(config)
    print(f"Saved stage-2 outputs to {buffer_path}")


if __name__ == "__main__":
    main()
