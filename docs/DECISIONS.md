# Decisions

本文档记录当前复现线中已经稳定下来的关键设计决策。每条决策尽量说明：

- 决策内容
- 采用原因
- 备选方案
- 未选原因

## D-001 保持 `cmorl_minicage` 与仓库其他主线隔离

- 决策：论文复现和 MiniCAGE 迁移实现继续集中在 [cmorl_minicage](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage)，不与仓库其他训练主线混写。
- 原因：
  - 更容易判断当前结果是“论文方法迁移版”还是“现有工程变体”。
  - 降低对仓库其他研究路径的干扰。
  - 便于后续把论文式实现和升级版实现并排对照。
- 备选方案：直接在现有训练主线上增量修改。
- 未选原因：会让论文复现边界变模糊，后续实验对照困难。

## D-002 采用 MiniCAGE 作为论文算法迁移载体，而不是直接回到论文 benchmark

- 决策：当前优先在 MiniCAGE 上迁移论文 C-MORL，而不是先严格重建 MO-Gymnasium / SustainGym 原始实验。
- 原因：
  - 当前仓库已经具备 MiniCAGE 资源和环境上下文。
  - 更适合作为后续迁移到更复杂 CybORG/CybORG++ 场景前的中间层。
  - 降低环境搭建复杂度。
- 备选方案：先在论文 benchmark 上做原样复现。
- 未选原因：
  - 会显著增加环境搭建和实验组织成本。
  - 与当前仓库已有资产复用度较低。

## D-003 把 MiniCAGE 标量 reward 严格拆成 3 目标 reward vector

- 决策：通过 [env.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/env.py) 将 MiniCAGE 的单一 reward 分解为：
  - `threat_containment`
  - `business_critical_loss`
  - `defense_cost`
- 原因：
  - 必须把任务明确变成 MORL 形式，才能迁移论文算法。
  - 三目标划分贴近当前网络安全场景中的防御收益、业务损失和操作代价。
  - 当前实现已经加入严格对账，保证三目标和原始标量 reward 一致。
- 备选方案：
  - 只做二目标拆分。
  - 直接人为重写 reward，而不对账原标量 reward。
- 未选原因：
  - 二目标表达不够丰富。
  - 不对账会让实验解释失去可靠性。

## D-004 保持默认配置入口稳定，新增分层模板目录

- 决策：保留 [stage1.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/configs/stage1.yaml)、[stage2.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/configs/stage2.yaml)、[evaluate.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/configs/evaluate.yaml) 作为稳定默认入口；新增 `smoke / formal / ablation` 模板目录。
- 原因：
  - 既能提供更清晰的实验模板分层，又不会破坏现有命令和脚本习惯。
  - 便于区分链路验证、正式实验和消融实验。
- 备选方案：
  - 只保留 profile 目录。
  - 把默认配置直接改成某个 profile。
- 未选原因：
  - 会增加迁移成本。
  - 不利于已有命令复用。

## D-005 保留 Stage-1 中间 checkpoint 到 solution buffer

- 决策：Stage-1 不只保留每个 preference 的最终策略，也保留中间 checkpoint 和评估记录。
- 原因：
  - 更贴近论文附录中“solution buffer”思路。
  - 有利于扩大候选策略池，提高后续 Stage-2 selection 的多样性。
  - 便于分析“最终最好策略”和“中间 Pareto 候选”之间的差异。
- 备选方案：每个 preference 只保留最终 checkpoint。
- 未选原因：
  - 候选池过小。
  - 不利于后续多样性分析。

## D-006 Stage-2 当前采用 IPO 分支，不实现 CPO 分支

- 决策：当前只实现 IPO-style constrained extension，不实现 CPO。
- 原因：
  - IPO 更容易和现有 PPO 训练主干集成。
  - 在多目标场景下，IPO 的实现复杂度和运行代价更低。
  - 更适合当前 MiniCAGE 迁移验证阶段。
- 备选方案：同时实现 IPO 和 CPO。
- 未选原因：
  - 当前精力更应集中在跑通和调稳一条主线。
  - CPO 对实现和调试要求更高。

## D-007 IPO 先采用 PPO-compatible 的工程近似版

- 决策：当前 `algorithms/ipo.py` 实现使用 PPO surrogate + log barrier，但 barrier 中的 return 量采用 batch surrogate return 近似，而不是直接优化真实 `G_i^π`。
- 原因：
  - 更容易与现有 PPO 训练主干结合。
  - 更容易做可微的 mini-batch 训练。
  - 工程上更轻量，能尽快跑通 Stage-2 链路。
- 备选方案：更直接地按论文 F.2 重构 IPO 数值过程。
- 未选原因：
  - 当前优先级是先获得稳定的可运行实现与调参反馈。
  - 直接落地真实 return barrier 实现与调试成本更高。

## D-008 Stage-2 增加工程化 feasibility gate

- 决策：Stage-2 在 IPO 更新后，用真实评估结果再加一层 `constraint_tolerance` feasibility gate。
- 原因：
  - 纯 surrogate barrier 在随机环境中可能高估约束满足情况。
  - 增加 gate 后更容易识别“训练看似可行但真实评估不可行”的候选点。
  - 有助于当前阶段分析 Stage-2 为什么会失败。
- 备选方案：完全依赖 IPO 内部 barrier，不再做额外 gate。
- 未选原因：
  - 当前环境和 reward 噪声下不够稳。
  - 不利于定位 Stage-2 失败原因。

## D-009 每条 Stage-2 扩展路径只保留 `best_feasible` 结果

- 决策：当前实现不是把每个 constrained update step 的候选点都存起来，而是最终只保留每条扩展路径的 `best_feasible` 结果。
- 原因：
  - 降低 buffer 膨胀速度。
  - 简化分析与可视化。
  - 避免低质量中间点挤满策略池。
- 备选方案：严格按论文 Algorithm 2 思路，逐步保存所有候选点。
- 未选原因：
  - 当前更重视稳定调试与可解释性。
  - 全量保存会增加筛选和分析复杂度。

## D-010 实验记录分成“结构化输出 + 文档日志”两层

- 决策：结构化事实保留在 `solution_buffer.json`、`stage1_summary.json`、`stage2_summary.json`、`metrics.json`；结论、异常和比较写入 [EXPERIMENT_LOG.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/docs/EXPERIMENT_LOG.md)。
- 原因：
  - 既便于程序化分析，也方便后续写作时回看结论。
  - 文本日志能记录“为什么这个结果值得关注”，JSON 本身做不到。
- 备选方案：只保留 JSON 输出，或者只手写实验日志。
- 未选原因：单独用任何一种都容易丢上下文或丢结构化信息。

## D-011 把可视化纳入正式实验产物

- 决策：通过 [visualize.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/visualize.py) 自动生成：
  - Pareto 2D projections
  - 3D Pareto scatter
  - Stage-1 vs Stage-2 overlay
  - assignment counts
  - round summary
  - ablation 总图
- 原因：
  - 当前结果已经不仅仅需要“能跑”，还需要“能解释”。
  - Pareto front 的几何形态用图比用 JSON 更直观。
  - 更有利于后续写论文和汇报。
- 备选方案：只保留数值表和 JSON。
- 未选原因：
  - 很难快速理解 front 形状和 assignment 结构。

## D-012 README 只提供高层入口，细节下沉到 `docs/`

- 决策：仓库根 [README.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/README.md) 提供高层入口；更细的项目边界、架构、决策、任务和实验记录放在 `docs/`。
- 原因：
  - 保持根 README 可读。
  - 方便新协作者快速定位不同层级的信息。
- 备选方案：把所有内容都塞进根 README。
- 未选原因：
  - 会过长。
  - 会和上游 CybORG++ 说明混在一起。
