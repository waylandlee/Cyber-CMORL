# Decisions

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

- [reward.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/reward.py)
- [semantics.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/semantics.py)
- [profiles/Scenario2.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/profiles/Scenario2.yaml)

## 2. Stage-1 preference 在正式线中要求并行

原因：

- Stage-1 的每个 preference 是独立训练任务
- 串行会显著拖慢正式 3-seed / 5-seed

实现：

- [stage1_main.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/configs/paper/stage1_main.yaml)
- [stage1_only_main.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/configs/paper/stage1_only_main.yaml)

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

- [stage2_main.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/configs/paper/stage2_main.yaml)

## 4. 主表 A 使用 shared reference point

原因：

- 多方法 Pareto / utility 比较必须在同一 reference 下完成

文件：

- [compare_suite_main.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/configs/paper/compare_suite_main.yaml)
- [shared_reference.json](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/paper_table_a/shared_reference.json)

## 5. 主表 B 使用来自 `stage1_only` 的 shared thresholds

原因：

- 需要一个独立于 `ours_stage2` 的统一约束参考
- `stage1_only` 是最自然的公共阈值来源

文件：

- [table_b_suite_main.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/configs/paper/table_b_suite_main.yaml)
- [shared_thresholds.json](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/paper_table_b/shared_thresholds.json)

## 6. 表 B 正式主规则保持 objective-based 选点

原因：

- protocol 更简单、统一
- semantic-aware / semantic-balanced 会明显改善 `feasible_rate / violation / disruption`
- 但会明显拉坏 `security_return`
- 因此更适合作为附录 operating-point 分析，而不是替换主表

文件：

- [evaluate_constraints.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/evaluate_constraints.py)
- [ours_stage2_semantic_selection.json](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/paper_table_b_semantic_selection/aggregated/ours_stage2_semantic_selection.json)
- [ours_stage2_semantic_balanced.json](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/paper_table_b_semantic_balanced/aggregated/ours_stage2_semantic_balanced.json)

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

- [stage2_main.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/configs/paper/stage2_main.yaml)
- [stage2_no_constraint_main.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/configs/paper/stage2_no_constraint_main.yaml)
