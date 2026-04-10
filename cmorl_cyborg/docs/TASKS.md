# Tasks

## 当前待办

- 固化 `fair_compare` 为 `ours_stage2` vs `no_constraint_stage2` 的公平消融口径
- 决定是否仍需要额外单独补 `no_constraint_stage2_matched` 主文表
- 决定是否进入 `5-seed formal`
- 把现有 `3-seed` 结果整理成论文可直接使用的结果总结
- 明确 semantic-aware / semantic-balanced 是否放入附录
- 统一 coverage 公平比较在论文中的表述边界

## 进行中

- 论文写作前的实验公平性梳理
- 表 B 讨论口径收束
- 文档与 README 的结果口径统一

## 已完成

- 固定正式 `security / business / cost` 口径
- 打通 `Stage-1 -> Stage-2 -> evaluate -> evaluate_constraints -> compare_suite -> export_tables`
- 建立 dev / holdout 调参闭环
- 生成正式 `3-seed` 主表 A / B
- 生成 `fair_compare_eval` 的 tight / loose 比较图
- 生成 `coverage_combo_fair` 与 `coverage_more_parents_fair` 聚合结果
- 为 week-2 formal runner 增加：
  - [status.json](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/paper_week2_runner/status.json)
  - [runner.log](/home/waylandlee/Cyber-CMORL/CybORG_plus_plus/cmorl_cyborg/outputs/paper_week2_runner/runner.log)
- 修复正式 `stage2_main`，让 Stage-2 不再空转
- 试过但未采用的表 B 改法：
  - semantic parent selection
  - semantic soft penalty
  - early termination 放松
  - very small B-tight 微调
  - semantic-aware / semantic-balanced 主选点替换
