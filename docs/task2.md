## AdaCS-DCS-CMORL 升格为主贡献后的任务调整

### 当前策略决策（主贡献版本）

- `In Progress` 当前论文主算法从“cyber-defense-oriented constrained MORL framework”升级为：
  - **AdaCS-DCS-CMORL**
  - 全称：Adaptive Candidate Selection and Dynamic Constraint Scheduling for Constrained MORL in Autonomous Cyber Defense
- `In Progress` 当前论文不再只强调“将两阶段 C-MORL 迁移到 CybORG”，而是明确主张：
  - 在原始两阶段 C-MORL 的基础上，
  - 提出新的 `Stage-2` 机制：
    - `AdaCS`：Adaptive Candidate Selection
    - `DCS`：Dynamic Constraint Scheduling
  - 并证明二者在正式 CybORG 自主防御场景中提升：
    - Pareto candidate set quality
    - preference coverage
    - strict-constraint feasible set quality
    - deployment-oriented utility
- `In Progress` 当前正式主线必须从“原始 ours_stage2”切换为“**AdaCS-DCS-CMORL vs 原始 C-MORL Stage-2**”。
- `Planned` 论文中“新算法”表述仅在以下条件满足后启用：
  - 正式 `cmorl_cyborg` 线完成一致口径重跑
  - 关键消融能证明 AdaCS 和 DCS 各自的独立贡献
  - 多 seed 下趋势稳定
  - tight / loose 约束设定下有一致结论或清晰 trade-off
- `Planned` 若上述条件任一未满足，则回退为：
  - “AdaCS-DCS-CMORL is a promising algorithmic enhancement”
  - 而非“我们提出新的主算法”

---

### 为什么必须这样调整

- `Done` 原始 C-MORL 的主干已经包括：
  - two-stage Pareto initialization + extension
  - crowd-distance-based policy selection
  - fixed-β constrained extension
  - policy assignment
- `Done` 原始论文也已经对：
  - `policy selection`（crowd vs random）
  - `β` 参数
  做过分析，因此如果要把 AdaCS / DCS 抬成主贡献，本轮必须围绕这两处做“**相对原始方法的增量证明**”，而不能只展示最终结果更好。:contentReference[oaicite:2]{index=2} :contentReference[oaicite:3]{index=3}

---

### P0 最高优先级：把 AdaCS-DCS-CMORL 变成正式主算法

#### A-001 统一命名与对外口径

- `Planned` 在以下位置统一使用：
  - `AdaCS-DCS-CMORL`
  - 中文可写为：自适应候选选择与动态约束调度的受限多目标强化学习算法
- `Planned` 更新：
  - `README.md`
  - `docs/PROJECT_BRIEF.md`
  - `docs/ARCHITECTURE.md`
  - `paper/main.tex`
- `Planned` 明确区分以下三者：
  - `Original C-MORL-style Stage-2`
  - `AdaCS-only`
  - `DCS-only`
  - `AdaCS-DCS full`
- `验收标准`
  - 文档和图表标题中不再混用 “ours_stage2 / upgraded stage2 / chase / adaptive / gentle”
  - 正式主文可直接把 AdaCS-DCS-CMORL 当作方法名写入标题、摘要、贡献点

#### A-002 固化“原始 C-MORL-style Stage-2”作为算法基线

- `Planned` 在正式 CybORG 线中单独固化一个对照版本：
  - `crowding + fixed beta`
- `Planned` 该版本在论文里承担“原始 C-MORL 风格 Stage-2”的角色
- `Planned` 所有 AdaCS / DCS 实验与图表默认都要与该版本直接对比
- `验收标准`
  - `cmorl_cyborg` 中存在独立、可复现、命名清晰的 `original_stage2` 或等价目录
  - 所有主消融都以同一 Stage-1 buffer、同一 evaluation protocol 为前提

---

### P0 最高优先级：补齐“独立增益”主消融

#### A-101 完成 2×2 核心消融矩阵（必须）

- `Planned` 在正式 `cmorl_cyborg` 主线中固定以下四组核心消融：
  1. `crowding + fixed beta`
  2. `adaptive selection + fixed beta`
  3. `crowding + dynamic beta`
  4. `adaptive selection + dynamic beta`
- `Planned` 这四组实验共享：
  - 同一 Stage-1 source buffer
  - 同一 seed 集
  - 同一 evaluation config
  - 同一 reference point / thresholds
- `验收标准`
  - 可以清楚回答：
    - AdaCS 单独带来了什么
    - DCS 单独带来了什么
    - 二者组合是否超过单独使用
  - 若无法回答，则不得在主文中写“新算法”

#### A-102 为 2×2 消融输出主指标与集合级指标

- `Planned` 对四组消融统一导出以下指标：
  - `hypervolume`
  - `expected_utility`
  - `coverage_ratio`
  - `unique_assigned_policies`
  - `num_pareto_records`
  - `tight_feasible_candidate_count`
  - `tight_feasible_ratio`
  - `best_feasible_security_return`
- `Planned` 新增：
  - `adacs_dcs_ablation_set_quality.csv`
  - `adacs_dcs_ablation_deployment.csv`
  - `adacs_dcs_ablation_tight_feasible.csv`
- `验收标准`
  - 主文至少有 1 张 AdaCS/DCS 核心消融表
  - appendix 至少有 1 张更完整的 2×2 结果表

#### A-103 证明 AdaCS / DCS 不是“调参增益”

- `Planned` 为 `adaptive selection` 和 `dynamic beta` 各自增加“关闭开关后退化为原始版本”的明确实现与日志记录
- `Planned` 对每个 run 保存：
  - `selection_mode`
  - `beta_mode`
  - `score_weights`
  - `beta_schedule_weights`
  - `beta_min`
  - `beta_max`
- `Planned` 新增 sanity check：
  - `adaptive selection` 关闭后，选择结果应与 `crowding` 一致
  - `dynamic beta` 关闭后，调度结果应退化为固定 `beta`
- `验收标准`
  - 可以从日志和 summary 中复核“新机制已真正启用”
  - 可以排除“只是换了别的默认参数”的质疑

---

### P0 最高优先级：把正式 CybORG 线变成 AdaCS / DCS 的主证据来源

#### A-201 正式 CybORG 主线重跑

- `Planned` 将 AdaCS / DCS 的所有主结论迁移到 `cmorl_cyborg` 正式线验证
- `Planned` 不再只依赖 `cmorl_minicage` 或探索性 `ablation_*` 目录作主证据
- `Planned` 当前至少完成：
  - `3-seed` 正式聚合
  - 若资源允许，扩到 `5-seed`
- `验收标准`
  - AdaCS / DCS 的主表、主图、结论全部来自 `cmorl_cyborg`
  - `cmorl_minicage` 只保留为历史探索和补充证据

#### A-202 tight / loose 双设定验证

- `Planned` 对四组核心消融同时报告：
  - `loose`
  - `tight`
- `Planned` 当前主文优先展示：
  - `loose`：总体集合质量与 deployment utility
  - `tight`：strict-constraint feasible set quality
- `验收标准`
  - 能清楚说明 AdaCS / DCS 在不同约束强度下的行为差异
  - 如果 tight 下不是绝对最好，也能形成清晰 trade-off 解释

#### A-203 多 seed 稳定性验证

- `Planned` 如果 AdaCS / DCS 要抬成主贡献，则正式主结果不能只停留在 3-seed 观察
- `Planned` 最少补以下方法到 5-seed：
  - `AdaCS-DCS full`
  - `crowding + fixed beta`
  - `adaptive + fixed beta`
  - `crowding + dynamic beta`
- `验收标准`
  - 可以在正文中写“trend remains stable across seeds”
  - 如果某一子模块高度不稳定，则不能单独抬为核心 claim

---

### P0 最高优先级：补“机制真的起作用”的中间证据

#### A-301 新增 selection-level diagnostics

- `Planned` 对每轮 selection 输出：
  - `selected_policy_ids`
  - `selected_policy_scores`
  - `selected_policy_components`
  - `selection_rank`
  - `extreme_kept`
- `Planned` 比较 `crowding` 与 `adaptive` 时，重点看：
  - 是否真的选出不同父策略
  - `coverage_gain` / `low_risk` / `expansion_potential` 是否影响了最终入选顺序
- `Planned` 新增图：
  - `selection_score_breakdown.png`
  - `selected_policy_components_by_round.png`
- `验收标准`
  - 可以回答“为什么 AdaCS 会比 crowding 更好”
  - 不是只看到终点指标提升，却看不到选择机制本身的变化

#### A-302 新增 beta-schedule diagnostics

- `Planned` 对每条扩展路径输出：
  - `dynamic_beta`
  - `beta_components`
  - `base_reference_objectives`
  - `candidate_margins`
  - `constraint_gate_passed`
- `Planned` 新增图：
  - `dynamic_beta_by_round.png`
  - `beta_vs_feasibility.png`
  - `beta_vs_front_growth.png`
- `验收标准`
  - 可以回答“DCS 为什么比固定 beta 更合适”
  - 能看到 beta 调度与 front growth / feasibility 的对应关系

#### A-303 新增 front-growth 过程证据

- `Planned` 对四组主消融记录：
  - `pareto_size_after_round`
  - `hv_after_round`
  - `eu_after_round`
  - `coverage_ratio_after_round`
  - `tight_feasible_count_after_round`
- `Planned` 新增图：
  - `front_growth_by_round.png`
  - `hv_eu_by_round.png`
- `验收标准`
  - 能证明 AdaCS / DCS 是“更快、更稳、更有方向地扩展 front”
  - 而不是终点偶然更优

---

### P1 次高优先级：补参数鲁棒性与交互效应分析

#### A-401 AdaCS 权重鲁棒性实验

- `Planned` 固定 DCS，系统比较 AdaCS score 权重组合：
  - `coverage-heavy`
  - `risk-heavy`
  - `balanced`
- `Planned` 目标不是穷举，而是证明 AdaCS 的有效性不依赖单点魔法权重
- `验收标准`
  - 至少 3 组权重配置下趋势一致
  - 可以说明正式主配置不是偶然挑出来的

#### A-402 DCS 范围与调度权重鲁棒性实验

- `Planned` 固定 AdaCS，系统比较：
  - `beta_min / beta_max`
  - `round-progress weight`
  - `risk weight`
  - `expansion weight`
- `Planned` 目标是说明动态调度优于固定 beta 不是建立在脆弱的 schedule 上
- `验收标准`
  - 至少证明 1 个较宽区间内保持优于 fixed beta
  - 若非常敏感，则主文只写“promising enhancement”，不写“robust new algorithm”

#### A-403 与 Stage-1 density 的交互实验

- `Planned` 比较：
  - 稀疏 Stage-1 front
  - dense / candidate-rich Stage-1 front
- `Planned` 目标是回答：
  - AdaCS / DCS 的收益是否依赖“足够厚”的初始 Pareto front
- `验收标准`
  - 正文可说明新算法适用前提
  - 避免被审稿人质疑“只有在特殊 buffer 上才成立”

---

### P1 次高优先级：补主会级安全叙事需要的额外结果

#### A-501 增加 strict-constraint deployment 价值主图

- `Planned` 若 AdaCS / DCS 升为主贡献，则主文必须展示其对“strict constraints 下可部署候选集”的提升
- `Planned` 核心指标：
  - `tight_feasible_candidate_count`
  - `tight_feasible_ratio`
  - `best_feasible_security_return`
- `验收标准`
  - 该图进入主文，而非只在 appendix
  - 可以将 AdaCS / DCS 的改进与“安全部署价值”直接绑定

#### A-502 增加 preference coverage 主图

- `Planned` 当前主文应把 AdaCS / DCS 的一个主价值写成：
  - 更好的 preference-conditioned assignment flexibility
- `Planned` 必须导出：
  - per-preference utility
  - assigned policy diversity
  - feasible preference ratio
- `验收标准`
  - 主文中有至少 1 张 preference coverage 图
  - 这张图能说明 AdaCS / DCS 不只是提高终点 reward，而是提高集合可选性

#### A-503 增加运行代价 / 计算开销报告

- `Planned` 由于原始 C-MORL 本身已经强调 selection 和 extension 的效率与复杂度，本轮若提出 AdaCS / DCS，需报告新增计算开销
- `Planned` 最少报告：
  - wall-clock time
  - per-round selection overhead
  - per-run total extension overhead
- `验收标准`
  - 能说明 AdaCS / DCS 的增益不是以不可接受的额外代价换来的
  - 若代价上升明显，也要给出 trade-off 说明

---

### P1 次高优先级：同步论文结构和贡献点

#### A-601 更新标题、摘要、贡献点（AdaCS / DCS 主贡献版）

- `Planned` 若主实验成立，论文标题改写为显式包含方法名或机制名的版本，例如：
  - `AdaCS-DCS-CMORL for Deployment-Aware Autonomous Cyber Defense`
  - 或保守一点：
    - `Adaptive Candidate Selection and Dynamic Constraint Scheduling for Constrained Multi-Objective Autonomous Cyber Defense`
- `Planned` 摘要中必须明确 3 件事：
  - 原始 C-MORL 风格 Stage-2 的局限
  - AdaCS / DCS 分别解决什么问题
  - 在 CybORG 中带来什么集合级与部署级收益
- `验收标准`
  - 摘要、方法节、实验节的主张全部围绕 AdaCS / DCS 展开
  - 不再把“迁移到 CybORG”写成第一创新点

#### A-602 更新贡献点排序

- `Planned` 当 AdaCS / DCS 升格后，贡献点排序改为：
  1. 提出 AdaCS-DCS-CMORL，作为原始两阶段 constrained MORL 的新算法变体
  2. 将该算法落地到 autonomous cyber defense / CybORG
  3. 提出 deployment-aware set-value + deployment-value 评估协议
  4. 通过正式 CybORG 结果验证其在 preference coverage 与 strict-constraint feasible-set quality 上的收益
- `验收标准`
  - 贡献点不再以“迁移 / operationalize”为首
  - 主文逻辑先算法，后场景，最后评估

---

### 当前不做

- `Planned` 若 AdaCS / DCS 升格为主贡献，则不再把“只做迁移”作为主卖点
- `Planned` 暂不再引入新的更大算法分支（如额外 CPO 完整重构），避免分散主贡献
- `Planned` 暂不同时把论文扩成完整红蓝双学习体 / 对抗博弈主线
- `原因`
  - 本轮需要把 novelty 牢牢集中在 `Stage-2` 的算法升级上
  - 过多新分支会削弱 AdaCS / DCS 的可解释性和可防守性

---

### 建议 Codex 的实现顺序（AdaCS / DCS 主贡献版）

1. `A-001 ~ A-002`
   - 统一命名与固化原始 Stage-2 对照版本
2. `A-101 ~ A-103`
   - 跑 2×2 核心消融并确保可复现
3. `A-201 ~ A-203`
   - 在正式 `cmorl_cyborg` 线完成 3-seed / 5-seed 验证
4. `A-301 ~ A-303`
   - 增加 selection / beta / front-growth 诊断输出
5. `A-401 ~ A-403`
   - 做最小参数鲁棒性与 Stage-1 density 交互验证
6. `A-501 ~ A-503`
   - 生成主文级 preference coverage / tight-feasible / runtime 图
7. `A-601 ~ A-602`
   - 同步改写标题、摘要、贡献点与方法节
8. 再回到 `paper/main.tex`
   - 以 AdaCS-DCS-CMORL 为主算法完成初稿

---

### 本轮完成标志（AdaCS / DCS 主贡献版）

- `Done` AdaCS / DCS 在正式 `cmorl_cyborg` 线完成统一口径验证
- `Done` 2×2 核心消融能清楚证明二者独立贡献
- `Done` 多 seed 与 tight / loose 结果足以支撑主文 claim
- `Done` 有 selection / beta / front-growth 的机制性证据
- `Done` 主文标题、摘要、贡献点已切换到 AdaCS-DCS-CMORL 主算法版本
- `Done` 可以合理使用：
  - “we propose AdaCS-DCS-CMORL”
  - “a new algorithmic variant”
  - “an adaptive-selection and dynamic-constraint-scheduling framework”