from __future__ import annotations

import argparse
import uuid
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

from cmorl_minicage.models import PreferenceConditionedActorCritic
from cmorl_minicage.storage import ScalarRolloutStorage
from cmorl_minicage.utils import ensure_dir, sample_preferences, save_json, set_seed

from .config import (
    DEFAULT_PREFERENCE_CONDITIONED_PPO_CONFIG,
    load_preference_conditioned_ppo_config,
)
from .env import CybORGMORLEnv


def _num_updates(total_timesteps: int, num_steps: int, num_envs: int) -> int:
    return max(total_timesteps // (num_steps * num_envs), 1)


def _sample_env_preferences(
    config,
    rng: np.random.Generator,
    num_envs: int,
    obj_dim: int,
) -> np.ndarray:
    if config.explicit_preferences:
        preferences = np.asarray(config.explicit_preferences, dtype=np.float32)
        indices = rng.integers(0, len(preferences), size=num_envs)
        return preferences[indices]
    preferences = sample_preferences(
        num_policies=num_envs,
        dimensions=obj_dim,
        strategy=config.preference_strategy,
        seed=int(rng.integers(0, 2**31 - 1)),
        step=config.preference_step,
        dirichlet_alpha=config.preference_dirichlet_alpha,
    )
    return np.asarray(preferences, dtype=np.float32)


def _collect_rollout(env, model, storage, device, config, rng) -> torch.Tensor:
    obs, _ = env.reset()
    obs_tensor = torch.as_tensor(obs, dtype=torch.float32, device=device)
    preference_batch = _sample_env_preferences(config, rng, env.num_envs, env.obj_dim)
    preference_tensor = torch.as_tensor(
        preference_batch,
        dtype=torch.float32,
        device=device,
    )

    storage.reset()
    storage.obs[0].copy_(obs_tensor)
    storage.preferences[0].copy_(preference_tensor)

    for _ in range(storage.num_steps):
        with torch.no_grad():
            output = model.act(obs_tensor, preference_tensor)
        actions = output.actions.cpu().numpy().reshape(env.num_envs, 1)
        next_obs, reward_vec, done, _, _ = env.step(actions)
        scalar_reward = np.sum(reward_vec * preference_batch, axis=1)
        next_obs_tensor = torch.as_tensor(next_obs, dtype=torch.float32, device=device)
        reward_tensor = torch.as_tensor(
            scalar_reward,
            dtype=torch.float32,
            device=device,
        )
        masks = torch.as_tensor(
            1.0 - done.astype(np.float32),
            dtype=torch.float32,
            device=device,
        )
        storage.insert(
            obs=next_obs_tensor,
            preference=preference_tensor,
            actions=output.actions,
            log_probs=output.log_probs,
            values=output.values,
            rewards=reward_tensor,
            masks=masks,
        )
        obs_tensor = next_obs_tensor
    with torch.no_grad():
        next_value = model.get_value(obs_tensor, preference_tensor)
    return next_value


def _ppo_update(model, optimizer, storage, config) -> dict[str, float]:
    advantages = storage.advantages()
    advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

    value_loss_epoch = 0.0
    action_loss_epoch = 0.0
    entropy_epoch = 0.0
    updates = 0

    for _ in range(config.ppo_epochs):
        for batch in storage.feed_forward_generator(config.num_mini_batch):
            batch_advantages = (
                batch.advantages - advantages.mean()
            ) / (advantages.std() + 1e-8)
            values, log_probs, entropy = model.evaluate_actions(
                batch.obs,
                batch.preference,
                batch.actions,
            )
            ratio = torch.exp(log_probs - batch.old_log_probs)
            surr1 = ratio * batch_advantages
            surr2 = torch.clamp(
                ratio,
                1.0 - config.clip_param,
                1.0 + config.clip_param,
            ) * batch_advantages
            action_loss = -torch.min(surr1, surr2).mean()
            value_loss = F.mse_loss(values, batch.returns)
            entropy_bonus = entropy.mean()

            optimizer.zero_grad()
            total_loss = (
                action_loss
                + config.value_loss_coef * value_loss
                - config.entropy_coef * entropy_bonus
            )
            total_loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), config.max_grad_norm)
            optimizer.step()

            value_loss_epoch += float(value_loss.item())
            action_loss_epoch += float(action_loss.item())
            entropy_epoch += float(entropy_bonus.item())
            updates += 1

    updates = max(updates, 1)
    return {
        "value_loss": value_loss_epoch / updates,
        "action_loss": action_loss_epoch / updates,
        "entropy": entropy_epoch / updates,
    }


def train_preference_conditioned_ppo(config) -> Path:
    set_seed(config.seed)
    run_dir = ensure_dir(Path(config.output_dir) / f"run_{uuid.uuid4().hex[:8]}")
    device = torch.device("cpu")
    env = CybORGMORLEnv(
        num_envs=config.env.num_envs,
        red_policy=config.env.red_policy,
        remove_bugs=config.env.remove_bugs,
        max_steps=config.env.max_episode_steps,
        seed=config.env.seed,
        scenario_name=config.env.scenario_name,
        scenario_profile=config.env.scenario_profile,
        gym_wrapper_name=config.env.gym_wrapper_name,
        blue_agent_name=config.env.blue_agent_name,
        red_agent_name=config.env.red_agent_name,
        obs_mode=config.env.obs_mode,
        state_mode=str(config.env.state_mode),
        obj_dim=config.model.obj_dim,
        critical_host_safety_mode=config.model.critical_host_safety_mode,
    )
    model = PreferenceConditionedActorCritic(
        obs_dim=env.obs_dim,
        preference_dim=env.obj_dim,
        action_dim=env.action_dim,
        hidden_sizes=(config.model.hidden_size, config.model.hidden_size),
    ).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    storage = ScalarRolloutStorage(
        num_steps=config.rollout.num_steps,
        num_envs=config.env.num_envs,
        obs_dim=env.obs_dim,
        preference_dim=env.obj_dim,
        device=device,
    )
    rng = np.random.default_rng(config.seed)

    num_updates = _num_updates(
        config.total_timesteps,
        config.rollout.num_steps,
        config.env.num_envs,
    )
    training_log: list[dict[str, float]] = []
    for update_idx in range(num_updates):
        next_value = _collect_rollout(env, model, storage, device, config, rng)
        storage.compute_returns(next_value, config.gamma, config.gae_lambda)
        stats = _ppo_update(model, optimizer, storage, config)
        training_log.append(
            {
                "update_index": update_idx,
                "timesteps_seen": int(
                    (update_idx + 1) * config.rollout.num_steps * config.env.num_envs
                ),
                **stats,
            }
        )

    checkpoint_path = run_dir / "policy_final.pt"
    torch.save(model.state_dict(), checkpoint_path)

    metadata = {
        "schema_version": "0.2.0",
        "method_name": "preference_conditioned_ppo",
        "model_type": "preference_conditioned_ppo",
        "policy_id": "pref_conditioned_final",
        "checkpoint_path": str(checkpoint_path),
        "env": {
            "num_envs": config.env.num_envs,
            "red_policy": config.env.red_policy,
            "remove_bugs": config.env.remove_bugs,
            "max_episode_steps": config.env.max_episode_steps,
            "seed": config.env.seed,
            "scenario_name": config.env.scenario_name,
            "scenario_profile": config.env.scenario_profile,
            "gym_wrapper_name": config.env.gym_wrapper_name,
            "blue_agent_name": config.env.blue_agent_name,
            "red_agent_name": config.env.red_agent_name,
            "obs_mode": config.env.obs_mode,
            "state_mode": str(config.env.state_mode),
        },
        "model": {
            "hidden_size": config.model.hidden_size,
            "obj_dim": config.model.obj_dim,
            "critical_host_safety_enabled": bool(
                config.model.critical_host_safety_enabled
            ),
            "critical_host_safety_mode": config.model.critical_host_safety_mode,
        },
        "rollout": {"num_steps": config.rollout.num_steps},
        "evaluation": {
            "eval_episodes": config.eval.eval_episodes,
            "preference_step": config.eval.preference_step,
        },
        "training": {
            "seed": config.seed,
            "total_timesteps": config.total_timesteps,
            "num_updates": num_updates,
            "preference_strategy": config.preference_strategy,
            "preference_step": config.preference_step,
            "preference_dirichlet_alpha": config.preference_dirichlet_alpha,
            "explicit_preferences": config.explicit_preferences,
            "clip_param": config.clip_param,
            "ppo_epochs": config.ppo_epochs,
            "num_mini_batch": config.num_mini_batch,
            "learning_rate": config.learning_rate,
            "gamma": config.gamma,
            "gae_lambda": config.gae_lambda,
            "output_dir": str(Path(config.output_dir)),
        },
    }
    metadata_path = run_dir / "run_metadata.json"
    legacy_metadata_path = run_dir / "conditioned_run_metadata.json"
    save_json(metadata_path, metadata)
    save_json(legacy_metadata_path, metadata)
    save_json(run_dir / "training_summary.json", training_log)
    return metadata_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Train a preference-conditioned PPO policy on formal CybORG."
    )
    parser.add_argument(
        "--config",
        default=str(DEFAULT_PREFERENCE_CONDITIONED_PPO_CONFIG),
    )
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()

    config = load_preference_conditioned_ppo_config(args.config)
    if args.output_dir is not None:
        config.output_dir = args.output_dir
    metadata_path = train_preference_conditioned_ppo(config)
    print(metadata_path)


if __name__ == "__main__":
    main()
