# CybORG 第二周收尾说明

日期：`2026-04-03`

本文件用于承接 [CYBORG_WEEK2_CHECKLIST.md](/home/waylandlee/CMORL2/Cyber-CMORL/docs/CYBORG_WEEK2_CHECKLIST.md)，给出第二周在正式 `CybORG` 线上的收尾状态、最终运行命令与 `5-seed formal` 准入判断口径。

## 2026-04-08 补充状态

相对本文件最初写下时的“待补齐”状态，当前已经发生的变化是：

1. `cmorl_cyborg` 的 `3-seed` 主表 B 聚合已经完成。
2. `fair_compare_eval` 的 tight / loose 图和 coverage 聚合已经生成。
3. 当前更重要的问题已经不是“能不能跑完 3-seed”，而是“怎么解释 coverage 公平比较结果，不写过强 claim”。

因此，下面正文里凡是“3-seed 尚未补齐”“暂不进入分析”的部分，都应该按这个补充状态理解。

## 冻结前提

- `实验层` 继续使用 `Scenario2`
- `scenario_profile` 默认跟随 `Scenario2`
- 第二周固定 `3-seed = 7 / 11 / 19`
- 第三周候选 `5-seed = 7 / 11 / 19 / 23 / 29`
- 不再混用 `preformal` 与 `dev_tuning` 结果作为正式主表输入

## 第二周已补齐的链路

当前 `cmorl_cyborg` 已补齐以下正式导表入口：

- 主表 A：
  - [compare_suite_main.yaml](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/configs/paper/compare_suite_main.yaml)
  - [main_table_a.py](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/main_table_a.py)
- 主表 B：
  - [table_b_suite_main.yaml](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/configs/paper/table_b_suite_main.yaml)
  - [main_table_b.py](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/main_table_b.py)
  - [evaluate_constraints.py](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/evaluate_constraints.py)
- 总导表：
  - [export_tables_main.yaml](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/configs/paper/export_tables_main.yaml)
  - [export_tables.py](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/export_tables.py)

这些入口现在都只面向第二周正式 `Scenario2` 协议，不再指向 `week1` 的草稿产物。

## 最终运行命令

以下命令是进入 `5-seed formal` 前建议固定下来的第二周正式命令模板。

### 1. 先补齐 `3-seed` 训练产物

注意：所有正式运行都建议把 `--output-dir` 指到稳定的 `seed_xxxx` 根目录下，避免后续主表脚本无法唯一匹配 `run_*`。

```bash
conda run -n cc4 python -m cmorl_cyborg.train_stage1 \
  --config cmorl_cyborg/configs/paper/stage1_only_main.yaml \
  --output-dir cmorl_cyborg/outputs/paper_appendix/stage1_only/seed_0007

conda run -n cc4 python -m cmorl_cyborg.train_stage2 \
  --config cmorl_cyborg/configs/paper/stage2_main.yaml \
  --stage1-buffer cmorl_cyborg/outputs/paper_appendix/stage1_only/seed_0007/run_<id>/solution_buffer.json \
  --output-dir cmorl_cyborg/outputs/paper_table_a/ours_stage2/seed_0007

conda run -n cc4 python -m cmorl_cyborg.baselines weighted-sum \
  --stage1-config cmorl_cyborg/configs/paper/weighted_sum_main.yaml \
  --output-dir cmorl_cyborg/outputs/paper_table_a/weighted_sum/seed_0007

conda run -n cc4 python -m cmorl_cyborg.train_pref_conditioned_ppo \
  --config cmorl_cyborg/configs/paper/pref_cond_ppo.yaml \
  --output-dir cmorl_cyborg/outputs/paper_table_a/preference_conditioned_ppo/seed_0007

conda run -n cc4 python -m cmorl_cyborg.train_pcn \
  --config cmorl_cyborg/configs/paper/pcn.yaml \
  --output-dir cmorl_cyborg/outputs/paper_appendix/pcn/seed_0007

conda run -n cc4 python -m cmorl_cyborg.train_stage2 \
  --config cmorl_cyborg/configs/paper/stage2_no_constraint_main.yaml \
  --stage1-buffer cmorl_cyborg/outputs/paper_appendix/stage1_only/seed_0007/run_<id>/solution_buffer.json \
  --output-dir cmorl_cyborg/outputs/paper_appendix/no_constraint_stage2/seed_0007

conda run -n cc4 python -m cmorl_cyborg.baselines single-objective \
  --stage1-config cmorl_cyborg/configs/paper/single_objective_main.yaml \
  --output-dir cmorl_cyborg/outputs/paper_table_b/single_objective/seed_0007

conda run -n cc4 python -m cmorl_cyborg.train_lagrangian_ppo \
  --config cmorl_cyborg/configs/paper/lagrangian_ppo.yaml \
  --output-dir cmorl_cyborg/outputs/paper_table_b/lagrangian_ppo/seed_0007
```

对 `seed_0011` 与 `seed_0019` 重复同样命令，并把 config 中的 `seed` 与 `env.seed` 一并改成对应值。

### 2. 生成正式主表 A

```bash
conda run -n cc4 python -m cmorl_cyborg.main_table_a \
  --config cmorl_cyborg/configs/paper/compare_suite_main.yaml
```

### 3. 生成正式主表 B

```bash
conda run -n cc4 python -m cmorl_cyborg.main_table_b \
  --config cmorl_cyborg/configs/paper/table_b_suite_main.yaml
```

### 4. 统一导出 CSV / TEX

```bash
conda run -n cc4 python -m cmorl_cyborg.export_tables \
  --config cmorl_cyborg/configs/paper/export_tables_main.yaml
```

## 当前准入判断

截至 `2026-04-08`，第二周相关链路应更新为以下判断：

1. `shared thresholds` 已在当前 `paper_table_b` 与 `fair_compare_eval` 中实际使用，可视为本轮 `3-seed` 结果口径的一部分。
2. 主表 B 的 `3-seed` 聚合已经产出，当前不再卡在“跑完结果”这一步。
3. 当前仍不建议直接把文档切成“5-seed formal 已完成”的口径，因为仓库内最新强结论仍主要来自 `3-seed`。
4. 进入下一阶段前，应优先完成结果解释与文档统一，而不是继续沿用第二周的计划态表述。

## `5-seed formal` 暂定方法名单

若第二周 `3-seed` 完整跑齐后趋势稳定，建议先按以下名单进入 `5-seed formal`：

- 主表 A：
  - `ours_stage2`
  - `weighted_sum`
  - `preference_conditioned_ppo`
  - `pcn`
- 主表 B：
  - `ours_stage2`
  - `lagrangian_ppo`
  - `weighted_sum`
  - `stage1_only`
  - `no_constraint_stage2`
  - `single_objective`

如果 `PCN` 在正式 `3-seed` 下仍不稳定，建议降级到 appendix。

## 第二周结束时的更新结论

现在更准确的收尾总结应是：

- 协议、目录与导表链已经冻结。
- `3-seed` 主表 B 与公平比较产物已经形成。
- 原始 `ours_stage2` 仍是正式主线参照，但 coverage 公平比较没有形成“全面更优”的新结论。
- 下一步重点应是收紧叙事和同步文档，而不是继续把第二周写成“结果尚未出来”。
