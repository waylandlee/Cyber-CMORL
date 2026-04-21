from __future__ import annotations

from dataclasses import dataclass

import torch


@dataclass
class RolloutBatch:
    obs: torch.Tensor
    actions: torch.Tensor
    action_masks: torch.Tensor
    old_log_probs: torch.Tensor
    returns: torch.Tensor
    value_preds: torch.Tensor
    advantages: torch.Tensor
    masks: torch.Tensor


class VectorRolloutStorage:
    def __init__(
        self,
        num_steps: int,
        num_envs: int,
        obs_dim: int,
        obj_dim: int,
        action_dim: int,
        device: torch.device,
    ) -> None:
        self.num_steps = num_steps
        self.num_envs = num_envs
        self.obs_dim = obs_dim
        self.obj_dim = obj_dim
        self.action_dim = action_dim
        self.device = device
        self.reset()

    def reset(self) -> None:
        self.step = 0
        self.obs = torch.zeros(
            self.num_steps + 1, self.num_envs, self.obs_dim, device=self.device
        )
        self.actions = torch.zeros(
            self.num_steps, self.num_envs, dtype=torch.long, device=self.device
        )
        self.action_masks = torch.ones(
            self.num_steps,
            self.num_envs,
            self.action_dim,
            dtype=torch.bool,
            device=self.device,
        )
        self.log_probs = torch.zeros(
            self.num_steps, self.num_envs, device=self.device
        )
        self.rewards = torch.zeros(
            self.num_steps, self.num_envs, self.obj_dim, device=self.device
        )
        self.value_preds = torch.zeros(
            self.num_steps + 1, self.num_envs, self.obj_dim, device=self.device
        )
        self.returns = torch.zeros(
            self.num_steps + 1, self.num_envs, self.obj_dim, device=self.device
        )
        self.masks = torch.ones(self.num_steps + 1, self.num_envs, device=self.device)

    def insert(
        self,
        obs: torch.Tensor,
        actions: torch.Tensor,
        action_masks: torch.Tensor,
        log_probs: torch.Tensor,
        values: torch.Tensor,
        rewards: torch.Tensor,
        masks: torch.Tensor,
    ) -> None:
        self.obs[self.step + 1].copy_(obs)
        self.actions[self.step].copy_(actions)
        self.action_masks[self.step].copy_(action_masks)
        self.log_probs[self.step].copy_(log_probs)
        self.value_preds[self.step].copy_(values)
        self.rewards[self.step].copy_(rewards)
        self.masks[self.step + 1].copy_(masks)
        self.step = (self.step + 1) % self.num_steps

    def compute_returns(
        self, next_value: torch.Tensor, gamma: float, gae_lambda: float
    ) -> None:
        self.value_preds[-1].copy_(next_value)
        gae = torch.zeros(self.num_envs, self.obj_dim, device=self.device)
        for step in reversed(range(self.num_steps)):
            delta = (
                self.rewards[step]
                + gamma * self.value_preds[step + 1] * self.masks[step + 1].unsqueeze(-1)
                - self.value_preds[step]
            )
            gae = (
                delta
                + gamma
                * gae_lambda
                * self.masks[step + 1].unsqueeze(-1)
                * gae
            )
            self.returns[step] = gae + self.value_preds[step]
        self.returns[-1].copy_(next_value)

    def advantages(self) -> torch.Tensor:
        return self.returns[:-1] - self.value_preds[:-1]

    def feed_forward_generator(
        self, num_mini_batch: int
    ) -> list[RolloutBatch]:
        batch_size = self.num_steps * self.num_envs
        mini_batch_size = batch_size // num_mini_batch
        if mini_batch_size == 0:
            raise ValueError("num_mini_batch is too large for collected rollouts")

        obs = self.obs[:-1].reshape(batch_size, self.obs_dim)
        actions = self.actions.reshape(batch_size)
        action_masks = self.action_masks.reshape(batch_size, self.action_dim)
        old_log_probs = self.log_probs.reshape(batch_size)
        returns = self.returns[:-1].reshape(batch_size, self.obj_dim)
        value_preds = self.value_preds[:-1].reshape(batch_size, self.obj_dim)
        advantages = self.advantages().reshape(batch_size, self.obj_dim)
        masks = self.masks[1:].reshape(batch_size)

        sampler = torch.randperm(batch_size, device=self.device)
        batches: list[RolloutBatch] = []
        for start in range(0, batch_size, mini_batch_size):
            indices = sampler[start : start + mini_batch_size]
            if len(indices) == 0:
                continue
            batches.append(
                RolloutBatch(
                    obs=obs[indices],
                    actions=actions[indices],
                    action_masks=action_masks[indices],
                    old_log_probs=old_log_probs[indices],
                    returns=returns[indices],
                    value_preds=value_preds[indices],
                    advantages=advantages[indices],
                    masks=masks[indices],
                )
            )
        return batches
