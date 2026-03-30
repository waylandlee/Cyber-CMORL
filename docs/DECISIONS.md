# Decisions

## D-001 保持 `cmorl_minicage` 与仓库其他主线隔离

- 决策：论文复现和 MiniCAGE 迁移实现继续集中在 [cmorl_minicage](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage)，不与仓库其他训练主线混写。
- 原因：这样更容易判断当前结果是“论文方法迁移版”还是“现有工程变体”。
- 备选方案：直接在现有训练主线上增量修改。
- 未选原因：会让论文复现边界变模糊，后续实验对照困难。

## D-002 保持默认配置入口稳定，新增分层模板目录

- 决策：保留 [stage1.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/configs/stage1.yaml)、[stage2.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/configs/stage2.yaml)、[evaluate.yaml](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_minicage/configs/evaluate.yaml) 作为稳定默认入口；新增 `smoke / formal / ablation` 模板目录。
- 原因：既能提供更清晰的实验模板分层，又不会破坏现有命令和脚本习惯。
- 备选方案：把默认配置直接改造成某一种 profile，或者只保留 profile 目录。
- 未选原因：会增加迁移成本，也不利于已有命令复用。

## D-003 实验记录分成“结构化输出 + 文档日志”两层

- 决策：结构化事实保留在 `solution_buffer.json`、`stage1_summary.json`、`stage2_summary.json`、`metrics.json`；结论、异常和比较写入 [EXPERIMENT_LOG.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/docs/EXPERIMENT_LOG.md)。
- 原因：这样既便于程序化分析，也方便后续写作时回看结论。
- 备选方案：只保留 JSON 输出，或者只手写实验日志。
- 未选原因：单独用任何一种都容易丢上下文或丢结构化信息。

## D-004 README 只提供高层入口，细节下沉到 `docs/`

- 决策：仓库根 [README.md](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/README.md) 负责告诉读者“MiniCAGE C-MORL 复现线在哪里、怎么跑、有哪些配置层级”；更细的项目边界、架构和任务拆分放在 `docs/`。
- 原因：避免根 README 被实现细节淹没，同时让新协作者能快速定位文档。
- 备选方案：把所有复现细节都写进根 README。
- 未选原因：会让 README 过长，也会和上游 CybORG++ 说明混在一起。
