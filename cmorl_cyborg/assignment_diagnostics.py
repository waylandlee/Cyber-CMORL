from __future__ import annotations

import argparse

import cmorl_minicage.assignment_diagnostics as base
import cmorl_minicage.evaluate_constraints as constraint_base

from .config import (
    DEFAULT_ASSIGNMENT_DIAGNOSTICS_CONFIG,
    load_assignment_diagnostics_config,
)
from .env import CybORGMORLEnv

constraint_base.MiniCageMORLEnv = CybORGMORLEnv
base.constraint_eval.MiniCageMORLEnv = CybORGMORLEnv

run_assignment_diagnostics = base.run_assignment_diagnostics
load_candidate_semantics_jsonl = base.load_candidate_semantics_jsonl
diagnose_assignment_problem = base.diagnose_assignment_problem


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run replay-only assignment diagnostics on CybORG buffers."
    )
    parser.add_argument(
        "--config",
        default=str(DEFAULT_ASSIGNMENT_DIAGNOSTICS_CONFIG),
    )
    parser.add_argument("--buffer-path", default=None)
    parser.add_argument("--thresholds-path", default=None)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--run-label", default=None)
    parser.add_argument("--source-set", choices=("pareto", "records"), default=None)
    args = parser.parse_args()

    config = load_assignment_diagnostics_config(args.config)
    if args.buffer_path is not None:
        config.buffer_path = args.buffer_path
    if args.thresholds_path is not None:
        config.thresholds_path = args.thresholds_path
    if args.output_dir is not None:
        config.output_dir = args.output_dir
    if args.run_label is not None:
        config.run_label = args.run_label
    if args.source_set is not None:
        config.source_set = args.source_set
    outputs = run_assignment_diagnostics(config, config_anchor=args.config)
    print(outputs["summary_path"])


if __name__ == "__main__":
    main()
