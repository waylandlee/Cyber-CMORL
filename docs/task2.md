## 一、先说最重要的结论

你要做的表格结构我建议调整成下面这样：

### 主表 A：Pareto / utility

- **Ours (Stage-2 / current best method)**
- **Weighted-Sum**
- **Preference-Conditioned PPO**
- **PCN**

### 主表 B：约束处理

- **Ours (从 Pareto set 中取满足约束且主目标最优的策略)**
- **Lagrangian-PPO**

### 补充实验

- **No Pareto Extension** = `stage1-only`（这个其实已经有了）
- **No Constraint** = 需要新增
- **Single-Objective**（我建议补上，已经有现成入口，几乎零成本）
- **Multiseed stability**（至少 3 seeds，最好 5 seeds）

这里最关键的是：你仓库里当前 baseline 入口只正式支持 `sleep / random-valid / stage1-only / single-objective / weighted-sum`，其中 `weighted-sum` 和 `stage1-only` 已经能直接复用；但 **Preference-Conditioned PPO、PCN、Lagrangian-PPO 目前都没有现成训练入口**。同时，当前 `ActorCritic` 完全不接收 preference 输入，所以 **Preference-Conditioned PPO 不是调个配置就能跑**，必须新增条件化模型和训练脚本。

---

## 二、你仓库当前“已经有”的东西

### 1. 你的方法主线已经完整

仓库 README 和项目文档都说明了，当前 `cmorl_minicage` 已经具备：

- MiniCAGE 多目标包装
- Stage-1 Pareto initialization
- Stage-2 IPO-style extension
- SMP assignment
- HV / EU / SP evaluation
- YAML 驱动配置
- 统一 buffer / summary / metrics 输出  
    而 formal 主线目前推荐配置就是 `stage1_c2.yaml + stage2_c2.yaml + evaluate.yaml`。

### 2. Weighted-Sum 已经有现成实现

`baselines.py` 里的 `run_weighted_sum_baseline()` 已经存在，而且它本质上是复用 `train_stage1()`，用一组显式固定 preference 训练一组独立 policy。当前默认 preference 是 5 组固定权重。

### 3. “去掉 Pareto extension” 其实已经有

你补充实验里写的 “去掉 Pareto extension”，在当前仓库里其实就是 `stage1-only`。`baselines.py` 已经有 `run_stage1_only_baseline()`；项目文档里也把 `stage1-only` 作为当前正式 baseline suite 的一部分。

### 4. 你已经有 multiseed 验证框架

`multiseed.py` 已经可以批量跑 `Stage-1 -> Stage-2`，然后在**共享 reference point** 下汇总稳定性指标。这个脚本非常重要，因为你后面做主表时，不应该只给单 seed 结果。

---

## 三、你仓库当前“还没有”的东西

### 1. 没有 Preference-Conditioned PPO

当前 `ActorCritic` 的输入只有 `obs`，没有 `preference`；actor 输出离散动作分布，critic 输出向量 value。也就是说，它只支持“固定 preference 训练多个 policy”的 Stage-1，不支持“一个 policy 接收 preference 条件输入”。

### 2. 没有 PCN 的数据与训练链路

当前仓库没有轨迹归档、目标 return 条件输入、PCN-style command training 这条线。你现在有的是在线 PPO 和 Stage-2 extension，不是 PCN 需要的 command-conditioned imitation / archive pipeline。这个是你计划里最难的一块。

### 3. 没有 Lagrangian-PPO

虽然你的论文主方法和上传的 C-MORL 论文都涉及 constrained optimization / Lagrangian 思路，但仓库里当前并没有独立的 Lagrangian baseline 训练入口；`TASKS.md` 也把 CPO 分支列为未来工作。

### 4. 当前 `evaluate.py` 不适合直接评估单策略条件基线

`evaluate.py` 的逻辑是：  
读一个 `solution_buffer.json`，从中拿一组策略，做 Pareto filtering，再通过 `assign_policy()` 在 Pareto set 上做 SMP 分配并算 EU。这个逻辑天然适合 **multi-policy** 方法。

但你上传的 C-MORL 论文明确区分了两类评估方式：

- **multi-policy**：直接用 Pareto set 算 HV/SP
- **single preference-conditioned policy**：先在 evaluation preference grid 上逐个跑，再从这些结果里提 non-dominated solutions 去算 HV/SP。

所以，**Preference-Conditioned PPO 和 PCN 不能直接拿当前 `evaluate.py` 生搬硬套**，必须加一个 `evaluate_conditioned.py`。

---

## 四、我建议 Codex 先锁死的“统一实验协议”

这个部分最重要。你让 Codex 做实验，第一件事不是写算法，而是**冻结 protocol**。

### 1. 统一环境与 reward 口径

所有方法统一使用当前 formal 主线的环境和 reward 定义：

- `red_policy: bline`
- `num_envs: 8`
- `remove_bugs: true`
- `max_episode_steps: 100`
- `obj_dim: 3`
- reward 仍然是当前仓库正式采用的 `security / business / cost` 三目标  
    不要改 env，不要改 reward，不要改 reference 策略。

### 2. 主表 A 统一评估网格与 reference

所有方法统一使用：

- `preference_step: 0.1`
- `reference_strategy: data_min_range`
- `reference_margin: 0.25`
- `hv_max_exact_points: 18`
- `hv_mc_samples: 100000`  
    这和你当前 formal `evaluate.yaml` 一致。

### 3. 所有方法必须用**共享 reference point**

不能每个方法各算各的 reference point。  
你仓库当前 multiseed 里已经实现了 `_combine_reference_point()` 的思路，可以直接推广到“多方法共享 reference point”版本。

### 4. 训练预算必须统一

这是很多人最容易忽略的点。

按你当前 formal 配置：

- Stage-1：`num_policies=6`，每个 policy `total_timesteps=8192`  
    所以 Stage-1 总预算 = `6 × 8192 = 49152`
- Stage-2：`extension_rounds=2 × num_extension_policies=4 × obj_dim=3 × constrained_updates=2 × total_timesteps_per_update=1024`  
    所以 Stage-2 总预算 = `2 × 4 × 3 × 2 × 1024 = 49152`

于是 **Ours 总预算正好是 `98304` env steps**。  
我建议你让 Codex 统一把：

- Weighted-Sum
- Preference-Conditioned PPO
- PCN
- Lagrangian-PPO

都按 **98304 env steps** 来配预算。这样最公平。这个总预算推导来自当前 formal 配置和 `train_stage1.py / train_stage2.py` 的循环结构。

---

## 五、我建议 Codex 的实现顺序

### Phase 0：先补“评估与对比骨架”，不要先写 PCN

这是最稳的顺序。

先让 Codex做 4 个基础脚本：

1. `cmorl_minicage/evaluate_conditioned.py`  
    用于 Preference-Conditioned PPO / PCN
2. `cmorl_minicage/evaluate_constraints.py`  
    用于表 B
3. `cmorl_minicage/compare_suite.py`  
    输入多个方法结果，计算共享 reference point，导出主表 A CSV/JSON
4. `cmorl_minicage/configs/paper/`  
    专门放 paper configs，不污染 formal 旧配置

原因是：  
如果没有这 4 个骨架，就算 Preference-Conditioned PPO 训出来了，你也没法和现有 `solution_buffer.json` 体系公平合并。

---

## 六、每个方法，Codex 应该怎么实现

## A. Ours

这个最简单，直接复用当前 formal 主线：

- `stage1_c2.yaml`
- `stage2_c2.yaml`
- `evaluate.yaml`

然后额外做两个补充：

- `stage1-only`
- `no-constraint stage2`

当前 formal 主线已经是仓库里的标准入口。

### A1. No Pareto Extension

直接复用已有 `stage1-only`。  
不要重写。

### A2. No Constraint

建议 Codex这样做：

新增配置项：

- `stage2.extension_mode: constrained | unconstrained`

然后在 `train_stage2.py` 中：

- `unconstrained` 时仍保留：
    - selection
    - extension_rounds
    - num_extension_policies
    - objective-wise extension
- 但关闭：
    - IPO barrier bonus
    - feasibility gate
    - `constraint_tolerance` 判定

也就是保留 Stage-2 的结构，但不施加约束。  
这样才是真正“只去掉 constraints，别的都不动”的受控消融。  
因为当前 `IPOTrainer` 里 barrier bonus 是明确存在的，`train_stage2.py` 里 feasibility gate 也是明确存在的。

---

## B. Weighted-Sum

这个已经有，但我建议 Codex做两件小改动。

### B1. 别用默认 5 个权重，改成 paper 主表专用 preference 文件

当前默认只有 5 个权重。

我建议增加：

- `configs/paper/preferences_main_table_a.yaml`

里面放 6 或 10 个显式偏好，比如：

- [1.0, 0.0, 0.0]
- [0.75, 0.25, 0.0]
- [0.75, 0.0, 0.25]
- [0.5, 0.5, 0.0]
- [0.5, 0.25, 0.25]
- [0.5, 0.0, 0.5]
- [0.25, 0.75, 0.0]
- [0.25, 0.5, 0.25]
- [0.25, 0.25, 0.5]
- [0.0, 0.5, 0.5]

然后让 `baselines.py weighted-sum` 支持：

- `--preferences-file`

### B2. 预算要改成总预算 98304

当前 `run_weighted_sum_baseline()` 本质是 `_run_learning_baseline()`，它复用 Stage-1 配置。

所以让 Codex：

- 根据权重数 `K`
- 设置 `total_timesteps = 98304 / K`

这样和 Ours 总预算一致。

---

## C. Preference-Conditioned PPO

这是你最应该优先补的主基线。

### C1. 新文件

让 Codex新增：

- `cmorl_minicage/models/preference_conditioned_actor_critic.py`
- `cmorl_minicage/train_pref_conditioned_ppo.py`
- `cmorl_minicage/configs/paper/pref_cond_ppo.yaml`

### C2. 模型最小设计

最小可行版本：

- 输入：`concat(obs, preference)`
- actor：输出离散动作 logits
- critic：输出**标量 value**（对当前 preference 的 scalarized utility）

因为当前仓库是离散 actor，很适合直接扩展。当前 `ActorCritic` 结构也很简单，改成 conditional 版本不难。

### C3. 训练规则

最小稳妥实现：

- 每个并行 env 在 reset 时采样一个训练 preference
- 整个 episode 内该 preference 固定
- 每步用 `r_scalar = w · r_vec`
- 用 PPO 更新单个条件策略

不要一开始就做“每步切换 preference”，太容易训崩。

### C4. 评估规则

不能走当前 `evaluate.py`。  
要走新写的 `evaluate_conditioned.py`：

- 用 evaluation simplex grid 跑全套 preference
- 每个 preference 评估出一个 objective vector
- 收集所有点
- 对这些点评估：
    - nondominated filter
    - HV
    - SP
    - EU = 直接对每个 preference 的 utility 取平均

这正是你上传的 C-MORL 论文对 single preference-conditioned 方法的评估方式。

---

## D. PCN

这是整个计划里**最难的一项**。我的建议是：  
**让 Codex 最后实现。**

### D1. 新文件

- `cmorl_minicage/train_pcn.py`
- `cmorl_minicage/models/pcn_policy.py`
- `cmorl_minicage/datasets/trajectory_archive.py`
- `cmorl_minicage/configs/paper/pcn.yaml`

### D2. 最小可行版本

不要上来就追完整论文细节。  
先做一个 repo-compatible 的 **PCN-lite**：

1. 收集 trajectory archive  
    来源可以先用：
    - weighted-sum run
    - stage1-only run
    - random-valid rollout
2. 每条 transition 存：
    - obs
    - action
    - return-to-go vector
    - remaining horizon
3. 模型输入：
    - obs
    - desired return vector
    - desired horizon
4. 输出：
    - action logits
5. 训练：
    - 行为克隆 / 监督学习

### D3. 评估

和 Preference-Conditioned PPO 一样：

- 对 evaluation preference grid 逐个跑
- 得到 objective vectors
- nondominated filter
- 算 HV/EU/SP

### D4. 我对 PCN 的建议

如果 Codex第一轮做不稳，不要让它拖主实验进度。  
先把：

- Ours
- Weighted-Sum
- Preference-Conditioned PPO
- Lagrangian-PPO
- 两个补充实验

全部跑通，再补 PCN。

---

## E. Lagrangian-PPO

这是主表 B 的核心。

### E1. 新文件

- `cmorl_minicage/train_lagrangian_ppo.py`
- `cmorl_minicage/configs/paper/lagrangian_ppo.yaml`
- `cmorl_minicage/evaluate_constraints.py`

### E2. 推荐的 constrained problem

我建议表 B 不做“偏好网格”，而是固定一个部署约束问题：

- **主目标**：maximize `security`
- **约束**：
    - `business >= d_business`
    - `cost >= d_cost`

### E3. 阈值怎么定

最稳妥做法：

- 用 `stage1-only` 的 Pareto front
- 取其中 `business` 和 `cost` 的 **25% 分位点**作为阈值  
    即：
- `d_business = q25(stage1_pareto.business)`
- `d_cost = q25(stage1_pareto.cost)`

这样阈值不是拍脑袋定的，也不会直接看 stage2 最优结果，比较公平。

### E4. Lagrangian 更新最小实现

用你当前向量 critic 架构就能做：

- actor objective:
    
    Asec+λbAbusiness+λcAcostA_{sec} + \lambda_b A_{business} + \lambda_c A_{cost}Asec​+λb​Abusiness​+λc​Acost​
    
    因为你的约束形式是“business/cost 越大越好，且要超过下界”
    
- dual update:
    
    λi←max⁡(0,λi+α(di−Gi))\lambda_i \leftarrow \max(0, \lambda_i + \alpha(d_i - G_i))λi​←max(0,λi​+α(di​−Gi​))

也就是说，business/cost 低于阈值时，乘子增大。

### E5. 表 B 的评估方式

表 B 不看 HV。  
看：

- `security return`
- `business return`
- `cost return`
- `mean constraint violation`
- `feasible rate`
- `critical_impact_count`
- `high_disruption_action_rate`

对于你的方法，不是重新训练单个 constrained policy，而是：

**从最终 Pareto set 中选出满足约束且 security 最高的那个 policy**，然后和 Lagrangian-PPO 对比。

这样是合理的，因为你的方法本来就是“先学 Pareto set，再 assignment / selection”。

---

## 七、我建议 Codex 新增的脚本与配置

### 新增脚本

- `train_pref_conditioned_ppo.py`
- `train_pcn.py`
- `train_lagrangian_ppo.py`
- `evaluate_conditioned.py`
- `evaluate_constraints.py`
- `compare_suite.py`
- `export_tables.py`

### 新增配置目录

- `cmorl_minicage/configs/paper/`

建议至少包括：

- `stage1_main.yaml`
- `stage2_main.yaml`
- `stage2_no_constraint.yaml`
- `weighted_sum_main.yaml`
- `pref_cond_ppo.yaml`
- `pcn.yaml`
- `lagrangian_ppo.yaml`
- `evaluate_main_table_a.yaml`
- `evaluate_main_table_b.yaml`
- `preferences_main_table_a.yaml`

### 新增输出目录

- `outputs/paper_table_a/`
- `outputs/paper_table_b/`
- `outputs/paper_appendix/`

---

## 八、建议的运行顺序

### Step 1：先跑当前主方法与已有 baseline

1. Ours Stage-1
2. Ours Stage-2
3. stage1-only
4. weighted-sum
5. single-objective

这一步你仓库已经基本支持。

### Step 2：补 evaluator

1. `evaluate_conditioned.py`
2. `compare_suite.py`
3. `evaluate_constraints.py`

### Step 3：补新的 baseline

1. Preference-Conditioned PPO
2. Lagrangian-PPO
3. PCN

### Step 4：跑 smoke

每个新 baseline 先做 smoke：

- 2 seeds 以内
- 少量 timesteps
- 检查输出 JSON 和 plot 是否兼容

### Step 5：跑 formal

主表 A：

- 5 seeds，统一 reference point

主表 B：

- 5 seeds，统一 thresholds

### Step 6：导出表与图

至少输出：

- `table_a_metrics.csv`
- `table_b_constraints.csv`
- `main_table_a_pairwise.png`
- `main_table_b_bar.png`
- `appendix_ablations.csv`

---

## 九、结果怎么分析

## 表 A：Pareto / utility

你最应该关注：

### 1. HV

如果 Ours 最高，说明你在 MiniCAGE 上确实更会发现前沿。  
这是你最核心的 claim。

### 2. EU

如果 Preference-Conditioned PPO 的 EU 不差，但 HV 明显低于 Ours，说明：

- 单策略条件方法能“适应偏好”
- 但不能很好覆盖 Pareto front

### 3. SP

如果 Ours HV 高，但 SP 不最好，也正常。  
你上传的 C-MORL 论文里就明确提到：某些方法 SP 看起来低，可能只是因为它只找到一小块相似点，而不是 front 真更好。

### 4. assignment summary

你当前 `evaluate.py` 已经会输出：

- `coverage_ratio`
- `unique_assigned_policies`
- `mean_assigned_utility`  
    这些都应该进入表 A 的补充说明。

---

## 表 B：约束处理

你最应该关注：

### 1. feasible rate

Lagrangian-PPO 如果 feasible rate 高，但 security 很低，说明太保守。

### 2. mean violation

如果 violation 低但 utility 全线差，说明约束压得太死。

### 3. security vs semantic metrics

特别看：

- `critical_impact_count`
- `high_disruption_action_rate`
- `final_critical_compromised_hosts`  
    这些是你 cyber 论文最有说服力的结果层语义指标。当前仓库已经有这些指标。