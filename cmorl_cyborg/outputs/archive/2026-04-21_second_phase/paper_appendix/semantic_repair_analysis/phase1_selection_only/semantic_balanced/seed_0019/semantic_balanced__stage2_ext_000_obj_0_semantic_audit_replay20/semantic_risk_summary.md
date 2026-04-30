# Semantic Risk Summary: stage2_ext_000_obj_0

- Candidate: `semantic_balanced` / `stage2_ext_000_obj_0`
- Trace dir: `/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/semantic_repair_analysis/phase1_selection_only/semantic_balanced/seed_0019/semantic_balanced__stage2_ext_000_obj_0_semantic_audit_replay20/replay_trace/ours_stage2_fair/seed_0019/semantic_balanced__stage2_ext_000_obj_0`
- Tight thresholds: `business >= -125.0` `cost >= -22.0`
- Audit verdict: `Red`

## Core Metrics

- Mean returns: `security=-407.4775` `business=-106.4737` `cost=-26.9874`
- Env-run feasible rate: `0.0000`
- Per-env violation rate: `business=0.0125` `cost=1.0000`
- Critical breach: `ever=1.0000` `persistent=0.6375`
- Mean critical dwell steps: `55.0750`
- Mean `Op_Server0` impact count: `49.7313`

## Risk Tiers

- `Tier 0 Safe`: count=`0` rate=`0.0000`
- `Tier 1 Near-Miss`: count=`0` rate=`0.0000`
- `Tier 2 Transient Critical Breach`: count=`58` rate=`0.3625`
- `Tier 3 Persistent Critical Breach`: count=`102` rate=`0.6375`

## Questionable Defense Actions

- High-confidence events: `count=1152` `env_run_rate=0.9938`
- Medium-confidence events: `count=65` `env_run_rate=0.3312`
- `Q1_sleep_during_critical_breach`: `events=1` `env_runs=1`
- `Q2_user_action_during_critical_breach`: `events=1146` `env_runs=159`
- `Q3_missed_immediate_response_to_critical_hit`: `events=5` `env_runs=5`
- `Q4_user_focus_after_enterprise_foothold`: `events=30` `env_runs=26`
- `Q5_repeated_low_value_decoy_loop`: `events=35` `env_runs=35`

## Audit Comparison

| Audit | env-runs | feasible_rate | ever_critical | persistent_critical | high_conf_env_rate | verdict |
| --- | --- | --- | --- | --- | --- | --- |
| 20-episode audit | 160 | 0.0000 | 1.0000 | 0.6375 | 0.9938 | Red |
| 3-episode confirmatory audit | 24 | 0.0000 | 1.0000 | 0.8333 | 1.0000 | Red |

## Final Diagnosis

- `constraint-feasible but semantically fragile`