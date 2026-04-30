# Semantic Risk Summary: stage2_ext_023_obj_2

- Candidate: `closest_candidate` / `stage2_ext_023_obj_2`
- Trace dir: `/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/figure2_attack_defense_traces/no_constraint_stage2_fair/seed_0019/closest_candidate__stage2_ext_023_obj_2`
- Tight thresholds: `business >= -125.0` `cost >= -22.0`
- Audit verdict: `Red`

## Core Metrics

- Mean returns: `security=-834.7937` `business=-107.9447` `cost=-15.6604`
- Env-run feasible rate: `0.5833`
- Per-env violation rate: `business=0.4167` `cost=0.0000`
- Critical breach: `ever=0.6250` `persistent=0.6250`
- Mean critical dwell steps: `42.1250`
- Mean `Op_Server0` impact count: `40.8333`

## Risk Tiers

- `Tier 0 Safe`: count=`0` rate=`0.0000`
- `Tier 1 Near-Miss`: count=`9` rate=`0.3750`
- `Tier 2 Transient Critical Breach`: count=`0` rate=`0.0000`
- `Tier 3 Persistent Critical Breach`: count=`15` rate=`0.6250`

## Questionable Defense Actions

- High-confidence events: `count=566` `env_run_rate=0.6250`
- Medium-confidence events: `count=425` `env_run_rate=1.0000`
- `Q2_user_action_during_critical_breach`: `events=561` `env_runs=15`
- `Q3_missed_immediate_response_to_critical_hit`: `events=5` `env_runs=5`
- `Q4_user_focus_after_enterprise_foothold`: `events=405` `env_runs=24`
- `Q5_repeated_low_value_decoy_loop`: `events=20` `env_runs=17`

## Audit Comparison

| Audit | env-runs | feasible_rate | ever_critical | persistent_critical | high_conf_env_rate | verdict |
| --- | --- | --- | --- | --- | --- | --- |
| 3-episode audit | 24 | 0.5833 | 0.6250 | 0.6250 | 0.6250 | Red |
| 20-episode confirmatory audit | 160 | 0.4313 | 0.7625 | 0.7625 | 0.7562 | Red |

## Final Diagnosis

- `constraint-feasible but semantically fragile`