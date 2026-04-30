# Semantic Risk Summary: stage2_ext_005_obj_0

- Candidate: `objective_selected` / `stage2_ext_005_obj_0`
- Trace dir: `/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/semantic_repair_traces/phase0_objective_selected/ours_stage2_fair/seed_0007/objective_selected__stage2_ext_005_obj_0`
- Tight thresholds: `business >= -125.0` `cost >= -22.0`
- Audit verdict: `Red`

## Core Metrics

- Mean returns: `security=-459.5062` `business=-115.8552` `cost=-24.1600`
- Env-run feasible rate: `0.0000`
- Per-env violation rate: `business=0.3333` `cost=0.9583`
- Critical breach: `ever=1.0000` `persistent=0.7917`
- Mean critical dwell steps: `65.5000`
- Mean `Op_Server0` impact count: `61.5833`

## Risk Tiers

- `Tier 0 Safe`: count=`0` rate=`0.0000`
- `Tier 1 Near-Miss`: count=`0` rate=`0.0000`
- `Tier 2 Transient Critical Breach`: count=`5` rate=`0.2083`
- `Tier 3 Persistent Critical Breach`: count=`19` rate=`0.7917`

## Questionable Defense Actions

- High-confidence events: `count=452` `env_run_rate=1.0000`
- Medium-confidence events: `count=66` `env_run_rate=0.9583`
- `Q1_sleep_during_critical_breach`: `events=21` `env_runs=15`
- `Q2_user_action_during_critical_breach`: `events=429` `env_runs=24`
- `Q3_missed_immediate_response_to_critical_hit`: `events=2` `env_runs=2`
- `Q4_user_focus_after_enterprise_foothold`: `events=44` `env_runs=19`
- `Q5_repeated_low_value_decoy_loop`: `events=22` `env_runs=21`

## Audit Comparison

| Audit | env-runs | feasible_rate | ever_critical | persistent_critical | high_conf_env_rate | verdict |
| --- | --- | --- | --- | --- | --- | --- |
| 3-episode audit | 24 | 0.0000 | 1.0000 | 0.7917 | 1.0000 | Red |
| 20-episode confirmatory audit | 160 | 0.0000 | 1.0000 | 0.7750 | 1.0000 | Red |

## Final Diagnosis

- `constraint-feasible but semantically fragile`