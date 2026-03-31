from __future__ import annotations

import copy
import os
from dataclasses import dataclass
from typing import Any

import numpy as np

from mini_CAGE import B_line_minimal, Meander_minimal, SimplifiedCAGE
from mini_CAGE.minimal import EXPLOITS


def _env_float(name: str, default: float) -> float:
    value = os.environ.get(name)
    if value is None:
        return default
    return float(value)

SECURITY_DWELL_PENALTY = 2.0
SECURITY_FINAL_COMPROMISED_PENALTY = 1.0
SECURITY_FINAL_CRITICAL_COMPROMISED_PENALTY = 4.0
SECURITY_NEW_CRITICAL_IMPACT_PENALTY = 10.0
SECURITY_RECOVERY_BONUS = 0.5
SECURITY_NOOP_COMPROMISE_PENALTY = _env_float("CMORL_SECURITY_NOOP_COMPROMISE_PENALTY", 3.5)
SECURITY_NOOP_CRITICAL_COMPROMISE_PENALTY = _env_float(
    "CMORL_SECURITY_NOOP_CRITICAL_COMPROMISE_PENALTY", 2.5
)
BUSINESS_DISTURBANCE_WEIGHTS = np.asarray([0.0, 0.05, 0.15, 0.40, 0.80], dtype=np.float32)
OPERATION_COST_WEIGHTS = np.asarray([0.0, 0.02, 0.10, 0.20, 0.50], dtype=np.float32)
PRIORITY_DISTURBANCE_MULTIPLIERS = np.asarray([0.0, 1.0, 1.5, 2.0], dtype=np.float32)
BUSINESS_ATTEMPT_BASE = 0.5
BUSINESS_SUCCESS_BONUS = 0.5
NOOP_BUSINESS_COMPROMISE_PENALTY = _env_float("CMORL_NOOP_BUSINESS_COMPROMISE_PENALTY", 0.30)
NOOP_BUSINESS_CRITICAL_COMPROMISE_PENALTY = _env_float(
    "CMORL_NOOP_BUSINESS_CRITICAL_COMPROMISE_PENALTY", 0.90
)
NOOP_OPERATION_BASE_COST = _env_float("CMORL_NOOP_OPERATION_BASE_COST", 0.05)
NOOP_OPERATION_COMPROMISE_COST = _env_float("CMORL_NOOP_OPERATION_COMPROMISE_COST", 0.10)
NOOP_OPERATION_CRITICAL_COMPROMISE_COST = _env_float(
    "CMORL_NOOP_OPERATION_CRITICAL_COMPROMISE_COST", 0.25
)


@dataclass
class RewardTerms:
    security: np.ndarray
    business: np.ndarray
    cost: np.ndarray

    def as_array(self) -> np.ndarray:
        return np.stack(
            [
                self.security,
                self.business,
                self.cost,
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
        reward_terms, semantic_info = self._project_reward_terms(red_action, action_array)
        obs_dict, reward_dict, terminated, info = self.sim.step(
            red_action=red_action,
            blue_action=action_array,
            red_agent=self.red_agent,
        )

        self._step_count += 1
        self._red_obs = obs_dict["Red"].copy()
        reward_vec = reward_terms.as_array()
        mini_cage_scalar_reward = reward_dict["Blue"].reshape(self.num_envs).astype(np.float32)
        morl_scalar_reward = reward_vec.sum(axis=-1).astype(np.float32)

        done = np.full((self.num_envs,), bool(self._step_count >= self.max_steps)) | terminated.reshape(-1).astype(bool)
        truncated = np.zeros_like(done, dtype=bool)

        decorated = self._decorate_info(info)
        decorated["reward_terms"] = {
            "security": reward_terms.security.tolist(),
            "business": reward_terms.business.tolist(),
            "cost": reward_terms.cost.tolist(),
            "morl_scalar_reward": morl_scalar_reward.tolist(),
            "mini_cage_scalar_reward": mini_cage_scalar_reward.tolist(),
        }
        decorated["red_action"] = red_action.reshape(-1).astype(int).tolist()
        decorated["blue_action"] = action_array.reshape(-1).astype(int).tolist()
        decorated["blue_success"] = self.sim.blue_success.reshape(-1).astype(float).tolist()
        decorated["red_success"] = self.sim.red_success.reshape(-1).astype(float).tolist()
        decorated["selected_exploit"] = self.sim.selected_exploit.reshape(-1).astype(float).tolist()
        decorated["semantic_info"] = semantic_info

        return obs_dict["Blue"].astype(np.float32), reward_vec, done, truncated, decorated

    def _decorate_info(self, info: dict[str, Any]) -> dict[str, Any]:
        decorated = dict(info)
        decorated["impacted"] = np.asarray(self.sim.impacted).copy()
        decorated["current_processes"] = np.asarray(self.sim.current_processes).copy()
        decorated["current_decoys"] = np.asarray(self.sim.current_decoys).copy()
        return decorated

    def _project_reward_terms(
        self, red_action: np.ndarray, blue_action: np.ndarray
    ) -> tuple[RewardTerms, dict[str, Any]]:
        rng_state = np.random.get_state()
        probe = copy.deepcopy(self.sim)
        previous_impacted = probe.impacted.copy()
        true_state, after_red_state, action_reward = probe._process_actions(
            probe.state,
            red_action,
            blue_action,
            probe.subnets,
        )
        np.random.set_state(rng_state)
        blue_action_flat = blue_action.reshape(-1)
        blue_success = probe.blue_success.reshape(-1).astype(np.float32)
        security = self._security_reward(
            probe,
            blue_action=blue_action_flat,
            after_red_state=after_red_state,
            final_state=true_state,
            previous_impacted=previous_impacted,
        )
        reward_terms = RewardTerms(
            security=security,
            business=self._business_disruption(
                probe,
                blue_action_flat,
                blue_success,
                after_red_state=after_red_state,
            ),
            cost=self._operation_cost(
                blue_action_flat,
                action_reward["Blue"].reshape(probe.num_envs).astype(np.float32),
                after_red_state=after_red_state,
            ),
        )
        semantic_info = self._semantic_step_info(
            probe=probe,
            blue_action=blue_action_flat,
            after_red_state=after_red_state,
            final_state=true_state,
            previous_impacted=previous_impacted,
        )
        return reward_terms, semantic_info

    def _security_reward(
        self,
        sim: SimplifiedCAGE,
        *,
        blue_action: np.ndarray,
        after_red_state: np.ndarray,
        final_state: np.ndarray,
        previous_impacted: np.ndarray,
    ) -> np.ndarray:
        security_after_blue = self._state_security_risk(sim, final_state, sim.impacted)
        after_red_compromised_mask = self._compromised_host_mask(sim, after_red_state)
        after_red_compromised = after_red_compromised_mask.sum(axis=1).astype(np.float32)
        final_compromised = self._compromised_host_mask(sim, final_state)
        final_compromised_count = final_compromised.sum(axis=1).astype(np.float32)
        recovered_hosts = np.logical_and(
            after_red_compromised_mask,
            np.logical_not(final_compromised),
        ).sum(axis=1).astype(np.float32)
        critical_mask = sim.host_priority == 3
        final_critical_compromised = np.logical_and(final_compromised, critical_mask).sum(axis=1).astype(
            np.float32
        )
        new_critical_impacts = np.logical_and(
            np.logical_and(sim.impacted.astype(bool), critical_mask),
            np.logical_not(np.logical_and(previous_impacted.astype(bool), critical_mask)),
        ).sum(axis=1).astype(np.float32)
        security = security_after_blue
        security -= SECURITY_DWELL_PENALTY * after_red_compromised
        security -= SECURITY_FINAL_COMPROMISED_PENALTY * final_compromised_count
        security -= SECURITY_FINAL_CRITICAL_COMPROMISED_PENALTY * final_critical_compromised
        security -= SECURITY_NEW_CRITICAL_IMPACT_PENALTY * new_critical_impacts
        security += SECURITY_RECOVERY_BONUS * recovered_hosts
        action_group, _ = self._action_groups(sim, blue_action)
        no_op_mask = action_group == 0
        if np.any(no_op_mask):
            after_red_critical_compromised = np.logical_and(
                after_red_compromised_mask,
                critical_mask,
            ).sum(axis=1).astype(np.float32)
            security[no_op_mask] -= (
                SECURITY_NOOP_COMPROMISE_PENALTY * after_red_compromised[no_op_mask]
                + SECURITY_NOOP_CRITICAL_COMPROMISE_PENALTY
                * after_red_critical_compromised[no_op_mask]
            )
        return security.astype(np.float32)

    def _compromised_host_mask(
        self,
        sim: SimplifiedCAGE,
        state: np.ndarray,
    ) -> np.ndarray:
        state_info = state.reshape(sim.num_envs, sim.num_nodes, 3).copy()
        state_info[:, 8] = 0

        user_access = state_info[:, :, 1] > 0
        priv_access = state_info[:, :, 2] > 0

        host_exploits = sim.host_exploits.reshape(-1).astype(int)
        exploit_rewards = sim.exploit_rewards.reshape(-1, len(EXPLOITS))
        valid_rewards = np.zeros_like(host_exploits, dtype=np.float32)
        valid_indices = np.nonzero(host_exploits >= 0)[0]
        if len(valid_indices) > 0:
            valid_rewards[valid_indices] = exploit_rewards[
                valid_indices, host_exploits[valid_indices]
            ]
        valid_rewards = valid_rewards.reshape(sim.num_envs, sim.num_nodes)
        rewarded_user_access = np.logical_and(user_access, valid_rewards > 0)
        return np.logical_or(rewarded_user_access, priv_access)

    def _semantic_step_info(
        self,
        *,
        probe: SimplifiedCAGE,
        blue_action: np.ndarray,
        after_red_state: np.ndarray,
        final_state: np.ndarray,
        previous_impacted: np.ndarray,
    ) -> dict[str, Any]:
        action_group, _ = self._action_groups(probe, blue_action)
        final_compromised_mask = self._compromised_host_mask(probe, final_state)
        after_red_compromised_mask = self._compromised_host_mask(probe, after_red_state)
        recovered_mask = np.logical_and(after_red_compromised_mask, np.logical_not(final_compromised_mask))

        host_priority = probe.host_priority.astype(np.int32)
        critical_mask = host_priority == 3
        current_impacted = probe.impacted.astype(bool)
        new_critical_impacts = np.logical_and(
            np.logical_and(current_impacted, critical_mask),
            np.logical_not(np.logical_and(previous_impacted.astype(bool), critical_mask)),
        )

        return {
            "final_compromised_hosts": final_compromised_mask.sum(axis=1).astype(int).tolist(),
            "final_critical_compromised_hosts": np.logical_and(
                final_compromised_mask, critical_mask
            ).sum(axis=1).astype(int).tolist(),
            "critical_impact_count": new_critical_impacts.sum(axis=1).astype(int).tolist(),
            "recovered_hosts": recovered_mask.sum(axis=1).astype(int).tolist(),
            "analyse_count": (action_group == 1).astype(int).tolist(),
            "remove_count": (action_group == 3).astype(int).tolist(),
            "restore_count": (action_group == 4).astype(int).tolist(),
            "high_disruption_action_count": np.isin(action_group, [3, 4]).astype(int).tolist(),
            "total_action_count": np.ones(probe.num_envs, dtype=int).tolist(),
            "blue_action_group": action_group.astype(int).tolist(),
        }

    def _action_groups(
        self,
        sim: SimplifiedCAGE,
        blue_action: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        action = blue_action.reshape(-1).astype(np.int32)
        host_idx = np.where(action > 0, (action - 1) % sim.num_nodes, -1).astype(np.int32)
        action_group = np.where(action > 0, ((action - 1) // sim.num_nodes) + 1, 0).astype(np.int32)
        action_group = np.clip(action_group, 0, len(BUSINESS_DISTURBANCE_WEIGHTS) - 1)
        return action_group, host_idx

    def _business_disruption(
        self,
        sim: SimplifiedCAGE,
        blue_action: np.ndarray,
        blue_success: np.ndarray,
        *,
        after_red_state: np.ndarray,
    ) -> np.ndarray:
        action_group, host_idx = self._action_groups(sim, blue_action)
        disturbance = BUSINESS_DISTURBANCE_WEIGHTS[action_group]
        host_priorities = np.ones(sim.num_envs, dtype=np.int32)
        valid_hosts = host_idx >= 0
        if np.any(valid_hosts):
            host_priorities[valid_hosts] = sim.host_priority[
                np.arange(sim.num_envs)[valid_hosts],
                host_idx[valid_hosts],
            ].astype(np.int32)
        host_priorities = np.clip(host_priorities, 1, len(PRIORITY_DISTURBANCE_MULTIPLIERS) - 1)
        priority_multiplier = PRIORITY_DISTURBANCE_MULTIPLIERS[host_priorities]
        attempt_mask = (blue_action.reshape(-1) > 0).astype(np.float32)
        effect_multiplier = attempt_mask * (
            BUSINESS_ATTEMPT_BASE + BUSINESS_SUCCESS_BONUS * np.clip(blue_success, 0.0, 1.0)
        )
        business = -(disturbance * priority_multiplier * effect_multiplier).astype(np.float32)

        # Opportunity-loss version of business impact:
        # choosing not to intervene while compromise is already present still disrupts business.
        no_op_mask = action_group == 0
        if np.any(no_op_mask):
            after_red_compromised = self._compromised_host_mask(sim, after_red_state)
            after_red_compromised_count = after_red_compromised.sum(axis=1).astype(np.float32)
            after_red_critical_compromised = np.logical_and(
                after_red_compromised,
                sim.host_priority == 3,
            ).sum(axis=1).astype(np.float32)
            business[no_op_mask] = -(
                NOOP_BUSINESS_COMPROMISE_PENALTY * after_red_compromised_count[no_op_mask]
                + NOOP_BUSINESS_CRITICAL_COMPROMISE_PENALTY
                * after_red_critical_compromised[no_op_mask]
            )
        return business.astype(np.float32)

    def _operation_cost(
        self,
        blue_action: np.ndarray,
        mini_cage_action_reward: np.ndarray,
        *,
        after_red_state: np.ndarray,
    ) -> np.ndarray:
        action_group = np.where(
            blue_action.reshape(-1) > 0,
            ((blue_action.reshape(-1) - 1) // self.sim.num_nodes) + 1,
            0,
        ).astype(np.int32)
        action_group = np.clip(action_group, 0, len(OPERATION_COST_WEIGHTS) - 1)
        attempt_cost = -OPERATION_COST_WEIGHTS[action_group]
        # Keep the original MiniCAGE restore penalty visible inside the new cost term.
        restore_floor = np.minimum(mini_cage_action_reward, 0.0)
        cost = np.minimum(attempt_cost, restore_floor).astype(np.float32)

        # No-op is not free under active compromise: there is still triage/monitoring overhead.
        no_op_mask = action_group == 0
        if np.any(no_op_mask):
            after_red_compromised = self._compromised_host_mask(self.sim, after_red_state)
            after_red_compromised_count = after_red_compromised.sum(axis=1).astype(np.float32)
            after_red_critical_compromised = np.logical_and(
                after_red_compromised,
                self.sim.host_priority == 3,
            ).sum(axis=1).astype(np.float32)
            cost[no_op_mask] = -(
                NOOP_OPERATION_BASE_COST
                + NOOP_OPERATION_COMPROMISE_COST * after_red_compromised_count[no_op_mask]
                + NOOP_OPERATION_CRITICAL_COMPROMISE_COST
                * after_red_critical_compromised[no_op_mask]
            )
        return cost.astype(np.float32)

    def _state_security_risk(
        self,
        sim: SimplifiedCAGE,
        state: np.ndarray,
        impacted: np.ndarray,
    ) -> np.ndarray:
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
        security = -0.1 * low_priority.sum(axis=-1).astype(np.float32)

        medium_or_critical = np.logical_and(
            privileged_or_rewarded,
            np.logical_or(flat_host_priority == 2, flat_host_priority == 3),
        )
        medium_or_critical = medium_or_critical.reshape(sim.num_envs, sim.num_nodes)
        security += -1.0 * medium_or_critical.sum(axis=-1).astype(np.float32)
        security += -10.0 * impacted[:, 7].astype(np.float32)
        return security.astype(np.float32)
