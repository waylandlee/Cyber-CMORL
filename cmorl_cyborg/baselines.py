from __future__ import annotations

import cmorl_minicage.baselines as base

from .config import (
    DEFAULT_EVALUATE_CONFIG,
    DEFAULT_STAGE1_CONFIG,
    load_evaluate_config,
    load_stage1_config,
)
from .env import CybORGMORLEnv
from .train_stage1 import train_stage1

import cmorl_minicage.evaluate as evaluate_base
import cmorl_minicage.train_stage1 as stage1_base

stage1_base.MiniCageMORLEnv = CybORGMORLEnv
evaluate_base.MiniCageMORLEnv = CybORGMORLEnv
base.MiniCageMORLEnv = CybORGMORLEnv
base.DEFAULT_STAGE1_CONFIG = DEFAULT_STAGE1_CONFIG
base.DEFAULT_EVALUATE_CONFIG = DEFAULT_EVALUATE_CONFIG
base.load_stage1_config = load_stage1_config
base.load_evaluate_config = load_evaluate_config
base.train_stage1 = train_stage1


def main() -> None:
    base.main()


if __name__ == "__main__":
    main()
