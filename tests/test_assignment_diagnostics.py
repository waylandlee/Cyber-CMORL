from __future__ import annotations

import json
from pathlib import Path

from cmorl_minicage.assignment_diagnostics import (
    _select_risk_adjusted_utility,
    _select_strict_lexi,
    _select_utility_argmax,
    diagnose_assignment_problem,
    run_assignment_diagnostics,
)
from cmorl_minicage.config import AssignmentDiagnosticsConfig
from cmorl_minicage.deployability import (
    CandidateMetrics,
    ThresholdProfile,
    evaluate_profile,
)
from cmorl_minicage.strict_level_diagnostics import run_strict_level_diagnostics_rows


def _candidate_row(
    *,
    policy_id: str,
    objective_vector: list[float],
    business_return: float,
    cost_return: float,
    mean_violation: float,
    final_critical: float,
    high_disruption: float,
) -> dict:
    profile = ThresholdProfile(
        name="tight",
        business_min=-125.0,
        cost_min=-22.0,
        mean_violation_max=0.50,
        final_critical_max=0.25,
        high_disruption_max=0.50,
    )
    metrics = CandidateMetrics(
        policy_id=policy_id,
        objective_vector=objective_vector,
        security_return=float(objective_vector[0]),
        business_return=business_return,
        cost_return=cost_return,
        mean_violation=mean_violation,
        final_critical_compromised_hosts=final_critical,
        high_disruption_action_rate=high_disruption,
        feasible_rate=1.0 if business_return >= -125.0 and cost_return >= -22.0 else 0.0,
    )
    profile_eval = evaluate_profile(metrics, profile)
    return {
        **metrics.to_dict(),
        "passed_strict": bool(profile_eval["passed"]),
        "fail_dims": list(profile_eval["fail_dims"]),
        "margins": dict(profile_eval["margins"]),
        "normalized_margins": dict(profile_eval["normalized_margins"]),
        "strict_margin": float(profile_eval["strict_margin"]),
        "profile_eval": profile_eval,
    }


def test_selector_behaviour_prefers_strict_candidate() -> None:
    candidates = [
        _candidate_row(
            policy_id="A",
            objective_vector=[10.0, -130.0, -25.0],
            business_return=-130.0,
            cost_return=-25.0,
            mean_violation=0.80,
            final_critical=0.60,
            high_disruption=0.70,
        ),
        _candidate_row(
            policy_id="B",
            objective_vector=[9.95, -120.0, -20.0],
            business_return=-120.0,
            cost_return=-20.0,
            mean_violation=0.10,
            final_critical=0.10,
            high_disruption=0.20,
        ),
        _candidate_row(
            policy_id="C",
            objective_vector=[6.0, -124.0, -21.0],
            business_return=-124.0,
            cost_return=-21.0,
            mean_violation=0.55,
            final_critical=0.30,
            high_disruption=0.30,
        ),
    ]
    preference = [1.0, 0.0, 0.0]

    utility_selected = _select_utility_argmax(candidates, preference)
    strict_selected = _select_strict_lexi(candidates, preference)
    risk_selected = _select_risk_adjusted_utility(
        candidates,
        preference,
        risk_penalty_weights={
            "business": 1.0,
            "cost": 1.0,
            "mean_violation": 2.0,
            "final_critical": 2.0,
            "high_disruption": 1.0,
        },
        utility_floor_ratio=0.10,
    )

    assert utility_selected["policy_id"] == "A"
    assert strict_selected["policy_id"] == "B"
    assert risk_selected["policy_id"] == "B"
    assert len(candidates) == 3
    assert sum(1 for candidate in candidates if candidate["passed_strict"]) == 1
    assert sum(
        1
        for candidate in candidates
        if (not candidate["passed_strict"]) and candidate["strict_margin"] >= -0.10
    ) == 1


def test_diagnose_assignment_problem_cases() -> None:
    assert (
        diagnose_assignment_problem(
            strict_candidate_count=0,
            selector_summaries={
                "utility_argmax": {"selected_strict_count": 0},
                "strict_lexi": {"selected_strict_count": 0},
                "risk_adjusted_utility": {"selected_strict_count": 0},
            },
            num_preferences=10,
        )
        == "candidate_supply_problem"
    )
    assert (
        diagnose_assignment_problem(
            strict_candidate_count=2,
            selector_summaries={
                "utility_argmax": {"selected_strict_count": 0},
                "strict_lexi": {"selected_strict_count": 2},
                "risk_adjusted_utility": {"selected_strict_count": 2},
            },
            num_preferences=10,
        )
        == "assignment_selection_problem"
    )
    assert (
        diagnose_assignment_problem(
            strict_candidate_count=2,
            selector_summaries={
                "utility_argmax": {"selected_strict_count": 1},
                "strict_lexi": {"selected_strict_count": 1},
                "risk_adjusted_utility": {"selected_strict_count": 1},
            },
            num_preferences=10,
        )
        == "mixed_problem"
    )


def test_strict_level_classifier_outputs(tmp_path: Path) -> None:
    candidate_rows = [
        _candidate_row(
            policy_id="L0_only",
            objective_vector=[1.0, -120.0, -20.0],
            business_return=-120.0,
            cost_return=-20.0,
            mean_violation=1.20,
            final_critical=0.98,
            high_disruption=0.20,
        ),
        _candidate_row(
            policy_id="L2_reached",
            objective_vector=[1.0, -120.0, -20.0],
            business_return=-120.0,
            cost_return=-20.0,
            mean_violation=0.70,
            final_critical=0.70,
            high_disruption=0.20,
        ),
        _candidate_row(
            policy_id="STRICT_reached",
            objective_vector=[1.0, -120.0, -20.0],
            business_return=-120.0,
            cost_return=-20.0,
            mean_violation=0.10,
            final_critical=0.10,
            high_disruption=0.20,
        ),
    ]

    outputs = run_strict_level_diagnostics_rows(
        candidate_rows,
        thresholds={"d_business": -125.0, "d_cost": -22.0},
        output_root=tmp_path,
        run_label="levels",
        profile_name="tight",
        high_disruption_max=0.50,
        levels=[
            {"name": "L0", "final_critical_max": 1.0, "mean_violation_max": 1.25},
            {"name": "L1", "final_critical_max": 0.95, "mean_violation_max": 1.0},
            {"name": "L2", "final_critical_max": 0.75, "mean_violation_max": 0.75},
            {"name": "L3", "final_critical_max": 0.50, "mean_violation_max": 0.60},
            {"name": "STRICT", "final_critical_max": 0.25, "mean_violation_max": 0.50},
        ],
    )

    summary = json.loads(Path(outputs["summary_path"]).read_text(encoding="utf-8"))
    csv_text = Path(outputs["candidates_path"]).read_text(encoding="utf-8")

    assert summary["best_level_reached_counts"]["L0"] == 1
    assert summary["best_level_reached_counts"]["L2"] == 1
    assert summary["best_level_reached_counts"]["STRICT"] == 1
    assert "policy_id,best_level_reached" in csv_text
    assert "STRICT_reached,STRICT" in csv_text


def test_run_assignment_diagnostics_writes_outputs(tmp_path: Path, monkeypatch) -> None:
    candidate_rows = [
        _candidate_row(
            policy_id="strict_a",
            objective_vector=[5.0, -120.0, -20.0],
            business_return=-120.0,
            cost_return=-20.0,
            mean_violation=0.10,
            final_critical=0.10,
            high_disruption=0.20,
        ),
        _candidate_row(
            policy_id="strict_b",
            objective_vector=[4.0, -121.0, -20.5],
            business_return=-121.0,
            cost_return=-20.5,
            mean_violation=0.20,
            final_critical=0.20,
            high_disruption=0.20,
        ),
    ]

    def fake_cache_rows(**kwargs):
        return (
            candidate_rows,
            {"d_business": -125.0, "d_cost": -22.0},
            {
                "name": "tight",
                "business_min": -125.0,
                "cost_min": -22.0,
                "mean_violation_max": 0.5,
                "final_critical_max": 0.25,
                "high_disruption_max": 0.5,
            },
        )

    monkeypatch.setattr(
        "cmorl_minicage.assignment_diagnostics._candidate_cache_rows",
        fake_cache_rows,
    )

    config = AssignmentDiagnosticsConfig(
        buffer_path="cmorl_cyborg/outputs/paper_table_a/ours_stage2/seed_0007/run_ddb937f9/solution_buffer.json",
        thresholds_path="cmorl_cyborg/outputs/fair_compare_eval/thresholds_tight.json",
        output_dir=str(tmp_path / "assignment"),
        run_label="toy",
        preference_step=0.5,
        run_strict_level_on_supply=True,
        strict_level_output_dir=str(tmp_path / "levels"),
    )

    repo_root = Path(__file__).resolve().parents[1]
    outputs = run_assignment_diagnostics(config, config_anchor=repo_root)
    summary = json.loads(Path(outputs["summary_path"]).read_text(encoding="utf-8"))

    assert Path(outputs["candidate_semantics_path"]).exists()
    assert Path(outputs["per_preference_path"]).exists()
    assert Path(outputs["summary_path"]).exists()
    assert summary["candidate_count"] == 2
    assert summary["strict_candidate_count"] == 2
    assert summary["diagnosis"] == "mixed_problem"
    assert "strict_level_outputs" not in summary
