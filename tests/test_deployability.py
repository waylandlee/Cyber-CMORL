from __future__ import annotations

from cmorl_minicage.deployability import (
    CandidateMetrics,
    ThresholdProfile,
    evaluate_profile,
)


def test_evaluate_profile_passes_strict_candidate() -> None:
    metrics = CandidateMetrics(
        policy_id="strict_ok",
        objective_vector=[1.0, -120.0, -20.0],
        security_return=1.0,
        business_return=-120.0,
        cost_return=-20.0,
        mean_violation=0.10,
        final_critical_compromised_hosts=0.10,
        high_disruption_action_rate=0.20,
        feasible_rate=1.0,
    )
    profile = ThresholdProfile(
        name="tight",
        business_min=-125.0,
        cost_min=-22.0,
        mean_violation_max=0.50,
        final_critical_max=0.25,
        high_disruption_max=0.50,
    )

    result = evaluate_profile(metrics, profile)

    assert result["passed"] is True
    assert result["fail_dims"] == []
    assert result["strict_margin"] > 0.0


def test_evaluate_profile_reports_single_dim_failure() -> None:
    metrics = CandidateMetrics(
        policy_id="single_fail",
        objective_vector=[1.0, -120.0, -20.0],
        security_return=1.0,
        business_return=-120.0,
        cost_return=-20.0,
        mean_violation=0.55,
        final_critical_compromised_hosts=0.10,
        high_disruption_action_rate=0.20,
        feasible_rate=0.0,
    )
    profile = ThresholdProfile(
        name="tight",
        business_min=-125.0,
        cost_min=-22.0,
        mean_violation_max=0.50,
        final_critical_max=0.25,
        high_disruption_max=0.50,
    )

    result = evaluate_profile(metrics, profile)

    assert result["passed"] is False
    assert result["fail_dims"] == ["mean_violation"]
    assert result["normalized_margins"]["mean_violation"] < 0.0
    assert result["strict_margin"] == result["normalized_margins"]["mean_violation"]


def test_evaluate_profile_reports_multiple_failures() -> None:
    metrics = CandidateMetrics(
        policy_id="multi_fail",
        objective_vector=[1.0, -130.0, -24.0],
        security_return=1.0,
        business_return=-130.0,
        cost_return=-24.0,
        mean_violation=0.80,
        final_critical_compromised_hosts=0.60,
        high_disruption_action_rate=0.70,
        feasible_rate=0.0,
    )
    profile = ThresholdProfile(
        name="tight",
        business_min=-125.0,
        cost_min=-22.0,
        mean_violation_max=0.50,
        final_critical_max=0.25,
        high_disruption_max=0.50,
    )

    result = evaluate_profile(metrics, profile)

    assert result["passed"] is False
    assert set(result["fail_dims"]) == {
        "business",
        "cost",
        "mean_violation",
        "final_critical",
        "high_disruption",
    }
    assert result["strict_margin"] < 0.0
