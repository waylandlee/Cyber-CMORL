from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import torch

import cmorl_cyborg.v2_2_4obj_pilot_runner as v2_2_runner
import cmorl_cyborg.v2_4obj_pilot_runner as v2_base
from cmorl_cyborg.config import load_stage1_config, load_stage2_config
from cmorl_cyborg.export_candidate_semantic_audit import export_candidate_semantic_audit
from cmorl_minicage.models.actor_critic import ActorCritic
from cmorl_minicage.shield import (
    SHIELD_LEVEL_CRITICAL,
    SHIELD_LEVEL_ENTERPRISE_ALERT,
    SHIELD_MODE_CRITICAL_PATH_HARD,
    build_shielded_action_mask,
)
from cmorl_minicage.utils import save_json


def test_v2_2_default_configs_enable_hard_shield() -> None:
    stage1_path = v2_2_runner.DEFAULT_STAGE1_CONFIG
    stage2_path = v2_2_runner.DEFAULT_STAGE2_CONFIG

    assert stage1_path.exists()
    assert stage2_path.exists()

    stage1 = load_stage1_config(stage1_path)
    stage2 = load_stage2_config(stage2_path)

    assert stage1.model.obj_dim == 4
    assert stage2.model.obj_dim == 4
    assert stage1.model.critical_host_safety_mode == "v2_1_dense_persistent"
    assert stage2.model.critical_host_safety_mode == "v2_1_dense_persistent"
    assert stage1.shield.mode == SHIELD_MODE_CRITICAL_PATH_HARD
    assert stage2.shield.mode == SHIELD_MODE_CRITICAL_PATH_HARD
    assert stage2.tail_acceptance.mode == "critical_tail"
    assert stage2.selection.semantic_thresholds_path.endswith("thresholds_tight.json")


def test_build_shielded_action_mask_prioritizes_critical_path_targets() -> None:
    native_mask = np.asarray([[1, 1, 1, 1, 1]], dtype=np.float32)
    action_catalog = [
        {
            "_shield_is_critical_path_target": False,
            "_shield_is_non_user_non_sleep": False,
            "_shield_is_enterprise_operational_non_sleep": False,
        },
        {
            "_shield_is_critical_path_target": True,
            "_shield_is_non_user_non_sleep": True,
            "_shield_is_enterprise_operational_non_sleep": True,
        },
        {
            "_shield_is_critical_path_target": False,
            "_shield_is_non_user_non_sleep": False,
            "_shield_is_enterprise_operational_non_sleep": False,
        },
        {
            "_shield_is_critical_path_target": True,
            "_shield_is_non_user_non_sleep": True,
            "_shield_is_enterprise_operational_non_sleep": True,
        },
        {
            "_shield_is_critical_path_target": False,
            "_shield_is_non_user_non_sleep": True,
            "_shield_is_enterprise_operational_non_sleep": True,
        },
    ]

    mask, diagnostics = build_shielded_action_mask(
        native_mask=native_mask,
        action_catalog=action_catalog,
        critical_present=np.asarray([1], dtype=np.int32),
        enterprise_foothold_present=np.asarray([0], dtype=np.int32),
    )

    assert mask.tolist() == [[0.0, 1.0, 0.0, 1.0, 0.0]]
    assert diagnostics["shield_active_flag"] == [1]
    assert diagnostics["shield_level"] == [SHIELD_LEVEL_CRITICAL]
    assert diagnostics["shield_fallback_flag"] == [0]
    assert diagnostics["shield_allowed_action_count"] == [2]


def test_build_shielded_action_mask_enterprise_alert_blocks_user_and_sleep() -> None:
    native_mask = np.asarray([[1, 1, 1, 1]], dtype=np.float32)
    action_catalog = [
        {
            "_shield_is_critical_path_target": False,
            "_shield_is_non_user_non_sleep": False,
            "_shield_is_enterprise_operational_non_sleep": False,
        },
        {
            "_shield_is_critical_path_target": False,
            "_shield_is_non_user_non_sleep": False,
            "_shield_is_enterprise_operational_non_sleep": False,
        },
        {
            "_shield_is_critical_path_target": False,
            "_shield_is_non_user_non_sleep": True,
            "_shield_is_enterprise_operational_non_sleep": True,
        },
        {
            "_shield_is_critical_path_target": False,
            "_shield_is_non_user_non_sleep": True,
            "_shield_is_enterprise_operational_non_sleep": True,
        },
    ]

    mask, diagnostics = build_shielded_action_mask(
        native_mask=native_mask,
        action_catalog=action_catalog,
        critical_present=np.asarray([0], dtype=np.int32),
        enterprise_foothold_present=np.asarray([1], dtype=np.int32),
    )

    assert mask.tolist() == [[0.0, 0.0, 1.0, 1.0]]
    assert diagnostics["shield_active_flag"] == [1]
    assert diagnostics["shield_level"] == [SHIELD_LEVEL_ENTERPRISE_ALERT]
    assert diagnostics["shield_fallback_flag"] == [0]
    assert diagnostics["shield_allowed_action_count"] == [2]


def test_build_shielded_action_mask_falls_back_to_native_when_filtered_empty() -> None:
    native_mask = np.asarray([[1, 0]], dtype=np.float32)
    action_catalog = [
        {
            "_shield_is_critical_path_target": False,
            "_shield_is_non_user_non_sleep": False,
            "_shield_is_enterprise_operational_non_sleep": False,
        },
        {
            "_shield_is_critical_path_target": False,
            "_shield_is_non_user_non_sleep": False,
            "_shield_is_enterprise_operational_non_sleep": False,
        },
    ]

    mask, diagnostics = build_shielded_action_mask(
        native_mask=native_mask,
        action_catalog=action_catalog,
        critical_present=np.asarray([1], dtype=np.int32),
        enterprise_foothold_present=np.asarray([0], dtype=np.int32),
    )

    assert mask.tolist() == native_mask.tolist()
    assert diagnostics["shield_active_flag"] == [1]
    assert diagnostics["shield_fallback_flag"] == [1]
    assert diagnostics["shield_allowed_action_count"] == [1]


def test_actor_critic_masked_sampling_matches_evaluate_actions() -> None:
    actor = ActorCritic(
        obs_dim=2,
        action_dim=4,
        obj_dim=4,
        hidden_sizes=(),
    )
    with torch.no_grad():
        actor.actor_head.weight.zero_()
        actor.actor_head.bias.copy_(torch.tensor([0.0, 2.0, 1.0, -1.0]))
        actor.critic_head.weight.zero_()
        actor.critic_head.bias.zero_()

    obs = torch.zeros((64, 2), dtype=torch.float32)
    action_mask = torch.tensor([[1.0, 0.0, 1.0, 0.0]], dtype=torch.float32).expand(
        64, -1
    )

    policy_output = actor.act(obs, action_mask=action_mask)
    values, log_probs, _ = actor.evaluate_actions(
        obs,
        policy_output.actions,
        action_mask=action_mask,
    )

    assert set(policy_output.actions.tolist()).issubset({0, 2})
    assert torch.allclose(log_probs, policy_output.log_probs)
    assert torch.allclose(values, policy_output.values)
    assert policy_output.allowed_action_count is not None
    assert torch.all(policy_output.allowed_action_count == 2)
    assert policy_output.blocked_probability_mass is not None

    base_probs = torch.softmax(torch.tensor([0.0, 2.0, 1.0, -1.0]), dim=-1)
    expected_blocked_mass = float(base_probs[1] + base_probs[3])
    assert float(policy_output.blocked_probability_mass[0]) == pytest.approx(
        expected_blocked_mass
    )


def test_export_candidate_semantic_audit_reports_rule_rates_and_shield_metrics(
    tmp_path: Path,
) -> None:
    trace_dir = tmp_path / "trace"
    trace_dir.mkdir()
    save_json(
        trace_dir / "trace_manifest.json",
        {
            "method_name": "ours_stage2_fair_critical_safe_v2_2_4obj",
            "seed": 11,
            "policy_id": "stage2_ext_001_obj_0",
            "candidate_label": "audit_shortlist",
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
                "num_trace_rows": 4,
                "env_summaries": [
                    {
                        "env_idx": 0,
                        "env_seed": 11,
                        "step_count": 4,
                        "return_vector": [8.0, -120.0, -20.0, -0.6],
                        "final_state": {
                            "compromised_hosts": ["Enterprise0", "Op_Server0"],
                            "critical_compromised_hosts": ["Op_Server0"],
                            "compromised_host_count": 2,
                        },
                    }
                ],
            }
        ],
    )

    rows = [
        {
            "episode_id": "episode_000",
            "env_idx": 0,
            "step_idx": 0,
            "blue_action": {
                "name": "Analyse",
                "target_hostname": "Enterprise0",
                "target_subnet": "Enterprise",
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
            "shield_active_flag": False,
            "shield_fallback_flag": False,
            "shield_blocked_probability_mass": 0.0,
        },
        {
            "episode_id": "episode_000",
            "env_idx": 0,
            "step_idx": 1,
            "blue_action": {
                "name": "Monitor",
                "target_hostname": None,
                "target_subnet": None,
            },
            "red_action": {
                "name": "Impact",
                "target_hostname": "Op_Server0",
                "target_subnet": "Operational",
            },
            "state_before": {
                "compromised_hosts": ["Enterprise0"],
                "critical_compromised_hosts": [],
                "compromised_host_count": 1,
            },
            "state_after": {
                "compromised_hosts": ["Enterprise0", "Op_Server0"],
                "critical_compromised_hosts": ["Op_Server0"],
                "compromised_host_count": 2,
            },
            "newly_compromised_hosts": ["Op_Server0"],
            "recovered_hosts": [],
            "shield_active_flag": True,
            "shield_fallback_flag": False,
            "shield_blocked_probability_mass": 0.4,
        },
        {
            "episode_id": "episode_000",
            "env_idx": 0,
            "step_idx": 2,
            "blue_action": {
                "name": "Analyse",
                "target_hostname": "User0",
                "target_subnet": "User",
            },
            "red_action": {
                "name": "Sleep",
                "target_hostname": None,
                "target_subnet": None,
            },
            "state_before": {
                "compromised_hosts": ["Enterprise0", "Op_Server0"],
                "critical_compromised_hosts": ["Op_Server0"],
                "compromised_host_count": 2,
            },
            "state_after": {
                "compromised_hosts": ["Enterprise0", "Op_Server0"],
                "critical_compromised_hosts": ["Op_Server0"],
                "compromised_host_count": 2,
            },
            "newly_compromised_hosts": [],
            "recovered_hosts": [],
            "shield_active_flag": True,
            "shield_fallback_flag": True,
            "shield_blocked_probability_mass": 0.2,
        },
        {
            "episode_id": "episode_000",
            "env_idx": 0,
            "step_idx": 3,
            "blue_action": {
                "name": "Monitor",
                "target_hostname": None,
                "target_subnet": None,
            },
            "red_action": {
                "name": "Sleep",
                "target_hostname": None,
                "target_subnet": None,
            },
            "state_before": {
                "compromised_hosts": ["Enterprise0", "Op_Server0"],
                "critical_compromised_hosts": ["Op_Server0"],
                "compromised_host_count": 2,
            },
            "state_after": {
                "compromised_hosts": ["Enterprise0", "Op_Server0"],
                "critical_compromised_hosts": ["Op_Server0"],
                "compromised_host_count": 2,
            },
            "newly_compromised_hosts": [],
            "recovered_hosts": [],
            "shield_active_flag": False,
            "shield_fallback_flag": False,
            "shield_blocked_probability_mass": 0.0,
        },
    ]
    (trace_dir / "episode_000.jsonl").write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )

    result = export_candidate_semantic_audit(
        trace_dir=trace_dir,
        output_dir=tmp_path / "audit",
    )
    summary = result["stage_a"]

    assert summary["questionable_rule_env_run_rates"][
        "Q2_user_action_during_critical_breach"
    ] == pytest.approx(1.0)
    assert summary["questionable_rule_env_run_rates"][
        "Q3_missed_immediate_response_to_critical_hit"
    ] == pytest.approx(1.0)
    assert summary["shield_active_step_rate"] == pytest.approx(0.5)
    assert summary["shield_fallback_step_rate"] == pytest.approx(0.25)
    assert summary["mean_shield_blocked_probability_mass"] == pytest.approx(0.15)


def test_finalize_v2_2_pilot_respects_overridden_method_metadata(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    runner_root = tmp_path / "runner"
    runner_root.mkdir()
    pilot_summary_path = runner_root / "seed_0011_pilot_summary.json"
    final_summary_path = runner_root / "seed_0011_final_summary.json"
    selected_constraint_metrics_path = (
        runner_root / "seed_0011_selected_constraint_metrics.json"
    )
    selection_diagnostics_path = runner_root / "seed_0011_selection_diagnostics.json"
    audit_selection_diagnostics_path = (
        runner_root / "seed_0011_audit_selection_diagnostics.json"
    )
    baseline_constraint_metrics_path = (
        runner_root / "seed_0011_baseline_constraint_metrics.json"
    )
    stage1_config = tmp_path / "stage1.yaml"
    stage2_config = tmp_path / "stage2.yaml"
    baseline_localized_buffer = tmp_path / "baseline_localized.json"
    stage1_config.write_text("stage1: true\n", encoding="utf-8")
    stage2_config.write_text("stage2: true\n", encoding="utf-8")

    method_calls: list[tuple[str, str]] = []
    replay_calls: list[tuple[str, str]] = []

    def fake_run_constraint_eval(**kwargs):
        method_calls.append((kwargs["selection_policy"], kwargs["method_name"]))
        if kwargs["selection_policy"] == "critical_safe_balanced":
            return {
                "selected_policy_id": "stage2_ext_099_obj_2",
                "selected_objective_vector": [-1.0, -2.0, -3.0, -4.0],
                "business_return": -61.0,
                "cost_return": -26.0,
                "mean_first_critical_hit_step": 60.0,
                "critical_hit_latency_score": 0.60,
                "selection_diagnostics": {
                    "evaluated_candidates": [
                        {
                            "policy_id": "stage2_ext_099_obj_2",
                            "objective_vector": [-1.0, -2.0, -3.0, -4.0],
                            "critical_host_safety_cvar_alpha": -3.5,
                        }
                    ]
                },
            }
        return {
            "selected_policy_id": "stage2_ext_016_obj_0",
            "selected_objective_vector": [-5.0, -6.0, -7.0, -8.0],
            "business_return": -120.0,
            "cost_return": -22.6,
            "mean_first_critical_hit_step": 20.75,
            "critical_hit_latency_score": 0.20,
        }

    def fake_export_replay_audit(**kwargs):
        replay_calls.append((kwargs["candidate"].candidate_label, kwargs["method_name"]))
        label = kwargs["candidate"].candidate_label
        summary = {
            "ever_critical_breach_rate": 0.5 if label != "objective_selected" else 1.0,
            "persistent_critical_breach_rate": 0.0 if label != "objective_selected" else 0.8,
            "mean_critical_dwell_steps": 2.0 if label != "objective_selected" else 67.0,
            "high_confidence_env_run_rate": 0.0 if label != "objective_selected" else 1.0,
            "questionable_rule_env_run_rates": {
                "Q2_user_action_during_critical_breach": (
                    0.0 if label != "objective_selected" else 1.0
                ),
                "Q3_missed_immediate_response_to_critical_hit": 0.0,
                "Q4_user_focus_after_enterprise_foothold": (
                    0.05 if label != "objective_selected" else 0.7
                ),
                "Q5_repeated_low_value_decoy_loop": (
                    0.1 if label != "objective_selected" else 0.2
                ),
            },
        }
        return {
            "trace_dir": str(tmp_path / f"{label}_trace"),
            "analysis_dir": str(tmp_path / f"{label}_analysis"),
            "summary_path": str(tmp_path / f"{label}_summary.json"),
            "summary": summary,
        }

    monkeypatch.setattr(v2_2_runner, "_runner_root", lambda: runner_root)
    monkeypatch.setattr(
        v2_2_runner,
        "_pilot_summary_path",
        lambda seed: pilot_summary_path,
    )
    monkeypatch.setattr(
        v2_2_runner,
        "_final_summary_path",
        lambda seed: final_summary_path,
    )
    monkeypatch.setattr(
        v2_2_runner,
        "_selected_constraint_metrics_output_path",
        lambda seed: selected_constraint_metrics_path,
    )
    monkeypatch.setattr(
        v2_2_runner,
        "_selection_diagnostics_output_path",
        lambda seed: selection_diagnostics_path,
    )
    monkeypatch.setattr(
        v2_2_runner,
        "_audit_selection_diagnostics_output_path",
        lambda seed: audit_selection_diagnostics_path,
    )
    monkeypatch.setattr(v2_2_runner.base, "_configure_experiment", lambda **kwargs: None)
    monkeypatch.setattr(
        v2_2_runner.base,
        "_resolve_existing_stage1_buffer",
        lambda seed, path: str(tmp_path / "stage1_buffer.json"),
    )
    monkeypatch.setattr(
        v2_2_runner.base,
        "_resolve_existing_stage2_buffer",
        lambda seed, path: str(tmp_path / "stage2_buffer.json"),
    )
    monkeypatch.setattr(
        v2_2_runner.base,
        "_materialize_stage1_config",
        lambda **kwargs: stage1_config,
    )
    monkeypatch.setattr(
        v2_2_runner.base,
        "_materialize_stage2_config",
        lambda **kwargs: stage2_config,
    )
    monkeypatch.setattr(
        v2_2_runner.base,
        "_load_yaml",
        lambda path: {
            "tail_acceptance": {
                "mode": "critical_tail",
                "tail_eval_episodes": 16,
                "tail_alpha": 0.25,
            }
        },
    )
    monkeypatch.setattr(v2_2_runner.base, "_run_constraint_eval", fake_run_constraint_eval)
    monkeypatch.setattr(
        v2_2_runner.base,
        "_record_lookup",
        lambda path: ({"metadata": {}}, {}),
    )
    monkeypatch.setattr(
        v2_2_runner.base,
        "_aggregate_tail_reject_reason_counts",
        lambda summaries: {},
    )
    monkeypatch.setattr(
        v2_2_runner.base,
        "_resolve_baseline_buffer",
        lambda seed: str(tmp_path / "baseline_buffer.json"),
    )
    monkeypatch.setattr(
        v2_2_runner.base,
        "_baseline_localized_buffer_output_path",
        lambda seed: baseline_localized_buffer,
    )
    monkeypatch.setattr(
        v2_2_runner.base,
        "_localize_buffer_for_eval",
        lambda buffer_path, output_path: str(output_path),
    )
    monkeypatch.setattr(
        v2_2_runner.base,
        "_baseline_constraint_metrics_output_path",
        lambda seed: baseline_constraint_metrics_path,
    )
    monkeypatch.setattr(
        v2_2_runner.base,
        "_resolve_record_for_replay",
        lambda *args, **kwargs: {
            "notes": {
                "tail_acceptance": {
                    "parent_tail_metrics": {"ever_critical_breach_rate": 0.8},
                    "child_tail_metrics": {"ever_critical_breach_rate": 0.5},
                }
            }
        },
    )
    monkeypatch.setattr(v2_2_runner.base, "_export_replay_audit", fake_export_replay_audit)
    monkeypatch.setattr(
        v2_2_runner.base,
        "_build_gate_selection_diagnostics",
        lambda **kwargs: {
            "raw_selection_policy": "critical_safe_balanced",
            "selected_policy_id": "stage2_ext_099_obj_2",
            "stage2_candidates_considered": ["stage2_ext_099_obj_2"],
            "stage2_gate_pass_policy_ids": ["stage2_ext_099_obj_2"],
            "stage2_gate_reject_reason_counts": {},
            "stage2_gate_results": [
                {
                    "policy_id": "stage2_ext_099_obj_2",
                    "objective_vector": [-1.0, -2.0, -3.0, -4.0],
                }
            ],
        },
    )
    monkeypatch.setattr(
        v2_2_runner.base,
        "_selected_entry_from_constraint_metrics",
        lambda metrics: {
            "policy_id": metrics["selected_policy_id"],
            "objective_vector": metrics["selected_objective_vector"],
        },
    )
    monkeypatch.setattr(
        v2_2_runner.base,
        "_materialize_selected_constraint_metrics",
        lambda **kwargs: {
            "selected_policy_id": "stage2_ext_099_obj_2",
            "selected_objective_vector": [-1.0, -2.0, -3.0, -4.0],
            "business_return": -61.0,
            "cost_return": -26.0,
            "mean_first_critical_hit_step": 60.0,
            "critical_hit_latency_score": 0.60,
            "critical_host_safety_return": -1.0,
            "critical_host_safety_cvar_alpha": -3.5,
        },
    )
    monkeypatch.setattr(
        v2_2_runner,
        "_audit_selection",
        lambda **kwargs: {
            "gate_selected_policy_id": "stage2_ext_099_obj_2",
            "final_selected_policy_id": "stage2_ext_099_obj_2",
            "audit_gate_passed": True,
            "audit_shortlist_policy_ids": ["stage2_ext_099_obj_2"],
            "audit_gate_pass_policy_ids": ["stage2_ext_099_obj_2"],
            "audit_gate_reject_reason_counts": {},
            "selected_short_audit_summary_path": str(
                tmp_path / "short_audit_summary.json"
            ),
        },
    )

    final_summary = v2_2_runner.finalize_v2_2_4obj_pilot(
        seed=11,
        stage1_config_path=stage1_config,
        stage2_config_path=stage2_config,
        method_name="ours_stage2_fair_critical_safe_v2_3_4obj",
        baseline_method_name="ours_stage2_fair_custom",
        runner_dirname="fair_compare_critical_safe_v2_3_4obj_runner",
    )

    assert final_summary["method_name"] == "ours_stage2_fair_critical_safe_v2_3_4obj"
    assert final_summary["baseline_method_name"] == "ours_stage2_fair_custom"
    assert final_summary["runner_dirname"] == "fair_compare_critical_safe_v2_3_4obj_runner"

    pilot_summary = json.loads(pilot_summary_path.read_text(encoding="utf-8"))
    assert pilot_summary["method_name"] == "ours_stage2_fair_critical_safe_v2_3_4obj"
    assert pilot_summary["baseline_method_name"] == "ours_stage2_fair_custom"
    assert pilot_summary["runner_dirname"] == "fair_compare_critical_safe_v2_3_4obj_runner"

    assert ("critical_safe_balanced", "ours_stage2_fair_critical_safe_v2_3_4obj") in method_calls
    assert ("objective", "ours_stage2_fair_custom_objective_baseline") in method_calls
    assert ("audit_selected", "ours_stage2_fair_critical_safe_v2_3_4obj") in replay_calls
    assert ("objective_selected", "ours_stage2_fair_custom") in replay_calls


def test_run_v2_2_pilot_propagates_overridden_metadata_to_finalize(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    captured: dict[str, object] = {}

    monkeypatch.setattr(v2_2_runner.base, "_configure_experiment", lambda **kwargs: None)
    monkeypatch.setattr(v2_2_runner, "_runner_root", lambda: tmp_path / "runner")
    monkeypatch.setattr(
        v2_2_runner.base,
        "_materialize_stage1_config",
        lambda **kwargs: tmp_path / "stage1.yaml",
    )
    monkeypatch.setattr(
        v2_2_runner.base,
        "_materialize_stage2_config",
        lambda **kwargs: tmp_path / "stage2.yaml",
    )
    monkeypatch.setattr(
        v2_2_runner,
        "train_stage1",
        lambda cfg: str(tmp_path / "stage1_buffer.json"),
    )
    monkeypatch.setattr(
        v2_2_runner,
        "train_stage2",
        lambda cfg: str(tmp_path / "stage2_buffer.json"),
    )
    monkeypatch.setattr(v2_2_runner, "load_stage1_config", lambda path: object())
    monkeypatch.setattr(v2_2_runner, "load_stage2_config", lambda path: object())

    def fake_finalize(**kwargs):
        captured.update(kwargs)
        return {"ok": True}

    monkeypatch.setattr(v2_2_runner, "finalize_v2_2_4obj_pilot", fake_finalize)

    summary = v2_2_runner.run_v2_2_4obj_pilot(
        seed=11,
        method_name="ours_stage2_fair_critical_safe_v2_4_4obj",
        baseline_method_name="ours_stage2_fair",
        runner_dirname="fair_compare_critical_safe_v2_4_4obj_runner",
    )

    assert summary == {"ok": True}
    assert captured["method_name"] == "ours_stage2_fair_critical_safe_v2_4_4obj"
    assert captured["baseline_method_name"] == "ours_stage2_fair"
    assert captured["runner_dirname"] == "fair_compare_critical_safe_v2_4_4obj_runner"


def test_audit_selection_prefers_lower_q2_and_high_confidence(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    stage2_buffer = tmp_path / "stage2_buffer.json"
    stage2_buffer.write_text("{}", encoding="utf-8")
    stage2_payload = {"metadata": {"env": {"seed": 11}, "shield": {"mode": "critical_path_hard"}}}
    stage2_records = {
        "stage1_pref_000": {
            "policy_id": "stage1_pref_000",
            "checkpoint_path": "dummy.pt",
            "objective_vector": [9.4, -128.0, -20.5, -0.7],
        },
        "stage2_ext_001": {
            "policy_id": "stage2_ext_001",
            "checkpoint_path": "dummy.pt",
            "objective_vector": [9.8, -119.0, -20.4, -0.5],
        },
        "stage2_ext_002": {
            "policy_id": "stage2_ext_002",
            "checkpoint_path": "dummy.pt",
            "objective_vector": [9.7, -119.5, -20.3, -0.45],
        },
    }
    raw_selected_entry = {
        "policy_id": "stage1_pref_000",
        "objective_vector": [9.4, -128.0, -20.5, -0.7],
    }
    gate_selection_diagnostics = {
        "selected_policy_id": "stage2_ext_001",
        "stage2_gate_pass_policy_ids": ["stage2_ext_001", "stage2_ext_002"],
        "stage2_gate_results": [
            {"policy_id": "stage2_ext_001"},
            {"policy_id": "stage2_ext_002"},
        ],
        "raw_selection_diagnostics": {
            "evaluated_candidates": [
                {
                    "policy_id": "stage1_pref_000",
                    "objective_vector": [9.4, -128.0, -20.5, -0.7],
                    "business_return": -128.0,
                    "cost_return": -20.5,
                    "mean_violation": 8.0,
                    "ever_critical_breach_rate": 0.75,
                    "persistent_critical_breach_rate": 0.65,
                    "mean_first_critical_hit_step": 38.0,
                    "critical_hit_latency_score": 0.36,
                    "mean_critical_dwell_steps": 20.0,
                    "critical_host_safety_return": -0.70,
                    "critical_host_safety_cvar_alpha": -0.90,
                },
                {
                    "policy_id": "stage2_ext_001",
                    "objective_vector": [9.8, -119.0, -20.4, -0.5],
                    "business_return": -119.0,
                    "cost_return": -20.4,
                    "mean_violation": 2.0,
                    "ever_critical_breach_rate": 0.75,
                    "persistent_critical_breach_rate": 0.55,
                    "mean_first_critical_hit_step": 26.0,
                    "critical_hit_latency_score": 0.42,
                    "mean_critical_dwell_steps": 9.0,
                    "critical_host_safety_return": -0.50,
                    "critical_host_safety_cvar_alpha": -0.45,
                },
                {
                    "policy_id": "stage2_ext_002",
                    "objective_vector": [9.7, -119.5, -20.3, -0.45],
                    "business_return": -119.5,
                    "cost_return": -20.3,
                    "mean_violation": 2.0,
                    "ever_critical_breach_rate": 0.75,
                    "persistent_critical_breach_rate": 0.55,
                    "mean_first_critical_hit_step": 27.0,
                    "critical_hit_latency_score": 0.41,
                    "mean_critical_dwell_steps": 9.0,
                    "critical_host_safety_return": -0.45,
                    "critical_host_safety_cvar_alpha": -0.40,
                },
            ]
        },
    }
    baseline_constraint_metrics = {
        "business_return": -120.0,
        "cost_return": -20.0,
        "mean_first_critical_hit_step": 10.0,
        "critical_hit_latency_score": 0.20,
        "critical_host_safety_return": -0.80,
        "critical_host_safety_cvar_alpha": -0.95,
        "selected_policy_id": "base_3d",
    }
    baseline_trace = {
        "summary": {
            "ever_critical_breach_rate": 0.80,
            "persistent_critical_breach_rate": 0.60,
            "mean_critical_dwell_steps": 16.0,
            "high_confidence_env_run_rate": 0.50,
            "questionable_rule_env_run_rates": {
                "Q2_user_action_during_critical_breach": 0.40,
                "Q3_missed_immediate_response_to_critical_hit": 0.20,
                "Q4_user_focus_after_enterprise_foothold": 0.30,
                "Q5_repeated_low_value_decoy_loop": 0.20,
            },
        }
    }
    short_audit_summaries = {
        "stage2_ext_001": {
            "ever_critical_breach_rate": 0.75,
            "persistent_critical_breach_rate": 0.50,
            "mean_critical_dwell_steps": 8.0,
            "high_confidence_env_run_rate": 0.30,
            "questionable_rule_env_run_rates": {
                "Q2_user_action_during_critical_breach": 0.25,
                "Q3_missed_immediate_response_to_critical_hit": 0.15,
                "Q4_user_focus_after_enterprise_foothold": 0.20,
                "Q5_repeated_low_value_decoy_loop": 0.10,
            },
        },
        "stage2_ext_002": {
            "ever_critical_breach_rate": 0.75,
            "persistent_critical_breach_rate": 0.50,
            "mean_critical_dwell_steps": 8.0,
            "high_confidence_env_run_rate": 0.20,
            "questionable_rule_env_run_rates": {
                "Q2_user_action_during_critical_breach": 0.15,
                "Q3_missed_immediate_response_to_critical_hit": 0.15,
                "Q4_user_focus_after_enterprise_foothold": 0.20,
                "Q5_repeated_low_value_decoy_loop": 0.10,
            },
        },
    }

    def fake_export_replay_audit(**kwargs):
        policy_id = str(kwargs["candidate"].policy_id)
        return {
            "trace_dir": str((tmp_path / "trace" / policy_id).resolve()),
            "analysis_dir": str((tmp_path / "audit" / policy_id).resolve()),
            "summary_path": str((tmp_path / "audit" / policy_id / "risk_tier_summary.json").resolve()),
            "summary": dict(short_audit_summaries[policy_id]),
        }

    monkeypatch.setattr(v2_base, "_export_replay_audit", fake_export_replay_audit)

    diagnostics = v2_2_runner._audit_selection(
        seed=11,
        method_name="ours_stage2_fair_critical_safe_v2_2_4obj",
        stage2_buffer_path=stage2_buffer,
        stage2_payload=stage2_payload,
        stage2_records=stage2_records,
        raw_selected_entry=raw_selected_entry,
        gate_selection_diagnostics=gate_selection_diagnostics,
        baseline_constraint_metrics=baseline_constraint_metrics,
        baseline_trace=baseline_trace,
        shortlist_k=3,
        audit_eval_episodes=10,
    )

    assert diagnostics["gate_selected_policy_id"] == "stage2_ext_001"
    assert diagnostics["final_selected_policy_id"] == "stage2_ext_002"
    assert set(diagnostics["audit_gate_pass_policy_ids"]) == {
        "stage2_ext_001",
        "stage2_ext_002",
    }
    assert diagnostics["selection_fallback_reason"] is None
    assert diagnostics["selected_short_audit_summary_path"].endswith(
        "stage2_ext_002/risk_tier_summary.json"
    )


def test_finalize_v2_2_4obj_pilot_falls_back_when_no_audited_child_passes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    stage1_template = tmp_path / "stage1.yaml"
    stage2_template = tmp_path / "stage2.yaml"
    stage1_template.write_text(
        "model:\n"
        "  obj_dim: 4\n"
        "  critical_host_safety_mode: v2_1_dense_persistent\n"
        "shield:\n"
        "  mode: critical_path_hard\n",
        encoding="utf-8",
    )
    stage2_template.write_text(
        "model:\n"
        "  obj_dim: 4\n"
        "  critical_host_safety_mode: v2_1_dense_persistent\n"
        "shield:\n"
        "  mode: critical_path_hard\n"
        "tail_acceptance:\n"
        "  mode: critical_tail\n"
        "  tail_eval_episodes: 16\n"
        "  tail_alpha: 0.25\n",
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
            "metadata": {
                "env": {"seed": 11},
                "model": {"obj_dim": 4, "hidden_size": 8},
                "round_summaries": [
                    {"tail_reject_reason_counts": {"persistent_non_regression": 1}}
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
                                "persistent_critical_breach_rate": 0.6,
                                "mean_critical_dwell_steps": 7.0,
                            },
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
                    "policy_id": "stage2_ext_006_obj_0",
                    "checkpoint_path": "dummy.pt",
                    "objective_vector": [10.0, -121.0, -21.0, -0.55],
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

    monkeypatch.setattr(v2_base, "_runner_root", lambda: tmp_path / "runner")
    monkeypatch.setattr(
        v2_base,
        "_selected_constraint_metrics_path",
        lambda seed: tmp_path / f"raw_selected_constraint_metrics_seed_{seed:04d}.json",
    )
    monkeypatch.setattr(
        v2_base,
        "_baseline_constraint_metrics_output_path",
        lambda seed: tmp_path / f"baseline_constraint_metrics_seed_{seed:04d}.json",
    )
    monkeypatch.setattr(
        v2_base,
        "_baseline_localized_buffer_output_path",
        lambda seed: tmp_path / f"baseline_buffer_localized_seed_{seed:04d}.json",
    )
    monkeypatch.setattr(v2_base, "_resolve_baseline_buffer", lambda seed: baseline_buffer)
    monkeypatch.setattr(
        v2_base,
        "_localize_buffer_for_eval",
        lambda *, buffer_path, output_path: Path(buffer_path),
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
                            "ever_critical_breach_rate": 0.80,
                            "persistent_critical_breach_rate": 0.60,
                            "mean_first_critical_hit_step": 25.0,
                            "critical_hit_latency_score": 0.36,
                            "mean_critical_dwell_steps": 7.0,
                            "user_action_during_critical_breach_rate": 0.05,
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
                "ever_critical_breach_rate": 0.85,
                "persistent_critical_breach_rate": 0.60,
                "mean_first_critical_hit_step": 10.0,
                "critical_hit_latency_score": 0.20,
                "mean_critical_dwell_steps": 14.0,
                "critical_host_safety_return": None,
                "critical_host_safety_cvar_alpha": None,
            }
        save_json(output_path, payload)
        return payload

    audit_summaries = {
        ("baseline", "base_3d"): {
            "ever_critical_breach_rate": 0.85,
            "persistent_critical_breach_rate": 0.60,
            "mean_critical_dwell_steps": 14.0,
            "high_confidence_env_run_rate": 0.50,
            "questionable_rule_env_run_rates": {
                "Q2_user_action_during_critical_breach": 0.30,
                "Q3_missed_immediate_response_to_critical_hit": 0.10,
                "Q4_user_focus_after_enterprise_foothold": 0.20,
                "Q5_repeated_low_value_decoy_loop": 0.10,
            },
        },
        ("audit_shortlist", "stage2_ext_006_obj_0"): {
            "ever_critical_breach_rate": 0.80,
            "persistent_critical_breach_rate": 0.65,
            "mean_critical_dwell_steps": 11.0,
            "high_confidence_env_run_rate": 0.55,
            "questionable_rule_env_run_rates": {
                "Q2_user_action_during_critical_breach": 0.25,
                "Q3_missed_immediate_response_to_critical_hit": 0.15,
                "Q4_user_focus_after_enterprise_foothold": 0.20,
                "Q5_repeated_low_value_decoy_loop": 0.10,
            },
        },
        ("pilot", "stage2_ext_006_obj_0"): {
            "ever_critical_breach_rate": 0.80,
            "persistent_critical_breach_rate": 0.65,
            "mean_critical_dwell_steps": 11.0,
            "high_confidence_env_run_rate": 0.55,
            "questionable_rule_env_run_rates": {
                "Q2_user_action_during_critical_breach": 0.25,
                "Q3_missed_immediate_response_to_critical_hit": 0.15,
                "Q4_user_focus_after_enterprise_foothold": 0.20,
                "Q5_repeated_low_value_decoy_loop": 0.10,
            },
        },
    }

    def fake_export_replay_audit(**kwargs):
        policy_id = str(kwargs["candidate"].policy_id)
        analysis_kind = str(kwargs["analysis_kind"])
        summary = dict(audit_summaries[(analysis_kind, policy_id)])
        label = f"{kwargs['candidate'].candidate_label}__{policy_id}"
        return {
            "trace_dir": str((tmp_path / "trace" / label).resolve()),
            "analysis_dir": str((tmp_path / "audit" / label).resolve()),
            "summary_path": str(
                (tmp_path / "audit" / label / "risk_tier_summary.json").resolve()
            ),
            "summary": summary,
        }

    monkeypatch.setattr(v2_base, "_run_constraint_eval", fake_run_constraint_eval)
    monkeypatch.setattr(v2_base, "_export_replay_audit", fake_export_replay_audit)

    final_summary = v2_2_runner.finalize_v2_2_4obj_pilot(
        seed=11,
        stage1_config_path=stage1_template,
        stage2_config_path=stage2_template,
        stage1_buffer_path=stage1_buffer,
        stage2_buffer_path=stage2_buffer,
        thresholds_path="ignored.json",
        constraint_eval_episodes=8,
        replay_eval_episodes=20,
        audit_eval_episodes=10,
        audit_shortlist_k=3,
    )

    pilot_summary = json.loads(
        (tmp_path / "runner" / "seed_0011_pilot_summary.json").read_text(
            encoding="utf-8"
        )
    )
    audit_selection = json.loads(
        (tmp_path / "runner" / "seed_0011_audit_selection_diagnostics.json").read_text(
            encoding="utf-8"
        )
    )
    selected_metrics = json.loads(
        (tmp_path / "runner" / "seed_0011_selected_constraint_metrics.json").read_text(
            encoding="utf-8"
        )
    )

    assert final_summary["selected_policy_id"] == "stage2_ext_006_obj_0"
    assert final_summary["selection_fallback_used"] is True
    assert (
        final_summary["selection_fallback_reason"]
        == v2_2_runner.SELECTION_FALLBACK_REASON_NO_CANDIDATE_PASSED_AUDIT_GATE
    )
    assert final_summary["pilot_passed"] is False
    assert "audit_gate_passed" in final_summary["failure_reasons"]

    assert pilot_summary["selection_mode"] == v2_2_runner.SELECTION_MODE_STAGE2_GATE_AUDIT_SHIELDED
    assert pilot_summary["raw_selected_policy_id"] == "stage1_pref_003_ckpt_191"
    assert pilot_summary["gate_selected_policy_id"] == "stage2_ext_006_obj_0"
    assert pilot_summary["final_selected_policy_id"] == "stage2_ext_006_obj_0"
    assert pilot_summary["audit_shortlist_policy_ids"] == ["stage2_ext_006_obj_0"]
    assert pilot_summary["audit_gate_pass_policy_ids"] == []
    assert (
        pilot_summary["selection_fallback_reason"]
        == v2_2_runner.SELECTION_FALLBACK_REASON_NO_CANDIDATE_PASSED_AUDIT_GATE
    )

    assert audit_selection["gate_selected_policy_id"] == "stage2_ext_006_obj_0"
    assert audit_selection["final_selected_policy_id"] == "stage2_ext_006_obj_0"
    assert (
        audit_selection["selection_fallback_reason"]
        == v2_2_runner.SELECTION_FALLBACK_REASON_NO_CANDIDATE_PASSED_AUDIT_GATE
    )
    assert audit_selection["audit_gate_pass_policy_ids"] == []

    assert selected_metrics["selection_policy"] == v2_2_runner.SELECTION_MODE_STAGE2_GATE_AUDIT_SHIELDED
