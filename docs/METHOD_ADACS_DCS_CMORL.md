 
 # AdaCS-DCS-CMORL

本文档记录当前 Stage-2 升级线的正式方法口径。该升级建立在现有 `Stage-1 -> Stage-2 -> evaluate -> visualize` 主线上，只替换 Stage-2 的两个核心部件：

- `AdaCS`: Adaptive Candidate Selection
- `DCS`: Dynamic Constraint Scheduling

## 1. 总体思路

当前 Stage-2 不再只依赖：

- crowding distance 选点
- 固定 `beta` 做 IPO 约束扩展

而是把每个候选 Pareto policy 视为一个待评分对象，综合考虑：

- 稀疏性
- 可扩展性
- 风险
- 对 preference 集的覆盖能力

然后再按目标方向和 round 进度，对约束强度做动态调度。

## 2. AdaCS 选择分数

对当前 Pareto front 上的每个候选策略 `x_i`，定义：

- `crowding_score_i`
- `expansion_potential_i`
- `constraint_risk_i`
- `low_risk_i = 1 - constraint_risk_i`
- `utility_coverage_gain_i`

综合分数为：

\[
S_i
=
w_c \cdot crowding_i
+ w_e \cdot expansion_i
+ w_r \cdot low\_risk_i
+ w_u \cdot coverage_i
\]

当前默认权重为：

- `crowding = 0.30`
- `expansion = 0.30`
- `low_risk = 0.20`
- `coverage = 0.20`

选择策略：

1. 先保留每个目标维度上的 extreme policy
2. 再按 `S_i` 降序排序补足 top-N
3. tie-break 顺序：
   - `utility_coverage_gain`
   - `crowding_score`
   - `policy_id`

## 3. DCS 动态 beta

对候选 `x_i`、目标方向 `k`、扩展轮次 `r`，定义：

- `crowding_i`
- `target_expansion_{i,k}`
- `low_risk_i`
- `progress_r = r / max(R-1, 1)`

严格度定义为：

\[
s_{i,k,r}
=
\frac{
w_c \cdot crowding_i
+ w_e \cdot target\_expansion_{i,k}
+ w_l \cdot low\_risk_i
+ w_p \cdot progress_r
}{
w_c + w_e + w_l + w_p
}
\]

动态 beta 为：

\[
\beta_{i,k,r}
=
\beta_{max}
- s_{i,k,r}(\beta_{max} - \beta_{min})
\]

原始实验中首先尝试过：

- `beta_min = 0.88`
- `beta_max = 0.98`

在当前实现语义下：

- `beta` 越小，约束越严格
- 因此 strictness 越高，`beta` 越靠近 `beta_min`

但在 `independent + E3 Stage-1` 协议下，这一档区间被证明过严，会把几乎所有扩展路径卡死。当前可工作的温和调参区间是围绕旧 fixed beta `1.005` 的轻微浮动，例如：

- `gentle`
  - `beta_min = 1.000`
  - `beta_max = 1.010`
- `verygentle`
  - `beta_min = 1.004`
  - `beta_max = 1.012`

这两档都已经恢复可行扩展，且在当前 `E3 Stage-1` 基线上把 `dynamic beta` 的几何结果拉回到了与 `fixed beta` 同水平。

## 4. 与旧 Stage-2 的关系

旧 Stage-2 是：

- `crowding + fixed beta`

新 Stage-2 支持四种模式：

1. `crowding + fixed beta`
2. `adaptive selection + fixed beta`
3. `crowding + dynamic beta`
4. `adaptive selection + dynamic beta`

因此旧实现是新实现的一个可回退特例，而不是被删除的历史分支。

## 5. 当前实验状态解释

截至当前代码状态，`AdaCS-DCS-CMORL` 的实验结论应分开看：

1. `DCS` 是否可用  
   结论：可用，但必须采用温和区间。原始 `0.88~0.98` 在当前负回报目标语义下过严；围绕 `1.005` 的温和 DCS 已能稳定生成 `7~8` 个 Stage-2 候选，并把 Pareto front 扩到 `5` 个点。

2. `AdaCS` 是否已经显出独立增益  
   结论：暂时还没有。当前 `E3 Stage-1` 的 Pareto front 只有 `3` 个点，而且 `keep_extremes=true` 时这 `3` 个点会被全部保留，所以 `crowding` 与 `adaptive` 在 round 0 实际选到同一组父策略，导致最终结果与 `fixed beta` 或温和 `DCS` 路径完全重合。

因此，当前瓶颈已经从“DCS 太严”转移为“Stage-1 前沿太薄，AdaCS 无点可分”。

## 6. 当前输出

升级后，Stage-2 额外输出：

- `method_diagnostics.json`
- `stage2_summary.json` 中的：
  - `selection_mode`
  - `beta_schedule_mode`
  - `selected_policy_scores`
  - `selected_policy_components`
- 每个新 record `notes` 中的：
  - `selection_score`
  - `crowding_score`
  - `expansion_potential`
  - `constraint_risk`
  - `utility_coverage_gain`
  - `dynamic_beta`
  - `beta_components`

## 7. 三个性质

当前升级线希望满足三条方法性质：

1. `extreme-point preservation`
   - extreme Pareto policies 不会因为综合打分被完全挤掉

2. `dynamic beta monotone conservativeness`
   - 在其他条件不变时，更高 strictness 会映射到更小的 `beta`

3. `fixed-beta as a special case`
   - 当 `selection.mode=crowding` 且 `ipo.beta_mode=fixed` 时，行为退化为旧 Stage-2
