from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import nn
from torch.distributions import Categorical


@dataclass
class PolicyOutput:
    actions: torch.Tensor
    log_probs: torch.Tensor
    entropy: torch.Tensor
    values: torch.Tensor


class ActorCritic(nn.Module):
    def __init__(
        self,
        obs_dim: int,
        action_dim: int,
        obj_dim: int = 3,
        hidden_sizes: tuple[int, int] = (128, 128),
    ) -> None:
        super().__init__()
        layers: list[nn.Module] = []
        input_dim = obs_dim
        for hidden_size in hidden_sizes:
            layers.extend([nn.Linear(input_dim, hidden_size), nn.Tanh()])
            input_dim = hidden_size
        self.backbone = nn.Sequential(*layers)
        self.actor_head = nn.Linear(input_dim, action_dim)
        self.critic_head = nn.Linear(input_dim, obj_dim)

    def _features(self, obs: torch.Tensor) -> torch.Tensor:
        return self.backbone(obs)

    def forward(self, obs: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        features = self._features(obs)
        logits = self.actor_head(features)
        values = self.critic_head(features)
        return logits, values

    def get_value(self, obs: torch.Tensor) -> torch.Tensor:
        _, values = self.forward(obs)
        return values

    def act(self, obs: torch.Tensor) -> PolicyOutput:
        logits, values = self.forward(obs)
        dist = Categorical(logits=logits)
        actions = dist.sample()
        return PolicyOutput(
            actions=actions,
            log_probs=dist.log_prob(actions),
            entropy=dist.entropy(),
            values=values,
        )

    def evaluate_actions(
        self, obs: torch.Tensor, actions: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        logits, values = self.forward(obs)
        dist = Categorical(logits=logits)
        log_probs = dist.log_prob(actions)
        entropy = dist.entropy()
        return values, log_probs, entropy
