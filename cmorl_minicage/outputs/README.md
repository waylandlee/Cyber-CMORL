# MiniCAGE Outputs

`cmorl_minicage/outputs/` is now best understood as a historical reference and
upgrade workspace rather than the default paper-facing artifact root.

## Keep As Long-Lived Reference

- `paper_table_a/`
- `paper_table_b/`
- `paper_appendix/`
- `formal_c2/`
- `formal_c2_independent/`
- `formal_c2_independent_stage1_density/`
- `formal_c2_independent_adacs_dcs/`
- `baselines_formal_c2/`
- `baselines_formal_c2_suite/`
- `ablation_adacs_dcs_dense/`
- `ablation_adacs_dcs_marginal/`
- `plots/`

These directories document the migration path, dense-front improvements, and
baseline comparisons that still matter when explaining how the project evolved.

## Treat As Ephemeral

Inside the kept directories, the following are still transient by default:

- nested `run_*`
- `policy_*.pt`
- duplicate checkpoint trees kept only for convenience

If a plot or summary can be reproduced from a smaller anchor, prefer keeping the
summary and manifesting the anchor instead of preserving the whole run tree in
place forever.

## Cleanup Rule

Before archiving a MiniCAGE run tree, make sure the corresponding:

- plot
- summary table
- config
- kept seed anchor

are all still easy to find from the higher-level directory.
