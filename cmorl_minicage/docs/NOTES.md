# C-MORL MiniCAGE 复现 Notes

本文档用于记录训练现象、不稳定原因，以及与论文实现不一致的已确认事实。首版不伪造实验结果，但预留统一记录结构，便于后续持续追加。

## 训练现象

- 尚未开始系统训练，待填。
- 建议后续记录格式：
  - 日期：
  - 阶段：Stage-1 / Stage-2 / Evaluation
  - 现象：
  - 可能原因：
  - 是否复现：
  - 后续处理：

## 不稳定原因

- 稀疏奖励可能与 Stage-2 的 IPO / log-barrier 项发生较强相互作用，导致扩展阶段对约束边界较敏感。
- SMP / Expected Utility 对 Pareto set 的覆盖密度敏感；如果 Stage-1 初始策略过少，Stage-2 可能需要承担过多“补 front”任务。
- reward vector 由现有标量 reward 拆分得到，因此 reward 拆分方式本身会显著影响 HV / EU / SP。
- MiniCAGE 使用脚本化 red 对手，策略分布可能比论文 benchmark 更窄，导致 Pareto front 的可探索区域受到对手行为分布影响。
- 如果 Stage-2 每轮扩展步数过大，可能更容易出现 barrier 主导更新、主目标收益提升不足的现象。

## 与论文实现的不一致处

- 当前复现使用 MiniCAGE，而非论文中的 MO-Gymnasium / SustainGym benchmark。
- 当前复现默认构造 3 目标 reward vector，而论文 benchmark 中不同任务的 objective 定义并不统一。
- 当前复现默认训练 Blue-only policy，环境中的 red 由脚本对手提供；这与论文中通用 MORL benchmark 的任务形式不同。
- 当前复现首版只计划实现 IPO 分支，不实现论文附录中的 CPO 分支。
- 当前复现会在环境层做 MiniCAGE reward decomposition，这属于本地适配，不是论文原 benchmark 的原生接口。

## 后续观察记录

- 2026-03-30：初始化文档结构，尚未开始系统训练。
- 2026-03-30：在 reward decomposition 初版中，发现仅按最终 `true_state` 拆分会少算 `after_red_state` 的 reward 贡献；现已改为按 MiniCAGE 的双阶段记账逻辑投影 reward terms。
- 2026-03-30：probe 版 reward 投影最初会消费 `numpy` 随机数，导致 probe 路径与真实 `sim.step()` 随机分支不一致；现已在投影前后恢复 RNG state。
- 2026-03-30：已完成 `schema_version 0.3.0` 的统一 buffer metadata / record 格式，顶层 schema 与 metadata version 已对齐，并新增 `stage1_summary.json` / `stage2_summary.json`。
- 2026-03-30：已将训练与评估入口收口为 YAML 配置文件驱动；当前默认模板位于 `cmorl_minicage/configs/`，CLI 只保留少量路径覆盖项。
- 2026-03-30：Stage-1 preference 初始化已扩展为 `grid`、`dirichlet`、`dirichlet_extremes`；当前默认改为 `dirichlet_extremes`，用于同时覆盖极端策略和 simplex 内部策略。
- 2026-03-30：evaluation 已不再限制为 3 目标；当前 HV 对小规模 Pareto set 使用 exact inclusion-exclusion，对更大集合回退 Monte Carlo 近似。
- 2026-03-30：在当前较严格的 Stage-2 feasibility gate 下，最小 smoke run 可能不生成新的 stage-2 policy；这更接近 constrained extension 的预期行为，但也提示后续需要继续调 IPO 与约束阈值。
- 2026-03-30：已将配置模板分层为 `smoke / formal / ablation`，用于区分链路验证、正式实验和单点对比；默认入口配置保持不变。
- 2026-03-30：已建立仓库根 `docs/` 级别的实验记录体系，结构化输出仍来自 run 目录下 JSON 文件，结论和观察统一写入 `docs/EXPERIMENT_LOG.md`。

后续新增记录时建议使用以下格式：

```text
YYYY-MM-DD
阶段：
现象：
可能原因：
处理动作：
结果：
```

## 维护约定

- 这里只记录已观察到的训练现象和已确认的不一致处。
- 如果某个问题仍是猜测，应写入“可能原因”，不要写成既定事实。
- 若某项不一致已被消除，应追加更正记录，而不是直接删除历史现象。
