from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn.functional as F

from cmorl_minicage.storage.scalar_rollout_storage import ScalarRolloutStorage
from cmorl_minicage.storage.rollout_storage import VectorRolloutStorage


@dataclass
class IPOConfig:
    clip_param: float = 0.2
    ppo_epochs: int = 4
    num_mini_batch: int = 4
    value_loss_coef: float = 0.5
    entropy_coef: float = 0.01
    learning_rate: float = 3e-4
    max_grad_norm: float = 0.5
    barrier_coef: float = 20.0
    beta: float = 0.9
    gamma: float = 0.995
    gae_lambda: float = 0.95
    eps: float = 1e-8


class IPOTrainer:
    def __init__(self, actor_critic, config: IPOConfig) -> None:
        self.actor_critic = actor_critic
        self.config = config
        self.optimizer = torch.optim.Adam(
            self.actor_critic.parameters(), lr=config.learning_rate
        )

    def update(
        self,
        storage: VectorRolloutStorage,
        objective_idx: int,
        reference_objectives,
        beta_override: float | None = None,
        use_barrier: bool = True,
        risk_storage: ScalarRolloutStorage | None = None,
        risk_objective_mode: str = "none",
        risk_penalty_coef: float = 0.0,
    ) -> dict[str, float]:
        reference = torch.as_tensor(
            reference_objectives, device=storage.device, dtype=torch.float32
        )
        beta_value = (
            float(beta_override) if beta_override is not None else float(self.config.beta)
        )
        value_loss_epoch = 0.0
        action_loss_epoch = 0.0
        barrier_epoch = 0.0
        objective_epoch = 0.0
        margin_epoch = 0.0
        feasible_epoch = 0.0
        entropy_epoch = 0.0
        risk_epoch = 0.0
        updates = 0
        batch_size = storage.num_steps * storage.num_envs
        mini_batch_size = batch_size // self.config.num_mini_batch
        if mini_batch_size == 0:
            raise ValueError("num_mini_batch is too large for collected rollouts")

        obs = storage.obs[:-1].reshape(batch_size, storage.obs_dim)
        actions = storage.actions.reshape(batch_size)
        old_log_probs = storage.log_probs.reshape(batch_size)
        returns = storage.returns[:-1].reshape(batch_size, storage.obj_dim)
        value_preds = storage.value_preds[:-1].reshape(batch_size, storage.obj_dim)
        advantages = storage.advantages().reshape(batch_size, storage.obj_dim)

        risk_advantages = None
        if risk_storage is not None and risk_objective_mode != "none":
            risk_advantages = risk_storage.advantages().reshape(batch_size)

        for _ in range(self.config.ppo_epochs):
            sampler = torch.randperm(batch_size, device=storage.device)
            for start in range(0, batch_size, mini_batch_size):
                indices = sampler[start : start + mini_batch_size]
                if len(indices) == 0:
                    continue
                batch_obs = obs[indices]
                batch_actions = actions[indices]
                batch_old_log_probs = old_log_probs[indices]
                batch_returns = returns[indices]
                batch_advantages = advantages[indices]
                values, log_probs, entropy = self.actor_critic.evaluate_actions(
                    batch_obs, batch_actions
                )
                ratio = torch.exp(log_probs - batch_old_log_probs)
                clipped_ratio = torch.clamp(
                    ratio,
                    1.0 - self.config.clip_param,
                    1.0 + self.config.clip_param,
                )

                objective_adv = batch_advantages[:, objective_idx]
                clipped_objective_gain = torch.min(
                    ratio * objective_adv,
                    clipped_ratio * objective_adv,
                )
                objective_surrogate = reference[objective_idx] + clipped_objective_gain.mean()
                action_loss = -clipped_objective_gain.mean()

                risk_action_loss = torch.zeros((), device=storage.device)
                if risk_advantages is not None and risk_objective_mode == "ppo_cost_surrogate":
                    batch_risk_advantages = risk_advantages[indices]
                    neg_risk_advantages = -batch_risk_advantages
                    clipped_risk_gain = torch.min(
                        ratio * neg_risk_advantages,
                        clipped_ratio * neg_risk_advantages,
                    )
                    risk_action_loss = -clipped_risk_gain.mean()

                barrier_terms = []
                margin_values = []
                if use_barrier:
                    for idx in range(batch_advantages.shape[1]):
                        if idx == objective_idx:
                            continue
                        clipped_constraint_gain = torch.min(
                            ratio * batch_advantages[:, idx],
                            clipped_ratio * batch_advantages[:, idx],
                        )
                        surrogate_return = reference[idx] + clipped_constraint_gain.mean()
                        margin = surrogate_return - beta_value * reference[idx]
                        margin_values.append(margin.detach())
                        barrier_terms.append(
                            torch.log(torch.clamp(margin, min=self.config.eps))
                            / self.config.barrier_coef
                        )
                barrier_bonus = (
                    torch.stack(barrier_terms).sum()
                    if barrier_terms
                    else torch.zeros((), device=storage.device)
                )
                if margin_values:
                    margins = torch.stack(margin_values)
                    min_margin = margins.min()
                    feasible_ratio = (margins > 0).float().mean()
                else:
                    min_margin = torch.zeros((), device=storage.device)
                    feasible_ratio = torch.ones((), device=storage.device)

                value_loss = F.mse_loss(values, batch_returns)
                entropy_bonus = entropy.mean()

                self.optimizer.zero_grad()
                total_loss = (
                    action_loss
                    + float(risk_penalty_coef) * risk_action_loss
                    + self.config.value_loss_coef * value_loss
                    - barrier_bonus
                    - self.config.entropy_coef * entropy_bonus
                )
                total_loss.backward()
                torch.nn.utils.clip_grad_norm_(
                    self.actor_critic.parameters(), self.config.max_grad_norm
                )
                self.optimizer.step()

                value_loss_epoch += float(value_loss.item())
                action_loss_epoch += float(action_loss.item())
                barrier_epoch += float(barrier_bonus.item())
                objective_epoch += float(objective_surrogate.item())
                margin_epoch += float(min_margin.item())
                feasible_epoch += float(feasible_ratio.item())
                entropy_epoch += float(entropy_bonus.item())
                risk_epoch += float(risk_action_loss.item())
                updates += 1

        if updates == 0:
            updates = 1
        return {
            "value_loss": value_loss_epoch / updates,
            "action_loss": action_loss_epoch / updates,
            "risk_action_loss": risk_epoch / updates,
            "objective_surrogate": objective_epoch / updates,
            "barrier_bonus": barrier_epoch / updates,
            "min_constraint_margin": margin_epoch / updates,
            "feasible_ratio": feasible_epoch / updates,
            "entropy": entropy_epoch / updates,
            "beta_used": beta_value,
        }
