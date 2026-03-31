# Project Brief

## 项目目标

本项目当前的主线是：在 [cmorl_minicage](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage) 中复现论文 *Efficient Discovery of Pareto Front for Multi-Objective Reinforcement Learning (C-MORL)* 的核心训练流程，并将其迁移到 MiniCAGE 网络安全场景。

当前目标聚焦在四件事：

- 保持一条可运行、可验证、可对照的 `Stage-1 -> Stage-2 -> evaluate -> visualize` 主线。
- 用 `security / business / cost` 三目标在 MiniCAGE 中建立可解释的 MORL 训练与评估口径。
- 用统一参考点、统一评估步长和统一语义指标比较主方法与 baseline。
- 沉淀可直接用于写作和汇报的图、表、文档与实验记录。

## 当前定位

当前实现最准确的定位是：

**“论文 C-MORL 方法在 MiniCAGE 上的高保真迁移复现版”**

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

正式配置入口：

- [cmorl_minicage/configs/formal/stage1_c2.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/configs/formal/stage1_c2.yaml)
- [cmorl_minicage/configs/formal/stage2_c2.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/configs/formal/stage2_c2.yaml)
- [cmorl_minicage/configs/formal/evaluate.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/configs/formal/evaluate.yaml)

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

截至 2026-03-31，当前保留并可直接引用的正式结果分为两层。

### Formal 主线

- `Stage-1`
  - [run_446acb6c](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/formal_c2/stage1/run_446acb6c)
- `Stage-2`
  - [run_46e57616](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/formal_c2/stage2/run_46e57616)

统一参考点下：

- `Stage-1`
  - `HV = 362094.86`
  - `EU = -170.55`
  - `Pareto Count = 4`
- `Stage-2`
  - `HV = 601513.12`
  - `EU = -114.70`
  - `Pareto Count = 6`

这说明在当前正式 reward 口径下，`Stage-2` 已经显著优于 `Stage-1`。

### 5-Baseline Suite

当前已重跑并统一评估的 baseline 套餐包括：

- `sleep`
- `random-valid`
- `stage1-only`
- `single-objective`
- `weighted-sum`

统一参考点下的关键结果：

- `Stage-2`
  - `HV = 1699877.00`
  - `EU = -114.69`
  - `Pareto Count = 6`
- `Stage-1 Only`
  - `HV = 1436297.75`
  - `EU = -170.55`
  - `Pareto Count = 4`
- `Single-Objective`
  - `HV = 1412946.75`
  - `EU = -170.83`
  - `Pareto Count = 3`
- `Sleep`
  - `HV = 714105.19`
  - `EU = -229.84`
  - `Pareto Count = 1`
- `Weighted-Sum`
  - `HV = 618307.75`
  - `EU = -189.66`
  - `Pareto Count = 3`
- `Random Valid`
  - `HV = 26100.41`
  - `EU = -454.18`
  - `Pareto Count = 1`

## 当前主结果判断

截至当前代码和实验状态，最稳妥的判断是：

- `Stage-2` 是当前项目里表现最强的正式主方法结果。
- `Stage-2` 不仅优于 formal `Stage-1`，也优于当前保留的 5 个 baseline。
- `Stage-2` 的优势不仅体现在 `HV / EU / Pareto Count`，也体现在核心网络安全语义指标上。
- 当前最需要推进的工作，已经从“证明方法能工作”转向“继续让前沿更满、更均匀、更贴近论文式数值实现”。

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
