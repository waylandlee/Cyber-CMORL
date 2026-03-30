from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

import numpy as np

from mini_CAGE import B_line_minimal, Meander_minimal, SimplifiedCAGE
from mini_CAGE.minimal import EXPLOITS


@dataclass
class RewardTerms:
    threat_containment: np.ndarray
    business_critical_loss: np.ndarray
    defense_cost: np.ndarray

    def as_array(self) -> np.ndarray:
        return np.stack(
            [
                self.threat_containment,
                self.business_critical_loss,
                self.defense_cost,
            ],
            axis=-1,
        ).astype(np.float32)


def make_red_agent(name: str):
    normalized = name.lower()
    if normalized in {"bline", "b_line", "b_line_minimal"}:
        return B_line_minimal()
    if normalized in {"meander", "meander_minimal"}:
        return Meander_minimal()
    raise ValueError(f"Unknown red policy: {name}")


class MiniCageMORLEnv:
    """Blue-only MORL wrapper for MiniCAGE."""

    def __init__(
        self,
        num_envs: int = 1,
        red_policy: str = "bline",
        remove_bugs: bool = True,
        max_steps: int = 100,
        seed: int | None = None,
    ) -> None:
        self.num_envs = num_envs
        self.red_policy_name = red_policy
        self.max_steps = max_steps
        self.seed = seed

        self.sim = SimplifiedCAGE(num_envs=num_envs, remove_bugs=remove_bugs)
        self.red_agent = make_red_agent(red_policy)
        self.action_map = self.sim.action_mapping["Blue"]
        self.action_dim = len(self.action_map)
        self.obj_dim = 3
        self.obs_dim = 6 * self.sim.num_nodes

        self._red_obs: np.ndarray | None = None
        self._step_count = 0

    def reset(self) -> tuple[np.ndarray, dict[str, Any]]:
        if self.seed is not None:
            np.random.seed(self.seed)
        if hasattr(self.red_agent, "reset"):
            self.red_agent.reset()

        self._step_count = 0
        obs_dict, info = self.sim.reset()
        self._red_obs = obs_dict["Red"].copy()
        return obs_dict["Blue"].astype(np.float32), self._decorate_info(info)

    def step(
        self, blue_action: np.ndarray | list[int] | list[list[int]]
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]:
        action_array = np.asarray(blue_action, dtype=np.int32).reshape(self.num_envs, 1)
        red_action = self.red_agent.get_action(self._red_obs).astype(np.int32)
        reward_terms = self._project_reward_terms(red_action, action_array)
        obs_dict, reward_dict, terminated, info = self.sim.step(
            red_action=red_action,
            blue_action=action_array,
            red_agent=self.red_agent,
        )

        self._step_count += 1
        self._red_obs = obs_dict["Red"].copy()
        reward_vec = reward_terms.as_array()
        scalar_reward = reward_dict["Blue"].reshape(self.num_envs).astype(np.float32)

        if not np.allclose(reward_vec.sum(axis=-1), scalar_reward, atol=1e-6):
            raise RuntimeError("reward decomposition does not match MiniCAGE scalar reward")

        done = np.full((self.num_envs,), bool(self._step_count >= self.max_steps)) | terminated.reshape(-1).astype(bool)
        truncated = np.zeros_like(done, dtype=bool)

        decorated = self._decorate_info(info)
        decorated["reward_terms"] = {
            "threat_containment": reward_terms.threat_containment.tolist(),
            "business_critical_loss": reward_terms.business_critical_loss.tolist(),
            "defense_cost": reward_terms.defense_cost.tolist(),
            "scalar_reward": scalar_reward.tolist(),
        }
        decorated["red_action"] = red_action.reshape(-1).astype(int).tolist()
        decorated["blue_action"] = action_array.reshape(-1).astype(int).tolist()
        decorated["blue_success"] = self.sim.blue_success.reshape(-1).astype(float).tolist()
        decorated["red_success"] = self.sim.red_success.reshape(-1).astype(float).tolist()
        decorated["selected_exploit"] = self.sim.selected_exploit.reshape(-1).astype(float).tolist()

        return obs_dict["Blue"].astype(np.float32), reward_vec, done, truncated, decorated

    def _decorate_info(self, info: dict[str, Any]) -> dict[str, Any]:
        decorated = dict(info)
        decorated["impacted"] = np.asarray(self.sim.impacted).copy()
        decorated["current_processes"] = np.asarray(self.sim.current_processes).copy()
        decorated["current_decoys"] = np.asarray(self.sim.current_decoys).copy()
        return decorated

    def _project_reward_terms(
        self, red_action: np.ndarray, blue_action: np.ndarray
    ) -> RewardTerms:
        rng_state = np.random.get_state()
        probe = copy.deepcopy(self.sim)
        true_state, after_red_state, action_reward = probe._process_actions(
            probe.state,
            red_action,
            blue_action,
            probe.subnets,
        )
        np.random.set_state(rng_state)
        after_terms = self._reward_terms_from_state(probe, after_red_state, probe.impacted)
        final_terms = self._reward_terms_from_state(probe, true_state, probe.impacted)
        return RewardTerms(
            threat_containment=after_terms.threat_containment
            + final_terms.threat_containment,
            business_critical_loss=after_terms.business_critical_loss
            + final_terms.business_critical_loss,
            defense_cost=action_reward["Blue"].reshape(probe.num_envs).astype(np.float32),
        )

    def _reward_terms_from_state(
        self,
        sim: SimplifiedCAGE,
        state: np.ndarray,
        impacted: np.ndarray,
    ) -> RewardTerms:
        state_info = state.reshape(sim.num_envs, sim.num_nodes, 3).copy()
        state_info[:, 8] = 0

        user_access = state_info[:, :, 1].reshape(-1) > 0
        priv_access = state_info[:, :, 2].reshape(-1) > 0

        flat_host_priority = sim.host_priority.reshape(-1)
        host_exploits = sim.host_exploits.reshape(-1).astype(int)
        exploit_rewards = sim.exploit_rewards.reshape(-1, len(EXPLOITS))

        valid_rewards = np.zeros_like(host_exploits, dtype=np.float32)
        valid_indices = np.nonzero(host_exploits >= 0)[0]
        if len(valid_indices) > 0:
            valid_rewards[valid_indices] = exploit_rewards[
                valid_indices, host_exploits[valid_indices]
            ]

        rewarded_user_access = (user_access * valid_rewards).astype(bool)
        privileged_or_rewarded = np.logical_or(rewarded_user_access, priv_access)

        low_priority = np.logical_and(privileged_or_rewarded, flat_host_priority == 1)
        low_priority = low_priority.reshape(sim.num_envs, sim.num_nodes)
        threat_containment = -0.1 * low_priority.sum(axis=-1).astype(np.float32)

        medium_or_critical = np.logical_and(
            privileged_or_rewarded,
            np.logical_or(flat_host_priority == 2, flat_host_priority == 3),
        )
        medium_or_critical = medium_or_critical.reshape(sim.num_envs, sim.num_nodes)
        business_critical_loss = -1.0 * medium_or_critical.sum(axis=-1).astype(np.float32)
        business_critical_loss += -10.0 * impacted[:, 7].astype(np.float32)

        return RewardTerms(
            threat_containment=threat_containment,
            business_critical_loss=business_critical_loss,
            defense_cost=np.zeros(sim.num_envs, dtype=np.float32),
        )
