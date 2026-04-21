# Decisions

## 2026-04-17 语义修复路线决策

以下决策基于已经跑完的 `phase1/2/3` 结果，而不是基于尚未完成的 `Critical-First V1` pilot。

## 8. 停止旧 `phase4` 与旧 gate/target 微调

原因：

- `phase1 selection-only` 的 `helpful_seed_count = 0/3`
- `semantic_balanced` 虽然经常降低 `persistent_critical_breach_rate`
- 但没有把 `ever_critical_breach_rate` 从 `1.0` 拉下来
- `seed_0019` 甚至出现了 `ever: 0.9625 -> 1.0`
- `phase2 gate` 在 `seed_0011` 上把 `persistent` 从 `0.79375` 拉高到 `0.8875`
- `phase3 target` 只能把 `persistent` 压到 `0.70625`，但 `ever` 仍然是 `1.0`

结论：

- 旧三维修补版更擅长减轻最终损失，不擅长阻止第一次关键突破
- 因此不再继续做旧 `phase4`，也不再继续微调旧 `semantic_gate / semantic_target`

相关结果：

- [phase1_selection_only_summary.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/fair_compare_semantic_repair_runner/phase1_selection_only_summary.json)
- [phase2_gate_summary.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/fair_compare_semantic_repair_runner/phase2_gate_summary.json)
- [phase3_target_summary.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/fair_compare_semantic_repair_runner/phase3_target_summary.json)

## 9. 语义修复默认路线切到 `Critical-First V1`

原因：

- 当前最关键的失败模式是 `ever_critical_breach_rate` 长期接近或等于 `1.0`
- 旧规则把 `business / cost` 放在了过高优先级，容易接受“每次都被打到，只是最后没那么惨”的候选
- 需要把首次关键突破和 critical dwell 明确拉进主链路

结论：

- 当前活动方法线改为 `Critical-First V1`
- 默认选点改为 `critical_safe_balanced`
- 默认接收逻辑改为 critical-first hard gate
- `business / cost` 在 V1 中只作为 guardrail，不再作为主排序目标

相关配置：

- [stage2_fair_critical_safe_v1_seed_0011.yaml](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/configs/paper/fair_compare_semantic/stage2_fair_critical_safe_v1_seed_0011.yaml)

## 10. `Critical-First V1` 未完成前，不把任何新结果写成结论

原因：

- 当前 `Critical-First V1` 的 `seed_0011` pilot 还在运行
- 尚未产出新的 `phase2_gate_summary` 风格结果文件
- 现有 [final_summary.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/fair_compare_semantic_repair_runner/final_summary.json) 仍对应旧的 `stop_after_phase = 3` 实验

结论：

- 文档中允许同步的方法结论只包括：
  - 旧 `phase1/2/3` 已完成结果
  - 从这些结果推导出的路线切换决策
- 不把进行中的 `Critical-First V1` 训练状态表述成“通过”或“失败”

## 2026-04-08 状态说明

以下决策应结合当前结果来理解：

- `cmorl_cyborg` 负责正式论文主结果；
- `cmorl_minicage` 负责迁移验证、开发决策与补充材料；
- 后续若与当前 `3-seed` 结果冲突，论文叙事以 `cmorl_cyborg` 为准。

## 1. 正式环境口径冻结为 `security / business / cost`

原因：

- 需要把 `CybORG` 的 Blue 防御问题写成稳定的三目标 MORL 协议
- 后续 dev / holdout / formal 结果必须共用同一口径

实现：

- [reward.py](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/reward.py)
- [semantics.py](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/semantics.py)
- [profiles/Scenario2.yaml](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/profiles/Scenario2.yaml)

## 2. Stage-1 preference 在正式线中要求并行

原因：

- Stage-1 的每个 preference 是独立训练任务
- 串行会显著拖慢正式 3-seed / 5-seed

实现：

- [stage1_main.yaml](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/configs/paper/stage1_main.yaml)
- [stage1_only_main.yaml](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/configs/paper/stage1_only_main.yaml)

## 3. 正式 `stage2_main` 使用温和 DCS 区间

当前正式配置：

- `constrained_updates: 5`
- `constraint_tolerance: -2.0`
- `total_timesteps_per_update: 1536`
- `beta_min: 1.002`
- `beta_max: 1.008`

原因：

- 旧 formal 的 `beta < 1` 区间会把 constrained extension 全部卡死
- 现配置已经在 dev / holdout / formal 上证明能稳定生成新 `stage2_ext_*`

文件：

- [stage2_main.yaml](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/configs/paper/stage2_main.yaml)

## 4. 主表 A 使用 shared reference point

原因：

- 多方法 Pareto / utility 比较必须在同一 reference 下完成

文件：

- [compare_suite_main.yaml](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/configs/paper/compare_suite_main.yaml)
- [shared_reference.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_table_a/shared_reference.json)

## 5. 主表 B 使用来自 `stage1_only` 的 shared thresholds

原因：

- 需要一个独立于 `ours_stage2` 的统一约束参考
- `stage1_only` 是最自然的公共阈值来源

文件：

- [table_b_suite_main.yaml](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/configs/paper/table_b_suite_main.yaml)
- [shared_thresholds.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_table_b/shared_thresholds.json)

## 6. 表 B 正式主规则保持 objective-based 选点

原因：

- protocol 更简单、统一
- semantic-aware / semantic-balanced 会明显改善 `feasible_rate / violation / disruption`
- 但会明显拉坏 `security_return`
- 因此更适合作为附录 operating-point 分析，而不是替换主表

文件：

- [evaluate_constraints.py](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/evaluate_constraints.py)
- [ours_stage2_semantic_selection.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_table_b_semantic_selection/aggregated/ours_stage2_semantic_selection.json)
- [ours_stage2_semantic_balanced.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_table_b_semantic_balanced/aggregated/ours_stage2_semantic_balanced.json)

## 7. 当前最大的公平性缺口是 `no_constraint_stage2` 未 matched

现状：

- `ours_stage2` 和 `no_constraint_stage2` 不仅 `extension_mode` 不同
- 连 `constrained_updates`、`total_timesteps_per_update`、`beta` 区间也不同

影响：

- 这更像工程对照，不是严格因果消融

建议：

- 后续补一组 `no_constraint_stage2_matched`
- 只改 `extension_mode`

相关配置：

- [stage2_main.yaml](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/configs/paper/stage2_main.yaml)
- [stage2_no_constraint_main.yaml](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/configs/paper/stage2_no_constraint_main.yaml)
