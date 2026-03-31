# C-MORL MiniCAGE 复现 TODO

本文档用于跟踪 MiniCAGE 上的 C-MORL 论文复现进度，只记录执行状态、未完成模块和当前已知差异，不展开成长篇设计文档。

状态字段统一使用：
- `Planned`
- `In Progress`
- `Done`
- `Blocked`

## 当前进度

- `Done` 已阅读 `PROMPT_CONTEXT.md` 中与“原论文算法实现细节”相关的部分，并明确本轮不采用其中的大型项目组织方案。
- `Done` 已读取论文《Efficient Discovery of Pareto Front for Multi-Objective Reinforcement Learning》，确认本地复现的核心链路应覆盖：Pareto initialization、policy selection、Pareto extension、IPO、SMP assignment、HV/EU/SP。
- `Done` 已验证 `cc4` 环境可用，基础依赖中 `python`、`numpy`、`torch` 可正常导入。
- `Done` 已验证 `mini_CAGE` 可运行，`reset` 与 `step` 正常返回。
- `Done` 已锁定复现主线为：MiniCAGE 上的论文式 C-MORL，而不是复用其他工程训练主线。
- `Done` 已确定文档落点为 `CybORG_plus_plus/cmorl_minicage/docs/`。
- `Done` 已初始化 `PAPER_MAPPING.md`、`TODO.md`、`NOTES.md`。
- `Done` 已完成 `cmorl_minicage` 首版代码骨架，包括环境包装、模型、storage、Stage-1、Stage-2、selection、IPO、assignment、evaluation。
- `Done` 已完成旧版 reward decomposition 与 MiniCAGE 标量奖励严格对账，并修复了 probe 过程对 `numpy` 随机状态的扰动问题。
- `Done` 已将环境奖励口径切换为 `security / business / cost`，并采用方案 A 保留 MORL 总回报与 MiniCAGE 原始标量 reward 的双口径记录。
- `Done` 已统一 Stage-1 / Stage-2 的 buffer schema 与 metadata，当前版本为 `schema_version 0.3.0`。
- `Done` 已跑通最小 `stage1 -> stage2 -> evaluate` smoke test。
- `Done` 已将训练与评估入口收敛为 YAML 配置文件驱动，并补齐 `cmorl_minicage/configs/stage1.yaml`、`stage2.yaml`、`evaluate.yaml`。
- `Done` 已将 Stage-1 preference 初始化扩展为可配置策略，当前支持 `grid`、`dirichlet`、`dirichlet_extremes`。
- `Done` 已将 evaluation 中的 HV 扩展为任意目标维实现，并补充 reference point 配置与 assignment summary 输出。
- `Done` 已补充 Stage-1 / Stage-2 训练过程统计，包括 `stage1_summary.json`、`stage2_summary.json` 与更丰富的 record notes。
- `Done` 已补齐分层配置模板，当前提供 `smoke / formal / ablation` 三组配置目录。
- `Done` 已补充仓库根 README 的 MiniCAGE C-MORL 入口说明，并初始化根 `docs/` 下的项目说明、决策、任务和实验日志文档。

## 未完成模块

- `In Progress` IPO 细化：继续把当前可运行 surrogate 向论文训练细节收紧，并补更多约束诊断量。
- `Planned` Evaluation 进一步细化：根据正式实验需要继续校准 reference point 策略，并视 Pareto set 规模决定是否引入更高效 HV 算法。
- `Planned` 指标导出：把训练过程中的 selection / extension 统计进一步做成更适合横向比较的实验日志。
- `In Progress` 文档维护：随着正式实验推进，持续更新根 `docs/EXPERIMENT_LOG.md` 与 `cmorl_minicage/docs/NOTES.md`。

## 已知差异

- 当前复现环境使用 `MiniCAGE`，而不是论文中的原始 benchmark 组合。
- 当前复现默认使用 3 目标 reward vector，该向量由 MiniCAGE 现有 Blue 标量 reward 拆分得到，而不是直接来自原 benchmark 的原生多目标定义。
- 当前复现默认优先实现 IPO（interior point optimization / log-barrier），不实现 CPO 分支。
- 当前复现默认训练 Blue-only policy，red 由脚本对手驱动。
- 当前复现的 reward vector 设计会包含对 MiniCAGE 奖励语义的本地适配，因此环境层存在明确的任务映射步骤。

## 维护约定

- 新增核心模块后，先更新本文件“未完成模块”的状态，再同步更新 `PAPER_MAPPING.md`。
- 跑训练、评估或发现不稳定现象后，不在这里记实验细节，统一写入 `NOTES.md`。
