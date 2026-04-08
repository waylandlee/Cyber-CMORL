from __future__ import annotations

import argparse

import cmorl_minicage.train_pcn as base
import cmorl_minicage.datasets.trajectory_archive as archive_base

from .config import DEFAULT_PCN_CONFIG, load_pcn_config
from .env import CybORGMORLEnv

base.MiniCageMORLEnv = CybORGMORLEnv
archive_base.MiniCageMORLEnv = CybORGMORLEnv
train_pcn = base.train_pcn


def main() -> None:
    parser = argparse.ArgumentParser(description="Train PCN-lite on formal CybORG.")
    parser.add_argument("--config", default=str(DEFAULT_PCN_CONFIG))
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()

    config = load_pcn_config(args.config)
    if args.output_dir is not None:
        config.output_dir = args.output_dir
    metadata_path = train_pcn(config)
    print(metadata_path)


if __name__ == "__main__":
    main()
