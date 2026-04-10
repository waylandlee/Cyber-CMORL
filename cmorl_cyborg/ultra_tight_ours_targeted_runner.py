from __future__ import annotations

from . import strong_tightplus_ours_fair_compare_runner as base


def main() -> None:
    base.DEFAULT_PILOT_SEEDS = (7, 11)
    base.DEFAULT_FULL_SEEDS = (7, 11)
    base.DEFAULT_CONSTRAINT_TOLERANCE = 0.0
    base.DEFAULT_CONSTRAINED_UPDATES = 10
    base.DEFAULT_BARRIER_COEF = 50.0
    base.DEFAULT_BETA_MIN = 1.004
    base.DEFAULT_BETA_MAX = 1.015

    base.METHOD_NAME = "ours_stage2_fair_ultratight"
    base.DISPLAY_NAME = "Ours Stage2 UltraTight"
    base.RUNNER_DIRNAME = "fair_compare_ultratight_runner"
    base.COMPARE_PLOT_NAME = "fair_compare_table_b_tight_with_ultratight_ours.png"
    base.SUMMARY_CSV_NAME = "reevaluated_tight_feasible_set_summary_with_ultratight_ours.csv"
    base.SUMMARY_JSON_NAME = "reevaluated_tight_feasible_set_summary_with_ultratight_ours.json"
    base.SUMMARY_FIGURE_NAME = "reevaluated_tight_feasible_set_quality_with_ultratight_ours.png"

    base.main()


if __name__ == "__main__":
    main()
