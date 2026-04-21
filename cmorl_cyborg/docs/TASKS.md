# Tasks

## 2026-04-20 Semantic Safety Snapshot

### 当前主方法

- `Done` 当前语义安全主线已经从旧 `Critical-First / V2.1 / V2.2 / V2.3` 收敛到 `V2.4 pre-critical containment`
- `Done` 方法名固定为 `ours_stage2_fair_critical_safe_v2_4_4obj`
- `Done` `3-seed = 0007 / 0011 / 0019` 已全部完成并通过 `pilot_passed`
- `Done` `seed_0011` 的 verifier 已可解释：
  - `containment_hypothesis_status = evaluable`
  - `containment_hypothesis_triggered_vs_v2_3 = true`

### 当前结论

- `Done` 三颗 seed 的 selected replay20 semantic audit 共同结果：
  - `ever_critical_breach_rate = 0.0`
  - `persistent_critical_breach_rate = 0.0`
  - `mean_critical_dwell_steps = 0.0`
  - `high_confidence_env_run_rate = 0.0`
- `Done` pre-critical containment 机制已稳定触发：
  - `precritical_action_family_step_rates.restore = 1.0`
  - `precritical_action_family_step_rates.decoy = 0.0`
  - `precritical_compromised_target_focus_step_rate = 1.0`
- `In Progress` 当前未解决项已经从 `critical breach` 转成 `near-miss margin`：
  - `Tier 1 Near-Miss = 1.0`
  - `Tier 0 Safe` 仍未转正

### 导表状态

- `Done` 已打通独立 `V2.4` 导表支线：
  - `cmorl_cyborg/configs/paper/compare_suite_v2_4_row.yaml`
  - `cmorl_cyborg/configs/paper/export_tables_v2_4_row.yaml`
  - `cmorl_cyborg/outputs/paper_table_v2_4/`
- `Done` 已生成 `V2.4` 专属 `table_a / table_b` row
- `In Progress` `table_b` 当前可作为主表候选行
- `In Progress` `table_a` 当前只适合作为独立 semantic-safety set-quality row，因为它属于 `4-objective` 口径，不能直接替换当前旧 `3-objective` 主表 A

### 当前下一步

- `In Progress` 决定 `V2.4 table_b` 是否进入论文主表
- `Planned` 若论文继续保留旧 `3-objective Table A`，则把 `V2.4 table_a` 放补充表
- `Planned` 若要把 `V2.4` 推入主表 A，需要先重定义 paper-level 的 `4-objective set-quality` 口径

## Historical Backlog

- 完成 `Critical-First V1` 的 `seed_0011` pilot，并只在通过后扩到 `3-seed`
- 若 V1 仍无法把 `ever_critical_breach_rate` 从 `1.0` 拉下来，直接进入四维 `V2`
- 决定是否仍需要额外单独补 `no_constraint_stage2_matched` 主文表
- 决定是否进入 `5-seed formal`
- 把现有 `3-seed` 与 semantic repair 结果整理成论文可直接使用的结果总结
- 统一 coverage 公平比较在论文中的表述边界

## Historical In Progress

- 论文写作前的实验公平性梳理
- 表 B 讨论口径收束
- 文档与 README 的结果口径统一
- `Critical-First V1` `seed_0011` pilot 训练与收尾评估

## Historical Done

- 固定正式 `security / business / cost` 口径
- 打通 `Stage-1 -> Stage-2 -> evaluate -> evaluate_constraints -> compare_suite -> export_tables`
- 建立 dev / holdout 调参闭环
- 生成正式 `3-seed` 主表 A / B
- 生成 `fair_compare_eval` 的 tight / loose 比较图
- 生成 `coverage_combo_fair` 与 `coverage_more_parents_fair` 聚合结果
- 为 week-2 formal runner 增加：
  - [status.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_week2_runner/status.json)
  - [runner_summary.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_week2_runner/runner_summary.json)
  - [formal_run_manifest.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_week2_runner/formal_run_manifest.json)
- 修复正式 `stage2_main`，让 Stage-2 不再空转
- 试过但未采用的表 B 改法：
  - semantic parent selection
  - semantic soft penalty
  - early termination 放松
  - very small B-tight 微调
  - semantic-aware / semantic-balanced 主选点替换
- 旧 semantic repair `phase1/2/3` 已完成并形成稳定结论：
  - selection-only `0/3` helpful seeds
  - `phase2 gate` 未通过
  - `phase3 target` 仍未把 `ever_critical_breach_rate` 拉离 `1.0`
- 已决定停止旧 `phase4` 与旧 gate/target 微调，转入 `Critical-First V1`
