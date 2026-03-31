from __future__ import annotations

import argparse
import uuid
from pathlib import Path

import numpy as np
import torch

from cmorl_minicage.buffer import buffer_metadata, policy_record, save_policy_buffer
from cmorl_minicage.config import (
    DEFAULT_STAGE1_CONFIG,
    load_stage1_config,
)
from cmorl_minicage.algorithms.ppo_vector import PPOConfig, VectorPPO
from cmorl_minicage.algorithms.selection import nondominated_filter
from cmorl_minicage.env import MiniCageMORLEnv
from cmorl_minicage.models import ActorCritic
from cmorl_minicage.storage import VectorRolloutStorage
from cmorl_minicage.utils import ensure_dir, save_json, sample_preferences, set_seed

def evaluate_policy(
    env: MiniCageMORLEnv, actor_critic: ActorCritic, device: torch.device, episodes: int = 3
) -> np.ndarray:
    returns = np.zeros(env.obj_dim, dtype=np.float64)
    with torch.no_grad():
        for _ in range(episodes):
            obs, _ = env.reset()
            done = np.zeros(env.num_envs, dtype=bool)
            while not np.all(done):
                obs_tensor = torch.as_tensor(obs, dtype=torch.float32, device=device)
                actions = actor_critic.act(obs_tensor).actions.cpu().numpy().reshape(env.num_envs, 1)
                obs, reward_vec, done, _, _ = env.step(actions)
                returns += reward_vec.mean(axis=0)
    returns /= episodes
    return returns.astype(np.float32)


def collect_rollout(
    env: MiniCageMORLEnv,
    actor_critic: ActorCritic,
    storage: VectorRolloutStorage,
    device: torch.device,
) -> np.ndarray:
    obs, _ = env.reset()
    obs_tensor = torch.as_tensor(obs, dtype=torch.float32, device=device)
    storage.reset()
    storage.obs[0].copy_(obs_tensor)
    episode_return = np.zeros((env.num_envs, env.obj_dim), dtype=np.float32)

    for step in range(storage.num_steps):
        with torch.no_grad():
            policy_output = actor_critic.act(obs_tensor)
        actions = policy_output.actions.cpu().numpy().reshape(env.num_envs, 1)
        next_obs, reward_vec, done, _, _ = env.step(actions)
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
        obs_tensor = next_obs_tensor
        episode_return += reward_vec

    with torch.no_grad():
        next_value = actor_critic.get_value(obs_tensor)
    return episode_return.mean(axis=0), next_value


def train_stage1(config: Stage1Config) -> Path:
    set_seed(config.seed)
    output_dir = ensure_dir(Path(config.output_dir))
    run_dir = ensure_dir(output_dir / f"run_{uuid.uuid4().hex[:8]}")
    device = torch.device("cpu")

    env = MiniCageMORLEnv(
        num_envs=config.env.num_envs,
        red_policy=config.env.red_policy,
        remove_bugs=config.env.remove_bugs,
        max_steps=config.env.max_episode_steps,
        seed=config.env.seed,
    )

    if config.explicit_preferences:
        preferences = [
            list(map(float, preference)) for preference in config.explicit_preferences
        ]
        if any(len(preference) != env.obj_dim for preference in preferences):
            raise ValueError(
                f"All explicit_preferences must have length {env.obj_dim}"
            )
    else:
        preferences = sample_preferences(
            num_policies=config.num_policies,
            dimensions=env.obj_dim,
            strategy=config.preference_strategy,
            seed=config.seed,
            step=config.preference_step,
            dirichlet_alpha=config.preference_dirichlet_alpha,
        )

    num_policies = len(preferences)
    ppo_config = PPOConfig()
    records: list[dict] = []
    policy_id_counter = 0
    stage1_summary: list[dict] = []

    for pref_idx, preference in enumerate(preferences):
        actor_critic = ActorCritic(
            obs_dim=env.obs_dim,
            action_dim=env.action_dim,
            obj_dim=env.obj_dim,
            hidden_sizes=(config.model.hidden_size, config.model.hidden_size),
        ).to(device)
        trainer = VectorPPO(actor_critic, ppo_config)
        storage = VectorRolloutStorage(
            num_steps=config.rollout.num_steps,
            num_envs=config.env.num_envs,
            obs_dim=env.obs_dim,
            obj_dim=env.obj_dim,
            device=device,
        )

        num_updates = max(
            config.total_timesteps // (config.rollout.num_steps * config.env.num_envs),
            1,
        )
        save_every = config.save_interval_updates or max(num_updates // 2, 1)
        preference_saves: list[dict] = []
        for update_idx in range(num_updates):
            rollout_return, next_value = collect_rollout(env, actor_critic, storage, device)
            storage.compute_returns(next_value, ppo_config.gamma, ppo_config.gae_lambda)
            trainer_stats = trainer.update(storage, preference)

            if update_idx == num_updates - 1 or update_idx % save_every == 0:
                objective_vector = evaluate_policy(
                    env, actor_critic, device, episodes=config.eval.eval_episodes
                )
                scalarized_utility = float(np.dot(np.asarray(preference), objective_vector))
                checkpoint_path = run_dir / f"policy_{policy_id_counter:03d}.pt"
                torch.save(actor_critic.state_dict(), checkpoint_path)
                record = policy_record(
                    policy_id=f"stage1_pref_{pref_idx:03d}_ckpt_{update_idx:03d}",
                    checkpoint_path=str(checkpoint_path),
                    preference=list(map(float, preference)),
                    objective_vector=objective_vector.tolist(),
                    stage="stage1",
                    source="stage1",
                    update_index=update_idx,
                    notes={
                        "preference_index": pref_idx,
                        "save_index_within_policy": len(preference_saves),
                        "timesteps_seen": int((update_idx + 1) * config.rollout.num_steps * config.env.num_envs),
                        "rollout_return_estimate": rollout_return.tolist(),
                        "scalarized_utility": scalarized_utility,
                        "trainer_stats": trainer_stats,
                    },
                )
                pareto_after_save = nondominated_filter(records + [record])
                record.setdefault("notes", {})
                record["notes"].update(
                    {
                        "pareto_size_after_save": len(pareto_after_save),
                        "is_nondominated_after_save": any(
                            entry["policy_id"] == record["policy_id"] for entry in pareto_after_save
                        ),
                    }
                )
                records.append(record)
                preference_saves.append(
                    {
                        "policy_id": record["policy_id"],
                        "update_index": update_idx,
                        "objective_vector": objective_vector.tolist(),
                        "scalarized_utility": scalarized_utility,
                    }
                )
                policy_id_counter += 1

        final_entry = preference_saves[-1] if preference_saves else None
        best_entry = (
            max(preference_saves, key=lambda entry: entry["scalarized_utility"])
            if preference_saves
            else None
        )
        stage1_summary.append(
            {
                "preference_index": pref_idx,
                "preference": list(map(float, preference)),
                "num_updates": num_updates,
                "save_every": save_every,
                "timesteps_per_policy": int(num_updates * config.rollout.num_steps * config.env.num_envs),
                "num_saved_checkpoints": len(preference_saves),
                "final_policy_id": None if final_entry is None else final_entry["policy_id"],
                "final_objective_vector": None if final_entry is None else final_entry["objective_vector"],
                "best_policy_id": None if best_entry is None else best_entry["policy_id"],
                "best_scalarized_utility": None if best_entry is None else best_entry["scalarized_utility"],
            }
        )

    pareto_front = nondominated_filter(records)
    buffer_path = run_dir / "solution_buffer.json"
    save_policy_buffer(
        buffer_path,
        metadata=buffer_metadata(
            stage="stage1",
            env_config=config.env,
            model_config=config.model,
            rollout_config=config.rollout,
            optimizer_config=ppo_config,
            eval_config=config.eval,
            extra={
                "seed": config.seed,
                "num_policies": num_policies,
                "preference_strategy": config.preference_strategy,
                "preference_step": config.preference_step,
                "preference_dirichlet_alpha": config.preference_dirichlet_alpha,
                "explicit_preferences": config.explicit_preferences,
                "preferences": preferences,
                "total_timesteps": config.total_timesteps,
                "timesteps_per_policy": int(num_updates * config.rollout.num_steps * config.env.num_envs),
                "total_stage_timesteps": int(
                    num_policies * num_updates * config.rollout.num_steps * config.env.num_envs
                ),
                "stage1_summary": stage1_summary,
            },
        ),
        records=records,
        pareto_front=pareto_front,
    )
    save_json(run_dir / "pareto_front_stage1.json", pareto_front)
    save_json(run_dir / "stage1_summary.json", stage1_summary)
    return buffer_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage-1 C-MORL training on MiniCAGE.")
    parser.add_argument("--config", default=str(DEFAULT_STAGE1_CONFIG))
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()

    config = load_stage1_config(args.config)
    if args.output_dir is not None:
        config.output_dir = args.output_dir
    buffer_path = train_stage1(config)
    print(f"Saved stage-1 outputs to {buffer_path}")


if __name__ == "__main__":
    main()
