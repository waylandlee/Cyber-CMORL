from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

import cmorl_cyborg.v2_2_4obj_pilot_runner as v2_2_runner
import cmorl_cyborg.v2_4_4obj_pilot_runner as v2_4_runner
from cmorl_cyborg.config import load_stage1_config, load_stage2_config
from cmorl_cyborg.export_candidate_semantic_audit import export_candidate_semantic_audit
from cmorl_minicage.shield import (
    ACTION_FAMILY_ANALYSE,
    ACTION_FAMILY_DECOY,
    ACTION_FAMILY_REMOVE,
    ACTION_FAMILY_RESTORE,
    SHIELD_LEVEL_PRE_CRITICAL_CONTAINMENT,
    SHIELD_MODE_PRE_CRITICAL_CONTAINMENT_PRIORITY,
    SHIELD_RESPONSE_TIER_CRITICAL_RESTORE_ON_CRITICAL,
    SHIELD_RESPONSE_TIER_FALLBACK_NATIVE,
    SHIELD_RESPONSE_TIER_PRECRITICAL_GENERAL_ENTERPRISE_OPERATIONAL,
    SHIELD_RESPONSE_TIER_PRECRITICAL_RESTORE_ON_ENTERPRISE_OPERATIONAL_COMPROMISED,
    build_shielded_action_mask,
)
from cmorl_minicage.utils import save_json


def test_v2_4_default_configs_enable_precritical_containment_shield() -> None:
    stage1 = load_stage1_config(v2_4_runner.DEFAULT_STAGE1_CONFIG)
    stage2 = load_stage2_config(v2_4_runner.DEFAULT_STAGE2_CONFIG)

    assert stage1.model.obj_dim == 4
    assert stage2.model.obj_dim == 4
    assert stage1.model.critical_host_safety_mode == "v2_1_dense_persistent"
    assert stage2.model.critical_host_safety_mode == "v2_1_dense_persistent"
    assert stage1.shield.mode == SHIELD_MODE_PRE_CRITICAL_CONTAINMENT_PRIORITY
    assert stage2.shield.mode == SHIELD_MODE_PRE_CRITICAL_CONTAINMENT_PRIORITY
    assert stage2.tail_acceptance.mode == "critical_tail"


def test_precritical_containment_prefers_restore_on_compromised_enterprise_operational_target() -> None:
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
            "_shield_is_critical_path_target": False,
            "_shield_is_non_user_non_sleep": True,
            "_shield_is_enterprise_operational_non_sleep": True,
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
        mode=SHIELD_MODE_PRE_CRITICAL_CONTAINMENT_PRIORITY,
        enterprise_operational_compromised_target_mask=np.asarray(
            [[0, 1, 1, 1, 0]],
            dtype=np.int32,
        ),
    )

    assert mask.tolist() == [[0.0, 1.0, 0.0, 0.0, 0.0]]
    assert diagnostics["shield_level"] == [SHIELD_LEVEL_PRE_CRITICAL_CONTAINMENT]
    assert diagnostics["shield_response_tier"] == [
        SHIELD_RESPONSE_TIER_PRECRITICAL_RESTORE_ON_ENTERPRISE_OPERATIONAL_COMPROMISED
    ]


def test_precritical_containment_falls_back_to_general_enterprise_operational_actions() -> None:
    native_mask = np.asarray([[1, 1, 1, 1]], dtype=np.float32)
    action_catalog = [
        {
            "_shield_action_family": ACTION_FAMILY_DECOY,
            "_shield_is_critical_path_target": False,
            "_shield_is_non_user_non_sleep": False,
            "_shield_is_enterprise_operational_non_sleep": False,
        },
        {
            "_shield_action_family": ACTION_FAMILY_DECOY,
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
            "_shield_action_family": ACTION_FAMILY_REMOVE,
            "_shield_is_critical_path_target": False,
            "_shield_is_non_user_non_sleep": False,
            "_shield_is_enterprise_operational_non_sleep": False,
        },
    ]

    mask, diagnostics = build_shielded_action_mask(
        native_mask=native_mask,
        action_catalog=action_catalog,
        critical_present=np.asarray([0], dtype=np.int32),
        enterprise_foothold_present=np.asarray([1], dtype=np.int32),
        mode=SHIELD_MODE_PRE_CRITICAL_CONTAINMENT_PRIORITY,
        enterprise_operational_compromised_target_mask=np.asarray(
            [[0, 0, 0, 0]],
            dtype=np.int32,
        ),
    )

    assert mask.tolist() == [[0.0, 1.0, 1.0, 0.0]]
    assert diagnostics["shield_response_tier"] == [
        SHIELD_RESPONSE_TIER_PRECRITICAL_GENERAL_ENTERPRISE_OPERATIONAL
    ]


def test_precritical_containment_falls_back_to_native_when_no_tier_matches() -> None:
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
        critical_present=np.asarray([0], dtype=np.int32),
        enterprise_foothold_present=np.asarray([1], dtype=np.int32),
        mode=SHIELD_MODE_PRE_CRITICAL_CONTAINMENT_PRIORITY,
        enterprise_operational_compromised_target_mask=np.asarray(
            [[0, 0]],
            dtype=np.int32,
        ),
    )

    assert mask.tolist() == native_mask.tolist()
    assert diagnostics["shield_level"] == [SHIELD_LEVEL_PRE_CRITICAL_CONTAINMENT]
    assert diagnostics["shield_fallback_flag"] == [1]
    assert diagnostics["shield_response_tier"] == [SHIELD_RESPONSE_TIER_FALLBACK_NATIVE]


def test_precritical_containment_keeps_critical_recovery_branch_unchanged() -> None:
    native_mask = np.asarray([[1, 1, 1]], dtype=np.float32)
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
    ]

    mask, diagnostics = build_shielded_action_mask(
        native_mask=native_mask,
        action_catalog=action_catalog,
        critical_present=np.asarray([1], dtype=np.int32),
        enterprise_foothold_present=np.asarray([1], dtype=np.int32),
        mode=SHIELD_MODE_PRE_CRITICAL_CONTAINMENT_PRIORITY,
        critical_compromised_target_mask=np.asarray([[0, 1, 1]], dtype=np.int32),
        enterprise_operational_compromised_target_mask=np.asarray(
            [[0, 1, 1]],
            dtype=np.int32,
        ),
    )

    assert mask.tolist() == [[0.0, 1.0, 0.0]]
    assert diagnostics["shield_response_tier"] == [
        SHIELD_RESPONSE_TIER_CRITICAL_RESTORE_ON_CRITICAL
    ]


def test_export_candidate_semantic_audit_reports_precritical_metrics(
    tmp_path: Path,
) -> None:
    trace_dir = tmp_path / "trace"
    trace_dir.mkdir()
    save_json(
        trace_dir / "trace_manifest.json",
        {
            "method_name": "ours_stage2_fair_critical_safe_v2_4_4obj",
            "seed": 11,
            "policy_id": "stage2_ext_016_obj_2",
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
                            "compromised_hosts": ["Enterprise0"],
                            "critical_compromised_hosts": [],
                            "compromised_host_count": 1,
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
            "blue_action": {"name": "Restore", "target_hostname": "Enterprise0", "target_subnet": "Enterprise"},
            "red_action": {"name": "Sleep", "target_hostname": None, "target_subnet": None},
            "state_before": {"compromised_hosts": ["Enterprise0"], "critical_compromised_hosts": [], "compromised_host_count": 1},
            "state_after": {"compromised_hosts": ["Enterprise0"], "critical_compromised_hosts": [], "compromised_host_count": 1},
            "newly_compromised_hosts": [],
            "recovered_hosts": [],
            "semantic_info": {"enterprise_foothold_present": 1.0, "critical_present": 0.0},
            "shield_active_flag": True,
            "shield_fallback_flag": False,
            "shield_blocked_probability_mass": 0.1,
        },
        {
            "episode_id": "episode_000",
            "env_idx": 0,
            "step_idx": 1,
            "blue_action": {"name": "Analyse", "target_hostname": "Enterprise0", "target_subnet": "Enterprise"},
            "red_action": {"name": "Sleep", "target_hostname": None, "target_subnet": None},
            "state_before": {"compromised_hosts": ["Enterprise0"], "critical_compromised_hosts": [], "compromised_host_count": 1},
            "state_after": {"compromised_hosts": ["Enterprise0"], "critical_compromised_hosts": [], "compromised_host_count": 1},
            "newly_compromised_hosts": [],
            "recovered_hosts": [],
            "semantic_info": {"enterprise_foothold_present": 1.0, "critical_present": 0.0},
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
            "state_before": {"compromised_hosts": ["Enterprise0"], "critical_compromised_hosts": [], "compromised_host_count": 1},
            "state_after": {"compromised_hosts": ["Enterprise0"], "critical_compromised_hosts": [], "compromised_host_count": 1},
            "newly_compromised_hosts": [],
            "recovered_hosts": [],
            "semantic_info": {"enterprise_foothold_present": 1.0, "critical_present": 0.0},
            "shield_active_flag": True,
            "shield_fallback_flag": False,
            "shield_blocked_probability_mass": 0.3,
        },
        {
            "episode_id": "episode_000",
            "env_idx": 0,
            "step_idx": 3,
            "blue_action": {"name": "Restore", "target_hostname": "Op_Server0", "target_subnet": "Operational"},
            "red_action": {"name": "Impact", "target_hostname": "Op_Server0", "target_subnet": "Operational"},
            "state_before": {"compromised_hosts": ["Enterprise0"], "critical_compromised_hosts": [], "compromised_host_count": 1},
            "state_after": {"compromised_hosts": ["Enterprise0", "Op_Server0"], "critical_compromised_hosts": ["Op_Server0"], "compromised_host_count": 2},
            "newly_compromised_hosts": ["Op_Server0"],
            "recovered_hosts": [],
            "semantic_info": {"enterprise_foothold_present": 1.0, "critical_present": 1.0},
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

    assert summary["precritical_action_family_step_rates"]["restore"] == pytest.approx(1.0 / 3.0)
    assert summary["precritical_action_family_step_rates"]["analyse"] == pytest.approx(1.0 / 3.0)
    assert summary["precritical_action_family_step_rates"]["decoy"] == pytest.approx(1.0 / 3.0)
    assert summary["precritical_action_family_env_run_rates"]["restore"] == pytest.approx(1.0)
    assert summary["precritical_action_family_env_run_rates"]["analyse"] == pytest.approx(1.0)
    assert summary["precritical_action_family_env_run_rates"]["decoy"] == pytest.approx(1.0)
    assert summary["precritical_compromised_target_focus_step_rate"] == pytest.approx(2.0 / 3.0)
    assert summary["precritical_compromised_target_focus_env_run_rate"] == pytest.approx(1.0)
    casebook = (tmp_path / "audit" / "critical_casebook.md").read_text(encoding="utf-8")
    assert "Pre-critical containment summary" in casebook
    assert "Pre-critical top action families" in casebook
    assert "Pre-critical compromised-target recovery counts" in casebook
    assert "Pre-critical no-containment top actions" in casebook


def test_finalize_v2_4_pilot_augments_saved_summaries_with_containment_verification(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    runner_root = tmp_path / "runner"
    runner_root.mkdir()
    selected_risk_summary = tmp_path / "selected_risk_summary.json"
    save_json(
        selected_risk_summary,
        {
            "precritical_action_family_step_rates": {
                "restore": 0.30,
                "remove": 0.20,
                "analyse": 0.10,
                "decoy": 0.20,
                "other": 0.20,
            },
            "precritical_action_family_env_run_rates": {
                "restore": 0.60,
                "remove": 0.55,
                "analyse": 0.20,
                "decoy": 0.40,
                "other": 0.30,
            },
            "precritical_compromised_target_focus_step_rate": 0.65,
            "ever_critical_breach_rate": 0.45,
            "tier_rates": {"Tier 0 Safe": 0.10},
        },
    )
    reference_risk_summary = tmp_path / "reference_risk_summary.json"
    save_json(
        reference_risk_summary,
        {
            "precritical_action_family_step_rates": {
                "restore": 0.10,
                "remove": 0.10,
                "analyse": 0.05,
                "decoy": 0.50,
                "other": 0.25,
            },
            "precritical_action_family_env_run_rates": {
                "restore": 0.30,
                "remove": 0.25,
                "analyse": 0.10,
                "decoy": 0.80,
                "other": 0.40,
            },
            "precritical_compromised_target_focus_step_rate": 0.20,
            "ever_critical_breach_rate": 0.60,
            "tier_rates": {"Tier 0 Safe": 0.0},
        },
    )
    reference_final_summary = tmp_path / "reference_final_summary.json"
    save_json(
        reference_final_summary,
        {
            "selected_policy_id": "stage2_ext_016_obj_2",
            "selected_risk_summary_path": str(reference_risk_summary),
        },
    )
    pilot_summary_path = runner_root / "seed_0011_pilot_summary.json"
    final_summary_path = runner_root / "seed_0011_final_summary.json"
    base_summary = {
        "selected_policy_id": "stage2_ext_021_obj_3",
        "selected_risk_summary_path": str(selected_risk_summary),
        "pilot_passed": True,
    }
    save_json(pilot_summary_path, dict(base_summary))
    save_json(final_summary_path, dict(base_summary))

    def fake_finalize(**kwargs):
        return dict(base_summary)

    monkeypatch.setattr(v2_2_runner, "finalize_v2_2_4obj_pilot", fake_finalize)
    monkeypatch.setattr(v2_4_runner, "_pilot_summary_path", lambda seed: pilot_summary_path)
    monkeypatch.setattr(v2_4_runner, "_final_summary_path", lambda seed: final_summary_path)
    monkeypatch.setattr(
        v2_4_runner,
        "_reference_v2_3_final_summary_path",
        lambda seed: reference_final_summary,
    )

    final_summary = v2_4_runner.finalize_v2_4_4obj_pilot(seed=11)

    verification = final_summary["containment_mechanism_verification"]
    assert verification["precritical_decoy_step_rate_decreased_vs_v2_3"] is True
    assert verification["precritical_recovery_step_rate_increased_vs_v2_3"] is True
    assert verification["precritical_compromised_target_focus_increased_vs_v2_3"] is True
    assert verification["ever_critical_breach_rate_decreased_vs_v2_3"] is True
    assert verification["containment_hypothesis_triggered_vs_v2_3"] is True
    assert verification["eligible_for_seed_expansion"] is True

    pilot_summary = json.loads(pilot_summary_path.read_text(encoding="utf-8"))
    assert (
        pilot_summary["containment_mechanism_verification"][
            "current_precritical_decoy_step_rate"
        ]
        == pytest.approx(0.20)
    )
