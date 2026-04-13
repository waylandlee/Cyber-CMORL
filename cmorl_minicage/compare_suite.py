from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from cmorl_minicage.buffer import load_policy_buffer
from cmorl_minicage.config import load_compare_suite_config
from cmorl_minicage.evaluate import (
    archive_diagnostics_payload,
    evaluate_policy_buffer,
    evaluate_policy_buffer_all_modes,
    resolve_reference_point,
)
from cmorl_minicage.evaluate_conditioned import (
    evaluate_conditioned_points_payload,
)
from cmorl_minicage.utils import load_json, save_json


def _load_conditioned_payload(path: str | Path) -> dict[str, Any]:
    payload = load_json(path)
    if "evaluated_points" not in payload:
        raise ValueError(f"Expected conditioned_points payload: {path}")
    return payload


def _entry_pareto_points(entry: dict[str, Any]) -> list[list[float]]:
    artifact_kind = entry["artifact_kind"]
    artifact_path = entry["artifact_path"]
    if artifact_kind == "buffer":
        payload = load_policy_buffer(artifact_path)
        pareto = payload.get("pareto_front", [])
        return [record["objective_vector"] for record in pareto]
    if artifact_kind == "conditioned_points":
        payload = _load_conditioned_payload(artifact_path)
        points_payload = evaluate_conditioned_points_payload(
            payload,
            preference_step=entry.get("preference_step"),
            reference_strategy=entry.get("reference_strategy", "data_min_range"),
            reference_margin=float(entry.get("reference_margin", 0.25)),
            reference_point=None,
            hv_max_exact_points=int(entry.get("hv_max_exact_points", 18)),
            hv_mc_samples=int(entry.get("hv_mc_samples", 100000)),
        )
        return [record["objective_vector"] for record in points_payload["pareto_front"]]
    raise ValueError(f"Unsupported artifact_kind: {artifact_kind}")


def _summary_row(entry: dict[str, Any], metrics_payload: dict[str, Any]) -> dict[str, Any]:
    metrics = metrics_payload["metrics"]
    assignment_summary = metrics_payload.get("assignment_summary", {})
    semantic_metrics = metrics_payload.get("semantic_metrics", {})
    return {
        "method_name": entry["method_name"],
        "display_group": entry.get("display_group", entry["method_name"]),
        "seed": int(entry.get("seed", 0)),
        "artifact_kind": entry["artifact_kind"],
        "artifact_path": entry["artifact_path"],
        "hypervolume": float(metrics["hypervolume"]),
        "expected_utility": float(metrics["expected_utility"]),
        "sparsity": float(metrics["sparsity"]),
        "num_pareto_records": int(metrics["num_pareto_records"]),
        "coverage_ratio": float(assignment_summary.get("coverage_ratio", 0.0)),
        "unique_assigned_policies": int(
            assignment_summary.get("unique_assigned_policies", 0)
        ),
        "semantic_metrics": semantic_metrics,
        "metrics_path": "",
    }


def _aggregate_method_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["method_name"]].append(row)

    aggregated: list[dict[str, Any]] = []
    for method_name, method_rows in sorted(grouped.items()):
        display_group = method_rows[0]["display_group"]
        metric_names = [
            "hypervolume",
            "expected_utility",
            "sparsity",
            "num_pareto_records",
            "coverage_ratio",
            "unique_assigned_policies",
        ]
        semantic_keys = sorted(
            {
                key
                for row in method_rows
                for key in row.get("semantic_metrics", {})
                if key != "semantic_eval_episodes"
            }
        )
        entry: dict[str, Any] = {
            "method_name": method_name,
            "display_group": display_group,
            "num_runs": len(method_rows),
            "runs": method_rows,
        }
        for metric_name in metric_names:
            values = np.asarray([row[metric_name] for row in method_rows], dtype=np.float64)
            entry[metric_name] = {
                "mean": float(np.mean(values)),
                "std": float(np.std(values)),
            }
        entry["semantic_metrics"] = {
            key: {
                "mean": float(
                    np.mean(
                        [
                            float(row.get("semantic_metrics", {}).get(key, 0.0))
                            for row in method_rows
                        ]
                    )
                ),
                "std": float(
                    np.std(
                        [
                            float(row.get("semantic_metrics", {}).get(key, 0.0))
                            for row in method_rows
                        ]
                    )
                ),
            }
            for key in semantic_keys
        }
        aggregated.append(entry)
    return aggregated


def compare_suite(config_path: str | Path) -> Path:
    config = load_compare_suite_config(config_path)
    if not config.entries:
        raise ValueError("compare_suite entries must not be empty")

    all_points: list[list[float]] = []
    obj_dim = 0
    for entry in config.entries:
        entry_points = _entry_pareto_points(entry)
        if not entry_points:
            continue
        obj_dim = len(entry_points[0])
        all_points.extend(entry_points)
    if not all_points:
        raise ValueError("Could not compute shared reference from empty suite")

    reference_point = resolve_reference_point(
        np.asarray(all_points, dtype=np.float32),
        obj_dim=obj_dim,
        reference_strategy=config.reference_strategy,
        reference_margin=config.reference_margin,
        reference_point=config.reference_point,
    ).tolist()

    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    save_json(output_dir / "shared_reference.json", {"reference_point": reference_point})

    per_run_rows: list[dict[str, Any]] = []
    metrics_paths: list[str] = []
    metrics_paths_by_mode: dict[str, list[str]] = {"union": [], "strict": [], "hybrid": []}
    diagnostics_paths: list[str] = []
    for entry in config.entries:
        method_dir = output_dir / entry["method_name"] / f"seed_{int(entry.get('seed', 0)):04d}"
        method_dir.mkdir(parents=True, exist_ok=True)
        if entry["artifact_kind"] == "buffer":
            all_metrics = evaluate_policy_buffer_all_modes(
                entry["artifact_path"],
                entry.get("preference_step", config.preference_step),
                penalty_weights=entry.get("hybrid_penalty_weights"),
                strict_require_tight=bool(entry.get("strict_require_tight", False)),
                reference_strategy=config.reference_strategy,
                reference_margin=config.reference_margin,
                reference_point=reference_point,
                hv_max_exact_points=config.hv_max_exact_points,
                hv_mc_samples=config.hv_mc_samples,
            )
            for mode, payload in all_metrics.items():
                mode_path = method_dir / f"metrics_shared_ref_{mode}.json"
                save_json(mode_path, payload)
                metrics_paths_by_mode[mode].append(str(mode_path))
            diagnostics_path = method_dir / "archive_diagnostics.json"
            save_json(
                diagnostics_path,
                archive_diagnostics_payload(
                    entry["artifact_path"],
                    strict_payload=all_metrics["strict"],
                    hybrid_payload=all_metrics["hybrid"],
                ),
            )
            diagnostics_paths.append(str(diagnostics_path))
            metrics_payload = all_metrics["union"]
        elif entry["artifact_kind"] == "conditioned_points":
            payload = _load_conditioned_payload(entry["artifact_path"])
            metrics_payload = evaluate_conditioned_points_payload(
                payload,
                preference_step=entry.get("preference_step", config.preference_step),
                reference_strategy=config.reference_strategy,
                reference_margin=config.reference_margin,
                reference_point=reference_point,
                hv_max_exact_points=config.hv_max_exact_points,
                hv_mc_samples=config.hv_mc_samples,
            )
        else:
            raise ValueError(f"Unsupported artifact_kind: {entry['artifact_kind']}")

        metrics_path = method_dir / "metrics_shared_ref.json"
        save_json(metrics_path, metrics_payload)
        row = _summary_row(entry, metrics_payload)
        row["metrics_path"] = str(metrics_path)
        if entry["artifact_kind"] == "buffer":
            row["metrics_union_path"] = str(method_dir / "metrics_shared_ref_union.json")
            row["metrics_strict_path"] = str(method_dir / "metrics_shared_ref_strict.json")
            row["metrics_hybrid_path"] = str(method_dir / "metrics_shared_ref_hybrid.json")
            row["archive_diagnostics_path"] = str(method_dir / "archive_diagnostics.json")
        per_run_rows.append(row)
        metrics_paths.append(str(metrics_path))

    summary = {
        "reference_point": reference_point,
        "config_path": str(config_path),
        "per_run": per_run_rows,
        "method_summary": _aggregate_method_rows(per_run_rows),
        "metrics_paths": metrics_paths,
        "metrics_paths_by_mode": metrics_paths_by_mode,
        "archive_diagnostics_paths": diagnostics_paths,
    }
    summary_path = output_dir / "table_a_summary.json"
    save_json(summary_path, summary)
    return summary_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare multiple methods under a shared reference point."
    )
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    summary_path = compare_suite(args.config)
    print(summary_path)


if __name__ == "__main__":
    main()
