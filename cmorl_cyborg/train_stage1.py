from __future__ import annotations

import argparse

import cmorl_minicage.train_stage1 as base

from .config import DEFAULT_STAGE1_CONFIG, load_stage1_config
from .env import CybORGMORLEnv

base.MiniCageMORLEnv = CybORGMORLEnv

train_stage1 = base.train_stage1


def main() -> None:
    parser = argparse.ArgumentParser(description="Train Stage-1 on formal CybORG.")
    parser.add_argument("--config", default=str(DEFAULT_STAGE1_CONFIG))
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()

    config = load_stage1_config(args.config)
    if args.output_dir is not None:
        config.output_dir = args.output_dir
    output_path = train_stage1(config)
    print(output_path)


if __name__ == "__main__":
    main()
