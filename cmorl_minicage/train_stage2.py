from __future__ import annotations

import argparse
import copy
import uuid
from pathlib import Path
from typing import Any

import numpy as np
import torch

from cmorl_minicage.algorithms.adaptive_selection import select_top_n_adaptive
from cmorl_minicage.buffer import (
    buffer_metadata,
    load_policy_buffer,
    policy_record,
    save_policy_buffer,
)
from cmorl_minicage.config import (
    DEFAULT_STAGE2_CONFIG,
    DeployabilityGateConfig,
    DeployabilityTargetConfig,
    Stage2Config,
    TailAcceptanceConfig,
    load_stage2_config,
)
from cmorl_minicage.deployability import (
    build_threshold_profile,
    build_support_threshold_profile,
    candidate_metrics_from_metrics,
    deployability_note_payload,
    empty_semantic_totals,
    evaluate_support_profile,
    summarize_semantic_totals,
    support_shell_rank,
    support_shell_thresholds,
    support_aware_deployability_score,
)
from cmorl_minicage.algorithms.dynamic_beta import compute_dynamic_beta
from cmorl_minicage.algorithms.ipo import IPOConfig, IPOTrainer
from cmorl_minicage.algorithms.selection import crowding_distance, nondominated_filter, select_top_n_by_crowding
from cmorl_minicage.env import MiniCageMORLEnv
from cmorl_minicage.evaluate_constraints import (
    _critical_host_safety_cvar,
    _evaluate_actor_critic_model,
    _evaluate_actor_critic_policy_detailed,
    _evaluate_actor_critic_record,
    _evaluate_actor_critic_record_detailed,
    _load_thresholds,
)
from cmorl_minicage.models import ActorCritic
from cmorl_minicage.shield import default_policy_action_mask, record_policy_mask_stats
from cmorl_minicage.storage import VectorRolloutStorage
from cmorl_minicage.train_stage1 import collect_rollout, evaluate_policy
from cmorl_minicage.utils import ensure_dir, save_json, set_seed, simplex_grid


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _resolve_repo_path(raw_path: str | Path) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return (_repo_root() / path).resolve()


def _selection_preferences(config: Stage2Config, obj_dim: int) -> list[list[float]]:
    step = config.eval.preference_step
    if step is None:
        step = 0.5 if obj_dim == 2 else 0.1
    return simplex_grid(float(step), obj_dim)


def _selected_components_for_crowding(
    selection_records: list[dict],
    extension_records: list[dict],
    selection_crowding: np.ndarray,
) -> tuple[dict[str, float], dict[str, dict[str, float | list[float]]], dict[str, int]]:
    records_by_id = {
        record["policy_id"]: index for index, record in enumerate(selection_records)
    }
    selected_scores: dict[str, float] = {}
    selected_components: dict[str, dict[str, float | list[float]]] = {}
    ranking_source: list[tuple[float, str]] = []
    for record in extension_records:
        index = records_by_id.get(record["policy_id"])
        crowding_value = float(selection_crowding[index]) if index is not None else 0.0
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
    shield_mode: str = "disabled",
) -> dict[str, float]:
    env = MiniCageMORLEnv(
        num_envs=env_config.num_envs,
        red_policy=env_config.red_policy,
        remove_bugs=env_config.remove_bugs,
        max_steps=env_config.max_episode_steps,
        seed=env_config.seed,
        obj_dim=int(model_config.obj_dim),
        critical_host_safety_mode=str(model_config.critical_host_safety_mode),
        shield_mode=str(shield_mode),
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

    totals = empty_semantic_totals()
    base_seed = int(env_config.seed)
    max_episode_steps = int(getattr(env_config, "max_episode_steps", getattr(env, "max_steps", 100)))
    first_hit_sentinel = float(max_episode_steps + 1)
    with torch.no_grad():
        for episode_idx in range(max(int(eval_episodes), 1)):
            env.seed = base_seed + episode_idx
            obs, _ = env.reset()
            done = np.zeros(env.num_envs, dtype=bool)
            episode_semantics = {
                "critical_impact_count": np.zeros(env.num_envs, dtype=np.float64),
                "recovered_hosts": np.zeros(env.num_envs, dtype=np.float64),
                "analyse_count": np.zeros(env.num_envs, dtype=np.float64),
                "remove_count": np.zeros(env.num_envs, dtype=np.float64),
                "restore_count": np.zeros(env.num_envs, dtype=np.float64),
                "high_disruption_action_count": np.zeros(env.num_envs, dtype=np.float64),
                "total_action_count": np.zeros(env.num_envs, dtype=np.float64),
                "critical_dwell_steps": np.zeros(env.num_envs, dtype=np.float64),
                "critical_path_compromise_count": np.zeros(env.num_envs, dtype=np.float64),
                "sleep_during_critical_breach": np.zeros(env.num_envs, dtype=np.float64),
                "user_action_during_critical_breach": np.zeros(env.num_envs, dtype=np.float64),
                "user_action_after_enterprise_foothold": np.zeros(env.num_envs, dtype=np.float64),
            }
            final_compromised = np.zeros(env.num_envs, dtype=np.float64)
            final_critical = np.zeros(env.num_envs, dtype=np.float64)
            ever_critical_breach = np.zeros(env.num_envs, dtype=np.float64)
            first_critical_hit_step = np.full(env.num_envs, first_hit_sentinel, dtype=np.float64)
            step_idx = 0

            while not np.all(done):
                obs_tensor = torch.as_tensor(obs, dtype=torch.float32)
                action_mask = torch.as_tensor(
                    default_policy_action_mask(env),
                    dtype=torch.bool,
                )
                policy_output = actor_critic.act(obs_tensor, action_mask=action_mask)
                record_policy_mask_stats(env, policy_output.blocked_probability_mass)
                actions = policy_output.actions.cpu().numpy().reshape(
                    env.num_envs,
                    1,
                )
                obs, _, done, _, info = env.step(actions)
                semantic_info = info["semantic_info"]
                final_compromised = np.asarray(
                    semantic_info["final_compromised_hosts"],
                    dtype=np.float64,
                )
                final_critical = np.asarray(
                    semantic_info["final_critical_compromised_hosts"],
                    dtype=np.float64,
                )
                for key in episode_semantics:
                    source_key = (
                        "critical_dwell_flag"
                        if key == "critical_dwell_steps"
                        else key
                    )
                    episode_semantics[key] += np.asarray(
                        semantic_info.get(source_key, np.zeros(env.num_envs)),
                        dtype=np.float64,
                    )
                critical_present = np.asarray(
                    semantic_info.get("critical_present", np.zeros(env.num_envs)),
                    dtype=np.float64,
                )
                critical_hit_event = np.asarray(
                    semantic_info.get("critical_hit_event", np.zeros(env.num_envs)),
                    dtype=np.float64,
                )
                ever_critical_breach = np.maximum(ever_critical_breach, critical_present)
                newly_hit_mask = np.logical_and(
                    critical_hit_event > 0.0,
                    first_critical_hit_step >= first_hit_sentinel,
                )
                first_critical_hit_step[newly_hit_mask] = float(step_idx)
                step_idx += 1

            totals["final_compromised_hosts"].extend(final_compromised.tolist())
            totals["final_critical_compromised_hosts"].extend(final_critical.tolist())
            totals["ever_critical_breach"].extend(ever_critical_breach.tolist())
            totals["first_critical_hit_step"].extend(first_critical_hit_step.tolist())
            totals["critical_hit_latency_score"].extend(
                (first_critical_hit_step / first_hit_sentinel).tolist()
            )
            for key in episode_semantics:
                totals[key].extend(episode_semantics[key].tolist())

    return summarize_semantic_totals(totals)


def _semantic_component_overrides(
    records: list[dict],
    config: Stage2Config,
) -> dict[str, dict[str, float | dict[str, float]]]:
    if config.selection.semantic_eval_episodes <= 0 or not records:
        return {}

    if (
        str(config.selection.semantic_score_mode).lower() == "support_aware"
        and config.selection.semantic_thresholds_path
    ):
        thresholds = _load_thresholds(
            _resolve_repo_path(config.selection.semantic_thresholds_path)
        )
        support_profile = build_support_threshold_profile(
            name="selection_support_aware",
            business_min=float(thresholds["d_business"]),
            cost_min=float(thresholds["d_cost"]),
        )
        overrides: dict[str, dict[str, float | dict[str, float]]] = {}
        for record in records:
            deployability = dict(record.get("notes", {}).get("deployability", {}))
            if deployability:
                support_score = float(deployability.get("deployability_score", 0.0))
                metrics = {
                    "business_return": float(deployability.get("business_return", 0.0)),
                    "cost_return": float(deployability.get("cost_return", 0.0)),
                    "mean_violation": float(deployability.get("mean_violation", 0.0)),
                    "high_disruption_action_rate": float(
                        deployability.get("high_disruption_action_rate", 0.0)
                    ),
                    "final_critical_compromised_hosts": float(
                        deployability.get("final_critical_compromised_hosts", 0.0)
                    ),
                }
            else:
                metrics = _evaluate_actor_critic_record(
                    _resolve_repo_path(record["checkpoint_path"])
                    if record.get("checkpoint_path")
                    else None,
                    {"env": vars(config.env), "model": vars(config.model)},
                    thresholds,
                    eval_episodes=config.selection.semantic_eval_episodes,
                    baseline_kind=record.get("notes", {}).get("baseline_kind"),
                )
                candidate_metrics = candidate_metrics_from_metrics(
                    policy_id=str(record["policy_id"]),
                    objective_vector=list(record.get("objective_vector", [])),
                    metrics=metrics,
                )
                support_score = support_aware_deployability_score(
                    candidate_metrics,
                    support_profile,
                    weights=dict(config.selection.semantic_support_score_weights),
                )
            overrides[record["policy_id"]] = {
                "semantic_risk": float(1.0 - support_score),
                "semantic_low_risk_score": float(support_score),
                "semantic_metrics": {
                    "business_return": float(metrics["business_return"]),
                    "cost_return": float(metrics["cost_return"]),
                    "mean_violation": float(metrics["mean_violation"]),
                    "high_disruption_action_rate": float(
                        metrics["high_disruption_action_rate"]
                    ),
                    "final_critical_compromised_hosts": float(
                        metrics["final_critical_compromised_hosts"]
                    ),
                },
            }
        return overrides

    metric_names = tuple(config.selection.semantic_metric_weights.keys())
    by_policy: dict[str, dict[str, float]] = {}
    for record in records:
        by_policy[record["policy_id"]] = _semantic_selection_metrics(
            config.env,
            config.model,
            record["checkpoint_path"],
            eval_episodes=config.selection.semantic_eval_episodes,
            shield_mode=str(config.shield.mode),
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


def _stage2_eval_metadata(
    config: Stage2Config,
) -> dict[str, dict[str, float | int | bool | str]]:
    return {
        "env": vars(config.env),
        "model": vars(config.model),
        "shield": vars(config.shield),
    }


def _record_notes(record: dict) -> dict[str, Any]:
    notes = record.get("notes")
    if not isinstance(notes, dict):
        notes = {}
        record["notes"] = notes
    return notes


def _record_eval_metadata(
    record: dict,
    *,
    parent_buffer_metadata: dict[str, Any],
    stage2_metadata: dict[str, Any],
) -> dict[str, Any]:
    if str(record.get("stage", "")) == "stage2" or str(record.get("source", "")) == "stage2":
        return copy.deepcopy(stage2_metadata)
    if "env" in parent_buffer_metadata and "model" in parent_buffer_metadata:
        payload = {
            "env": copy.deepcopy(parent_buffer_metadata.get("env", {})),
            "model": copy.deepcopy(parent_buffer_metadata.get("model", {})),
        }
        if "shield" in parent_buffer_metadata:
            payload["shield"] = copy.deepcopy(parent_buffer_metadata.get("shield", {}))
        return payload
    return copy.deepcopy(stage2_metadata)


def _deployability_selection_enabled(config: Stage2Config) -> bool:
    return bool(
        str(config.selection.pool_mode).lower() == "pareto_plus_deployability"
        and config.selection.semantic_thresholds_path
    )


def _tail_acceptance_enabled(config: Stage2Config) -> bool:
    return bool(str(config.tail_acceptance.mode).lower() == "critical_tail")


def _tail_metrics_from_detailed_metrics(
    detailed_metrics: dict[str, Any],
    *,
    alpha: float,
) -> dict[str, Any]:
    audit_details = dict(detailed_metrics.get("audit_details", {}))
    tail_returns = np.asarray(
        audit_details.get("critical_host_safety_episode_returns", []),
        dtype=np.float64,
    )
    cvar_value = detailed_metrics.get("critical_host_safety_cvar_alpha")
    if tail_returns.size:
        cvar_value = _critical_host_safety_cvar(tail_returns, alpha=float(alpha))
    return {
        "business_return": float(detailed_metrics.get("business_return", 0.0)),
        "cost_return": float(detailed_metrics.get("cost_return", 0.0)),
        "mean_violation": float(detailed_metrics.get("mean_violation", 0.0)),
        "feasible_rate": float(detailed_metrics.get("feasible_rate", 0.0)),
        "critical_host_safety_return": float(
            detailed_metrics.get("critical_host_safety_return", 0.0) or 0.0
        ),
        "critical_host_safety_cvar_alpha": (
            None if cvar_value is None else float(cvar_value)
        ),
        "tail_alpha": float(alpha),
        "ever_critical_breach_rate": float(
            detailed_metrics.get("ever_critical_breach_rate", 0.0)
        ),
        "persistent_critical_breach_rate": float(
            detailed_metrics.get(
                "persistent_critical_breach_rate",
                detailed_metrics.get("final_critical_compromised_hosts", 0.0),
            )
        ),
        "mean_critical_dwell_steps": float(
            detailed_metrics.get("mean_critical_dwell_steps", 0.0)
        ),
        "mean_first_critical_hit_step": float(
            detailed_metrics.get("mean_first_critical_hit_step", 0.0)
        ),
        "critical_hit_latency_score": float(
            detailed_metrics.get("critical_hit_latency_score", 0.0)
        ),
    }


def _tail_acceptance_key(
    tail_metrics: dict[str, Any],
    *,
    objective_improvement: float,
) -> tuple[float, float, float, float, float, float]:
    cvar_value = tail_metrics.get("critical_host_safety_cvar_alpha")
    return (
        -float(tail_metrics.get("persistent_critical_breach_rate", float("inf"))),
        float(cvar_value if cvar_value is not None else float("-inf")),
        -float(tail_metrics.get("mean_critical_dwell_steps", float("inf"))),
        -float(tail_metrics.get("ever_critical_breach_rate", float("inf"))),
        float(tail_metrics.get("critical_hit_latency_score", 0.0)),
        float(objective_improvement),
    )


def _tail_acceptance_result(
    parent_metrics: dict[str, Any] | None,
    child_metrics: dict[str, Any] | None,
    *,
    objective_improvement: float,
    tail_config: TailAcceptanceConfig,
) -> dict[str, Any]:
    mode = str(tail_config.mode).lower()
    parent_payload = dict(parent_metrics or {})
    child_payload = dict(child_metrics or {})
    business_regression = max(
        0.0,
        float(parent_payload.get("business_return", 0.0))
        - float(child_payload.get("business_return", 0.0)),
    )
    cost_regression = max(
        0.0,
        float(parent_payload.get("cost_return", 0.0))
        - float(child_payload.get("cost_return", 0.0)),
    )
    persistent_delta = float(
        child_payload.get("persistent_critical_breach_rate", 0.0)
    ) - float(parent_payload.get("persistent_critical_breach_rate", 0.0))
    dwell_increase = float(
        child_payload.get("mean_critical_dwell_steps", 0.0)
    ) - float(parent_payload.get("mean_critical_dwell_steps", 0.0))
    result = {
        "gate_mode": mode,
        "gate_passed": False,
        "gate_reason": "disabled" if mode != "critical_tail" else "missing_tail_metrics",
        "business_regression": float(business_regression),
        "cost_regression": float(cost_regression),
        "persistent_delta": float(persistent_delta),
        "dwell_increase": float(dwell_increase),
        "objective_improvement": float(objective_improvement),
        "parent_tail_metrics": dict(parent_payload),
        "child_tail_metrics": dict(child_payload),
    }
    if mode != "critical_tail":
        result["gate_passed"] = True
        return result
    if not parent_payload or not child_payload:
        return result
    if business_regression > float(tail_config.business_guardrail):
        result["gate_reason"] = "business_guardrail"
        return result
    if cost_regression > float(tail_config.cost_guardrail):
        result["gate_reason"] = "cost_guardrail"
        return result
    if bool(tail_config.persistent_non_regression) and persistent_delta > 1e-9:
        result["gate_reason"] = "persistent_non_regression"
        return result
    if dwell_increase > float(tail_config.dwell_slack):
        result["gate_reason"] = "critical_dwell_guardrail"
        return result
    result["gate_passed"] = True
    result["gate_reason"] = "tail_metrics_ranked"
    return result


def _tail_acceptance_decision(
    parent_metrics: dict[str, Any] | None,
    child_metrics: dict[str, Any] | None,
    *,
    objective_improvement: float,
    tail_config: TailAcceptanceConfig,
) -> dict[str, Any]:
    gate_result = _tail_acceptance_result(
        parent_metrics,
        child_metrics,
        objective_improvement=objective_improvement,
        tail_config=tail_config,
    )
    should_rank = bool(child_metrics) and bool(gate_result["gate_passed"])
    acceptance_key = (
        _tail_acceptance_key(
            dict(child_metrics or {}),
            objective_improvement=objective_improvement,
        )
        if should_rank
        else None
    )
    return {
        "should_rank": should_rank,
        "acceptance_key": acceptance_key,
        "gate_result": gate_result,
    }


def _sorted_near_frontier_records(records: list[dict]) -> list[dict]:
    return sorted(
        [
            record
            for record in records
            if not bool(
                record.get("notes", {}).get("deployability", {}).get("passed_strict", False)
            )
        ],
        key=lambda record: (
            -float(record["notes"]["deployability"]["strict_margin"]),
            -float(record["notes"]["deployability"]["deployability_score"]),
            str(record["policy_id"]),
        ),
    )


def _sorted_strict_frontier_records(records: list[dict]) -> list[dict]:
    return sorted(
        [
            record
            for record in records
            if bool(
                record.get("notes", {}).get("deployability", {}).get("passed_strict", False)
            )
        ],
        key=lambda record: (
            -float(record["notes"]["deployability"]["strict_margin"]),
            -float(record["notes"]["deployability"]["deployability_score"]),
            str(record["policy_id"]),
        ),
    )


def _selection_pool_records(
    records: list[dict],
    *,
    near_frontier_quota: int,
    strict_frontier_quota: int,
) -> tuple[list[dict], dict[str, list[str]]]:
    value_frontier = nondominated_filter(records)
    near_frontier = _sorted_near_frontier_records(records)[: max(int(near_frontier_quota), 0)]
    strict_frontier = _sorted_strict_frontier_records(records)[
        : max(int(strict_frontier_quota), 0)
    ]
    seen: set[str] = set()
    selection_pool: list[dict] = []
    for frontier in (value_frontier, near_frontier, strict_frontier):
        for record in frontier:
            policy_id = str(record["policy_id"])
            if policy_id in seen:
                continue
            selection_pool.append(record)
            seen.add(policy_id)
    return selection_pool, {
        "value_frontier_policy_ids": [str(record["policy_id"]) for record in value_frontier],
        "near_frontier_policy_ids": [str(record["policy_id"]) for record in near_frontier],
        "strict_frontier_policy_ids": [str(record["policy_id"]) for record in strict_frontier],
    }


def _deployability_acceptance_key(
    deployability: dict[str, Any],
    *,
    objective_improvement: float,
) -> tuple[float, float, float, float]:
    return (
        float(support_shell_rank(str(deployability.get("support_shell_reached", "NONE")))),
        float(deployability.get("strict_margin", float("-inf"))),
        float(deployability.get("deployability_score", float("-inf"))),
        float(objective_improvement),
    )


def _deployability_target_acceptance_key(
    deployability: dict[str, Any],
    *,
    objective_improvement: float,
    target_result: dict[str, Any],
) -> tuple[float, float, float, float, float, float]:
    return (
        float(target_result.get("child_target_score", float("-inf"))),
        float(-float(target_result.get("child_target_excess", float("inf")))),
        float(support_shell_rank(str(deployability.get("support_shell_reached", "NONE")))),
        float(deployability.get("strict_margin", float("-inf"))),
        float(deployability.get("deployability_score", float("-inf"))),
        float(objective_improvement),
    )


def _deployability_gate_enabled(config: Stage2Config) -> bool:
    return bool(str(config.deployability_gate.mode).lower() == "hard")


def _deployability_target_enabled(config: Stage2Config) -> bool:
    return bool(str(config.deployability_target.mode).lower() == "global_support")


def _candidate_metrics_from_deployability_note(
    deployability: dict[str, Any] | None,
    *,
    policy_id: str = "",
    objective_vector: list[float] | None = None,
) -> Any | None:
    payload = dict(deployability or {})
    if not payload:
        return None
    return candidate_metrics_from_metrics(
        policy_id=policy_id,
        objective_vector=list(objective_vector or []),
        metrics={
            "business_return": float(payload.get("business_return", 0.0)),
            "cost_return": float(payload.get("cost_return", 0.0)),
            "mean_violation": float(payload.get("mean_violation", 0.0)),
            "high_disruption_action_rate": float(
                payload.get("high_disruption_action_rate", 0.0)
            ),
            "final_critical_compromised_hosts": float(
                payload.get("final_critical_compromised_hosts", 0.0)
            ),
        },
    )


def _deployability_target_profile(
    records: list[dict],
    *,
    shell_thresholds: dict[str, dict[str, float]],
    target_config: DeployabilityTargetConfig,
) -> dict[str, Any]:
    shell_name = str(target_config.reference_shell).upper()
    shell_threshold = dict(
        shell_thresholds.get(shell_name, shell_thresholds.get("S0", {}))
    )
    if not shell_threshold:
        return {
            "name": f"stage2_target:{shell_name}",
            "business_min": 0.0,
            "cost_min": 0.0,
            "mean_violation_max": 0.0,
            "high_disruption_max": 0.0,
            "reference_shell": shell_name,
            "anchor_policy_id": "",
            "anchor_strict_margin": float("-inf"),
        }
    best_record = max(
        records,
        key=lambda record: float(
            record.get("notes", {}).get("deployability", {}).get("strict_margin", float("-inf"))
        ),
    )
    anchor = dict(best_record.get("notes", {}).get("deployability", {}))
    return {
        "name": f"stage2_target:{shell_name}",
        "business_min": float(
            max(
                float(shell_threshold.get("business_min", 0.0)),
                float(anchor.get("business_return", 0.0)),
            )
        ),
        "cost_min": float(
            max(
                float(shell_threshold.get("cost_min", 0.0)),
                float(anchor.get("cost_return", 0.0)),
            )
        ),
        "mean_violation_max": float(
            min(
                float(shell_threshold.get("mean_violation_max", 0.0)),
                float(anchor.get("mean_violation", 0.0)),
            )
        ),
        "high_disruption_max": float(
            min(
                float(shell_threshold.get("high_disruption_max", 0.0)),
                float(anchor.get("high_disruption_action_rate", 0.0)),
            )
        ),
        "reference_shell": shell_name,
        "anchor_policy_id": str(best_record["policy_id"]),
        "anchor_strict_margin": float(anchor.get("strict_margin", float("-inf"))),
    }


def _deployability_target_stats(
    deployability: dict[str, Any] | None,
    *,
    target_profile_dict: dict[str, Any],
    target_config: DeployabilityTargetConfig,
) -> dict[str, Any]:
    metrics = _candidate_metrics_from_deployability_note(deployability)
    if metrics is None:
        return {
            "target_score": 0.0,
            "target_excess": 1.0,
            "target_margin": float("-inf"),
            "target_fail_dims": [],
            "target_profile_name": str(target_profile_dict.get("name", "")),
        }
    target_profile = build_support_threshold_profile(
        name=str(target_profile_dict.get("name", "stage2_target:S0")),
        business_min=float(target_profile_dict.get("business_min", 0.0)),
        cost_min=float(target_profile_dict.get("cost_min", 0.0)),
        mean_violation_max=float(target_profile_dict.get("mean_violation_max", 0.0)),
        high_disruption_max=float(target_profile_dict.get("high_disruption_max", 0.0)),
    )
    profile_eval = evaluate_support_profile(metrics, target_profile)
    target_score = support_aware_deployability_score(
        metrics,
        target_profile,
        weights=dict(target_config.weights),
    )
    return {
        "target_score": float(target_score),
        "target_excess": float(max(0.0, 1.0 - float(target_score))),
        "target_margin": float(profile_eval.get("support_margin", float("-inf"))),
        "target_fail_dims": list(profile_eval.get("fail_dims", [])),
        "target_profile_name": str(target_profile.name),
    }


def _persistent_critical_breach_rate(payload: dict[str, Any]) -> float:
    return float(
        payload.get(
            "persistent_critical_breach_rate",
            payload.get("final_critical_compromised_hosts", 0.0),
        )
    )


def _critical_first_guardrail_deltas(
    parent_payload: dict[str, Any],
    child_payload: dict[str, Any],
) -> dict[str, float]:
    return {
        "ever_critical_breach_increase": max(
            0.0,
            float(child_payload.get("ever_critical_breach_rate", 0.0))
            - float(parent_payload.get("ever_critical_breach_rate", 0.0)),
        ),
        "persistent_critical_breach_increase": max(
            0.0,
            _persistent_critical_breach_rate(child_payload)
            - _persistent_critical_breach_rate(parent_payload),
        ),
        "critical_hit_latency_score_drop": max(
            0.0,
            float(parent_payload.get("critical_hit_latency_score", 0.0))
            - float(child_payload.get("critical_hit_latency_score", 0.0)),
        ),
        "mean_critical_dwell_steps_increase": max(
            0.0,
            float(child_payload.get("mean_critical_dwell_steps", 0.0))
            - float(parent_payload.get("mean_critical_dwell_steps", 0.0)),
        ),
        "user_action_during_critical_breach_rate_increase": max(
            0.0,
            float(child_payload.get("user_action_during_critical_breach_rate", 0.0))
            - float(parent_payload.get("user_action_during_critical_breach_rate", 0.0)),
        ),
    }


def _critical_first_improvements(
    parent_payload: dict[str, Any],
    child_payload: dict[str, Any],
) -> dict[str, float]:
    return {
        "ever_critical_breach_reduction": float(
            parent_payload.get("ever_critical_breach_rate", 0.0)
        )
        - float(child_payload.get("ever_critical_breach_rate", 0.0)),
        "persistent_critical_breach_reduction": _persistent_critical_breach_rate(
            parent_payload
        )
        - _persistent_critical_breach_rate(child_payload),
        "critical_hit_latency_score_improvement": float(
            child_payload.get("critical_hit_latency_score", 0.0)
        )
        - float(parent_payload.get("critical_hit_latency_score", 0.0)),
    }


def _deployability_gate_result(
    parent: dict[str, Any] | None,
    child: dict[str, Any] | None,
    *,
    gate_config: DeployabilityGateConfig,
) -> dict[str, Any]:
    mode = str(gate_config.mode).lower()
    parent_payload = dict(parent or {})
    child_payload = dict(child or {})
    support_shell_before = str(parent_payload.get("support_shell_reached", "NONE"))
    support_shell_after = str(child_payload.get("support_shell_reached", "NONE"))
    strict_margin_delta = float(child_payload.get("strict_margin", 0.0)) - float(
        parent_payload.get("strict_margin", 0.0)
    )
    mean_violation_delta = float(parent_payload.get("mean_violation", 0.0)) - float(
        child_payload.get("mean_violation", 0.0)
    )
    high_disruption_delta = float(
        parent_payload.get("high_disruption_action_rate", 0.0)
    ) - float(child_payload.get("high_disruption_action_rate", 0.0))
    business_regression = max(
        0.0,
        float(parent_payload.get("business_return", 0.0))
        - float(child_payload.get("business_return", 0.0)),
    )
    cost_regression = max(
        0.0,
        float(parent_payload.get("cost_return", 0.0))
        - float(child_payload.get("cost_return", 0.0)),
    )
    final_critical_increase = max(
        0.0,
        float(child_payload.get("final_critical_compromised_hosts", 0.0))
        - float(parent_payload.get("final_critical_compromised_hosts", 0.0)),
    )
    critical_first_deltas = _critical_first_guardrail_deltas(
        parent_payload,
        child_payload,
    )
    critical_first_improvements = _critical_first_improvements(
        parent_payload,
        child_payload,
    )
    result = {
        "gate_mode": mode,
        "gate_passed": False,
        "gate_reason": "disabled" if mode != "hard" else "missing_deployability_context",
        "strict_margin_delta": strict_margin_delta,
        "mean_violation_delta": mean_violation_delta,
        "high_disruption_delta": high_disruption_delta,
        "business_regression": business_regression,
        "cost_regression": cost_regression,
        "final_critical_increase": final_critical_increase,
        **critical_first_deltas,
        **critical_first_improvements,
        "support_shell_before": support_shell_before,
        "support_shell_after": support_shell_after,
    }
    if mode != "hard":
        result["gate_passed"] = True
        return result
    if not parent_payload or not child_payload:
        return result
    if business_regression > float(gate_config.max_business_regression):
        result["gate_reason"] = "business_regression_guardrail"
        return result
    if cost_regression > float(gate_config.max_cost_regression):
        result["gate_reason"] = "cost_regression_guardrail"
        return result
    if final_critical_increase > float(gate_config.max_final_critical_increase):
        result["gate_reason"] = "final_critical_guardrail"
        return result
    if (
        critical_first_deltas["ever_critical_breach_increase"]
        > float(gate_config.max_ever_critical_breach_increase)
    ):
        result["gate_reason"] = "ever_critical_guardrail"
        return result
    if (
        critical_first_deltas["persistent_critical_breach_increase"]
        > float(gate_config.max_persistent_critical_breach_increase)
    ):
        result["gate_reason"] = "persistent_critical_guardrail"
        return result
    if (
        critical_first_deltas["critical_hit_latency_score_drop"]
        > float(gate_config.max_critical_hit_latency_score_drop)
    ):
        result["gate_reason"] = "critical_hit_latency_guardrail"
        return result
    if (
        critical_first_deltas["mean_critical_dwell_steps_increase"]
        > float(gate_config.max_mean_critical_dwell_steps_increase)
    ):
        result["gate_reason"] = "critical_dwell_guardrail"
        return result
    if (
        critical_first_deltas["user_action_during_critical_breach_rate_increase"]
        > float(gate_config.max_user_action_during_critical_breach_rate_increase)
    ):
        result["gate_reason"] = "user_action_during_critical_guardrail"
        return result
    if (
        critical_first_improvements["ever_critical_breach_reduction"]
        >= float(gate_config.min_ever_critical_breach_reduction)
    ):
        result["gate_passed"] = True
        result["gate_reason"] = "ever_critical_improved"
        return result
    if (
        critical_first_improvements["persistent_critical_breach_reduction"]
        >= float(gate_config.min_persistent_critical_breach_reduction)
    ):
        result["gate_passed"] = True
        result["gate_reason"] = "persistent_critical_improved"
        return result
    if (
        critical_first_improvements["critical_hit_latency_score_improvement"]
        >= float(gate_config.min_critical_hit_latency_score_improvement)
        and critical_first_deltas["mean_critical_dwell_steps_increase"] <= 1e-9
    ):
        result["gate_passed"] = True
        result["gate_reason"] = "critical_latency_improved"
        return result
    result["gate_reason"] = "no_improvement_path"
    return result


def _deployability_target_result(
    parent: dict[str, Any] | None,
    child: dict[str, Any] | None,
    *,
    target_profile_dict: dict[str, Any],
    target_config: DeployabilityTargetConfig,
) -> dict[str, Any]:
    mode = str(target_config.mode).lower()
    parent_payload = dict(parent or {})
    child_payload = dict(child or {})
    support_shell_before = str(parent_payload.get("support_shell_reached", "NONE"))
    support_shell_after = str(child_payload.get("support_shell_reached", "NONE"))
    strict_margin_delta = float(child_payload.get("strict_margin", 0.0)) - float(
        parent_payload.get("strict_margin", 0.0)
    )
    business_regression = max(
        0.0,
        float(parent_payload.get("business_return", 0.0))
        - float(child_payload.get("business_return", 0.0)),
    )
    cost_regression = max(
        0.0,
        float(parent_payload.get("cost_return", 0.0))
        - float(child_payload.get("cost_return", 0.0)),
    )
    final_critical_increase = max(
        0.0,
        float(child_payload.get("final_critical_compromised_hosts", 0.0))
        - float(parent_payload.get("final_critical_compromised_hosts", 0.0)),
    )
    critical_first_deltas = _critical_first_guardrail_deltas(
        parent_payload,
        child_payload,
    )
    critical_first_improvements = _critical_first_improvements(
        parent_payload,
        child_payload,
    )
    parent_stats = _deployability_target_stats(
        parent_payload,
        target_profile_dict=target_profile_dict,
        target_config=target_config,
    )
    child_stats = _deployability_target_stats(
        child_payload,
        target_profile_dict=target_profile_dict,
        target_config=target_config,
    )
    target_score_delta = float(child_stats["target_score"]) - float(
        parent_stats["target_score"]
    )
    target_excess_reduction = float(parent_stats["target_excess"]) - float(
        child_stats["target_excess"]
    )
    result = {
        "target_mode": mode,
        "gate_mode": mode,
        "gate_passed": False,
        "gate_reason": "disabled" if mode != "global_support" else "missing_deployability_context",
        "strict_margin_delta": strict_margin_delta,
        "business_regression": business_regression,
        "cost_regression": cost_regression,
        "final_critical_increase": final_critical_increase,
        **critical_first_deltas,
        **critical_first_improvements,
        "support_shell_before": support_shell_before,
        "support_shell_after": support_shell_after,
        "target_profile_name": str(child_stats["target_profile_name"]),
        "parent_target_score": float(parent_stats["target_score"]),
        "child_target_score": float(child_stats["target_score"]),
        "target_score_delta": target_score_delta,
        "parent_target_excess": float(parent_stats["target_excess"]),
        "child_target_excess": float(child_stats["target_excess"]),
        "target_excess_reduction": target_excess_reduction,
        "parent_target_margin": float(parent_stats["target_margin"]),
        "child_target_margin": float(child_stats["target_margin"]),
        "parent_target_fail_dims": list(parent_stats["target_fail_dims"]),
        "child_target_fail_dims": list(child_stats["target_fail_dims"]),
    }
    if mode != "global_support":
        result["gate_passed"] = True
        return result
    if not parent_payload or not child_payload:
        return result
    if business_regression > float(target_config.max_business_regression):
        result["gate_reason"] = "business_regression_guardrail"
        return result
    if cost_regression > float(target_config.max_cost_regression):
        result["gate_reason"] = "cost_regression_guardrail"
        return result
    if final_critical_increase > float(target_config.max_final_critical_increase):
        result["gate_reason"] = "final_critical_guardrail"
        return result
    if (
        critical_first_deltas["ever_critical_breach_increase"]
        > float(target_config.max_ever_critical_breach_increase)
    ):
        result["gate_reason"] = "ever_critical_guardrail"
        return result
    if (
        critical_first_deltas["persistent_critical_breach_increase"]
        > float(target_config.max_persistent_critical_breach_increase)
    ):
        result["gate_reason"] = "persistent_critical_guardrail"
        return result
    if (
        critical_first_deltas["critical_hit_latency_score_drop"]
        > float(target_config.max_critical_hit_latency_score_drop)
    ):
        result["gate_reason"] = "critical_hit_latency_guardrail"
        return result
    if (
        critical_first_deltas["mean_critical_dwell_steps_increase"]
        > float(target_config.max_mean_critical_dwell_steps_increase)
    ):
        result["gate_reason"] = "critical_dwell_guardrail"
        return result
    if (
        critical_first_deltas["user_action_during_critical_breach_rate_increase"]
        > float(target_config.max_user_action_during_critical_breach_rate_increase)
    ):
        result["gate_reason"] = "user_action_during_critical_guardrail"
        return result
    if support_shell_rank(support_shell_after) > support_shell_rank(support_shell_before):
        result["gate_passed"] = True
        result["gate_reason"] = "shell_rank_improved"
        return result
    if (
        critical_first_improvements["ever_critical_breach_reduction"]
        >= float(target_config.min_ever_critical_breach_reduction)
    ):
        result["gate_passed"] = True
        result["gate_reason"] = "ever_critical_improved"
        return result
    if (
        critical_first_improvements["persistent_critical_breach_reduction"]
        >= float(target_config.min_persistent_critical_breach_reduction)
    ):
        result["gate_passed"] = True
        result["gate_reason"] = "persistent_critical_improved"
        return result
    if (
        critical_first_improvements["critical_hit_latency_score_improvement"]
        >= float(target_config.min_critical_hit_latency_score_improvement)
        and critical_first_deltas["mean_critical_dwell_steps_increase"] <= 1e-9
    ):
        result["gate_passed"] = True
        result["gate_reason"] = "critical_latency_improved"
        return result
    if target_score_delta >= float(target_config.min_target_score_improvement):
        result["gate_passed"] = True
        result["gate_reason"] = "target_score_improved"
        return result
    if target_excess_reduction >= float(target_config.min_target_excess_reduction):
        result["gate_passed"] = True
        result["gate_reason"] = "target_excess_reduced"
        return result
    result["gate_reason"] = "no_target_progress"
    return result


def _deployability_acceptance_decision(
    parent: dict[str, Any] | None,
    child: dict[str, Any] | None,
    *,
    objective_improvement: float,
    gate_config: DeployabilityGateConfig,
) -> dict[str, Any]:
    gate_result = _deployability_gate_result(parent, child, gate_config=gate_config)
    should_rank = bool(child) and bool(gate_result["gate_passed"])
    acceptance_key = (
        _deployability_acceptance_key(child_payload, objective_improvement=objective_improvement)
        if should_rank and (child_payload := dict(child or {}))
        else None
    )
    return {
        "should_rank": should_rank,
        "acceptance_key": acceptance_key,
        "gate_result": gate_result,
    }


def _deployability_target_decision(
    parent: dict[str, Any] | None,
    child: dict[str, Any] | None,
    *,
    objective_improvement: float,
    target_profile_dict: dict[str, Any],
    target_config: DeployabilityTargetConfig,
) -> dict[str, Any]:
    target_result = _deployability_target_result(
        parent,
        child,
        target_profile_dict=target_profile_dict,
        target_config=target_config,
    )
    should_rank = bool(child) and bool(target_result["gate_passed"])
    acceptance_key = (
        _deployability_target_acceptance_key(
            child_payload,
            objective_improvement=objective_improvement,
            target_result=target_result,
        )
        if should_rank and (child_payload := dict(child or {}))
        else None
    )
    return {
        "should_rank": should_rank,
        "acceptance_key": acceptance_key,
        "gate_result": target_result,
    }


def _deployability_improved(
    parent: dict[str, Any] | None,
    child: dict[str, Any] | None,
) -> bool:
    if not parent or not child:
        return False
    return bool(
        support_shell_rank(str(child.get("support_shell_reached", "NONE")))
        > support_shell_rank(str(parent.get("support_shell_reached", "NONE")))
        or float(child.get("strict_margin", float("-inf")))
        > float(parent.get("strict_margin", float("-inf")))
        or float(child.get("deployability_score", float("-inf")))
        > float(parent.get("deployability_score", float("-inf")))
    )


def _annotate_records_with_deployability(
    records: list[dict],
    *,
    parent_buffer_metadata: dict[str, Any],
    config: Stage2Config,
    thresholds: dict[str, float],
) -> tuple[dict[str, Any], dict[str, dict[str, float]], dict[str, list[str]], list[dict]]:
    strict_profile = build_threshold_profile(
        name="stage2_deployability",
        thresholds=thresholds,
    )
    stage2_metadata = _stage2_eval_metadata(config)
    eval_episodes = max(int(config.selection.semantic_eval_episodes), 1)
    metrics_by_id: dict[str, Any] = {}
    metric_rows: list[Any] = []
    for record in records:
        checkpoint_path = (
            _resolve_repo_path(record["checkpoint_path"]) if record.get("checkpoint_path") else None
        )
        eval_metadata = _record_eval_metadata(
            record,
            parent_buffer_metadata=parent_buffer_metadata,
            stage2_metadata=stage2_metadata,
        )
        metrics = _evaluate_actor_critic_record(
            checkpoint_path,
            eval_metadata,
            thresholds,
            eval_episodes=eval_episodes,
            baseline_kind=record.get("notes", {}).get("baseline_kind"),
        )
        candidate_metrics = candidate_metrics_from_metrics(
            policy_id=str(record["policy_id"]),
            objective_vector=list(record.get("objective_vector", [])),
            metrics=metrics,
        )
        metrics_by_id[str(record["policy_id"])] = candidate_metrics
        metric_rows.append(candidate_metrics)

    shell_thresholds = support_shell_thresholds(metric_rows)
    for record in records:
        policy_id = str(record["policy_id"])
        _record_notes(record)["deployability"] = deployability_note_payload(
            metrics_by_id[policy_id],
            strict_profile=strict_profile,
            shell_thresholds=shell_thresholds,
            profile_name="stage2_deployability",
            weights=dict(config.selection.semantic_support_score_weights),
        )

    selection_pool, frontiers = _selection_pool_records(
        records,
        near_frontier_quota=int(config.selection.near_frontier_quota),
        strict_frontier_quota=int(config.selection.strict_frontier_quota),
    )
    return strict_profile.to_dict(), shell_thresholds, frontiers, selection_pool


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


def _collect_rollout_stage2(
    env: MiniCageMORLEnv,
    actor_critic: ActorCritic,
    storage: VectorRolloutStorage,
    device: torch.device,
    *,
    semantic_penalty_coef: float,
    semantic_penalty_weights: dict[str, float],
) -> np.ndarray:
    obs, _ = env.reset()
    obs_tensor = torch.as_tensor(obs, dtype=torch.float32, device=device)
    storage.reset()
    storage.obs[0].copy_(obs_tensor)
    episode_return = np.zeros((env.num_envs, env.obj_dim), dtype=np.float32)

    for _ in range(storage.num_steps):
        with torch.no_grad():
            action_mask = torch.as_tensor(
                default_policy_action_mask(env),
                dtype=torch.bool,
                device=device,
            )
            policy_output = actor_critic.act(obs_tensor, action_mask=action_mask)
            record_policy_mask_stats(env, policy_output.blocked_probability_mass)
        actions = policy_output.actions.cpu().numpy().reshape(env.num_envs, 1)
        next_obs, reward_vec, done, _, info = env.step(actions)
        reward_vec = np.asarray(reward_vec, dtype=np.float32)
        penalty = _semantic_penalty(
            info.get("semantic_info", {}),
            semantic_penalty_weights,
            semantic_penalty_coef,
        )
        if penalty.size:
            reward_vec = reward_vec - penalty[:, None]
        next_obs_tensor = torch.as_tensor(next_obs, dtype=torch.float32, device=device)
        reward_tensor = torch.as_tensor(reward_vec, dtype=torch.float32, device=device)
        masks = torch.as_tensor(1.0 - done.astype(np.float32), dtype=torch.float32, device=device)
        storage.insert(
            obs=next_obs_tensor,
            actions=policy_output.actions,
            action_masks=action_mask,
            log_probs=policy_output.log_probs,
            values=policy_output.values,
            rewards=reward_tensor,
            masks=masks,
        )
        obs_tensor = next_obs_tensor
        episode_return += reward_vec

    with torch.no_grad():
        next_value = actor_critic.get_value(obs_tensor)
    return episode_return.mean(axis=0), next_value


def train_stage2(config: Stage2Config) -> Path:
    if not config.stage1_buffer:
        raise ValueError("stage1_buffer must be provided")
    if int(config.model.obj_dim) not in (3, 4):
        raise ValueError("model.obj_dim must be 3 or 4")
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
        obj_dim=int(config.model.obj_dim),
        critical_host_safety_mode=str(config.model.critical_host_safety_mode),
        shield_mode=str(config.shield.mode),
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
        "selection_pool_mode": config.selection.pool_mode,
        "beta_schedule_mode": config.ipo.beta_mode,
        "selection_preferences": _selection_preferences(config, env.obj_dim),
        "round_diagnostics": [],
    }
    deployability_thresholds = None
    tail_thresholds = None
    if _deployability_selection_enabled(config):
        deployability_thresholds = _load_thresholds(
            _resolve_repo_path(config.selection.semantic_thresholds_path)
        )
    if _tail_acceptance_enabled(config):
        if _deployability_gate_enabled(config) or _deployability_target_enabled(config):
            raise ValueError(
                "tail_acceptance is mutually exclusive with deployability gate/target"
            )
        if not config.selection.semantic_thresholds_path:
            raise ValueError(
                "tail_acceptance requires selection.semantic_thresholds_path"
            )
        tail_thresholds = _load_thresholds(
            _resolve_repo_path(config.selection.semantic_thresholds_path)
        )
    if (
        (_deployability_gate_enabled(config) or _deployability_target_enabled(config))
        and deployability_thresholds is None
    ):
        raise ValueError(
            "deployability-aware gate/target requires deployability-aware thresholds and selection metadata"
        )
    num_updates = max(
        config.total_timesteps_per_update
        // (config.rollout.num_steps * config.env.num_envs),
        1,
    )

    for round_idx in range(config.extension_rounds):
        current_pareto = nondominated_filter(records)
        selection_records = list(current_pareto)
        deployability_frontiers = {
            "value_frontier_policy_ids": [str(record["policy_id"]) for record in current_pareto],
            "near_frontier_policy_ids": [],
            "strict_frontier_policy_ids": [],
        }
        strict_profile_dict = {}
        shell_thresholds = {}
        target_profile_dict = {}
        if deployability_thresholds is not None:
            (
                strict_profile_dict,
                shell_thresholds,
                deployability_frontiers,
                selection_records,
            ) = _annotate_records_with_deployability(
                records,
                parent_buffer_metadata=dict(payload.get("metadata", {})),
                config=config,
                thresholds=deployability_thresholds,
            )
            if _deployability_target_enabled(config):
                target_profile_dict = _deployability_target_profile(
                    records,
                    shell_thresholds=shell_thresholds,
                    target_config=config.deployability_target,
                )
        current_crowding = crowding_distance(selection_records)
        if config.selection.mode == "adaptive":
            semantic_component_overrides = _semantic_component_overrides(
                selection_records, config
            )
            extension_records, selected_scores, selected_components = select_top_n_adaptive(
                selection_records,
                config.num_extension_policies,
                diagnostics["selection_preferences"],
                config.selection.score_weights,
                config.selection.utility_tolerance,
                coverage_mode=config.selection.coverage_mode,
                keep_extremes=config.selection.keep_extremes,
                pareto_only=False,
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
                selection_records,
                config.num_extension_policies,
                pareto_only=False,
            )
            selected_scores, selected_components, selected_ranks = (
                _selected_components_for_crowding(
                    selection_records, extension_records, current_crowding
                )
            )
        round_summary = {
            "round_index": round_idx,
            "num_records_before_round": len(records),
            "pareto_size_before_round": len(current_pareto),
            "selection_pool_size": len(selection_records),
            "selection_mode": config.selection.mode,
            "selection_pool_mode": config.selection.pool_mode,
            "deployability_gate_mode": str(config.deployability_gate.mode),
            "deployability_target_mode": str(config.deployability_target.mode),
            "hard_gate_pass_count": 0,
            "hard_gate_reject_count": 0,
            "target_pass_count": 0,
            "target_reject_count": 0,
            "tail_acceptance_mode": str(config.tail_acceptance.mode),
            "tail_eval_episodes": int(config.tail_acceptance.tail_eval_episodes),
            "tail_alpha": float(config.tail_acceptance.tail_alpha),
            "tail_reject_reason_counts": {},
            "beta_schedule_mode": config.ipo.beta_mode,
            "deployability_frontier_sizes": {
                key.replace("_policy_ids", ""): len(value)
                for key, value in deployability_frontiers.items()
            },
            "deployability_frontiers": dict(deployability_frontiers),
            "selection_pool_policy_ids": [
                str(record["policy_id"]) for record in selection_records
            ],
            "strict_profile": dict(strict_profile_dict),
            "support_shell_thresholds": dict(shell_thresholds),
            "target_profile": dict(target_profile_dict),
            "selected_policy_ids": [record["policy_id"] for record in extension_records],
            "selected_policy_crowding": {
                record["policy_id"]: float(current_crowding[index])
                for index, record in enumerate(selection_records)
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
            parent_deployability = dict(
                base_record.get("notes", {}).get("deployability", {})
            )
            parent_tail_metrics = None
            if _tail_acceptance_enabled(config):
                parent_eval_metadata = _record_eval_metadata(
                    base_record,
                    parent_buffer_metadata=dict(payload.get("metadata", {})),
                    stage2_metadata=_stage2_eval_metadata(config),
                )
                parent_tail_detailed = _evaluate_actor_critic_record_detailed(
                    _resolve_repo_path(base_record["checkpoint_path"])
                    if base_record.get("checkpoint_path")
                    else None,
                    parent_eval_metadata,
                    tail_thresholds or {"d_business": 0.0, "d_cost": 0.0},
                    eval_episodes=max(int(config.tail_acceptance.tail_eval_episodes), 1),
                    baseline_kind=base_record.get("notes", {}).get("baseline_kind"),
                )
                parent_tail_metrics = _tail_metrics_from_detailed_metrics(
                    parent_tail_detailed,
                    alpha=float(config.tail_acceptance.tail_alpha),
                )
            for objective_idx in range(env.obj_dim):
                actor_critic = ActorCritic(
                    obs_dim=env.obs_dim,
                    action_dim=env.action_dim,
                    obj_dim=env.obj_dim,
                    hidden_sizes=(config.model.hidden_size, config.model.hidden_size),
                ).to(device)
                actor_critic.load_state_dict(
                    torch.load(
                        _resolve_repo_path(base_record["checkpoint_path"]),
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
                    action_dim=env.action_dim,
                    device=device,
                )
                current_reference = np.asarray(
                    base_record["objective_vector"], dtype=np.float32
                )
                best_feasible_state = None
                best_feasible_objectives = None
                best_feasible_deployability = None
                best_feasible_tail_metrics = None
                best_acceptance_key = None
                best_gate_result = None
                best_tail_result = None
                successful_updates = 0
                terminated_due_to_constraints = False
                consecutive_constraint_failures = 0
                hard_gate_passes = 0
                hard_gate_rejects = 0
                target_passes = 0
                target_rejects = 0
                last_constraint_margins = None
                last_trainer_stats: dict[str, float] = {}
                last_gate_result = None
                last_tail_result = None
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
                        _, next_value = _collect_rollout_stage2(
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
                    objective_improvement = float(
                        candidate_objectives[objective_idx]
                        - np.asarray(
                            base_record["objective_vector"], dtype=np.float32
                        )[objective_idx]
                    )
                    candidate_deployability = None
                    candidate_tail_metrics = None
                    acceptance_key = (objective_improvement,)
                    if _tail_acceptance_enabled(config):
                        eval_metadata = _stage2_eval_metadata(config)
                        tail_detailed_metrics = _evaluate_actor_critic_policy_detailed(
                            actor_critic,
                            eval_metadata,
                            tail_thresholds or {"d_business": 0.0, "d_cost": 0.0},
                            eval_episodes=max(
                                int(config.tail_acceptance.tail_eval_episodes),
                                1,
                            ),
                            baseline_kind=base_record.get("notes", {}).get("baseline_kind"),
                        )
                        candidate_tail_metrics = _tail_metrics_from_detailed_metrics(
                            tail_detailed_metrics,
                            alpha=float(config.tail_acceptance.tail_alpha),
                        )
                        tail_acceptance_decision = _tail_acceptance_decision(
                            parent_tail_metrics,
                            candidate_tail_metrics,
                            objective_improvement=objective_improvement,
                            tail_config=config.tail_acceptance,
                        )
                        last_tail_result = dict(tail_acceptance_decision["gate_result"])
                        if not bool(tail_acceptance_decision["should_rank"]):
                            reject_reason = str(
                                last_tail_result.get("gate_reason", "tail_rejected")
                            )
                            tail_counts = round_summary["tail_reject_reason_counts"]
                            tail_counts[reject_reason] = int(
                                tail_counts.get(reject_reason, 0)
                            ) + 1
                            continue
                        acceptance_key = tail_acceptance_decision["acceptance_key"]
                    if deployability_thresholds is not None:
                        eval_metadata = _stage2_eval_metadata(config)
                        deployability_metrics = _evaluate_actor_critic_model(
                            actor_critic,
                            eval_metadata,
                            deployability_thresholds,
                            eval_episodes=max(int(config.selection.semantic_eval_episodes), 1),
                            baseline_kind=base_record.get("notes", {}).get("baseline_kind"),
                        )
                        deployability_candidate = candidate_metrics_from_metrics(
                            policy_id=str(base_record["policy_id"]),
                            objective_vector=candidate_objectives.astype(np.float32).tolist(),
                            metrics=deployability_metrics,
                        )
                        candidate_deployability = deployability_note_payload(
                            deployability_candidate,
                            strict_profile=build_threshold_profile(
                                name=str(strict_profile_dict.get("name", "stage2_deployability")),
                                thresholds=deployability_thresholds,
                                mean_violation_max=float(
                                    strict_profile_dict.get("mean_violation_max", 0.50)
                                ),
                                final_critical_max=float(
                                    strict_profile_dict.get("final_critical_max", 0.25)
                                ),
                                high_disruption_max=float(
                                    strict_profile_dict.get("high_disruption_max", 0.50)
                                ),
                            ),
                            shell_thresholds=shell_thresholds,
                            profile_name="stage2_deployability",
                            weights=dict(config.selection.semantic_support_score_weights),
                        )
                        acceptance_decision = _deployability_acceptance_decision(
                            parent_deployability,
                            objective_improvement=objective_improvement,
                            child=candidate_deployability,
                            gate_config=config.deployability_gate,
                        )
                        if _deployability_target_enabled(config):
                            acceptance_decision = _deployability_target_decision(
                                parent_deployability,
                                objective_improvement=objective_improvement,
                                child=candidate_deployability,
                                target_profile_dict=target_profile_dict,
                                target_config=config.deployability_target,
                            )
                        last_gate_result = dict(acceptance_decision["gate_result"])
                        if _deployability_target_enabled(config):
                            if bool(acceptance_decision["gate_result"]["gate_passed"]):
                                target_passes += 1
                            else:
                                target_rejects += 1
                        elif _deployability_gate_enabled(config):
                            if bool(acceptance_decision["gate_result"]["gate_passed"]):
                                hard_gate_passes += 1
                            else:
                                hard_gate_rejects += 1
                        if not bool(acceptance_decision["should_rank"]):
                            continue
                        acceptance_key = acceptance_decision["acceptance_key"]
                    if best_acceptance_key is None or acceptance_key > best_acceptance_key:
                        best_acceptance_key = acceptance_key
                        best_feasible_objectives = candidate_objectives.copy()
                        best_feasible_state = copy.deepcopy(actor_critic.state_dict())
                        best_feasible_deployability = (
                            dict(candidate_deployability)
                            if candidate_deployability is not None
                            else None
                        )
                        best_feasible_tail_metrics = (
                            dict(candidate_tail_metrics)
                            if candidate_tail_metrics is not None
                            else None
                        )
                        best_gate_result = (
                            dict(last_gate_result) if last_gate_result is not None else None
                        )
                        best_tail_result = (
                            dict(last_tail_result) if last_tail_result is not None else None
                        )

                round_summary["hard_gate_pass_count"] += int(hard_gate_passes)
                round_summary["hard_gate_reject_count"] += int(hard_gate_rejects)
                round_summary["target_pass_count"] += int(target_passes)
                round_summary["target_reject_count"] += int(target_rejects)
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
                            "hard_gate_mode": str(config.deployability_gate.mode),
                            "deployability_target_mode": str(config.deployability_target.mode),
                            "tail_acceptance_mode": str(config.tail_acceptance.mode),
                            "hard_gate_passes": int(hard_gate_passes),
                            "hard_gate_rejects": int(hard_gate_rejects),
                            "target_passes": int(target_passes),
                            "target_rejects": int(target_rejects),
                            "rejected_by_hard_gate": bool(
                                _deployability_gate_enabled(config)
                                and hard_gate_rejects > 0
                            ),
                            "rejected_by_target": bool(
                                _deployability_target_enabled(config)
                                and target_rejects > 0
                            ),
                            "last_gate_reason": (
                                str(last_gate_result.get("gate_reason", ""))
                                if isinstance(last_gate_result, dict)
                                else ""
                            ),
                            "last_tail_gate_reason": (
                                str(last_tail_result.get("gate_reason", ""))
                                if isinstance(last_tail_result, dict)
                                else ""
                            ),
                            "parent_tail_metrics": (
                                None
                                if parent_tail_metrics is None
                                else dict(parent_tail_metrics)
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
                    checkpoint_path=str(checkpoint_path),
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
                if best_feasible_deployability is not None:
                    record["notes"]["deployability"] = dict(best_feasible_deployability)
                    best_gate_payload = dict(best_gate_result or {})
                    record["notes"]["deployability_acceptance"] = {
                        "gate_mode": str(best_gate_payload.get("gate_mode", "disabled")),
                        "target_mode": str(best_gate_payload.get("target_mode", "disabled")),
                        "gate_passed": bool(best_gate_payload.get("gate_passed", True)),
                        "gate_reason": str(best_gate_payload.get("gate_reason", "disabled")),
                        "accepted_without_shell_gain": bool(
                            not _deployability_improved(
                                parent_deployability, best_feasible_deployability
                            )
                        ),
                        "strict_margin_delta": float(
                            best_gate_payload.get(
                                "strict_margin_delta",
                                best_feasible_deployability.get("strict_margin", 0.0)
                                - float(parent_deployability.get("strict_margin", 0.0)),
                            )
                        ),
                        "mean_violation_delta": float(
                            best_gate_payload.get("mean_violation_delta", 0.0)
                        ),
                        "high_disruption_delta": float(
                            best_gate_payload.get("high_disruption_delta", 0.0)
                        ),
                        "business_regression": float(
                            best_gate_payload.get("business_regression", 0.0)
                        ),
                        "cost_regression": float(
                            best_gate_payload.get("cost_regression", 0.0)
                        ),
                        "final_critical_increase": float(
                            best_gate_payload.get("final_critical_increase", 0.0)
                        ),
                        "parent_target_score": float(
                            best_gate_payload.get("parent_target_score", 0.0)
                        ),
                        "child_target_score": float(
                            best_gate_payload.get("child_target_score", 0.0)
                        ),
                        "target_score_delta": float(
                            best_gate_payload.get("target_score_delta", 0.0)
                        ),
                        "parent_target_excess": float(
                            best_gate_payload.get("parent_target_excess", 0.0)
                        ),
                        "child_target_excess": float(
                            best_gate_payload.get("child_target_excess", 0.0)
                        ),
                        "target_excess_reduction": float(
                            best_gate_payload.get("target_excess_reduction", 0.0)
                        ),
                        "parent_target_margin": float(
                            best_gate_payload.get("parent_target_margin", 0.0)
                        ),
                        "child_target_margin": float(
                            best_gate_payload.get("child_target_margin", 0.0)
                        ),
                        "parent_target_fail_dims": list(
                            best_gate_payload.get("parent_target_fail_dims", [])
                        ),
                        "child_target_fail_dims": list(
                            best_gate_payload.get("child_target_fail_dims", [])
                        ),
                        "target_profile_name": str(
                            best_gate_payload.get("target_profile_name", "")
                        ),
                        "deployability_score_delta": float(
                            best_feasible_deployability.get("deployability_score", 0.0)
                            - float(parent_deployability.get("deployability_score", 0.0))
                        ),
                        "support_shell_before": str(
                            best_gate_payload.get(
                                "support_shell_before",
                                parent_deployability.get("support_shell_reached", "NONE"),
                            )
                        ),
                        "support_shell_after": str(
                            best_gate_payload.get(
                                "support_shell_after",
                                best_feasible_deployability.get("support_shell_reached", "NONE"),
                            )
                        ),
                    }
                if best_feasible_tail_metrics is not None:
                    best_tail_payload = dict(best_tail_result or {})
                    record["notes"]["tail_acceptance"] = {
                        "gate_mode": str(best_tail_payload.get("gate_mode", "disabled")),
                        "gate_passed": bool(best_tail_payload.get("gate_passed", True)),
                        "gate_reason": str(
                            best_tail_payload.get("gate_reason", "tail_metrics_ranked")
                        ),
                        "business_regression": float(
                            best_tail_payload.get("business_regression", 0.0)
                        ),
                        "cost_regression": float(
                            best_tail_payload.get("cost_regression", 0.0)
                        ),
                        "persistent_delta": float(
                            best_tail_payload.get("persistent_delta", 0.0)
                        ),
                        "dwell_increase": float(
                            best_tail_payload.get("dwell_increase", 0.0)
                        ),
                        "tail_alpha": float(config.tail_acceptance.tail_alpha),
                        "parent_tail_metrics": (
                            None
                            if parent_tail_metrics is None
                            else dict(parent_tail_metrics)
                        ),
                        "child_tail_metrics": dict(best_feasible_tail_metrics),
                    }
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
                        "hard_gate_mode": str(config.deployability_gate.mode),
                        "deployability_target_mode": str(config.deployability_target.mode),
                        "tail_acceptance_mode": str(config.tail_acceptance.mode),
                        "hard_gate_passes": int(hard_gate_passes),
                        "hard_gate_rejects": int(hard_gate_rejects),
                        "target_passes": int(target_passes),
                        "target_rejects": int(target_rejects),
                        "selected_gate_reason": (
                            str(best_gate_result.get("gate_reason", ""))
                            if isinstance(best_gate_result, dict)
                            else ""
                        ),
                        "selected_tail_gate_reason": (
                            str(best_tail_result.get("gate_reason", ""))
                            if isinstance(best_tail_result, dict)
                            else ""
                        ),
                        "parent_tail_metrics": (
                            None
                            if parent_tail_metrics is None
                            else dict(parent_tail_metrics)
                        ),
                        "child_tail_metrics": (
                            None
                            if best_feasible_tail_metrics is None
                            else dict(best_feasible_tail_metrics)
                        ),
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
                "selection_pool_mode": config.selection.pool_mode,
                "deployability_gate_mode": str(config.deployability_gate.mode),
                "deployability_target_mode": str(config.deployability_target.mode),
                "tail_acceptance_mode": str(config.tail_acceptance.mode),
                "tail_eval_episodes": int(config.tail_acceptance.tail_eval_episodes),
                "tail_alpha": float(config.tail_acceptance.tail_alpha),
                "hard_gate_pass_count": int(round_summary["hard_gate_pass_count"]),
                "hard_gate_reject_count": int(round_summary["hard_gate_reject_count"]),
                "target_pass_count": int(round_summary["target_pass_count"]),
                "target_reject_count": int(round_summary["target_reject_count"]),
                "tail_reject_reason_counts": dict(
                    round_summary["tail_reject_reason_counts"]
                ),
                "beta_schedule_mode": config.ipo.beta_mode,
                "selected_policy_scores": round_summary["selected_policy_scores"],
                "selected_policy_components": round_summary["selected_policy_components"],
            }
        )

    final_deployability_frontiers = {
        "value_frontier_policy_ids": [str(record["policy_id"]) for record in nondominated_filter(records)],
        "near_frontier_policy_ids": [],
        "strict_frontier_policy_ids": [],
    }
    if deployability_thresholds is not None:
        _, _, final_deployability_frontiers, _ = _annotate_records_with_deployability(
            records,
            parent_buffer_metadata=dict(payload.get("metadata", {})),
            config=config,
            thresholds=deployability_thresholds,
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
                "shield": vars(config.shield),
                "seed": config.seed,
                "stage1_buffer": config.stage1_buffer,
                "num_extension_policies": config.num_extension_policies,
                "extension_rounds": config.extension_rounds,
                "constrained_updates": config.constrained_updates,
                "max_consecutive_constraint_failures": config.max_consecutive_constraint_failures,
                "constraint_tolerance": config.constraint_tolerance,
                "total_timesteps_per_update": config.total_timesteps_per_update,
                "selection_mode": config.selection.mode,
                "selection_pool_mode": config.selection.pool_mode,
                "deployability_gate_mode": str(config.deployability_gate.mode),
                "deployability_target_mode": str(config.deployability_target.mode),
                "tail_acceptance_mode": str(config.tail_acceptance.mode),
                "deployability_gate": {
                    "mode": str(config.deployability_gate.mode),
                    "min_strict_margin_improvement": float(
                        config.deployability_gate.min_strict_margin_improvement
                    ),
                    "min_mean_violation_reduction": float(
                        config.deployability_gate.min_mean_violation_reduction
                    ),
                    "min_high_disruption_reduction": float(
                        config.deployability_gate.min_high_disruption_reduction
                    ),
                    "max_business_regression": float(
                        config.deployability_gate.max_business_regression
                    ),
                    "max_cost_regression": float(
                        config.deployability_gate.max_cost_regression
                    ),
                    "max_final_critical_increase": float(
                        config.deployability_gate.max_final_critical_increase
                    ),
                },
                "deployability_target": {
                    "mode": str(config.deployability_target.mode),
                    "reference_shell": str(config.deployability_target.reference_shell),
                    "min_target_score_improvement": float(
                        config.deployability_target.min_target_score_improvement
                    ),
                    "min_target_excess_reduction": float(
                        config.deployability_target.min_target_excess_reduction
                    ),
                    "max_business_regression": float(
                        config.deployability_target.max_business_regression
                    ),
                    "max_cost_regression": float(
                        config.deployability_target.max_cost_regression
                    ),
                    "max_final_critical_increase": float(
                        config.deployability_target.max_final_critical_increase
                    ),
                    "weights": dict(config.deployability_target.weights),
                },
                "tail_acceptance": {
                    "mode": str(config.tail_acceptance.mode),
                    "tail_eval_episodes": int(config.tail_acceptance.tail_eval_episodes),
                    "tail_alpha": float(config.tail_acceptance.tail_alpha),
                    "business_guardrail": float(
                        config.tail_acceptance.business_guardrail
                    ),
                    "cost_guardrail": float(config.tail_acceptance.cost_guardrail),
                    "persistent_non_regression": bool(
                        config.tail_acceptance.persistent_non_regression
                    ),
                    "dwell_slack": float(config.tail_acceptance.dwell_slack),
                },
                "selection_weights": dict(config.selection.score_weights),
                "selection_utility_tolerance": config.selection.utility_tolerance,
                "selection_keep_extremes": config.selection.keep_extremes,
                "selection_near_frontier_quota": int(config.selection.near_frontier_quota),
                "selection_strict_frontier_quota": int(config.selection.strict_frontier_quota),
                "extension_mode": config.extension_mode,
                "beta_mode": config.ipo.beta_mode,
                "beta_min": config.ipo.beta_min,
                "beta_max": config.ipo.beta_max,
                "beta_schedule_weights": dict(config.ipo.schedule_weights),
                "round_summaries": round_summaries,
                "deployability_frontiers": dict(final_deployability_frontiers),
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
