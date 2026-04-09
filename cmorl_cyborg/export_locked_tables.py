from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

SET_METHOD_ORDER = [
    "ours_stage2",
    "stage1_only",
    "weighted_sum",
    "preference_conditioned_ppo",
    "pcn",
]

DEPLOYMENT_METHOD_ORDER = [
    "ours_stage2",
    "lagrangian_ppo",
    "weighted_sum",
    "stage1_only",
    "no_constraint_stage2",
    "single_objective",
]

DISPLAY_NAME = {
    "ours_stage2": "Ours Stage2",
    "stage1_only": "Stage1 Only",
    "weighted_sum": "Weighted-Sum",
    "preference_conditioned_ppo": "Preference-Conditioned PPO",
    "pcn": "PCN",
    "lagrangian_ppo": "Lagrangian PPO",
    "no_constraint_stage2": "No-Constraint Stage2",
    "single_objective": "Single-Objective",
}


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_json(path: str | Path, payload: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _parse_export_config(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    lines = config_path.read_text(encoding="utf-8").splitlines()
    compare_summary_path = ""
    output_dir = ""
    constraint_metrics_paths: list[str] = []
    appendix_metrics_paths: list[str] = []
    current_list: list[str] | None = None

    for raw_line in lines:
        line = raw_line.split("#", 1)[0].rstrip()
        if not line:
            continue
        if line.startswith("compare_summary_path:"):
            compare_summary_path = line.split(":", 1)[1].strip()
            current_list = None
        elif line.startswith("output_dir:"):
            output_dir = line.split(":", 1)[1].strip()
            current_list = None
        elif line.startswith("constraint_metrics_paths:"):
            current_list = constraint_metrics_paths
        elif line.startswith("appendix_metrics_paths:"):
            current_list = appendix_metrics_paths
        elif line.lstrip().startswith("- ") and current_list is not None:
            current_list.append(line.lstrip()[2:].strip())
        else:
            current_list = None

    return {
        "compare_summary_path": compare_summary_path,
        "output_dir": output_dir,
        "constraint_metrics_paths": constraint_metrics_paths,
        "appendix_metrics_paths": appendix_metrics_paths,
    }


def _format_mean_std(mean: float, std: float) -> str:
    return f"{mean:.4f} $\\pm$ {std:.4f}"


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _write_tex(path: Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
    def tex_escape(value: Any, *, preserve_math: bool = False) -> str:
        text = str(value)
        if preserve_math:
            return text.replace("_", "\\_")
        return text.replace("\\", "\\textbackslash{}").replace("_", "\\_")

    path.parent.mkdir(parents=True, exist_ok=True)
    align = "l" + "c" * (len(columns) - 1)
    lines = [
        "\\begin{tabular}{" + align + "}",
        "\\hline",
        " & ".join(tex_escape(column) for column in columns) + " \\\\",
        "\\hline",
    ]
    for row in rows:
        lines.append(
            " & ".join(tex_escape(row[column], preserve_math=True) for column in columns) + " \\\\"
        )
    lines.extend(["\\hline", "\\end{tabular}"])
    path.write_text("\n".join(lines), encoding="utf-8")


def _ordered_rows(rows_by_method: dict[str, dict[str, Any]], order: list[str]) -> list[dict[str, Any]]:
    return [rows_by_method[method_name] for method_name in order if method_name in rows_by_method]


def _build_set_quality(compare_summary: dict[str, Any]) -> dict[str, Any]:
    rows_by_method: dict[str, dict[str, Any]] = {}
    json_rows: list[dict[str, Any]] = []
    for entry in compare_summary.get("method_summary", []):
        method_name = entry["method_name"]
        row = {
            "method_name": method_name,
            "display_name": entry.get("display_group", DISPLAY_NAME.get(method_name, method_name)),
            "hypervolume": _format_mean_std(entry["hypervolume"]["mean"], entry["hypervolume"]["std"]),
            "expected_utility": _format_mean_std(
                entry["expected_utility"]["mean"], entry["expected_utility"]["std"]
            ),
            "coverage_ratio": _format_mean_std(
                entry["coverage_ratio"]["mean"], entry["coverage_ratio"]["std"]
            ),
            "unique_assigned_policies": _format_mean_std(
                entry["unique_assigned_policies"]["mean"], entry["unique_assigned_policies"]["std"]
            ),
            "num_pareto_records": _format_mean_std(
                entry["num_pareto_records"]["mean"], entry["num_pareto_records"]["std"]
            ),
        }
        rows_by_method[method_name] = row
        json_rows.append(
            {
                "method_name": method_name,
                "display_name": row["display_name"],
                "num_runs": entry["num_runs"],
                "metrics": {
                    "hypervolume": entry["hypervolume"],
                    "expected_utility": entry["expected_utility"],
                    "coverage_ratio": entry["coverage_ratio"],
                    "unique_assigned_policies": entry["unique_assigned_policies"],
                    "num_pareto_records": entry["num_pareto_records"],
                },
            }
        )
    return {
        "rows": _ordered_rows(rows_by_method, SET_METHOD_ORDER),
        "json_rows": _ordered_rows({row["method_name"]: row for row in json_rows}, SET_METHOD_ORDER),
        "reference_point": compare_summary.get("reference_point"),
        "source_summary_path": compare_summary.get("config_path"),
    }


def _build_deployment(constraint_paths: list[str]) -> dict[str, Any]:
    rows_by_method: dict[str, dict[str, Any]] = {}
    json_rows: list[dict[str, Any]] = []
    shared_thresholds: dict[str, Any] | None = None
    for path_str in constraint_paths:
        payload = load_json(path_str)
        method_name = payload["method_name"]
        row = {
            "method_name": method_name,
            "display_name": DISPLAY_NAME.get(method_name, method_name),
            "security_return": _format_mean_std(
                float(payload.get("security_return", 0.0)),
                float(payload.get("security_return_std", 0.0)),
            ),
            "business_return": _format_mean_std(
                float(payload.get("business_return", 0.0)),
                float(payload.get("business_return_std", 0.0)),
            ),
            "cost_return": _format_mean_std(
                float(payload.get("cost_return", 0.0)),
                float(payload.get("cost_return_std", 0.0)),
            ),
            "feasible_rate": _format_mean_std(
                float(payload.get("feasible_rate", 0.0)),
                float(payload.get("feasible_rate_std", 0.0)),
            ),
            "mean_violation": _format_mean_std(
                float(payload.get("mean_violation", 0.0)),
                float(payload.get("mean_violation_std", 0.0)),
            ),
            "final_critical_compromised_hosts": _format_mean_std(
                float(payload.get("final_critical_compromised_hosts", 0.0)),
                float(payload.get("final_critical_compromised_hosts_std", 0.0)),
            ),
        }
        rows_by_method[method_name] = row
        json_rows.append(
            {
                "method_name": method_name,
                "display_name": row["display_name"],
                "num_runs": int(payload.get("num_runs", 0)),
                "thresholds": payload.get("thresholds", {}),
                "metrics": {
                    "security_return": {
                        "mean": float(payload.get("security_return", 0.0)),
                        "std": float(payload.get("security_return_std", 0.0)),
                    },
                    "business_return": {
                        "mean": float(payload.get("business_return", 0.0)),
                        "std": float(payload.get("business_return_std", 0.0)),
                    },
                    "cost_return": {
                        "mean": float(payload.get("cost_return", 0.0)),
                        "std": float(payload.get("cost_return_std", 0.0)),
                    },
                    "feasible_rate": {
                        "mean": float(payload.get("feasible_rate", 0.0)),
                        "std": float(payload.get("feasible_rate_std", 0.0)),
                    },
                    "mean_violation": {
                        "mean": float(payload.get("mean_violation", 0.0)),
                        "std": float(payload.get("mean_violation_std", 0.0)),
                    },
                    "final_critical_compromised_hosts": {
                        "mean": float(payload.get("final_critical_compromised_hosts", 0.0)),
                        "std": float(payload.get("final_critical_compromised_hosts_std", 0.0)),
                    },
                },
            }
        )
        if shared_thresholds is None:
            shared_thresholds = payload.get("thresholds", {})
    return {
        "rows": _ordered_rows(rows_by_method, DEPLOYMENT_METHOD_ORDER),
        "json_rows": _ordered_rows({row["method_name"]: row for row in json_rows}, DEPLOYMENT_METHOD_ORDER),
        "shared_thresholds": shared_thresholds or {},
        "source_constraint_paths": constraint_paths,
    }


def export_locked_tables(config_path: str | Path) -> dict[str, str]:
    config = _parse_export_config(config_path)
    compare_summary = load_json(config["compare_summary_path"])

    set_quality = _build_set_quality(compare_summary)
    deployment = _build_deployment(list(config["constraint_metrics_paths"]))

    set_dir = Path("cmorl_cyborg/outputs/paper_table_a").resolve()
    deploy_dir = Path("cmorl_cyborg/outputs/paper_table_b").resolve()

    set_csv = set_dir / "set_quality_table.csv"
    set_tex = set_dir / "set_quality_table.tex"
    set_json = set_dir / "set_quality_table.json"
    deploy_csv = deploy_dir / "deployment_table.csv"
    deploy_tex = deploy_dir / "deployment_table.tex"
    deploy_json = deploy_dir / "deployment_table.json"

    set_columns = [
        "method_name",
        "display_name",
        "hypervolume",
        "expected_utility",
        "coverage_ratio",
        "unique_assigned_policies",
        "num_pareto_records",
    ]
    deploy_columns = [
        "method_name",
        "display_name",
        "security_return",
        "business_return",
        "cost_return",
        "feasible_rate",
        "mean_violation",
        "final_critical_compromised_hosts",
    ]

    _write_csv(set_csv, set_columns, set_quality["rows"])
    _write_tex(set_tex, set_columns, set_quality["rows"])
    _write_csv(deploy_csv, deploy_columns, deployment["rows"])
    _write_tex(deploy_tex, deploy_columns, deployment["rows"])

    save_json(
        set_json,
        {
            "table_name": "Set Quality Table",
            "metrics": [
                "hypervolume",
                "expected_utility",
                "coverage_ratio",
                "unique_assigned_policies",
            "num_pareto_records",
        ],
        "reference_point": set_quality["reference_point"],
        "source_compare_summary_path": str(Path(config["compare_summary_path"]).resolve()),
        "rows": set_quality["json_rows"],
        },
    )
    save_json(
        deploy_json,
        {
            "table_name": "Deployment Table",
            "metrics": [
                "security_return",
                "business_return",
                "cost_return",
                "feasible_rate",
            "mean_violation",
            "final_critical_compromised_hosts",
        ],
        "shared_thresholds": deployment["shared_thresholds"],
        "source_constraint_paths": [
            str(Path(path).resolve()) for path in config["constraint_metrics_paths"]
        ],
        "rows": deployment["json_rows"],
        },
    )
    return {
        "set_csv": str(set_csv),
        "set_tex": str(set_tex),
        "set_json": str(set_json),
        "deployment_csv": str(deploy_csv),
        "deployment_tex": str(deploy_tex),
        "deployment_json": str(deploy_json),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Export locked CybORG paper tables.")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    outputs = export_locked_tables(args.config)
    print(outputs)


if __name__ == "__main__":
    main()
