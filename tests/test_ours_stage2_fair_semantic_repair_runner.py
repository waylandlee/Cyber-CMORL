from __future__ import annotations

import pytest

from cmorl_cyborg.ours_stage2_fair_semantic_repair_runner import (
    _full_phase_result,
    _full_seed_comparison,
    _pilot_comparison,
    _selection_only_comparison,
)


def _summary(
    *,
    business: float,
    cost: float,
    feasible: float,
    ever: float,
    persistent: float,
    first_hit: float = 0.0,
    latency: float = 0.0,
    dwell: float = 0.0,
    high_conf: float,
) -> dict[str, float]:
    return {
        "mean_business_return": float(business),
        "mean_cost_return": float(cost),
        "env_run_feasible_rate": float(feasible),
        "ever_critical_breach_rate": float(ever),
        "persistent_critical_breach_rate": float(persistent),
        "mean_first_critical_hit_step": float(first_hit),
        "critical_hit_latency_score": float(latency),
        "mean_critical_dwell_steps": float(dwell),
        "high_confidence_env_run_rate": float(high_conf),
    }


def test_selection_only_requires_persistent_drop_and_small_regressions() -> None:
    baseline = _summary(
        business=-120.0,
        cost=-20.0,
        feasible=0.20,
        ever=1.0,
        persistent=0.80,
        high_conf=1.0,
    )
    candidate = _summary(
        business=-123.5,
        cost=-21.8,
        feasible=0.30,
        ever=0.95,
        persistent=0.60,
        high_conf=0.90,
    )

    comparison = _selection_only_comparison(candidate, baseline)

    assert comparison["persistent_drop"] == pytest.approx(0.20)
    assert comparison["business_regression"] == pytest.approx(3.5)
    assert comparison["cost_regression"] == pytest.approx(1.8)
    assert comparison["meets_phase1_rule"] is True


def test_pilot_comparison_accepts_latency_improvement_path() -> None:
    baseline = _summary(
        business=-121.0,
        cost=-22.0,
        feasible=0.10,
        ever=1.0,
        persistent=0.85,
        first_hit=10.0,
        latency=0.20,
        high_conf=0.90,
    )
    candidate = _summary(
        business=-124.0,
        cost=-23.5,
        feasible=0.20,
        ever=0.95,
        persistent=0.55,
        first_hit=16.0,
        latency=0.32,
        high_conf=0.90,
    )

    comparison = _pilot_comparison(
        candidate,
        baseline,
        business_limit=5.0,
        cost_limit=2.0,
    )

    assert comparison["persistent_drop"] == pytest.approx(0.30)
    assert comparison["ever_drop"] == pytest.approx(0.05)
    assert comparison["latency_improvement"] == pytest.approx(0.12)
    assert comparison["first_hit_delay"] == pytest.approx(6.0)
    assert comparison["criteria"]["ever_critical_breach_below_one"] is True
    assert comparison["criteria"]["persistent_critical_breach_ok"] is True
    assert comparison["criteria"]["latency_or_delay_ok"] is True
    assert comparison["criteria"]["high_confidence_not_worse"] is True
    assert comparison["meets_phase2_rule"] is True


def test_pilot_comparison_rejects_high_confidence_regression() -> None:
    baseline = _summary(
        business=-120.0,
        cost=-20.0,
        feasible=0.30,
        ever=1.0,
        persistent=0.80,
        first_hit=12.0,
        latency=0.24,
        high_conf=0.60,
    )
    candidate = _summary(
        business=-121.0,
        cost=-20.5,
        feasible=0.35,
        ever=0.85,
        persistent=0.50,
        first_hit=18.0,
        latency=0.36,
        high_conf=0.70,
    )

    comparison = _pilot_comparison(
        candidate,
        baseline,
        business_limit=5.0,
        cost_limit=2.0,
    )

    assert comparison["criteria"]["high_confidence_not_worse"] is False
    assert "high_confidence_not_worse" in comparison["failure_reasons"]
    assert comparison["meets_phase2_rule"] is False


def test_full_phase_result_requires_two_passing_seeds_and_one_strong_seed() -> None:
    baseline = _summary(
        business=-121.0,
        cost=-22.0,
        feasible=0.10,
        ever=1.0,
        persistent=0.80,
        high_conf=0.90,
    )
    seed_a = {
        "comparison": _full_seed_comparison(
            _summary(
                business=-122.0,
                cost=-23.0,
                feasible=0.20,
                ever=0.85,
                persistent=0.45,
                high_conf=0.90,
            ),
            baseline,
        )
    }
    seed_b = {
        "comparison": _full_seed_comparison(
            _summary(
                business=-123.0,
                cost=-24.0,
                feasible=0.18,
                ever=0.95,
                persistent=0.60,
                high_conf=0.90,
            ),
            baseline,
        )
    }
    seed_c = {
        "comparison": _full_seed_comparison(
            _summary(
                business=-132.0,
                cost=-26.5,
                feasible=0.05,
                ever=1.0,
                persistent=0.78,
                high_conf=0.95,
            ),
            baseline,
        )
    }

    result = _full_phase_result(
        {
            "seed_0007": seed_a,
            "seed_0011": seed_b,
            "seed_0019": seed_c,
        }
    )

    assert result["seed_pass_count"] == 2
    assert result["guardrail_violating_seeds"] == ["seed_0019"]
    assert result["has_strong_seed"] is True
    assert result["meets_phase4_rule"] is False
