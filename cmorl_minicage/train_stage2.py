from __future__ import annotations

import argparse
import copy
import uuid
from pathlib import Path

import numpy as np
import torch

from cmorl_minicage.buffer import (
    buffer_metadata,
    load_policy_buffer,
    policy_record,
    save_policy_buffer,
)
from cmorl_minicage.config import (
    DEFAULT_STAGE2_CONFIG,
    load_stage2_config,
)
from cmorl_minicage.algorithms.ipo import IPOConfig, IPOTrainer
from cmorl_minicage.algorithms.selection import crowding_distance, nondominated_filter, select_top_n_by_crowding
from cmorl_minicage.env import MiniCageMORLEnv
from cmorl_minicage.models import ActorCritic
from cmorl_minicage.storage import VectorRolloutStorage
from cmorl_minicage.train_stage1 import collect_rollout, evaluate_policy
from cmorl_minicage.utils import ensure_dir, save_json, set_seed


def train_stage2(config: Stage2Config) -> Path:
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
    num_updates = max(
        config.total_timesteps_per_update
        // (config.rollout.num_steps * config.env.num_envs),
        1,
    )

    for round_idx in range(config.extension_rounds):
        current_pareto = nondominated_filter(records)
        current_crowding = crowding_distance(current_pareto)
        extension_records = select_top_n_by_crowding(records, config.num_extension_policies)
        round_summary = {
            "round_index": round_idx,
            "num_records_before_round": len(records),
            "pareto_size_before_round": len(current_pareto),
            "selected_policy_ids": [record["policy_id"] for record in extension_records],
            "selected_policy_crowding": {
                record["policy_id"]: float(current_crowding[index])
                for index, record in enumerate(current_pareto)
                if record["policy_id"] in {entry["policy_id"] for entry in extension_records}
            },
            "extension_results": [],
        }
        for base_record in extension_records:
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
                last_constraint_margins = None
                last_trainer_stats: dict[str, float] = {}

                for _ in range(config.constrained_updates):
                    for _ in range(num_updates):
                        _, next_value = collect_rollout(env, actor_critic, storage, device)
                        storage.compute_returns(
                            next_value, ipo_config.gamma, ipo_config.gae_lambda
                        )
                        last_trainer_stats = trainer.update(
                            storage, objective_idx, current_reference
                        )
                    candidate_objectives = evaluate_policy(
                        env,
                        actor_critic,
                        device,
                        episodes=config.eval.eval_episodes,
                    )
                    candidate_margins = candidate_objectives - (
                        ipo_config.beta * current_reference
                    )
                    constraint_margins = np.delete(candidate_margins, objective_idx)
                    last_constraint_margins = constraint_margins.astype(np.float32)
                    is_feasible = bool(
                        np.all(constraint_margins > config.constraint_tolerance)
                    )
                    if not is_feasible:
                        terminated_due_to_constraints = True
                        break

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
                        "successful_constrained_updates": successful_updates,
                        "terminated_due_to_constraints": terminated_due_to_constraints,
                        "constraint_tolerance": config.constraint_tolerance,
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
                "constraint_tolerance": config.constraint_tolerance,
                "total_timesteps_per_update": config.total_timesteps_per_update,
                "round_summaries": round_summaries,
                "parent_buffer_metadata": payload.get("metadata", {}),
            },
        ),
        records=records,
        pareto_front=pareto_front,
    )
    save_json(run_dir / "pareto_front_stage2.json", pareto_front)
    save_json(run_dir / "stage2_summary.json", round_summaries)
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
