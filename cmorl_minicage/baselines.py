from __future__ import annotations

import argparse
import uuid
from dataclasses import replace
from pathlib import Path
from typing import Callable, Sequence

import numpy as np
import yaml

from cmorl_minicage.buffer import buffer_metadata, policy_record, save_policy_buffer
from cmorl_minicage.config import (
    DEFAULT_EVALUATE_CONFIG,
    DEFAULT_STAGE1_CONFIG,
    Stage1Config,
    load_evaluate_config,
    load_stage1_config,
)
from cmorl_minicage.env import MiniCageMORLEnv
from cmorl_minicage.evaluate import evaluate_policy_buffer
from cmorl_minicage.train_stage1 import train_stage1
from cmorl_minicage.utils import ensure_dir, save_json, set_seed

DEFAULT_WEIGHTED_SUM_PREFERENCES = [
    [0.8, 0.1, 0.1],
    [0.6, 0.2, 0.2],
    [1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0],
    [0.2, 0.6, 0.2],
    [0.2, 0.2, 0.6],
]


def _load_preferences_file(path: str | Path) -> list[list[float]]:
    with Path(path).open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    if isinstance(payload, dict):
        preferences = payload.get("preferences", [])
    else:
        preferences = payload
    if not isinstance(preferences, list) or not preferences:
        raise ValueError(f"Invalid preferences file: {path}")
    return [list(map(float, preference)) for preference in preferences]


def _evaluate_policy_fn(
    env: MiniCageMORLEnv,
    action_fn: Callable[[MiniCageMORLEnv, np.ndarray], np.ndarray],
    *,
    episodes: int,
) -> tuple[np.ndarray, dict[str, float]]:
    returns = np.zeros(env.obj_dim, dtype=np.float64)
    base_seed = env.seed
    semantic_totals = {
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

    for episode_idx in range(max(episodes, 1)):
        env.seed = base_seed if base_seed is None else int(base_seed) + episode_idx
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

        while not np.all(done):
            actions = action_fn(env, obs).reshape(env.num_envs, 1)
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
        semantic_totals["final_compromised_hosts"].extend(final_compromised_hosts.tolist())
        semantic_totals["final_critical_compromised_hosts"].extend(
            final_critical_compromised_hosts.tolist()
        )
        for key in episode_semantics:
            semantic_totals[key].extend(episode_semantics[key].tolist())

    returns /= max(episodes, 1)
    total_action_sum = max(float(np.sum(semantic_totals["total_action_count"])), 1.0)
    semantic_metrics = {
        "final_compromised_hosts": float(np.mean(semantic_totals["final_compromised_hosts"])),
        "final_critical_compromised_hosts": float(
            np.mean(semantic_totals["final_critical_compromised_hosts"])
        ),
        "critical_impact_count": float(np.mean(semantic_totals["critical_impact_count"])),
        "recovered_hosts": float(np.mean(semantic_totals["recovered_hosts"])),
        "analyse_count": float(np.mean(semantic_totals["analyse_count"])),
        "remove_count": float(np.mean(semantic_totals["remove_count"])),
        "restore_count": float(np.mean(semantic_totals["restore_count"])),
        "high_disruption_action_rate": float(
            np.sum(semantic_totals["high_disruption_action_count"]) / total_action_sum
        ),
        "semantic_eval_episodes": int(len(semantic_totals["final_compromised_hosts"])),
    }
    return returns.astype(np.float32), semantic_metrics


def _sleep_action_fn(env: MiniCageMORLEnv, obs: np.ndarray) -> np.ndarray:
    return np.zeros(env.num_envs, dtype=np.int32)


def _random_valid_action_fn(env: MiniCageMORLEnv, obs: np.ndarray) -> np.ndarray:
    blue_mask = env.sim.get_mask(env.sim.state, env.sim.current_decoys)["Blue"]
    actions = np.zeros(env.num_envs, dtype=np.int32)
    for idx in range(env.num_envs):
        valid_actions = np.flatnonzero(blue_mask[idx] > 0)
        actions[idx] = int(np.random.choice(valid_actions))
    return actions


def _heuristic_buffer(
    *,
    baseline_kind: str,
    objective_vector: Sequence[float],
    output_dir: str | Path,
    stage1_config: Stage1Config,
) -> Path:
    output_dir = ensure_dir(Path(output_dir))
    run_dir = ensure_dir(output_dir / f"run_{uuid.uuid4().hex[:8]}")
    record = policy_record(
        policy_id=f"{baseline_kind}_policy",
        checkpoint_path="",
        objective_vector=list(map(float, objective_vector)),
        stage="baseline",
        source="baseline_heuristic",
        notes={"baseline_kind": baseline_kind},
    )
    buffer_path = run_dir / "solution_buffer.json"
    save_policy_buffer(
        buffer_path,
        metadata=buffer_metadata(
            stage="baseline",
            env_config=stage1_config.env,
            model_config=stage1_config.model,
            rollout_config=stage1_config.rollout,
            optimizer_config={"name": baseline_kind},
            eval_config=stage1_config.eval,
            extra={
                "seed": stage1_config.seed,
                "baseline_kind": baseline_kind,
            },
        ),
        records=[record],
        pareto_front=[record],
    )
    save_json(run_dir / "pareto_front_baseline.json", [record])
    return buffer_path


def run_sleep_baseline(
    stage1_config: Stage1Config,
    evaluate_config,
    output_dir: str | Path,
) -> tuple[Path, Path]:
    set_seed(stage1_config.seed)
    env = MiniCageMORLEnv(
        num_envs=stage1_config.env.num_envs,
        red_policy=stage1_config.env.red_policy,
        remove_bugs=stage1_config.env.remove_bugs,
        max_steps=stage1_config.env.max_episode_steps,
        seed=stage1_config.env.seed,
    )
    objective_vector, _ = _evaluate_policy_fn(
        env,
        _sleep_action_fn,
        episodes=stage1_config.eval.eval_episodes,
    )
    buffer_path = _heuristic_buffer(
        baseline_kind="sleep",
        objective_vector=objective_vector,
        output_dir=output_dir,
        stage1_config=stage1_config,
    )
    result = evaluate_policy_buffer(
        buffer_path,
        evaluate_config.preference_step,
        reference_strategy=evaluate_config.reference_strategy,
        reference_margin=evaluate_config.reference_margin,
        reference_point=evaluate_config.reference_point,
        hv_max_exact_points=evaluate_config.hv_max_exact_points,
        hv_mc_samples=evaluate_config.hv_mc_samples,
        semantic_eval_batches=stage1_config.eval.eval_episodes,
    )
    metrics_path = buffer_path.with_name("metrics.json")
    save_json(metrics_path, result)
    return buffer_path, metrics_path


def run_random_valid_baseline(
    stage1_config: Stage1Config,
    evaluate_config,
    output_dir: str | Path,
) -> tuple[Path, Path]:
    set_seed(stage1_config.seed)
    env = MiniCageMORLEnv(
        num_envs=stage1_config.env.num_envs,
        red_policy=stage1_config.env.red_policy,
        remove_bugs=stage1_config.env.remove_bugs,
        max_steps=stage1_config.env.max_episode_steps,
        seed=stage1_config.env.seed,
    )
    objective_vector, _ = _evaluate_policy_fn(
        env,
        _random_valid_action_fn,
        episodes=stage1_config.eval.eval_episodes,
    )
    buffer_path = _heuristic_buffer(
        baseline_kind="random_valid",
        objective_vector=objective_vector,
        output_dir=output_dir,
        stage1_config=stage1_config,
    )
    result = evaluate_policy_buffer(
        buffer_path,
        evaluate_config.preference_step,
        reference_strategy=evaluate_config.reference_strategy,
        reference_margin=evaluate_config.reference_margin,
        reference_point=evaluate_config.reference_point,
        hv_max_exact_points=evaluate_config.hv_max_exact_points,
        hv_mc_samples=evaluate_config.hv_mc_samples,
        semantic_eval_batches=stage1_config.eval.eval_episodes,
    )
    metrics_path = buffer_path.with_name("metrics.json")
    save_json(metrics_path, result)
    return buffer_path, metrics_path


def run_stage1_only_baseline(
    buffer_path: str | Path,
    evaluate_config,
    output_path: str | Path | None = None,
) -> Path:
    result = evaluate_policy_buffer(
        buffer_path,
        evaluate_config.preference_step,
        reference_strategy=evaluate_config.reference_strategy,
        reference_margin=evaluate_config.reference_margin,
        reference_point=evaluate_config.reference_point,
        hv_max_exact_points=evaluate_config.hv_max_exact_points,
        hv_mc_samples=evaluate_config.hv_mc_samples,
    )
    if output_path is None:
        output_path = Path(buffer_path).with_name("metrics_stage1_only.json")
    output_path = Path(output_path)
    save_json(output_path, result)
    return output_path


def _run_learning_baseline(
    stage1_config: Stage1Config,
    evaluate_config,
    *,
    explicit_preferences: Sequence[Sequence[float]],
    output_dir: str | Path,
) -> tuple[Path, Path]:
    config = replace(
        stage1_config,
        explicit_preferences=[list(map(float, preference)) for preference in explicit_preferences],
        num_policies=len(explicit_preferences),
        preference_strategy="explicit",
        output_dir=str(output_dir),
    )
    buffer_path = train_stage1(config)
    result = evaluate_policy_buffer(
        buffer_path,
        evaluate_config.preference_step,
        reference_strategy=evaluate_config.reference_strategy,
        reference_margin=evaluate_config.reference_margin,
        reference_point=evaluate_config.reference_point,
        hv_max_exact_points=evaluate_config.hv_max_exact_points,
        hv_mc_samples=evaluate_config.hv_mc_samples,
    )
    metrics_path = Path(buffer_path).with_name("metrics.json")
    save_json(metrics_path, result)
    return Path(buffer_path), metrics_path


def run_single_objective_baseline(
    stage1_config: Stage1Config,
    evaluate_config,
    output_dir: str | Path,
) -> tuple[Path, Path]:
    preferences = np.eye(stage1_config.model.obj_dim, dtype=np.float32).tolist()
    return _run_learning_baseline(
        stage1_config,
        evaluate_config,
        explicit_preferences=preferences,
        output_dir=output_dir,
    )


def run_weighted_sum_baseline(
    stage1_config: Stage1Config,
    evaluate_config,
    output_dir: str | Path,
    *,
    preferences: Sequence[Sequence[float]] | None = None,
) -> tuple[Path, Path]:
    preference_list = preferences or DEFAULT_WEIGHTED_SUM_PREFERENCES
    per_policy_timesteps = max(
        int(stage1_config.total_timesteps // max(len(preference_list), 1)),
        stage1_config.rollout.num_steps * stage1_config.env.num_envs,
    )
    adjusted_config = replace(stage1_config, total_timesteps=per_policy_timesteps)
    return _run_learning_baseline(
        adjusted_config,
        evaluate_config,
        explicit_preferences=preference_list,
        output_dir=output_dir,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run baseline experiments for C-MORL MiniCAGE.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sleep_parser = subparsers.add_parser("sleep")
    sleep_parser.add_argument("--stage1-config", default=str(DEFAULT_STAGE1_CONFIG))
    sleep_parser.add_argument("--evaluate-config", default=str(DEFAULT_EVALUATE_CONFIG))
    sleep_parser.add_argument("--output-dir", required=True)

    random_parser = subparsers.add_parser("random-valid")
    random_parser.add_argument("--stage1-config", default=str(DEFAULT_STAGE1_CONFIG))
    random_parser.add_argument("--evaluate-config", default=str(DEFAULT_EVALUATE_CONFIG))
    random_parser.add_argument("--output-dir", required=True)

    stage1_only_parser = subparsers.add_parser("stage1-only")
    stage1_only_parser.add_argument("--buffer-path", required=True)
    stage1_only_parser.add_argument("--evaluate-config", default=str(DEFAULT_EVALUATE_CONFIG))
    stage1_only_parser.add_argument("--output-path", default=None)

    single_parser = subparsers.add_parser("single-objective")
    single_parser.add_argument("--stage1-config", default=str(DEFAULT_STAGE1_CONFIG))
    single_parser.add_argument("--evaluate-config", default=str(DEFAULT_EVALUATE_CONFIG))
    single_parser.add_argument("--output-dir", required=True)

    weighted_parser = subparsers.add_parser("weighted-sum")
    weighted_parser.add_argument("--stage1-config", default=str(DEFAULT_STAGE1_CONFIG))
    weighted_parser.add_argument("--evaluate-config", default=str(DEFAULT_EVALUATE_CONFIG))
    weighted_parser.add_argument("--output-dir", required=True)
    weighted_parser.add_argument("--preferences-file", default=None)

    args = parser.parse_args()
    if args.command == "stage1-only":
        evaluate_config = load_evaluate_config(args.evaluate_config)
        output_path = run_stage1_only_baseline(
            args.buffer_path, evaluate_config, args.output_path
        )
        print(output_path)
        return

    stage1_config = load_stage1_config(args.stage1_config)
    evaluate_config = load_evaluate_config(args.evaluate_config)

    if args.command == "sleep":
        buffer_path, metrics_path = run_sleep_baseline(
            stage1_config, evaluate_config, args.output_dir
        )
    elif args.command == "random-valid":
        buffer_path, metrics_path = run_random_valid_baseline(
            stage1_config, evaluate_config, args.output_dir
        )
    elif args.command == "single-objective":
        buffer_path, metrics_path = run_single_objective_baseline(
            stage1_config, evaluate_config, args.output_dir
        )
    else:
        preference_list = (
            _load_preferences_file(args.preferences_file)
            if getattr(args, "preferences_file", None)
            else None
        )
        buffer_path, metrics_path = run_weighted_sum_baseline(
            stage1_config,
            evaluate_config,
            args.output_dir,
            preferences=preference_list,
        )
    print(buffer_path)
    print(metrics_path)


if __name__ == "__main__":
    main()
