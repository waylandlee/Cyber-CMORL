# CybORG 正式环境第二周执行清单

## 当前状态

截至 `2026-04-08`，本清单的大部分“基础设施与 3-seed 产出”任务已经完成。

当前应把第二周遗留问题理解为：

- 不是继续补链路；
- 而是确认哪些 `3-seed` 结果值得带入后续正式叙事；
- 尤其是主表 B 与 `fair_compare_eval` 的结论边界。

## 目的

本清单承接 [CYBORG_EXECUTION_CHECKLIST.md](/home/waylandlee/CMORL2/Cyber-CMORL/docs/CYBORG_EXECUTION_CHECKLIST.md)。

第二周的目标不是继续搭基础设施，而是把已经稳定的 `cmorl_cyborg` 链路推进到：

- 可以在正式 `CybORG` 上做方法横评
- 可以产出 `3-seed` 汇总
- 可以冻结 shared reference point 与 shared thresholds
- 可以判断是否具备进入 `5-seed formal` 的条件

第二周重点：

- 重跑正式环境 baseline
- 形成 `3-seed` 主表 A / 主表 B 初版
- 固定正式环境共享 reference / thresholds
- 为 `5-seed formal` 做最后准入检查

第二周不做：

- 在协议未冻结前反复改 reward 口径
- 在 baseline 未重跑齐前下最终论文结论
- 在 `3-seed` 都不稳定时直接上 `5-seed formal`

## 第二周总验收标准

到第二周结束时，应满足以下五项：

1. `Ours` 与主要 baseline 都已在正式 `CybORG` 上完成至少 `3-seed` 小规模运行。
2. [cmorl_cyborg/compare_suite.py](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/compare_suite.py) 已基于正式环境结果生成稳定的 shared reference point。
3. [cmorl_cyborg/evaluate_constraints.py](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/evaluate_constraints.py) 已基于正式环境 `stage1-only` 结果生成稳定的 shared thresholds。
4. 主表 A / 主表 B 的 CSV / JSON / TEX 都能从正式环境产物导出。
5. 已能明确判断：是否进入 `5-seed formal`，还是需要再做一轮小调参。

### 2026-04-08 回看

- 第 `1-4` 项目前都已具备。
- 第 `5` 项当前仍应保守处理：仓库还不适合把叙事写成“5-seed formal 已正式定稿”。

---

## Day 1：冻结第二周协议与目录

### 要改的文件

- [cmorl_cyborg/configs/paper/compare_suite_main.yaml](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/configs/paper/compare_suite_main.yaml)
- [cmorl_cyborg/configs/paper/export_tables_main.yaml](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/configs/paper/export_tables_main.yaml)
- [cmorl_cyborg/configs/paper/stage1_main.yaml](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/configs/paper/stage1_main.yaml)
- [cmorl_cyborg/configs/paper/stage2_main.yaml](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/configs/paper/stage2_main.yaml)

### 要做的事

1. 冻结第二周使用的正式环境协议，不再改 reward / semantics 定义。
2. 固定输出目录结构：
   - `cmorl_cyborg/outputs/paper_table_a/`
   - `cmorl_cyborg/outputs/paper_table_b/`
   - `cmorl_cyborg/outputs/paper_appendix/`
3. 固定第二周 seed 集合，例如：
   - `dev`: `7`
   - `holdout`: `11`
   - `3-seed`: `7, 11, 19`
4. 固定第二周参与横评的方法名单。

### 建议纳入的第二周方法

- `ours_stage2`
- `stage1_only`
- `no_constraint_stage2`
- `weighted_sum`
- `single_objective`
- `lagrangian_ppo`
- `preference_conditioned_ppo`
- `pcn`  

### 验收标准

- 所有方法都有独立配置和独立输出根目录。
- 参与第二周横评的方法名单固定。
- `3-seed` 协议写入配置或文档，不再临时改 seed。

### 如果失败，优先检查

- 是否还有 reward / semantic 口径在摇摆
- 是否输出目录仍混用 MiniCAGE 路径

---

## Day 2-3：重跑正式环境 Baseline

### 要改的文件

- [cmorl_cyborg/baselines.py](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/baselines.py)
- [cmorl_cyborg/train_pref_conditioned_ppo.py](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/train_pref_conditioned_ppo.py)
- [cmorl_cyborg/train_lagrangian_ppo.py](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/train_lagrangian_ppo.py)
- [cmorl_cyborg/train_pcn.py](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/train_pcn.py)
- [cmorl_cyborg/configs/paper/weighted_sum_main.yaml](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/configs/paper/weighted_sum_main.yaml)
- [cmorl_cyborg/configs/paper/pref_cond_ppo.yaml](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/configs/paper/pref_cond_ppo.yaml)
- [cmorl_cyborg/configs/paper/lagrangian_ppo.yaml](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/configs/paper/lagrangian_ppo.yaml)
- [cmorl_cyborg/configs/paper/pcn.yaml](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/configs/paper/pcn.yaml)

### 要做的事

1. 先跑每个 baseline 的 `1-seed` smoke / dev。
2. 通过后统一扩展到第二周的 `3-seed` 集合。
3. 统一记录：
   - 训练预算
   - 输出路径
   - 是否成功产出标准 artifact

### 每种方法最低要求

- `weighted_sum`
  - 成功产出 `solution_buffer.json` 和 `metrics.json`
- `preference_conditioned_ppo`
  - 成功产出 `conditioned_run_metadata.json`
  - 成功产出 `evaluated_points.json`、`pareto_front_conditioned.json`、`metrics.json`
- `lagrangian_ppo`
  - 成功产出 `run_metadata.json`
  - 成功产出 `constraint_metrics.json`
- `pcn`
  - 至少在 `3-seed` 内无 NaN / Inf
  - 能产出 conditioned evaluator 所需 artifact

### 验收标准

- 所有 baseline 至少完成 `1-seed`。
- 核心 baseline 全部完成 `3-seed`。
- 每种方法都产出统一 schema 的标准文件。

### 如果失败，优先检查

- 正式环境下模型或 action dim 是否不稳定
- baseline 配置是否仍带有 MiniCAGE 的默认假设
- `PCN` 是否仍需保留为 smoke-only，而不是纳入正式表

---

## Day 3-4：生成正式环境 3-Seed 主表 A 初版

### 要改的文件

- [cmorl_cyborg/evaluate.py](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/evaluate.py)
- [cmorl_cyborg/evaluate_conditioned.py](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/evaluate_conditioned.py)
- [cmorl_cyborg/compare_suite.py](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/compare_suite.py)

### 要做的事

1. 用第二周所有方法的正式环境结果，重新生成 shared reference point。
2. 在统一 reference point 下重评估所有主表 A 方法。
3. 导出 `table_a_summary.json` 和 `table_a_metrics.csv/.tex`。

### 验收标准

- 新的 `shared_reference.json` 来自 `cmorl_cyborg` 结果，而不是 MiniCAGE 结果。
- 所有主表 A 方法都在同一个 reference point 下比较。
- `HV / EU / SP / num_pareto_records / coverage_ratio / unique_assigned_policies` 均有值。

### 如果失败，优先检查

- 是否仍有 checkpoint 重评估路径回退到 `cmorl_minicage`
- conditioned evaluator 是否还在读旧路径或旧 config

---

## Day 4-5：生成正式环境 3-Seed 主表 B 初版

### 要改的文件

- [cmorl_cyborg/evaluate_constraints.py](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/evaluate_constraints.py)
- [cmorl_cyborg/configs/paper/evaluate_main_table_b.yaml](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/configs/paper/evaluate_main_table_b.yaml)

### 要做的事

1. 用正式环境 `stage1-only` 的 Pareto 点重建 shared thresholds。
2. 在这组共享阈值下评估所有表 B 方法。
3. 导出 `table_b_constraints.csv/.tex`。

### 验收标准

- `shared_thresholds.json` 来自 `cmorl_cyborg` 的正式环境结果。
- 所有表 B 方法使用同一组 `d_business / d_cost`。
- 至少以下字段完整：
  - `security_return`
  - `business_return`
  - `cost_return`
  - `feasible_rate`
  - `mean_violation`
  - `final_critical_compromised_hosts`
  - `critical_impact_count`
  - `high_disruption_action_rate`

### 如果失败，优先检查

- `stage1-only` 是否没有足够稳定的 Pareto 点
- threshold 计算是否受异常 seed 强烈影响

---

## Day 5-6：做 3-Seed 结果复盘与准入判断

### 要改的文件

- [docs/EXPERIMENT_LOG.md](/home/waylandlee/CMORL2/Cyber-CMORL/docs/EXPERIMENT_LOG.md)
- 可选补充到 [README.md](/home/waylandlee/CMORL2/Cyber-CMORL/README.md)

### 要做的事

1. 汇总第二周 `3-seed` 的主表 A / B 结果。
2. 逐方法判断：
   - 是否稳定
   - 是否值得带入 `5-seed formal`
3. 对 `PCN` 单独判断：
   - 是否进入正式主表
   - 还是只保留 appendix / smoke
4. 对 `Ours` 做一次是否需要再微调的判断。

### 重点判断问题

1. `Ours` 在 `3-seed` 下是否稳定，不只是单 seed 偶然好。
2. `Weighted-Sum` 是否依然是表 A 的主要对手。
3. `Lagrangian-PPO` 是否依然在表 B 上明显不稳。
4. `Single-objective` 是否依然会对表 B 形成强竞争。
5. `Pref-Cond PPO / PCN` 是否值得保留在正式主表 A。

### 当前补充判断

- 主表 B 原始 `ours_stage2` 结果已经稳定聚合完成。
- `coverage_combo_fair` 在 `Loose` 下改善了 `security_return` 与 `mean_violation`，但 `feasible_rate` 明显下降，因此不能直接替代原始 `ours_stage2`。
- `coverage_combo_fair` 与 `coverage_more_parents_fair` 在 `Loose` 下选中了同一组 policy id，说明 coverage 机制的新增差异目前还不够大。

### 验收标准

- 至少形成一份 `3-seed` 结果复盘结论。
- 能明确写出哪些方法进入 `5-seed formal`。
- 能明确写出是否需要最后一轮微调。

### 如果失败，优先检查

- `3-seed` 是否还不足以稳定判断
- 是否 reward 口径仍导致指标波动过大

---

## Day 6-7：进入 5-Seed Formal 前的最后检查

### 要改的文件

- [cmorl_cyborg/configs/paper](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/configs/paper)

### 要做的事

1. 冻结 `5-seed formal` 的配置和方法名单。
2. 确认所有方法预算对齐。
3. 确认输出路径、共享 reference、共享 thresholds 都已固定。
4. 列出最终运行命令，避免临时手敲。

### 建议的 Formal 准入标准

只有同时满足以下条件，才进入 `5-seed formal`：

1. `reward / semantics` 口径在第二周中途没有再变。
2. `3-seed` 下 `Ours` 和 baseline 的趋势稳定。
3. 主表 A / B 的导表链路无错误。
4. 至少核心方法都能稳定产出完整 artifact。

### 验收标准

- 有一份冻结后的 formal 运行清单。
- 有一组最终 seed 集合，例如 `7 / 11 / 19 / 23 / 29`。
- 已明确：
  - 哪些方法进入主表
  - 哪些方法只进 appendix
  - 哪些方法暂时不进入 formal

---

## 第二周结束时必须回答的 7 个问题

到第二周结束时，必须能明确回答：

1. 哪些方法已经完成正式环境 `3-seed`？
2. 正式环境 shared reference point 是否已经固定？
3. 正式环境 shared thresholds 是否已经固定？
4. 主表 A / B 的 CSV / TEX 是否已经可以稳定导出？
5. `Ours` 是否已经具备进入 `5-seed formal` 的稳定性？
6. 是否还需要最后一轮小调参？
7. 哪些方法进入最终论文主表，哪些只保留 appendix？

如果其中任意 `3` 个问题回答不上来，不建议进入 `5-seed formal`。

---

## 第三周起点

只有当本清单全部完成，才进入第三周任务：

- 跑正式环境 `5-seed formal`
- 导出最终主表 A / 主表 B / appendix
- 写结果分析
- 决定论文中最终 claim 的强弱范围

第二周的成功标准不是“论文结果已经定稿”，而是：

- baseline 已齐
- `3-seed` 已有
- 协议已冻结
- `5-seed formal` 可以低风险启动
