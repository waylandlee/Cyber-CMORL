from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from cmorl_minicage.utils import load_json, save_json

from .export_figure2_attack_defense_trace import resolve_artifact_path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TABLE_A_SUMMARY_PATH = (
    REPO_ROOT / "cmorl_cyborg" / "outputs" / "paper_4obj" / "table_a" / "table_a_summary.json"
)
DEFAULT_TABLE_B_SUMMARY_PATH = (
    REPO_ROOT / "cmorl_cyborg" / "outputs" / "paper_4obj" / "table_b" / "table_b_summary.json"
)
DEFAULT_OUTPUT_ROOT = (
    REPO_ROOT / "cmorl_cyborg" / "outputs" / "paper_4obj" / "per_seed_main_results"
)
DEFAULT_PAPER_TABLE_DIR = REPO_ROOT / "paper" / "table"
DEFAULT_SEEDS = (7, 11, 19)

ARCHIVE_METHOD_ORDER = (
    "ours_stage2_v2_4",
    "stage1_only_4obj",
    "weighted_sum_4obj",
    "preference_conditioned_ppo_4obj",
)
ASSIGNMENT_METHOD_ORDER = (
    "ours_stage2_v2_4",
    "stage1_only_4obj",
    "weighted_sum_4obj",
    "lagrangian_ppo_4obj",
    "no_constraint_stage2_4obj",
)
DISPLAY_GROUP_FALLBACKS = {
    "ours_stage2_v2_4": "Ours Stage2 V2.4",
    "stage1_only_4obj": "Stage1 Only 4obj",
    "weighted_sum_4obj": "Weighted-Sum 4obj",
    "preference_conditioned_ppo_4obj": "Preference-Conditioned PPO 4obj",
    "lagrangian_ppo_4obj": "Lagrangian PPO 4obj",
    "no_constraint_stage2_4obj": "Unconstrained Stage-2 4obj",
}
PAPER_DISPLAY_NAMES = {
    "ours_stage2_v2_4": "Constraint-Aware Stage-2",
    "stage1_only_4obj": "Stage-1 Archive",
    "weighted_sum_4obj": "Weighted-Sum",
    "preference_conditioned_ppo_4obj": "Preference-Conditioned PPO",
    "lagrangian_ppo_4obj": "Lagrangian PPO",
    "no_constraint_stage2_4obj": "Unconstrained Stage-2",
}
ARCHIVE_COLUMNS = [
    "seed",
    "method_name",
    "display_group",
    "hypervolume",
    "expected_utility",
]
ASSIGNMENT_COLUMNS = [
    "seed",
    "method_name",
    "display_group",
    "selected_policy_id",
    "feasible_rate",
    "mean_violation",
    "critical_impact_count",
    "final_critical_compromised_hosts",
]
_VERIFY_TOL = 1e-9


def _zero_padded_seed(seed: int) -> str:
    return f"{int(seed):04d}"


def _write_csv(path: str | Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
    return path.resolve()


def _format_float(value: float, *, scale: float = 1.0) -> str:
    return f"{float(value) / scale:.3f}"


def _write_archive_tex(path: str | Path, rows: list[dict[str, Any]]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        r"\begin{tabular}{@{}llrr@{}}",
        r"\toprule",
        r"Seed & Method & Hypervolume ($\times 10^6$) & Expected Utility \\",
        r"\midrule",
    ]
    for row in rows:
        lines.append(
            f"{_zero_padded_seed(int(row['seed']))} & "
            f"{PAPER_DISPLAY_NAMES.get(str(row['method_name']), str(row['display_group']))} & "
            f"{_format_float(float(row['hypervolume']), scale=1_000_000.0)} & "
            f"{_format_float(float(row['expected_utility']))} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path.resolve()


def _write_assignment_tex(path: str | Path, rows: list[dict[str, Any]]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        r"\begin{tabular}{@{}llrrrr@{}}",
        r"\toprule",
        r"Seed & Method & Feasible Rate & Violation & Final Critical Hosts & Critical Impacts \\",
        r"\midrule",
    ]
    for row in rows:
        lines.append(
            f"{_zero_padded_seed(int(row['seed']))} & "
            f"{PAPER_DISPLAY_NAMES.get(str(row['method_name']), str(row['display_group']))} & "
            f"{_format_float(float(row['feasible_rate']))} & "
            f"{_format_float(float(row['mean_violation']))} & "
            f"{_format_float(float(row['final_critical_compromised_hosts']))} & "
            f"{_format_float(float(row['critical_impact_count']))} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path.resolve()


def _group_mean(records: list[dict[str, Any]], field_name: str) -> float:
    values = [float(record[field_name]) for record in records]
    if not values:
        raise ValueError(f"No values found for {field_name}")
    return float(sum(values) / len(values))


def _collect_archive_rows(
    table_a_summary_path: Path,
    *,
    seeds: tuple[int, ...],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    payload = load_json(table_a_summary_path)
    method_summary_lookup = {
        str(entry["method_name"]): entry for entry in payload.get("method_summary", [])
    }
    grouped: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in payload.get("per_run", []):
        method_name = str(row.get("method_name"))
        seed = int(row.get("seed", -1))
        grouped[(method_name, seed)].append(row)

    records: list[dict[str, Any]] = []
    for seed in seeds:
        for method_name in ARCHIVE_METHOD_ORDER:
            matched = grouped.get((method_name, seed), [])
            if len(matched) != 1:
                raise ValueError(
                    f"Expected exactly one archive-quality row for method={method_name} seed={seed} "
                    f"in {table_a_summary_path}, found {len(matched)}"
                )
            row = matched[0]
            display_group = str(
                row.get("display_group")
                or method_summary_lookup.get(method_name, {}).get("display_group")
                or DISPLAY_GROUP_FALLBACKS[method_name]
            )
            records.append(
                {
                    "seed": int(seed),
                    "method_name": method_name,
                    "display_group": display_group,
                    "hypervolume": float(row["hypervolume"]),
                    "expected_utility": float(row["expected_utility"]),
                }
            )
    return records, method_summary_lookup


def _collect_assignment_rows(
    table_b_summary_path: Path,
    *,
    seeds: tuple[int, ...],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    payload = load_json(table_b_summary_path)
    record_lookup: dict[tuple[str, int], dict[str, Any]] = {}
    for row in payload.get("per_run_records", []):
        method_name = str(row.get("method_name"))
        seed = int(row.get("seed", -1))
        key = (method_name, seed)
        if key in record_lookup:
            raise ValueError(
                f"Duplicate assignment row for method={method_name} seed={seed} in {table_b_summary_path}"
            )
        record_lookup[key] = row

    aggregate_lookup: dict[str, dict[str, Any]] = {}
    for raw_path in payload.get("aggregated_paths", []):
        aggregate_payload = load_json(resolve_artifact_path(raw_path, anchor_path=table_b_summary_path))
        aggregate_lookup[str(aggregate_payload["method_name"])] = aggregate_payload

    records: list[dict[str, Any]] = []
    for seed in seeds:
        for method_name in ASSIGNMENT_METHOD_ORDER:
            record = record_lookup.get((method_name, seed))
            if record is None:
                raise ValueError(
                    f"Missing assignment row for method={method_name} seed={seed} in {table_b_summary_path}"
                )
            metrics_path = resolve_artifact_path(str(record["output_path"]), anchor_path=table_b_summary_path)
            if not metrics_path.exists():
                raise FileNotFoundError(
                    f"Missing constraint metrics for method={method_name} seed={seed}: {metrics_path}"
                )
            metrics = load_json(metrics_path)
            records.append(
                {
                    "seed": int(seed),
                    "method_name": method_name,
                    "display_group": DISPLAY_GROUP_FALLBACKS[method_name],
                    "selected_policy_id": str(metrics.get("selected_policy_id", "")),
                    "feasible_rate": float(metrics["feasible_rate"]),
                    "mean_violation": float(metrics["mean_violation"]),
                    "critical_impact_count": float(metrics["critical_impact_count"]),
                    "final_critical_compromised_hosts": float(
                        metrics["final_critical_compromised_hosts"]
                    ),
                }
            )
    return records, aggregate_lookup


def _build_verification_summary(
    *,
    archive_rows: list[dict[str, Any]],
    assignment_rows: list[dict[str, Any]],
    archive_method_summary: dict[str, dict[str, Any]],
    assignment_aggregate_summary: dict[str, dict[str, Any]],
    table_a_summary_path: Path,
    table_b_summary_path: Path,
    seeds: tuple[int, ...],
) -> dict[str, Any]:
    archive_grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in archive_rows:
        archive_grouped[str(row["method_name"])].append(row)

    archive_comparisons: list[dict[str, Any]] = []
    archive_all_match = True
    for method_name in ARCHIVE_METHOD_ORDER:
        records = archive_grouped[method_name]
        summary = archive_method_summary.get(method_name)
        if summary is None:
            raise ValueError(f"Missing method_summary entry for {method_name} in {table_a_summary_path}")
        hypervolume_mean = _group_mean(records, "hypervolume")
        expected_utility_mean = _group_mean(records, "expected_utility")
        hv_target = float(summary["hypervolume"]["mean"])
        eu_target = float(summary["expected_utility"]["mean"])
        hv_match = math.isclose(hypervolume_mean, hv_target, rel_tol=0.0, abs_tol=_VERIFY_TOL)
        eu_match = math.isclose(expected_utility_mean, eu_target, rel_tol=0.0, abs_tol=_VERIFY_TOL)
        archive_all_match = archive_all_match and hv_match and eu_match
        archive_comparisons.append(
            {
                "method_name": method_name,
                "display_group": str(summary.get("display_group", DISPLAY_GROUP_FALLBACKS[method_name])),
                "num_records": len(records),
                "hypervolume": {
                    "derived_mean": hypervolume_mean,
                    "aggregate_mean": hv_target,
                    "delta": hypervolume_mean - hv_target,
                    "matches": hv_match,
                },
                "expected_utility": {
                    "derived_mean": expected_utility_mean,
                    "aggregate_mean": eu_target,
                    "delta": expected_utility_mean - eu_target,
                    "matches": eu_match,
                },
            }
        )

    assignment_grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in assignment_rows:
        assignment_grouped[str(row["method_name"])].append(row)

    assignment_comparisons: list[dict[str, Any]] = []
    assignment_all_match = True
    for method_name in ASSIGNMENT_METHOD_ORDER:
        records = assignment_grouped[method_name]
        summary = assignment_aggregate_summary.get(method_name)
        if summary is None:
            raise ValueError(f"Missing aggregated assignment entry for {method_name} in {table_b_summary_path}")
        metric_checks: dict[str, Any] = {}
        row_match = True
        for field_name in (
            "feasible_rate",
            "mean_violation",
            "critical_impact_count",
            "final_critical_compromised_hosts",
        ):
            derived_mean = _group_mean(records, field_name)
            aggregate_mean = float(summary[field_name])
            matches = math.isclose(derived_mean, aggregate_mean, rel_tol=0.0, abs_tol=_VERIFY_TOL)
            row_match = row_match and matches
            metric_checks[field_name] = {
                "derived_mean": derived_mean,
                "aggregate_mean": aggregate_mean,
                "delta": derived_mean - aggregate_mean,
                "matches": matches,
            }
        assignment_all_match = assignment_all_match and row_match
        assignment_comparisons.append(
            {
                "method_name": method_name,
                "display_group": DISPLAY_GROUP_FALLBACKS[method_name],
                "num_records": len(records),
                **metric_checks,
            }
        )

    return {
        "schema_version": "0.1.0",
        "table_a_summary_path": str(table_a_summary_path.resolve()),
        "table_b_summary_path": str(table_b_summary_path.resolve()),
        "seeds": list(seeds),
        "archive_quality": {
            "all_match": archive_all_match,
            "comparisons": archive_comparisons,
        },
        "operational_assignment": {
            "all_match": assignment_all_match,
            "comparisons": assignment_comparisons,
        },
        "all_match": archive_all_match and assignment_all_match,
    }


def export_per_seed_main_results_4obj(
    table_a_summary_path: str | Path = DEFAULT_TABLE_A_SUMMARY_PATH,
    table_b_summary_path: str | Path = DEFAULT_TABLE_B_SUMMARY_PATH,
    *,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    paper_table_dir: str | Path = DEFAULT_PAPER_TABLE_DIR,
    seeds: Iterable[int] = DEFAULT_SEEDS,
) -> dict[str, str]:
    table_a_summary_path = Path(table_a_summary_path).resolve()
    table_b_summary_path = Path(table_b_summary_path).resolve()
    output_root = Path(output_root).resolve()
    paper_table_dir = Path(paper_table_dir).resolve()
    seed_tuple = tuple(int(seed) for seed in seeds)
    if not seed_tuple:
        raise ValueError("At least one seed must be provided")

    archive_rows, archive_method_summary = _collect_archive_rows(
        table_a_summary_path,
        seeds=seed_tuple,
    )
    assignment_rows, assignment_aggregate_summary = _collect_assignment_rows(
        table_b_summary_path,
        seeds=seed_tuple,
    )
    verification_summary = _build_verification_summary(
        archive_rows=archive_rows,
        assignment_rows=assignment_rows,
        archive_method_summary=archive_method_summary,
        assignment_aggregate_summary=assignment_aggregate_summary,
        table_a_summary_path=table_a_summary_path,
        table_b_summary_path=table_b_summary_path,
        seeds=seed_tuple,
    )

    output_root.mkdir(parents=True, exist_ok=True)
    paper_table_dir.mkdir(parents=True, exist_ok=True)

    archive_json_path = output_root / "archive_quality_per_seed.json"
    archive_csv_path = output_root / "archive_quality_per_seed.csv"
    archive_tex_path = output_root / "archive_quality_per_seed.tex"
    assignment_json_path = output_root / "operational_assignment_per_seed.json"
    assignment_csv_path = output_root / "operational_assignment_per_seed.csv"
    assignment_tex_path = output_root / "operational_assignment_per_seed.tex"
    verification_path = output_root / "verification_summary.json"

    save_json(
        archive_json_path,
        {
            "schema_version": "0.1.0",
            "table_a_summary_path": str(table_a_summary_path),
            "seeds": list(seed_tuple),
            "method_names": list(ARCHIVE_METHOD_ORDER),
            "records": archive_rows,
        },
    )
    _write_csv(archive_csv_path, archive_rows, ARCHIVE_COLUMNS)
    _write_archive_tex(archive_tex_path, archive_rows)

    save_json(
        assignment_json_path,
        {
            "schema_version": "0.1.0",
            "table_b_summary_path": str(table_b_summary_path),
            "seeds": list(seed_tuple),
            "method_names": list(ASSIGNMENT_METHOD_ORDER),
            "records": assignment_rows,
        },
    )
    _write_csv(assignment_csv_path, assignment_rows, ASSIGNMENT_COLUMNS)
    _write_assignment_tex(assignment_tex_path, assignment_rows)

    paper_archive_tex_path = paper_table_dir / "per_seed_archive_quality_4obj.tex"
    paper_assignment_tex_path = paper_table_dir / "per_seed_operational_assignment_4obj.tex"
    paper_archive_tex_path.write_text(archive_tex_path.read_text(encoding="utf-8"), encoding="utf-8")
    paper_assignment_tex_path.write_text(
        assignment_tex_path.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    save_json(verification_path, verification_summary)
    if not verification_summary["all_match"]:
        raise ValueError(f"Per-seed verification failed; see {verification_path}")

    return {
        "archive_quality_json": str(archive_json_path.resolve()),
        "archive_quality_csv": str(archive_csv_path.resolve()),
        "archive_quality_tex": str(archive_tex_path.resolve()),
        "operational_assignment_json": str(assignment_json_path.resolve()),
        "operational_assignment_csv": str(assignment_csv_path.resolve()),
        "operational_assignment_tex": str(assignment_tex_path.resolve()),
        "paper_archive_quality_tex": str(paper_archive_tex_path.resolve()),
        "paper_operational_assignment_tex": str(paper_assignment_tex_path.resolve()),
        "verification_summary_json": str(verification_path.resolve()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export per-seed appendix tables from the official 4-objective paper artifacts."
    )
    parser.add_argument(
        "--table-a-summary-path",
        default=str(DEFAULT_TABLE_A_SUMMARY_PATH),
    )
    parser.add_argument(
        "--table-b-summary-path",
        default=str(DEFAULT_TABLE_B_SUMMARY_PATH),
    )
    parser.add_argument(
        "--output-root",
        default=str(DEFAULT_OUTPUT_ROOT),
    )
    parser.add_argument(
        "--paper-table-dir",
        default=str(DEFAULT_PAPER_TABLE_DIR),
    )
    parser.add_argument(
        "--seeds",
        nargs="+",
        type=int,
        default=list(DEFAULT_SEEDS),
    )
    args = parser.parse_args()
    outputs = export_per_seed_main_results_4obj(
        table_a_summary_path=args.table_a_summary_path,
        table_b_summary_path=args.table_b_summary_path,
        output_root=args.output_root,
        paper_table_dir=args.paper_table_dir,
        seeds=args.seeds,
    )
    print(json.dumps(outputs, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
