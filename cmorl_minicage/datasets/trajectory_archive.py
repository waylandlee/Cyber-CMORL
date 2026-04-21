from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import torch

from cmorl_minicage.buffer import load_policy_buffer
from cmorl_minicage.env import MiniCageMORLEnv
from cmorl_minicage.models import ActorCritic
from cmorl_minicage.shield import default_policy_action_mask, record_policy_mask_stats
from cmorl_minicage.utils import save_json


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


def _random_valid_actions(env: MiniCageMORLEnv) -> np.ndarray:
    blue_mask = default_policy_action_mask(env)
    actions = np.zeros(env.num_envs, dtype=np.int32)
    for idx in range(env.num_envs):
        valid_actions = np.flatnonzero(blue_mask[idx] > 0)
        actions[idx] = int(np.random.choice(valid_actions))
    return actions


def _record_trajectories(
    env: MiniCageMORLEnv,
    *,
    action_source: str,
    checkpoint_path: str | None,
    baseline_kind: str | None,
    hidden_size: int,
    episodes: int,
) -> tuple[list[dict[str, Any]], list[list[float]]]:
    device = torch.device("cpu")
    actor_critic = None
    if action_source == "policy":
        actor_critic = ActorCritic(
            obs_dim=env.obs_dim,
            action_dim=env.action_dim,
            obj_dim=env.obj_dim,
            hidden_sizes=(hidden_size, hidden_size),
        ).to(device)
        checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=True)
        actor_critic.load_state_dict(checkpoint)
        actor_critic.eval()

    transitions: list[dict[str, Any]] = []
    command_returns: list[list[float]] = []
    with torch.no_grad():
        for _ in range(max(episodes, 1)):
            obs, _ = env.reset()
            done = np.zeros(env.num_envs, dtype=bool)
            per_env_obs: list[list[np.ndarray]] = [[] for _ in range(env.num_envs)]
            per_env_actions: list[list[int]] = [[] for _ in range(env.num_envs)]
            per_env_rewards: list[list[np.ndarray]] = [[] for _ in range(env.num_envs)]

            step_idx = 0
            while not np.all(done):
                if actor_critic is not None:
                    obs_tensor = torch.as_tensor(obs, dtype=torch.float32, device=device)
                    action_mask = torch.as_tensor(
                        default_policy_action_mask(env),
                        dtype=torch.bool,
                        device=device,
                    )
                    policy_output = actor_critic.act(
                        obs_tensor,
                        action_mask=action_mask,
                    )
                    record_policy_mask_stats(env, policy_output.blocked_probability_mass)
                    actions = policy_output.actions.cpu().numpy().reshape(env.num_envs)
                elif baseline_kind == "random_valid":
                    actions = _random_valid_actions(env)
                else:
                    actions = np.zeros(env.num_envs, dtype=np.int32)

                next_obs, reward_vec, done, _, _ = env.step(actions.reshape(env.num_envs, 1))
                for env_idx in range(env.num_envs):
                    per_env_obs[env_idx].append(np.asarray(obs[env_idx], dtype=np.float32))
                    per_env_actions[env_idx].append(int(actions[env_idx]))
                    per_env_rewards[env_idx].append(np.asarray(reward_vec[env_idx], dtype=np.float32))
                obs = next_obs
                step_idx += 1

            for env_idx in range(env.num_envs):
                rewards = per_env_rewards[env_idx]
                if not rewards:
                    continue
                returns = np.asarray(rewards, dtype=np.float32)
                rtg = np.flip(np.cumsum(np.flip(returns, axis=0), axis=0), axis=0)
                trajectory_return = rtg[0].tolist()
                command_returns.append(trajectory_return)
                horizon = len(rewards)
                for t, (obs_t, action_t, rtg_t) in enumerate(
                    zip(per_env_obs[env_idx], per_env_actions[env_idx], rtg)
                ):
                    transitions.append(
                        {
                            "obs": obs_t.tolist(),
                            "action": int(action_t),
                            "return_to_go_vec": rtg_t.tolist(),
                            "remaining_horizon": int(horizon - t),
                            "trajectory_return": trajectory_return,
                        }
                    )
    return transitions, command_returns


def build_trajectory_archive(
    source_paths: list[str | Path],
    *,
    output_path: str | Path,
    episodes_per_source: int,
) -> dict[str, Any]:
    all_transitions: list[dict[str, Any]] = []
    all_command_returns: list[list[float]] = []
    source_summaries: list[dict[str, Any]] = []

    for source_path in source_paths:
        payload = load_policy_buffer(source_path)
        metadata = payload.get("metadata", {})
        env = MiniCageMORLEnv(
            num_envs=int(metadata.get("env", {}).get("num_envs", 8)),
            red_policy=metadata.get("env", {}).get("red_policy", "bline"),
            remove_bugs=bool(metadata.get("env", {}).get("remove_bugs", True)),
            max_steps=int(metadata.get("env", {}).get("max_episode_steps", 100)),
            seed=int(metadata.get("env", {}).get("seed", 7)),
            obj_dim=int(metadata.get("model", {}).get("obj_dim", 3)),
            critical_host_safety_mode=str(
                metadata.get("model", {}).get("critical_host_safety_mode", "v2_legacy")
            ),
            shield_mode=str(metadata.get("shield", {}).get("mode", "disabled")),
        )
        hidden_size = int(metadata.get("model", {}).get("hidden_size", 128))
        records = payload.get("pareto_front") or payload.get("records", [])
        source_transition_count = 0
        source_command_count = 0
        for record in records:
            if record.get("source") == "baseline_heuristic":
                baseline_kind = record.get("notes", {}).get("baseline_kind", "sleep")
                transitions, command_returns = _record_trajectories(
                    env,
                    action_source="heuristic",
                    checkpoint_path=None,
                    baseline_kind=baseline_kind,
                    hidden_size=hidden_size,
                    episodes=episodes_per_source,
                )
            else:
                transitions, command_returns = _record_trajectories(
                    env,
                    action_source="policy",
                    checkpoint_path=str(_resolve_path(source_path, record["checkpoint_path"])),
                    baseline_kind=None,
                    hidden_size=hidden_size,
                    episodes=episodes_per_source,
                )
            all_transitions.extend(transitions)
            all_command_returns.extend(command_returns)
            source_transition_count += len(transitions)
            source_command_count += len(command_returns)
        source_summaries.append(
            {
                "source_path": str(source_path),
                "num_records": len(records),
                "num_transitions": source_transition_count,
                "num_commands": source_command_count,
            }
        )

    payload = {
        "schema_version": "0.1.0",
        "transitions": all_transitions,
        "command_returns": all_command_returns,
        "sources": source_summaries,
    }
    save_json(output_path, payload)
    return payload
