from __future__ import annotations

import inspect
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from cmorl_minicage.shield import (
    SHIELD_MODE_DISABLED,
    action_family_from_name,
    build_shielded_action_mask,
    shield_enabled,
)

from .compat import ensure_cyborg_on_path
from .reward import (
    CRITICAL_HOST_SAFETY_MODE_LEGACY,
    RewardTerms,
    critical_host_safety_step_reward,
    project_reward_terms,
)
from .scenario_profiles import load_scenario_profile
from .semantics import (
    action_name,
    semantic_step_info,
    serialize_action,
    snapshot_from_true_state,
    snapshot_payload,
    snapshot_transition,
)
from .topology import subnet_for_host

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
    owner: Any = None
    state: Any = None
    current_decoys: Any = None

    def get_mask(self, state: Any, current_decoys: Any) -> dict[str, np.ndarray]:
        if self.owner is not None and hasattr(self.owner, "native_action_mask"):
            return {"Blue": self.owner.native_action_mask()}
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
        obj_dim: int,
        critical_host_safety_mode: str,
        shield_mode: str,
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
        self.max_steps = int(max_steps)
        self.obj_dim = int(obj_dim)
        self.critical_host_safety_mode = str(critical_host_safety_mode)
        self.shield_mode = str(shield_mode)
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
        self.step_idx = 0

    def _possible_action(self, action_idx: int) -> Any:
        try:
            return self.wrapper.env.get_attr("possible_actions")[int(action_idx)]
        except Exception:
            return None

    def action_catalog(self) -> list[dict[str, Any]]:
        actions = self.wrapper.env.get_attr("possible_actions")
        catalog: list[dict[str, Any]] = []
        for idx, action in enumerate(actions):
            entry = serialize_action(
                action,
                scenario_name=self.scenario_name,
                scenario_profile=self.scenario_profile,
            )
            entry["index"] = idx
            catalog.append(entry)
        return catalog

    def _subnet_aliases(self, true_state: dict[str, Any]) -> dict[str, str]:
        aliases: dict[str, str] = {}
        for hostname, host_state in true_state.items():
            if hostname == "success" or not isinstance(host_state, dict):
                continue
            logical_subnet = subnet_for_host(
                str(hostname),
                scenario_name=self.scenario_name,
                scenario_profile=self.scenario_profile,
            )
            if logical_subnet is None:
                continue
            interfaces = host_state.get("Interface", [])
            if isinstance(interfaces, dict):
                interfaces = [interfaces]
            for interface in interfaces:
                if not isinstance(interface, dict):
                    continue
                subnet = interface.get("Subnet")
                if subnet is None:
                    continue
                aliases[str(subnet)] = logical_subnet
        return aliases

    def reset(self, seed: int | None = None) -> tuple[np.ndarray, dict[str, Any]]:
        self.done = False
        self.step_idx = 0
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
        subnet_aliases = self._subnet_aliases(self.last_true_state)
        transition = snapshot_transition(self.last_snapshot, self.last_snapshot)
        return self.last_obs.copy(), {
            **dict(info),
            "reward_terms": {
                "security": 0.0,
                "business": 0.0,
                "cost": 0.0,
                "critical_host_safety": 0.0,
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
            "blue_action_index": None,
            "blue_action_struct": serialize_action(
                None,
                scenario_name=self.scenario_name,
                scenario_profile=self.scenario_profile,
                subnet_aliases=subnet_aliases,
            ),
            "red_action_struct": serialize_action(
                None,
                scenario_name=self.scenario_name,
                scenario_profile=self.scenario_profile,
                subnet_aliases=subnet_aliases,
            ),
            "state_before": transition["state_before"],
            "state_after": transition["state_after"],
            "newly_compromised_hosts": transition["newly_compromised_hosts"],
            "recovered_hosts": transition["recovered_hosts"],
            "critical_compromised_hosts": transition["critical_compromised_hosts"],
            "weighted_security_exposure": transition["weighted_security_exposure"],
            "weighted_business_exposure": transition["weighted_business_exposure"],
            "padding_step": False,
            "scenario_profile": self.profile.profile_name,
        }

    def step(
        self, action_idx: int
    ) -> tuple[np.ndarray, np.ndarray, bool, bool, dict[str, Any]]:
        if self.done:
            zero_terms = RewardTerms(
                0.0,
                0.0,
                0.0,
                0.0 if self.obj_dim >= 4 else None,
            )
            subnet_aliases = self._subnet_aliases(self.last_true_state)
            transition = snapshot_transition(self.last_snapshot, self.last_snapshot)
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
                        "critical_host_safety": 0.0,
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
                    "blue_action_index": None,
                    "blue_action_struct": serialize_action(
                        None,
                        scenario_name=self.scenario_name,
                        scenario_profile=self.scenario_profile,
                        subnet_aliases=subnet_aliases,
                    ),
                    "red_action_struct": serialize_action(
                        None,
                        scenario_name=self.scenario_name,
                        scenario_profile=self.scenario_profile,
                        subnet_aliases=subnet_aliases,
                    ),
                    "state_before": transition["state_before"],
                    "state_after": transition["state_after"],
                    "newly_compromised_hosts": transition["newly_compromised_hosts"],
                    "recovered_hosts": transition["recovered_hosts"],
                    "critical_compromised_hosts": transition["critical_compromised_hosts"],
                    "weighted_security_exposure": transition["weighted_security_exposure"],
                    "weighted_business_exposure": transition["weighted_business_exposure"],
                    "padding_step": True,
                    "scenario_profile": self.profile.profile_name,
                },
            )

        previous_snapshot = self.last_snapshot
        step_idx = int(self.step_idx)
        blue_action = self._possible_action(int(action_idx))
        obs, raw_reward, terminated, truncated, info = self.wrapper.step(int(action_idx))
        red_action = self.wrapper.get_last_action("Red")
        current_true_state = self.base_env.get_true_state(self.true_state_info)
        current_snapshot = snapshot_from_true_state(
            current_true_state,
            self.scenario_name,
            self.scenario_profile,
        )
        subnet_aliases = self._subnet_aliases(current_true_state)
        reward_terms = project_reward_terms(
            previous=self.last_snapshot,
            current=current_snapshot,
            raw_reward=float(raw_reward),
            blue_action=blue_action,
            scenario_name=self.scenario_name,
            scenario_profile=self.scenario_profile,
        )
        semantic_info = semantic_step_info(
            previous_snapshot,
            current_snapshot,
            blue_action,
            self.scenario_name,
            self.scenario_profile,
        )
        if self.obj_dim >= 4:
            reward_terms = reward_terms.with_critical_host_safety(
                critical_host_safety_step_reward(
                    critical_hit_event=float(semantic_info.get("critical_hit_event", 0.0)),
                    critical_present=float(semantic_info.get("critical_present", 0.0)),
                    episode_done=bool(terminated or truncated),
                    step_idx=step_idx,
                    max_episode_steps=self.max_steps,
                    mode=self.critical_host_safety_mode,
                )
            )
        transition = snapshot_transition(previous_snapshot, current_snapshot)
        self.last_snapshot = current_snapshot
        self.last_true_state = current_true_state
        self.last_obs = np.asarray(obs, dtype=np.float32)
        self.last_raw_info = dict(info)
        self.done = bool(terminated or truncated)
        self.step_idx = step_idx + 1
        decorated = {
            **dict(info),
            "reward_terms": {
                "security": float(reward_terms.security),
                "business": float(reward_terms.business),
                "cost": float(reward_terms.cost),
                "critical_host_safety": float(
                    reward_terms.critical_host_safety or 0.0
                ),
                "morl_scalar_reward": float(np.sum(reward_terms.as_array())),
                "cyborg_scalar_reward": float(raw_reward),
            },
            "semantic_info": semantic_info,
            "blue_action_index": int(action_idx),
            "blue_action_struct": serialize_action(
                blue_action,
                scenario_name=self.scenario_name,
                scenario_profile=self.scenario_profile,
                subnet_aliases=subnet_aliases,
            ),
            "red_action_struct": serialize_action(
                red_action,
                scenario_name=self.scenario_name,
                scenario_profile=self.scenario_profile,
                subnet_aliases=subnet_aliases,
            ),
            "blue_action": action_name(blue_action),
            "red_action": action_name(red_action),
            "state_before": transition["state_before"],
            "state_after": transition["state_after"],
            "newly_compromised_hosts": transition["newly_compromised_hosts"],
            "recovered_hosts": transition["recovered_hosts"],
            "critical_compromised_hosts": transition["critical_compromised_hosts"],
            "weighted_security_exposure": transition["weighted_security_exposure"],
            "weighted_business_exposure": transition["weighted_business_exposure"],
            "true_state_compromised_hosts": sorted(current_snapshot.compromised_hosts),
            "padding_step": False,
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
        obj_dim: int = 3,
        critical_host_safety_mode: str = CRITICAL_HOST_SAFETY_MODE_LEGACY,
        shield_mode: str = SHIELD_MODE_DISABLED,
    ) -> None:
        del remove_bugs, gym_wrapper_name, red_agent_name, obs_mode, state_mode
        self.num_envs = int(num_envs)
        self.red_policy_name = red_policy
        self.max_steps = int(max_steps)
        self.seed = seed
        self.scenario_name = scenario_name
        self.scenario_profile = scenario_profile
        self.blue_agent_name = blue_agent_name
        self.obj_dim = int(obj_dim)
        self.critical_host_safety_mode = str(critical_host_safety_mode)
        self.shield_mode = str(shield_mode)
        if self.obj_dim not in (3, 4):
            raise ValueError(f"CybORGMORLEnv only supports obj_dim 3 or 4, got {self.obj_dim}")
        self._envs = [
            _SingleCybORGEnv(
                scenario_name=scenario_name,
                scenario_profile=scenario_profile,
                red_policy=red_policy,
                blue_agent_name=blue_agent_name,
                max_steps=max_steps,
                seed=None if seed is None else int(seed) + (idx * 1000),
                obj_dim=self.obj_dim,
                critical_host_safety_mode=self.critical_host_safety_mode,
                shield_mode=self.shield_mode,
            )
            for idx in range(self.num_envs)
        ]
        self.obs_dim = self._envs[0].obs_dim
        self.action_dim = self._envs[0].action_dim
        self.profile = self._envs[0].profile
        self.sim = _VectorMaskShim(
            action_dim=self.action_dim,
            num_envs=self.num_envs,
            owner=self,
        )
        self._shield_action_catalog = self._build_shield_action_catalog()
        self._last_shield_diagnostics = self._default_shield_diagnostics()

    def _env_seed(self, env_index: int) -> int | None:
        if self.seed is None:
            return None
        return int(self.seed) + env_index * 1000

    def action_catalog(self) -> list[dict[str, Any]]:
        return self._envs[0].action_catalog()

    def _default_shield_diagnostics(self) -> dict[str, Any]:
        return {
            "shield_active_flag": np.zeros(self.num_envs, dtype=np.int32).tolist(),
            "shield_level": ["none" for _ in range(self.num_envs)],
            "shield_response_tier": ["none" for _ in range(self.num_envs)],
            "shield_fallback_flag": np.zeros(self.num_envs, dtype=np.int32).tolist(),
            "shield_blocked_probability_mass": np.zeros(
                self.num_envs, dtype=np.float32
            ).tolist(),
            "shield_allowed_action_count": np.full(
                self.num_envs,
                self.action_dim,
                dtype=np.int32,
            ).tolist(),
        }

    def _build_shield_action_catalog(self) -> list[dict[str, Any]]:
        catalog: list[dict[str, Any]] = []
        for entry in self.action_catalog():
            target_hostname = entry.get("target_hostname")
            target_subnet = entry.get("target_subnet")
            target_hostname_key = (
                None if target_hostname is None else str(target_hostname).lower()
            )
            target_subnet_key = (
                None if target_subnet is None else str(target_subnet).lower()
            )
            name = str(entry.get("name", ""))
            is_non_sleep = name != "Sleep"
            catalog.append(
                {
                    **dict(entry),
                    "_shield_action_family": action_family_from_name(name),
                    "_shield_is_critical_path_target": target_hostname_key
                    in {"enterprise0", "enterprise1", "enterprise2", "op_server0"},
                    "_shield_is_non_user_non_sleep": bool(
                        is_non_sleep and target_subnet_key != "user"
                    ),
                    "_shield_is_enterprise_operational_non_sleep": bool(
                        is_non_sleep
                        and target_subnet_key in {"enterprise", "operational"}
                    ),
                }
            )
        return catalog

    def native_action_mask(self) -> np.ndarray:
        return np.ones((self.num_envs, self.action_dim), dtype=np.float32)

    def _current_target_mask(self, targets_by_env: list[set[str]]) -> np.ndarray:
        mask = np.zeros((self.num_envs, self.action_dim), dtype=bool)
        for env_idx, targets in enumerate(targets_by_env):
            normalized_targets = {str(target).lower() for target in targets}
            if not normalized_targets:
                continue
            for action_idx, entry in enumerate(self._shield_action_catalog):
                target_hostname = entry.get("target_hostname")
                if target_hostname is None:
                    continue
                if str(target_hostname).lower() in normalized_targets:
                    mask[env_idx, action_idx] = True
        return mask

    def _current_shield_state(
        self,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        critical_present = np.asarray(
            [
                bool(env.last_snapshot.critical_compromised_hosts)
                for env in self._envs
            ],
            dtype=bool,
        )
        enterprise_foothold_present = np.asarray(
            [
                bool(env.last_snapshot.enterprise_compromised_hosts)
                for env in self._envs
            ],
            dtype=bool,
        )
        critical_compromised_target_mask = self._current_target_mask(
            [
                set(env.last_snapshot.critical_compromised_hosts)
                for env in self._envs
            ]
        )
        enterprise_operational_compromised_target_mask = self._current_target_mask(
            [
                set(env.last_snapshot.enterprise_compromised_hosts)
                | set(env.last_snapshot.operational_compromised_hosts)
                | set(env.last_snapshot.critical_compromised_hosts)
                for env in self._envs
            ]
        )
        return (
            critical_present,
            enterprise_foothold_present,
            critical_compromised_target_mask,
            enterprise_operational_compromised_target_mask,
        )

    def current_action_mask(self) -> np.ndarray:
        native_mask = self.native_action_mask()
        if not shield_enabled(self.shield_mode):
            diagnostics = self._default_shield_diagnostics()
            diagnostics["shield_allowed_action_count"] = (
                (native_mask > 0.0).sum(axis=1).astype(np.int32).tolist()
            )
            self._last_shield_diagnostics = diagnostics
            return native_mask

        (
            critical_present,
            enterprise_foothold_present,
            critical_compromised_target_mask,
            enterprise_operational_compromised_target_mask,
        ) = self._current_shield_state()
        shield_mask, diagnostics = build_shielded_action_mask(
            native_mask=native_mask,
            action_catalog=self._shield_action_catalog,
            critical_present=critical_present,
            enterprise_foothold_present=enterprise_foothold_present,
            mode=self.shield_mode,
            critical_compromised_target_mask=critical_compromised_target_mask,
            enterprise_operational_compromised_target_mask=enterprise_operational_compromised_target_mask,
        )
        self._last_shield_diagnostics = diagnostics
        return shield_mask

    def set_last_policy_mask_stats(self, *, blocked_probability_mass: np.ndarray) -> None:
        values = np.asarray(blocked_probability_mass, dtype=np.float32).reshape(
            self.num_envs
        )
        diagnostics = dict(self._last_shield_diagnostics)
        diagnostics["shield_blocked_probability_mass"] = values.tolist()
        self._last_shield_diagnostics = diagnostics

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
            for key in (
                "security",
                "business",
                "cost",
                "critical_host_safety",
                "morl_scalar_reward",
                "cyborg_scalar_reward",
            )
        }
        semantic_info = {
            key: [
                float(info.get("semantic_info", {}).get(key, 0.0))
                for info in infos
            ]
            for key in (
                "final_compromised_hosts",
                "final_critical_compromised_hosts",
                "persistent_critical_breach_rate",
                "critical_impact_count",
                "recovered_hosts",
                "analyse_count",
                "remove_count",
                "restore_count",
                "high_disruption_action_count",
                "total_action_count",
                "enterprise_foothold_present",
                "critical_present",
                "critical_hit_event",
                "critical_dwell_flag",
                "critical_path_compromise_count",
                "sleep_during_critical_breach",
                "user_action_during_critical_breach",
                "user_action_after_enterprise_foothold",
            )
        }
        return {
            "reward_terms": reward_terms,
            "semantic_info": semantic_info,
            "blue_action_index": [info.get("blue_action_index") for info in infos],
            "blue_action": [info.get("blue_action", "Sleep") for info in infos],
            "red_action": [info.get("red_action", "Sleep") for info in infos],
            "blue_action_struct": [info.get("blue_action_struct", {}) for info in infos],
            "red_action_struct": [info.get("red_action_struct", {}) for info in infos],
            "state_before": [info.get("state_before", snapshot_payload(env.last_snapshot)) for env, info in zip(self._envs, infos)],
            "state_after": [info.get("state_after", snapshot_payload(env.last_snapshot)) for env, info in zip(self._envs, infos)],
            "newly_compromised_hosts": [
                info.get("newly_compromised_hosts", []) for info in infos
            ],
            "recovered_hosts": [info.get("recovered_hosts", []) for info in infos],
            "critical_compromised_hosts": [
                info.get("critical_compromised_hosts", []) for info in infos
            ],
            "weighted_security_exposure": [
                float(info.get("weighted_security_exposure", 0.0)) for info in infos
            ],
            "weighted_business_exposure": [
                float(info.get("weighted_business_exposure", 0.0)) for info in infos
            ],
            "padding_step": [bool(info.get("padding_step", False)) for info in infos],
            "true_state_compromised_hosts": [
                info.get("true_state_compromised_hosts", []) for info in infos
            ],
            "scenario_profile": self.profile.profile_name,
            "shield_active_flag": list(
                self._last_shield_diagnostics.get("shield_active_flag", [])
            ),
            "shield_level": list(self._last_shield_diagnostics.get("shield_level", [])),
            "shield_response_tier": list(
                self._last_shield_diagnostics.get("shield_response_tier", [])
            ),
            "shield_fallback_flag": list(
                self._last_shield_diagnostics.get("shield_fallback_flag", [])
            ),
            "shield_blocked_probability_mass": list(
                self._last_shield_diagnostics.get(
                    "shield_blocked_probability_mass",
                    np.zeros(self.num_envs, dtype=np.float32).tolist(),
                )
            ),
            "shield_allowed_action_count": list(
                self._last_shield_diagnostics.get(
                    "shield_allowed_action_count",
                    np.full(self.num_envs, self.action_dim, dtype=np.int32).tolist(),
                )
            ),
        }
