# Architecture

## 模块结构

MiniCAGE C-MORL 复现线的核心目录是 [cmorl_minicage](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage)。

主要模块分工如下：

- [env.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/env.py)
  - 把 `mini_CAGE` 包装成多目标训练接口。
  - 输出 Blue 观测和 3 维 reward vector。
  - 负责构造 `security / business / cost` 三目标。
  - 保留 MiniCAGE 原始标量 reward 作为对照信息，而不是强制与三目标逐项对账。
- [models/actor_critic.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/models/actor_critic.py)
  - Actor 输出离散动作分布。
  - Critic 输出向量 value。
- [storage/rollout_storage.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/storage/rollout_storage.py)
  - 保存向量 rewards、returns、advantages。
- [algorithms/ppo_vector.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/algorithms/ppo_vector.py)
  - Stage-1 的 vector-critic PPO。
  - 用 `ω^T A_vec` 做 actor 标量化更新。
- [algorithms/selection.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/algorithms/selection.py)
  - `nondominated_filter`
  - `crowding_distance`
  - `select_top_n_by_crowding`
- [algorithms/ipo.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/algorithms/ipo.py)
  - Stage-2 的 IPO-style constrained extension。
  - 当前是 PPO-compatible 的近似实现。
- [algorithms/assignment.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/algorithms/assignment.py)
  - SMP assignment。
  - 给定任意 preference，返回 utility 最大的 policy。
- [buffer.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/buffer.py)
  - 定义 solution buffer schema、record、metadata。
- [config.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/config.py)
  - YAML 配置加载。
  - dataclass 配置定义。
- [train_stage1.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/train_stage1.py)
  - Stage-1 训练入口。
  - 初始策略池构建。
- [train_stage2.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/train_stage2.py)
  - Stage-2 selection-extension 训练入口。
  - 负责读取 Stage-1 buffer，选择 Pareto 解并扩展。
- [evaluate.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/evaluate.py)
  - HV、EU、SP 与 assignment summary。
- [visualize.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/visualize.py)
  - 单 run 图像生成。
  - 多实验对比图。
  - 主线图、suite 图、2D/3D/pairwise 论文风格图。
- [baselines.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/baselines.py)
  - baseline 实验入口。
  - 统一管理 `sleep`、`random-valid`、`stage1-only`、`single-objective`、`weighted-sum`。
- [select_policy.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/select_policy.py)
  - 给定任意 preference，从 `solution_buffer.json` 中返回当前最优策略。

## 核心类与关键函数

### 环境层

- `MiniCageMORLEnv`
  - `reset()`
  - `step()`
  - `_project_reward_terms()`
  - `_state_security_risk()`
  - `_business_disruption()`
  - `_operation_cost()`
  - `_semantic_step_info()`

这一层最重要的职责不是“跑环境”，而是：

- 把 MiniCAGE 的安全状态、业务扰动和动作成本拆成更符合当前项目语义的三目标。
- 同时保留原始 MiniCAGE 标量 reward，方便后续分析新旧口径之间的差异。
- 把当前任务明确变成“Blue-only MORL + scripted red opponent”。
- 在 `info["semantic_info"]` 中提供逐步语义统计，支撑后续评估层汇总。

### 模型层

- `ActorCritic`
  - `act()`
  - `get_value()`
  - `evaluate_actions()`

这里的一个关键点是：

- actor 和 critic 共用 backbone
- critic head 输出 `obj_dim` 维

### 存储层

- `VectorRolloutStorage`
  - `insert()`
  - `compute_returns()`
  - `advantages()`
  - `feed_forward_generator()`

### Stage-1 算法层

- `VectorPPO.update(storage, preference)`
  - 先把向量 advantage 通过 preference 标量化
  - 再走 PPO clip loss

### Stage-2 算法层

- `IPOTrainer.update(storage, objective_idx, reference_objectives)`
  - 针对一个目标方向优化 clipped surrogate
  - 对其他目标施加 log-barrier
  - 当前 barrier 是基于 surrogate return 的近似

### Baseline 层

- `run_sleep_baseline(...)`
- `run_random_valid_baseline(...)`
- `run_stage1_only_baseline(...)`
- `run_single_objective_baseline(...)`
- `run_weighted_sum_baseline(...)`
- `select_policy.py`
  - `load_records(...)`
  - `compute_utility(...)`
  - `select_best_record(...)`

这一层的作用是：

- 让启发式 baseline、Stage-1 自身、学习型 baseline 走同一套 buffer 和评估接口。
- 让 baseline 也能输出和主方法同结构的 `metrics.json` 与语义指标。
- 让“给一个 preference，取当前最优策略”这件事直接变成可复用工具，而不是只在 `assignment` 内部使用。

### 选择与赋值层

- `nondominated_filter(records)`
- `crowding_distance(records)`
- `select_top_n_by_crowding(records, top_n)`
- `assign_policy(preference, policy_set)`

## 关键数据流

### Stage-1 数据流

1. `MiniCageMORLEnv` 输出 `obs` 和 `reward_vec`
   - 当前 `reward_vec = [security, business, cost]`
2. `ActorCritic` 基于 `obs` 采样动作，并给出向量 critic value
3. `VectorRolloutStorage` 保存 rollout
4. `VectorPPO` 使用 preference 对向量 advantage 做 scalarization
5. `train_stage1.py` 定期评估 policy，保存 checkpoint 和 policy record
6. 所有 records 写入 `solution_buffer.json`
7. 对 records 做 Pareto filtering，导出 `pareto_front_stage1.json`

### Baseline 数据流

1. `baselines.py` 读取 formal 或 smoke 配置
2. 对启发式 baseline：
   - 直接在环境中 rollout
   - 构造 synthetic `solution_buffer.json`
3. 对学习型 baseline：
   - 复用 `train_stage1.py`
   - 用显式 preference 生成对应策略集
4. 统一走 `evaluate.py`
5. 输出：
   - `metrics.json`
   - `semantic_metrics`
   - 可继续进入 `visualize.py`

### Stage-2 数据流

1. 读取 Stage-1 `solution_buffer.json`
2. 用 `nondominated_filter + crowding_distance` 选出待扩展策略
3. 对每个被选 policy、每个 objective 方向分别做 constrained extension
4. `IPOTrainer` 更新时：
   - 优化目标方向 surrogate
   - 同时用 barrier 约束其他目标
5. `train_stage2.py` 用真实评估结果再做一次 feasibility gate
6. 当前实现只保留每条扩展路径的 `best_feasible` 结果
7. 新 records 回写 `solution_buffer.json`
8. 导出 `pareto_front_stage2.json` 和 `stage2_summary.json`

### 评估与可视化数据流

1. `evaluate.py` 读取 buffer
2. 重新做 Pareto filtering
3. 基于 simplex grid 构造 preference 集合
4. 计算：
   - Hypervolume
   - Expected Utility
   - Sparsity
   - assignment summary
   - semantic policy metrics
   - assignment-weighted semantic metrics
5. `visualize.py` 再读取：
   - `solution_buffer.json`
   - `stage2_summary.json`
   - `metrics.json`
6. 输出：
   - `pareto_projections.png`
   - `pareto_3d_scatter.png`
   - `stage1_vs_stage2_overlay.png`
   - `assignment_counts.png`
   - `stage2_rounds.png`
   - `paper_style_ablation_summary.png`
   - baseline metrics comparison
   - baseline semantic comparison
   - main-vs-baseline comparison
   - compact objective map
   - pairwise objective panels
   - suite metrics / suite 3D / suite pairwise

## 关键产物

每条 run 至少会产生：

- `solution_buffer.json`
  - 当前 run 的完整策略集合、metadata、Pareto front
- `pareto_front_stage1.json` 或 `pareto_front_stage2.json`
  - 最终非支配策略集合
- `stage1_summary.json` 或 `stage2_summary.json`
  - 阶段级过程统计
- `metrics.json`
  - HV / EU / SP / assignment summary / semantic metrics
- `metrics_fixed_ref.json` 或 `metrics_compare_main.json`
  - 统一 reference point 下的公平比较结果
- `metrics_compare_suite.json`
  - `Stage-2 + 5 baselines` 的统一 reference point 公平比较结果
- `plots/*.png`
  - 图形化结果

这些产物共同组成实验记录体系的事实来源；文本结论再同步写入 [EXPERIMENT_LOG.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/docs/EXPERIMENT_LOG.md)。

## 当前架构与论文同构度

从系统结构上看，当前实现和论文最接近的部分是：

- Stage-1 vector PPO 初始化
- Pareto filter + crowding selection
- Stage-2 按 objective 方向做 constrained extension
- SMP assignment
- HV / EU / SP 评估

当前最不完全同构的部分是：

- Stage-1 仍是串行，不是论文默认并行
- IPO 是 surrogate 近似实现
- Stage-2 多了工程化 feasibility gate
- 运行环境已切换为 MiniCAGE 适配任务，并采用自定义的 `security / business / cost` 奖励口径

## 建议的后续扩展点

从架构角度看，后续最值得扩展的点有：

1. Stage-1 多 worker 并行初始化
2. 更贴近论文的 IPO 数值实现
3. CPO 分支
4. 更系统的 Stage-2 buffer / candidate 保存策略
5. 更统一的 fair-comparison evaluation pipeline
6. 面向论文写作的 figure/export pipeline
7. baseline suite 与主线结果的一体化导出脚本
