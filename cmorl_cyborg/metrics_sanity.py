from __future__ import annotations

import argparse

import cmorl_minicage.evaluate_constraints as constraint_base
import cmorl_minicage.metrics_sanity as base

from .config import DEFAULT_METRICS_SANITY_CONFIG, load_metrics_sanity_config
from .env import CybORGMORLEnv

constraint_base.MiniCageMORLEnv = CybORGMORLEnv
base._evaluate_actor_critic_record_detailed.__globals__["MiniCageMORLEnv"] = CybORGMORLEnv

run_metrics_sanity = base.run_metrics_sanity


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit replay metrics and semantics consistency on CybORG candidate caches."
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
