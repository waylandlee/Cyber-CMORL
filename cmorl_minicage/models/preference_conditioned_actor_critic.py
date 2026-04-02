from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import nn
from torch.distributions import Categorical


@dataclass
class ConditionedPolicyOutput:
    actions: torch.Tensor
    log_probs: torch.Tensor
    entropy: torch.Tensor
    values: torch.Tensor


class PreferenceConditionedActorCritic(nn.Module):
    def __init__(
        self,
        obs_dim: int,
        preference_dim: int,
        action_dim: int,
        hidden_sizes: tuple[int, int] = (128, 128),
    ) -> None:
        super().__init__()
        layers: list[nn.Module] = []
        input_dim = obs_dim + preference_dim
        for hidden_size in hidden_sizes:
            layers.extend([nn.Linear(input_dim, hidden_size), nn.Tanh()])
            input_dim = hidden_size
        self.backbone = nn.Sequential(*layers)
        self.actor_head = nn.Linear(input_dim, action_dim)
        self.critic_head = nn.Linear(input_dim, 1)

    def _features(self, obs: torch.Tensor, preference: torch.Tensor) -> torch.Tensor:
        return self.backbone(torch.cat([obs, preference], dim=-1))

    def forward(
        self, obs: torch.Tensor, preference: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor]:
        features = self._features(obs, preference)
        logits = self.actor_head(features)
        values = self.critic_head(features).squeeze(-1)
        return logits, values

    def get_value(self, obs: torch.Tensor, preference: torch.Tensor) -> torch.Tensor:
        _, values = self.forward(obs, preference)
        return values

    def act(
        self, obs: torch.Tensor, preference: torch.Tensor
    ) -> ConditionedPolicyOutput:
        logits, values = self.forward(obs, preference)
        dist = Categorical(logits=logits)
        actions = dist.sample()
        return ConditionedPolicyOutput(
            actions=actions,
            log_probs=dist.log_prob(actions),
            entropy=dist.entropy(),
            values=values,
        )

    def evaluate_actions(
        self, obs: torch.Tensor, preference: torch.Tensor, actions: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        logits, values = self.forward(obs, preference)
        dist = Categorical(logits=logits)
        log_probs = dist.log_prob(actions)
        entropy = dist.entropy()
        return values, log_probs, entropy
