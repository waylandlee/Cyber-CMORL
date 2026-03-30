# Project Brief

## 项目目标

本项目当前的独立主线是：在不干扰 `CybORG_plus_plus` 其他研究路径的前提下，在 [cmorl_minicage](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage) 中复现论文 *Efficient Discovery of Pareto Front for Multi-Objective Reinforcement Learning (C-MORL)* 的核心训练流程，并将其迁移到 MiniCAGE 场景。

当前目标聚焦在三件事：

- 做出一条可运行、可验证、可对照的 MiniCAGE C-MORL 复现线
- 尽量向论文训练细节收紧，同时明确记录与原论文 benchmark 的差异
- 为后续正式实验、消融实验和方法升级提供稳定的配置、输出和文档体系

## 范围

当前范围包括：

- MiniCAGE 多目标环境包装
- Stage-1 Pareto initialization
- Stage-2 selection + IPO-style Pareto extension
- SMP assignment
- HV / EU / SP evaluation
- YAML 配置驱动训练与评估
- 统一 buffer / summary / experiment logging

当前不包含：

- 论文原 benchmark 的逐任务原样复刻
- CPO 分支实现
- 与仓库其他训练主线的深度整合

## 当前主线

当前主线代码位于：

- [cmorl_minicage/env.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/env.py)
- [cmorl_minicage/train_stage1.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/train_stage1.py)
- [cmorl_minicage/train_stage2.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/train_stage2.py)
- [cmorl_minicage/evaluate.py](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/evaluate.py)

当前默认实验入口：

- [cmorl_minicage/configs/stage1.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/configs/stage1.yaml)
- [cmorl_minicage/configs/stage2.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/configs/stage2.yaml)
- [cmorl_minicage/configs/evaluate.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/configs/evaluate.yaml)

## 配置层次

为避免把“冒烟验证”和“正式实验”混在一起，配置模板分为三层：

- `smoke`
  - 用于最小链路验证，预算小，优先确认训练和评估流程不报错
- `formal`
  - 用于较完整的论文式运行，预算更高，统计更稳定
- `ablation`
  - 用于单点对比，比如 preference 初始化策略和 Stage-2 约束强度

## 输出约定

所有复现线输出默认写入 [cmorl_minicage/outputs](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/outputs)，每次 run 目录下至少关注：

- `solution_buffer.json`
- `stage1_summary.json` 或 `stage2_summary.json`
- `pareto_front_*.json`
- `metrics*.json`

实验结论和异常现象统一记录到 [EXPERIMENT_LOG.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/docs/EXPERIMENT_LOG.md)。
