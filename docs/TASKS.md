# Tasks

## 当前待办

- `In Progress` 继续把 Stage-2 IPO surrogate 向论文训练细节收紧。
- `In Progress` 继续调 Stage-2 约束超参，找到“能保持 feasibility 且能产生有效 extension”的区间。
- `Planned` 把当前 config profile 的使用经验沉淀成更明确的运行建议。

## 进行中

- `In Progress` MiniCAGE C-MORL 论文迁移复现主线维护。
- `In Progress` 文档、配置、输出格式持续对齐，避免代码和记录体系脱节。

## 已完成

- `Done` 建立独立的 [cmorl_minicage](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage) 工作区。
- `Done` 完成 Stage-1 / Stage-2 / evaluation 首版可运行链路。
- `Done` 完成 reward vector 与 MiniCAGE 标量奖励的严格对账。
- `Done` 完成 YAML 配置驱动入口。
- `Done` 完成 P0 收紧：IPO surrogate 与 Stage-2 feasibility gate。
- `Done` 完成 P1 收紧：Stage-1 preference 初始化、泛化 HV、训练过程统计。
- `Done` 完成配置模板分层、README 入口补充和实验记录体系初版。

## 下一步建议

- `Planned` 跑一组正式 `formal` 配置实验并写入 [EXPERIMENT_LOG.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/docs/EXPERIMENT_LOG.md)。
- `Planned` 基于 `ablation` 模板比较 `grid`、`dirichlet`、`dirichlet_extremes` 初始化差异。
- `Planned` 针对 Stage-2 feasibility gate 做一次系统超参扫描。
