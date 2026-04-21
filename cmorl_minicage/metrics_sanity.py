from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import numpy as np

from cmorl_minicage.buffer import load_policy_buffer
from cmorl_minicage.config import (
    DEFAULT_METRICS_SANITY_CONFIG,
    MetricsSanityConfig,
    load_metrics_sanity_config,
)
from cmorl_minicage.evaluate_constraints import (
    _evaluate_actor_critic_record_detailed,
    _load_thresholds,
)
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
    config: MetricsSanityConfig,
    *,
    config_anchor: str | Path | None,
) -> tuple[Path | None, Path, Path, Path, Path, str]:
    anchor = Path(config_anchor).resolve() if config_anchor is not None else Path.cwd()
    assignment_summary_path = None
    buffer_path = config.buffer_path
    candidate_cache_path = config.candidate_cache_path
    thresholds_path = config.thresholds_path
    run_label = config.run_label
    if config.assignment_summary_path:
        assignment_summary_path = _resolve_path(anchor, config.assignment_summary_path)
        summary = _load_json(assignment_summary_path)
        if not candidate_cache_path:
            candidate_cache_path = str(summary["candidate_semantics_path"])
        if not buffer_path:
            buffer_path = str(summary["buffer_path"])
        if not thresholds_path:
            thresholds_path = str(summary["thresholds_path"])
        if not run_label:
            run_label = Path(str(summary["output_dir"])).name
    if not candidate_cache_path:
        raise ValueError("candidate_cache_path must be provided directly or via assignment_summary_path")
    if not buffer_path:
        raise ValueError("buffer_path must be provided directly or via assignment_summary_path")
    if not thresholds_path:
        raise ValueError("thresholds_path must be provided directly or via assignment_summary_path")
    output_root = _resolve_path(anchor, config.output_dir)
    return (
        assignment_summary_path,
        _resolve_path(anchor, candidate_cache_path),
        _resolve_path(anchor, buffer_path),
        _resolve_path(anchor, thresholds_path),
        output_root,
        run_label or Path(candidate_cache_path).resolve().parent.name,
    )


def _normalized_mean_violation(
    business_violation_values: list[float],
    cost_violation_values: list[float],
    thresholds: dict[str, float],
) -> float:
    business_scale = max(abs(float(thresholds["d_business"])), 1.0)
    cost_scale = max(abs(float(thresholds["d_cost"])), 1.0)
    normalized = [
        (float(bv) / business_scale) + (float(cv) / cost_scale)
        for bv, cv in zip(business_violation_values, cost_violation_values)
    ]
    return float(np.mean(normalized)) if normalized else 0.0


def _candidate_audit_rows(
    *,
    candidate_rows: list[dict[str, Any]],
    buffer_path: Path,
    thresholds: dict[str, float],
    eval_episodes: int,
) -> list[dict[str, Any]]:
    payload = load_policy_buffer(buffer_path)
    metadata = dict(payload.get("metadata", {}))
    records = list(payload.get("records", []))
    record_by_id = {str(record["policy_id"]): record for record in records}
    audit_rows: list[dict[str, Any]] = []
    for candidate in candidate_rows:
        policy_id = str(candidate["policy_id"])
        if policy_id not in record_by_id:
            raise KeyError(f"Missing record for policy_id={policy_id} in {buffer_path}")
        record = record_by_id[policy_id]
        raw_checkpoint_path = record.get("checkpoint_path")
        checkpoint_path = None
        if raw_checkpoint_path:
            checkpoint_path = _resolve_path(buffer_path, raw_checkpoint_path)
        baseline_kind = record.get("notes", {}).get("baseline_kind")
        detailed = _evaluate_actor_critic_record_detailed(
            checkpoint_path,
            metadata,
            thresholds,
            eval_episodes=int(eval_episodes),
            baseline_kind=baseline_kind,
        )
        audit_details = dict(detailed.get("audit_details", {}))
        business_threshold = float(thresholds["d_business"])
        cost_threshold = float(thresholds["d_cost"])
        business_return = float(detailed["business_return"])
        cost_return = float(detailed["cost_return"])
        business_margin = float(business_return - business_threshold)
        cost_margin = float(cost_return - cost_threshold)
        recomputed_mean_violation = float(detailed["mean_violation"])
        recomputed_high_disruption = float(detailed["high_disruption_action_rate"])
        row = {
            "policy_id": policy_id,
            "checkpoint_path": str(checkpoint_path) if checkpoint_path is not None else "",
            "cached_mean_violation": float(candidate["mean_violation"]),
            "recomputed_mean_violation": recomputed_mean_violation,
            "mean_violation_abs_diff": abs(
                float(candidate["mean_violation"]) - recomputed_mean_violation
            ),
            "normalized_mean_violation": _normalized_mean_violation(
                list(audit_details.get("business_violation_values", [])),
                list(audit_details.get("cost_violation_values", [])),
                thresholds,
            ),
            "cached_high_disruption_action_rate": float(
                candidate["high_disruption_action_rate"]
            ),
            "recomputed_high_disruption_action_rate": recomputed_high_disruption,
            "high_disruption_abs_diff": abs(
                float(candidate["high_disruption_action_rate"]) - recomputed_high_disruption
            ),
            "business_return": business_return,
            "business_threshold": business_threshold,
            "business_margin": business_margin,
            "business_sign_ok": bool(
                (business_margin >= 0.0) == (business_return >= business_threshold)
            ),
            "cost_return": cost_return,
            "cost_threshold": cost_threshold,
            "cost_margin": cost_margin,
            "cost_sign_ok": bool((cost_margin >= 0.0) == (cost_return >= cost_threshold)),
            "cached_final_critical_compromised_hosts": float(
                candidate["final_critical_compromised_hosts"]
            ),
            "recomputed_final_critical_compromised_hosts": float(
                detailed["final_critical_compromised_hosts"]
            ),
            "feasible_rate": float(detailed["feasible_rate"]),
            "semantic_total_high_disruption_action_count": float(
                audit_details.get("semantic_totals_sum", {}).get(
                    "high_disruption_action_count", 0.0
                )
            ),
            "semantic_total_action_count": float(
                audit_details.get("semantic_totals_sum", {}).get("total_action_count", 0.0)
            ),
        }
        audit_rows.append(row)
    return audit_rows


def _markdown_report(summary: dict[str, Any]) -> str:
    audits = dict(summary["audits"])
    continue_flag = bool(summary["continue_to_next_phase"])
    status = "PASS" if continue_flag else "FAIL"
    return "\n".join(
        [
            "# Metrics Sanity Check",
            "",
            f"- Verdict: `{status}`",
            f"- Candidate count: `{summary['candidate_count']}`",
            f"- Continue to Phase 2: `{continue_flag}`",
            "",
            "## Checks",
            "",
            (
                "- `mean_violation`: "
                f"`passed={audits['mean_violation']['passed']}`; "
                f"`max_abs_diff={audits['mean_violation']['max_abs_diff']:.8f}`"
            ),
            (
                "- `high_disruption_action_rate`: "
                f"`passed={audits['high_disruption_action_rate']['passed']}`; "
                f"`max_abs_diff={audits['high_disruption_action_rate']['max_abs_diff']:.8f}`"
            ),
            (
                "- `business/cost margin sign`: "
                f"`passed={audits['business_cost_sign']['passed']}`; "
                f"`sign_mismatch_detected={audits['business_cost_sign']['sign_mismatch_detected']}`"
            ),
            "",
            "## Notes",
            "",
            "- `normalized_mean_violation` is a reporting-only audit metric.",
            "- It uses per-episode `(business_shortfall / |d_business|) + (cost_shortfall / |d_cost|)` and does not replace the main `mean_violation` definition.",
        ]
    )


def run_metrics_sanity(
    config: MetricsSanityConfig,
    *,
    config_anchor: str | Path | None = None,
) -> dict[str, str]:
    (
        assignment_summary_path,
        candidate_cache_path,
        buffer_path,
        thresholds_path,
        output_root,
        run_label,
    ) = _resolve_inputs(config, config_anchor=config_anchor)
    candidate_rows = _load_candidate_cache(candidate_cache_path)
    thresholds = _load_thresholds(thresholds_path)
    run_dir = output_root / run_label
    run_dir.mkdir(parents=True, exist_ok=True)

    audit_rows = _candidate_audit_rows(
        candidate_rows=candidate_rows,
        buffer_path=buffer_path,
        thresholds=thresholds,
        eval_episodes=int(config.eval_episodes),
    )
    max_mean_diff = max(float(row["mean_violation_abs_diff"]) for row in audit_rows)
    max_high_diff = max(float(row["high_disruption_abs_diff"]) for row in audit_rows)
    sign_mismatch_detected = any(
        (not bool(row["business_sign_ok"])) or (not bool(row["cost_sign_ok"]))
        for row in audit_rows
    )
    summary = {
        "assignment_summary_path": (
            str(assignment_summary_path.resolve()) if assignment_summary_path is not None else ""
        ),
        "candidate_cache_path": str(candidate_cache_path.resolve()),
        "buffer_path": str(buffer_path.resolve()),
        "thresholds_path": str(thresholds_path.resolve()),
        "candidate_count": len(audit_rows),
        "audits": {
            "mean_violation": {
                "passed": bool(max_mean_diff <= 1e-6),
                "max_abs_diff": float(max_mean_diff),
                "mean_abs_diff": float(
                    np.mean([float(row["mean_violation_abs_diff"]) for row in audit_rows])
                ),
                "normalized_mean_violation_mean": float(
                    np.mean([float(row["normalized_mean_violation"]) for row in audit_rows])
                ),
            },
            "high_disruption_action_rate": {
                "passed": bool(max_high_diff <= 1e-6),
                "max_abs_diff": float(max_high_diff),
                "mean_abs_diff": float(
                    np.mean([float(row["high_disruption_abs_diff"]) for row in audit_rows])
                ),
            },
            "business_cost_sign": {
                "passed": bool(not sign_mismatch_detected),
                "sign_mismatch_detected": bool(sign_mismatch_detected),
                "business_threshold_direction": "lower_bound",
                "cost_threshold_direction": "lower_bound",
            },
        },
    }
    summary["continue_to_next_phase"] = bool(
        summary["audits"]["mean_violation"]["passed"]
        and summary["audits"]["high_disruption_action_rate"]["passed"]
        and summary["audits"]["business_cost_sign"]["passed"]
    )

    candidates_path = run_dir / "metrics_sanity_candidates.csv"
    summary_path = run_dir / "metrics_sanity_summary.json"
    markdown_path = run_dir / "metrics_sanity.md"
    with candidates_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(audit_rows[0].keys()))
        writer.writeheader()
        for row in audit_rows:
            writer.writerow(row)
    save_json(summary_path, summary)
    markdown_path.write_text(_markdown_report(summary), encoding="utf-8")
    return {
        "run_dir": str(run_dir.resolve()),
        "summary_path": str(summary_path.resolve()),
        "candidates_path": str(candidates_path.resolve()),
        "markdown_path": str(markdown_path.resolve()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit replay metrics and semantics consistency on a fixed candidate cache."
    )
    parser.add_argument("--config", default=str(DEFAULT_METRICS_SANITY_CONFIG))
    parser.add_argument("--assignment-summary-path", default=None)
    parser.add_argument("--candidate-cache-path", default=None)
    parser.add_argument("--buffer-path", default=None)
    parser.add_argument("--thresholds-path", default=None)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--run-label", default=None)
    args = parser.parse_args()

    config = load_metrics_sanity_config(args.config)
    if args.assignment_summary_path is not None:
        config.assignment_summary_path = args.assignment_summary_path
    if args.candidate_cache_path is not None:
        config.candidate_cache_path = args.candidate_cache_path
    if args.buffer_path is not None:
        config.buffer_path = args.buffer_path
    if args.thresholds_path is not None:
        config.thresholds_path = args.thresholds_path
    if args.output_dir is not None:
        config.output_dir = args.output_dir
    if args.run_label is not None:
        config.run_label = args.run_label
    outputs = run_metrics_sanity(config, config_anchor=args.config)
    print(outputs["summary_path"])


if __name__ == "__main__":
    main()
