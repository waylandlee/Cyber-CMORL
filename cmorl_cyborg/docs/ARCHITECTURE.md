# Architecture

## 2026-04-08 状态说明

本文件描述的是 `cmorl_cyborg` 当前正式线的代码结构。写论文时，这套结构应承担“正式实验平台”的角色；`cmorl_minicage` 则主要承担开发验证和 supplementary 角色。

## 顶层模块

- [env.py](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/env.py)
  正式 `CybORG` 环境包装，输出 `obs / reward_vec / semantic_info`
- [reward.py](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/reward.py)
  定义 `security / business / cost`
- [semantics.py](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/semantics.py)
  定义 cyber semantic 指标与状态快照
- [scenario_profiles.py](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/scenario_profiles.py)
  读取 `Scenario2.yaml` 这类 profile
- [config.py](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/config.py)
  所有训练、评估、主表配置 dataclass

## 训练链路

- [train_stage1.py](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/train_stage1.py)
  复用 `cmorl_minicage.train_stage1`，但环境替换成 `CybORGMORLEnv`
- [train_stage2.py](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/train_stage2.py)
  复用 `cmorl_minicage.train_stage2`，环境替换成 `CybORGMORLEnv`
- [baselines.py](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/baselines.py)
  `weighted_sum`、`stage1_only`、`single_objective` 等 baseline 入口
- [train_pref_conditioned_ppo.py](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/train_pref_conditioned_ppo.py)
  preference-conditioned PPO 入口
- [train_lagrangian_ppo.py](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/train_lagrangian_ppo.py)
  Lagrangian PPO 入口
- [train_pcn.py](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/train_pcn.py)
  PCN 入口

## 评估链路

- [evaluate.py](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/evaluate.py)
  buffer 方法主评估
- [evaluate_conditioned.py](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/evaluate_conditioned.py)
  conditioned 方法先评估 preference 网格，再构造点集
- [evaluate_constraints.py](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/evaluate_constraints.py)
  表 B 约束评估
- [compare_suite.py](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/compare_suite.py)
  shared reference 下比较多方法 A 表指标

## 导表与出图

- [main_table_a.py](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/main_table_a.py)
  生成主表 A 输入与摘要
- [main_table_b.py](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/main_table_b.py)
  生成主表 B 输入与摘要
- [export_tables.py](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/export_tables.py)
  导出 CSV / TEX
- [paper_plots.py](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/paper_plots.py)
  绘制正式图

## 正式运行编排

- [week2_formal_runner.py](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/week2_formal_runner.py)
  组织 `3-seed` 正式运行
- 输出状态：
  - [status.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_week2_runner/status.json)
  - [runner_summary.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_week2_runner/runner_summary.json)
  - [formal_run_manifest.json](/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_week2_runner/formal_run_manifest.json)

## 数据流

1. `train_stage1` 产出：
   - `solution_buffer.json`
   - `stage1_summary.json`
   - `pareto_front_stage1.json`

2. `train_stage2` 读取 `stage1_buffer`，产出：
   - `solution_buffer.json`
   - `stage2_summary.json`
   - `method_diagnostics.json`

3. `evaluate / evaluate_conditioned / evaluate_constraints`
   分别生成：
   - `metrics.json`
   - `evaluated_points.json`
   - `constraint_metrics.json`

4. `main_table_a / main_table_b`
   汇总为：
   - `table_a_summary.json`
   - `table_b_summary.json`

5. `export_tables / paper_plots`
   产出：
   - `table_a_metrics.csv/.tex`
   - `table_b_constraints.csv/.tex`
   - 主表 PNG
