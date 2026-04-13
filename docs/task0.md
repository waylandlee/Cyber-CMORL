# 论文实验部分待办清单（2026-04-09）

## 当前总判断

- 论文实验主线已经成型，不需要再新增一整套大实验。
- 现在最需要改进的，不是“实验数量不够”，而是：
  - Figure D 的口径和摆放方式
  - `ours` vs `no_constraint_stage2` 的公平比较口径
  - appendix 中仍然空着的实验细节
  - 主文 claim 强度与结果的一致性
  - Table A / Table B 的论文化展示
- 如果还要继续补实验，最值得做的不是加新 baseline，而是只针对 tight-constraint 弱点做小而准的补强。

## 已经具备的实验资产

- 主文主结果已经齐全：
  - Table A = Set Quality Table
  - Table B = Deployment Table
  - Figure C = Preference Coverage
  - Figure D = Tight Feasible Set Quality
- 关键方法已经有最小 5-seed 稳定性增强：
  - `ours_stage2`
  - `stage1_only`
  - `weighted_sum`
- `E-401` 已完成：
  - business / cost semantics 已有 appendix 表和图
  - 可以支持 deployment trade-off 的运维语义解释
- `E-501` 已完成：
  - held-out attacker shift 已做
  - 当前结果更适合写成 limitation / appendix stress test，而不是主文卖点

## 当前实验部分最主要的优点

- [`CybORG_plus_plus/paper/main.tex`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/paper/main.tex) 已经把实验组织成 `set value + deployment value` 两层，这个结构是对的。
- Table A 结果足够稳：
  - `ours_stage2` 在 HV / EU 上仍是主胜点。
- Table B 结果也足够支撑主文：
  - `ours_stage2` 相比 `weighted_sum` 在 security / business / feasible rate / mean violation 上更好。
- 但 `no_constraint_stage2` 在某些 deployment 指标上更强，所以主文必须继续保持 trade-off aware 口径。
- Figure C 和 business/cost semantics 已经形成比较完整的辅助证据链。

## 本轮问答形成的关键事实备忘

### 1. 关于正式 CybORG 环境本身是否被改动

- 正式实验并不是跑未修改的 upstream CybORG，而是跑仓库中的 `Debugged_CybORG` 修复版。
- 但 `cmorl_cyborg` 这条正式实验线并没有重写 `Scenario2` 的核心状态转移机制。
- 当前真正额外加上的主要是：
  - wrapper 层的多目标 reward 投影
  - `semantic_info` 语义统计
  - deployment-aware evaluation protocol
- 因此更准确的表述应是：
  - “正式实验基于修复版 CybORG 运行；核心环境机制未被重写，但外层增加了多目标 reward 与语义评估层。”

### 2. 关于红方攻击者设定

- 当前主线是蓝方学习、红方固定。
- 默认红方是 `B_lineAgent`，即：
  - train-time mainline = `bline`
  - held-out attacker appendix = `meander`
- “红方固定”指的是：
  - 固定策略类
  - 不参与训练更新
  - 不是每局都执行完全相同的动作序列
- 对论文与答辩最稳妥的说法应是：
  - “主结果在固定脚本红方 `B_lineAgent` 下训练和评估，附录再用 `RedMeanderAgent` 做小型 held-out stress test。”

### 3. 关于 held-out attacker 小泛化

- 这项实验本质上是：
  - `train on bline`
  - `eval on meander`
  - 不重训
  - 不微调
  - 不做 shift-specific adaptation
- 当前实现是纯 reevaluation：
  - 复制已有 `solution_buffer.json`
  - 只把 `metadata.env.red_policy` 从 `bline` 改成 `meander`
  - 再按原 deployment selection 规则重评估
- 因此它可以算：
  - 一个比较严格的零适配 held-out attacker stress test
- 但不能算：
  - 足以支撑强 attacker-robust generalization 主张的完整泛化实验
- 当前最稳妥的论文口径应是：
  - 把它写成 appendix limitation / stress test
  - 不把它写成 main-text strength claim

### 4. 关于部署阶段到底在做什么

- “部署”需要分成两层：
  - 先从候选策略集合中选最终部署策略
  - 再让该策略在环境中实际 rollout
- deployment-time selection 的输入是：
  - `solution_buffer.json` 中的 candidate policy set
  - preference vector / thresholds / selection rule
- deployment-time selection 的输出是：
  - 一个最终被选中的 policy / checkpoint
  - 以及对应的 deployment metrics
- 真正 runtime rollout 时，策略的输入输出是：
  - 输入：environment observation
  - 输出：blue action
- 因此答辩时不应把“部署输入”简化成“只是一条 observation”。

### 5. 关于 AdaCS / DCS 在正式线中的位置

- 当前 `cmorl_cyborg` 的 `ours_stage2` 已经不是旧的原始 Stage-2。
- 它使用的是：
  - `AdaCS = adaptive selection`
  - `DCS = dynamic beta`
- 二者作用位置不同：
  - `AdaCS` 决定从当前候选集中挑哪些 parent policies 去做 Stage-2 扩展
  - `DCS` 决定每条扩展路径上的 `beta` / 约束松紧程度
- 当前 `cmorl_cyborg` 正式主线使用的是温和版 `adaptive + dynamic`
- 不是 `minicage` 里更激进的 `AdaCS-DCS chase`

### 6. 关于当前 Table 3 / Table 4 的解释口径

- 当前完整编译版里，附录表的口径应理解为：
  - Table 3 = held-out attacker shift
  - Table 4 = business and cost semantics
- 其中：
  - Table 3 主要是在报告 attacker-shift limitation
  - Table 4 主要是在把 business / cost 从抽象 reward 翻译成运维语义
- 因此：
  - Table 3 不是主胜点
  - Table 4 是 deployment trade-off 的解释性证据

### 关于 Stage-2 当前配置是否“已最优”的判断

- 目前更准确的判断是：
  - `cmorl_minicage` 线里的 `AdaCS-DCS chase` 已经明显强于早期温和版 `gentle / verygentle`
  - 但 `cmorl_cyborg` 当前主线使用的仍是更温和的 `stage2_main` 配置，而不是 `chase`
- 因此：
  - 不能把 `minicage chase` 的优势直接表述成“CybORG 正式线也已证实最优”
  - 当前 `cmorl_cyborg` 的 `ours_stage2` 更适合表述为：
    - 一个稳定、可复现、能支撑主文结论的近优 operating point
    - 而不是一个已经被严格证明的全局最优配置

当前把 `cmorl_cyborg` 主线视为“近优而非已最优”的主要原因是：

- 它已经明显脱离早期失败区：
  - 不再出现旧 DCS 过严时那种 `generated = 0` / Stage-2 空转状态
- 它已经足够支撑当前论文主张：
  - Table A 上 `ours_stage2` 仍是 `HV / EU` 主胜点
  - Table B 上 `ours_stage2` 也保持了有竞争力的 deployment trade-off
- 它附近仍然存在一些“局部更好”的变体：
  - `coverage_combo` / `coverage_more_parents` 在部分 loose 指标上更好
  - `tightplus` 在 tight stress test 下能救回一部分 feasible candidate
  - 但这些变体都还没有形成对当前主线的严格支配

因此，当前更稳妥的项目口径应是：

- 不宣称 `stage2_main` 已达到全局最优
- 但可以宣称它已经达到：
  - 当前正式主线里一个近优、稳定、可防守的配置点
- 如果还要继续提升 `Ours`，优先级应放在：
  - 更有针对性的机制 / 协议层补强
  - tight stress case 的定向修复
  - `fair_compare` 与 deployment 结果的公平表达
- 不建议再做大范围训练超参搜索，期待出现“全面更好”的新主点

### 关于 `crowding + fixed beta` 在 `cmorl_cyborg` 里当前是否有可比结果

- 截至 `2026-04-10 00:15`，`cmorl_cyborg` 里这条 matched baseline 已经完整补齐：
  - `Original Stage2 = crowding + fixed beta`
  - 固定配置路径：
    - [`CybORG_plus_plus/cmorl_cyborg/configs/paper/fair_compare_original/stage2_original_stage2_fair_seed_0007.yaml`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/configs/paper/fair_compare_original/stage2_original_stage2_fair_seed_0007.yaml)
    - [`CybORG_plus_plus/cmorl_cyborg/configs/paper/fair_compare_original/stage2_original_stage2_fair_seed_0011.yaml`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/configs/paper/fair_compare_original/stage2_original_stage2_fair_seed_0011.yaml)
    - [`CybORG_plus_plus/cmorl_cyborg/configs/paper/fair_compare_original/stage2_original_stage2_fair_seed_0019.yaml`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/configs/paper/fair_compare_original/stage2_original_stage2_fair_seed_0019.yaml)
- 这条线的 matched 原则是：
  - 与当前 `fair_compare` 线共享同一 `stage1_buffer`
  - 共享同一 `constraint_tolerance / extension_rounds / constrained_updates / total_timesteps_per_update`
  - 只把：
    - `selection.mode` 改成 `crowding`
    - `ipo.beta_mode` 改成 `fixed`
    - `ipo.beta` 固定为 `1.005`
- 当前进度：
  - `seed_0007 / seed_0011 / seed_0019` 已全部完成训练、`metrics.json`、`constraint_metrics.json` 与 reevaluated tight feasible summary
  - 自动 runner 在：
    - [`CybORG_plus_plus/cmorl_cyborg/original_stage2_fair_runner.py`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/original_stage2_fair_runner.py)
    - 当前状态文件：
      - [`CybORG_plus_plus/cmorl_cyborg/outputs/fair_compare_original_stage2_runner/status.json`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/fair_compare_original_stage2_runner/status.json)
- 因此现在更准确的说法应是：
  - `cmorl_cyborg` 已经有一条完整的、3-seed matched `crowding + fixed beta` 正式对照线
  - 后续论文里如果要把 `Original Stage2` 当作正式 baseline 写，应该引用这条线，而不是混用旧的非 matched 结果

### 关于 `ours` vs `no_constraint_stage2` 的当前判断

- 这组对照现在必须分成两条线来理解：
  - `Table B`：broad deployment comparison
  - `fair_compare`：matched ablation line
- 对于“constraint-aware expansion 到底有没有用”这个因果问题，后续应统一使用 `fair_compare` 作为正式口径。
- 原因是：
  - `fair_compare` 中 `ours_stage2_fair` 和 `no_constraint_stage2_fair` 只在 `extension_mode` 上不同，其他核心 Stage-2 参数保持一致。
  - `Table B` 当前使用的 `ours_stage2` 和 `no_constraint_stage2` 并不是严格 matched config，更适合做 broad main-paper comparison，而不是严格因果消融。

### 关于 `Original Stage2` matched baseline 的最终结果（2026-04-10 凌晨，3-seed）

- 当前已经生成 `AdaCS-DCS (ours)` vs `Original Stage2` 的完整 `3-seed` 对比：
  - set-value compare：
    - [`CybORG_plus_plus/cmorl_cyborg/outputs/fair_compare_eval/set_value_compare_original_vs_ours/table_a_summary.json`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/fair_compare_eval/set_value_compare_original_vs_ours/table_a_summary.json)
    - [`CybORG_plus_plus/cmorl_cyborg/outputs/fair_compare_eval/set_value_compare_original_vs_ours/set_value_compare_original_vs_ours.png`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/fair_compare_eval/set_value_compare_original_vs_ours/set_value_compare_original_vs_ours.png)
  - selected-policy tight compare：
    - [`CybORG_plus_plus/cmorl_cyborg/outputs/fair_compare_eval/aggregated/fair_compare_table_b_tight_with_original_stage2.png`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/fair_compare_eval/aggregated/fair_compare_table_b_tight_with_original_stage2.png)
  - reevaluated tight feasible-set compare：
    - [`CybORG_plus_plus/cmorl_cyborg/outputs/fair_compare_eval/aggregated/reevaluated_tight_feasible_set_quality_with_original_stage2.png`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/fair_compare_eval/aggregated/reevaluated_tight_feasible_set_quality_with_original_stage2.png)
    - [`CybORG_plus_plus/cmorl_cyborg/outputs/fair_compare_eval/aggregated/reevaluated_tight_feasible_set_summary_with_original_stage2.json`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/fair_compare_eval/aggregated/reevaluated_tight_feasible_set_summary_with_original_stage2.json)
- 汇总差异文件：
  - [`CybORG_plus_plus/cmorl_cyborg/outputs/fair_compare_original_stage2_runner/original_stage2_fair_diff.json`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/fair_compare_original_stage2_runner/original_stage2_fair_diff.json)
- 当前最关键的结果分三层看：

1. `Set value` 层

- `Original Stage2` 相比 `AdaCS-DCS`：
  - `hypervolume` 略高：
    - `2024963.70 ± 42021.32` vs `2004702.78 ± 148622.68`
  - `expected_utility` 更差：
    - `-179.97 ± 8.95` vs `-175.40 ± 2.89`
  - `sparsity` 明显更差：
    - `24255.42 ± 7158.34` vs `42087.12 ± 11909.79`
  - `coverage_ratio` 更差：
    - `0.2317 ± 0.0540` vs `0.2833 ± 0.0419`
  - `unique_assigned_policies` 略少：
    - `3.33 ± 0.47` vs `3.67 ± 0.47`
  - `num_pareto_records` 更多：
    - `14.67 ± 1.25` vs `13.00 ± 0.82`
- 这说明：
  - `Original Stage2` 现在不再只是“点多但整体差”；在 3-seed 下它把 `hypervolume` 也拉到了略高于 `AdaCS-DCS`
  - 但 `AdaCS-DCS` 仍然保持了更好的平均效用、更好的 front spread、更好的 preference coverage 和略高的最终策略多样性
  - 因此 set-value 层的更准确表述应是：
    - `Original Stage2` 在 `HV + Pareto count` 上占优
    - `AdaCS-DCS` 在 `EU + sparsity + coverage + variety` 上占优
  - 这更像两种不同前沿形状：
    - `Original Stage2` 更“厚”
    - `AdaCS-DCS` 更“展开、更均衡”

2. `Selected-policy under tight constraints` 层

- `Original Stage2` 相比 `AdaCS-DCS`：
  - `security_return` 更差：
    - `-603.48 ± 110.48` vs `-549.80 ± 80.12`
  - `business_return` 更差：
    - `-121.52 ± 4.54` vs `-118.16 ± 5.17`
  - `cost_return` 略好：
    - `-22.67 ± 1.62` vs `-23.12 ± 0.90`
  - `feasible_rate` 更高：
    - `0.198 ± 0.256` vs `0.142 ± 0.150`
  - 但 `mean_violation` 反而更高：
    - `7.375 ± 1.551` vs `5.776 ± 0.528`
  - `final_critical_compromised_hosts` 略少：
    - `0.781 ± 0.045` vs `0.842 ± 0.062`
  - `critical_impact_count` 略高：
    - `3.316 ± 1.708` vs `3.017 ± 1.168`
  - `high_disruption_action_rate` 略低：
    - `0.911 ± 0.025` vs `0.931 ± 0.029`
- 这说明：
  - `Original Stage2` 在 tight selection 下更像“更保守、更便宜一点、更容易偶尔过线”
  - 但它并没有在 selected-policy 层面形成全面优势，因为：
    - 安全回报更差
    - 商业回报也更差
    - 且一旦违反约束，平均违反幅度更大

3. `Reevaluated tight feasible set` 层

- `AdaCS-DCS`：
  - `reevaluated_feasible_candidate_count = 0`
  - `reevaluated_feasible_pareto_ratio = 0`
  - `num_runs_with_reevaluated_feasible_candidate = 0 / 3`
  - `closest_candidate_margin = -1.1563 ± 1.0744`
- `Original Stage2`：
  - `reevaluated_feasible_candidate_count = 0.667 ± 0.471`
  - `reevaluated_feasible_pareto_ratio = 0.0465 ± 0.0334`
  - `num_runs_with_reevaluated_feasible_candidate = 2 / 3`
  - `best_reevaluated_feasible_security_return = -988.87 ± 225.81`
  - `closest_candidate_margin = +0.2805 ± 1.6128`
- 逐 seed 看：
  - `seed_0007` 有 `1` 个过线候选，最佳可行安全回报约 `-1214.68`
  - `seed_0011` 没有过线候选，最近 margin 约 `-1.986`
  - `seed_0019` 有 `1` 个过线候选，最佳可行安全回报约 `-763.06`
- 这说明：
  - 3-seed 完整结果已经支持更强的结论：
    - `Original Stage2` 在锁死 tight protocol 下，确实更容易保住“偶发但真实”的可行候选
    - `AdaCS-DCS` 在这组 tight reevaluation 里仍然是 `0`
  - 但这仍然不是“Original Stage2 全面优于 Ours”，因为它的优势主要集中在：
    - strict feasibility retention
    - 更保守的 selected-policy 行为
  - `AdaCS-DCS` 的主胜点仍然在：
    - expected utility
    - candidate-set spread / coverage
    - 更强的 selected-policy security return

- 因此当前最稳妥的论文口径应是：
  - 可以把 `Original Stage2` 作为正式 matched baseline 写入
  - 主文不要写成某一方“全面胜出”
  - 更准确的主叙事是：
    - `AdaCS-DCS` improves utility, spread, and preference coverage, but the original crowding + fixed-beta line retains occasional conservative feasible candidates under the locked tight protocol.
  - 如果篇幅允许，tight feasible-set 这一点应作为：
    - limitation / trade-off
    - 或 appendix 中的 stress-test nuance

### 关于 `AdaCS / DCS` 2×2 核心消融矩阵的最终结果（2026-04-10 凌晨，3-seed）

- `A-101` 里缺的两条 matched 消融现在已经完整补齐并跑完：
  - `AdaCS Only = adaptive selection + fixed beta`
  - `DCS Only = crowding + dynamic beta`
- 新增固定配置：
  - [`CybORG_plus_plus/cmorl_cyborg/configs/paper/fair_compare_ablation/stage2_adaptive_fixed_fair_seed_0007.yaml`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/configs/paper/fair_compare_ablation/stage2_adaptive_fixed_fair_seed_0007.yaml)
  - [`CybORG_plus_plus/cmorl_cyborg/configs/paper/fair_compare_ablation/stage2_adaptive_fixed_fair_seed_0011.yaml`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/configs/paper/fair_compare_ablation/stage2_adaptive_fixed_fair_seed_0011.yaml)
  - [`CybORG_plus_plus/cmorl_cyborg/configs/paper/fair_compare_ablation/stage2_adaptive_fixed_fair_seed_0019.yaml`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/configs/paper/fair_compare_ablation/stage2_adaptive_fixed_fair_seed_0019.yaml)
  - [`CybORG_plus_plus/cmorl_cyborg/configs/paper/fair_compare_ablation/stage2_crowding_dynamic_fair_seed_0007.yaml`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/configs/paper/fair_compare_ablation/stage2_crowding_dynamic_fair_seed_0007.yaml)
  - [`CybORG_plus_plus/cmorl_cyborg/configs/paper/fair_compare_ablation/stage2_crowding_dynamic_fair_seed_0011.yaml`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/configs/paper/fair_compare_ablation/stage2_crowding_dynamic_fair_seed_0011.yaml)
  - [`CybORG_plus_plus/cmorl_cyborg/configs/paper/fair_compare_ablation/stage2_crowding_dynamic_fair_seed_0019.yaml`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/configs/paper/fair_compare_ablation/stage2_crowding_dynamic_fair_seed_0019.yaml)
- 两条自动 runner：
  - [`CybORG_plus_plus/cmorl_cyborg/stage2_ablation_variant_runner.py`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/stage2_ablation_variant_runner.py)
  - 当前状态：
    - [`CybORG_plus_plus/cmorl_cyborg/outputs/fair_compare_adaptive_fixed_runner/status.json`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/fair_compare_adaptive_fixed_runner/status.json)
    - [`CybORG_plus_plus/cmorl_cyborg/outputs/fair_compare_crowding_dynamic_runner/status.json`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/fair_compare_crowding_dynamic_runner/status.json)
- 统一 2×2 汇总脚本：
  - [`CybORG_plus_plus/cmorl_cyborg/adacs_dcs_ablation_compare.py`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/adacs_dcs_ablation_compare.py)
- 核心输出目录：
  - [`CybORG_plus_plus/cmorl_cyborg/outputs/adacs_dcs_ablation`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/adacs_dcs_ablation)
  - 图：
    - [`CybORG_plus_plus/cmorl_cyborg/outputs/adacs_dcs_ablation/adacs_dcs_ablation_set_quality.png`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/adacs_dcs_ablation/adacs_dcs_ablation_set_quality.png)
    - [`CybORG_plus_plus/cmorl_cyborg/outputs/adacs_dcs_ablation/adacs_dcs_ablation_deployment.png`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/adacs_dcs_ablation/adacs_dcs_ablation_deployment.png)
    - [`CybORG_plus_plus/cmorl_cyborg/outputs/adacs_dcs_ablation/adacs_dcs_ablation_tight_feasible.png`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/adacs_dcs_ablation/adacs_dcs_ablation_tight_feasible.png)
  - 表：
    - [`CybORG_plus_plus/cmorl_cyborg/outputs/adacs_dcs_ablation/adacs_dcs_ablation_set_quality.csv`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/adacs_dcs_ablation/adacs_dcs_ablation_set_quality.csv)
    - [`CybORG_plus_plus/cmorl_cyborg/outputs/adacs_dcs_ablation/adacs_dcs_ablation_deployment.csv`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/adacs_dcs_ablation/adacs_dcs_ablation_deployment.csv)
    - [`CybORG_plus_plus/cmorl_cyborg/outputs/adacs_dcs_ablation/adacs_dcs_ablation_tight_feasible.csv`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/adacs_dcs_ablation/adacs_dcs_ablation_tight_feasible.csv)
    - [`CybORG_plus_plus/cmorl_cyborg/outputs/adacs_dcs_ablation/adacs_dcs_ablation_summary.json`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/adacs_dcs_ablation/adacs_dcs_ablation_summary.json)

补充说明：

- `tight selected-policy` 和 `tight feasible-set` 对比使用的是 matched `fair_compare` 四角：
  - `Original Stage2`
  - `AdaCS Only`
  - `DCS Only`
  - `AdaCS-DCS Full`
- `set-value` 这一栏的 `AdaCS-DCS Full` 仍沿用了正式 `ours_stage2` buffer 路径，而不是旧的 `ours_stage2_fair` buffer。
- 原因是旧 `ours_stage2_fair` buffer 里挂着已经删除的 checkpoint 路径，会在 `compare_suite` 的 semantic metrics 阶段报错。
- 这和前面 `Original Stage2` matched compare 用的 workaround 是同一个问题，因此这里需要在文档里明确记账，避免以后误以为四角 set-value 完全同源。

1. `Set value` 层

- 四角结果：
  - `Original Stage2`：
    - `HV = 2075510.21 ± 41654.97`
    - `EU = -179.97 ± 8.95`
    - `coverage = 0.2317 ± 0.0540`
    - `unique policies = 3.33 ± 0.47`
    - `Pareto count = 14.67 ± 1.25`
    - `sparsity = 24255.42 ± 7158.34`
  - `AdaCS Only`：
    - `HV = 2064713.77 ± 68106.71`
    - `EU = -176.999 ± 4.95`
    - `coverage = 0.2652 ± 0.0657`
    - `unique policies = 3.67 ± 0.47`
    - `Pareto count = 14.33 ± 2.05`
    - `sparsity = 24946.58 ± 4710.91`
  - `DCS Only`：
    - `HV = 2048336.80 ± 106484.44`
    - `EU = -172.859 ± 6.91`
    - `coverage = 0.2874 ± 0.0913`
    - `unique policies = 3.67 ± 0.47`
    - `Pareto count = 13.67 ± 2.87`
    - `sparsity = 25311.30 ± 7407.54`
  - `AdaCS-DCS Full`：
    - `HV = 2055289.16 ± 151699.96`
    - `EU = -175.402 ± 2.89`
    - `coverage = 0.2833 ± 0.0419`
    - `unique policies = 3.67 ± 0.47`
    - `Pareto count = 13.00 ± 0.82`
    - `sparsity = 42087.12 ± 11909.79`
- 当前最值得记住的 set-level 结论：
  - `AdaCS` 单独打开后，相比 `Original Stage2`：
    - `EU` 提升约 `+2.97`
    - `coverage` 提升约 `+0.033`
    - `unique policies` 提升约 `+0.33`
    - 但 `HV` 略降约 `-10.8k`
  - `DCS` 单独打开后，相比 `Original Stage2`：
    - `EU` 提升约 `+7.11`
    - `coverage` 提升约 `+0.0557`
    - 但 `HV` 降约 `-27.2k`
    - `Pareto count` 也降 `-1.0`
  - `AdaCS-DCS Full` 相比 `Original Stage2`：
    - `EU` 提升约 `+4.57`
    - `coverage` 提升约 `+0.0515`
    - `sparsity` 提升约 `+17831.69`
    - 但 `HV` 仍低约 `-20.2k`
    - `Pareto count` 低约 `-1.67`
- 因此 set-value 层更准确的机制解释应是：
  - `AdaCS` 主要带来：
    - 更好的 coverage
    - 更好的平均效用
    - 略更多样的最终策略分配
  - `DCS` 主要带来：
    - 更强的效用改善
    - 更强的 coverage 改善
    - 但会牺牲一些 `HV` 和 Pareto 点数
  - 二者组合后：
    - 最大的额外收益体现在 `front spread / sparsity`
    - 但并没有在 `HV` 上超过 `Original Stage2`
  - 所以不能把 `AdaCS-DCS` 写成：
    - “在 set value 的所有维度都更好”
  - 更稳的表述应是：
    - 它改善了 `EU + coverage + front spread`
    - 但 `HV` 仍存在 trade-off

2. `Selected-policy under tight constraints` 层

- 四角结果：
  - `Original Stage2`：
    - `security = -603.48`
    - `business = -121.52`
    - `cost = -22.67`
    - `feasible_rate = 0.198`
    - `mean_violation = 7.375`
  - `AdaCS Only`：
    - `security = -604.81`
    - `business = -121.21`
    - `cost = -22.71`
    - `feasible_rate = 0.173`
    - `mean_violation = 7.576`
  - `DCS Only`：
    - `security = -560.01`
    - `business = -121.38`
    - `cost = -23.85`
    - `feasible_rate = 0.026`
    - `mean_violation = 7.759`
  - `AdaCS-DCS Full`：
    - `security = -549.80`
    - `business = -118.16`
    - `cost = -23.12`
    - `feasible_rate = 0.142`
    - `mean_violation = 5.776`
- 这层最重要的结论是：
  - `AdaCS-DCS Full` 在 selected-policy 层最强的点是：
    - 最好的 `security return`
    - 最好的 `business return`
    - 最低的 `mean violation`
    - 最低的 `critical impact count`
  - `Original Stage2` 在 selected-policy 层最强的点是：
    - 最高的 `feasible_rate`
    - 最好的 `cost return`
    - 最低的 `high_disruption_action_rate`
  - `DCS Only` 虽然把 `security return` 拉高了很多，但：
    - `feasible_rate` 几乎掉到 `0.026`
    - `cost` 也最差
    - 所以它不能单独承担 deployment 主论点
  - `AdaCS Only` 在 selected-policy 层没有形成特别强的独立优势：
    - 相比 `Original Stage2`，主要只是把 `business` 微幅拉好
    - 但 `feasible_rate` 和 `mean_violation` 没有改善
- 因此 deployment 层可以更稳地写成：
  - `AdaCS-DCS Full` 更像高效用型部署策略
  - `Original Stage2` 更像保守可部署型策略
  - `DCS` 的主要风险是：
    - 如果单独使用，会让 deployment feasibility 显著下滑

3. `Reevaluated tight feasible set` 层

- 四角结果：
  - `Original Stage2`：
    - `feasible count = 0.667 ± 0.471`
    - `feasible ratio = 0.0465 ± 0.0334`
    - `runs with feasible candidate = 2 / 3`
    - `closest margin = +0.2805 ± 1.6128`
  - `AdaCS Only`：
    - `feasible count = 0.333 ± 0.471`
    - `feasible ratio = 0.0278 ± 0.0393`
    - `runs with feasible candidate = 1 / 3`
    - `best feasible security = -769.10`
    - `closest margin = -0.6962 ± 1.8120`
  - `DCS Only`：
    - `feasible count = 0`
    - `feasible ratio = 0`
    - `runs with feasible candidate = 0 / 3`
    - `closest margin = -1.1328 ± 0.6005`
  - `AdaCS-DCS Full`：
    - `feasible count = 0`
    - `feasible ratio = 0`
    - `runs with feasible candidate = 0 / 3`
    - `closest margin = -1.1563 ± 1.0744`
- 这层现在非常关键，因为它清楚回答了：
  - `AdaCS` 单独带来了什么
  - `DCS` 单独带来了什么
- 更准确的结论是：
  - `AdaCS` 单独打开后，确实对 strict-feasible retention 有正向帮助：
    - 从 `0` 拉到 `1 / 3` 个 seed 有真实可行候选
    - 且那一个可行点的 `security return` 还不错
  - `DCS` 单独打开后，对 strict-feasible retention 没有帮助：
    - 仍然是 `0 / 3`
  - `AdaCS-DCS Full` 在 tight reevaluation 下也仍然是 `0 / 3`
  - 因此当前不能把 `DCS` 写成：
    - 会改善 strict-feasible candidate retention
  - 更不能把 `AdaCS-DCS Full` 写成：
    - 在 strict-feasible set 上稳定优于 `Original Stage2`

4. 当前最稳妥的机制结论

- `AdaCS` 的独立贡献目前比较清楚：
  - 改善 `coverage`
  - 改善 `EU`
  - 略增策略分配多样性
  - 对 tight feasible retention 有一定正向帮助
- `DCS` 的独立贡献也比较清楚，但需要带 trade-off 一起写：
  - 改善 `EU`
  - 改善 `coverage`
  - 但会明显伤害 tight deployment feasibility
  - 且对 strict-feasible candidate retention 没有单独帮助
- `AdaCS-DCS Full` 的组合效果不是简单线性叠加：
  - 它在 `sparsity / front spread` 上最强
  - 在 selected-policy utility 上也最强
  - 但没有在 `HV` 和 strict-feasible candidate retention 上形成全面最优
- 所以 `A-101` 现在已经可以回答“各模块各自带来了什么”，但论文主文的 claim 仍需收敛到：
  - `AdaCS-DCS` improves utility, coverage, and front diversity.
  - `AdaCS` contributes part of the coverage / feasibility-retention gain.
  - `DCS` contributes part of the utility / coverage gain, but introduces a tighter-feasibility trade-off.
- 当前不建议把 `AdaCS-DCS` 写成：
  - 对原始 `crowding + fixed beta` 的“全面支配”
  - 或在 `strict-feasible set quality` 上“稳定更优”

## P0 必须先做的改进

### 1. 先固化 `fair_compare` 作为 `ours` vs `no_constraint_stage2` 的公平口径

- 当前需要正式固定的规则是：
  - `ours_stage2` vs `weighted_sum` 等 broad baselines：继续用主文 Table B
  - `ours_stage2` vs `no_constraint_stage2`：优先引用 matched `fair_compare`
- 这条规则应同时写进：
  - `todo.md`
  - `paper/main.tex`
  - `ARTIFACT_README.md`
  - `OPEN_SCIENCE_APPENDIX.md`
- 推荐表述：
  - `Table B` is the broad deployment comparison table.
  - The constrained vs unconstrained Stage-2 comparison should be interpreted through the locked fair-compare line, where only `extension_mode` differs.

### 2. 修 Figure D 的口径，不要继续直接把它当成“已解决问题”

- 当前主文使用的是：
  - [`CybORG_plus_plus/paper/images/tight_feasible_set_quality.png`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/paper/images/tight_feasible_set_quality.png)
- 这个图对应的是旧的 fair-compare tight line，`ours_stage2` 在前两个面板里是 `0`。
- 后续已经补做过更细的检查：
  - reevaluated baseline 仍然是 `0`
  - `tightplus` 版本有改善
  - `ultratight` 版本失败
- 目前最重要的结论是：
  - `tight constraints` 依旧是当前论文最弱的一块
  - 不能在主文里把这一块写成“我们已经明显胜出”

建议动作：

- 主文保守方案：
  - 继续把 Figure D 当 stress test，用来界定 claim 边界
  - 但需要更明确写出它不是主胜点
- 更稳的论文方案：
  - 把当前 Figure D 降到 appendix
  - 主文只保留一句 tight-constraint limitation 说明
- 如果想保留在主文：
  - 至少补一句，说明它来自 locked fair-compare tight line
  - 并明确指出这部分结论是 limitation，不是 headline claim

### 3. 把 appendix 中仍然是占位符的实验细节补齐

- 当前 [`CybORG_plus_plus/paper/main.tex`](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/paper/main.tex) 里还有两处明显的 placeholder：
  - `Provide reward coefficients, constraint thresholds, scenario details, and training hyperparameters.`
  - `Provide extra tables, sensitivity analyses, and extended attacker-setting results.`
- 这会直接削弱实验部分的可信度和可复现性。

至少需要补上的内容：

- reward coefficients
- loose / tight thresholds
- scenario / red-policy setting
- seeds
- preference grid
- training budgets
- evaluation episodes
- 5-seed 扩展到底覆盖了哪些方法

### 4. 下调 abstract 里的 tight-constraint 强 claim

- 当前 abstract 里还有一句：
  - `stronger feasible deployment choices under strict operational constraints`
- 这句话和当前 Figure D、attacker-shift 的证据并不完全一致。

建议改成更稳的口径，例如：

- stronger candidate-set quality
- broader preference coverage
- competitive constrained deployment behavior
- with strict-constraint feasible-set quality treated as a stress-test limitation

### 5. 把 Table A / Table B 改成更像论文，而不是机器导表

- 当前导出的表格还保留了：
  - `method_name`
  - `display_name`
- 这对论文阅读体验不够好。

建议动作：

- 表中只保留 `display_name`
- 指标列改成短标题 + 箭头
- 最佳值加粗
- 在 caption 或 table note 里显式写出：
  - key methods are 5-seed
  - remaining baselines are 3-seed

## P1 值得做，但不是必须的新实验 / 结果优化

### 6. 如果还要补实验，只做一条：`tightplus + refinement tail`

- 这是目前唯一值得继续的结果优化方向。
- 现有证据是：
  - baseline tight feasible set: `ours_stage2 = 0`
  - `tightplus` 版本已经把平均 feasible candidate count 拉到 `0.6667`
  - `seed_0019` 已经成功过线
  - `seed_0011` 很接近过线
  - `ultratight` 反而更差

当前最有价值的方向不是继续“全局加压”，而是：

- 保留 `tightplus` 级别参数
- 加一个 `feasibility refinement tail`
- 专门修 `cost` 维度
- 重点瞄准：
  - `seed_0011`
  - `seed_0007`

原因：

- `seed_0011` 的 tightplus 最接近候选 `margin` 约为 `-0.965`
- `seed_0007` 更难，但仍可针对 `cost` 维度单独修
- `ultratight` 说明“继续提高 barrier / tolerance”不是好方向

### 7. 如果不继续新实验，就把 tightplus / ultratight 结果作为 appendix 经验结论

这个方向也很值，因为它能把之前做过的实验变成有用结论，而不是散在目录里的结果：

- `tightplus` 说明：
  - tighter constraint-aware expansion 有机会救回 tight-feasible candidates
- `ultratight` 说明：
  - 盲目加强全局约束会破坏 frontier，未必能救 tight-feasible set

这可以整理成一个 appendix 小节，例如：

- `Constraint-Pressure Sensitivity for Tight Feasible Set Quality`

## 当前不建议继续做的事

### 8. 不建议再加新的大 baseline

- 当前主文方法集合已经够了。
- 不建议现在再把：
  - `AdaCS`
  - `DCS`
  - 其他 exploratory 线
  强行并入主文。

原因：

- 会把实验结构重新打散
- 成本高
- 对主文主线帮助不大

### 9. 不建议继续沿 `ultratight` 方向加压

- 当前结果已经说明：
  - `ultratight` 对 `seed_0007` 和 `seed_0011` 没有帮助
  - 比 `tightplus` 更差

因此：

- 不建议再继续做更高 barrier / 更紧 tolerance 的同类实验

### 10. 不建议再扩 attacker-shift

- 当前 attacker-shift 已足够说明边界：
  - 所有方法在 held-out `meander` 下都退化
- 这已经能支撑 appendix limitation。
- 再扩更多 red policies，当前收益不高。

## 推荐执行顺序

1. 先固化 `fair_compare` 作为 `ours` vs `no_constraint_stage2` 的公平口径。
2. 再补 appendix 中真实的实验细节，去掉 placeholder。
3. 立即修 Figure D 的论文口径。
4. 清理 Table A / Table B 的表格格式和 mixed-seed 说明。
5. 同步下调 abstract 中关于 strict constraints 的表述。
6. 如果还有算力，再做 `tightplus + refinement tail`。
7. 如果不再跑新实验，就把 tightplus / ultratight 写成 appendix 的负结果与敏感性分析。

## 最终建议

- 结论一：
  - 现在的实验部分已经足够支撑一版可投初稿，不需要再大规模加实验。
- 结论二：
  - 当前最需要修的不是“实验不够多”，而是“tight-constraint 这块的叙事和证据还不够整齐”。
- 结论三：
  - 如果还要优化实验结果，只建议继续做一条非常聚焦的补强：
    - `tightplus + feasibility refinement tail`
  - 不建议再继续 `ultratight` 式的全局加压。
