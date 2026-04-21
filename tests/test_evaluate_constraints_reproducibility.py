from __future__ import annotations

from pathlib import Path

import numpy as np
import torch

import cmorl_minicage.evaluate_constraints as constraint_eval


class _FakeEnv:
    def __init__(self) -> None:
        self.num_envs = 1
        self.obs_dim = 3
        self.action_dim = 2
        self.obj_dim = 3
        self.seed = None
        self._steps = 0

    def reset(self) -> tuple[np.ndarray, dict]:
        self._steps = 0
        return np.zeros((self.num_envs, self.obs_dim), dtype=np.float32), {}

    def step(self, actions: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, dict]:
        action = int(np.asarray(actions, dtype=np.int64).reshape(-1)[0])
        self._steps += 1
        reward_vec = np.asarray(
            [[1.0, -130.0 + (15.0 * action), -25.0 + (5.0 * action)]],
            dtype=np.float32,
        )
        done = np.asarray([self._steps >= 2], dtype=bool)
        truncated = np.asarray([False], dtype=bool)
        semantic_info = {
            "final_compromised_hosts": [1.0 - (0.5 * action)],
            "final_critical_compromised_hosts": [0.75 - (0.50 * action)],
            "critical_impact_count": [2.0 - action],
            "recovered_hosts": [float(action)],
            "analyse_count": [0.0],
            "remove_count": [float(action)],
            "restore_count": [0.0],
            "high_disruption_action_count": [4.0 * action],
            "total_action_count": [4.0],
        }
        return (
            np.zeros((self.num_envs, self.obs_dim), dtype=np.float32),
            reward_vec,
            done,
            truncated,
            {"semantic_info": semantic_info},
        )


class _FakeActorCritic:
    def __init__(self, obs_dim: int, action_dim: int, obj_dim: int, hidden_sizes: tuple[int, int]) -> None:
        self.action_dim = action_dim

    def to(self, device: torch.device) -> "_FakeActorCritic":
        return self

    def load_state_dict(self, state_dict: dict) -> None:
        return None

    def eval(self) -> None:
        return None

    def act(self, obs: torch.Tensor):
        logits = torch.zeros((obs.shape[0], self.action_dim), dtype=torch.float32)
        dist = torch.distributions.Categorical(logits=logits)
        actions = dist.sample()
        return type("PolicyOutput", (), {"actions": actions})()


def test_evaluate_actor_critic_record_detailed_is_reproducible(monkeypatch, tmp_path: Path) -> None:
    checkpoint_path = tmp_path / "fake.pt"
    checkpoint_path.write_bytes(b"placeholder")

    monkeypatch.setattr(
        constraint_eval,
        "_build_env_from_metadata",
        lambda metadata: _FakeEnv(),
    )
    monkeypatch.setattr(constraint_eval, "ActorCritic", _FakeActorCritic)
    monkeypatch.setattr(constraint_eval.torch, "load", lambda *args, **kwargs: {})

    metadata = {
        "env": {
            "num_envs": 1,
            "seed": 7,
            "max_episode_steps": 2,
        },
        "model": {
            "obj_dim": 3,
            "hidden_size": 8,
        },
    }
    thresholds = {"d_business": -125.0, "d_cost": -22.0}

    first = constraint_eval._evaluate_actor_critic_record_detailed(
        checkpoint_path,
        metadata,
        thresholds,
        eval_episodes=5,
    )
    second = constraint_eval._evaluate_actor_critic_record_detailed(
        checkpoint_path,
        metadata,
        thresholds,
        eval_episodes=5,
    )

    assert first["mean_violation"] == second["mean_violation"]
    assert first["high_disruption_action_rate"] == second["high_disruption_action_rate"]
    assert first["business_return"] == second["business_return"]
    assert first["cost_return"] == second["cost_return"]
    assert first["final_critical_compromised_hosts"] == second["final_critical_compromised_hosts"]
