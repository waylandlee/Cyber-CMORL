# Open Science Appendix Checklist

This file records which experiment outputs are currently reflected in the manuscript and which outputs remain artifact-only.

## Recorded In `paper/main.tex`

The following result blocks are already wired into [`main.tex`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/paper/main.tex):

- Table A from [`set_quality_table.tex`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/paper_table_a/set_quality_table.tex)
- Table B from [`deployment_table.tex`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/paper_table_b/deployment_table.tex)
- Figure C from [`preference_coverage.png`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/paper_figure_c/preference_coverage.png)
- Figure D from [`tight_feasible_set_quality.png`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/fair_compare_eval/aggregated/tight_feasible_set_quality.png)
- Appendix attacker-shift table from [`attacker_shift_summary.tex`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/paper_appendix/attacker_shift/attacker_shift_summary.tex)
- Appendix business/cost semantics table from [`business_cost_semantics.tex`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/paper_appendix/business_cost_semantics/business_cost_semantics.tex)
- Appendix business/cost semantics figure from [`business_cost_semantics.png`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/paper_appendix/business_cost_semantics/business_cost_semantics.png)

The paper also explicitly records the current seed protocol:

- three-seed default: `7, 11, 19`
- five-seed extension for key methods: `7, 11, 19, 23, 29`

## Result Blocks Reflected In Narrative Form

These outputs are not directly `\input`-ed, but they are already represented in the prose:

- [`table_a_summary.json`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/paper_table_a/table_a_summary.json)
- [`table_b_summary.json`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/paper_table_b/table_b_summary.json)
- [`tight_feasible_set_summary.json`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/fair_compare_eval/aggregated/tight_feasible_set_summary.json)
- [`business_cost_semantics.json`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/paper_appendix/business_cost_semantics/business_cost_semantics.json)
- [`attacker_shift_summary.json`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/paper_appendix/attacker_shift/attacker_shift_summary.json)

## Not Explicitly Recorded In `paper/main.tex`

The answer to “have all previous experiment results been recorded in the current manuscript?” is `not completely`.

What is already covered:

- all current main-paper result blocks
- the appendix stress test we promoted
- the appendix business/cost semantics results we promoted

What is not explicitly surfaced in the manuscript:

- raw progress logs such as [`paper_5seed_runner/runner.log`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/paper_5seed_runner/runner.log)
- live status files such as [`paper_5seed_runner/status.json`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/paper_5seed_runner/status.json)
- run manifests such as [`paper_5seed_runner/run_manifest.json`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/paper_5seed_runner/run_manifest.json)
- raw per-preference assignment dumps such as [`per_preference_assignment.csv`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/paper_figure_c/per_preference_assignment.csv)
- auxiliary machine-readable summaries such as the `.csv` and `.json` companions for the main tables
- exploratory or storage-only artifact directories under `cmorl_cyborg/outputs/` that are not part of the locked manuscript line

This is expected. The manuscript should record the canonical result blocks and their interpretations, not every intermediate or audit log.

## Current Gaps Worth Deciding Explicitly

These are the main remaining “do we want this in the paper?” decisions:

- whether to add a short appendix sentence pointing readers to the exact 5-seed manifest and logs
- whether to add one appendix sentence clarifying that Figure D still uses the fair-compare tight-threshold line rather than the full main-paper method set
- whether to add an appendix note that the attacker-shift result is a held-out evaluation without retraining

## Suggested Submission-Time Bundle

If we package a minimal anonymous artifact, the highest-value files to include are:

- [`ARTIFACT_README.md`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/paper/ARTIFACT_README.md)
- [`main.tex`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/paper/main.tex)
- [`refs.bib`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/paper/refs.bib)
- [`compare_suite_main.yaml`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/configs/paper/compare_suite_main.yaml)
- [`table_b_suite_main.yaml`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/configs/paper/table_b_suite_main.yaml)
- [`export_tables_main.yaml`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/configs/paper/export_tables_main.yaml)
- [`export_locked_tables.py`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/export_locked_tables.py)
- [`export_preference_coverage.py`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/export_preference_coverage.py)
- [`export_tight_feasible_set.py`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/export_tight_feasible_set.py)
- [`export_business_cost_semantics.py`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/export_business_cost_semantics.py)
- [`export_attacker_shift_summary.py`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/export_attacker_shift_summary.py)
- the canonical paper-facing outputs listed in [`ARTIFACT_README.md`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/paper/ARTIFACT_README.md)
