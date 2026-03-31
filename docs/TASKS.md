# Tasks

本文档记录当前复现线的待办、进行中和已完成事项。状态含义如下：

- `Planned`
- `In Progress`
- `Blocked`
- `Done`

## 当前优先级

### P0 最高优先级

- `In Progress` 在当前 `formal_c2` 主线胜出的基础上，继续把 Stage-2 IPO surrogate 向论文 F.2 收紧。
- `In Progress` 研究如何让 Stage-2 前沿从“更强但偏稀”继续向“更满、更均匀”推进。
- `In Progress` 把当前 formal 主线、5-baseline suite 和图像口径同步到 README / docs / 对外展示材料。

### P1 次高优先级

- `Planned` 用更多 seed 验证当前 `formal_c2` 主线胜出结论的稳定性。
- `Planned` 系统比较 Stage-2 的 `beta`、`constraint_tolerance`、`constrained_updates` 和 `total_timesteps_per_update`。
- `Planned` 为 Stage-1 增加独立 reseed / 独立 env 模式，降低串行随机耦合。
- `Planned` 为 `visualize.py` 增加可选 policy id 标注与更统一的 figure export 命名。

### P2 中期优先级

- `Planned` 实现 CPO 分支。
- `Planned` 评估是否把 Stage-1 改成真正并行初始化。
- `Planned` 增加更贴近论文 benchmark 的外部验证实验。

## 当前待办

- `In Progress` 整理 formal `Stage-1 / Stage-2 / baseline suite` 的正式对比说明。
- `In Progress` 把 pairwise / 3D / compact objective 图进一步统一成论文展示风格。
- `Planned` 增加 `business` 与 `cost` 的更结果化语义指标。
- `Planned` 为 `select_policy.py` 增加默认最新 buffer 选择模式，减少命令行参数输入。

## 进行中

- `In Progress` MiniCAGE C-MORL 论文迁移复现主线维护。
- `In Progress` 文档、配置、输出格式持续对齐，避免代码和记录体系脱节。
- `In Progress` Stage-2 数值行为与论文差异梳理。
- `In Progress` 图像、实验记录与论文展示材料同步更新。

## 已完成

- `Done` 建立独立的 [cmorl_minicage](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage) 工作区。
- `Done` 完成 Stage-1 / Stage-2 / evaluation 首版可运行链路。
- `Done` 完成 YAML 配置驱动入口。
- `Done` 完成 IPO surrogate + Stage-2 feasibility gate 工程实现。
- `Done` 把环境奖励口径切换到 `security / business / cost`。
- `Done` 完成 reward 校准，消除 `sleep` 在公平 HV / EU 下的异常占优。
- `Done` 固化 `C2 / cand_g` 作为当前默认正式 reward 口径。
- `Done` 完成 formal 主线重跑：
  - `Stage-1`
  - `Stage-2`
- `Done` 完成 5 个 baseline 的正式重跑：
  - `sleep`
  - `random-valid`
  - `stage1-only`
  - `single-objective`
  - `weighted-sum`
- `Done` 完成统一 reference point 下的 baseline suite 重评估。
- `Done` 完成核心语义指标：
  - `final_compromised_hosts`
  - `final_critical_compromised_hosts`
  - `critical_impact_count`
  - `recovered_hosts`
  - `analyse_count`
  - `remove_count`
  - `restore_count`
  - `high_disruption_action_rate`
- `Done` 完成主结果图与 suite 图：
  - `formal_c2_mainline_metrics.png`
  - `formal_c2_mainline_semantics.png`
  - `formal_c2_core_security.png`
  - `formal_c2_compact_objective_map.png`
  - `formal_c2_objective_3d_comparison.png`
  - `formal_c2_pairwise_objectives.png`
  - `formal_c2_suite_metrics.png`
  - `formal_c2_suite_3d.png`
  - `formal_c2_suite_pairwise.png`
- `Done` 完成 [select_policy.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/select_policy.py)，支持按 preference 选当前最优策略。

## 关键观察驱动的任务

### O-001 当前 Stage-2 已经成为正式最优方法

- 观察：
  - 在统一参考点下，`Stage-2` 的 `HV / EU / Pareto Count` 均优于 `Stage-1` 和 5 个 baseline。
- 推导任务：
  - `In Progress` 解释当前优势来自 reward 校准、前沿扩展，还是两者共同作用。
  - `Planned` 用多 seed 验证该优势的稳定性。

### O-002 当前前沿更强，但仍偏稀

- 观察：
  - `Stage-2` 的 `Pareto Count = 6`，`HV` 很高，但 `Coverage Ratio` 仍不是最满。
- 推导任务：
  - `In Progress` 继续研究如何让 front 更均匀、更“满”。
  - `Planned` 对比“只保留 best feasible”与“保留 top-k feasible”的差异。

### O-003 `Weighted-Sum` 仍是重要强 baseline

- 观察：
  - 在当前口径下它已不再最优，但仍然是最值得保留的学习型强 baseline。
- 推导任务：
  - `Planned` 保留它作为后续主结果对照的稳定参照组。

## 风险与阻塞

- `Risk` Stage-2 仍对约束阈值和扩展预算敏感。
- `Risk` IPO 仍是 surrogate 近似实现，限制与论文数值过程的严格同构性。
- `Risk` Stage-1 串行训练仍会拖慢更大规模 seed 扩展。
- `Risk` `business` 与 `cost` 的结果化语义指标仍不如 `security` 完整。

## 下一步建议

- `In Progress` 把当前 formal 主线和 5-baseline suite 的结果写成对外可直接引用的实验结论。
- `Planned` 基于当前 `formal_c2` 结果做多 seed 验证。
- `Planned` 继续收紧 IPO 数值实现，使其更贴近论文 F.2。
- `Planned` 评估是否要引入：
  - 并行 Stage-1 worker
  - top-k feasible Stage-2 保存
  - 更细粒度的 semantic evaluation
