


<p align="center">
    <img src="Extras/images/logo_cyborg.png" alt="Diagram of the system" width="400"/>
</p>

# 当前项目概况

本仓库当前包含两条相互独立但相关的主线：

- `CybORG++` 原始环境与开发说明
  - 包括修复后的 CAGE 2 CybORG 环境
  - 包括轻量快速的 `MiniCAGE`
- `MiniCAGE C-MORL` 论文复现主线
  - 位于 [cmorl_minicage](./cmorl_minicage)
  - 目标是在不改动其他研究主线的前提下，复现论文 *Efficient Discovery of Pareto Front for Multi-Objective Reinforcement Learning (C-MORL)* 的核心训练流程，并将其迁移到 MiniCAGE 场景

## 当前复现主线在做什么

当前 `cmorl_minicage` 主要实现了以下能力：

- MiniCAGE 的多目标环境包装
- Stage-1 Pareto initialization
- Stage-2 selection + IPO-style Pareto extension
- SMP assignment
- HV / EU / SP evaluation
- YAML 配置驱动训练与评估
- 统一的 buffer / summary / metrics 输出格式

当前实现更适合被理解为：

**“C-MORL 方法在 MiniCAGE 上的迁移复现版”**

也就是说，它已经比较贴近论文的算法结构和训练逻辑，但实验环境不是论文原 benchmark，而是本地适配后的 MiniCAGE。

## 当前项目状态

截至目前，这条复现线已经具备：

- 可以独立运行的 `stage1 -> stage2 -> evaluate` 完整链路
- 分层配置模板：
  - `cmorl_minicage/configs/smoke/`
  - `cmorl_minicage/configs/formal/`
  - `cmorl_minicage/configs/ablation/`
- 结构化输出：
  - `solution_buffer.json`
  - `stage1_summary.json`
  - `stage2_summary.json`
  - `metrics.json`

当前实验现状可以概括为：

- Stage-1 已经能在 MiniCAGE 上产生有 trade-off 结构的 Pareto front
- Stage-2 的约束扩展链路已经打通，但在当前超参数下仍然偏严格，常出现 feasibility gate 过早截断的情况
- evaluation 链路已经稳定可用，并支持新的 HV / EU / SP 评估输出

## 目录说明

当前最值得关注的目录如下：

- [cmorl_minicage](./cmorl_minicage)
  - MiniCAGE 上的 C-MORL 论文复现实现
- [docs](./docs)
  - 当前项目的中文项目说明、架构、决策、任务和实验日志
- [Debugged_CybORG](./Debugged_CybORG)
  - 修复后的 CAGE 2 CybORG 环境
- [mini_CAGE](./mini_CAGE)
  - MiniCAGE 轻量环境实现

如果你主要关注当前论文复现主线，建议优先看：

- [docs/PROJECT_BRIEF.md](./docs/PROJECT_BRIEF.md)
- [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)
- [docs/TASKS.md](./docs/TASKS.md)
- [docs/EXPERIMENT_LOG.md](./docs/EXPERIMENT_LOG.md)

## 快速开始

建议在仓库根目录、使用 `cc4` conda 环境运行：

```bash
conda run -n cc4 python -m cmorl_minicage.train_stage1 --config cmorl_minicage/configs/smoke/stage1.yaml
conda run -n cc4 python -m cmorl_minicage.train_stage2 --config cmorl_minicage/configs/smoke/stage2.yaml --stage1-buffer <stage1_solution_buffer>
conda run -n cc4 python -m cmorl_minicage.evaluate --config cmorl_minicage/configs/smoke/evaluate.yaml --buffer-path <solution_buffer>
```

如果要跑更正式的实验，可以切换到：

- `cmorl_minicage/configs/formal/`
- `cmorl_minicage/configs/ablation/`

## 输出与实验记录

当前复现线所有实验输出默认写入：

- `cmorl_minicage/outputs/`

实验过程中的结构化事实来自 run 目录下的 JSON 文件；实验现象、结论和后续动作统一记录在：

- [docs/EXPERIMENT_LOG.md](./docs/EXPERIMENT_LOG.md)

## 说明

本 README 顶部这部分中文内容用于描述当前仓库里“正在推进的项目状态”和“MiniCAGE C-MORL 复现主线”的基本情况；后续更细的实现和实验细节，请以 `docs/` 与 `cmorl_minicage/docs/` 中的文档为准。
