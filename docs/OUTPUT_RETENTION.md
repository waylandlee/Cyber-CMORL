# Output Retention

## Goal

This document is the non-destructive landing of the `2026-04-21` cleanup pass.

The immediate goal is not to rename every historical directory. The goal is to
make it unambiguous which artifacts are:

- official reports
- reproduction inputs
- ephemeral run products
- archive candidates

That lets us clean the repository in phases without breaking the current paper
line, active `4-objective` work, or old document links.

## Four Artifact Classes

### `official_report`

Files we want humans and the paper to read directly.

Typical examples:

- final `csv/json/tex/png` tables and figures
- aggregated summaries such as `table_a_summary.json`
- shared references and shared thresholds when they define the locked protocol

### `repro_input`

Files needed to regenerate an official report without rediscovering the setup.

Typical examples:

- `compare_suite_config.yaml`
- `export_tables_*.yaml`
- selected `solution_buffer.json`
- per-seed `metrics_shared_ref.json`
- explicit seed lists and runner manifests

### `ephemeral_run`

Heavy outputs produced while training, replaying, or debugging.

Typical examples:

- `run_*`
- `policy_*.pt`
- `generated_configs/`
- `tmp_configs/`
- replay traces
- live `runner.log` / `status.json`

### `archive_candidate`

A result line that was useful for reasoning, but is not part of the locked
paper-facing line anymore.

Typical examples in this repository:

- old deployability variants such as `_v2` / `_v3`
- exploratory appendix-first analyses
- superseded `critical_safe_v2_*` pilot trees
- dense trace bundles once the corresponding summary has been promoted

## Current Repository Mapping

### `cmorl_cyborg`

Treat the following as the current official CybORG result line:

- `cmorl_cyborg/outputs/paper_table_a/`
- `cmorl_cyborg/outputs/paper_table_b/`
- `cmorl_cyborg/outputs/fair_compare_eval/aggregated/`
- `cmorl_cyborg/outputs/paper_figure_c/`
- `cmorl_cyborg/outputs/paper_appendix/attacker_shift/`
- `cmorl_cyborg/outputs/paper_appendix/business_cost_semantics/`

Treat the following as the active `4-objective` candidate line:

- `cmorl_cyborg/outputs/paper_table_v2_4/`
- `paper/table/set_quality_4obj.tex`
- `paper/table/constrained_deployment_performance_4obj.tex`
- the `4-objective` semantic-risk figures under `paper/images/`

Treat the following as mostly `ephemeral_run` or `archive_candidate` material:

- `cmorl_cyborg/outputs/paper_appendix/critical_safe_v2_*`
- `cmorl_cyborg/outputs/paper_appendix/semantic_repair_analysis/`
- `cmorl_cyborg/outputs/paper_appendix/semantic_repair_traces/`
- `cmorl_cyborg/outputs/*_runner/`
- `cmorl_cyborg/outputs/tmp_configs/`
- any nested `run_*` directory and its `policy_*.pt` checkpoints

### `cmorl_minicage`

Treat `cmorl_minicage` as a historical reference and upgrade sandbox, not the
default paper source of truth.

Keep as long-lived reference outputs:

- `cmorl_minicage/outputs/paper_table_a/`
- `cmorl_minicage/outputs/paper_table_b/`
- `cmorl_minicage/outputs/paper_appendix/`
- `cmorl_minicage/outputs/formal_c2*`
- `cmorl_minicage/outputs/baselines_formal_c2*`
- `cmorl_minicage/outputs/ablation_adacs_dcs_*`
- `cmorl_minicage/outputs/plots/`

Everything under nested `run_*` directories is still `ephemeral_run` unless it
is the only surviving anchor for a published summary.

## Keep Rules

### For an official table or figure directory

Keep:

- the top-level final exports
- the config that generated them
- the shared reference or shared thresholds
- the small per-seed summaries that explain aggregation

Move out or archive later:

- raw checkpoints
- duplicated `run_*` trees after buffer anchors are recorded
- old variant directories once a single official version is chosen

### For a runner directory

Keep by default:

- `run_manifest.json`
- minimal status needed to explain what was executed

Archive later:

- generated configs after the run is frozen elsewhere
- transient logs that are only useful during execution

### For appendix analysis trees

Keep the smallest promoted summary close at hand:

- `summary.json`
- `summary.csv`
- `summary.tex`
- one representative figure if the paper cites it

Archive later:

- full trace bundles
- replay copies
- repeated baseline mirrors across seeds

## Safe Cleanup Order

When cleaning a directory, use this order:

1. Freeze the official output in `paper/` or the top-level report directory.
2. Record the generating config and kept seed anchors in
   `cmorl_cyborg/outputs/manifests/official_artifacts.yaml`.
3. Confirm that no current doc or script still points to the nested `run_*`
   path as its only canonical source.
4. Move the heavy run products to an archive location or external storage.
5. Only then consider removing tracked outputs from Git history or the index.

## What This Pass Does Not Do

This pass does not:

- physically rename legacy directories that code already points to
- rewrite old experimental docs to a new path scheme
- delete any existing run product

Those actions are intentionally deferred until the manifest and retention rules
are stable.

## Canonical Entry Points

Start here when deciding whether a file should stay:

- `README.md`
- `cmorl_cyborg/outputs/README.md`
- `cmorl_cyborg/outputs/manifests/official_artifacts.yaml`
- `cmorl_minicage/outputs/README.md`

## Git Tracking Rule

As of the third cleanup pass on `2026-04-21`, `outputs/` is no longer treated
as a version-controlled storage surface.

What should remain tracked in Git:

- top-level `outputs/README.md`
- `outputs/archive/README.md`
- lightweight manifests under `outputs/manifests/`

What should not remain tracked in Git:

- raw experiment results
- checkpoints
- per-run tables copied from live outputs
- replay traces
- generated configs and live runner logs

## Path Normalization Rule

As of the third cleanup pass on `2026-04-21`, experiment configs should not
hard-code a machine-specific repository root.

Use these conventions:

- config files should use repo-relative paths such as
  `cmorl_cyborg/outputs/paper_table_a/...`
- manifests may record archive targets relative to the repository root
- docs may keep current absolute local links only when they are intentionally
  used as IDE-friendly navigation links

Avoid reintroducing:

- `/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/...`
- `/home/waylandlee/Cyber-CMORL/...`
