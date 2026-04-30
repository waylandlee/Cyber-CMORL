# Semantic Risk Summary: stage2_ext_002_obj_2

- Candidate: `selected` / `stage2_ext_002_obj_2`
- Trace dir: `/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_4obj/rq3_symmetric/traces/no_constraint_stage2_4obj/seed_0011/selected__stage2_ext_002_obj_2`
- Tight thresholds: `business >= -125.0` `cost >= -22.0`
- Audit verdict: `Green`

## Core Metrics

- Mean returns: `security=-136.7794` `business=-23.0312` `cost=-25.2518`
- Mean `critical_host_safety`: `0.0000`
- Env-run feasible rate: `0.3812`
- Per-env violation rate: `business=0.0000` `cost=0.6188`
- Critical breach: `ever=0.0000` `persistent=0.0000`
- Mean critical dwell steps: `0.0000`
- Mean `Op_Server0` impact count: `0.0000`

## Risk Tiers

- `Tier 0 Safe`: count=`4` rate=`0.0250`
- `Tier 1 Near-Miss`: count=`156` rate=`0.9750`
- `Tier 2 Transient Critical Breach`: count=`0` rate=`0.0000`
- `Tier 3 Persistent Critical Breach`: count=`0` rate=`0.0000`

## Questionable Defense Actions

- High-confidence events: `count=0` `env_run_rate=0.0000`
- Medium-confidence events: `count=280` `env_run_rate=0.6562`
- `Q4_user_focus_after_enterprise_foothold`: `events=152` `env_runs=56`
- `Q5_repeated_low_value_decoy_loop`: `events=128` `env_runs=99`

## Critical Action Families

- `restore`: `step_rate=0.0000` `env_run_rate=0.0000`
- `remove`: `step_rate=0.0000` `env_run_rate=0.0000`
- `analyse`: `step_rate=0.0000` `env_run_rate=0.0000`
- `decoy`: `step_rate=0.0000` `env_run_rate=0.0000`
- `other`: `step_rate=0.0000` `env_run_rate=0.0000`

## Pre-Critical Containment

- `restore`: `step_rate=1.0000` `env_run_rate=1.0000`
- `remove`: `step_rate=0.0000` `env_run_rate=0.0000`
- `analyse`: `step_rate=0.0000` `env_run_rate=0.0000`
- `decoy`: `step_rate=0.0000` `env_run_rate=0.0000`
- `other`: `step_rate=0.0000` `env_run_rate=0.0000`
- `compromised_target_focus`: `step_rate=1.0000` `env_run_rate=1.0000`