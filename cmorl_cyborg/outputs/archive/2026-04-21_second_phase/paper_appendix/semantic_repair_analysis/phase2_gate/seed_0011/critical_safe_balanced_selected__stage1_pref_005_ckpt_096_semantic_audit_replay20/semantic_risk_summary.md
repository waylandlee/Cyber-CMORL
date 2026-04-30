# Semantic Risk Summary: stage1_pref_005_ckpt_096

- Candidate: `critical_safe_balanced_selected` / `stage1_pref_005_ckpt_096`
- Trace dir: `/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/semantic_repair_analysis/phase2_gate/seed_0011/critical_safe_balanced_selected__stage1_pref_005_ckpt_096_semantic_audit_replay20/replay_trace/ours_stage2_fair_critical_safe_v1/seed_0011/critical_safe_balanced_selected__stage1_pref_005_ckpt_096`
- Tight thresholds: `business >= -125.0` `cost >= -22.0`
- Audit verdict: `Red`

## Core Metrics

- Mean returns: `security=-513.7631` `business=-131.8501` `cost=-25.3676`
- Env-run feasible rate: `0.0000`
- Per-env violation rate: `business=0.8875` `cost=1.0000`
- Critical breach: `ever=1.0000` `persistent=0.8375`
- Mean critical dwell steps: `69.4813`
- Mean `Op_Server0` impact count: `59.7375`

## Risk Tiers

- `Tier 0 Safe`: count=`0` rate=`0.0000`
- `Tier 1 Near-Miss`: count=`0` rate=`0.0000`
- `Tier 2 Transient Critical Breach`: count=`26` rate=`0.1625`
- `Tier 3 Persistent Critical Breach`: count=`134` rate=`0.8375`

## Questionable Defense Actions

- High-confidence events: `count=3123` `env_run_rate=1.0000`
- Medium-confidence events: `count=437` `env_run_rate=0.9563`
- `Q1_sleep_during_critical_breach`: `events=1` `env_runs=1`
- `Q2_user_action_during_critical_breach`: `events=3112` `env_runs=160`
- `Q3_missed_immediate_response_to_critical_hit`: `events=10` `env_runs=10`
- `Q4_user_focus_after_enterprise_foothold`: `events=300` `env_runs=125`
- `Q5_repeated_low_value_decoy_loop`: `events=137` `env_runs=136`

## Audit Comparison

| Audit | env-runs | feasible_rate | ever_critical | persistent_critical | high_conf_env_rate | verdict |
| --- | --- | --- | --- | --- | --- | --- |
| 20-episode audit | 160 | 0.0000 | 1.0000 | 0.8375 | 1.0000 | Red |
| 3-episode confirmatory audit | 24 | 0.0000 | 1.0000 | 0.9167 | 1.0000 | Red |

## Final Diagnosis

- `constraint-feasible but semantically fragile`