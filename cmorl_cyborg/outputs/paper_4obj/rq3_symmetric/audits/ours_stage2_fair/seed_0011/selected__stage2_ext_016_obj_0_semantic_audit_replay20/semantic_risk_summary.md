# Semantic Risk Summary: stage2_ext_016_obj_0

- Candidate: `selected` / `stage2_ext_016_obj_0`
- Trace dir: `/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_4obj/rq3_symmetric/traces/ours_stage2_fair/seed_0011/selected__stage2_ext_016_obj_0`
- Tight thresholds: `business >= -125.0` `cost >= -22.0`
- Audit verdict: `Red`

## Core Metrics

- Mean returns: `security=-505.7781` `business=-121.7293` `cost=-22.6838`
- Env-run feasible rate: `0.1313`
- Per-env violation rate: `business=0.4188` `cost=0.7688`
- Critical breach: `ever=1.0000` `persistent=0.7937`
- Mean critical dwell steps: `67.3375`
- Mean `Op_Server0` impact count: `62.9625`

## Risk Tiers

- `Tier 0 Safe`: count=`0` rate=`0.0000`
- `Tier 1 Near-Miss`: count=`0` rate=`0.0000`
- `Tier 2 Transient Critical Breach`: count=`33` rate=`0.2062`
- `Tier 3 Persistent Critical Breach`: count=`127` rate=`0.7937`

## Questionable Defense Actions

- High-confidence events: `count=3109` `env_run_rate=1.0000`
- Medium-confidence events: `count=370` `env_run_rate=0.8125`
- `Q1_sleep_during_critical_breach`: `events=15` `env_runs=14`
- `Q2_user_action_during_critical_breach`: `events=3067` `env_runs=160`
- `Q3_missed_immediate_response_to_critical_hit`: `events=27` `env_runs=27`
- `Q4_user_focus_after_enterprise_foothold`: `events=335` `env_runs=126`
- `Q5_repeated_low_value_decoy_loop`: `events=35` `env_runs=34`

## Critical Action Families

- `restore`: `step_rate=0.1459` `env_run_rate=1.0000`
- `remove`: `step_rate=0.1149` `env_run_rate=1.0000`
- `analyse`: `step_rate=0.0768` `env_run_rate=0.9750`
- `decoy`: `step_rate=0.6295` `env_run_rate=1.0000`
- `other`: `step_rate=0.0329` `env_run_rate=0.8938`

## Pre-Critical Containment

- `restore`: `step_rate=0.2547` `env_run_rate=0.9875`
- `remove`: `step_rate=0.0901` `env_run_rate=0.7688`
- `analyse`: `step_rate=0.0686` `env_run_rate=0.7375`
- `decoy`: `step_rate=0.5551` `env_run_rate=1.0000`
- `other`: `step_rate=0.0316` `env_run_rate=0.5000`
- `compromised_target_focus`: `step_rate=0.2380` `env_run_rate=0.9563`