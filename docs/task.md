## CCS 2026 主会冲刺路线（实验与写作联动）

### 当前策略决策

- `In Progress` 本轮不再把任务理解为“继续无上限扩实验”，而是切换为 **正式结果收口 + 缺口最小补强 + 主文快速成稿**。
- `In Progress` 当前论文实验主线统一按 **集合价值（set value） + 部署价值（deployment value）** 两层组织：
  - `集合价值`：证明方法能生成更高质量、更广覆盖、更有偏好适应性的候选策略集合
  - `部署价值`：证明从集合中选出的最终可部署策略在约束下具有良好效果
- `In Progress` 当前对外结果口径继续优先使用 `cmorl_cyborg`，不把 `cmorl_minicage` 的升级探索结果直接混入主文主结果。
- `Planned` 本轮主文只保留少量核心图表；扩展图、散点图、更多消融图默认下放到 appendix。
- `Planned` 本轮主消融优先使用当前正式 CybORG 线中已经成型的变体：
  - `ours_stage2`
  - `stage1_only`
  - `no_constraint_stage2`
  - `weighted_sum`
- `Planned` `AdaCS / DCS` 只有在 `cmorl_cyborg` 正式线补齐一致口径后，才考虑进入主文主消融；否则只保留在 appendix / future work / separate branch。

---

### 本轮总目标

- `In Progress` 把当前实验部分收敛成 **2 张主表 + 2 张主图 + 1 个核心消融小节**。
- `In Progress` 让 `paper/main.tex` 从 starter skeleton 升级为可提交初稿。
- `In Progress` 为后续提交准备匿名 artifact、Open Science appendix、Ethical Considerations appendix 所需的最小复现实验包。
- `Planned` 在不大规模推翻当前正式结果线的前提下，只补最值钱的新统计与最小稳定性增强。

---

### P0 最高优先级：锁定实验叙事与主结果结构

#### E-001 固化实验主叙事为“集合价值 + 部署价值”

- `Planned` 在论文与文档中统一以下结构：
  - `Table A = Set Quality Table`
  - `Table B = Deployment Table`
  - `Figure C = Preference Coverage`
  - `Figure D = Tight Feasible Set Quality`
- `Planned` 不再把主实验写成“很多 baseline 的普通 RL 对比表”，而是明确区分：
  - 哪些结果说明 **候选集合本身更好**
  - 哪些结果说明 **最终部署点更好**
- `验收标准`
  - `paper/main.tex` 中实验节小标题与上述 4 个模块完全一致
  - README / docs / figure 命名中不再混用“主表 A/B”与“集合/部署价值”的口径

#### E-002 锁定主文保留的核心方法集合

- `Planned` 固化 `Table A` 使用的正式方法组：
  - `ours_stage2`
  - `stage1_only`
  - `weighted_sum`
  - `preference_conditioned_ppo`
  - `pcn`
- `Planned` 固化 `Table B` 使用的正式方法组：
  - `ours_stage2`
  - `lagrangian_ppo`
  - `weighted_sum`
  - `stage1_only`
  - `no_constraint_stage2`
  - `single_objective`
- `Planned` 如果某方法当前未在正式 CybORG 线完成统一聚合，则：
  - 不强行纳入主文
  - 先放 appendix 或写成 TODO
- `验收标准`
  - `docs/TASKS.md`、导表配置、论文草稿三处方法名保持一致
  - 不再出现“主文表里方法集合”和“代码导表方法集合”不一致的问题

---

### P0 最高优先级：把现有结果整理成可直接入论文的主表

#### E-101 重构现有 Table A 为 Set Quality Table

- `Planned` 直接基于当前 `paper_table_a` 聚合结果生成新的论文主表版本。
- `Planned` `Table A` 保留以下 5 个指标：
  - `hypervolume`
  - `expected_utility`
  - `coverage_ratio`
  - `unique_assigned_policies`
  - `num_pareto_records`
- `Planned` 指标解读规则：
  - `hypervolume / expected_utility` 作为主指标
  - `coverage_ratio / unique_assigned_policies` 作为偏好覆盖与集合可选性指标
  - `num_pareto_records` 只作为辅助规模指标，不写成 headline claim
- `Planned` 新增导出文件：
  - `cmorl_cyborg/outputs/paper_table_a/set_quality_table.csv`
  - `cmorl_cyborg/outputs/paper_table_a/set_quality_table.tex`
  - `cmorl_cyborg/outputs/paper_table_a/set_quality_table.json`
- `验收标准`
  - 表格可直接插入 `paper/main.tex`
  - 每个方法均值 ± 方差齐全
  - 表标题和 caption 明确写成 “candidate set quality” 而非泛泛 “main results”

#### E-102 固化现有 Table B 为 Deployment Table

- `Planned` 基于当前 `paper_table_b/aggregated/` 和 `fair_compare_eval/aggregated/` 结果，输出统一部署表。
- `Planned` `Table B` 保留以下指标：
  - `security_return`
  - `business_return`
  - `cost_return`
  - `feasible_rate`
  - `mean_violation`
  - `final_critical_compromised_hosts`
- `Planned` caption 与正文口径统一写成：
  - “deployment quality under constraints”
  - 不写成“全指标绝对最优”
- `Planned` 新增导出文件：
  - `cmorl_cyborg/outputs/paper_table_b/deployment_table.csv`
  - `cmorl_cyborg/outputs/paper_table_b/deployment_table.tex`
  - `cmorl_cyborg/outputs/paper_table_b/deployment_table.json`
- `验收标准`
  - 表格中所有方法使用同一约束阈值口径
  - 结果与现有 aggregated json 一致
  - caption 明确区分“集合价值”和“部署价值”

---

### P0 最高优先级：补两个最值钱的新统计量

#### E-201 导出 per-preference assignment 结果，用于 Preference Coverage 图

- `Planned` 在 `evaluate.py` 或单独新脚本中增加 per-preference 导出能力。
- `Planned` 为每个方法、每个 seed、每个评估 preference 导出：
  - `preference_id`
  - `preference_vector`
  - `assigned_policy_id`
  - `utility`
  - `security_return`
  - `business_return`
  - `cost_return`
  - `is_feasible`
- `Planned` 新增文件：
  - `cmorl_cyborg/outputs/paper_table_a/preference_assignments/<method>/seed_xxxx/per_preference_assignment.json`
  - `cmorl_cyborg/outputs/paper_table_a/preference_assignments/aggregated/per_preference_assignment_summary.csv`
- `Planned` 基于该文件绘制：
  - `preference_coverage_utility.png`
  - `preference_assignment_diversity.png`
  - 可选：`preference_feasibility_heatmap.png`
- `验收标准`
  - 能看出不同方法在不同 preference 下的 utility 变化
  - 能统计“有多少不同 preference 最终分配到同一策略”
  - 输出文件可供论文图与 appendix 图共用

#### E-202 统计 tight 阈值下的 feasible candidate set，用于 Tight Feasible Set 图

- `Planned` 新增候选集合级可行性统计，不再只看最终 selected policy。
- `Planned` 在 tight 阈值下，为每个方法、每个 seed 统计：
  - `feasible_candidate_count`
  - `feasible_pareto_ratio`
  - `best_feasible_security_return`
  - 可选：`mean_feasible_utility`
- `Planned` 新增文件：
  - `cmorl_cyborg/outputs/fair_compare_eval/tight_feasible_set_summary/<method>/seed_xxxx.json`
  - `cmorl_cyborg/outputs/fair_compare_eval/aggregated/tight_feasible_set_summary.csv`
- `Planned` 绘制：
  - `tight_feasible_candidate_count.png`
  - `tight_feasible_ratio.png`
  - `tight_best_feasible_security.png`
  - 或统一 `tight_feasible_set_quality.png`
- `验收标准`
  - 图和表都反映“严格约束下还有多少真正可部署候选”
  - 不再把 tight 分析仅停留在 selected-policy 聚合层面
  - 结果可直接支持“constrained set value”叙事

---

### P0 最高优先级：实验与写作同步推进

#### W-001 立即填满 `paper/main.tex` 的实验节骨架

- `Planned` 在 `paper/main.tex` 中优先完成以下节的正式文字：
  - `Environment and Threat Model`
  - `Objectives, Constraints, and Evaluation Protocol`
  - `Baselines`
  - `Metrics`
  - `Candidate Set Quality`
  - `Deployment Quality`
  - `Preference Coverage`
  - `Tight Feasible Set Quality`
  - `Ablation`
- `Planned` 先写“空框架 + 占位图表引用 + 保守 claim”，不要等所有新图完工才开始写。
- `Planned` 把当前 starter abstract 改写成更贴近正式实验结果的版本。
- `验收标准`
  - `paper/main.tex` 中实验节不再是 placeholder bullet
  - 所有主表主图在正文中都有明确引用位置
  - 当前草稿可在无最终图表情况下独立编译并通读

#### W-002 统一论文中的 claim 强度

- `Planned` 当前主结果部分只允许写以下强度的 claim：
  - `ours_stage2` 在集合级 `HV / EU` 上最好
  - `ours_stage2` 提供更高质量、更广覆盖的候选集合
  - 部署结果体现的是 trade-off-aware quality，而非所有约束指标绝对最优
  - strict constraints 下的集合部署价值需要通过 feasible-set statistics 展示
- `Planned` 禁止在主文中直接写：
  - “无条件最优”
  - “在所有指标上都显著领先”
  - “coverage 机制已经稳定优于原始主线”
- `验收标准`
  - 引言、实验节、讨论节中的结论口径一致
  - 不出现与现有 aggregated 结果相冲突的强 claim

---

### P1 次高优先级：最小稳定性增强

#### E-301 扩展 3-seed 到最小 5-seed 稳定性验证

- `Planned` 不全面重跑所有方法，只优先补最关键 2~3 个方法：
  - `ours_stage2`
  - `weighted_sum`
  - `stage1_only`
  - 如资源紧张，可把 `stage1_only` 替换为 `no_constraint_stage2`
- `Planned` 使用与当前正式协议一致的设置重跑新增 seed。
- `Planned` 更新：
  - `set_quality_table.*`
  - `deployment_table.*`
  - `preference coverage` 的方差带
  - `tight feasible set quality` 的 seed 级分布
- `验收标准`
  - 至少 2 个最关键基线完成 5-seed 统计
  - 主文中可以把“3-seed 现象”升级为“5-seed 下趋势保持一致”
  - 新结果不破坏当前正式口径目录结构

---

### P1 次高优先级：补 business / cost 的结果化语义解释

#### E-401 增加 business / cost 的结果化语义指标

- `Planned` 当前 security 语义指标已较完整，本轮补 business / cost 的更结果化解释。
- `Planned` 候选指标优先级：
  - `business_disruption_steps`
  - `service_affected_hosts`
  - `avg_intervention_count`
  - `expensive_action_ratio`
  - `mean_recovery_delay`
- `Planned` 不要求这些指标全部进入主表；优先用于：
  - 部署表正文解释
  - appendix 附图/附表
- `验收标准`
  - business / cost 不再只依赖抽象 reward 数值解释
  - 至少有 2 个能落到安全运维语义上的指标
  - 主文 Discussion 可引用这些指标解释 trade-off

---

### P1 次高优先级：最小泛化增强（如时间允许）

#### E-501 增加 held-out attacker / alternate red 的小型泛化评测

- `Planned` 本轮不把论文升级成完整 robust-opponent 工作，但补一个最小 attacker-shift 检查。
- `Planned` 最小实验形式：
  - 在当前默认 red 设定上训练
  - 在另一个 red policy / attacker configuration / holdout evaluation setting 上测试
- `Planned` 只比较最关键方法：
  - `ours_stage2`
  - `weighted_sum`
  - `stage1_only` 或 `no_constraint_stage2`
- `Planned` 新增文件：
  - `cmorl_cyborg/outputs/paper_appendix/attacker_shift_summary.json`
  - `cmorl_cyborg/outputs/paper_appendix/attacker_shift_table.tex`
- `验收标准`
  - 能回答“方法是否只对单一脚本红方成立”
  - 如果结果一般，也可保守写入 appendix，不强行升格为主结果

---

### P1 次高优先级：最小主消融收敛

#### E-601 固化主文只保留 3 组核心消融

- `Planned` 主文消融默认只保留：
  - `stage1_only`
  - `no_constraint_stage2`
  - `ours_stage2`
- `Planned` 如版面允许，再加入：
  - `weighted_sum`
- `Planned` 主消融回答 3 个问题：
  - Pareto extension 是否有效
  - 约束机制是否有效
  - 方法是否只是 scalarization baseline 的换皮
- `Planned` `AdaCS / DCS` 暂不进入主文核心消融，除非在 `cmorl_cyborg` 正式线补齐一致实验。
- `验收标准`
  - 消融节短而清楚
  - 每个变体都能对应一个明确因果问题
  - 不再把探索线结果和正式线结果混写

---

### P1 次高优先级：Open Science 与匿名 artifact 收口

#### A-001 准备匿名 artifact 最小包

- `Planned` 按主文核心贡献整理最小 artifact：
  - 关键代码路径
  - 关键 config
  - 运行脚本
  - 导表脚本
  - 关键结果 json/csv
  - 复现实验说明
- `Planned` artifact 包只围绕主文核心结果，不追求把整个仓库所有历史输出都放进去。
- `Planned` 新增文档：
  - `paper/OPEN_SCIENCE_APPENDIX.md`
  - `paper/ARTIFACT_README.md`
- `验收标准`
  - 审稿人可匿名访问并复现主表 A / B 的导表流程
  - artifact 不暴露作者身份
  - 代码、图表、论文表格三者路径对应清楚

#### A-002 准备伦理与匿名检查

- `Planned` 新增：
  - `paper/ETHICAL_CONSIDERATIONS.md`
  - `paper/ANONYMITY_CHECKLIST.md`
- `Planned` 检查项至少包括：
  - 作者信息是否移除
  - acknowledgements 是否关闭
  - 仓库链接是否匿名化
  - 自引用是否第三人称
  - artifact 是否不含 deanonymizing metadata
- `验收标准`
  - `paper/main.tex` 可切换到正式匿名投稿状态
  - artifact 与正文均不暴露身份信息

---

### P2 中期优先级：可视化与 appendix 整理

#### V-001 统一主文与 appendix 图像导出

- `Planned` 本轮主文图只保留：
  - `preference_coverage_utility.png`
  - `tight_feasible_set_quality.png`
  - 如需要，再加一张紧凑的 objective-space figure
- `Planned` appendix 图可保留：
  - `objective_space_scatter`
  - `pairwise objective overlay`
  - `per-seed semantic comparison`
  - `extra fair compare panels`
- `Planned` 图文件命名统一成论文友好形式，避免沿用开发期命名。
- `验收标准`
  - 主文图表编号清晰
  - appendix 图表可独立引用
  - 不再出现“输出文件名看不出用途”的问题

---

### 当前不做

- `Planned` 暂不把 `AdaCS / DCS` 作为本轮主文主贡献重心。
- `Planned` 暂不引入新的大算法分支，如 `CPO` 正式复刻。
- `Planned` 暂不把任务扩成完整红蓝双学习体或博弈均衡论文。
- `Planned` 暂不做全量多方法 5-seed 重跑。
- `原因`
  - 本轮最重要的是把当前正式结果线收成一篇能提交的 CCS 主会稿
  - 新开大线会稀释主文叙事并拖慢提交节奏

---

### 建议 Codex 的实现顺序

1. `E-001 ~ E-002`
   - 锁定主表/主图/主方法集合
2. `E-101 ~ E-102`
   - 导出正式 `Set Quality Table` 与 `Deployment Table`
3. `E-201`
   - 导出 per-preference assignment 并生成 Preference Coverage 图
4. `E-202`
   - 导出 tight feasible set summary 并生成 Tight Feasible Set 图
5. `W-001 ~ W-002`
   - 立即同步填写 `paper/main.tex`
6. `E-301`
   - 做最小 5-seed 稳定性增强
7. `E-401`
   - 补 business/cost 语义解释
8. `E-501`
   - 如资源允许，补 held-out attacker 小泛化
9. `A-001 ~ A-002`
   - 收 Open Science、Ethics、匿名 artifact
10. `V-001`
   - 整理 appendix 图表与导表脚本

---

### 本轮完成标志

- `Done` 形成可直接插入论文的：
  - `Table A = Set Quality Table`
  - `Table B = Deployment Table`
  - `Figure C = Preference Coverage`
  - `Figure D = Tight Feasible Set Quality`
- `Done` `paper/main.tex` 的实验节完成从 skeleton 到可投初稿的升级
- `Done` 至少完成一轮最小稳定性增强
- `Done` Open Science appendix、Ethical Considerations、匿名 artifact 基本齐备
- `Done` 主文叙事从“普通 RL 对比”升级为“集合价值 + 部署价值”的安全论文叙事





