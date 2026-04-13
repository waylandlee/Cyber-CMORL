from __future__ import annotations

import argparse
from pathlib import Path

import cmorl_minicage.evaluate as base

from .config import DEFAULT_EVALUATE_CONFIG, load_evaluate_config
from .env import CybORGMORLEnv
from cmorl_minicage.utils import save_json

base.MiniCageMORLEnv = CybORGMORLEnv
evaluate_policy_buffer = base.evaluate_policy_buffer
evaluate_policy_buffer_all_modes = base.evaluate_policy_buffer_all_modes


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate a CybORG policy buffer.")
    parser.add_argument("--config", default=str(DEFAULT_EVALUATE_CONFIG))
    parser.add_argument("--buffer-path", default=None)
    parser.add_argument("--output-path", default=None)
    parser.add_argument("--preference-step", type=float, default=None)
    parser.add_argument("--mode", choices=("union", "strict", "hybrid"), default=None)
    parser.add_argument("--strict-require-tight", action="store_true")
    args = parser.parse_args()

    config = load_evaluate_config(args.config)
    buffer_path = args.buffer_path or config.buffer_path
    if not buffer_path:
        raise ValueError("buffer_path must be provided via config or --buffer-path")
    if args.preference_step is not None:
        config.preference_step = args.preference_step
    if args.mode is not None:
        config.selector_mode = args.mode
    if args.strict_require_tight:
        config.strict_require_tight = True
    output_path = Path(args.output_path or config.output_path or Path(buffer_path).with_name("metrics.json"))
    results = evaluate_policy_buffer_all_modes(
        buffer_path,
        config.preference_step,
        penalty_weights=config.hybrid_penalty_weights,
        strict_require_tight=config.strict_require_tight,
        reference_strategy=config.reference_strategy,
        reference_margin=config.reference_margin,
        reference_point=config.reference_point,
        hv_max_exact_points=config.hv_max_exact_points,
        hv_mc_samples=config.hv_mc_samples,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    mode_paths = {
        "union": output_path.parent / "metrics_union.json",
        "strict": output_path.parent / "metrics_strict.json",
        "hybrid": output_path.parent / "metrics_hybrid.json",
    }
    for mode, payload in results.items():
        save_json(mode_paths[mode], payload)
    diagnostics_path = output_path.parent / "archive_diagnostics.json"
    save_json(
        diagnostics_path,
        base.archive_diagnostics_payload(
            buffer_path,
            strict_payload=results["strict"],
            hybrid_payload=results["hybrid"],
        ),
    )
    selected_mode = config.selector_mode if config.selector_mode in results else "union"
    save_json(output_path, results[selected_mode])
    if output_path.name != "metrics.json":
        save_json(output_path.parent / "metrics.json", results["union"])
    print(output_path)


if __name__ == "__main__":
    main()
