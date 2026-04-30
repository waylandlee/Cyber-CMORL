from __future__ import annotations

import argparse
from pathlib import Path

import cmorl_minicage.evaluate_conditioned as base

from cmorl_minicage.utils import save_json

from .config import (
    DEFAULT_CONDITIONED_EVALUATE_CONFIG,
    load_conditioned_evaluate_config,
)
from .env import CybORGMORLEnv

base.MiniCageMORLEnv = CybORGMORLEnv


def _build_cyborg_env_from_metadata(metadata: dict[str, object]) -> CybORGMORLEnv:
    env_config = dict(metadata.get("env", {})) if isinstance(metadata, dict) else {}
    model_config = dict(metadata.get("model", {})) if isinstance(metadata, dict) else {}
    shield_config = dict(metadata.get("shield", {})) if isinstance(metadata, dict) else {}
    return CybORGMORLEnv(
        num_envs=int(env_config.get("num_envs", 8)),
        red_policy=str(env_config.get("red_policy", "bline")),
        remove_bugs=bool(env_config.get("remove_bugs", True)),
        max_steps=int(env_config.get("max_episode_steps", 100)),
        seed=int(env_config.get("seed", 7)),
        scenario_name=str(env_config.get("scenario_name", "Scenario2")),
        scenario_profile=str(env_config.get("scenario_profile", "")),
        gym_wrapper_name=str(env_config.get("gym_wrapper_name", "ChallengeWrapper")),
        blue_agent_name=str(env_config.get("blue_agent_name", "Blue")),
        red_agent_name=str(env_config.get("red_agent_name", "Red")),
        obs_mode=str(env_config.get("obs_mode", "vector")),
        state_mode=str(env_config.get("state_mode", "true")),
        obj_dim=int(model_config.get("obj_dim", 3)),
        critical_host_safety_mode=str(
            model_config.get("critical_host_safety_mode", "v2_legacy")
        ),
        shield_mode=str(shield_config.get("mode", "disabled")),
    )


base._build_env = _build_cyborg_env_from_metadata


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

    output_dir = Path(
        args.output_dir
        or config.output_path
        or Path(config.input_path).resolve().parent
    )
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
