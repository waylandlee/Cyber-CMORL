# Project Brief

## 2026-04-08 当前状态

`cmorl_cyborg` 现在已经不只是“迁移中的正式线”，而是仓库里当前论文主结果所在的位置。

当前最重要的结果文件包括：

- [ours_stage2.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_table_b/aggregated/ours_stage2.json)
- [main_table_b_bar.png](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_table_b/main_table_b_bar.png)
- [coverage_combo_fair_loose.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/fair_compare_eval/aggregated/coverage_combo_fair_loose.json)
- [coverage_more_parents_fair_loose.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/fair_compare_eval/aggregated/coverage_more_parents_fair_loose.json)
- [fair_compare_table_b_loose_with_coverage.png](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/fair_compare_eval/aggregated/fair_compare_table_b_loose_with_coverage.png)
- [fair_compare_table_b_tight_with_coverage.png](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/fair_compare_eval/aggregated/fair_compare_table_b_tight_with_coverage.png)

## 项目目标

`cmorl_cyborg` 的目标是把两阶段约束多目标强化学习主线迁移到正式 `CybORG` 蓝队环境，并产出可用于论文主表的正式结果：

- 主表 A：Pareto / utility 质量比较
- 主表 B：约束满足与 cyber semantics 比较

当前主方法是：

- `Stage-1`：多 preference 并行训练，构建初始 Pareto policy buffer
- `Stage-2`：基于 AdaCS + DCS 的受约束扩展，输出 `ours_stage2`

## 当前范围

当前目录主要覆盖：

- 正式 `CybORG` 环境包装与三目标 reward / semantics
- `Stage-1 / Stage-2` 训练入口
- baseline 训练入口
- `evaluate / evaluate_conditioned / evaluate_constraints`
- `main_table_a / main_table_b / export_tables / paper_plots`
- week-2 formal runner 与状态跟踪

不在本目录内单独维护的方法骨架：

- 一部分底层算法、buffer、模型和通用评估逻辑仍复用 `cmorl_minicage`

## 当前主线

当前正式主线配置：

- [stage1_main.yaml](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/configs/paper/stage1_main.yaml)
- [stage2_main.yaml](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/configs/paper/stage2_main.yaml)
- [compare_suite_main.yaml](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/configs/paper/compare_suite_main.yaml)
- [table_b_suite_main.yaml](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/configs/paper/table_b_suite_main.yaml)
- [export_tables_main.yaml](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/configs/paper/export_tables_main.yaml)

当前正式 `3-seed` 结果产物：

- [table_a_summary.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_table_a/table_a_summary.json)
- [table_b_summary.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_table_b/table_b_summary.json)
- [main_table_a_metrics.png](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_table_a/main_table_a_metrics.png)
- [main_table_b_bar.png](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_table_b/main_table_b_bar.png)

当前公平比较与 coverage 扩展结果：

- [ours_stage2_fair_loose.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/fair_compare_eval/aggregated/ours_stage2_fair_loose.json)
- [no_constraint_stage2_fair_loose.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/fair_compare_eval/aggregated/no_constraint_stage2_fair_loose.json)
- [coverage_combo_fair_loose.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/fair_compare_eval/aggregated/coverage_combo_fair_loose.json)
- [coverage_more_parents_fair_loose.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/fair_compare_eval/aggregated/coverage_more_parents_fair_loose.json)

## 当前判断

现阶段可以支持：

- 论文初稿写作
- 主表 A / B 解释
- `Ours` 与 baseline 的正式 `3-seed` 比较
- coverage 公平比较的保守结果分析

当前保守结论是：

- 原始 `ours_stage2` 仍是主线参照结果。
- `coverage_combo_fair` 在 `Loose` 下改善了 `security / business` 与 `mean_violation`，但降低了 `feasible_rate`，因此不是严格改进。
- `coverage_combo_fair` 与 `coverage_more_parents_fair` 在 `Loose` 下选中同一组 policy，差异有限。
- `Tight` 结果目前更适合作为压力测试，而不是正式主卖点。

现阶段仍建议补充：

- `5-seed formal`
- `no_constraint_stage2_matched` 公平消融
- 一份更面向论文的结果总结文档
