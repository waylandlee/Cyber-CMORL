# CybORG Outputs

## Why This File Exists

`cmorl_cyborg/outputs/` has accumulated multiple paper lines, pilot lines,
runner directories, and replay-heavy appendix analyses. We are not physically
renaming everything in one step because the current code, docs, and manuscript
still point to the legacy paths.

This file defines the logical organization that new cleanup work should follow.

## Current Logical Layers

### Official Reports

These directories are the current paper-facing source of truth:

- `paper_table_a/`
- `paper_table_b/`
- `fair_compare_eval/aggregated/`
- `paper_figure_c/`
- `paper_appendix/attacker_shift/`
- `paper_appendix/business_cost_semantics/`
- `paper_table_v2_4/` for the active `4-objective` candidate line

Keep top-level report products here:

- final `csv/json/tex/png`
- locked aggregation summaries
- shared references or thresholds
- compare/export configs that define the protocol

### Reproduction Inputs

These should stay close to the report they regenerate:

- `compare_suite_config.yaml`
- `shared_reference.json`
- selected per-seed `metrics_shared_ref.json`
- `export_summary.json`
- compact manifests pointing to kept seed anchors

### Ephemeral Runs

These are necessary while experiments are active, but they are not the stable
paper-facing artifact:

- nested `run_*`
- `policy_*.pt`
- `generated_configs/`
- `tmp_configs/`
- replay `trace/`
- live `runner.log` / `status.json`

When a result line is frozen, these should be the first things moved out of the
official report directory.

### Archive Candidates

These are important for auditability, but they should not stay mixed into the
current official line forever:

- `paper_appendix/critical_safe_v2_1_4obj_analysis/`
- `paper_appendix/critical_safe_v2_2_4obj_analysis/`
- `paper_appendix/critical_safe_v2_3_4obj_analysis/`
- `paper_appendix/critical_safe_v2_4_4obj_analysis/`
- `paper_appendix/critical_safe_v2_4obj_analysis/`
- `paper_appendix/semantic_repair_analysis/`
- `paper_appendix/semantic_repair_traces/`
- `paper_table_a/ours_stage2_deployability/`
- `paper_table_a/ours_stage2_deployability_v2/`
- `paper_table_a/ours_stage2_deployability_v3/`

## New Rules For Future Cleanup

1. Do not treat a nested `run_*` directory as the only canonical source of a
   paper result.
2. Before deleting or archiving a heavy run tree, record the kept config and
   seed anchors in `manifests/official_artifacts.yaml`.
3. If a directory contains both final tables and raw checkpoints, the final
   tables stay here and the checkpoints become archive candidates.
4. If a variant is superseded, keep one official version and move the rest to
   `archive/` or external storage.

## First Places To Check

- `manifests/official_artifacts.yaml`
- `manifests/archive_second_phase_2026_04_21.yaml`
- `manifests/phase3_cleanup_2026_04_21.yaml`
- `manifests/README.md`
- `../../docs/OUTPUT_RETENTION.md`

## Git Tracking Surface

`cmorl_cyborg/outputs/` should now be understood as an on-disk artifact root,
not a Git-tracked results tree.

Only the following are meant to stay tracked:

- this `README.md`
- `archive/README.md`
- lightweight manifests under `manifests/`

The third cleanup pass also normalizes config paths to repo-relative form so
active experiment entrypoints do not depend on one workstation-specific root.
