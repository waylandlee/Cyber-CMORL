from __future__ import annotations

import argparse

import cmorl_minicage.evaluate as base

from .config import DEFAULT_EVALUATE_CONFIG, load_evaluate_config
from .env import CybORGMORLEnv
from cmorl_minicage.utils import save_json

base.MiniCageMORLEnv = CybORGMORLEnv
evaluate_policy_buffer = base.evaluate_policy_buffer


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate a CybORG policy buffer.")
    parser.add_argument("--config", default=str(DEFAULT_EVALUATE_CONFIG))
    parser.add_argument("--buffer-path", default=None)
    parser.add_argument("--output-path", default=None)
    args = parser.parse_args()

    config = load_evaluate_config(args.config)
    buffer_path = args.buffer_path or config.buffer_path
    if not buffer_path:
        raise ValueError("buffer_path must be provided via config or --buffer-path")
    output_path = args.output_path or config.output_path
    payload = evaluate_policy_buffer(
        buffer_path,
        config.preference_step,
        reference_strategy=config.reference_strategy,
        reference_margin=config.reference_margin,
        reference_point=config.reference_point,
        hv_max_exact_points=config.hv_max_exact_points,
        hv_mc_samples=config.hv_mc_samples,
    )
    if output_path:
        save_json(output_path, payload)
        print(output_path)
    else:
        print(payload)


if __name__ == "__main__":
    main()
