from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import yaml

from cmorl_minicage.algorithms.assignment import assign_policy
from cmorl_minicage.algorithms.selection import nondominated_filter
from cmorl_minicage.buffer import load_policy_buffer
from cmorl_minicage.evaluate import hypervolume, resolve_reference_point
from cmorl_minicage.utils import ensure_dir, load_json, save_json, simplex_grid

from .evaluate_constraints import evaluate_constraints, write_aggregated_constraint_metrics
from .export_candidate_semantic_audit import (
    DEFAULT_CRITICAL_HOST,
    DEFAULT_CRITICAL_PATH_HOSTS,
    export_candidate_semantic_audit,
)
from .export_figure2_attack_defense_trace import (
    Figure2ReplayCandidate,
    export_candidate_trace,
    resolve_artifact_path,
)
from .export_figure2_trace_analysis import export_figure2_trace_analysis
from .export_rq3_symmetric_analysis import _collect_metric_consistency
from .export_semantic_risk_summary import build_method_comparison_semantic_summary


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = (
    REPO_ROOT / "cmorl_cyborg" / "outputs" / "paper_ablation" / "objective_3obj_vs_4obj"
)
DEFAULT_3OBJ_COMPARE_CONFIG = REPO_ROOT / "cmorl_cyborg" / "configs" / "paper" / "compare_suite_main.yaml"
DEFAULT_4OBJ_TABLE_B_SUMMARY = (
    REPO_ROOT / "cmorl_cyborg" / "outputs" / "paper_4obj" / "table_b" / "table_b_summary.json"
)
DEFAULT_4OBJ_THRESHOLDS_PATH = (
    REPO_ROOT / "cmorl_cyborg" / "outputs" / "paper_4obj" / "table_b" / "shared_thresholds.json"
)
DEFAULT_PAPER_PROJECTED_SET_TABLE_PATH = (
    REPO_ROOT / "paper" / "table" / "rq4_objective_projected_set_quality.tex"
)
DEFAULT_PAPER_SEMANTIC_APPENDIX_TABLE_PATH = (
    REPO_ROOT / "paper" / "table" / "rq4_objective_semantic_full_audit.tex"
)
DEFAULT_PAPER_SELECTED_POLICIES_TABLE_PATH = (
    REPO_ROOT / "paper" / "table" / "rq4_objective_selected_policies.tex"
)

DEFAULT_SEEDS = (7, 11, 19)
DEFAULT_EVAL_EPISODES = 20
DEFAULT_DEPLOYMENT_EVAL_EPISODES = 5
DEFAULT_PREFERENCE_STEP = 0.1
DEFAULT_REFERENCE_STRATEGY = "data_min_range"
DEFAULT_REFERENCE_MARGIN = 0.25
DEFAULT_HV_MAX_EXACT_POINTS = 18
DEFAULT_HV_MC_SAMPLES = 100000

LEFT_METHOD_NAME = "ours_stage2"
RIGHT_METHOD_NAME = "ours_stage2_v2_4"

METHOD_DISPLAY = {
    LEFT_METHOD_NAME: "3-Objective Stage-2",
    RIGHT_METHOD_NAME: "4-Objective Stage-2",
}

PROJECTED_SET_METRICS = (
    ("projected_hypervolume_3d", "Projected 3D Hypervolume"),
    ("projected_expected_utility_3d", "Projected 3D Expected Utility"),
)
DEPLOYMENT_METRICS = (
    ("feasible_rate", "Feasible Rate"),
    ("mean_violation", "Mean Violation"),
)
SEMANTIC_METRICS = (
    ("ever_critical_breach_rate", "Ever Critical Breach"),
    ("persistent_critical_breach_rate", "Persistent Critical Breach"),
    ("Q4_user_focus_after_enterprise_foothold", "Post-Foothold Drift (Q4)"),
    ("Q5_repeated_low_value_decoy_loop", "Repeated Low-Value Decoy Loop (Q5)"),
)


@dataclass(frozen=True)
class ObjectiveAuditArtifact:
    method_name: str
    display_name: str
    seed: int
    policy_id: str
    trace_dir: Path
    audit_dir: Path
    risk_summary_path: Path
    trace_analysis_dir: Path


def _load_yaml(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"Expected YAML mapping: {path}")
    return payload


def _canonicalize_path(raw_path: str | Path, *, anchor_path: str | Path | None = None) -> Path:
    return resolve_artifact_path(raw_path, anchor_path=anchor_path)


def _write_csv(path: Path, rows: list[dict[str, Any]], *, fieldnames: list[str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
    return path.resolve()


def _latex_escape(value: Any) -> str:
    text = str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "_": r"\_",
        "&": r"\&",
        "%": r"\%",
        "#": r"\#",
        "{": r"\{",
        "}": r"\}",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def _repo_relative_path(value: str | Path) -> str:
    path = Path(value).resolve()
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _compact_audit_dir(value: str | Path) -> str:
    path = Path(value).resolve()
    audits_root = (
        DEFAULT_OUTPUT_ROOT / "semantic_comparison" / "audits"
    ).resolve()
    try:
        return str(path.relative_to(audits_root))
    except ValueError:
        return _repo_relative_path(path)


def _mean_std(values: list[float]) -> dict[str, float]:
    array = np.asarray(values, dtype=np.float64)
    return {
        "mean": float(np.mean(array)) if len(array) else 0.0,
        "std": float(np.std(array)) if len(array) else 0.0,
    }


def _format_metric_value(metric_key: str, value: float) -> str:
    if "hypervolume" in metric_key:
        return f"{float(value) / 1_000_000.0:.3f}"
    if "expected_utility" in metric_key:
        return f"{float(value):.3f}"
    return f"{float(value):.3f}"


def _write_metric_table_tex(
    path: Path,
    *,
    title: str,
    left_display_name: str,
    right_display_name: str,
    rows: list[dict[str, Any]],
) -> Path:
    lines = [
        r"\centering",
        r"\setlength{\tabcolsep}{3pt}",
        r"\resizebox{\textwidth}{!}{%",
        r"\begin{tabular}{lcc}",
        r"\toprule",
        rf"\multicolumn{{3}}{{l}}{{\textbf{{{title}}}}} \\",
        rf"Metric & {left_display_name} & {right_display_name} \\",
        r"\midrule",
    ]
    for row in rows:
        lines.append(
            f"{row['metric_label']} & "
            f"{_format_metric_value(str(row['metric_key']), float(row['left_mean']))} & "
            f"{_format_metric_value(str(row['metric_key']), float(row['right_mean']))} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}%", r"}"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path.resolve()


def _write_selected_policy_table_tex(
    path: Path,
    *,
    rows: list[dict[str, Any]],
) -> Path:
    lines = [
        r"\centering",
        r"\setlength{\tabcolsep}{3pt}",
        r"\resizebox{\textwidth}{!}{%",
        r"\begin{tabular}{lp{0.22\textwidth}p{0.22\textwidth}p{0.22\textwidth}p{0.22\textwidth}}",
        r"\toprule",
        r"Seed & 3-Objective Selected Policy & 4-Objective Selected Policy & 3-Objective Audit Dir & 4-Objective Audit Dir \\",
        r"\midrule",
    ]
    for row in rows:
        left_audit_dir = _compact_audit_dir(str(row["left_audit_dir"]))
        right_audit_dir = _compact_audit_dir(str(row["right_audit_dir"]))
        lines.append(
            f"{int(row['seed']):04d} & "
            f"\\texttt{{{_latex_escape(row['left_policy_id'])}}} & "
            f"\\texttt{{{_latex_escape(row['right_policy_id'])}}} & "
            f"\\nolinkurl{{{_latex_escape(left_audit_dir)}}} & "
            f"\\nolinkurl{{{_latex_escape(right_audit_dir)}}} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}%", r"}"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path.resolve()


def _write_semantic_appendix_table(
    aggregate_payload: dict[str, Any],
    *,
    output_path: Path,
) -> Path:
    left = aggregate_payload["left"]
    right = aggregate_payload["right"]
    left_name = aggregate_payload["left_display_name"]
    right_name = aggregate_payload["right_display_name"]

    def _fmt(value: float) -> str:
        return f"{float(value):.3f}"

    lines = [
        r"\centering",
        r"\setlength{\tabcolsep}{3pt}",
        r"\resizebox{\textwidth}{!}{%",
        r"\begin{tabular}{lccccccccc}",
        r"\toprule",
        r"Method & Ever & Persist & Dwell & High-Conf. & Tier~0 Safe & Tier~1 Near-Miss & Tier~2 Transient & Tier~3 Persistent \\",
        r"\midrule",
        f"{left_name} & {_fmt(left['ever_critical_breach_rate'])} & {_fmt(left['persistent_critical_breach_rate'])} & {_fmt(left['mean_critical_dwell_steps'])} & {_fmt(left['high_confidence_env_run_rate'])} & {_fmt(left['Tier 0 Safe'])} & {_fmt(left['Tier 1 Near-Miss'])} & {_fmt(left['Tier 2 Transient Critical Breach'])} & {_fmt(left['Tier 3 Persistent Critical Breach'])} \\\\",
        f"{right_name} & {_fmt(right['ever_critical_breach_rate'])} & {_fmt(right['persistent_critical_breach_rate'])} & {_fmt(right['mean_critical_dwell_steps'])} & {_fmt(right['high_confidence_env_run_rate'])} & {_fmt(right['Tier 0 Safe'])} & {_fmt(right['Tier 1 Near-Miss'])} & {_fmt(right['Tier 2 Transient Critical Breach'])} & {_fmt(right['Tier 3 Persistent Critical Breach'])} \\\\",
        r"\bottomrule",
        r"\end{tabular}%",
        r"}",
        r"",
        r"\vspace{0.4em}",
        r"",
        r"\resizebox{\textwidth}{!}{%",
        r"\begin{tabular}{lccccccc}",
        r"\toprule",
        r"Method & Q2 User Action During Critical & Q3 Missed Immediate Critical Response & Q4 Post-Foothold Drift & Q5 Repeated Low-Value Decoy Loop & Pre-Restore & Pre-Decoy & Pre-Focus \\",
        r"\midrule",
        f"{left_name} & {_fmt(left['Q2_user_action_during_critical_breach'])} & {_fmt(left['Q3_missed_immediate_response_to_critical_hit'])} & {_fmt(left['Q4_user_focus_after_enterprise_foothold'])} & {_fmt(left['Q5_repeated_low_value_decoy_loop'])} & {_fmt(left['precritical_action_family_step_rates.restore'])} & {_fmt(left['precritical_action_family_step_rates.decoy'])} & {_fmt(left['precritical_compromised_target_focus_step_rate'])} \\\\",
        f"{right_name} & {_fmt(right['Q2_user_action_during_critical_breach'])} & {_fmt(right['Q3_missed_immediate_response_to_critical_hit'])} & {_fmt(right['Q4_user_focus_after_enterprise_foothold'])} & {_fmt(right['Q5_repeated_low_value_decoy_loop'])} & {_fmt(right['precritical_action_family_step_rates.restore'])} & {_fmt(right['precritical_action_family_step_rates.decoy'])} & {_fmt(right['precritical_compromised_target_focus_step_rate'])} \\\\",
        r"\bottomrule",
        r"\end{tabular}%",
        r"}",
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path.resolve()


def _compare_entry_buffer_paths(
    config_path: Path,
    *,
    method_name: str,
    seeds: Iterable[int],
) -> dict[int, Path]:
    config = _load_yaml(config_path)
    wanted = {int(seed) for seed in seeds}
    resolved: dict[int, Path] = {}
    for entry in config.get("entries", []):
        if str(entry.get("method_name")) != method_name:
            continue
        seed = int(entry.get("seed", -1))
        if seed not in wanted:
            continue
        raw_path = entry.get("artifact_path") or entry.get("artifact_path_glob")
        if raw_path is None:
            continue
        resolved[seed] = _canonicalize_path(raw_path, anchor_path=config_path)
    missing = sorted(wanted - set(resolved))
    if missing:
        raise ValueError(f"Missing {method_name} compare-suite buffers for seeds={missing}")
    return resolved


def _metrics_paths_for_method(
    *,
    root_dir: Path,
    method_name: str,
    seeds: Iterable[int],
) -> dict[int, Path]:
    resolved: dict[int, Path] = {}
    for seed in seeds:
        path = root_dir / method_name / f"seed_{int(seed):04d}" / "metrics_shared_ref.json"
        if not path.exists():
            raise FileNotFoundError(path)
        resolved[int(seed)] = path.resolve()
    return resolved


def _project_record(record: dict[str, Any]) -> dict[str, Any]:
    projected = dict(record)
    vector = list(record.get("objective_vector", []) or [])
    if len(vector) < 3:
        raise ValueError(f"Expected objective vector with at least 3 dimensions: {vector}")
    projected["objective_vector"] = [float(vector[idx]) for idx in range(3)]
    return projected


def _build_projected_set_quality(
    *,
    output_root: Path,
    left_metrics_paths: dict[int, Path],
    right_metrics_paths: dict[int, Path],
    preference_step: float = DEFAULT_PREFERENCE_STEP,
    reference_strategy: str = DEFAULT_REFERENCE_STRATEGY,
    reference_margin: float = DEFAULT_REFERENCE_MARGIN,
    hv_max_exact_points: int = DEFAULT_HV_MAX_EXACT_POINTS,
    hv_mc_samples: int = DEFAULT_HV_MC_SAMPLES,
    paper_table_path: Path = DEFAULT_PAPER_PROJECTED_SET_TABLE_PATH,
) -> dict[str, Any]:
    all_points: list[list[float]] = []
    seed_rows: list[dict[str, Any]] = []
    projected_cache: dict[tuple[str, int], list[dict[str, Any]]] = {}
    metrics_paths_by_method = {
        LEFT_METHOD_NAME: left_metrics_paths,
        RIGHT_METHOD_NAME: right_metrics_paths,
    }

    for method_name, seed_lookup in metrics_paths_by_method.items():
        for seed, metrics_path in seed_lookup.items():
            payload = load_json(metrics_path)
            projected_pareto = nondominated_filter(
                [_project_record(record) for record in payload.get("pareto_front", [])]
            )
            if not projected_pareto:
                raise ValueError(f"Projected pareto_front is empty for {metrics_path}")
            projected_cache[(method_name, seed)] = projected_pareto
            all_points.extend(
                [list(record["objective_vector"]) for record in projected_pareto]
            )

    reference_point = resolve_reference_point(
        np.asarray(all_points, dtype=np.float32),
        obj_dim=3,
        reference_strategy=reference_strategy,
        reference_margin=reference_margin,
        reference_point=None,
    ).tolist()
    preferences = simplex_grid(preference_step, 3)

    for method_name, seed_lookup in metrics_paths_by_method.items():
        for seed, metrics_path in seed_lookup.items():
            projected_pareto = projected_cache[(method_name, seed)]
            points = np.asarray(
                [record["objective_vector"] for record in projected_pareto],
                dtype=np.float32,
            )
            hv_value, hv_method = hypervolume(
                points,
                reference_point,
                max_exact_points=hv_max_exact_points,
                mc_samples=hv_mc_samples,
            )
            assignments = [assign_policy(preference, projected_pareto) for preference in preferences]
            assignment_counts: dict[str, int] = defaultdict(int)
            for assigned in assignments:
                assignment_counts[str(assigned.get("policy_id", ""))] += 1
            seed_rows.append(
                {
                    "method_name": method_name,
                    "display_name": METHOD_DISPLAY[method_name],
                    "seed": int(seed),
                    "metrics_path": str(metrics_path.resolve()),
                    "projected_dimensions": ["security", "business", "cost"],
                    "projected_pareto_count": len(projected_pareto),
                    "projected_hypervolume_3d": float(hv_value),
                    "projected_hypervolume_method": hv_method,
                    "projected_expected_utility_3d": float(
                        np.mean([float(entry["utility"]) for entry in assignments])
                    )
                    if assignments
                    else 0.0,
                    "coverage_ratio": float(
                        len(assignment_counts) / len(projected_pareto)
                    ),
                    "unique_assigned_policies": int(len(assignment_counts)),
                }
            )

    method_summary: list[dict[str, Any]] = []
    for method_name in (LEFT_METHOD_NAME, RIGHT_METHOD_NAME):
        rows = [row for row in seed_rows if row["method_name"] == method_name]
        entry = {
            "method_name": method_name,
            "display_name": METHOD_DISPLAY[method_name],
            "num_runs": len(rows),
        }
        for metric_key in (
            "projected_hypervolume_3d",
            "projected_expected_utility_3d",
            "coverage_ratio",
            "unique_assigned_policies",
        ):
            entry[metric_key] = _mean_std([float(row[metric_key]) for row in rows])
        method_summary.append(entry)

    payload = {
        "comparison_name": "rq4_objective_ablation_projected_3d",
        "left_method_name": LEFT_METHOD_NAME,
        "left_display_name": METHOD_DISPLAY[LEFT_METHOD_NAME],
        "right_method_name": RIGHT_METHOD_NAME,
        "right_display_name": METHOD_DISPLAY[RIGHT_METHOD_NAME],
        "projected_dimensions": ["security", "business", "cost"],
        "reference_strategy": reference_strategy,
        "reference_margin": float(reference_margin),
        "reference_point": [float(value) for value in reference_point],
        "preference_step": float(preference_step),
        "preference_count": len(preferences),
        "seed_rows": seed_rows,
        "method_summary": method_summary,
        "source_paths": {
            "left_metrics_paths": {
                str(seed): str(path.resolve()) for seed, path in sorted(left_metrics_paths.items())
            },
            "right_metrics_paths": {
                str(seed): str(path.resolve()) for seed, path in sorted(right_metrics_paths.items())
            },
        },
    }

    summary_json = output_root / "projected_set_quality_summary.json"
    summary_csv = output_root / "projected_set_quality_summary.csv"
    summary_tex = output_root / "projected_set_quality_summary.tex"
    save_json(summary_json, payload)
    _write_csv(
        summary_csv,
        seed_rows,
        fieldnames=[
            "method_name",
            "display_name",
            "seed",
            "projected_pareto_count",
            "projected_hypervolume_3d",
            "projected_expected_utility_3d",
            "coverage_ratio",
            "unique_assigned_policies",
            "metrics_path",
        ],
    )

    method_lookup = {entry["method_name"]: entry for entry in method_summary}
    projected_rows = [
        {
            "metric_key": metric_key,
            "metric_label": metric_label,
            "left_mean": method_lookup[LEFT_METHOD_NAME][metric_key]["mean"],
            "right_mean": method_lookup[RIGHT_METHOD_NAME][metric_key]["mean"],
        }
        for metric_key, metric_label in (
            ("projected_hypervolume_3d", "Projected 3D Hypervolume"),
            ("projected_expected_utility_3d", "Projected 3D Expected Utility"),
            ("coverage_ratio", "Coverage Ratio"),
            ("unique_assigned_policies", "Unique Assigned Policies"),
        )
    ]
    _write_metric_table_tex(
        summary_tex,
        title="Projected 3D Set-Quality Summary",
        left_display_name=METHOD_DISPLAY[LEFT_METHOD_NAME],
        right_display_name=METHOD_DISPLAY[RIGHT_METHOD_NAME],
        rows=projected_rows,
    )
    _write_metric_table_tex(
        paper_table_path,
        title="Projected 3D Set-Quality Summary",
        left_display_name=METHOD_DISPLAY[LEFT_METHOD_NAME],
        right_display_name=METHOD_DISPLAY[RIGHT_METHOD_NAME],
        rows=projected_rows,
    )

    verification_payload = {
        "all_projected_dimensions_match": all(
            len(_project_record(record)["objective_vector"]) == 3
            for rows in projected_cache.values()
            for record in rows
        ),
        "reference_point_length": len(reference_point),
        "reference_point_shared": len(reference_point) == 3,
        "preference_count": len(preferences),
    }
    save_json(output_root / "verification" / "projected_set_quality_sanity.json", verification_payload)

    return {
        "summary_json": str(summary_json.resolve()),
        "summary_csv": str(summary_csv.resolve()),
        "summary_tex": str(summary_tex.resolve()),
        "paper_table_path": str(paper_table_path.resolve()),
        "payload": payload,
    }


def _table_b_record(table_b_summary_path: Path, *, method_name: str, seed: int) -> dict[str, Any]:
    summary = load_json(table_b_summary_path)
    for record in summary.get("per_run_records", []):
        if str(record.get("method_name")) == method_name and int(record.get("seed", -1)) == int(seed):
            result = dict(record)
            for key in ("input_path", "output_path"):
                if result.get(key):
                    result[key] = str(
                        _canonicalize_path(result[key], anchor_path=table_b_summary_path)
                    )
            return result
    raise KeyError(
        f"Missing table_b record for method={method_name} seed={seed} in {table_b_summary_path}"
    )


def _build_matched_deployment(
    *,
    output_root: Path,
    left_buffer_paths: dict[int, Path],
    table_b_summary_path: Path,
    thresholds_path: Path,
    deployment_eval_episodes: int = DEFAULT_DEPLOYMENT_EVAL_EPISODES,
) -> dict[str, Any]:
    thresholds = load_json(thresholds_path)
    matched_root = ensure_dir(output_root / "matched_deployment")
    aggregated_root = ensure_dir(matched_root / "aggregated")

    metrics_paths_by_method: dict[str, list[Path]] = defaultdict(list)
    per_seed_records: list[dict[str, Any]] = []
    for seed in sorted(left_buffer_paths):
        left_metrics = evaluate_constraints(
            method_name=LEFT_METHOD_NAME,
            input_kind="buffer",
            input_path=left_buffer_paths[seed],
            selection_source="pareto",
            selection_policy="objective",
            thresholds_path=thresholds_path,
            eval_episodes=int(deployment_eval_episodes),
        )
        left_output_path = matched_root / LEFT_METHOD_NAME / f"seed_{seed:04d}" / "constraint_metrics.json"
        save_json(left_output_path, left_metrics)
        metrics_paths_by_method[LEFT_METHOD_NAME].append(left_output_path)
        per_seed_records.append(
            {
                "method_name": LEFT_METHOD_NAME,
                "display_name": METHOD_DISPLAY[LEFT_METHOD_NAME],
                "seed": int(seed),
                "input_kind": "buffer",
                "input_path": str(left_buffer_paths[seed].resolve()),
                "output_path": str(left_output_path.resolve()),
                "selected_policy_id": str(left_metrics.get("selected_policy_id", "")),
                "thresholds_path": str(thresholds_path.resolve()),
                "thresholds": thresholds,
            }
        )

        right_record = _table_b_record(
            table_b_summary_path,
            method_name=RIGHT_METHOD_NAME,
            seed=seed,
        )
        right_metrics = load_json(right_record["output_path"])
        right_metrics["source_output_path"] = str(right_record["output_path"])
        right_metrics["source_input_path"] = str(right_record["input_path"])
        right_output_path = matched_root / RIGHT_METHOD_NAME / f"seed_{seed:04d}" / "constraint_metrics.json"
        save_json(right_output_path, right_metrics)
        metrics_paths_by_method[RIGHT_METHOD_NAME].append(right_output_path)
        per_seed_records.append(
            {
                "method_name": RIGHT_METHOD_NAME,
                "display_name": METHOD_DISPLAY[RIGHT_METHOD_NAME],
                "seed": int(seed),
                "input_kind": str(right_record.get("input_kind", "single_policy")),
                "input_path": str(Path(right_record["input_path"]).resolve()),
                "output_path": str(right_output_path.resolve()),
                "selected_policy_id": str(right_metrics.get("selected_policy_id", right_metrics.get("policy_id", ""))),
                "thresholds_path": str(thresholds_path.resolve()),
                "thresholds": thresholds,
            }
        )

    aggregate_paths: dict[str, Path] = {}
    method_summary: list[dict[str, Any]] = []
    for method_name in (LEFT_METHOD_NAME, RIGHT_METHOD_NAME):
        aggregate_path = aggregated_root / f"{method_name}.json"
        write_aggregated_constraint_metrics(
            [str(path.resolve()) for path in metrics_paths_by_method[method_name]],
            aggregate_path,
            method_name=method_name,
        )
        aggregate_paths[method_name] = aggregate_path
        payload = load_json(aggregate_path)
        payload["display_name"] = METHOD_DISPLAY[method_name]
        method_summary.append(payload)

    summary_payload = {
        "comparison_name": "rq4_objective_ablation_matched_deployment",
        "left_method_name": LEFT_METHOD_NAME,
        "left_display_name": METHOD_DISPLAY[LEFT_METHOD_NAME],
        "right_method_name": RIGHT_METHOD_NAME,
        "right_display_name": METHOD_DISPLAY[RIGHT_METHOD_NAME],
        "thresholds_source_path": str(thresholds_path.resolve()),
        "thresholds": thresholds,
        "deployment_eval_episodes": int(deployment_eval_episodes),
        "method_summary": method_summary,
        "aggregate_paths": {
            method_name: str(path.resolve()) for method_name, path in aggregate_paths.items()
        },
        "per_seed_records": sorted(per_seed_records, key=lambda row: (row["method_name"], row["seed"])),
    }

    summary_json = matched_root / "matched_deployment_summary.json"
    summary_csv = matched_root / "matched_deployment_summary.csv"
    summary_tex = matched_root / "matched_deployment_summary.tex"
    save_json(summary_json, summary_payload)

    method_lookup = {entry["method_name"]: entry for entry in method_summary}
    metric_rows = [
        {
            "metric_key": metric_key,
            "metric_label": metric_label,
            "left_mean": float(method_lookup[LEFT_METHOD_NAME][metric_key]),
            "right_mean": float(method_lookup[RIGHT_METHOD_NAME][metric_key]),
        }
        for metric_key, metric_label in (
            ("feasible_rate", "Feasible Rate"),
            ("mean_violation", "Mean Violation"),
            ("security_return", "Security Return"),
            ("business_return", "Business Return"),
            ("cost_return", "Cost Return"),
            ("high_disruption_action_rate", "High-Disruption Action Rate"),
        )
    ]
    _write_csv(
        summary_csv,
        metric_rows,
        fieldnames=["metric_key", "metric_label", "left_mean", "right_mean"],
    )
    _write_metric_table_tex(
        summary_tex,
        title="Matched Deployment Summary under 4obj Thresholds",
        left_display_name=METHOD_DISPLAY[LEFT_METHOD_NAME],
        right_display_name=METHOD_DISPLAY[RIGHT_METHOD_NAME],
        rows=metric_rows,
    )

    protocol_rows = []
    for row in sorted(per_seed_records, key=lambda value: (value["seed"], value["method_name"])):
        protocol_rows.append(
            {
                "method_name": row["method_name"],
                "seed": int(row["seed"]),
                "selected_policy_id": str(row["selected_policy_id"]),
                "thresholds_path": str(row["thresholds_path"]),
                "uses_4obj_thresholds": str(row["thresholds_path"]) == str(thresholds_path.resolve()),
            }
        )
    save_json(
        output_root / "verification" / "protocol_match.json",
        {
            "seeds": [int(seed) for seed in sorted(left_buffer_paths)],
            "thresholds_source_path": str(thresholds_path.resolve()),
            "rows": protocol_rows,
        },
    )

    return {
        "summary_json": str(summary_json.resolve()),
        "summary_csv": str(summary_csv.resolve()),
        "summary_tex": str(summary_tex.resolve()),
        "payload": summary_payload,
        "aggregate_paths": aggregate_paths,
    }


def _buffer_record_lookup(buffer_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for record in list(buffer_payload.get("records", [])) + list(buffer_payload.get("pareto_front", [])):
        policy_id = str(record.get("policy_id", ""))
        if policy_id and policy_id not in lookup:
            lookup[policy_id] = record
    return lookup


def _trace_artifact_completeness(artifacts: Iterable[ObjectiveAuditArtifact], *, eval_episodes: int) -> dict[str, Any]:
    required_trace = ("trace_manifest.json", "episode_summaries.json", "topology_snapshot.json")
    required_audit = (
        "risk_tier_summary.json",
        "critical_casebook.md",
        "questionable_defense_actions.csv",
    )
    required_analysis = (
        "timeline_table.csv",
        "timeline_table.md",
        "host_level_summary.csv",
        "host_attack_defense_heatmap.png",
    )
    rows: list[dict[str, Any]] = []
    for artifact in artifacts:
        trace_checks = {
            name: (artifact.trace_dir / name).exists() for name in required_trace
        }
        audit_checks = {
            name: (artifact.audit_dir / name).exists() for name in required_audit
        }
        analysis_checks = {
            name: (artifact.trace_analysis_dir / name).exists() for name in required_analysis
        }
        episode_count = len(list(artifact.trace_dir.glob("episode_*.jsonl")))
        rows.append(
            {
                "method_name": artifact.method_name,
                "seed": int(artifact.seed),
                "policy_id": artifact.policy_id,
                "trace_complete": all(trace_checks.values()) and episode_count == int(eval_episodes),
                "audit_complete": all(audit_checks.values()),
                "trace_analysis_complete": all(analysis_checks.values()),
                "episode_file_count": episode_count,
                "expected_episode_file_count": int(eval_episodes),
                "trace_checks": trace_checks,
                "audit_checks": audit_checks,
                "trace_analysis_checks": analysis_checks,
            }
        )
    return {"rows": rows, "all_required_present": all(
        row["trace_complete"] and row["audit_complete"] and row["trace_analysis_complete"]
        for row in rows
    )}


def _build_objective_semantic_comparison(
    *,
    output_root: Path,
    matched_deployment_summary: dict[str, Any],
    table_b_summary_path: Path,
    eval_episodes: int,
    paper_appendix_table_path: Path,
    paper_selected_policies_table_path: Path,
) -> dict[str, Any]:
    semantic_root = ensure_dir(output_root / "semantic_comparison")
    trace_root = ensure_dir(semantic_root / "traces")
    audit_root = ensure_dir(semantic_root / "audits")
    trace_analysis_root = ensure_dir(semantic_root / "trace_analysis")
    verification_root = ensure_dir(output_root / "verification")

    per_seed_lookup: dict[tuple[str, int], dict[str, Any]] = {}
    for row in matched_deployment_summary.get("per_seed_records", []):
        per_seed_lookup[(str(row["method_name"]), int(row["seed"]))] = row

    artifacts: list[ObjectiveAuditArtifact] = []
    comparison_seed_inputs: list[Path] = []
    selected_policy_rows: list[dict[str, Any]] = []

    for seed in DEFAULT_SEEDS:
        left_row = per_seed_lookup[(LEFT_METHOD_NAME, int(seed))]
        right_row = per_seed_lookup[(RIGHT_METHOD_NAME, int(seed))]

        per_method_artifacts: dict[str, ObjectiveAuditArtifact] = {}
        for row in (left_row, right_row):
            method_name = str(row["method_name"])
            policy_id = str(row["selected_policy_id"])
            input_path = Path(str(row["input_path"])).resolve()
            input_kind = str(row["input_kind"])
            candidate = Figure2ReplayCandidate(
                policy_id=policy_id,
                candidate_label="selected",
                candidate_aliases=("selected",),
            )
            if input_kind == "single_policy":
                metadata = load_json(input_path)
                record = {"checkpoint_path": metadata.get("checkpoint_path")}
                trace_dir = export_candidate_trace(
                    method_name=method_name,
                    seed=int(seed),
                    candidate=candidate,
                    buffer_path=input_path,
                    buffer_anchor_path=input_path,
                    record=record,
                    metadata=metadata,
                    output_root=trace_root,
                    eval_episodes=int(eval_episodes),
                )
            else:
                buffer_payload = load_policy_buffer(input_path)
                record_lookup = _buffer_record_lookup(buffer_payload)
                metadata = dict(buffer_payload.get("metadata", {}))
                if policy_id not in record_lookup:
                    raise KeyError(
                        f"Selected policy_id={policy_id} not found in buffer for method={method_name} seed={seed}"
                    )
                trace_dir = export_candidate_trace(
                    method_name=method_name,
                    seed=int(seed),
                    candidate=candidate,
                    buffer_path=input_path,
                    buffer_anchor_path=input_path,
                    record=record_lookup[policy_id],
                    metadata=metadata,
                    output_root=trace_root,
                    eval_episodes=int(eval_episodes),
                )

            audit_dir = ensure_dir(
                audit_root
                / method_name
                / f"seed_{int(seed):04d}"
                / f"selected__{policy_id}_semantic_audit_replay{int(eval_episodes)}"
            )
            export_candidate_semantic_audit(
                trace_dir=trace_dir,
                output_dir=audit_dir,
                critical_host=DEFAULT_CRITICAL_HOST,
                critical_path_hosts=DEFAULT_CRITICAL_PATH_HOSTS,
            )
            artifact = ObjectiveAuditArtifact(
                method_name=method_name,
                display_name=METHOD_DISPLAY[method_name],
                seed=int(seed),
                policy_id=policy_id,
                trace_dir=Path(trace_dir),
                audit_dir=audit_dir,
                risk_summary_path=audit_dir / "risk_tier_summary.json",
                trace_analysis_dir=trace_analysis_root / method_name / f"seed_{int(seed):04d}",
            )
            artifacts.append(artifact)
            per_method_artifacts[method_name] = artifact

        comparison_seed_path = semantic_root / f"seed_{int(seed):04d}_comparison.json"
        save_json(
            comparison_seed_path,
            {
                "seed": int(seed),
                "left_method_name": LEFT_METHOD_NAME,
                "left_display_name": METHOD_DISPLAY[LEFT_METHOD_NAME],
                "left_policy_id": left_row["selected_policy_id"],
                "left_risk_summary_path": str(
                    per_method_artifacts[LEFT_METHOD_NAME].risk_summary_path.resolve()
                ),
                "right_method_name": RIGHT_METHOD_NAME,
                "right_display_name": METHOD_DISPLAY[RIGHT_METHOD_NAME],
                "right_policy_id": right_row["selected_policy_id"],
                "right_risk_summary_path": str(
                    per_method_artifacts[RIGHT_METHOD_NAME].risk_summary_path.resolve()
                ),
            },
        )
        comparison_seed_inputs.append(comparison_seed_path)
        selected_policy_rows.append(
            {
                "seed": int(seed),
                "left_policy_id": str(left_row["selected_policy_id"]),
                "right_policy_id": str(right_row["selected_policy_id"]),
                "left_audit_dir": str(per_method_artifacts[LEFT_METHOD_NAME].audit_dir.resolve()),
                "right_audit_dir": str(per_method_artifacts[RIGHT_METHOD_NAME].audit_dir.resolve()),
            }
        )

    for method_name in (LEFT_METHOD_NAME, RIGHT_METHOD_NAME):
        export_figure2_trace_analysis(
            trace_root=trace_root / method_name,
            output_root=trace_analysis_root / method_name,
            seed_filters=set(DEFAULT_SEEDS),
        )

    aggregate_path = build_method_comparison_semantic_summary(
        comparison_seed_inputs,
        output_dir=semantic_root,
        left_method_name=LEFT_METHOD_NAME,
        left_display_name=METHOD_DISPLAY[LEFT_METHOD_NAME],
        right_method_name=RIGHT_METHOD_NAME,
        right_display_name=METHOD_DISPLAY[RIGHT_METHOD_NAME],
    )
    aggregate_payload = load_json(aggregate_path)
    _write_semantic_appendix_table(
        aggregate_payload,
        output_path=paper_appendix_table_path,
    )
    _write_selected_policy_table_tex(
        paper_selected_policies_table_path,
        rows=selected_policy_rows,
    )
    completeness = _trace_artifact_completeness(artifacts, eval_episodes=int(eval_episodes))
    save_json(verification_root / "semantic_artifact_completeness.json", completeness)
    save_json(
        verification_root / "selected_policy_alignment.json",
        {
            "rows": selected_policy_rows,
        },
    )
    save_json(
        verification_root / "semantic_metric_consistency.json",
        _collect_metric_consistency(semantic_root),
    )

    return {
        "semantic_root": str(semantic_root.resolve()),
        "semantic_comparison_aggregate_path": str(Path(aggregate_path).resolve()),
        "paper_appendix_table_path": str(paper_appendix_table_path.resolve()),
        "paper_selected_policies_table_path": str(
            paper_selected_policies_table_path.resolve()
        ),
        "selected_policy_rows": selected_policy_rows,
        "aggregate_payload": aggregate_payload,
    }


def _build_objective_panel_summary(
    *,
    output_root: Path,
    projected_summary: dict[str, Any],
    matched_deployment_summary: dict[str, Any],
    semantic_summary: dict[str, Any],
) -> dict[str, Any]:
    projected_payload = projected_summary["payload"]
    deployment_payload = matched_deployment_summary["payload"]
    semantic_payload = semantic_summary["aggregate_payload"]

    projected_lookup = {
        row["method_name"]: row for row in projected_payload["method_summary"]
    }
    deployment_lookup = {
        row["method_name"]: row for row in deployment_payload["method_summary"]
    }
    left_semantic = semantic_payload["left"]
    right_semantic = semantic_payload["right"]

    rows: list[dict[str, Any]] = []
    for metric_key, metric_label in PROJECTED_SET_METRICS:
        row = {
            "panel_key": "objective_3obj_vs_4obj",
            "panel_title": "Panel C: 3-Objective vs. 4-Objective Stage-2",
            "metric_key": metric_key,
            "metric_label": metric_label,
            "metric_source": "projected_table_a",
            "left_method_name": LEFT_METHOD_NAME,
            "left_display_name": METHOD_DISPLAY[LEFT_METHOD_NAME],
            "left_mean": float(projected_lookup[LEFT_METHOD_NAME][metric_key]["mean"]),
            "left_std": float(projected_lookup[LEFT_METHOD_NAME][metric_key]["std"]),
            "right_method_name": RIGHT_METHOD_NAME,
            "right_display_name": METHOD_DISPLAY[RIGHT_METHOD_NAME],
            "right_mean": float(projected_lookup[RIGHT_METHOD_NAME][metric_key]["mean"]),
            "right_std": float(projected_lookup[RIGHT_METHOD_NAME][metric_key]["std"]),
        }
        row["delta_right_minus_left"] = float(row["right_mean"]) - float(row["left_mean"])
        rows.append(row)

    for metric_key, metric_label in DEPLOYMENT_METRICS:
        row = {
            "panel_key": "objective_3obj_vs_4obj",
            "panel_title": "Panel C: 3-Objective vs. 4-Objective Stage-2",
            "metric_key": metric_key,
            "metric_label": metric_label,
            "metric_source": "matched_deployment",
            "left_method_name": LEFT_METHOD_NAME,
            "left_display_name": METHOD_DISPLAY[LEFT_METHOD_NAME],
            "left_mean": float(deployment_lookup[LEFT_METHOD_NAME][metric_key]),
            "left_std": float(deployment_lookup[LEFT_METHOD_NAME].get(f"{metric_key}_std", 0.0)),
            "right_method_name": RIGHT_METHOD_NAME,
            "right_display_name": METHOD_DISPLAY[RIGHT_METHOD_NAME],
            "right_mean": float(deployment_lookup[RIGHT_METHOD_NAME][metric_key]),
            "right_std": float(deployment_lookup[RIGHT_METHOD_NAME].get(f"{metric_key}_std", 0.0)),
        }
        row["delta_right_minus_left"] = float(row["right_mean"]) - float(row["left_mean"])
        rows.append(row)

    for metric_key, metric_label in SEMANTIC_METRICS:
        row = {
            "panel_key": "objective_3obj_vs_4obj",
            "panel_title": "Panel C: 3-Objective vs. 4-Objective Stage-2",
            "metric_key": metric_key,
            "metric_label": metric_label,
            "metric_source": "semantic",
            "left_method_name": LEFT_METHOD_NAME,
            "left_display_name": METHOD_DISPLAY[LEFT_METHOD_NAME],
            "left_mean": float(left_semantic[metric_key]),
            "left_std": None,
            "right_method_name": RIGHT_METHOD_NAME,
            "right_display_name": METHOD_DISPLAY[RIGHT_METHOD_NAME],
            "right_mean": float(right_semantic[metric_key]),
            "right_std": None,
        }
        row["delta_right_minus_left"] = float(row["right_mean"]) - float(row["left_mean"])
        rows.append(row)

    payload = {
        "panel_key": "objective_3obj_vs_4obj",
        "panel_title": "Panel C: 3-Objective vs. 4-Objective Stage-2",
        "left_method_name": LEFT_METHOD_NAME,
        "left_display_name": METHOD_DISPLAY[LEFT_METHOD_NAME],
        "right_method_name": RIGHT_METHOD_NAME,
        "right_display_name": METHOD_DISPLAY[RIGHT_METHOD_NAME],
        "rows": rows,
        "selected_policy_rows": semantic_summary["selected_policy_rows"],
        "source_paths": {
            "projected_set_quality_summary": projected_summary["summary_json"],
            "matched_deployment_summary": matched_deployment_summary["summary_json"],
            "semantic_comparison_aggregate": semantic_summary["semantic_comparison_aggregate_path"],
        },
    }
    summary_json = output_root / "objective_ablation_summary.json"
    summary_csv = output_root / "objective_ablation_summary.csv"
    summary_tex = output_root / "objective_ablation_summary.tex"
    save_json(summary_json, payload)
    _write_csv(
        summary_csv,
        rows,
        fieldnames=[
            "panel_key",
            "panel_title",
            "metric_key",
            "metric_label",
            "metric_source",
            "left_method_name",
            "left_display_name",
            "left_mean",
            "left_std",
            "right_method_name",
            "right_display_name",
            "right_mean",
            "right_std",
            "delta_right_minus_left",
        ],
    )
    _write_metric_table_tex(
        summary_tex,
        title="Objective-Level 3obj vs. 4obj Ablation Summary",
        left_display_name=METHOD_DISPLAY[LEFT_METHOD_NAME],
        right_display_name=METHOD_DISPLAY[RIGHT_METHOD_NAME],
        rows=rows,
    )
    return {
        "summary_json": str(summary_json.resolve()),
        "summary_csv": str(summary_csv.resolve()),
        "summary_tex": str(summary_tex.resolve()),
        "payload": payload,
    }


def export_rq4_objective_ablation(
    *,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    compare_config_3obj_path: str | Path = DEFAULT_3OBJ_COMPARE_CONFIG,
    table_b_summary_4obj_path: str | Path = DEFAULT_4OBJ_TABLE_B_SUMMARY,
    thresholds_4obj_path: str | Path = DEFAULT_4OBJ_THRESHOLDS_PATH,
    seeds: Iterable[int] = DEFAULT_SEEDS,
    eval_episodes: int = DEFAULT_EVAL_EPISODES,
    deployment_eval_episodes: int = DEFAULT_DEPLOYMENT_EVAL_EPISODES,
    paper_projected_set_table_path: str | Path = DEFAULT_PAPER_PROJECTED_SET_TABLE_PATH,
    paper_semantic_appendix_table_path: str | Path = DEFAULT_PAPER_SEMANTIC_APPENDIX_TABLE_PATH,
    paper_selected_policies_table_path: str | Path = DEFAULT_PAPER_SELECTED_POLICIES_TABLE_PATH,
) -> dict[str, str]:
    output_root = ensure_dir(Path(output_root))
    ensure_dir(output_root / "verification")
    seeds = tuple(int(seed) for seed in seeds)
    compare_config_3obj_path = Path(compare_config_3obj_path).resolve()
    table_b_summary_4obj_path = Path(table_b_summary_4obj_path).resolve()
    thresholds_4obj_path = Path(thresholds_4obj_path).resolve()
    paper_projected_set_table_path = Path(paper_projected_set_table_path)
    paper_semantic_appendix_table_path = Path(paper_semantic_appendix_table_path)
    paper_selected_policies_table_path = Path(paper_selected_policies_table_path)
    paper_projected_set_table_path.parent.mkdir(parents=True, exist_ok=True)
    paper_semantic_appendix_table_path.parent.mkdir(parents=True, exist_ok=True)
    paper_selected_policies_table_path.parent.mkdir(parents=True, exist_ok=True)

    left_buffer_paths = _compare_entry_buffer_paths(
        compare_config_3obj_path,
        method_name=LEFT_METHOD_NAME,
        seeds=seeds,
    )
    left_metrics_paths = _metrics_paths_for_method(
        root_dir=REPO_ROOT / "cmorl_cyborg" / "outputs" / "paper_table_a",
        method_name=LEFT_METHOD_NAME,
        seeds=seeds,
    )
    right_metrics_paths = _metrics_paths_for_method(
        root_dir=REPO_ROOT / "cmorl_cyborg" / "outputs" / "paper_4obj" / "table_a",
        method_name=RIGHT_METHOD_NAME,
        seeds=seeds,
    )

    projected_summary = _build_projected_set_quality(
        output_root=output_root,
        left_metrics_paths=left_metrics_paths,
        right_metrics_paths=right_metrics_paths,
        paper_table_path=paper_projected_set_table_path,
    )
    matched_deployment_summary = _build_matched_deployment(
        output_root=output_root,
        left_buffer_paths=left_buffer_paths,
        table_b_summary_path=table_b_summary_4obj_path,
        thresholds_path=thresholds_4obj_path,
        deployment_eval_episodes=deployment_eval_episodes,
    )
    semantic_summary = _build_objective_semantic_comparison(
        output_root=output_root,
        matched_deployment_summary=matched_deployment_summary["payload"],
        table_b_summary_path=table_b_summary_4obj_path,
        eval_episodes=eval_episodes,
        paper_appendix_table_path=paper_semantic_appendix_table_path,
        paper_selected_policies_table_path=paper_selected_policies_table_path,
    )
    objective_summary = _build_objective_panel_summary(
        output_root=output_root,
        projected_summary=projected_summary,
        matched_deployment_summary=matched_deployment_summary,
        semantic_summary=semantic_summary,
    )

    summary_payload = {
        "comparison_name": "rq4_objective_ablation_3obj_vs_4obj",
        "left_method_name": LEFT_METHOD_NAME,
        "left_display_name": METHOD_DISPLAY[LEFT_METHOD_NAME],
        "right_method_name": RIGHT_METHOD_NAME,
        "right_display_name": METHOD_DISPLAY[RIGHT_METHOD_NAME],
        "seeds": [int(seed) for seed in seeds],
        "source_paths": {
            "compare_config_3obj_path": str(compare_config_3obj_path.resolve()),
            "table_b_summary_4obj_path": str(table_b_summary_4obj_path.resolve()),
            "thresholds_4obj_path": str(thresholds_4obj_path.resolve()),
        },
        "projected_set_quality_summary_path": projected_summary["summary_json"],
        "matched_deployment_summary_path": matched_deployment_summary["summary_json"],
        "semantic_comparison_aggregate_path": semantic_summary["semantic_comparison_aggregate_path"],
        "objective_ablation_summary_path": objective_summary["summary_json"],
        "paper_projected_set_table_path": str(paper_projected_set_table_path.resolve()),
        "paper_semantic_appendix_table_path": str(
            paper_semantic_appendix_table_path.resolve()
        ),
        "paper_selected_policies_table_path": str(
            paper_selected_policies_table_path.resolve()
        ),
    }
    save_json(output_root / "summary.json", summary_payload)

    return {
        "summary_json": str((output_root / "summary.json").resolve()),
        "projected_set_quality_summary_json": projected_summary["summary_json"],
        "matched_deployment_summary_json": matched_deployment_summary["summary_json"],
        "semantic_comparison_aggregate_json": semantic_summary["semantic_comparison_aggregate_path"],
        "objective_ablation_summary_json": objective_summary["summary_json"],
        "paper_projected_set_table_path": str(paper_projected_set_table_path.resolve()),
        "paper_semantic_appendix_table_path": str(
            paper_semantic_appendix_table_path.resolve()
        ),
        "paper_selected_policies_table_path": str(
            paper_selected_policies_table_path.resolve()
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export the protocol-matched 3obj vs 4obj objective-level ablation."
    )
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--compare-config-3obj-path", default=str(DEFAULT_3OBJ_COMPARE_CONFIG))
    parser.add_argument("--table-b-summary-4obj-path", default=str(DEFAULT_4OBJ_TABLE_B_SUMMARY))
    parser.add_argument("--thresholds-4obj-path", default=str(DEFAULT_4OBJ_THRESHOLDS_PATH))
    parser.add_argument("--paper-projected-set-table-path", default=str(DEFAULT_PAPER_PROJECTED_SET_TABLE_PATH))
    parser.add_argument(
        "--paper-semantic-appendix-table-path",
        default=str(DEFAULT_PAPER_SEMANTIC_APPENDIX_TABLE_PATH),
    )
    parser.add_argument(
        "--paper-selected-policies-table-path",
        default=str(DEFAULT_PAPER_SELECTED_POLICIES_TABLE_PATH),
    )
    parser.add_argument("--eval-episodes", type=int, default=DEFAULT_EVAL_EPISODES)
    parser.add_argument(
        "--deployment-eval-episodes",
        type=int,
        default=DEFAULT_DEPLOYMENT_EVAL_EPISODES,
    )
    parser.add_argument("--seeds", nargs="+", type=int, default=list(DEFAULT_SEEDS))
    args = parser.parse_args()

    outputs = export_rq4_objective_ablation(
        output_root=args.output_root,
        compare_config_3obj_path=args.compare_config_3obj_path,
        table_b_summary_4obj_path=args.table_b_summary_4obj_path,
        thresholds_4obj_path=args.thresholds_4obj_path,
        seeds=args.seeds,
        eval_episodes=int(args.eval_episodes),
        deployment_eval_episodes=int(args.deployment_eval_episodes),
        paper_projected_set_table_path=args.paper_projected_set_table_path,
        paper_semantic_appendix_table_path=args.paper_semantic_appendix_table_path,
        paper_selected_policies_table_path=args.paper_selected_policies_table_path,
    )
    print(json.dumps(outputs, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
