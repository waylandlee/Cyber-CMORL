# Tasks

本文档用于记录当前复现线的待办、进行中和已完成事项。状态含义如下：

- `Planned`
- `In Progress`
- `Blocked`
- `Done`

## 当前优先级

### P0 最高优先级

- `In Progress` 收紧 Stage-2 IPO surrogate，使其更接近论文 F.2 的数值语义。
- `In Progress` 系统分析 Stage-2 feasibility gate 对有效 front extension 的影响。
- `Planned` 明确 Stage-2 中“generated point 多但 HV/EU 不升”的具体成因，并沉淀成代码或配置层面的修正方案。

### P1 次高优先级

- `In Progress` 基于当前已跑结果，沉淀正式实验建议配置。
- `Planned` 为 Stage-1 增加独立 reseed / 独立 env 的训练模式，降低串行随机耦合。
- `Planned` 评估是否需要把 Stage-1 改成真正并行初始化。
- `Planned` 为图像输出增加更论文风格的标注、字号和统一版式。

### P2 中期优先级

- `Planned` 实现 CPO 分支。
- `Planned` 增加更贴近论文原 benchmark 的外部验证实验。
- `Planned` 研究从 MiniCAGE 迁移到更复杂 CybORG++ 任务时的 reward/objective 继承方案。

## 当前待办

- `In Progress` 继续把 Stage-2 IPO surrogate 向论文训练细节收紧。
- `In Progress` 继续调 Stage-2 约束超参，找到“能保持 feasibility 且能产生有效 extension”的稳定区间。
- `In Progress` 把当前 config profile 的使用经验沉淀成更明确的运行建议。
- `Planned` 补一版“正式实验推荐配置”说明，回答不同目标下该优先用哪组 Stage-2 配置。
- `Planned` 为 `visualize.py` 增加按点标注 policy id 的可选开关。
- `Planned` 增加一组 Stage-1 初始化策略比较实验：
  - `grid`
  - `dirichlet`
  - `dirichlet_extremes`

## 进行中

- `In Progress` MiniCAGE C-MORL 论文迁移复现主线维护。
- `In Progress` 文档、配置、输出格式持续对齐，避免代码和记录体系脱节。
- `In Progress` Stage-2 调参结果解释与可视化整理。
- `In Progress` 论文流程 vs 当前实现差异梳理。

## 已完成

- `Done` 建立独立的 [cmorl_minicage](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage) 工作区。
- `Done` 完成 Stage-1 / Stage-2 / evaluation 首版可运行链路。
- `Done` 完成 reward vector 与 MiniCAGE 标量奖励的严格对账。
- `Done` 完成 YAML 配置驱动入口。
- `Done` 完成 P0 收紧：IPO surrogate 与 Stage-2 feasibility gate。
- `Done` 完成 P1 收紧：Stage-1 preference 初始化、泛化 HV、训练过程统计。
- `Done` 完成配置模板分层、README 入口补充和实验记录体系初版。
- `Done` 跑通 Stage-2 调参实验：
  - `conservative`
  - `balanced`
  - `relaxed`
  - `beta_1005`
  - `beta_1020`
  - `steps_1024`
  - `steps_1536`
  - `tol_025`
  - `tol_075`
- `Done` 统一生成 Stage-2 ablation 的 `metrics.json`。
- `Done` 增加结果可视化：
  - Pareto projections
  - 3D Pareto scatter
  - Stage-1 vs Stage-2 overlay
  - assignment counts
  - Stage-2 round plots
  - 论文风格总对比图
- `Done` 完成 README 中“论文算法流程 vs 当前代码流程”的对照整理。

## 关键观察驱动的任务

### O-001 Stage-2 可行但不一定有效

- 观察：
  - 某些配置会生成更多 Stage-2 policy，但 HV / EU 并不随之显著提升。
- 推导任务：
  - `In Progress` 检查当前 IPO barrier 与真实 evaluation 之间的偏差来源。
  - `Planned` 对比“保存所有 feasible 点”与“只保存 best feasible”的差异。

### O-002 `beta_1005` 和 `tol_025` 在当前 seed 下等效

- 观察：
  - 这两组配置在当前实验中得到完全一致的指标。
- 推导任务：
  - `Planned` 验证这种等效性是否仅限于当前 seed 和当前 Stage-1 buffer。

### O-003 `steps_1536` 有很高 EU，但 coverage 很低

- 观察：
  - `steps_1536` 的 `EU` 最高，但 `coverage_ratio` 和 `unique_assigned_policies` 很低。
- 推导任务：
  - `Planned` 分析它是否适合作为“专家型 policy”补充分支，而非默认 Stage-2 配置。

## 风险与阻塞

- `Risk` Stage-2 当前对约束阈值很敏感，小改动就可能把 front 推回严格门控区。
- `Risk` 当前 IPO 数值实现仍然是近似版，可能限制与论文原结果的严格可比性。
- `Risk` Stage-1 串行初始化会拖慢更大规模实验，影响后续 seed 扩展和正式统计。
- `Risk` MiniCAGE reward decomposition 虽已对账，但 objective 定义本身仍是本地设计，不可直接等同论文 benchmark objective。

## 下一步建议

- `Planned` 跑一组正式 `formal` 配置实验并写入 [EXPERIMENT_LOG.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/docs/EXPERIMENT_LOG.md)。
- `Planned` 基于 `ablation` 模板系统比较 Stage-2：
  - `beta`
  - `constraint_tolerance`
  - `total_timesteps_per_update`
- `Planned` 为 `beta_1005`、`steps_1536`、`relaxed` 三条线各自整理一份“使用建议”。
- `Planned` 评估是否要引入：
  - 真正并行的 Stage-1 worker
  - 更贴论文的 IPO return 估计
  - 更细粒度的 Stage-2 candidate 保存策略
