# Project Brief

## 项目目标

本项目当前的主线已经分成两层：

- 历史复现与升级探索线：
  [cmorl_minicage](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage)
- 正式环境结果线：
  [cmorl_cyborg](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg)

当前对外口径应优先以 `cmorl_cyborg` 为准；`cmorl_minicage` 主要用于保留算法迁移背景、历史探索和升级思路。

当前目标聚焦在四件事：

- 保持一条可运行、可验证、可对照的 `Stage-1 -> Stage-2 -> evaluate -> visualize` 主线。
- 用 `security / business / cost` 三目标在 MiniCAGE 中建立可解释的 MORL 训练与评估口径。
- 用统一参考点、统一评估步长和统一语义指标比较主方法与 baseline。
- 沉淀可直接用于写作和汇报的图、表、文档与实验记录。

## 当前定位

当前实现最准确的定位是：

**“C-MORL 在 MiniCAGE 完成迁移验证，并在正式 CybORG 上形成统一 3-seed 对比口径的双线项目”**

而不是：

**“论文原 benchmark 上的逐项同构复现版”**

这意味着：

- 算法主骨架已经与论文对齐：
  - Stage-1 Pareto initialization
  - Stage-2 policy selection + constrained extension
  - SMP assignment
  - HV / EU / SP evaluation
- 但环境、奖励定义、IPO 数值实现和工程化 gate 仍然是本地适配。

## 当前范围

当前范围包括：

- MiniCAGE 多目标环境包装
- `security / business / cost` 三目标奖励建模
- Stage-1 Pareto initialization
- Stage-2 IPO-style constrained extension
- SMP assignment
- HV / EU / SP + 网络安全语义评估
- baseline 套餐与统一公平比较
- 图像与文档输出

当前不包含：

- 论文原 benchmark 的逐任务复刻
- CPO 分支
- 多 GPU / 多 worker Stage-1 并行训练
- 论文结果的一比一数值复现声明

## 当前主线代码

- [cmorl_minicage/env.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/env.py)
- [cmorl_minicage/train_stage1.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/train_stage1.py)
- [cmorl_minicage/train_stage2.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/train_stage2.py)
- [cmorl_minicage/evaluate.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/evaluate.py)
- [cmorl_minicage/visualize.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/visualize.py)
- [cmorl_minicage/baselines.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/baselines.py)
- [cmorl_minicage/select_policy.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/select_policy.py)

正式配置入口当前分为两条：

- 已发布 formal 主线：
  - [cmorl_minicage/configs/formal/stage1_c2.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/configs/formal/stage1_c2.yaml)
  - [cmorl_minicage/configs/formal/stage2_c2.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/configs/formal/stage2_c2.yaml)
  - [cmorl_minicage/configs/formal/evaluate.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/configs/formal/evaluate.yaml)
- 当前升级主线：
  - [cmorl_minicage/configs/formal/stage1_c2_independent.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/configs/formal/stage1_c2_independent.yaml)
  - [cmorl_minicage/configs/formal/stage2_c2_adacs_dcs.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/configs/formal/stage2_c2_adacs_dcs.yaml)

## 当前三目标定义

当前环境正式采用三目标：

- `security`
  - 刻画失陷主机、关键资产 impact、关键残留失陷和 no-op under compromise 的安全后果。
- `business`
  - 刻画蓝方动作及 no-op under compromise 对业务扰动造成的代价。
- `cost`
  - 刻画动作本身和 no-op under compromise 的操作成本。

三目标统一按“越大越好”解释；由于数值通常为负，实际阅读上等价于“越接近 0 越好”。

当前默认 reward 已固化为 `C2 / cand_g` 校准版本，其目的有两个：

- 消除 `sleep` 在统一 HV / EU 下的异常占优问题。
- 保留 `Weighted-Sum` 等强 baseline 的非支配前沿结构。

## 当前正式结果概况

截至 `2026-04-08`，项目文档应优先阅读 `cmorl_cyborg` 的正式环境 `3-seed` 结果。

### CybORG 主表 B

原始主表 B 的 `ours_stage2` 聚合结果位于：

- [ours_stage2.json](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/paper_table_b/aggregated/ours_stage2.json)
- [main_table_b_bar.png](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/paper_table_b/main_table_b_bar.png)

其代表性指标为：

- `security_return = -518.70 ± 17.16`
- `feasible_rate = 0.800 ± 0.089`
- `mean_violation = 0.380 ± 0.300`
- `final_critical_compromised_hosts = 0.817 ± 0.024`
- `high_disruption_action_rate = 0.954 ± 0.012`

### CybORG Fair Compare + Coverage

新增 coverage 公平比较结果位于：

- [coverage_combo_fair_loose.json](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/fair_compare_eval/aggregated/coverage_combo_fair_loose.json)
- [coverage_more_parents_fair_loose.json](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/fair_compare_eval/aggregated/coverage_more_parents_fair_loose.json)
- [fair_compare_table_b_loose_with_coverage.png](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/fair_compare_eval/aggregated/fair_compare_table_b_loose_with_coverage.png)
- [fair_compare_table_b_tight_with_coverage.png](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/fair_compare_eval/aggregated/fair_compare_table_b_tight_with_coverage.png)

当前最保守的结论是：

- `Loose` 下，`coverage_combo_fair` 比原始 `ours_stage2` 有更好的 `security_return`、更低的 `mean_violation`，但 `feasible_rate` 明显更低，因此不是严格改进。
- `coverage_combo_fair` 与 `coverage_more_parents_fair` 在 `Loose` 下选中了同一组 policy id，说明二者效果接近，`combo` 只是在聚合结果上更均衡。
- `Loose` 下最稳的可行性基线仍是 `no_constraint_stage2_fair`，其 `feasible_rate = 0.892 ± 0.042`，`mean_violation = 0.084 ± 0.054`。
- `Tight` 下所有方法的可行性都明显变差，coverage 变体没有形成清晰优势，因此当前不宜围绕 `tight` 结果写强 claim。

## 当前主结果判断

截至当前代码和实验状态，最稳妥的判断是：

- `cmorl_cyborg` 已经具备可以支撑论文写作的 `3-seed` 主表 B 和公平比较产物。
- 原始 `ours_stage2` 仍然是当前正式主线的重要参照，但不应再被表述成“无条件最好”。
- 新的 `coverage_combo_fair` 更像偏重回报与平均违约的替代方案，不是对原始 `ours_stage2` 的严格升级。
- `fair_compare_eval` 的价值主要在于帮助收紧 claim，而不是证明 coverage 机制已经稳定优于所有旧方法。

## 当前升级线状态

当前最活跃的升级线不是直接替换 `legacy formal_c2`，而是：

- `independent Stage-1`
  - 去除串行随机耦合
  - 当前默认基线已切到 `E3` explicit preference 设计
- `AdaCS-DCS-CMORL`
  - `Stage-2` 支持：
    - `crowding + fixed beta`
    - `adaptive selection + fixed beta`
    - `crowding + dynamic beta`
    - `adaptive selection + dynamic beta`

当前这条升级线的最新判断是：

- 原始 `DCS(0.88~0.98)` 在 independent 协议下过严，曾导致 `generated = 0`
- 把 `dynamic beta` 调整到围绕 `1.005` 的温和区间后，DCS 已恢复到和 `fixed beta` 同水平
- `E3-dense-ckpt` 已把 independent `Stage-1` 从 `3` 点增厚到 `8` 点，并把 `HV / EU` 提升到：
  - `HV = 6188564.23`
  - `EU = -104.38`
- 在 dense-front 上，`AdaCS` 已显出独立收益；当前 `AdaCS-DCS` 的正式主配置已经升级为 `chase`
- `AdaCS-DCS chase` 在统一参考点下已经实现对 `crowding + dcs_gentle` 的 `HV / EU` 双反超：
  - `HV = 6612380.50`
  - `EU = -100.078`

当前升级线最值得记住的两条结果是：

- candidate-rich `Stage-1`
  - [e3_dense_ckpt/run_011d7162](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/formal_c2_independent_stage1_density/e3_dense_ckpt/run_011d7162)
- 当前最强 `AdaCS-DCS`
  - [chase/run_57a6c14a](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/ablation_adacs_dcs_marginal/chase/run_57a6c14a)

## 当前保留的关键图

主结果图：

- [formal_c2_mainline_metrics.png](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/plots/formal_c2_mainline_metrics.png)
- [formal_c2_mainline_semantics.png](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/plots/formal_c2_mainline_semantics.png)
- [formal_c2_core_security.png](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/plots/formal_c2_core_security.png)

目标空间图：

- [formal_c2_compact_objective_map.png](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/plots/formal_c2_compact_objective_map.png)
- [formal_c2_objective_3d_comparison.png](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/plots/formal_c2_objective_3d_comparison.png)
- [formal_c2_pairwise_objectives.png](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/plots/formal_c2_pairwise_objectives.png)

6 方法公平比较图：

- [formal_c2_suite_metrics.png](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/plots/formal_c2_suite_metrics.png)
- [formal_c2_suite_3d.png](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/plots/formal_c2_suite_3d.png)
- [formal_c2_suite_pairwise.png](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/plots/formal_c2_suite_pairwise.png)

## 当前最关键的差异点

当前实现与论文真正拉开差距的地方主要有四个：

1. Stage-1 仍是串行训练，不是论文默认的并行初始化。
2. IPO 是 PPO-compatible 的近似实现，barrier 仍作用在 surrogate return 上。
3. Stage-2 使用工程化 feasibility gate，且每条扩展路径只保留 `best_feasible`。
4. 环境、奖励和任务形式均为 MiniCAGE 适配版，而非论文原 benchmark。

## 推荐阅读顺序

1. [README.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/README.md)
2. [docs/PROJECT_BRIEF.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/docs/PROJECT_BRIEF.md)
3. [docs/ARCHITECTURE.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/docs/ARCHITECTURE.md)
4. [docs/DECISIONS.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/docs/DECISIONS.md)
5. [docs/TASKS.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/docs/TASKS.md)
6. [docs/EXPERIMENT_LOG.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/docs/EXPERIMENT_LOG.md)
