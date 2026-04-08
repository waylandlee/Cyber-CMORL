# CybORG 第二周冻结协议

## 状态说明

截至 `2026-04-08`，本文件应被视为“历史冻结协议”，不是当前待办清单。

当前已确认的事实是：

- 第二周约定的 `3-seed = 7 / 11 / 19` 已成为当前 `cmorl_cyborg` 文档默认口径。
- `paper_table_b` 与 `fair_compare_eval` 当前都使用同一组 shared thresholds：
  - `d_business = -148.14463806152344`
  - `d_cost = -24.94145965576172`
- 后续文档若出现“即将补齐 3-seed”的说法，应以本轮结果为准做更新，不再按计划态理解。

本文件用于冻结第二周正式 `CybORG` 实验协议。第二周期间不再改 reward / semantics 口径，`实验层` 继续使用 `Scenario2`，但实现层通过 `scenario-profile` 驱动。

## 冻结范围

- 不再改 [cmorl_cyborg/reward.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/reward.py) 与 [cmorl_cyborg/semantics.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/semantics.py) 的工作定义。
- 不再改第二周 seed 协议。
- 不再混用 `preformal` 与 `dev_tuning` 输出路径作为正式横评输入。

## 场景协议

- `scenario_name`: `Scenario2`
- `scenario_profile`: 默认跟随 `Scenario2`
- 说明：
  当前实验结论在第二周仍然限定于 `Scenario2`，但配置和实现已经允许后续切换到别的 scenario-profile。

## 冻结 Seed

- `dev`: `7`
- `holdout`: `11`
- `3-seed`: `7, 11, 19`
- `5-seed` 预留候选：`7, 11, 19, 23, 29`

## 冻结输出根目录

- `cmorl_cyborg/outputs/paper_table_a/`
- `cmorl_cyborg/outputs/paper_table_b/`
- `cmorl_cyborg/outputs/paper_appendix/`

## 第二周横评方法名单

- `ours_stage2`
- `stage1_only`
- `no_constraint_stage2`
- `weighted_sum`
- `single_objective`
- `lagrangian_ppo`
- `preference_conditioned_ppo`
- `pcn`

## 方法到配置与输出根目录映射

- `ours_stage2`
  - 配置：[stage2_main.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/configs/paper/stage2_main.yaml)
  - 输出根目录：`cmorl_cyborg/outputs/paper_table_a/ours_stage2`
- `stage1_only`
  - 配置：[stage1_only_main.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/configs/paper/stage1_only_main.yaml)
  - 输出根目录：`cmorl_cyborg/outputs/paper_appendix/stage1_only`
- `no_constraint_stage2`
  - 配置：[stage2_no_constraint_main.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/configs/paper/stage2_no_constraint_main.yaml)
  - 输出根目录：`cmorl_cyborg/outputs/paper_appendix/no_constraint_stage2`
- `weighted_sum`
  - 配置：[weighted_sum_main.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/configs/paper/weighted_sum_main.yaml)
  - 输出根目录：`cmorl_cyborg/outputs/paper_table_a/weighted_sum`
- `single_objective`
  - 配置：[single_objective_main.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/configs/paper/single_objective_main.yaml)
  - 输出根目录：`cmorl_cyborg/outputs/paper_table_b/single_objective`
- `lagrangian_ppo`
  - 配置：[lagrangian_ppo.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/configs/paper/lagrangian_ppo.yaml)
  - 输出根目录：`cmorl_cyborg/outputs/paper_table_b/lagrangian_ppo`
- `preference_conditioned_ppo`
  - 配置：[pref_cond_ppo.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/configs/paper/pref_cond_ppo.yaml)
  - 输出根目录：`cmorl_cyborg/outputs/paper_table_a/preference_conditioned_ppo`
- `pcn`
  - 配置：[pcn.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/configs/paper/pcn.yaml)
  - 输出根目录：`cmorl_cyborg/outputs/paper_appendix/pcn`

## 第二周 Compare / Export 协议

- 主表 A 协议配置：
  [compare_suite_main.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/configs/paper/compare_suite_main.yaml)
- 主表 A 导表入口：
  [main_table_a.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/main_table_a.py)
- 主表 B 协议配置：
  [table_b_suite_main.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/configs/paper/table_b_suite_main.yaml)
- 主表 B 导表入口：
  [main_table_b.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/main_table_b.py)
- 导表协议配置：
  [export_tables_main.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/configs/paper/export_tables_main.yaml)

这两个文件从现在开始只表达第二周正式环境协议，不再继续指向 week1 的 `preformal` 或 `dev_tuning` 具体产物。
