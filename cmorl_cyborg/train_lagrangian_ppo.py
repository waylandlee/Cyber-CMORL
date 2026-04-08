from __future__ import annotations

import argparse

import cmorl_minicage.train_lagrangian_ppo as base
import cmorl_minicage.evaluate_constraints as constraints_base

from .config import DEFAULT_LAGRANGIAN_PPO_CONFIG, load_lagrangian_ppo_config
from .env import CybORGMORLEnv

base.MiniCageMORLEnv = CybORGMORLEnv
constraints_base.MiniCageMORLEnv = CybORGMORLEnv
train_lagrangian_ppo = base.train_lagrangian_ppo


def main() -> None:
    parser = argparse.ArgumentParser(description="Train Lagrangian PPO on formal CybORG.")
    parser.add_argument("--config", default=str(DEFAULT_LAGRANGIAN_PPO_CONFIG))
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()

    config = load_lagrangian_ppo_config(args.config)
    if args.output_dir is not None:
        config.output_dir = args.output_dir
    metadata_path = train_lagrangian_ppo(config)
    print(metadata_path)


if __name__ == "__main__":
    main()
