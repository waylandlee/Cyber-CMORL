# Semantic Risk Summary: stage2_ext_016_obj_0

- Candidate: `selected` / `stage2_ext_016_obj_0`
- Trace dir: `/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/figure2_attack_defense_traces/ours_stage2_fair/seed_0011/selected__stage2_ext_016_obj_0`
- Tight thresholds: `business >= -125.0` `cost >= -22.0`
- Audit verdict: `Red`

## Core Metrics

- Mean returns: `security=-465.0021` `business=-118.9057` `cost=-22.5113`
- Env-run feasible rate: `0.0833`
- Per-env violation rate: `business=0.3750` `cost=0.7500`
- Critical breach: `ever=1.0000` `persistent=0.9167`
- Mean critical dwell steps: `64.2083`
- Mean `Op_Server0` impact count: `59.5833`

## Risk Tiers

- `Tier 0 Safe`: count=`0` rate=`0.0000`
- `Tier 1 Near-Miss`: count=`0` rate=`0.0000`
- `Tier 2 Transient Critical Breach`: count=`2` rate=`0.0833`
- `Tier 3 Persistent Critical Breach`: count=`22` rate=`0.9167`

## Questionable Defense Actions

- High-confidence events: `count=421` `env_run_rate=1.0000`
- Medium-confidence events: `count=51` `env_run_rate=0.8333`
- `Q1_sleep_during_critical_breach`: `events=2` `env_runs=2`
- `Q2_user_action_during_critical_breach`: `events=417` `env_runs=24`
- `Q3_missed_immediate_response_to_critical_hit`: `events=2` `env_runs=2`
- `Q4_user_focus_after_enterprise_foothold`: `events=46` `env_runs=19`
- `Q5_repeated_low_value_decoy_loop`: `events=5` `env_runs=5`

## Audit Comparison

| Audit | env-runs | feasible_rate | ever_critical | persistent_critical | high_conf_env_rate | verdict |
| --- | --- | --- | --- | --- | --- | --- |
| 3-episode audit | 24 | 0.0833 | 1.0000 | 0.9167 | 1.0000 | Red |
| 20-episode confirmatory audit | 160 | 0.1313 | 1.0000 | 0.7937 | 1.0000 | Red |

## Final Diagnosis

- `constraint-feasible but semantically fragile`