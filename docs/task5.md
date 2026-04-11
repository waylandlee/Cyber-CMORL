# Task 5 — 在主线 B 的基础上推进主线 A（CVaR Conservative Branch）

## 任务定位

本任务不是回退到旧的单前沿 Stage-2，也不是继续把当前 `mainline B / Dual-Archive` 当成主方法硬磨。

本任务的目标是：

> **保留 Task 3 / Task 4 已经建立起来的 dual-archive 训练—评估—导表—选择语义框架，把 `mainline A` 作为新的 conservative branch 核心接入 `A_cons`。**

也就是说，下一阶段的目标形态不是：

- `single-archive + CVaR`，也不是
- `继续调当前 B 的 conservative operator`

而是：

- **`Dual-Archive + CVaR Conservative Branch`**

当前研发判断依据如下：

- B-fix 之后，工程与诊断层面已经足够干净，可被公平测试。
- 但在 smoke 与 fair-budget `seed_0007` 正式实验里：
  - `cons_attempted_children > 0`
  - `cons_successful_children = 0`
  - `cons_routed_children = 0`
  - `strict_candidate_count = 0`
  - `strict_hit_rate = 0`
- 因此，当前最主要的问题已经不是 annotation / gate / route 噪音，而是：
  - **conservative branch 本体没有形成有效的 child 生成能力。**

这说明继续在 B 上做小修补的边际收益已经变低，而把 conservative branch 从 mean-feasibility 升级成 risk-aware feasibility，是更合理的下一步。

---

## 本任务的关键决策

### 决策 1：不回退单前沿

必须保留以下 Task 3 / 4 已完成资产：

- `A_cons / A_uc / union_front` 的结构
- strict / hybrid selector 语义
- archive-aware comparable evaluation
- compare / export pipeline
- 当前 `uc` 分支与其 operator
- 现有 diagnostics 字段与 buffer 输出格式

### 决策 2：A 只先接入 `A_cons`

第一版 `mainline A` 不做“全局 Stage-2 风险化”，只替换当前失效的 conservative branch：

- `A_uc`：保持当前 `AdaCS-DCS` / utility-coverage 分支不变
- `A_cons`：从当前 conservative operator 升级为 **CVaR conservative branch**

### 决策 3：先做 CVaR，不做 OCE

原因：

- CVaR 更容易接到当前 PPO / IPO 风格训练器上
- 更适合先验证“坏尾部是不是 conservative branch 失效的主因”
- 可以更快在现有 CybORG 正式链路里跑 comparable 实验

OCE 留作下一阶段可选升级，不作为本任务的必做项。

---

## 任务目标

本任务要回答的核心问题是：

> **如果把 `A_cons` 从 mean-feasibility / fixed-beta 风格，升级成 CVaR-aware conservative branch，它能否生成 strict / near-strict conservative child，并建立真实可用的 strict candidate pool？**

具体目标拆成三层：

### G1. 训练层目标

让 `A_cons` 分支能够真正生成 child，而不是只尝试但不产出：

- `cons_attempted_children > 0`
- `cons_successful_children > 0`
- 至少部分 Stage-2 child 被路由到 `A_cons`

### G2. strict 语义目标

让 strict pool 不再长期为 0：

- `strict_candidate_count > 0`
- `strict_hit_rate > 0`
- `hybrid_fallback_rate < 1.0`

### G3. 风险语义目标

即便 set-level 不全面反超，也至少应在 conservative 侧看到更稳的部署语义：

- `final_critical_compromised_hosts` 不应恶化
- `critical_impact_count` 不应恶化
- `mean_violation` 不应恶化
- `A_cons` 中的 child 应比当前 B-fix 更接近 strict / near-strict 可部署候选

---

## 当前代码与改动原则

优先修改共享实现层，而不是单独在 `cmorl_cyborg/` 里复制逻辑。

### 共享主实现层（必须优先改）

- `cmorl_minicage/train_stage2.py`
- `cmorl_minicage/config.py`
- `cmorl_minicage/buffer.py`
- `cmorl_minicage/evaluate.py`
- `cmorl_minicage/select_policy.py`
- `cmorl_minicage/algorithms/assignment.py`
- **本地 dual-archive 相关实现文件**
  - 优先查找并复用当前 Task 3 / 4 已引入的 dual-archive 管理模块
  - 若本地为 `cmorl_minicage/algorithms/dual_archive.py`，就在该文件继续扩展
  - 若路径不同，以本地真实文件为准，不要新造平行版本

### CybORG 层（只保留透传和协议差异）

- `cmorl_cyborg/train_stage2.py`
- `cmorl_cyborg/configs/paper/...`
- `cmorl_cyborg` 下 formal compare / export 路径

原则：

- 方法逻辑改在共享层
- 正式验证仍以 `cmorl_cyborg` 为准
- 不要在 `cmorl_cyborg` 再写一份重复的 CVaR 分支逻辑

---

## 方法设计要求

## A-001 把 conservative branch 明确升级为 CVaR branch

### 目标

在 dual-archive 框架里，把当前 `A_cons` 的扩展逻辑替换为 risk-aware conservative branch。

### 设计要求

1. `A_uc` 保持现有逻辑不变。
2. `A_cons` 使用新的 CVaR-aware conservative update。
3. risk-aware 逻辑只先用于 `A_cons`，不要一上来推广到 `A_uc`。
4. 保留 current strict / near 语义、archive route 和 selector 语义，不要推翻 Task 4 的选择框架。

### 禁止事项

- 禁止回退成单 archive 训练
- 禁止移除 strict / hybrid selector
- 禁止为了接入 CVaR 而删除 `A_cons / A_uc / union_front`

---

## A-002 定义 conservative branch 的风险对象

第一版 CVaR branch 必须至少支持对以下风险量之一进行 conservative 约束：

### 必选项

- `final_critical_compromised_hosts`

### 强烈建议同时纳入

- `critical_impact_count`
- `mean_violation`

### 可选项

- `high_disruption_action_rate`
- 业务 / 成本相关 conservative 语义

### 要求

不要把 CVaR 只定义在原始 reward vector 上；优先围绕当前项目中已经明确进入 deployment 语义的指标构造 conservative risk 目标。

也就是说，第一版 A 的问题定义应该更像：

> conservative branch 优先压低关键资产最终失陷风险和 violation tail risk

而不是：

> 只在原 reward scalar 上机械套一个 CVaR

---

## A-003 先做 episode-level / batch-level 风险统计接口

在接入 CVaR 之前，必须先补一层风险统计支持。

### 目标

让 conservative branch 能拿到 episode-level 或 batch-level 的风险样本，而不是只看均值。

### 建议实现

在 Stage-2 训练过程中，为 `A_cons` 分支额外记录：

- 每个 episode 的 `final_critical_compromised_hosts`
- 每个 episode 的 `critical_impact_count`
- 每个 episode 的 violation / margin
- 必要时保留 per-batch risk sample summary

### 注意

- 不需要把全量轨迹永久存盘
- 但至少要在训练 update 时能估计 conservative branch 的 tail statistics
- 这一步是 CVaR 的前置条件

---

## A-004 设计第一版 CVaR conservative objective

### 第一版建议形式

从简单可用出发，优先做以下之一：

1. **penalty 版**
   - PPO / IPO 主目标不变
   - 对 `A_cons` 分支额外加 CVaR 风险 penalty

2. **constraint 版**
   - `A_cons` 分支使用“主目标 + CVaR 风险约束”

优先建议：

- **先做 penalty 版**，因为更容易接到当前 shared trainer 里
- 但代码结构要保留以后升级到真正 constraint 版的接口

### 设计要求

- 清晰区分 `mean metric` 和 `tail risk metric`
- 清晰区分 `training-time risk estimate` 和 `evaluation-time strict selector semantics`
- 不要让 CVaR 分支改坏 `A_uc` 当前行为

### 命名要求

新增配置与日志字段时统一使用：

- `cons_risk_mode = cvar`
- `cvar_alpha`
- `cvar_metric`
- `cvar_penalty_coef`
- `cons_risk_stats`

---

## A-005 配置层新增 conservative risk 配置

在 `Stage2Config` 中补入 conservative branch 风险配置。

### 必要字段

- `archive_mode`
- `cons_operator_mode`
- `cons_risk_mode`
- `cvar_alpha`
- `cvar_metric`
- `cvar_penalty_coef`
- `cons_risk_eval_batches` 或等价字段

### 要求

1. 必须能显式切换：
   - 旧版 conservative branch
   - 新版 CVaR conservative branch
2. 必须允许 smoke / fair / formal 配置独立设置
3. 默认值要保守，不要一上来给太极端的风险权重

---

## A-006 保留并增强 B-fix 的 diagnostics

CVaR 接入后，原有 diagnostics 不能丢，反而要更强。

### 必须继续输出

- `cons_attempted_children`
- `cons_successful_children`
- `cons_routed_children`
- `cons_rejected_by_cost_gate`
- `cons_rejected_by_feasibility`

### 新增风险诊断

- `cons_risk_mode`
- `cons_cvar_alpha`
- `cons_cvar_metric`
- `cons_cvar_estimate_mean`
- `cons_cvar_estimate_tail`
- `cons_rejected_by_risk_gate`
- `cons_risk_penalty_mean`

### 目标

本任务结束后，必须能区分：

- `cons` 为什么没长出来
- 是因为 feasibility
- 还是因为 risk gate
- 还是训练本体仍没改观

---

## A-007 评估层保持三套语义，不要回退

Task 4 已经把评估语义切成：

- `union`
- `strict`
- `hybrid`

Task 5 必须继续沿用，不允许回退到单一 `metrics.json` + plain SMP 的旧语义。

### 继续要求输出

- `metrics_union.json`
- `metrics_strict.json`
- `metrics_hybrid.json`
- `archive_diagnostics.json`

### 额外要求

在 strict / hybrid 结果旁边，补充 conservative branch 风险指标摘要，至少包括：

- strict candidate 中的 `final_critical_compromised_hosts`
- strict candidate 中的 `critical_impact_count`
- strict candidate 中的 `mean_violation`

---

## A-008 `select_policy.py` 与 assignment 语义继续兼容 dual-archive

不要为 Task 5 重新发明单独的“风险选择脚本”。

而是：

- 在现有 strict / hybrid 语义上，继续让 `select_policy.py` 和 assignment 支持 dual-archive 选择
- 必要时新增 conservative-aware selection mode
- 但不要破坏 Task 4 已经建立起来的选择接口

如果需要新增 selector，命名建议：

- `strict_cons`
- `hybrid_cons`

而不是回到只有 `pareto / records` 的旧 source_set 语义。

---

## 实验计划

## E-001 Smoke：验证 conservative branch 是否终于能长出 child

### 方法组

- `Original Stage2`
- `AdaCS-DCS`
- `B-fix Dual-Archive`
- `Task5 Dual-Archive + CVaR Cons`

### 核心检查项

- `cons_attempted_children`
- `cons_successful_children`
- `cons_routed_children`
- `strict_candidate_count`
- `strict_hit_rate`

### 最低成功标准

至少满足以下两条中的一条：

- `cons_successful_children > 0`
- `strict_candidate_count > 0`

如果 smoke 仍然完全为 0，则先不要进入正式 fair-budget 实验，优先修 conservative objective / risk estimate。

---

## E-002 Fair-budget seed_0007：与当前 B-fix 做正面对比

### 方法组

- `B-fix Dual-Archive`
- `Task5 Dual-Archive + CVaR Cons`

### 关键表

#### Table A

看：
- HV
- EU
- coverage
- Pareto count
- unique assigned policies

#### Table B strict

看：
- `strict_candidate_count`
- `strict_hit_rate`
- feasible rate
- mean violation
- final critical compromised
- critical impact count

#### Table B hybrid

看：
- `hybrid_fallback_rate`
- selected-policy 的 security / business / cost
- final critical compromised
- critical impact count

### 最低成功标准

与当前 B-fix 相比，至少满足下面一条：

1. `strict_candidate_count` 从 0 变成 > 0
2. `strict_hit_rate` 从 0 变成 > 0
3. `cons_successful_children` 从 0 变成 > 0，且至少有一个 routed to `A_cons`

如果三条全部不满足，则说明 A 的第一版接法也未能激活 conservative branch，需要单独复查 CVaR objective / alpha / risk statistic。

---

## E-003 若 smoke 与 seed_0007 都有正向信号，再进入多 seed

只有在前两步出现“cons 终于开始产出”的证据后，再做多 seed。

### 多 seed 关注点

- conservative branch 产出是否稳定
- strict candidate pool 是否稳定非空
- 是否只是单 seed 偶然
- CVaR 是否导致 set-level 结果严重崩坏

---

## 验收标准

### 本任务完成，不要求一步拿到论文最终最优结果

但至少要达到：

1. conservative branch 不再是纯空转
2. strict pool 不再长期为 0
3. diagnostics 能说明 risk-aware branch 是否真的起作用
4. 不破坏 current `A_uc` 和 current Task 4 评估语义

### 本任务失败的判定标准

若以下全部成立，可视为 Task 5 第一版失败：

- smoke 中 `cons_successful_children = 0`
- smoke 中 `strict_candidate_count = 0`
- fair-budget `seed_0007` 中 `cons_successful_children = 0`
- fair-budget `seed_0007` 中 `strict_candidate_count = 0`

这说明即使引入 CVaR conservative branch，也没有让 `A_cons` 站起来，需要重新审视：

- CVaR 风险对象是否定义错
- conservative operator 是否仍然过于弱
- strict protocol 是否仍然与训练目标错位

---

## 禁止事项

- 禁止回退到单 archive / 单前沿
- 禁止删除 strict / hybrid selector
- 禁止为了接入 CVaR 而重写整套 Stage-2 并丢掉 Task 3 / 4 的诊断资产
- 禁止一上来就做 OCE 并增加不必要复杂度
- 禁止在 `cmorl_cyborg` 单独复制一份方法实现

---

## 推荐 Codex 实现顺序

1. 识别并复用当前本地 dual-archive 管理模块
2. 在共享层为 `A_cons` 接入 episode-level / batch-level risk statistics
3. 新增 conservative risk config
4. 先做 penalty 版 CVaR conservative branch
5. 保留 strict / hybrid 评估接口并补风险诊断输出
6. 跑 smoke
7. 若 smoke 有正向信号，再跑 fair-budget `seed_0007`
8. 根据 `cons_successful_children` 与 `strict_candidate_count` 决定是否进入多 seed

---

## 对 Codex 的执行提醒

本任务的目标不是“把 A 写得多漂亮”，而是：

> **在保留 B 已经建立起来的 dual-archive 与评估语义基础上，最低成本验证：risk-aware conservative branch 能不能让 `A_cons` 真正站起来。**

因此，优先级必须是：

- 少改外层结构
- 不破坏 `A_uc`
- 强化 diagnostics
- 尽快得到一个能回答 `cons branch 是否终于生成 child` 的实验结果

---

## Task 5 Execution Log

### Step T5-1: A_cons rollout-based CVaR penalty 实现
- Status: done
- Files changed:
  - `CybORG_plus_plus/cmorl_minicage/train_stage2.py`
  - `CybORG_plus_plus/cmorl_minicage/config.py`
  - `CybORG_plus_plus/cmorl_cyborg/config.py`
  - `CybORG_plus_plus/cmorl_minicage/evaluate.py`
  - `CybORG_plus_plus/cmorl_cyborg/configs/ablation/stage2_dual_archive_cvar_cons.yaml`
  - `CybORG_plus_plus/cmorl_cyborg/configs/paper/fair_compare_dual/stage2_dual_archive_cvar_cons_fair_seed_0007.yaml`
  - `task5.md`
- Result:
  - 在共享 `Stage-2` 实现中，仅对 `A_cons` 分支接入了 rollout-based CVaR penalty，`A_uc` 保持不变。
  - 新增 `cons_risk_mode`、`cvar_alpha`、`cvar_metric`、`cvar_penalty_coef` 配置，默认 `cons_risk_mode="none"`，兼容现有 B-fix Dual-Archive。
  - CVaR v1 固定使用 rollout 内 `final_critical_compromised_hosts` 样本；若 rollout 内某 env 没有结束 episode，则使用该 env 最后一次观测值作为 proxy sample。
  - 新增 conservative risk 诊断字段，写入 `stage2_summary.json`、`method_diagnostics.json`、buffer metadata，并在 `archive_diagnostics.json` 中透出。
  - 顺手修复了 Stage-2 child `checkpoint_path` 的相对路径漂移问题，改为保存绝对路径，避免 dual-archive 语义回放时 anchor 解析到错误仓库根目录。
- Verification:
  - 运行了 `py_compile` 检查修改后的 `train_stage2.py`、`config.py`、`evaluate.py` 与 CybORG wrapper。
  - 在 `cc4` 环境中验证 `_rollout_cvar_penalty([0, 1, 2, 4], alpha=0.25, penalty_coef=0.25)` 可得到 `worst_k=1`、`tail=4.0`、`penalty=1.0`。
  - 验证新增 ablation 配置能正确加载 `cons_risk_mode=cvar`、`cvar_alpha=0.25`、`cvar_metric=final_critical_compromised_hosts`。
- Notes:
  - 这一版没有修改 `IPOTrainer` 目标函数形式，也没有引入 routing-time risk gate；风险只通过 rollout reward penalty 接入。

### Step T5-2: Smoke 验证
- Status: done
- Files changed:
  - `task5.md`
- Result:
  - 完成了最小 smoke 对照：
    - `B-fix Dual-Archive`: `/tmp/t5_bfix_smoke_run/run_25646376/solution_buffer.json`
    - `Task5 Dual-Archive + CVaR Cons`: `/tmp/t5_cvar_smoke_run/run_0e678ae6/solution_buffer.json`
  - smoke 结果显示两组都出现了 `cons_successful_children = 6`，说明 conservative 分支在小预算下并非完全空转。
  - 但两组都仍然是：
    - `cons_routed_children = 0`
    - `strict_candidate_count = 0`
    - `strict_hit_rate = 0`
  - CVaR 组额外记录到了风险估计：
    - `cons_cvar_estimate_tail = 0.9583`
    - `cons_risk_penalty_mean = 0.2396`
    - `cons_risk_rollout_count = 48`
- Verification:
  - smoke 评估输出：
    - `/tmp/t5_bfix_smoke_eval/archive_diagnostics.json`
    - `/tmp/t5_cvar_smoke_eval/archive_diagnostics.json`
  - 检查了两组的 `solution_buffer.json`、`stage2_summary.json`、`method_diagnostics.json`。
- Notes:
  - 这个 smoke 信号是“弱正向”而不是“方法成功”：它只说明 rollout-CVaR 没有把 `A_cons` 训练链路打坏，并不足以说明 strict pool 已经恢复。
  - 按 Task 5 预设规则，由于 smoke 至少满足 `cons_successful_children > 0`，继续执行 fair-budget `seed_0007`。

### Step T5-3: Fair-budget `seed_0007` 正式验证
- Status: done
- Files changed:
  - `task5.md`
- Result:
  - 完成了 `Task5 Dual-Archive + CVaR Cons` 的 fair-budget `seed_0007` 运行：
    - `/home/waylandlee/Cyber-CMORL/cmorl_cyborg/outputs/fair_compare_dual/dual_archive_cvar_cons_stage2_fair/seed_0007/run_8f913fb9/solution_buffer.json`
  - 并与现有 B-fix fair 基线同口径评估对照：
    - B-fix: `/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/fair_compare_dual/b_fix_dual_archive_stage2_fair/seed_0007/run_0810320f/solution_buffer.json`
    - B-fix eval: `/tmp/t5_bfix_fair_eval/metrics.json`
    - CVaR eval: `/tmp/t5_cvar_fair_eval/metrics.json`
  - fair-budget 对照结果如下：
    - B-fix:
      - `cons_attempted_children = 18`
      - `cons_successful_children = 0`
      - `cons_routed_children = 0`
      - `strict_candidate_count = 0`
      - `strict_hit_rate = 0.0`
      - `hybrid_fallback_rate = 1.0`
      - `final_critical_compromised_hosts (hybrid) = 0.7014`
      - `mean_violation (hybrid) = 5.8391`
    - CVaR Cons:
      - `cons_attempted_children = 18`
      - `cons_successful_children = 0`
      - `cons_routed_children = 0`
      - `strict_candidate_count = 0`
      - `strict_hit_rate = 0.0`
      - `hybrid_fallback_rate = 1.0`
      - `final_critical_compromised_hosts (hybrid) = 0.6944`
      - `mean_violation (hybrid) = 5.8391`
      - `cons_cvar_estimate_tail = 1.0`
      - `cons_risk_penalty_mean = 0.25`
      - `cons_risk_rollout_count = 54`
  - 两轮 `round_uc_generated_policy_ids` 与 B-fix 基本一致，`round_cons_generated_policy_ids` 仍然为空。
- Verification:
  - 检查了以下输出文件均已生成：
    - `/tmp/t5_bfix_fair_eval/metrics_union.json`
    - `/tmp/t5_bfix_fair_eval/metrics_strict.json`
    - `/tmp/t5_bfix_fair_eval/metrics_hybrid.json`
    - `/tmp/t5_bfix_fair_eval/archive_diagnostics.json`
    - `/tmp/t5_cvar_fair_eval/metrics_union.json`
    - `/tmp/t5_cvar_fair_eval/metrics_strict.json`
    - `/tmp/t5_cvar_fair_eval/metrics_hybrid.json`
    - `/tmp/t5_cvar_fair_eval/archive_diagnostics.json`
- Notes:
  - 这一步已经说明：CVaR penalty 确实被训练侧采样、计算并记录了，但它没有把 `A_cons` 从 “fair-budget 下完全无成功 child” 这个状态里拉出来。
  - `final_critical_compromised_hosts` 仅出现了非常轻微的下降，但没有伴随 strict pool 恢复，也没有带来 `cons` routed child。

### Step T5-4: Decision gate
- Status: done
- Files changed:
  - `task5.md`
- Result:
  - 按 Task 5 第一版的正式成功标准检查：
    - `strict_candidate_count` 没有从 `0` 变成 `> 0`
    - `strict_hit_rate` 没有从 `0` 变成 `> 0`
    - `cons_routed_children` 没有从 `0` 变成 `> 0`
  - 因此，**Task 5 第一版 `Dual-Archive + CVaR Cons` 判定为失败**。
- Verification:
  - 判定依据来自：
    - `/tmp/t5_bfix_fair_eval/archive_diagnostics.json`
    - `/tmp/t5_cvar_fair_eval/archive_diagnostics.json`
    - 两组 fair run 的 `solution_buffer.json`、`stage2_summary.json`、`method_diagnostics.json`
- Notes:
  - 失败的含义是：`rollout-level final_critical_compromised_hosts CVaR penalty` 这一版接法，没有在 fair-budget `seed_0007` 上建立 strict candidate pool，也没有让 `A_cons` 出现 routed child。
  - 这一结果不等于“risk-aware conservative branch 永远无效”，但它足以说明：**当前这版最小 CVaR penalty 接法不足以让 `A_cons` 站起来。**
  - 因此，不应直接扩成多 seed；若继续推进 mainline A，需要先重新审视风险对象、penalty 位置或 conservative objective 形式，而不是仅放大当前 v1 复杂度。

## Task 5 v2 优化计划：Strict-Aligned CVaR Conservative Objective

### 一、目标

下一版不再继续放大当前 `rollout-level scalar penalty`，而是把 `A_cons` 的风险目标改成与 strict deployment semantics 对齐的 **composite tail risk**，并让风险信号直接进入 conservative update。

本轮固定决策如下：

- 只改 `A_cons`
- `A_uc` 不变
- dual-archive 结构不变
- strict / hybrid selector 不变
- routing 规则暂不改
- 不做多 seed
- 先只做 `seed_0007`
- 若 v2 仍未恢复 strict pool，则停止扩复杂度，不继续做参数放大

### 二、关键改动

#### 1. 风险对象：从单指标改成 strict-aligned composite risk

将 `A_cons` 的训练风险从单一 `final_critical_compromised_hosts` 改为固定的组合风险：

```text
episode_risk
= 1.0 * final_critical_compromised_hosts
+ 1.0 * mean_violation
+ 0.5 * max(0, high_disruption_action_rate - cons_thresholds.high_disruption)
```

固定规则：

- `mean_violation` 取 episode/replay 语义下的非负 violation
- `high_disruption_action_rate` 低于阈值部分不计罚，只罚超出部分
- `critical_impact_count` 本版不纳入主风险，保留到后续版本
- `cvar_alpha` 固定仍为 `0.25`

新增配置固定为：

- `cons_risk_mode: strict_aligned_cvar`
- `cvar_metric: strict_aligned_composite`
- `cvar_metric_weights`:
  - `final_critical_compromised_hosts: 1.0`
  - `mean_violation: 1.0`
  - `high_disruption_excess: 0.5`

#### 2. 训练接法：不再对所有 reward 维度统一减 penalty

v2 不沿用“对整个 reward vector 等量减一个标量 penalty”的做法，而改成：

- 在 `A_cons` rollout 中单独维护一个 scalar risk channel
- 复用现有 `ScalarRolloutStorage` 存储 tail-risk cost
- `A_uc` 仍只走原有 `VectorRolloutStorage`

具体实现固定为：

- rollout 结束后，对每个 env 得到一个 `episode_risk_sample`
- 若 env 在 rollout 内未结束，则用该 env 本 rollout 最后一次风险观测值作为 proxy
- `worst_k = max(1, ceil(alpha * num_envs))`
- 只对 tail set 中的 env 赋非零 risk cost
- risk cost 按该 env 的 `episode_risk_sample / num_steps` 均匀摊到 rollout 各 step
- 非 tail env 的 risk cost 固定为 0

#### 3. Conservative objective：风险直接进入 `IPOTrainer.update`

扩展 `IPOTrainer.update(...)`，仅在 `A_cons` 且 `cons_risk_mode=strict_aligned_cvar` 时启用额外的 risk surrogate。

固定公式：

- 原有目标 surrogate 保持不变
- 新增 `risk_advantage = risk_return`，本版不引入独立 risk critic
- 风险项按 PPO clipping 形式，对 `-risk_advantage` 构造 surrogate
- 总损失固定为：

```text
total_loss
= action_loss
+ cons_risk_penalty_coef * risk_action_loss
+ value_loss_coef * value_loss
- barrier_bonus
- entropy_coef * entropy_bonus
```

默认配置固定为：

- `cons_risk_objective_mode: ppo_cost_surrogate`
- `cons_risk_penalty_coef: 0.5`

说明：

- 本版不加 risk value head
- 本版不改 `ActorCritic` 结构
- 本版不改 `A_uc` update
- 本版不引入 routing-time risk gate

#### 4. 诊断：把“长不出来”的原因拆开

新增并固定输出以下 conservative risk diagnostics：

- `cons_tail_env_count`
- `cons_tail_risk_mean`
- `cons_tail_risk_max`
- `cons_episode_risk_mean`
- `cons_episode_risk_tail`
- `cons_risk_objective_mode`
- `cons_risk_penalty_coef`

同时新增 strict 失败分桶：

- `cons_child_failed_by_violation`
- `cons_child_failed_by_final_critical`
- `cons_child_failed_by_disruption`
- `cons_child_failed_by_multiple`

这些字段写入：

- `stage2_summary.json`
- `method_diagnostics.json`
- buffer metadata
- `archive_diagnostics.json`

#### 5. 文档与配置更新

实现时同步更新两处文档/配置承载：

- `results.md`：追加 Task 5 正式结论
- `task5.md`：追加 `Task 5 v2 优化计划`

新增/修改配置模板时固定保留两套：

- smoke: `stage2_dual_archive_strict_aligned_cvar_cons.yaml`
- fair: `stage2_dual_archive_strict_aligned_cvar_cons_fair_seed_0007.yaml`

### 三、测试计划

#### 1. 纯逻辑检查

必须覆盖：

- composite risk 计算正确
- `high_disruption` 只处罚超阈值部分
- `worst_k` 计算正确
- 未结束 episode 的 proxy sample 生效
- 非 tail env 的 risk cost 为 0
- `A_uc` 路径不读取 risk storage

#### 2. smoke

只比较两组：

- `B-fix Dual-Archive`
- `Task5 v2 Strict-Aligned CVaR Cons`

smoke 最低继续条件固定为至少满足一条：

- `cons_routed_children > 0`
- `strict_candidate_count > 0`
- `strict_hit_rate > 0`

如果三条全部不满足，则不进入 fair-budget。

#### 3. fair-budget `seed_0007`

只比较两组：

- `B-fix Dual-Archive`
- `Task5 v2 Strict-Aligned CVaR Cons`

正式成功标准固定为至少满足一条：

- `cons_routed_children` 从 `0` 变为 `> 0`
- `strict_candidate_count` 从 `0` 变为 `> 0`
- `strict_hit_rate` 从 `0` 变为 `> 0`

同时满足两个 guardrail：

- `final_critical_compromised_hosts (hybrid)` 不高于当前 B-fix 基线 `0.7014`
- `mean_violation (hybrid)` 不高于当前 B-fix 基线 `5.8391`

#### 4. 失败判定

若 fair-budget `seed_0007` 后仍同时满足：

- `cons_routed_children = 0`
- `strict_candidate_count = 0`
- `strict_hit_rate = 0`

则直接判定 **Task 5 v2 失败**，不继续多 seed，不继续单纯放大 penalty 系数。

### 四、执行假设

- `results.md` 继续作为正式实验结论文档，`task5.md` 继续作为 Task 5 的执行与决策日志
- v2 仍然只推进 `A_cons`，不把 risk-aware 逻辑扩到 `A_uc`
- v2 的重点是让风险目标和 strict deployment semantics 对齐，而不是重新改造 archive route / selector / compare pipeline

### Step T5-5: v2 配置模板与逻辑校验
- Status: done
- Files changed:
  - `CybORG_plus_plus/cmorl_cyborg/configs/ablation/stage2_dual_archive_strict_aligned_cvar_cons.yaml`
  - `CybORG_plus_plus/cmorl_cyborg/configs/paper/fair_compare_dual/stage2_dual_archive_strict_aligned_cvar_cons_fair_seed_0007.yaml`
  - `task5.md`
- Result:
  - 为 v2 补齐了两套固定入口配置：
    - smoke: `strict_aligned_cvar`
    - fair-budget `seed_0007`: `strict_aligned_cvar`
  - 固定启用：
    - `cons_risk_mode = strict_aligned_cvar`
    - `cvar_metric = strict_aligned_composite`
    - `cons_risk_objective_mode = ppo_cost_surrogate`
    - `cons_risk_penalty_coef = 0.5`
    - `cvar_metric_weights = {final_critical_compromised_hosts: 1.0, mean_violation: 1.0, high_disruption_excess: 0.5}`
  - smoke 首次运行因 Stage-1 checkpoint 使用 `hidden_size=128` 而配置写成 `64` 导致载入失败；随后已将 smoke 模型宽度改为 `128` 并重跑。
- Verification:
  - 对共享训练/评估入口执行了 `py_compile`。
  - 用直接函数校验确认：
    - composite risk 计算正确
    - `high_disruption` 只处罚超阈值部分
    - `worst_k = max(1, ceil(alpha * num_envs))`
    - `_rollout_cvar_penalty([0.2, 0.8, 0.5, 1.3], alpha=0.25, penalty_coef=0.5)` 得到 `worst_k=1`、`tail=1.3`、`penalty=0.65`

### Step T5-6: v2 Smoke 验证
- Status: done
- Files changed:
  - `task5.md`
- Result:
  - 完成了 v2 smoke 训练：
    - `/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/ablation/stage2_dual_archive_strict_aligned_cvar_cons/run_e84bdddc/solution_buffer.json`
  - 完成了 fresh smoke 评估：
    - `/tmp/t5_v2_smoke_eval_fresh/archive_diagnostics.json`
  - 与现有 B-fix smoke 基线对照：
    - B-fix: `/tmp/t5_bfix_smoke_eval/archive_diagnostics.json`
    - v2: `/tmp/t5_v2_smoke_eval_fresh/archive_diagnostics.json`
  - 关键结果如下：
    - B-fix smoke:
      - `cons_attempted_children = 6`
      - `cons_successful_children = 6`
      - `cons_routed_children = 0`
      - `strict_candidate_count = 0`
      - `strict_hit_rate = 0.0`
    - v2 smoke:
      - `cons_attempted_children = 6`
      - `cons_successful_children = 6`
      - `cons_routed_children = 0`
      - `strict_candidate_count = 1`
      - `strict_hit_rate = 0.0`
      - `cons_cvar_estimate_tail = 0.6875`
      - `cons_risk_penalty_mean = 0.34375`
      - `cons_child_failed_by_final_critical = 6`
  - 这说明 v2 在 smoke 中没有让 `A_cons` routed child 恢复，也没有让 strict 命中恢复；
    但它确实把 `strict_candidate_count` 从 `0` 拉到了 `1`，满足了继续进入 fair-budget 的最低门槛。
- Verification:
  - 同时检查了：
    - `stage2_summary.json`
    - `method_diagnostics.json`
    - fresh `archive_diagnostics.json`

### Step T5-7: v2 Fair-budget `seed_0007` 正式验证
- Status: done
- Files changed:
  - `task5.md`
- Result:
  - 完成了 v2 fair-budget `seed_0007` 训练：
    - `/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/fair_compare_dual/dual_archive_strict_aligned_cvar_cons_stage2_fair/seed_0007/run_fcd1d299/solution_buffer.json`
  - 训练侧 diagnostics 显示：
    - `cons_attempted_children = 18`
    - `cons_successful_children = 0`
    - `cons_routed_children = 0`
    - `cons_cvar_estimate_tail = 1.0`
    - `cons_risk_penalty_mean = 0.5`
    - `cons_child_failed_by_violation = 0`
    - `cons_child_failed_by_final_critical = 0`
    - `cons_child_failed_by_disruption = 0`
    - `cons_child_failed_by_multiple = 0`
  - 我另外用轻量 assignment / archive summary 对照了 B-fix fair 基线：
    - B-fix:
      - `cons_successful_children = 0`
      - `cons_routed_children = 0`
      - `strict_candidate_count = 0`
      - `strict_hit_rate = 0.0`
    - v2:
      - `cons_successful_children = 0`
      - `cons_routed_children = 0`
      - `strict_candidate_count = 0`
      - `strict_hit_rate = 0.0`
  - 说明到了正式 fair-budget，v2 在决定性门控指标上没有保留 smoke 中的弱正向信号。
- Verification:
  - 直接检查了 fair run 的：
    - `stage2_summary.json`
    - `method_diagnostics.json`
    - `solution_buffer.json`
- Notes:
  - 我启动过完整 fresh fair 评估，但在确认三项正式成功条件全部仍为 `0` 后中止了这一步，因为无论 guardrail 最终数值如何，v2 都已经不满足 Task 5 v2 的成功定义。

### Step T5-8: v2 Decision gate
- Status: done
- Files changed:
  - `results.md`
  - `task5.md`
- Result:
  - 按 Task 5 v2 的正式成功标准检查：
    - `cons_routed_children` 没有从 `0` 变为 `> 0`
    - `strict_candidate_count` 没有在 fair-budget `seed_0007` 中从 `0` 变为 `> 0`
    - `strict_hit_rate` 没有从 `0` 变为 `> 0`
  - 因此，**Task 5 v2 `Strict-Aligned CVaR Conservative Objective` 判定为失败。**
- Verification:
  - 判定依据来自：
    - smoke fresh 评估：
      - `/tmp/t5_v2_smoke_eval_fresh/archive_diagnostics.json`
    - fair run 训练诊断：
      - `/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/fair_compare_dual/dual_archive_strict_aligned_cvar_cons_stage2_fair/seed_0007/run_fcd1d299/method_diagnostics.json`
      - `/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/fair_compare_dual/dual_archive_strict_aligned_cvar_cons_stage2_fair/seed_0007/run_fcd1d299/stage2_summary.json`
- Notes:
  - v2 的失败比 v1 更有信息量：
    - smoke 确实短暂出现了 `strict_candidate_count = 1`
    - 但一到 fair-budget 就完全消失
  - 这说明“让风险目标更贴近 strict 语义”本身还不够；
    当前更深层的问题仍然是：
    - conservative branch 没有在正式预算下稳定地产出可路由 child
    - `A_cons` 的恢复瓶颈不只是 risk definition，还包括 operator / route / deployment semantic 的联动失配
