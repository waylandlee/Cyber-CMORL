# Artifact README

This document fixes the current reproduction chain for the CybORG paper line in this repository.

## Scope

The current paper artifact is centered on:

- main-paper Table A: Set Quality Table
- main-paper Table B: Deployment Table
- main-paper Figure C: Preference Coverage
- main-paper Figure D: Tight Feasible Set Quality
- appendix attacker-shift table
- appendix business/cost semantics table and figure

The canonical paper source is [`main.tex`](/home/waylandlee/CMORL2/Cyber-CMORL/paper/main.tex).

## Interpretation Rule

The current manuscript uses two different comparison roles:

- `Table B` is the broad deployment comparison table across the fixed main-paper baseline set.
- The `ours` vs `no_constraint_stage2` causal ablation should be interpreted through the locked `fair_compare` line, where the constrained and unconstrained Stage-2 runs share the same Stage-2 budget and differ only in `extension_mode`.

This distinction is important because the main-paper `ours_stage2` and `no_constraint_stage2` artifacts are not the strict matched pair for causal interpretation, while the `fair_compare` artifacts are.

## Canonical Inputs

The current locked configs are:

- [`compare_suite_main.yaml`](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/configs/paper/compare_suite_main.yaml)
- [`table_b_suite_main.yaml`](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/configs/paper/table_b_suite_main.yaml)
- [`export_tables_main.yaml`](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/configs/paper/export_tables_main.yaml)

The locked matched ablation configs for `ours` vs `no_constraint_stage2` are:

- [`stage2_fair_constrained_seed_0007.yaml`](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/configs/paper/fair_compare/stage2_fair_constrained_seed_0007.yaml)
- [`stage2_fair_unconstrained_seed_0007.yaml`](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/configs/paper/fair_compare/stage2_fair_unconstrained_seed_0007.yaml)
- and the corresponding `0011` / `0019` fair-compare seed configs in the same directory

The current 5-seed runner artifacts are tracked in:

- [`status.json`](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_5seed_runner/status.json)
- [`run_manifest.json`](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_5seed_runner/run_manifest.json)

## Reproduction Root

Run all commands from:

```bash
cd /home/waylandlee/CMORL2/Cyber-CMORL
```

Use the same Python or conda environment that was used for the CybORG experiments. A bare system Python may fail on dependencies such as `PyYAML`, CybORG, or the MORL stack.

## Minimal Reproduction Chain

### 1. Optional: rerun the minimal 5-seed extension

This is only needed if the extra seeds need to be regenerated.

```bash
python -m cmorl_cyborg.minimal_5seed_stability_runner --extra-only
```

This records run state in:

- [`status.json`](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_5seed_runner/status.json)
- [`run_manifest.json`](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_5seed_runner/run_manifest.json)

### 2. Regenerate the set-quality comparison summary

```bash
python -m cmorl_cyborg.compare_suite --config cmorl_cyborg/configs/paper/compare_suite_main.yaml
```

This refreshes the main Table A source summary:

- [`table_a_summary.json`](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_table_a/table_a_summary.json)

### 3. Regenerate the deployment summary

```bash
python -m cmorl_cyborg.main_table_b --config cmorl_cyborg/configs/paper/table_b_suite_main.yaml
```

This refreshes:

- [`table_b_summary.json`](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_table_b/table_b_summary.json)
- aggregated deployment metrics under [`paper_table_b/aggregated`](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_table_b/aggregated)

### 4. Export the locked main-paper tables

```bash
python -m cmorl_cyborg.export_locked_tables --config cmorl_cyborg/configs/paper/export_tables_main.yaml
```

This refreshes:

- [`set_quality_table.csv`](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_table_a/set_quality_table.csv)
- [`set_quality_table.tex`](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_table_a/set_quality_table.tex)
- [`set_quality_table.json`](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_table_a/set_quality_table.json)
- [`deployment_table.csv`](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_table_b/deployment_table.csv)
- [`deployment_table.tex`](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_table_b/deployment_table.tex)
- [`deployment_table.json`](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_table_b/deployment_table.json)

### 5. Export Preference Coverage

```bash
python -m cmorl_cyborg.export_preference_coverage
```

This refreshes:

- [`per_preference_assignment.csv`](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_figure_c/per_preference_assignment.csv)
- [`per_preference_assignment_summary.csv`](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_figure_c/per_preference_assignment_summary.csv)
- [`preference_coverage.json`](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_figure_c/preference_coverage.json)
- [`preference_coverage.png`](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_figure_c/preference_coverage.png)

### 6. Export Tight Feasible Set Quality

This assumes the tight-evaluation inputs already exist under `cmorl_cyborg/outputs/fair_compare_eval/tight/`.

```bash
python -m cmorl_cyborg.export_tight_feasible_set
```

This refreshes:

- [`tight_feasible_set_summary.csv`](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/fair_compare_eval/aggregated/tight_feasible_set_summary.csv)
- [`tight_feasible_set_summary.json`](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/fair_compare_eval/aggregated/tight_feasible_set_summary.json)
- [`tight_feasible_set_quality.png`](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/fair_compare_eval/aggregated/tight_feasible_set_quality.png)

This figure is also the canonical matched comparison line for:

- `ours_stage2_fair`
- `no_constraint_stage2_fair`

and should be preferred over the broad Table-B line when discussing whether constraint-aware expansion matters causally.

### 7. Export appendix business/cost semantics

```bash
python -m cmorl_cyborg.export_business_cost_semantics
```

This refreshes:

- [`business_cost_semantics.csv`](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/business_cost_semantics/business_cost_semantics.csv)
- [`business_cost_semantics.tex`](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/business_cost_semantics/business_cost_semantics.tex)
- [`business_cost_semantics.json`](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/business_cost_semantics/business_cost_semantics.json)
- [`business_cost_semantics.png`](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/business_cost_semantics/business_cost_semantics.png)

### 8. Export appendix attacker-shift stress test

This re-evaluates the locked methods under held-out `meander`.

```bash
python -m cmorl_cyborg.export_attacker_shift_summary --red-policy meander
```

This refreshes:

- [`attacker_shift_summary.csv`](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/attacker_shift/attacker_shift_summary.csv)
- [`attacker_shift_summary.json`](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/attacker_shift/attacker_shift_summary.json)
- [`attacker_shift_summary.tex`](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/attacker_shift/attacker_shift_summary.tex)
- [`status.json`](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/attacker_shift/status.json)

### 9. Compile the paper

```bash
cd /home/waylandlee/CMORL2/Cyber-CMORL/paper
latexmk -pdf -interaction=nonstopmode main.tex
```

The compiled PDF is:

- [`main.pdf`](/home/waylandlee/CMORL2/Cyber-CMORL/paper/main.pdf)

## Canonical Paper-Facing Outputs

These are the files currently treated as canonical paper-facing artifacts:

- [`set_quality_table.tex`](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_table_a/set_quality_table.tex)
- [`deployment_table.tex`](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_table_b/deployment_table.tex)
- [`preference_coverage.png`](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_figure_c/preference_coverage.png)
- [`tight_feasible_set_quality.png`](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/fair_compare_eval/aggregated/tight_feasible_set_quality.png)
- [`attacker_shift_summary.tex`](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/attacker_shift/attacker_shift_summary.tex)
- [`business_cost_semantics.tex`](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/business_cost_semantics/business_cost_semantics.tex)
- [`business_cost_semantics.png`](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/business_cost_semantics/business_cost_semantics.png)

## Notes

- The locked main-paper line is intentionally narrower than the full history of `cmorl_cyborg/outputs/`.
- Raw logs, intermediate JSON/CSV files, and exploratory appendix-first runs are useful for auditability, but they are not all meant to be surfaced directly in the manuscript.
- The current manuscript compiles successfully, and `latexmk` reports that [`main.pdf`](/home/waylandlee/CMORL2/Cyber-CMORL/paper/main.pdf) is up to date.
