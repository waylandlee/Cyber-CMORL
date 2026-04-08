from __future__ import annotations

import inspect
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from .compat import ensure_cyborg_on_path
from .reward import RewardTerms, project_reward_terms
from .scenario_profiles import load_scenario_profile
from .semantics import action_name, semantic_step_info, snapshot_from_true_state

ensure_cyborg_on_path()

from CybORG import CybORG  # type: ignore  # noqa: E402
from CybORG.Agents import B_lineAgent, RedMeanderAgent, SleepAgent  # type: ignore  # noqa: E402
from CybORG.Agents.Wrappers import ChallengeWrapper  # type: ignore  # noqa: E402


RED_POLICY_BUILDERS = {
    "bline": B_lineAgent,
    "meander": RedMeanderAgent,
    "sleep": SleepAgent,
}


def resolve_scenario_path(scenario_name: str) -> Path:
    cyborg_root = Path(inspect.getfile(CybORG)).resolve().parent
    return cyborg_root / "Shared" / "Scenarios" / f"{scenario_name}.yaml"


def make_red_agent(name: str):
    key = name.lower()
    if key not in RED_POLICY_BUILDERS:
        raise ValueError(f"Unsupported red_policy for CybORG migration: {name}")
    return RED_POLICY_BUILDERS[key]


@dataclass
class _VectorMaskShim:
    action_dim: int
    num_envs: int
    state: Any = None
    current_decoys: Any = None

    def get_mask(self, state: Any, current_decoys: Any) -> dict[str, np.ndarray]:
        return {"Blue": np.ones((self.num_envs, self.action_dim), dtype=np.float32)}


class _SingleCybORGEnv:
    def __init__(
        self,
        *,
        scenario_name: str,
        scenario_profile: str | None,
        red_policy: str,
        blue_agent_name: str,
        max_steps: int,
        seed: int | None,
    ) -> None:
        scenario_path = resolve_scenario_path(scenario_name)
        red_agent_cls = make_red_agent(red_policy)
        self.base_env = CybORG(str(scenario_path), "sim", agents={"Red": red_agent_cls})
        self.wrapper = ChallengeWrapper(
            env=self.base_env,
            agent_name=blue_agent_name,
            max_steps=max_steps,
        )
        self.scenario_name = scenario_name
        self.scenario_profile = scenario_profile or ""
        self.profile = load_scenario_profile(scenario_name, self.scenario_profile)
        self.seed = seed
        self.blue_agent_name = blue_agent_name
        self.obs_dim = int(self.wrapper.observation_space.shape[0])
        self.action_dim = int(self.wrapper.action_space.n)
        self.true_state_info = self.base_env.environment_controller.INFO_DICT["True"]
        self.last_obs = np.zeros(self.obs_dim, dtype=np.float32)
        self.last_raw_info: dict[str, Any] = {}
        self.last_true_state: dict[str, Any] = {}
        self.last_snapshot = snapshot_from_true_state(
            {},
            self.scenario_name,
            self.scenario_profile,
        )
        self.done = False

    def _possible_action(self, action_idx: int) -> Any:
        try:
            return self.wrapper.env.get_attr("possible_actions")[int(action_idx)]
        except Exception:
            return None

    def action_catalog(self) -> list[dict[str, Any]]:
        actions = self.wrapper.env.get_attr("possible_actions")
        catalog: list[dict[str, Any]] = []
        for idx, action in enumerate(actions):
            params = action.get_params() if hasattr(action, "get_params") else {}
            catalog.append(
                {
                    "index": idx,
                    "name": action.__class__.__name__,
                    "params": dict(params),
                }
            )
        return catalog

    def reset(self, seed: int | None = None) -> tuple[np.ndarray, dict[str, Any]]:
        self.done = False
        active_seed = self.seed if seed is None else seed
        self.seed = active_seed
        obs, info = self.wrapper.reset(seed=active_seed)
        self.last_obs = np.asarray(obs, dtype=np.float32)
        self.last_raw_info = dict(info)
        self.last_true_state = self.base_env.get_true_state(self.true_state_info)
        self.last_snapshot = snapshot_from_true_state(
            self.last_true_state,
            self.scenario_name,
            self.scenario_profile,
        )
        return self.last_obs.copy(), {
            **dict(info),
            "reward_terms": {
                "security": 0.0,
                "business": 0.0,
                "cost": 0.0,
                "morl_scalar_reward": 0.0,
                "cyborg_scalar_reward": 0.0,
            },
            "semantic_info": semantic_step_info(
                self.last_snapshot,
                self.last_snapshot,
                None,
                self.scenario_name,
                self.scenario_profile,
            ),
            "scenario_profile": self.profile.profile_name,
        }

    def step(
        self, action_idx: int
    ) -> tuple[np.ndarray, np.ndarray, bool, bool, dict[str, Any]]:
        if self.done:
            zero_terms = RewardTerms(0.0, 0.0, 0.0)
            return (
                self.last_obs.copy(),
                zero_terms.as_array(),
                True,
                False,
                {
                    **self.last_raw_info,
                    "reward_terms": {
                        "security": 0.0,
                        "business": 0.0,
                        "cost": 0.0,
                        "morl_scalar_reward": 0.0,
                        "cyborg_scalar_reward": 0.0,
                    },
                    "semantic_info": semantic_step_info(
                        self.last_snapshot,
                        self.last_snapshot,
                        None,
                        self.scenario_name,
                        self.scenario_profile,
                    ),
                    "scenario_profile": self.profile.profile_name,
                },
            )

        blue_action = self._possible_action(int(action_idx))
        obs, raw_reward, terminated, truncated, info = self.wrapper.step(int(action_idx))
        current_true_state = self.base_env.get_true_state(self.true_state_info)
        current_snapshot = snapshot_from_true_state(
            current_true_state,
            self.scenario_name,
            self.scenario_profile,
        )
        reward_terms = project_reward_terms(
            previous=self.last_snapshot,
            current=current_snapshot,
            raw_reward=float(raw_reward),
            blue_action=blue_action,
            scenario_name=self.scenario_name,
            scenario_profile=self.scenario_profile,
        )
        semantic_info = semantic_step_info(
            self.last_snapshot,
            current_snapshot,
            blue_action,
            self.scenario_name,
            self.scenario_profile,
        )
        self.last_snapshot = current_snapshot
        self.last_true_state = current_true_state
        self.last_obs = np.asarray(obs, dtype=np.float32)
        self.last_raw_info = dict(info)
        self.done = bool(terminated or truncated)
        decorated = {
            **dict(info),
            "reward_terms": {
                "security": float(reward_terms.security),
                "business": float(reward_terms.business),
                "cost": float(reward_terms.cost),
                "morl_scalar_reward": float(np.sum(reward_terms.as_array())),
                "cyborg_scalar_reward": float(raw_reward),
            },
            "semantic_info": semantic_info,
            "blue_action": action_name(blue_action),
            "red_action": str(self.wrapper.get_last_action("Red")),
            "true_state_compromised_hosts": sorted(current_snapshot.compromised_hosts),
            "scenario_profile": self.profile.profile_name,
        }
        return (
            self.last_obs.copy(),
            reward_terms.as_array(),
            bool(terminated or truncated),
            bool(truncated),
            decorated,
        )


class CybORGMORLEnv:
    """Blue-only MORL wrapper for formal CybORG using the official gym wrapper stack."""

    def __init__(
        self,
        num_envs: int = 1,
        red_policy: str = "bline",
        remove_bugs: bool = True,
        max_steps: int = 100,
        seed: int | None = None,
        scenario_name: str = "Scenario2",
        scenario_profile: str = "",
        gym_wrapper_name: str = "ChallengeWrapper",
        blue_agent_name: str = "Blue",
        red_agent_name: str = "Red",
        obs_mode: str = "vector",
        state_mode: str = "true",
    ) -> None:
        del remove_bugs, gym_wrapper_name, red_agent_name, obs_mode, state_mode
        self.num_envs = int(num_envs)
        self.red_policy_name = red_policy
        self.max_steps = int(max_steps)
        self.seed = seed
        self.scenario_name = scenario_name
        self.scenario_profile = scenario_profile
        self.blue_agent_name = blue_agent_name
        self.obj_dim = 3
        self._envs = [
            _SingleCybORGEnv(
                scenario_name=scenario_name,
                scenario_profile=scenario_profile,
                red_policy=red_policy,
                blue_agent_name=blue_agent_name,
                max_steps=max_steps,
                seed=None if seed is None else int(seed) + (idx * 1000),
            )
            for idx in range(self.num_envs)
        ]
        self.obs_dim = self._envs[0].obs_dim
        self.action_dim = self._envs[0].action_dim
        self.profile = self._envs[0].profile
        self.sim = _VectorMaskShim(action_dim=self.action_dim, num_envs=self.num_envs)

    def _env_seed(self, env_index: int) -> int | None:
        if self.seed is None:
            return None
        return int(self.seed) + env_index * 1000

    def action_catalog(self) -> list[dict[str, Any]]:
        return self._envs[0].action_catalog()

    def find_action_index(
        self,
        action_name: str,
        *,
        hostname: str | None = None,
    ) -> int:
        for entry in self.action_catalog():
            if entry["name"] != action_name:
                continue
            params = entry.get("params", {})
            if hostname is not None and params.get("hostname") != hostname:
                continue
            return int(entry["index"])
        raise ValueError(
            f"Could not find action index for {action_name} hostname={hostname!r}"
        )

    def reset(self) -> tuple[np.ndarray, dict[str, Any]]:
        obs_batch = []
        infos = []
        for idx, env in enumerate(self._envs):
            env_seed = self._env_seed(idx)
            obs, info = env.reset(env_seed)
            obs_batch.append(obs)
            infos.append(info)
        return np.stack(obs_batch, axis=0).astype(np.float32), self._aggregate_infos(infos)

    def step(
        self, blue_action: np.ndarray | list[int] | list[list[int]]
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]:
        action_array = np.asarray(blue_action, dtype=np.int32).reshape(self.num_envs)
        obs_batch = []
        reward_batch = []
        done_batch = []
        trunc_batch = []
        infos = []
        for idx, env in enumerate(self._envs):
            obs, reward_vec, done, truncated, info = env.step(int(action_array[idx]))
            obs_batch.append(obs)
            reward_batch.append(reward_vec)
            done_batch.append(done)
            trunc_batch.append(truncated)
            infos.append(info)
        return (
            np.stack(obs_batch, axis=0).astype(np.float32),
            np.stack(reward_batch, axis=0).astype(np.float32),
            np.asarray(done_batch, dtype=bool),
            np.asarray(trunc_batch, dtype=bool),
            self._aggregate_infos(infos),
        )

    def _aggregate_infos(self, infos: list[dict[str, Any]]) -> dict[str, Any]:
        reward_terms = {
            key: [
                float(info.get("reward_terms", {}).get(key, 0.0))
                for info in infos
            ]
            for key in ("security", "business", "cost", "morl_scalar_reward", "cyborg_scalar_reward")
        }
        semantic_info = {
            key: [
                float(info.get("semantic_info", {}).get(key, 0.0))
                for info in infos
            ]
            for key in (
                "final_compromised_hosts",
                "final_critical_compromised_hosts",
                "critical_impact_count",
                "recovered_hosts",
                "analyse_count",
                "remove_count",
                "restore_count",
                "high_disruption_action_count",
                "total_action_count",
            )
        }
        return {
            "reward_terms": reward_terms,
            "semantic_info": semantic_info,
            "blue_action": [info.get("blue_action", "Sleep") for info in infos],
            "red_action": [info.get("red_action", "Sleep") for info in infos],
            "true_state_compromised_hosts": [
                info.get("true_state_compromised_hosts", []) for info in infos
            ],
            "scenario_profile": self.profile.profile_name,
        }
