# Experiment Log

## 记录目标

本文件只记录 `cmorl_cyborg` 当前主线最关键的实验结论，不替代 `outputs/` 下的原始产物。

## 正式主线结果

### Formal 3-seed 主表 A

结果文件：

- [table_a_summary.json](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/paper_table_a/table_a_summary.json)
- [main_table_a_metrics.png](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/paper_table_a/main_table_a_metrics.png)

结论：

- `Ours Stage2` 已明显优于 `Stage1 Only`
- Stage-2 不再是“名义存在、实际未生成新 front”
- 当前正式结果已经能支撑主表 A 的方法有效性叙事

### Formal 3-seed 主表 B

结果文件：

- [table_b_summary.json](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/paper_table_b/table_b_summary.json)
- [main_table_b_bar.png](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/paper_table_b/main_table_b_bar.png)
- [ours_stage2.json](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/paper_table_b/aggregated/ours_stage2.json)

结论：

- `Ours` 相比 `Stage1 Only` 明显改善
- `Ours` 在 objective-based 表 B 规则下尚未全面压过 `no_constraint_stage2`
- `Ours` 与 `lagrangian_ppo` 更像不同 operating point，而不是单向碾压

## 2026-04-08 新增公平比较

### `coverage_combo_fair` vs 原始 `ours_stage2`

结果文件：

- [ours_stage2.json](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/paper_table_b/aggregated/ours_stage2.json)
- [coverage_combo_fair_loose.json](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/fair_compare_eval/aggregated/coverage_combo_fair_loose.json)

结论：

- `coverage_combo_fair` 在 `Loose` 下改善了 `security_return`、`business_return` 和 `mean_violation`
- 但 `feasible_rate` 从 `0.800` 降到 `0.633`
- 因此它不是对原始 `ours_stage2` 的严格改进，而是一个 trade-off 更不同的替代 operating point

### `Loose` fair compare

结果文件：

- [fair_compare_table_b_loose_with_coverage.png](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/fair_compare_eval/aggregated/fair_compare_table_b_loose_with_coverage.png)
- [coverage_combo_fair_loose.json](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/fair_compare_eval/aggregated/coverage_combo_fair_loose.json)
- [coverage_more_parents_fair_loose.json](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/fair_compare_eval/aggregated/coverage_more_parents_fair_loose.json)

结论：

- `coverage_combo_fair` 与 `coverage_more_parents_fair` 选中了同一组聚合 policy id
- `combo` 比 `more_parents` 更均衡，但优势幅度有限
- `no_constraint_stage2_fair` 仍然是 `Loose` 设定下最稳的可行性基线

### `Tight` fair compare

结果文件：

- [fair_compare_table_b_tight_with_coverage.png](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/fair_compare_eval/aggregated/fair_compare_table_b_tight_with_coverage.png)

结论：

- 四个方法在 `Tight` 下都表现出明显更差的可行率与更高的平均违约
- 当前 coverage 结果不支持围绕 `Tight` 写强 claim

## 调参结论

### 正向结果

- `gentle_guarded_tol2` 成为当前正式 `stage2_main` 主线
- 关键参数见：
  - [stage2_main.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/configs/paper/stage2_main.yaml)

### 负向结果

以下路线都已试过，当前不建议继续作为主线：

- semantic low-risk 父策略偏置
- 训练期 semantic soft penalty
- early termination 放松
- `B-tight` / `B-softbeta-v2` very small B 向微调

相关结果目录示例：

- [cand_b_tight](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/dev_tuning/holdout_seed/cand_b_tight)
- [cand_b_softbeta_v2](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/dev_tuning/holdout_seed/cand_b_softbeta_v2)
- [cand_gentle_guarded_tol2_softpen](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/dev_tuning/holdout_seed/cand_gentle_guarded_tol2_softpen)
- [cand_gentle_guarded_tol2_fail2](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/dev_tuning/holdout_seed/cand_gentle_guarded_tol2_fail2)

## 表 B 选点实验

### Objective-based 主规则

- 当前正式主表继续使用 objective-based 选点
- 理由：`security_return` 更稳，适合作为主表协议

### Semantic-aware / Semantic-balanced

结果文件：

- [ours_stage2_semantic_selection.json](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/paper_table_b_semantic_selection/aggregated/ours_stage2_semantic_selection.json)
- [ours_stage2_semantic_balanced.json](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/paper_table_b_semantic_balanced/aggregated/ours_stage2_semantic_balanced.json)

结论：

- 它们能改善：
  - `feasible_rate`
  - `mean_violation`
  - `critical_impact_count`
  - `high_disruption_action_rate`
- 但会明显拉坏：
  - `security_return`
  - `final_critical_compromised_hosts`

因此：

- 可作为附录 operating-point 分析
- 不建议替换主表 B

## 当前建议

- 保留当前正式 `stage2_main`
- 表 B 不再继续大改训练
- 优先补 `no_constraint_stage2_matched`
