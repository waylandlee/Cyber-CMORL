from __future__ import annotations

import cmorl_minicage.compare_suite as base
import cmorl_minicage.evaluate as evaluate_base
import cmorl_minicage.evaluate_conditioned as conditioned_base

from .config import load_compare_suite_config
from .env import CybORGMORLEnv

base.load_compare_suite_config = load_compare_suite_config
evaluate_base.MiniCageMORLEnv = CybORGMORLEnv
conditioned_base.MiniCageMORLEnv = CybORGMORLEnv
compare_suite = base.compare_suite


def main() -> None:
    base.main()


if __name__ == "__main__":
    main()
