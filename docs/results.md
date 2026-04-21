# Strict-Feasible Stop-Loss And Deployability-Aware Upgrade Notes

## 2026-04-20 V2.4 Semantic Safety Update

当前主线已经切到 `V2.4 pre-critical containment`，而不是继续沿用本文件下面这条旧的 deployability-aware stop-loss 线。

### 当前结论

- `V2.4 = ours_stage2_fair_critical_safe_v2_4_4obj`
- `3-seed = 0007 / 0011 / 0019` 已全部完成
- `3/3 seeds pilot_passed = true`
- 最终 selected policy：
  - `seed_0007 -> stage2_ext_008_obj_0`
  - `seed_0011 -> stage2_ext_005_obj_1`
  - `seed_0019 -> stage2_ext_005_obj_2`
- 三颗 seed 的 selected replay20 semantic audit 共同结果：
  - `ever_critical_breach_rate = 0.0`
  - `persistent_critical_breach_rate = 0.0`
  - `mean_critical_dwell_steps = 0.0`
  - `high_confidence_env_run_rate = 0.0`
  - `Q2 / Q3 / Q5 = 0.0`
  - `Q4` 仅在 `seed_0007` 留有极小残留：`0.00625`
- pre-critical containment 机制在三颗 seed 上都呈现一致行为：
  - `precritical_action_family_step_rates.restore = 1.0`
  - `precritical_action_family_step_rates.decoy = 0.0`
  - `precritical_compromised_target_focus_step_rate = 1.0`
- 仍保留的限制：
  - `Tier 1 Near-Miss = 1.0`
  - 当前语义图景是“总能在 pre-critical 阶段拦住”，不是“全程完全无险情”

关键产物：

- [seed_0007_final_summary.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/fair_compare_critical_safe_v2_4_4obj_runner/seed_0007_final_summary.json)
- [seed_0011_final_summary.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/fair_compare_critical_safe_v2_4_4obj_runner/seed_0011_final_summary.json)
- [seed_0019_final_summary.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/fair_compare_critical_safe_v2_4_4obj_runner/seed_0019_final_summary.json)

### V2.4 独立导表支线

本轮已经把 `V2.4` 单独接入 `table_a / table_b` 导表链，并产出一版专属 row：

- set-quality summary：
  - [table_a_summary.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_table_v2_4/table_a/table_a_summary.json)
  - [table_a_metrics.csv](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_table_v2_4/tables/table_a_metrics.csv)
- deployment summary：
  - [ours_stage2_v2_4.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_table_v2_4/table_b/aggregated/ours_stage2_v2_4.json)
  - [table_b_constraints.csv](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_table_v2_4/tables/table_b_constraints.csv)

`V2.4` 专属 row 的当前数值：

- `table_a`
  - `hypervolume = 1764.2480 ± 1117.9673`
  - `expected_utility = -41.9193 ± 4.1438`
  - `coverage_ratio = 0.6048 ± 0.0875`
  - `unique_assigned_policies = 3.3333 ± 1.2472`
  - `final_critical_compromised_hosts = 0.0000 ± 0.0000`
- `table_b`
  - `security_return = -170.5713`
  - `business_return = -27.8684`
  - `cost_return = -20.6367`
  - `feasible_rate = 0.6667`
  - `mean_violation = 0.4066`
  - `final_critical_compromised_hosts = 0.0000`
  - `critical_impact_count = 0.0000`

### 当前判断

- `table_b` 这行已经具备论文候选行价值，因为它直接聚合了三颗 seed 的最终 selected deployment metrics，没有绕开 `audit-aware reselection`。
- `table_a` 这行当前只适合做 `V2.4` 自己的 set-quality 体检，不应直接与现有论文主表 A 横向比较。
- 原因有两层：
  - 这版 `table_a` 只在 `V2.4` 自己的方法集合上重算了 shared reference point
  - 更关键的是，`V2.4` 当前是 `4-objective` 语义安全线，而现有论文主表 A 仍是旧的 `3-objective` 口径
- 因此，当前最稳的结论是：
  - `V2.4 table_b` 可以作为主表替换候选或新增方法行候选
  - `V2.4 table_a` 更适合作为补充表，或在论文正式升级到 `4-objective` 主线后再讨论是否替换主表 A

### 下一步

- 若要把 `V2.4` 正式推入论文主表，需要先做 paper-level 决策：
  - 继续保留旧 `3-objective Table A`
  - 还是把 set-quality 主表整体升级到 `4-objective semantic safety` 口径
- 在这个决策之前，`V2.4` 最稳妥的摆放方式是：
  - `Table B` 先作为新增方法行候选
  - `Table A` 先作为补充表或独立 semantic-safety set-quality 表

## Historical Notes

下面内容保留为旧 stop-loss / deployability-aware 升级记录，供回溯实现过程使用。

## Current Status

`main` 上这条线现在已经完成三件关键工作：

- reproducibility fix 已落地，并重新打通了 `metrics_sanity` gate
- `ours_stage2` 的 deployability-aware v1 升级已经实现到代码里，并通过了 focused unit tests + smoke verification
- `ours_stage2_deployability_v2` 的 hard-gate 版本也已经实现，并完成了 smoke + full `seed_0007` 验收

当前结论分两层：

- 机制结论不变：replay-only assignment diagnostics 仍然支持 `candidate_supply_problem`，不是 selector artifact。
- 工程状态已前进：我们不再停在“先修评估口径”，而是已经把 deployability-aware selection / tagging / acceptance 接进了 `Stage-2` 主线，并进一步验证了 hard gate 的效果边界。

## Replay-Only Baseline

当前机制基线仍然来自 replay-only assignment diagnostics：

- `buffer_path = cmorl_cyborg/outputs/paper_table_a/ours_stage2/seed_0007/run_ddb937f9/solution_buffer.json`
- `candidate_count = 12`
- `strict_candidate_count = 0`
- `near_candidate_count = 0`
- `diagnosis = candidate_supply_problem`

3 个 selector 都没有选出 strict candidate：

- `utility_argmax.selected_strict_count = 0`
- `strict_lexi.selected_strict_count = 0`
- `risk_adjusted_utility.selected_strict_count = 0`

这一步仍然 cleanly 排除了 “tight-feasible 失败主要来自 final assignment 规则” 这个解释。

## Reproducibility Fix

最初的 `metrics_sanity` 审计曾经失败：

- `mean_violation.max_abs_diff = 4.38000107`
- `high_disruption_action_rate.max_abs_diff = 0.02050000`
- `continue_to_next_phase = false`

现在这个问题已经修复并验证通过：

- 在 `evaluate_constraints` 的 episode 评估循环中，为每个 `episode_seed = base_seed + episode_idx` 同步固定 Python / NumPy / Torch RNG
- 评估结束后恢复调用方原始 RNG state，避免副作用污染
- 新增回归测试：
  - [tests/test_evaluate_constraints_reproducibility.py](/home/waylandlee/CMORL2/Cyber-CMORL/tests/test_evaluate_constraints_reproducibility.py:1)

重新生成 cache 并重跑 `metrics_sanity` 后：

- `cmorl_cyborg/outputs/metrics_sanity/tight_strict_seed0007_exec_20260415_reprofix/metrics_sanity_summary.json`
- `continue_to_next_phase = true`
- `mean_violation.max_abs_diff = 0.0`
- `high_disruption_action_rate.max_abs_diff = 0.0`

当前最合理的解释是：

- 之前的 gate 失败主要来自评估复现性问题，而不是 `business/cost` threshold sign bug
- 这个问题已经被修复并通过审计验证

## Deployability-Aware Upgrade

本轮已经把 `ours_stage2` 升级成 deployability-aware v1，但没有推翻两阶段主骨架。

保留不变的部分：

- `Stage-1 initialization`
- `Stage-2 constrained Pareto expansion`
- single-buffer maintenance
- deployment-time assignment

已经实现的升级点：

- 所有 candidate 现在都可以写入 `record["notes"]["deployability"]`
  - `business_return`
  - `cost_return`
  - `mean_violation`
  - `high_disruption_action_rate`
  - `final_critical_compromised_hosts`
  - `strict_margin`
  - `passed_strict`
  - `support_shell_reached`
  - `deployability_score`
- `Stage-2` parent pool 不再只能在 reward-space Pareto 上选
  - 新增 `selection.pool_mode`
  - 支持 `value_frontier + near_frontier + strict_frontier` 的显式 selection pool
- `adaptive` selection 不再强制在函数内部重新做 `nondominated_filter`
  - 这样 `near_frontier / strict_frontier` 不会在选择前被吞掉
- child acceptance 不再只是“reward-feasible 后保留最后一个可行点”
  - 现在 reward-feasible child 会按以下词典序比较：
    1. `support_shell_reached`
    2. `strict_margin`
    3. `deployability_score`
    4. 目标 objective improvement
- 新 child 会额外记录 `notes.deployability_acceptance`
  - `accepted_without_shell_gain`
  - `strict_margin_delta`
  - `deployability_score_delta`
  - `support_shell_before`
  - `support_shell_after`
- `solution_buffer.json` 顶层 schema 没有被破坏
  - `pareto_front` 仍保持 reward-space nondominated 语义
  - 新增的是 `metadata.deployability_frontiers` 只读视图：
    - `value_frontier_policy_ids`
    - `near_frontier_policy_ids`
    - `strict_frontier_policy_ids`

与这条升级一起落地的配置变更：

- `SelectionConfig` 新增：
  - `pool_mode`
  - `near_frontier_quota`
  - `strict_frontier_quota`
- 新增 profile config：
  - [ours_stage2_deployability.yaml](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/configs/paper/ours_stage2_deployability.yaml:1)

## Verification

focused unit tests：

- `conda run -n cc4 python -m pytest -q tests/test_deployability.py tests/test_assignment_diagnostics.py tests/test_evaluate_constraints_reproducibility.py tests/test_stage2_deployability_upgrade.py`
- 结果：`15 passed`

新增测试覆盖了：

- deployability tagging
- selection pool 组成
- child acceptance 优先级
- adaptive selector 在显式 non-pareto pool 上工作
- hard-gate predicate
- `cmorl_minicage / cmorl_cyborg` 双配置路径上的 `deployability_gate` 加载

### Smoke Verification

为了验证不是只有 helper 测试过，本轮还跑通了一个轻量 smoke：

1. fresh stage1 smoke：
   - `cmorl_cyborg/outputs/smoke/stage1_repro/run_7c6d995d/solution_buffer.json`
2. deployability-aware stage2 smoke：
   - `cmorl_cyborg/outputs/smoke/stage2_deployability/run_55e51760/solution_buffer.json`

smoke buffer 验证到的结构性结果：

- `metadata.deployability_frontiers` 已写入
- `record_count = 10`
- `with_deployability = 10`
- `with_acceptance = 1`

示例上可以确认：

- 所有 record 都带 `notes.deployability`
- 新生成的 child 带 `notes.deployability_acceptance`

smoke diagnostics 链路也已走通：

- assignment diagnostics：
  - `cmorl_cyborg/outputs/assignment_diag/stage2_deployability_smoke/assignment_diag_summary.json`
  - `candidate_count = 1`
  - `diagnosis = candidate_supply_problem`
- metrics sanity：
  - `cmorl_cyborg/outputs/metrics_sanity/stage2_deployability_smoke/metrics_sanity_summary.json`
  - `continue_to_next_phase = true`
  - `mean_violation.max_abs_diff = 0.0`
  - `high_disruption_action_rate.max_abs_diff = 0.0`

这说明：

- deployability-aware Stage-2 产物已经能被现有 diagnostics 链路正确消费
- 新加的 tagging / selection / acceptance 逻辑没有再次破坏 reproducibility gate

### Hard-Gate Smoke

v2 hard-gate 也已做过单独 smoke：

1. config：
   - `/tmp/ours_stage2_deployability_v2_smoke.yaml`
2. child buffer：
   - `cmorl_cyborg/outputs/smoke/stage2_deployability_v2/run_5de18faf/solution_buffer.json`

smoke 结果说明：

- `metadata.deployability_gate` 已写入
- `record_count = 9`
- `pareto_count = 4`
- `hard_gate_pass_count = 0`
- `hard_gate_reject_count = 10`
- `metrics_sanity.continue_to_next_phase = true`

这里最重要的不是 smoke 指标本身，而是：

- `stage2_summary.json` 已能记录 `hard_gate_pass_count / hard_gate_reject_count`
- reject reason 已能落盘并区分：
  - `business_regression_guardrail`
  - `cost_regression_guardrail`
  - `final_critical_guardrail`
- v2 训练产物和 diagnostics 链路都能正确消费新的 hard-gate metadata

## Full Seed_0007 Deployability-Aware Run

这一步现在已经执行完了，不再是“待运行”状态。

full `seed_0007` deployability-aware Stage-2 输出：

- child buffer：
  [solution_buffer.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_table_a/ours_stage2_deployability/seed_0007/run_6c10796a/solution_buffer.json:1)
- assignment diagnostics：
  [assignment_diag_summary.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/assignment_diag/ours_stage2_deployability_seed0007/assignment_diag_summary.json:1)
- support shell diagnostics：
  [support_shell_summary.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/support_shell_diag/ours_stage2_deployability_seed0007/support_shell_summary.json:1)
- metrics sanity：
  [metrics_sanity_summary.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/metrics_sanity/ours_stage2_deployability_seed0007/metrics_sanity_summary.json:1)

新 child buffer 的结构状态：

- `record_count = 30`
- `pareto_front size = 16`
- `metadata.deployability_frontiers.near_frontier_policy_ids = 6`
- `metadata.deployability_frontiers.strict_frontier_policy_ids = 0`

assignment diagnostics 结果：

- `candidate_count = 16`
- `strict_candidate_count = 0`
- `near_candidate_count = 0`
- `diagnosis = candidate_supply_problem`

和 replay-only baseline 对比，方向上有轻微改善，但没有机制性翻转：

- `utility_argmax.avg_strict_margin`：`-12.3775 -> -12.3456`
- `strict_lexi.avg_strict_margin`：`-4.1166 -> -4.0917`
- `risk_adjusted_utility.avg_strict_margin`：`-7.4838 -> -7.1657`
- `strict_lexi.avg_mean_violation`：`4.6166 -> 4.5917`
- `strict_lexi.avg_high_disruption_action_rate`：`0.9390 -> 0.9225`

当前最接近 strict 的 candidate 已经从 baseline 的 `stage1_pref_000_ckpt_096` 变成新的 Stage-2 child `stage2_ext_011_obj_1`，但改善仍然很小：

- baseline closest：
  - `strict_margin = -4.1166`
  - `mean_violation = 4.6166`
  - `high_disruption = 0.9390`
  - `final_critical = 0.5250`
- deployability-aware child closest：
  - `strict_margin = -4.0917`
  - `mean_violation = 4.5917`
  - `high_disruption = 0.9225`
  - `final_critical = 0.8000`

这说明 deployability-aware v1 确实开始把 child 往更低 `mean_violation / high_disruption` 的方向拉，但幅度还不足以生成 `near-strict` 或 `strict` candidate。

support shell diagnostics 的 gate 结果更直接：

- `pass_counts_by_shell = {S0: 0, S1: 0, S2: 0, STRICT: 0}`
- `recommended_repair_shell = ""`
- `highest_shell_with_support = None`

因此，这轮 **没有继续运行 repair**。这不是遗漏，而是按既定 gate 规则执行：

- 只有在 `recommended_repair_shell` 非空时，才允许进入 `support_aware_tight_runner --selection-profile repair`
- 当前结果说明，即使换成 deployability-aware Stage-2，candidate support 仍然没有进入任何 non-empty shell

metrics sanity 结果通过：

- `continue_to_next_phase = true`
- `mean_violation.max_abs_diff = 0.0`
- `high_disruption_action_rate.max_abs_diff = 0.0`
- `business_cost_sign.passed = true`

这意味着本轮结论可以直接归因给 candidate support 本身，而不是 cache/recompute 不一致。

## Deployability-Aware v2 Hard Gate

v2 不是另一个 selector 变体，而是对 v1 child acceptance 的进一步收紧：

- 新增 `deployability_gate` 配置块
- `mode = hard`
- 只有 reward-feasible 且满足 deployability hard gate 的 child 才允许进入 best-child 排序
- gate 判断固定优先围绕：
  - `strict_margin_delta`
  - `mean_violation_delta`
  - `high_disruption_delta`
  - `business / cost / final_critical` guardrail

本轮新增 profile：

- [ours_stage2_deployability_v2.yaml](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/configs/paper/ours_stage2_deployability_v2.yaml:1)

full `seed_0007` v2 输出：

- child buffer：
  [solution_buffer.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_table_a/ours_stage2_deployability_v2/seed_0007/run_afd914e3/solution_buffer.json:1)
- assignment diagnostics：
  [assignment_diag_summary.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/assignment_diag/ours_stage2_deployability_v2_seed0007/assignment_diag_summary.json:1)
- support shell diagnostics：
  [support_shell_summary.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/support_shell_diag/ours_stage2_deployability_v2_seed0007/support_shell_summary.json:1)
- metrics sanity：
  [metrics_sanity_summary.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/metrics_sanity/ours_stage2_deployability_v2_seed0007/metrics_sanity_summary.json:1)

结构结果：

- `record_count = 22`
- `pareto_front size = 10`
- `stage2_children = 4`
- `with_acceptance = 4`
- `strict_frontier_policy_ids = []`

hard-gate 运行统计：

- round 0：
  - `hard_gate_pass_count = 2`
  - `hard_gate_reject_count = 10`
- round 1：
  - `hard_gate_pass_count = 3`
  - `hard_gate_reject_count = 7`

这说明 v2 的确显著减少了被保存的 child，hard gate 不是“挂名存在”，而是真的在筛掉 reward-feasible 但 deployability 不够好的更新。

但正式结果并没有比 v1 更好：

- `candidate_count = 10`
- `strict_candidate_count = 0`
- `near_candidate_count = 0`
- `diagnosis = candidate_supply_problem`

和 baseline / v1 对比：

- baseline：
  - `strict_lexi.avg_strict_margin = -4.1166`
  - `strict_lexi.avg_mean_violation = 4.6166`
  - `strict_lexi.avg_high_disruption_action_rate = 0.9390`
- v1：
  - `strict_lexi.avg_strict_margin = -4.0917`
  - `strict_lexi.avg_mean_violation = 4.5917`
  - `strict_lexi.avg_high_disruption_action_rate = 0.9225`
- v2：
  - `strict_lexi.avg_strict_margin = -4.1166`
  - `strict_lexi.avg_mean_violation = 4.6166`
  - `strict_lexi.avg_high_disruption_action_rate = 0.9390`

也就是说：

- v1 带来的那一点轻微改善，在 v2 里没有保住
- v2 把 Pareto candidate set 压得更小了，但没有把“最接近 strict 的点”往前推

最关键的现象是：

- v2 保存下来的 4 个 child，`gate_reason` 都是 `strict_margin_improved`
- 但这些改善都是 **相对各自 parent 的局部改善**
- 它们并没有超过全局最接近 strict 的 baseline candidate `stage1_pref_000_ckpt_096`

换句话说，v2 hard gate 做到了：

- “只保留比 parent 更 deployable 的 child”

但没有做到：

- “把最终 Pareto candidate set 推到比现有全局 best candidate 更接近 strict 的区域”

support shell diagnostics 仍然是全空：

- `pass_counts_by_shell = {S0: 0, S1: 0, S2: 0, STRICT: 0}`
- `recommended_repair_shell = ""`

因此，这轮和 v1 一样，**没有进入 repair**。理由比 v1 更强：

- 不是因为 v2 没起作用
- 而是因为 v2 的作用只体现在 parent-relative filtering 上，还没有把 global candidate support 推进到任何 non-empty shell

metrics sanity 仍然通过：

- `continue_to_next_phase = true`
- `mean_violation.max_abs_diff = 0.0`
- `high_disruption_action_rate.max_abs_diff = 0.0`
- `business_cost_sign.passed = true`

所以 v2 的负结果同样是可信的，不是评估漂移导致的。

## Deployability-Aware v3 Global Target

v3 不再继续加 parent-relative hard gate，而是把 acceptance 改成一个更明确的 global-target 版本：

- 新增 `deployability_target` 配置块
- `mode = global_support`
- 每轮先基于当前 candidate set 构造一个 `stage2_target:S0`
  - `reference_shell = S0`
  - business / cost 用 `S0` lower-bound
  - `mean_violation / high_disruption` 用 `S0` 与当前全局 best strict candidate 的组合 target
- reward-feasible child 不再只看 “相对 parent 是否更好”
  - 现在要显式减少对这个 global target 的 excess，或者提升 shell rank

本轮新增 profile：

- [ours_stage2_deployability_v3.yaml](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/configs/paper/ours_stage2_deployability_v3.yaml:1)

full `seed_0007` v3 输出：

- child buffer：
  [solution_buffer.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_table_a/ours_stage2_deployability_v3/seed_0007/run_1cf494e3/solution_buffer.json:1)
- stage2 summary：
  [stage2_summary.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_table_a/ours_stage2_deployability_v3/seed_0007/run_1cf494e3/stage2_summary.json:1)
- assignment diagnostics：
  [assignment_diag_summary.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/assignment_diag/ours_stage2_deployability_v3_seed0007/assignment_diag_summary.json:1)
- support shell diagnostics：
  [support_shell_summary.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/support_shell_diag/ours_stage2_deployability_v3_seed0007/support_shell_summary.json:1)
- metrics sanity：
  [metrics_sanity_summary.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/metrics_sanity/ours_stage2_deployability_v3_seed0007/metrics_sanity_summary.json:1)

结构结果：

- `record_count = 20`
- `pareto_front size = 11`
- `stage2_children = 2`
- `with_acceptance = 2`

target-driven 运行统计：

- round 0：
  - `target_pass_count = 2`
  - `target_reject_count = 13`
  - `generated = 2`
- round 1：
  - `target_pass_count = 0`
  - `target_reject_count = 8`
  - `generated = 0`

这说明 v3 的 global-target acceptance 不是空挂钩：

- 它确实筛掉了大多数 reward-feasible child
- 也确实保留了 2 个能够降低 global target excess 的 child

但正式结果仍然没有打开 strict route：

- `candidate_count = 11`
- `strict_candidate_count = 0`
- `near_candidate_count = 0`
- `diagnosis = candidate_supply_problem`

最接近 strict 的点仍然是旧的 baseline candidate：

- `policy_id = stage1_pref_000_ckpt_096`
- `strict_margin = -4.1166`
- `mean_violation = 4.6166`
- `high_disruption_action_rate = 0.9390`

也就是说：

- v3 新保存的 2 个 child 并没有超过当前全局 best strict-side candidate
- `strict_lexi.avg_strict_margin` 也没有比 v2 / baseline 更进一步

这两个 v3 child 的性质是：

- `stage2_ext_000_obj_0`
  - `gate_reason = target_score_improved`
  - `strict_margin = -6.5382`
  - `mean_violation = 7.0382`
  - `high_disruption_action_rate = 0.6623`
  - `business = -130.9716`
  - `cost = -17.6260`
- `stage2_ext_001_obj_1`
  - `gate_reason = shell_rank_improved`
  - `strict_margin = -7.4826`
  - `mean_violation = 7.9826`
  - `high_disruption_action_rate = 0.5470`
  - `business = -132.7231`
  - `cost = -15.9870`

这说明 v3 的 target 方向确实开始更明显地偏向：

- 降 `high_disruption`
- 保住更好的 `cost`
- 减少对 `S0`-style support target 的 excess

但它仍然没有同时解决：

- `business`
- `mean_violation`

support shell diagnostics 仍然是全空：

- `pass_counts_by_shell = {S0: 0, S1: 0, S2: 0, STRICT: 0}`
- `recommended_repair_shell = ""`

并且这次的 `S0` 也不是一个明显过严的手工阈值：

- `business_min = -119.7021`
- `cost_min = -17.6157`
- `mean_violation_max = 7.5884`
- `high_disruption_max = 0.6615`

但即使在这组 data-driven shell 下，candidate set 还是没有任何点能 joint-pass `S0`。所以这轮 **仍然没有进入 repair**。

metrics sanity 继续通过：

- `continue_to_next_phase = true`
- `mean_violation.max_abs_diff = 0.0`
- `high_disruption_action_rate.max_abs_diff = 0.0`
- `business_cost_sign.passed = true`

所以 v3 的负结果同样是可信的，不是 cache/recompute 不一致导致的。

## Mechanism Takeaway

replay-only assignment study proves that the tight-feasible failure is a candidate-supply problem rather than a selector artifact.

The current method improves Pareto candidate-set value, but does not push policy support into the strict-deployable region.

现在这条结论可以进一步收紧成：

- diagnostics gate 已经稳定
- deployability-aware Stage-2 upgrade 已经实现，并通过了 focused tests + smoke + full `seed_0007`
- 但 full `seed_0007` 的结果表明：当前 v1 只带来了轻微 deployability improvement，没有把 candidate support 推进到任何 non-empty deployable shell
- hard-gate v2 进一步证明：即使只保留 parent-relative deployability-improving child，也仍不足以把全局 Pareto candidate set 推进到 strict-deployable region
- global-target v3 进一步证明：即使把 acceptance 改成减少绝对 deployability excess 的方向，当前 `ours_stage2` 也仍未把 candidate support 推进到任何 non-empty shell
- 因而，这轮不支持“继续靠 repair 或 selector 微调就能打通 strict route”的判断

## Immediate Next Action

这条执行线已经跑完，当前最合理的下一步不是强行 repair，而是收束为：

1. 保留这次 full run 作为 deployability-aware v1 的正式结果
2. 保留这次 full run 作为 hard-gate v2 的正式结果
3. 保留这次 full run 作为 global-target v3 的正式结果
4. 明确记录：v1 / v2 / v3 都没有触发 repair，因为 `recommended_repair_shell` 一直为空
5. 把结论升级为：
   - `ours_stage2` candidate support 仍未被推入 deployable shell
   - 下一步若还继续做方法实验，就必须进入更深的 Stage-2 training objective redesign，而不是再调 selector、继续做 repair，或继续做 `final_critical` 单轴补丁

## Paper Sync

2026-04-16 已将上述已完成结果同步到 [paper/main.tex](/home/waylandlee/CMORL2/Cyber-CMORL/paper/main.tex:1) 的相关表述中，重点包括：

- abstract 不再把结果写成“strict operational constraints 下已取得更强可部署结果”，而改成“common constrained protocol 下 competitive，并明确 strict-feasible 仍是 candidate-supply bottleneck”
- Figure D / Tight-Feasible 段落补上机制解释：
  - replay-only diagnostics 支持 `candidate_supply_problem`
  - tight-feasible failure 不是 selector artifact
- Discussion / Limitations / Conclusion 全部与当前证据对齐：
  - set-value gain 成立
  - strict-deployable support 仍未打通
  - 下一步需要更上游的 Stage-2 objective redesign

## Interpretation Notes

### 1. Strict failure does not mean the main deployment story fails

当前必须把两条 deployment 口径分开：

- `common constrained protocol`
  - 这是 main-paper Table B 的正式 deployment 口径
  - 在这条线上，`ours_stage2` 仍然是 `competitive constrained deployment behavior`
- `tight / strict-feasible protocol`
  - 这是 Figure D 的 stress-test 口径
  - 在这条线上，`ours_stage2` 当前仍然没有 strict 或 near-strict candidate

因此，“现在部署不出来”如果指的是 `STRICT`，不能直接改写成“整个方法部署不出来”。更准确的解释是：

- main-paper 的 common deployment 仍然成立
- 失败的是 tight/strict 这条 stress line

同时，现有 evidence 也不支持把 strict failure 简单解释成“threshold 只是设得太严”。原因是：

- replay diagnostics 一直是 `strict_candidate_count = 0` 且 `near_candidate_count = 0`
- v3 的 support-shell diagnostics 里，连 data-driven 的 `S0` 都还是空的：
  - `pass_counts_by_shell = {S0: 0, S1: 0, S2: 0, STRICT: 0}`
  - `recommended_repair_shell = ""`

这意味着：

- `STRICT` 的确是更严的 stress case
- 但当前失败不只是 “strict threshold 过硬”
- 更核心的问题仍然是 `candidate support` 没有推进到 strict-deployable region 附近

如果后续要放宽 deployment 口径，只能作为一个新的、明确命名的 tier 来报告，例如：

- `common constrained`
- `moderate deployable`
- `strict deployable`

不能把放宽后的口径重新命名成现在的 `STRICT`，否则会破坏论文解释的一致性。

### 2. Why `no_constraint_stage2` cannot replace the deployment-aware method

`no_constraint_stage2` 在若干 deployment metric 上更强，这点需要正面承认。例如在当前 Table B 口径下，它仍然有更强的：

- `security_return`
- `feasible_rate`
- `mean_violation`

但它不能被当成与 `ours_stage2` 同语义的正式替代，原因是它的角色是：

- `unconstrained ablation`
- 不是 another deployment-aware constrained method

也就是说，`no_constraint_stage2` 回答的问题是：

- “如果去掉 Stage-2 的 constraint-aware expansion，会发生什么？”

而不是：

- “在同样 deployment-aware constrained 语义下，哪个正式方法更好？”

因此，当前最稳的论文口径是：

- 可以把 `no_constraint_stage2` 保留在 deployment table 和 ablation 里
- 但不把它当作 main deployment story 的唯一对手
- main deployment narrative 仍然以 `weighted_sum`、`stage1_only`、`single_objective`、`lagrangian_ppo` 为主来支持 `competitive deployment quality`

更准确地说：

- `no_constraint_stage2` 说明 constraint-awareness 有代价，也有作用
- 它是因果解释用的 matched ablation
- 它不应被直接读成“deployment-aware constrained method 的更优正式替身”
