from __future__ import annotations

import argparse
import multiprocessing as mp
import uuid
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import torch

from cmorl_minicage.algorithms.ppo_vector import PPOConfig, VectorPPO
from cmorl_minicage.algorithms.selection import nondominated_filter
from cmorl_minicage.buffer import buffer_metadata, policy_record, save_policy_buffer
from cmorl_minicage.config import DEFAULT_STAGE1_CONFIG, Stage1Config, load_stage1_config
from cmorl_minicage.env import MiniCageMORLEnv
from cmorl_minicage.models import ActorCritic
from cmorl_minicage.shield import default_policy_action_mask, record_policy_mask_stats
from cmorl_minicage.storage import VectorRolloutStorage
from cmorl_minicage.utils import ensure_dir, sample_preferences, save_json, set_seed


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
                action_mask = torch.as_tensor(
                    default_policy_action_mask(env),
                    dtype=torch.bool,
                    device=device,
                )
                policy_output = actor_critic.act(obs_tensor, action_mask=action_mask)
                record_policy_mask_stats(env, policy_output.blocked_probability_mass)
                actions = policy_output.actions.cpu().numpy().reshape(env.num_envs, 1)
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
            action_mask = torch.as_tensor(
                default_policy_action_mask(env),
                dtype=torch.bool,
                device=device,
            )
            policy_output = actor_critic.act(obs_tensor, action_mask=action_mask)
            record_policy_mask_stats(env, policy_output.blocked_probability_mass)
        actions = policy_output.actions.cpu().numpy().reshape(env.num_envs, 1)
        next_obs, reward_vec, done, _, _ = env.step(actions)
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


def _validate_stage1_config(config: Stage1Config) -> None:
    if config.reseed_mode not in {"shared", "per_preference"}:
        raise ValueError(f"Unsupported reseed_mode: {config.reseed_mode}")
    if config.parallel_backend != "process":
        raise ValueError(f"Unsupported parallel_backend: {config.parallel_backend}")
    if config.merge_order != "preference_index":
        raise ValueError(f"Unsupported merge_order: {config.merge_order}")
    if config.parallel_workers <= 0:
        raise ValueError("parallel_workers must be positive")
    if config.preference_seed_stride <= 0:
        raise ValueError("preference_seed_stride must be positive")
    if config.env_seed_stride <= 0:
        raise ValueError("env_seed_stride must be positive")
    if int(config.model.obj_dim) not in (3, 4):
        raise ValueError("model.obj_dim must be 3 or 4")


def _resolve_preference_seed(config: Stage1Config, pref_idx: int) -> int:
    if config.reseed_mode == "shared":
        return int(config.seed)
    return int(config.seed + pref_idx * config.preference_seed_stride)


def _resolve_env_seed(config: Stage1Config, pref_idx: int) -> int:
    if not config.independent_env_per_preference:
        return int(config.env.seed)
    return int(config.env.seed + pref_idx * config.env_seed_stride)


def _build_env(config: Stage1Config, env_seed: int) -> MiniCageMORLEnv:
    return MiniCageMORLEnv(
        num_envs=config.env.num_envs,
        red_policy=config.env.red_policy,
        remove_bugs=config.env.remove_bugs,
        max_steps=config.env.max_episode_steps,
        seed=env_seed,
        obj_dim=int(config.model.obj_dim),
        critical_host_safety_mode=str(config.model.critical_host_safety_mode),
        shield_mode=str(config.shield.mode),
    )


def _checkpoint_path(run_dir: Path, pref_idx: int, update_idx: int) -> Path:
    return run_dir / f"policy_pref_{pref_idx:03d}_ckpt_{update_idx:03d}.pt"


def _num_updates(config: Stage1Config) -> int:
    return max(config.total_timesteps // (config.rollout.num_steps * config.env.num_envs), 1)


def _save_every(config: Stage1Config, num_updates: int) -> int:
    return config.save_interval_updates or max(num_updates // 2, 1)


def train_single_preference(
    *,
    pref_idx: int,
    preference: list[float],
    config: Stage1Config,
    device: torch.device,
    pref_seed: int,
    pref_env_seed: int,
    run_dir: Path,
    execution_mode: str,
    env: MiniCageMORLEnv | None = None,
) -> dict:
    if execution_mode == "parallel":
        torch.set_num_threads(1)

    num_updates = _num_updates(config)
    save_every = _save_every(config, num_updates)

    if env is None:
        if config.reseed_mode == "per_preference" or execution_mode == "parallel":
            set_seed(pref_seed)
        env = _build_env(config, pref_env_seed)
    else:
        env.seed = pref_env_seed
        if config.reseed_mode == "per_preference":
            set_seed(pref_seed)

    actor_critic = ActorCritic(
        obs_dim=env.obs_dim,
        action_dim=env.action_dim,
        obj_dim=env.obj_dim,
        hidden_sizes=(config.model.hidden_size, config.model.hidden_size),
    ).to(device)
    trainer = VectorPPO(actor_critic, PPOConfig())
    storage = VectorRolloutStorage(
        num_steps=config.rollout.num_steps,
        num_envs=config.env.num_envs,
        obs_dim=env.obs_dim,
        obj_dim=env.obj_dim,
        action_dim=env.action_dim,
        device=device,
    )

    preference_saves: list[dict] = []
    records: list[dict] = []

    for update_idx in range(num_updates):
        rollout_return, next_value = collect_rollout(env, actor_critic, storage, device)
        storage.compute_returns(next_value, trainer.config.gamma, trainer.config.gae_lambda)
        trainer_stats = trainer.update(storage, preference)

        if update_idx == num_updates - 1 or update_idx % save_every == 0:
            objective_vector = evaluate_policy(env, actor_critic, device, episodes=config.eval.eval_episodes)
            scalarized_utility = float(np.dot(np.asarray(preference), objective_vector))
            checkpoint_path = _checkpoint_path(run_dir, pref_idx, update_idx)
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
                    "preference_seed": pref_seed,
                    "env_seed": pref_env_seed,
                    "protocol_name": config.stage1_protocol_name,
                    "execution_mode": execution_mode,
                },
            )
            preference_saves.append(
                {
                    "policy_id": record["policy_id"],
                    "update_index": update_idx,
                    "objective_vector": objective_vector.tolist(),
                    "scalarized_utility": scalarized_utility,
                }
            )
            records.append(record)

    final_entry = preference_saves[-1] if preference_saves else None
    best_entry = max(preference_saves, key=lambda entry: entry["scalarized_utility"]) if preference_saves else None
    preference_summary = {
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
        "preference_seed": pref_seed,
        "env_seed": pref_env_seed,
        "protocol_name": config.stage1_protocol_name,
        "execution_mode": execution_mode,
    }
    return {
        "preference_index": pref_idx,
        "records": records,
        "preference_summary": preference_summary,
    }


def _preference_worker(task: dict) -> dict:
    config = task["config"]
    return train_single_preference(
        pref_idx=task["pref_idx"],
        preference=task["preference"],
        config=config,
        device=torch.device("cpu"),
        pref_seed=task["pref_seed"],
        pref_env_seed=task["pref_env_seed"],
        run_dir=Path(task["run_dir"]),
        execution_mode="parallel",
        env=None,
    )


def _merge_stage1_outputs(results: list[dict]) -> tuple[list[dict], list[dict]]:
    sorted_results = sorted(results, key=lambda item: int(item["preference_index"]))
    records = [
        record
        for result in sorted_results
        for record in sorted(result["records"], key=lambda entry: int(entry["update_index"]))
    ]
    stage1_summary = [result["preference_summary"] for result in sorted_results]
    pareto_running: list[dict] = []
    merged_records: list[dict] = []
    for record in records:
        pareto_after_save = nondominated_filter(pareto_running + [record])
        record = dict(record)
        notes = dict(record.get("notes", {}))
        notes.update(
            {
                "pareto_size_after_save": len(pareto_after_save),
                "is_nondominated_after_save": any(
                    entry["policy_id"] == record["policy_id"] for entry in pareto_after_save
                ),
            }
        )
        record["notes"] = notes
        merged_records.append(record)
        pareto_running.append(record)
    return merged_records, stage1_summary


def train_stage1(config: Stage1Config) -> Path:
    _validate_stage1_config(config)
    output_dir = ensure_dir(Path(config.output_dir))
    run_dir = ensure_dir(output_dir / f"run_{uuid.uuid4().hex[:8]}")
    device = torch.device("cpu")

    set_seed(config.seed)

    template_env = _build_env(config, int(config.env.seed))
    if config.explicit_preferences:
        preferences = [list(map(float, preference)) for preference in config.explicit_preferences]
        if any(len(preference) != template_env.obj_dim for preference in preferences):
            raise ValueError(f"All explicit_preferences must have length {template_env.obj_dim}")
    else:
        preferences = sample_preferences(
            num_policies=config.num_policies,
            dimensions=template_env.obj_dim,
            strategy=config.preference_strategy,
            seed=config.seed,
            step=config.preference_step,
            dirichlet_alpha=config.preference_dirichlet_alpha,
        )

    num_policies = len(preferences)
    tasks = [
        {
            "pref_idx": pref_idx,
            "preference": list(map(float, preference)),
            "config": config,
            "pref_seed": _resolve_preference_seed(config, pref_idx),
            "pref_env_seed": _resolve_env_seed(config, pref_idx),
            "run_dir": str(run_dir),
        }
        for pref_idx, preference in enumerate(preferences)
    ]

    results: list[dict] = []
    if config.parallel_workers == 1:
        shared_env = None
        if not config.independent_env_per_preference:
            shared_env = _build_env(config, int(config.env.seed))
        for task in tasks:
            results.append(
                train_single_preference(
                    pref_idx=task["pref_idx"],
                    preference=task["preference"],
                    config=config,
                    device=device,
                    pref_seed=task["pref_seed"],
                    pref_env_seed=task["pref_env_seed"],
                    run_dir=run_dir,
                    execution_mode="serial",
                    env=shared_env,
                )
            )
    else:
        ctx = mp.get_context("spawn")
        with ProcessPoolExecutor(
            max_workers=config.parallel_workers,
            mp_context=ctx,
        ) as executor:
            results = list(executor.map(_preference_worker, tasks))

    records, stage1_summary = _merge_stage1_outputs(results)
    pareto_front = nondominated_filter(records)
    num_updates = _num_updates(config)

    buffer_path = run_dir / "solution_buffer.json"
    save_policy_buffer(
        buffer_path,
        metadata=buffer_metadata(
            stage="stage1",
            env_config=config.env,
            model_config=config.model,
            rollout_config=config.rollout,
            optimizer_config=PPOConfig(),
            eval_config=config.eval,
            extra={
                "shield": vars(config.shield),
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
                "stage1_protocol_name": config.stage1_protocol_name,
                "reseed_mode": config.reseed_mode,
                "independent_env_per_preference": config.independent_env_per_preference,
                "preference_seed_stride": config.preference_seed_stride,
                "env_seed_stride": config.env_seed_stride,
                "parallel_workers": config.parallel_workers,
                "parallel_backend": config.parallel_backend,
                "merge_order": config.merge_order,
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
