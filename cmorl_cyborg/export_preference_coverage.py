from __future__ import annotations

import argparse
import csv
import json
import os
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-cmorl-cyborg")


METHOD_ORDER = [
    "ours_stage2",
    "stage1_only",
    "weighted_sum",
    "preference_conditioned_ppo",
    "pcn",
]

DISPLAY_NAMES = {
    "ours_stage2": "Ours Stage2",
    "stage1_only": "Stage1 Only",
    "weighted_sum": "Weighted-Sum",
    "preference_conditioned_ppo": "Preference-Conditioned PPO",
    "pcn": "PCN",
}

PALETTE = [
    "#4c78a8",
    "#f58518",
    "#54a24b",
    "#e45756",
    "#72b7b2",
    "#b279a2",
    "#ff9da6",
    "#9d755d",
    "#bab0ab",
]


def _load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _short_preference(preference: list[float]) -> str:
    cleaned = []
    for value in preference:
        rounded = round(float(value), 1)
        if abs(rounded - round(rounded)) < 1e-8:
            cleaned.append(str(int(round(rounded))))
        else:
            cleaned.append(f"{rounded:.1f}")
    return f"({cleaned[0]}, {cleaned[1]}, {cleaned[2]})"


def _import_matplotlib():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    return plt, Rectangle


def _resolve_table_a_summary(path: str | Path | None) -> Path:
    if path is not None:
        return Path(path).resolve()
    return (
        Path(__file__).resolve().parent
        / "outputs"
        / "paper_table_a"
        / "table_a_summary.json"
    )


def _extract_long_rows(summary: dict[str, Any]) -> tuple[list[dict[str, Any]], list[list[float]]]:
    rows: list[dict[str, Any]] = []
    reference_preferences: list[list[float]] = []

    method_rows = {
        entry["method_name"]: entry
        for entry in summary.get("method_summary", [])
        if entry.get("method_name") in METHOD_ORDER
    }

    for method_name in METHOD_ORDER:
        if method_name not in method_rows:
            raise ValueError(f"Missing method in table_a_summary: {method_name}")
        method_entry = method_rows[method_name]
        for run in method_entry.get("runs", []):
            metrics_path = Path(run["metrics_path"]).resolve()
            metrics_payload = _load_json(metrics_path)
            assignments = metrics_payload.get("assignments", [])
            if not assignments:
                raise ValueError(f"No assignments found in {metrics_path}")
            if not reference_preferences:
                reference_preferences = [
                    list(map(float, assignment["preference"])) for assignment in assignments
                ]
            elif len(reference_preferences) != len(assignments):
                raise ValueError(
                    f"Preference grid mismatch for {metrics_path}: "
                    f"expected {len(reference_preferences)} rows, got {len(assignments)}"
                )

            seed = int(run["seed"])
            for pref_idx, assignment in enumerate(assignments):
                preference = list(map(float, assignment["preference"]))
                rows.append(
                    {
                        "method_name": method_name,
                        "display_name": DISPLAY_NAMES[method_name],
                        "seed": seed,
                        "preference_index": pref_idx,
                        "preference": preference,
                        "assigned_policy_id": str(assignment["policy_id"]),
                        "utility": float(assignment.get("utility", 0.0)),
                    }
                )
    return rows, reference_preferences


def _aggregate_rows(
    rows: list[dict[str, Any]],
    reference_preferences: list[list[float]],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, int]]]:
    grouped: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    policy_totals: dict[str, Counter[str]] = defaultdict(Counter)
    seed_counts: dict[str, set[int]] = defaultdict(set)

    for row in rows:
        method_name = str(row["method_name"])
        preference_index = int(row["preference_index"])
        grouped[(method_name, preference_index)].append(row)
        policy_totals[method_name][str(row["assigned_policy_id"])] += 1
        seed_counts[method_name].add(int(row["seed"]))

    slot_maps: dict[str, dict[str, int]] = {}
    for method_name, counter in policy_totals.items():
        ordered_policy_ids = sorted(counter, key=lambda item: (-counter[item], item))
        slot_maps[method_name] = {
            policy_id: slot_idx + 1 for slot_idx, policy_id in enumerate(ordered_policy_ids)
        }

    aggregate_rows: list[dict[str, Any]] = []
    for method_name in METHOD_ORDER:
        n_seeds = len(seed_counts.get(method_name, set()))
        for preference_index, preference in enumerate(reference_preferences):
            entries = grouped[(method_name, preference_index)]
            policy_counter = Counter(str(entry["assigned_policy_id"]) for entry in entries)
            dominant_policy_id = sorted(
                policy_counter,
                key=lambda item: (
                    -policy_counter[item],
                    -policy_totals[method_name][item],
                    item,
                ),
            )[0]
            dominant_count = int(policy_counter[dominant_policy_id])
            aggregate_rows.append(
                {
                    "method_name": method_name,
                    "display_name": DISPLAY_NAMES[method_name],
                    "preference_index": preference_index,
                    "preference": preference,
                    "preference_label": _short_preference(preference),
                    "dominant_policy_id": dominant_policy_id,
                    "dominant_slot": slot_maps[method_name][dominant_policy_id],
                    "dominant_count": dominant_count,
                    "dominant_share": (
                        float(dominant_count / n_seeds) if n_seeds > 0 else 0.0
                    ),
                    "num_distinct_policies": len(policy_counter),
                    "assigned_policy_ids": sorted(policy_counter),
                    "policy_counts": dict(sorted(policy_counter.items())),
                }
            )

    return aggregate_rows, slot_maps


def _write_long_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "method_name",
                "display_name",
                "seed",
                "preference_index",
                "pref_security",
                "pref_business",
                "pref_cost",
                "assigned_policy_id",
                "utility",
            ],
        )
        writer.writeheader()
        for row in rows:
            preference = row["preference"]
            writer.writerow(
                {
                    "method_name": row["method_name"],
                    "display_name": row["display_name"],
                    "seed": row["seed"],
                    "preference_index": row["preference_index"],
                    "pref_security": preference[0],
                    "pref_business": preference[1],
                    "pref_cost": preference[2],
                    "assigned_policy_id": row["assigned_policy_id"],
                    "utility": row["utility"],
                }
            )


def _write_aggregate_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "method_name",
                "display_name",
                "preference_index",
                "preference_label",
                "pref_security",
                "pref_business",
                "pref_cost",
                "dominant_policy_id",
                "dominant_slot",
                "dominant_count",
                "dominant_share",
                "num_distinct_policies",
            ],
        )
        writer.writeheader()
        for row in rows:
            preference = row["preference"]
            writer.writerow(
                {
                    "method_name": row["method_name"],
                    "display_name": row["display_name"],
                    "preference_index": row["preference_index"],
                    "preference_label": row["preference_label"],
                    "pref_security": preference[0],
                    "pref_business": preference[1],
                    "pref_cost": preference[2],
                    "dominant_policy_id": row["dominant_policy_id"],
                    "dominant_slot": row["dominant_slot"],
                    "dominant_count": row["dominant_count"],
                    "dominant_share": row["dominant_share"],
                    "num_distinct_policies": row["num_distinct_policies"],
                }
            )


def _plot_preference_coverage(
    aggregate_rows: list[dict[str, Any]],
    slot_maps: dict[str, dict[str, int]],
    output_path: Path,
) -> None:
    plt, Rectangle = _import_matplotlib()
    grouped_by_method: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in aggregate_rows:
        grouped_by_method[str(row["method_name"])].append(row)

    fig_height = 1.1 * len(METHOD_ORDER) + 1.7
    fig, ax = plt.subplots(figsize=(16, fig_height))
    ax.set_facecolor("white")

    for row_idx, method_name in enumerate(METHOD_ORDER):
        method_rows = sorted(
            grouped_by_method[method_name], key=lambda item: int(item["preference_index"])
        )
        y = len(METHOD_ORDER) - row_idx - 1
        for cell in method_rows:
            slot = int(cell["dominant_slot"])
            share = float(cell["dominant_share"])
            color = PALETTE[(slot - 1) % len(PALETTE)]
            rect = Rectangle(
                (int(cell["preference_index"]), y),
                1.0,
                0.82,
                facecolor=color,
                edgecolor="#ffffff",
                linewidth=0.8,
                alpha=0.3 + (0.7 * share),
            )
            ax.add_patch(rect)
        ax.text(
            len(method_rows) + 0.4,
            y + 0.41,
            f"{len(slot_maps[method_name])} assigned policies",
            va="center",
            ha="left",
            fontsize=10,
            color="#333333",
        )

    reference_rows = sorted(
        grouped_by_method[METHOD_ORDER[0]], key=lambda item: int(item["preference_index"])
    )
    tick_indices = [0, 10, 20, 30, 40, 50, 65]
    tick_indices = [idx for idx in tick_indices if idx < len(reference_rows)]
    tick_labels = [reference_rows[idx]["preference_label"] for idx in tick_indices]

    ax.set_xlim(0, len(reference_rows) + 10)
    ax.set_ylim(0, len(METHOD_ORDER))
    ax.set_yticks([len(METHOD_ORDER) - idx - 1 + 0.41 for idx in range(len(METHOD_ORDER))])
    ax.set_yticklabels([DISPLAY_NAMES[name] for name in METHOD_ORDER], fontsize=11)
    ax.set_xticks([idx + 0.5 for idx in tick_indices])
    ax.set_xticklabels(tick_labels, fontsize=10)
    ax.set_xlabel("Preference vector $(w_{sec}, w_{biz}, w_{cost})$", fontsize=11)
    ax.set_title(
        "Preference Coverage: assignment regions across the evaluation simplex",
        fontsize=13,
        pad=12,
    )

    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", length=0)
    ax.grid(False)

    ax.text(
        0,
        -0.52,
        "Within each row, colors denote different assigned policies for that method; darker cells mean higher seed agreement.",
        fontsize=10,
        ha="left",
        va="top",
        color="#444444",
    )

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def export_preference_coverage(summary_path: str | Path | None = None) -> dict[str, str]:
    summary_path = _resolve_table_a_summary(summary_path)
    summary = _load_json(summary_path)
    long_rows, reference_preferences = _extract_long_rows(summary)
    aggregate_rows, slot_maps = _aggregate_rows(long_rows, reference_preferences)

    output_dir = summary_path.parent.parent / "paper_figure_c"
    output_dir.mkdir(parents=True, exist_ok=True)

    long_csv_path = output_dir / "per_preference_assignment.csv"
    aggregate_csv_path = output_dir / "per_preference_assignment_summary.csv"
    json_path = output_dir / "preference_coverage.json"
    figure_path = output_dir / "preference_coverage.png"

    _write_long_csv(long_csv_path, long_rows)
    _write_aggregate_csv(aggregate_csv_path, aggregate_rows)
    json_path.write_text(
        json.dumps(
            {
                "summary_path": str(summary_path),
                "methods": METHOD_ORDER,
                "display_names": DISPLAY_NAMES,
                "policy_slot_maps": slot_maps,
                "preference_grid_size": len(reference_preferences),
                "aggregate_rows": aggregate_rows,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    _plot_preference_coverage(aggregate_rows, slot_maps, figure_path)

    return {
        "long_csv": str(long_csv_path),
        "aggregate_csv": str(aggregate_csv_path),
        "json": str(json_path),
        "figure": str(figure_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export per-preference assignments and generate Preference Coverage figure."
    )
    parser.add_argument("--summary-path", default=None)
    args = parser.parse_args()

    outputs = export_preference_coverage(args.summary_path)
    for key, value in outputs.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
