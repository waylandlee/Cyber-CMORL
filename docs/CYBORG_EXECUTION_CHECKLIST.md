# CybORG 正式环境执行版清单

## 状态说明

本文件主要记录第一阶段把 `cmorl_cyborg` 从迁移骨架推进到可跑通主表链路的执行计划。

截至 `2026-04-08`，这份清单应被视为“已完成的历史执行计划”，不是当前最高优先级待办。当前优先级已经转到：

- 同步 `paper_table_b` 与 `fair_compare_eval` 的真实结果；
- 统一 README、周报、实验日志中的结论边界；
- 避免把早期执行计划误读成当前项目状态。

## 目的

本清单是 [MINICAGE_TO_CYBORG_MIGRATION.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/docs/MINICAGE_TO_CYBORG_MIGRATION.md) 的执行版补充。

目标不是继续扩展想法，而是把当前 [cmorl_cyborg](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg) 从“已跑通迁移骨架”推进到“可支撑正式环境调参与后续论文 formal”的状态。

本周重点：

- 固定正式 `CybORG` 的 reward / semantics 口径
- 提升环境适配可信度
- 建立正式环境上的 dev 调参闭环
- 为下周 `3-seed` 和 `5-seed formal` 做准备

本周不做：

- 直接跑正式 `5-seed formal`
- 直接对外宣称正式环境结果
- 在 reward 口径未稳定前做大规模 baseline 横评

## 本周总验收标准

到本周结束时，应满足以下四项：

1. [cmorl_cyborg/reward.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/reward.py) 与 [cmorl_cyborg/semantics.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/semantics.py) 具有明确、文档化的正式定义。
2. [cmorl_cyborg/env.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/env.py) 在多 seed、多步 rollout 下稳定，且 `reward_terms` / `semantic_info` 字段完整。
3. `Stage-1 -> Stage-2 -> evaluate -> evaluate_constraints -> compare_suite -> export_tables` 在 `cmorl_cyborg` 线上都可跑通。
4. 已经形成一组可用于下周正式调参的 `dev` 配置，并完成 `dev + holdout` 两个 seed 的小预算验证。

---

## Day 1-2：固定 Reward / Semantics 口径

### 要改的文件

- [cmorl_cyborg/reward.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/reward.py)
- [cmorl_cyborg/semantics.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/semantics.py)
- [docs/MINICAGE_TO_CYBORG_MIGRATION.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/docs/MINICAGE_TO_CYBORG_MIGRATION.md)

### 要做的事

1. 把 `security / business / cost` 写成正式口径，不再停留在“迁移近似版”。
2. 明确 `security` 由哪些 compromise / critical impact / recovery 项构成。
3. 明确 `business` 由哪些 operational / critical host 受损或扰动构成。
4. 明确 `cost` 由哪些 Blue actions 或恢复操作代价构成。
5. 明确以下语义量的判定规则：
   - `critical host`
   - `critical impact`
   - `recovered_hosts`
   - `high_disruption_action`
6. 在文档中写清“为什么这样定义”，避免后续调参时口径漂移。

### 验收标准

- `reward.py` 中每个目标的组成项都能口头解释清楚。
- `semantics.py` 中每个语义指标都能对应到正式环境中的状态或事件。
- 不再只依赖 hostname 前缀做关键指标定义，至少要有清晰、稳定的规则来源。
- 文档中有一段简要说明：
  - 定义来源
  - 近似项有哪些
  - 后续还需校准什么

### 如果失败，优先检查

- 当前 `ChallengeWrapper` 暴露的信息是否不足以支撑正式定义
- 是否需要在 [cmorl_cyborg/env.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/env.py) 中补 true-state diff 或 helper 提取

---

## Day 2-3：提升环境适配可信度

### 要改的文件

- [cmorl_cyborg/env.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/env.py)
- [cmorl_cyborg/rollout_smoke.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/rollout_smoke.py)

### 要做的事

1. 检查 `num_envs > 1` 时的批量封装是否稳定。
2. 检查 `seed` 传播是否一致，避免不同 env 实例意外共享轨迹。
3. 补充更多 rollout smoke 断言：
   - `obs.shape` 稳定
   - `reward_vec.shape[-1] == 3`
   - `reward_terms` 字段完整
   - `semantic_info` 字段完整
4. 记录不同 Blue 动作类别下 reward / semantics 是否符合直觉。

### 验收标准

- 连续 rollout `100` steps 不报错。
- 至少 `3` 个不同 seed 下 smoke 均通过。
- `reward_terms` 中 `security / business / cost` 每步都存在。
- `semantic_info` 中正式评估所需字段每步都存在。
- 同一 seed 重跑时，分布行为基本一致。

### 如果失败，优先检查

- `_SingleCybORGEnv` 的 reset / step 后状态更新是否漏掉 true-state 刷新
- 多实例封装是否引入了过强的同步性
- wrapper 返回的动作或 observation 是否在某些步骤动态变化

---

## Day 3-4：建立正式环境 Dev 调参闭环

### 要改的文件

- [cmorl_cyborg/configs/smoke/stage1_smoke.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/configs/smoke/stage1_smoke.yaml)
- [cmorl_cyborg/configs/smoke/stage2_smoke.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/configs/smoke/stage2_smoke.yaml)
- [cmorl_cyborg/configs/paper/stage1_main.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/configs/paper/stage1_main.yaml)
- [cmorl_cyborg/configs/paper/stage2_main.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/configs/paper/stage2_main.yaml)

### 要做的事

1. 准备一份 `dev seed` 配置。
2. 准备一份 `holdout seed` 配置。
3. 让这两份配置都能跑完整个闭环：
   - `train_stage1`
   - `train_stage2`
   - `evaluate`
   - `evaluate_constraints`
4. 确认主表 A / B 所需 artifact 都会产出。

### 验收标准

- `Stage-1` 能输出：
  - `solution_buffer.json`
  - `stage1_summary.json`
  - `pareto_front_stage1.json`
- `Stage-2` 能输出：
  - `solution_buffer.json`
  - `stage2_summary.json`
  - `method_diagnostics.json`
- `evaluate.py` 能输出 `metrics.json`
- `evaluate_constraints.py` 能输出 `constraint_metrics.json`
- 至少存在 1 个非空 Pareto front
- 不出现 NaN / Inf / 空 buffer / 全路径 `generated = 0`

### 如果失败，优先检查

- `reward` 尺度是否导致 Stage-2 barrier 过强或过弱
- `constraint_tolerance` 是否过严
- `total_timesteps_per_update` 是否太小

---

## Day 4-5：先做 Ours 的正式环境小规模调参

### 要改的文件

- [cmorl_cyborg/configs/paper/stage1_main.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/configs/paper/stage1_main.yaml)
- [cmorl_cyborg/configs/paper/stage2_main.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/configs/paper/stage2_main.yaml)

### 优先调的超参

- `barrier_coef`
- `beta`
- `beta_min`
- `beta_max`
- `constraint_tolerance`
- `constrained_updates`
- `total_timesteps_per_update`
- Stage-1 / Stage-2 预算比例

### 要做的事

1. 先只用 `1` 个 `dev seed` 跑 4-8 组配置，不要过多。
2. 每组都检查表 A 与表 B，不接受“只提升一张表”的配置。
3. 先保留方法结构不变，优先调环境敏感数值超参。

### 验收标准

- 至少得到 `1-2` 组明显优于初始迁移版的配置。
- 这些配置在 `feasible_rate`、`mean_violation` 上没有彻底恶化。
- `Stage-2` 的可行扩展路径没有明显塌缩。

### 建议的保底规则

- 不接受 `feasible_rate` 明显低于当前迁移基线的配置。
- 不接受 `mean_violation` 大幅爆炸的配置。
- 不接受 Pareto front 为空的配置。

---

## Day 5-6：做 Holdout 验证

### 要改的文件

- 无需新增文件，主要是复用 `dev` 阶段筛出的配置

### 要做的事

1. 选出 `dev` 上最好的 `1-2` 组配置。
2. 在 `holdout seed` 上重复同样流程。
3. 对比 `dev` 与 `holdout` 指标趋势是否一致。

### 验收标准

- `holdout seed` 不崩。
- 指标趋势与 `dev seed` 基本一致。
- 没有出现“dev 很好，holdout 完全失真”的情况。

### 如果失败，优先检查

- 是否在 `MiniCAGE` 上遗留过强的超参偏置
- 是否 reward 口径仍过于脆弱，对 seed 太敏感

---

## Day 6-7：为下周 Formal 做准备

### 要改的文件

- [cmorl_cyborg/compare_suite.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/compare_suite.py)
- [cmorl_cyborg/export_tables.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/export_tables.py)
- [cmorl_cyborg/configs/paper/compare_suite_main.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/configs/paper/compare_suite_main.yaml)
- [cmorl_cyborg/configs/paper/export_tables_main.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/configs/paper/export_tables_main.yaml)

### 要做的事

1. 用正式 `cmorl_cyborg` 结果重建 shared reference point。
2. 用正式 `cmorl_cyborg` 的 `stage1-only` 结果重建 shared thresholds。
3. 确认 `compare_suite`、`evaluate_constraints`、`export_tables` 都能只消费正式环境产物。

### 验收标准

- 能生成新的 `shared_reference.json`
- 能生成新的 `shared_thresholds.json`
- 能导出：
  - `table_a_metrics.csv`
  - `table_a_metrics.tex`
  - `table_b_constraints.csv`
  - `table_b_constraints.tex`

### 如果失败，优先检查

- 评估脚本中是否仍有回落到 `cmorl_minicage` 环境假设的地方
- metrics schema 是否仍沿用旧路径或旧默认值

---

## 本周结束时必须回答的 6 个问题

到周末前，必须能明确回答：

1. 正式 `CybORG` 上 `security / business / cost` 的最终工作定义是什么？
2. `critical host` 和 `critical impact` 的正式判定规则是什么？
3. `Stage-1` 与 `Stage-2` 是否都能在正式环境上稳定跑通？
4. `dev + holdout` 两个 seed 下，是否存在一致更优的配置趋势？
5. `compare_suite` 和 `export_tables` 是否已经完全接上正式环境产物？
6. 下周是否具备启动 `3-seed` 的条件？

如果其中任意 2 个问题回答不上来，就不建议进入 `3-seed formal`。

---

## 下周起点

只有当本清单全部完成，才进入下周任务：

- 正式环境 baseline 重跑
- `3-seed` 汇总
- shared reference / thresholds 固定
- 最后才是 `5-seed formal`

本周的成功标准不是“数值已经最好”，而是：

- 口径稳定
- 链路可信
- 配置可调
- 下周可以正式开始追结果
