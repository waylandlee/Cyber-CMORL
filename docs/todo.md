# 当前待办（暂停扩实验版）

## 当前原则

- 不继续无边界补实验，不再把主要精力放在新增训练和大规模重跑上。
- 当前优先级是把已有结果讲清楚、写完整、整理成可提交的论文与附录材料。
- 如果后续真的恢复方法实验，默认从 `Task 5 / mainline A` 接续，而不是回到旧主线 B 重复补试。

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
