# Semantic Risk Summary: stage2_ext_022_obj_1

- Candidate: `selected` / `stage2_ext_022_obj_1`
- Trace dir: `/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_4obj/rq3_symmetric/traces/no_constraint_stage2_fair/seed_0011/selected__stage2_ext_022_obj_1`
- Tight thresholds: `business >= -125.0` `cost >= -22.0`
- Audit verdict: `Red`

## Core Metrics

- Mean returns: `security=-570.1887` `business=-109.3067` `cost=-21.4446`
- Env-run feasible rate: `0.5813`
- Per-env violation rate: `business=0.2750` `cost=0.2125`
- Critical breach: `ever=0.9313` `persistent=0.8125`
- Mean critical dwell steps: `56.0125`
- Mean `Op_Server0` impact count: `53.1125`

## Risk Tiers

- `Tier 0 Safe`: count=`0` rate=`0.0000`
- `Tier 1 Near-Miss`: count=`11` rate=`0.0688`
- `Tier 2 Transient Critical Breach`: count=`19` rate=`0.1187`
- `Tier 3 Persistent Critical Breach`: count=`130` rate=`0.8125`

## Questionable Defense Actions

- High-confidence events: `count=2696` `env_run_rate=0.9250`
- Medium-confidence events: `count=384` `env_run_rate=0.8125`
- `Q1_sleep_during_critical_breach`: `events=10` `env_runs=10`
- `Q2_user_action_during_critical_breach`: `events=2671` `env_runs=148`
- `Q3_missed_immediate_response_to_critical_hit`: `events=15` `env_runs=15`
- `Q4_user_focus_after_enterprise_foothold`: `events=371` `env_runs=129`
- `Q5_repeated_low_value_decoy_loop`: `events=13` `env_runs=13`

## Critical Action Families

- `restore`: `step_rate=0.1098` `env_run_rate=0.9933`
- `remove`: `step_rate=0.0430` `env_run_rate=0.8591`
- `analyse`: `step_rate=0.1090` `env_run_rate=0.9530`
- `decoy`: `step_rate=0.7359` `env_run_rate=1.0000`
- `other`: `step_rate=0.0023` `env_run_rate=0.1342`

## Pre-Critical Containment

- `restore`: `step_rate=0.1551` `env_run_rate=0.9688`
- `remove`: `step_rate=0.0349` `env_run_rate=0.5938`
- `analyse`: `step_rate=0.1094` `env_run_rate=0.8812`
- `decoy`: `step_rate=0.6981` `env_run_rate=1.0000`
- `other`: `step_rate=0.0024` `env_run_rate=0.0813`
- `compromised_target_focus`: `step_rate=0.2196` `env_run_rate=0.9938`