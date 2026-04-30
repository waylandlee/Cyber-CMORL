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
DEFAULT_TABLE_B_SUMMARY_PATH = (
    REPO_ROOT / "cmorl_cyborg" / "outputs" / "paper_4obj" / "table_b" / "table_b_summary.json"
)
DEFAULT_OUTPUT_ROOT = (
    REPO_ROOT / "cmorl_cyborg" / "outputs" / "paper_4obj" / "zero_event_confidence_bounds"
)
DEFAULT_PAPER_TABLE_DIR = REPO_ROOT / "paper" / "table"
DEFAULT_SEEDS = (7, 11, 19)
DEFAULT_ALPHA = 0.05
_COUNT_TOL = 1e-6

METHOD_ORDER = (
    "ours_stage2_v2_4",
    "stage1_only_4obj",
    "weighted_sum_4obj",
    "lagrangian_ppo_4obj",
    "no_constraint_stage2_4obj",
)
PAPER_DISPLAY_NAMES = {
    "ours_stage2_v2_4": "Constraint-Aware Stage-2",
    "stage1_only_4obj": "Stage-1 Archive",
    "weighted_sum_4obj": "Weighted-Sum",
    "lagrangian_ppo_4obj": "Lagrangian PPO",
    "no_constraint_stage2_4obj": "Unconstrained Stage-2",
}
EVENT_SPECS = (
    {
        "event_key": "ever_critical_breach",
        "event_name": "Ever Critical Breach",
        "metric_field": "ever_critical_breach_rate",
        "metric_kind": "rate",
    },
    {
        "event_key": "persistent_critical_breach",
        "event_name": "Persistent Critical Breach",
        "metric_field": "persistent_critical_breach_rate",
        "metric_kind": "rate",
    },
    {
        "event_key": "critical_impact",
        "event_name": "Any Critical Impact",
        "metric_field": "critical_impact_count",
        "metric_kind": "count_mean",
    },
    {
        "event_key": "final_critical_compromised_host",
        "event_name": "Any Final Critical Host Compromised",
        "metric_field": "final_critical_compromised_hosts",
        "metric_kind": "count_mean",
    },
)
PER_SEED_COLUMNS = [
    "method_name",
    "display_name",
    "seed",
    "event_key",
    "event_name",
    "metric_field",
    "metric_kind",
    "semantic_eval_episodes",
    "observed_value",
    "observed_count",
    "observed_rate",
    "bound_applicable",
    "clopper_pearson_upper",
    "hoeffding_upper",
    "metrics_path",
]
SUMMARY_COLUMNS = [
    "method_name",
    "display_name",
    "event_key",
    "event_name",
    "metric_field",
    "metric_kind",
    "num_seeds",
    "total_episodes",
    "observed_count",
    "observed_rate",
    "bound_applicable",
    "clopper_pearson_upper",
    "hoeffding_upper",
]


def clopper_pearson_zero_upper(num_trials: int, alpha: float = DEFAULT_ALPHA) -> float:
    if num_trials <= 0:
        raise ValueError("num_trials must be positive")
    if not 0.0 < float(alpha) < 1.0:
        raise ValueError("alpha must be in (0, 1)")
    return float(1.0 - float(alpha) ** (1.0 / float(num_trials)))


def hoeffding_zero_upper(num_trials: int, alpha: float = DEFAULT_ALPHA) -> float:
    if num_trials <= 0:
        raise ValueError("num_trials must be positive")
    if not 0.0 < float(alpha) < 1.0:
        raise ValueError("alpha must be in (0, 1)")
    return float(math.sqrt(math.log(1.0 / float(alpha)) / (2.0 * float(num_trials))))


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
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        return json.dumps(value, sort_keys=True)
    return value


def _format_float(value: Any) -> str:
    if value is None:
        return "NA"
    return f"{float(value):.3f}"


def _format_percent(value: Any) -> str:
    if value is None:
        return "NA"
    return f"{100.0 * float(value):.2f}\\%"


def _display_name(method_name: str) -> str:
    return PAPER_DISPLAY_NAMES.get(method_name, method_name)


def _observed_count(
    *,
    method_name: str,
    seed: int,
    metric_field: str,
    metric_kind: str,
    observed_value: float,
    num_episodes: int,
) -> int:
    scaled = float(observed_value) * int(num_episodes)
    count = int(round(scaled))
    if abs(scaled - count) > _COUNT_TOL:
        raise ValueError(
            f"Could not reconstruct integer observed count for method={method_name} "
            f"seed={seed} field={metric_field}: value={observed_value} "
            f"episodes={num_episodes} scaled={scaled}"
        )
    if count < 0:
        raise ValueError(
            f"Observed count must be non-negative for method={method_name} "
            f"seed={seed} field={metric_field}: {count}"
        )
    if metric_kind == "rate" and count > int(num_episodes):
        raise ValueError(
            f"Rate-derived observed count exceeds episodes for method={method_name} "
            f"seed={seed} field={metric_field}: count={count} episodes={num_episodes}"
        )
    if metric_kind not in {"rate", "count_mean"}:
        raise ValueError(f"Unknown metric_kind={metric_kind} for field={metric_field}")
    return count


def _collect_metric_paths(
    table_b_summary_path: Path,
    *,
    seeds: tuple[int, ...],
    methods: tuple[str, ...],
) -> dict[tuple[str, int], Path]:
    payload = load_json(table_b_summary_path)
    grouped: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    allowed_seeds = {int(seed) for seed in seeds}
    allowed_methods = set(methods)
    for row in payload.get("per_run_records", []):
        method_name = str(row.get("method_name"))
        seed = int(row.get("seed", -1))
        if method_name in allowed_methods and seed in allowed_seeds:
            grouped[(method_name, seed)].append(row)

    paths: dict[tuple[str, int], Path] = {}
    for method_name in methods:
        for seed in seeds:
            matched = grouped.get((method_name, int(seed)), [])
            if len(matched) != 1:
                raise ValueError(
                    f"Expected exactly one Table B record for method={method_name} "
                    f"seed={seed}, found {len(matched)}"
                )
            output_path = resolve_artifact_path(
                str(matched[0]["output_path"]),
                anchor_path=table_b_summary_path,
            )
            if not output_path.exists():
                raise FileNotFoundError(
                    f"Missing constraint metrics for method={method_name} seed={seed}: {output_path}"
                )
            paths[(method_name, int(seed))] = output_path.resolve()
    return paths


def _build_per_seed_rows(
    *,
    metric_paths: dict[tuple[str, int], Path],
    seeds: tuple[int, ...],
    methods: tuple[str, ...],
    alpha: float,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for method_name in methods:
        for seed in seeds:
            metrics_path = metric_paths[(method_name, int(seed))]
            metrics = load_json(metrics_path)
            if "semantic_eval_episodes" not in metrics:
                raise ValueError(
                    f"Missing semantic_eval_episodes for method={method_name} seed={seed}: {metrics_path}"
                )
            num_episodes = int(metrics["semantic_eval_episodes"])
            if num_episodes <= 0:
                raise ValueError(
                    f"semantic_eval_episodes must be positive for method={method_name} seed={seed}"
                )
            for spec in EVENT_SPECS:
                metric_field = str(spec["metric_field"])
                if metric_field not in metrics:
                    raise ValueError(
                        f"Missing event metric {metric_field} for method={method_name} "
                        f"seed={seed}: {metrics_path}"
                    )
                observed_value = float(metrics[metric_field])
                count = _observed_count(
                    method_name=method_name,
                    seed=int(seed),
                    metric_field=metric_field,
                    metric_kind=str(spec["metric_kind"]),
                    observed_value=observed_value,
                    num_episodes=num_episodes,
                )
                bound_applicable = count == 0
                rows.append(
                    {
                        "method_name": method_name,
                        "display_name": _display_name(method_name),
                        "seed": int(seed),
                        "event_key": str(spec["event_key"]),
                        "event_name": str(spec["event_name"]),
                        "metric_field": metric_field,
                        "metric_kind": str(spec["metric_kind"]),
                        "semantic_eval_episodes": int(num_episodes),
                        "observed_value": float(observed_value),
                        "observed_count": int(count),
                        "observed_rate": float(count / num_episodes),
                        "bound_applicable": bound_applicable,
                        "clopper_pearson_upper": (
                            clopper_pearson_zero_upper(num_episodes, alpha)
                            if bound_applicable
                            else None
                        ),
                        "hoeffding_upper": (
                            hoeffding_zero_upper(num_episodes, alpha)
                            if bound_applicable
                            else None
                        ),
                        "metrics_path": str(metrics_path),
                    }
                )
    return rows


def _build_summary_rows(
    *,
    per_seed_rows: list[dict[str, Any]],
    methods: tuple[str, ...],
    alpha: float,
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in per_seed_rows:
        grouped[(str(row["method_name"]), str(row["event_key"]))].append(row)

    rows: list[dict[str, Any]] = []
    for method_name in methods:
        for spec in EVENT_SPECS:
            event_key = str(spec["event_key"])
            group = grouped[(method_name, event_key)]
            if not group:
                raise ValueError(f"Missing per-seed rows for method={method_name} event={event_key}")
            total_episodes = int(sum(int(row["semantic_eval_episodes"]) for row in group))
            observed_count = int(sum(int(row["observed_count"]) for row in group))
            bound_applicable = observed_count == 0
            rows.append(
                {
                    "method_name": method_name,
                    "display_name": _display_name(method_name),
                    "event_key": event_key,
                    "event_name": str(spec["event_name"]),
                    "metric_field": str(spec["metric_field"]),
                    "metric_kind": str(spec["metric_kind"]),
                    "num_seeds": len(group),
                    "total_episodes": total_episodes,
                    "observed_count": observed_count,
                    "observed_rate": float(observed_count / total_episodes),
                    "bound_applicable": bound_applicable,
                    "clopper_pearson_upper": (
                        clopper_pearson_zero_upper(total_episodes, alpha)
                        if bound_applicable
                        else None
                    ),
                    "hoeffding_upper": (
                        hoeffding_zero_upper(total_episodes, alpha)
                        if bound_applicable
                        else None
                    ),
                }
            )
    return rows


def _write_summary_tex(path: str | Path, rows: list[dict[str, Any]], *, alpha: float) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    zero_rows = [row for row in rows if bool(row["bound_applicable"])]
    confidence = 100.0 * (1.0 - float(alpha))
    lines = [
        r"\begin{table*}[t]",
        r"\centering",
        r"\small",
        rf"\caption{{Zero-observed critical-event confidence bounds under the finite semantic replay protocol. Bounds are one-sided Clopper--Pearson upper bounds at {confidence:.0f}\% confidence and do not imply zero risk.}}",
        r"\label{tab:app-zero-event-confidence-bounds}",
        r"\resizebox{\textwidth}{!}{%",
        r"\begin{tabular}{@{}llrrr@{}}",
        r"\toprule",
        rf"Event & Method & Observed Events / Episodes & Observed Rate & {confidence:.0f}\% CP Upper Bound \\",
        r"\midrule",
    ]
    for row in zero_rows:
        lines.append(
            f"{row['event_name']} & "
            f"{row['display_name']} & "
            f"{int(row['observed_count'])}/{int(row['total_episodes'])} & "
            f"{_format_percent(row['observed_rate'])} & "
            f"{_format_percent(row['clopper_pearson_upper'])} \\\\"
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
    per_seed_rows: list[dict[str, Any]],
    summary_rows: list[dict[str, Any]],
    seeds: tuple[int, ...],
    methods: tuple[str, ...],
    alpha: float,
) -> dict[str, Any]:
    expected_per_seed = len(methods) * len(seeds) * len(EVENT_SPECS)
    expected_summary = len(methods) * len(EVENT_SPECS)
    output_seeds = sorted({int(row["seed"]) for row in per_seed_rows})
    output_methods = sorted({str(row["method_name"]) for row in per_seed_rows})
    output_events = sorted({str(row["event_key"]) for row in per_seed_rows})
    expected_events = sorted(str(spec["event_key"]) for spec in EVENT_SPECS)
    zero_summary_rows = [row for row in summary_rows if bool(row["bound_applicable"])]
    zero_rows_valid = all(
        int(row["observed_count"]) == 0
        and row["clopper_pearson_upper"] is not None
        and row["hoeffding_upper"] is not None
        for row in zero_summary_rows
    )
    nonzero_rows_valid = all(
        bool(row["bound_applicable"]) is False
        and row["clopper_pearson_upper"] is None
        and row["hoeffding_upper"] is None
        for row in summary_rows
        if int(row["observed_count"]) > 0
    )
    episodes_by_method = {
        method_name: sorted(
            {
                int(row["total_episodes"])
                for row in summary_rows
                if str(row["method_name"]) == method_name
            }
        )
        for method_name in methods
    }
    episode_count_match = all(values == [120] for values in episodes_by_method.values())
    row_count_checks = {
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
    seed_match = output_seeds == sorted(int(seed) for seed in seeds)
    method_match = output_methods == sorted(methods)
    event_match = output_events == expected_events
    all_match = (
        all(check["matches"] for check in row_count_checks.values())
        and seed_match
        and method_match
        and event_match
        and zero_rows_valid
        and nonzero_rows_valid
        and episode_count_match
    )
    return {
        "schema_version": "0.1.0",
        "alpha": float(alpha),
        "confidence": float(1.0 - alpha),
        "row_count_checks": row_count_checks,
        "seed_coverage": {
            "observed": output_seeds,
            "expected": sorted(int(seed) for seed in seeds),
            "matches": seed_match,
        },
        "method_coverage": {
            "observed": output_methods,
            "expected": sorted(methods),
            "matches": method_match,
        },
        "event_coverage": {
            "observed": output_events,
            "expected": expected_events,
            "matches": event_match,
        },
        "episodes_by_method": episodes_by_method,
        "episode_count_match": episode_count_match,
        "zero_bound_applicability": {
            "zero_summary_rows": len(zero_summary_rows),
            "zero_rows_valid": zero_rows_valid,
            "nonzero_rows_valid": nonzero_rows_valid,
        },
        "all_match": all_match,
    }


def export_zero_event_confidence_bounds_4obj(
    table_b_summary_path: str | Path = DEFAULT_TABLE_B_SUMMARY_PATH,
    *,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    paper_table_dir: str | Path = DEFAULT_PAPER_TABLE_DIR,
    seeds: Iterable[int] = DEFAULT_SEEDS,
    methods: Iterable[str] = METHOD_ORDER,
    alpha: float = DEFAULT_ALPHA,
) -> dict[str, str]:
    table_b_summary_path = Path(table_b_summary_path).resolve()
    output_root = Path(output_root).resolve()
    paper_table_dir = Path(paper_table_dir).resolve()
    seed_tuple = tuple(int(seed) for seed in seeds)
    method_tuple = tuple(str(method) for method in methods)
    if seed_tuple != DEFAULT_SEEDS:
        raise ValueError(f"Zero-event bounds must use seeds {DEFAULT_SEEDS}")
    if method_tuple != METHOD_ORDER:
        raise ValueError(f"Zero-event bounds must use methods {METHOD_ORDER}")
    if not 0.0 < float(alpha) < 1.0:
        raise ValueError("alpha must be in (0, 1)")

    metric_paths = _collect_metric_paths(
        table_b_summary_path,
        seeds=seed_tuple,
        methods=method_tuple,
    )
    per_seed_rows = _build_per_seed_rows(
        metric_paths=metric_paths,
        seeds=seed_tuple,
        methods=method_tuple,
        alpha=float(alpha),
    )
    summary_rows = _build_summary_rows(
        per_seed_rows=per_seed_rows,
        methods=method_tuple,
        alpha=float(alpha),
    )
    verification_summary = _build_verification_summary(
        per_seed_rows=per_seed_rows,
        summary_rows=summary_rows,
        seeds=seed_tuple,
        methods=method_tuple,
        alpha=float(alpha),
    )

    output_root.mkdir(parents=True, exist_ok=True)
    paper_table_dir.mkdir(parents=True, exist_ok=True)
    per_seed_json_path = output_root / "zero_event_bounds_per_seed.json"
    per_seed_csv_path = output_root / "zero_event_bounds_per_seed.csv"
    summary_json_path = output_root / "zero_event_bounds_summary.json"
    summary_csv_path = output_root / "zero_event_bounds_summary.csv"
    summary_tex_path = output_root / "zero_event_bounds_summary.tex"
    verification_path = output_root / "verification_summary.json"
    paper_tex_path = paper_table_dir / "zero_event_confidence_bounds_4obj.tex"

    common_metadata = {
        "schema_version": "0.1.0",
        "table_b_summary_path": str(table_b_summary_path),
        "seeds": list(seed_tuple),
        "methods": list(method_tuple),
        "alpha": float(alpha),
        "confidence": float(1.0 - alpha),
        "event_specs": list(EVENT_SPECS),
    }
    save_json(per_seed_json_path, {**common_metadata, "records": per_seed_rows})
    _write_csv(per_seed_csv_path, per_seed_rows, PER_SEED_COLUMNS)
    save_json(summary_json_path, {**common_metadata, "records": summary_rows})
    _write_csv(summary_csv_path, summary_rows, SUMMARY_COLUMNS)
    _write_summary_tex(summary_tex_path, summary_rows, alpha=float(alpha))
    paper_tex_path.write_text(summary_tex_path.read_text(encoding="utf-8"), encoding="utf-8")
    save_json(verification_path, verification_summary)

    if not verification_summary["all_match"]:
        raise ValueError(f"Zero-event confidence-bound verification failed; see {verification_path}")

    return {
        "zero_event_bounds_per_seed_json": str(per_seed_json_path.resolve()),
        "zero_event_bounds_per_seed_csv": str(per_seed_csv_path.resolve()),
        "zero_event_bounds_summary_json": str(summary_json_path.resolve()),
        "zero_event_bounds_summary_csv": str(summary_csv_path.resolve()),
        "zero_event_bounds_summary_tex": str(summary_tex_path.resolve()),
        "paper_zero_event_bounds_tex": str(paper_tex_path.resolve()),
        "verification_summary_json": str(verification_path.resolve()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export zero-observed critical-event confidence bounds for the 4-objective paper suite."
    )
    parser.add_argument("--table-b-summary-path", default=str(DEFAULT_TABLE_B_SUMMARY_PATH))
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--paper-table-dir", default=str(DEFAULT_PAPER_TABLE_DIR))
    parser.add_argument("--alpha", type=float, default=DEFAULT_ALPHA)
    args = parser.parse_args()
    outputs = export_zero_event_confidence_bounds_4obj(
        table_b_summary_path=args.table_b_summary_path,
        output_root=args.output_root,
        paper_table_dir=args.paper_table_dir,
        alpha=args.alpha,
    )
    print(json.dumps(outputs, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
