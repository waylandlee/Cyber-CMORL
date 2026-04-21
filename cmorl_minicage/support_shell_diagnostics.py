from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from cmorl_minicage.config import (
    DEFAULT_SUPPORT_SHELL_DIAGNOSTICS_CONFIG,
    SupportShellDiagnosticsConfig,
    load_support_shell_diagnostics_config,
)
from cmorl_minicage.deployability import (
    CandidateMetrics,
    build_support_threshold_profile,
    build_threshold_profile,
    evaluate_profile,
    evaluate_support_profile,
    support_shell_thresholds,
)
from cmorl_minicage.evaluate_constraints import _load_thresholds
from cmorl_minicage.utils import save_json

SHELL_ORDER = ("S0", "S1", "S2", "STRICT")


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


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_candidate_cache(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                rows.append(json.loads(stripped))
    return rows


def _resolve_inputs(
    config: SupportShellDiagnosticsConfig,
    *,
    config_anchor: str | Path | None,
) -> tuple[Path | None, Path, Path, Path, str]:
    anchor = Path(config_anchor).resolve() if config_anchor is not None else Path.cwd()
    assignment_summary_path = None
    candidate_cache_path = config.candidate_cache_path
    thresholds_path = config.thresholds_path
    run_label = config.run_label
    if config.assignment_summary_path:
        assignment_summary_path = _resolve_path(anchor, config.assignment_summary_path)
        summary = _load_json(assignment_summary_path)
        if not candidate_cache_path:
            candidate_cache_path = str(summary["candidate_semantics_path"])
        if not thresholds_path:
            thresholds_path = str(summary["thresholds_path"])
        if not run_label:
            run_label = Path(str(summary["output_dir"])).name
    if not candidate_cache_path:
        raise ValueError("candidate_cache_path must be provided directly or via assignment_summary_path")
    if not thresholds_path:
        raise ValueError("thresholds_path must be provided directly or via assignment_summary_path")
    output_root = _resolve_path(anchor, config.output_dir)
    return (
        assignment_summary_path,
        _resolve_path(anchor, candidate_cache_path),
        _resolve_path(anchor, thresholds_path),
        output_root,
        run_label or Path(candidate_cache_path).resolve().parent.name,
    )


def run_support_shell_diagnostics(
    config: SupportShellDiagnosticsConfig,
    *,
    config_anchor: str | Path | None = None,
) -> dict[str, str]:
    (
        assignment_summary_path,
        candidate_cache_path,
        thresholds_path,
        output_root,
        run_label,
    ) = _resolve_inputs(config, config_anchor=config_anchor)
    candidate_rows = _load_candidate_cache(candidate_cache_path)
    thresholds = _load_thresholds(thresholds_path)
    shell_thresholds = support_shell_thresholds(candidate_rows)
    strict_profile = build_threshold_profile(
        name=f"{config.profile_name}:STRICT",
        thresholds=thresholds,
        mean_violation_max=float(config.strict_mean_violation_max),
        final_critical_max=float(config.strict_final_critical_max),
        high_disruption_max=float(config.strict_high_disruption_max),
    )
    run_dir = output_root / run_label
    run_dir.mkdir(parents=True, exist_ok=True)

    pass_counts = {name: 0 for name in SHELL_ORDER}
    best_shell_counts = {name: 0 for name in SHELL_ORDER}
    blocker_histogram = {
        "none->S0": {},
        "S0->S1": {},
        "S1->S2": {},
        "S2->STRICT": {},
    }
    candidate_output_rows: list[dict[str, Any]] = []

    for row in candidate_rows:
        metrics = CandidateMetrics.from_dict(row)
        shell_evals: dict[str, dict[str, Any]] = {}
        for shell_name in ("S0", "S1", "S2"):
            shell_profile = build_support_threshold_profile(
                name=f"{config.profile_name}:{shell_name}",
                business_min=float(shell_thresholds[shell_name]["business_min"]),
                cost_min=float(shell_thresholds[shell_name]["cost_min"]),
                mean_violation_max=float(shell_thresholds[shell_name]["mean_violation_max"]),
                high_disruption_max=float(shell_thresholds[shell_name]["high_disruption_max"]),
            )
            shell_evals[shell_name] = evaluate_support_profile(metrics, shell_profile)
            if shell_evals[shell_name]["passed"]:
                pass_counts[shell_name] += 1
        strict_eval = evaluate_profile(metrics, strict_profile)
        shell_evals["STRICT"] = strict_eval
        if strict_eval["passed"]:
            pass_counts["STRICT"] += 1

        passed_shells = [name for name in SHELL_ORDER if bool(shell_evals[name]["passed"])]
        best_shell = passed_shells[-1] if passed_shells else ""
        if best_shell:
            best_shell_counts[best_shell] += 1

        if not best_shell:
            transition = "none->S0"
            next_shell = "S0"
        elif best_shell == "S0":
            transition = "S0->S1"
            next_shell = "S1"
        elif best_shell == "S1":
            transition = "S1->S2"
            next_shell = "S2"
        elif best_shell == "S2":
            transition = "S2->STRICT"
            next_shell = "STRICT"
        else:
            transition = ""
            next_shell = ""

        if next_shell:
            next_eval = shell_evals[next_shell]
            sorted_fail_dims = sorted(
                list(next_eval.get("fail_dims", [])),
                key=lambda dim: (
                    float(next_eval.get("normalized_margins", {}).get(dim, 0.0)),
                    dim,
                ),
            )
            primary_blocker = sorted_fail_dims[0] if sorted_fail_dims else ""
            secondary_blocker = sorted_fail_dims[1] if len(sorted_fail_dims) > 1 else ""
            for dim in sorted_fail_dims:
                blocker_histogram[transition][dim] = int(
                    blocker_histogram[transition].get(dim, 0)
                ) + 1
        else:
            primary_blocker = ""
            secondary_blocker = ""

        output_row = {
            "policy_id": metrics.policy_id,
            "best_shell_reached": best_shell,
            "primary_blocker": primary_blocker,
            "secondary_blocker": secondary_blocker,
            "business_return": float(metrics.business_return),
            "cost_return": float(metrics.cost_return),
            "mean_violation": float(metrics.mean_violation),
            "high_disruption_action_rate": float(metrics.high_disruption_action_rate),
            "final_critical_compromised_hosts": float(
                metrics.final_critical_compromised_hosts
            ),
            "strict_margin": float(row.get("strict_margin", strict_eval["strict_margin"])),
        }
        for shell_name in ("S0", "S1", "S2"):
            output_row[f"passed_{shell_name}"] = bool(shell_evals[shell_name]["passed"])
            output_row[f"margin_{shell_name}"] = float(
                shell_evals[shell_name]["support_margin"]
            )
        output_row["passed_STRICT"] = bool(strict_eval["passed"])
        output_row["margin_STRICT"] = float(strict_eval["strict_margin"])
        candidate_output_rows.append(output_row)

    recommended_repair_shell = ""
    for shell_name in ("S2", "S1", "S0"):
        if int(pass_counts[shell_name]) > 0:
            recommended_repair_shell = shell_name
            break

    summary = {
        "assignment_summary_path": (
            str(assignment_summary_path.resolve()) if assignment_summary_path is not None else ""
        ),
        "candidate_cache_path": str(candidate_cache_path.resolve()),
        "thresholds_path": str(thresholds_path.resolve()),
        "profile_name": config.profile_name,
        "candidate_count": len(candidate_rows),
        "shell_thresholds": shell_thresholds,
        "strict_profile": strict_profile.to_dict(),
        "pass_counts_by_shell": pass_counts,
        "best_shell_reached_counts": best_shell_counts,
        "blocker_histogram": blocker_histogram,
        "recommended_repair_shell": recommended_repair_shell,
        "s0_nonempty": bool(pass_counts["S0"] > 0),
        "shell_order_valid": bool(
            pass_counts["S0"] >= pass_counts["S1"] >= pass_counts["S2"] >= pass_counts["STRICT"]
        ),
    }

    summary_path = run_dir / "support_shell_summary.json"
    candidates_path = run_dir / "support_shell_candidates.csv"
    blockers_path = run_dir / "support_shell_blockers.json"
    save_json(summary_path, summary)
    save_json(
        blockers_path,
        {
            "candidate_count": len(candidate_rows),
            "pass_counts_by_shell": pass_counts,
            "best_shell_reached_counts": best_shell_counts,
            "recommended_repair_shell": recommended_repair_shell,
            "blocker_histogram": blocker_histogram,
        },
    )
    with candidates_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(candidate_output_rows[0].keys()))
        writer.writeheader()
        for row in candidate_output_rows:
            writer.writerow(row)
    return {
        "run_dir": str(run_dir.resolve()),
        "summary_path": str(summary_path.resolve()),
        "candidates_path": str(candidates_path.resolve()),
        "blockers_path": str(blockers_path.resolve()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run support-aware shell diagnostics on a replay candidate cache."
    )
    parser.add_argument("--config", default=str(DEFAULT_SUPPORT_SHELL_DIAGNOSTICS_CONFIG))
    parser.add_argument("--assignment-summary-path", default=None)
    parser.add_argument("--candidate-cache-path", default=None)
    parser.add_argument("--thresholds-path", default=None)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--run-label", default=None)
    args = parser.parse_args()

    config = load_support_shell_diagnostics_config(args.config)
    if args.assignment_summary_path is not None:
        config.assignment_summary_path = args.assignment_summary_path
    if args.candidate_cache_path is not None:
        config.candidate_cache_path = args.candidate_cache_path
    if args.thresholds_path is not None:
        config.thresholds_path = args.thresholds_path
    if args.output_dir is not None:
        config.output_dir = args.output_dir
    if args.run_label is not None:
        config.run_label = args.run_label
    outputs = run_support_shell_diagnostics(config, config_anchor=args.config)
    print(outputs["summary_path"])


if __name__ == "__main__":
    main()
