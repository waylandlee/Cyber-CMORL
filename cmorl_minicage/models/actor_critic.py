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
    blocked_probability_mass: torch.Tensor | None = None
    allowed_action_count: torch.Tensor | None = None


def masked_logits_and_stats(
    logits: torch.Tensor,
    action_mask: torch.Tensor | None = None,
) -> tuple[torch.Tensor, torch.Tensor | None, torch.Tensor | None]:
    if action_mask is None:
        return logits, None, None

    mask = torch.as_tensor(action_mask, device=logits.device)
    if mask.dtype != torch.bool:
        mask = mask > 0.0
    if mask.ndim == 1:
        mask = mask.unsqueeze(0)
    if mask.shape != logits.shape:
        raise ValueError(
            f"action_mask shape {tuple(mask.shape)} does not match logits {tuple(logits.shape)}"
        )

    safe_mask = mask.clone()
    invalid_rows = ~safe_mask.any(dim=-1)
    if torch.any(invalid_rows):
        safe_mask[invalid_rows] = True

    base_probs = torch.softmax(logits, dim=-1)
    blocked_probability_mass = torch.where(
        safe_mask.all(dim=-1),
        torch.zeros(logits.shape[0], device=logits.device, dtype=logits.dtype),
        (base_probs * (~safe_mask).to(logits.dtype)).sum(dim=-1),
    )
    allowed_action_count = safe_mask.sum(dim=-1).to(logits.dtype)
    masked_logits = logits.masked_fill(~safe_mask, -1e9)
    return masked_logits, blocked_probability_mass, allowed_action_count


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

    def act(
        self,
        obs: torch.Tensor,
        action_mask: torch.Tensor | None = None,
    ) -> PolicyOutput:
        logits, values = self.forward(obs)
        masked_logits, blocked_probability_mass, allowed_action_count = (
            masked_logits_and_stats(logits, action_mask)
        )
        dist = Categorical(logits=masked_logits)
        actions = dist.sample()
        return PolicyOutput(
            actions=actions,
            log_probs=dist.log_prob(actions),
            entropy=dist.entropy(),
            values=values,
            blocked_probability_mass=blocked_probability_mass,
            allowed_action_count=allowed_action_count,
        )

    def evaluate_actions(
        self,
        obs: torch.Tensor,
        actions: torch.Tensor,
        action_mask: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        logits, values = self.forward(obs)
        masked_logits, _, _ = masked_logits_and_stats(logits, action_mask)
        dist = Categorical(logits=masked_logits)
        log_probs = dist.log_prob(actions)
        entropy = dist.entropy()
        return values, log_probs, entropy
