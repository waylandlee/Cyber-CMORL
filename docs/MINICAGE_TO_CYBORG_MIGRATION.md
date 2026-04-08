# MiniCAGE 到正式 CybORG 迁移清单

## 2026-04-08 状态说明

这份文档现在应理解为“迁移设计文档 + 历史边界说明”，而不是“尚未开始的计划”。

当前项目分工已经比较明确：

- [cmorl_minicage](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage)
  负责方法迁移验证、ablation、机制解释和 supplementary 素材
- [cmorl_cyborg](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg)
  负责正式环境 `3-seed` 结果、主表 B、公平比较与当前论文主结论

因此，后续写作不应把这份文档理解成“还要不要迁移”，而应理解成“这次迁移为什么这样做、哪些资产从 MiniCAGE 继承而来、哪些结论必须在 CybORG 中重新验证”。

## 目标

本清单用于把当前 [cmorl_minicage](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage) 中已经稳定的两阶段 C-MORL 实验链路迁移到正式 `CybORG` 环境。

迁移目标不是“直接复用 MiniCAGE 的数值结果”，而是：

- 保留当前已经稳定的算法主干
- 只替换环境包装与 reward / semantic metrics 适配层
- 在正式 `CybORG` 上重建一套可运行、可调参、可做表 A / 表 B 的统一实验系统

## 当前判断

当前项目已经完成核心迁移链路，并形成了 `cmorl_cyborg` 的正式 `3-seed` 结果。

已经成熟、可直接复用的部分：

- `Stage-1 -> Stage-2 -> evaluate` 主线
- `adaptive selection`
- `dynamic beta scheduling`
- `IPO-style constrained extension`
- `Preference-Conditioned PPO`
- `PCN-lite`
- `Lagrangian-PPO`
- `compare_suite.py`
- `evaluate_constraints.py`
- `export_tables.py`
- 主表 A / 主表 B / appendix 的统一输出 schema

当前仍未完全结束的部分：

- 更大规模 `5-seed formal`
- 更严格的 matched fair ablation
- 把当前结果收敛成论文主叙事

## 迁移原则

迁移时建议遵守以下原则：

1. 不同时做“环境迁移 + reward 重定义 + 算法升级”三件事。
2. 先复用现有算法主干，再重建环境适配层。
3. 先跑 smoke，再做小预算调参，再跑 formal。
4. 所有正式 CybORG 结果都重新计算 shared reference point 和 shared thresholds。

## 可直接复用的文件

以下文件原则上应直接复用，除非 CybORG 状态维度或动作接口逼迫改动：

- [cmorl_minicage/train_stage1.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/train_stage1.py)
- [cmorl_minicage/train_stage2.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/train_stage2.py)
- [cmorl_minicage/algorithms/ppo_vector.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/algorithms/ppo_vector.py)
- [cmorl_minicage/algorithms/ipo.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/algorithms/ipo.py)
- [cmorl_minicage/algorithms/adaptive_selection.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/algorithms/adaptive_selection.py)
- [cmorl_minicage/algorithms/dynamic_beta.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/algorithms/dynamic_beta.py)
- [cmorl_minicage/algorithms/selection.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/algorithms/selection.py)
- [cmorl_minicage/algorithms/assignment.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/algorithms/assignment.py)
- [cmorl_minicage/buffer.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/buffer.py)
- [cmorl_minicage/evaluate_conditioned.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/evaluate_conditioned.py)
- [cmorl_minicage/evaluate_constraints.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/evaluate_constraints.py)
- [cmorl_minicage/compare_suite.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/compare_suite.py)
- [cmorl_minicage/export_tables.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/export_tables.py)
- [cmorl_minicage/train_pref_conditioned_ppo.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/train_pref_conditioned_ppo.py)
- [cmorl_minicage/train_lagrangian_ppo.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/train_lagrangian_ppo.py)
- [cmorl_minicage/train_pcn.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/train_pcn.py)

## 必须新建或重写的文件

以下部分建议为正式 CybORG 单独新建，不要直接在 MiniCAGE wrapper 上硬改：

### 1. 环境包装

建议新增：

- `cmorl_cyborg/env.py`

建议提供：

- `CybORGMORLEnv.reset()`
- `CybORGMORLEnv.step()`
- `_project_reward_terms()`
- `_semantic_step_info()`

最重要的不是接口名字，而是输出要与当前 `MiniCageMORLEnv` 对齐：

- `obs: np.ndarray`
- `reward_vec: [security, business, cost]`
- `done`
- `info["reward_terms"]`
- `info["semantic_info"]`

### 2. CybORG 专用配置

建议新增目录：

- `cmorl_minicage/configs/cyborg/`

第一轮至少需要：

- `stage1_smoke.yaml`
- `stage2_smoke.yaml`
- `evaluate_smoke.yaml`
- `stage1_main.yaml`
- `stage2_main.yaml`
- `evaluate_main_table_a.yaml`
- `evaluate_main_table_b.yaml`

### 3. 语义指标映射

正式 CybORG 里要重新实现以下语义统计：

- `final_compromised_hosts`
- `final_critical_compromised_hosts`
- `critical_impact_count`
- `recovered_hosts`
- `analyse_count`
- `remove_count`
- `restore_count`
- `high_disruption_action_rate`

这部分建议单独做成 helper，避免全塞进 env wrapper：

- `cmorl_cyborg/semantics.py`

### 4. 当前正式环境口径草案

当前 `cmorl_cyborg` 已切换为 scenario-profile 驱动。代码不再把 `Scenario2` 写死在
`reward.py` / `semantics.py` 中，而是优先从 `env.scenario_profile` 或
`env.scenario_name` 解析 YAML profile。内置 profile 目录为：

- [cmorl_cyborg/profiles](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/profiles)

目前仓库内置的是 `Scenario2.yaml`，因此当前正式实验口径仍以 `Scenario2` 为主，但
后续新增 scenario 时原则上只需新增 profile 文件，而不再需要改核心奖励与语义代码。

当前资产分层为：

- `mission-critical`
  - `Op_Server0`
- `operational`
  - `Op_Host0`
  - `Op_Host1`
  - `Op_Host2`
- `enterprise-support`
  - `Enterprise0`
  - `Enterprise1`
  - `Enterprise2`
  - `Defender`
- `user-endpoint`
  - `User0` 到 `User4`

其中：

- `critical host`
  - 仅指 mission-critical 资产，即 `Op_Server0`
- `critical impact`
  - 指某一步中新出现的 mission-critical 资产失陷
- `recovered_hosts`
  - 指上一步存在 Red session、这一步不再存在 Red session 的主机
- `high_disruption_action`
  - 指 `Remove`、`Restore` 以及所有 `Decoy*` 动作

当前 reward 三目标写法为：

- `security`
  - `raw CybORG blue reward`
  - 减去当前所有 Red foothold 的加权暴露
  - 再减去新发生的 `critical impact`
  - 再加上恢复主机的 bonus
- `business`
  - 当前受失陷影响主机的加权业务暴露
  - 加上高扰动 Blue 动作在目标主机上的业务扰动
  - 加上新发生 `critical impact` 的额外业务惩罚
- `cost`
  - 仅表示 Blue 动作执行成本
  - `Sleep / Monitor / Analyse / Remove / Restore / Decoy*` 使用固定成本表

这套口径的设计目标是：

1. `security / business / cost` 三目标都保持“越大越好”的统一方向；
2. `security` 主要表达对 Red foothold 和 mission-critical 失陷的抑制；
3. `business` 主要表达 Operational 资产受损和高扰动防御动作带来的业务影响；
4. `cost` 单独表达运维与响应动作成本，避免与 `business` 完全混在一起。

需要注意：

- 当前代码已经不是 `Scenario2-only`，而是 `scenario-profile driven`。
- 但仓库当前只内置了 `Scenario2` profile，因此现有实验结果仍然是 `Scenario2` 结果。
- 如果后续切换正式 CybORG 其它 scenario，必须新增对应 profile，而不是沿用 `Scenario2` 权重。
- 当前权重与动作成本表是“场景语义驱动 + 工程可解释”的工作定义，后续正式调参仍需要做分布校准。

## 迁移时优先保留的超参

这些更像“算法结构偏好”，迁移到正式 CybORG 时建议先保留：

- `selection.mode`
- `selection.score_weights` 的相对方向
- `selection.coverage_mode`
- `selection.keep_extremes`
- `ipo.beta_mode`
- `ipo.schedule_weights` 的相对关系
- `extension_rounds`
- `num_extension_policies`

换句话说，先保留“怎么选点、怎么调 beta”的思路。

## 迁移时优先重调的超参

这些强依赖环境尺度、episode 长度和 reward 范围，迁移后应优先重调：

- `barrier_coef`
- `beta`
- `beta_min`
- `beta_max`
- `constraint_tolerance`
- `constrained_updates`
- `total_timesteps_per_update`
- `learning_rate`
- `entropy_coef`
- `hidden_size`
- `Stage-1 / Stage-2` 预算分配

## 正式迁移前的接口检查项

在开始训练前，先逐项确认以下事实：

1. `obs_dim` 已知且稳定。
2. `action_dim` 已知且 Blue action 可离散索引化。
3. 每步都能得到 reward 所需的中间状态或事件日志。
4. 关键资产、关键主机、业务优先级在正式环境里可识别。
5. `security / business / cost` 三目标都能做成“越大越好”的统一口径。
6. 能够复现 `info["semantic_info"]` 这类评估依赖信息。

如果其中任一项不成立，应该先补环境适配，不要急着跑 Stage-1。

## 迁移实施顺序

建议按以下顺序执行：

### Phase 1. 跑通环境适配

- 新建 `CybORGMORLEnv`
- 只做随机动作 rollout
- 确认 `obs / reward_vec / done / info` 全部正常

验收标准：

- 单步和多步 rollout 都不报错
- `reward_vec.shape[-1] == 3`
- `semantic_info` 字段存在

### Phase 2. 跑通 Stage-1 smoke

- 用极小预算跑 `Stage-1`
- 确认能导出：
  - `solution_buffer.json`
  - `stage1_summary.json`
  - `pareto_front_stage1.json`

验收标准：

- 至少产生 2 个不同 preference policy
- 没有 NaN / Inf
- 能做 nondominated filtering

### Phase 3. 跑通 Stage-2 smoke

- 接上 `train_stage2.py`
- 先用最保守配置
- 确认能导出：
  - `pareto_front_stage2.json`
  - `stage2_summary.json`
  - `method_diagnostics.json`

验收标准：

- 至少能生成 1 个 `best_feasible` 扩展策略
- 不出现全路径 `generated = 0`

### Phase 4. 跑通评估与导表

- 跑 `evaluate.py`
- 跑 `evaluate_constraints.py`
- 跑 `compare_suite.py`
- 跑 `export_tables.py`

验收标准：

- 能生成主表 A 的 `metrics.json` 兼容输出
- 能生成主表 B 的 `constraint_metrics.json`
- 能导出 CSV / JSON / TEX

### Phase 5. 小预算调参

- 先用 1 个 dev seed
- 再用 1 个 holdout seed
- 最后 3-seed

不建议一开始直接上 5-seed formal。

## 第一轮 smoke 命令建议

下面这组命令是正式 CybORG 迁移后的第一轮最小闭环目标。

```bash
conda run -n cc4 python -m cmorl_cyborg.rollout_smoke --config cmorl_minicage/configs/cyborg/stage1_smoke.yaml
conda run -n cc4 python -m cmorl_minicage.train_stage1 --config cmorl_minicage/configs/cyborg/stage1_smoke.yaml
conda run -n cc4 python -m cmorl_minicage.train_stage2 --config cmorl_minicage/configs/cyborg/stage2_smoke.yaml --stage1-buffer <stage1_solution_buffer>
conda run -n cc4 python -m cmorl_minicage.evaluate --config cmorl_minicage/configs/cyborg/evaluate_smoke.yaml --buffer-path <solution_buffer>
conda run -n cc4 python -m cmorl_minicage.evaluate_constraints --config cmorl_minicage/configs/paper/evaluate_main_table_b.yaml --input-path <solution_buffer>
```

## 第一轮 smoke 成功的定义

只有同时满足以下条件，才建议进入正式 CybORG 调参：

- 环境 wrapper 稳定
- Stage-1 能形成非空 Pareto front
- Stage-2 能至少生成 1 个可行扩展点
- 主表 A / B evaluator 均能跑通
- reward 与 semantic metrics 没有明显口径错误

## 当前建议的下一步

如果要正式开启迁移，建议按下面顺序做：

1. 新建 `cmorl_cyborg/env.py`
2. 补 `cmorl_cyborg/semantics.py`
3. 新建 `configs/cyborg/stage1_smoke.yaml`
4. 跑随机 rollout smoke
5. 跑 Stage-1 smoke
6. 跑 Stage-2 smoke
7. 通过后再开始正式环境调参
