# Architecture

## 模块结构

MiniCAGE C-MORL 复现线的核心目录是 [cmorl_minicage](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage)。

主要模块分工如下：

- [env.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/env.py)
  - 把 `mini_CAGE` 包装成多目标训练接口，输出 Blue 观测和 reward vector
- [models/actor_critic.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/models/actor_critic.py)
  - Actor 输出离散动作分布，Critic 输出向量 value
- [storage/rollout_storage.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/storage/rollout_storage.py)
  - 保存向量 rewards、returns、advantages
- [algorithms/ppo_vector.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/algorithms/ppo_vector.py)
  - Stage-1 的 vector-critic PPO
- [algorithms/selection.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/algorithms/selection.py)
  - nondominated filter、crowding distance、selection
- [algorithms/ipo.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/algorithms/ipo.py)
  - Stage-2 的 IPO-style constrained extension
- [algorithms/assignment.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/algorithms/assignment.py)
  - SMP assignment
- [buffer.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/buffer.py)
  - solution buffer schema、record、metadata
- [config.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/config.py)
  - YAML 配置加载与 dataclass 配置定义
- [train_stage1.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/train_stage1.py)
  - Stage-1 训练入口与初始策略池构建
- [train_stage2.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/train_stage2.py)
  - Stage-2 selection-extension 训练入口
- [evaluate.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/evaluate.py)
  - HV、EU、SP 与 assignment summary

## 关键数据流

训练与评估数据流如下：

1. `MiniCageMORLEnv` 输出 `obs` 和 `reward_vec`
2. `ActorCritic` 基于 `obs` 采样动作，并给出向量 critic value
3. `VectorRolloutStorage` 保存 rollout
4. Stage-1 使用 `VectorPPO` 结合 preference 做标量化 actor update
5. Stage-2 从已有 `solution_buffer.json` 中选 policy，再做 IPO-style extension
6. 新 policy 与评估结果统一写回 buffer / summary / metrics 文件

## 关键产物

每条主线 run 至少会产生：

- `solution_buffer.json`
- `pareto_front_stage1.json` 或 `pareto_front_stage2.json`
- `stage1_summary.json` 或 `stage2_summary.json`
- `metrics.json` 或自定义评估输出

这些产物共同组成实验记录体系的事实来源；文本结论再同步写入 [EXPERIMENT_LOG.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/docs/EXPERIMENT_LOG.md)。
