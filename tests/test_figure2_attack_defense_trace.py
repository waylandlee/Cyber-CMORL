from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch

from cmorl_cyborg.export_figure2_attack_defense_trace import (
    Figure2ReplayCandidate,
    export_candidate_trace,
    select_figure2_replay_candidates,
)
from cmorl_cyborg.semantics import serialize_action
from cmorl_cyborg.topology import topology_snapshot


class _HostnameAction:
    def __init__(self, hostname: str) -> None:
        self.hostname = hostname

    def get_params(self) -> dict[str, str]:
        return {"hostname": self.hostname}

    def __str__(self) -> str:
        return f"Analyse(hostname={self.hostname})"


class _OpaqueRedAction:
    def __str__(self) -> str:
        return "DiscoverRemoteSystems"


class _SubnetAction:
    def get_params(self) -> dict[str, str]:
        return {"subnet": "10.0.202.32/28"}

    def __str__(self) -> str:
        return "DiscoverRemoteSystems 10.0.202.32/28"


def _state(compromised_hosts: list[str]) -> dict[str, object]:
    return {
        "compromised_hosts": list(compromised_hosts),
        "critical_compromised_hosts": [host for host in compromised_hosts if host == "Op_Server0"],
        "operational_compromised_hosts": [],
        "enterprise_compromised_hosts": [],
        "defender_compromised_hosts": [],
        "user_compromised_hosts": list(compromised_hosts),
        "compromised_host_count": len(compromised_hosts),
        "critical_compromised_host_count": int("Op_Server0" in compromised_hosts),
        "weighted_security_exposure": float(len(compromised_hosts)),
        "weighted_business_exposure": float(len(compromised_hosts)),
    }


class _FakeTraceEnv:
    def __init__(self) -> None:
        self.num_envs = 2
        self.obs_dim = 4
        self.action_dim = 2
        self.obj_dim = 3
        self.scenario_name = "Scenario2"
        self.scenario_profile = ""
        self.red_policy_name = "bline"
        self.profile = type("Profile", (), {"profile_name": "Scenario2"})()
        self.seed = None
        self._step = 0

    def action_catalog(self) -> list[dict[str, object]]:
        return [
            {
                "index": 0,
                "name": "Sleep",
                "params": {},
                "target_hostname": None,
                "target_subnet": None,
                "target_role_group": None,
                "raw": "Sleep",
            },
            {
                "index": 1,
                "name": "Analyse",
                "params": {"hostname": "User0"},
                "target_hostname": "User0",
                "target_subnet": "User",
                "target_role_group": "user",
                "raw": "Analyse",
            },
        ]

    def reset(self) -> tuple[np.ndarray, dict]:
        self._step = 0
        state = _state([])
        return np.zeros((self.num_envs, self.obs_dim), dtype=np.float32), {
            "state_after": [state, state],
        }

    def step(self, actions: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, dict]:
        self._step += 1
        reward_vec = np.asarray(
            [
                [1.0, -120.0, -20.0],
                [0.5, -121.0, -21.0],
            ],
            dtype=np.float32,
        )
        done = np.asarray([self._step >= 2, self._step >= 1], dtype=bool)
        truncated = np.asarray([False, False], dtype=bool)

        if self._step == 1:
            before = [_state([]), _state([])]
            after = [_state(["User0"]), _state(["User1"])]
            new_hosts = [["User0"], ["User1"]]
            recovered = [[], []]
        else:
            before = [_state(["User0"]), _state(["User1"])]
            after = [_state([]), _state(["User1"])]
            new_hosts = [[], []]
            recovered = [["User0"], []]

        info = {
            "reward_terms": {
                "security": [1.0, 0.5],
                "business": [-120.0, -121.0],
                "cost": [-20.0, -21.0],
                "morl_scalar_reward": [-139.0, -141.5],
                "cyborg_scalar_reward": [-1.0, -1.5],
            },
            "semantic_info": {
                "final_compromised_hosts": [float(len(after[0]["compromised_hosts"])), float(len(after[1]["compromised_hosts"]))],
                "final_critical_compromised_hosts": [0.0, 0.0],
                "critical_impact_count": [0.0, 0.0],
                "recovered_hosts": [float(len(recovered[0])), float(len(recovered[1]))],
                "analyse_count": [1.0, 1.0],
                "remove_count": [0.0, 0.0],
                "restore_count": [0.0, 0.0],
                "high_disruption_action_count": [0.0, 0.0],
                "total_action_count": [1.0, 1.0],
            },
            "blue_action_struct": [
                {
                    "name": "Analyse",
                    "params": {"hostname": "User0"},
                    "target_hostname": "User0",
                    "target_subnet": "User",
                    "target_role_group": "user",
                    "raw": "Analyse",
                },
                {
                    "name": "Analyse",
                    "params": {"hostname": "User1"},
                    "target_hostname": "User1",
                    "target_subnet": "User",
                    "target_role_group": "user",
                    "raw": "Analyse",
                },
            ],
            "red_action_struct": [
                {
                    "name": "DiscoverRemoteSystems",
                    "params": {"subnet": "Enterprise"},
                    "target_hostname": None,
                    "target_subnet": "Enterprise",
                    "target_role_group": "enterprise",
                    "raw": "DiscoverRemoteSystems",
                },
                {
                    "name": "DiscoverRemoteSystems",
                    "params": {"subnet": "User"},
                    "target_hostname": None,
                    "target_subnet": "User",
                    "target_role_group": "user",
                    "raw": "DiscoverRemoteSystems",
                },
            ],
            "state_before": before,
            "state_after": after,
            "newly_compromised_hosts": new_hosts,
            "recovered_hosts": recovered,
            "critical_compromised_hosts": [[], []],
        }
        return (
            np.zeros((self.num_envs, self.obs_dim), dtype=np.float32),
            reward_vec,
            done,
            truncated,
            info,
        )


class _FakeActorCritic:
    def act(self, obs: torch.Tensor):
        actions = torch.ones((obs.shape[0],), dtype=torch.int64)
        return type("PolicyOutput", (), {"actions": actions})()


def test_topology_snapshot_extracts_expected_host_locations() -> None:
    snapshot = topology_snapshot("Scenario2", "")

    assert sorted(subnet["name"] for subnet in snapshot["subnets"]) == [
        "Enterprise",
        "Operational",
        "User",
    ]
    assert snapshot["host_to_subnet"]["Op_Server0"] == "Operational"
    assert snapshot["host_to_subnet"]["Enterprise2"] == "Enterprise"
    assert snapshot["host_to_subnet"]["User0"] == "User"


def test_serialize_action_preserves_location_and_raw_fields() -> None:
    blue_action = serialize_action(_HostnameAction("User0"), scenario_name="Scenario2")
    red_action = serialize_action(_OpaqueRedAction(), scenario_name="Scenario2")
    subnet_action = serialize_action(
        _SubnetAction(),
        scenario_name="Scenario2",
        subnet_aliases={"10.0.202.32/28": "User"},
    )

    assert blue_action["name"] == "_HostnameAction"
    assert blue_action["params"] == {"hostname": "User0"}
    assert blue_action["target_hostname"] == "User0"
    assert blue_action["target_subnet"] == "User"
    assert blue_action["target_role_group"] == "user"

    assert red_action["params"] == {}
    assert red_action["raw"] == "DiscoverRemoteSystems"
    assert subnet_action["target_subnet"] == "User"
    assert subnet_action["target_role_group"] == "user"


def test_select_figure2_replay_candidates_dedupes_aliases() -> None:
    ours_candidates = select_figure2_replay_candidates(
        "ours_stage2_fair",
        {"selected_policy_id": "policy_a"},
        {
            "closest_candidate_policy_id": "policy_a",
            "candidate_rows": [
                {"policy_id": "policy_b", "is_reevaluated_feasible": False},
            ],
        },
    )
    assert ours_candidates == [
        Figure2ReplayCandidate(
            policy_id="policy_a",
            candidate_label="selected",
            candidate_aliases=("selected", "closest_candidate"),
        )
    ]

    no_constraint_candidates = select_figure2_replay_candidates(
        "no_constraint_stage2_fair",
        {"selected_policy_id": "policy_a"},
        {
            "closest_candidate_policy_id": "policy_b",
            "candidate_rows": [
                {
                    "policy_id": "policy_c",
                    "is_reevaluated_feasible": True,
                    "reevaluated_security_return": 10.0,
                },
                {
                    "policy_id": "policy_b",
                    "is_reevaluated_feasible": True,
                    "reevaluated_security_return": 8.0,
                },
            ],
        },
    )
    assert [candidate.policy_id for candidate in no_constraint_candidates] == [
        "policy_a",
        "policy_b",
        "policy_c",
    ]
    assert no_constraint_candidates[-1].candidate_label == "best_feasible_security"


def test_export_candidate_trace_writes_jsonl_and_manifest(
    monkeypatch,
    tmp_path: Path,
) -> None:
    checkpoint_path = tmp_path / "policy.pt"
    checkpoint_path.write_bytes(b"placeholder")
    buffer_path = tmp_path / "solution_buffer.json"
    buffer_path.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(
        "cmorl_cyborg.export_figure2_attack_defense_trace._build_cyborg_env_from_metadata",
        lambda metadata: _FakeTraceEnv(),
    )
    monkeypatch.setattr(
        "cmorl_cyborg.export_figure2_attack_defense_trace._load_actor_critic",
        lambda checkpoint_path, metadata: _FakeActorCritic(),
    )

    output_dir = export_candidate_trace(
        method_name="ours_stage2_fair",
        seed=7,
        candidate=Figure2ReplayCandidate(
            policy_id="policy_demo",
            candidate_label="selected",
            candidate_aliases=("selected", "closest_candidate"),
        ),
        buffer_path=buffer_path,
        buffer_anchor_path=buffer_path,
        record={"policy_id": "policy_demo", "checkpoint_path": str(checkpoint_path)},
        metadata={"env": {"seed": 7}, "model": {"hidden_size": 8, "obj_dim": 3}},
        output_root=tmp_path / "exports",
        eval_episodes=1,
    )

    manifest = json.loads((output_dir / "trace_manifest.json").read_text(encoding="utf-8"))
    rows = [
        json.loads(line)
        for line in (output_dir / "episode_000.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    summaries = json.loads((output_dir / "episode_summaries.json").read_text(encoding="utf-8"))

    assert manifest["figure_context"] == "Figure 2 tight fair-compare"
    assert manifest["candidate_aliases"] == ["selected", "closest_candidate"]
    assert (output_dir / "topology_snapshot.json").exists()
    assert (output_dir / "action_catalog.json").exists()
    assert len(rows) == 3
    assert rows[0]["blue_action"]["target_hostname"] == "User0"
    assert rows[0]["red_action"]["target_subnet"] == "Enterprise"
    assert {row["env_idx"] for row in rows} == {0, 1}
    assert summaries[0]["num_trace_rows"] == 3
