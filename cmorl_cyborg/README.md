# `cmorl_cyborg`

This package is the formal-environment migration line for C-MORL on `CybORG`.

It keeps `cmorl_minicage/` intact and provides a separate Blue-only, single-agent
entrypoint family for:

- `train_stage1`
- `train_stage2`
- `evaluate`
- `evaluate_conditioned`
- `evaluate_constraints`
- `baselines`
- `compare_suite`
- `export_tables`
- `rollout_smoke`

## Design Notes

- Environment access uses the local `Debugged_CybORG` package and the official
  `ChallengeWrapper` stack.
- The first version focuses on interface compatibility and artifact-schema
  continuity rather than reproducing MiniCAGE numbers.
- Reward and semantic statistics are now scenario-profile driven. The active
  profile is resolved from `env.scenario_profile` when provided, otherwise from
  `env.scenario_name`, using YAML files under `cmorl_cyborg/profiles/`.
- Reward and semantic statistics are reconstructed from wrapper outputs and true
  state snapshots. They remain working definitions and should still be
  recalibrated before any final formal CybORG claim.

## Current Status

As of `2026-04-08`, this package should be read as the active formal-results
line of the repository.

The current stable artifacts are centered on the `3-seed` protocol
(`7 / 11 / 19`) and include:

- `paper_table_b/aggregated/ours_stage2.json`
- `paper_table_b/main_table_b_bar.png`
- `fair_compare_eval/aggregated/fair_compare_table_b_tight_with_coverage.png`
- `fair_compare_eval/aggregated/fair_compare_table_b_loose_with_coverage.png`
- `fair_compare_eval/aggregated/coverage_combo_fair_loose.json`
- `fair_compare_eval/aggregated/coverage_more_parents_fair_loose.json`

The current reading of those results is:

- original `ours_stage2` remains the reference `paper_table_b` result;
- `coverage_combo_fair` improves security/business return and lowers mean
  violation under the `loose` fair-compare setting;
- but `coverage_combo_fair` also lowers feasible rate, so it should not be
  documented as a strict improvement over `ours_stage2`;
- `coverage_combo_fair` and `coverage_more_parents_fair` choose the same policy
  ids in the `loose` aggregation, so their difference is modest.

## Outputs

Use `cmorl_cyborg/outputs/` for all formal-environment runs so they stay
separate from the MiniCAGE outputs already tracked in this repository.
