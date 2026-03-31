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

## 口径变更说明

从 2026-03-31 开始，`cmorl_minicage` 的环境奖励口径切换为：

- `security`
- `business`
- `cost`

并采用方案 A：

- 不再要求三目标逐项求和等于 MiniCAGE 原始标量 reward
- `reward_vec.sum()` 作为 MORL 内部总回报
- MiniCAGE 原始标量 reward 仅作为 `mini_cage_scalar_reward` 保留在 `info["reward_terms"]`

因此：

- 本文件中 2026-03-31 之前的实验结果，属于旧版目标定义
- 切换之后的新实验，需要作为新口径单独记录
- 新旧两批结果不能直接做严格数值横比

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

### 2026-03-31 / P3-NewObjectives-Stage1-Semantic

- 实验 ID：`run_b01c7843`
- 阶段：Stage-1 + Evaluation
- 目标：在新的 `security / business / cost` 定义下重新建立 Stage-1 baseline，并验证 8 个语义指标能稳定输出
- 配置文件：
  - [cmorl_minicage/configs/stage1.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/configs/stage1.yaml)
  - [cmorl_minicage/configs/evaluate.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/configs/evaluate.yaml)
- 输出目录：[run_b01c7843](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/p2_stage1_semantic_check/run_b01c7843)
- 关键指标：
  - `HV = 320.98`
  - `EU = -53.89`
  - `Pareto Count = 2`
  - `final_compromised_hosts = 2.25`
  - `final_critical_compromised_hosts = 0.42`
  - `critical_impact_count = 1.12`
  - `high_disruption_action_rate = 0.44`
- 现象：
  - 新三目标口径已能稳定完成训练、评估和语义统计。
  - Pareto front 仍然较小，说明新口径下 Stage-1 初始前沿还比较薄。
- 结论：
  - 这条 run 可以作为新目标定义下的 Stage-1 基线。
  - 后续 Stage-2 应与这条 baseline 做直接语义对比。
- 下一步：
  - 在相同新目标定义下跑一版 Stage-2，并与该 baseline 公平比较。

### 2026-03-31 / P3-NewObjectives-Stage2-Semantic

- 实验 ID：`run_ec06fdce`
- 阶段：Stage-2 + Evaluation
- 目标：在新的 `security / business / cost` 定义下验证 Stage-2 `beta_1005` 是否仍能带来有效扩展
- 输入 buffer：[solution_buffer.json](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/p2_stage1_semantic_check/run_b01c7843/solution_buffer.json)
- 输出目录：[run_ec06fdce](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/p2_stage2_semantic_beta1005/run_ec06fdce)
- 关键指标：
  - `HV = 87.18`
  - `EU = -53.67`
  - `Pareto Count = 3`
  - `final_compromised_hosts = 2.20`
  - `final_critical_compromised_hosts = 0.38`
  - `critical_impact_count = 0.70`
  - `high_disruption_action_rate = 0.43`
- 现象：
  - 最终 Pareto front 包含 1 个 Stage-1 点和 2 个 Stage-2 扩展点。
  - 相比新目标 Stage-1 baseline，关键影响次数明显下降。
- 结论：
  - 新目标定义下，Stage-2 机制仍然有效。
  - 但当前这版 Stage-2 还只是“相对 Stage-1 有改进”，并不等于“已经超过强 baseline”。
- 下一步：
  - 把它和正式 baseline 套餐直接比较。

### 2026-03-31 / P3-Formal-Baselines

- 实验 ID：
  - `run_bdc3cfa1` sleep
  - `run_8a580b0d` random-valid
  - `run_771cd77c` stage1-only
  - `run_6219e73a` single-objective
  - `run_62da19e2` weighted-sum
- 阶段：Formal Baselines + Evaluation
- 目标：在新三目标定义下建立一套可直接对照主方法的正式 baseline 套餐
- 配置文件：
  - [cmorl_minicage/configs/formal/stage1.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/configs/formal/stage1.yaml)
  - [cmorl_minicage/configs/formal/evaluate.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/configs/formal/evaluate.yaml)
- 输出目录：
  - [sleep/run_bdc3cfa1](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/baselines_formal/sleep/run_bdc3cfa1)
  - [random_valid/run_8a580b0d](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/baselines_formal/random_valid/run_8a580b0d)
  - [stage1_only/run_771cd77c](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/baselines_formal/stage1_only/run_771cd77c)
  - [single_objective/run_6219e73a](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/baselines_formal/single_objective/run_6219e73a)
  - [weighted_sum/run_62da19e2](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/baselines_formal/weighted_sum/run_62da19e2)
- 关键结果：
  - `Weighted-Sum`
    - `EU = -28.22`
    - `final_compromised_hosts = 1.33`
    - `critical_impact_count = 0.171`
  - `Stage-1 Only`
    - `EU = -28.46`
    - `high_disruption_action_rate = 0.285`
  - `Single-Objective`
    - `EU = -69.47`
    - `recovered_hosts = 7.73`
  - `Random Valid`
    - `EU = -177.31`
    - `high_disruption_action_rate = 0.553`
- 现象：
  - `Weighted-Sum` 是当前最强的正式 baseline。
  - `Stage-1 Only` 很接近 `Weighted-Sum`，但动作更克制。
  - `Single-Objective` 更像极端点集合，不适合作为默认主线。
- 结论：
  - 当前项目已经从“只有主方法”进入“必须和强 baseline 正面对比”的阶段。
  - 之后所有主结论都应把 `Weighted-Sum` 作为首要对照。
- 下一步：
  - 做统一 reference point 下的公平 HV 重评估。

### 2026-03-31 / P3-FixedReference-Baselines

- 实验 ID：formal baseline `metrics_fixed_ref.json`
- 阶段：Re-evaluation / Fair HV
- 目标：给 5 组 formal baseline 统一同一个 `reference_point`，得到可公平横比的 HV
- 统一参考点：
  - `[-806.4847, -74.4281, -66.7700]`
- 输出文件：
  - [sleep metrics_fixed_ref.json](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/baselines_formal/sleep/run_bdc3cfa1/metrics_fixed_ref.json)
  - [random_valid metrics_fixed_ref.json](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/baselines_formal/random_valid/run_8a580b0d/metrics_fixed_ref.json)
  - [stage1_only metrics_fixed_ref.json](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/baselines_formal/stage1_only/run_771cd77c/metrics_fixed_ref.json)
  - [single_objective metrics_fixed_ref.json](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/baselines_formal/single_objective/run_6219e73a/metrics_fixed_ref.json)
  - [weighted_sum metrics_fixed_ref.json](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/baselines_formal/weighted_sum/run_62da19e2/metrics_fixed_ref.json)
- 关键指标：
  - `sleep = 3959276.75`
  - `stage1_only = 2668390.50`
  - `weighted_sum = 1927210.75`
  - `single_objective = 1910749.38`
  - `random_valid = 379004.75`
- 现象：
  - `sleep` 在统一参考点下 HV 最高。
- 结论：
  - 统一参考点让 HV 变得可横比，但也暴露出当前 reward 设计可能过度偏袒“不动作”策略。
  - 因此当前项目不应只用 HV 定主结论，仍需结合 `EU` 和语义指标。
- 下一步：
  - 分析为什么 `sleep` 在统一 HV 下异常占优。

### 2026-03-31 / P3-Main-vs-WeightedSum

- 实验 ID：`metrics_compare_main.json`
- 阶段：Main Method vs Strong Baseline
- 目标：把当前新三目标 `Stage-2 beta_1005` 和最强 baseline `Weighted-Sum` 放到同一评估口径下直接比较
- 统一参考点：
  - `[-557.1790, -53.3703, -46.2695]`
- 输出文件：
  - [weighted_sum metrics_compare_main.json](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/baselines_formal/weighted_sum/run_62da19e2/metrics_compare_main.json)
  - [stage2 metrics_compare_main.json](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/p2_stage2_semantic_beta1005/run_ec06fdce/metrics_compare_main.json)
  - [main_vs_weighted_sum_metrics.png](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/plots/main_vs_weighted_sum_metrics.png)
  - [main_vs_weighted_sum_semantics.png](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/plots/main_vs_weighted_sum_semantics.png)
- 关键指标：
  - `Weighted-Sum`
    - `HV = 441929.16`
    - `EU = -28.22`
    - `critical_impact_count = 0.204`
    - `high_disruption_action_rate = 0.344`
  - `Stage-2 beta_1005`
    - `HV = 179813.52`
    - `EU = -53.67`
    - `critical_impact_count = 0.717`
    - `high_disruption_action_rate = 0.436`
- 现象：
  - `Weighted-Sum` 在统一评估口径下显著强于当前这版 `Stage-2`。
  - `Stage-2` 采取了更多高扰动动作，但最终安全结果反而更差。
- 结论：
  - 当前新三目标下，`Weighted-Sum` 是主结果层面的强 baseline，且优于当前 `Stage-2` 主方法。
  - 因此项目当前最重要的问题，不再是“Stage-2 能不能工作”，而是“为什么它目前输给强 baseline”。
- 下一步：
  - 用 formal 训练协议重跑一版同预算 Stage-2。
  - 分析 reward 设计和 Stage-2 扩展方向为何过度牺牲 `security`。

### 2026-03-31 / P4-C2-Reward-Calibrated-Mainline

- 实验 ID：
  - `run_446acb6c` formal `Stage-1`
  - `run_46e57616` formal `Stage-2`
  - `run_bc553e0f` formal `Weighted-Sum` under calibrated reward
- 阶段：Reward Calibration + Formal Mainline Re-run
- 目标：
  - 在修正 `sleep` 异常占优问题后，重新用 formal 预算跑 `Stage-1 -> Stage-2 -> evaluate`
  - 再与当前 reward 下的 formal `Weighted-Sum` 做统一参考点公平比较
- 当前默认 reward 口径：
  - 采用 `C2 / cand_g` 版本
  - 核心变化是：
    - `security` 中加入 no-op under compromise 的显式安全惩罚
    - no-op 在 `business / cost` 上不再接近免费
- 配置文件：
  - [cmorl_minicage/configs/formal/stage1_c2.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/configs/formal/stage1_c2.yaml)
  - [cmorl_minicage/configs/formal/stage2_c2.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/configs/formal/stage2_c2.yaml)
  - [cmorl_minicage/configs/formal/evaluate.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/configs/formal/evaluate.yaml)
- 输出目录：
  - [stage1/run_446acb6c](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/formal_c2/stage1/run_446acb6c)
  - [stage2/run_46e57616](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/formal_c2/stage2/run_46e57616)
  - [weighted_sum/run_bc553e0f](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/baselines_formal_c2/cand_g/weighted_sum/run_bc553e0f)
  - 统一参考点评估：
    - [stage1 metrics_compare_c2main.json](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/formal_c2/stage1/run_446acb6c/metrics_compare_c2main.json)
    - [stage2 metrics_compare_c2main.json](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/formal_c2/stage2/run_46e57616/metrics_compare_c2main.json)
    - [weighted_sum metrics_compare_c2main.json](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/baselines_formal_c2/cand_g/weighted_sum/run_bc553e0f/metrics_compare_c2main.json)
- 统一参考点：
  - `[-746.9993, -55.7503, -45.4993]`
- 关键指标：
  - `Stage-1`
    - `HV = 362094.86`
    - `EU = -170.55`
    - `Pareto Count = 4`
    - `final_compromised_hosts = 1.48`
    - `critical_impact_count = 0.167`
    - `high_disruption_action_rate = 0.177`
  - `Stage-2`
    - `HV = 601513.12`
    - `EU = -114.70`
    - `Pareto Count = 6`
    - `final_compromised_hosts = 1.31`
    - `critical_impact_count = 0.141`
    - `high_disruption_action_rate = 0.135`
  - `Weighted-Sum`
    - `HV = 140942.10`
    - `EU = -189.66`
    - `Pareto Count = 3`
    - `final_compromised_hosts = 1.99`
    - `critical_impact_count = 0.333`
    - `high_disruption_action_rate = 0.389`
- 现象：
  - reward 修正后，`sleep` 已不再在公平 `HV / EU` 上异常占优。
  - formal `Stage-2` 不仅相对新 formal `Stage-1` 有明显提升，而且在统一参考点下已经显著超过 formal `Weighted-Sum`。
  - `Stage-2` 的前沿规模从 `Pareto Count = 4` 提升到 `6`，同时 `EU` 也大幅改善。
  - 从语义指标看，`Stage-2` 不再表现为“高扰动换差结果”，反而在更低扰动下取得更好的最终安全结果。
- 结论：
  - 在当前 `C2 / cand_g` reward 口径下，论文方法主线已经重新建立了竞争力。
  - 这轮结果表明：之前“`Weighted-Sum` 强于 `Stage-2`”的现象，很大程度上受 reward geometry 扭曲影响。
  - 经过 reward 校准后，formal `Stage-2` 已成为当前项目里表现最强的主方法结果。
- 下一步：
  - 为这轮 formal `Stage-2` 生成新的可视化主图与 `Stage-1 / Weighted-Sum` 对比图。
  - 把 [PROJECT_BRIEF.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/docs/PROJECT_BRIEF.md) 和 [README.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/README.md) 的“当前主结果判断”同步更新到这轮结论。

#### 图 1：常规指标解释与结果分析

- 图文件：
  - [formal_c2_mainline_metrics.png](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/plots/formal_c2_mainline_metrics.png)
- 比较对象：
  - `Stage-1`
  - `Stage-2`
  - `Weighted-Sum`
- 指标解释：
  - `Hypervolume`：衡量最终 Pareto front 在统一参考点下所支配的总体积，反映前沿是否整体向外扩展。该指标 `越大越好`。
  - `Expected Utility`：对评估 preference 网格做 assignment 后得到的平均 utility，反映这组策略对真实偏好分布的平均服务能力。该指标 `越大越好`；在当前实验中数值多为负，因此“越大”也可理解为“越接近 0 越好”。
  - `Sparsity`：衡量 Pareto 点在各维目标上的间距平方和，反映前沿是稠密平滑还是由少量间隔较大的点组成。该指标通常 `越小越好`，但必须结合 `Hypervolume` 与 `Pareto Count` 一起解释，不能单独下结论。
  - `Pareto Count`：最终非支配解数量，反映前沿是否足够丰富。该指标通常 `越大越好`，但点数增加只有在 `HV` 或 `EU` 不退化时才说明前沿质量真正提升。
  - `Coverage Ratio`：最终 Pareto front 中至少被一个 preference 分配到的策略比例，反映前沿中的点是否真正被使用。该指标 `越大越好`。
- 结果解释：
  - `Stage-2` 在 `Hypervolume` 上达到 `601513.12`，显著高于 `Stage-1` 的 `362094.86` 和 `Weighted-Sum` 的 `140942.10`。这说明在统一参考点下，`Stage-2` 得到了当前最外扩、最完整的 Pareto front。
  - `Stage-2` 的 `Expected Utility` 为 `-114.70`，明显优于 `Stage-1` 的 `-170.55` 和 `Weighted-Sum` 的 `-189.66`。这说明 `Stage-2` 的改进不只是几何意义上的前沿扩张，而是实实在在提升了偏好分配后的平均决策质量。
  - `Stage-2` 的 `Pareto Count` 从 `Stage-1` 的 `4` 个点提升到 `6` 个点，说明 constrained extension 的确新增了有效非支配解，而不是只把原有点微调。
  - `Stage-2` 的 `Coverage Ratio` 为 `0.667`，低于 `Stage-1` 的 `0.75` 和 `Weighted-Sum` 的 `1.0`。这说明 `Stage-2` 虽然扩展出更多点，但 assignment 仍集中在少数核心策略上，前沿还不是特别均匀、特别“满”的形态。
  - `Stage-2` 的 `Sparsity` 最高，表明当前前沿是“更外扩但更稀”的结构。这与其 `HV` 提升是一致的：当前方法更像是在高价值方向上推开了 front，而不是把整条前沿均匀加密。
  - 综合判断：这张图支持的正式结论是，当前 `Stage-2` 已经实现了“更大、更有用、但仍相对稀疏”的 Pareto front。它足以证明论文方法有效且当前最强，但也提示后续仍有继续加密前沿的空间。

#### 图 2：网络安全语义指标解释与结果分析

- 图文件：
  - [formal_c2_mainline_semantics.png](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/plots/formal_c2_mainline_semantics.png)
- 比较对象：
  - `Stage-1`
  - `Stage-2`
  - `Weighted-Sum`
- 指标解释：
  - `Final Compromised Hosts`：episode 结束时仍处于失陷状态的主机数。该指标 `越小越好`。
  - `Final Critical Compromised`：episode 结束时仍处于失陷状态的关键主机数。该指标 `越小越好`。
  - `Critical Impact Count`：episode 过程中关键资产真正遭受 impact 的次数。该指标 `越小越好`。
  - `Recovered Hosts`：被蓝方成功恢复的主机数量。该指标不能孤立判断；在相同安全结果下通常可理解为 `越大越好`，但若同时失陷也很多，则更可能意味着“反复救火”。
  - `Analyse Count`：执行 `analyse` 动作的次数，是策略侦察/确认倾向的风格指标，没有绝对的大好或小好。
  - `Remove Count`：执行 `remove` 动作的次数，是中等强度主动干预频率指标，没有绝对的大好或小好。
  - `Restore Count`：执行 `restore` 动作的次数，是高强度恢复动作频率指标，通常希望“够用但不过多”，因此不宜机械追求越大。
  - `High Disruption Rate`：高扰动动作在所有动作中的比例，反映策略是否依赖强干预。该指标通常 `越小越好`。
- 结果解释：
  - `Stage-2` 在三项核心安全结果上均为最优：`Final Compromised Hosts = 1.31`、`Final Critical Compromised = 0.096`、`Critical Impact Count = 0.141`，均优于 `Stage-1` 与 `Weighted-Sum`。这说明当前论文方法最终不仅改善了 Pareto 几何，也实际降低了网络残留失陷与关键后果。
  - `Stage-2` 的 `High Disruption Rate = 0.135`，低于 `Stage-1` 的 `0.177` 和 `Weighted-Sum` 的 `0.389`。这说明当前最优结果不是靠更粗暴的动作堆出来的，而是在更低业务扰动下取得了更好的安全结果。
  - `Weighted-Sum` 的 `Recovered Hosts = 5.151` 最高，同时 `Remove Count` 与 `Restore Count` 也显著更高。这说明 `Weighted-Sum` 更像“重干预、重恢复”的策略风格：它大量依赖强动作进行事后处置，但最终残留失陷和关键影响反而更高。
  - `Stage-1` 的 `Analyse Count = 58.19` 最高，而 `Stage-2` 为 `48.59`。这说明 `Stage-1` 更偏保守侦察型；`Stage-2` 则在保留一定确认行为的同时，减少了不必要的高扰动动作，并把干预更集中地用在真正有效的位置。
  - `Stage-2` 的 `Recovered Hosts = 0.219` 低于另外两者，这不是负面信号。结合其更低的 `Final Compromised Hosts` 与 `Critical Impact Count`，更合理的解释是：`Stage-2` 让局面在更早阶段就被控制住了，因此需要事后“恢复”的主机反而更少。
  - 综合判断：语义图说明当前 `Stage-2` 的优势并不是抽象的数学指标优势，而是具有明确网络安全意义的优势。它表现为更少的残留失陷、更少的关键主机失陷、更少的关键影响事件，以及更低的高扰动动作比例。换言之，当前论文方法已经学出了“更安全且更克制”的策略集合。

### 2026-03-31 / P5-Formal-C2-Baseline-Suite

- 实验 ID：
  - `run_162d138e` `sleep`
  - `run_c52c29c6` `random-valid`
  - `stage1_only` metrics only
  - `run_cc1669d6` `single-objective`
  - `run_19ca174c` `weighted-sum`
  - `run_46e57616` `formal Stage-2`
- 阶段：Formal C2 Baseline Suite + Unified Evaluation
- 目标：
  - 在当前默认 `C2 / cand_g` reward 口径下，把 5 个 baseline 与正式 `Stage-2` 放到同一评估协议中统一比较。
  - 一次性生成 suite 级 metrics 图、3D 图和三图 pairwise 图。
- 输出目录：
  - [sleep/run_162d138e](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/baselines_formal_c2_suite/sleep/run_162d138e)
  - [random_valid/run_c52c29c6](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/baselines_formal_c2_suite/random_valid/run_c52c29c6)
  - [stage1_only](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/baselines_formal_c2_suite/stage1_only)
  - [single_objective/run_cc1669d6](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/baselines_formal_c2_suite/single_objective/run_cc1669d6)
  - [weighted_sum/run_19ca174c](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/baselines_formal_c2_suite/weighted_sum/run_19ca174c)
  - [formal Stage-2 run_46e57616](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/formal_c2/stage2/run_46e57616)
  - 统一评估结果：
    - [sleep metrics_compare_suite.json](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/baselines_formal_c2_suite/sleep/run_162d138e/metrics_compare_suite.json)
    - [random_valid metrics_compare_suite.json](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/baselines_formal_c2_suite/random_valid/run_c52c29c6/metrics_compare_suite.json)
    - [stage1_only metrics_compare_suite.json](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/baselines_formal_c2_suite/stage1_only/metrics_compare_suite.json)
    - [single_objective metrics_compare_suite.json](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/baselines_formal_c2_suite/single_objective/run_cc1669d6/metrics_compare_suite.json)
    - [weighted_sum metrics_compare_suite.json](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/baselines_formal_c2_suite/weighted_sum/run_19ca174c/metrics_compare_suite.json)
    - [stage2 metrics_compare_suite.json](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/formal_c2/stage2/run_46e57616/metrics_compare_suite.json)
- 统一参考点：
  - `[-1523.38696, -55.75031, -45.49925]`
- 关键指标：
  - `Stage-2`
    - `HV = 1699877.00`
    - `EU = -114.69`
    - `Pareto Count = 6`
  - `Stage-1 Only`
    - `HV = 1436297.75`
    - `EU = -170.55`
    - `Pareto Count = 4`
  - `Single-Objective`
    - `HV = 1412946.75`
    - `EU = -170.83`
    - `Pareto Count = 3`
  - `Sleep`
    - `HV = 714105.19`
    - `EU = -229.84`
    - `Pareto Count = 1`
  - `Weighted-Sum`
    - `HV = 618307.75`
    - `EU = -189.66`
    - `Pareto Count = 3`
  - `Random Valid`
    - `HV = 26100.41`
    - `EU = -454.18`
    - `Pareto Count = 1`
- 图文件：
  - [formal_c2_suite_metrics.png](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/plots/formal_c2_suite_metrics.png)
  - [formal_c2_suite_3d.png](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/plots/formal_c2_suite_3d.png)
  - [formal_c2_suite_pairwise.png](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs/plots/formal_c2_suite_pairwise.png)
- 现象：
  - `Stage-2` 在 6 方法统一比较中保持最强，说明它当前不是只赢过 `Weighted-Sum`，而是同时赢过 `Stage-1 Only` 与 `Single-Objective`。
  - `Stage-1 Only` 与 `Single-Objective` 的 HV 都明显高于 `Weighted-Sum`，说明这两条线在当前 reward 口径下也是强基线，不能被视为弱对照。
  - `Sleep` 虽然在几何体积上仍不算极低，但 `EU` 已明显落后于学习型方法，说明当前 reward 校准已经把它压回正常弱 baseline 区间。
  - `Random Valid` 在 `HV / EU / Pareto Count` 上均最差，稳定充当下界。
- 结论：
  - 当前 `formal_c2` 主线的正式结论已经足够稳固：`Stage-2` 是现阶段最强方法，不只是“优于某一个 baseline”，而是优于整套 5-baseline suite。
  - 当前 `Stage-2` 最需要继续改进的方向，不再是“先证明自己能赢”，而是“把当前更强但偏稀的前沿进一步加密，并把 IPO 数值过程继续向论文靠拢”。
