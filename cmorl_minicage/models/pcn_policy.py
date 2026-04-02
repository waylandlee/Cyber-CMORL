from __future__ import annotations

import torch
from torch import nn
from torch.distributions import Categorical


class PCNPolicy(nn.Module):
    def __init__(
        self,
        obs_dim: int,
        command_dim: int,
        action_dim: int,
        hidden_sizes: tuple[int, int] = (128, 128),
    ) -> None:
        super().__init__()
        layers: list[nn.Module] = []
        input_dim = obs_dim + command_dim + 1
        for hidden_size in hidden_sizes:
            layers.extend([nn.Linear(input_dim, hidden_size), nn.ReLU()])
            input_dim = hidden_size
        self.backbone = nn.Sequential(*layers)
        self.actor_head = nn.Linear(input_dim, action_dim)

    def forward(
        self,
        obs: torch.Tensor,
        desired_return: torch.Tensor,
        horizon: torch.Tensor,
    ) -> torch.Tensor:
        if horizon.ndim == 1:
            horizon = horizon.unsqueeze(-1)
        features = self.backbone(torch.cat([obs, desired_return, horizon], dim=-1))
        return self.actor_head(features)

    def act(
        self,
        obs: torch.Tensor,
        desired_return: torch.Tensor,
        horizon: torch.Tensor,
    ) -> torch.Tensor:
        logits = self.forward(obs, desired_return, horizon)
        dist = Categorical(logits=logits)
        return dist.sample()
