from __future__ import annotations

from pathlib import Path

from cmorl_cyborg.config import load_stage2_config as load_cyborg_stage2_config
from cmorl_minicage.algorithms.adaptive_selection import select_top_n_adaptive
from cmorl_minicage.config import (
    DeployabilityGateConfig,
    DeployabilityTargetConfig,
    Stage2Config,
    load_stage2_config as load_minicage_stage2_config,
)
from cmorl_minicage.train_stage2 import (
    _deployability_acceptance_decision,
    _annotate_records_with_deployability,
    _deployability_acceptance_key,
    _deployability_gate_result,
    _deployability_improved,
    _deployability_target_acceptance_key,
    _deployability_target_decision,
    _deployability_target_profile,
    _deployability_target_result,
)


def _critical_first_parent() -> dict[str, float | str]:
    return {
        "support_shell_reached": "NONE",
        "strict_margin": -4.50,
        "mean_violation": 4.80,
        "high_disruption_action_rate": 0.95,
        "business_return": -118.0,
        "cost_return": -24.0,
        "final_critical_compromised_hosts": 0.70,
        "deployability_score": 0.10,
        "ever_critical_breach_rate": 1.0,
        "persistent_critical_breach_rate": 0.70,
        "mean_first_critical_hit_step": 10.0,
        "critical_hit_latency_score": 0.20,
        "mean_critical_dwell_steps": 12.0,
        "user_action_during_critical_breach_rate": 0.10,
        "sleep_during_critical_breach_rate": 0.05,
    }


def test_annotate_records_with_deployability_builds_frontiers_and_tags(monkeypatch) -> None:
    metrics_by_name = {
        "policy_value": {
            "security_return": 10.0,
            "business_return": -120.0,
            "cost_return": -20.0,
            "feasible_rate": 1.0,
            "mean_violation": 0.80,
            "high_disruption_action_rate": 0.70,
            "final_critical_compromised_hosts": 0.60,
        },
        "policy_near": {
            "security_return": 9.0,
            "business_return": -121.0,
            "cost_return": -20.5,
            "feasible_rate": 1.0,
            "mean_violation": 0.40,
            "high_disruption_action_rate": 0.40,
            "final_critical_compromised_hosts": 0.30,
        },
        "policy_strict": {
            "security_return": 8.0,
            "business_return": -122.0,
            "cost_return": -21.0,
            "feasible_rate": 1.0,
            "mean_violation": 0.10,
            "high_disruption_action_rate": 0.10,
            "final_critical_compromised_hosts": 0.10,
        },
    }

    def fake_eval(checkpoint_path, metadata, thresholds, *, eval_episodes, baseline_kind=None):
        return dict(metrics_by_name[Path(str(checkpoint_path)).stem])

    monkeypatch.setattr("cmorl_minicage.train_stage2._evaluate_actor_critic_record", fake_eval)

    records = [
        {
            "policy_id": "policy_value",
            "checkpoint_path": "policy_value.pt",
            "objective_vector": [10.0, -120.0, -20.0],
            "stage": "stage1",
            "source": "stage1",
        },
        {
            "policy_id": "policy_near",
            "checkpoint_path": "policy_near.pt",
            "objective_vector": [9.0, -121.0, -20.5],
            "stage": "stage1",
            "source": "stage1",
        },
        {
            "policy_id": "policy_strict",
            "checkpoint_path": "policy_strict.pt",
            "objective_vector": [8.0, -122.0, -21.0],
            "stage": "stage1",
            "source": "stage1",
        },
    ]
    config = Stage2Config()
    config.selection.pool_mode = "pareto_plus_deployability"
    config.selection.semantic_eval_episodes = 3
    config.selection.near_frontier_quota = 1
    config.selection.strict_frontier_quota = 1
    config.selection.semantic_support_score_weights = {
        "mean_violation": 0.45,
        "high_disruption": 0.30,
        "business": 0.15,
        "cost": 0.10,
    }

    strict_profile, shell_thresholds, frontiers, selection_pool = _annotate_records_with_deployability(
        records,
        parent_buffer_metadata={"env": {"seed": 7}, "model": {"obj_dim": 3, "hidden_size": 8}},
        config=config,
        thresholds={"d_business": -125.0, "d_cost": -22.0},
    )

    assert strict_profile["name"] == "stage2_deployability"
    assert set(shell_thresholds.keys()) == {"S0", "S1", "S2"}
    assert frontiers["value_frontier_policy_ids"] == ["policy_value"]
    assert frontiers["near_frontier_policy_ids"] == ["policy_near"]
    assert frontiers["strict_frontier_policy_ids"] == ["policy_strict"]
    assert [record["policy_id"] for record in selection_pool] == [
        "policy_value",
        "policy_near",
        "policy_strict",
    ]

    value_tag = records[0]["notes"]["deployability"]
    near_tag = records[1]["notes"]["deployability"]
    strict_tag = records[2]["notes"]["deployability"]

    assert {
        "business_return",
        "cost_return",
        "mean_violation",
        "high_disruption_action_rate",
        "final_critical_compromised_hosts",
        "ever_critical_breach_rate",
        "persistent_critical_breach_rate",
        "mean_first_critical_hit_step",
        "critical_hit_latency_score",
        "mean_critical_dwell_steps",
        "user_action_during_critical_breach_rate",
        "strict_margin",
        "passed_strict",
        "support_shell_reached",
        "deployability_score",
    }.issubset(value_tag.keys())
    assert near_tag["passed_strict"] is False
    assert strict_tag["passed_strict"] is True
    assert strict_tag["support_shell_reached"] == "STRICT"


def test_deployability_acceptance_prefers_shell_then_margin_then_score() -> None:
    lower_shell = {
        "support_shell_reached": "S0",
        "strict_margin": 0.80,
        "deployability_score": 0.95,
    }
    higher_shell = {
        "support_shell_reached": "S1",
        "strict_margin": 0.10,
        "deployability_score": 0.30,
    }
    better_margin = {
        "support_shell_reached": "S1",
        "strict_margin": 0.20,
        "deployability_score": 0.10,
    }
    worse_child = {
        "support_shell_reached": "S0",
        "strict_margin": -0.10,
        "deployability_score": 0.05,
    }

    assert _deployability_acceptance_key(
        higher_shell, objective_improvement=0.5
    ) > _deployability_acceptance_key(lower_shell, objective_improvement=5.0)
    assert _deployability_acceptance_key(
        better_margin, objective_improvement=0.1
    ) > _deployability_acceptance_key(higher_shell, objective_improvement=10.0)
    assert _deployability_improved(lower_shell, higher_shell) is True
    assert _deployability_improved(better_margin, higher_shell) is True
    assert _deployability_improved(higher_shell, worse_child) is False


def test_deployability_gate_accepts_critical_first_improvement_paths() -> None:
    gate_config = DeployabilityGateConfig(mode="hard")
    parent = _critical_first_parent()

    ever_improved_child = {
        **parent,
        "ever_critical_breach_rate": 0.90,
    }
    persistent_improved_child = {
        **parent,
        "persistent_critical_breach_rate": 0.55,
        "final_critical_compromised_hosts": 0.55,
    }
    latency_improved_child = {
        **parent,
        "critical_hit_latency_score": 0.32,
        "mean_first_critical_hit_step": 16.0,
        "mean_critical_dwell_steps": 12.0,
    }

    assert _deployability_gate_result(
        parent, ever_improved_child, gate_config=gate_config
    )["gate_reason"] == "ever_critical_improved"
    assert _deployability_gate_result(
        parent, persistent_improved_child, gate_config=gate_config
    )["gate_reason"] == "persistent_critical_improved"
    assert _deployability_gate_result(
        parent, latency_improved_child, gate_config=gate_config
    )["gate_reason"] == "critical_latency_improved"


def test_deployability_gate_rejects_guardrail_failures_and_non_improving_child() -> None:
    gate_config = DeployabilityGateConfig(mode="hard")
    parent = _critical_first_parent()

    assert _deployability_gate_result(
        parent,
        {**parent, "business_return": -127.0},
        gate_config=gate_config,
    )["gate_reason"] == "business_regression_guardrail"
    assert _deployability_gate_result(
        parent,
        {**parent, "cost_return": -29.0},
        gate_config=gate_config,
    )["gate_reason"] == "cost_regression_guardrail"
    assert _deployability_gate_result(
        parent,
        {**parent, "persistent_critical_breach_rate": 0.80},
        gate_config=gate_config,
    )["gate_reason"] == "persistent_critical_guardrail"
    assert _deployability_gate_result(
        parent,
        {**parent, "critical_hit_latency_score": 0.10},
        gate_config=gate_config,
    )["gate_reason"] == "critical_hit_latency_guardrail"
    assert _deployability_gate_result(
        parent,
        {**parent, "mean_critical_dwell_steps": 16.0},
        gate_config=gate_config,
    )["gate_reason"] == "critical_dwell_guardrail"
    assert _deployability_gate_result(
        parent,
        {**parent, "user_action_during_critical_breach_rate": 0.13},
        gate_config=gate_config,
    )["gate_reason"] == "user_action_during_critical_guardrail"
    assert _deployability_gate_result(
        parent,
        {**parent, "mean_violation": 4.70, "high_disruption_action_rate": 0.90},
        gate_config=gate_config,
    )["gate_reason"] == "no_improvement_path"


def test_hard_gate_acceptance_only_ranks_gate_passing_children() -> None:
    gate_config = DeployabilityGateConfig(mode="hard")
    parent = _critical_first_parent()
    gate_reject_child = {
        **parent,
        "mean_violation": 4.70,
        "high_disruption_action_rate": 0.90,
        "deployability_score": 0.95,
    }
    gate_pass_child = {
        **parent,
        "ever_critical_breach_rate": 0.94,
        "deployability_score": 0.20,
    }

    reject_decision = _deployability_acceptance_decision(
        parent,
        gate_reject_child,
        objective_improvement=10.0,
        gate_config=gate_config,
    )
    pass_decision = _deployability_acceptance_decision(
        parent,
        gate_pass_child,
        objective_improvement=0.1,
        gate_config=gate_config,
    )

    assert reject_decision["should_rank"] is False
    assert reject_decision["acceptance_key"] is None
    assert pass_decision["should_rank"] is True
    assert pass_decision["acceptance_key"] == _deployability_acceptance_key(
        gate_pass_child,
        objective_improvement=0.1,
    )


def test_deployability_target_profile_anchors_s0_to_current_best_strict_record() -> None:
    records = [
        {
            "policy_id": "best_strict",
            "notes": {
                "deployability": {
                    "business_return": -112.0,
                    "cost_return": -25.0,
                    "mean_violation": 4.5,
                    "high_disruption_action_rate": 0.94,
                    "strict_margin": -4.0,
                }
            },
        },
        {
            "policy_id": "other",
            "notes": {
                "deployability": {
                    "business_return": -130.0,
                    "cost_return": -17.0,
                    "mean_violation": 7.0,
                    "high_disruption_action_rate": 0.60,
                    "strict_margin": -7.0,
                }
            },
        },
    ]
    target_profile = _deployability_target_profile(
        records,
        shell_thresholds={
            "S0": {
                "business_min": -118.0,
                "cost_min": -18.0,
                "mean_violation_max": 8.0,
                "high_disruption_max": 0.70,
            }
        },
        target_config=DeployabilityTargetConfig(mode="global_support", reference_shell="S0"),
    )

    assert target_profile["anchor_policy_id"] == "best_strict"
    assert target_profile["business_min"] == -112.0
    assert target_profile["cost_min"] == -18.0
    assert target_profile["mean_violation_max"] == 4.5
    assert target_profile["high_disruption_max"] == 0.70


def test_deployability_target_accepts_score_or_excess_improvement_paths() -> None:
    target_config = DeployabilityTargetConfig(mode="global_support")
    excess_only_config = DeployabilityTargetConfig(
        mode="global_support",
        min_target_score_improvement=0.20,
        min_target_excess_reduction=0.02,
    )
    target_profile = {
        "name": "stage2_target:S0",
        "business_min": -112.0,
        "cost_min": -18.0,
        "mean_violation_max": 4.5,
        "high_disruption_max": 0.70,
    }
    parent = {
        "support_shell_reached": "NONE",
        "strict_margin": -4.50,
        "business_return": -118.0,
        "cost_return": -24.0,
        "mean_violation": 4.80,
        "high_disruption_action_rate": 0.95,
        "final_critical_compromised_hosts": 0.70,
        "deployability_score": 0.10,
    }
    shell_child = {**parent, "support_shell_reached": "S0"}
    score_child = {
        **parent,
        "business_return": -113.0,
        "cost_return": -20.0,
        "mean_violation": 4.55,
        "high_disruption_action_rate": 0.72,
    }
    excess_child = {
        **parent,
        "business_return": -118.0,
        "cost_return": -20.5,
        "mean_violation": 4.55,
        "high_disruption_action_rate": 0.70,
    }

    assert _deployability_target_result(
        parent,
        shell_child,
        target_profile_dict=target_profile,
        target_config=target_config,
    )["gate_reason"] == "shell_rank_improved"
    assert _deployability_target_result(
        parent,
        score_child,
        target_profile_dict=target_profile,
        target_config=target_config,
    )["gate_reason"] == "target_score_improved"
    assert _deployability_target_result(
        parent,
        excess_child,
        target_profile_dict=target_profile,
        target_config=excess_only_config,
    )["gate_reason"] == "target_excess_reduced"


def test_deployability_target_rejects_guardrail_failures_and_non_progressing_child() -> None:
    target_config = DeployabilityTargetConfig(mode="global_support")
    target_profile = {
        "name": "stage2_target:S0",
        "business_min": -112.0,
        "cost_min": -18.0,
        "mean_violation_max": 4.5,
        "high_disruption_max": 0.70,
    }
    parent = {
        "support_shell_reached": "NONE",
        "strict_margin": -4.50,
        "business_return": -118.0,
        "cost_return": -24.0,
        "mean_violation": 4.80,
        "high_disruption_action_rate": 0.95,
        "final_critical_compromised_hosts": 0.70,
        "deployability_score": 0.10,
    }

    assert _deployability_target_result(
        parent,
        {**parent, "business_return": -127.5},
        target_profile_dict=target_profile,
        target_config=target_config,
    )["gate_reason"] == "business_regression_guardrail"
    assert _deployability_target_result(
        parent,
        {**parent, "cost_return": -29.0},
        target_profile_dict=target_profile,
        target_config=target_config,
    )["gate_reason"] == "cost_regression_guardrail"
    assert _deployability_target_result(
        parent,
        {**parent, "final_critical_compromised_hosts": 0.90},
        target_profile_dict=target_profile,
        target_config=target_config,
    )["gate_reason"] == "final_critical_guardrail"
    assert _deployability_target_result(
        parent,
        {**parent, "business_return": -117.9, "cost_return": -24.0},
        target_profile_dict=target_profile,
        target_config=target_config,
    )["gate_reason"] == "no_target_progress"


def test_deployability_target_acceptance_only_ranks_target_passing_children() -> None:
    target_config = DeployabilityTargetConfig(mode="global_support")
    target_profile = {
        "name": "stage2_target:S0",
        "business_min": -112.0,
        "cost_min": -18.0,
        "mean_violation_max": 4.5,
        "high_disruption_max": 0.70,
    }
    parent = {
        "support_shell_reached": "NONE",
        "strict_margin": -4.50,
        "business_return": -118.0,
        "cost_return": -24.0,
        "mean_violation": 4.80,
        "high_disruption_action_rate": 0.95,
        "final_critical_compromised_hosts": 0.70,
        "deployability_score": 0.10,
    }
    target_reject_child = {
        **parent,
        "business_return": -117.9,
        "cost_return": -24.0,
    }
    target_pass_child = {
        **parent,
        "business_return": -113.0,
        "cost_return": -20.0,
        "mean_violation": 4.55,
        "high_disruption_action_rate": 0.72,
        "deployability_score": 0.20,
    }

    reject_decision = _deployability_target_decision(
        parent,
        target_reject_child,
        objective_improvement=10.0,
        target_profile_dict=target_profile,
        target_config=target_config,
    )
    pass_decision = _deployability_target_decision(
        parent,
        target_pass_child,
        objective_improvement=0.1,
        target_profile_dict=target_profile,
        target_config=target_config,
    )

    assert reject_decision["should_rank"] is False
    assert reject_decision["acceptance_key"] is None
    assert pass_decision["should_rank"] is True
    assert pass_decision["acceptance_key"] == _deployability_target_acceptance_key(
        target_pass_child,
        objective_improvement=0.1,
        target_result=pass_decision["gate_result"],
    )


def test_stage2_config_loads_deployability_gate_and_target_for_minicage_and_cyborg(tmp_path) -> None:
    config_path = tmp_path / "stage2_gate.yaml"
    config_path.write_text(
        "\n".join(
            [
                "deployability_gate:",
                "  mode: hard",
                "  min_strict_margin_improvement: 0.5",
                "  min_mean_violation_reduction: 0.4",
                "  min_high_disruption_reduction: 0.02",
                "  max_business_regression: 4.0",
                "  max_cost_regression: 1.5",
                "  max_final_critical_increase: 0.05",
                "  max_ever_critical_breach_increase: 0.0",
                "  max_persistent_critical_breach_increase: 0.04",
                "  max_critical_hit_latency_score_drop: 0.03",
                "  max_mean_critical_dwell_steps_increase: 2.0",
                "  max_user_action_during_critical_breach_rate_increase: 0.01",
                "  min_ever_critical_breach_reduction: 0.07",
                "  min_persistent_critical_breach_reduction: 0.12",
                "  min_critical_hit_latency_score_improvement: 0.11",
                "deployability_target:",
                "  mode: global_support",
                "  reference_shell: S1",
                "  min_target_score_improvement: 0.03",
                "  min_target_excess_reduction: 0.04",
                "  max_business_regression: 7.0",
                "  max_cost_regression: 3.0",
                "  max_final_critical_increase: 0.12",
                "  weights:",
                "    mean_violation: 0.6",
                "    high_disruption: 0.25",
                "    business: 0.1",
                "    cost: 0.05",
            ]
        ),
        encoding="utf-8",
    )

    minicage_config = load_minicage_stage2_config(config_path)
    cyborg_config = load_cyborg_stage2_config(config_path)

    assert minicage_config.deployability_gate.mode == "hard"
    assert minicage_config.deployability_gate.min_strict_margin_improvement == 0.5
    assert minicage_config.deployability_gate.max_ever_critical_breach_increase == 0.0
    assert minicage_config.deployability_gate.max_persistent_critical_breach_increase == 0.04
    assert minicage_config.deployability_gate.min_critical_hit_latency_score_improvement == 0.11
    assert minicage_config.deployability_target.mode == "global_support"
    assert minicage_config.deployability_target.reference_shell == "S1"
    assert cyborg_config.deployability_gate.mode == "hard"
    assert cyborg_config.deployability_gate.max_final_critical_increase == 0.05
    assert cyborg_config.deployability_gate.max_mean_critical_dwell_steps_increase == 2.0
    assert cyborg_config.deployability_target.min_target_excess_reduction == 0.04


def test_adaptive_selection_can_operate_on_explicit_non_pareto_pool() -> None:
    selection_pool = [
        {"policy_id": "value", "objective_vector": [10.0, -120.0, -20.0]},
        {"policy_id": "near", "objective_vector": [9.0, -121.0, -20.5]},
        {"policy_id": "strict", "objective_vector": [8.0, -122.0, -21.0]},
    ]

    selected, _, _ = select_top_n_adaptive(
        selection_pool,
        top_n=3,
        preferences=[[1.0, 0.0, 0.0]],
        weights={
            "crowding": 0.0,
            "expansion": 0.0,
            "low_risk": 0.0,
            "coverage": 0.0,
            "semantic_low_risk": 1.0,
        },
        tolerance=0.0,
        keep_extremes=False,
        pareto_only=False,
        component_overrides={
            "value": {"semantic_low_risk_score": 0.1},
            "near": {"semantic_low_risk_score": 0.8},
            "strict": {"semantic_low_risk_score": 0.9},
        },
    )

    assert {record["policy_id"] for record in selected} == {"value", "near", "strict"}
