from __future__ import annotations

import argparse
import csv
import json
import os
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-cmorl-cyborg")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from cmorl_minicage.utils import ensure_dir

from .topology import topology_snapshot


DEFAULT_METHOD_NAME = "no_constraint_stage2_fair"
DEFAULT_TRACE_ROOT = (
    Path(__file__).resolve().parent
    / "outputs"
    / "paper_appendix"
    / "figure2_attack_defense_traces"
    / DEFAULT_METHOD_NAME
)
DEFAULT_OUTPUT_ROOT = (
    Path(__file__).resolve().parent
    / "outputs"
    / "paper_appendix"
    / "figure2_attack_defense_analysis"
    / DEFAULT_METHOD_NAME
)


def _method_display_name(method_name: str) -> str:
    mapping = {
        "ours_stage2_fair": "Constraint-Aware Stage-2",
        "no_constraint_stage2_fair": "Unconstrained Stage-2",
    }
    return mapping.get(method_name, method_name)


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _trace_rows(candidate_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for episode_path in sorted(candidate_dir.glob("episode_*.jsonl")):
        with episode_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                rows.append(json.loads(line))
    return rows


def _seed_dirs(trace_root: Path) -> list[Path]:
    return sorted(path for path in trace_root.glob("seed_*") if path.is_dir())


def _candidate_dirs(seed_dir: Path) -> list[Path]:
    return sorted(path for path in seed_dir.iterdir() if path.is_dir())


def _mode_with_share(values: list[str]) -> tuple[str, float]:
    if not values:
        return ("", 0.0)
    counts = Counter(values)
    label, count = counts.most_common(1)[0]
    return (label, float(count) / float(len(values)))


def _format_host_list(counter: Counter[str], top_k: int = 3) -> str:
    if not counter:
        return ""
    parts = [f"{host}({count})" for host, count in counter.most_common(top_k)]
    return ", ".join(parts)


def _host_order(snapshot: dict[str, Any]) -> list[str]:
    preferred_subnets = ("User", "Enterprise", "Operational")
    ordered: list[str] = []
    by_subnet: dict[str, list[str]] = defaultdict(list)
    for hostname, payload in snapshot["hosts"].items():
        subnet = payload.get("subnet") or "Unknown"
        by_subnet[str(subnet)].append(str(hostname))
    for subnet in preferred_subnets:
        ordered.extend(sorted(by_subnet.get(subnet, [])))
    for subnet in sorted(key for key in by_subnet if key not in preferred_subnets):
        ordered.extend(sorted(by_subnet[subnet]))
    return ordered


def _subnet_boundaries(hostnames: list[str], snapshot: dict[str, Any]) -> list[tuple[int, str]]:
    boundaries: list[tuple[int, str]] = []
    current_subnet: str | None = None
    for index, hostname in enumerate(hostnames):
        subnet = str(snapshot["hosts"][hostname].get("subnet") or "Unknown")
        if subnet != current_subnet:
            boundaries.append((index, subnet))
            current_subnet = subnet
    return boundaries


def _timeline_rows_for_candidate(
    *,
    seed: int,
    candidate_label: str,
    policy_id: str,
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_step: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_step[int(row["step_idx"])].append(row)

    timeline_rows: list[dict[str, Any]] = []
    for step_idx in sorted(by_step):
        step_rows = by_step[step_idx]
        blue_action_labels = [str(row["blue_action"]["name"]) for row in step_rows]
        blue_targets = [
            str(row["blue_action"].get("target_hostname") or row["blue_action"].get("target_subnet") or "")
            for row in step_rows
            if row["blue_action"].get("target_hostname") or row["blue_action"].get("target_subnet")
        ]
        red_action_labels = [str(row["red_action"]["name"]) for row in step_rows]
        red_targets = [
            str(row["red_action"].get("target_hostname") or row["red_action"].get("target_subnet") or "")
            for row in step_rows
            if row["red_action"].get("target_hostname") or row["red_action"].get("target_subnet")
        ]
        new_hosts = Counter(
            host for row in step_rows for host in row.get("newly_compromised_hosts", [])
        )
        recovered_hosts = Counter(
            host for row in step_rows for host in row.get("recovered_hosts", [])
        )
        state_after = [row["state_after"] for row in step_rows]
        op_server0_compromised_rate = mean(
            1.0 if "Op_Server0" in payload.get("compromised_hosts", []) else 0.0
            for payload in state_after
        )
        enterprise2_compromised_rate = mean(
            1.0 if "Enterprise2" in payload.get("compromised_hosts", []) else 0.0
            for payload in state_after
        )
        impact_rate = mean(
            1.0 if row["red_action"]["name"] == "Impact" else 0.0 for row in step_rows
        )
        restore_rate = mean(
            1.0 if row["blue_action"]["name"] == "Restore" else 0.0 for row in step_rows
        )
        sleep_rate = mean(
            1.0 if row["blue_action"]["name"] == "Sleep" else 0.0 for row in step_rows
        )
        mean_new_hosts = mean(len(row.get("newly_compromised_hosts", [])) for row in step_rows)
        mean_recovered_hosts = mean(len(row.get("recovered_hosts", [])) for row in step_rows)
        blue_mode, blue_mode_share = _mode_with_share(blue_action_labels)
        red_mode, red_mode_share = _mode_with_share(red_action_labels)
        blue_target_mode, _ = _mode_with_share(blue_targets)
        red_target_mode, _ = _mode_with_share(red_targets)

        timeline_rows.append(
            {
                "seed": seed,
                "candidate_label": candidate_label,
                "policy_id": policy_id,
                "step_idx": step_idx,
                "sample_count": len(step_rows),
                "blue_action_mode": blue_mode,
                "blue_action_mode_share": round(blue_mode_share, 4),
                "blue_target_mode": blue_target_mode,
                "red_action_mode": red_mode,
                "red_action_mode_share": round(red_mode_share, 4),
                "red_target_mode": red_target_mode,
                "newly_compromised_top_hosts": _format_host_list(new_hosts),
                "recovered_top_hosts": _format_host_list(recovered_hosts),
                "mean_newly_compromised_hosts": round(mean_new_hosts, 4),
                "mean_recovered_hosts": round(mean_recovered_hosts, 4),
                "op_server0_compromised_rate": round(op_server0_compromised_rate, 4),
                "enterprise2_compromised_rate": round(enterprise2_compromised_rate, 4),
                "impact_rate": round(impact_rate, 4),
                "restore_rate": round(restore_rate, 4),
                "sleep_rate": round(sleep_rate, 4),
            }
        )
    return timeline_rows


def _host_summary_rows_for_candidate(
    *,
    seed: int,
    candidate_label: str,
    policy_id: str,
    rows: list[dict[str, Any]],
    snapshot: dict[str, Any],
) -> list[dict[str, Any]]:
    hostnames = _host_order(snapshot)
    total_rows = max(len(rows), 1)
    blue_target_count = Counter()
    blue_restore_count = Counter()
    blue_analyse_count = Counter()
    blue_decoy_count = Counter()
    red_target_count = Counter()
    red_impact_count = Counter()
    new_compromise_count = Counter()
    recovered_count = Counter()
    compromised_presence_count = Counter()

    for row in rows:
        blue_action = row["blue_action"]
        red_action = row["red_action"]
        blue_target = blue_action.get("target_hostname")
        red_target = red_action.get("target_hostname")
        if blue_target:
            blue_target_count[str(blue_target)] += 1
            blue_name = str(blue_action.get("name") or "")
            if blue_name == "Restore":
                blue_restore_count[str(blue_target)] += 1
            if blue_name == "Analyse":
                blue_analyse_count[str(blue_target)] += 1
            if blue_name.startswith("Decoy"):
                blue_decoy_count[str(blue_target)] += 1
        if red_target:
            red_target_count[str(red_target)] += 1
            if str(red_action.get("name") or "") == "Impact":
                red_impact_count[str(red_target)] += 1
        for host in row.get("newly_compromised_hosts", []):
            new_compromise_count[str(host)] += 1
        for host in row.get("recovered_hosts", []):
            recovered_count[str(host)] += 1
        for host in row.get("state_after", {}).get("compromised_hosts", []):
            compromised_presence_count[str(host)] += 1

    summary_rows: list[dict[str, Any]] = []
    for hostname in hostnames:
        host_payload = snapshot["hosts"][hostname]
        summary_rows.append(
            {
                "seed": seed,
                "candidate_label": candidate_label,
                "policy_id": policy_id,
                "hostname": hostname,
                "subnet": host_payload.get("subnet"),
                "role_group": host_payload.get("role_group"),
                "is_critical": bool(host_payload.get("is_critical", False)),
                "compromised_presence_rate": round(
                    float(compromised_presence_count[hostname]) / float(total_rows),
                    4,
                ),
                "new_compromise_count": int(new_compromise_count[hostname]),
                "recovered_count": int(recovered_count[hostname]),
                "blue_target_count": int(blue_target_count[hostname]),
                "blue_restore_count": int(blue_restore_count[hostname]),
                "blue_analyse_count": int(blue_analyse_count[hostname]),
                "blue_decoy_count": int(blue_decoy_count[hostname]),
                "red_target_count": int(red_target_count[hostname]),
                "red_impact_count": int(red_impact_count[hostname]),
            }
        )
    return summary_rows


def _candidate_heatmap_arrays(
    rows: list[dict[str, Any]],
    snapshot: dict[str, Any],
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    hostnames = _host_order(snapshot)
    host_to_index = {hostname: idx for idx, hostname in enumerate(hostnames)}
    max_step = max(int(row["step_idx"]) for row in rows) if rows else 0
    step_count = max_step + 1
    compromise = np.zeros((len(hostnames), step_count), dtype=np.float32)
    defense = np.zeros((len(hostnames), step_count), dtype=np.float32)
    samples_by_step = np.zeros((step_count,), dtype=np.float32)

    for row in rows:
        step_idx = int(row["step_idx"])
        samples_by_step[step_idx] += 1.0
        for host in row.get("state_after", {}).get("compromised_hosts", []):
            idx = host_to_index.get(str(host))
            if idx is not None:
                compromise[idx, step_idx] += 1.0
        blue_target = row.get("blue_action", {}).get("target_hostname")
        if blue_target:
            idx = host_to_index.get(str(blue_target))
            if idx is not None:
                defense[idx, step_idx] += 1.0

    for step_idx in range(step_count):
        denom = max(samples_by_step[step_idx], 1.0)
        compromise[:, step_idx] /= denom
        defense[:, step_idx] /= denom
    return compromise, defense, hostnames


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_timeline_markdown(path: Path, rows: list[dict[str, Any]]) -> None:
    columns = [
        "candidate_label",
        "policy_id",
        "step_idx",
        "blue_action_mode",
        "blue_target_mode",
        "red_action_mode",
        "red_target_mode",
        "newly_compromised_top_hosts",
        "recovered_top_hosts",
        "op_server0_compromised_rate",
        "enterprise2_compromised_rate",
        "impact_rate",
        "restore_rate",
    ]
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["candidate_label"]), str(row["policy_id"]))].append(row)

    lines: list[str] = []
    for (candidate_label, policy_id), group_rows in grouped.items():
        lines.append(f"## {candidate_label} ({policy_id})")
        lines.append("")
        lines.append("| " + " | ".join(columns) + " |")
        lines.append("| " + " | ".join("---" for _ in columns) + " |")
        for row in group_rows:
            lines.append("| " + " | ".join(str(row[column]) for column in columns) + " |")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _plot_seed_heatmap(
    *,
    seed: int,
    candidate_payloads: list[dict[str, Any]],
    snapshot: dict[str, Any],
    output_path: Path,
) -> None:
    if not candidate_payloads:
        return
    hostnames = _host_order(snapshot)
    boundaries = _subnet_boundaries(hostnames, snapshot)
    ncols = len(candidate_payloads)
    fig, axes = plt.subplots(
        2,
        ncols,
        figsize=(5.0 * ncols, 10.0),
        squeeze=False,
        sharey=True,
    )
    compromise_image = None
    defense_image = None
    method_names = sorted(
        {
            str(payload.get("method_name", ""))
            for payload in candidate_payloads
            if str(payload.get("method_name", ""))
        }
    )
    title_prefix = (
        _method_display_name(method_names[0])
        if len(method_names) == 1
        else " / ".join(_method_display_name(name) for name in method_names)
    )
    for col, payload in enumerate(candidate_payloads):
        compromise, defense, ordered_hosts = _candidate_heatmap_arrays(payload["rows"], snapshot)
        ax_comp = axes[0][col]
        ax_def = axes[1][col]
        compromise_image = ax_comp.imshow(
            compromise,
            aspect="auto",
            interpolation="nearest",
            cmap="Reds",
            vmin=0.0,
            vmax=1.0,
        )
        defense_image = ax_def.imshow(
            defense,
            aspect="auto",
            interpolation="nearest",
            cmap="Blues",
            vmin=0.0,
            vmax=max(float(np.max(defense)), 0.05),
        )
        ax_comp.set_title(
            f"{payload['candidate_label']} ({payload['policy_id']})\nCompromised Rate",
            fontsize=10,
        )
        ax_def.set_title(
            f"{payload['candidate_label']} ({payload['policy_id']})\nBlue Target Rate",
            fontsize=10,
        )
        ax_comp.set_xlabel("step_idx")
        ax_def.set_xlabel("step_idx")
        if col == 0:
            ax_comp.set_ylabel("host")
            ax_def.set_ylabel("host")
            ax_comp.set_yticks(range(len(ordered_hosts)))
            ax_comp.set_yticklabels(ordered_hosts, fontsize=8)
            ax_def.set_yticks(range(len(ordered_hosts)))
            ax_def.set_yticklabels(ordered_hosts, fontsize=8)
        else:
            ax_comp.set_yticks(range(len(ordered_hosts)))
            ax_comp.set_yticklabels([])
            ax_def.set_yticks(range(len(ordered_hosts)))
            ax_def.set_yticklabels([])
        for ax in (ax_comp, ax_def):
            for boundary_index, subnet_name in boundaries:
                ax.axhline(boundary_index - 0.5, color="white", linewidth=1.0)
                if boundary_index < len(ordered_hosts):
                    ax.text(
                        -0.02,
                        boundary_index / max(len(ordered_hosts), 1),
                        subnet_name,
                        transform=ax.transAxes,
                        ha="right",
                        va="bottom",
                        fontsize=8,
                    )
    fig.suptitle(f"{title_prefix} seed {seed:04d} host-level attack-defense heatmap")
    if compromise_image is not None:
        fig.colorbar(compromise_image, ax=axes[0, :].tolist(), shrink=0.85, label="compromised rate")
    if defense_image is not None:
        fig.colorbar(defense_image, ax=axes[1, :].tolist(), shrink=0.85, label="blue target rate")
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def export_figure2_trace_analysis(
    *,
    trace_root: str | Path = DEFAULT_TRACE_ROOT,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    seed_filters: set[int] | None = None,
    policy_id_filters: set[str] | None = None,
    output_subdir: str | None = None,
) -> list[Path]:
    trace_root = Path(trace_root)
    output_root = Path(output_root)
    exported_paths: list[Path] = []
    snapshot = topology_snapshot("Scenario2", "")
    for seed_dir in _seed_dirs(trace_root):
        seed = int(seed_dir.name.split("_")[1])
        if seed_filters is not None and seed not in seed_filters:
            continue
        seed_output_dir = output_root / seed_dir.name
        if output_subdir:
            seed_output_dir = seed_output_dir / output_subdir
        seed_output_dir = ensure_dir(seed_output_dir)
        timeline_rows: list[dict[str, Any]] = []
        host_summary_rows: list[dict[str, Any]] = []
        candidate_payloads: list[dict[str, Any]] = []

        for candidate_dir in _candidate_dirs(seed_dir):
            manifest = _load_json(candidate_dir / "trace_manifest.json")
            rows = _trace_rows(candidate_dir)
            candidate_label = str(manifest["candidate_label"])
            policy_id = str(manifest["policy_id"])
            if policy_id_filters is not None and policy_id not in policy_id_filters:
                continue
            timeline_rows.extend(
                _timeline_rows_for_candidate(
                    seed=seed,
                    candidate_label=candidate_label,
                    policy_id=policy_id,
                    rows=rows,
                )
            )
            host_summary_rows.extend(
                _host_summary_rows_for_candidate(
                    seed=seed,
                    candidate_label=candidate_label,
                    policy_id=policy_id,
                    rows=rows,
                    snapshot=snapshot,
                )
            )
            candidate_payloads.append(
                {
                    "method_name": str(manifest.get("method_name", "")),
                    "candidate_label": candidate_label,
                    "policy_id": policy_id,
                    "rows": rows,
                }
            )

        if not candidate_payloads:
            continue

        timeline_csv = seed_output_dir / "timeline_table.csv"
        timeline_md = seed_output_dir / "timeline_table.md"
        host_summary_csv = seed_output_dir / "host_level_summary.csv"
        heatmap_png = seed_output_dir / "host_attack_defense_heatmap.png"

        _write_csv(timeline_csv, timeline_rows)
        _write_timeline_markdown(timeline_md, timeline_rows)
        _write_csv(host_summary_csv, host_summary_rows)
        _plot_seed_heatmap(
            seed=seed,
            candidate_payloads=candidate_payloads,
            snapshot=snapshot,
            output_path=heatmap_png,
        )
        exported_paths.extend([timeline_csv, timeline_md, host_summary_csv, heatmap_png])
    return exported_paths


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export seed-level timeline tables and host-level heatmaps for Figure 2 traces."
    )
    parser.add_argument("--trace-root", default=str(DEFAULT_TRACE_ROOT))
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument(
        "--seed",
        dest="seeds",
        action="append",
        type=int,
        help="Restrict export to one or more seed values. Repeat to pass multiple.",
    )
    parser.add_argument(
        "--policy-id",
        dest="policy_ids",
        action="append",
        help="Restrict export to one or more candidate policy ids. Repeat to pass multiple.",
    )
    parser.add_argument(
        "--output-subdir",
        default=None,
        help="Optional subdirectory name created under each exported seed directory.",
    )
    args = parser.parse_args()

    exported = export_figure2_trace_analysis(
        trace_root=args.trace_root,
        output_root=args.output_root,
        seed_filters=None if not args.seeds else set(int(seed) for seed in args.seeds),
        policy_id_filters=None if not args.policy_ids else set(args.policy_ids),
        output_subdir=args.output_subdir,
    )
    print(f"Exported {len(exported)} analysis artifacts to {Path(args.output_root)}")


if __name__ == "__main__":
    main()
