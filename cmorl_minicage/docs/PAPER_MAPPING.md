# C-MORL MiniCAGE 论文映射

本文档用于把论文《Efficient Discovery of Pareto Front for Multi-Objective Reinforcement Learning (C-MORL)》中的核心算法模块，与 `cmorl_minicage` 本地复现实现逐项对应起来。

状态字段统一使用：
- `Planned`
- `In Progress`
- `Done`
- `Blocked`

说明：
- “忠实复现”用于标记当前目标是否以论文算法口径为准。
- “是否改造”用于标记是否因 MiniCAGE 环境或本地复现条件做了适配。

| 论文部分 | 核心算法点 | 对应代码模块 | 实现状态 | 忠实复现 | 是否改造 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| Section 5.1 Pareto Initialization | 多个初始策略并行训练，基于固定 preference 初始化 Pareto set | `cmorl_minicage.train_stage1` | Done | Target | Yes | 已支持独立 policy 训练、checkpoint 保存与初始 Pareto front 导出；当前新增 `dirichlet` / `dirichlet_extremes` 初始化策略以更接近论文式多策略初始化。 |
| Section 5.1 Pareto Initialization | 向量 critic 与向量 advantage（vectorized value / advantage） | `cmorl_minicage.models.actor_critic` | Done | Target | No | Critic 输出 3 维 value，actor 更新前再做 scalarization。 |
| Section 5.1 Pareto Initialization | 向量 rewards / values / returns 的 rollout storage | `cmorl_minicage.storage.rollout_storage` | Done | Target | No | 当前按 `[T, N, obj_dim]` 保存 reward / return / advantage。 |
| Section 5.1 Pareto Initialization | PPO actor 使用 preference 对向量 advantage 做标量化 | `cmorl_minicage.algorithms.ppo_vector` | Done | Target | No | `A_w = w^T A_vec` 已实现。 |
| Section 5.2 Policy Selection | Pareto-optimal 过滤（nondominated filter） | `cmorl_minicage.algorithms.selection` | Done | Target | No | 已用于 Stage-1 后处理与 Stage-2 selection。 |
| Section 5.2 Policy Selection | crowding distance 计算与 top-N 选择 | `cmorl_minicage.algorithms.selection` | Done | Target | No | 已支持 crowding-based top-N。 |
| Appendix A Algorithm 1 | extreme policy 优先保留，再按 crowding 补齐 | `cmorl_minicage.algorithms.selection` | Done | Target | No | 已实现 extreme-first 选择逻辑。 |
| Section 5.3 Pareto Extension | 多轮 selection-extension 交替扩展 Pareto front | `cmorl_minicage.train_stage2` | Done | Target | No | 已支持按轮次执行 selection-extension。 |
| Section 5.3 Pareto Extension | 按目标方向逐个做 constrained extension | `cmorl_minicage.train_stage2` | Done | Target | No | 已按 objective 方向做扩展。 |
| Section 5.3 Pareto Extension / Appendix F.2 | IPO / log-barrier 约束优化 | `cmorl_minicage.algorithms.ipo` | In Progress | Target | Yes | 已实现可运行版 IPO surrogate，但仍属于论文口径近似版，不是官方逐行复刻。 |
| Section 5.3 Pareto Extension | 约束形式 `G_i^pi >= beta * G_i^pi_r` | `cmorl_minicage.algorithms.ipo` | Done | Target | No | barrier margin 已按 `beta * G_i^pi_r` 构造。 |
| Section 5.4 Policy Assignment / Definition 3.1 | SMP（Set Max Policy）策略分配 | `cmorl_minicage.algorithms.assignment` | Done | Target | No | 给定任意 preference 返回 utility 最大策略。 |
| Definition E.1 / E.2 / E.3 | Hypervolume / Expected Utility / Sparsity 评估 | `cmorl_minicage.evaluate` | Done | Target | Yes | 已支持任意目标维的 HV / EU / SP、reference point 配置与 assignment summary；HV 当前对小 Pareto set 用 exact inclusion-exclusion，大集合回退 Monte Carlo。 |
| 本地环境适配 | MiniCAGE MORL reward vector wrapper | `cmorl_minicage.env` | Done | Target | Yes | 已做与 MiniCAGE 标量 reward 严格对账的 3 目标拆分。 |
| 本地环境适配 | Blue-only 训练接口，red 为脚本对手 | `cmorl_minicage.env` | Done | Target | Yes | 默认 `bline`，保留 `meander` 开关。 |
| 本地实验管理 | solution buffer / policy pool / checkpoint index | `cmorl_minicage.buffer`、`cmorl_minicage.train_stage1`、`cmorl_minicage.train_stage2` | Done | Target | Yes | 已统一到 `schema_version 0.3.0` 的 buffer metadata / record 格式，并补充 `stage1_summary` / `stage2_summary` 与更细的保存时统计。 |
| 本地实验管理 | 配置文件驱动训练与评估入口 | `cmorl_minicage.config`、`cmorl_minicage/configs/*.yaml` | Done | Yes | Yes | 训练/评估已优先使用 YAML 配置文件，CLI 仅保留少量路径覆盖项。 |

## 更新约定

- 每新增一个核心模块后，更新本表中的“实现状态”。
- 如果某模块实现时偏离论文做法，需要同步更新“忠实复现”“是否改造”“备注”三列。
- 已实现模块应尽量补上更精确的模块路径与关键接口名。
