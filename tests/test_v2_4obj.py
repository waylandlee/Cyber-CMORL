from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import pytest

import cmorl_cyborg.v2_4obj_pilot_runner as v2_runner
import cmorl_minicage.evaluate_constraints as constraint_eval
import cmorl_minicage.train_stage2 as stage2_train
from cmorl_cyborg.export_candidate_semantic_audit import export_candidate_semantic_audit
from cmorl_cyborg.reward import (
    CRITICAL_HOST_SAFETY_MODE_DENSE_PERSISTENT,
    CRITICAL_HOST_SAFETY_MODE_LEGACY,
    RewardTerms,
    critical_host_safety_objective,
    critical_host_safety_step_reward,
)
from cmorl_minicage.utils import save_json


def test_critical_host_safety_reward_matches_episode_objective() -> None:
    max_episode_steps = 100
    first_hit_step = 15
    reward = (
        critical_host_safety_step_reward(
            critical_hit_event=1.0,
            critical_present=1.0,
            episode_done=False,
            step_idx=first_hit_step,
            max_episode_steps=max_episode_steps,
            mode=CRITICAL_HOST_SAFETY_MODE_LEGACY,
        )
        + critical_host_safety_step_reward(
            critical_hit_event=0.0,
            critical_present=1.0,
            episode_done=True,
            step_idx=max_episode_steps - 1,
            max_episode_steps=max_episode_steps,
            mode=CRITICAL_HOST_SAFETY_MODE_LEGACY,
        )
    )
    expected = critical_host_safety_objective(
        ever_critical_breach=1.0,
        persistent_critical_breach=1.0,
        critical_hit_latency_score=first_hit_step / float(max_episode_steps + 1),
        mode=CRITICAL_HOST_SAFETY_MODE_LEGACY,
    )

    assert reward == pytest.approx(expected)
    assert np.allclose(
        RewardTerms(1.0, 2.0, 3.0, -0.5).as_array(),
        np.asarray([1.0, 2.0, 3.0, -0.5], dtype=np.float32),
    )


def test_v2_1_dense_critical_host_safety_reward_matches_episode_objective() -> None:
    max_episode_steps = 100
    first_hit_step = 15
    dwell_steps = max_episode_steps - first_hit_step
    reward = 0.0
    for step_idx in range(first_hit_step, max_episode_steps):
        reward += critical_host_safety_step_reward(
            critical_hit_event=1.0 if step_idx == first_hit_step else 0.0,
            critical_present=1.0,
            episode_done=bool(step_idx == max_episode_steps - 1),
            step_idx=step_idx,
            max_episode_steps=max_episode_steps,
            mode=CRITICAL_HOST_SAFETY_MODE_DENSE_PERSISTENT,
        )
    expected = critical_host_safety_objective(
        ever_critical_breach=1.0,
        persistent_critical_breach=1.0,
        critical_hit_latency_score=first_hit_step / float(max_episode_steps + 1),
        dwell_ratio=dwell_steps / float(max_episode_steps),
        mode=CRITICAL_HOST_SAFETY_MODE_DENSE_PERSISTENT,
    )
    assert reward == pytest.approx(expected)


def test_constraint_eval_reports_critical_host_safety_return(monkeypatch) -> None:
    class _FakeEnv:
        def __init__(self) -> None:
            self.num_envs = 2
            self.obj_dim = 4
            self.obs_dim = 3
            self.action_dim = 2
            self.max_steps = 100
            self.seed = 7

        def reset(self):
            return np.zeros((self.num_envs, self.obs_dim), dtype=np.float32), {}

        def step(self, actions):
            reward_vec = np.asarray(
                [
                    [10.0, -120.0, -20.0, -0.65],
                    [8.0, -121.0, -21.0, 0.0],
                ],
                dtype=np.float32,
            )
            done = np.asarray([True, True], dtype=bool)
            semantic_info = {
                "final_compromised_hosts": [1.0, 0.0],
                "final_critical_compromised_hosts": [1.0, 0.0],
                "critical_impact_count": [1.0, 0.0],
                "recovered_hosts": [0.0, 0.0],
                "analyse_count": [0.0, 0.0],
                "remove_count": [0.0, 0.0],
                "restore_count": [0.0, 0.0],
                "high_disruption_action_count": [0.0, 0.0],
                "total_action_count": [1.0, 1.0],
                "critical_present": [1.0, 0.0],
                "critical_hit_event": [1.0, 0.0],
                "critical_dwell_flag": [1.0, 0.0],
                "critical_path_compromise_count": [2.0, 0.0],
                "sleep_during_critical_breach": [0.0, 0.0],
                "user_action_during_critical_breach": [0.0, 0.0],
                "user_action_after_enterprise_foothold": [0.0, 0.0],
            }
            return (
                np.zeros((self.num_envs, self.obs_dim), dtype=np.float32),
                reward_vec,
                done,
                np.zeros_like(done, dtype=bool),
                {"semantic_info": semantic_info},
            )

    monkeypatch.setattr(
        constraint_eval,
        "_build_env_from_metadata",
        lambda metadata: _FakeEnv(),
    )

    metrics = constraint_eval._evaluate_actor_critic_policy_detailed(
        actor_critic=None,
        metadata={"env": {"seed": 7}, "model": {"obj_dim": 4}},
        thresholds={"d_business": -125.0, "d_cost": -22.0},
        eval_episodes=1,
        baseline_kind="sleep",
    )

    assert metrics["security_return"] == 9.0
    assert metrics["business_return"] == -120.5
    assert metrics["cost_return"] == -20.5
    assert metrics["critical_host_safety_return"] == pytest.approx(-0.325)
    assert metrics["critical_host_safety_cvar_alpha"] == pytest.approx(-0.65)


def test_export_candidate_semantic_audit_keeps_business_cost_and_fourth_return(tmp_path: Path) -> None:
    trace_dir = tmp_path / "trace"
    trace_dir.mkdir()
    save_json(
        trace_dir / "trace_manifest.json",
        {
            "method_name": "ours_stage2_fair_critical_safe_v2_4obj",
            "seed": 11,
            "policy_id": "cand_4d",
            "candidate_label": "critical_safe_balanced_selected",
            "eval_episodes": 1,
            "tight_thresholds": {"d_business": -125.0, "d_cost": -22.0},
        },
    )
    save_json(
        trace_dir / "episode_summaries.json",
        [
            {
                "episode_id": "episode_000",
                "episode_seed": 11,
                "num_trace_rows": 1,
                "env_summaries": [
                    {
                        "env_idx": 0,
                        "env_seed": 11,
                        "step_count": 1,
                        "return_vector": [5.0, -120.0, -20.0, -0.7],
                        "final_state": {
                            "compromised_hosts": ["Enterprise0"],
                            "critical_compromised_hosts": [],
                            "compromised_host_count": 1,
                        },
                    }
                ],
            }
        ],
    )
    row = {
        "episode_id": "episode_000",
        "env_idx": 0,
        "step_idx": 0,
        "blue_action": {
            "name": "Analyse",
            "target_hostname": "User0",
            "target_subnet": "User",
        },
        "red_action": {
            "name": "DiscoverRemoteSystems",
            "target_hostname": None,
            "target_subnet": "Enterprise",
        },
        "state_before": {
            "compromised_hosts": [],
            "critical_compromised_hosts": [],
            "compromised_host_count": 0,
        },
        "state_after": {
            "compromised_hosts": ["Enterprise0"],
            "critical_compromised_hosts": [],
            "compromised_host_count": 1,
        },
        "newly_compromised_hosts": ["Enterprise0"],
        "recovered_hosts": [],
    }
    (trace_dir / "episode_000.jsonl").write_text(
        json.dumps(row, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    output_dir = tmp_path / "audit"
    result = export_candidate_semantic_audit(trace_dir=trace_dir, output_dir=output_dir)
    summary = result["stage_a"]

    assert summary["mean_business_return"] == -120.0
    assert summary["mean_cost_return"] == -20.0
    assert summary["mean_critical_host_safety_return"] == -0.7

    with (output_dir / "env_run_risk_table.csv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["business_return"] == "-120.0"
    assert rows[0]["cost_return"] == "-20.0"
    assert rows[0]["critical_host_safety_return"] == "-0.7"


def test_tail_acceptance_rejects_persistent_regression() -> None:
    decision = stage2_train._tail_acceptance_decision(
        {
            "business_return": -120.0,
            "cost_return": -20.0,
            "persistent_critical_breach_rate": 0.40,
            "mean_critical_dwell_steps": 10.0,
            "critical_host_safety_cvar_alpha": -0.50,
            "ever_critical_breach_rate": 0.60,
            "critical_hit_latency_score": 0.30,
        },
        {
            "business_return": -119.0,
            "cost_return": -19.0,
            "persistent_critical_breach_rate": 0.55,
            "mean_critical_dwell_steps": 8.0,
            "critical_host_safety_cvar_alpha": -0.40,
            "ever_critical_breach_rate": 0.55,
            "critical_hit_latency_score": 0.35,
        },
        objective_improvement=1.0,
        tail_config=stage2_train.TailAcceptanceConfig(
            mode="critical_tail",
            persistent_non_regression=True,
        ),
    )
    assert decision["should_rank"] is False
    assert decision["gate_result"]["gate_reason"] == "persistent_non_regression"


def test_critical_safe_balanced_prefers_better_tail_cvar(monkeypatch) -> None:
    records = [
        {"policy_id": "cand_a"},
        {"policy_id": "cand_b"},
    ]
    diagnostics = {
        "evaluated_candidates": [
            {
                "policy_id": "cand_a",
                "business_return": -124.0,
                "cost_return": -21.0,
                "ever_critical_breach_rate": 0.80,
                "persistent_critical_breach_rate": 0.60,
                "critical_host_safety_cvar_alpha": -0.90,
                "mean_critical_dwell_steps": 12.0,
                "critical_hit_latency_score": 0.40,
                "user_action_during_critical_breach_rate": 0.10,
                "sleep_during_critical_breach_rate": 0.01,
                "mean_violation": 2.0,
                "security_return": -500.0,
            },
            {
                "policy_id": "cand_b",
                "business_return": -124.0,
                "cost_return": -21.0,
                "ever_critical_breach_rate": 0.80,
                "persistent_critical_breach_rate": 0.60,
                "critical_host_safety_cvar_alpha": -0.40,
                "mean_critical_dwell_steps": 14.0,
                "critical_hit_latency_score": 0.35,
                "user_action_during_critical_breach_rate": 0.12,
                "sleep_during_critical_breach_rate": 0.01,
                "mean_violation": 2.0,
                "security_return": -510.0,
            },
        ]
    }

    monkeypatch.setattr(
        constraint_eval,
        "_select_record_semantic_aware",
        lambda *args, **kwargs: (records[0], diagnostics),
    )

    selected, selection_diagnostics = constraint_eval._select_record_critical_safe_balanced(
        records,
        metadata={},
        buffer_anchor="unused.json",
        thresholds={"d_business": -125.0, "d_cost": -22.0},
        eval_episodes=8,
        semantic_metric_weights={},
    )

    assert selected["policy_id"] == "cand_b"
    assert selection_diagnostics["selection_policy"] == "critical_safe_balanced"


def _patch_runner_pilot_io(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    stage1_buffer: Path,
    stage2_buffer: Path,
    baseline_buffer: Path,
) -> None:
    monkeypatch.setattr(v2_runner, "_runner_root", lambda: tmp_path / "runner")
    monkeypatch.setattr(
        v2_runner,
        "_selected_constraint_metrics_path",
        lambda seed: tmp_path / f"raw_selected_constraint_metrics_seed_{seed:04d}.json",
    )
    monkeypatch.setattr(
        v2_runner,
        "_baseline_constraint_metrics_output_path",
        lambda seed: tmp_path / f"baseline_constraint_metrics_seed_{seed:04d}.json",
    )
    monkeypatch.setattr(v2_runner, "train_stage1", lambda config: stage1_buffer)
    monkeypatch.setattr(v2_runner, "train_stage2", lambda config: stage2_buffer)
    monkeypatch.setattr(v2_runner, "_resolve_baseline_buffer", lambda seed: baseline_buffer)
    monkeypatch.setattr(
        v2_runner,
        "_export_replay_audit",
        lambda **kwargs: {
            "trace_dir": str(
                (
                    tmp_path
                    / "trace"
                    / f"{kwargs['candidate'].candidate_label}__{kwargs['candidate'].policy_id}"
                ).resolve()
            ),
            "analysis_dir": str(
                (
                    tmp_path
                    / "audit"
                    / f"{kwargs['candidate'].candidate_label}__{kwargs['candidate'].policy_id}"
                ).resolve()
            ),
            "summary_path": str(
                (
                    tmp_path
                    / "audit"
                    / f"{kwargs['candidate'].candidate_label}__{kwargs['candidate'].policy_id}"
                    / "risk_tier_summary.json"
                ).resolve()
            ),
            "audit_result": {"stage_a": {}},
            "summary": {
                "high_confidence_env_run_rate": (
                    1.0 if kwargs["method_name"] == v2_runner.BASELINE_METHOD_NAME else 0.9
                )
            },
        },
    )


def test_run_v2_4obj_pilot_gate_aware_reselection_writes_summary(
    monkeypatch, tmp_path: Path
) -> None:
    stage1_template = tmp_path / "stage1.yaml"
    stage2_template = tmp_path / "stage2.yaml"
    stage1_template.write_text(
        "model:\n  obj_dim: 4\n  critical_host_safety_mode: v2_1_dense_persistent\n",
        encoding="utf-8",
    )
    stage2_template.write_text(
        "model:\n  obj_dim: 4\n  critical_host_safety_mode: v2_1_dense_persistent\n"
        "tail_acceptance:\n  mode: critical_tail\n  tail_eval_episodes: 16\n  tail_alpha: 0.25\n",
        encoding="utf-8",
    )

    stage1_buffer = tmp_path / "stage1_buffer.json"
    stage2_buffer = tmp_path / "stage2_buffer.json"
    baseline_buffer = tmp_path / "baseline_buffer.json"
    save_json(
        stage1_buffer,
        {
            "schema_version": "0.3.0",
            "metadata": {
                "env": {"seed": 11},
                "model": {"obj_dim": 4, "hidden_size": 8},
                "round_summaries": [
                    {"tail_reject_reason_counts": {"persistent_non_regression": 2}}
                ],
            },
            "records": [
                {
                    "policy_id": "stage1_pref_003_ckpt_191",
                    "checkpoint_path": "dummy.pt",
                    "objective_vector": [9.5, -132.0, -20.2, -0.66],
                }
            ],
            "pareto_front": [
                {
                    "policy_id": "stage1_pref_003_ckpt_191",
                    "checkpoint_path": "dummy.pt",
                    "objective_vector": [9.5, -132.0, -20.2, -0.66],
                }
            ],
        },
    )
    save_json(
        stage2_buffer,
        {
            "schema_version": "0.3.0",
            "metadata": {
                "env": {"seed": 11},
                "model": {"obj_dim": 4, "hidden_size": 8},
                "round_summaries": [
                    {"tail_reject_reason_counts": {"persistent_non_regression": 2}}
                ],
            },
            "records": [
                {
                    "policy_id": "stage1_pref_003_ckpt_191",
                    "checkpoint_path": "dummy.pt",
                    "objective_vector": [9.5, -132.0, -20.2, -0.66],
                },
                {
                    "policy_id": "stage2_ext_006_obj_0",
                    "checkpoint_path": "dummy.pt",
                    "objective_vector": [10.0, -121.0, -21.0, -0.55],
                    "notes": {
                        "tail_acceptance": {
                            "parent_tail_metrics": {
                                "persistent_critical_breach_rate": 0.8,
                                "mean_critical_dwell_steps": 12.0,
                            },
                            "child_tail_metrics": {
                                "persistent_critical_breach_rate": 0.8,
                                "mean_critical_dwell_steps": 6.0,
                            },
                        }
                    },
                },
                {
                    "policy_id": "stage2_ext_008_obj_1",
                    "checkpoint_path": "dummy.pt",
                    "objective_vector": [9.8, -129.5, -21.0, -0.59],
                },
            ],
            "pareto_front": [
                {
                    "policy_id": "stage1_pref_003_ckpt_191",
                    "checkpoint_path": "dummy.pt",
                    "objective_vector": [9.5, -132.0, -20.2, -0.66],
                },
                {
                    "policy_id": "stage2_ext_006_obj_0",
                    "checkpoint_path": "dummy.pt",
                    "objective_vector": [10.0, -121.0, -21.0, -0.55],
                },
                {
                    "policy_id": "stage2_ext_008_obj_1",
                    "checkpoint_path": "dummy.pt",
                    "objective_vector": [9.8, -129.5, -21.0, -0.59],
                },
            ],
        },
    )
    save_json(
        baseline_buffer,
        {
            "schema_version": "0.3.0",
            "metadata": {"env": {"seed": 11}, "model": {"obj_dim": 3, "hidden_size": 8}},
            "records": [
                {
                    "policy_id": "base_3d",
                    "checkpoint_path": "dummy.pt",
                    "objective_vector": [9.0, -120.0, -20.0],
                }
            ],
            "pareto_front": [
                {
                    "policy_id": "base_3d",
                    "checkpoint_path": "dummy.pt",
                    "objective_vector": [9.0, -120.0, -20.0],
                }
            ],
        },
    )

    _patch_runner_pilot_io(
        monkeypatch,
        tmp_path,
        stage1_buffer=stage1_buffer,
        stage2_buffer=stage2_buffer,
        baseline_buffer=baseline_buffer,
    )

    def fake_run_constraint_eval(
        *,
        method_name,
        input_path,
        selection_policy,
        thresholds_path,
        eval_episodes,
        output_path,
    ):
        if selection_policy == "critical_safe_balanced":
            payload = {
                "selection_policy": "critical_safe_balanced",
                "selected_policy_id": "stage1_pref_003_ckpt_191",
                "selected_objective_vector": [9.5, -132.0, -20.2, -0.66],
                "business_return": -132.0,
                "cost_return": -20.2,
                "feasible_rate": 0.4,
                "mean_violation": 21.3,
                "ever_critical_breach_rate": 0.75,
                "persistent_critical_breach_rate": 0.75,
                "mean_first_critical_hit_step": 44.0,
                "critical_hit_latency_score": 0.44,
                "mean_critical_dwell_steps": 55.0,
                "critical_host_safety_return": -0.66,
                "critical_host_safety_cvar_alpha": -0.94,
                "selection_diagnostics": {
                    "selection_policy": "critical_safe_balanced",
                    "shortlist_policy_ids": [
                        "stage2_ext_006_obj_0",
                        "stage1_pref_003_ckpt_191",
                        "stage2_ext_008_obj_1",
                    ],
                    "evaluated_candidates": [
                        {
                            "policy_id": "stage1_pref_003_ckpt_191",
                            "objective_vector": [9.5, -132.0, -20.2, -0.66],
                            "business_return": -132.0,
                            "cost_return": -20.2,
                            "feasible_rate": 0.4,
                            "mean_violation": 21.3,
                            "security_return": -100.0,
                            "critical_host_safety_return": -0.66,
                            "critical_host_safety_cvar_alpha": -0.94,
                            "ever_critical_breach_rate": 0.75,
                            "persistent_critical_breach_rate": 0.75,
                            "mean_first_critical_hit_step": 44.0,
                            "critical_hit_latency_score": 0.44,
                            "mean_critical_dwell_steps": 55.0,
                            "user_action_during_critical_breach_rate": 0.10,
                            "sleep_during_critical_breach_rate": 0.01,
                        },
                        {
                            "policy_id": "stage2_ext_006_obj_0",
                            "objective_vector": [10.0, -121.0, -21.0, -0.55],
                            "business_return": -121.0,
                            "cost_return": -21.0,
                            "feasible_rate": 0.8,
                            "mean_violation": 3.0,
                            "security_return": -110.0,
                            "critical_host_safety_return": -0.55,
                            "critical_host_safety_cvar_alpha": -0.70,
                            "ever_critical_breach_rate": 0.89,
                            "persistent_critical_breach_rate": 0.8,
                            "mean_first_critical_hit_step": 25.0,
                            "critical_hit_latency_score": 0.36,
                            "mean_critical_dwell_steps": 6.0,
                            "user_action_during_critical_breach_rate": 0.05,
                            "sleep_during_critical_breach_rate": 0.01,
                        },
                        {
                            "policy_id": "stage2_ext_008_obj_1",
                            "objective_vector": [9.8, -129.5, -21.0, -0.59],
                            "business_return": -129.5,
                            "cost_return": -21.0,
                            "feasible_rate": 0.7,
                            "mean_violation": 4.0,
                            "security_return": -105.0,
                            "critical_host_safety_return": -0.59,
                            "critical_host_safety_cvar_alpha": -0.75,
                            "ever_critical_breach_rate": 0.85,
                            "persistent_critical_breach_rate": 0.8,
                            "mean_first_critical_hit_step": 26.0,
                            "critical_hit_latency_score": 0.38,
                            "mean_critical_dwell_steps": 7.0,
                            "user_action_during_critical_breach_rate": 0.06,
                            "sleep_during_critical_breach_rate": 0.01,
                        },
                    ],
                },
            }
        else:
            payload = {
                "selected_policy_id": "base_3d",
                "selected_objective_vector": [9.0, -120.0, -20.0],
                "business_return": -120.0,
                "cost_return": -20.0,
                "feasible_rate": 1.0,
                "ever_critical_breach_rate": 1.0,
                "persistent_critical_breach_rate": 0.8,
                "mean_first_critical_hit_step": 10.0,
                "critical_hit_latency_score": 0.20,
                "mean_critical_dwell_steps": 12.0,
                "critical_host_safety_return": None,
                "critical_host_safety_cvar_alpha": None,
            }
        save_json(output_path, payload)
        return payload

    monkeypatch.setattr(v2_runner, "_run_constraint_eval", fake_run_constraint_eval)

    final_summary = v2_runner.run_v2_4obj_pilot(
        seed=11,
        stage1_config_path=stage1_template,
        stage2_config_path=stage2_template,
        thresholds_path="ignored.json",
        constraint_eval_episodes=8,
        replay_eval_episodes=20,
        method_name="ours_stage2_fair_critical_safe_v2_1_4obj",
        baseline_method_name="ours_stage2_fair",
        runner_dirname="fair_compare_critical_safe_v2_1_4obj_runner",
    )

    pilot_summary = json.loads(
        (tmp_path / "runner" / "seed_0011_pilot_summary.json").read_text(encoding="utf-8")
    )
    selected_metrics = json.loads(
        (tmp_path / "runner" / "seed_0011_selected_constraint_metrics.json").read_text(
            encoding="utf-8"
        )
    )
    selection_diagnostics = json.loads(
        (tmp_path / "runner" / "seed_0011_selection_diagnostics.json").read_text(
            encoding="utf-8"
        )
    )
    assert final_summary["pilot_passed"] is True
    assert final_summary["failure_reasons"] == []
    assert pilot_summary["selected_policy_id"] == "stage2_ext_006_obj_0"
    assert pilot_summary["raw_selected_policy_id"] == "stage1_pref_003_ckpt_191"
    assert pilot_summary["baseline_policy_id"] == "base_3d"
    assert pilot_summary["pilot_passed"] is True
    assert pilot_summary["selection_mode"] == v2_runner.SELECTION_MODE_STAGE2_GATE_AWARE
    assert pilot_summary["selection_fallback_used"] is False
    assert pilot_summary["selection_fallback_reason"] is None
    assert pilot_summary["stage2_candidates_considered"] == [
        "stage2_ext_006_obj_0",
        "stage2_ext_008_obj_1",
    ]
    assert pilot_summary["stage2_gate_pass_policy_ids"] == ["stage2_ext_006_obj_0"]
    assert pilot_summary["stage2_gate_reject_reason_counts"] == {"business_guardrail_ok": 1}
    assert pilot_summary["tail_acceptance_mode"] == "critical_tail"
    assert pilot_summary["tail_eval_episodes"] == 16
    assert pilot_summary["tail_alpha"] == pytest.approx(0.25)
    assert pilot_summary["critical_host_safety_cvar_alpha"] == pytest.approx(-0.7)
    assert pilot_summary["parent_tail_metrics"]["persistent_critical_breach_rate"] == pytest.approx(
        0.8
    )
    assert pilot_summary["child_tail_metrics"]["mean_critical_dwell_steps"] == pytest.approx(
        6.0
    )
    assert pilot_summary["tail_reject_reason_counts"] == {"persistent_non_regression": 2}
    assert final_summary["critical_host_safety_cvar_alpha"] == pytest.approx(-0.7)
    assert final_summary["selected_policy_id"] == "stage2_ext_006_obj_0"
    assert final_summary["raw_selected_policy_id"] == "stage1_pref_003_ckpt_191"
    assert final_summary["parent_tail_metrics"]["persistent_critical_breach_rate"] == pytest.approx(
        0.8
    )
    assert final_summary["tail_reject_reason_counts"] == {"persistent_non_regression": 2}
    assert "gate_selected__stage2_ext_006_obj_0" in pilot_summary["selected_audit_dir"]
    assert "gate_selected__stage2_ext_006_obj_0" in pilot_summary["selected_risk_summary_path"]
    assert selected_metrics["selected_policy_id"] == "stage2_ext_006_obj_0"
    assert selected_metrics["selection_policy"] == v2_runner.SELECTION_MODE_STAGE2_GATE_AWARE
    assert selection_diagnostics["raw_selected_policy_id"] == "stage1_pref_003_ckpt_191"
    assert selection_diagnostics["selected_policy_id"] == "stage2_ext_006_obj_0"
    assert selection_diagnostics["selection_fallback_used"] is False


def test_run_v2_4obj_pilot_gate_aware_reselection_falls_back_to_raw_selector(
    monkeypatch, tmp_path: Path
) -> None:
    stage1_template = tmp_path / "stage1.yaml"
    stage2_template = tmp_path / "stage2.yaml"
    stage1_template.write_text(
        "model:\n  obj_dim: 4\n  critical_host_safety_mode: v2_1_dense_persistent\n",
        encoding="utf-8",
    )
    stage2_template.write_text(
        "model:\n  obj_dim: 4\n  critical_host_safety_mode: v2_1_dense_persistent\n"
        "tail_acceptance:\n  mode: critical_tail\n  tail_eval_episodes: 16\n  tail_alpha: 0.25\n",
        encoding="utf-8",
    )

    stage1_buffer = tmp_path / "stage1_buffer.json"
    stage2_buffer = tmp_path / "stage2_buffer.json"
    baseline_buffer = tmp_path / "baseline_buffer.json"
    save_json(
        stage1_buffer,
        {
            "schema_version": "0.3.0",
            "metadata": {"env": {"seed": 11}, "model": {"obj_dim": 4, "hidden_size": 8}},
            "records": [
                {
                    "policy_id": "stage1_pref_003_ckpt_191",
                    "checkpoint_path": "dummy.pt",
                    "objective_vector": [9.5, -132.0, -20.2, -0.66],
                }
            ],
            "pareto_front": [
                {
                    "policy_id": "stage1_pref_003_ckpt_191",
                    "checkpoint_path": "dummy.pt",
                    "objective_vector": [9.5, -132.0, -20.2, -0.66],
                }
            ],
        },
    )
    save_json(
        stage2_buffer,
        {
            "schema_version": "0.3.0",
            "metadata": {"env": {"seed": 11}, "model": {"obj_dim": 4, "hidden_size": 8}},
            "records": [
                {
                    "policy_id": "stage1_pref_003_ckpt_191",
                    "checkpoint_path": "dummy.pt",
                    "objective_vector": [9.5, -132.0, -20.2, -0.66],
                },
                {
                    "policy_id": "stage2_ext_008_obj_1",
                    "checkpoint_path": "dummy.pt",
                    "objective_vector": [9.8, -129.5, -21.0, -0.59],
                    "notes": {
                        "tail_acceptance": {
                            "parent_tail_metrics": {"persistent_critical_breach_rate": 0.8},
                            "child_tail_metrics": {"mean_critical_dwell_steps": 7.0},
                        }
                    },
                },
            ],
            "pareto_front": [
                {
                    "policy_id": "stage1_pref_003_ckpt_191",
                    "checkpoint_path": "dummy.pt",
                    "objective_vector": [9.5, -132.0, -20.2, -0.66],
                },
                {
                    "policy_id": "stage2_ext_008_obj_1",
                    "checkpoint_path": "dummy.pt",
                    "objective_vector": [9.8, -129.5, -21.0, -0.59],
                },
            ],
        },
    )
    save_json(
        baseline_buffer,
        {
            "schema_version": "0.3.0",
            "metadata": {"env": {"seed": 11}, "model": {"obj_dim": 3, "hidden_size": 8}},
            "records": [
                {
                    "policy_id": "base_3d",
                    "checkpoint_path": "dummy.pt",
                    "objective_vector": [9.0, -120.0, -20.0],
                }
            ],
            "pareto_front": [
                {
                    "policy_id": "base_3d",
                    "checkpoint_path": "dummy.pt",
                    "objective_vector": [9.0, -120.0, -20.0],
                }
            ],
        },
    )

    _patch_runner_pilot_io(
        monkeypatch,
        tmp_path,
        stage1_buffer=stage1_buffer,
        stage2_buffer=stage2_buffer,
        baseline_buffer=baseline_buffer,
    )

    def fake_run_constraint_eval(
        *,
        method_name,
        input_path,
        selection_policy,
        thresholds_path,
        eval_episodes,
        output_path,
    ):
        if selection_policy == "critical_safe_balanced":
            payload = {
                "selection_policy": "critical_safe_balanced",
                "selected_policy_id": "stage1_pref_003_ckpt_191",
                "selected_objective_vector": [9.5, -132.0, -20.2, -0.66],
                "business_return": -132.0,
                "cost_return": -20.2,
                "feasible_rate": 0.4,
                "mean_violation": 21.3,
                "ever_critical_breach_rate": 0.75,
                "persistent_critical_breach_rate": 0.75,
                "mean_first_critical_hit_step": 44.0,
                "critical_hit_latency_score": 0.44,
                "mean_critical_dwell_steps": 55.0,
                "critical_host_safety_return": -0.66,
                "critical_host_safety_cvar_alpha": -0.94,
                "selection_diagnostics": {
                    "selection_policy": "critical_safe_balanced",
                    "shortlist_policy_ids": [
                        "stage2_ext_008_obj_1",
                        "stage1_pref_003_ckpt_191",
                    ],
                    "evaluated_candidates": [
                        {
                            "policy_id": "stage1_pref_003_ckpt_191",
                            "objective_vector": [9.5, -132.0, -20.2, -0.66],
                            "business_return": -132.0,
                            "cost_return": -20.2,
                            "feasible_rate": 0.4,
                            "mean_violation": 21.3,
                            "security_return": -100.0,
                            "critical_host_safety_return": -0.66,
                            "critical_host_safety_cvar_alpha": -0.94,
                            "ever_critical_breach_rate": 0.75,
                            "persistent_critical_breach_rate": 0.75,
                            "mean_first_critical_hit_step": 44.0,
                            "critical_hit_latency_score": 0.44,
                            "mean_critical_dwell_steps": 55.0,
                            "user_action_during_critical_breach_rate": 0.10,
                            "sleep_during_critical_breach_rate": 0.01,
                        },
                        {
                            "policy_id": "stage2_ext_008_obj_1",
                            "objective_vector": [9.8, -129.5, -21.0, -0.59],
                            "business_return": -129.5,
                            "cost_return": -21.0,
                            "feasible_rate": 0.7,
                            "mean_violation": 4.0,
                            "security_return": -105.0,
                            "critical_host_safety_return": -0.59,
                            "critical_host_safety_cvar_alpha": -0.75,
                            "ever_critical_breach_rate": 0.85,
                            "persistent_critical_breach_rate": 0.81,
                            "mean_first_critical_hit_step": 26.0,
                            "critical_hit_latency_score": 0.38,
                            "mean_critical_dwell_steps": 7.0,
                            "user_action_during_critical_breach_rate": 0.06,
                            "sleep_during_critical_breach_rate": 0.01,
                        },
                    ],
                },
            }
        else:
            payload = {
                "selected_policy_id": "base_3d",
                "selected_objective_vector": [9.0, -120.0, -20.0],
                "business_return": -120.0,
                "cost_return": -20.0,
                "feasible_rate": 1.0,
                "ever_critical_breach_rate": 1.0,
                "persistent_critical_breach_rate": 0.8,
                "mean_first_critical_hit_step": 10.0,
                "critical_hit_latency_score": 0.20,
                "mean_critical_dwell_steps": 12.0,
                "critical_host_safety_return": None,
                "critical_host_safety_cvar_alpha": None,
            }
        save_json(output_path, payload)
        return payload

    monkeypatch.setattr(v2_runner, "_run_constraint_eval", fake_run_constraint_eval)

    final_summary = v2_runner.run_v2_4obj_pilot(
        seed=11,
        stage1_config_path=stage1_template,
        stage2_config_path=stage2_template,
        thresholds_path="ignored.json",
        constraint_eval_episodes=8,
        replay_eval_episodes=20,
        method_name="ours_stage2_fair_critical_safe_v2_1_4obj",
        baseline_method_name="ours_stage2_fair",
        runner_dirname="fair_compare_critical_safe_v2_1_4obj_runner",
    )

    pilot_summary = json.loads(
        (tmp_path / "runner" / "seed_0011_pilot_summary.json").read_text(encoding="utf-8")
    )
    selection_diagnostics = json.loads(
        (tmp_path / "runner" / "seed_0011_selection_diagnostics.json").read_text(
            encoding="utf-8"
        )
    )
    assert final_summary["pilot_passed"] is False
    assert final_summary["failure_reasons"] == [
        "stage2_child_selected",
        "critical_dwell_ok",
        "business_guardrail_ok",
    ]
    assert pilot_summary["selected_policy_id"] == "stage1_pref_003_ckpt_191"
    assert pilot_summary["raw_selected_policy_id"] == "stage1_pref_003_ckpt_191"
    assert pilot_summary["selection_fallback_used"] is True
    assert (
        pilot_summary["selection_fallback_reason"]
        == v2_runner.SELECTION_FALLBACK_REASON_NO_STAGE2_CHILD_PASSED_GATE
    )
    assert pilot_summary["stage2_candidates_considered"] == ["stage2_ext_008_obj_1"]
    assert pilot_summary["stage2_gate_pass_policy_ids"] == []
    assert pilot_summary["stage2_gate_reject_reason_counts"] == {
        "persistent_critical_breach_ok": 1,
        "business_guardrail_ok": 1,
    }
    assert pilot_summary["parent_tail_metrics"] is None
    assert pilot_summary["child_tail_metrics"] is None
    assert (
        "critical_safe_balanced_selected__stage1_pref_003_ckpt_191"
        in pilot_summary["selected_audit_dir"]
    )
    assert selection_diagnostics["selection_fallback_used"] is True
