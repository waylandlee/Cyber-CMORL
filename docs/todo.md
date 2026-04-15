# 当前待办（暂停扩实验版）

## 当前原则

- 不继续无边界补实验，不再把主要精力放在新增训练和大规模重跑上。
- 当前优先级是把已有结果讲清楚、写完整、整理成可提交的论文与附录材料。
- 如果后续真的恢复方法实验，默认从 `Task 5 / mainline A` 接续，而不是回到旧主线 B 重复补试。

## 如果恢复实验（最新顺序）

- `A1 + route_near` 仍然是这条线最后一个清晰可解释的恢复基线，不要再回退到 `A0/A2/A3` 或旧主线 B。
- `semantic checkpoint` 只保留为 side finding：
  - 它改善了 hybrid fallback 的 `final_critical`
  - 但没有恢复 strict pool
- `final_critical` 单轴增强 (`route_near_fc_w2`) 也已经验证：
  - strict 仍为 `0`
  - 没有触发继续跑 `fc_w4` 的条件
- 因此默认策略已经更新为：
  - **不再继续 Dual-Archive + CVaR 这条局部 reweighting 线**
  - 将其作为 limitation 写入正文与 appendix
- 只有当后续出现新的机制性改动方向，而不是继续调权重/阈值时，才重新打开这条实验线。

## P0 文档与论文

- 补齐 `paper/main.tex` 的实验节文字：
  - `Environment and Threat Model`
  - `Objectives, Constraints, and Evaluation Protocol`
  - `Baselines`
  - `Metrics`
  - `Candidate Set Quality`
  - `Deployment Quality`
  - `Preference Coverage`
  - `Tight Feasible Set Quality`
  - `Ablation`
- 把主文中的 claim 全部校准到当前结果：
  - 强调 `set value + deployment value`
  - 避免“所有指标全面最优”式表述
  - 把 held-out attacker 明确写成 appendix stress test / limitation
- 补 appendix 仍缺的实验细节：
  - 训练协议
  - 约束阈值
  - fair-compare 说明
  - strict / hybrid 选择语义
  - business / cost 语义解释

## P0 结果整理

- 把主表、主图、结果文件路径和文字口径统一起来，避免图表命名与正文叙事不一致。
- 为当前结果补一份“图表到数据源”的映射清单，方便后续写作和答辩引用。
- 统一说明哪些结果属于：
  - 主文证据
  - appendix 证据
  - limitation / stress test
- 补充最新 `Task 5 v3-A` 后续结果的统一口径：
  - `route_near` 修复了 route，但没有恢复 strict
  - `semantic checkpoint` 改善了 hybrid fallback 的 `final_critical`，但仍未形成 strict-deployable pool
  - 最终 strict 判断应以正式评估的 `archive_diagnostics` / `metrics_strict` 为准，而不是训练期 diagnostics

## P1 项目文档同步

- 同步 `README.md`、`docs/PROJECT_BRIEF.md`、`docs/ARCHITECTURE.md` 与当前方法命名。
- 检查 `docs/DECISIONS.md` 是否需要追加“暂停扩实验、优先文档收口”的最新决策。
- 保持根目录 `task*.md`、`results.md`、`docs/TASKS.md` 三类文档的分工清晰：
  - `task*.md` 记录任务背景与详细过程
  - `results.md` 记录跨任务结果摘要
  - `docs/TASKS.md` 记录总状态与阅读入口

## P1 交付准备

- 整理匿名 artifact / open-science appendix / reproducibility 说明。
- 检查最终提交包里是否已经包含：
  - 关键配置路径
  - 主要图表来源
  - 结果复现入口
  - 必要的环境说明
