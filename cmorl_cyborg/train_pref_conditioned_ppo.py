from __future__ import annotations

import argparse

import cmorl_minicage.train_pref_conditioned_ppo as base

from .config import DEFAULT_PREFERENCE_CONDITIONED_PPO_CONFIG, load_preference_conditioned_ppo_config
from .env import CybORGMORLEnv

base.MiniCageMORLEnv = CybORGMORLEnv
train_preference_conditioned_ppo = base.train_preference_conditioned_ppo


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Train a preference-conditioned PPO policy on formal CybORG."
    )
    parser.add_argument("--config", default=str(DEFAULT_PREFERENCE_CONDITIONED_PPO_CONFIG))
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()

    config = load_preference_conditioned_ppo_config(args.config)
    if args.output_dir is not None:
        config.output_dir = args.output_dir
    metadata_path = train_preference_conditioned_ppo(config)
    print(metadata_path)


if __name__ == "__main__":
    main()
