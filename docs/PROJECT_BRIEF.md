# Project Brief

## 项目目标

本项目当前的独立主线是：在不干扰 `CybORG_plus_plus` 其他研究路径的前提下，在 [cmorl_minicage](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage) 中复现论文 *Efficient Discovery of Pareto Front for Multi-Objective Reinforcement Learning (C-MORL)* 的核心训练流程，并将其迁移到 MiniCAGE 场景。

当前目标聚焦在四件事：

- 做出一条可运行、可验证、可对照的 MiniCAGE C-MORL 复现线。
- 尽量向论文训练细节收紧，同时明确记录与原论文 benchmark 的差异。
- 建立稳定的配置、输出、文档和可视化体系，支持后续正式实验和写作。
- 基于 Stage-2 的调参结果，明确当前最有效的扩展配置和后续优化方向。

## 当前定位

当前实现最准确的定位是：

**“论文 C-MORL 算法思想在 MiniCAGE 上的高保真迁移复现版”**

而不是：

**“论文原 benchmark 上的逐项同构复现版”**

这意味着：

- 算法骨架已经和论文高度对齐：
  - Stage-1 Pareto initialization
  - Stage-2 policy selection + constrained extension
  - SMP assignment
  - HV / EU / SP evaluation
- 但实验环境、reward/objective 定义、IPO 数值实现和 Stage-2 工程门控仍然存在本地适配。

## 范围

当前范围包括：

- MiniCAGE 多目标环境包装
- Stage-1 Pareto initialization
- Stage-2 selection + IPO-style Pareto extension
- SMP assignment
- HV / EU / SP evaluation
- YAML 配置驱动训练与评估
- 统一 buffer / summary / experiment logging
- 可视化脚本与论文风格对比图输出

当前不包含：

- 论文原 benchmark 的逐任务原样复刻
- CPO 分支实现
- 多进程/多 GPU 的 Stage-1 并行初始化训练
- 与仓库其他训练主线的深度整合
- 论文结果的数值级一比一复现声明

## 当前主线

当前主线代码位于：

- [cmorl_minicage/env.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/env.py)
- [cmorl_minicage/train_stage1.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/train_stage1.py)
- [cmorl_minicage/train_stage2.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/train_stage2.py)
- [cmorl_minicage/evaluate.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/evaluate.py)
- [cmorl_minicage/visualize.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/visualize.py)

当前默认实验入口：

- [cmorl_minicage/configs/stage1.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/configs/stage1.yaml)
- [cmorl_minicage/configs/stage2.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/configs/stage2.yaml)
- [cmorl_minicage/configs/evaluate.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/configs/evaluate.yaml)

## 配置层次

为避免把“冒烟验证”和“正式实验”混在一起，配置模板分为三层：

- `smoke`
  - 用于最小链路验证，预算小，优先确认训练和评估流程不报错。
- `formal`
  - 用于较完整的论文式运行，预算更高，统计更稳定。
- `ablation`
  - 用于单点对比，例如 Stage-2 约束强度、`beta`、`constraint_tolerance`、每次扩展 timesteps 等。

当前额外已经积累出一组 `local_search` 风格的 Stage-2 配置，用于围绕当前最敏感的超参数做局部扫描。

## 当前结果概况

截至 2026-03-31，当前主线已经具备：

- 可独立运行的 `stage1 -> stage2 -> evaluate -> visualize` 完整链路。
- 稳定的结构化产物：
  - `solution_buffer.json`
  - `stage1_summary.json`
  - `stage2_summary.json`
  - `pareto_front_*.json`
  - `metrics.json`
- 针对 Stage-2 的一轮较完整调参实验和可视化解释。

当前最重要的实验结论如下：

- Stage-1 已经能在 MiniCAGE 上产生有 trade-off 结构的 Pareto front。
- 默认严格 Stage-2 配置经常会被 feasibility gate 过早截断。
- 当前最好的一组综合 Stage-2 配置是：
  - `beta=1.005`
  - 或等价现象下的 `constraint_tolerance=-0.25`
- 当前最好的一组“整体 front 扩展”结果来自：
  - [stage2_beta_1005/run_89adf296](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/ablation/local_search/stage2_beta_1005/run_89adf296)
  - 关键指标：
    - `HV = 2873.94`
    - `EU = -125.33`
    - `Pareto Count = 9`
- 当前最好的一组“高 expected utility 但偏集中化”的结果来自：
  - [stage2_steps_1536/run_28007b1b](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/ablation/local_search/stage2_steps_1536/run_28007b1b)
  - 关键指标：
    - `HV = 2757.88`
    - `EU = -103.23`
    - `Pareto Count = 7`
    - `Assigned Policy Variety = 2`

## 当前最关键的差异点

当前实现与论文真正拉开差距的地方主要有四个：

1. Stage-1 现在是串行训练，不是论文强调的并行初始化。
2. IPO 是 PPO-compatible 的近似实现，barrier 作用在 surrogate return 近似上，而不是真实 `G_i^π` 本体。
3. Stage-2 增加了工程化 feasibility gate，并且每条扩展路径只保留 `best_feasible` 结果。
4. 实验环境、reward/objective 定义和任务形式已经被 MiniCAGE 本地适配。

这些差异不会否定当前工作的算法价值，但会影响：

- 与论文原结果的严格可比性
- Stage-2 的数值行为
- Stage-1 的工程效率
- 调参时对 feasibility 的敏感度

## 输出约定

所有复现线输出默认写入 [cmorl_minicage/outputs](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs)，每次 run 目录下至少关注：

- `solution_buffer.json`
- `stage1_summary.json` 或 `stage2_summary.json`
- `pareto_front_*.json`
- `metrics*.json`
- `plots/*.png`

当前已经支持自动生成的图包括：

- Pareto 2D projections
- 3D Pareto scatter
- Stage-1 vs Stage-2 overlay
- assignment counts
- Stage-2 round summary
- 论文风格总对比图

## 推荐阅读顺序

如果是第一次接手当前复现线，建议按以下顺序阅读：

1. [README.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/README.md)
2. [docs/PROJECT_BRIEF.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/docs/PROJECT_BRIEF.md)
3. [docs/ARCHITECTURE.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/docs/ARCHITECTURE.md)
4. [docs/DECISIONS.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/docs/DECISIONS.md)
5. [docs/TASKS.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/docs/TASKS.md)
6. [docs/EXPERIMENT_LOG.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/docs/EXPERIMENT_LOG.md)

如果是直接想复现实验，建议优先看：

- [cmorl_minicage/configs/ablation](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/configs/ablation)
- [cmorl_minicage/outputs/plots/paper_style_ablation_summary.png](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/plots/paper_style_ablation_summary.png)
- [docs/EXPERIMENT_LOG.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/docs/EXPERIMENT_LOG.md)
