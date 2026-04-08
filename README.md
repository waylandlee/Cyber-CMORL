


<p align="center">
    <img src="Extras/images/logo_cyborg.png" alt="Diagram of the system" width="400"/>
</p>

# 当前项目概况

本仓库当前包含两条相互独立但相关的主线：

- `CybORG++` 原始环境与开发说明
  - 包括修复后的 CAGE 2 CybORG 环境
  - 包括轻量快速的 `MiniCAGE`
- `MiniCAGE C-MORL` 论文实验主线
  - 位于 [cmorl_minicage](./cmorl_minicage)
  - 目标是在不改动其他研究主线的前提下，复现论文 *Efficient Discovery of Pareto Front for Multi-Objective Reinforcement Learning (C-MORL)* 的核心训练流程，并将其迁移到 MiniCAGE 场景
  - 当前已经补齐统一论文实验系统，可直接生成主表 A、主表 B、补充实验、CSV/TEX 表格与图片
- `CybORG formal migration` 正式环境主线
  - 位于 [cmorl_cyborg](./cmorl_cyborg)
  - 目标是把 `security / business / cost` 三目标、主表 A/B 导表协议和约束评估协议迁移到正式 `CybORG`
  - 当前文档口径以 `cmorl_cyborg` 的 `3-seed (7/11/19)` 结果为准

## 2026-04-08 当前状态

如果你现在是第一次进仓库，建议优先把项目理解为：

- `cmorl_minicage`：历史复现与升级探索线
- `cmorl_cyborg`：当前论文正式环境结果线

截至 `2026-04-08`，`cmorl_cyborg` 已完成：

- 正式 `Scenario2` 协议下的 `3-seed` 主表 A / 主表 B 聚合
- 共享 `reference point` 与共享 `thresholds` 的固定
- `fair_compare_eval` 下 tight / loose 两组公平比较
- 新增 `coverage_combo_fair` 与 `coverage_more_parents_fair` 的聚合与出图

当前最重要的几个结果文件是：

- 主表 B 原始 3-seed 聚合：
  - [ours_stage2.json](./cmorl_cyborg/outputs/paper_table_b/aggregated/ours_stage2.json)
  - [main_table_b_bar.png](./cmorl_cyborg/outputs/paper_table_b/main_table_b_bar.png)
- 公平比较：
  - [fair_compare_table_b_tight_with_coverage.png](./cmorl_cyborg/outputs/fair_compare_eval/aggregated/fair_compare_table_b_tight_with_coverage.png)
  - [fair_compare_table_b_loose_with_coverage.png](./cmorl_cyborg/outputs/fair_compare_eval/aggregated/fair_compare_table_b_loose_with_coverage.png)
- 新增 coverage 聚合：
  - [coverage_combo_fair_loose.json](./cmorl_cyborg/outputs/fair_compare_eval/aggregated/coverage_combo_fair_loose.json)
  - [coverage_more_parents_fair_loose.json](./cmorl_cyborg/outputs/fair_compare_eval/aggregated/coverage_more_parents_fair_loose.json)

## 当前复现主线在做什么

当前 `cmorl_minicage` 主要实现了以下能力：

- MiniCAGE 的多目标环境包装
- Stage-1 Pareto initialization
- Stage-2 selection + IPO-style Pareto extension
- AdaCS-DCS-CMORL 升级骨架
  - `adaptive selection`
  - `dynamic beta scheduling`
- SMP assignment
- HV / EU / SP evaluation
- conditioned evaluator
- constraint evaluator
- shared-reference compare suite
- CSV / JSON / TeX table export
- YAML 配置驱动训练与评估
- 统一的 buffer / summary / metrics 输出格式

当前还已经补入以下论文 baseline 入口：

- `Weighted-Sum`
- `Preference-Conditioned PPO`
- `PCN-lite`
- `Lagrangian-PPO`
- `stage1-only`
- `no-constraint stage2`
- `single-objective`

当前 Stage-2 已支持四种模式：

- `crowding + fixed beta`
- `adaptive selection + fixed beta`
- `crowding + dynamic beta`
- `adaptive selection + dynamic beta`

当前实现更适合被理解为：

**“C-MORL 方法在 MiniCAGE 上的迁移复现版”**

也就是说，它已经比较贴近论文的算法结构和训练逻辑，但实验环境不是论文原 benchmark，而是本地适配后的 MiniCAGE。

## 当前项目状态

截至目前，这条复现线已经具备：

- 可以独立运行的 `stage1 -> stage2 -> evaluate` 完整链路
- 分层配置模板：
  - `cmorl_minicage/configs/smoke/`
  - `cmorl_minicage/configs/formal/`
  - `cmorl_minicage/configs/ablation/`
- 结构化输出：
  - `solution_buffer.json`
  - `stage1_summary.json`
  - `stage2_summary.json`
  - `metrics.json`
  - `constraint_metrics.json`
  - `table_a_summary.json`
  - `table_a_metrics.csv`
  - `table_b_constraints.csv`

当前正式论文实验链路已经固定为：

- 主表 A：Pareto / utility 比较
  - `Ours (stage2)`
  - `Weighted-Sum`
  - `Preference-Conditioned PPO`
  - `PCN-lite`
- 主表 B：约束处理比较
  - `Ours (stage2)`
  - `Lagrangian-PPO`
  - `Weighted-Sum`
  - `stage1-only`
  - `no-constraint stage2`
  - `single-objective`
- 补充实验
  - `stage1-only`
  - `no-constraint stage2`
  - `single-objective`
  - `multiseed summary`

当前统一 paper protocol 的固定口径是：

- 环境：
  - `num_envs=8`
  - `red_policy=bline`
  - `remove_bugs=true`
  - `max_episode_steps=100`
- 目标维度：
  - `obj_dim=3`
- 主表 A 评估：
  - `preference_step=0.1`
  - `reference_strategy=data_min_range`
  - `reference_margin=0.25`
- 统一总训练预算：
  - `98304 env steps`
- 主表 A 使用共享 reference point：
  - `[-884.1681, -82.3076, -99.1242]`
- 主表 B 使用共享 thresholds：
  - `d_business=-29.2917`
  - `d_cost=-20.9862`

当前 `cmorl_cyborg` 文档默认使用的正式 seed 集为：

- `3-seed`: `7 / 11 / 19`
- `5-seed formal`: 仍保留为下一阶段候选，不在本轮文档里假装已经完成

当前这轮正式环境结果最值得直接查看的是：

- 主表 B 汇总：
  - [ours_stage2.json](./cmorl_cyborg/outputs/paper_table_b/aggregated/ours_stage2.json)
  - [no_constraint_stage2.json](./cmorl_cyborg/outputs/paper_table_b/aggregated/no_constraint_stage2.json)
  - [main_table_b_bar.png](./cmorl_cyborg/outputs/paper_table_b/main_table_b_bar.png)
- 公平比较汇总：
  - [ours_stage2_fair_loose.json](./cmorl_cyborg/outputs/fair_compare_eval/aggregated/ours_stage2_fair_loose.json)
  - [no_constraint_stage2_fair_loose.json](./cmorl_cyborg/outputs/fair_compare_eval/aggregated/no_constraint_stage2_fair_loose.json)
  - [coverage_combo_fair_loose.json](./cmorl_cyborg/outputs/fair_compare_eval/aggregated/coverage_combo_fair_loose.json)
  - [coverage_more_parents_fair_loose.json](./cmorl_cyborg/outputs/fair_compare_eval/aggregated/coverage_more_parents_fair_loose.json)

主表 B 当前导出的代表性结果为：

| Method | Security | Feasible Rate | Mean Violation |
| --- | --- | --- | --- |
| Ours (`paper_table_b`) | `-518.70 ± 17.16` | `0.800 ± 0.089` | `0.380 ± 0.300` |
| coverage combo fair (`loose`) | `-491.02 ± 13.59` | `0.633 ± 0.116` | `0.287 ± 0.119` |
| coverage more parents fair (`loose`) | `-509.10 ± 21.99` | `0.600 ± 0.094` | `0.380 ± 0.037` |
| no-constraint stage2 fair (`loose`) | `-490.91 ± 34.04` | `0.892 ± 0.042` | `0.084 ± 0.054` |

当前对这些结果的保守解读是：

- `coverage_combo_fair` 相比原始 `ours_stage2`，在 `security / business` 和 `mean_violation` 上更好。
- 但它的 `feasible_rate` 从 `0.800` 降到 `0.633`，因此不能当成对原始 `ours_stage2` 的严格改进。
- 在 `Loose` 公平比较下，`coverage_combo_fair` 与 `coverage_more_parents_fair` 选中了同一组策略，说明二者差别更像评估波动而不是机制性分化。
- 在 `Loose` 设定下，`no_constraint_stage2_fair` 仍然是最稳的可行性基线。

## 论文算法流程 vs 当前代码流程

下面这张表用于回答一个高频问题：

**当前实现是否已经等价于论文《Efficient Discovery of Pareto Front for Multi-Objective Reinforcement Learning (C-MORL)》中的原始算法流程？**

结论是：

- 从算法骨架看，当前实现已经复现了论文的核心主线
- 从实验协议和数值实现细节看，当前实现仍然是一个 **MiniCAGE 迁移复现版**，而不是论文原 benchmark 上的严格同构复现

标记说明：

- `完全一致`
- `思想一致但实现近似`
- `本地适配改造`
- `尚未实现`

| 模块 | 论文算法流程 | 当前代码流程 | 判断 |
| --- | --- | --- | --- |
| 总体框架 | 两阶段：Pareto initialization -> policy selection + Pareto extension -> SMP assignment | `train_stage1.py` + `train_stage2.py` + `algorithms/assignment.py` | `完全一致` |
| Stage-1 固定 preference 初始化 | 每个初始 policy 对一个固定 preference 训练 | `train_stage1.py` 中逐个 preference 训练 | `完全一致` |
| Stage-1 并行训练 M 个 policy | 论文默认强调 parallel training of M policies | 当前是串行 for-loop，不是并行 worker | `思想一致但实现近似` |
| 向量 critic | value function 输出多目标向量 | `models/actor_critic.py` 的 critic 输出 `obj_dim` 维 | `完全一致` |
| 向量 rollout / returns / advantages | 保存向量 reward、return、advantage | `storage/rollout_storage.py` 按向量存储 | `完全一致` |
| Stage-1 actor 更新 | 用 `ω^T A` 做 scalarization 后进行 policy gradient / PPO 更新 | `algorithms/ppo_vector.py` 用向量 advantage 再标量化 | `完全一致` |
| Solution buffer | 初始化阶段维护 buffer，不只保留最终 policy，也保留中间策略 | `train_stage1.py` 持续保存 checkpoint 到 `solution_buffer.json` | `完全一致` |
| Pareto filter | 先筛非支配解 | `algorithms/selection.py` 的 `nondominated_filter` | `完全一致` |
| crowding distance | 用 crowd distance 找稀疏区域 | `algorithms/selection.py` 的 `crowding_distance` | `完全一致` |
| extreme policy 优先保留 | extreme solutions 默认选入，再按 crowding 补齐 | `algorithms/selection.py` 中先选 extreme，再补 top-N | `完全一致` |
| Stage-2 selection-extension 交替 | 每轮先 selection，再 extension，再重新 selection | `train_stage2.py` 按 round 执行 selection-extension | `完全一致` |
| 按目标方向逐个扩展 | 对每个被选 policy，沿每个 objective 方向做 constrained extension | `train_stage2.py` 对每个 `objective_idx` 分别扩展 | `完全一致` |
| 约束形式 | 论文用 `G_i^π >= β G_i^{π_r}` | `train_stage2.py` 中按 `candidate_objectives - beta * current_reference` 判断 | `完全一致` |
| IPO / log barrier 思路 | PPO surrogate + log barrier 约束其它目标 | `algorithms/ipo.py` 中是 PPO 风格目标加 barrier bonus | `思想一致但实现近似` |
| IPO 中的 return 量 | 论文公式作用在真实 `G_i^π - β G_i^{π_r}` 上 | 当前实现用 `reference + batch surrogate gain` 近似 `G_i^π` | `思想一致但实现近似` |
| CPO 分支 | 论文附录同时给了 C-MORL-CPO | 当前仓库没有 CPO 训练实现 | `尚未实现` |
| Stage-2 每步都入库 | 论文 Algorithm 2 可理解为每个 constrained update step 都存入 `X` | 当前实现只保留每条扩展路径的 `best_feasible` 结果 | `思想一致但实现近似` |
| feasibility gate | 论文核心公式未单独强调工程 gate | 当前有 `constraint_tolerance` 做额外截断 | `思想一致但实现近似` |
| SMP assignment | 给定 preference，从 Pareto set 中选 utility 最大的 policy | `algorithms/assignment.py` 直接做 argmax utility | `完全一致` |
| Evaluation 偏好网格 | 2/3-4/6-9 目标分别用 `0.01 / 0.1 / 0.5` | `evaluate.py` 采用同样规则 | `完全一致` |
| HV / EU / SP | 用 Hypervolume、Expected Utility、Sparsity 评估 | `evaluate.py` 中全部实现 | `完全一致` |
| HV 数值实现 | 论文定义指标，但不限定具体数值算法 | 当前小集合 exact，大集合 Monte Carlo | `思想一致但实现近似` |
| benchmark 环境 | 论文用 MO-Gymnasium / SustainGym | 当前用 `MiniCageMORLEnv` | `本地适配改造` |
| objective 定义 | 论文 benchmark objective 是原生给定的 | 当前把 MiniCAGE 标量 reward 拆成 3 目标 | `本地适配改造` |
| 任务形式 | 论文是通用 MORL benchmark 任务 | 当前是 Blue-only policy，对手 Red 是脚本 agent | `本地适配改造` |
| 配置与实验管理 | 论文不强调本地工程结构 | 当前使用 YAML 配置、buffer schema、summary、plots | `本地适配改造` |

## 当前实现与论文真正拉开差距的 4 个点

### 1. Stage-1 现在是串行训练，不是论文强调的并行训练

论文把 Pareto initialization 描述为：

- 同时训练 `M` 个初始策略
- 每个策略对应一个固定 preference
- 这些策略彼此独立，可以天然并行

当前 `train_stage1.py` 仍然遵循“每个 preference 单独训练一个 policy”的算法定义，但实现方式是串行循环，而不是并行 worker。

这带来的差异主要不在算法正确性，而在工程层面：

- 墙钟时间更长
- 固定时间预算下，能负担的 `M`、timesteps 和 seed 数更少
- Stage-1 更容易因为耗时被压缩，导致初始 Pareto front 更稀疏
- 当前实现里随机数流是连续消费的，不同 preference 间的随机性独立性不如并行 worker 干净

所以这部分的结论是：

- 算法定义没变
- 但实验吞吐、资源分配和随机性结构与论文默认实现习惯存在差异

### 2. IPO 的思想一致，但当前是 PPO-compatible 的近似实现

论文附录 F.2 的 IPO 核心形式是：

- 用 PPO 的 clipped surrogate 优化目标方向
- 对其他目标加入 `log(G_i^π - β G_i^{π_r}) / t` 的 barrier

当前 `algorithms/ipo.py` 确实实现了 “PPO + log barrier” 这条思路，但 barrier 中并没有直接使用真实的策略级期望回报 `G_i^π`，而是使用了基于当前 batch advantage 的 surrogate return 近似。

这意味着：

- 方法论上和论文一致
- 数值实现上更偏工程可训练版本
- barrier 优化的是一个局部代理目标，而不是论文公式中的真实 return 本体

这也是为什么当前 Stage-2 有时会出现：

- 训练时 barrier 看起来有效
- 但真实评估后，新增点未必真的把 Pareto front 推得更好

### 3. Stage-2 多了工程化 feasibility gate，而且保存策略更保守

论文 Algorithm 2 更接近这样的语义：

- 每做一次 constrained update
- 都把候选解加入解集 `X`

当前实现更保守：

- 先用 `constraint_tolerance` 做一个额外的 feasibility gate
- 不可行就立刻终止当前扩展方向
- 即使过程中生成了多个候选点，最后也只保留 `best_feasible` 那一个

这样做的好处是：

- 跑起来更稳
- 解集不会膨胀得太快
- 更容易调试和检查每条扩展路径

但代价是：

- 与论文的“逐步填充 front”过程并不完全同构
- 某些本来可以作为中间 Pareto 候选点的策略没有被保留下来
- front 的细粒度覆盖可能会比论文式实现更弱

### 4. 当前实验环境、目标定义和任务形式都已经被 MiniCAGE 适配

这是最大的外部差异。

论文的实验是在 MO-Gymnasium / SustainGym 等 benchmark 上进行的，而当前实现运行在 MiniCAGE 上，并做了几层本地改造：

- 环境从论文 benchmark 换成了 `MiniCAGE`
- 任务变成 Blue-only policy vs scripted red opponent
- reward 从 MiniCAGE 的标量记账中拆分成 3 目标 reward vector

这会带来一个非常重要的结论：

- 当前结果可以用于验证论文方法在 MiniCAGE 上是否成立
- 但不能直接把数值结果当成论文原 benchmark 上的严格复现结果

也就是说，当前工作最准确的定位是：

**“论文 C-MORL 算法思想在 MiniCAGE 上的高保真迁移复现版”**

而不是：

**“论文原实验设置上的逐项同构复现版”**

## 目录说明

当前最值得关注的目录如下：

- [cmorl_minicage](./cmorl_minicage)
  - MiniCAGE 上的 C-MORL 论文复现实现
- [docs](./docs)
  - 当前项目的中文项目说明、架构、决策、任务和实验日志
- [Debugged_CybORG](./Debugged_CybORG)
  - 修复后的 CAGE 2 CybORG 环境
- [mini_CAGE](./mini_CAGE)
  - MiniCAGE 轻量环境实现

如果你主要关注当前论文复现主线，建议优先看：

- [docs/PROJECT_BRIEF.md](./docs/PROJECT_BRIEF.md)
- [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)
- [docs/MINICAGE_TO_CYBORG_MIGRATION.md](./docs/MINICAGE_TO_CYBORG_MIGRATION.md)
- [docs/TASKS.md](./docs/TASKS.md)
- [docs/EXPERIMENT_LOG.md](./docs/EXPERIMENT_LOG.md)

## 快速开始

建议在仓库根目录、使用 `cc4` conda 环境运行。

基础 smoke 链路：

```bash
conda run -n cc4 python -m cmorl_minicage.train_stage1 --config cmorl_minicage/configs/smoke/stage1.yaml
conda run -n cc4 python -m cmorl_minicage.train_stage2 --config cmorl_minicage/configs/smoke/stage2.yaml --stage1-buffer <stage1_solution_buffer>
conda run -n cc4 python -m cmorl_minicage.evaluate --config cmorl_minicage/configs/smoke/evaluate.yaml --buffer-path <solution_buffer>
```

如果要跑当前统一论文配置，优先看：

- [cmorl_minicage/configs/paper](./cmorl_minicage/configs/paper)

其中最常用的入口是：

- `stage1_main.yaml`
- `stage2_main.yaml`
- `stage2_no_constraint.yaml`
- `weighted_sum_main.yaml`
- `pref_cond_ppo.yaml`
- `lagrangian_ppo.yaml`
- `pcn.yaml`

运行 Ours 的 paper 配置：

```bash
conda run -n cc4 python -m cmorl_minicage.train_stage1 --config cmorl_minicage/configs/paper/stage1_main.yaml
conda run -n cc4 python -m cmorl_minicage.train_stage2 --config cmorl_minicage/configs/paper/stage2_main.yaml --stage1-buffer <stage1_solution_buffer>
conda run -n cc4 python -m cmorl_minicage.evaluate --config cmorl_minicage/configs/paper/evaluate_main_table_a.yaml --buffer-path <solution_buffer>
```

运行 conditioned / constrained baseline：

```bash
conda run -n cc4 python -m cmorl_minicage.baselines weighted-sum --stage1-config cmorl_minicage/configs/paper/weighted_sum_main.yaml --preferences-file cmorl_minicage/configs/paper/preferences_main_table_a.yaml --output-dir cmorl_minicage/outputs/paper_table_a/weighted_sum
conda run -n cc4 python -m cmorl_minicage.train_pref_conditioned_ppo --config cmorl_minicage/configs/paper/pref_cond_ppo.yaml
conda run -n cc4 python -m cmorl_minicage.evaluate_conditioned --config cmorl_minicage/configs/paper/evaluate_main_table_a.yaml --input-path <conditioned_run_metadata_or_points>
conda run -n cc4 python -m cmorl_minicage.train_lagrangian_ppo --config cmorl_minicage/configs/paper/lagrangian_ppo.yaml
conda run -n cc4 python -m cmorl_minicage.train_pcn --config cmorl_minicage/configs/paper/pcn.yaml
```

运行统一对比与导表：

```bash
conda run -n cc4 python -m cmorl_minicage.compare_suite --config cmorl_minicage/outputs/paper_table_a/compare_suite_config.yaml
conda run -n cc4 python -m cmorl_minicage.export_tables --config cmorl_minicage/outputs/paper_table_a/export_tables_config.yaml
```

## 输出与实验记录

当前复现线所有实验输出默认写入：

- `cmorl_minicage/outputs/`

本轮论文实验系统的核心输出目录是：

- `cmorl_minicage/outputs/paper_table_a/`
- `cmorl_minicage/outputs/paper_table_b/`
- `cmorl_minicage/outputs/paper_appendix/`

其中包含：

- 主表 A：
  - `shared_reference.json`
  - `table_a_summary.json`
  - `tables/table_a_metrics.csv`
  - `tables/table_a_metrics.tex`
  - `main_table_a_metrics.png`
  - `main_table_a_pairwise.png`
- 主表 B：
  - `shared_thresholds.json`
  - `aggregated/*.json`
  - `tables/table_b_constraints.csv`
  - `tables/table_b_constraints.tex`
  - `main_table_b_bar.png`
- 补充实验：
  - `multiseed_summary.json`
  - `aggregated/*.json`

实验过程中的结构化事实来自 run 目录下的 JSON 文件；实验现象、结论和后续动作统一记录在：

- [docs/EXPERIMENT_LOG.md](./docs/EXPERIMENT_LOG.md)

## 说明

本 README 顶部这部分中文内容用于描述当前仓库里“正在推进的项目状态”和“MiniCAGE C-MORL 复现主线”的基本情况；后续更细的实现和实验细节，请以 `docs/` 与 `cmorl_minicage/docs/` 中的文档为准。
