from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import yaml

from cmorl_minicage.algorithms.assignment import assign_policy
from cmorl_minicage.algorithms.selection import nondominated_filter
from cmorl_minicage.buffer import load_policy_buffer
from cmorl_minicage.utils import load_json, save_json, simplex_grid

from .export_figure2_attack_defense_trace import resolve_artifact_path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TABLE_A_SUMMARY_PATH = (
    REPO_ROOT / "cmorl_cyborg" / "outputs" / "paper_4obj" / "table_a" / "table_a_summary.json"
)
DEFAULT_TABLE_B_SUMMARY_PATH = (
    REPO_ROOT / "cmorl_cyborg" / "outputs" / "paper_4obj" / "table_b" / "table_b_summary.json"
)
DEFAULT_OUTPUT_ROOT = (
    REPO_ROOT / "cmorl_cyborg" / "outputs" / "paper_4obj" / "threshold_sensitivity"
)
DEFAULT_PAPER_TABLE_DIR = REPO_ROOT / "paper" / "table"
DEFAULT_SEEDS = (7, 11, 19)
DEFAULT_PREFERENCE_STEP = 0.1

METHOD_ORDER = (
    "ours_stage2_v2_4",
    "stage1_only_4obj",
    "weighted_sum_4obj",
    "lagrangian_ppo_4obj",
    "no_constraint_stage2_4obj",
)
ARCHIVE_METHODS = (
    "ours_stage2_v2_4",
    "stage1_only_4obj",
    "weighted_sum_4obj",
)
BUFFER_TABLE_B_METHODS = ("no_constraint_stage2_4obj",)
SINGLE_POLICY_TABLE_B_METHODS = ("lagrangian_ppo_4obj",)
PROFILE_SPECS = (
    ("looser", 0.10),
    ("default", 0.25),
    ("stricter", 0.50),
)
DISPLAY_FALLBACKS = {
    "ours_stage2_v2_4": "DA-CPSL",
    "stage1_only_4obj": "Stage-1 Only",
    "weighted_sum_4obj": "Weighted-Sum",
    "lagrangian_ppo_4obj": "Lagrangian PPO",
    "no_constraint_stage2_4obj": "Unconstrained Stage-2",
}
PAPER_DISPLAY_NAMES = {
    "ours_stage2_v2_4": "Constraint-Aware Stage-2",
    "stage1_only_4obj": "Stage-1 Archive",
    "weighted_sum_4obj": "Weighted-Sum",
    "lagrangian_ppo_4obj": "Lagrangian PPO",
    "no_constraint_stage2_4obj": "Unconstrained Stage-2",
}
AUDIT_FIELDS = (
    "critical_impact_count",
    "final_critical_compromised_hosts",
    "ever_critical_breach_rate",
    "persistent_critical_breach_rate",
)
ASSIGNMENT_COLUMNS = [
    "seed",
    "method_name",
    "display_group",
    "threshold_profile",
    "threshold_quantile",
    "d_business",
    "d_cost",
    "preference_index",
    "preference",
    "selected_policy_id",
    "selected_objective_vector",
    "utility",
    "business_violation",
    "cost_violation",
    "mean_violation",
    "is_feasible",
    "is_raw_pareto",
]
PER_SEED_COLUMNS = [
    "seed",
    "method_name",
    "display_group",
    "threshold_profile",
    "threshold_quantile",
    "d_business",
    "d_cost",
    "num_preferences",
    "unique_selected_policies",
    "feasible_assignment_rate",
    "mean_violation",
    "business_violation",
    "cost_violation",
    "mean_utility",
    "candidate_count",
    "raw_pareto_size",
    *[f"table_b_replay_{field}" for field in AUDIT_FIELDS],
]
SUMMARY_COLUMNS = [
    "threshold_profile",
    "threshold_quantile",
    "d_business",
    "d_cost",
    "method_name",
    "display_group",
    "num_seeds",
    "feasible_assignment_rate",
    "feasible_assignment_rate_std",
    "mean_violation",
    "mean_violation_std",
    "mean_utility",
    "mean_utility_std",
    *[
        column
        for field in AUDIT_FIELDS
        for column in (f"table_b_replay_{field}", f"table_b_replay_{field}_std")
    ],
]
_TOL = 1e-9


def _load_yaml(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"YAML config must contain a mapping: {path}")
    return payload


def _write_csv(path: str | Path, rows: list[dict[str, Any]], columns: list[str]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: _csv_value(row.get(column, "")) for column in columns})
    return path.resolve()


def _csv_value(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True)
    if value is None:
        return ""
    return value


def _format_float(value: Any) -> str:
    return f"{float(value):.3f}"


def _objective_vector(record: dict[str, Any]) -> list[float]:
    vector = record.get("objective_vector")
    if not isinstance(vector, list) or len(vector) != 4:
        raise ValueError(
            f"Candidate {record.get('policy_id', '<unknown>')} must contain a 4-objective vector"
        )
    return [float(value) for value in vector]


def _policy_id(record: dict[str, Any]) -> str:
    policy_id = str(record.get("policy_id", ""))
    if not policy_id:
        raise ValueError("Encountered candidate record without policy_id")
    return policy_id


def _violations(vector: list[float], profile: dict[str, Any]) -> tuple[float, float, float]:
    business_violation = max(0.0, float(profile["d_business"]) - float(vector[1]))
    cost_violation = max(0.0, float(profile["d_cost"]) - float(vector[2]))
    return business_violation, cost_violation, business_violation + cost_violation


def _mean(values: Iterable[float]) -> float:
    values = [float(value) for value in values]
    if not values:
        raise ValueError("Cannot average an empty list")
    return float(sum(values) / len(values))


def _mean_or_none(values: Iterable[Any]) -> float | None:
    present = [float(value) for value in values if value is not None]
    if not present:
        return None
    return _mean(present)


def _std(values: Iterable[float]) -> float:
    values = [float(value) for value in values]
    if len(values) <= 1:
        return 0.0
    return float(statistics.pstdev(values))


def _std_or_none(values: Iterable[Any]) -> float | None:
    present = [float(value) for value in values if value is not None]
    if not present:
        return None
    return _std(present)


def _load_shared_thresholds(path: str | Path) -> dict[str, float]:
    payload = load_json(path)
    return {"d_business": float(payload["d_business"]), "d_cost": float(payload["d_cost"])}


def _profile_thresholds(
    threshold_buffer_paths: list[Path],
    shared_thresholds_path: Path,
) -> dict[str, dict[str, Any]]:
    if not threshold_buffer_paths:
        raise ValueError("No threshold calibration buffers were provided")
    business_values: list[float] = []
    cost_values: list[float] = []
    for path in threshold_buffer_paths:
        if not path.exists():
            raise FileNotFoundError(f"Missing threshold calibration buffer: {path}")
        payload = load_policy_buffer(path)
        pareto_front = payload.get("pareto_front", [])
        if not pareto_front:
            raise ValueError(f"Threshold calibration buffer has an empty Pareto front: {path}")
        for record in pareto_front:
            vector = np.asarray(record["objective_vector"], dtype=np.float32)
            business_values.append(float(vector[1]))
            cost_values.append(float(vector[2]))

    profiles: dict[str, dict[str, Any]] = {}
    for name, quantile in PROFILE_SPECS:
        profiles[name] = {
            "threshold_profile": name,
            "threshold_quantile": float(quantile),
            "d_business": float(np.quantile(np.asarray(business_values), quantile)),
            "d_cost": float(np.quantile(np.asarray(cost_values), quantile)),
        }

    shared = _load_shared_thresholds(shared_thresholds_path)
    default = profiles["default"]
    if not math.isclose(default["d_business"], shared["d_business"], abs_tol=_TOL) or not math.isclose(
        default["d_cost"], shared["d_cost"], abs_tol=_TOL
    ):
        raise ValueError("Default threshold profile does not match official shared thresholds")
    return profiles


def _profiles_from_summary(table_b_summary_path: Path, shared_thresholds_path: Path) -> dict[str, dict[str, Any]]:
    payload = load_json(table_b_summary_path)
    paths = [
        resolve_artifact_path(str(path), anchor_path=table_b_summary_path)
        for path in payload.get("threshold_buffer_paths", [])
    ]
    return _profile_thresholds(paths, shared_thresholds_path)


def _profiles_from_config(table_b_config_path: Path, shared_thresholds_path: Path) -> dict[str, dict[str, Any]]:
    payload = _load_yaml(table_b_config_path)
    paths = [
        resolve_artifact_path(str(source["path"]), anchor_path=table_b_config_path)
        for source in payload.get("threshold_buffer_sources", [])
        if source.get("path")
    ]
    return _profile_thresholds(paths, shared_thresholds_path)


def _archive_runs_from_summary(
    table_a_summary_path: Path,
    seeds: tuple[int, ...],
) -> dict[tuple[str, int], dict[str, Any]]:
    payload = load_json(table_a_summary_path)
    grouped: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in payload.get("per_run", []):
        method = str(row.get("method_name"))
        if method in ARCHIVE_METHODS:
            grouped[(method, int(row.get("seed", -1)))].append(row)

    runs: dict[tuple[str, int], dict[str, Any]] = {}
    for method in ARCHIVE_METHODS:
        for seed in seeds:
            matched = grouped.get((method, int(seed)), [])
            if len(matched) != 1:
                raise ValueError(
                    f"Expected exactly one Table A archive row for method={method} seed={seed}"
                )
            row = matched[0]
            path = resolve_artifact_path(str(row["artifact_path"]), anchor_path=table_a_summary_path)
            if not path.exists():
                raise FileNotFoundError(f"Missing archive artifact for method={method} seed={seed}: {path}")
            runs[(method, int(seed))] = {
                "method_name": method,
                "display_group": str(row.get("display_group") or DISPLAY_FALLBACKS[method]),
                "seed": int(seed),
                "input_kind": "buffer",
                "artifact_path": str(path.resolve()),
            }
    return runs


def _archive_runs_from_config(
    compare_config_path: Path,
    seeds: tuple[int, ...],
) -> dict[tuple[str, int], dict[str, Any]]:
    payload = _load_yaml(compare_config_path)
    grouped: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in payload.get("entries", []):
        method = str(row.get("method_name"))
        if method in ARCHIVE_METHODS:
            grouped[(method, int(row.get("seed", -1)))].append(row)

    runs: dict[tuple[str, int], dict[str, Any]] = {}
    for method in ARCHIVE_METHODS:
        for seed in seeds:
            matched = grouped.get((method, int(seed)), [])
            if len(matched) != 1:
                raise ValueError(f"Missing compare-config archive entry for method={method} seed={seed}")
            row = matched[0]
            path = resolve_artifact_path(str(row["artifact_path"]), anchor_path=compare_config_path)
            if not path.exists():
                raise FileNotFoundError(f"Missing archive artifact for method={method} seed={seed}: {path}")
            runs[(method, int(seed))] = {
                "method_name": method,
                "display_group": str(row.get("display_group") or DISPLAY_FALLBACKS[method]),
                "seed": int(seed),
                "input_kind": "buffer",
                "artifact_path": str(path.resolve()),
            }
    return runs


def _table_b_runs_from_summary(
    table_b_summary_path: Path,
    seeds: tuple[int, ...],
) -> dict[tuple[str, int], dict[str, Any]]:
    payload = load_json(table_b_summary_path)
    grouped: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    wanted = set(BUFFER_TABLE_B_METHODS + SINGLE_POLICY_TABLE_B_METHODS)
    for row in payload.get("per_run_records", []):
        method = str(row.get("method_name"))
        if method in wanted:
            grouped[(method, int(row.get("seed", -1)))].append(row)

    runs: dict[tuple[str, int], dict[str, Any]] = {}
    for method in BUFFER_TABLE_B_METHODS + SINGLE_POLICY_TABLE_B_METHODS:
        for seed in seeds:
            matched = grouped.get((method, int(seed)), [])
            if len(matched) != 1:
                raise ValueError(f"Expected exactly one Table B row for method={method} seed={seed}")
            row = matched[0]
            path = resolve_artifact_path(str(row["input_path"]), anchor_path=table_b_summary_path)
            if not path.exists():
                raise FileNotFoundError(f"Missing Table-B artifact for method={method} seed={seed}: {path}")
            runs[(method, int(seed))] = {
                "method_name": method,
                "display_group": DISPLAY_FALLBACKS[method],
                "seed": int(seed),
                "input_kind": str(row.get("input_kind", "buffer")),
                "artifact_path": str(path.resolve()),
            }
    return runs


def _table_b_runs_from_config(
    table_b_config_path: Path,
    seeds: tuple[int, ...],
) -> dict[tuple[str, int], dict[str, Any]]:
    payload = _load_yaml(table_b_config_path)
    grouped: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    wanted = set(BUFFER_TABLE_B_METHODS + SINGLE_POLICY_TABLE_B_METHODS)
    for row in payload.get("entries", []):
        method = str(row.get("method_name"))
        if method in wanted:
            grouped[(method, int(row.get("seed", -1)))].append(row)

    runs: dict[tuple[str, int], dict[str, Any]] = {}
    for method in BUFFER_TABLE_B_METHODS:
        for seed in seeds:
            matched = grouped.get((method, int(seed)), [])
            if len(matched) != 1:
                raise ValueError(f"Missing Table-B buffer entry for method={method} seed={seed}")
            row = matched[0]
            path = resolve_artifact_path(str(row["input_path"]), anchor_path=table_b_config_path)
            if not path.exists():
                raise FileNotFoundError(f"Missing Table-B artifact for method={method} seed={seed}: {path}")
            runs[(method, int(seed))] = {
                "method_name": method,
                "display_group": DISPLAY_FALLBACKS[method],
                "seed": int(seed),
                "input_kind": "buffer",
                "artifact_path": str(path.resolve()),
            }
    for method in SINGLE_POLICY_TABLE_B_METHODS:
        for seed in seeds:
            matched = grouped.get((method, int(seed)), [])
            if len(matched) != 1:
                raise ValueError(f"Missing Table-B single-policy entry for method={method} seed={seed}")
            row = matched[0]
            path = resolve_artifact_path(str(row["input_path"]), anchor_path=table_b_config_path)
            if not path.exists():
                raise FileNotFoundError(f"Missing Table-B artifact for method={method} seed={seed}: {path}")
            runs[(method, int(seed))] = {
                "method_name": method,
                "display_group": DISPLAY_FALLBACKS[method],
                "seed": int(seed),
                "input_kind": "single_policy",
                "artifact_path": str(path.resolve()),
            }
    return runs


def _audit_metrics_from_summary(
    table_b_summary_path: Path,
    seeds: tuple[int, ...],
) -> dict[tuple[str, int], dict[str, float]]:
    payload = load_json(table_b_summary_path)
    metrics: dict[tuple[str, int], dict[str, float]] = {}
    allowed_seeds = {int(seed) for seed in seeds}
    for row in payload.get("per_run_records", []):
        method = str(row.get("method_name"))
        seed = int(row.get("seed", -1))
        if method not in METHOD_ORDER or seed not in allowed_seeds or not row.get("output_path"):
            continue
        path = resolve_artifact_path(str(row["output_path"]), anchor_path=table_b_summary_path)
        if not path.exists():
            continue
        payload = load_json(path)
        metrics[(method, seed)] = {
            f"table_b_replay_{field}": float(payload[field])
            for field in AUDIT_FIELDS
            if field in payload
        }
    return metrics


def _ordered_runs(
    archive_runs: dict[tuple[str, int], dict[str, Any]],
    table_b_runs: dict[tuple[str, int], dict[str, Any]],
    seeds: tuple[int, ...],
) -> list[dict[str, Any]]:
    lookup = {**archive_runs, **table_b_runs}
    rows: list[dict[str, Any]] = []
    for seed in seeds:
        for method in METHOD_ORDER:
            key = (method, int(seed))
            if key not in lookup:
                raise ValueError(f"Missing run artifact for method={method} seed={seed}")
            rows.append(lookup[key])
    return rows


def _single_policy_record(path: Path) -> dict[str, Any]:
    payload = load_json(path)
    vector = payload.get("final_objective_vector")
    if not isinstance(vector, list):
        raise ValueError(f"Single-policy metadata is missing final_objective_vector: {path}")
    checkpoint_path = str(payload.get("checkpoint_path", ""))
    if not checkpoint_path:
        raise ValueError(f"Single-policy metadata is missing checkpoint_path: {path}")
    return {
        "policy_id": str(payload.get("policy_id") or path.parent.name),
        "checkpoint_path": checkpoint_path,
        "objective_vector": [float(value) for value in vector],
        "stage": "single_policy",
        "source": str(payload.get("method_name", "")),
    }


def _load_policy_set(run: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    path = Path(str(run["artifact_path"]))
    if str(run["input_kind"]) == "single_policy":
        record = _single_policy_record(path)
        _policy_id(record)
        _objective_vector(record)
        return [record], {"candidate_count": 1, "raw_pareto_size": 1}

    payload = load_policy_buffer(path)
    records = [dict(record) for record in payload.get("records", [])]
    if not records:
        raise ValueError(f"Archive contains no records: {path}")
    for record in records:
        _policy_id(record)
        _objective_vector(record)
    pareto = nondominated_filter(records)
    return pareto, {"candidate_count": len(records), "raw_pareto_size": len(pareto)}


def _assignment_rows_for_run(
    run: dict[str, Any],
    policy_set: list[dict[str, Any]],
    profiles: dict[str, dict[str, Any]],
    preference_step: float,
) -> list[dict[str, Any]]:
    preferences = simplex_grid(preference_step, 4)
    pareto_ids = {_policy_id(record) for record in policy_set}
    rows: list[dict[str, Any]] = []
    for profile_name, profile in profiles.items():
        for index, preference in enumerate(preferences):
            assigned = assign_policy(preference, policy_set)
            policy_id = _policy_id(assigned)
            vector = _objective_vector(assigned)
            business_violation, cost_violation, total_violation = _violations(vector, profile)
            rows.append(
                {
                    "seed": int(run["seed"]),
                    "method_name": str(run["method_name"]),
                    "display_group": str(run["display_group"]),
                    "threshold_profile": profile_name,
                    "threshold_quantile": float(profile["threshold_quantile"]),
                    "d_business": float(profile["d_business"]),
                    "d_cost": float(profile["d_cost"]),
                    "preference_index": int(index),
                    "preference": [float(value) for value in preference],
                    "selected_policy_id": policy_id,
                    "selected_objective_vector": vector,
                    "utility": float(assigned["utility"]),
                    "business_violation": float(business_violation),
                    "cost_violation": float(cost_violation),
                    "mean_violation": float(total_violation),
                    "is_feasible": total_violation <= 1e-12,
                    "is_raw_pareto": policy_id in pareto_ids,
                }
            )
    return rows


def _per_seed_summary(
    assignment_rows: list[dict[str, Any]],
    contexts: dict[tuple[str, int], dict[str, int]],
    audit_metrics: dict[tuple[str, int], dict[str, float]],
    seeds: tuple[int, ...],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[int, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in assignment_rows:
        grouped[(int(row["seed"]), str(row["method_name"]), str(row["threshold_profile"]))].append(row)

    rows: list[dict[str, Any]] = []
    for seed in seeds:
        for method in METHOD_ORDER:
            for profile_name, _ in PROFILE_SPECS:
                logs = grouped[(int(seed), method, profile_name)]
                if not logs:
                    raise ValueError(f"Missing assignment rows for method={method} seed={seed} profile={profile_name}")
                audit = audit_metrics.get((method, int(seed)), {})
                rows.append(
                    {
                        "seed": int(seed),
                        "method_name": method,
                        "display_group": logs[0]["display_group"],
                        "threshold_profile": profile_name,
                        "threshold_quantile": float(logs[0]["threshold_quantile"]),
                        "d_business": float(logs[0]["d_business"]),
                        "d_cost": float(logs[0]["d_cost"]),
                        "num_preferences": len(logs),
                        "unique_selected_policies": len({str(row["selected_policy_id"]) for row in logs}),
                        "feasible_assignment_rate": float(sum(bool(row["is_feasible"]) for row in logs) / len(logs)),
                        "mean_violation": _mean(float(row["mean_violation"]) for row in logs),
                        "business_violation": _mean(float(row["business_violation"]) for row in logs),
                        "cost_violation": _mean(float(row["cost_violation"]) for row in logs),
                        "mean_utility": _mean(float(row["utility"]) for row in logs),
                        **contexts[(method, int(seed))],
                        **{column: audit.get(column) for column in PER_SEED_COLUMNS if column.startswith("table_b_replay_")},
                    }
                )
    return rows


def _summary_rows(per_seed_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in per_seed_rows:
        grouped[(str(row["threshold_profile"]), str(row["method_name"]))].append(row)

    rows: list[dict[str, Any]] = []
    for profile_name, _ in PROFILE_SPECS:
        for method in METHOD_ORDER:
            method_rows = grouped[(profile_name, method)]
            audit_values: dict[str, float | None] = {}
            for field in AUDIT_FIELDS:
                key = f"table_b_replay_{field}"
                values = [row.get(key) for row in method_rows]
                audit_values[key] = _mean_or_none(values)
                audit_values[f"{key}_std"] = _std_or_none(values)
            rows.append(
                {
                    "threshold_profile": profile_name,
                    "threshold_quantile": float(method_rows[0]["threshold_quantile"]),
                    "d_business": float(method_rows[0]["d_business"]),
                    "d_cost": float(method_rows[0]["d_cost"]),
                    "method_name": method,
                    "display_group": method_rows[0]["display_group"],
                    "num_seeds": len(method_rows),
                    "feasible_assignment_rate": _mean(row["feasible_assignment_rate"] for row in method_rows),
                    "feasible_assignment_rate_std": _std(row["feasible_assignment_rate"] for row in method_rows),
                    "mean_violation": _mean(row["mean_violation"] for row in method_rows),
                    "mean_violation_std": _std(row["mean_violation"] for row in method_rows),
                    "mean_utility": _mean(row["mean_utility"] for row in method_rows),
                    "mean_utility_std": _std(row["mean_utility"] for row in method_rows),
                    **audit_values,
                }
            )
    return rows


def _write_tex(path: str | Path, rows: list[dict[str, Any]]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        r"\begin{table*}[t]",
        r"\centering",
        r"\small",
        r"\caption{Operational-threshold sensitivity under looser, default, and stricter business/cost limits. Feasible-assignment rate and mean violation are computed over preference-grid assignments from each method's raw Pareto candidates.}",
        r"\label{tab:app-threshold-sensitivity}",
        r"\resizebox{\textwidth}{!}{%",
        r"\begin{tabular}{@{}llrr@{}}",
        r"\toprule",
        r"Threshold Profile & Method & Feasible Assign. Rate & Mean Violation \\",
        r"\midrule",
    ]
    current = None
    for row in rows:
        profile = str(row["threshold_profile"]).title()
        if current is not None and current != profile:
            lines.append(r"\addlinespace")
        current = profile
        lines.append(
            f"{profile} & "
            f"{PAPER_DISPLAY_NAMES.get(str(row['method_name']), str(row['display_group']))} & "
            f"{_format_float(row['feasible_assignment_rate'])} & "
            f"{_format_float(row['mean_violation'])} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}%", r"}", r"\end{table*}"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path.resolve()


def _verification(
    profiles: dict[str, dict[str, Any]],
    shared_thresholds: dict[str, float],
    assignment_rows: list[dict[str, Any]],
    per_seed_rows: list[dict[str, Any]],
    summary_rows: list[dict[str, Any]],
    seeds: tuple[int, ...],
    num_preferences: int,
) -> dict[str, Any]:
    profile_names = list(profiles)
    profile_match = profile_names == [name for name, _ in PROFILE_SPECS]
    default = profiles["default"]
    default_business_match = math.isclose(default["d_business"], shared_thresholds["d_business"], abs_tol=_TOL)
    default_cost_match = math.isclose(default["d_cost"], shared_thresholds["d_cost"], abs_tol=_TOL)
    default_match = default_business_match and default_cost_match
    ordering_match = (
        profiles["looser"]["d_business"] <= profiles["default"]["d_business"] <= profiles["stricter"]["d_business"]
        and profiles["looser"]["d_cost"] <= profiles["default"]["d_cost"] <= profiles["stricter"]["d_cost"]
    )
    expected_assignment = len(METHOD_ORDER) * len(seeds) * len(profiles) * int(num_preferences)
    expected_per_seed = len(METHOD_ORDER) * len(seeds) * len(profiles)
    expected_summary = len(METHOD_ORDER) * len(profiles)
    output_seeds = sorted({int(row["seed"]) for row in assignment_rows})
    output_methods = sorted({str(row["method_name"]) for row in assignment_rows})
    output_profiles = sorted({str(row["threshold_profile"]) for row in assignment_rows})
    seed_match = output_seeds == sorted(seeds)
    method_match = output_methods == sorted(METHOD_ORDER)
    profile_coverage_match = output_profiles == sorted(profiles)
    row_counts = {
        "assignment_log_rows": {
            "observed": len(assignment_rows),
            "expected": expected_assignment,
            "matches": len(assignment_rows) == expected_assignment,
        },
        "per_seed_rows": {
            "observed": len(per_seed_rows),
            "expected": expected_per_seed,
            "matches": len(per_seed_rows) == expected_per_seed,
        },
        "summary_rows": {
            "observed": len(summary_rows),
            "expected": expected_summary,
            "matches": len(summary_rows) == expected_summary,
        },
    }
    row_count_checks = {
        "assignment_log": row_counts["assignment_log_rows"],
        "per_seed_summary": row_counts["per_seed_rows"],
        "aggregate_summary": row_counts["summary_rows"],
    }
    all_match = (
        profile_match
        and ordering_match
        and default_match
        and seed_match
        and method_match
        and profile_coverage_match
        and all(check["matches"] for check in row_counts.values())
    )
    return {
        "schema_version": "0.1.0",
        "profile_names": profile_names,
        "profile_name_match": profile_match,
        "profile_ordering_match": ordering_match,
        "default_threshold_alignment": {
            "matches": default_match,
            "d_business": {
                "derived": default["d_business"],
                "shared": shared_thresholds["d_business"],
                "matches": default_business_match,
            },
            "d_cost": {
                "derived": default["d_cost"],
                "shared": shared_thresholds["d_cost"],
                "matches": default_cost_match,
            },
        },
        "default_threshold_alignment_match": default_match,
        "row_counts": row_counts,
        "row_count_checks": row_count_checks,
        "method_coverage": {
            "observed": output_methods,
            "expected": sorted(METHOD_ORDER),
            "matches": method_match,
        },
        "seed_coverage": {
            "observed": output_seeds,
            "expected": sorted(seeds),
            "matches": seed_match,
        },
        "profile_coverage": {
            "observed": output_profiles,
            "expected": sorted(profiles),
            "matches": profile_coverage_match,
        },
        "all_match": all_match,
    }


def export_threshold_sensitivity_4obj(
    table_a_summary_path: str | Path = DEFAULT_TABLE_A_SUMMARY_PATH,
    table_b_summary_path: str | Path = DEFAULT_TABLE_B_SUMMARY_PATH,
    *,
    compare_config_path: str | Path | None = None,
    table_b_config_path: str | Path | None = None,
    official_thresholds_path: str | Path | None = None,
    shared_thresholds_path: str | Path | None = None,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    paper_table_dir: str | Path = DEFAULT_PAPER_TABLE_DIR,
    seeds: Iterable[int] = DEFAULT_SEEDS,
    preference_step: float = DEFAULT_PREFERENCE_STEP,
) -> dict[str, str]:
    seed_tuple = tuple(int(seed) for seed in seeds)
    if not seed_tuple:
        raise ValueError("At least one seed must be provided")

    table_a_summary_path = Path(table_a_summary_path).resolve()
    table_b_summary_path = Path(table_b_summary_path).resolve()
    compare_config = Path(compare_config_path).resolve() if compare_config_path else None
    table_b_config = Path(table_b_config_path).resolve() if table_b_config_path else None
    if shared_thresholds_path is None and official_thresholds_path is not None:
        shared_thresholds_path = official_thresholds_path

    if table_b_config is not None:
        table_b_config_payload = _load_yaml(table_b_config)
        raw_thresholds_path = shared_thresholds_path or table_b_config_payload["shared_thresholds_path"]
        thresholds_path = resolve_artifact_path(str(raw_thresholds_path), anchor_path=table_b_config)
        profiles = _profiles_from_config(table_b_config, thresholds_path)
        if compare_config is None:
            raise ValueError("compare_config_path must be provided with table_b_config_path")
        archive_runs = _archive_runs_from_config(compare_config, seed_tuple)
        table_b_runs = _table_b_runs_from_config(table_b_config, seed_tuple)
        audit_metrics: dict[tuple[str, int], dict[str, float]] = {}
    else:
        table_b_summary = load_json(table_b_summary_path)
        raw_thresholds_path = shared_thresholds_path or table_b_summary.get(
            "shared_thresholds_path",
            REPO_ROOT / "cmorl_cyborg" / "outputs" / "paper_4obj" / "table_b" / "shared_thresholds.json",
        )
        thresholds_path = resolve_artifact_path(str(raw_thresholds_path), anchor_path=table_b_summary_path)
        profiles = _profiles_from_summary(table_b_summary_path, thresholds_path)
        archive_runs = _archive_runs_from_summary(table_a_summary_path, seed_tuple)
        table_b_runs = _table_b_runs_from_summary(table_b_summary_path, seed_tuple)
        audit_metrics = _audit_metrics_from_summary(table_b_summary_path, seed_tuple)

    shared_thresholds = _load_shared_thresholds(thresholds_path)
    runs = _ordered_runs(archive_runs, table_b_runs, seed_tuple)
    preferences = simplex_grid(preference_step, 4)

    assignment_rows: list[dict[str, Any]] = []
    contexts: dict[tuple[str, int], dict[str, int]] = {}
    for run in runs:
        policy_set, context = _load_policy_set(run)
        contexts[(str(run["method_name"]), int(run["seed"]))] = context
        assignment_rows.extend(_assignment_rows_for_run(run, policy_set, profiles, preference_step))

    per_seed_rows = _per_seed_summary(assignment_rows, contexts, audit_metrics, seed_tuple)
    summary_rows = _summary_rows(per_seed_rows)
    verification = _verification(
        profiles,
        shared_thresholds,
        assignment_rows,
        per_seed_rows,
        summary_rows,
        seed_tuple,
        len(preferences),
    )

    output_root = Path(output_root).resolve()
    paper_table_dir = Path(paper_table_dir).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    paper_table_dir.mkdir(parents=True, exist_ok=True)

    threshold_profiles_path = output_root / "threshold_profiles.json"
    assignment_json_path = output_root / "threshold_sensitivity_assignment_log.json"
    assignment_csv_path = output_root / "threshold_sensitivity_assignment_log.csv"
    per_seed_json_path = output_root / "threshold_sensitivity_per_seed.json"
    per_seed_csv_path = output_root / "threshold_sensitivity_per_seed.csv"
    summary_json_path = output_root / "threshold_sensitivity_summary.json"
    summary_csv_path = output_root / "threshold_sensitivity_summary.csv"
    summary_tex_path = output_root / "threshold_sensitivity_summary.tex"
    verification_path = output_root / "verification_summary.json"
    paper_tex_path = paper_table_dir / "threshold_sensitivity_4obj.tex"

    metadata = {
        "schema_version": "0.1.0",
        "table_a_summary_path": str(table_a_summary_path),
        "table_b_summary_path": str(table_b_summary_path),
        "shared_thresholds_path": str(thresholds_path),
        "compare_config_path": str(compare_config) if compare_config is not None else "",
        "table_b_config_path": str(table_b_config) if table_b_config is not None else "",
        "seeds": list(seed_tuple),
        "methods": list(METHOD_ORDER),
        "preference_step": float(preference_step),
        "num_preferences": len(preferences),
    }
    save_json(threshold_profiles_path, profiles)
    save_json(assignment_json_path, {**metadata, "records": assignment_rows})
    _write_csv(assignment_csv_path, assignment_rows, ASSIGNMENT_COLUMNS)
    save_json(per_seed_json_path, {**metadata, "records": per_seed_rows})
    _write_csv(per_seed_csv_path, per_seed_rows, PER_SEED_COLUMNS)
    save_json(summary_json_path, {**metadata, "records": summary_rows})
    _write_csv(summary_csv_path, summary_rows, SUMMARY_COLUMNS)
    _write_tex(summary_tex_path, summary_rows)
    paper_tex_path.write_text(summary_tex_path.read_text(encoding="utf-8"), encoding="utf-8")
    save_json(verification_path, verification)

    if not verification["all_match"]:
        raise ValueError(f"Threshold-sensitivity verification failed; see {verification_path}")

    return {
        "threshold_profiles_json": str(threshold_profiles_path),
        "threshold_sensitivity_assignment_log_json": str(assignment_json_path),
        "threshold_sensitivity_assignment_log_csv": str(assignment_csv_path),
        "threshold_sensitivity_per_seed_json": str(per_seed_json_path),
        "threshold_sensitivity_per_seed_csv": str(per_seed_csv_path),
        "threshold_sensitivity_summary_json": str(summary_json_path),
        "threshold_sensitivity_summary_csv": str(summary_csv_path),
        "threshold_sensitivity_summary_tex": str(summary_tex_path),
        "paper_threshold_sensitivity_tex": str(paper_tex_path),
        "verification_summary_json": str(verification_path),
        "assignment_log_json": str(assignment_json_path),
        "assignment_log_csv": str(assignment_csv_path),
        "per_seed_json": str(per_seed_json_path),
        "per_seed_csv": str(per_seed_csv_path),
        "summary_json": str(summary_json_path),
        "summary_csv": str(summary_csv_path),
        "summary_tex": str(summary_tex_path),
        "paper_tex": str(paper_tex_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export operational-threshold sensitivity artifacts for the 4-objective paper suite."
    )
    parser.add_argument("--table-a-summary-path", default=str(DEFAULT_TABLE_A_SUMMARY_PATH))
    parser.add_argument("--table-b-summary-path", default=str(DEFAULT_TABLE_B_SUMMARY_PATH))
    parser.add_argument("--compare-config-path", default=None)
    parser.add_argument("--table-b-config-path", default=None)
    parser.add_argument("--shared-thresholds-path", default=None)
    parser.add_argument("--official-thresholds-path", default=None)
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--paper-table-dir", default=str(DEFAULT_PAPER_TABLE_DIR))
    parser.add_argument("--seeds", nargs="+", type=int, default=list(DEFAULT_SEEDS))
    parser.add_argument("--preference-step", type=float, default=DEFAULT_PREFERENCE_STEP)
    args = parser.parse_args()
    outputs = export_threshold_sensitivity_4obj(
        table_a_summary_path=args.table_a_summary_path,
        table_b_summary_path=args.table_b_summary_path,
        compare_config_path=args.compare_config_path,
        table_b_config_path=args.table_b_config_path,
        shared_thresholds_path=args.shared_thresholds_path,
        official_thresholds_path=args.official_thresholds_path,
        output_root=args.output_root,
        paper_table_dir=args.paper_table_dir,
        seeds=args.seeds,
        preference_step=args.preference_step,
    )
    print(json.dumps(outputs, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
