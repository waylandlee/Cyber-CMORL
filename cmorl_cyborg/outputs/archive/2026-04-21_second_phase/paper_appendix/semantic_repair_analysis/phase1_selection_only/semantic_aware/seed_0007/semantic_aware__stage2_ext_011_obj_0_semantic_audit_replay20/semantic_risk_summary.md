# Semantic Risk Summary: stage2_ext_011_obj_0

- Candidate: `semantic_aware` / `stage2_ext_011_obj_0`
- Trace dir: `/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/semantic_repair_analysis/phase1_selection_only/semantic_aware/seed_0007/semantic_aware__stage2_ext_011_obj_0_semantic_audit_replay20/replay_trace/ours_stage2_fair/seed_0007/semantic_aware__stage2_ext_011_obj_0`
- Tight thresholds: `business >= -125.0` `cost >= -22.0`
- Audit verdict: `Red`

## Core Metrics

- Mean returns: `security=-617.0859` `business=-147.5466` `cost=-19.2366`
- Env-run feasible rate: `0.1875`
- Per-env violation rate: `business=0.8125` `cost=0.0000`
- Critical breach: `ever=0.9938` `persistent=0.8875`
- Mean critical dwell steps: `64.4875`
- Mean `Op_Server0` impact count: `59.3312`

## Risk Tiers

- `Tier 0 Safe`: count=`0` rate=`0.0000`
- `Tier 1 Near-Miss`: count=`1` rate=`0.0063`
- `Tier 2 Transient Critical Breach`: count=`17` rate=`0.1062`
- `Tier 3 Persistent Critical Breach`: count=`142` rate=`0.8875`

## Questionable Defense Actions

- High-confidence events: `count=2817` `env_run_rate=0.9875`
- Medium-confidence events: `count=287` `env_run_rate=0.7500`
- `Q1_sleep_during_critical_breach`: `events=8` `env_runs=8`
- `Q2_user_action_during_critical_breach`: `events=2801` `env_runs=157`
- `Q3_missed_immediate_response_to_critical_hit`: `events=8` `env_runs=8`
- `Q4_user_focus_after_enterprise_foothold`: `events=286` `env_runs=120`
- `Q5_repeated_low_value_decoy_loop`: `events=1` `env_runs=1`

## Audit Comparison

| Audit | env-runs | feasible_rate | ever_critical | persistent_critical | high_conf_env_rate | verdict |
| --- | --- | --- | --- | --- | --- | --- |
| 20-episode audit | 160 | 0.1875 | 0.9938 | 0.8875 | 0.9875 | Red |
| 3-episode confirmatory audit | 24 | 0.2917 | 1.0000 | 0.7917 | 1.0000 | Red |

## Final Diagnosis

- `constraint-feasible but semantically fragile`