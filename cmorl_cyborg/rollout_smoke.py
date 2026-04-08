from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from cmorl_minicage.utils import save_json

from .config import DEFAULT_STAGE1_CONFIG, load_stage1_config
from .env import CybORGMORLEnv
from .scenario_profiles import load_scenario_profile


def _build_env(config, seed: int) -> CybORGMORLEnv:
    return CybORGMORLEnv(
        num_envs=config.env.num_envs,
        red_policy=config.env.red_policy,
        max_steps=config.env.max_episode_steps,
        seed=seed,
        scenario_name=config.env.scenario_name,
        scenario_profile=config.env.scenario_profile,
        blue_agent_name=config.env.blue_agent_name,
    )


def _find_action_index(
    env: CybORGMORLEnv,
    *,
    exact_name: str | None = None,
    name_prefix: str | None = None,
    hostname: str | None = None,
) -> int | None:
    for entry in env.action_catalog():
        name = str(entry["name"])
        params = entry.get("params", {})
        if exact_name is not None and name != exact_name:
            continue
        if name_prefix is not None and not name.startswith(name_prefix):
            continue
        if hostname is not None and params.get("hostname") != hostname:
            continue
        return int(entry["index"])
    return None


def _plan_actions(env: CybORGMORLEnv) -> dict[str, int]:
    profile = load_scenario_profile(env.scenario_name, env.scenario_profile)
    focus_host = profile.primary_focus_host
    sleep_idx = _find_action_index(env, exact_name="Sleep")
    if sleep_idx is None:
        raise ValueError("Sleep action not found in action catalog")
    monitor_idx = _find_action_index(env, exact_name="Monitor")
    if monitor_idx is None:
        monitor_idx = sleep_idx
    analyse_idx = (
        _find_action_index(env, exact_name="Analyse", hostname=focus_host)
        if focus_host is not None
        else None
    )
    if analyse_idx is None:
        analyse_idx = _find_action_index(env, exact_name="Analyse")
    if analyse_idx is None:
        analyse_idx = sleep_idx
    remove_idx = (
        _find_action_index(env, exact_name="Remove", hostname=focus_host)
        if focus_host is not None
        else None
    )
    if remove_idx is None:
        remove_idx = _find_action_index(env, exact_name="Remove")
    if remove_idx is None:
        remove_idx = sleep_idx
    restore_idx = (
        _find_action_index(env, exact_name="Restore", hostname=focus_host)
        if focus_host is not None
        else None
    )
    if restore_idx is None:
        restore_idx = _find_action_index(env, exact_name="Restore")
    if restore_idx is None:
        restore_idx = sleep_idx
    decoy_idx = (
        _find_action_index(
            env,
            name_prefix=profile.decoy_action_prefix,
            hostname=focus_host,
        )
        if focus_host is not None
        else None
    )
    if decoy_idx is None:
        decoy_idx = _find_action_index(env, name_prefix=profile.decoy_action_prefix)
    if decoy_idx is None:
        decoy_idx = sleep_idx
    return {
        "sleep": sleep_idx,
        "monitor": monitor_idx,
        f"analyse_{focus_host or 'focus'}": analyse_idx,
        f"remove_{focus_host or 'focus'}": remove_idx,
        f"restore_{focus_host or 'focus'}": restore_idx,
        f"decoy_{focus_host or 'focus'}": decoy_idx,
    }


def _assert_step_payload(
    env: CybORGMORLEnv,
    obs: np.ndarray,
    reward_vec: np.ndarray,
    done: np.ndarray,
    truncated: np.ndarray,
    info: dict,
) -> None:
    assert obs.shape == (env.num_envs, env.obs_dim), f"Unexpected obs shape: {obs.shape}"
    assert reward_vec.shape == (
        env.num_envs,
        3,
    ), f"Unexpected reward_vec shape: {reward_vec.shape}"
    assert done.shape == (env.num_envs,), f"Unexpected done shape: {done.shape}"
    assert truncated.shape == (
        env.num_envs,
    ), f"Unexpected truncated shape: {truncated.shape}"
    assert "reward_terms" in info, "Missing reward_terms"
    assert "semantic_info" in info, "Missing semantic_info"
    reward_terms = info["reward_terms"]
    semantic_info = info["semantic_info"]
    for key in ("security", "business", "cost", "morl_scalar_reward", "cyborg_scalar_reward"):
        assert key in reward_terms, f"Missing reward_terms[{key}]"
        assert len(reward_terms[key]) == env.num_envs, f"Unexpected reward_terms[{key}] length"
    for key in (
        "final_compromised_hosts",
        "final_critical_compromised_hosts",
        "critical_impact_count",
        "recovered_hosts",
        "analyse_count",
        "remove_count",
        "restore_count",
        "high_disruption_action_count",
        "total_action_count",
    ):
        assert key in semantic_info, f"Missing semantic_info[{key}]"
        assert len(semantic_info[key]) == env.num_envs, f"Unexpected semantic_info[{key}] length"
    assert np.isfinite(obs).all(), "Observation contains non-finite values"
    assert np.isfinite(reward_vec).all(), "Reward vector contains non-finite values"


def _run_plan(
    config,
    *,
    seed: int,
    steps: int,
    action_index: int,
    plan_name: str,
) -> dict:
    env = _build_env(config, seed)
    obs, reset_info = env.reset()
    _assert_step_payload(
        env,
        obs,
        np.zeros((env.num_envs, 3), dtype=np.float32),
        np.zeros(env.num_envs, dtype=bool),
        np.zeros(env.num_envs, dtype=bool),
        reset_info,
    )
    steps_payload: list[dict] = []
    compromised_counts: list[float] = []
    critical_counts: list[float] = []
    for step_idx in range(steps):
        actions = np.full((env.num_envs, 1), action_index, dtype=np.int32)
        obs, reward_vec, done, truncated, info = env.step(actions)
        _assert_step_payload(env, obs, reward_vec, done, truncated, info)
        compromised = info["semantic_info"]["final_compromised_hosts"]
        critical = info["semantic_info"]["final_critical_compromised_hosts"]
        compromised_counts.extend(compromised)
        critical_counts.extend(critical)
        steps_payload.append(
            {
                "step_index": step_idx,
                "action_index": int(action_index),
                "action_name": plan_name,
                "mean_reward": reward_vec.mean(axis=0).tolist(),
                "done_count": int(done.sum()),
                "mean_compromised_hosts": float(np.mean(compromised)),
                "mean_critical_compromised_hosts": float(np.mean(critical)),
            }
        )
        if np.all(done | truncated):
            break
    return {
        "seed": int(seed),
        "plan_name": plan_name,
        "obs_shape": list(obs.shape),
        "reward_shape": [env.num_envs, 3],
        "action_dim": env.action_dim,
        "completed_steps": len(steps_payload),
        "steps": steps_payload,
        "max_compromised_hosts": float(np.max(compromised_counts)) if compromised_counts else 0.0,
        "max_critical_compromised_hosts": float(np.max(critical_counts)) if critical_counts else 0.0,
    }


def rollout_smoke(
    config_path: str | Path,
    steps: int = 20,
    *,
    num_seeds: int = 3,
) -> dict:
    config = load_stage1_config(config_path)
    seed_values = [int(config.env.seed) + i for i in range(num_seeds)]
    probe_env = _build_env(config, seed_values[0])
    action_plans = _plan_actions(probe_env)
    runs = []
    for seed in seed_values:
        for plan_name, action_index in action_plans.items():
            runs.append(
                _run_plan(
                    config,
                    seed=seed,
                    steps=steps,
                    action_index=action_index,
                    plan_name=plan_name,
                )
            )
    return {
        "scenario_name": config.env.scenario_name,
        "num_envs": int(config.env.num_envs),
        "scenario_profile": load_scenario_profile(
            config.env.scenario_name,
            config.env.scenario_profile,
        ).profile_name,
        "seed_values": seed_values,
        "action_plans": action_plans,
        "num_runs": len(runs),
        "runs": runs,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a simple CybORG rollout smoke test.")
    parser.add_argument("--config", default=str(DEFAULT_STAGE1_CONFIG))
    parser.add_argument("--steps", type=int, default=20)
    parser.add_argument("--num-seeds", type=int, default=3)
    parser.add_argument("--output-path", default=None)
    args = parser.parse_args()

    payload = rollout_smoke(args.config, steps=args.steps, num_seeds=args.num_seeds)
    if args.output_path:
        save_json(args.output_path, payload)
        print(args.output_path)
    else:
        print(payload)


if __name__ == "__main__":
    main()
