# CybORG 正式环境第四周执行清单

## 当前状态

截至 `2026-04-08`，第四周最现实的入口已经很明确：

- 图已经有了；
- `3-seed` 主表 B 和 fair compare 聚合已经有了；
- 现在最需要的是把结论写稳，而不是继续堆新实验。

因此，本清单里的任务应优先理解为“文档整理与最终叙事清理”。

## 目的

本清单承接 [CYBORG_WEEK3_CHECKLIST.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/docs/CYBORG_WEEK3_CHECKLIST.md)。

第四周的目标不再是“把实验跑出来”，而是把已经完成的正式环境结果整理成可交付的论文与仓库成果，也就是：

- 论文实验段落定稿
- 图表排版与展示定稿
- supplementary / appendix 材料补全
- 代码、文档、结果目录清理
- 最终提交与发布准备

第四周重点：

- 让结果表达清楚、可信、可复现
- 让论文中的 claim 与最终数据完全对齐
- 让仓库中的正式环境入口、配置、产物路径一目了然

第四周不做：

- 在正文定稿后再修改实验协议
- 在结果不变的前提下反复追加无关实验
- 在未同步文档时先做最终公开发布

## 第四周总验收标准

到第四周结束时，应满足以下六项：

1. 论文实验部分已经有一版与正式环境结果一致的最终文字。
2. 主表 A / 主表 B / appendix 图表已经完成定稿排版。
3. supplementary / appendix 中的方法细节、配置与额外结果已经补齐。
4. 仓库中的 `cmorl_cyborg` 使用说明、配置入口、结果路径都已同步到 README。
5. 正式环境结果目录、配置目录、文档目录已经清理完毕，可直接交付。
6. 代码与文档已达到可提交、可推送、可归档状态。

---

## Day 1：冻结论文叙事与结果边界

### 要改的文件

- 论文正文草稿文件
- [docs/EXPERIMENT_LOG.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/docs/EXPERIMENT_LOG.md)
- [README.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/README.md)

### 要做的事

1. 重新确认正式环境下最终要讲的结论。
2. 明确哪些结论是“强支持”，哪些只能“部分支持”。
3. 决定正文保留哪些 baseline，哪些只放 appendix。
4. 冻结实验叙事，不再改方法名、表名、指标名。

### 必须明确的叙事问题

1. 主表 A 主要想证明什么？
2. 主表 B 主要想证明什么？
3. `Ours` 的最强卖点到底是：
   - Pareto coverage
   - preference adaptation
   - constraint stability
   - cyber semantic robustness
   - 还是这几项里的某个组合
4. 是否需要主动收紧不被结果完全支持的 claim

### 当前应优先固定的叙事边界

- 不把 `coverage_combo_fair` 写成对原始 `ours_stage2` 的全面超越。
- 不把 `Loose` 下 coverage 的局部提升扩展成普遍结论。
- 不把 `Tight` 下仍不稳定的结果写成正式主卖点。

### 验收标准

- 有一版冻结后的实验叙事摘要。
- 所有主结论都能映射到最终表格或图。
- 不再保留与最终结果冲突的旧叙事。

### 如果失败，优先检查

- 是否仍混用 MiniCAGE 结论和正式 CybORG 结论
- 是否表 A / 表 B 的目标定义还不够聚焦

---

## Day 1-2：完成主表 A / 主表 B 图表定稿

### 要改的文件

- 图表生成脚本或 notebook
- [cmorl_cyborg/export_tables.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/export_tables.py)
- 最终图片输出目录

### 要做的事

1. 确认主表 A 的最终展示形式：
   - 指标表
   - pairwise 图
   - 可选综合图
2. 确认主表 B 的最终展示形式：
   - 约束指标表
   - 柱状图
3. 调整图题、图例、方法名、颜色和坐标轴。
4. 确保正文中的方法名与图表中的方法名完全一致。

### 图表定稿检查项

- 方法排序是否固定
- 颜色是否一致
- 标题和 caption 是否直观
- 坐标轴是否说明“越大越好/越小越好”
- 条件方法与多策略方法是否区分清楚

### 验收标准

- 主表 A / 主表 B 所有图片已导出最终版。
- `csv / tex / png` 对应同一版数据。
- 图表无需再做结构性修改，只允许微调格式。

### 如果失败，优先检查

- 是否仍在使用中间版 summary 文件
- 是否方法名在图表和表格中不一致

---

## Day 2-3：补全 Supplementary / Appendix

### 要改的文件

- 论文 supplementary / appendix 草稿
- [docs/METHOD_ADACS_DCS_CMORL.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/docs/METHOD_ADACS_DCS_CMORL.md)
- [docs/ARCHITECTURE.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/docs/ARCHITECTURE.md)
- [docs/DECISIONS.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/docs/DECISIONS.md)

### 要做的事

1. 补齐算法细节：
   - Stage-1
   - Stage-2
   - adaptive selection
   - dynamic beta
2. 补齐正式环境 reward / semantics 定义。
3. 补齐 appendix 结果：
   - `stage1-only`
   - `no-constraint stage2`
   - `single-objective`
   - `multiseed summary`
4. 记录不进入主表的方法和原因。

### 验收标准

- supplementary 中可找到所有正式环境关键实现说明。
- appendix 中的实验与正文主表形成清晰分工。
- 读者能从 supplementary 复现关键协议。

### 如果失败，优先检查

- 是否关键实现细节只存在聊天记录中，没有落文档
- 是否 appendix 结果还没和正式环境路径对齐

---

## Day 3-4：整理仓库文档与用户入口

### 要改的文件

- [README.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/README.md)
- [cmorl_cyborg/README.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/README.md)
- [docs/MINICAGE_TO_CYBORG_MIGRATION.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/docs/MINICAGE_TO_CYBORG_MIGRATION.md)
- [docs/CYBORG_EXECUTION_CHECKLIST.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/docs/CYBORG_EXECUTION_CHECKLIST.md)
- [docs/CYBORG_WEEK2_CHECKLIST.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/docs/CYBORG_WEEK2_CHECKLIST.md)
- [docs/CYBORG_WEEK3_CHECKLIST.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/docs/CYBORG_WEEK3_CHECKLIST.md)

### 要做的事

1. 在 README 中明确区分：
   - `cmorl_minicage`
   - `cmorl_cyborg`
2. 给出正式环境推荐阅读顺序：
   - 迁移文档
   - 第 1-4 周 checklist
   - 方法文档
3. 给出正式环境的关键运行命令：
   - train
   - evaluate
   - compare
   - export
4. 明确最终结果目录与配置目录。

### 验收标准

- 新读者只看 README 就能找到正式环境入口。
- README 中所有链接都有效。
- 文档结构不混乱，MiniCAGE 与 CybORG 边界清晰。

### 如果失败，优先检查

- 是否 README 仍以 MiniCAGE 为主、正式环境入口不明显
- 是否 checklist 文档没有串起来

---

## Day 4-5：清理代码、配置与结果目录

### 要改的文件

- 仓库内所有正式环境相关代码和配置

### 要做的事

1. 清理不用的临时配置、临时脚本、临时输出路径。
2. 检查 `/tmp` 中的临时调试产物是否已转存或不再需要。
3. 统一配置命名、方法名、输出目录命名。
4. 清理文档中的中间版数字和失效路径。

### 清理检查项

- 是否还有 `/tmp/...` 路径残留在文档中
- 是否还有 smoke 临时命令被写进正式 README
- 是否有旧结果文件可能被误认成正式结果
- 是否有文件名仍带 `smoke`、`debug`、`tmp` 但实际想作为正式文件保留

### 验收标准

- 仓库目录结构清晰，正式结果与中间结果分离。
- 配置和输出命名统一。
- 文档中不再引用无效路径或临时目录。

### 如果失败，优先检查

- 是否 formal 结果和 smoke 结果混在同一层目录
- 是否 README 中命令仍指向调试版本

---

## Day 5-6：准备最终提交与发布说明

### 要改的文件

- [README.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/README.md)
- 提交说明或发布说明文档

### 要做的事

1. 整理最终提交说明：
   - 加了什么
   - 如何复现
   - 关键结果在哪
2. 检查 Git 状态，确认要提交的文件范围。
3. 准备最终推送前的摘要说明。
4. 如果有需要，准备补充 release note。

### 验收标准

- 有一份清晰的最终提交摘要。
- 代码、配置、文档和结果目录都能解释清楚。
- 推送前没有不确定是否应提交的关键文件。

### 如果失败，优先检查

- 是否工作区仍有大量无关改动
- 是否某些重要文档还没纳入提交范围

---

## Day 6-7：最终复核与交付

### 要改的文件

- 无新增文件，主要做复核

### 要做的事

1. 逐项复核：
   - 结果
   - 文档
   - 配置
   - 代码入口
2. 再次确认论文主结论与最终数据一致。
3. 最终确认仓库达到了“可交付”状态。

### 最终复核问题

1. 所有正式环境结果是否可追溯到配置和 seed？
2. 所有主表 / 图 / appendix 是否都来自最终 formal 结果？
3. 所有 claim 是否被结果支持？
4. README 是否足够指导他人复现？
5. 仓库是否已经适合最终提交、推送和对外展示？

### 验收标准

- 有一版最终交付前复核结论。
- 剩余问题只限于小的排版或文字修正。
- 仓库可以进入最终提交与发布阶段。

### 如果失败，优先检查

- 是否还有结果和文档不一致
- 是否还有 formal / appendix / smoke 结果混淆

---

## 第四周结束时必须回答的 8 个问题

到第四周结束时，必须能明确回答：

1. 论文实验部分是否已经定稿？
2. 主表 A / B / appendix 图表是否已经全部定稿？
3. supplementary 是否已经补齐关键细节？
4. README 是否已经能完整引导正式环境复现？
5. 仓库中是否还存在影响交付的临时文件或临时路径？
6. 最终 claim 是否已经与数据完全对齐？
7. 项目是否已经达到可提交、可推送、可归档状态？
8. 是否已经可以进入最终发布或论文提交阶段？

如果其中任意 `2` 个问题回答不上来，就不应做最终发布。

---

## 第五周起点

只有当本清单全部完成，才进入第五周任务：

- 论文全文定稿与投稿材料整理
- 最终开源发布
- 可能的 rebuttal / supplementary 补充准备

第四周的成功标准是：

- 文本定稿
- 图表定稿
- 文档定稿
- 仓库可交付

而不是继续追加实验。真正目标是：

- 结果表达清楚
- 证据链完整
- 项目可复现
