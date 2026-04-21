from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

import cmorl_minicage.evaluate_constraints as constraint_eval
from cmorl_minicage.algorithms.assignment import assign_policy
from cmorl_minicage.buffer import load_policy_buffer
from cmorl_minicage.config import (
    AssignmentDiagnosticsConfig,
    DEFAULT_ASSIGNMENT_DIAGNOSTICS_CONFIG,
    load_assignment_diagnostics_config,
)
from cmorl_minicage.deployability import (
    CandidateMetrics,
    build_threshold_profile,
    candidate_metrics_from_metrics,
    evaluate_profile,
    normalized_excess,
)
from cmorl_minicage.strict_level_diagnostics import run_strict_level_diagnostics_rows
from cmorl_minicage.utils import save_json, simplex_grid

SELECTOR_ORDER = ("utility_argmax", "strict_lexi", "risk_adjusted_utility")


def _repo_root_from_path(path: str | Path) -> Path:
    path = Path(path).resolve()
    for candidate in (path, *path.parents):
        if (candidate / "cmorl_minicage").exists():
            return candidate
    raise ValueError(f"Could not infer repository root from {path}")


def _resolve_path(anchor: str | Path, raw_path: str | Path) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return (_repo_root_from_path(anchor) / path).resolve()


def _write_jsonl(path: str | Path, rows: list[dict[str, Any]]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_candidate_semantics_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            rows.append(json.loads(stripped))
    return rows


def _run_label(config: AssignmentDiagnosticsConfig, buffer_path: Path) -> str:
    if config.run_label:
        return str(config.run_label)
    parent_name = buffer_path.parent.name or buffer_path.stem
    return f"{parent_name}_{config.source_set}_{config.profile_name}"


def _utility(record: dict[str, Any], preference: list[float]) -> float:
    objectives = np.asarray(record["objective_vector"], dtype=np.float32)
    weights = np.asarray(preference, dtype=np.float32)
    return float(np.dot(weights, objectives))


def _near_strict(candidate: dict[str, Any]) -> bool:
    return (not bool(candidate.get("passed_strict", False))) and float(
        candidate.get("strict_margin", -1.0)
    ) >= -0.10


def _select_utility_argmax(
    candidates: list[dict[str, Any]],
    preference: list[float],
) -> dict[str, Any]:
    selected = assign_policy(preference, candidates)
    selected_record = next(
        candidate for candidate in candidates if candidate["policy_id"] == selected["policy_id"]
    )
    result = dict(selected_record)
    result["utility"] = float(selected["utility"])
    return result


def _select_strict_lexi(
    candidates: list[dict[str, Any]],
    preference: list[float],
) -> dict[str, Any]:
    return max(
        (
            {
                **candidate,
                "utility": _utility(candidate, preference),
            }
            for candidate in candidates
        ),
        key=lambda candidate: (
            1 if bool(candidate["passed_strict"]) else 0,
            float(candidate["strict_margin"]),
            float(candidate["utility"]),
            str(candidate["policy_id"]),
        ),
    )


def _normalize_utilities(candidates: list[dict[str, Any]]) -> dict[str, float]:
    utilities = np.asarray(
        [float(candidate["utility"]) for candidate in candidates],
        dtype=np.float32,
    )
    if utilities.size == 0:
        return {}
    umin = float(np.min(utilities))
    umax = float(np.max(utilities))
    if np.isclose(umax, umin):
        return {candidate["policy_id"]: 0.0 for candidate in candidates}
    return {
        candidate["policy_id"]: float((float(candidate["utility"]) - umin) / (umax - umin))
        for candidate in candidates
    }


def _risk_penalty(
    candidate: dict[str, Any],
    weights: dict[str, float],
) -> float:
    return float(
        sum(
            float(weight) * normalized_excess(candidate["profile_eval"], dim=dim)
            for dim, weight in weights.items()
        )
    )


def _select_risk_adjusted_utility(
    candidates: list[dict[str, Any]],
    preference: list[float],
    *,
    risk_penalty_weights: dict[str, float],
    utility_floor_ratio: float,
) -> dict[str, Any]:
    with_utilities = [
        {
            **candidate,
            "utility": _utility(candidate, preference),
        }
        for candidate in candidates
    ]
    utilities = np.asarray(
        [float(candidate["utility"]) for candidate in with_utilities],
        dtype=np.float32,
    )
    max_utility = float(np.max(utilities))
    min_utility = float(np.min(utilities))
    utility_floor = max_utility - float(utility_floor_ratio) * (max_utility - min_utility)
    shortlist = [
        candidate for candidate in with_utilities if float(candidate["utility"]) >= utility_floor
    ]
    if not shortlist:
        shortlist = with_utilities
    normalized_utilities = _normalize_utilities(shortlist)
    return max(
        (
            {
                **candidate,
                "utility_norm": float(normalized_utilities[candidate["policy_id"]]),
                "risk_penalty": _risk_penalty(candidate, risk_penalty_weights),
            }
            for candidate in shortlist
        ),
        key=lambda candidate: (
            float(candidate["utility_norm"] - candidate["risk_penalty"]),
            1 if bool(candidate["passed_strict"]) else 0,
            float(candidate["strict_margin"]),
            float(candidate["utility"]),
            str(candidate["policy_id"]),
        ),
    )


def _selector_dispatch(
    selector_name: str,
    candidates: list[dict[str, Any]],
    preference: list[float],
    *,
    risk_penalty_weights: dict[str, float],
    utility_floor_ratio: float,
) -> dict[str, Any]:
    if selector_name == "utility_argmax":
        return _select_utility_argmax(candidates, preference)
    if selector_name == "strict_lexi":
        return _select_strict_lexi(candidates, preference)
    if selector_name == "risk_adjusted_utility":
        return _select_risk_adjusted_utility(
            candidates,
            preference,
            risk_penalty_weights=risk_penalty_weights,
            utility_floor_ratio=utility_floor_ratio,
        )
    raise ValueError(f"Unsupported selector: {selector_name}")


def _selector_summary(
    selector_rows: list[dict[str, Any]],
    *,
    candidate_count: int,
    strict_candidate_count: int,
    near_candidate_count: int,
) -> dict[str, Any]:
    return {
        "candidate_count": int(candidate_count),
        "strict_candidate_count": int(strict_candidate_count),
        "near_candidate_count": int(near_candidate_count),
        "selected_strict_count": int(
            sum(1 for row in selector_rows if bool(row["selected_passed_strict"]))
        ),
        "selected_near_count": int(
            sum(1 for row in selector_rows if bool(row["selected_near_strict"]))
        ),
        "avg_strict_margin": float(
            np.mean([float(row["selected_strict_margin"]) for row in selector_rows])
        )
        if selector_rows
        else 0.0,
        "avg_final_critical_compromised_hosts": float(
            np.mean(
                [
                    float(row["selected_final_critical_compromised_hosts"])
                    for row in selector_rows
                ]
            )
        )
        if selector_rows
        else 0.0,
        "avg_mean_violation": float(
            np.mean([float(row["selected_mean_violation"]) for row in selector_rows])
        )
        if selector_rows
        else 0.0,
        "avg_high_disruption_action_rate": float(
            np.mean(
                [float(row["selected_high_disruption_action_rate"]) for row in selector_rows]
            )
        )
        if selector_rows
        else 0.0,
    }


def diagnose_assignment_problem(
    *,
    strict_candidate_count: int,
    selector_summaries: dict[str, dict[str, Any]],
    num_preferences: int,
) -> str:
    if strict_candidate_count == 0 and all(
        int(selector_summaries[name]["selected_strict_count"]) == 0
        for name in SELECTOR_ORDER
    ):
        return "candidate_supply_problem"

    utility_selected = int(selector_summaries["utility_argmax"]["selected_strict_count"])
    improvement_threshold = int(math.ceil(0.10 * float(num_preferences)))
    improved = any(
        int(selector_summaries[name]["selected_strict_count"])
        >= utility_selected + improvement_threshold
        for name in ("strict_lexi", "risk_adjusted_utility")
    )
    if strict_candidate_count > 0 and improved:
        return "assignment_selection_problem"
    return "mixed_problem"


def _candidate_cache_rows(
    *,
    buffer_path: Path,
    source_set: str,
    thresholds_path: Path,
    eval_episodes: int,
    profile_name: str,
    mean_violation_max: float,
    final_critical_max: float,
    high_disruption_max: float,
) -> tuple[list[dict[str, Any]], dict[str, float], dict[str, Any]]:
    payload = load_policy_buffer(buffer_path)
    if source_set == "pareto":
        candidate_records = list(payload.get("pareto_front", []))
    elif source_set == "records":
        candidate_records = list(payload.get("records", []))
    else:
        raise ValueError(f"Unsupported source_set: {source_set}")
    if not candidate_records:
        raise ValueError(f"No candidate records found for source_set={source_set}")

    thresholds = constraint_eval._load_thresholds(thresholds_path)
    strict_profile = build_threshold_profile(
        name=profile_name,
        thresholds=thresholds,
        mean_violation_max=mean_violation_max,
        final_critical_max=final_critical_max,
        high_disruption_max=high_disruption_max,
    )
    cache_rows: list[dict[str, Any]] = []
    for record in candidate_records:
        checkpoint_path = (
            constraint_eval._resolve_path(buffer_path, record["checkpoint_path"])
            if record.get("checkpoint_path")
            else None
        )
        baseline_kind = record.get("notes", {}).get("baseline_kind")
        rollout_metrics = constraint_eval._evaluate_actor_critic_record(
            checkpoint_path,
            payload.get("metadata", {}),
            thresholds,
            eval_episodes=eval_episodes,
            baseline_kind=baseline_kind,
        )
        metrics = candidate_metrics_from_metrics(
            policy_id=str(record["policy_id"]),
            objective_vector=list(record.get("objective_vector", [])),
            metrics=rollout_metrics,
        )
        profile_eval = evaluate_profile(metrics, strict_profile)
        cache_rows.append(
            {
                **metrics.to_dict(),
                "passed_strict": bool(profile_eval["passed"]),
                "fail_dims": list(profile_eval["fail_dims"]),
                "margins": dict(profile_eval["margins"]),
                "normalized_margins": dict(profile_eval["normalized_margins"]),
                "strict_margin": float(profile_eval["strict_margin"]),
                "profile_eval": profile_eval,
            }
        )
    return cache_rows, thresholds, strict_profile.to_dict()


def run_assignment_diagnostics(
    config: AssignmentDiagnosticsConfig,
    *,
    config_anchor: str | Path | None = None,
) -> dict[str, str]:
    if not config.buffer_path:
        raise ValueError("buffer_path must be provided")
    if not config.thresholds_path:
        raise ValueError("thresholds_path must be provided")
    anchor = Path(config_anchor).resolve() if config_anchor is not None else Path.cwd()
    buffer_path = _resolve_path(anchor, config.buffer_path)
    thresholds_path = _resolve_path(anchor, config.thresholds_path)
    output_root = _resolve_path(anchor, config.output_dir)
    run_label = _run_label(config, buffer_path)
    run_dir = output_root / run_label
    run_dir.mkdir(parents=True, exist_ok=True)

    candidate_rows, thresholds, strict_profile = _candidate_cache_rows(
        buffer_path=buffer_path,
        source_set=config.source_set,
        thresholds_path=thresholds_path,
        eval_episodes=int(config.eval_episodes),
        profile_name=config.profile_name,
        mean_violation_max=float(config.mean_violation_max),
        final_critical_max=float(config.final_critical_max),
        high_disruption_max=float(config.high_disruption_max),
    )
    obj_dim = len(candidate_rows[0]["objective_vector"])
    preferences = simplex_grid(float(config.preference_step), obj_dim)

    candidate_semantics_path = run_dir / "candidate_semantics.jsonl"
    per_preference_path = run_dir / "assignment_diag_per_preference.csv"
    summary_path = run_dir / "assignment_diag_summary.json"
    _write_jsonl(candidate_semantics_path, candidate_rows)

    candidate_count = len(candidate_rows)
    strict_candidate_count = sum(
        1 for candidate in candidate_rows if bool(candidate["passed_strict"])
    )
    near_candidate_count = sum(1 for candidate in candidate_rows if _near_strict(candidate))

    per_preference_rows: list[dict[str, Any]] = []
    selector_rows: dict[str, list[dict[str, Any]]] = {name: [] for name in SELECTOR_ORDER}
    for preference_index, preference in enumerate(preferences):
        for selector_name in SELECTOR_ORDER:
            selected = _selector_dispatch(
                selector_name,
                candidate_rows,
                preference,
                risk_penalty_weights=dict(config.risk_penalty_weights),
                utility_floor_ratio=float(config.utility_floor_ratio),
            )
            row = {
                "selector": selector_name,
                "preference_index": int(preference_index),
                "preference": json.dumps(list(map(float, preference))),
                "selected_policy_id": str(selected["policy_id"]),
                "selected_utility": float(selected["utility"]),
                "selected_passed_strict": bool(selected["passed_strict"]),
                "selected_near_strict": bool(_near_strict(selected)),
                "selected_strict_margin": float(selected["strict_margin"]),
                "selected_business_return": float(selected["business_return"]),
                "selected_cost_return": float(selected["cost_return"]),
                "selected_mean_violation": float(selected["mean_violation"]),
                "selected_final_critical_compromised_hosts": float(
                    selected["final_critical_compromised_hosts"]
                ),
                "selected_high_disruption_action_rate": float(
                    selected["high_disruption_action_rate"]
                ),
            }
            selector_rows[selector_name].append(row)
            per_preference_rows.append(row)

    with per_preference_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(per_preference_rows[0].keys()))
        writer.writeheader()
        for row in per_preference_rows:
            writer.writerow(row)

    selector_summaries = {
        selector_name: _selector_summary(
            selector_rows[selector_name],
            candidate_count=candidate_count,
            strict_candidate_count=strict_candidate_count,
            near_candidate_count=near_candidate_count,
        )
        for selector_name in SELECTOR_ORDER
    }
    diagnosis = diagnose_assignment_problem(
        strict_candidate_count=strict_candidate_count,
        selector_summaries=selector_summaries,
        num_preferences=len(preferences),
    )

    summary_payload: dict[str, Any] = {
        "buffer_path": str(buffer_path.resolve()),
        "source_set": config.source_set,
        "thresholds_path": str(thresholds_path.resolve()),
        "candidate_semantics_path": str(candidate_semantics_path.resolve()),
        "per_preference_csv_path": str(per_preference_path.resolve()),
        "output_dir": str(run_dir.resolve()),
        "profile": strict_profile,
        "candidate_count": int(candidate_count),
        "strict_candidate_count": int(strict_candidate_count),
        "near_candidate_count": int(near_candidate_count),
        "num_preferences": int(len(preferences)),
        "selectors": selector_summaries,
        "diagnosis": diagnosis,
    }

    if diagnosis == "candidate_supply_problem" and bool(config.run_strict_level_on_supply):
        strict_level_outputs = run_strict_level_diagnostics_rows(
            candidate_rows,
            thresholds=thresholds,
            output_root=_resolve_path(anchor, config.strict_level_output_dir),
            run_label=run_label,
            profile_name=config.profile_name,
            high_disruption_max=float(config.high_disruption_max),
            levels=[
                {
                    "name": "L0",
                    "final_critical_max": 1.00,
                    "mean_violation_max": 1.25,
                },
                {
                    "name": "L1",
                    "final_critical_max": 0.95,
                    "mean_violation_max": 1.00,
                },
                {
                    "name": "L2",
                    "final_critical_max": 0.75,
                    "mean_violation_max": 0.75,
                },
                {
                    "name": "L3",
                    "final_critical_max": 0.50,
                    "mean_violation_max": 0.60,
                },
                {
                    "name": "STRICT",
                    "final_critical_max": 0.25,
                    "mean_violation_max": 0.50,
                },
            ],
        )
        summary_payload["strict_level_outputs"] = strict_level_outputs

    save_json(summary_path, summary_payload)
    return {
        "run_dir": str(run_dir.resolve()),
        "candidate_semantics_path": str(candidate_semantics_path.resolve()),
        "per_preference_path": str(per_preference_path.resolve()),
        "summary_path": str(summary_path.resolve()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run replay-only assignment diagnostics on a fixed candidate set."
    )
    parser.add_argument(
        "--config",
        default=str(DEFAULT_ASSIGNMENT_DIAGNOSTICS_CONFIG),
    )
    parser.add_argument("--buffer-path", default=None)
    parser.add_argument("--thresholds-path", default=None)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--run-label", default=None)
    parser.add_argument("--source-set", choices=("pareto", "records"), default=None)
    args = parser.parse_args()

    config = load_assignment_diagnostics_config(args.config)
    if args.buffer_path is not None:
        config.buffer_path = args.buffer_path
    if args.thresholds_path is not None:
        config.thresholds_path = args.thresholds_path
    if args.output_dir is not None:
        config.output_dir = args.output_dir
    if args.run_label is not None:
        config.run_label = args.run_label
    if args.source_set is not None:
        config.source_set = args.source_set
    outputs = run_assignment_diagnostics(config, config_anchor=args.config)
    print(outputs["summary_path"])


if __name__ == "__main__":
    main()
