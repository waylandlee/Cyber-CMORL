from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from cmorl_minicage.config import (
    DEFAULT_STRICT_LEVEL_DIAGNOSTICS_CONFIG,
    StrictLevelDiagnosticsConfig,
    load_strict_level_diagnostics_config,
)
from cmorl_minicage.deployability import (
    CandidateMetrics,
    ThresholdProfile,
    build_threshold_profile,
    evaluate_profile,
)
from cmorl_minicage.evaluate_constraints import _load_thresholds
from cmorl_minicage.utils import save_json


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


def load_candidate_cache(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            rows.append(json.loads(stripped))
    return rows


def _level_profiles(
    *,
    profile_name: str,
    thresholds: dict[str, float],
    high_disruption_max: float,
    levels: list[dict[str, Any]],
) -> list[ThresholdProfile]:
    profiles: list[ThresholdProfile] = []
    for level in levels:
        profiles.append(
            build_threshold_profile(
                name=f"{profile_name}:{level['name']}",
                thresholds=thresholds,
                mean_violation_max=float(level["mean_violation_max"]),
                final_critical_max=float(level["final_critical_max"]),
                high_disruption_max=float(high_disruption_max),
            )
        )
    return profiles


def _sorted_fail_dims(profile_eval: dict[str, Any]) -> list[str]:
    normalized_margins = dict(profile_eval.get("normalized_margins", {}))
    fail_dims = list(profile_eval.get("fail_dims", []))
    return sorted(
        fail_dims,
        key=lambda dim: (float(normalized_margins.get(dim, 0.0)), dim),
    )


def run_strict_level_diagnostics_rows(
    candidate_rows: list[dict[str, Any]],
    *,
    thresholds: dict[str, float],
    output_root: str | Path,
    run_label: str,
    profile_name: str,
    high_disruption_max: float,
    levels: list[dict[str, Any]],
) -> dict[str, str]:
    output_root = Path(output_root)
    run_dir = output_root / run_label
    run_dir.mkdir(parents=True, exist_ok=True)

    profiles = _level_profiles(
        profile_name=profile_name,
        thresholds=thresholds,
        high_disruption_max=high_disruption_max,
        levels=levels,
    )
    level_names = [str(level["name"]) for level in levels]
    best_level_counts = {level_name: 0 for level_name in level_names}
    pass_counts = {level_name: 0 for level_name in level_names}
    blocker_histogram = {
        f"{'none' if idx == 0 else level_names[idx - 1]}->{level_name}": {}
        for idx, level_name in enumerate(level_names)
    }
    unreached_count = 0
    candidate_output_rows: list[dict[str, Any]] = []

    for row in candidate_rows:
        metrics = CandidateMetrics.from_dict(row)
        level_evals: dict[str, dict[str, Any]] = {}
        best_level_name = ""
        best_level_idx = -1
        for idx, profile in enumerate(profiles):
            level_name = level_names[idx]
            profile_eval = evaluate_profile(metrics, profile)
            level_evals[level_name] = profile_eval
            if profile_eval["passed"]:
                pass_counts[level_name] += 1
                best_level_idx = idx
                best_level_name = level_name

        if best_level_idx >= 0:
            best_level_counts[best_level_name] += 1
        else:
            unreached_count += 1

        next_level_idx = min(best_level_idx + 1, len(level_names) - 1)
        next_level_name = level_names[next_level_idx]
        next_level_eval = level_evals[next_level_name]
        if best_level_idx == len(level_names) - 1 and next_level_eval["passed"]:
            primary_blocker = ""
            secondary_blocker = ""
        else:
            sorted_fail_dims = _sorted_fail_dims(next_level_eval)
            primary_blocker = sorted_fail_dims[0] if sorted_fail_dims else ""
            secondary_blocker = sorted_fail_dims[1] if len(sorted_fail_dims) > 1 else ""
            transition = (
                f"{'none' if best_level_idx < 0 else level_names[best_level_idx]}->{next_level_name}"
            )
            histogram = blocker_histogram[transition]
            for dim in sorted_fail_dims:
                histogram[dim] = int(histogram.get(dim, 0)) + 1

        output_row = {
            "policy_id": metrics.policy_id,
            "best_level_reached": best_level_name,
            "primary_blocker": primary_blocker,
            "secondary_blocker": secondary_blocker,
            "business_return": float(metrics.business_return),
            "cost_return": float(metrics.cost_return),
            "mean_violation": float(metrics.mean_violation),
            "final_critical_compromised_hosts": float(
                metrics.final_critical_compromised_hosts
            ),
            "high_disruption_action_rate": float(metrics.high_disruption_action_rate),
        }
        for level_name in level_names:
            output_row[f"margin_{level_name}"] = float(
                level_evals[level_name]["strict_margin"]
            )
        candidate_output_rows.append(output_row)

    summary = {
        "profile_name": profile_name,
        "candidate_count": len(candidate_rows),
        "best_level_reached_counts": best_level_counts,
        "pass_counts_by_level": pass_counts,
        "unreached_count": unreached_count,
        "blocker_histogram": blocker_histogram,
        "thresholds": {
            "d_business": float(thresholds["d_business"]),
            "d_cost": float(thresholds["d_cost"]),
            "high_disruption_max": float(high_disruption_max),
        },
        "levels": levels,
    }

    summary_path = run_dir / "strict_level_summary.json"
    blockers_path = run_dir / "strict_level_blockers.json"
    candidates_path = run_dir / "strict_level_candidates.csv"
    save_json(summary_path, summary)
    save_json(
        blockers_path,
        {
            "candidate_count": len(candidate_rows),
            "best_level_reached_counts": best_level_counts,
            "unreached_count": unreached_count,
            "blocker_histogram": blocker_histogram,
        },
    )
    fieldnames = list(candidate_output_rows[0].keys()) if candidate_output_rows else [
        "policy_id",
        "best_level_reached",
        "primary_blocker",
        "secondary_blocker",
    ]
    with candidates_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in candidate_output_rows:
            writer.writerow(row)

    return {
        "run_dir": str(run_dir.resolve()),
        "summary_path": str(summary_path.resolve()),
        "blockers_path": str(blockers_path.resolve()),
        "candidates_path": str(candidates_path.resolve()),
    }


def run_strict_level_diagnostics(
    config: StrictLevelDiagnosticsConfig,
    *,
    config_anchor: str | Path | None = None,
) -> dict[str, str]:
    if not config.candidate_cache_path:
        raise ValueError("candidate_cache_path must be provided")
    if not config.thresholds_path:
        raise ValueError("thresholds_path must be provided")
    anchor = Path(config_anchor).resolve() if config_anchor is not None else Path.cwd()
    candidate_cache_path = _resolve_path(anchor, config.candidate_cache_path)
    thresholds_path = _resolve_path(anchor, config.thresholds_path)
    output_root = _resolve_path(anchor, config.output_dir)
    candidate_rows = load_candidate_cache(candidate_cache_path)
    thresholds = _load_thresholds(thresholds_path)
    run_label = config.run_label or candidate_cache_path.parent.name
    return run_strict_level_diagnostics_rows(
        candidate_rows,
        thresholds=thresholds,
        output_root=output_root,
        run_label=run_label,
        profile_name=config.profile_name,
        high_disruption_max=float(config.high_disruption_max),
        levels=list(config.levels),
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run offline strict-level diagnostics from a candidate semantics cache."
    )
    parser.add_argument(
        "--config",
        default=str(DEFAULT_STRICT_LEVEL_DIAGNOSTICS_CONFIG),
    )
    parser.add_argument("--candidate-cache-path", default=None)
    parser.add_argument("--thresholds-path", default=None)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--run-label", default=None)
    args = parser.parse_args()

    config = load_strict_level_diagnostics_config(args.config)
    if args.candidate_cache_path is not None:
        config.candidate_cache_path = args.candidate_cache_path
    if args.thresholds_path is not None:
        config.thresholds_path = args.thresholds_path
    if args.output_dir is not None:
        config.output_dir = args.output_dir
    if args.run_label is not None:
        config.run_label = args.run_label
    outputs = run_strict_level_diagnostics(config, config_anchor=args.config)
    print(outputs["summary_path"])


if __name__ == "__main__":
    main()
