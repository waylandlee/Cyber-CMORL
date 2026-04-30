# Semantic Risk Summary: stage2_ext_006_obj_0

- Candidate: `semantic_balanced_selected` / `stage2_ext_006_obj_0`
- Trace dir: `/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/semantic_repair_analysis/phase3_target/seed_0011/semantic_balanced_selected__stage2_ext_006_obj_0_semantic_audit_replay20/replay_trace/ours_stage2_fair_semantic_target/seed_0011/semantic_balanced_selected__stage2_ext_006_obj_0`
- Tight thresholds: `business >= -125.0` `cost >= -22.0`
- Audit verdict: `Red`

## Core Metrics

- Mean returns: `security=-479.5922` `business=-127.9147` `cost=-27.4845`
- Env-run feasible rate: `0.0000`
- Per-env violation rate: `business=0.6312` `cost=1.0000`
- Critical breach: `ever=1.0000` `persistent=0.7063`
- Mean critical dwell steps: `62.3000`
- Mean `Op_Server0` impact count: `52.8500`

## Risk Tiers

- `Tier 0 Safe`: count=`0` rate=`0.0000`
- `Tier 1 Near-Miss`: count=`0` rate=`0.0000`
- `Tier 2 Transient Critical Breach`: count=`47` rate=`0.2938`
- `Tier 3 Persistent Critical Breach`: count=`113` rate=`0.7063`

## Questionable Defense Actions

- High-confidence events: `count=2855` `env_run_rate=1.0000`
- Medium-confidence events: `count=383` `env_run_rate=0.8375`
- `Q1_sleep_during_critical_breach`: `events=35` `env_runs=33`
- `Q2_user_action_during_critical_breach`: `events=2797` `env_runs=160`
- `Q3_missed_immediate_response_to_critical_hit`: `events=23` `env_runs=23`
- `Q4_user_focus_after_enterprise_foothold`: `events=303` `env_runs=122`
- `Q5_repeated_low_value_decoy_loop`: `events=80` `env_runs=71`

## Audit Comparison

| Audit | env-runs | feasible_rate | ever_critical | persistent_critical | high_conf_env_rate | verdict |
| --- | --- | --- | --- | --- | --- | --- |
| 20-episode audit | 160 | 0.0000 | 1.0000 | 0.7063 | 1.0000 | Red |
| 3-episode confirmatory audit | 24 | 0.0000 | 1.0000 | 0.7500 | 1.0000 | Red |

## Final Diagnosis

- `constraint-feasible but semantically fragile`