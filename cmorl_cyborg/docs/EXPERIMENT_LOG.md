# Experiment Log

## 记录目标

本文件只记录 `cmorl_cyborg` 当前主线最关键的实验结论，不替代 `outputs/` 下的原始产物。

## 2026-04-17 语义修复主线结论

### 旧 `phase1/2/3` 结果已完成并可作为决策依据

结果文件：

- [phase0_baselines.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/fair_compare_semantic_repair_runner/phase0_baselines.json)
- [phase1_selection_only_summary.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/fair_compare_semantic_repair_runner/phase1_selection_only_summary.json)
- [phase2_gate_summary.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/fair_compare_semantic_repair_runner/phase2_gate_summary.json)
- [phase3_target_summary.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/fair_compare_semantic_repair_runner/phase3_target_summary.json)
- [final_summary.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/fair_compare_semantic_repair_runner/final_summary.json)
- [final_report.md](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/fair_compare_semantic_repair_runner/final_report.md)

结论：

- 这些产物对应的是旧的 `semantic_aware / semantic_balanced / semantic_gate / semantic_target` 实验线，不是 `Critical-First V1`。
- `final_summary.json` 的时间戳是 `2026-04-17T11:57:57+08:00`，并且 `stop_after_phase = 3`，因此它只能支持“旧三维修补版到 phase3 为止”的结论。

### Phase 1: selection-only 没有形成可接受修复

结果文件：

- [phase1_selection_only_summary.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/fair_compare_semantic_repair_runner/phase1_selection_only_summary.json)
- [seed_0007 semantic_balanced replay20](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/semantic_repair_analysis/phase1_selection_only/semantic_balanced/seed_0007/semantic_balanced__stage1_pref_000_ckpt_191_semantic_audit_replay20/risk_tier_summary.json)
- [seed_0011 semantic_balanced replay20](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/semantic_repair_analysis/phase1_selection_only/semantic_balanced/seed_0011/semantic_balanced__stage2_ext_002_obj_0_semantic_audit_replay20/risk_tier_summary.json)
- [seed_0019 semantic_balanced replay20](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/semantic_repair_analysis/phase1_selection_only/semantic_balanced/seed_0019/semantic_balanced__stage2_ext_000_obj_0_semantic_audit_replay20/risk_tier_summary.json)

结论：

- `selection_only_helpful_seed_count = 0/3`，说明单纯换选点没有一个 seed 达到“清晰有帮助”。
- `semantic_balanced` 的共同模式是降低 `persistent_critical_breach_rate`，但没有解决“是否会首次打穿”。
- `seed_0007`：`persistent` 从 `0.775 -> 0.45625`，但 `ever` 仍是 `1.0`，`cost_return` 从 `-24.43 -> -30.80`。
- `seed_0011`：`persistent` 从 `0.79375 -> 0.60625`，但 `ever` 仍是 `1.0`，`cost_return` 从 `-22.68 -> -27.81`。
- `seed_0019`：`persistent` 从 `0.875 -> 0.6375`，但 `ever` 反而从 `0.9625 -> 1.0`，`high_confidence_env_run_rate` 从 `0.95 -> 0.99375`。
- 从 replay20 trace 看，`semantic_balanced` 更像是在缩短 critical dwell，而不是阻止首次 critical breach。

### Phase 2: gate 版失败且方向错误

结果文件：

- [phase2_gate_summary.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/fair_compare_semantic_repair_runner/phase2_gate_summary.json)
- [phase2 gate replay20 risk summary](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/semantic_repair_analysis/phase2_gate/seed_0011/semantic_balanced_selected__stage1_pref_005_ckpt_191_semantic_audit_replay20/risk_tier_summary.json)
- [baseline replay20 risk summary](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/semantic_repair_analysis/phase0_objective_selected/seed_0011/objective_selected__stage2_ext_016_obj_0_semantic_audit_replay20/risk_tier_summary.json)

结论：

- `seed_0011` gate 选中了 `stage1_pref_005_ckpt_191`。
- `persistent_critical_breach_rate` 从基线的 `0.79375` 升到 `0.8875`。
- `ever_critical_breach_rate` 仍是 `1.0`。
- `mean_critical_dwell_steps` 从 `67.3375` 升到 `77.39375`。
- `business_return` 回退 `14.05`，超过 guardrail。
- 因此 gate 版不是“没修好”，而是把关键风险推向了更差方向。

### Phase 3: target 版只是在减轻后果，没有阻止首次突破

结果文件：

- [phase3_target_summary.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/fair_compare_semantic_repair_runner/phase3_target_summary.json)
- [phase3 target replay20 risk summary](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/semantic_repair_analysis/phase3_target/seed_0011/semantic_balanced_selected__stage2_ext_006_obj_0_semantic_audit_replay20/risk_tier_summary.json)

结论：

- `seed_0011` target 选中了 `stage2_ext_006_obj_0`。
- `persistent_critical_breach_rate` 从 `0.79375` 降到 `0.70625`。
- `mean_critical_dwell_steps` 从 `67.3375` 降到 `62.3`。
- 但 `ever_critical_breach_rate` 仍是 `1.0`，`env_run_feasible_rate` 变成 `0.0`。
- `business_regression = 6.19` 在 guardrail 内，但 `cost_regression = 4.80` 超过 guardrail。
- 这说明 target 版更擅长“被打穿后少持续一会儿”，仍不擅长阻止第一次 critical hit。

### 语义指标口径说明

说明：

- 上述已完成的 `phase1/2/3` replay20 artifacts 还没有给出可用的 `mean_first_critical_hit_step` 和 `critical_hit_latency_score`，对应字段在历史 summary 中仍为 `null`。
- 新代码已经把这些 first-hit 指标接进评估主链路，但需要等 `Critical-First V1` pilot 跑完后，才会有同口径的新结果。

### `Critical-First V1` 当前状态

相关文件：

- [stage2_fair_critical_safe_v1_seed_0011.yaml](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/configs/paper/fair_compare_semantic/stage2_fair_critical_safe_v1_seed_0011.yaml)
- [ours_stage2_fair_critical_safe_v1 output root](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/fair_compare_semantic/ours_stage2_fair_critical_safe_v1/seed_0011)

当前状态：

- `seed_0011` 的 `Critical-First V1` pilot 已启动，但截至本次文档同步时尚未产出可解释的最终结果文件。
- 因此当前可同步到文档的稳定结论只包括旧 `phase1/2/3` 结果，以及“应当切换到 Critical-First 路线”的方法判断。

## 正式主线结果

### Formal 3-seed 主表 A

结果文件：

- [table_a_summary.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_table_a/table_a_summary.json)
- [main_table_a_metrics.png](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_table_a/main_table_a_metrics.png)

结论：

- `Ours Stage2` 已明显优于 `Stage1 Only`
- Stage-2 不再是“名义存在、实际未生成新 front”
- 当前正式结果已经能支撑主表 A 的方法有效性叙事

### Formal 3-seed 主表 B

结果文件：

- [table_b_summary.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_table_b/table_b_summary.json)
- [main_table_b_bar.png](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_table_b/main_table_b_bar.png)
- [ours_stage2.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_table_b/aggregated/ours_stage2.json)

结论：

- `Ours` 相比 `Stage1 Only` 明显改善
- `Ours` 在 objective-based 表 B 规则下尚未全面压过 `no_constraint_stage2`
- `Ours` 与 `lagrangian_ppo` 更像不同 operating point，而不是单向碾压

## 2026-04-08 新增公平比较

### `coverage_combo_fair` vs 原始 `ours_stage2`

结果文件：

- [ours_stage2.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_table_b/aggregated/ours_stage2.json)
- [coverage_combo_fair_loose.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/fair_compare_eval/aggregated/coverage_combo_fair_loose.json)

结论：

- `coverage_combo_fair` 在 `Loose` 下改善了 `security_return`、`business_return` 和 `mean_violation`
- 但 `feasible_rate` 从 `0.800` 降到 `0.633`
- 因此它不是对原始 `ours_stage2` 的严格改进，而是一个 trade-off 更不同的替代 operating point

### `Loose` fair compare

结果文件：

- [fair_compare_table_b_loose_with_coverage.png](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/fair_compare_eval/aggregated/fair_compare_table_b_loose_with_coverage.png)
- [coverage_combo_fair_loose.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/fair_compare_eval/aggregated/coverage_combo_fair_loose.json)
- [coverage_more_parents_fair_loose.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/fair_compare_eval/aggregated/coverage_more_parents_fair_loose.json)

结论：

- `coverage_combo_fair` 与 `coverage_more_parents_fair` 选中了同一组聚合 policy id
- `combo` 比 `more_parents` 更均衡，但优势幅度有限
- `no_constraint_stage2_fair` 仍然是 `Loose` 设定下最稳的可行性基线

### `Tight` fair compare

结果文件：

- [fair_compare_table_b_tight_with_coverage.png](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/fair_compare_eval/aggregated/fair_compare_table_b_tight_with_coverage.png)

结论：

- 四个方法在 `Tight` 下都表现出明显更差的可行率与更高的平均违约
- 当前 coverage 结果不支持围绕 `Tight` 写强 claim

## 调参结论

### 正向结果

- `gentle_guarded_tol2` 成为当前正式 `stage2_main` 主线
- 关键参数见：
  - [stage2_main.yaml](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/configs/paper/stage2_main.yaml)

### 负向结果

以下路线都已试过，当前不建议继续作为主线：

- semantic low-risk 父策略偏置
- 训练期 semantic soft penalty
- early termination 放松
- `B-tight` / `B-softbeta-v2` very small B 向微调

相关结果目录示例：

- [cand_b_tight](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/dev_tuning/holdout_seed/cand_b_tight)
- [cand_b_softbeta_v2](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/dev_tuning/holdout_seed/cand_b_softbeta_v2)
- [cand_gentle_guarded_tol2_softpen](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/dev_tuning/holdout_seed/cand_gentle_guarded_tol2_softpen)
- [cand_gentle_guarded_tol2_fail2](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/dev_tuning/holdout_seed/cand_gentle_guarded_tol2_fail2)

## 表 B 选点实验

### Objective-based 主规则

- 当前正式主表继续使用 objective-based 选点
- 理由：`security_return` 更稳，适合作为主表协议

### Semantic-aware / Semantic-balanced

结果文件：

- [ours_stage2_semantic_selection.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_table_b_semantic_selection/aggregated/ours_stage2_semantic_selection.json)
- [ours_stage2_semantic_balanced.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_table_b_semantic_balanced/aggregated/ours_stage2_semantic_balanced.json)

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
