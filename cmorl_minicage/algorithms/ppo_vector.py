from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn.functional as F

from cmorl_minicage.storage.rollout_storage import VectorRolloutStorage


@dataclass
class PPOConfig:
    clip_param: float = 0.2
    ppo_epochs: int = 4
    num_mini_batch: int = 4
    value_loss_coef: float = 0.5
    entropy_coef: float = 0.01
    learning_rate: float = 3e-4
    max_grad_norm: float = 0.5
    gamma: float = 0.995
    gae_lambda: float = 0.95


class VectorPPO:
    def __init__(self, actor_critic, config: PPOConfig) -> None:
        self.actor_critic = actor_critic
        self.config = config
        self.optimizer = torch.optim.Adam(
            self.actor_critic.parameters(), lr=config.learning_rate
        )

    def update(self, storage: VectorRolloutStorage, preference) -> dict[str, float]:
        preference_tensor = torch.as_tensor(
            preference, device=storage.device, dtype=torch.float32
        )
        advantages_vec = storage.advantages()
        scalar_advantages = torch.matmul(advantages_vec, preference_tensor)
        scalar_advantages = (scalar_advantages - scalar_advantages.mean()) / (
            scalar_advantages.std() + 1e-8
        )

        value_loss_epoch = 0.0
        action_loss_epoch = 0.0
        entropy_epoch = 0.0
        updates = 0

        for _ in range(self.config.ppo_epochs):
            for batch in storage.feed_forward_generator(self.config.num_mini_batch):
                batch_scalar_advantages = torch.matmul(batch.advantages, preference_tensor)
                batch_scalar_advantages = (
                    batch_scalar_advantages - scalar_advantages.mean()
                ) / (scalar_advantages.std() + 1e-8)

                values, log_probs, entropy = self.actor_critic.evaluate_actions(
                    batch.obs, batch.actions
                )
                ratio = torch.exp(log_probs - batch.old_log_probs)
                surr1 = ratio * batch_scalar_advantages
                surr2 = torch.clamp(
                    ratio,
                    1.0 - self.config.clip_param,
                    1.0 + self.config.clip_param,
                ) * batch_scalar_advantages
                action_loss = -torch.min(surr1, surr2).mean()
                value_loss = F.mse_loss(values, batch.returns)
                entropy_bonus = entropy.mean()

                self.optimizer.zero_grad()
                total_loss = (
                    action_loss
                    + self.config.value_loss_coef * value_loss
                    - self.config.entropy_coef * entropy_bonus
                )
                total_loss.backward()
                torch.nn.utils.clip_grad_norm_(
                    self.actor_critic.parameters(), self.config.max_grad_norm
                )
                self.optimizer.step()

                value_loss_epoch += float(value_loss.item())
                action_loss_epoch += float(action_loss.item())
                entropy_epoch += float(entropy_bonus.item())
                updates += 1

        if updates == 0:
            updates = 1
        return {
            "value_loss": value_loss_epoch / updates,
            "action_loss": action_loss_epoch / updates,
            "entropy": entropy_epoch / updates,
        }
