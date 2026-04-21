from __future__ import annotations

from pathlib import Path

import cmorl_minicage.evaluate_constraints as constraint_eval
from cmorl_cyborg.semantics import (
    SemanticSnapshot,
    semantic_step_info,
)
from cmorl_minicage.config import DeployabilityGateConfig
from cmorl_minicage.train_stage2 import _deployability_gate_result


def _snapshot(
    *,
    compromised: set[str] | None = None,
    critical: set[str] | None = None,
    enterprise: set[str] | None = None,
    operational: set[str] | None = None,
    defender: set[str] | None = None,
    user: set[str] | None = None,
) -> SemanticSnapshot:
    return SemanticSnapshot(
        compromised_hosts=set(compromised or set()),
        critical_compromised_hosts=set(critical or set()),
        operational_compromised_hosts=set(operational or set()),
        enterprise_compromised_hosts=set(enterprise or set()),
        defender_compromised_hosts=set(defender or set()),
        user_compromised_hosts=set(user or set()),
        weighted_security_exposure=0.0,
        weighted_business_exposure=0.0,
    )


class Sleep:
    pass


class AnalyseUserSubnet:
    def get_params(self) -> dict[str, str]:
        return {"subnet": "User"}


def test_semantic_step_info_tracks_critical_hit_dwell_and_antipatterns() -> None:
    before_hit = _snapshot(
        compromised={"Enterprise0"},
        enterprise={"Enterprise0"},
    )
    after_hit = _snapshot(
        compromised={"Enterprise0", "Op_Server0"},
        critical={"Op_Server0"},
        enterprise={"Enterprise0"},
        operational={"Op_Server0"},
    )

    hit_info = semantic_step_info(before_hit, after_hit, AnalyseUserSubnet())
    assert hit_info["critical_present"] == 1.0
    assert hit_info["critical_hit_event"] == 1.0
    assert hit_info["critical_dwell_flag"] == 1.0
    assert hit_info["critical_path_compromise_count"] == 2.0
    assert hit_info["user_action_during_critical_breach"] == 0.0
    assert hit_info["user_action_after_enterprise_foothold"] == 1.0

    sleep_info = semantic_step_info(after_hit, after_hit, Sleep())
    assert sleep_info["critical_hit_event"] == 0.0
    assert sleep_info["sleep_during_critical_breach"] == 1.0
    assert sleep_info["critical_dwell_flag"] == 1.0

    user_info = semantic_step_info(after_hit, after_hit, AnalyseUserSubnet())
    assert user_info["user_action_during_critical_breach"] == 1.0
    assert user_info["user_action_after_enterprise_foothold"] == 1.0


def test_critical_safe_balanced_prefers_lower_critical_breach_candidates(monkeypatch) -> None:
    metrics_by_name = {
        "cand_a": {
            "security_return": 20.0,
            "business_return": -121.0,
            "cost_return": -21.0,
            "feasible_rate": 1.0,
            "mean_violation": 0.10,
            "final_critical_compromised_hosts": 0.55,
            "persistent_critical_breach_rate": 0.55,
            "ever_critical_breach_rate": 1.0,
            "mean_first_critical_hit_step": 10.0,
            "critical_hit_latency_score": 0.20,
            "mean_critical_dwell_steps": 14.0,
            "sleep_during_critical_breach_rate": 0.10,
            "user_action_during_critical_breach_rate": 0.08,
            "user_action_after_enterprise_foothold_rate": 0.08,
            "critical_impact_count": 1.0,
            "high_disruption_action_rate": 0.10,
        },
        "cand_b": {
            "security_return": 18.0,
            "business_return": -122.0,
            "cost_return": -21.5,
            "feasible_rate": 1.0,
            "mean_violation": 0.12,
            "final_critical_compromised_hosts": 0.45,
            "persistent_critical_breach_rate": 0.45,
            "ever_critical_breach_rate": 0.75,
            "mean_first_critical_hit_step": 17.0,
            "critical_hit_latency_score": 0.34,
            "mean_critical_dwell_steps": 8.0,
            "sleep_during_critical_breach_rate": 0.04,
            "user_action_during_critical_breach_rate": 0.03,
            "user_action_after_enterprise_foothold_rate": 0.03,
            "critical_impact_count": 1.0,
            "high_disruption_action_rate": 0.12,
        },
        "cand_c": {
            "security_return": 15.0,
            "business_return": -140.0,
            "cost_return": -40.0,
            "feasible_rate": 0.0,
            "mean_violation": 5.0,
            "final_critical_compromised_hosts": 0.20,
            "persistent_critical_breach_rate": 0.20,
            "ever_critical_breach_rate": 0.20,
            "mean_first_critical_hit_step": 40.0,
            "critical_hit_latency_score": 0.80,
            "mean_critical_dwell_steps": 2.0,
            "sleep_during_critical_breach_rate": 0.0,
            "user_action_during_critical_breach_rate": 0.0,
            "user_action_after_enterprise_foothold_rate": 0.0,
            "critical_impact_count": 1.0,
            "high_disruption_action_rate": 0.05,
        },
    }

    def fake_eval(checkpoint_path, metadata, thresholds, *, eval_episodes, baseline_kind=None):
        return dict(metrics_by_name[Path(str(checkpoint_path)).stem])

    monkeypatch.setattr(constraint_eval, "_evaluate_actor_critic_record", fake_eval)

    records = [
        {
            "policy_id": "cand_a",
            "checkpoint_path": "cand_a.pt",
            "objective_vector": [20.0, -121.0, -21.0],
        },
        {
            "policy_id": "cand_b",
            "checkpoint_path": "cand_b.pt",
            "objective_vector": [18.0, -122.0, -21.5],
        },
        {
            "policy_id": "cand_c",
            "checkpoint_path": "cand_c.pt",
            "objective_vector": [15.0, -140.0, -40.0],
        },
    ]

    selected, diagnostics = constraint_eval._select_record_critical_safe_balanced(
        records,
        metadata={"env": {}, "model": {}},
        buffer_anchor=Path(__file__).resolve().parents[1] / "cmorl_minicage" / "config.py",
        thresholds={"d_business": -125.0, "d_cost": -22.0},
        eval_episodes=1,
        semantic_metric_weights={
            "high_disruption_action_rate": 0.5,
            "final_critical_compromised_hosts": 0.3,
            "critical_impact_count": 0.2,
        },
    )

    assert selected["policy_id"] == "cand_b"
    assert diagnostics["selection_policy"] == "critical_safe_balanced"
    assert diagnostics["shortlist_reason"] == "relaxed_budget_band"


def test_hard_gate_rejects_child_that_only_improves_cost_without_critical_progress() -> None:
    parent = {
        "business_return": -118.0,
        "cost_return": -24.0,
        "final_critical_compromised_hosts": 0.70,
        "ever_critical_breach_rate": 1.0,
        "persistent_critical_breach_rate": 0.70,
        "critical_hit_latency_score": 0.20,
        "mean_critical_dwell_steps": 12.0,
        "user_action_during_critical_breach_rate": 0.10,
    }
    child = {
        **parent,
        "cost_return": -22.0,
    }

    result = _deployability_gate_result(
        parent,
        child,
        gate_config=DeployabilityGateConfig(mode="hard"),
    )

    assert result["gate_passed"] is False
    assert result["gate_reason"] == "no_improvement_path"
