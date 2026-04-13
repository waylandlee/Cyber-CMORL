# 项目任务总览（2026-04-13）

## 当前总决策

- 当前不再继续无边界扩实验，优先转为文档补齐、论文成稿、结果口径统一。
- 正式对外结论继续以 `cmorl_cyborg` 为主；`cmorl_minicage` 主要保留为共享实现层和历史探索证据。
- 如果后续恢复方法实验，默认从 `Task 5 / mainline A (CVaR conservative branch)` 继续，而不是回到旧的主线 B 反复补跑。

## 任务状态总览

### Task 0 - 总体实验判断与论文口径备忘

- Status: active reference
- 作用：记录当前最重要的实验结论、论文 claim 边界、fair-compare 口径和答辩表述。
- 当前结论：
  - 不需要再新增一整套大实验。
  - 当前更重要的是补 appendix 细节、统一 Figure/Table 口径、校准主文 claim 强度。
  - held-out attacker 更适合作为 appendix stress test，而不是主卖点。
- 主文件：`task0.md`

### Task 2 - AdaCS-DCS 升格为主贡献的任务调整

- Status: partially completed / historical roadmap
- 已形成内容：
  - `AdaCS / DCS` 作为主算法增量的命名、2x2 核心消融框架、正式 CybORG 证据优先级。
  - loose / tight 双设定与多 seed 稳定性的目标口径。
- 当前说明：
  - 这份任务更像方法定位与论文路线图。
  - 其中的关键判断已经被后续 `task0.md`、`task4.md`、`results.md` 吸收。
- 主文件：`task2.md`

### Task 3 - Dual-Archive Stage-2 实现

- Status: completed
- 已完成资产：
  - `A_cons / A_uc / union_front` 双档案结构
  - dual-archive routing
  - strict / hybrid selector 所需的基础 schema 和实现入口
  - 共享层主实现改造，`cmorl_cyborg` 继续只做薄封装
- 当前说明：
  - Task 3 解决的是“怎么把双档案方法真正实现出来”。
  - 它是后续 Task 4 / Task 5 的工程基础，不再是当前最需要补的文档缺口。
- 主文件：`task3.md`

### Task 4 - Dual-Archive 评估与选择语义

- Status: completed
- 已完成资产：
  - `union / strict / hybrid` 三套评估与部署选择语义
  - archive-aware evaluation / compare / export pipeline
  - B-fix 之后的 smoke 与 fair-budget 决策门
- 最终结论：
  - 即使在补齐 strict 字段、cost gate 与诊断后，主线 B 仍未建立 strict candidate pool。
  - 因此，如果未来继续做方法推进，应正式转向 `mainline A / CVaR conservative branch`。
- 主文件：`task4.md`
- 结果摘要：`results.md`

### Task 5 - 在主线 B 基础上推进 mainline A（CVaR conservative branch）

- Status: paused
- 目标：
  - 保留 Task 3 / 4 的 dual-archive 框架。
  - 仅把失效的 conservative branch 升级为 risk-aware 的 `A_cons`。
- 当前说明：
  - 任务设计、v2 补充和 v3-A 结果已经写入 `task5.md` / `results.md`。
  - 但按照当前项目决策，先暂停继续实验，优先把已有结论整理成论文和文档。
- 主文件：`task5.md`
- 结果摘要：`results.md`

## 推荐阅读顺序

1. `task0.md`：看当前最高层判断、实验口径和论文表述边界。
2. `results.md`：看 Task 4 / Task 5 的跨任务结果摘要与结论。
3. `task3.md`、`task4.md`、`task5.md`：按实现、评估、后续主线切换的顺序看详细过程。
4. `todo.md`：看当前在“不继续扩实验”前提下的文档与论文待办。

## 当前仍需补齐的文档方向

- `paper/main.tex` 里的实验节、指标说明、baseline 口径与当前结果保持完全一致。
- appendix 中仍空缺的实验细节、协议说明与图表解释需要补齐。
- `README` / `PROJECT_BRIEF` / `ARCHITECTURE` 的方法命名与最终论文口径仍需统一。
- artifact / open-science / reproducibility 相关说明还需要整理成可提交版本。
