# Experiment Log

## 记录规范

每次正式记录一条实验时，建议至少填写以下字段：

- 日期
- 实验 ID
- 目标
- 配置文件
- 输入 buffer
- 输出目录
- 关键指标
- 现象
- 结论
- 下一步

结构化事实优先来自：

- `solution_buffer.json`
- `stage1_summary.json`
- `stage2_summary.json`
- `metrics.json`

本文件负责记录“如何理解这些结果”，而不是替代这些产物。

## 模板

```text
日期：
实验 ID：
阶段：
目标：
配置文件：
输入 buffer：
输出目录：
关键指标：
现象：
结论：
下一步：
```

## 已记录实验

### 2026-03-30 / P1-Stage1-Smoke

- 实验 ID：`run_29deaae7`
- 阶段：Stage-1
- 目标：验证新的 preference 初始化策略、summary 产物和 buffer schema 是否能正常写出
- 配置文件：[cmorl_minicage/configs/stage1.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/configs/stage1.yaml)
- 输出目录：[run_29deaae7](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/p1_stage1_check/run_29deaae7)
- 关键指标：`schema_version = 0.3.0`，`preferences count = 6`，`stage1_summary entries = 6`
- 现象：新版本成功写出 `stage1_summary.json`，record notes 中包含 `scalarized_utility`、`trainer_stats` 和 `pareto_size_after_save`
- 结论：Stage-1 的初始化策略和过程统计已接入稳定输出链路
- 下一步：继续用 `formal` 配置做更长训练，观察初始化策略对 Stage-1 Pareto set 密度的影响

### 2026-03-30 / P1-Stage2-Smoke

- 实验 ID：`run_81cbc3c2`
- 阶段：Stage-2 + Evaluation
- 目标：验证 round summary、泛化 HV 和 assignment summary 是否正常写出
- 配置文件：
  - [cmorl_minicage/configs/stage2.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/configs/stage2.yaml)
  - [cmorl_minicage/configs/evaluate.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/configs/evaluate.yaml)
- 输入 buffer：[solution_buffer.json](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/p1_stage1_check/run_29deaae7/solution_buffer.json)
- 输出目录：[run_81cbc3c2](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/p1_stage2_check/run_81cbc3c2)
- 关键指标：`hypervolume_method = exact_inclusion_exclusion`，`unique_assigned_policies = 4`
- 现象：在当前较严格的 feasibility gate 下，没有新增 stage-2 policy，但 `stage2_summary.json` 和 `metrics_p1.json` 均成功写出
- 结论：新的约束门控与评估体系已经工作，但 Stage-2 仍需超参调节来产生更有效的 front extension
- 下一步：使用 `formal` 或更宽松的 ablation 配置探索 Stage-2 的可行扩展区间
