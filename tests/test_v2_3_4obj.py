from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

import cmorl_cyborg.v2_2_4obj_pilot_runner as v2_2_runner
import cmorl_cyborg.v2_3_4obj_pilot_runner as v2_3_runner
from cmorl_cyborg.config import load_stage1_config, load_stage2_config
from cmorl_cyborg.export_candidate_semantic_audit import export_candidate_semantic_audit
from cmorl_minicage.shield import (
    ACTION_FAMILY_ANALYSE,
    ACTION_FAMILY_DECOY,
    ACTION_FAMILY_REMOVE,
    ACTION_FAMILY_RESTORE,
    SHIELD_LEVEL_CRITICAL,
    SHIELD_LEVEL_ENTERPRISE_ALERT,
    SHIELD_MODE_CRITICAL_RECOVERY_PRIORITY,
    SHIELD_RESPONSE_TIER_CRITICAL_REMOVE_ON_ENTERPRISE_OPERATIONAL,
    SHIELD_RESPONSE_TIER_CRITICAL_RESTORE_ON_CRITICAL,
    SHIELD_RESPONSE_TIER_ENTERPRISE_ALERT,
    SHIELD_RESPONSE_TIER_FALLBACK_NATIVE,
    build_shielded_action_mask,
)
from cmorl_minicage.utils import save_json


def test_v2_3_default_configs_enable_recovery_priority_shield() -> None:
    stage1 = load_stage1_config(v2_3_runner.DEFAULT_STAGE1_CONFIG)
    stage2 = load_stage2_config(v2_3_runner.DEFAULT_STAGE2_CONFIG)

    assert stage1.model.obj_dim == 4
    assert stage2.model.obj_dim == 4
    assert stage1.model.critical_host_safety_mode == "v2_1_dense_persistent"
    assert stage2.model.critical_host_safety_mode == "v2_1_dense_persistent"
    assert stage1.shield.mode == SHIELD_MODE_CRITICAL_RECOVERY_PRIORITY
    assert stage2.shield.mode == SHIELD_MODE_CRITICAL_RECOVERY_PRIORITY
    assert stage2.tail_acceptance.mode == "critical_tail"


def test_recovery_priority_shield_prefers_restore_on_critical_target() -> None:
    native_mask = np.asarray([[1, 1, 1, 1, 1]], dtype=np.float32)
    action_catalog = [
        {
            "_shield_action_family": ACTION_FAMILY_DECOY,
            "_shield_is_critical_path_target": False,
            "_shield_is_non_user_non_sleep": False,
            "_shield_is_enterprise_operational_non_sleep": False,
        },
        {
            "_shield_action_family": ACTION_FAMILY_RESTORE,
            "_shield_is_critical_path_target": True,
            "_shield_is_non_user_non_sleep": True,
            "_shield_is_enterprise_operational_non_sleep": True,
        },
        {
            "_shield_action_family": ACTION_FAMILY_REMOVE,
            "_shield_is_critical_path_target": True,
            "_shield_is_non_user_non_sleep": True,
            "_shield_is_enterprise_operational_non_sleep": True,
        },
        {
            "_shield_action_family": ACTION_FAMILY_ANALYSE,
            "_shield_is_critical_path_target": True,
            "_shield_is_non_user_non_sleep": True,
            "_shield_is_enterprise_operational_non_sleep": True,
        },
        {
            "_shield_action_family": ACTION_FAMILY_DECOY,
            "_shield_is_critical_path_target": True,
            "_shield_is_non_user_non_sleep": True,
            "_shield_is_enterprise_operational_non_sleep": True,
        },
    ]

    mask, diagnostics = build_shielded_action_mask(
        native_mask=native_mask,
        action_catalog=action_catalog,
        critical_present=np.asarray([1], dtype=np.int32),
        enterprise_foothold_present=np.asarray([0], dtype=np.int32),
        mode=SHIELD_MODE_CRITICAL_RECOVERY_PRIORITY,
        critical_compromised_target_mask=np.asarray([[0, 1, 1, 1, 1]], dtype=np.int32),
        enterprise_operational_compromised_target_mask=np.asarray(
            [[0, 1, 1, 1, 1]],
            dtype=np.int32,
        ),
    )

    assert mask.tolist() == [[0.0, 1.0, 0.0, 0.0, 0.0]]
    assert diagnostics["shield_active_flag"] == [1]
    assert diagnostics["shield_level"] == [SHIELD_LEVEL_CRITICAL]
    assert diagnostics["shield_response_tier"] == [
        SHIELD_RESPONSE_TIER_CRITICAL_RESTORE_ON_CRITICAL
    ]


def test_recovery_priority_shield_uses_enterprise_operational_tier_when_critical_host_not_actionable() -> None:
    native_mask = np.asarray([[1, 1, 1, 1]], dtype=np.float32)
    action_catalog = [
        {
            "_shield_action_family": ACTION_FAMILY_DECOY,
            "_shield_is_critical_path_target": False,
            "_shield_is_non_user_non_sleep": False,
            "_shield_is_enterprise_operational_non_sleep": False,
        },
        {
            "_shield_action_family": ACTION_FAMILY_REMOVE,
            "_shield_is_critical_path_target": False,
            "_shield_is_non_user_non_sleep": True,
            "_shield_is_enterprise_operational_non_sleep": True,
        },
        {
            "_shield_action_family": ACTION_FAMILY_ANALYSE,
            "_shield_is_critical_path_target": False,
            "_shield_is_non_user_non_sleep": True,
            "_shield_is_enterprise_operational_non_sleep": True,
        },
        {
            "_shield_action_family": ACTION_FAMILY_DECOY,
            "_shield_is_critical_path_target": True,
            "_shield_is_non_user_non_sleep": True,
            "_shield_is_enterprise_operational_non_sleep": True,
        },
    ]

    mask, diagnostics = build_shielded_action_mask(
        native_mask=native_mask,
        action_catalog=action_catalog,
        critical_present=np.asarray([1], dtype=np.int32),
        enterprise_foothold_present=np.asarray([0], dtype=np.int32),
        mode=SHIELD_MODE_CRITICAL_RECOVERY_PRIORITY,
        critical_compromised_target_mask=np.asarray([[0, 0, 0, 0]], dtype=np.int32),
        enterprise_operational_compromised_target_mask=np.asarray(
            [[0, 1, 1, 0]],
            dtype=np.int32,
        ),
    )

    assert mask.tolist() == [[0.0, 1.0, 0.0, 0.0]]
    assert diagnostics["shield_response_tier"] == [
        SHIELD_RESPONSE_TIER_CRITICAL_REMOVE_ON_ENTERPRISE_OPERATIONAL
    ]


def test_recovery_priority_shield_keeps_enterprise_alert_behavior() -> None:
    native_mask = np.asarray([[1, 1, 1, 1]], dtype=np.float32)
    action_catalog = [
        {
            "_shield_action_family": "sleep",
            "_shield_is_critical_path_target": False,
            "_shield_is_non_user_non_sleep": False,
            "_shield_is_enterprise_operational_non_sleep": False,
        },
        {
            "_shield_action_family": ACTION_FAMILY_ANALYSE,
            "_shield_is_critical_path_target": False,
            "_shield_is_non_user_non_sleep": False,
            "_shield_is_enterprise_operational_non_sleep": False,
        },
        {
            "_shield_action_family": ACTION_FAMILY_REMOVE,
            "_shield_is_critical_path_target": False,
            "_shield_is_non_user_non_sleep": True,
            "_shield_is_enterprise_operational_non_sleep": True,
        },
        {
            "_shield_action_family": ACTION_FAMILY_DECOY,
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
        mode=SHIELD_MODE_CRITICAL_RECOVERY_PRIORITY,
    )

    assert mask.tolist() == [[0.0, 0.0, 1.0, 1.0]]
    assert diagnostics["shield_level"] == [SHIELD_LEVEL_ENTERPRISE_ALERT]
    assert diagnostics["shield_response_tier"] == [SHIELD_RESPONSE_TIER_ENTERPRISE_ALERT]


def test_recovery_priority_shield_falls_back_to_native_with_response_tier() -> None:
    native_mask = np.asarray([[1, 0]], dtype=np.float32)
    action_catalog = [
        {
            "_shield_action_family": ACTION_FAMILY_DECOY,
            "_shield_is_critical_path_target": False,
            "_shield_is_non_user_non_sleep": False,
            "_shield_is_enterprise_operational_non_sleep": False,
        },
        {
            "_shield_action_family": ACTION_FAMILY_RESTORE,
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
        mode=SHIELD_MODE_CRITICAL_RECOVERY_PRIORITY,
        critical_compromised_target_mask=np.asarray([[0, 0]], dtype=np.int32),
        enterprise_operational_compromised_target_mask=np.asarray(
            [[0, 0]],
            dtype=np.int32,
        ),
    )

    assert mask.tolist() == native_mask.tolist()
    assert diagnostics["shield_fallback_flag"] == [1]
    assert diagnostics["shield_response_tier"] == [SHIELD_RESPONSE_TIER_FALLBACK_NATIVE]


def test_export_candidate_semantic_audit_reports_critical_action_family_rates(
    tmp_path: Path,
) -> None:
    trace_dir = tmp_path / "trace"
    trace_dir.mkdir()
    save_json(
        trace_dir / "trace_manifest.json",
        {
            "method_name": "ours_stage2_fair_critical_safe_v2_3_4obj",
            "seed": 11,
            "policy_id": "stage2_ext_018_obj_3",
            "candidate_label": "audit_selected",
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
            "blue_action": {"name": "Analyse", "target_hostname": "Enterprise0", "target_subnet": "Enterprise"},
            "red_action": {"name": "DiscoverRemoteSystems", "target_hostname": None, "target_subnet": "Enterprise"},
            "state_before": {"compromised_hosts": [], "critical_compromised_hosts": [], "compromised_host_count": 0},
            "state_after": {"compromised_hosts": ["Enterprise0"], "critical_compromised_hosts": [], "compromised_host_count": 1},
            "newly_compromised_hosts": ["Enterprise0"],
            "recovered_hosts": [],
            "semantic_info": {"critical_present": 0.0},
            "shield_active_flag": False,
            "shield_fallback_flag": False,
            "shield_blocked_probability_mass": 0.0,
        },
        {
            "episode_id": "episode_000",
            "env_idx": 0,
            "step_idx": 1,
            "blue_action": {"name": "Restore", "target_hostname": "Op_Server0", "target_subnet": "Operational"},
            "red_action": {"name": "Impact", "target_hostname": "Op_Server0", "target_subnet": "Operational"},
            "state_before": {"compromised_hosts": ["Enterprise0"], "critical_compromised_hosts": [], "compromised_host_count": 1},
            "state_after": {"compromised_hosts": ["Enterprise0", "Op_Server0"], "critical_compromised_hosts": ["Op_Server0"], "compromised_host_count": 2},
            "newly_compromised_hosts": ["Op_Server0"],
            "recovered_hosts": [],
            "semantic_info": {"critical_present": 1.0},
            "shield_active_flag": True,
            "shield_fallback_flag": False,
            "shield_blocked_probability_mass": 0.2,
        },
        {
            "episode_id": "episode_000",
            "env_idx": 0,
            "step_idx": 2,
            "blue_action": {"name": "DecoyApache", "target_hostname": "Op_Server0", "target_subnet": "Operational"},
            "red_action": {"name": "Sleep", "target_hostname": None, "target_subnet": None},
            "state_before": {"compromised_hosts": ["Enterprise0", "Op_Server0"], "critical_compromised_hosts": ["Op_Server0"], "compromised_host_count": 2},
            "state_after": {"compromised_hosts": ["Enterprise0", "Op_Server0"], "critical_compromised_hosts": ["Op_Server0"], "compromised_host_count": 2},
            "newly_compromised_hosts": [],
            "recovered_hosts": [],
            "semantic_info": {"critical_present": 1.0},
            "shield_active_flag": True,
            "shield_fallback_flag": False,
            "shield_blocked_probability_mass": 0.3,
        },
        {
            "episode_id": "episode_000",
            "env_idx": 0,
            "step_idx": 3,
            "blue_action": {"name": "Remove", "target_hostname": "Enterprise0", "target_subnet": "Enterprise"},
            "red_action": {"name": "Sleep", "target_hostname": None, "target_subnet": None},
            "state_before": {"compromised_hosts": ["Enterprise0", "Op_Server0"], "critical_compromised_hosts": ["Op_Server0"], "compromised_host_count": 2},
            "state_after": {"compromised_hosts": ["Op_Server0"], "critical_compromised_hosts": ["Op_Server0"], "compromised_host_count": 1},
            "newly_compromised_hosts": [],
            "recovered_hosts": ["Enterprise0"],
            "semantic_info": {"critical_present": 1.0},
            "shield_active_flag": True,
            "shield_fallback_flag": False,
            "shield_blocked_probability_mass": 0.4,
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

    assert summary["critical_action_family_step_rates"]["restore"] == pytest.approx(1.0 / 3.0)
    assert summary["critical_action_family_step_rates"]["remove"] == pytest.approx(1.0 / 3.0)
    assert summary["critical_action_family_step_rates"]["decoy"] == pytest.approx(1.0 / 3.0)
    assert summary["critical_action_family_env_run_rates"]["restore"] == pytest.approx(1.0)
    assert summary["critical_action_family_env_run_rates"]["remove"] == pytest.approx(1.0)
    assert summary["critical_action_family_env_run_rates"]["decoy"] == pytest.approx(1.0)
    casebook = (tmp_path / "audit" / "critical_casebook.md").read_text(encoding="utf-8")
    assert "Critical-step top action families" in casebook
    assert "Critical-step recovery counts" in casebook
    assert "Critical-step no-recovery top actions" in casebook


def test_finalize_v2_3_pilot_augments_saved_summaries_with_mechanism_verification(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    runner_root = tmp_path / "runner"
    runner_root.mkdir()
    selected_risk_summary = tmp_path / "selected_risk_summary.json"
    save_json(
        selected_risk_summary,
        {
            "critical_action_family_step_rates": {
                "restore": 0.20,
                "remove": 0.25,
                "analyse": 0.05,
                "decoy": 0.30,
                "other": 0.20,
            },
            "critical_action_family_env_run_rates": {
                "restore": 0.50,
                "remove": 0.55,
                "analyse": 0.10,
                "decoy": 0.60,
                "other": 0.30,
            },
        },
    )
    reference_risk_summary = tmp_path / "reference_risk_summary.json"
    save_json(
        reference_risk_summary,
        {
            "critical_action_family_step_rates": {
                "restore": 0.05,
                "remove": 0.10,
                "analyse": 0.05,
                "decoy": 0.60,
                "other": 0.20,
            },
            "critical_action_family_env_run_rates": {
                "restore": 0.20,
                "remove": 0.25,
                "analyse": 0.10,
                "decoy": 0.90,
                "other": 0.30,
            },
        },
    )
    reference_final_summary = tmp_path / "reference_final_summary.json"
    save_json(
        reference_final_summary,
        {
            "selected_policy_id": "stage2_ext_018_obj_3",
            "selected_risk_summary_path": str(reference_risk_summary),
        },
    )
    pilot_summary_path = runner_root / "seed_0011_pilot_summary.json"
    final_summary_path = runner_root / "seed_0011_final_summary.json"
    base_summary = {
        "selected_policy_id": "stage2_ext_021_obj_3",
        "selected_risk_summary_path": str(selected_risk_summary),
    }
    save_json(pilot_summary_path, dict(base_summary))
    save_json(final_summary_path, dict(base_summary))

    def fake_finalize(**kwargs):
        return dict(base_summary)

    monkeypatch.setattr(v2_2_runner, "finalize_v2_2_4obj_pilot", fake_finalize)
    monkeypatch.setattr(v2_3_runner, "_pilot_summary_path", lambda seed: pilot_summary_path)
    monkeypatch.setattr(v2_3_runner, "_final_summary_path", lambda seed: final_summary_path)
    monkeypatch.setattr(
        v2_3_runner,
        "_reference_v2_2_final_summary_path",
        lambda seed: reference_final_summary,
    )

    final_summary = v2_3_runner.finalize_v2_3_4obj_pilot(seed=11)

    mechanism = final_summary["mechanism_verification"]
    assert mechanism["decoy_step_rate_decreased_vs_v2_2"] is True
    assert mechanism["restore_remove_step_rate_increased_vs_v2_2"] is True
    assert mechanism["mechanism_hypothesis_triggered_vs_v2_2"] is True

    pilot_summary = json.loads(pilot_summary_path.read_text(encoding="utf-8"))
    assert pilot_summary["mechanism_verification"]["current_decoy_step_rate"] == pytest.approx(0.30)
