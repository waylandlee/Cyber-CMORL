# Semantic Risk Summary: stage2_ext_022_obj_1

- Candidate: `selected` / `stage2_ext_022_obj_1`
- Trace dir: `/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_4obj/rq3_symmetric/traces/no_constraint_stage2_fair/seed_0007/selected__stage2_ext_022_obj_1`
- Tight thresholds: `business >= -125.0` `cost >= -22.0`
- Audit verdict: `Red`

## Core Metrics

- Mean returns: `security=-1092.4781` `business=-118.2996` `cost=-18.8480`
- Env-run feasible rate: `0.5813`
- Per-env violation rate: `business=0.4188` `cost=0.0000`
- Critical breach: `ever=0.9750` `persistent=0.9688`
- Mean critical dwell steps: `73.1125`
- Mean `Op_Server0` impact count: `71.0938`

## Risk Tiers

- `Tier 0 Safe`: count=`0` rate=`0.0000`
- `Tier 1 Near-Miss`: count=`4` rate=`0.0250`
- `Tier 2 Transient Critical Breach`: count=`1` rate=`0.0063`
- `Tier 3 Persistent Critical Breach`: count=`155` rate=`0.9688`

## Questionable Defense Actions

- High-confidence events: `count=5237` `env_run_rate=0.9750`
- Medium-confidence events: `count=368` `env_run_rate=0.8125`
- `Q1_sleep_during_critical_breach`: `events=1794` `env_runs=155`
- `Q2_user_action_during_critical_breach`: `events=3401` `env_runs=155`
- `Q3_missed_immediate_response_to_critical_hit`: `events=42` `env_runs=42`
- `Q4_user_focus_after_enterprise_foothold`: `events=338` `env_runs=127`
- `Q5_repeated_low_value_decoy_loop`: `events=30` `env_runs=28`

## Critical Action Families

- `restore`: `step_rate=0.1384` `env_run_rate=0.9872`
- `remove`: `step_rate=0.0580` `env_run_rate=0.9615`
- `analyse`: `step_rate=0.0895` `env_run_rate=0.9808`
- `decoy`: `step_rate=0.5567` `env_run_rate=1.0000`
- `other`: `step_rate=0.1574` `env_run_rate=0.9936`

## Pre-Critical Containment

- `restore`: `step_rate=0.1398` `env_run_rate=0.7875`
- `remove`: `step_rate=0.0515` `env_run_rate=0.4938`
- `analyse`: `step_rate=0.0853` `env_run_rate=0.6625`
- `decoy`: `step_rate=0.5689` `env_run_rate=0.9875`
- `other`: `step_rate=0.1545` `env_run_rate=0.8063`
- `compromised_target_focus`: `step_rate=0.1417` `env_run_rate=0.7312`