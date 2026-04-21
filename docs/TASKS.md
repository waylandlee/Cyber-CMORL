# Tasks

本文档记录当前复现线的待办、进行中和已完成事项。状态含义如下：

- `Planned`
- `In Progress`
- `Blocked`
- `Done`

## 2026-04-20 V2.4 Snapshot

- `Done` `V2.4 = ours_stage2_fair_critical_safe_v2_4_4obj` 的 `3-seed` 扩展已完成：
  - `seed_0007`
  - `seed_0011`
  - `seed_0019`
- `Done` `3/3 seeds pilot_passed = true`
- `Done` `seed_0011` 的 verifier 回填已完成：
  - `containment_hypothesis_status = evaluable`
  - `containment_hypothesis_triggered_vs_v2_3 = true`
- `Done` `V2.4` 独立 `table_a / table_b` 导表支线已打通：
  - `cmorl_cyborg/outputs/paper_table_v2_4/table_a`
  - `cmorl_cyborg/outputs/paper_table_v2_4/table_b`
  - `cmorl_cyborg/outputs/paper_table_v2_4/tables`
- `In Progress` 当前需要做的不是继续设计 `V2.5`，而是决定：
  - `V2.4 table_b` 是否作为主表 `Table B` 的新增方法行或替换候选
  - `V2.4 table_a` 是否先作为补充表，因为它当前是 `4-objective` 独立口径
- `Planned` 若论文仍保留旧 `3-objective Table A`，则明确把 `V2.4 set-quality row` 视为补充表，不与当前主表 A 直接横向比较

## 2026-04-20 4-Objective Upgrade Execution Plan

### Upgrade Goal

- `In Progress` 将论文主线从旧 `3-objective` 升级为 `4-objective semantic safety`：
  - `security`
  - `business`
  - `cost`
  - `critical_host_safety`
- `In Progress` 主方法固定为 `V2.4 pre-critical containment`，即：
  - `ours_stage2_fair_critical_safe_v2_4_4obj`
- `Planned` 当前默认 paper seed 协议先锁定为 `3-seed = 0007 / 0011 / 0019`，除非后续明确决定扩到 `5-seed`

### Paper-Level Locks Needed First

- `In Progress` 锁定 `4-objective` 论文最终方法名与主方法描述
- `In Progress` 锁定 `Table A` 和 `Table B` 在升级后的主方法集合
- `In Progress` 决定 `Table A` 是否整体升级到 `4-objective`
- `In Progress` 决定 `Table B` 是否直接纳入 `V2.4` 新方法行
- `Planned` 在 paper-level 决策没有锁定前，不再启动 `V2.5`

### Must Rerun Vs Reuse

| 项目 | 论文位置 | 必须重训 | 必须重评估/导表 | 可复用现有产物 | 当前判断 |
|---|---|---:|---:|---|---|
| `ours_stage2_v2_4` set-quality | `Table A` | 否 | 是 | `cmorl_cyborg/outputs/paper_table_v2_4/table_a/` 与 3 个 V2.4 stage2 buffer | 现有 row 只能作 sanity check，最终要在共享 `4D reference point` 下重算 |
| `ours_stage2_v2_4` deployment | `Table B` | 否 | 是 | `seed_*_selected_constraint_metrics.json` 与 `paper_table_v2_4/table_b/aggregated/ours_stage2_v2_4.json` | 当前最接近可直接入论文主表的产物 |
| `stage1_only_4obj` set-quality | `Table A` | 否 | 是 | V2.4 三颗 seed 已完成的 Stage1 buffer | 可直接复用当前 V2.4 Stage1 产物 |
| `stage1_only_4obj` deployment | `Table B` | 否 | 是 | 同上 | 需要重新跑 constraint evaluate 和 aggregation |
| `weighted_sum_4obj` set-quality | `Table A` | 是 | 是 | 无 | 旧 `weighted_sum` 是 `3-objective`，不能直接沿用 |
| `weighted_sum_4obj` deployment | `Table B` | 是 | 是 | 无 | 与上面同一套训练产物顺带导出 |
| `preference_conditioned_ppo_4obj` | `Table A` | 是 | 是 | 无 | 若保留在主表 A，就必须补齐 `4-objective` 版本 |
| `pcn_4obj` | `Table A` | 是 | 是 | 无 | 若保留在主表 A，就必须补齐 `4-objective` 版本 |
| `no_constraint_stage2_4obj` | `Table B / Ablation` | 是 | 是 | 无 | 若主文继续保留 matched ablation，则需要重训 |
| `lagrangian_ppo_4obj` | `Table B` | 是 | 是 | 无 | 若保留在升级后的主表 B，就必须补齐 `4-objective` 版本 |
| `single_objective_4obj` | `Table B` | 是 | 是 | 无 | 需要先定义“单目标”在 `4-objective` 下的 paper 语义 |
| `3-seed semantic risk summary` | 正文结果 / Appendix | 否 | 是 | 三颗 seed 的 final summaries 与 selected risk summaries | 这是 `4-objective` 论文里最关键的正式证据 |
| `V2.3 -> V2.4` 机制对照 | Ablation / Appendix | 否 | 是 | `seed_0011` verifier/backfill 已完成 | `seed_0011` 版已足够，不必强制扩成 `3-seed` |
| `case study / trace appendix` | 正文图 / Appendix | 否 | 是 | 现有 `critical_casebook.md`、semantic audit trace | 不需要重训，只需整理与导出 |

### Minimum Recommended Method Set

- `In Progress` 最小 `4-objective Table A` 方法组建议固定为：
  - `ours_stage2_v2_4`
  - `stage1_only_4obj`
  - `weighted_sum_4obj`
- `Planned` `preference_conditioned_ppo_4obj` 与 `pcn_4obj` 默认先降到 appendix，除非后续确认时间预算充足
- `In Progress` 最小 `4-objective Table B` 方法组建议固定为：
  - `ours_stage2_v2_4`
  - `stage1_only_4obj`
  - `weighted_sum_4obj`
  - `no_constraint_stage2_4obj`
- `Planned` `lagrangian_ppo_4obj` 与 `single_objective_4obj` 只有在 paper-level 决定保留旧 deployment baseline 角色时才补齐

### Concrete Execution Order

- `P0` 锁定升级后的 paper-level 方法组：
  - `Table A` 保留哪些方法
  - `Table B` 保留哪些方法
- `P0` 先产出 `3-seed semantic risk summary`
- `P0` 复用现有 V2.4 和 Stage1-only 产物，补齐无需重训的方法行
- `P0` 重训 `weighted_sum_4obj`
- `P0` 在共享 `4D reference point` 下重建正式 `Table A`
- `P0` 重建 matched `4-objective Table B`
- `P1` 补 `V2.3 -> V2.4` 机制性 ablation
- `P1` 补 case study / trace appendix
- `P2` 再决定是否补：
  - `pcn_4obj`
  - `preference_conditioned_ppo_4obj`
  - `lagrangian_ppo_4obj`
  - `single_objective_4obj`

### Immediate Next Experiments

- `In Progress` 先做 `3-seed semantic risk summary`，不再等待新的训练
- `In Progress` 复用现有产物补一版 `stage1_only_4obj` 的 set-quality 与 deployment 结果
- `Planned` 启动 `weighted_sum_4obj` 的 `3-seed` 训练与导表
- `Planned` 在 `weighted_sum_4obj` 完成后，统一重建 `4-objective Table A`
- `Planned` 在 `Table A` 锁定后，再统一重建 matched `4-objective Table B`

### What Not To Do

- `Planned` 在 `4-objective Table A` 没有重建前，不把当前 `paper_table_v2_4/table_a` 直接当成论文主表 A
- `Planned` 在 `paper-level` 方法组没有锁定前，不同时开启：
  - `pcn_4obj`
  - `preference_conditioned_ppo_4obj`
  - `lagrangian_ppo_4obj`
  - `single_objective_4obj`
- `Planned` 在 `4-objective` 升级完成前，不继续设计 `V2.5`

## CybORG Paper Lock

### 当前主叙事

- `In Progress` 当前论文主线统一锁定为 `集合价值（set value） + 部署价值（deployment value）` 两层结构。
- `Planned` 主文实验固定组织为 4 个模块：
  - `Table A = Set Quality Table`
  - `Table B = Deployment Table`
  - `Figure C = Preference Coverage`
  - `Figure D = Tight Feasible Set Quality`
- `Planned` 当前正式结果口径优先使用 `cmorl_cyborg`，不把 `cmorl_minicage` 的探索升级结果直接混入主文主结果。
- `Planned` 主文只保留少量核心图表；扩展图与更多消融默认下放 appendix。

### 当前主方法集合

- `Planned` `Table A = Set Quality Table` 固定方法组：
  - `ours_stage2`
  - `stage1_only`
  - `weighted_sum`
  - `preference_conditioned_ppo`
  - `pcn`
- `In Progress` `V2.4` 当前不直接写入主表 `Table A` 固定方法组，因为它属于 `4-objective semantic safety` 线，和现有 `3-objective` 主表 A 口径不一致。
- `Planned` `Table B = Deployment Table` 固定方法组：
  - `ours_stage2`
  - `lagrangian_ppo`
  - `weighted_sum`
  - `stage1_only`
  - `no_constraint_stage2`
  - `single_objective`
- `In Progress` `V2.4` 已具备进入 `Table B` 候选行的条件，正在决定是：
  - 作为新增方法行
  - 还是替换当前 `ours_stage2` 主结果行
- `Planned` 主文核心消融默认只保留：
  - `ours_stage2`
  - `stage1_only`
  - `no_constraint_stage2`
  - `weighted_sum` 仅在版面允许时加入
- `Planned` 若某方法尚未在正式 CybORG 线完成统一聚合，则不强行进入主文主表，先放 appendix。

### 当前 claim 约束

- `Planned` 主文允许的强度：
  - `ours_stage2` 在集合级 `HV / EU` 上最好
  - `ours_stage2` 提供更高质量、更广覆盖的候选集合
  - 部署结果强调 `trade-off-aware deployment quality`，不表述为“全指标绝对最优”
  - 严格约束下的价值通过 `tight feasible set` 统计来支撑
- `Planned` 主文禁止直接写：
  - “无条件最优”
  - “在所有指标上都显著领先”
  - “探索线方法已经稳定全面超越正式主线”

## 当前优先级

### P0 最高优先级

- `In Progress` 在当前 `formal_c2` 主线胜出的基础上，继续把 Stage-2 IPO surrogate 向论文 F.2 收紧。
- `In Progress` 研究如何让 Stage-2 前沿从“更强但偏稀”继续向“更满、更均匀”推进。
- `In Progress` 把当前 formal 主线、5-baseline suite 和图像口径同步到 README / docs / 对外展示材料。

### P1 次高优先级

- `Planned` 用更多 seed 验证当前 `formal_c2` 主线胜出结论的稳定性。
- `Done` 增加 [cmorl_minicage/multiseed.py](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_minicage/multiseed.py)，支持按 seed 批跑 `Stage-1 -> Stage-2` 并汇总共享参考点下的稳定性指标。
- `Planned` 系统比较 Stage-2 的 `beta`、`constraint_tolerance`、`constrained_updates` 和 `total_timesteps_per_update`。
- `Planned` 为 Stage-1 增加独立 reseed / 独立 env 模式，降低串行随机耦合。
- `Planned` 为 `visualize.py` 增加可选 policy id 标注与更统一的 figure export 命名。

### P2 中期优先级

- `Planned` 实现 CPO 分支。
- `Planned` 评估是否把 Stage-1 改成真正并行初始化。
- `Planned` 增加更贴近论文 benchmark 的外部验证实验。

## 当前待办

- `In Progress` 把 `V2.4 3-seed` 结果整理成论文可直接复用的实验结论与 case-study。
- `In Progress` 决定 `V2.4 table_b` 是主表替换项、补充方法行，还是 appendix 先行。
- `Planned` 若需要把 `V2.4` 推入主表 A，先定义新的 `4-objective` set-quality 表达方式，而不是直接覆盖旧 `3-objective Table A`。
- `Planned` 更新 `paper/main.tex` 中的方法与实验叙事，使其与 `V2.4` 当前主线一致。

## 进行中

- `In Progress` MiniCAGE C-MORL 论文迁移复现主线维护。
- `In Progress` 文档、配置、输出格式持续对齐，避免代码和记录体系脱节。
- `In Progress` Stage-2 数值行为与论文差异梳理。
- `In Progress` 图像、实验记录与论文展示材料同步更新。
- `In Progress` `V2.4` 结果与主表口径收束：
  - `table_b` 可直接比较
  - `table_a` 当前仅作独立 semantic-safety row

## 已完成

- `Done` 建立独立的 [cmorl_minicage](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_minicage) 工作区。
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
- `Done` 完成 [select_policy.py](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_minicage/select_policy.py)，支持按 preference 选当前最优策略。

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



下面这段可以**直接追加到 `docs/TASKS.md`**。

---

## AdaCS-DCS-CMORL 升级路线（用于指导 Codex 实施）

### 当前策略决策

* `In Progress` 先把当前主线从原始 `Stage-2 crowding selection + fixed beta extension` 升级为 **AdaCS-DCS-CMORL**：

  * `AdaCS` = Adaptive Candidate Selection
  * `DCS` = Dynamic Constraint Scheduling
* `Planned` 保持 `Stage-1` 主体不动，优先升级 `Stage-2`，因为当前代码里 `train_stage2.py` 已明确把“候选选择”和“固定 beta 约束扩展”作为两个核心插拔点，最适合原位升级。
* `Planned` 当前论文先把 **AdaCS-DCS-CMORL** 作为主算法；`robust-opponent` 先作为后续扩展方向和接口预留，不在这一轮实现中强行做成主承诺。
* `Planned` 当前算法升级继续以 `MiniCAGE` 为主要验证场；后续再迁移到 `CybORG`。这一路线与公开 C-MORL 工作关注的 Pareto front discovery 主线一致，也与 CybORG 官方提供的 Gym / PettingZoo wrapper 生态兼容。([OpenReview][1])

### AdaCS 增益验证的下一轮实验设计

* `In Progress` 当前 `AdaCS` 还没有显出独立增益，主要不是因为实现无效，而是因为当前 `E3 Stage-1` 的 Pareto front 只有 `3` 个点，且 `keep_extremes=true` 时这 `3` 个点会被全部保留，导致：

  * `crowding` 与 `adaptive` 在 round 0 选到完全相同的父策略集合
  * 即使 `DCS` 已修复到可生成新点，`AdaCS` 仍然“无点可分”

* `Planned` 下一轮实验的核心目标不是继续调 `beta`，而是**创造一个能让 selection 机制真正产生差异的候选池**。为此实验拆成两步：

  1. 先把 `Stage-1` 做成 candidate-rich 的厚前沿
  2. 再在同一厚前沿上比较 `crowding` 和 `adaptive`

#### G-001 先构造 candidate-rich Stage-1

* `Done` 保持 `independent` 协议不变：

  * `stage1_protocol_name = independent`
  * `reseed_mode = per_preference`
  * `independent_env_per_preference = true`
  * `parallel_workers = 1`

* `Done` 在当前 `E3` 基线之上完成了两组最小增厚：

  * `E3-dense-ckpt`

    * `num_policies = 10`
    * `preference_strategy = explicit`
    * `timesteps_per_policy = 16384`
    * `save_interval_updates = 2`
  * `E3-dense-pref`

    * `num_policies = 12`
    * `preference_strategy = explicit`
    * 在当前 `E3` 的 10 个 preference 上，额外补 2 个中间偏好
    * `timesteps_per_policy = 8192`
    * `save_interval_updates = 2`

* `结果`

  * `E3-dense-ckpt`
    * 已把 `Stage-1` 从 `3` 点增厚到 `8` 点
    * `HV = 6188564.23`
    * `EU = -104.38`
    * 当前已被选为 candidate-rich Stage-1 主基线
  * `E3-dense-pref`
    * 点数虽增多，但整体质量不如 `dense-ckpt`

* `验收标准`

  * `num_pareto_records >= 5`
  * `unique_assigned_policies >= 4`
  * 2D/3D/pairwise 图上不再是单一粗粒度三角壳

#### G-002 在厚前沿上做 AdaCS 主消融

* `Done` 已在 `E3-dense-ckpt` 上完成：

  * `crowding + fixed beta`
  * `adaptive selection + fixed beta`
  * `crowding + dynamic beta (gentle)`
  * `adaptive selection + dynamic beta (gentle)`

* `结果`

  * `crowding + dcs_gentle` 在 dense-front 上先拿到最高 `HV / EU`
  * `AdaCS + fixed beta` 和 `AdaCS + dcs_gentle` 已经显出“更精、更稳、更安全”的独立收益
  * 但第一轮 dense-front 消融里，AdaCS 还没有完成对 `crowding + dcs_gentle` 的主指标反超

  * `num_extension_policies = 4`
  * `extension_rounds = 3`
  * `constrained_updates = 2`
  * `total_timesteps_per_update = 1024`
  * `selection.keep_extremes = true`

* `Planned` 这里故意把 `extension_rounds` 从 `2` 提到 `3`，是为了让 selection 差异能在 round 1/2 累积出来，而不是只比较 round 0。

* `Done` 当前默认 DCS 使用已修复可用的温和区间：

  * `beta_min ≈ 1.000`
  * `beta_max ≈ 1.010`

#### G-003 如果仍然看不出 AdaCS 差异，再加一档 selection pressure

* `Done` 已进一步沿四个方向做持续优化：

  * 更高 `crowding + expansion`
  * `coverage_gain -> marginal coverage`
  * 更友好的 DCS 区间
  * 更高 `num_extension_policies / extension_rounds`

* `结果`

  * `marginal_aggressive / balanced / safe` 已明显把 AdaCS 的 `HV / EU` 推近 `crowding + dcs_gentle`
  * 最终 `chase` 配置完成 `HV / EU` 双反超
    * `HV = 6612380.50`
    * `EU = -100.078`

* `当前结论`

  * 当前主瓶颈已经不是“DCS 太严”或“AdaCS 无点可分”
  * 当前下一步更适合做的是多 seed 验证与 formal 主线整合，而不是继续基础性结构试探

#### G-004 下一轮重点看哪些指标

* `Planned` 不只看最终 `HV / EU`，还要看 selection 层是否真的起作用：

  * 每轮 `selected_policy_ids` 是否出现 `crowding` 和 `adaptive` 的差异
  * `selected_policy_components` 中：

    * `expansion_potential`
    * `utility_coverage_gain`
    * `low_risk_score`
    是否真正影响了入选顺序
  * 每轮 `pareto_size_after_round` 是否更快增长
  * `coverage_ratio` / `unique_assigned_policies` 是否改善
  * 在语义层：

    * `final_compromised_hosts`
    * `critical_impact_count`
    * `high_disruption_action_rate`
    是否在不降低 `HV / EU` 的前提下更优

#### G-005 这一轮实验的判定标准

* `Planned` 只有满足下面至少一条，才算“`AdaCS` 真正显出独立增益”：

  * `adaptive + fixed beta` 明显优于 `crowding + fixed beta`
  * `adaptive + gentle DCS` 明显优于 `crowding + gentle DCS`
  * `adaptive` 在保持相近 `HV / EU` 的同时，能降低：

    * `high_disruption_action_rate`
    * `critical_impact_count`
  * `adaptive` 让 `selection_summary` 中的父策略分布更分散，不再长期集中在同一组极端点

* `Planned` 如果厚前沿 + selection pressure 之后 AdaCS 仍然没有独立增益，则下一步优先怀疑：

  * `selection score` 设计本身还不够区分性
  * `keep_extremes` 的保留逻辑过强
  * 当前 `Stage-2` 的真正瓶颈已从 selection 转向 expansion dynamics

### 本轮升级目标

* `In Progress` 把原始静态 `crowding-based selection` 升级为 **自适应候选选择**。
* `In Progress` 把原始固定 `beta` 的 return-constraint rule 升级为 **动态约束调度**。
* `Planned` 保持当前 `Stage-1 -> Stage-2 -> evaluate -> visualize` 主线可运行，不破坏已有 buffer、summary、metrics 输出格式。
* `Planned` 让新方法能直接在当前 formal / smoke 配置体系下运行，并支持后续做 ablation。

---

### P0 最高优先级：主算法最小闭环

#### A-001 新建方法分支与命名固化

* `Planned` 在代码与文档中固化新算法名：

  * `AdaCS-DCS-CMORL`
  * 中文：自适应候选选择与动态约束调度的受限多目标强化学习算法
* `Planned` 在 README / docs 中统一术语：

  * `Adaptive Candidate Selection`
  * `Dynamic Constraint Scheduling`
  * `selection score`
  * `dynamic beta`
* `验收标准`

  * 文档中不再把当前升级简单描述为“调参版 Stage-2”
  * 新方法命名在配置、summary、plot 标题中保持一致

#### A-002 新建自适应候选选择模块

* `Planned` 新增文件：

  * `cmorl_minicage/algorithms/adaptive_selection.py`
* `Planned` 实现以下函数：

  * `compute_crowding_score(records)`
  * `compute_expansion_potential(records)`
  * `compute_constraint_risk(records)`
  * `compute_utility_coverage_gain(records, preferences, tolerance)`
  * `compute_selection_score(record, components, weights)`
  * `select_top_n_adaptive(records, top_n, preferences, weights, tolerance)`
* `Planned` 先采用可解释的四项打分：

  * `crowding`
  * `expansion_potential`
  * `constraint_risk`
  * `utility_coverage_gain`
* `Planned` 保留原论文 / 当前实现中的 `extreme policy` 默认保留逻辑，不让新打分覆盖掉边界点。当前仓库的 selection 模块与 docs 都已把 extreme policy 保留视为重要机制。
* `验收标准`

  * 可以在不改 `train_stage2.py` 主循环逻辑的前提下，用新接口替换 `select_top_n_by_crowding`
  * summary 中能输出每个被选策略的 4 项子分数与总分
  * extreme policies 始终入选

#### A-003 新建动态 beta 调度模块

* `Planned` 新增文件：

  * `cmorl_minicage/algorithms/dynamic_beta.py`
* `Planned` 实现函数：

  * `compute_dynamic_beta(crowding, expansion, risk, round_idx, total_rounds, beta_min, beta_max, weights)`
* `Planned` 首版动态 beta 仅依赖：

  * 当前候选策略的 crowding score
  * expansion potential
  * constraint risk
  * 当前 extension round
* `Planned` beta 取值统一做 clip：

  * `beta_min <= beta <= beta_max`
* `Planned` 保留退化情形：

  * 当动态项关闭时，完全退化为当前固定 `beta` 版本
* `验收标准`

  * 不改整体训练入口时，可对每个 `base_record × objective_idx × round` 产生独立的 `dynamic_beta`
  * 可在 config 中显式切换：

    * `fixed_beta`
    * `dynamic_beta`

#### A-004 把 AdaCS 接入 `train_stage2.py`

* `Done` 替换当前：

  * `crowding_distance`
  * `select_top_n_by_crowding`
* `Done` 改为：

  * `select_top_n_adaptive(...)`
* `Done` 在 `round_summary` 中新增：

  * `selected_policy_scores`
  * `selected_policy_components`
  * `selection_mode`
* `Done` 当前 `train_stage2.py` 中 selection / extension 交替框架保持不变，只替换“如何选”这一子逻辑，避免无关改动。
* `验收标准`

  * smoke 配置下能跑通
  * 与当前 buffer schema 兼容
  * 不影响已有 `nondominated_filter` 和最终 `pareto_front_stage2.json` 产出

#### A-005 把 DCS 接入 `train_stage2.py` 与 `IPOTrainer`

* `Done` 修改：

  * `cmorl_minicage/train_stage2.py`
  * `cmorl_minicage/algorithms/ipo.py`
* `Done` 将当前固定 `ipo_config.beta` 改为每次扩展动态计算的 `dynamic_beta`
* `Done` 在两处统一替换：

  1. `trainer.update(...)` 使用动态 beta
  2. `candidate_margins = candidate_objectives - (dynamic_beta * current_reference)`
* `Done` 在每条扩展路径记录：

  * `dynamic_beta`
  * `beta_components`
  * `beta_schedule_mode`
* `验收标准`

  * 可以从 config 开关恢复旧版固定 beta
  * 新版运行后，每条 extension record 都能回看 beta 取值
  * `last_constraint_margins` 与 `dynamic_beta` 对应关系清晰可追踪

#### A-006 扩展 record / buffer / summary schema

* `Done` 在 `policy_record.notes` 与 `stage2_summary.json` 中新增字段：

  * `selection_score`
  * `crowding_score`
  * `expansion_potential`
  * `constraint_risk`
  * `utility_coverage_gain`
  * `dynamic_beta`
  * `beta_components`
  * `selection_rank`
* `Done` 保持旧字段不删，保证历史结果仍可读取。当前项目已经把“结构化输出 + 文档日志”作为固定决策。
* `验收标准`

  * 旧 run 不报错
  * 新 run 的 summary 足以支撑后续论文图表

#### A-007 新增最小 smoke 配置

* `Done` 新增：

  * `cmorl_minicage/configs/smoke/stage2_adacs_dcs.yaml`
* `Done` 配置项至少包括：

  * `selection.mode`
  * `selection.score_weights`
  * `selection.utility_tolerance`
  * `ipo.beta_mode`
  * `ipo.beta_min`
  * `ipo.beta_max`
  * `ipo.schedule_weights`
* `验收标准`

  * Codex 能用一条命令跑通 smoke 实验
  * 与当前 `stage1 -> stage2 -> evaluate` CLI 保持一致

---

### P1 次高优先级：评估、可视化、消融

#### A-101 扩展 evaluate 与主结果汇总

* `Planned` 在 `evaluate.py` 中补充新方法字段汇总：

  * selection score 统计
  * dynamic beta 分布
  * 每轮被选中策略的 utility coverage 统计
* `Planned` 在不改变 HV / EU / SP 与 cyber semantic metrics 主体计算方式的前提下，新增方法内部诊断指标。当前项目已固定输出 HV / EU / SP 与安全语义指标。
* `验收标准`

  * `metrics.json` 或新增 `method_diagnostics.json` 能独立反映新方法行为
  * 不破坏当前公平比较流程

#### A-102 扩展可视化

* `Planned` 在 `visualize.py` 新增：

  * `selection_score_breakdown.png`
  * `dynamic_beta_by_round.png`
  * `selected_vs_unselected_policies.png`
  * `front_repair_progress.png`
* `Planned` 优先做论文风格图：

  * round 维度 beta 曲线
  * 被选策略 4 项子分数柱状图
  * AdaCS-DCS vs 原 Stage-2 的 pairwise objective overlay
* `验收标准`

  * 图名统一
  * 可直接纳入后续论文草稿

#### A-103 Ablation 配置与实验矩阵

* `Planned` 新增：

  * `cmorl_minicage/configs/ablation/`

    * `stage2_crowding_fixedbeta.yaml`
    * `stage2_adacs_fixedbeta.yaml`
    * `stage2_crowding_dcs.yaml`
    * `stage2_adacs_dcs.yaml`
* `Planned` 固定四组主消融：

  1. 原始 `crowding + fixed beta`
  2. `adaptive selection + fixed beta`
  3. `crowding + dynamic beta`
  4. `adaptive selection + dynamic beta`
* `Planned` 后续再做权重和 `beta_min / beta_max` 消融
* `验收标准`

  * 4 组实验共用同一 stage1 buffer 与 evaluation config
  * 可以自动输出对比表

---

### P1 次高优先级：理论与文档对齐

#### A-201 新增方法文档

* `Planned` 新增：

  * `docs/METHOD_ADACS_DCS_CMORL.md`
* `Planned` 文档内容至少包括：

  * 问题动机
  * selection score 公式
  * dynamic beta 公式
  * 与原始 C-MORL 的差异
  * 三个性质命题草案：

    * extreme-point preservation
    * monotone conservativeness of dynamic beta
    * fixed-beta as a special case
* `验收标准`

  * 文档中的公式和代码字段一一对应
  * 不出现“文档说一套、代码实现一套”的情况

#### A-202 同步项目文档

* `Planned` 更新：

  * `README.md`
  * `docs/PROJECT_BRIEF.md`
  * `docs/ARCHITECTURE.md`
  * `docs/DECISIONS.md`
* `Planned` 新增一条关键决策：

  * 当前论文主算法采用 `AdaCS-DCS-CMORL`
  * `robust-opponent` 暂不作为本轮主承诺，只做后续扩展方向
* `验收标准`

  * 对外口径统一
  * 不再把当前升级线描述成“仅做 Stage-2 小改”

---

### P2 中期优先级：为 robust-opponent / CybORG 预留接口

#### A-301 预留 attacker-family 接口，但暂不做主实现

* `Planned` 在 config 中预留：

  * `eval.red_policy_list`
  * `training.red_policy_list`
* `Planned` 在 env 包装层预留单条红方 / 多红方切换接口
* `Planned` 当前只需支持：

  * 单 red 正常运行
  * 多 red 评估模式结构不报错
* `验收标准`

  * 不影响当前 MiniCAGE 主线
  * 为后续 robust-opponent 扩展减少重构成本

#### A-302 预留 robust score 钩子

* `Planned` 在 selection / beta scheduler 中预留可选输入：

  * `robust_constraint_risk`
  * `robust_utility_coverage`
* `Planned` 当前先用普通单-red版本；未来 attacker-family 时再替换
* `验收标准`

  * 不强行实现 robust-opponent
  * 但新主算法以后能平滑升级

#### A-303 CybORG 迁移前的接口对齐检查

* `Planned` 在升级完成后单独做一轮检查：

  * 当前 AdaCS-DCS-CMORL 是否仍然只依赖统一 env 接口
  * selection / beta / evaluate 是否与具体环境解耦
* `Planned` 因 CybORG 官方仓库已提供 OpenAI Gym 与 PettingZoo wrappers，后续迁移时应优先保持当前算法主干不动，只替换 env wrapper。([GitHub][2])
* `验收标准`

  * 方法层与环境层边界清晰
  * 不在本轮把 CybORG 迁移和算法升级混做

---

### 当前不做

* `Planned` 暂不把 `robust-opponent` 写成已完成主方法
* `Planned` 暂不同时做：

  * 多 red 训练
  * CybORG 正式迁移
  * CPO 分支重构
  * Stage-1 并行化
* `原因`

  * 当前优先级应放在把 `AdaCS-DCS-CMORL` 做成一个完整、可运行、可消融、可写论文的新主算法
  * 避免同一轮改动里同时引入“问题重定义 + 环境迁移 + 算法升级”三条主线，增加失控风险

---

### 建议 Codex 的实现顺序

1. `A-001` 命名与 config schema 固化
2. `A-002` 实现 `adaptive_selection.py`
3. `A-003` 实现 `dynamic_beta.py`
4. `A-004` 接入 `train_stage2.py` 的 selection
5. `A-005` 接入 `IPOTrainer` 与 feasibility gate
6. `A-006` 扩展 record / summary schema
7. `A-007` 跑 smoke 配置
8. `A-101 ~ A-103` 做评估、可视化、ablation
9. `A-201 ~ A-202` 同步方法文档
10. `A-301 ~ A-303` 预留 robust-opponent / CybORG 接口

---

### 本轮完成标志

* `Done` 新算法 `AdaCS-DCS-CMORL` 有独立命名、独立配置、独立方法文档
* `Done` `train_stage2.py` 不再只支持 `crowding + fixed beta`
* `Done` smoke 实验可跑通
* `Done` 4 组核心 ablation 可复现
* `Done` 图表与 summary 足以支撑论文方法节与实验节
* `Done` 不破坏后续 `robust-opponent` 和 `CybORG` 迁移接口

---

如果你愿意，我下一步就按这份任务路线，继续给你写一版 **“可直接发给 Codex 的实施提示词”**。

[1]: https://openreview.net/forum?id=fDGPIuCdGi&utm_source=chatgpt.com "Efficient Discovery of Pareto Front for Multi-Objective Reinforcement Learning | OpenReview"
[2]: https://github.com/cage-challenge/CybORG?utm_source=chatgpt.com "GitHub - cage-challenge/CybORG: Cyber Operations Research Gym"
