# Task 4 - 在 Cyber-CMORL 中补齐 Dual-Archive 的评估与选择语义（面向 Codex）

## 0. 任务目的

Task 3 已经把 Stage-2 从“单档案、单选择器”改成了 **Dual-Archive Stage-2**。下一步最重要的不是继续堆新机制，而是把双档案真正变成：

- **评估时成立**
- **导表时成立**
- **选策略时成立**
- **正式 CybORG 验证时成立**

本任务的核心目标是：

1. 把当前默认的 **单集合 + plain SMP** 评估方式，升级成 **union / strict / hybrid 三种语义**。
2. 让 `evaluate.py`、`assignment.py`、`select_policy.py`、compare/export pipeline 能识别双档案。
3. 跑出第一轮正式实验，判断 Task 3 的双档案是否已经足以缓解当前 trade-off。
4. 为“是否进入主线 A（risk-aware conservative branch）”建立明确决策门。

本任务默认前提：

- Task 3 的双档案实现已经完成，至少包括：
  - `A_cons`
  - `A_uc`
  - dual-archive routing
  - strict / hybrid selector 的训练侧或方法侧接口
- 正式结论仍以 `cmorl_cyborg` 线为准，但主要算法改动优先在共享实现层完成。

---

## 1. 当前代码事实（必须对齐）

### 1.1 正式环境入口仍是共享主实现

- `cmorl_cyborg/train_stage2.py` 是一个薄封装：
  - 只把环境替换成 `CybORGMORLEnv`
  - 然后直接复用 `cmorl_minicage.train_stage2`
- 因此，Task 4 的主改动仍然优先写在共享层：
  - `cmorl_minicage/evaluate.py`
  - `cmorl_minicage/algorithms/assignment.py`
  - `cmorl_minicage/select_policy.py`
  - `cmorl_minicage/config.py`
  - 如 compare/export 也在共享层，则同步改共享层
- `cmorl_cyborg/` 侧只做：
  - 环境透传
  - 正式配置
  - 正式实验输出目录

### 1.2 当前评估与选择仍偏单档案语义

当前代码仍主要建立在：

- `evaluate.py`
  - `records -> nondominated_filter(records) -> pareto_records`
  - 再对 `pareto_records` 做：
    - HV
    - EU
    - SP
    - assignment summary
- `assignment.py`
  - 只有简单版 `assign_policy(preference, policy_set)`
  - 即 plain SMP：从给定集合里选 utility 最大的 policy
- `select_policy.py`
  - 当前只支持：
    - `source_set=pareto`
    - `source_set=records`

这意味着：如果 Task 3 已经完成，但 Task 4 不做，双档案只存在于训练态，**不会完整进入论文主表与部署评估语义**。

### 1.3 当前主文结构已经固定

项目文档已经把主叙事锁成：

- `Table A = Set Quality Table`
- `Table B = Deployment Table`

因此 Task 4 的目标不是另起炉灶，而是把双档案自然塞入这两层结构中。

---

## 2. 本任务的总体设计

## 2.1 三套结果口径必须同时存在

Task 4 之后，Dual-Archive 方法至少要支持下面三种结果口径：

### A. `union`
面向 **Set Quality**。

语义：

- 使用 `A_cons ∪ A_uc`
- 对 union 做 Pareto filter
- 再计算：
  - HV
  - EU
  - Sparsity / spread
  - Coverage
  - Pareto count
  - Unique assigned policies

回答的问题：

> 这个双档案方法最终发现了什么样的候选集合？

### B. `strict`
面向 **保守部署选择**。

语义：

- 只允许从 `A_cons` 选策略
- 且优先只用 strict/near-feasible 候选
- 如果没有符合条件的候选，返回 `None` 或记为 strict miss，不自动回退

回答的问题：

> 如果部署优先，双档案方法最终能交付什么？

### C. `hybrid`
面向 **恢复式部署选择**。

语义：

- 优先从 `A_cons` 选
- 如果 `A_cons` 中没有足够好的候选，则退回 union
- 在 union 中不做 plain utility 选择，而是做 **带 penalty 的折中选择**

回答的问题：

> 当保守部署集不足时，双档案有没有比单档案更好的 fallback？

---

## 2.2 不要把 strict / hybrid 藏在训练日志里

Task 4 之后，`strict` 和 `hybrid` 不能只存在于：

- `stage2_summary.json`
- `method_diagnostics.json`
- 某个 notebook

而要变成：

- `evaluate.py` 的正式输出
- compare/export pipeline 的正式输入
- `select_policy.py` 的正式 CLI 选择模式

这样它们才算真正进入论文线。

---

## 3. 本任务的优先级

### P0 - 最高优先级

1. 让 `evaluate.py` 支持 `union / strict / hybrid`
2. 让 `assignment.py` 支持 strict / hybrid selector
3. 让 `select_policy.py` 支持 dual-archive source set 与 selector mode
4. 跑出第一轮正式结果矩阵：
   - `Original Stage2`
   - `AdaCS-DCS`
   - `Dual-Archive Stage2`

### P1 - 次高优先级

5. 让 compare/export/table pipeline 能吃下三种结果口径
6. 增加 archive diagnostics
7. 补图：strict vs hybrid vs union

### P2 - 中期优先级

8. 根据结果判断是否进入主线 A（CVaR conservative branch）
9. 如果不进入主线 A，则冻结 Task 3/4 结构，转入多 seed 与写作

---

## 4. 需要新增/修改的文件

## 4.1 重点修改文件

### A. `cmorl_minicage/evaluate.py`
这是本任务主战场。

必须新增：

- dual-archive aware evaluation entry
- `mode=union | strict | hybrid`
- dual-archive metadata 解析
- strict selector miss 统计
- hybrid fallback 统计

### B. `cmorl_minicage/algorithms/assignment.py`
必须扩展为：

- `assign_policy_union(...)`
- `assign_policy_strict(...)`
- `assign_policy_hybrid(...)`
- 或统一为：
  - `assign_policy(preference, policy_set, selector_mode=...)`

要求：

- `strict` 不允许静默回退
- `hybrid` 必须带 penalty，而不是 union 上 plain SMP

### C. `cmorl_minicage/select_policy.py`
必须支持 CLI：

- `--source-set cons`
- `--source-set uc`
- `--source-set union`
- `--selector-mode plain`
- `--selector-mode strict`
- `--selector-mode hybrid`

### D. `cmorl_minicage/config.py`
扩展 evaluate / selector 配置。

建议新增：

- `selector_mode`
- `archive_source`
- `hybrid_penalty_weights`
- `strict_require_tight_feasible`

### E. compare/export pipeline（如有共享实现）
让导表脚本能区分：

- `metrics_union.json`
- `metrics_strict.json`
- `metrics_hybrid.json`

### F. `cmorl_cyborg/` 对应 evaluate 入口与 formal configs
如果 `cmorl_cyborg` 有单独评估入口或 formal configs，需要同步新增 dual-archive 配置，但尽量不复制逻辑。

---

## 4.2 可选新增文件

建议新增：

- `cmorl_minicage/algorithms/deployment_selector.py`

如果你不想把 strict / hybrid 逻辑都塞进 `assignment.py`，可以把 deployment-aware selector 单独拆出去。

建议新增实验配置：

- `cmorl_cyborg/configs/ablation/evaluate_union.yaml`
- `cmorl_cyborg/configs/ablation/evaluate_strict.yaml`
- `cmorl_cyborg/configs/ablation/evaluate_hybrid.yaml`

---

## 5. 详细任务拆分

## T4-1 先做结构验收与 schema 锁定

### 目标
确认 Task 3 的训练输出已经足够支撑 Task 4。

### 要做的事

1. 检查 `solution_buffer.json` 中是否已有：
   - `archive_role`
   - `operator_source`
   - strict/hybrid 所需 deployment 字段
2. 检查 metadata 中是否已有：
   - dual-archive mode
   - `cons_policy_ids`
   - `uc_policy_ids`
3. 如果字段还只存在于 `notes` 且命名不稳定，先统一并冻结字段名。
4. 必要时升级 `SCHEMA_VERSION`。

### 验收标准

- buffer 中已经能可靠区分：
  - `A_cons`
  - `A_uc`
  - union 候选
- 不需要重新读训练日志才能做后续评估

---

## T4-2 改 `assignment.py`：补齐 strict / hybrid selector

### 目标
把 plain SMP 扩展成可正式用于部署评估的 selector。

### 具体要求

#### 5.2.1 保留 plain selector
旧接口不能直接删。

```python
assign_policy(preference, policy_set)
```

仍保留作 union/plain SMP。

#### 5.2.2 新增 strict selector
语义：

- 输入 `preference`
- 输入 `cons_policy_set`
- 只在 `tight_feasible_flag` 或 `near_feasible_flag` 的候选中选
- 无满足者则返回 `None`

建议接口：

```python
assign_policy_strict(preference, cons_policy_set, *, require_tight=False)
```

#### 5.2.3 新增 hybrid selector
语义：

- 先尝试 strict
- strict 命中则直接返回
- 否则在 union 中做 penalty-aware 选择

建议接口：

```python
assign_policy_hybrid(
    preference,
    cons_policy_set,
    union_policy_set,
    *,
    penalty_weights,
    require_tight=False,
)
```

其中 union fallback 分数建议写成：

```python
score = utility \
        - lam_v * mean_violation \
        - lam_d * high_disruption_rate \
        - lam_k * final_critical_compromised
```

#### 5.2.4 返回结果中显式带出 selector 元信息
返回 dict 中增加：

- `selector_mode`
- `source_set`
- `strict_hit`
- `fallback_used`
- `score_breakdown`（可选）

### 验收标准

- 单元测试或最小脚本能区分 plain / strict / hybrid
- strict miss 时不会静默回退
- hybrid 确实使用 penalty-aware fallback

---

## T4-3 改 `evaluate.py`：输出三种正式结果文件

### 目标
让 Dual-Archive 的三种结果口径成为正式评估输出。

### 具体要求

#### 5.3.1 增加 archive-aware record loading
`evaluate.py` 需要从 buffer 中解析：

- `cons_records`
- `uc_records`
- `union_records`

如果 buffer 里只保存了单一 `records`，则：

- 按 `archive_role` 重新拆分
- union = `records`

#### 5.3.2 新增 evaluation mode
建议支持：

```python
mode = "union" | "strict" | "hybrid"
```

#### 5.3.3 union 模式
流程：

1. 取 `A_cons ∪ A_uc`
2. Pareto filter
3. 算：
   - HV
   - EU
   - SP
   - coverage
   - Pareto count
   - unique assigned policies

输出：

- `metrics_union.json`

#### 5.3.4 strict 模式
流程：

1. 只取 `A_cons`
2. 对每个 preference 做 strict selector
3. 统计：
   - strict hit rate
   - strict miss count
   - strict selected utility
   - strict selected deployment metrics

输出：

- `metrics_strict.json`

#### 5.3.5 hybrid 模式
流程：

1. 先 strict
2. miss 则走 union fallback
3. 统计：
   - strict hit rate
   - hybrid fallback rate
   - selected utility
   - selected deployment metrics

输出：

- `metrics_hybrid.json`

#### 5.3.6 保留原 `metrics.json` 兼容逻辑
为避免破坏旧脚本：

- 可以让 `metrics.json` 默认等于 `metrics_union.json`
- 但必须额外输出 strict / hybrid 两份专用文件

### 验收标准

- 对同一个 dual-archive buffer，能稳定产出三份结果文件
- strict / hybrid 与 union 的数值语义明显不同
- 旧单档案 buffer 仍可跑通 union 模式

---

## T4-4 改 `select_policy.py`：让 CLI 真正支持 dual-archive 选择

### 目标
让命令行选策略工具能直接服务于正式实验与部署分析。

### 具体要求

#### 5.4.1 扩展 `source_set`
增加：

- `cons`
- `uc`
- `union`

兼容旧的：

- `pareto`
- `records`

推荐后续默认：

- dual-archive buffer 默认用 `union`

#### 5.4.2 新增 `selector_mode`
支持：

- `plain`
- `strict`
- `hybrid`

#### 5.4.3 输出更多选择元信息
打印或 JSON 中明确显示：

- 命中的是 `cons` 还是 `union`
- 是否发生 fallback
- utility 与 penalty 后 score

### 验收标准

- 能从同一个 dual-archive buffer 上直接测试：
  - strict 选谁
  - hybrid 选谁
- 输出中能看懂为何选中该 policy

---

## T4-5 在 `config.py` 中补齐评估/选择配置

### 目标
让 dual-archive 评估不是硬编码，而是配置驱动。

### 具体要求

建议为 `EvaluateConfig` 新增：

```python
selector_mode: str = "union"          # union | strict | hybrid
archive_source: str = "union"         # union | cons | uc
strict_require_tight: bool = False
hybrid_penalty_weights: dict[str, float] = {
    "mean_violation": 1.0,
    "high_disruption_rate": 1.0,
    "final_critical_compromised": 1.0,
}
```

如果你希望部署评估与 set-level 评估彻底分开，也可以考虑新增：

- `DeploymentEvaluateConfig`

但第一版不强制。

### 验收标准

- 不改代码也能通过 YAML 切换 union / strict / hybrid
- penalty 权重能从 config 控制

---

## T4-6 跑第一轮正式实验矩阵

### 目标
判断 Task 3 的双档案是否已经有正式主线价值。

### 方法组
先固定三组，不要立刻加主线 A：

1. `Original Stage2`
2. `AdaCS-DCS`
3. `Dual-Archive Stage2`

### 结果组
每组都导出：

- union
- strict
- hybrid

### Table A（Set Quality）
只看 union：

- HV
- EU
- Coverage
- Pareto count
- Unique assigned policies
- Spread / Sparsity

### Table B（Deployment）
至少分两张：

#### B1 Strict
- feasible rate
- mean violation
- security
- business
- cost
- critical impact
- final critical compromised
- high disruption

#### B2 Hybrid
同上。

### 验收标准

Task 3 至少满足下面一条才算进入正式主线候选：

- Table A 更均衡，且 Strict / Hybrid 至少有一版明显优于单档案
- Table A 不明显变差，且 Strict feasible retention / fallback quality 更稳

---

## T4-7 新增 archive diagnostics（强烈建议）

### 目标
证明双档案不是“换名字的单池子”。

### 建议输出一张 diagnostics 表或 JSON
至少包括：

- `num_cons_records`
- `num_uc_records`
- `num_union_records`
- `num_union_pareto_records`
- `strict_candidate_count`
- `strict_hit_rate`
- `hybrid_fallback_rate`
- `from_original_to_cons`
- `from_original_to_uc`
- `from_adacs_to_cons`
- `from_adacs_to_uc`

### 价值
这张表会直接回答：

- 两个 branch 是否真在分工
- 路由是否只是形式存在
- selector 是否真的用到了 `A_cons`

### 验收标准

- diagnostics 能和主表结果一起解释
- 至少能支持一张 appendix 表或一幅机制图

---

## T4-8 对齐 compare/export/table pipeline

### 目标
让双档案结果真正进入论文导表链路。

### 具体要求

1. compare suite 能识别多份 metrics 文件
2. export table 脚本能区分：
   - union
   - strict
   - hybrid
3. 图像导出至少支持：
   - strict vs hybrid 柱状图
   - archive routing / archive size 图
   - union front 图

### 验收标准

- 不需要手动 notebook 拼表
- 可以从正式 CybORG run 目录直接导出图表

---

## 6. 推荐实施顺序（给 Codex）

### Step 1
先做 T4-1：

- 锁定 Task 3 buffer/schema
- 确认 dual-archive 字段稳定

### Step 2
做 T4-2：

- 改 `assignment.py`
- 先让 strict / hybrid selector 跑通

### Step 3
做 T4-3：

- 改 `evaluate.py`
- 输出 `metrics_union.json` / `metrics_strict.json` / `metrics_hybrid.json`

### Step 4
做 T4-4：

- 改 `select_policy.py`
- 确保 CLI 可直接测试 dual-archive 选择语义

### Step 5
做 T4-5：

- 配置化 selector mode / penalty weights

### Step 6
做 T4-6：

- 跑正式矩阵：Original / AdaCS-DCS / Dual-Archive
- 生成 Table A / Table B 初版

### Step 7
做 T4-7：

- 补 archive diagnostics

### Step 8
做 T4-8：

- 接 compare/export/paper pipeline

---

## 7. 结果后的决策门：是否进入主线 A

Task 4 不是终点，它的输出要直接决定下一步。

### 如果出现下面情况，则 **先不要进入主线 A**

- `strict` 已明显改善
- `mean_violation` 明显下降
- `tight feasible retention` 回升
- `hybrid` fallback 触发很少，或触发时也很稳

说明当前主要问题是 **Stage-2 结构组织问题**，双档案已经基本解决。

### 如果出现下面情况，则 **进入主线 A（先做 CVaR conservative branch）**

- union front 更好了，但 strict 仍经常 miss
- hybrid fallback 触发频繁
- final critical compromised / critical impact 仍存在坏尾部
- feasible rate / mean violation 仍不稳

说明双档案只解决了“候选池组织问题”，没有解决“保守分支本身的尾部风险问题”。

### 结论

Task 4 的最终目的之一，就是为下面这个判断提供证据：

> Dual-Archive 是否已经足够作为正式主方法，还是必须继续叠加主线 A。

---

## 8. 本轮完成标志

以下条件同时满足，Task 4 才算完成：

- `evaluate.py` 能输出 union / strict / hybrid 三份正式结果
- `assignment.py` / `select_policy.py` 已支持 strict / hybrid 选择语义
- 能在 `cmorl_cyborg` 正式线跑出三组方法的第一轮矩阵
- 至少有一张 Table A、两张 Table B（Strict / Hybrid）
- 有一份 archive diagnostics
- 已经能明确判断：下一步是直接写作，还是进入主线 A

---

## 9. 对 Codex 的实现要求

- 优先最小改动，不重写 Task 3 的训练主逻辑
- 不复制 `cmorl_minicage` 主实现到 `cmorl_cyborg`
- 保持旧单档案配置兼容
- 每做完一个子任务，都要同步更新：
  - `docs/TASKS.md`
  - `docs/DECISIONS.md`
  - 如有必要更新 `README.md`
- 所有新增 JSON / 表格输出都要命名稳定，便于 compare/export pipeline 使用

---

## Task 4 Execution Log

### Step T4-1: Schema acceptance and field lock
- Status: done
- Files changed:
  - `task4.md`
  - `docs/TASKS.md`
  - `docs/DECISIONS.md`
- Result:
  - Verified Task 3 dual-archive buffers expose `cons_records`, `uc_records`, `union_front`, `archive_role`, `operator_source`, strict/hybrid selector fields, and metadata keys without reading training logs.
  - Confirmed `SCHEMA_VERSION` is already `0.4.0`, so no schema bump is needed for T4-1.
- Verification:
  - Checked `/tmp/cyber_cmorl_dual_stage2_smoke/run_0b11f0ff/solution_buffer.json`.
  - Checked `/tmp/cyber_cmorl_dual_stage2_smoke_unconstrained/run_13a4b40f/solution_buffer.json`.
- Notes:
  - Both inspected buffers had `archive_mode=dual`, non-empty archive payloads, and no missing required record or metadata fields.

### Step T4-2/T4-4: Selector semantics and CLI metadata
- Status: done
- Files changed:
  - `CybORG_plus_plus/cmorl_minicage/algorithms/assignment.py`
  - `CybORG_plus_plus/cmorl_minicage/algorithms/__init__.py`
  - `CybORG_plus_plus/cmorl_minicage/select_policy.py`
  - `task4.md`
  - `docs/TASKS.md`
  - `docs/DECISIONS.md`
- Result:
  - Formalized plain, union, strict, and hybrid selector modes.
  - Strict selection now returns a structured miss instead of silently falling back.
  - Hybrid selection tries conservative strict selection first, then uses union penalty-aware fallback with score breakdown metadata.
  - `select_policy.py` now defaults to `source_set=union`, supports `--strict-require-tight`, and prints JSON/non-JSON miss and fallback metadata.
- Verification:
  - Ran mock selector checks for plain, strict hit, strict miss, hybrid strict hit, and hybrid fallback.
  - Ran CLI checks on `/tmp/t4_selector_buffer.json` for strict miss and hybrid fallback.
  - Ran `py_compile` on `assignment.py` and `select_policy.py`.
- Notes:
  - `assign_policy(preference, policy_set)` remains compatible and still performs plain utility selection by default.

### Step T4-3/T4-5: Archive-aware evaluation modes and config
- Status: done
- Files changed:
  - `CybORG_plus_plus/cmorl_minicage/evaluate.py`
  - `CybORG_plus_plus/cmorl_minicage/config.py`
  - `CybORG_plus_plus/cmorl_cyborg/config.py`
  - `task4.md`
  - `docs/TASKS.md`
  - `docs/DECISIONS.md`
- Result:
  - Added archive-aware loading for `cons_records`, `uc_records`, `union`, and `union_front`.
  - Added formal `union`, `strict`, and `hybrid` evaluation modes.
  - CLI evaluation now writes `metrics_union.json`, `metrics_strict.json`, `metrics_hybrid.json`, and legacy-compatible `metrics.json`.
  - Added evaluate config fields for selector mode, archive source, tight-feasible strict mode, and hybrid penalty weights in minicage and cyborg configs.
- Verification:
  - Ran `py_compile` on `evaluate.py` and both config modules.
  - Evaluated the Task 3 dual smoke buffer into `/tmp/t4_eval_smoke/metrics_*.json`.
  - Evaluated an old single-archive Stage-1 buffer into `/tmp/t4_eval_single_compat/metrics_*.json`.
- Notes:
  - `evaluate_policy_buffer(...)` still defaults to union mode, preserving existing compare-suite call semantics.

### Step T4-7/T4-8: Archive diagnostics and compare/export pipeline
- Status: done
- Files changed:
  - `CybORG_plus_plus/cmorl_minicage/evaluate.py`
  - `CybORG_plus_plus/cmorl_minicage/compare_suite.py`
  - `CybORG_plus_plus/cmorl_minicage/export_tables.py`
  - `CybORG_plus_plus/cmorl_cyborg/configs/ablation/evaluate_union.yaml`
  - `CybORG_plus_plus/cmorl_cyborg/configs/ablation/evaluate_strict.yaml`
  - `CybORG_plus_plus/cmorl_cyborg/configs/ablation/evaluate_hybrid.yaml`
  - `task4.md`
  - `docs/TASKS.md`
  - `docs/DECISIONS.md`
- Result:
  - Added `archive_diagnostics.json` output with archive sizes, strict candidate count, selector rates, and operator-to-archive route counts.
  - Updated compare suite to save `metrics_shared_ref_union.json`, `metrics_shared_ref_strict.json`, `metrics_shared_ref_hybrid.json`, and archive diagnostics for buffer entries.
  - Updated table export to generate Table A plus separate `table_b_strict.*` and `table_b_hybrid.*` deployment tables.
  - Added CybORG ablation evaluate configs for union, strict, and hybrid modes.
- Verification:
  - Ran `py_compile` on `evaluate.py`, `compare_suite.py`, and `export_tables.py`.
  - Ran a temporary compare/export smoke chain under `/tmp/t4_compare_smoke` and `/tmp/t4_export_smoke`.
- Notes:
  - Conditioned-points entries remain union-only; strict/hybrid mode outputs are generated for buffer artifacts.

### Step T4-6: First-round formal-lite matrix and decision gate
- Status: partial
- Files changed:
  - `CybORG_plus_plus/cmorl_cyborg/evaluate.py`
  - `task4.md`
  - `docs/TASKS.md`
  - `docs/DECISIONS.md`
- Result:
  - Updated the CybORG evaluate wrapper so it also writes union, strict, hybrid, and archive diagnostics outputs through the shared implementation.
  - Ran a small CybORG Dual-Archive Stage-2 smoke from the existing seed-0007 Stage-1 buffer.
  - Ran a three-method formal-lite matrix with `Original Stage2`, `AdaCS-DCS`, and `Dual-Archive Stage2`.
  - Exported Table A, Table B Strict, and Table B Hybrid from the formal-lite matrix.
- Verification:
  - Dual-Archive CybORG smoke output: `/tmp/t4_cyborg_dual_stage2_formal_lite/run_e143a005/solution_buffer.json`.
  - Matrix summary: `/tmp/t4_cyborg_formal_lite_compare_h100/table_a_summary.json`.
  - Exported tables: `/tmp/t4_cyborg_formal_lite_export_h100/table_a_metrics.csv`, `table_b_strict.csv`, and `table_b_hybrid.csv`.
  - CybORG evaluate wrapper smoke output: `/tmp/t4_cyborg_eval_wrapper/metrics_union.json`, `metrics_strict.json`, `metrics_hybrid.json`, and `archive_diagnostics.json`.
  - Ran final `py_compile` over modified minicage and cyborg modules.
- Notes:
  - This is a formal-lite pipeline validation, not a final scientific claim: Dual-Archive used a tiny single-seed smoke run while Original/AdaCS-DCS used existing seed-0007 buffers.
  - Preliminary gate signal: strict hit rate was 0 and hybrid fallback rate was 1.0 in the formal-lite matrix, so Dual-Archive is not yet proven sufficient. If the same pattern persists in full comparable runs, the next direction should be mainline A / CVaR conservative branch.

### Step T4-6a: Comparable Dual-Archive run
- Status: done
- Files changed:
  - `CybORG_plus_plus/cmorl_cyborg/configs/paper/fair_compare_dual/stage2_dual_archive_fair_seed_0007.yaml`
  - `task4.md`
  - `docs/TASKS.md`
  - `docs/DECISIONS.md`
- Result:
  - Added a seed-0007 Dual-Archive Stage-2 config aligned with the fair-compare baselines on `stage1_buffer`, `seed`, `max_episode_steps`, `model.hidden_size`, `total_timesteps_per_update`, `extension_rounds`, and `constrained_updates`.
  - Ran the comparable CybORG Dual-Archive experiment successfully and produced a formal output buffer at `cmorl_cyborg/outputs/fair_compare_dual/dual_archive_stage2_fair/seed_0007/run_5b1ae302/solution_buffer.json`.
  - The completed run produced dual-archive artifacts with `records=29`, `cons_records=11`, `uc_records=14`, `union_front=10`, plus `stage2_summary.json` and `method_diagnostics.json`.
- Verification:
  - Checked `CybORG_plus_plus/cmorl_cyborg/configs/paper/fair_compare_original/stage2_original_stage2_fair_seed_0007.yaml`.
  - Checked `CybORG_plus_plus/cmorl_cyborg/configs/paper/fair_compare/stage2_fair_constrained_seed_0007.yaml`.
  - Checked `CybORG_plus_plus/cmorl_cyborg/outputs/fair_compare_dual/dual_archive_stage2_fair/seed_0007/run_5b1ae302/solution_buffer.json`.
  - Confirmed `archive_mode=dual` and the presence of `stage2_summary.json` and `method_diagnostics.json`.
- Notes:
  - This run is budget-aligned with the seed-0007 fair baselines and replaces the earlier smoke-only Dual-Archive evidence for subsequent comparison work.

### Step T4-6b: Comparable evaluation outputs
- Status: done
- Files changed:
  - `task4.md`
  - `docs/TASKS.md`
  - `docs/DECISIONS.md`
- Result:
  - Generated comparable `union / strict / hybrid / archive_diagnostics` outputs for `Original Stage2`, `AdaCS-DCS`, and `Dual-Archive Stage2` under `cmorl_cyborg/outputs/fair_compare_dual/comparable_eval_seed_0007/`.
  - `Original Stage2` outputs: `.../original_stage2/metrics_union.json`, `metrics_strict.json`, `metrics_hybrid.json`, `archive_diagnostics.json`.
  - `AdaCS-DCS` outputs: `.../adacs_dcs/metrics_union.json`, `metrics_strict.json`, `metrics_hybrid.json`, `archive_diagnostics.json`.
  - `Dual-Archive Stage2` outputs: `.../dual_archive_stage2/metrics_union.json`, `metrics_strict.json`, `metrics_hybrid.json`, `archive_diagnostics.json`.
  - Comparable evaluation summary snapshot:
    - `Original Stage2`: `HV=1923403.0156`, `coverage=0.1875`, `strict_hit_rate=0.0`, `hybrid_fallback_rate=1.0`
    - `AdaCS-DCS`: `HV=1888852.7031`, `coverage=0.3333`, `strict_hit_rate=0.0`, `hybrid_fallback_rate=1.0`
    - `Dual-Archive Stage2`: `HV=1833580.0391`, `coverage=0.3000`, `strict_hit_rate=0.0`, `hybrid_fallback_rate=1.0`
- Verification:
  - Confirmed that all three method directories contain `metrics.json`, `metrics_union.json`, `metrics_strict.json`, `metrics_hybrid.json`, and `archive_diagnostics.json`.
  - Verified `strict_candidate_count=0` for all three methods in the comparable evaluation outputs.
- Notes:
  - `AdaCS-DCS` had to be evaluated from the original run buffer at `/home/waylandlee/Cyber-CMORL/cmorl_cyborg/outputs/fair_compare/ours_stage2_fair/seed_0007/run_97631fb4/solution_buffer.json`, because the copied `fair_compare_eval_inputs` buffer referenced relative checkpoint paths that resolve incorrectly for semantic replay.

### Step T4-6c: Comparable tables
- Status: done
- Files changed:
  - `CybORG_plus_plus/cmorl_cyborg/configs/paper/fair_compare_dual/compare_suite_seed_0007.yaml`
  - `CybORG_plus_plus/cmorl_cyborg/configs/paper/fair_compare_dual/export_tables_seed_0007.yaml`
  - `CybORG_plus_plus/cmorl_minicage/export_tables.py`
  - `task4.md`
  - `docs/TASKS.md`
  - `docs/DECISIONS.md`
- Result:
  - Added a dedicated comparable compare-suite config for `Original Stage2`, `AdaCS-DCS`, and `Dual-Archive Stage2` at seed `0007`.
  - Added a dedicated export config that consumes the comparable compare summary and the six comparable strict/hybrid metrics files.
  - Generated shared-reference comparison outputs under `cmorl_cyborg/outputs/fair_compare_dual/comparable_compare_seed_0007/`.
  - Exported formal comparable tables under `cmorl_cyborg/outputs/fair_compare_dual/comparable_tables_seed_0007/`, including:
    - `table_a_metrics.csv`
    - `table_b_strict.csv`
    - `table_b_hybrid.csv`
  - Fixed `export_tables.py` so Table B rows infer method names from their parent directories when the metrics payload itself does not contain `method_name`.
- Verification:
  - Verified `cmorl_cyborg/outputs/fair_compare_dual/comparable_compare_seed_0007/table_a_summary.json`.
  - Verified `cmorl_cyborg/outputs/fair_compare_dual/comparable_tables_seed_0007/table_a_metrics.csv`.
  - Verified `cmorl_cyborg/outputs/fair_compare_dual/comparable_tables_seed_0007/table_b_strict.csv`.
  - Verified `cmorl_cyborg/outputs/fair_compare_dual/comparable_tables_seed_0007/table_b_hybrid.csv`.
  - Confirmed all three methods appear explicitly in Table A, Table B Strict, and Table B Hybrid after the export label fix.
- Notes:
  - Comparable shared-reference Table A summary at seed `0007`:
    - `Original Stage2`: `HV=1923403.0156`, `coverage=0.1875`, `EU=-171.3691`
    - `AdaCS-DCS`: `HV=1890954.7344`, `coverage=0.3333`, `EU=-171.3308`
    - `Dual-Archive Stage2`: `HV=1835675.2891`, `coverage=0.3000`, `EU=-171.3703`

### Step T4-6d: Decision gate
- Status: done
- Files changed:
  - `task4.md`
  - `docs/TASKS.md`
  - `docs/DECISIONS.md`
- Result:
  - Completed the seed-0007 comparable decision gate using the budget-aligned Dual-Archive run, the comparable per-method evaluation outputs, and the shared-reference tables.
  - The gate signal is consistent across both direct evaluation and shared-reference comparison:
    - `strict_hit_rate = 0.0` for `Original Stage2`, `AdaCS-DCS`, and `Dual-Archive Stage2`
    - `hybrid_fallback_rate = 1.0` for all three methods
    - `strict_candidate_count = 0` for all three methods
  - `Dual-Archive Stage2` did not show evidence that `A_cons` was producing deployable strict candidates under the comparable seed-0007 setup, and its shared-reference `HV` remained below both baselines.
- Verification:
  - Checked `cmorl_cyborg/outputs/fair_compare_dual/comparable_eval_seed_0007/*/metrics_strict.json`.
  - Checked `cmorl_cyborg/outputs/fair_compare_dual/comparable_eval_seed_0007/*/metrics_hybrid.json`.
  - Checked `cmorl_cyborg/outputs/fair_compare_dual/comparable_eval_seed_0007/*/archive_diagnostics.json`.
  - Checked `cmorl_cyborg/outputs/fair_compare_dual/comparable_compare_seed_0007/table_a_summary.json`.
- Notes:
  - 这是一次**可比的单种子门控结论**，不是最终论文结论；但它已经足够作为“下一步研发方向”的决策依据。
  - **下一步进入 mainline A / CVaR conservative branch。**

## Task 4 后续计划

### 一、当前结论

目前 Task 4 的工程链路已经基本补齐：

- T4-1：schema 验收与字段冻结已完成
- T4-2 / T4-4：selector 语义与 CLI 元信息已完成
- T4-3 / T4-5：archive-aware evaluate 与配置已完成
- T4-7 / T4-8：archive diagnostics 与 compare/export pipeline 已完成

但 T4-6 目前仍然只是 **formal-lite 流水线验证**，不能作为最终科学结论。原因是：

- `Dual-Archive` 使用的是一个非常小的单 seed smoke run
- `Original Stage2` / `AdaCS-DCS` 使用的是已有正式 `seed_0007` buffer

因此，这一轮结果只能证明：

- Task 4 的评估、导表、部署选择链路已经打通
- 但还不能证明 `Dual-Archive` 是否已经足够作为正式主方法

### 二、核心问题

当前最关键的门控信号是：

- `strict_hit_rate = 0`
- `hybrid_fallback_rate = 1.0`

这意味着：

- `A_cons` 目前还没有形成真正可部署的候选集合
- 当前 hybrid 选择主要仍靠 fallback 在工作
- `Dual-Archive` 的结构组织本身是否已经足够有效，仍然需要在 **正式可比实验** 中验证

如果这一模式在完整、可比的正式实验中仍然持续出现，那么更可能说明：

- 双档案解决了一部分“候选组织”问题
- 但 conservative branch 自身仍然没有稳定交付能力
- 下一步应转向 **mainline A / CVaR conservative branch**

### 三、后续执行步骤

#### Step N1：补齐可比的 Dual-Archive 正式 run

目标：让 `Dual-Archive Stage2` 与 `Original Stage2` / `AdaCS-DCS` 处于同等比较条件。

执行要求：

- 使用与现有 fair / original / adacs 正式线一致的：
  - `stage1_buffer`
  - `seed`
  - `max_episode_steps`
  - `model.hidden_size`
  - `total_timesteps_per_update`
  - `extension_rounds`
  - `constrained_updates`
  - 其他关键训练预算参数
- 优先先跑 `seed_0007`
- 输出目录单独命名，避免与 formal-lite smoke 混淆

记录要求：

- 在 `Task 4 Execution Log` 末尾新增：
  - `Step T4-6a: Comparable Dual-Archive run`
- `Notes` 中明确说明该 run 是否已与基线预算对齐

#### Step N2：统一评估三组方法

目标：对三种方法都生成正式三口径结果。

方法组固定为：

- `Original Stage2`
- `AdaCS-DCS`
- `Dual-Archive Stage2`

每组都必须导出：

- `metrics_union.json`
- `metrics_strict.json`
- `metrics_hybrid.json`
- `archive_diagnostics.json`

记录要求：

- 在 `Task 4 Execution Log` 末尾新增：
  - `Step T4-6b: Comparable evaluation outputs`
- `Result` 中写明三组方法的输出路径
- `Verification` 中确认三类 metrics 与 diagnostics 文件均存在

#### Step N3：重新导出正式表格

目标：形成真正可用于决策的初版主表。

必须导出：

- Table A：只看 union
- Table B Strict
- Table B Hybrid

要求：

- 三组方法都必须出现在表中
- 不再混用 smoke-only 与正式 buffer
- 导出结果路径写入 `task4.md`

记录要求：

- 在 `Task 4 Execution Log` 末尾新增：
  - `Step T4-6c: Comparable tables`
- `Result` 中列出：
  - `table_a_metrics.csv`
  - `table_b_strict.csv`
  - `table_b_hybrid.csv`

#### Step N4：做门控判断

目标：决定下一步继续写作还是进入 mainline A。

判断规则固定如下：

**保留 Dual-Archive 主线** 的条件：

- `strict_hit_rate` 明显上升
- `hybrid_fallback_rate` 明显下降
- Table A 没有明显变差
- `mean_violation` / `high_disruption` / `final_critical_compromised` 没有恶化

**转入 mainline A / CVaR conservative branch** 的条件：

- `strict_hit_rate` 仍接近 0
- `hybrid_fallback_rate` 仍接近 1
- strict miss 仍频繁
- fallback 仍是主要工作模式
- 保守分支没有稳定交付候选

记录要求：

- 在 `Task 4 Execution Log` 末尾新增：
  - `Step T4-6d: Decision gate`
- `Notes` 中必须明确写成一句中文结论：
  - `下一步继续冻结 Dual-Archive 并进入写作`
  - 或
  - `下一步进入 mainline A / CVaR conservative branch`

### 四、记录规则

后续每完成一个步骤，都继续在当前 `Task 4 Execution Log` 末尾追加中文条目，条目格式保持不变：

- `Step`
- `Status`
- `Files changed`
- `Result`
- `Verification`
- `Notes`

### 五、检查清单

后续执行时至少检查以下项目：

#### 配置对齐检查

- Dual-Archive 正式 run 的关键训练参数必须与基线一致

#### 输出完整性检查

- 三种方法都必须生成：
  - `union`
  - `strict`
  - `hybrid`
  - `archive_diagnostics`

#### 表格完整性检查

- 三组方法都必须进入：
  - Table A
  - Table B Strict
  - Table B Hybrid

#### 门控指标检查

- `strict_hit_rate`
- `hybrid_fallback_rate`
- `strict_candidate_count`
- `mean_violation`
- `high_disruption_action_rate`
- `final_critical_compromised_hosts`

#### 记录完整性检查

- 每个后续步骤完成后，都必须把结果继续写入 `task4.md`

### 六、执行假设

- 现有 T4-1、T4-2/T4-4、T4-3/T4-5、T4-7/T4-8 记录保持不动
- T4-6 当前继续保持 `partial` 状态，直到完成真正可比的正式实验矩阵
- 本计划段落作为后续推进的统一指引，不替代后续新增的执行日志
- 后续所有实验结果继续写入 `task4.md`，不另起独立记录文件

## Task 4 结果复盘与主线 B 修正计划

以下内容作为对 `T4-6d` 的后续复盘与纠偏说明。`T4-6d` 应视为**未修正 B 前的 provisional gate**，不是最终方法判决。

### 一、修正后的当前结论

- 当前结果**不支持**“union front 更强”
- 当前结果**不支持**“strict candidate pool 更干净”
- 当前结果显示：
  - `strict_candidate_count = 0`
  - `strict_hit_rate = 0`
  - `hybrid_fallback_rate = 1.0`
- 当前结果说明的不是“只剩 tail-risk”，而是：
  - `A_cons` 还没有真正建立起来
  - B 还没有被公平地按设计意图运行起来

因此，不应仅凭当前结果直接宣判必须切到 mainline A。

### 二、根本原因

1. **`A_cons` 语义字段缺失**
   - `cons_records` 中大量 Stage-1 seed 记录缺少：
     - `mean_violation`
     - `near_feasible_flag`
     - `tight_feasible_flag`
     - `high_disruption_action_rate`
     - `final_critical_compromised_hosts`
   - strict selector 实际依赖的就是这些字段，因此 strict pool 会被结构性清空

2. **conservative routing 的 cost gate 与 reward 符号失配**
   - 当前 `cons_thresholds.cost_margin = 0.0`
   - 但当前 child 的 `cost_return` 全为负值
   - 导致即使 child 已经 `tight_feasible = True`，仍可能进不了 `cons`

3. **`uc` 接纳条件过宽**
   - `delta_eu / delta_coverage / novelty / spread_gain` 当前阈值过低
   - 导致 `uc` 吸收了几乎所有新增 child
   - 双档案退化成“冻结的 cons + 持续膨胀的 uc”

4. **conservative branch 本身没有产出成功 child**
   - 当前两轮里 `cons_generated_policy_ids` 为空
   - 成功 child 基本全部来自 `adacs_dcs -> uc`

### 三、主线 B 的最小改良方案

**B1. 补齐 `A_cons` 语义字段**

- 在 Stage-1 seed 进入 `A_cons` 时，统一补齐：
  - `security_return`
  - `business_return`
  - `cost_return`
  - `mean_violation`
  - `feasible_flag`
  - `near_feasible_flag`
  - `tight_feasible_flag`
  - `high_disruption_action_rate`
  - `final_critical_compromised_hosts`
- 若某记录无法得到 strict 所需字段，则在文档中明确：**它不应计入 strict candidate pool**

**B2. 修正 conservative routing 的 cost gate**

- 不再把 `cost_return >= 0.0` 作为 conservative entry 条件
- 改成**相对 parent 的 cost 退化容忍**
- 默认规则固定为：
  - `cost_return >= base_cost_return - 3.0`
- 文档里明确说明：这是为了避免 reward 符号失配把本来可行的保守 child 全挡在 `cons` 外

**B3. 收紧 `uc` 接纳条件**

- 把 `uc` 的默认“材料性增益”阈值写死为：
  - `delta_coverage >= 0.01`
  - `delta_eu >= 0.001`
  - `novelty_score >= 5.0`
  - `spread_gain >= 5.0`
- 记录里明确说明：极小的数值扰动不再视为足够进入 `uc` 的理由

**B4. 单独验证 conservative branch 的生成能力**

- 在下一轮 B 修正验证中，单独记录：
  - `cons_attempted_children`
  - `cons_successful_children`
  - `cons_routed_children`
  - `cons_rejected_by_cost_gate`
  - `cons_rejected_by_feasibility`
- 文档里明确：这一步的目标不是提升分数，而是判断 conservative branch 到底是“长不出来”还是“长出来后被路由丢掉”

### 四、重新判门规则

把“是否转向 A”的判断改成一个新的、显式的二次门控，不再沿用旧的直接结论。

继续保留 B 的条件固定为：

- `cons_records` 中用于 strict 的记录都具备完整语义字段
- 至少有 `1` 个 Stage-2 child 被成功路由到 `cons`
- `strict_candidate_count > 0`
- `strict_hit_rate > 0`
- `final_critical_compromised_hosts` 相比当前 Dual-Archive 结果不再恶化

转向 `mainline A / CVaR conservative branch` 的条件固定为：

- 完成上述 B 修正后，仍然出现：
  - `strict_candidate_count = 0`
  - 或 `strict_hit_rate = 0`
  - 或 `cons` 仍无新增 routed child
  - 或 `final_critical_compromised_hosts` 仍未改善

只有在修正后的 B 仍无法建立 strict 候选池时，转向 mainline A 才是更有把握的主线选择。

### 五、记录规则

- 以后如果执行 B 修正验证，不再沿用旧的“直接切 A”叙述
- 新的实验记录应按：
  - `B-fix validation`
  - `strict pool restoration`
  - `A-decision gate`
  三步来追加

## Task 4 B-fix Execution Log

### Step T4-B1: 主线 B 最小改良实现
- Status: done
- Files changed:
  - `CybORG_plus_plus/cmorl_minicage/algorithms/dual_archive.py`
  - `CybORG_plus_plus/cmorl_minicage/train_stage2.py`
  - `CybORG_plus_plus/cmorl_minicage/evaluate.py`
  - `CybORG_plus_plus/cmorl_minicage/select_policy.py`
  - `CybORG_plus_plus/cmorl_minicage/config.py`
  - `CybORG_plus_plus/cmorl_cyborg/config.py`
  - `CybORG_plus_plus/cmorl_minicage/buffer.py`
  - `CybORG_plus_plus/cmorl_minicage/configs/ablation/stage2_dual_archive.yaml`
  - `CybORG_plus_plus/cmorl_cyborg/configs/ablation/stage2_dual_archive.yaml`
  - `CybORG_plus_plus/cmorl_cyborg/configs/paper/fair_compare_dual/stage2_dual_archive_fair_seed_0007.yaml`
  - `task4.md`
- Result:
  - 在 dual-archive 共享逻辑中实现了 `b_fix_v1` 规则：Stage-1 seed 语义回填、relative cost gate、收紧 `uc` 材料性增益阈值、以及 structured route diagnosis。
  - `select_policy.py` 与 `evaluate.py` 现在都会通过同一套 archive normalization 读取 dual buffer，避免训练态、CLI、评估态口径漂移。
  - `train_stage2.py` 的 dual 分支新增了 `cons_attempted_children`、`cons_successful_children`、`cons_routed_children`、`cons_rejected_by_cost_gate`、`cons_rejected_by_feasibility` 计数，并把 `archive_rule_version` 和 `archive_seed_thresholds` 写入 metadata。
  - buffer schema 提升到 `0.4.1`，保持 additive-only 兼容。
- Verification:
  - 运行 `py_compile` 通过：
    - `dual_archive.py`
    - `train_stage2.py`
    - `evaluate.py`
    - `select_policy.py`
    - `config.py`
    - `cmorl_cyborg/config.py`
    - `buffer.py`
  - 纯逻辑检查确认 relative cost gate 与 `uc` routing 行为符合预期：
    - `c_ok -> accepted_cons`
    - `c_bad_cost -> rejected_cost_gate`
    - `c_uc -> accepted_uc`
- Notes:
  - 这一轮先修的是“能否被公平测试”的结构问题，不是 CVaR 或 risk-aware critic。

### Step T4-B2: B-fix smoke validation 与 strict pool restoration
- Status: done
- Files changed:
  - `task4.md`
- Result:
  - 使用 `seed_0007` Stage-1 buffer 跑通了一次 CybORG B-fix smoke：
    - 输出路径：`/tmp/t4_bfix_smoke/run_17393107/solution_buffer.json`
  - smoke buffer 已带有：
    - `schema_version = 0.4.1`
    - `archive_rule_version = b_fix_v1`
    - `archive_seed_thresholds = {d_business: -144.6052, d_cost: -23.0158}`
  - Stage-1 `cons_records` 的 strict 相关字段已完成回填，不再因为缺字段被结构性清空：
    - `strict_eligible = 11`
    - `missing = 0`
  - 但 smoke 结果也很清楚地说明：
    - `cons_attempted_children = 9`
    - `cons_successful_children = 0`
    - `cons_routed_children = 0`
    - `cons_rejected_by_cost_gate = 0`
    - `cons_rejected_by_feasibility = 0`
    - 当前 `cons` 分支依然没有成功长出新的 Stage-2 child
  - strict selector smoke 结果为 miss：
    - `source_set=cons`
    - `selector_mode=strict`
    - `miss_reason=no_strict_candidate`
- Verification:
  - Stage-1 seed normalization check：
    - `records = 18`
    - `cons = 18`
    - `eligible = 18`
    - `missing = 0`
  - 单条 seed 语义回填样例：
    - `policy_id = stage1_pref_000_ckpt_096`
    - `mean_violation = 2.0483`
    - `high_disruption_action_rate = 0.92`
    - `final_critical_compromised_hosts = 0.75`
    - `eligible = True`
    - `tight = False`
    - `near = False`
  - smoke summary：
    - `cons_generated_policy_ids = []`
    - `uc_generated_policy_ids = ['stage2_ext_000_obj_0', 'stage2_ext_002_obj_2']`
    - `discarded_policy_ids = ['stage2_ext_001_obj_1', 'stage2_ext_003_obj_0', 'stage2_ext_004_obj_1', 'stage2_ext_005_obj_2']`
- Notes:
  - 这一步已经验证：strict pool restoration 本身是成功的，旧问题从“字段缺失导致 strict 池为空”转成了“conservative branch 仍未生成可用 child”。

### Step T4-B3: B-fix smoke deploy semantics
- Status: done
- Files changed:
  - `task4.md`
- Result:
  - 已完成 smoke buffer 的全模式评估：
    - 输出目录：`/tmp/t4_bfix_smoke_eval`
  - 关键结果如下：
    - `strict_candidate_count = 0`
    - `strict_hit_rate = 0.0`
    - `hybrid_fallback_rate = 1.0`
    - `from_adacs_to_uc = 2`
    - `from_original_to_cons = 0`
    - `from_adacs_to_cons = 0`
  - strict selector CLI 也与正式评估一致，返回：
    - `selection_status = miss`
    - `miss_reason = no_strict_candidate`
- Verification:
  - `metrics_strict.json`：
    - `selected_count = 0`
    - `strict_miss_count = 6`
  - `metrics_hybrid.json`：
    - `selected_count = 6`
    - `fallback_count = 6`
    - `final_critical_compromised_hosts = 0.8125`
    - `high_disruption_action_rate = 0.9208`
  - `archive_diagnostics.json`：
    - `strict_candidate_count = 0`
    - `strict_hit_rate = 0.0`
    - `hybrid_fallback_rate = 1.0`
- Notes:
  - smoke 结果说明：B-fix 已经修复了 `cons` 语义缺字段问题，但还没有修复“`cons` 没有 strict candidate、hybrid 全靠 fallback”的核心现象。
  - 下一步仍然需要看 fair-budget `seed_0007` 正式门控，判断这是不是 smoke 预算太小导致的，还是结构修正后依然无效。

### Step T4-B4: fair-budget seed_0007 B-fix validation
- Status: done
- Files changed:
  - `task4.md`
- Result:
  - 已完成 fair-budget `seed_0007` 的正式 B-fix Dual-Archive run：
    - 输出路径：`/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/fair_compare_dual/b_fix_dual_archive_stage2_fair/seed_0007/run_0810320f/solution_buffer.json`
  - 正式 run 的核心结果如下：
    - `num_records = 22`
    - `num_cons_records = 11`
    - `num_uc_records = 7`
    - `cons_attempted_children = 18`
    - `cons_successful_children = 0`
    - `cons_routed_children = 0`
    - `cons_rejected_by_cost_gate = 0`
    - `cons_rejected_by_feasibility = 0`
  - 两轮结果都一致：
    - `cons_generated_policy_ids = []`
    - 所有新增 routed child 仍然都进了 `uc`
  - 正式 run 的 strict pool 结果：
    - `strict_eligible = 11`
    - `strict_candidate_count = 0`
    - `stage2_in_cons = []`
    - `stage2_in_uc = ['stage2_ext_000_obj_0', 'stage2_ext_004_obj_1', 'stage2_ext_005_obj_0', 'stage2_ext_008_obj_2']`
  - strict selector CLI 在正式 run 上继续返回：
    - `selection_status = miss`
    - `miss_reason = no_strict_candidate`
- Verification:
  - `schema_version = 0.4.1`
  - `archive_rule_version = b_fix_v1`
  - `archive_seed_thresholds = {d_business: -144.6052, d_cost: -23.0158}`
  - `stage2_summary.json` 显示：
    - Round 0: `cons_attempted_children = 9`, `cons_successful_children = 0`
    - Round 1: `cons_attempted_children = 9`, `cons_successful_children = 0`
- Notes:
  - 这一轮是比 smoke 更硬的结论：在 fair-budget 下，`cons` 分支依旧没有成功生成任何 child，也没有任何 Stage-2 child 被路由到 `cons`。
  - 这意味着 B-fix 虽然修复了 strict 字段缺失，但没有修复 conservative branch 的生成问题。

### Step T4-B5: A-decision gate after B-fix
- Status: done
- Files changed:
  - `task4.md`
- Result:
  - 根据 `Task 4 结果复盘与主线 B 修正计划` 中的二次门控规则，正式 B-fix run 已满足转向 A 的条件：
    - `strict_candidate_count = 0`
    - `cons` 仍无新增 routed child
    - strict selector 继续 miss
  - 因此，Task 4 的修正后结论更新为：
    - **主线 B 的最小改良已经完成并被公平测试，但仍未建立 strict 候选池；下一步应正式转向 `mainline A / CVaR conservative branch`。**
- Verification:
  - smoke B-fix：
    - `strict_candidate_count = 0`
    - `strict_hit_rate = 0.0`
    - `hybrid_fallback_rate = 1.0`
  - fair-budget B-fix：
    - `cons_successful_children = 0`
    - `cons_routed_children = 0`
    - `strict_candidate_count = 0`
    - strict CLI `miss_reason = no_strict_candidate`
- Notes:
  - 这次转向 A 的依据比之前更扎实，因为它不是“字段没补齐的旧 B”，而是“修正过语义、cost gate、uc 阈值和诊断后的 B”。
  - 因而，后续如果进入 `mainline A`，应视为在完成一次公平的 B-fix 验证后作出的主线切换，而不是为了继续做实验而提前放弃 B。
