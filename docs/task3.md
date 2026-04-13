# Task 3 - 在 Cyber-CMORL 中实现 Dual-Archive Stage-2（面向 Codex）

## 0. 任务目的

本任务不是继续把 `AdaCS-DCS` 当成单一 Stage-2 的打分增强版，而是基于当前实验事实，把 `Original Stage2` 与 `AdaCS-DCS` 升格为 **同一次 Stage-2 内部的两种扩展角色**：

- `conservative-volume` 分支：保留 `Original Stage2` 更强的性质
  - `HV`
  - `Pareto count`
  - `tight selected-policy feasible rate`
  - `cost`
  - `high-disruption 更低`
  - `tight feasible-set retention`
- `utility-coverage` 分支：保留 `AdaCS-DCS` 更强的性质
  - `EU`
  - `coverage`
  - `unique assigned policies`
  - `front spread / sparsity`
  - `selected-policy security`
  - `business`
  - `mean violation`
  - `critical impact count`

最终目标：把当前单档案 Stage-2 改造成 **双档案、双分支、双选择器** 的结构化 Stage-2，同时尽量复用现有代码，不重写 PPO/IPO 内核。

---

## 1. 当前代码事实（必须先对齐）

### 1.1 代码主入口

当前正式环境 `cmorl_cyborg/train_stage2.py` 只是一个薄封装：它把环境类替换为 `CybORGMORLEnv`，然后直接复用 `cmorl_minicage.train_stage2` 的主逻辑。因此，本任务的主要改动应集中在：

- `cmorl_minicage/train_stage2.py`
- `cmorl_minicage/buffer.py`
- `cmorl_minicage/config.py`
- `cmorl_minicage/algorithms/assignment.py`
- `cmorl_minicage/select_policy.py`
- 新增 `cmorl_minicage/algorithms/dual_archive.py`

而 `cmorl_cyborg/` 只需要最小包装与配置透传，不要在 `cmorl_cyborg/train_stage2.py` 里复制主逻辑。

### 1.2 当前 Stage-2 的结构

`cmorl_minicage/train_stage2.py` 当前流程是：

1. 读取 `stage1_buffer`
2. 从 `records` 做 `nondominated_filter`
3. 按 `crowding` 或 `adaptive` 选 `extension_records`
4. 对每个 parent、每个 objective 方向做 constrained extension
5. 对每条路径只保留 `best_feasible`
6. 新 child 直接 append 回统一 `records`
7. 最后保存：
   - `solution_buffer.json`
   - `pareto_front_stage2.json`
   - `stage2_summary.json`
   - `method_diagnostics.json`

也就是说，当前系统只有 **一个档案 / 一个记录池**。

### 1.3 当前 schema 与选择接口的限制

- `cmorl_minicage/buffer.py` 的 `policy_record()` 只支持单一记录语义，没有 archive role、operator source、selector 相关字段。
- `cmorl_minicage/config.py` 的 `Stage2Config` 目前没有 dual-archive 所需配置。
- `cmorl_minicage/algorithms/assignment.py` 目前只支持单一 `assign_policy(preference, policy_set)`。
- `cmorl_minicage/select_policy.py` 目前只支持从：
  - `pareto_front`
  - `records`
  两种 source set 做普通 SMP 选择。

---

## 2. 本任务的核心设计

## 2.1 不是“参数分支”，而是“结构化双档案”

不要把本任务实现成：

- branch A 用 Original 参数
- branch B 用 AdaCS-DCS 参数
- 最后仍然都写回同一个 `records`

这只是混合调参，不是双档案方法。

本任务要求实现成：

- `A_cons`: conservative archive
- `A_uc`: utility-coverage archive
- `cons branch operator`: 先复用 `Original Stage2`
- `uc branch operator`: 先复用 `AdaCS-DCS`
- child 最终进入哪个 archive，由 **评估结果路由** 决定，而不是由 operator 来源硬绑定

### 2.2 角色定义

#### `A_cons`
专门维护更偏保守、体积型、可保留 tight-feasible 候选的前沿子集。

优先吸收更符合以下性质的 child：

- `tight_feasible_flag` 或 `near_feasible_flag`
- `cost_return` 更好
- `high_disruption_rate` 更低
- `mean_violation` 不高
- 允许保持较高 `HV` / `Pareto count`

#### `A_uc`
专门维护更偏 utility / coverage / assignment diversity / selected-policy trade-off 的前沿子集。

优先吸收更符合以下性质的 child：

- `delta_eu` 更高
- `delta_coverage` 更高
- `assignment_diversity_gain` 更高
- `spread_gain` 更高
- `security_return` / `business_return` 更好
- `critical_impact_count` 更低

---

## 3. 总体实现原则

1. **先做编排层改造，不先重写优化器。**
2. **优先复用现有两种 Stage-2 扩展算子。**
3. **先做互斥归档，不做一条 child 同时进两个 archive。**
4. **先做 strict / hybrid selector，再考虑更复杂的 risk-aware 选择器。**
5. **保证旧配置还能跑通。** 旧的单档案逻辑不能被直接删掉，应通过 config 开关兼容。

---

## 4. 需要新增/修改的文件

## 4.1 新增文件

### A. `cmorl_minicage/algorithms/dual_archive.py`
新增 `DualArchiveManager`，负责：

- 管理 `cons_records`
- 管理 `uc_records`
- 管理 `union_records`
- 路由 child
- 选择 parent
- 刷新 union front
- strict / hybrid selector

### B. 新增配置模板
建议新增以下 YAML：

- `cmorl_minicage/configs/ablation/stage2_dual_archive.yaml`
- `cmorl_cyborg/configs/ablation/stage2_dual_archive.yaml`（如 formal 线已有配置镜像体系）

---

## 4.2 修改文件

### A. `cmorl_minicage/buffer.py`
扩展 `policy_record()` schema。

### B. `cmorl_minicage/config.py`
扩展 `Stage2Config`，新增 dual-archive 配置。

### C. `cmorl_minicage/train_stage2.py`
这是本任务的主战场：

- 从单档案 Stage-2 改成双档案编排
- 支持 `cons branch` 和 `uc branch`
- 支持 route-and-insert
- 支持双分支 round summary / diagnostics

### D. `cmorl_minicage/algorithms/assignment.py`
增加：

- strict selector
- hybrid selector
- 受惩罚的 fallback utility

### E. `cmorl_minicage/select_policy.py`
CLI 支持：

- `source_set=cons`
- `source_set=uc`
- `source_set=union`
- `selector_mode=strict`
- `selector_mode=hybrid`

### F. `cmorl_cyborg/train_stage2.py`
原则上只做最小透传，不复制逻辑。

---

## 5. 详细任务拆分

## T3-1 扩展 `policy_record` 与 buffer schema

### 目标
让 buffer 能表示双档案语义，而不是只有单一 `records`。

### 具体要求

#### 5.1.1 在 `policy_record()` 中新增字段
至少支持：

```python
archive_role: str | None          # "cons" | "uc" | None
operator_source: str | None       # "original" | "adacs_dcs" | None

feasible_flag: bool | None
near_feasible_flag: bool | None
tight_feasible_flag: bool | None

business_return: float | None
cost_return: float | None
security_return: float | None
mean_violation: float | None
critical_impact_count: float | None
final_critical_compromised: float | None
high_disruption_rate: float | None

delta_hv: float | None
delta_eu: float | None
delta_coverage: float | None
novelty_score: float | None
assignment_diversity_gain: float | None
spread_gain: float | None
```

#### 5.1.2 在 `save_policy_buffer()` 的 metadata.extra 中预留
- `archive_mode`
- `cons_policy_ids`
- `uc_policy_ids`
- `selector_defaults`

### 验收标准
- 旧 buffer 仍可读取
- 新 buffer 中每条 Stage-2 child record 能记录 archive role 与 operator source
- `pareto_front` 仍可按旧逻辑保存

---

## T3-2 在 `config.py` 中新增 dual-archive 配置

### 目标
让新逻辑通过 config 驱动，而不是写死。

### 具体要求

在 `Stage2Config` 中新增：

```python
archive_mode: str = "single"      # "single" | "dual"
num_cons_parents: int = 3
num_uc_parents: int = 3
route_mode: str = "exclusive"     # 先只支持 exclusive

cons_operator_mode: str = "original"
uc_operator_mode: str = "adacs_dcs"

cons_thresholds: dict[str, float] = {
    "violation": 0.5,
    "high_disruption": 1.0,
    "cost_margin": 0.0,
}

uc_thresholds: dict[str, float] = {
    "delta_eu": 0.0,
    "delta_coverage": 0.0,
    "novelty": 0.0,
    "spread_gain": 0.0,
}

selector_mode_default: str = "strict"
selector_penalty_weights: dict[str, float] = {
    "violation": 1.0,
    "high_disruption": 1.0,
    "final_critical": 1.0,
}
```

### 注意
- 默认仍应保持 `archive_mode="single"`，避免破坏旧实验
- `num_cons_parents + num_uc_parents` 不要求等于 `num_extension_policies`，但推荐在加载配置时检查一致性或给 warning

### 验收标准
- 旧 config 不报错
- 新 dual-archive config 能完整加载

---

## T3-3 新建 `DualArchiveManager`

### 目标
实现双档案状态管理与路由逻辑。

### 具体要求

新增类：

```python
class DualArchiveManager:
    def __init__(self, ...):
        self.cons_records = []
        self.uc_records = []
        self.union_records = []
```

必须至少实现以下方法：

### 5.3.1 `seed_from_stage1(records)`
- 输入：Stage-1 records
- 输出：初始化后的 `cons_records` / `uc_records`
- 第一版可简单做：
  - 对 Stage-1 Pareto points 统一评估后再 route
  - 若没有足够信息，则默认所有 Stage-1 Pareto points 先进入 `cons_records`
  - 同时允许 top-n utility/coverage 候选进入 `uc_records`

### 5.3.2 `is_cons_candidate(record)`
第一版建议逻辑：

```text
if tight_feasible_flag or near_feasible_flag:
    if mean_violation <= threshold
       and high_disruption_rate <= threshold
       and cost_return >= threshold:
           True
```

注意：
- 不要用 `business_return` 作为 conservative archive 的核心定义条件
- 因为当前结果里 `business_return` 更偏 AdaCS-DCS 强项

### 5.3.3 `is_uc_candidate(record)`
第一版建议逻辑：

```text
if delta_eu > eps_eu
   or delta_coverage > eps_cov
   or novelty_score > eps_nov
   or spread_gain > eps_spread:
       True
```

第二版再把：
- `security_return`
- `business_return`
- `critical_impact_count`
- `assignment_diversity_gain`
补进去。

### 5.3.4 `route_and_insert(record)`
先做互斥版：

```text
if is_cons_candidate(record):
    -> cons_records
elif is_uc_candidate(record):
    -> uc_records
else:
    -> discard
```

### 5.3.5 `select_cons_parents(n)`
按 conservative score 排序选 parent。

第一版建议分数：

```text
score_cons =
    + feasible_score
    + cost_margin
    - mean_violation
    - high_disruption_rate
    + crowding_in_cons
```

### 5.3.6 `select_uc_parents(n)`
按 utility-coverage score 排序选 parent。

第一版建议分数：

```text
score_uc =
    + novelty_score
    + delta_eu
    + delta_coverage
    + spread_gain
```

### 5.3.7 `refresh_union_front()`
- `union_records = cons_records + uc_records`
- 对 union 做 `nondominated_filter`
- 保存当前 union pareto front

### 5.3.8 `select_strict_policy(preference)`
- 只在 `cons_records` 中选
- 先过滤 `tight_feasible_flag or near_feasible_flag`
- 再按 utility 最大选

### 5.3.9 `select_hybrid_policy(preference)`
- 先尝试 `select_strict_policy`
- 若无候选，则在 `union_records` 中选：

```text
utility(preference, objective_vector)
- lam_v * mean_violation
- lam_d * high_disruption_rate
- lam_k * final_critical_compromised
```

### 验收标准
- manager 可独立单测
- 输入一组 mock records 后，能正确完成 route / parent select / strict / hybrid select

---

## T3-4 改造 `cmorl_minicage/train_stage2.py`

### 目标
把当前单档案 Stage-2 编排成双档案 Stage-2。

### 原则
**不要重写 IPO/PPO 内核；先复用现有两套 operator。**

### 具体要求

#### 5.4.1 保留旧逻辑入口
当前：

```python
if archive_mode == "single":
    # 走旧版单档案逻辑
```

#### 5.4.2 新增 dual-archive 分支
新逻辑：

1. 读取 Stage-1 buffer
2. 初始化 `DualArchiveManager`
3. 用 Stage-1 records seed 两个 archive
4. 每个 round：
   - `cons_parents = manager.select_cons_parents(num_cons_parents)`
   - `uc_parents = manager.select_uc_parents(num_uc_parents)`
5. 对 `cons_parents` 调 conservative operator
6. 对 `uc_parents` 调 utility-coverage operator
7. child 统一评估后 route-and-insert
8. refresh union front
9. 写 round summaries / diagnostics
10. 最终保存 buffer

#### 5.4.3 conservative operator 的第一版
直接复用当前 `Original Stage2` 路径：

- `selection.mode = crowding`
- `ipo.beta_mode = fixed`
- 固定 `beta`
- 走当前 constrained extension 流程

实现方式：
- 不要复制一整份 train loop
- 抽出一个较小粒度函数，例如：

```python
run_stage2_extension_for_parent(
    base_record,
    objective_idx,
    operator_mode,
    ...
)
```

其中：
- `operator_mode="original"` 对应 crowding + fixed beta 风格
- `operator_mode="adacs_dcs"` 对应 adaptive selection + dynamic beta 风格

#### 5.4.4 utility-coverage operator 的第一版
直接复用当前 AdaCS-DCS 路径：

- adaptive selection 打分组件
- dynamic beta
- 当前 IPOTrainer.update(..., beta_override=...) 逻辑

#### 5.4.5 关键要求：child 归档由结果决定，不由 operator 来源决定
即：

- `operator_source` 记录 child 来自 `original` 还是 `adacs_dcs`
- 但最终 `archive_role` 由 `route_and_insert()` 决定

### 验收标准
- `archive_mode="single"` 时行为与旧版基本一致
- `archive_mode="dual"` 时可完整跑通
- `stage2_summary.json` 和 `method_diagnostics.json` 中能看到：
  - cons / uc 两路 parent ids
  - child 的 archive_role
  - operator_source

---

## T3-5 增强诊断输出

### 目标
让新方法可解释，便于后续写论文和 debug。

### 具体要求

在 `stage2_summary.json` 和 `method_diagnostics.json` 中新增：

- `archive_mode`
- `cons_parent_ids`
- `uc_parent_ids`
- `cons_generated_policy_ids`
- `uc_generated_policy_ids`
- 每个 child 的：
  - `archive_role`
  - `operator_source`
  - `delta_eu`
  - `delta_coverage`
  - `spread_gain`
  - `tight_feasible_flag`
  - `high_disruption_rate`
  - `mean_violation`

### 验收标准
- 不需要再次从 CSV 人工拼接，单看 summary / diagnostics 就能知道 child 为什么进了哪个 archive

---

## T3-6 改造 policy selection 接口

### 目标
让 deployment selection 不再只有普通 SMP。

### 具体要求

#### 5.6.1 修改 `cmorl_minicage/algorithms/assignment.py`
新增函数：

- `assign_policy_strict(preference, policy_set)`
- `assign_policy_hybrid(preference, policy_set, penalty_weights)`

或封装成：

- `assign_policy(preference, policy_set, mode="plain", penalty_weights=None)`

#### 5.6.2 修改 `cmorl_minicage/select_policy.py`
CLI 新增参数：

- `--source-set cons|uc|union|pareto|records`
- `--selector-mode plain|strict|hybrid`

行为：

- `source_set=cons`：只从 `cons_records` 选
- `source_set=uc`：只从 `uc_records` 选
- `source_set=union`：从两者并集选
- `selector_mode=strict`：只允许 strict selection 逻辑
- `selector_mode=hybrid`：safe 优先、union fallback

### 验收标准
- CLI 能从 dual-archive buffer 中选策略
- strict / hybrid 行为与设计一致

---

## T3-7 新的 buffer 保存格式

### 目标
让 `solution_buffer.json` 明确携带双档案状态。

### 具体要求

在 `save_policy_buffer()` 的 payload 中新增（不破坏旧字段）：

```json
{
  "records": [...],
  "pareto_front": [...],
  "cons_records": [...],
  "uc_records": [...],
  "union_front": [...]
}
```

如不想复制完整 record，可至少保存 `policy_id` 列表，但更推荐直接保存完整列表，便于选择器与评估复用。

### 验收标准
- 旧代码读取不报错
- 新代码可直接从 buffer 恢复两个 archive

---

## T3-8 评估与论文表的最小支持

### 目标
虽然本任务不要求一次性重写全套 Table A / B pipeline，但至少要给出可用接口。

### 具体要求

#### 5.8.1 Table A
- 默认对 `union_front` 做 Pareto filter
- 计算 HV / EU / SP / coverage

#### 5.8.2 Table B
至少能支持两种选择模式：

- `strict`：优先 `cons_records`
- `hybrid`：若 `cons_records` 无候选，则回退到 `union_records`

#### 5.8.3 本任务可以先不彻底改 `evaluate.py`
允许第一版通过：
- `select_policy.py` + 现有评估脚本 组合验证

但要在 `task3.md` 中明确标记：
- `evaluate.py` 的正式双档案整合属于下一轮任务

### 验收标准
- 至少能从 dual-archive buffer 中手动或脚本化地跑出：
  - union set-level 结果
  - strict selector deployment 结果
  - hybrid selector deployment 结果

---

## 6. 实现顺序（Codex 必须遵守）

1. **先改 schema 和 config**
   - `buffer.py`
   - `config.py`
2. **实现 `DualArchiveManager`**
3. **给 `train_stage2.py` 增加 `archive_mode="dual"` 分支**
4. **先复用现有两种 operator，不重写 IPO/PPO 内核**
5. **接入 strict / hybrid selector**
6. **扩展 `select_policy.py`**
7. **补最小 smoke / ablation 配置**
8. **最后再考虑正式整合进 Table A / B 导表流程**

不要一开始就：
- 重写 `evaluate.py`
- 重写 IPO loss
- 重写 Stage-1
- 引入 risk-aware critics

---

## 7. 非目标（本任务暂不做）

以下内容不是本任务范围：

1. 不实现 risk-aware distributional critic
2. 不实现 OCE / CVaR 新约束
3. 不重写 Stage-1
4. 不把 child 同时插入两个 archive
5. 不在第一版里做跨档案 handoff / repair
6. 不在第一版里改 formal 论文表全部脚本
7. 不把 `cmorl_cyborg/` 和 `cmorl_minicage/` 逻辑分叉复制

---

## 8. Smoke 验证建议

在新增 dual-archive 配置后，至少验证：

### 8.1 结构正确性
- 能跑完 1 个 stage1 buffer 上的 dual stage2
- 输出 `solution_buffer.json`
- buffer 中包含：
  - `cons_records`
  - `uc_records`
  - `union_front`

### 8.2 语义正确性
- 至少有部分 child 进入 `cons_records`
- 至少有部分 child 进入 `uc_records`
- `operator_source` 与 `archive_role` 不完全一一绑定

### 8.3 选择器正确性
- `select_policy.py --source-set cons --selector-mode strict`
- `select_policy.py --source-set union --selector-mode hybrid`
都能工作

---

## 9. 建议的提交粒度

建议 Codex 分 5 个 commit：

1. `add dual-archive config and buffer schema`
2. `add DualArchiveManager and routing logic`
3. `wire dual-archive mode into train_stage2`
4. `add strict/hybrid selector and select_policy support`
5. `add dual-archive smoke config and diagnostics`

---

## 10. 本任务完成标志

满足以下条件即可视为 Task 3 完成：

- `archive_mode="dual"` 可跑通
- `solution_buffer.json` 可保存双档案状态
- `Original Stage2` 与 `AdaCS-DCS` 已在同一次 Stage-2 内被组织为两种扩展角色
- child 通过 outcome-based routing 进入 `A_cons` 或 `A_uc`
- strict / hybrid selector 可从 dual-archive buffer 选策略
- 旧版单档案配置仍可运行

---

## 11. 给 Codex 的最后提醒

本任务的价值不在于“再加两套参数”，而在于把你当前已经观察到的 **两种 Stage-2 偏好** 正式上升成一个可运行、可诊断、可写论文的方法结构。

因此请优先保证：

- 架构边界清晰
- 与当前仓库主实现兼容
- 结果可追踪
- summary / diagnostics 足够解释每个 child 为什么进了哪个 archive

先把结构搭起来，再谈第二轮性能优化。

---

## Task 3 Execution Log

### Step T3-1/T3-2: Buffer schema and dual-archive config
- Status: done
- Files changed:
  - `CybORG_plus_plus/cmorl_minicage/buffer.py`
  - `CybORG_plus_plus/cmorl_minicage/config.py`
  - `CybORG_plus_plus/cmorl_cyborg/config.py`
- Result:
  - Extended `policy_record()` with archive role, operator source, feasibility, semantic metric, and archive delta fields.
  - Extended `save_policy_buffer()` to optionally persist `cons_records`, `uc_records`, and `union_front` without removing legacy fields.
  - Added dual-archive Stage-2 config defaults to both minicage and cyborg configs, with `archive_mode` defaulting to `single`.
- Verification:
  - Loaded old minicage and cyborg Stage-2 configs and confirmed `archive_mode == "single"`.
  - Created and round-tripped a dual-archive-shaped policy buffer with `cons_records` and `union_front`.
- Notes:
  - Used `/home/waylandlee/miniconda3/envs/cc4/bin/python` from `CybORG_plus_plus` so project dependencies resolve correctly.

### Step T3-3: DualArchiveManager
- Status: done
- Files changed:
  - `CybORG_plus_plus/cmorl_minicage/algorithms/dual_archive.py`
  - `CybORG_plus_plus/cmorl_minicage/algorithms/__init__.py`
- Result:
  - Added `DualArchiveManager` with Stage-1 seeding, outcome-based exclusive routing, conservative/utility parent selection, union front refresh, and strict/hybrid selection helpers.
  - Added metric annotation for objective returns, delta expected utility, delta coverage, novelty, spread, and feasibility defaults.
- Verification:
  - Ran a mock-record smoke test covering `seed_from_stage1`, `route_and_insert`, `select_cons_parents`, `select_uc_parents`, `select_strict_policy`, and hybrid fallback.
- Notes:
  - Stage-1 seed records may appear in both seed archives for warm-start coverage; generated Stage-2 children use exclusive routing.

### Step T3-4/T3-5: Dual Stage-2 orchestration and diagnostics
- Status: done
- Files changed:
  - `CybORG_plus_plus/cmorl_minicage/train_stage2.py`
- Result:
  - Added `archive_mode == "dual"` dispatch while preserving the existing single-archive Stage-2 path.
  - Added a reusable parent/objective extension helper that keeps the existing PPO/IPO update flow intact.
  - Added dual-archive orchestration with conservative and utility-coverage branches, operator-source tracking, outcome-based routing, union front saving, and expanded round diagnostics.
- Verification:
  - Ran `py_compile` over `train_stage2.py`, `dual_archive.py`, `buffer.py`, and both config modules.
- Notes:
  - Conservative branch maps to `original` operator settings (`crowding`, fixed beta); utility-coverage branch maps to `adacs_dcs` settings (`adaptive`, dynamic beta).

### Step T3-6/T3-7: Strict/hybrid assignment and dual buffer selection
- Status: done
- Files changed:
  - `CybORG_plus_plus/cmorl_minicage/algorithms/assignment.py`
  - `CybORG_plus_plus/cmorl_minicage/algorithms/__init__.py`
  - `CybORG_plus_plus/cmorl_minicage/select_policy.py`
- Result:
  - Extended assignment to support `plain`, `strict`, and `hybrid` modes.
  - Extended `select_policy.py` with `--source-set cons|uc|union|pareto|records` and `--selector-mode plain|strict|hybrid`.
  - Added dual-buffer source resolution for conservative, utility-coverage, and union policy sets.
- Verification:
  - Ran an in-process selector smoke test using a temporary dual-archive buffer for `cons/strict` and `union/hybrid`.
  - Ran `py_compile` over `assignment.py` and `select_policy.py`.
- Notes:
  - Hybrid selection first tries strict feasible candidates, then falls back to penalized utility with metadata-provided selector weights when available.

### Step T3-8: Dual-archive smoke configs and verification
- Status: done
- Files changed:
  - `CybORG_plus_plus/cmorl_minicage/configs/ablation/stage2_dual_archive.yaml`
  - `CybORG_plus_plus/cmorl_cyborg/configs/ablation/stage2_dual_archive.yaml`
  - `CybORG_plus_plus/cmorl_minicage/select_policy.py`
- Result:
  - Added minicage and cyborg dual-archive Stage-2 config templates.
  - Kept `evaluate.py` formal dual-archive integration out of scope for this task; current validation uses buffer output plus selector CLI.
  - Made `select_policy.py` work both as a module and as a directly executed script.
- Verification:
  - Loaded both new dual-archive configs and confirmed `archive_mode == "dual"`.
  - Ran a constrained minicage dual Stage-2 smoke using an existing Stage-1 buffer; output buffer contained `cons_records`, `uc_records`, and `union_front`.
  - Ran selector CLI smoke for `--source-set cons --selector-mode strict` and `--source-set union --selector-mode hybrid`.
  - Ran an unconstrained routing smoke that confirmed `operator_source` and `archive_role` are not hard-bound: `original` generated children routed into `uc` by outcome.
  - Ran a zero-round single-mode Stage-2 compatibility smoke and confirmed legacy `records` / `pareto_front` output still saves.
  - Ran final `py_compile` over modified Python modules.
- Notes:
  - Smoke outputs were written under `/tmp/cyber_cmorl_dual_stage2_smoke*`.
