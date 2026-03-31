from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

import numpy as np

from cmorl_minicage.algorithms.assignment import assign_policy
from cmorl_minicage.buffer import load_policy_buffer


def _repo_root_from_path(path: str | Path) -> Path:
    path = Path(path).resolve()
    for candidate in (path, *path.parents):
        if (candidate / "cmorl_minicage").exists():
            return candidate
    raise ValueError(f"Could not infer repository root from {path}")


def _resolve_checkpoint_path(buffer_path: str | Path, checkpoint_path: str | Path) -> Path:
    checkpoint = Path(checkpoint_path)
    if checkpoint.is_absolute():
        return checkpoint
    return (_repo_root_from_path(buffer_path) / checkpoint).resolve()


def _parse_preference(raw_values: Sequence[str]) -> list[float]:
    if not raw_values:
        raise ValueError("At least one preference value is required")

    if len(raw_values) == 1 and "," in raw_values[0]:
        values = [part.strip() for part in raw_values[0].split(",") if part.strip()]
    else:
        values = list(raw_values)
    preference = [float(value) for value in values]
    if any(value < 0 for value in preference):
        raise ValueError("Preference values must be non-negative")
    total = float(sum(preference))
    if total <= 0:
        raise ValueError("Preference values must sum to a positive number")
    return [value / total for value in preference]


def select_policy(
    buffer_path: str | Path,
    preference: Sequence[float],
    *,
    source_set: str = "pareto",
) -> dict:
    payload = load_policy_buffer(buffer_path)
    if source_set == "pareto":
        policy_set = payload.get("pareto_front", [])
    elif source_set == "records":
        policy_set = payload.get("records", [])
    else:
        raise ValueError(f"Unsupported source_set: {source_set}")
    if not policy_set:
        raise ValueError(f"No policies found in source_set={source_set}")

    selected = assign_policy(preference, policy_set)
    selected["checkpoint_path_resolved"] = str(
        _resolve_checkpoint_path(buffer_path, selected["checkpoint_path"])
    )
    selected["source_set"] = source_set
    return selected


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Select the best available policy for a given preference vector."
    )
    parser.add_argument(
        "--buffer-path",
        type=Path,
        required=True,
        help="Path to solution_buffer.json",
    )
    parser.add_argument(
        "--preference",
        nargs="+",
        required=True,
        help="Preference vector, e.g. --preference 0.7 0.2 0.1 or --preference 0.7,0.2,0.1",
    )
    parser.add_argument(
        "--source-set",
        choices=("pareto", "records"),
        default="pareto",
        help="Select only from final Pareto front or from all saved records.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the selected result as JSON.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    preference = _parse_preference(args.preference)
    selected = select_policy(args.buffer_path, preference, source_set=args.source_set)

    if args.json:
        print(json.dumps(selected, indent=2))
        return

    print(f"source_set: {selected['source_set']}")
    print(f"preference: {selected['preference']}")
    print(f"policy_id: {selected['policy_id']}")
    print(f"objective_vector: {selected['objective_vector']}")
    print(f"utility: {selected['utility']:.6f}")
    print(f"checkpoint_path: {selected['checkpoint_path']}")
    print(f"checkpoint_path_resolved: {selected['checkpoint_path_resolved']}")
    print(f"stage: {selected.get('stage')}")
    print(f"source: {selected.get('source')}")


if __name__ == "__main__":
    main()
