from __future__ import annotations

import argparse
import uuid
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

from cmorl_minicage.config import load_lagrangian_ppo_config
from cmorl_minicage.env import MiniCageMORLEnv
from cmorl_minicage.evaluate_constraints import compute_shared_thresholds, evaluate_constraints
from cmorl_minicage.models import ActorCritic
from cmorl_minicage.storage import VectorRolloutStorage
from cmorl_minicage.train_stage1 import collect_rollout, evaluate_policy
from cmorl_minicage.utils import ensure_dir, load_json, save_json, set_seed


def _num_updates(total_timesteps: int, num_steps: int, num_envs: int) -> int:
    return max(total_timesteps // (num_steps * num_envs), 1)


def _lagrangian_update(model, optimizer, storage, lambdas, config) -> dict[str, float]:
    advantages_vec = storage.advantages()
    scalar_advantages = (
        advantages_vec[..., 0]
        + float(lambdas[0]) * advantages_vec[..., 1]
        + float(lambdas[1]) * advantages_vec[..., 2]
    )
    scalar_advantages = (scalar_advantages - scalar_advantages.mean()) / (
        scalar_advantages.std() + 1e-8
    )

    value_loss_epoch = 0.0
    action_loss_epoch = 0.0
    entropy_epoch = 0.0
    updates = 0

    for _ in range(config.ppo_epochs):
        for batch in storage.feed_forward_generator(config.num_mini_batch):
            batch_scalar_advantages = (
                batch.advantages[:, 0]
                + float(lambdas[0]) * batch.advantages[:, 1]
                + float(lambdas[1]) * batch.advantages[:, 2]
            )
            batch_scalar_advantages = (
                batch_scalar_advantages - scalar_advantages.mean()
            ) / (scalar_advantages.std() + 1e-8)

            values, log_probs, entropy = model.evaluate_actions(batch.obs, batch.actions)
            ratio = torch.exp(log_probs - batch.old_log_probs)
            surr1 = ratio * batch_scalar_advantages
            surr2 = torch.clamp(
                ratio,
                1.0 - config.clip_param,
                1.0 + config.clip_param,
            ) * batch_scalar_advantages
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
        "lambda_business": float(lambdas[0]),
        "lambda_cost": float(lambdas[1]),
    }


def train_lagrangian_ppo(config) -> Path:
    set_seed(config.seed)
    run_dir = ensure_dir(Path(config.output_dir) / f"run_{uuid.uuid4().hex[:8]}")
    device = torch.device("cpu")

    thresholds_path = Path(config.thresholds_path) if config.thresholds_path else None
    if thresholds_path is None:
        if not config.stage1_buffer:
            raise ValueError("Either thresholds_path or stage1_buffer must be provided")
        thresholds_path = run_dir / "shared_thresholds.json"
        compute_shared_thresholds([config.stage1_buffer], thresholds_path)

    env = MiniCageMORLEnv(
        num_envs=config.env.num_envs,
        red_policy=config.env.red_policy,
        remove_bugs=config.env.remove_bugs,
        max_steps=config.env.max_episode_steps,
        seed=config.env.seed,
    )
    model = ActorCritic(
        obs_dim=env.obs_dim,
        action_dim=env.action_dim,
        obj_dim=env.obj_dim,
        hidden_sizes=(config.model.hidden_size, config.model.hidden_size),
    ).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    storage = VectorRolloutStorage(
        num_steps=config.rollout.num_steps,
        num_envs=config.env.num_envs,
        obs_dim=env.obs_dim,
        obj_dim=env.obj_dim,
        device=device,
    )
    thresholds = {key: float(value) for key, value in load_json(thresholds_path).items()}

    lambdas = np.zeros(2, dtype=np.float32)
    num_updates = _num_updates(
        config.total_timesteps,
        config.rollout.num_steps,
        config.env.num_envs,
    )
    training_log: list[dict[str, float]] = []
    for update_idx in range(num_updates):
        rollout_return, next_value = collect_rollout(env, model, storage, device)
        storage.compute_returns(next_value, config.gamma, config.gae_lambda)
        stats = _lagrangian_update(model, optimizer, storage, lambdas, config)
        lambdas[0] = max(
            0.0, float(lambdas[0] + config.dual_lr * (thresholds["d_business"] - rollout_return[1]))
        )
        lambdas[1] = max(
            0.0, float(lambdas[1] + config.dual_lr * (thresholds["d_cost"] - rollout_return[2]))
        )
        training_log.append(
            {
                "update_index": update_idx,
                "timesteps_seen": int(
                    (update_idx + 1) * config.rollout.num_steps * config.env.num_envs
                ),
                "rollout_security": float(rollout_return[0]),
                "rollout_business": float(rollout_return[1]),
                "rollout_cost": float(rollout_return[2]),
                "lambda_business": float(lambdas[0]),
                "lambda_cost": float(lambdas[1]),
                **stats,
            }
        )

    final_objective_vector = evaluate_policy(
        env, model, device, episodes=config.eval.eval_episodes
    ).tolist()
    checkpoint_path = run_dir / "policy_final.pt"
    torch.save(model.state_dict(), checkpoint_path)
    metadata_path = run_dir / "run_metadata.json"
    metadata = {
        "schema_version": "0.1.0",
        "method_name": "lagrangian_ppo",
        "model_type": "actor_critic",
        "policy_id": "lagrangian_ppo_final",
        "checkpoint_path": str(checkpoint_path),
        "final_objective_vector": final_objective_vector,
        "env": {
            "num_envs": config.env.num_envs,
            "red_policy": config.env.red_policy,
            "remove_bugs": config.env.remove_bugs,
            "max_episode_steps": config.env.max_episode_steps,
            "seed": config.env.seed,
        },
        "model": {
            "hidden_size": config.model.hidden_size,
            "obj_dim": config.model.obj_dim,
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
            "dual_lr": config.dual_lr,
            "thresholds_path": str(thresholds_path),
            "thresholds": thresholds,
            "final_lambdas": {
                "business": float(lambdas[0]),
                "cost": float(lambdas[1]),
            },
        },
    }
    save_json(metadata_path, metadata)
    save_json(run_dir / "training_summary.json", training_log)

    constraint_metrics = evaluate_constraints(
        method_name="lagrangian_ppo",
        input_kind="single_policy",
        input_path=metadata_path,
        selection_source="pareto",
        thresholds_path=thresholds_path,
        eval_episodes=config.eval.eval_episodes,
    )
    save_json(run_dir / "constraint_metrics.json", constraint_metrics)
    return metadata_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Train Lagrangian PPO on MiniCAGE.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()

    config = load_lagrangian_ppo_config(args.config)
    if args.output_dir is not None:
        config.output_dir = args.output_dir
    metadata_path = train_lagrangian_ppo(config)
    print(metadata_path)


if __name__ == "__main__":
    main()
