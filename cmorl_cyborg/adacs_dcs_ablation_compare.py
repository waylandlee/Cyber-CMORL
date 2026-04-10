from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from cmorl_minicage.utils import ensure_dir, load_json, save_json

from . import export_tight_feasible_set_reevaluated as reevaluate_mod
from .compare_suite import compare_suite
from .evaluate_constraints import write_aggregated_constraint_metrics
from .paper_plots import plot_fair_compare_table_b, plot_main_table_a

SEEDS = (7, 11, 19)

METHOD_SPECS = [
    {
        "method_name": "original_stage2_fair",
        "display_name": "Original Stage2",
        "color": "#9d755d",
    },
    {
        "method_name": "adaptive_fixed_stage2_fair",
        "display_name": "AdaCS Only",
        "color": "#54a24b",
    },
    {
        "method_name": "crowding_dynamic_stage2_fair",
        "display_name": "DCS Only",
        "color": "#f58518",
    },
    {
        "method_name": "ours_stage2_fair",
        "display_name": "AdaCS-DCS Full",
        "color": "#4c78a8",
    },
]

SET_METRICS = [
    "hypervolume",
    "expected_utility",
    "coverage_ratio",
    "unique_assigned_policies",
    "num_pareto_records",
    "sparsity",
]
DEPLOYMENT_METRICS = [
    "security_return",
    "business_return",
    "cost_return",
    "feasible_rate",
    "mean_violation",
    "final_critical_compromised_hosts",
    "critical_impact_count",
    "high_disruption_action_rate",
]
TIGHT_FEASIBLE_METRICS = [
    "reevaluated_feasible_candidate_count",
    "reevaluated_feasible_pareto_ratio",
    "best_reevaluated_feasible_security_return",
    "num_runs_with_reevaluated_feasible_candidate",
    "closest_candidate_margin",
]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _resolve_repo_path(raw_path: str | Path) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return (_repo_root() / path).resolve()


def _analysis_root() -> Path:
    return ensure_dir(_resolve_repo_path("cmorl_cyborg/outputs/adacs_dcs_ablation"))


def _aggregated_root() -> Path:
    return ensure_dir(_analysis_root() / "aggregated")


def _set_compare_root() -> Path:
    return ensure_dir(_analysis_root() / "set_value_compare")


def _buffer_path(method_name: str, seed: int) -> Path:
    if method_name == "ours_stage2_fair":
        config_path = _resolve_repo_path("cmorl_cyborg/configs/paper/compare_suite_main.yaml")
        import yaml

        payload = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        for entry in payload.get("entries", []):
            if str(entry.get("method_name")) != "ours_stage2":
                continue
            if int(entry.get("seed", -1)) != int(seed):
                continue
            raw_path = entry.get("artifact_path")
            if not raw_path:
                raise ValueError(
                    f"Missing artifact_path for ours_stage2 seed {seed} in {config_path}"
                )
            return _resolve_repo_path(raw_path)
    return _resolve_repo_path(
        f"cmorl_cyborg/outputs/fair_compare_eval_inputs/{method_name}/seed_{seed:04d}/solution_buffer.json"
    )


def _tight_metrics_path(method_name: str, seed: int) -> Path:
    return _resolve_repo_path(
        f"cmorl_cyborg/outputs/fair_compare_eval/tight/{method_name}/seed_{seed:04d}/constraint_metrics.json"
    )


def _seed_summary_path(method_name: str, seed: int) -> Path:
    return _resolve_repo_path(
        f"cmorl_cyborg/outputs/fair_compare_eval/reevaluated_tight_feasible_set_summary/{method_name}/seed_{seed:04d}.json"
    )


def _method_spec(method_name: str) -> dict[str, str]:
    for spec in METHOD_SPECS:
        if spec["method_name"] == method_name:
            return spec
    raise ValueError(f"Unknown method_name: {method_name}")


def _materialize_set_compare_config(seeds: tuple[int, ...]) -> Path:
    entries: list[dict[str, Any]] = []
    for spec in METHOD_SPECS:
        method_name = spec["method_name"]
        for seed in seeds:
            entries.append(
                {
                    "method_name": method_name,
                    "artifact_kind": "buffer",
                    "artifact_path": str(_buffer_path(method_name, seed).resolve()),
                    "display_group": spec["display_name"],
                    "seed": int(seed),
                }
            )
    payload = {
        "output_dir": str(_set_compare_root().resolve()),
        "entries": entries,
        "preference_step": 0.1,
        "reference_strategy": "data_min_range",
        "reference_margin": 0.25,
        "reference_point": [],
        "hv_max_exact_points": 18,
        "hv_mc_samples": 100000,
    }
    config_path = _analysis_root() / "adacs_dcs_ablation_compare_suite.yaml"
    import yaml

    config_path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return config_path


def _aggregate_selected_policy(method_name: str, seeds: tuple[int, ...]) -> Path:
    output_path = _aggregated_root() / f"{method_name}_tight.json"
    write_aggregated_constraint_metrics(
        [str(_tight_metrics_path(method_name, seed).resolve()) for seed in seeds],
        output_path,
        method_name=method_name,
    )
    return output_path.resolve()


def _aggregate_reevaluated_method(method_name: str, seeds: tuple[int, ...]) -> dict[str, Any]:
    spec = _method_spec(method_name)
    reevaluate_mod.DISPLAY_NAMES[method_name] = spec["display_name"]
    reevaluate_mod.COLORS[method_name] = spec["color"]
    seed_rows = [load_json(_seed_summary_path(method_name, seed)) for seed in seeds]
    return reevaluate_mod._aggregate_method_rows(method_name, seed_rows)


def _write_csv(path: Path, header: list[str], rows: list[list[Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)
    return path.resolve()


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    if value != value:
        return None
    return value


def _delta(mean_a: float | None, mean_b: float | None) -> float | None:
    if mean_a is None or mean_b is None:
        return None
    return float(mean_a) - float(mean_b)


def run_ablation_compare(*, seeds: tuple[int, ...]) -> dict[str, Any]:
    seed_order = tuple(dict.fromkeys(int(seed) for seed in seeds))
    config_path = _materialize_set_compare_config(seed_order)
    set_compare_summary_path = Path(compare_suite(config_path)).resolve()
    set_compare_figure = _analysis_root() / "adacs_dcs_ablation_set_quality.png"
    plot_main_table_a(
        set_compare_summary_path,
        output_path=set_compare_figure,
        title="AdaCS/DCS 2x2 Ablation: Set Quality",
    )

    selected_aggregate_paths = [
        _aggregate_selected_policy(spec["method_name"], seed_order) for spec in METHOD_SPECS
    ]
    deployment_figure = _analysis_root() / "adacs_dcs_ablation_deployment.png"
    plot_fair_compare_table_b(
        aggregated_paths=[str(path) for path in selected_aggregate_paths],
        output_path=deployment_figure,
        title="AdaCS/DCS 2x2 Ablation: Tight Selected-Policy Deployment",
        label_map={spec["method_name"]: spec["display_name"] for spec in METHOD_SPECS},
    )

    reevaluated_rows = [
        _aggregate_reevaluated_method(spec["method_name"], seed_order) for spec in METHOD_SPECS
    ]
    tight_feasible_figure = _analysis_root() / "adacs_dcs_ablation_tight_feasible.png"
    reevaluate_mod._plot_reevaluated_tight_feasible_set(reevaluated_rows, tight_feasible_figure)
    tight_feasible_json = _analysis_root() / "adacs_dcs_ablation_tight_feasible.json"
    save_json(
        tight_feasible_json,
        {
            "methods": reevaluated_rows,
            "thresholds": load_json(_resolve_repo_path("cmorl_cyborg/outputs/fair_compare_eval/thresholds_tight.json")),
            "seeds": list(seed_order),
        },
    )

    set_compare_payload = load_json(set_compare_summary_path)
    set_rows = {
        str(row["method_name"]): row for row in set_compare_payload.get("method_summary", [])
    }
    deployment_rows = {
        str(load_json(path).get("method_name")): load_json(path) for path in selected_aggregate_paths
    }
    tight_rows = {str(row["method_name"]): row for row in reevaluated_rows}

    set_csv_rows: list[list[Any]] = []
    deployment_csv_rows: list[list[Any]] = []
    tight_csv_rows: list[list[Any]] = []

    for spec in METHOD_SPECS:
        method_name = spec["method_name"]
        set_row = set_rows[method_name]
        deployment_row = deployment_rows[method_name]
        tight_row = tight_rows[method_name]

        set_csv_rows.append(
            [
                spec["display_name"],
                method_name,
                *[
                    set_row.get(metric, {}).get("mean")
                    for metric in SET_METRICS
                ],
                *[
                    set_row.get(metric, {}).get("std")
                    for metric in SET_METRICS
                ],
            ]
        )
        deployment_csv_rows.append(
            [
                spec["display_name"],
                method_name,
                *[deployment_row.get(metric) for metric in DEPLOYMENT_METRICS],
                *[deployment_row.get(f"{metric}_std") for metric in DEPLOYMENT_METRICS],
            ]
        )
        tight_csv_rows.append(
            [
                spec["display_name"],
                method_name,
                *[tight_row.get(metric) for metric in TIGHT_FEASIBLE_METRICS],
                *[tight_row.get(f"{metric}_std") for metric in TIGHT_FEASIBLE_METRICS[:-2]],
            ]
        )

    set_csv_path = _write_csv(
        _analysis_root() / "adacs_dcs_ablation_set_quality.csv",
        ["display_name", "method_name"]
        + [f"{metric}_mean" for metric in SET_METRICS]
        + [f"{metric}_std" for metric in SET_METRICS],
        set_csv_rows,
    )
    deployment_csv_path = _write_csv(
        _analysis_root() / "adacs_dcs_ablation_deployment.csv",
        ["display_name", "method_name"]
        + DEPLOYMENT_METRICS
        + [f"{metric}_std" for metric in DEPLOYMENT_METRICS],
        deployment_csv_rows,
    )
    tight_csv_path = _write_csv(
        _analysis_root() / "adacs_dcs_ablation_tight_feasible.csv",
        ["display_name", "method_name"]
        + TIGHT_FEASIBLE_METRICS
        + [f"{metric}_std" for metric in TIGHT_FEASIBLE_METRICS[:-2]],
        tight_csv_rows,
    )

    original = set_rows["original_stage2_fair"]
    adacs_only = set_rows["adaptive_fixed_stage2_fair"]
    dcs_only = set_rows["crowding_dynamic_stage2_fair"]
    full = set_rows["ours_stage2_fair"]

    summary = {
        "seeds": list(seed_order),
        "set_compare_summary_path": str(set_compare_summary_path),
        "set_compare_figure": str(set_compare_figure.resolve()),
        "deployment_figure": str(deployment_figure.resolve()),
        "tight_feasible_figure": str(tight_feasible_figure.resolve()),
        "set_quality_csv": str(set_csv_path),
        "deployment_csv": str(deployment_csv_path),
        "tight_feasible_csv": str(tight_csv_path),
        "tight_feasible_json": str(tight_feasible_json.resolve()),
        "marginal_effects": {
            "adacs_at_fixed_beta": {
                metric: _delta(
                    _float_or_none(adacs_only.get(metric, {}).get("mean")),
                    _float_or_none(original.get(metric, {}).get("mean")),
                )
                for metric in SET_METRICS
            },
            "dcs_at_crowding": {
                metric: _delta(
                    _float_or_none(dcs_only.get(metric, {}).get("mean")),
                    _float_or_none(original.get(metric, {}).get("mean")),
                )
                for metric in SET_METRICS
            },
            "full_vs_original": {
                metric: _delta(
                    _float_or_none(full.get(metric, {}).get("mean")),
                    _float_or_none(original.get(metric, {}).get("mean")),
                )
                for metric in SET_METRICS
            },
        },
    }
    summary_path = _analysis_root() / "adacs_dcs_ablation_summary.json"
    save_json(summary_path, summary)
    return {"summary_path": str(summary_path.resolve()), **summary}


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate the full AdaCS/DCS 2x2 ablation results.")
    parser.add_argument("--seeds", nargs="+", type=int, default=list(SEEDS))
    args = parser.parse_args()

    outputs = run_ablation_compare(seeds=tuple(int(seed) for seed in args.seeds))
    for key, value in outputs.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
