from __future__ import annotations

import argparse

import cmorl_minicage.train_stage2 as base

from .config import DEFAULT_STAGE2_CONFIG, load_stage2_config
from .env import CybORGMORLEnv

base.MiniCageMORLEnv = CybORGMORLEnv

train_stage2 = base.train_stage2


def main() -> None:
    parser = argparse.ArgumentParser(description="Train Stage-2 on formal CybORG.")
    parser.add_argument("--config", default=str(DEFAULT_STAGE2_CONFIG))
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()

    config = load_stage2_config(args.config)
    if args.output_dir is not None:
        config.output_dir = args.output_dir
    output_path = train_stage2(config)
    print(output_path)


if __name__ == "__main__":
    main()
