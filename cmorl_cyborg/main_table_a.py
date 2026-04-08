from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
import os
from pathlib import Path
from typing import Any

import yaml

from .compare_suite import compare_suite
import cmorl_minicage.evaluate_conditioned as conditioned_base
from .env import CybORGMORLEnv
from cmorl_minicage.utils import save_json

conditioned_base.MiniCageMORLEnv = CybORGMORLEnv


def _repo_root_from_path(path: str | Path) -> Path:
    path = Path(path).resolve()
    for candidate in (path, *path.parents):
        if (candidate / "cmorl_cyborg").exists():
            return candidate
    raise ValueError(f"Could not infer repository root from {path}")


def _resolve_path(anchor: str | Path, raw_path: str | Path) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return (_repo_root_from_path(anchor) / path).resolve()


def _resolve_unique_glob(anchor: str | Path, pattern: str) -> Path:
    pattern_path = _resolve_path(anchor, pattern)
    if pattern_path.is_absolute():
        matches = sorted(Path("/").glob(str(pattern_path)[1:]))
    else:
        matches = sorted(Path(".").glob(str(pattern_path)))
    if len(matches) != 1:
        raise ValueError(
            f"Expected exactly one match for {pattern!r}, found {len(matches)}: {matches}"
        )
    return matches[0].resolve()


def _resolve_source_path(anchor: str | Path, entry: dict[str, Any], key: str) -> Path:
    raw_path = entry.get(key)
    raw_glob = entry.get(f"{key}_glob")
    if raw_path:
        return _resolve_path(anchor, raw_path)
    if raw_glob:
        return _resolve_unique_glob(anchor, raw_glob)
    raise ValueError(f"Entry must provide {key} or {key}_glob")


def _load_yaml_config(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"Config file must contain a mapping: {path}")
    return payload


def _materialize_conditioned_entry(
    *,
    anchor: Path,
    entry: dict[str, Any],
    output_dir: Path,
    preference_step: float | None,
    reference_strategy: str,
    reference_margin: float,
    reference_point: list[float],
    hv_max_exact_points: int,
    hv_mc_samples: int,
    default_eval_episodes: int,
    preference_eval_workers: int,
) -> dict[str, Any]:
    method_name = str(entry["method_name"])
    seed = int(entry["seed"])
    method_dir = output_dir / method_name / f"seed_{seed:04d}"
    method_dir.mkdir(parents=True, exist_ok=True)

    artifact_kind = str(entry["artifact_kind"])
    if artifact_kind == "conditioned_points":
        artifact_path = _resolve_source_path(anchor, entry, "artifact_path")
    elif artifact_kind == "conditioned_run_metadata":
        evaluated_points_path = method_dir / "evaluated_points.json"
        pareto_front_path = method_dir / "pareto_front_conditioned.json"
        metrics_path = method_dir / "metrics.json"
        reuse_existing = bool(entry.get("reuse_existing", True))
        if (
            reuse_existing
            and evaluated_points_path.exists()
            and pareto_front_path.exists()
            and metrics_path.exists()
        ):
            print(
                f"[main_table_a] REUSE conditioned method={method_name} seed={seed} "
                f"path={evaluated_points_path}",
                flush=True,
            )
            artifact_path = evaluated_points_path
        else:
            print(
                f"[main_table_a] START conditioned method={method_name} seed={seed}",
                flush=True,
            )
            input_path = _resolve_source_path(anchor, entry, "artifact_path")
            evaluated_payload, metrics_payload = conditioned_base.evaluate_conditioned_model(
                input_path,
                preference_step=entry.get("preference_step", preference_step),
                reference_strategy=entry.get("reference_strategy", reference_strategy),
                reference_margin=float(entry.get("reference_margin", reference_margin)),
                reference_point=entry.get("reference_point", reference_point),
                hv_max_exact_points=int(
                    entry.get("hv_max_exact_points", hv_max_exact_points)
                ),
                hv_mc_samples=int(entry.get("hv_mc_samples", hv_mc_samples)),
                eval_episodes=int(entry.get("eval_episodes", default_eval_episodes)),
                preference_eval_workers=int(
                    entry.get(
                        "preference_eval_workers",
                        os.environ.get("CMORL_CONDITIONED_PREF_WORKERS", "1"),
                    )
                ),
            )
            artifact_path = evaluated_points_path
            save_json(artifact_path, evaluated_payload)
            pareto_front = evaluated_payload.get(
                "pareto_front",
                metrics_payload.get("pareto_front", []),
            )
            save_json(pareto_front_path, pareto_front)
            save_json(metrics_path, metrics_payload)
            print(
                f"[main_table_a] DONE conditioned method={method_name} seed={seed} "
                f"records={len(evaluated_payload.get('evaluated_points', []))}",
                flush=True,
            )
    else:
        raise ValueError(f"Unsupported conditioned artifact_kind: {artifact_kind}")

    return {
        "method_name": method_name,
        "artifact_kind": "conditioned_points",
        "artifact_path": str(Path(artifact_path).resolve()),
        "display_group": entry.get("display_group", method_name),
        "seed": seed,
        "preference_step": entry.get("preference_step", preference_step),
        "reference_strategy": entry.get("reference_strategy", reference_strategy),
        "reference_margin": float(entry.get("reference_margin", reference_margin)),
        "reference_point": entry.get("reference_point", reference_point),
        "hv_max_exact_points": int(entry.get("hv_max_exact_points", hv_max_exact_points)),
        "hv_mc_samples": int(entry.get("hv_mc_samples", hv_mc_samples)),
    }


def _materialize_conditioned_entry_worker(task: dict[str, Any]) -> dict[str, Any]:
    return _materialize_conditioned_entry(**task)


def generate_main_table_a(config_path: str | Path) -> Path:
    config_path = Path(config_path).resolve()
    config = _load_yaml_config(config_path)
    entries = config.get("entries", [])
    if not entries:
        raise ValueError("entries must not be empty")

    output_dir = _resolve_path(config_path, config["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    conditioned_workers = int(
        config.get(
            "conditioned_eval_workers",
            os.environ.get("CMORL_CONDITIONED_EVAL_WORKERS", "1"),
        )
    )
    conditioned_workers = max(conditioned_workers, 1)
    preference_eval_workers = int(
        config.get(
            "preference_eval_workers",
            os.environ.get("CMORL_CONDITIONED_PREF_WORKERS", "1"),
        )
    )
    preference_eval_workers = max(preference_eval_workers, 1)

    print(
        f"[main_table_a] START output_dir={output_dir} "
        f"conditioned_entries={sum(1 for entry in entries if str(entry['artifact_kind']) != 'buffer')} "
        f"conditioned_eval_workers={conditioned_workers} "
        f"preference_eval_workers={preference_eval_workers}",
        flush=True,
    )

    materialized_entries: list[dict[str, Any] | None] = [None] * len(entries)
    conditioned_tasks: list[tuple[int, dict[str, Any]]] = []
    for index, entry in enumerate(entries):
        artifact_kind = str(entry["artifact_kind"])
        if artifact_kind == "buffer":
            artifact_path = _resolve_source_path(config_path, entry, "artifact_path")
            materialized_entries[index] = (
                {
                    "method_name": str(entry["method_name"]),
                    "artifact_kind": "buffer",
                    "artifact_path": str(artifact_path.resolve()),
                    "display_group": entry.get("display_group", entry["method_name"]),
                    "seed": int(entry["seed"]),
                }
            )
            continue
        conditioned_tasks.append(
            (
                index,
                {
                    "anchor": config_path,
                    "entry": entry,
                    "output_dir": output_dir,
                    "preference_step": config.get("preference_step"),
                    "reference_strategy": str(
                        config.get("reference_strategy", "data_min_range")
                    ),
                    "reference_margin": float(config.get("reference_margin", 0.25)),
                    "reference_point": list(config.get("reference_point", [])),
                    "hv_max_exact_points": int(config.get("hv_max_exact_points", 18)),
                    "hv_mc_samples": int(config.get("hv_mc_samples", 100000)),
                    "default_eval_episodes": int(config.get("eval_episodes", 3)),
                    "preference_eval_workers": preference_eval_workers,
                },
            )
        )

    if conditioned_workers == 1 or len(conditioned_tasks) <= 1:
        for index, task in conditioned_tasks:
            materialized_entries[index] = _materialize_conditioned_entry_worker(task)
    else:
        max_workers = min(conditioned_workers, len(conditioned_tasks))
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            for index, result in zip(
                [idx for idx, _ in conditioned_tasks],
                executor.map(
                    _materialize_conditioned_entry_worker,
                    [task for _, task in conditioned_tasks],
                ),
            ):
                materialized_entries[index] = result

    final_entries = [entry for entry in materialized_entries if entry is not None]

    materialized_config = {
        "output_dir": str(output_dir.resolve()),
        "entries": final_entries,
        "preference_step": config.get("preference_step", 0.1),
        "reference_strategy": config.get("reference_strategy", "data_min_range"),
        "reference_margin": config.get("reference_margin", 0.25),
        "reference_point": list(config.get("reference_point", [])),
        "hv_max_exact_points": int(config.get("hv_max_exact_points", 18)),
        "hv_mc_samples": int(config.get("hv_mc_samples", 100000)),
        "conditioned_eval_workers": conditioned_workers,
    }
    materialized_config_path = output_dir / "compare_suite_config.yaml"
    with materialized_config_path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(materialized_config, handle, sort_keys=False, allow_unicode=True)
    print(
        f"[main_table_a] MATERIALIZED compare_suite_config={materialized_config_path}",
        flush=True,
    )
    return compare_suite(materialized_config_path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate the formal Scenario2 main-table-A artifacts."
    )
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    summary_path = generate_main_table_a(args.config)
    print(summary_path)


if __name__ == "__main__":
    main()
