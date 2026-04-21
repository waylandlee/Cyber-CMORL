from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

DEFAULT_MEAN_VIOLATION_MAX = 0.50
DEFAULT_FINAL_CRITICAL_MAX = 0.25
DEFAULT_HIGH_DISRUPTION_MAX = 0.50

_PROFILE_DIM_ORDER = (
    "business",
    "cost",
    "mean_violation",
    "final_critical",
    "high_disruption",
)
_SUPPORT_DIM_ORDER = (
    "mean_violation",
    "high_disruption",
    "business",
    "cost",
)
SUPPORT_SHELL_LEVELS = (
    ("S0", 0.20, 0.80),
    ("S1", 0.10, 0.90),
    ("S2", 0.05, 0.95),
)
SUPPORT_SHELL_ORDER = ("NONE", "S0", "S1", "S2", "STRICT")


@dataclass
class CandidateMetrics:
    policy_id: str
    objective_vector: list[float]
    security_return: float
    business_return: float
    cost_return: float
    mean_violation: float
    final_critical_compromised_hosts: float
    high_disruption_action_rate: float
    feasible_rate: float
    ever_critical_breach_rate: float = 0.0
    persistent_critical_breach_rate: float = 0.0
    mean_first_critical_hit_step: float = 0.0
    critical_hit_latency_score: float = 0.0
    mean_critical_dwell_steps: float = 0.0
    sleep_during_critical_breach_rate: float = 0.0
    user_action_during_critical_breach_rate: float = 0.0
    user_action_after_enterprise_foothold_rate: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "CandidateMetrics":
        return cls(
            policy_id=str(payload["policy_id"]),
            objective_vector=list(map(float, payload.get("objective_vector", []))),
            security_return=float(payload.get("security_return", 0.0)),
            business_return=float(payload.get("business_return", 0.0)),
            cost_return=float(payload.get("cost_return", 0.0)),
            mean_violation=float(payload.get("mean_violation", 0.0)),
            final_critical_compromised_hosts=float(
                payload.get("final_critical_compromised_hosts", 0.0)
            ),
            high_disruption_action_rate=float(
                payload.get("high_disruption_action_rate", 0.0)
            ),
            feasible_rate=float(payload.get("feasible_rate", 0.0)),
            ever_critical_breach_rate=float(
                payload.get("ever_critical_breach_rate", 0.0)
            ),
            persistent_critical_breach_rate=float(
                payload.get(
                    "persistent_critical_breach_rate",
                    payload.get("final_critical_compromised_hosts", 0.0),
                )
            ),
            mean_first_critical_hit_step=float(
                payload.get("mean_first_critical_hit_step", 0.0)
            ),
            critical_hit_latency_score=float(
                payload.get("critical_hit_latency_score", 0.0)
            ),
            mean_critical_dwell_steps=float(
                payload.get("mean_critical_dwell_steps", 0.0)
            ),
            sleep_during_critical_breach_rate=float(
                payload.get("sleep_during_critical_breach_rate", 0.0)
            ),
            user_action_during_critical_breach_rate=float(
                payload.get("user_action_during_critical_breach_rate", 0.0)
            ),
            user_action_after_enterprise_foothold_rate=float(
                payload.get("user_action_after_enterprise_foothold_rate", 0.0)
            ),
        )


@dataclass
class ThresholdProfile:
    name: str
    business_min: float
    cost_min: float
    mean_violation_max: float
    final_critical_max: float
    high_disruption_max: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SupportThresholdProfile:
    name: str
    business_min: float
    cost_min: float
    mean_violation_max: float
    high_disruption_max: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def empty_semantic_totals() -> dict[str, list[float]]:
    return {
        "final_compromised_hosts": [],
        "final_critical_compromised_hosts": [],
        "critical_impact_count": [],
        "recovered_hosts": [],
        "analyse_count": [],
        "remove_count": [],
        "restore_count": [],
        "high_disruption_action_count": [],
        "total_action_count": [],
        "ever_critical_breach": [],
        "first_critical_hit_step": [],
        "critical_hit_latency_score": [],
        "critical_dwell_steps": [],
        "critical_path_compromise_count": [],
        "sleep_during_critical_breach": [],
        "user_action_during_critical_breach": [],
        "user_action_after_enterprise_foothold": [],
    }


def summarize_semantic_totals(totals: dict[str, list[float]]) -> dict[str, float]:
    total_action_sum = max(float(np.sum(totals["total_action_count"])), 1.0)
    return {
        "final_compromised_hosts": float(np.mean(totals["final_compromised_hosts"])),
        "final_critical_compromised_hosts": float(
            np.mean(totals["final_critical_compromised_hosts"])
        ),
        "persistent_critical_breach_rate": float(
            np.mean(totals["final_critical_compromised_hosts"])
        ),
        "critical_impact_count": float(np.mean(totals["critical_impact_count"])),
        "recovered_hosts": float(np.mean(totals["recovered_hosts"])),
        "analyse_count": float(np.mean(totals["analyse_count"])),
        "remove_count": float(np.mean(totals["remove_count"])),
        "restore_count": float(np.mean(totals["restore_count"])),
        "high_disruption_action_rate": float(
            np.sum(totals["high_disruption_action_count"]) / total_action_sum
        ),
        "ever_critical_breach_rate": float(np.mean(totals["ever_critical_breach"])),
        "mean_first_critical_hit_step": float(np.mean(totals["first_critical_hit_step"])),
        "critical_hit_latency_score": float(
            np.mean(totals["critical_hit_latency_score"])
        ),
        "mean_critical_dwell_steps": float(np.mean(totals["critical_dwell_steps"])),
        "mean_critical_path_compromise_count": float(
            np.mean(totals["critical_path_compromise_count"])
        ),
        "sleep_during_critical_breach_rate": float(
            np.sum(totals["sleep_during_critical_breach"]) / total_action_sum
        ),
        "user_action_during_critical_breach_rate": float(
            np.sum(totals["user_action_during_critical_breach"]) / total_action_sum
        ),
        "user_action_after_enterprise_foothold_rate": float(
            np.sum(totals["user_action_after_enterprise_foothold"]) / total_action_sum
        ),
        "semantic_eval_episodes": int(len(totals["final_compromised_hosts"])),
    }


def build_threshold_profile(
    *,
    name: str,
    thresholds: dict[str, float],
    mean_violation_max: float = DEFAULT_MEAN_VIOLATION_MAX,
    final_critical_max: float = DEFAULT_FINAL_CRITICAL_MAX,
    high_disruption_max: float = DEFAULT_HIGH_DISRUPTION_MAX,
) -> ThresholdProfile:
    return ThresholdProfile(
        name=name,
        business_min=float(thresholds["d_business"]),
        cost_min=float(thresholds["d_cost"]),
        mean_violation_max=float(mean_violation_max),
        final_critical_max=float(final_critical_max),
        high_disruption_max=float(high_disruption_max),
    )


def build_support_threshold_profile(
    *,
    name: str,
    business_min: float,
    cost_min: float,
    mean_violation_max: float = DEFAULT_MEAN_VIOLATION_MAX,
    high_disruption_max: float = DEFAULT_HIGH_DISRUPTION_MAX,
) -> SupportThresholdProfile:
    return SupportThresholdProfile(
        name=name,
        business_min=float(business_min),
        cost_min=float(cost_min),
        mean_violation_max=float(mean_violation_max),
        high_disruption_max=float(high_disruption_max),
    )


def candidate_metrics_from_metrics(
    *,
    policy_id: str,
    objective_vector: list[float],
    metrics: dict[str, Any],
) -> CandidateMetrics:
    return CandidateMetrics(
        policy_id=str(policy_id),
        objective_vector=list(map(float, objective_vector)),
        security_return=float(metrics.get("security_return", 0.0)),
        business_return=float(metrics.get("business_return", 0.0)),
        cost_return=float(metrics.get("cost_return", 0.0)),
        mean_violation=float(metrics.get("mean_violation", 0.0)),
        final_critical_compromised_hosts=float(
            metrics.get("final_critical_compromised_hosts", 0.0)
        ),
        high_disruption_action_rate=float(
            metrics.get("high_disruption_action_rate", 0.0)
        ),
        feasible_rate=float(metrics.get("feasible_rate", 0.0)),
        ever_critical_breach_rate=float(metrics.get("ever_critical_breach_rate", 0.0)),
        persistent_critical_breach_rate=float(
            metrics.get(
                "persistent_critical_breach_rate",
                metrics.get("final_critical_compromised_hosts", 0.0),
            )
        ),
        mean_first_critical_hit_step=float(metrics.get("mean_first_critical_hit_step", 0.0)),
        critical_hit_latency_score=float(metrics.get("critical_hit_latency_score", 0.0)),
        mean_critical_dwell_steps=float(metrics.get("mean_critical_dwell_steps", 0.0)),
        sleep_during_critical_breach_rate=float(
            metrics.get("sleep_during_critical_breach_rate", 0.0)
        ),
        user_action_during_critical_breach_rate=float(
            metrics.get("user_action_during_critical_breach_rate", 0.0)
        ),
        user_action_after_enterprise_foothold_rate=float(
            metrics.get("user_action_after_enterprise_foothold_rate", 0.0)
        ),
    )


def evaluate_profile(
    metrics: CandidateMetrics,
    profile: ThresholdProfile,
) -> dict[str, Any]:
    margins = {
        "business": float(metrics.business_return - profile.business_min),
        "cost": float(metrics.cost_return - profile.cost_min),
        "mean_violation": float(profile.mean_violation_max - metrics.mean_violation),
        "final_critical": float(
            profile.final_critical_max - metrics.final_critical_compromised_hosts
        ),
        "high_disruption": float(
            profile.high_disruption_max - metrics.high_disruption_action_rate
        ),
    }
    normalized_margins = {
        "business": float(margins["business"] / max(abs(profile.business_min), 1.0, 1e-8)),
        "cost": float(margins["cost"] / max(abs(profile.cost_min), 1.0, 1e-8)),
        "mean_violation": float(
            margins["mean_violation"] / max(profile.mean_violation_max, 1.0, 1e-8)
        ),
        "final_critical": float(
            margins["final_critical"] / max(profile.final_critical_max, 1.0, 1e-8)
        ),
        "high_disruption": float(
            margins["high_disruption"] / max(profile.high_disruption_max, 1.0, 1e-8)
        ),
    }
    strict_margin = float(min(normalized_margins[dim] for dim in _PROFILE_DIM_ORDER))
    fail_dims = [dim for dim in _PROFILE_DIM_ORDER if margins[dim] < 0.0]
    return {
        "profile_name": profile.name,
        "passed": not fail_dims,
        "fail_dims": fail_dims,
        "margins": margins,
        "normalized_margins": normalized_margins,
        "strict_margin": strict_margin,
    }


def evaluate_support_profile(
    metrics: CandidateMetrics,
    profile: SupportThresholdProfile,
) -> dict[str, Any]:
    margins = {
        "business": float(metrics.business_return - profile.business_min),
        "cost": float(metrics.cost_return - profile.cost_min),
        "mean_violation": float(profile.mean_violation_max - metrics.mean_violation),
        "high_disruption": float(
            profile.high_disruption_max - metrics.high_disruption_action_rate
        ),
    }
    normalized_margins = {
        "business": float(margins["business"] / max(abs(profile.business_min), 1.0, 1e-8)),
        "cost": float(margins["cost"] / max(abs(profile.cost_min), 1.0, 1e-8)),
        "mean_violation": float(
            margins["mean_violation"] / max(profile.mean_violation_max, 1.0, 1e-8)
        ),
        "high_disruption": float(
            margins["high_disruption"] / max(profile.high_disruption_max, 1.0, 1e-8)
        ),
    }
    support_margin = float(min(normalized_margins[dim] for dim in _SUPPORT_DIM_ORDER))
    fail_dims = [dim for dim in _SUPPORT_DIM_ORDER if margins[dim] < 0.0]
    return {
        "profile_name": profile.name,
        "passed": not fail_dims,
        "fail_dims": fail_dims,
        "margins": margins,
        "normalized_margins": normalized_margins,
        "support_margin": support_margin,
    }


def support_aware_deployability_score(
    metrics: CandidateMetrics,
    profile: SupportThresholdProfile,
    *,
    weights: dict[str, float],
) -> float:
    profile_eval = evaluate_support_profile(metrics, profile)
    total_weight = max(
        float(sum(float(weights.get(dim, 0.0)) for dim in _SUPPORT_DIM_ORDER)),
        1e-8,
    )
    weighted_excess = sum(
        float(weights.get(dim, 0.0))
        * max(0.0, -float(profile_eval["normalized_margins"].get(dim, 0.0)))
        for dim in _SUPPORT_DIM_ORDER
    )
    return float(max(0.0, 1.0 - (weighted_excess / total_weight)))


def normalized_excess(
    profile_eval: dict[str, Any],
    *,
    dim: str,
) -> float:
    normalized_margins = dict(profile_eval.get("normalized_margins", {}))
    return float(max(0.0, -float(normalized_margins.get(dim, 0.0))))


def support_shell_rank(shell_name: str) -> int:
    try:
        return SUPPORT_SHELL_ORDER.index(str(shell_name))
    except ValueError:
        return -1


def support_shell_thresholds(
    candidate_rows: list[dict[str, Any]] | list[CandidateMetrics],
) -> dict[str, dict[str, float]]:
    if not candidate_rows:
        return {
            shell_name: {
                "business_min": 0.0,
                "cost_min": 0.0,
                "mean_violation_max": 0.0,
                "high_disruption_max": 0.0,
            }
            for shell_name, _, _ in SUPPORT_SHELL_LEVELS
        }
    metrics_rows = [
        row if isinstance(row, CandidateMetrics) else CandidateMetrics.from_dict(row)
        for row in candidate_rows
    ]
    business = np.asarray([row.business_return for row in metrics_rows], dtype=np.float64)
    cost = np.asarray([row.cost_return for row in metrics_rows], dtype=np.float64)
    mean_violation = np.asarray(
        [row.mean_violation for row in metrics_rows],
        dtype=np.float64,
    )
    high_disruption = np.asarray(
        [row.high_disruption_action_rate for row in metrics_rows],
        dtype=np.float64,
    )
    thresholds: dict[str, dict[str, float]] = {}
    for shell_name, lower_quantile, upper_quantile in SUPPORT_SHELL_LEVELS:
        thresholds[shell_name] = {
            "business_min": float(np.quantile(business, upper_quantile)),
            "cost_min": float(np.quantile(cost, upper_quantile)),
            "mean_violation_max": float(np.quantile(mean_violation, lower_quantile)),
            "high_disruption_max": float(np.quantile(high_disruption, lower_quantile)),
        }
    return thresholds


def evaluate_support_shells(
    metrics: CandidateMetrics,
    *,
    shell_thresholds: dict[str, dict[str, float]],
    strict_profile: ThresholdProfile,
    profile_name: str,
) -> dict[str, Any]:
    shell_evals: dict[str, dict[str, Any]] = {}
    for shell_name, _, _ in SUPPORT_SHELL_LEVELS:
        thresholds = dict(shell_thresholds[shell_name])
        support_profile = build_support_threshold_profile(
            name=f"{profile_name}:{shell_name}",
            business_min=float(thresholds["business_min"]),
            cost_min=float(thresholds["cost_min"]),
            mean_violation_max=float(thresholds["mean_violation_max"]),
            high_disruption_max=float(thresholds["high_disruption_max"]),
        )
        shell_evals[shell_name] = evaluate_support_profile(metrics, support_profile)
    strict_eval = evaluate_profile(metrics, strict_profile)
    shell_evals["STRICT"] = strict_eval
    best_shell = "NONE"
    for shell_name in SUPPORT_SHELL_ORDER[1:]:
        if bool(shell_evals[shell_name]["passed"]):
            best_shell = shell_name
    return {
        "shell_evals": shell_evals,
        "support_shell_reached": best_shell,
    }


def deployability_note_payload(
    metrics: CandidateMetrics,
    *,
    strict_profile: ThresholdProfile,
    shell_thresholds: dict[str, dict[str, float]],
    profile_name: str,
    weights: dict[str, float],
) -> dict[str, Any]:
    shell_payload = evaluate_support_shells(
        metrics,
        shell_thresholds=shell_thresholds,
        strict_profile=strict_profile,
        profile_name=profile_name,
    )
    strict_support_profile = build_support_threshold_profile(
        name=f"{profile_name}:support_score",
        business_min=float(strict_profile.business_min),
        cost_min=float(strict_profile.cost_min),
        mean_violation_max=float(strict_profile.mean_violation_max),
        high_disruption_max=float(strict_profile.high_disruption_max),
    )
    strict_eval = shell_payload["shell_evals"]["STRICT"]
    deployability_score = support_aware_deployability_score(
        metrics,
        strict_support_profile,
        weights=weights,
    )
    return {
        "business_return": float(metrics.business_return),
        "cost_return": float(metrics.cost_return),
        "mean_violation": float(metrics.mean_violation),
        "high_disruption_action_rate": float(metrics.high_disruption_action_rate),
        "final_critical_compromised_hosts": float(
            metrics.final_critical_compromised_hosts
        ),
        "ever_critical_breach_rate": float(metrics.ever_critical_breach_rate),
        "persistent_critical_breach_rate": float(
            metrics.persistent_critical_breach_rate
        ),
        "mean_first_critical_hit_step": float(metrics.mean_first_critical_hit_step),
        "critical_hit_latency_score": float(metrics.critical_hit_latency_score),
        "mean_critical_dwell_steps": float(metrics.mean_critical_dwell_steps),
        "sleep_during_critical_breach_rate": float(
            metrics.sleep_during_critical_breach_rate
        ),
        "user_action_during_critical_breach_rate": float(
            metrics.user_action_during_critical_breach_rate
        ),
        "user_action_after_enterprise_foothold_rate": float(
            metrics.user_action_after_enterprise_foothold_rate
        ),
        "strict_margin": float(strict_eval["strict_margin"]),
        "passed_strict": bool(strict_eval["passed"]),
        "support_shell_reached": str(shell_payload["support_shell_reached"]),
        "deployability_score": float(deployability_score),
    }
