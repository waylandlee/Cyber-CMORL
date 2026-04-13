from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

import numpy as np

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cmorl_minicage.algorithms.dual_archive import normalized_archive_sets
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
    source_set: str = "union",
    selector_mode: str = "plain",
    penalty_weights: dict[str, float] | None = None,
    strict_require_tight: bool = False,
) -> dict:
    payload = load_policy_buffer(buffer_path)
    archive_sets = normalized_archive_sets(
        payload,
        buffer_path=buffer_path,
        semantic_eval_episodes=int(
            payload.get("metadata", {}).get("evaluation", {}).get("eval_episodes", 1)
        ),
    )
    policy_set = _policy_set_from_payload(payload, source_set, archive_sets=archive_sets)
    if not policy_set:
        raise ValueError(f"No policies found in source_set={source_set}")

    if penalty_weights is None:
        penalty_weights = (
            payload.get("metadata", {})
            .get("selector_defaults", {})
            .get("penalty_weights", None)
        )
    selected = assign_policy(
        preference,
        policy_set,
        mode=selector_mode,
        penalty_weights=penalty_weights,
        source_set=source_set,
        strict_policy_set=_policy_set_from_payload(payload, "cons", archive_sets=archive_sets),
        require_tight=strict_require_tight,
    )
    if selected.get("checkpoint_path"):
        selected["checkpoint_path_resolved"] = str(
            _resolve_checkpoint_path(buffer_path, selected["checkpoint_path"])
        )
    else:
        selected["checkpoint_path_resolved"] = None
    selected["source_set"] = source_set
    selected["selector_mode_requested"] = selector_mode
    selected["strict_require_tight"] = bool(strict_require_tight)
    return selected


def _dedupe_by_policy_id(records: Sequence[dict]) -> list[dict]:
    by_id: dict[str, dict] = {}
    for record in records:
        by_id.setdefault(str(record["policy_id"]), dict(record))
    return list(by_id.values())


def _policy_set_from_payload(
    payload: dict,
    source_set: str,
    *,
    archive_sets: dict | None = None,
) -> list[dict]:
    if archive_sets is not None:
        if source_set == "pareto":
            return list(archive_sets["pareto"])
        if source_set == "records":
            return list(archive_sets["records"])
        if source_set == "cons":
            return list(archive_sets["cons"])
        if source_set == "uc":
            return list(archive_sets["uc"])
        if source_set == "union":
            return list(archive_sets["union"])
    if source_set == "pareto":
        return list(payload.get("pareto_front", []))
    if source_set == "records":
        return list(payload.get("records", []))
    if source_set == "cons":
        return list(payload.get("cons_records", []))
    if source_set == "uc":
        return list(payload.get("uc_records", []))
    if source_set == "union":
        cons_records = list(payload.get("cons_records", []))
        uc_records = list(payload.get("uc_records", []))
        if cons_records or uc_records:
            return _dedupe_by_policy_id([*cons_records, *uc_records])
        union_front = list(payload.get("union_front", []))
        if union_front:
            return union_front
        pareto_front = list(payload.get("pareto_front", []))
        if pareto_front:
            return pareto_front
        return list(payload.get("records", []))
    raise ValueError(f"Unsupported source_set: {source_set}")


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
        choices=("cons", "uc", "union", "pareto", "records"),
        default="union",
        help="Select from a saved policy set.",
    )
    parser.add_argument(
        "--selector-mode",
        choices=("plain", "strict", "hybrid"),
        default="plain",
        help="Policy selector mode.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the selected result as JSON.",
    )
    parser.add_argument(
        "--strict-require-tight",
        action="store_true",
        help="Require tight feasible candidates for strict selection.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    preference = _parse_preference(args.preference)
    selected = select_policy(
        args.buffer_path,
        preference,
        source_set=args.source_set,
        selector_mode=args.selector_mode,
        strict_require_tight=args.strict_require_tight,
    )

    if args.json:
        print(json.dumps(selected, indent=2))
        return

    print(f"source_set: {selected['source_set']}")
    print(f"selector_mode: {selected['selector_mode']}")
    print(f"selector_mode_requested: {selected['selector_mode_requested']}")
    print(f"preference: {selected['preference']}")
    if selected.get("policy_id") is None:
        print("selection_status: miss")
        print(f"miss_reason: {selected.get('miss_reason')}")
        print(f"strict_hit: {selected.get('strict_hit')}")
        print(f"fallback_used: {selected.get('fallback_used')}")
        return
    print(f"policy_id: {selected['policy_id']}")
    print(f"objective_vector: {selected['objective_vector']}")
    print(f"utility: {selected['utility']:.6f}")
    if selected.get("penalized_utility") is not None:
        print(f"penalized_utility: {selected['penalized_utility']:.6f}")
    print(f"strict_hit: {selected.get('strict_hit')}")
    print(f"fallback_used: {selected.get('fallback_used')}")
    if selected.get("score_breakdown"):
        print(f"score_breakdown: {selected['score_breakdown']}")
    print(f"checkpoint_path: {selected['checkpoint_path']}")
    print(f"checkpoint_path_resolved: {selected['checkpoint_path_resolved']}")
    print(f"stage: {selected.get('stage')}")
    print(f"source: {selected.get('source')}")


if __name__ == "__main__":
    main()
