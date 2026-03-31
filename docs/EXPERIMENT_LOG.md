# Experiment Log

## 记录规范

每次正式记录一条实验时，建议至少填写以下字段：

- 日期
- 实验 ID
- 阶段
- 目标
- 配置文件
- 输入 buffer
- 输出目录
- 关键指标
- 现象
- 结论
- 下一步

结构化事实优先来自：

- `solution_buffer.json`
- `stage1_summary.json`
- `stage2_summary.json`
- `metrics.json`

本文件负责记录“如何理解这些结果”，而不是替代这些产物。

## 模板

```text
日期：
实验 ID：
阶段：
目标：
配置文件：
输入 buffer：
输出目录：
关键指标：
现象：
结论：
下一步：
```

## 已记录实验

### 2026-03-30 / P1-Stage1-Smoke

- 实验 ID：`run_29deaae7`
- 阶段：Stage-1
- 目标：验证新的 preference 初始化策略、summary 产物和 buffer schema 是否能正常写出
- 配置文件：[cmorl_minicage/configs/stage1.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/configs/stage1.yaml)
- 输出目录：[run_29deaae7](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/p1_stage1_check/run_29deaae7)
- 关键指标：
  - `schema_version = 0.3.0`
  - `preferences count = 6`
  - `stage1_summary entries = 6`
  - `HV = 1681.15`
  - `EU = -135.91`
  - `Pareto Count = 9`
- 现象：
  - 成功写出 `stage1_summary.json`
  - record notes 中包含 `scalarized_utility`、`trainer_stats`、`pareto_size_after_save`
  - 最终 Pareto set 已具备可解释的 trade-off 结构
- 结论：
  - Stage-1 初始化链路和结构化输出链路已经稳定
  - 该 run 可以作为后续 Stage-2 调参与对照评估的稳定输入 buffer
- 下一步：
  - 继续用该 buffer 探索 Stage-2 的可行扩展区间

### 2026-03-30 / P1-Stage2-Smoke

- 实验 ID：`run_81cbc3c2`
- 阶段：Stage-2 + Evaluation
- 目标：验证 round summary、泛化 HV 和 assignment summary 是否正常写出
- 配置文件：
  - [cmorl_minicage/configs/stage2.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/configs/stage2.yaml)
  - [cmorl_minicage/configs/evaluate.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/configs/evaluate.yaml)
- 输入 buffer：[solution_buffer.json](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/p1_stage1_check/run_29deaae7/solution_buffer.json)
- 输出目录：[run_81cbc3c2](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/p1_stage2_check/run_81cbc3c2)
- 关键指标：
  - `hypervolume_method = exact_inclusion_exclusion`
  - `unique_assigned_policies = 4`
  - 相对 Stage-1 没有新增有效 Pareto 扩展
- 现象：
  - 在当前较严格的 feasibility gate 下，没有新增 Stage-2 policy
  - `stage2_summary.json` 和 `metrics_p1.json` 均成功写出
- 结论：
  - 约束门控与评估体系已经工作
  - 但当前 Stage-2 超参明显过于严格，无法产生有效 front extension
- 下一步：
  - 使用更宽松的 ablation 配置探索 Stage-2 可行区间

### 2026-03-31 / P2-Stage2-Ablation-Sweep

- 实验 ID：
  - `run_a29b1cf0` conservative
  - `run_3e8fb3a0` balanced
  - `run_5c3e7177` relaxed
  - `run_89adf296` beta_1005
  - `run_ec04a030` beta_1020
  - `run_68b8a4b2` steps_1024
  - `run_28007b1b` steps_1536
  - `run_2e112668` tol_025
  - `run_8e69e7c1` tol_075
- 阶段：Stage-2 + Evaluation
- 目标：围绕 Stage-2 约束强度与局部搜索步长，找到能产生有效 Pareto front extension 的超参数区间
- 配置文件：
  - [cmorl_minicage/configs/ablation/stage2_conservative.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/configs/ablation/stage2_conservative.yaml)
  - [cmorl_minicage/configs/ablation/stage2_balanced.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/configs/ablation/stage2_balanced.yaml)
  - [cmorl_minicage/configs/ablation/stage2_relaxed.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/configs/ablation/stage2_relaxed.yaml)
  - [cmorl_minicage/configs/ablation/local_search/stage2_beta_1005.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/configs/ablation/local_search/stage2_beta_1005.yaml)
  - [cmorl_minicage/configs/ablation/local_search/stage2_beta_1020.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/configs/ablation/local_search/stage2_beta_1020.yaml)
  - [cmorl_minicage/configs/ablation/local_search/stage2_steps_1024.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/configs/ablation/local_search/stage2_steps_1024.yaml)
  - [cmorl_minicage/configs/ablation/local_search/stage2_steps_1536.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/configs/ablation/local_search/stage2_steps_1536.yaml)
  - [cmorl_minicage/configs/ablation/local_search/stage2_tol_025.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/configs/ablation/local_search/stage2_tol_025.yaml)
  - [cmorl_minicage/configs/ablation/local_search/stage2_tol_075.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/configs/ablation/local_search/stage2_tol_075.yaml)
- 输入 buffer：[solution_buffer.json](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/p1_stage1_check/run_29deaae7/solution_buffer.json)
- 输出目录：
  - [stage2_conservative/run_a29b1cf0](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/ablation/stage2_conservative/run_a29b1cf0)
  - [stage2_balanced/run_3e8fb3a0](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/ablation/stage2_balanced/run_3e8fb3a0)
  - [stage2_relaxed/run_5c3e7177](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/ablation/stage2_relaxed/run_5c3e7177)
  - [stage2_beta_1005/run_89adf296](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/ablation/local_search/stage2_beta_1005/run_89adf296)
  - [stage2_beta_1020/run_ec04a030](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/ablation/local_search/stage2_beta_1020/run_ec04a030)
  - [stage2_steps_1024/run_68b8a4b2](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/ablation/local_search/stage2_steps_1024/run_68b8a4b2)
  - [stage2_steps_1536/run_28007b1b](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/ablation/local_search/stage2_steps_1536/run_28007b1b)
  - [stage2_tol_025/run_2e112668](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/ablation/local_search/stage2_tol_025/run_2e112668)
  - [stage2_tol_075/run_8e69e7c1](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/ablation/local_search/stage2_tol_075/run_8e69e7c1)
- 关键指标摘要：

| 配置 | HV | EU | SP | Pareto Count | Coverage | Unique Assigned |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| conservative | 1804.88 | -125.32 | 13362.87 | 6 | 0.50 | 3 |
| balanced | 2518.39 | -135.87 | 3435.11 | 11 | 0.36 | 4 |
| relaxed | 2507.34 | -135.88 | 2383.09 | 12 | 0.42 | 5 |
| beta_1005 | 2873.94 | -125.33 | 6531.60 | 9 | 0.44 | 4 |
| beta_1020 | 1804.88 | -125.32 | 13362.87 | 6 | 0.50 | 3 |
| steps_1024 | 2570.19 | -135.84 | 4916.36 | 9 | 0.56 | 5 |
| steps_1536 | 2757.88 | -103.23 | 10554.48 | 7 | 0.29 | 2 |
| tol_025 | 2873.94 | -125.33 | 6531.60 | 9 | 0.44 | 4 |
| tol_075 | 1804.88 | -125.32 | 13362.87 | 6 | 0.50 | 3 |

- 现象：
  - `beta_1005` 和 `tol_025` 得到完全一致的最优级 `HV`。
  - `steps_1536` 的 `EU` 最高，但 `coverage_ratio` 和 `unique_assigned_policies` 最低。
  - `relaxed` 和 `balanced` 生成更多 Pareto 点，但 `EU` 几乎没有提升。
  - `beta_1020`、`tol_075` 和 `conservative` 基本回到严格门控区，表现几乎重合。
- 结论：
  - 当前最佳“整体 front 扩展”配置是 `beta_1005` 或等效区间的 `tol_025`。
  - 当前最佳“高 utility 专家型”配置是 `steps_1536`，但它并不是最均衡的 Pareto front 配置。
  - 单纯放宽约束并不会自动带来更好的 HV / EU；`relaxed` 更像“堆点”，而不是“做出更有用的 front”。
- 下一步：
  - 围绕 `beta_1005 / tol_025` 继续做更细粒度局部搜索。
  - 分析 `steps_1536` 是否适合作为专家型补充分支，而非默认配置。

### 2026-03-31 / P2-Visualization-Baseline

- 实验 ID：`run_4a7029b6` 可视化补充
- 阶段：Visualization / Legacy Run Interpretation
- 目标：为旧版 `config_stage2` run 生成 Pareto 图，作为机制验证和文档解释样例
- 输入目录：[run_4a7029b6](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/config_stage2/run_4a7029b6)
- 输出图：
  - [pareto_projections.png](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/config_stage2/run_4a7029b6/plots/pareto_projections.png)
  - [pareto_3d_scatter.png](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/config_stage2/run_4a7029b6/plots/pareto_3d_scatter.png)
  - [stage1_vs_stage2_overlay.png](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/config_stage2/run_4a7029b6/plots/stage1_vs_stage2_overlay.png)
- 现象：
  - 该 run 最终只有 3 个 Pareto 点。
  - 第二目标恒为 `0.0`，说明这条 run 主要只在两个目标间发生 trade-off。
- 结论：
  - 该旧 run 更适合作为“Stage-2 机制已打通”的示意样例。
  - 不适合作为当前最强实验结果的代表。
- 下一步：
  - 以 `beta_1005` 和 `steps_1536` 的图为主进行结果解释和汇报。

### 2026-03-31 / P2-Visualization-Ablation

- 实验 ID：`run_89adf296` + 全 ablation 总览图
- 阶段：Visualization / Result Interpretation
- 目标：把当前最重要的一组 Stage-2 结果转成可直接解释的图形产物
- 输入目录：
  - [stage2_beta_1005/run_89adf296](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/ablation/local_search/stage2_beta_1005/run_89adf296)
  - [cmorl_minicage/outputs](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs)
- 输出图：
  - [beta_1005/pareto_projections.png](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/ablation/local_search/stage2_beta_1005/run_89adf296/plots/pareto_projections.png)
  - [beta_1005/pareto_3d_scatter.png](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/ablation/local_search/stage2_beta_1005/run_89adf296/plots/pareto_3d_scatter.png)
  - [beta_1005/stage1_vs_stage2_overlay.png](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/ablation/local_search/stage2_beta_1005/run_89adf296/plots/stage1_vs_stage2_overlay.png)
  - [beta_1005/assignment_counts.png](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/ablation/local_search/stage2_beta_1005/run_89adf296/plots/assignment_counts.png)
  - [beta_1005/stage2_rounds.png](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/ablation/local_search/stage2_beta_1005/run_89adf296/plots/stage2_rounds.png)
  - [ablation_triplet.png](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/plots/ablation_triplet.png)
  - [paper_style_ablation_summary.png](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/plots/paper_style_ablation_summary.png)
- 关键指标：
  - `beta_1005`：
    - `HV = 2873.94`
    - `EU = -125.33`
    - `Pareto Count = 9`
    - `max assignment count = 55`
  - `steps_1536`：
    - `EU = -103.23`
    - `coverage_ratio = 0.286`
    - `unique_assigned_policies = 2`
  - `relaxed`：
    - `Pareto Count = 12`
    - `EU ≈ Stage-1 baseline`
- 现象：
  - `beta_1005` 的 3D front 明显向多方向展开。
  - `assignment_counts` 显示 `stage2_ext_008_obj_1` 主导了大多数 evaluation preference。
  - `steps_1536` 尽管 EU 很高，但 front 实际由极少数 policy 主导。
  - 总览图清楚显示“点数多”和“utility 更高”不是同一件事。
- 结论：
  - 这组图已经足够支撑当前 Stage-2 结论的解释工作。
  - `beta_1005` 是最适合作为当前主结果展示的配置。
- 下一步：
  - 把可视化说明进一步沉淀到 README 或专门的分析文档中。
