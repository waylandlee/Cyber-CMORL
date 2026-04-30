from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

from cmorl_minicage.utils import ensure_dir, load_json, save_json


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "cmorl_cyborg" / "outputs" / "paper_4obj" / "rq4_ablation"
DEFAULT_TABLE_A_SUMMARY_PATH = (
    REPO_ROOT / "cmorl_cyborg" / "outputs" / "paper_4obj" / "table_a" / "table_a_summary.json"
)
DEFAULT_DEPLOYMENT_ROOT = (
    REPO_ROOT / "cmorl_cyborg" / "outputs" / "paper_4obj" / "table_b" / "aggregated"
)
DEFAULT_SEMANTIC_COMPARISON_PATH = (
    REPO_ROOT
    / "cmorl_cyborg"
    / "outputs"
    / "paper_4obj"
    / "rq3_symmetric"
    / "semantic_comparison"
    / "semantic_comparison_aggregate.json"
)
DEFAULT_PAPER_TABLE_PATH = REPO_ROOT / "paper" / "table" / "rq4_ablation_summary.tex"
DEFAULT_OBJECTIVE_ABLATION_SUMMARY_PATH = (
    REPO_ROOT
    / "cmorl_cyborg"
    / "outputs"
    / "paper_ablation"
    / "objective_3obj_vs_4obj"
    / "objective_ablation_summary.json"
)

METHOD_DISPLAY = {
    "ours_stage2_v2_4": "Constraint-Aware Stage-2",
    "stage1_only_4obj": "Stage-1 Policy Archive",
    "no_constraint_stage2_4obj": "Unconstrained Stage-2",
    "ours_stage2": "3-Objective Stage-2",
}

PANEL_SPECS = (
    {
        "panel_key": "stage2_vs_stage1",
        "panel_title": "A. Stage-1 vs. Constraint-Aware",
        "left_method_name": "stage1_only_4obj",
        "right_method_name": "ours_stage2_v2_4",
        "metrics": (
            {"source": "table_a", "metric_key": "hypervolume", "metric_label": "HV ($\\times 10^6$)"},
            {"source": "table_a", "metric_key": "expected_utility", "metric_label": "EU"},
            {"source": "deployment", "metric_key": "feasible_rate", "metric_label": "Feasible"},
            {"source": "deployment", "metric_key": "mean_violation", "metric_label": "Violation"},
        ),
    },
    {
        "panel_key": "constraint_aware_vs_unconstrained",
        "panel_title": "B. Unconstrained vs. Constraint-Aware",
        "left_method_name": "no_constraint_stage2_4obj",
        "right_method_name": "ours_stage2_v2_4",
        "metrics": (
            {"source": "deployment", "metric_key": "feasible_rate", "metric_label": "Feasible"},
            {"source": "deployment", "metric_key": "mean_violation", "metric_label": "Violation"},
            {
                "source": "semantic",
                "metric_key": "Q4_user_focus_after_enterprise_foothold",
                "metric_label": "Q4 Drift",
            },
            {
                "source": "semantic",
                "metric_key": "Q5_repeated_low_value_decoy_loop",
                "metric_label": "Q5 Decoy Loop",
            },
        ),
    },
)

OBJECTIVE_PANEL_METRICS = (
    ("projected_hypervolume_3d", "Proj. 3D HV"),
    ("projected_expected_utility_3d", "Proj. 3D EU"),
    ("feasible_rate", "Feasible"),
    ("mean_violation", "Violation"),
    ("ever_critical_breach_rate", "Any Critical Breach"),
    ("persistent_critical_breach_rate", "Sustained Critical Breach"),
    ("Q4_user_focus_after_enterprise_foothold", "Q4 Drift"),
    ("Q5_repeated_low_value_decoy_loop", "Q5 Decoy Loop"),
)

HIGHER_IS_BETTER_METRICS = {
    "hypervolume",
    "expected_utility",
    "feasible_rate",
    "projected_hypervolume_3d",
    "projected_expected_utility_3d",
}


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _table_a_lookup(summary_path: str | Path) -> dict[str, dict[str, Any]]:
    payload = _load_json(summary_path)
    lookup: dict[str, dict[str, Any]] = {}
    for row in payload.get("method_summary", []):
        method_name = str(row.get("method_name", ""))
        if method_name:
            lookup[method_name] = row
    if not lookup:
        raise ValueError(f"Missing method_summary rows in {summary_path}")
    return lookup


def _deployment_lookup(paths: dict[str, str | Path]) -> dict[str, dict[str, Any]]:
    return {
        method_name: _load_json(path)
        for method_name, path in paths.items()
    }


def _semantic_lookup(summary_path: str | Path) -> dict[str, dict[str, Any]]:
    payload = _load_json(summary_path)
    lookup = {
        str(payload["left_method_name"]): payload["left"],
        str(payload["right_method_name"]): payload["right"],
    }
    return lookup


def _metric_stats(
    *,
    source: str,
    metric_key: str,
    method_name: str,
    table_a_rows: dict[str, dict[str, Any]],
    deployment_rows: dict[str, dict[str, Any]],
    semantic_rows: dict[str, dict[str, Any]],
) -> tuple[float, float | None]:
    if source == "table_a":
        method_row = table_a_rows[method_name]
        metric = method_row[metric_key]
        return float(metric["mean"]), float(metric["std"])
    if source == "deployment":
        method_row = deployment_rows[method_name]
        return float(method_row[metric_key]), float(method_row.get(f"{metric_key}_std", 0.0))
    if source == "semantic":
        method_row = semantic_rows[method_name]
        return float(method_row[metric_key]), None
    raise ValueError(f"Unsupported source: {source}")


def _format_metric_value(metric_key: str, value: float) -> str:
    if "hypervolume" in metric_key:
        return f"{value / 1_000_000.0:.3f}"
    if "expected_utility" in metric_key:
        return f"{value:.3f}"
    return f"{value:.3f}"


def _metric_prefers_higher(metric_key: str) -> bool:
    return metric_key in HIGHER_IS_BETTER_METRICS


def _is_best(metric_key: str, value: float, other: float) -> bool:
    if _metric_prefers_higher(metric_key):
        return value > other or math.isclose(value, other, rel_tol=1e-12, abs_tol=1e-12)
    return value < other or math.isclose(value, other, rel_tol=1e-12, abs_tol=1e-12)


def _latex_metric_cell(metric_key: str, value: float, other: float) -> str:
    formatted = _format_metric_value(metric_key, value)
    if _is_best(metric_key, value, other):
        return f"\\textbf{{{formatted}}}"
    return formatted


def _load_objective_panel(path: str | Path) -> dict[str, Any]:
    payload = _load_json(path)
    required = {
        "panel_key",
        "panel_title",
        "left_method_name",
        "left_display_name",
        "right_method_name",
        "right_display_name",
        "rows",
    }
    missing = sorted(required - set(payload))
    if missing:
        raise ValueError(f"Missing objective ablation panel fields in {path}: {missing}")
    rows = list(payload.get("rows", []))
    if not rows:
        raise ValueError(f"Objective ablation panel has no rows: {path}")
    return payload


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> Path:
    fieldnames = [
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
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
    return path.resolve()


def _write_tex(path: Path, panels: list[dict[str, Any]]) -> Path:
    lines = [
        "\\resizebox{\\columnwidth}{!}{%",
        "\\begin{tabular}{@{}lcc@{}}",
        "\\toprule",
    ]
    for index, panel in enumerate(panels):
        if index > 0:
            lines.append("\\midrule")
        lines.append(f"\\multicolumn{{3}}{{@{{}}l}}{{\\textbf{{{panel['panel_title']}}}}}\\\\")
        lines.append(
            f"Metric & {panel['left_display_name']} & {panel['right_display_name']} \\\\"
        )
        lines.append("\\midrule")
        for row in panel["rows"]:
            left_mean = float(row["left_mean"])
            right_mean = float(row["right_mean"])
            lines.append(
                f"{row['metric_label']} & "
                f"{_latex_metric_cell(row['metric_key'], left_mean, right_mean)} & "
                f"{_latex_metric_cell(row['metric_key'], right_mean, left_mean)} \\\\"
            )
    lines.extend(["\\bottomrule", "\\end{tabular}%", "}"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path.resolve()


def export_rq4_ablation_summary(
    *,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    table_a_summary_path: str | Path = DEFAULT_TABLE_A_SUMMARY_PATH,
    semantic_comparison_path: str | Path = DEFAULT_SEMANTIC_COMPARISON_PATH,
    paper_table_path: str | Path = DEFAULT_PAPER_TABLE_PATH,
    objective_ablation_summary_path: str | Path | None = DEFAULT_OBJECTIVE_ABLATION_SUMMARY_PATH,
    deployment_paths: dict[str, str | Path] | None = None,
) -> dict[str, str]:
    output_root = ensure_dir(Path(output_root))
    paper_table_path = Path(paper_table_path)
    if deployment_paths is None:
        deployment_paths = {
            "ours_stage2_v2_4": DEFAULT_DEPLOYMENT_ROOT / "ours_stage2_v2_4.json",
            "stage1_only_4obj": DEFAULT_DEPLOYMENT_ROOT / "stage1_only_4obj.json",
            "no_constraint_stage2_4obj": DEFAULT_DEPLOYMENT_ROOT / "no_constraint_stage2_4obj.json",
        }

    table_a_rows = _table_a_lookup(table_a_summary_path)
    deployment_rows = _deployment_lookup(deployment_paths)
    semantic_rows = _semantic_lookup(semantic_comparison_path)

    panel_payloads: list[dict[str, Any]] = []
    flat_rows: list[dict[str, Any]] = []
    deltas: dict[str, dict[str, float]] = {}
    for spec in PANEL_SPECS:
        left_method_name = spec["left_method_name"]
        right_method_name = spec["right_method_name"]
        panel_rows: list[dict[str, Any]] = []
        panel_deltas: dict[str, float] = {}
        for metric_spec in spec["metrics"]:
            metric_key = str(metric_spec["metric_key"])
            left_mean, left_std = _metric_stats(
                source=str(metric_spec["source"]),
                metric_key=metric_key,
                method_name=left_method_name,
                table_a_rows=table_a_rows,
                deployment_rows=deployment_rows,
                semantic_rows=semantic_rows,
            )
            right_mean, right_std = _metric_stats(
                source=str(metric_spec["source"]),
                metric_key=metric_key,
                method_name=right_method_name,
                table_a_rows=table_a_rows,
                deployment_rows=deployment_rows,
                semantic_rows=semantic_rows,
            )
            delta = float(right_mean) - float(left_mean)
            row = {
                "panel_key": spec["panel_key"],
                "panel_title": spec["panel_title"],
                "metric_key": metric_key,
                "metric_label": metric_spec["metric_label"],
                "metric_source": metric_spec["source"],
                "left_method_name": left_method_name,
                "left_display_name": METHOD_DISPLAY[left_method_name],
                "left_mean": float(left_mean),
                "left_std": None if left_std is None else float(left_std),
                "right_method_name": right_method_name,
                "right_display_name": METHOD_DISPLAY[right_method_name],
                "right_mean": float(right_mean),
                "right_std": None if right_std is None else float(right_std),
                "delta_right_minus_left": delta,
            }
            panel_rows.append(row)
            flat_rows.append(row)
            panel_deltas[metric_key] = delta

        panel_payloads.append(
            {
                "panel_key": spec["panel_key"],
                "panel_title": spec["panel_title"],
                "left_method_name": left_method_name,
                "left_display_name": METHOD_DISPLAY[left_method_name],
                "right_method_name": right_method_name,
                "right_display_name": METHOD_DISPLAY[right_method_name],
                "rows": panel_rows,
            }
        )
        deltas[spec["panel_key"]] = panel_deltas

    objective_panel_path_resolved: str | None = None
    if objective_ablation_summary_path is not None and Path(objective_ablation_summary_path).exists():
        objective_panel = _load_objective_panel(objective_ablation_summary_path)
        objective_panel_path_resolved = str(Path(objective_ablation_summary_path).resolve())
        objective_row_lookup = {
            str(row["metric_key"]): row for row in objective_panel["rows"]
        }
        objective_rows: list[dict[str, Any]] = []
        objective_deltas: dict[str, float] = {}
        for metric_key, metric_label in OBJECTIVE_PANEL_METRICS:
            row = objective_row_lookup[metric_key]
            payload = {
                "panel_key": objective_panel["panel_key"],
                "panel_title": "C. 3obj vs. 4obj",
                "metric_key": metric_key,
                "metric_label": metric_label,
                "metric_source": str(row["metric_source"]),
                "left_method_name": str(row["left_method_name"]),
                "left_display_name": str(row["left_display_name"]),
                "left_mean": float(row["left_mean"]),
                "left_std": None if row.get("left_std") is None else float(row["left_std"]),
                "right_method_name": str(row["right_method_name"]),
                "right_display_name": str(row["right_display_name"]),
                "right_mean": float(row["right_mean"]),
                "right_std": None if row.get("right_std") is None else float(row["right_std"]),
                "delta_right_minus_left": float(row["delta_right_minus_left"]),
            }
            objective_rows.append(payload)
            flat_rows.append(payload)
            objective_deltas[payload["metric_key"]] = float(payload["delta_right_minus_left"])
        panel_payloads.append(
            {
                "panel_key": str(objective_panel["panel_key"]),
                "panel_title": "C. 3obj vs. 4obj",
                "left_method_name": str(objective_panel["left_method_name"]),
                "left_display_name": str(objective_panel["left_display_name"]),
                "right_method_name": str(objective_panel["right_method_name"]),
                "right_display_name": str(objective_panel["right_display_name"]),
                "rows": objective_rows,
            }
        )
        deltas[str(objective_panel["panel_key"])] = objective_deltas

    summary_payload = {
        "source_paths": {
            "table_a_summary_path": str(Path(table_a_summary_path).resolve()),
            "semantic_comparison_path": str(Path(semantic_comparison_path).resolve()),
            "objective_ablation_summary_path": objective_panel_path_resolved,
            "deployment_paths": {
                method_name: str(Path(path).resolve())
                for method_name, path in deployment_paths.items()
            },
        },
        "panels": panel_payloads,
        "paper_table_path": str(paper_table_path.resolve()),
    }

    summary_json = output_root / "rq4_ablation_summary.json"
    summary_csv = output_root / "rq4_ablation_summary.csv"
    summary_tex = output_root / "rq4_ablation_summary.tex"
    deltas_json = output_root / "rq4_ablation_deltas.json"
    save_json(summary_json, summary_payload)
    _write_csv(summary_csv, flat_rows)
    _write_tex(summary_tex, panel_payloads)
    save_json(deltas_json, deltas)
    _write_tex(paper_table_path, panel_payloads)

    return {
        "summary_json": str(summary_json.resolve()),
        "summary_csv": str(summary_csv.resolve()),
        "summary_tex": str(summary_tex.resolve()),
        "deltas_json": str(deltas_json.resolve()),
        "paper_table_path": str(paper_table_path.resolve()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export the current paper_4obj RQ4 ablation summary."
    )
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--table-a-summary-path", default=str(DEFAULT_TABLE_A_SUMMARY_PATH))
    parser.add_argument("--semantic-comparison-path", default=str(DEFAULT_SEMANTIC_COMPARISON_PATH))
    parser.add_argument("--paper-table-path", default=str(DEFAULT_PAPER_TABLE_PATH))
    parser.add_argument(
        "--objective-ablation-summary-path",
        default=str(DEFAULT_OBJECTIVE_ABLATION_SUMMARY_PATH),
    )
    args = parser.parse_args()

    outputs = export_rq4_ablation_summary(
        output_root=args.output_root,
        table_a_summary_path=args.table_a_summary_path,
        semantic_comparison_path=args.semantic_comparison_path,
        paper_table_path=args.paper_table_path,
        objective_ablation_summary_path=args.objective_ablation_summary_path,
    )
    print(json.dumps(outputs, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
