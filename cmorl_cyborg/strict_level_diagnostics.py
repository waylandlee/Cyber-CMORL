from __future__ import annotations

import argparse

import cmorl_minicage.strict_level_diagnostics as base

from .config import (
    DEFAULT_STRICT_LEVEL_DIAGNOSTICS_CONFIG,
    load_strict_level_diagnostics_config,
)

run_strict_level_diagnostics = base.run_strict_level_diagnostics
load_candidate_cache = base.load_candidate_cache


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run offline strict-level diagnostics on CybORG candidate caches."
    )
    parser.add_argument(
        "--config",
        default=str(DEFAULT_STRICT_LEVEL_DIAGNOSTICS_CONFIG),
    )
    parser.add_argument("--candidate-cache-path", default=None)
    parser.add_argument("--thresholds-path", default=None)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--run-label", default=None)
    args = parser.parse_args()

    config = load_strict_level_diagnostics_config(args.config)
    if args.candidate_cache_path is not None:
        config.candidate_cache_path = args.candidate_cache_path
    if args.thresholds_path is not None:
        config.thresholds_path = args.thresholds_path
    if args.output_dir is not None:
        config.output_dir = args.output_dir
    if args.run_label is not None:
        config.run_label = args.run_label
    outputs = run_strict_level_diagnostics(config, config_anchor=args.config)
    print(outputs["summary_path"])


if __name__ == "__main__":
    main()
