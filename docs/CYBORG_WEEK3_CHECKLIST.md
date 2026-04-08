# CybORG 正式环境第三周执行清单

## 当前状态

截至 `2026-04-08`，第三周文档不应再只写成“准备跑 formal”的计划稿。

当前已经拿到的关键结果包括：

- `paper_table_b` 的原始 `3-seed` 聚合与柱状图；
- `fair_compare_eval` 的 tight / loose 比较图；
- `coverage_combo_fair` 与 `coverage_more_parents_fair` 的新增聚合结果。

因此，第三周最核心的工作已经从“等结果出来”转成“对结果做保守解读并更新所有文档”。

## 目的

本清单承接 [CYBORG_WEEK2_CHECKLIST.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/docs/CYBORG_WEEK2_CHECKLIST.md)。

第三周的目标是把已经稳定的 `cmorl_cyborg` 协议推进到最终论文交付阶段，也就是：

- 完成正式环境 `5-seed formal`
- 生成最终主表 A / 主表 B / appendix
- 固定最终 shared reference point 与 shared thresholds
- 写出结果分析与最终 claim

第三周重点：

- 跑正式环境最终 `5-seed`
- 生成最终表格和结果产物
- 复核所有主结论是否被数据支持
- 冻结论文实验叙事

第三周不做：

- 在 formal 已开始后再改 reward / semantics 口径
- 在结果不满意时临时改协议或换 seed 集
- 在未完成全量结果前先写过强结论

## 第三周总验收标准

到第三周结束时，应满足以下六项：

1. 所有进入主表的方法都完成正式环境 `5-seed formal`。
2. shared reference point 与 shared thresholds 已基于最终 formal 结果冻结。
3. 主表 A / 主表 B / appendix 的 `csv / json / tex` 全部导出完成。
4. 所有结果文件路径、方法名、seed、预算和协议都可追溯。
5. 已完成结果分析，并明确哪些 claim 被支持、哪些不被支持。
6. README / 实验日志 / 方法文档已经同步到最终正式环境结果口径。

### 2026-04-08 回看

- 第 `5-6` 项正是当前最需要补齐的部分。
- 当前文档更新的目标就是让本清单与实际结果对齐。

---

## Day 1：冻结 Formal 运行清单

### 要改的文件

- [cmorl_cyborg/configs/paper](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/configs/paper)
- [docs/CYBORG_WEEK2_CHECKLIST.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/docs/CYBORG_WEEK2_CHECKLIST.md)

### 要做的事

1. 最终确认进入 `5-seed formal` 的方法名单。
2. 最终确认 `5-seed` 集合，例如：
   - `7 / 11 / 19 / 23 / 29`
3. 最终确认训练预算与评估预算。
4. 冻结所有 formal 配置文件，不再改 reward / semantics / seed / 预算。
5. 记录每个方法的运行命令与输出路径。

### 建议进入 Formal 的方法

- `ours_stage2`
- `stage1_only`
- `no_constraint_stage2`
- `weighted_sum`
- `single_objective`
- `lagrangian_ppo`
- `preference_conditioned_ppo`
- `pcn`  

如果某个方法在第二周 `3-seed` 中明显不稳定，可以降级到 appendix 或移出 formal。

### 验收标准

- 有一份明确的 formal 方法名单。
- 有一份明确的 seed 集合。
- 每个方法都有冻结后的 config 文件。
- 方法名单、seed、预算不再临时变更。

### 如果失败，优先检查

- 第二周是否还遗留未解决的稳定性问题
- 是否某些 baseline 仍未跑齐 `3-seed`

---

## Day 1-3：运行正式环境 5-Seed Formal

### 要改的文件

- 原则上不改代码，只运行冻结配置

### 要做的事

1. 按冻结后的 formal 配置运行所有方法。
2. 确保每个方法都完成 `5-seed`：
   - 训练
   - 评估
   - 约束评估
3. 统一检查每个 seed 的输出目录是否完整。

### 每种方法至少要有的产物

- 多策略方法：
  - `solution_buffer.json`
  - `pareto_front_*.json`
  - `metrics.json`
- conditioned 方法：
  - `conditioned_run_metadata.json` 或等价 metadata
  - `evaluated_points.json`
  - `pareto_front_conditioned.json`
  - `metrics.json`
- 约束方法：
  - `constraint_metrics.json`

### 验收标准

- 每种方法都完成 `5-seed`。
- 每个 seed 都有完整 artifact。
- 无 NaN / Inf / 空 front / 评估失败。
- 所有结果目录位于 `cmorl_cyborg/outputs/` 下。

### 如果失败，优先检查

- 是否有单个 seed 特别不稳定
- 是否正式环境时间预算不足导致训练未收敛
- 是否 conditioned evaluator / constraint evaluator 在个别 seed 上崩溃

---

## Day 3-4：冻结最终 Shared Reference 与 Shared Thresholds

### 要改的文件

- [cmorl_cyborg/compare_suite.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/compare_suite.py)
- [cmorl_cyborg/evaluate_constraints.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/evaluate_constraints.py)
- [cmorl_cyborg/configs/paper/compare_suite_main.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/configs/paper/compare_suite_main.yaml)
- [cmorl_cyborg/configs/paper/evaluate_main_table_b.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/configs/paper/evaluate_main_table_b.yaml)

### 要做的事

1. 用所有正式环境主表 A 方法的 final formal 结果，重新计算 shared reference point。
2. 用所有正式环境 `stage1-only` formal Pareto 点，重新计算 shared thresholds。
3. 将这两个量持久化为最终版，不再更新。

### 验收标准

- 最终 `shared_reference.json` 已生成且固定。
- 最终 `shared_thresholds.json` 已生成且固定。
- 所有主表 A 方法都在同一个最终 reference point 下重评估。
- 所有主表 B 方法都在同一个最终 threshold 下重评估。

### 如果失败，优先检查

- 是否有 formal 结果目录缺失或 schema 不一致
- 是否某个方法的 Pareto 点异常拉坏 reference 或 thresholds

---

## Day 4-5：导出最终主表 A / 主表 B / Appendix

### 要改的文件

- [cmorl_cyborg/export_tables.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/export_tables.py)
- [cmorl_cyborg/configs/paper/export_tables_main.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/configs/paper/export_tables_main.yaml)

### 要做的事

1. 导出最终主表 A：
   - `table_a_metrics.csv`
   - `table_a_metrics.tex`
   - `table_a_summary.json`
2. 导出最终主表 B：
   - `table_b_constraints.csv`
   - `table_b_constraints.tex`
3. 导出 appendix：
   - `appendix_ablations.csv`
   - appendix 汇总 JSON
4. 若需要，导出图片：
   - 主表 A 指标图
   - 主表 A pairwise 图
   - 主表 B 柱状图

### 验收标准

- 最终 `csv / tex / json` 均存在。
- 表格中的方法名、seed 聚合、指标名与正文一致。
- 图片若导出，也来自最终 formal 数据，而不是中间版本。

### 如果失败，优先检查

- `export_tables.py` 是否仍读取旧路径
- appendix 路径是否混入 MiniCAGE 结果

---

## Day 5-6：完成结果分析与 Claim 审核

### 要改的文件

- [docs/EXPERIMENT_LOG.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/docs/EXPERIMENT_LOG.md)
- [README.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/README.md)
- 可选补充到 [docs/METHOD_ADACS_DCS_CMORL.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/docs/METHOD_ADACS_DCS_CMORL.md)

### 要做的事

1. 逐表检查最终结论是否被数据支持。
2. 对主表 A 判断：
   - `Ours` 是否真的更能覆盖 Pareto / 适应偏好
3. 对主表 B 判断：
   - `Ours` 是否真的更能处理 cyber constraints
4. 如果数据不支持原始强 claim，及时收紧叙事。

### 必须明确回答的分析问题

1. `Ours` 相比 `Weighted-Sum` 的优势是否存在，存在于哪些指标？
2. `Ours` 相比 `Lagrangian-PPO` 的优势是否稳定，是否足以支撑“更适合 cyber constrained RL”的说法？
3. `Single-objective` 是否在表 B 上形成实质竞争？
4. `no_constraint_stage2` 的消融是否真的证明了 constraint-aware extension 的价值？
5. `Preference-Conditioned PPO / PCN` 在正式环境中是否保留在主表更合理，还是更适合放 appendix？

### 验收标准

- 至少形成一版正式结果分析文字。
- 明确写出以下结论边界：
  - `coverage_combo_fair` 不是对 `ours_stage2` 的严格改进；
  - `Loose` 下 `no_constraint_stage2_fair` 仍是最稳的可行性基线；
  - `Tight` 下当前 coverage 结果不支持强 claim。
- 每个结论都能对应到具体表格或图。
- 不再保留数据不支持的过强 claim。

### 如果失败，优先检查

- 是否还在用 MiniCAGE 的结论套正式环境
- 是否因为方法名或口径变化导致分析错位

---

## Day 6-7：同步文档与最终交付包

### 要改的文件

- [README.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/README.md)
- [docs/EXPERIMENT_LOG.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/docs/EXPERIMENT_LOG.md)
- [docs/MINICAGE_TO_CYBORG_MIGRATION.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/docs/MINICAGE_TO_CYBORG_MIGRATION.md)
- [docs/CYBORG_EXECUTION_CHECKLIST.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/docs/CYBORG_EXECUTION_CHECKLIST.md)
- [docs/CYBORG_WEEK2_CHECKLIST.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/docs/CYBORG_WEEK2_CHECKLIST.md)

### 要做的事

1. 在 README 中补正式环境结果入口与最终产物路径。
2. 在实验日志中记录：
   - 最终 formal 配置
   - seed 集合
   - shared reference
   - shared thresholds
   - 最终表格路径
3. 标记前两周 checklist 为已完成或记录偏差项。
4. 如需要，整理一份最终提交说明。

### 验收标准

- README 中能直接找到正式环境结果路径。
- 实验日志完整记录 formal 运行信息。
- 三周 checklist 状态清晰。

### 如果失败，优先检查

- 是否结果路径仍有临时目录或 `/tmp` 残留
- 是否文档中还保留旧的中间版数字

---

## 第三周结束时必须回答的 8 个问题

到第三周结束时，必须能明确回答：

1. 所有正式环境主表方法是否都完成了 `5-seed formal`？
2. shared reference point 是否已经最终固定？
3. shared thresholds 是否已经最终固定？
4. 主表 A / B / appendix 是否全部导出完成？
5. 哪些 claim 被正式环境结果支持？
6. 哪些 claim 不被支持，需要收紧？
7. 最终应在论文中保留哪些 baseline？
8. 项目是否已经达到“可用于论文正式结果”的状态？

如果其中任意 `2` 个问题回答不上来，就不应对外宣称正式环境实验已经完成。

---

## 第四周起点

只有当本清单全部完成，才进入第四周任务：

- 论文正文实验段落定稿
- 图表美化与排版
- supplementary 细节补全
- 最终代码清理、提交与仓库发布

第三周的成功标准是：

- formal 跑完
- 表格导出
- 结论收敛
- 文档同步

而不是“每一项结果都必须赢”。真正的目标是：

- 结果可信
- 口径一致
- claim 与数据匹配
