from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from cmorl_minicage.buffer import load_policy_buffer
from cmorl_minicage.shield import action_family_from_name
from cmorl_minicage.utils import ensure_dir, load_json, save_json

from .export_candidate_semantic_audit import (
    DEFAULT_CRITICAL_HOST,
    DEFAULT_CRITICAL_PATH_HOSTS,
    export_candidate_semantic_audit,
)
from .export_figure2_attack_defense_trace import (
    Figure2ReplayCandidate,
    export_candidate_trace,
)
from .export_figure2_trace_analysis import export_figure2_trace_analysis
from .export_semantic_risk_summary import build_method_comparison_semantic_summary
from .topology import topology_snapshot


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = (
    REPO_ROOT / "cmorl_cyborg" / "outputs" / "paper_4obj" / "rq3_symmetric"
)
DEFAULT_PAPER_TABLE_PATH = REPO_ROOT / "paper" / "table" / "rq3_semantic_comparison_4obj.tex"
DEFAULT_PAPER_APPENDIX_TABLE_PATH = (
    REPO_ROOT / "paper" / "table" / "rq3_semantic_full_audit_4obj.tex"
)
DEFAULT_METHODS = ("ours_stage2_v2_4", "no_constraint_stage2_4obj")
DEFAULT_SEEDS = (7, 11, 19)
DEFAULT_EVAL_EPISODES = 20

METHOD_DISPLAY = {
    "ours_stage2_v2_4": "Constraint-Aware Stage-2",
    "no_constraint_stage2_4obj": "Unconstrained Stage-2",
}
PHASE_KEYS = ("foothold", "precritical", "critical_present")
PHASE_DISPLAY = {
    "foothold": "Foothold",
    "precritical": "Pre-Critical",
    "critical_present": "Critical-Present",
}
ACTION_FAMILY_ORDER = ("restore", "decoy", "analyse", "remove", "sleep", "other")
TARGET_CATEGORY_ORDER = (
    "critical_path_host",
    "compromised_enterprise_or_operational_host",
    "user_host",
    "non_compromised_host",
    "no_target_or_other",
)
TRACE_REQUIRED_FILES = (
    "trace_manifest.json",
    "episode_summaries.json",
    "topology_snapshot.json",
)
AUDIT_REQUIRED_FILES = (
    "risk_tier_summary.json",
    "critical_casebook.md",
    "questionable_defense_actions.csv",
    "critical_path_heatmap.png",
)
TRACE_ANALYSIS_REQUIRED_FILES = (
    "timeline_table.csv",
    "timeline_table.md",
    "host_level_summary.csv",
    "host_attack_defense_heatmap.png",
)


@dataclass(frozen=True)
class AuditArtifact:
    method_name: str
    display_name: str
    seed: int
    policy_id: str
    trace_dir: Path
    audit_dir: Path
    risk_summary_path: Path
    trace_analysis_dir: Path


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _tight_summary_path(method_name: str, seed: int) -> Path:
    return (
        REPO_ROOT
        / "cmorl_cyborg"
        / "outputs"
        / "fair_compare_eval"
        / "tight_feasible_set_summary"
        / method_name
        / f"seed_{seed:04d}.json"
    )


def _table_b_summary_path() -> Path:
    return (
        REPO_ROOT
        / "cmorl_cyborg"
        / "outputs"
        / "paper_4obj"
        / "table_b"
        / "table_b_summary.json"
    )


def _table_b_record(method_name: str, seed: int) -> dict[str, Any]:
    summary = _load_json(_table_b_summary_path())
    for record in summary.get("per_run_records", []):
        if str(record.get("method_name")) == method_name and int(record.get("seed")) == int(seed):
            return record
    raise KeyError(f"Missing table_b record for method={method_name} seed={seed}")


def _buffer_record_lookup(buffer_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for record in list(buffer_payload.get("records", [])) + list(buffer_payload.get("pareto_front", [])):
        policy_id = str(record.get("policy_id", ""))
        if policy_id and policy_id not in lookup:
            lookup[policy_id] = record
    return lookup


def _trace_rows(trace_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for episode_path in sorted(trace_dir.glob("episode_*.jsonl")):
        with episode_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                rows.append(json.loads(line))
    return rows


def _manifest(trace_dir: Path) -> dict[str, Any]:
    return _load_json(trace_dir / "trace_manifest.json")


def _compromised_hosts(state: dict[str, Any]) -> set[str]:
    return {str(host) for host in state.get("compromised_hosts", [])}


def _critical_present(row: dict[str, Any]) -> bool:
    semantic = row.get("semantic_info", {}) or {}
    if "critical_present" in semantic:
        return bool(float(semantic.get("critical_present", 0.0)))
    before_hosts = set(row.get("state_before", {}).get("critical_compromised_hosts", []))
    after_hosts = set(row.get("state_after", {}).get("critical_compromised_hosts", []))
    return bool(before_hosts or after_hosts)


def _enterprise_foothold_present(row: dict[str, Any]) -> bool:
    semantic = row.get("semantic_info", {}) or {}
    if "enterprise_foothold_present" in semantic:
        return bool(float(semantic.get("enterprise_foothold_present", 0.0)))
    before_hosts = set(row.get("state_before", {}).get("enterprise_compromised_hosts", []))
    after_hosts = set(row.get("state_after", {}).get("enterprise_compromised_hosts", []))
    return bool(before_hosts or after_hosts)


def _critical_hit_event(row: dict[str, Any]) -> bool:
    semantic = row.get("semantic_info", {}) or {}
    if "critical_hit_event" in semantic:
        return bool(float(semantic.get("critical_hit_event", 0.0)))
    before_hosts = set(row.get("state_before", {}).get("critical_compromised_hosts", []))
    after_hosts = set(row.get("state_after", {}).get("critical_compromised_hosts", []))
    return bool(after_hosts - before_hosts)


def _phase_name(row: dict[str, Any]) -> str:
    if _critical_present(row):
        return "critical_present"
    if _enterprise_foothold_present(row):
        return "precritical"
    return "foothold"


def _host_subnet(snapshot: dict[str, Any], hostname: str | None) -> str:
    if not hostname:
        return ""
    return str(snapshot["hosts"].get(str(hostname), {}).get("subnet") or "")


def _host_role_group(snapshot: dict[str, Any], hostname: str | None) -> str:
    if not hostname:
        return ""
    return str(snapshot["hosts"].get(str(hostname), {}).get("role_group") or "")


def _blue_target_hostname(row: dict[str, Any]) -> str:
    return str(row.get("blue_action", {}).get("target_hostname") or "")


def _blue_target_subnet(row: dict[str, Any], snapshot: dict[str, Any]) -> str:
    action = row.get("blue_action", {}) or {}
    target_subnet = str(action.get("target_subnet") or "")
    if target_subnet:
        return target_subnet
    return _host_subnet(snapshot, action.get("target_hostname"))


def _target_focus_category(
    row: dict[str, Any],
    *,
    snapshot: dict[str, Any],
    critical_path_hosts: set[str],
) -> str:
    target_hostname = _blue_target_hostname(row)
    target_subnet = _blue_target_subnet(row, snapshot)
    if target_hostname in critical_path_hosts:
        return "critical_path_host"
    compromised_before = _compromised_hosts(row.get("state_before", {}))
    if (
        target_hostname
        and target_hostname in compromised_before
        and target_subnet in {"Enterprise", "Operational"}
    ):
        return "compromised_enterprise_or_operational_host"
    if target_subnet == "User":
        return "user_host"
    if target_hostname and target_hostname not in compromised_before:
        return "non_compromised_host"
    return "no_target_or_other"


def _first_step_matching(rows: list[dict[str, Any]], predicate) -> int | None:
    for row in rows:
        if predicate(row):
            return int(row["step_idx"])
    return None


def _run_groups(rows: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    grouped: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row.get("episode_id", "")), int(row.get("env_idx", 0)))].append(row)
    return [sorted(group, key=lambda item: int(item["step_idx"])) for _, group in sorted(grouped.items())]


def _mode_int(values: list[int | None]) -> int | None:
    filtered = [value for value in values if value is not None]
    if not filtered:
        return None
    counts = Counter(filtered)
    return counts.most_common(1)[0][0]


def _mode_str(values: list[str]) -> str:
    filtered = [value for value in values if value]
    if not filtered:
        return ""
    counts = Counter(filtered)
    return counts.most_common(1)[0][0]


def _close_enough(left: float, right: float, *, tol: float = 1e-9) -> bool:
    return abs(float(left) - float(right)) <= tol


def _first_enterprise_host(
    rows: list[dict[str, Any]],
    *,
    start_step: int | None,
    snapshot: dict[str, Any],
) -> str:
    if start_step is None:
        return ""
    for row in rows:
        if int(row["step_idx"]) < start_step:
            continue
        newly = [str(host) for host in row.get("newly_compromised_hosts", [])]
        enterprise_new = [
            host for host in newly if _host_subnet(snapshot, host) == "Enterprise"
        ]
        if enterprise_new:
            return enterprise_new[0]
        for field in ("state_after", "state_before"):
            hosts = [
                str(host)
                for host in row.get(field, {}).get("enterprise_compromised_hosts", [])
            ]
            if hosts:
                return hosts[0]
    return ""


def _response_target_is_relevant(
    row: dict[str, Any],
    critical_path_hosts: set[str],
) -> bool:
    return _blue_target_hostname(row) in critical_path_hosts


def _outcome_label(risk_summary: dict[str, Any]) -> str:
    if float(risk_summary.get("ever_critical_breach_rate", 0.0)) == 0.0:
        return "Contained before critical breach"
    if float(risk_summary.get("persistent_critical_breach_rate", 0.0)) > 0.5:
        return "Persistent critical breach common"
    return "Critical breach observed"


def _build_pair_summary(
    artifact: AuditArtifact,
    *,
    snapshot: dict[str, Any],
    critical_path_hosts: set[str],
) -> dict[str, Any]:
    rows = _trace_rows(artifact.trace_dir)
    risk_summary = _load_json(artifact.risk_summary_path)
    per_run = _run_groups(rows)

    enterprise_steps: list[int | None] = []
    response_steps: list[int | None] = []
    critical_steps: list[int | None] = []
    response_actions: list[str] = []
    response_targets: list[str] = []
    enterprise_hosts: list[str] = []

    for run_rows in per_run:
        enterprise_step = _first_step_matching(run_rows, _enterprise_foothold_present)
        enterprise_steps.append(enterprise_step)
        critical_step = _first_step_matching(run_rows, _critical_hit_event)
        critical_steps.append(critical_step)

        response_step = None
        response_row = None
        if enterprise_step is not None:
            for row in run_rows:
                step_idx = int(row["step_idx"])
                if step_idx <= enterprise_step:
                    continue
                if _response_target_is_relevant(row, critical_path_hosts):
                    response_step = step_idx
                    response_row = row
                    break
        response_steps.append(response_step)
        if response_row is not None:
            response_actions.append(str(response_row.get("blue_action", {}).get("name", "")))
            response_targets.append(_blue_target_hostname(response_row))

        enterprise_hosts.append(
            _first_enterprise_host(
                run_rows,
                start_step=enterprise_step,
                snapshot=snapshot,
            )
        )

    return {
        "method_name": artifact.method_name,
        "display_name": artifact.display_name,
        "seed": artifact.seed,
        "policy_id": artifact.policy_id,
        "trace_dir": str(artifact.trace_dir.resolve()),
        "audit_dir": str(artifact.audit_dir.resolve()),
        "risk_summary_path": str(artifact.risk_summary_path.resolve()),
        "trace_analysis_dir": str(artifact.trace_analysis_dir.resolve()),
        "selected_policy_id": artifact.policy_id,
        "run_count": len(per_run),
        "mode_enterprise_foothold_step": _mode_int(enterprise_steps),
        "mode_response_step": _mode_int(response_steps),
        "mode_first_critical_hit_step": _mode_int(critical_steps),
        "mode_response_action_name": _mode_str(response_actions),
        "mode_response_target": _mode_str(response_targets),
        "mode_enterprise_host": _mode_str(enterprise_hosts),
        "outcome_label": _outcome_label(risk_summary),
        "risk_summary": risk_summary,
    }


def _build_phase_summary(
    artifacts: Iterable[AuditArtifact],
    *,
    snapshot: dict[str, Any],
    critical_path_hosts: set[str],
) -> dict[str, Any]:
    seed_rows: list[dict[str, Any]] = []
    aggregate: dict[str, dict[str, dict[str, float]]] = {}

    for artifact in artifacts:
        rows = _trace_rows(artifact.trace_dir)
        by_phase: dict[str, list[dict[str, Any]]] = {phase: [] for phase in PHASE_KEYS}
        for row in rows:
            by_phase[_phase_name(row)].append(row)

        for phase in PHASE_KEYS:
            phase_rows = by_phase[phase]
            total_steps = len(phase_rows)
            action_counter: Counter[str] = Counter()
            target_counter: Counter[str] = Counter()
            for row in phase_rows:
                action_counter[action_family_from_name(row.get("blue_action", {}).get("name"))] += 1
                target_counter[_target_focus_category(
                    row,
                    snapshot=snapshot,
                    critical_path_hosts=critical_path_hosts,
                )] += 1

            row_payload: dict[str, Any] = {
                "method_name": artifact.method_name,
                "display_name": artifact.display_name,
                "seed": artifact.seed,
                "phase_name": phase,
                "phase_label": PHASE_DISPLAY[phase],
                "total_phase_steps": total_steps,
            }
            for family in ACTION_FAMILY_ORDER:
                row_payload[f"action_rate.{family}"] = (
                    float(action_counter.get(family, 0) / max(total_steps, 1))
                )
            for category in TARGET_CATEGORY_ORDER:
                row_payload[f"target_rate.{category}"] = (
                    float(target_counter.get(category, 0) / max(total_steps, 1))
                )
            seed_rows.append(row_payload)

    for method_name in DEFAULT_METHODS:
        display_name = METHOD_DISPLAY[method_name]
        aggregate[method_name] = {
            "display_name": display_name,
            "phases": {},
        }
        method_rows = [row for row in seed_rows if row["method_name"] == method_name]
        for phase in PHASE_KEYS:
            phase_rows = [row for row in method_rows if row["phase_name"] == phase]
            phase_payload: dict[str, Any] = {
                "phase_label": PHASE_DISPLAY[phase],
                "mean_total_phase_steps": sum(
                    float(row["total_phase_steps"]) for row in phase_rows
                )
                / max(len(phase_rows), 1),
            }
            for family in ACTION_FAMILY_ORDER:
                key = f"action_rate.{family}"
                phase_payload[key] = sum(float(row[key]) for row in phase_rows) / max(
                    len(phase_rows), 1
                )
            for category in TARGET_CATEGORY_ORDER:
                key = f"target_rate.{category}"
                phase_payload[key] = sum(float(row[key]) for row in phase_rows) / max(
                    len(phase_rows), 1
                )
            aggregate[method_name]["phases"][phase] = phase_payload

    return {"seed_rows": seed_rows, "aggregate": aggregate}


def _write_phase_outputs(phase_summary: dict[str, Any], *, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    save_json(output_dir / "phase_comparison.json", phase_summary["aggregate"])
    save_json(output_dir / "phase_comparison_seedwise.json", phase_summary["seed_rows"])

    fieldnames = [
        "method_name",
        "display_name",
        "seed",
        "phase_name",
        "phase_label",
        "total_phase_steps",
    ]
    fieldnames.extend(f"action_rate.{family}" for family in ACTION_FAMILY_ORDER)
    fieldnames.extend(f"target_rate.{category}" for category in TARGET_CATEGORY_ORDER)
    with (output_dir / "phase_comparison_seedwise.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        import csv

        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in phase_summary["seed_rows"]:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def _write_seed_pair_casebook(seed: int, pair_summary: dict[str, Any], *, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "seed": seed,
        "methods": pair_summary,
    }
    save_json(output_dir / f"seed_{seed:04d}_summary.json", payload)

    lines = [f"# RQ3 Paired Semantic Casebook: seed {seed:04d}", ""]
    for method_name in DEFAULT_METHODS:
        summary = pair_summary[method_name]
        risk_summary = summary["risk_summary"]
        lines.extend(
            [
                f"## {summary['display_name']}",
                "",
                f"- `policy_id={summary['policy_id']}`",
                f"- `enterprise_foothold_step={summary['mode_enterprise_foothold_step']}`",
                f"- `response_step={summary['mode_response_step']}`",
                f"- `response_action={summary['mode_response_action_name']}`",
                f"- `response_target={summary['mode_response_target']}`",
                f"- `first_critical_hit_step={summary['mode_first_critical_hit_step']}`",
                f"- `outcome={summary['outcome_label']}`",
                f"- `ever_critical_breach_rate={float(risk_summary.get('ever_critical_breach_rate', 0.0)):.4f}`",
                f"- `persistent_critical_breach_rate={float(risk_summary.get('persistent_critical_breach_rate', 0.0)):.4f}`",
                f"- `precritical_restore_step_rate={float((risk_summary.get('precritical_action_family_step_rates', {}) or {}).get('restore', 0.0)):.4f}`",
                f"- `precritical_decoy_step_rate={float((risk_summary.get('precritical_action_family_step_rates', {}) or {}).get('decoy', 0.0)):.4f}`",
                f"- `precritical_compromised_target_focus_step_rate={float(risk_summary.get('precritical_compromised_target_focus_step_rate', 0.0)):.4f}`",
                f"- Audit dir: `{summary['audit_dir']}`",
                f"- Trace analysis dir: `{summary['trace_analysis_dir']}`",
                "",
            ]
        )
    (output_dir / f"seed_{seed:04d}_paired_casebook.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def _write_policy_alignment(artifacts: Iterable[AuditArtifact], *, output_dir: Path) -> None:
    rows: list[dict[str, Any]] = []
    for artifact in artifacts:
        table_b_record = _table_b_record(artifact.method_name, artifact.seed)
        output_metrics = _load_json(table_b_record["output_path"])
        selected_policy_id = str(output_metrics.get("selected_policy_id") or output_metrics.get("policy_id") or "")
        row = {
            "method_name": artifact.method_name,
            "display_name": artifact.display_name,
            "seed": artifact.seed,
            "table_b_selected_policy_id": selected_policy_id,
            "exported_policy_id": artifact.policy_id,
            "alignment_ok": selected_policy_id == artifact.policy_id,
        }
        rows.append(row)
    save_json(output_dir / "policy_alignment.json", {"rows": rows})


def _collect_artifact_completeness(
    artifacts: Iterable[AuditArtifact],
    *,
    eval_episodes: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for artifact in artifacts:
        trace_checks = {
            name: (artifact.trace_dir / name).exists() for name in TRACE_REQUIRED_FILES
        }
        audit_checks = {
            name: (artifact.audit_dir / name).exists() for name in AUDIT_REQUIRED_FILES
        }
        trace_analysis_checks = {
            name: (artifact.trace_analysis_dir / name).exists()
            for name in TRACE_ANALYSIS_REQUIRED_FILES
        }
        episode_files = sorted(artifact.trace_dir.glob("episode_*.jsonl"))
        row = {
            "method_name": artifact.method_name,
            "display_name": artifact.display_name,
            "seed": artifact.seed,
            "policy_id": artifact.policy_id,
            "trace_dir": str(artifact.trace_dir.resolve()),
            "audit_dir": str(artifact.audit_dir.resolve()),
            "trace_analysis_dir": str(artifact.trace_analysis_dir.resolve()),
            "expected_episode_file_count": int(eval_episodes),
            "episode_file_count": len(episode_files),
            "episode_file_count_ok": len(episode_files) == int(eval_episodes),
            "trace_files": trace_checks,
            "audit_files": audit_checks,
            "trace_analysis_files": trace_analysis_checks,
        }
        row["trace_complete"] = bool(trace_checks) and all(trace_checks.values()) and bool(
            row["episode_file_count_ok"]
        )
        row["audit_complete"] = bool(audit_checks) and all(audit_checks.values())
        row["trace_analysis_complete"] = bool(trace_analysis_checks) and all(
            trace_analysis_checks.values()
        )
        row["all_required_present"] = bool(
            row["trace_complete"] and row["audit_complete"] and row["trace_analysis_complete"]
        )
        rows.append(row)
    return rows


def _write_artifact_completeness(
    artifacts: Iterable[AuditArtifact],
    *,
    output_dir: Path,
    eval_episodes: int,
) -> None:
    rows = _collect_artifact_completeness(artifacts, eval_episodes=eval_episodes)
    save_json(output_dir / "artifact_completeness.json", {"rows": rows})


def _collect_phase_sanity(
    artifacts: Iterable[AuditArtifact],
    phase_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    phase_lookup = {
        (str(row["method_name"]), int(row["seed"]), str(row["phase_name"])): row
        for row in phase_summary.get("seed_rows", [])
    }
    rows: list[dict[str, Any]] = []
    for artifact in artifacts:
        trace_rows = _trace_rows(artifact.trace_dir)
        phase_payload: dict[str, Any] = {}
        total_phase_steps = 0
        all_checks_ok = True
        for phase in PHASE_KEYS:
            row = phase_lookup[(artifact.method_name, int(artifact.seed), phase)]
            phase_steps = int(row.get("total_phase_steps", 0))
            total_phase_steps += phase_steps
            action_rate_sum = sum(
                float(row.get(f"action_rate.{family}", 0.0))
                for family in ACTION_FAMILY_ORDER
            )
            target_rate_sum = sum(
                float(row.get(f"target_rate.{category}", 0.0))
                for category in TARGET_CATEGORY_ORDER
            )
            expected_sum = 0.0 if phase_steps == 0 else 1.0
            action_ok = _close_enough(action_rate_sum, expected_sum)
            target_ok = _close_enough(target_rate_sum, expected_sum)
            all_checks_ok = bool(all_checks_ok and action_ok and target_ok)
            phase_payload[phase] = {
                "total_phase_steps": phase_steps,
                "action_rate_sum": action_rate_sum,
                "target_rate_sum": target_rate_sum,
                "action_distribution_ok": action_ok,
                "target_distribution_ok": target_ok,
            }
        trace_total_ok = total_phase_steps == len(trace_rows)
        rows.append(
            {
                "method_name": artifact.method_name,
                "display_name": artifact.display_name,
                "seed": artifact.seed,
                "policy_id": artifact.policy_id,
                "trace_row_count": len(trace_rows),
                "phase_step_total": total_phase_steps,
                "phase_total_matches_trace": trace_total_ok,
                "phases": phase_payload,
                "all_phase_checks_ok": bool(trace_total_ok and all_checks_ok),
            }
        )
    return rows


def _write_phase_sanity(
    artifacts: Iterable[AuditArtifact],
    phase_summary: dict[str, Any],
    *,
    output_dir: Path,
) -> None:
    rows = _collect_phase_sanity(artifacts, phase_summary)
    save_json(output_dir / "phase_segmentation_sanity.json", {"rows": rows})


def _collect_metric_consistency(semantic_root: Path) -> dict[str, Any]:
    seedwise = load_json(semantic_root / "semantic_comparison_seedwise.json")
    aggregate = load_json(semantic_root / "semantic_comparison_aggregate.json")
    seed_rows = list(seedwise.get("seed_summaries", []))
    metric_keys = list((aggregate.get("left") or {}).keys())
    sections = {
        "left": "left",
        "right": "right",
        "delta_left_minus_right": "delta",
    }
    checks: dict[str, dict[str, Any]] = {}
    all_ok = True
    for aggregate_key, prefix in sections.items():
        section_checks: dict[str, Any] = {}
        for metric_key in metric_keys:
            recomputed = sum(
                float(row.get(f"{prefix}_{metric_key}", 0.0)) for row in seed_rows
            ) / max(len(seed_rows), 1)
            aggregate_value = float((aggregate.get(aggregate_key) or {}).get(metric_key, 0.0))
            ok = _close_enough(recomputed, aggregate_value)
            all_ok = bool(all_ok and ok)
            section_checks[metric_key] = {
                "aggregate_value": aggregate_value,
                "recomputed_mean": recomputed,
                "match": ok,
            }
        checks[aggregate_key] = section_checks
    return {
        "num_seeds": len(seed_rows),
        "checks": checks,
        "all_metrics_match": all_ok,
    }


def _write_metric_consistency(semantic_root: Path, *, output_dir: Path) -> None:
    payload = _collect_metric_consistency(semantic_root)
    save_json(output_dir / "metric_consistency.json", payload)


def _write_rq3_latex_table(
    aggregate_payload: dict[str, Any],
    *,
    output_path: Path,
) -> None:
    left = aggregate_payload["left"]
    right = aggregate_payload["right"]
    left_name = aggregate_payload["left_display_name"]
    right_name = aggregate_payload["right_display_name"]

    def _fmt(value: float) -> str:
        return f"{float(value):.3f}"

    def _cell(value: float, other: float) -> str:
        formatted = _fmt(value)
        if value < other or math.isclose(value, other, rel_tol=1e-12, abs_tol=1e-12):
            return f"\\textbf{{{formatted}}}"
        return formatted

    lines = [
        r"\centering",
        r"\setlength{\tabcolsep}{3pt}",
        r"\resizebox{\textwidth}{!}{%",
        r"\begin{tabular}{lcccc}",
        r"\toprule",
        r"Method & Any Critical Breach & Sustained Critical Breach & Post-Foothold Drift (Q4) & Repeated Low-Value Decoy Loop (Q5) \\",
        r"\midrule",
        f"{left_name} & "
        f"{_cell(float(left['ever_critical_breach_rate']), float(right['ever_critical_breach_rate']))} & "
        f"{_cell(float(left['persistent_critical_breach_rate']), float(right['persistent_critical_breach_rate']))} & "
        f"{_cell(float(left['Q4_user_focus_after_enterprise_foothold']), float(right['Q4_user_focus_after_enterprise_foothold']))} & "
        f"{_cell(float(left['Q5_repeated_low_value_decoy_loop']), float(right['Q5_repeated_low_value_decoy_loop']))} \\\\",
        f"{right_name} & "
        f"{_cell(float(right['ever_critical_breach_rate']), float(left['ever_critical_breach_rate']))} & "
        f"{_cell(float(right['persistent_critical_breach_rate']), float(left['persistent_critical_breach_rate']))} & "
        f"{_cell(float(right['Q4_user_focus_after_enterprise_foothold']), float(left['Q4_user_focus_after_enterprise_foothold']))} & "
        f"{_cell(float(right['Q5_repeated_low_value_decoy_loop']), float(left['Q5_repeated_low_value_decoy_loop']))} \\\\",
        r"\bottomrule",
        r"\end{tabular}%",
        r"}",
    ]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_rq3_appendix_latex_table(
    aggregate_payload: dict[str, Any],
    *,
    output_path: Path,
) -> None:
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
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_rq3_symmetric_analysis(
    *,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    seeds: Iterable[int] = DEFAULT_SEEDS,
    eval_episodes: int = DEFAULT_EVAL_EPISODES,
    paper_table_path: str | Path = DEFAULT_PAPER_TABLE_PATH,
    paper_appendix_table_path: str | Path = DEFAULT_PAPER_APPENDIX_TABLE_PATH,
) -> dict[str, Any]:
    output_root = Path(output_root)
    trace_root = ensure_dir(output_root / "traces")
    audit_root = ensure_dir(output_root / "audits")
    trace_analysis_root = ensure_dir(output_root / "trace_analysis")
    semantic_root = ensure_dir(output_root / "semantic_comparison")
    phase_root = ensure_dir(output_root / "phase_analysis")
    paired_root = ensure_dir(output_root / "paired_casebooks")
    verification_root = ensure_dir(output_root / "verification")
    paper_table_path = Path(paper_table_path)
    paper_appendix_table_path = Path(paper_appendix_table_path)
    paper_table_path.parent.mkdir(parents=True, exist_ok=True)
    paper_appendix_table_path.parent.mkdir(parents=True, exist_ok=True)

    snapshot = topology_snapshot("Scenario2", "")
    critical_path_hosts = set(DEFAULT_CRITICAL_PATH_HOSTS)

    artifacts: list[AuditArtifact] = []
    for method_name in DEFAULT_METHODS:
        for seed in [int(value) for value in seeds]:
            table_b_record = _table_b_record(method_name, seed)
            input_path = Path(str(table_b_record["input_path"])).resolve()
            output_metrics = _load_json(table_b_record["output_path"])
            policy_id = str(output_metrics.get("selected_policy_id") or output_metrics.get("policy_id") or "")
            if not policy_id:
                raise ValueError(
                    f"Could not determine selected policy for method={method_name} seed={seed}"
                )
            candidate = Figure2ReplayCandidate(
                policy_id=policy_id,
                candidate_label="selected",
                candidate_aliases=("selected",),
            )
            if str(table_b_record.get("input_kind")) == "single_policy":
                metadata = _load_json(input_path)
                record = {"checkpoint_path": metadata.get("checkpoint_path")}
                trace_dir = export_candidate_trace(
                    method_name=method_name,
                    seed=seed,
                    candidate=candidate,
                    buffer_path=input_path,
                    buffer_anchor_path=input_path,
                    record=record,
                    metadata=metadata,
                    output_root=trace_root,
                    eval_episodes=eval_episodes,
                )
            else:
                buffer_payload = load_policy_buffer(input_path)
                metadata = dict(buffer_payload.get("metadata", {}))
                record_lookup = _buffer_record_lookup(buffer_payload)
                if policy_id not in record_lookup:
                    raise KeyError(
                        f"Selected policy_id={policy_id} not found in buffer for method={method_name} seed={seed}"
                    )
                trace_dir = export_candidate_trace(
                    method_name=method_name,
                    seed=seed,
                    candidate=candidate,
                    buffer_path=input_path,
                    buffer_anchor_path=input_path,
                    record=record_lookup[policy_id],
                    metadata=metadata,
                    output_root=trace_root,
                    eval_episodes=eval_episodes,
                )
            audit_dir = ensure_dir(
                audit_root
                / method_name
                / f"seed_{seed:04d}"
                / f"selected__{policy_id}_semantic_audit_replay{int(eval_episodes)}"
            )
            export_candidate_semantic_audit(
                trace_dir=trace_dir,
                output_dir=audit_dir,
                critical_host=DEFAULT_CRITICAL_HOST,
                critical_path_hosts=DEFAULT_CRITICAL_PATH_HOSTS,
            )
            artifacts.append(
                AuditArtifact(
                    method_name=method_name,
                    display_name=METHOD_DISPLAY[method_name],
                    seed=seed,
                    policy_id=policy_id,
                    trace_dir=Path(trace_dir),
                    audit_dir=audit_dir,
                    risk_summary_path=audit_dir / "risk_tier_summary.json",
                    trace_analysis_dir=trace_analysis_root / method_name / f"seed_{seed:04d}",
                )
            )

    for method_name in DEFAULT_METHODS:
        export_figure2_trace_analysis(
            trace_root=trace_root / method_name,
            output_root=trace_analysis_root / method_name,
            seed_filters=set(int(seed) for seed in seeds),
        )

    _write_policy_alignment(artifacts, output_dir=verification_root)

    artifacts_by_seed: dict[int, dict[str, AuditArtifact]] = defaultdict(dict)
    for artifact in artifacts:
        artifacts_by_seed[artifact.seed][artifact.method_name] = artifact

    comparison_seed_inputs: list[Path] = []
    paired_seed_summaries: dict[int, dict[str, Any]] = {}
    for seed in [int(value) for value in seeds]:
        per_seed = artifacts_by_seed[seed]
        left = per_seed["ours_stage2_v2_4"]
        right = per_seed["no_constraint_stage2_4obj"]
        seed_payload = {
            "seed": seed,
            "left_method_name": left.method_name,
            "left_display_name": left.display_name,
            "left_policy_id": left.policy_id,
            "left_risk_summary_path": str(left.risk_summary_path.resolve()),
            "right_method_name": right.method_name,
            "right_display_name": right.display_name,
            "right_policy_id": right.policy_id,
            "right_risk_summary_path": str(right.risk_summary_path.resolve()),
        }
        summary_input_path = semantic_root / f"seed_{seed:04d}_comparison.json"
        save_json(summary_input_path, seed_payload)
        comparison_seed_inputs.append(summary_input_path)

        paired_summary = {
            left.method_name: _build_pair_summary(
                left,
                snapshot=snapshot,
                critical_path_hosts=critical_path_hosts,
            ),
            right.method_name: _build_pair_summary(
                right,
                snapshot=snapshot,
                critical_path_hosts=critical_path_hosts,
            ),
        }
        paired_seed_summaries[seed] = paired_summary
        _write_seed_pair_casebook(seed, paired_summary, output_dir=paired_root)

    aggregate_path = build_method_comparison_semantic_summary(
        comparison_seed_inputs,
        output_dir=semantic_root,
        left_method_name="ours_stage2_v2_4",
        left_display_name=METHOD_DISPLAY["ours_stage2_v2_4"],
        right_method_name="no_constraint_stage2_4obj",
        right_display_name=METHOD_DISPLAY["no_constraint_stage2_4obj"],
    )
    aggregate_payload = load_json(aggregate_path)
    _write_rq3_latex_table(aggregate_payload, output_path=paper_table_path)
    _write_rq3_appendix_latex_table(
        aggregate_payload,
        output_path=paper_appendix_table_path,
    )

    phase_summary = _build_phase_summary(
        artifacts,
        snapshot=snapshot,
        critical_path_hosts=critical_path_hosts,
    )
    _write_phase_outputs(phase_summary, output_dir=phase_root)
    _write_artifact_completeness(
        artifacts,
        output_dir=verification_root,
        eval_episodes=int(eval_episodes),
    )
    _write_phase_sanity(
        artifacts,
        phase_summary,
        output_dir=verification_root,
    )
    _write_metric_consistency(semantic_root, output_dir=verification_root)

    return {
        "output_root": str(output_root.resolve()),
        "trace_root": str(trace_root.resolve()),
        "audit_root": str(audit_root.resolve()),
        "trace_analysis_root": str(trace_analysis_root.resolve()),
        "semantic_aggregate_path": str(aggregate_path),
        "phase_summary_path": str((phase_root / "phase_comparison.json").resolve()),
        "paper_table_path": str(paper_table_path.resolve()),
        "paper_appendix_table_path": str(paper_appendix_table_path.resolve()),
        "paired_casebook_root": str(paired_root.resolve()),
        "verification_path": str((verification_root / "policy_alignment.json").resolve()),
        "artifact_completeness_path": str(
            (verification_root / "artifact_completeness.json").resolve()
        ),
        "phase_sanity_path": str(
            (verification_root / "phase_segmentation_sanity.json").resolve()
        ),
        "metric_consistency_path": str(
            (verification_root / "metric_consistency.json").resolve()
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export the symmetric RQ3 semantic comparison between Constraint-Aware and Unconstrained Stage-2."
    )
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--paper-table-path", default=str(DEFAULT_PAPER_TABLE_PATH))
    parser.add_argument(
        "--paper-appendix-table-path",
        default=str(DEFAULT_PAPER_APPENDIX_TABLE_PATH),
    )
    parser.add_argument("--eval-episodes", type=int, default=DEFAULT_EVAL_EPISODES)
    parser.add_argument("--seeds", nargs="+", type=int, default=list(DEFAULT_SEEDS))
    args = parser.parse_args()

    summary = run_rq3_symmetric_analysis(
        output_root=args.output_root,
        seeds=args.seeds,
        eval_episodes=int(args.eval_episodes),
        paper_table_path=args.paper_table_path,
        paper_appendix_table_path=args.paper_appendix_table_path,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
