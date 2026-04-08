from __future__ import annotations

import argparse
from pathlib import Path

import cmorl_minicage.evaluate_conditioned as base

from .config import DEFAULT_CONDITIONED_EVALUATE_CONFIG, load_conditioned_evaluate_config
from .env import CybORGMORLEnv
from cmorl_minicage.utils import save_json

base.MiniCageMORLEnv = CybORGMORLEnv


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate conditioned CybORG policies on the preference grid."
    )
    parser.add_argument("--config", default=str(DEFAULT_CONDITIONED_EVALUATE_CONFIG))
    parser.add_argument("--input-path", default=None)
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()

    config = load_conditioned_evaluate_config(args.config)
    if args.input_path is not None:
        config.input_path = args.input_path
    if not config.input_path:
        raise ValueError("input_path must be provided")

    evaluated_payload, metrics_payload = base.evaluate_conditioned_model(
        config.input_path,
        preference_step=config.preference_step,
        reference_strategy=config.reference_strategy,
        reference_margin=config.reference_margin,
        reference_point=config.reference_point,
        hv_max_exact_points=config.hv_max_exact_points,
        hv_mc_samples=config.hv_mc_samples,
        eval_episodes=config.eval_episodes,
    )

    output_dir = Path(args.output_dir or config.output_path or Path(config.input_path).resolve().parent)
    output_dir.mkdir(parents=True, exist_ok=True)
    evaluated_path = output_dir / "evaluated_points.json"
    pareto_path = output_dir / "pareto_front_conditioned.json"
    metrics_path = output_dir / "metrics.json"
    pareto_front = evaluated_payload.get("pareto_front")
    if pareto_front is None:
        pareto_front = metrics_payload.get("pareto_front", [])
    save_json(evaluated_path, evaluated_payload)
    save_json(pareto_path, pareto_front)
    save_json(metrics_path, metrics_payload)
    print(metrics_path)


if __name__ == "__main__":
    main()
