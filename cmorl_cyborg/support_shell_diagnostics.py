from __future__ import annotations

import argparse

import cmorl_minicage.support_shell_diagnostics as base

from .config import (
    DEFAULT_SUPPORT_SHELL_DIAGNOSTICS_CONFIG,
    load_support_shell_diagnostics_config,
)

run_support_shell_diagnostics = base.run_support_shell_diagnostics


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run support-aware shell diagnostics on CybORG replay candidate caches."
    )
    parser.add_argument("--config", default=str(DEFAULT_SUPPORT_SHELL_DIAGNOSTICS_CONFIG))
    parser.add_argument("--assignment-summary-path", default=None)
    parser.add_argument("--candidate-cache-path", default=None)
    parser.add_argument("--thresholds-path", default=None)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--run-label", default=None)
    args = parser.parse_args()

    config = load_support_shell_diagnostics_config(args.config)
    if args.assignment_summary_path is not None:
        config.assignment_summary_path = args.assignment_summary_path
    if args.candidate_cache_path is not None:
        config.candidate_cache_path = args.candidate_cache_path
    if args.thresholds_path is not None:
        config.thresholds_path = args.thresholds_path
    if args.output_dir is not None:
        config.output_dir = args.output_dir
    if args.run_label is not None:
        config.run_label = args.run_label
    outputs = run_support_shell_diagnostics(config, config_anchor=args.config)
    print(outputs["summary_path"])


if __name__ == "__main__":
    main()
