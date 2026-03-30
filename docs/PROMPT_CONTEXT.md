# PROMPT_CONTEXT

## Purpose

本文件用于指导 Codex 在**不改动原项目现有代码**的前提下，单独复现并后续升级 ICLR 2025 论文 **Efficient Discovery of Pareto Front for Multi-Objective Reinforcement Learning (C-MORL)** 的算法思想，并首先在 **MiniCAGE** 上实现与验证。

目标不是直接修改现有 `src/` 主线，而是建立一套**隔离、可对照、可复现实验**的新实现，便于后续：
- 做原论文忠实复现版
- 做算法升级版
- 再迁移到更复杂的 CybORG / CybORG++ 设置中验证

---

# Part 1. 项目组织方案（不动原项目原有代码）

## 总原则

1. **不修改原有主线代码**
   - 不直接改动现有 `src/`
   - 不直接改动现有训练入口、当前 Stage-1 / Stage-2 实现
   - 不在现有实现上“打补丁式”混合论文复现版逻辑

2. **在同一仓库中新增一个独立顶层目录**
   - 先不要新开 GitHub 仓库
   - 先在当前仓库中建立一个**独立的论文复现工作区**
   - 这样可以最大化复用已有环境资源（尤其是 `mini_CAGE/`），同时避免污染原有研究主线

3. **新实现必须与原项目逻辑隔离**
   - 新目录要有独立的训练入口
   - 独立的 config
   - 独立的 output 目录
   - 独立的日志和文档
   - 不要复用原有 `src/training/*.py` 的训练逻辑后再局部魔改

---

## 推荐目录结构

建议新增一个顶层目录，例如：

```text
cmorl_repro/
  README.md
  __init__.py

  docs/
    NOTES.md
    TODO.md
    PAPER_MAPPING.md

  configs/
    env/
      minicage.yaml
    train/
      stage1.yaml
      stage2_ipo.yaml
    eval/
      metrics.yaml

  envs/
    minicage_morl_env.py
    wrappers.py

  models/
    actor_critic.py
    distributions.py

  storage/
    rollout_storage.py

  algorithms/
    ppo_vector.py
    ipo.py
    selection.py
    assignment.py

  training/
    train_stage1.py
    train_stage2.py
    evaluate.py

  utils/
    preference.py
    pareto.py
    metrics.py
    logging.py
    seeding.py

  scripts/
    run_stage1.sh
    run_stage2.sh
    run_eval.sh

  outputs/
```

---

## 为什么这样组织

### 1. 与原项目主线完全隔离
原项目当前主线是：
- `src/envs/cyborg_wrapper.py`
- `src/training/trainer_weighted.py`
- `src/training/trainer_cmorl_stage1.py`
- `src/training/trainer_cmorl_stage2.py`
- `src/agents/blue/*.py`

这些代码已经形成了你当前的工程化 C-MORL / constrained PPO 变体路线。复现论文时不要与之耦合，否则会很快陷入：
- 原逻辑和论文逻辑混杂
- 难以判断到底复现的是论文还是你现有变体
- 后续论文写作时很难清楚说明实现来源

### 2. 便于做严格对照
后续实验应能清楚区分三条线：
- 原项目工程主线
- 论文忠实复现版
- 论文基础上的升级版

### 3. 便于 Codex 工作
Codex 最适合处理**边界清晰、目录明确、职责分离**的项目。
因此新目录下每个模块必须职责单一。

---

## 文件职责建议

### `envs/minicage_morl_env.py`
职责：
- 基于 `mini_CAGE` 提供论文复现版所需的多目标环境接口
- 输出：
  - `obs`
  - 多目标 reward 向量
  - done
  - info
- 注意：这里应尽量贴近原论文代码风格，即**多目标奖励向量主通道化**

### `models/actor_critic.py`
职责：
- 实现论文风格 actor-critic
- Critic 输出维度应为 `obj_num`
- Actor 和 Critic 尽量结构清晰分离

### `storage/rollout_storage.py`
职责：
- 存储向量 rewards
- 存储向量 value_preds
- 存储向量 returns
- 支持 PPO actor update 所需的标量化 advantage 生成

### `algorithms/ppo_vector.py`
职责：
- 实现向量 critic 版本 PPO
- Critic loss 对向量 return 回归
- Actor update 时对 advantage 做 scalarization

### `algorithms/ipo.py`
职责：
- 实现论文中的 IPO / log-barrier 约束扩展逻辑
- 支持：
  - 选定目标方向 `l`
  - 对其余目标施加 barrier
  - 形成 Stage-2 的扩展更新

### `algorithms/selection.py`
职责：
- Pareto filtering
- crowding distance
- top-N candidate 选择
- 后续算法升级时也从这里扩展

### `algorithms/assignment.py`
职责：
- 显式实现 SMP / policy assignment
- 输入 preference
- 输出最优策略 / policy id / checkpoint / utility

### `training/train_stage1.py`
职责：
- 论文 Stage-1 复现版训练入口

### `training/train_stage2.py`
职责：
- 论文 Stage-2 复现版训练入口
- 真正实现 selection-extension 交替流程

### `training/evaluate.py`
职责：
- HV / EU / SP
- Pareto set 导出
- SMP 分配测试

---

## 版本控制建议

1. 新开一个 Git 分支，例如：
   - `cmorl-paper-repro`
2. 所有论文复现与升级开发都在这个分支进行
3. 等原论文忠实复现版稳定后，再考虑：
   - 继续在此分支上做升级版
   - 或另开 `cmorl-upgrade` 分支

---

## 输出与命名规范建议

所有论文复现版实验输出统一放到：

```text
outputs/cmorl_repro/
```

子目录命名建议：
- `stage1_pref_*`
- `stage2_iter_*`
- `eval_*`
- `ablation_*`

---

## 文档建议

必须新增以下文档：

### `docs/PAPER_MAPPING.md`
逐项记录：
- 原论文哪一节
- 对应代码模块
- 是否已实现
- 是否忠实复现
- 是否做了改造

### `docs/TODO.md`
记录：
- 当前复现进度
- 未完成模块
- 已知差异

### `docs/NOTES.md`
记录：
- 训练现象
- 不稳定原因
- 和论文实现的不一致处

---

# Part 2. 原论文算法实现细节（用于指导 Codex 在 MiniCAGE 上复现）

## 复现目标

这里的目标是先做一个**尽可能忠实于论文和官方实现风格**的版本，而不是一上来就做 cyber-specific 升级。

换句话说，第一阶段目标是：

> 在 MiniCAGE 上重新实现论文式 C-MORL，而不是基于现有工程代码“近似模仿”。

---

## 先明确：论文算法的核心不只是“两阶段训练”

原论文的核心包括 5 个部件：

1. 多目标 reward 向量主通道
2. Stage-1 Pareto initialization
3. Stage-2 policy selection
4. Stage-2 constrained Pareto extension（IPO）
5. Policy assignment / SMP

这些都要实现，不能只实现 Stage-1/2 的壳子。

---

## A. 环境接口：必须是“显式多目标环境”

### 目标
环境应返回多目标 reward 向量，而不是先加权成标量 reward。

### MiniCAGE 复现建议
基于 `mini_CAGE` 外包一层 MORL 环境接口，定义每一步输出：

```python
obs, reward_vec, done, info
```

其中：

```python
reward_vec = [security_reward, business_reward, cost_reward]
```

### 重要要求
- reward 向量必须作为训练主通道被保留
- 不要在环境层先做加权和
- `info` 中可以附带原始环境信息、红方信息、impact 信息、host 状态等

---

## B. 策略网络：使用向量 critic，而不是标量 critic

### 必须实现
Actor-Critic 结构中：

- Actor：输出动作分布
- Critic：输出 `obj_num` 维 value

例如三目标时：

```python
V(s) = [V_sec(s), V_biz(s), V_cost(s)]
```

### 不要做成
```python
V(s) = scalar_value
```

### 原因
论文官方实现是：
- 向量 rewards
- 向量 returns
- 向量 value_preds
- actor 更新时再做 scalarization

这是论文复现版与当前原项目主线最大的区别之一。

---

## C. Rollout Storage：必须保留向量 returns / 向量 values

### 存什么
Rollout storage 需要存：

- `obs`
- `actions`
- `log_probs`
- `rewards` shape = `[T, N, obj_num]`
- `value_preds` shape = `[T+1, N, obj_num]`
- `returns` shape = `[T+1, N, obj_num]`

### 需要支持的操作
1. 计算向量 GAE 或向量 returns
2. 存储用于 PPO 的 batch
3. 在 actor update 前，把向量优势按当前 scalarization 压成标量 advantage

---

## D. Stage-1：Pareto Initialization

### 目标
训练一批初始策略，每个策略对应一个 preference vector。

### 输入
一组 preference 向量，例如三目标时：
- `[1,0,0]`
- `[0.8,0.1,0.1]`
- `[0.6,0.2,0.2]`
- `[0.4,0.4,0.2]`
- ...

### 训练方式
每条初始策略使用 PPO 训练，但：
- Critic 仍然学向量 value
- Actor 更新时，使用当前 preference 对 advantage 做 scalarization

即：

\[
A_\omega(s,a)=\omega^\top (G(s,a)-V(s))
\]

### Stage-1 输出
每条策略应保存：
- checkpoint
- preference / weights
- 三目标 returns
- policy id

并形成：
- `policy_pool.json`
- `pareto_front.json`

---

## E. Policy Selection

### 原论文核心
Stage-2 不是随机扩展策略，而是先选出“最值得扩展的策略”。

### 论文基础做法
1. 从当前策略集合中过滤 Pareto-optimal solutions
2. 计算 crowding distance
3. 选取 crowding distance 最大的 top-N 策略进入 extension set

### 必须实现的基础模块
- `nondominated_filter`
- `crowding_distance`
- `select_top_n_by_crowding`

### 注意
原论文的选择逻辑是多轮反复使用的，不是只在 Stage-1 后调用一次。

---

## F. Stage-2：Pareto Extension（关键部分）

这是复现最重要的部分。

### 核心思想
对每个被选中的基策略 \(\pi_r\)，沿每个目标方向分别做 constrained extension：

\[
\max_\pi G_l^\pi
\quad
s.t.
\quad
G_i^\pi \ge \beta G_i^{\pi_r}, \ i \neq l
\]

也就是：
- 当前轮选一个主优化目标 \(l\)
- 其余目标不能低于上一轮基策略的一定比例

---

## G. IPO 实现（而不是简化拉格朗日惩罚版）

### 论文实验使用的是 IPO
所以复现版优先实现 **IPO / log-barrier**。

### IPO 目标形式
将约束问题转成无约束问题：

\[
\max_\pi
G_l^\pi
+
\sum_{i \neq l}
\phi(G_i^\pi)
\]

其中 barrier 项形如：

\[
\phi(G_i^\pi)
=
\frac{\log(G_i^\pi - \beta G_i^{\pi_r})}{t}
\]

### 实现要求
在 PPO actor loss 中加入 barrier term。

### 需要注意
- barrier 只作用于被约束目标
- 若当前策略接近约束边界，barrier 应急剧增大
- `t` 是 barrier 系数，越大越逼近原始问题
- `beta` 控制扩展保守性

---

## H. Stage-2 必须实现“多轮 selection-extension 交替”

不要只做：

- 选一次策略
- 扩展一次
- 结束

而应做成：

1. 当前 Pareto set 上做 selection
2. 对选中的策略做 K' 步 extension
3. 将新策略并入策略池
4. 重新计算 Pareto front
5. 再次 selection
6. 重复若干轮，直到预算耗尽

这是论文算法的重要结构。

---

## I. Policy Assignment / SMP

### 必须显式实现
给定任意 preference \(\omega\)，从 Pareto set 中选：

\[
\pi^*_\omega = \arg\max_{\pi \in \Pi_P} \omega^\top G^\pi
\]

### 不要只在 EU 里隐式实现
需要单独提供一个函数，例如：

```python
assign_policy(preference, policy_set) -> best_policy
```

### 输出建议
- best policy id
- utility
- corresponding objective vector
- checkpoint path

---

## J. 评估模块

### 必须实现的标准指标
- Hypervolume (HV)
- Expected Utility (EU)
- Sparsity (SP)

### MiniCAGE 复现阶段可先做这些
在忠实复现阶段，先确保这三个指标稳定可用。

### 可选增强
在后续 cyber-specific 版本中，再加入：
- critical asset protection rate
- red impact success rate
- avg business impact
- avg defense cost

---

# Part 3. 给 Codex 的具体实现要求

## 实现优先级

### 第一阶段：骨架复现
必须先完成：
1. `MiniCAGE MORL env`
2. `vector critic actor-critic`
3. `rollout storage with vector rewards`
4. `stage1 training`
5. `pareto filtering + crowding distance`
6. `IPO-based stage2 extension`
7. `explicit SMP assignment`
8. `HV/EU/SP evaluation`

### 第二阶段：对齐论文流程
1. 补齐多轮 selection-extension
2. 完善 config 和脚本
3. 做最小可运行实验

### 第三阶段：再做算法升级
只有在原论文复现版稳定后，才开始新增：
- adaptive selection
- dynamic beta
- recursive front repair
- robust assignment

---

## 编码约束

1. 不修改原项目 `src/` 主线代码
2. 不复用原项目当前 `trainer_weighted.py / trainer_cmorl_stage2.py` 作为论文复现核心逻辑
3. 新代码放在 `cmorl_repro/`
4. 先忠实复现，再做创新
5. 每新增一个核心模块，都在 `docs/PAPER_MAPPING.md` 中记录其对应的论文部分

---

## 对 Codex 的工作顺序要求

建议按以下顺序开发：

### Step 1
创建 `cmorl_repro/` 目录结构和基础 README

### Step 2
实现 `envs/minicage_morl_env.py`
- 基于 MiniCAGE 输出三目标 reward 向量

### Step 3
实现 `models/actor_critic.py`
- actor
- vector critic

### Step 4
实现 `storage/rollout_storage.py`
- 支持向量 rewards / values / returns

### Step 5
实现 `algorithms/ppo_vector.py`
- actor 标量化 advantage 更新
- critic 向量 value regression

### Step 6
实现 `training/train_stage1.py`
- preference-driven initial policy pool

### Step 7
实现 `algorithms/selection.py`
- Pareto filtering
- crowding distance
- top-N selection

### Step 8
实现 `algorithms/ipo.py`
- log-barrier objective
- constrained extension update

### Step 9
实现 `training/train_stage2.py`
- 多轮 selection-extension

### Step 10
实现 `algorithms/assignment.py`
- SMP / policy assignment

### Step 11
实现 `training/evaluate.py`
- HV / EU / SP

---

# Part 4. 最终目标

短期目标：
- 在 MiniCAGE 上复现原论文风格的 C-MORL

中期目标：
- 在此基础上提出你自己的升级版算法

长期目标：
- 再把最佳版本迁移到更复杂的 CybORG / CybORG++ 环境中验证
