from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from cmorl_minicage.utils import load_json, save_json

_QUESTIONABLE_RULE_KEYS = (
    "Q2_user_action_during_critical_breach",
    "Q3_missed_immediate_response_to_critical_hit",
    "Q4_user_focus_after_enterprise_foothold",
    "Q5_repeated_low_value_decoy_loop",
)
_TIER_KEYS = (
    "Tier 0 Safe",
    "Tier 1 Near-Miss",
    "Tier 2 Transient Critical Breach",
    "Tier 3 Persistent Critical Breach",
)
_PRECRITICAL_STEP_RATE_KEYS = (
    "restore",
    "decoy",
)
_NUMERIC_KEYS = (
    "ever_critical_breach_rate",
    "persistent_critical_breach_rate",
    "mean_critical_dwell_steps",
    "high_confidence_env_run_rate",
)


def _as_float(value: Any) -> float:
    if value is None:
        return 0.0
    return float(value)


def _risk_metrics(summary_path: str | Path) -> dict[str, float]:
    payload = load_json(summary_path)
    questionable = payload.get("questionable_rule_env_run_rates", {}) or {}
    tier_rates = payload.get("tier_rates", {}) or {}
    precritical_rates = payload.get("precritical_action_family_step_rates", {}) or {}

    metrics = {
        key: _as_float(payload.get(key))
        for key in _NUMERIC_KEYS
    }
    for key in _QUESTIONABLE_RULE_KEYS:
        metrics[key] = _as_float(questionable.get(key))
    for key in _TIER_KEYS:
        metrics[key] = _as_float(tier_rates.get(key))
    for key in _PRECRITICAL_STEP_RATE_KEYS:
        metrics[f"precritical_action_family_step_rates.{key}"] = _as_float(
            precritical_rates.get(key)
        )
    metrics["precritical_compromised_target_focus_step_rate"] = _as_float(
        payload.get("precritical_compromised_target_focus_step_rate")
    )
    return metrics


def _seed_from_summary(summary_path: Path, summary: dict[str, Any]) -> int:
    value = summary.get("seed")
    if value is not None:
        return int(value)
    stem = summary_path.stem
    if stem.startswith("seed_"):
        return int(stem.split("_")[1])
    raise ValueError(f"Could not infer seed from {summary_path}")


def _mean(rows: list[dict[str, Any]], key: str) -> float:
    return sum(float(row.get(key, 0.0)) for row in rows) / max(len(rows), 1)


def build_semantic_risk_summary(
    final_summary_paths: list[str | Path],
    *,
    output_dir: str | Path,
) -> Path:
    if not final_summary_paths:
        raise ValueError("final_summary_paths must not be empty")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    seed_rows: list[dict[str, Any]] = []
    metric_keys: list[str] = []
    for raw_path in final_summary_paths:
        summary_path = Path(raw_path).resolve()
        summary = load_json(summary_path)
        selected_path = summary.get("selected_risk_summary_path")
        baseline_path = summary.get("baseline_risk_summary_path")
        if not selected_path or not baseline_path:
            raise ValueError(
                f"Final summary must include selected_risk_summary_path and baseline_risk_summary_path: {summary_path}"
            )
        selected_metrics = _risk_metrics(selected_path)
        baseline_metrics = _risk_metrics(baseline_path)
        metric_keys = list(selected_metrics.keys())
        row: dict[str, Any] = {
            "seed": _seed_from_summary(summary_path, summary),
            "selected_policy_id": str(
                summary.get("final_selected_policy_id") or summary.get("selected_policy_id") or ""
            ),
            "baseline_policy_id": str(summary.get("baseline_policy_id") or ""),
            "final_summary_path": str(summary_path),
            "selected_risk_summary_path": str(Path(selected_path).resolve()),
            "baseline_risk_summary_path": str(Path(baseline_path).resolve()),
        }
        for key, value in selected_metrics.items():
            row[f"selected_{key}"] = value
        for key, value in baseline_metrics.items():
            row[f"baseline_{key}"] = value
        for key in metric_keys:
            row[f"delta_{key}"] = float(row[f"selected_{key}"]) - float(
                row[f"baseline_{key}"]
            )
        seed_rows.append(row)

    seed_rows.sort(key=lambda row: int(row["seed"]))

    aggregate_selected = {
        key: _mean(seed_rows, f"selected_{key}") for key in metric_keys
    }
    aggregate_baseline = {
        key: _mean(seed_rows, f"baseline_{key}") for key in metric_keys
    }
    aggregate_delta = {
        key: _mean(seed_rows, f"delta_{key}") for key in metric_keys
    }

    seedwise_payload = {
        "num_seeds": len(seed_rows),
        "source_final_summary_paths": [str(Path(path).resolve()) for path in final_summary_paths],
        "seed_summaries": seed_rows,
    }
    aggregate_payload = {
        "num_seeds": len(seed_rows),
        "selected": aggregate_selected,
        "baseline": aggregate_baseline,
        "delta": aggregate_delta,
    }

    save_json(output_dir / "semantic_risk_seedwise.json", seedwise_payload)
    save_json(output_dir / "semantic_risk_aggregate.json", aggregate_payload)

    csv_fieldnames = [
        "seed",
        "selected_policy_id",
        "baseline_policy_id",
    ]
    for prefix in ("selected", "baseline", "delta"):
        csv_fieldnames.extend(f"{prefix}_{key}" for key in metric_keys)
    with (output_dir / "semantic_risk_seedwise.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=csv_fieldnames)
        writer.writeheader()
        for row in seed_rows:
            writer.writerow({field: row.get(field, "") for field in csv_fieldnames})

    md_lines = [
        "# 3-Seed Semantic Risk Summary",
        "",
        "| seed | selected_policy_id | baseline_policy_id | selected_ever | baseline_ever | delta_ever | selected_persistent | baseline_persistent | delta_persistent | selected_tier1 | baseline_tier1 | delta_tier1 |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in seed_rows:
        md_lines.append(
            "| "
            f"{row['seed']} | "
            f"{row['selected_policy_id']} | "
            f"{row['baseline_policy_id']} | "
            f"{row['selected_ever_critical_breach_rate']:.4f} | "
            f"{row['baseline_ever_critical_breach_rate']:.4f} | "
            f"{row['delta_ever_critical_breach_rate']:.4f} | "
            f"{row['selected_persistent_critical_breach_rate']:.4f} | "
            f"{row['baseline_persistent_critical_breach_rate']:.4f} | "
            f"{row['delta_persistent_critical_breach_rate']:.4f} | "
            f"{row['selected_Tier 1 Near-Miss']:.4f} | "
            f"{row['baseline_Tier 1 Near-Miss']:.4f} | "
            f"{row['delta_Tier 1 Near-Miss']:.4f} |"
        )
    md_lines.extend(
        [
            "",
            "## Aggregate",
            "",
            f"- `selected ever_critical_breach_rate = {aggregate_selected['ever_critical_breach_rate']:.4f}`",
            f"- `baseline ever_critical_breach_rate = {aggregate_baseline['ever_critical_breach_rate']:.4f}`",
            f"- `delta ever_critical_breach_rate = {aggregate_delta['ever_critical_breach_rate']:.4f}`",
            f"- `selected persistent_critical_breach_rate = {aggregate_selected['persistent_critical_breach_rate']:.4f}`",
            f"- `baseline persistent_critical_breach_rate = {aggregate_baseline['persistent_critical_breach_rate']:.4f}`",
            f"- `delta persistent_critical_breach_rate = {aggregate_delta['persistent_critical_breach_rate']:.4f}`",
            f"- `selected Tier 1 Near-Miss = {aggregate_selected['Tier 1 Near-Miss']:.4f}`",
            f"- `baseline Tier 1 Near-Miss = {aggregate_baseline['Tier 1 Near-Miss']:.4f}`",
            f"- `delta Tier 1 Near-Miss = {aggregate_delta['Tier 1 Near-Miss']:.4f}`",
            f"- `selected precritical restore step rate = {aggregate_selected['precritical_action_family_step_rates.restore']:.4f}`",
            f"- `baseline precritical restore step rate = {aggregate_baseline['precritical_action_family_step_rates.restore']:.4f}`",
            f"- `delta precritical restore step rate = {aggregate_delta['precritical_action_family_step_rates.restore']:.4f}`",
            f"- `selected precritical decoy step rate = {aggregate_selected['precritical_action_family_step_rates.decoy']:.4f}`",
            f"- `baseline precritical decoy step rate = {aggregate_baseline['precritical_action_family_step_rates.decoy']:.4f}`",
            f"- `delta precritical decoy step rate = {aggregate_delta['precritical_action_family_step_rates.decoy']:.4f}`",
        ]
    )
    (output_dir / "semantic_risk_summary.md").write_text(
        "\n".join(md_lines),
        encoding="utf-8",
    )

    return output_dir / "semantic_risk_aggregate.json"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Aggregate selected-vs-baseline semantic risk summaries across seeds."
    )
    parser.add_argument("--final-summary-paths", nargs="+", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    output_path = build_semantic_risk_summary(
        args.final_summary_paths,
        output_dir=args.output_dir,
    )
    print(output_path)


if __name__ == "__main__":
    main()
