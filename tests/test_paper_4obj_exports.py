from __future__ import annotations

import json
from pathlib import Path

import yaml

from cmorl_cyborg.config import load_stage1_config, load_stage2_config
from cmorl_cyborg.export_semantic_risk_summary import build_semantic_risk_summary
from cmorl_cyborg.main_table_b import generate_main_table_b
from cmorl_minicage.baselines import run_weighted_sum_baseline
from cmorl_minicage.utils import load_json, save_json


def test_weighted_sum_and_no_constraint_4obj_configs_load() -> None:
    stage1 = load_stage1_config(
        "cmorl_cyborg/configs/paper/weighted_sum_main_4obj.yaml"
    )
    stage2 = load_stage2_config(
        "cmorl_cyborg/configs/paper/no_constraint_stage2_main_4obj.yaml"
    )

    assert stage1.model.obj_dim == 4
    assert stage1.model.critical_host_safety_enabled is True
    assert len(stage1.explicit_preferences) == 10
    assert stage2.model.obj_dim == 4
    assert stage2.extension_mode == "unconstrained"
    assert stage2.shield.mode == "pre_critical_containment_priority"


def test_weighted_sum_baseline_uses_config_explicit_preferences_by_default(
    monkeypatch,
) -> None:
    stage1 = load_stage1_config(
        "cmorl_cyborg/configs/paper/weighted_sum_main_4obj.yaml"
    )
    captured: dict[str, object] = {}

    def _fake_run_learning_baseline(stage1_config, evaluate_config, *, explicit_preferences, output_dir):
        captured["preferences"] = explicit_preferences
        captured["output_dir"] = output_dir
        return Path("buffer.json"), Path("metrics.json")

    monkeypatch.setattr(
        "cmorl_minicage.baselines._run_learning_baseline",
        _fake_run_learning_baseline,
    )

    run_weighted_sum_baseline(stage1, object(), "tmp-output")

    assert captured["preferences"] == stage1.explicit_preferences


def test_main_table_4obj_configs_have_expected_entry_counts() -> None:
    compare_config = yaml.safe_load(
        Path("cmorl_cyborg/configs/paper/compare_suite_main_4obj.yaml").read_text(
            encoding="utf-8"
        )
    )
    table_b_config = yaml.safe_load(
        Path("cmorl_cyborg/configs/paper/table_b_suite_main_4obj.yaml").read_text(
            encoding="utf-8"
        )
    )

    assert len(compare_config["entries"]) == 9
    assert len(table_b_config["entries"]) == 12
    assert sorted({entry["method_name"] for entry in compare_config["entries"]}) == [
        "ours_stage2_v2_4",
        "stage1_only_4obj",
        "weighted_sum_4obj",
    ]
    assert sorted({entry["method_name"] for entry in table_b_config["entries"]}) == [
        "no_constraint_stage2_4obj",
        "ours_stage2_v2_4",
        "stage1_only_4obj",
        "weighted_sum_4obj",
    ]
    ours_entries = [
        entry
        for entry in table_b_config["entries"]
        if entry["method_name"] == "ours_stage2_v2_4"
    ]
    assert len(ours_entries) == 3
    assert all(entry["input_kind"] == "single_policy" for entry in ours_entries)


def test_generate_main_table_b_supports_precomputed_metrics(
    tmp_path: Path, monkeypatch
) -> None:
    metrics_a = tmp_path / "metrics_seed7.json"
    metrics_b = tmp_path / "metrics_seed11.json"
    save_json(
        metrics_a,
        {
            "method_name": "ours_stage2_v2_4",
            "selected_policy_id": "policy_a",
            "security_return": -100.0,
            "business_return": -20.0,
            "cost_return": -10.0,
            "feasible_rate": 1.0,
            "mean_violation": 0.0,
            "final_critical_compromised_hosts": 0.0,
            "critical_impact_count": 0.0,
            "high_disruption_action_rate": 0.2,
        },
    )
    save_json(
        metrics_b,
        {
            "method_name": "ours_stage2_v2_4",
            "selected_policy_id": "policy_b",
            "security_return": -200.0,
            "business_return": -30.0,
            "cost_return": -20.0,
            "feasible_rate": 0.5,
            "mean_violation": 0.8,
            "final_critical_compromised_hosts": 0.0,
            "critical_impact_count": 0.0,
            "high_disruption_action_rate": 0.4,
        },
    )
    dummy_threshold_source = tmp_path / "threshold_buffer.json"
    dummy_threshold_source.write_text("{}", encoding="utf-8")

    config_path = tmp_path / "table_b.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "output_dir": str(tmp_path / "table_b"),
                "table_output_dir": str(tmp_path / "tables"),
                "shared_thresholds_path": str(tmp_path / "thresholds.json"),
                "threshold_buffer_sources": [{"path": str(dummy_threshold_source)}],
                "entries": [
                    {
                        "method_name": "ours_stage2_v2_4",
                        "seed": 7,
                        "input_kind": "precomputed_metrics",
                        "input_path": str(metrics_a),
                    },
                    {
                        "method_name": "ours_stage2_v2_4",
                        "seed": 11,
                        "input_kind": "precomputed_metrics",
                        "input_path": str(metrics_b),
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    def _fake_thresholds(paths: list[str], output_path: str | Path) -> dict[str, float]:
        save_json(output_path, {"d_business": -125.0})
        return {"d_business": -125.0}

    def _should_not_run(*args, **kwargs):  # pragma: no cover
        raise AssertionError("evaluate_constraints should not run for precomputed metrics")

    monkeypatch.setattr("cmorl_cyborg.main_table_b.compute_shared_thresholds", _fake_thresholds)
    monkeypatch.setattr("cmorl_cyborg.main_table_b.evaluate_constraints", _should_not_run)

    summary_path = generate_main_table_b(config_path)

    summary = load_json(summary_path)
    assert len(summary["aggregated_paths"]) == 1
    aggregate = load_json(summary["aggregated_paths"][0])
    assert aggregate["method_name"] == "ours_stage2_v2_4"
    assert aggregate["selected_policy_ids"] == ["policy_a", "policy_b"]
    assert aggregate["security_return"] == -150.0
    assert aggregate["business_return"] == -25.0
    assert aggregate["feasible_rate"] == 0.75


def test_generate_main_table_b_supports_single_policy_entries(
    tmp_path: Path, monkeypatch
) -> None:
    metadata_a = tmp_path / "policy_seed7.json"
    metadata_b = tmp_path / "policy_seed11.json"
    save_json(
        metadata_a,
        {
            "method_name": "ours_stage2_v2_4",
            "policy_id": "policy_a",
            "checkpoint_path": str(tmp_path / "policy_a.pt"),
            "final_objective_vector": [-10.0, -20.0, -30.0, 0.0],
            "env": {"num_envs": 8},
            "model": {"obj_dim": 4},
            "shield": {"mode": "pre_critical_containment_priority"},
        },
    )
    save_json(
        metadata_b,
        {
            "method_name": "ours_stage2_v2_4",
            "policy_id": "policy_b",
            "checkpoint_path": str(tmp_path / "policy_b.pt"),
            "final_objective_vector": [-11.0, -21.0, -31.0, 0.0],
            "env": {"num_envs": 8},
            "model": {"obj_dim": 4},
            "shield": {"mode": "pre_critical_containment_priority"},
        },
    )
    dummy_threshold_source = tmp_path / "threshold_buffer.json"
    dummy_threshold_source.write_text("{}", encoding="utf-8")

    config_path = tmp_path / "table_b_single_policy.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "output_dir": str(tmp_path / "table_b"),
                "table_output_dir": str(tmp_path / "tables"),
                "shared_thresholds_path": str(tmp_path / "thresholds.json"),
                "threshold_buffer_sources": [{"path": str(dummy_threshold_source)}],
                "entries": [
                    {
                        "method_name": "ours_stage2_v2_4",
                        "seed": 7,
                        "input_kind": "single_policy",
                        "input_path": str(metadata_a),
                    },
                    {
                        "method_name": "ours_stage2_v2_4",
                        "seed": 11,
                        "input_kind": "single_policy",
                        "input_path": str(metadata_b),
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    def _fake_thresholds(paths: list[str], output_path: str | Path) -> dict[str, float]:
        save_json(output_path, {"d_business": -125.0, "d_cost": -22.0})
        return {"d_business": -125.0, "d_cost": -22.0}

    calls: list[dict[str, object]] = []

    def _fake_evaluate_constraints(**kwargs):
        calls.append(dict(kwargs))
        input_path = Path(str(kwargs["input_path"]))
        metadata = load_json(input_path)
        offset = 0.0 if metadata["policy_id"] == "policy_a" else 10.0
        return {
            "method_name": kwargs["method_name"],
            "selected_policy_id": metadata["policy_id"],
            "security_return": -100.0 - offset,
            "business_return": -20.0 - offset,
            "cost_return": -10.0 - offset,
            "feasible_rate": 1.0 - (offset / 20.0),
            "mean_violation": offset / 10.0,
            "final_critical_compromised_hosts": 0.0,
            "critical_impact_count": 0.0,
            "high_disruption_action_rate": 0.25 + (offset / 100.0),
        }

    monkeypatch.setattr("cmorl_cyborg.main_table_b.compute_shared_thresholds", _fake_thresholds)
    monkeypatch.setattr("cmorl_cyborg.main_table_b.evaluate_constraints", _fake_evaluate_constraints)

    summary_path = generate_main_table_b(config_path)

    assert len(calls) == 2
    assert all(call["input_kind"] == "single_policy" for call in calls)
    assert all(call["selection_source"] == "pareto" for call in calls)
    aggregate = load_json(load_json(summary_path)["aggregated_paths"][0])
    assert aggregate["selected_policy_ids"] == ["policy_a", "policy_b"]
    assert aggregate["security_return"] == -105.0
    assert aggregate["business_return"] == -25.0
    assert aggregate["feasible_rate"] == 0.75


def test_build_semantic_risk_summary_aggregates_selected_and_baseline(tmp_path: Path) -> None:
    selected_a = tmp_path / "selected_a.json"
    baseline_a = tmp_path / "baseline_a.json"
    selected_b = tmp_path / "selected_b.json"
    baseline_b = tmp_path / "baseline_b.json"

    def _payload(*, ever: float, persistent: float, q4: float, tier1: float, restore: float, decoy: float, focus: float) -> dict[str, object]:
        return {
            "ever_critical_breach_rate": ever,
            "persistent_critical_breach_rate": persistent,
            "mean_critical_dwell_steps": 1.0,
            "high_confidence_env_run_rate": 0.0,
            "questionable_rule_env_run_rates": {
                "Q4_user_focus_after_enterprise_foothold": q4,
            },
            "tier_rates": {
                "Tier 0 Safe": 0.0,
                "Tier 1 Near-Miss": tier1,
                "Tier 2 Transient Critical Breach": 0.0,
                "Tier 3 Persistent Critical Breach": persistent,
            },
            "precritical_action_family_step_rates": {
                "restore": restore,
                "remove": 0.0,
                "analyse": 0.0,
                "decoy": decoy,
                "other": 0.0,
            },
            "precritical_compromised_target_focus_step_rate": focus,
        }

    save_json(selected_a, _payload(ever=0.0, persistent=0.0, q4=0.0, tier1=1.0, restore=1.0, decoy=0.0, focus=1.0))
    save_json(baseline_a, _payload(ever=1.0, persistent=0.8, q4=0.6, tier1=0.2, restore=0.2, decoy=0.5, focus=0.3))
    save_json(selected_b, _payload(ever=0.1, persistent=0.0, q4=0.1, tier1=0.9, restore=0.8, decoy=0.1, focus=0.9))
    save_json(baseline_b, _payload(ever=0.9, persistent=0.7, q4=0.5, tier1=0.3, restore=0.3, decoy=0.4, focus=0.4))

    final_a = tmp_path / "seed_0007_final_summary.json"
    final_b = tmp_path / "seed_0011_final_summary.json"
    save_json(
        final_a,
        {
            "seed": 7,
            "final_selected_policy_id": "policy_a",
            "baseline_policy_id": "baseline_a",
            "selected_risk_summary_path": str(selected_a),
            "baseline_risk_summary_path": str(baseline_a),
        },
    )
    save_json(
        final_b,
        {
            "seed": 11,
            "final_selected_policy_id": "policy_b",
            "baseline_policy_id": "baseline_b",
            "selected_risk_summary_path": str(selected_b),
            "baseline_risk_summary_path": str(baseline_b),
        },
    )

    output_path = build_semantic_risk_summary(
        [final_a, final_b],
        output_dir=tmp_path / "semantic",
    )

    aggregate = load_json(output_path)
    assert aggregate["selected"]["ever_critical_breach_rate"] == 0.05
    assert aggregate["baseline"]["ever_critical_breach_rate"] == 0.95
    assert aggregate["delta"]["ever_critical_breach_rate"] == -0.9
    assert aggregate["selected"]["precritical_action_family_step_rates.restore"] == 0.9
    assert aggregate["baseline"]["precritical_action_family_step_rates.decoy"] == 0.45
    assert (tmp_path / "semantic" / "semantic_risk_seedwise.csv").exists()
    assert (tmp_path / "semantic" / "semantic_risk_summary.md").exists()
