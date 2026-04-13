# 实验结果汇总与使用说明（2026-04-13）

## 这份文档覆盖什么

- 本文件主要汇总 `Task 4` 与 `Task 5` 的跨任务结果结论，以及后续补充得到的关键判断。
- 它不是完整的任务执行日志；详细过程、逐步修正和配置演化仍以对应的 `task*.md` 为准。
- 当前项目已经决定先暂停继续扩实验，因此本文件的主要作用是帮助后续写论文、整理附录和统一结论口径。

## 配套文档

- `task0.md`：当前最高层实验判断、论文口径和 claim 边界。
- `task4.md`：Dual-Archive 评估与选择语义、B-fix 门控和是否转向 mainline A 的详细过程。
- `task5.md`：mainline A / CVaR conservative branch 的任务设计与后续结果补充。
- `docs/TASKS.md`：项目总状态、任务分工和推荐阅读顺序。
- `todo.md`：当前“不继续扩实验”前提下的文档、论文和交付待办。

## 当前总判断

- 当前不需要再新增一整套大实验，优先做结果收口、文档补齐和论文成稿。
- 主线 B 已完成公平修正与验证；若未来恢复方法实验，应从 `mainline A / CVaR conservative branch` 接续。
- 现阶段最重要的不是继续跑更多实验，而是把已有结果的适用范围、限制和论文表述写清楚。

# Task 4 结果结论

## 一、当前实验结论

基于 seed `0007` 的预算对齐可比实验，当前 `Dual-Archive Stage2` 的结果**不能**被概括为“已经解决了候选池组织问题，只剩尾部风险没有解决”。更准确的结论是：

1. `Dual-Archive` 在工程上已经形成了完整的双档案训练、评估、导表与选择语义链路。
2. 但在当前这轮正式可比实验中，`A_cons` 并没有真正形成可部署的 strict 候选池。
3. 因此，当前失败**不能单纯归因于 tail failures**，而首先暴露出 conservative archive 的语义标注、路由阈值和分支生成能力没有对齐。

换句话说，这一轮结果说明的不是“主线 B 已经完成，只剩下 CVaR 风险控制”，而是：

> 主线 B 当前还没有被公平地按其设计意图运行起来。  
> 在此基础上，tail-risk 问题很可能仍然存在，但它不是当前唯一、也不是最先暴露出来的根因。

## 二、关键实验现象

### 1. Set-quality 结果并不支持“union front 更强”

共享参考点下，三种方法的 Table A 结果如下：

- `Original Stage2`
  - `HV = 1923403.0156`
  - `EU = -171.3691`
  - `coverage = 0.1875`
  - `Pareto count = 16`
- `AdaCS-DCS`
  - `HV = 1890954.7344`
  - `EU = -171.3308`
  - `coverage = 0.3333`
  - `Pareto count = 12`
- `Dual-Archive Stage2`
  - `HV = 1835675.2891`
  - `EU = -171.3703`
  - `coverage = 0.3000`
  - `Pareto count = 10`

这说明：

- `Dual-Archive` 的 `coverage` 比 `Original Stage2` 更高，但没有超过 `AdaCS-DCS`
- `Dual-Archive` 的 `HV` 低于两个基线
- 因而当前结果**不支持**“union front 更强”或“HV / EU / coverage 已经整体更均衡”

### 2. strict selector 当前不是“更干净”，而是基本为空

三种方法在这轮可比评估中都出现了：

- `strict_candidate_count = 0`
- `strict_hit_rate = 0.0`
- `hybrid_fallback_rate = 1.0`

这说明当前 strict 模式下没有任何候选能够被正式命中，hybrid 也完全依赖 union fallback。  
对于 `Dual-Archive` 而言，这意味着：

> `A_cons` 目前在训练输出里存在，但在部署语义上并没有真正转化为 strict 可部署候选集合。

### 3. critical host 风险没有改善，甚至更差

从 union replay 的语义指标看：

- `Original Stage2` 的 `final_critical_compromised_hosts = 0.2658`
- `AdaCS-DCS` 的 `final_critical_compromised_hosts = 0.4710`
- `Dual-Archive Stage2` 的 `final_critical_compromised_hosts = 0.7652`

因此，当前结果**不能**支持“主线 B 已经把候选池组织做好，只剩少数尾部 episode 有问题”。更准确的说法是：

> 当前 `Dual-Archive` 甚至还没有把平均层面的 critical-risk 语义压到优于基线的水平。

## 三、问题的根本原因

### 根因 1：`A_cons` 中大量记录缺少 strict 选择所需的语义字段

当前 `cons_records` 中大部分是从 Stage-1 seed 进入的记录。这些记录虽然被标记为 `archive_role = cons`，但通常缺少：

- `mean_violation`
- `near_feasible_flag`
- `tight_feasible_flag`
- `high_disruption_action_rate`
- `final_critical_compromised_hosts`

而 strict selector 的候选判定依赖的正是：

- `tight_feasible_flag`
- `near_feasible_flag`

结果就是：

> 很多被放进 `A_cons` 的记录，在 strict 语义里并不被视为候选。

所以当前 `strict_candidate_count = 0` 并不完全等于“策略本身全都不安全”，而是部分来自 **archive 语义标注缺失**。

### 根因 2：conservative routing 的 `cost_margin` 与当前 reward 符号失配

当前 `Dual-Archive` 配置中：

- `cons_thresholds.cost_margin = 0.0`

但这轮训练出来的 child 的 `cost_return` 全部是负值，范围大致在：

- `-20.5750` 到 `-0.3721`

conservative routing 逻辑要求：

- 如果 `cost_return < cost_margin`，则不能进入 `cons`

这意味着在当前 reward 符号下，几乎所有新 child 都会因为 cost gate 被排除在 `A_cons` 之外。

最典型的例子是 `stage2_ext_009_obj_2`：

- `feasible_flag = True`
- `near_feasible_flag = True`
- `tight_feasible_flag = True`
- `mean_violation = 0.0`

按直觉它已经非常接近 strict 候选，但它仍然被路由进了 `uc`，原因正是 `cost_return` 仍小于当前的 `cost_margin = 0.0`。

这说明：

> 当前 `A_cons` 的失败并不只是“tail-risk 没压住”，而是 conservative gate 的阈值定义本身就和实际 reward 分布不兼容。

### 根因 3：`uc` 接纳条件过宽，导致双档案结构失衡

当前 `uc_thresholds` 为：

- `delta_eu = 0.0`
- `delta_coverage = 0.0`
- `novelty = 0.0`
- `spread_gain = 0.0`

这使得 child 只要略微有一点 novelty / spread gain，就很容易进入 `uc`。  
与此相对，`cons` 的门又过严，于是系统实际表现为：

- `cons` 基本冻结为 Stage-1 seed 档案
- `uc` 持续吸收新增 child

因此当前双档案并没有形成“保守档案 + utility/coverage 档案”的平衡结构，而更像是：

> 一个静态 `A_cons` 加上一个不断扩张的 `A_uc`

### 根因 4：conservative branch 本身没有产出成功 child

从 Stage-2 summary / diagnostics 可以看到：

- 两轮里 `cons_generated_policy_ids` 都是空的
- 所有成功接受的新 child 都来自 `adacs_dcs`
- `route_counts` 基本表现为 `from_adacs_to_uc = 11`

这说明当前问题还包括：

> conservative branch 的 operator 本身没有有效生成新保守候选。

因此，这一轮失败同时包含：

- conservative archive 语义问题
- routing threshold 问题
- operator generation 问题

而不是一个已经“只剩尾部风险”的成熟主线。

## 四、现在是否应该直接转向 mainline A / CVaR conservative branch

当前证据支持下面这个判断：

### 不能直接下结论说：“B 已经完成，只剩 tail risk，所以必须立刻切 A”

原因是：

- `A_cons` 还没有被公平地建立起来
- strict candidate pool 为空，不完全是因为策略本身，而也因为语义标注和 routing 机制有结构性问题
- 这意味着当前实验还不足以证明 “Dual-Archive 的组织能力已经到位，只差 risk-aware objective”

### 但也不能说：“B 已经没问题，不需要 A”

因为即使把上面的结构问题考虑进去，当前 replay 结果仍然显示：

- `final_critical_compromised_hosts` 没有改善
- `high_disruption_action_rate` 也没有显著变好

这说明：

> 即便修正主线 B 的结构性问题，下一层最可能遇到的真实瓶颈，仍然会是 tail-risk / risk semantics。

因此，当前最合理的判断不是“立即放弃 B”，也不是“继续无限打磨 B”，而是：

> **先对主线 B 做一次窄范围、针对根因的修正。**  
> 如果修正后 `A_cons` 仍然不能形成 strict candidate，或者 critical-risk 指标仍无改善，再正式把主线切到 `mainline A / CVaR conservative branch`。

## 五、对主线 B 的建议：需要改良，但只做窄范围改良

当前我认为：**是的，需要改良 B。**  
但这里的改良不是继续做大规模调参，而是只修三个最根本的问题。

### 改良 1：补齐 `A_cons` 的语义字段

目标：

- 让 `cons_records` 中的记录真的能被 strict selector 识别

具体要做：

- 对 Stage-1 seed 进入 `A_cons` 的记录，补齐或回填：
  - `mean_violation`
  - `feasible_flag`
  - `near_feasible_flag`
  - `tight_feasible_flag`
  - `high_disruption_action_rate`
  - `final_critical_compromised_hosts`
- 如果一条记录没有这些字段，就不要把它当成 strict candidate pool 的正式成员

这一步的目标不是提升性能，而是确保：

> `A_cons` 的“档案含义”和 strict selector 的“候选含义”是一致的。

### 改良 2：修正 conservative routing 的 cost gate

目标：

- 避免 `cost_margin = 0.0` 在负 cost-return 语义下把所有 child 都挡在 `cons` 外

建议做法：

- 不要再使用绝对阈值 `cost_return >= 0.0`
- 改成相对式约束，例如：
  - 与 parent 相比的 `delta_cost`
  - 或允许一定范围的负 cost margin
- 至少要让“tight feasible 且 mean_violation = 0”的 child 有机会进入 `cons`

这一步的目标是修正：

> 当前 conservative routing 因 reward 符号失配而几乎不可达的问题。

### 改良 3：收紧 `uc` 接纳条件

目标：

- 防止 `uc` 因零阈值而吸收几乎所有新 child

建议做法：

- 把以下阈值从 `0.0` 调成明确的正阈值：
  - `delta_coverage`
  - `spread_gain`
  - `novelty`
- 避免“极小的数值波动”也被当成有效 utility/coverage 增益

这一步的目标是恢复双档案的结构平衡，让：

- `cons` 真的承担保守部署语义
- `uc` 真的承担探索与覆盖语义

### 改良 4：单独验证 conservative operator 是否有生成能力

目标：

- 分离“archive 组织失败”和“operator 本身不会生成候选”这两个问题

建议做法：

- 先保持双档案结构不变
- 单独检查当前 `cons_operator_mode = original` 为什么连续两轮没有成功 child
- 必要时做一次对照：
  - 保持 routing 不变
  - 仅替换 conservative branch 的 operator 或约束更新策略

这一步不是为了立刻换方法，而是为了回答一个更基本的问题：

> 当前失败到底是 conservative operator 不会长，还是长出来了却被 routing 丢掉了？

## 六、最终判断

当前最稳妥的正式判断是：

> 这轮 seed `0007` 的可比结果并不支持“主线 B 已经解决了候选池组织问题，只剩 tail-risk 没解决”这一说法。  
> 当前首先暴露出的，是 `A_cons` 没有真正建立起来，其根因包括语义字段缺失、conservative routing 的 cost gate 与 reward 符号失配、`uc` 接纳条件过宽，以及 conservative branch 本身缺少成功 child。  
> 因此，应该先对主线 B 做一次窄范围、结构性修正，再决定是否正式转向 `mainline A / CVaR conservative branch`。  
> 如果这些修正完成后，strict candidate pool 仍然为空，或者 critical-risk 指标仍无改善，那么转向 risk-aware conservative branch 就将变成更有把握、也更有说服力的主线选择。

# Task 5 结果结论

## 一、实验目标与设定

Task 5 的目标不是回退到单档案 Stage-2，也不是继续打磨当前主线 B 的 conservative operator，而是：

> 在保留 Dual-Archive 训练—评估—导表—选择语义框架不变的前提下，仅对 `A_cons` 分支接入 rollout-based CVaR penalty，验证 risk-aware conservative branch 能否恢复 strict 候选池。

本轮实验固定保持：

- `A_uc` 不变
- strict / hybrid selector 不变
- archive-aware evaluate / compare / export pipeline 不变
- 只在 `A_cons` 上加入基于 rollout episode risk sample 的 CVaR tail penalty

CVaR v1 仅使用一个风险指标：

- `final_critical_compromised_hosts`

## 二、核心实验结论

本轮实验的正式结论是：

> **Task 5 第一版 `Dual-Archive + CVaR Cons` 在工程接入上是成功的，但在方法验证上未达到目标。**

更具体地说：

1. CVaR penalty 已经被正确接入 `A_cons` 的训练链路，并能够稳定记录 conservative risk 统计信息。
2. 但在 fair-budget `seed_0007` 的正式比较中，它没有恢复 strict candidate pool，也没有让 `A_cons` 出现 routed child。
3. 因此，当前这版 rollout-level scalar CVaR penalty **不足以让 `A_cons` 站起来**。

## 三、smoke 结果说明了什么

在 smoke 对照中，`B-fix Dual-Archive` 与 `Dual-Archive + CVaR Cons` 均出现了非零的 `cons_successful_children`，说明：

- CVaR 接入并没有破坏 `A_cons` 的训练流程
- conservative branch 在小预算下并非完全空转

但两组方法在 smoke 中仍然同时表现为：

- `cons_routed_children = 0`
- `strict_candidate_count = 0`
- `strict_hit_rate = 0`

这说明 smoke 给出的只是一个**工程接线成功、训练链路未被打坏**的弱正向信号，而不是 conservative archive 已经恢复的证据。

## 四、fair-budget `seed_0007` 的正式结果

在 budget-aligned 的 `seed_0007` 正式比较中，`B-fix Dual-Archive` 与 `Dual-Archive + CVaR Cons` 的关键门控指标如下：

### B-fix Dual-Archive

- `cons_attempted_children = 18`
- `cons_successful_children = 0`
- `cons_routed_children = 0`
- `strict_candidate_count = 0`
- `strict_hit_rate = 0.0`
- `hybrid_fallback_rate = 1.0`
- `final_critical_compromised_hosts (hybrid) = 0.7014`
- `mean_violation (hybrid) = 5.8391`

### Dual-Archive + CVaR Cons

- `cons_attempted_children = 18`
- `cons_successful_children = 0`
- `cons_routed_children = 0`
- `strict_candidate_count = 0`
- `strict_hit_rate = 0.0`
- `hybrid_fallback_rate = 1.0`
- `final_critical_compromised_hosts (hybrid) = 0.6944`
- `mean_violation (hybrid) = 5.8391`

同时，CVaR 版本记录到了非零的 conservative risk 统计：

- `cons_cvar_estimate_tail = 1.0`
- `cons_risk_penalty_mean = 0.25`
- `cons_risk_rollout_count = 54`

这说明：

> CVaR 风险信号确实参与了训练，但它没有改变 conservative branch 的结构性结论。

## 五、如何解释这轮结果

这轮结果说明的不是“risk-aware 一定无效”，而是：

> **当前这版 rollout-level scalar CVaR penalty，虽然能够轻微压低尾部关键资产失陷风险，但它的强度和作用位置仍不足以改变 `A_cons` 的 child 生成与归档结果。**

从结果上看：

- `final_critical_compromised_hosts` 仅有轻微下降
- `mean_violation` 没有改善
- `strict_candidate_count` 仍为 0
- `strict_hit_rate` 仍为 0
- `hybrid` 仍完全依赖 fallback

因此，当前 CVaR v1 带来的只是**弱风险抑制**，而不是 conservative branch 的结构性恢复。

## 六、正式判断

因此，本轮实验的最终判断是：

> **Task 5 第一版失败。**

失败的含义不是“mainline A 永远无效”，而是：

- 仅在 rollout reward 上加入一个标量 `final_critical_compromised_hosts` CVaR penalty
- 还不足以让 `A_cons` 形成 strict / near-strict 候选
- 也不足以支撑真正可用的 conservative archive

这说明下一步若继续推进 mainline A，不能只是放大当前这版 scalar penalty，而应重新设计：

- conservative risk 的定义
- 风险信号进入训练目标的位置
- conservative objective 与 strict deployment semantics 的对齐方式

## 七、Task 5 v2 结果补充

在 Task 5 第一版失败之后，我继续执行了 `Task 5 v2`：

> 将 `A_cons` 的风险目标改成 strict-aligned composite risk，  
> 并把风险信号从“统一减 reward 标量 penalty”改为 `ppo_cost_surrogate` 形式直接接入 conservative update。

v2 固定采用：

- `cons_risk_mode = strict_aligned_cvar`
- `cvar_metric = strict_aligned_composite`
- `cons_risk_penalty_coef = 0.5`
- risk 组合为：
  - `1.0 * final_critical_compromised_hosts`
  - `1.0 * mean_violation`
  - `0.5 * high_disruption_excess`

### v2 smoke 结论

v2 smoke 相比 B-fix 出现了一个弱正向信号：

- `strict_candidate_count` 从 `0` 变成了 `1`

但同时仍然成立：

- `cons_routed_children = 0`
- `strict_hit_rate = 0.0`

因此，smoke 只能说明：

> v2 让 strict-aligned risk objective 在小预算下出现了轻微信号，  
> 但它还没有恢复 `A_cons` 的真实部署命中能力。

### v2 fair-budget `seed_0007` 结论

到了正式 fair-budget `seed_0007`，v2 的决定性门控指标再次全部回到失败状态：

- `cons_attempted_children = 18`
- `cons_successful_children = 0`
- `cons_routed_children = 0`
- `strict_candidate_count = 0`
- `strict_hit_rate = 0.0`

与此同时，训练侧风险统计仍然是非零的：

- `cons_cvar_estimate_tail = 1.0`
- `cons_risk_penalty_mean = 0.5`

这说明：

> v2 的风险目标确实进入了 conservative update，  
> 但它仍然没有改变 fair-budget 下 conservative branch 的结构性失败结论。

### v2 最终判断

因此，Task 5 v2 的正式结论是：

> **Task 5 v2 失败。**

更准确地说：

1. strict-aligned composite CVaR 比 v1 提供了更贴近部署语义的风险定义。
2. 它在 smoke 中给出了短暂的弱正向信号。
3. 但在 fair-budget `seed_0007` 中，这个信号没有保留下来。
4. 所以当前问题已经不能再简单归结为“risk metric 选得不够贴近 strict semantics”。

现阶段更可信的判断是：

> conservative branch 的主要瓶颈仍然不仅是 risk objective，  
> 而是 `operator -> feasible child generation -> archive routing -> strict deployment pool` 这一整条链路，在正式预算下没有真正打通。

## 八、Task 5 v3-A 结果补充

在 v2 失败之后，我继续执行了 `Task 5 v3-A 2×2 可归因优化计划`。  
v3-A 固定保留：

- `strict_aligned_cvar`
- `ppo_cost_surrogate`
- `cons_risk_penalty_coef = 0.5`

只做两条轴的 2×2 主消融：

- `operator`:
  - `original`
  - `adacs_dcs`
- `failure protocol`:
  - `max_consecutive_constraint_failures = 1`
  - `max_consecutive_constraint_failures = 2`

对应四组：

- `A0`: `original + fail=1`
- `A1`: `adacs_dcs + fail=1`
- `A2`: `original + fail=2`
- `A3`: `adacs_dcs + fail=2`

### v3-A smoke 结论

smoke 上四组结果完全一致：

- `cons_attempted_children = 6`
- `cons_successful_children = 6`
- `cons_routed_children = 0`
- `best_near_feasible_children = 1`

这说明：

> smoke 只能验证配置矩阵和新增 diagnostics 正常工作，  
> 但它不足以区分 operator 与 failure protocol 的真实作用。

### v3-A fair-budget `seed_0007` 结论

到了正式 fair `seed_0007`，2×2 消融出现了清晰分离：

- `A0`
  - `cons_successful_children = 0`
  - `cons_routed_children = 0`
  - `best_near_feasible_children = 0`
  - `failure_stage = constraint_margin_fail` 共 18 次
- `A1`
  - `cons_successful_children = 5`
  - `cons_routed_children = 0`
  - `best_near_feasible_children = 0`
  - `failure_stage = route_rejected_after_save` 共 5 次
- `A2`
  - `cons_successful_children = 0`
  - `cons_routed_children = 0`
  - `best_near_feasible_children = 0`
  - `failure_stage = constraint_margin_fail` 共 18 次
- `A3`
  - `cons_successful_children = 4`
  - `cons_routed_children = 0`
  - `best_near_feasible_children = 0`
  - `failure_stage = route_rejected_after_save` 共 4 次

### v3-A 正式归因

因此，按 v3-A 的 2×2 判读规则：

- `A1 > A0`
- `A2 ≈ A0`
- `A3` 没有明显优于 `A1`

可以正式得出：

> **operator 是当前 `A_cons` 的第一主瓶颈。**

更具体地说：

1. 只切换到 `adacs_dcs`，就能把 fair 中的 `cons_successful_children` 从 `0` 拉到 `5`。
2. 只放宽 `max_consecutive_constraint_failures`，并不能单独恢复 successful child。
3. 两者同时上也没有超过 `A1`，说明 failure protocol 不是当前第一决定因素。

### v3-A 之后的新瓶颈

v3-A 同时也告诉我们：

- `A1` / `A3` 已经能生成 successful child
- 但这些 child 全部被 route 到 `A_uc`
- `best_near_feasible_children` 仍然是 `0`
- `cons_routed_children` 仍然是 `0`

所以当前主问题已经从：

- “生成不出 conservative child”

转移为：

- “生成出的 child 仍然不满足 near / tight conservative semantics，因此进不了 `A_cons`”

换句话说，v3-A 的最终结论不是“Task 5 已成功”，而是：

> **v3-A 成功完成了归因，但没有完成 conservative route 恢复。**

最重要的实质性收获是：

> 下一步如果继续推进，不应再优先纠结 `failure protocol`，  
> 而应把 `A1` 作为新的最强基线，转向分析 successful child 为什么全部在 route 后变成 `accepted_uc`，以及 near / tight feasibility 语义为什么仍然过不去。

### A1 的 5 个 successful child：为什么都“只差一步”却还是没进 `A_cons`

这里需要先澄清一个容易误读的点：

- `extension_results` 里的 `feasible_flag / near_feasible_flag`
  - 表示的是 **IPO 训练时的 constraint-margin 可行性**
  - 它回答的是“这个 child 是否已经不再因为约束更新连续失败而中止”
- `A_cons` route 真正使用的则是 archive strict semantics：
  - `relative_cost_ok = True`
  - `mean_violation <= 0.5`
  - `final_critical_compromised_hosts <= 0.25`
  - `high_disruption_action_rate <= 1.0`
  - 满足这些条件后，才会得到 `best_near_feasible_flag = True` 或 `best_tight_feasible_flag = True`

因此，A1 的 5 个 successful child 看起来都“只差一步”，更准确地说是：

- 它们都已经跨过了 “生成失败 / 保存失败” 这一步
- 但还没有跨过 “strict deployment semantics” 这一步

也正因为如此，A1 中同时出现了下面这个表面矛盾、但其实合理的现象：

- `cons_successful_children = 5`
- `strict_candidate_count = 5`
- `best_near_feasible_children = 0`
- `cons_routed_children = 0`

含义是：

- 这 5 个 child 都是可保存、且语义字段齐全的 child
- 但它们在 strict 语义下没有一个真正达到 near-feasible
- 所以都没进 `A_cons`
- 同时又因为它们都有足够的 `spread_gain`，最后全部被 `A_uc` 吸收

#### 1. `stage2_ext_000_obj_0`

- parent: `stage1_pref_001_ckpt_191`
- `route_decision = accepted_uc`
- `cons_reason = rejected_feasibility`
- `relative_cost_ok = True`
- `spread_gain = 20.22`
- 训练侧 margin 语义上它已经是 successful child
- 但 archive strict 语义下它仍同时卡在两条线：
  - `mean_violation = 0.8824 > 0.5`
  - `final_critical_compromised_hosts = 1.0 > 0.25`

所以它离 `A_cons` 并不是“只差一个 route 开关”，而是：

> 已经跨过保存门，但 conservative semantics 还差 violation 和 final-critical 两条线。

#### 2. `stage2_ext_001_obj_1`

- parent: `stage1_pref_001_ckpt_191`
- `route_decision = accepted_uc`
- `cons_reason = rejected_feasibility`
- `relative_cost_ok = True`
- `spread_gain = 28.43`
- 它的 `final_critical` 曾短暂改善到 `0.9583`
- 但最终记录仍然没有进入 near/tight：
  - `mean_violation = 1.1768 > 0.5`
  - `final_critical_compromised_hosts = 1.0 > 0.25`

这说明它虽然在 operator 侧已经能产出“可保存”的 child，但这个 child 仍然明显不够保守。

#### 3. `stage2_ext_002_obj_0`

- parent: `stage1_pref_005_ckpt_191`
- `route_decision = accepted_uc`
- `cons_reason = rejected_feasibility`
- `relative_cost_ok = True`
- `spread_gain = 5.54`
- 它是 5 个 successful child 里最接近 `A_uc` 下限的一个，但仍然足以被 `uc` 接纳
- 它没有进 `A_cons` 的原因仍然是两条 near 语义都没过：
  - `mean_violation = 0.8305 > 0.5`
  - `final_critical_compromised_hosts = 1.0 > 0.25`

因此它说明的不是 “route 偶然偏向了 `uc`”，而是：

> 只要 conservative semantics 还不过线，而 `spread_gain` 又达到 `uc` 门槛，child 就会稳定流向 `A_uc`。

#### 4. `stage2_ext_008_obj_1`

- parent: `stage1_pref_001_ckpt_191`
- `route_decision = accepted_uc`
- `cons_reason = rejected_feasibility`
- `relative_cost_ok = True`
- `spread_gain = 6.96`
- 这是第二轮里最接近 “one more push” 的一个：
  - `mean_violation = 0.7998`
  - `final_critical_compromised_hosts = 0.9583`
- 但它仍然没有真正进入 near：
  - `mean_violation` 仍高于 `0.5`
  - `final_critical` 仍远高于 `0.25`

所以它看起来“很像已经差不多了”，其实仍然同时差着 violation 和 final-critical 两条语义线。

#### 5. `stage2_ext_009_obj_1`

- parent: `stage1_pref_005_ckpt_000`
- `route_decision = accepted_uc`
- `cons_reason = rejected_feasibility`
- `relative_cost_ok = True`
- `spread_gain = 43.99`
- 这是 5 个 child 里**唯一一个真的只差一步**的例子：
  - `mean_violation = 0.0439 <= 0.5`
  - `high_disruption_action_rate = 0.8942 <= 1.0`
  - `relative_cost_ok = True`
  - 但 `final_critical_compromised_hosts = 1.0 > 0.25`

也就是说，它离 `A_cons` 的最后阻塞项已经不再是 margin、也不再是 cost，而是：

> **关键资产最终失陷风险根本没有压下来。**

这也是为什么它虽然在表面上最像“almost there”，最终还是只能被 route 到 `A_uc`。

### 这个拆解告诉我们的精确结论

如果把 A1 的 5 个 successful child 全部拆开，最准确的说法不是：

> “这 5 个 child 都只差同一小步，route 稍微放宽就能进 `A_cons`。”

而是：

- 从 pipeline 阶段上看，它们确实都只差最后的 route 这一步
- 但从 strict semantics 上看，并不是 5 个都只差一条 conservative 条件
- 其中：
  - 4 个 child 仍然同时差 `mean_violation` 和 `final_critical`
  - 只有 `stage2_ext_009_obj_1` 真正只差 `final_critical` 这一条

因此，A1 的真正信息是：

> `adacs_dcs` 已经把 conservative branch 从“完全生成不出 child”推进到了“能生成并保存 child”，  
> 但这些 child 大多仍然停留在 margin-feasible / uc-useful，  
> 还没有进入 strict-deployable / cons-acceptable。

这意味着下一步最值得检查的，不是继续单独放宽 failure protocol，而是：

- 为什么 operator 生成出的 child 在 `final_critical` 上几乎都还停在 `0.9583 ~ 1.0`
- 为什么一旦 child 有 `spread_gain >= 5.0`，它就会稳定被 `A_uc` 吸走
- 是否需要把 `A_cons` 的 near/tight 语义与训练目标再做一次更直接的对齐

因此，后续若继续推进 `mainline A`，不应再只做 penalty 形式上的局部增强，而应优先审视：

- conservative operator 本身是否足够产生可部署 child
- 当前 route / feasibility protocol 是否仍然把本可用 child 挡在 `A_cons` 之外
- strict deployment semantics 与训练目标之间是否仍然存在结构性错位
