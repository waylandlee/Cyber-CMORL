# Architecture

## 模块结构

MiniCAGE C-MORL 复现线的核心目录是 [cmorl_minicage](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage)。

主要模块分工如下：

- [env.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/env.py)
  - 把 `mini_CAGE` 包装成多目标训练接口。
  - 输出 Blue 观测和 3 维 reward vector。
  - 负责把 MiniCAGE 标量 reward 严格投影到三目标记账。
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
  - 论文风格 ablation 总图。

## 核心类与关键函数

### 环境层

- `MiniCageMORLEnv`
  - `reset()`
  - `step()`
  - `_project_reward_terms()`
  - `_reward_terms_from_state()`

这一层最重要的职责不是“跑环境”，而是：

- 保证 reward vector 和原始 MiniCAGE 标量 reward 对账一致。
- 把当前任务明确变成“Blue-only MORL + scripted red opponent”。

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

### 选择与赋值层

- `nondominated_filter(records)`
- `crowding_distance(records)`
- `select_top_n_by_crowding(records, top_n)`
- `assign_policy(preference, policy_set)`

## 关键数据流

### Stage-1 数据流

1. `MiniCageMORLEnv` 输出 `obs` 和 `reward_vec`
2. `ActorCritic` 基于 `obs` 采样动作，并给出向量 critic value
3. `VectorRolloutStorage` 保存 rollout
4. `VectorPPO` 使用 preference 对向量 advantage 做 scalarization
5. `train_stage1.py` 定期评估 policy，保存 checkpoint 和 policy record
6. 所有 records 写入 `solution_buffer.json`
7. 对 records 做 Pareto filtering，导出 `pareto_front_stage1.json`

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

## 关键产物

每条 run 至少会产生：

- `solution_buffer.json`
  - 当前 run 的完整策略集合、metadata、Pareto front
- `pareto_front_stage1.json` 或 `pareto_front_stage2.json`
  - 最终非支配策略集合
- `stage1_summary.json` 或 `stage2_summary.json`
  - 阶段级过程统计
- `metrics.json`
  - HV / EU / SP / assignment summary
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
- 运行环境已切换为 MiniCAGE 适配任务

## 建议的后续扩展点

从架构角度看，后续最值得扩展的点有：

1. Stage-1 多 worker 并行初始化
2. 更贴近论文的 IPO 数值实现
3. CPO 分支
4. 更系统的 Stage-2 buffer / candidate 保存策略
5. 面向论文写作的 figure/export pipeline
