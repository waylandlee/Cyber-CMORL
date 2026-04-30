# Replay Diagnostics 结果结论

## 一、当前正式诊断结论

基于 `ours_stage2 / seed_0007 / thresholds_tight` 的 replay-only assignment diagnostics，当前问题应被归因为：

> `candidate_supply_problem`

更具体地说，这一轮结果不支持“当前失败主要来自 assignment rule 选错了候选”。  
相反，它表明：

1. 在固定 candidate set 上，当前 `pareto` 候选池中**不存在 strict 候选**。
2. 同一 candidate set 上，即使把 selector 从 `utility_argmax` 换成 `strict_lexi` 或 `risk_adjusted_utility`，也**无法选出 strict 或 near-strict 候选**。
3. 因此，这一轮 strict failure 的主因不是 selection，而是 **strict candidate supply 不足**。

## 二、Phase A：Replay-Only Assignment Diagnostics

本轮正式诊断的输入为：

- `buffer_path = cmorl_cyborg/outputs/paper_table_a/ours_stage2/seed_0007/run_ddb937f9/solution_buffer.json`
- `source_set = pareto`
- `thresholds_path = cmorl_cyborg/outputs/fair_compare_eval/thresholds_tight.json`
- strict 语义上限额外固定为：
  - `mean_violation <= 0.50`
  - `final_critical_compromised_hosts <= 0.25`
  - `high_disruption_action_rate <= 0.50`

固定 candidate set 的 replay 结果如下：

- `candidate_count = 12`
- `strict_candidate_count = 0`
- `near_candidate_count = 0`
- `num_preferences = 66`

这说明当前 candidate pool 中既没有 strict 候选，也没有“距离 strict 很近”的 near-strict 候选。

### 1. 三个 selector 的对照结果

- `utility_argmax`
  - `selected_strict_count = 0`
  - `selected_near_count = 0`
  - `avg_strict_margin = -11.6256`
  - `avg_mean_violation = 12.1256`
  - `avg_final_critical_compromised_hosts = 0.4856`
  - `avg_high_disruption_action_rate = 0.9255`
- `strict_lexi`
  - `selected_strict_count = 0`
  - `selected_near_count = 0`
  - `avg_strict_margin = -5.5592`
  - `avg_mean_violation = 6.0592`
  - `avg_final_critical_compromised_hosts = 0.9000`
  - `avg_high_disruption_action_rate = 0.9390`
- `risk_adjusted_utility`
  - `selected_strict_count = 0`
  - `selected_near_count = 0`
  - `avg_strict_margin = -8.3860`
  - `avg_mean_violation = 8.8860`
  - `avg_final_critical_compromised_hosts = 0.7216`
  - `avg_high_disruption_action_rate = 0.8881`

这组结果说明：

1. selector 改动能改变“选到的非 strict 候选长什么样”，但**不能把 0 strict 变成非 0**。
2. `strict_lexi` 已经把平均 strict margin 从 `-11.6256` 拉到 `-5.5592`，说明它确实在努力选“相对更接近 strict”的 candidate。
3. 即便如此，最好的平均 strict margin 仍远小于 `0`，因此当前失败并不是“有 strict 候选但 baseline 没选中”。

### 2. Selector 的实际选择模式

- `utility_argmax` 在 `66` 个 preference 中主要选中：
  - `stage1_pref_000_ckpt_191`：`56` 次
- `strict_lexi` 在 `66` 个 preference 中：
  - 全部都选中 `stage2_ext_005_obj_0`
- `risk_adjusted_utility` 在 `66` 个 preference 中共选中 `5` 个不同 candidate
  - 其中 `stage1_pref_000_ckpt_096` 被选中 `38` 次

这说明 replay 版 selector 确实有不同偏好，但这些偏好变化仍然只是在“严格失败的候选”之间重排。

## 三、Phase B：Offline Strict-Level Diagnostics

由于 Phase A 已经判定为 `candidate_supply_problem`，系统自动执行了离线 strict-level diagnostics。

当前结果是：

- `best_level_reached_counts`
  - `L0 = 0`
  - `L1 = 0`
  - `L2 = 0`
  - `L3 = 0`
  - `STRICT = 0`
- `unreached_count = 12`

这说明当前 `12` 个 candidate **连最宽松的 `L0` 都没有达到**。  
也就是说，问题不是“已经接近 strict，只差最后一跳”，而是：

> 当前 candidate pool 与 strict 语义之间仍存在显著距离。

### 1. `none -> L0` blocker histogram

- `mean_violation`：`12`
- `high_disruption`：`9`
- `business`：`7`
- `cost`：`5`

因此，这一轮最稳定、最主导的 blocker 是：

1. `mean_violation`
2. `high_disruption_action_rate`
3. `business` / `cost` 约束

值得注意的是，`final_critical_compromised_hosts` 没有出现在 `none -> L0` blocker histogram 里，不是因为它已经被解决，而是因为在当前更早的 level 上，`mean_violation` 和 `high_disruption` 已经先成为主导失败维度。

### 2. 最接近 strict 的 candidate 仍然很远

按 `STRICT` margin 从高到低排序，最接近 strict 的 candidate 是 `stage2_ext_005_obj_0`，其 replay 语义为：

- `business_return = -119.5501`
- `cost_return = -24.1928`
- `mean_violation = 6.0592`
- `final_critical_compromised_hosts = 0.9000`
- `high_disruption_action_rate = 0.9390`
- `strict_margin = -5.5592`
- `margin_L0 = -3.8474`

它的失败维度是：

- `cost`
- `mean_violation`
- `final_critical`
- `high_disruption`

这说明即使是当前“最接近 strict”的 candidate，也并不处在可通过轻微重排就能进入 strict 的状态。

## 四、这轮结果支持什么，不支持什么

### 支持的结论

1. 当前 `seed_0007 / tight` 线的主要问题是 **candidate supply problem**，不是 assignment selection problem。
2. replay-only selector 改写本身不足以救回 strict deployability。
3. 当前候选池离 `STRICT` 甚至离 `L0` 都还有明显距离，因此更像是“候选供给不足”，而不是“有一批 near-strict 候选但没被选中”。

### 不支持的结论

1. 不支持“当前 buffer 里已经有 strict 候选，只是 baseline selector 没选对”。
2. 不支持“已经形成了 near-strict reservoir，只需要做 deployment-time risk-aware assignment”。
3. 不支持“当前问题已经缩小到 final strict threshold 的最后一步”。

## 五、下一步解释

如果后续要继续推进，这一轮结果最直接支持的方向是：

1. 不再把主要精力放在 assignment 规则本身。
2. 优先关注 **如何提升 strict / near-strict candidate supply**。
3. 如果要继续做离线分析，重点应围绕 `mean_violation`。
4. 第二个优先维度是 `high_disruption_action_rate`。
5. 第三个优先维度是 `business / cost` 约束。

换句话说，这一轮正式诊断给出的结论非常清楚：

> 当前问题首先不是“选谁”，而是“根本没有谁可选”。
