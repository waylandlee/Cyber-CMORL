from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable, Iterable

from cmorl_minicage.algorithms.assignment import assign_policy
from cmorl_minicage.algorithms.selection import nondominated_filter
from cmorl_minicage.buffer import load_policy_buffer
from cmorl_minicage.evaluate_constraints import (
    _evaluate_actor_critic_record,
    _load_thresholds,
    _resolve_path,
)
from cmorl_minicage.evaluate import expected_utility
from cmorl_minicage.utils import load_json, save_json, simplex_grid

from .export_figure2_attack_defense_trace import resolve_artifact_path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TABLE_A_SUMMARY_PATH = (
    REPO_ROOT / "cmorl_cyborg" / "outputs" / "paper_4obj" / "table_a" / "table_a_summary.json"
)
DEFAULT_THRESHOLDS_PATH = (
    REPO_ROOT / "cmorl_cyborg" / "outputs" / "paper_4obj" / "table_b" / "shared_thresholds.json"
)
DEFAULT_OUTPUT_ROOT = (
    REPO_ROOT / "cmorl_cyborg" / "outputs" / "paper_4obj" / "raw_vs_acceptable_assignment"
)
DEFAULT_PAPER_TABLE_DIR = REPO_ROOT / "paper" / "table"
DEFAULT_SEEDS = (7, 11, 19)
DEFAULT_METHOD_NAME = "ours_stage2_v2_4"
DEFAULT_PREFERENCE_STEP = 0.1
DEFAULT_EVAL_EPISODES = 5

RAW_RULE = "raw_pareto"
ACCEPTABLE_RULE = "acceptable_pareto"
RULE_DISPLAY_NAMES = {
    RAW_RULE: "Raw Pareto Assignment",
    ACCEPTABLE_RULE: "Acceptable Pareto Assignment",
}
SUMMARY_COLUMNS = [
    "assignment_rule",
    "expected_utility",
    "feasible_assignment_rate",
    "mean_violation",
    "final_critical_compromised_hosts",
    "critical_impact_count",
]
PER_SEED_COLUMNS = [
    "seed",
    "rule",
    "assignment_rule",
    "num_preferences",
    "num_assigned_preferences",
    "num_infeasible_preferences",
    "feasible_assignment_rate",
    "expected_utility",
    "mean_violation",
    "replay_feasible_rate",
    "final_critical_compromised_hosts",
    "critical_impact_count",
    "unique_assigned_policies",
    "raw_pareto_size",
    "acceptable_candidate_count",
    "acceptable_pareto_size",
]
ASSIGNMENT_LOG_COLUMNS = [
    "seed",
    "rule",
    "assignment_rule",
    "preference_index",
    "preference",
    "is_assigned",
    "selected_policy_id",
    "selected_objective_vector",
    "utility",
    "is_acceptable",
    "is_raw_pareto",
    "is_acceptable_pareto",
]
REQUIRED_REPLAY_METRICS = (
    "feasible_rate",
    "mean_violation",
    "critical_impact_count",
    "final_critical_compromised_hosts",
)
_VERIFY_TOL = 1e-9

MetricProvider = Callable[..., dict[str, Any]]


def _write_csv(path: str | Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _csv_value(row.get(field, "")) for field in fieldnames})
    return path.resolve()


def _csv_value(value: Any) -> Any:
    if isinstance(value, (list, dict)):
        return json.dumps(value, sort_keys=True)
    if value is None:
        return ""
    return value


def _format_float(value: Any) -> str:
    if value is None:
        return "NA"
    return f"{float(value):.3f}"


def _record_key(seed: int, policy_id: str) -> str:
    return f"{int(seed):04d}:{policy_id}"


def _policy_lookup(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for record in records:
        policy_id = str(record.get("policy_id", ""))
        if not policy_id:
            raise ValueError("Encountered candidate record without policy_id")
        if policy_id in lookup:
            raise ValueError(f"Duplicate policy_id in archive: {policy_id}")
        lookup[policy_id] = record
    return lookup


def _objective_vector(record: dict[str, Any]) -> list[float]:
    vector = record.get("objective_vector")
    if not isinstance(vector, list) or len(vector) < 4:
        raise ValueError(f"Candidate {record.get('policy_id')} must contain a 4-objective vector")
    return [float(value) for value in vector]


def _objective_violations(
    record: dict[str, Any],
    thresholds: dict[str, float],
) -> tuple[float, float, float]:
    vector = _objective_vector(record)
    business_violation = max(0.0, float(thresholds["d_business"]) - vector[1])
    cost_violation = max(0.0, float(thresholds["d_cost"]) - vector[2])
    return business_violation, cost_violation, business_violation + cost_violation


def _is_objective_acceptable(
    record: dict[str, Any],
    thresholds: dict[str, float],
) -> bool:
    _, _, total_violation = _objective_violations(record, thresholds)
    return total_violation <= 1e-12


def _collect_official_runs(
    table_a_summary_path: Path,
    *,
    method_name: str,
    seeds: tuple[int, ...],
) -> list[dict[str, Any]]:
    payload = load_json(table_a_summary_path)
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in payload.get("per_run", []):
        if str(row.get("method_name")) == method_name:
            grouped[int(row.get("seed", -1))].append(row)

    runs: list[dict[str, Any]] = []
    for seed in seeds:
        matched = grouped.get(int(seed), [])
        if len(matched) != 1:
            raise ValueError(
                f"Expected exactly one {method_name} Table A row for seed={seed}, found {len(matched)}"
            )
        row = matched[0]
        artifact_path = resolve_artifact_path(
            str(row["artifact_path"]),
            anchor_path=table_a_summary_path,
        )
        if not artifact_path.exists():
            raise FileNotFoundError(f"Missing archive artifact for seed={seed}: {artifact_path}")
        runs.append(
            {
                "seed": int(seed),
                "method_name": method_name,
                "artifact_path": str(artifact_path.resolve()),
                "metrics_path": str(
                    resolve_artifact_path(
                        str(row["metrics_path"]),
                        anchor_path=table_a_summary_path,
                    ).resolve()
                )
                if row.get("metrics_path")
                else "",
                "expected_utility": float(row["expected_utility"]),
                "num_pareto_records": int(row["num_pareto_records"]),
            }
        )
    return runs


def _build_candidate_manifest_for_seed(
    *,
    seed: int,
    records: list[dict[str, Any]],
    raw_pareto_ids: set[str],
    acceptable_pareto_ids: set[str],
    thresholds: dict[str, float],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in records:
        policy_id = str(record["policy_id"])
        business_violation, cost_violation, total_violation = _objective_violations(
            record,
            thresholds,
        )
        rows.append(
            {
                "seed": int(seed),
                "policy_id": policy_id,
                "checkpoint_path": str(record.get("checkpoint_path", "")),
                "stage": str(record.get("stage", "")),
                "source": str(record.get("source", "")),
                "objective_vector": _objective_vector(record),
                "objective_business_violation": float(business_violation),
                "objective_cost_violation": float(cost_violation),
                "objective_total_violation": float(total_violation),
                "is_objective_acceptable": total_violation <= 1e-12,
                "is_raw_pareto": policy_id in raw_pareto_ids,
                "is_acceptable_pareto": policy_id in acceptable_pareto_ids,
            }
        )
    return rows


def _assignment_log_for_rule(
    *,
    seed: int,
    rule: str,
    policy_set: list[dict[str, Any]],
    preferences: list[list[float]],
    acceptable_ids: set[str],
    raw_pareto_ids: set[str],
    acceptable_pareto_ids: set[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for preference_index, preference in enumerate(preferences):
        if not policy_set:
            rows.append(
                {
                    "seed": int(seed),
                    "rule": rule,
                    "assignment_rule": RULE_DISPLAY_NAMES[rule],
                    "preference_index": int(preference_index),
                    "preference": [float(value) for value in preference],
                    "is_assigned": False,
                    "selected_policy_id": "",
                    "selected_objective_vector": [],
                    "utility": None,
                    "is_acceptable": False,
                    "is_raw_pareto": False,
                    "is_acceptable_pareto": False,
                }
            )
            continue
        assigned = assign_policy(preference, policy_set)
        policy_id = str(assigned["policy_id"])
        rows.append(
            {
                "seed": int(seed),
                "rule": rule,
                "assignment_rule": RULE_DISPLAY_NAMES[rule],
                "preference_index": int(preference_index),
                "preference": [float(value) for value in preference],
                "is_assigned": True,
                "selected_policy_id": policy_id,
                "selected_objective_vector": _objective_vector(assigned),
                "utility": float(assigned["utility"]),
                "is_acceptable": policy_id in acceptable_ids,
                "is_raw_pareto": policy_id in raw_pareto_ids,
                "is_acceptable_pareto": policy_id in acceptable_pareto_ids,
            }
        )
    return rows


def _build_seed_assignments(
    *,
    seed: int,
    records: list[dict[str, Any]],
    thresholds: dict[str, float],
    preference_step: float,
    expected_raw_pareto_count: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    if not records:
        raise ValueError(f"Archive for seed={seed} contains no records")
    obj_dim = len(_objective_vector(records[0]))
    preferences = simplex_grid(preference_step, obj_dim)
    raw_pareto = nondominated_filter(records)
    if len(raw_pareto) != expected_raw_pareto_count:
        raise ValueError(
            f"Raw Pareto count mismatch for seed={seed}: derived={len(raw_pareto)} "
            f"summary={expected_raw_pareto_count}"
        )

    acceptable_candidates = [
        dict(record) for record in records if _is_objective_acceptable(record, thresholds)
    ]
    acceptable_pareto = nondominated_filter(acceptable_candidates)
    raw_pareto_ids = {str(record["policy_id"]) for record in raw_pareto}
    acceptable_ids = {str(record["policy_id"]) for record in acceptable_candidates}
    acceptable_pareto_ids = {str(record["policy_id"]) for record in acceptable_pareto}

    logs = []
    logs.extend(
        _assignment_log_for_rule(
            seed=seed,
            rule=RAW_RULE,
            policy_set=raw_pareto,
            preferences=preferences,
            acceptable_ids=acceptable_ids,
            raw_pareto_ids=raw_pareto_ids,
            acceptable_pareto_ids=acceptable_pareto_ids,
        )
    )
    logs.extend(
        _assignment_log_for_rule(
            seed=seed,
            rule=ACCEPTABLE_RULE,
            policy_set=acceptable_pareto,
            preferences=preferences,
            acceptable_ids=acceptable_ids,
            raw_pareto_ids=raw_pareto_ids,
            acceptable_pareto_ids=acceptable_pareto_ids,
        )
    )
    manifest = _build_candidate_manifest_for_seed(
        seed=seed,
        records=records,
        raw_pareto_ids=raw_pareto_ids,
        acceptable_pareto_ids=acceptable_pareto_ids,
        thresholds=thresholds,
    )
    context = {
        "seed": int(seed),
        "num_preferences": len(preferences),
        "raw_pareto_size": len(raw_pareto),
        "acceptable_candidate_count": len(acceptable_candidates),
        "acceptable_pareto_size": len(acceptable_pareto),
        "raw_expected_utility": expected_utility(raw_pareto, preferences),
    }
    return logs, manifest, context


def _default_metric_provider(
    *,
    buffer_path: Path,
    metadata: dict[str, Any],
    record: dict[str, Any],
    thresholds: dict[str, float],
    eval_episodes: int,
    **_: Any,
) -> dict[str, Any]:
    checkpoint_path = str(record.get("checkpoint_path", ""))
    if not checkpoint_path:
        raise ValueError(f"Selected policy {record.get('policy_id')} is missing checkpoint_path")
    resolved_checkpoint = _resolve_path(buffer_path, checkpoint_path)
    if not resolved_checkpoint.exists():
        raise FileNotFoundError(
            f"Missing checkpoint for selected policy {record.get('policy_id')}: {resolved_checkpoint}"
        )
    baseline_kind = record.get("notes", {}).get("baseline_kind")
    return _evaluate_actor_critic_record(
        resolved_checkpoint,
        metadata,
        thresholds,
        eval_episodes=eval_episodes,
        baseline_kind=baseline_kind,
    )


def _metrics_from_cached_semantics(
    *,
    seed: int,
    record: dict[str, Any],
    thresholds: dict[str, float],
    cached_semantics_by_seed: dict[int, dict[str, dict[str, Any]]],
    fallback_reason: str,
) -> dict[str, Any]:
    policy_id = str(record["policy_id"])
    seed_cache = cached_semantics_by_seed.get(int(seed), {})
    if policy_id not in seed_cache:
        raise ValueError(
            f"No cached semantic metrics are available for selected policy "
            f"{_record_key(seed, policy_id)}"
        )
    _, _, total_violation = _objective_violations(record, thresholds)
    cached = seed_cache[policy_id]
    missing = [
        field
        for field in (
            "critical_impact_count",
            "final_critical_compromised_hosts",
        )
        if field not in cached
    ]
    if missing:
        raise ValueError(
            f"Cached semantic metrics for {_record_key(seed, policy_id)} are missing fields: {missing}"
        )
    return {
        "feasible_rate": 1.0 if total_violation <= 1e-12 else 0.0,
        "mean_violation": float(total_violation),
        "metric_source": "table_a_cached_semantics_plus_objective_constraints",
        "replay_fallback_reason": fallback_reason,
        **{
            key: float(value)
            for key, value in cached.items()
            if isinstance(value, (int, float))
        },
    }


def _validate_replay_metrics(policy_key: str, metrics: dict[str, Any]) -> None:
    missing = [field for field in REQUIRED_REPLAY_METRICS if field not in metrics]
    if missing:
        raise ValueError(f"Replay metrics for {policy_key} are missing fields: {missing}")


def _collect_selected_policy_metrics(
    *,
    selected_policy_ids_by_seed: dict[int, set[str]],
    run_payloads: dict[int, dict[str, Any]],
    run_paths: dict[int, Path],
    thresholds: dict[str, float],
    eval_episodes: int,
    metric_provider: MetricProvider | None,
    cached_semantics_by_seed: dict[int, dict[str, dict[str, Any]]] | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    provider = metric_provider or _default_metric_provider
    cached_semantics_by_seed = cached_semantics_by_seed or {}
    for seed in sorted(selected_policy_ids_by_seed):
        payload = run_payloads[seed]
        lookup = _policy_lookup(list(payload.get("records", [])))
        for policy_id in sorted(selected_policy_ids_by_seed[seed]):
            record = lookup.get(policy_id)
            if record is None:
                raise ValueError(f"Selected policy {policy_id} is missing from seed={seed} archive")
            if not record.get("checkpoint_path"):
                raise ValueError(f"Selected policy {policy_id} is missing checkpoint_path")
            try:
                metrics = provider(
                    seed=seed,
                    policy_id=policy_id,
                    buffer_path=run_paths[seed],
                    metadata=payload.get("metadata", {}),
                    record=record,
                    thresholds=thresholds,
                    eval_episodes=eval_episodes,
                )
            except RuntimeError as exc:
                message = str(exc)
                if metric_provider is not None or (
                    "size mismatch" not in message
                    and "Error(s) in loading state_dict" not in message
                ):
                    raise
                metrics = _metrics_from_cached_semantics(
                    seed=seed,
                    record=record,
                    thresholds=thresholds,
                    cached_semantics_by_seed=cached_semantics_by_seed,
                    fallback_reason=message.splitlines()[0],
                )
            policy_key = _record_key(seed, policy_id)
            _validate_replay_metrics(policy_key, metrics)
            non_numeric_metadata = {
                key: value
                for key, value in metrics.items()
                if key not in REQUIRED_REPLAY_METRICS
                and not isinstance(value, (int, float))
            }
            rows.append(
                {
                    "seed": int(seed),
                    "policy_id": policy_id,
                    "policy_key": policy_key,
                    "objective_vector": _objective_vector(record),
                    **{
                        key: float(metrics[key])
                        for key in REQUIRED_REPLAY_METRICS
                    },
                    **non_numeric_metadata,
                    **{
                        key: float(value)
                        for key, value in metrics.items()
                        if key not in REQUIRED_REPLAY_METRICS
                        and isinstance(value, (int, float))
                    },
                }
            )
    return rows


def _weighted_metric(
    *,
    assigned_policy_ids: list[str],
    seed: int,
    metric_lookup: dict[str, dict[str, Any]],
    metric_name: str,
) -> float | None:
    if not assigned_policy_ids:
        return None
    counts = Counter(assigned_policy_ids)
    total = sum(counts.values())
    value_sum = 0.0
    for policy_id, count in counts.items():
        policy_key = _record_key(seed, policy_id)
        if policy_key not in metric_lookup:
            raise ValueError(f"Missing replay metrics for selected policy {policy_key}")
        value_sum += float(metric_lookup[policy_key][metric_name]) * int(count)
    return float(value_sum / total)


def _mean_or_none(values: list[float | None]) -> float | None:
    present = [float(value) for value in values if value is not None]
    if not present:
        return None
    return float(sum(present) / len(present))


def _build_per_seed_summary(
    *,
    assignment_logs: list[dict[str, Any]],
    selected_policy_metrics: list[dict[str, Any]],
    seed_contexts: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    metric_lookup = {str(row["policy_key"]): row for row in selected_policy_metrics}
    grouped: dict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
    for row in assignment_logs:
        grouped[(int(row["seed"]), str(row["rule"]))].append(row)

    rows: list[dict[str, Any]] = []
    for seed in sorted(seed_contexts):
        context = seed_contexts[seed]
        for rule in (RAW_RULE, ACCEPTABLE_RULE):
            logs = grouped[(seed, rule)]
            if len(logs) != int(context["num_preferences"]):
                raise ValueError(
                    f"Expected {context['num_preferences']} assignment rows for seed={seed} "
                    f"rule={rule}, found {len(logs)}"
                )
            assigned = [row for row in logs if bool(row["is_assigned"])]
            assigned_policy_ids = [str(row["selected_policy_id"]) for row in assigned]
            utility_values = [float(row["utility"]) for row in assigned if row["utility"] is not None]
            feasible_count = sum(1 for row in logs if bool(row["is_acceptable"]))
            rows.append(
                {
                    "seed": int(seed),
                    "rule": rule,
                    "assignment_rule": RULE_DISPLAY_NAMES[rule],
                    "num_preferences": int(context["num_preferences"]),
                    "num_assigned_preferences": len(assigned),
                    "num_infeasible_preferences": len(logs) - len(assigned),
                    "feasible_assignment_rate": float(feasible_count / len(logs)) if logs else 0.0,
                    "expected_utility": (
                        float(sum(utility_values) / len(utility_values))
                        if utility_values
                        else None
                    ),
                    "mean_violation": _weighted_metric(
                        assigned_policy_ids=assigned_policy_ids,
                        seed=seed,
                        metric_lookup=metric_lookup,
                        metric_name="mean_violation",
                    ),
                    "replay_feasible_rate": _weighted_metric(
                        assigned_policy_ids=assigned_policy_ids,
                        seed=seed,
                        metric_lookup=metric_lookup,
                        metric_name="feasible_rate",
                    ),
                    "final_critical_compromised_hosts": _weighted_metric(
                        assigned_policy_ids=assigned_policy_ids,
                        seed=seed,
                        metric_lookup=metric_lookup,
                        metric_name="final_critical_compromised_hosts",
                    ),
                    "critical_impact_count": _weighted_metric(
                        assigned_policy_ids=assigned_policy_ids,
                        seed=seed,
                        metric_lookup=metric_lookup,
                        metric_name="critical_impact_count",
                    ),
                    "unique_assigned_policies": len(set(assigned_policy_ids)),
                    "raw_pareto_size": int(context["raw_pareto_size"]),
                    "acceptable_candidate_count": int(context["acceptable_candidate_count"]),
                    "acceptable_pareto_size": int(context["acceptable_pareto_size"]),
                }
            )
    return rows


def _build_aggregate_summary(per_seed_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in per_seed_rows:
        grouped[str(row["rule"])].append(row)

    rows: list[dict[str, Any]] = []
    for rule in (RAW_RULE, ACCEPTABLE_RULE):
        rule_rows = grouped[rule]
        if not rule_rows:
            raise ValueError(f"Missing per-seed rows for rule={rule}")
        rows.append(
            {
                "rule": rule,
                "assignment_rule": RULE_DISPLAY_NAMES[rule],
                "num_seeds": len(rule_rows),
                "expected_utility": _mean_or_none(
                    [row["expected_utility"] for row in rule_rows]
                ),
                "feasible_assignment_rate": _mean_or_none(
                    [row["feasible_assignment_rate"] for row in rule_rows]
                ),
                "mean_violation": _mean_or_none([row["mean_violation"] for row in rule_rows]),
                "replay_feasible_rate": _mean_or_none(
                    [row["replay_feasible_rate"] for row in rule_rows]
                ),
                "final_critical_compromised_hosts": _mean_or_none(
                    [row["final_critical_compromised_hosts"] for row in rule_rows]
                ),
                "critical_impact_count": _mean_or_none(
                    [row["critical_impact_count"] for row in rule_rows]
                ),
                "num_infeasible_preferences": int(
                    sum(int(row["num_infeasible_preferences"]) for row in rule_rows)
                ),
                "num_preferences": int(sum(int(row["num_preferences"]) for row in rule_rows)),
            }
        )
    return rows


def _write_summary_tex(path: str | Path, rows: list[dict[str, Any]]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        r"\begin{table*}[t]",
        r"\centering",
        r"\small",
        r"\caption{Raw Pareto assignment versus acceptable Pareto assignment on the DA-CPSL Stage~2 archive. Feasible-assignment rate is measured over preference-grid assignments; violation and critical-risk audit metrics are assignment-weighted over selected policies.}",
        r"\label{tab:app-raw-vs-acceptable-assignment}",
        r"\resizebox{\textwidth}{!}{%",
        r"\begin{tabular}{@{}lrrrrr@{}}",
        r"\toprule",
        r"Assignment Rule & Expected Utility & Feasible Assign. Rate & Mean Violation & Final Critical Hosts & Critical Impact Count \\",
        r"\midrule",
    ]
    for row in rows:
        lines.append(
            f"{row['assignment_rule']} & "
            f"{_format_float(row['expected_utility'])} & "
            f"{_format_float(row['feasible_assignment_rate'])} & "
            f"{_format_float(row['mean_violation'])} & "
            f"{_format_float(row['final_critical_compromised_hosts'])} & "
            f"{_format_float(row['critical_impact_count'])} \\\\"
        )
    lines.extend(
        [
            r"\bottomrule",
            r"\end{tabular}%",
            r"}",
            r"\end{table*}",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path.resolve()


def _build_verification_summary(
    *,
    runs: list[dict[str, Any]],
    seed_contexts: dict[int, dict[str, Any]],
    assignment_logs: list[dict[str, Any]],
    seeds: tuple[int, ...],
) -> dict[str, Any]:
    table_a_by_seed = {int(row["seed"]): row for row in runs}
    raw_comparisons: list[dict[str, Any]] = []
    raw_all_match = True
    for seed in seeds:
        context = seed_contexts[int(seed)]
        table_a_row = table_a_by_seed[int(seed)]
        eu_match = math.isclose(
            float(context["raw_expected_utility"]),
            float(table_a_row["expected_utility"]),
            rel_tol=0.0,
            abs_tol=_VERIFY_TOL,
        )
        count_match = int(context["raw_pareto_size"]) == int(table_a_row["num_pareto_records"])
        raw_all_match = raw_all_match and eu_match and count_match
        raw_comparisons.append(
            {
                "seed": int(seed),
                "raw_expected_utility": {
                    "derived": float(context["raw_expected_utility"]),
                    "table_a": float(table_a_row["expected_utility"]),
                    "delta": float(context["raw_expected_utility"])
                    - float(table_a_row["expected_utility"]),
                    "matches": eu_match,
                },
                "raw_pareto_size": {
                    "derived": int(context["raw_pareto_size"]),
                    "table_a": int(table_a_row["num_pareto_records"]),
                    "matches": count_match,
                },
            }
        )

    acceptable_logs = [row for row in assignment_logs if str(row["rule"]) == ACCEPTABLE_RULE]
    acceptable_selected = [row for row in acceptable_logs if bool(row["is_assigned"])]
    acceptable_all_selected_are_acceptable = all(
        bool(row["is_acceptable"]) for row in acceptable_selected
    )
    output_seeds = sorted({int(row["seed"]) for row in assignment_logs})
    seeds_match = output_seeds == sorted(int(seed) for seed in seeds)
    return {
        "schema_version": "0.1.0",
        "seeds": list(seeds),
        "output_seeds": output_seeds,
        "seeds_match": seeds_match,
        "raw_table_a_alignment": {
            "all_match": raw_all_match,
            "comparisons": raw_comparisons,
        },
        "acceptable_assignment": {
            "selected_rows": len(acceptable_selected),
            "all_selected_rows_are_objective_acceptable": acceptable_all_selected_are_acceptable,
        },
        "all_match": raw_all_match
        and seeds_match
        and acceptable_all_selected_are_acceptable,
    }


def export_raw_vs_acceptable_assignment_4obj(
    table_a_summary_path: str | Path = DEFAULT_TABLE_A_SUMMARY_PATH,
    thresholds_path: str | Path = DEFAULT_THRESHOLDS_PATH,
    *,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    paper_table_dir: str | Path = DEFAULT_PAPER_TABLE_DIR,
    seeds: Iterable[int] = DEFAULT_SEEDS,
    method_name: str = DEFAULT_METHOD_NAME,
    preference_step: float = DEFAULT_PREFERENCE_STEP,
    eval_episodes: int = DEFAULT_EVAL_EPISODES,
    metric_provider: MetricProvider | None = None,
) -> dict[str, str]:
    table_a_summary_path = Path(table_a_summary_path).resolve()
    thresholds_path = Path(thresholds_path).resolve()
    output_root = Path(output_root).resolve()
    paper_table_dir = Path(paper_table_dir).resolve()
    seed_tuple = tuple(int(seed) for seed in seeds)
    if not seed_tuple:
        raise ValueError("At least one seed must be provided")

    thresholds = _load_thresholds(thresholds_path)
    runs = _collect_official_runs(
        table_a_summary_path,
        method_name=method_name,
        seeds=seed_tuple,
    )

    run_payloads: dict[int, dict[str, Any]] = {}
    run_paths: dict[int, Path] = {}
    cached_semantics_by_seed: dict[int, dict[str, dict[str, Any]]] = {}
    assignment_logs: list[dict[str, Any]] = []
    candidate_manifest: list[dict[str, Any]] = []
    seed_contexts: dict[int, dict[str, Any]] = {}

    for run in runs:
        seed = int(run["seed"])
        buffer_path = Path(run["artifact_path"]).resolve()
        payload = load_policy_buffer(buffer_path)
        records = list(payload.get("records", []))
        logs, manifest, context = _build_seed_assignments(
            seed=seed,
            records=records,
            thresholds=thresholds,
            preference_step=preference_step,
            expected_raw_pareto_count=int(run["num_pareto_records"]),
        )
        assignment_logs.extend(logs)
        candidate_manifest.extend(manifest)
        seed_contexts[seed] = context
        run_payloads[seed] = payload
        run_paths[seed] = buffer_path
        if run.get("metrics_path"):
            metrics_path = Path(str(run["metrics_path"]))
            if not metrics_path.exists():
                raise FileNotFoundError(
                    f"Missing Table A metrics cache for seed={seed}: {metrics_path}"
                )
            metrics_payload = load_json(metrics_path)
            cached_semantics_by_seed[seed] = {
                str(policy_id): dict(metrics)
                for policy_id, metrics in metrics_payload.get(
                    "semantic_policy_metrics",
                    {},
                ).items()
            }

    selected_policy_ids_by_seed: dict[int, set[str]] = defaultdict(set)
    for row in assignment_logs:
        if bool(row["is_assigned"]):
            selected_policy_ids_by_seed[int(row["seed"])].add(str(row["selected_policy_id"]))
    selected_policy_metrics = _collect_selected_policy_metrics(
        selected_policy_ids_by_seed=selected_policy_ids_by_seed,
        run_payloads=run_payloads,
        run_paths=run_paths,
        thresholds=thresholds,
        eval_episodes=eval_episodes,
        metric_provider=metric_provider,
        cached_semantics_by_seed=cached_semantics_by_seed,
    )
    per_seed_rows = _build_per_seed_summary(
        assignment_logs=assignment_logs,
        selected_policy_metrics=selected_policy_metrics,
        seed_contexts=seed_contexts,
    )
    aggregate_rows = _build_aggregate_summary(per_seed_rows)
    verification_summary = _build_verification_summary(
        runs=runs,
        seed_contexts=seed_contexts,
        assignment_logs=assignment_logs,
        seeds=seed_tuple,
    )

    output_root.mkdir(parents=True, exist_ok=True)
    paper_table_dir.mkdir(parents=True, exist_ok=True)

    candidate_manifest_path = output_root / "candidate_manifest.json"
    selected_policy_metrics_path = output_root / "selected_policy_metrics.json"
    assignment_log_csv_path = output_root / "preference_assignment_log.csv"
    assignment_log_json_path = output_root / "preference_assignment_log.json"
    per_seed_csv_path = output_root / "raw_vs_acceptable_per_seed.csv"
    per_seed_json_path = output_root / "raw_vs_acceptable_per_seed.json"
    summary_csv_path = output_root / "raw_vs_acceptable_summary.csv"
    summary_json_path = output_root / "raw_vs_acceptable_summary.json"
    summary_tex_path = output_root / "raw_vs_acceptable_summary.tex"
    verification_path = output_root / "verification_summary.json"
    paper_tex_path = paper_table_dir / "raw_vs_acceptable_assignment_4obj.tex"

    common_metadata = {
        "schema_version": "0.1.0",
        "table_a_summary_path": str(table_a_summary_path),
        "thresholds_path": str(thresholds_path),
        "method_name": method_name,
        "seeds": list(seed_tuple),
        "preference_step": float(preference_step),
        "eval_episodes": int(eval_episodes),
        "thresholds": thresholds,
    }
    save_json(candidate_manifest_path, {**common_metadata, "records": candidate_manifest})
    save_json(
        selected_policy_metrics_path,
        {**common_metadata, "records": selected_policy_metrics},
    )
    save_json(assignment_log_json_path, {**common_metadata, "records": assignment_logs})
    _write_csv(assignment_log_csv_path, assignment_logs, ASSIGNMENT_LOG_COLUMNS)
    save_json(per_seed_json_path, {**common_metadata, "records": per_seed_rows})
    _write_csv(per_seed_csv_path, per_seed_rows, PER_SEED_COLUMNS)
    save_json(summary_json_path, {**common_metadata, "records": aggregate_rows})
    _write_csv(summary_csv_path, aggregate_rows, SUMMARY_COLUMNS)
    _write_summary_tex(summary_tex_path, aggregate_rows)
    paper_tex_path.write_text(summary_tex_path.read_text(encoding="utf-8"), encoding="utf-8")
    save_json(verification_path, verification_summary)

    if not verification_summary["all_match"]:
        raise ValueError(f"Raw-vs-acceptable verification failed; see {verification_path}")

    return {
        "candidate_manifest_json": str(candidate_manifest_path.resolve()),
        "selected_policy_metrics_json": str(selected_policy_metrics_path.resolve()),
        "preference_assignment_log_csv": str(assignment_log_csv_path.resolve()),
        "preference_assignment_log_json": str(assignment_log_json_path.resolve()),
        "raw_vs_acceptable_per_seed_csv": str(per_seed_csv_path.resolve()),
        "raw_vs_acceptable_per_seed_json": str(per_seed_json_path.resolve()),
        "raw_vs_acceptable_summary_csv": str(summary_csv_path.resolve()),
        "raw_vs_acceptable_summary_json": str(summary_json_path.resolve()),
        "raw_vs_acceptable_summary_tex": str(summary_tex_path.resolve()),
        "paper_raw_vs_acceptable_tex": str(paper_tex_path.resolve()),
        "verification_summary_json": str(verification_path.resolve()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export a raw-Pareto versus acceptable-Pareto assignment appendix table."
    )
    parser.add_argument("--table-a-summary-path", default=str(DEFAULT_TABLE_A_SUMMARY_PATH))
    parser.add_argument("--thresholds-path", default=str(DEFAULT_THRESHOLDS_PATH))
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--paper-table-dir", default=str(DEFAULT_PAPER_TABLE_DIR))
    parser.add_argument("--seeds", nargs="+", type=int, default=list(DEFAULT_SEEDS))
    parser.add_argument("--method-name", default=DEFAULT_METHOD_NAME)
    parser.add_argument("--preference-step", type=float, default=DEFAULT_PREFERENCE_STEP)
    parser.add_argument("--eval-episodes", type=int, default=DEFAULT_EVAL_EPISODES)
    args = parser.parse_args()
    outputs = export_raw_vs_acceptable_assignment_4obj(
        table_a_summary_path=args.table_a_summary_path,
        thresholds_path=args.thresholds_path,
        output_root=args.output_root,
        paper_table_dir=args.paper_table_dir,
        seeds=args.seeds,
        method_name=args.method_name,
        preference_step=args.preference_step,
        eval_episodes=args.eval_episodes,
    )
    print(json.dumps(outputs, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
