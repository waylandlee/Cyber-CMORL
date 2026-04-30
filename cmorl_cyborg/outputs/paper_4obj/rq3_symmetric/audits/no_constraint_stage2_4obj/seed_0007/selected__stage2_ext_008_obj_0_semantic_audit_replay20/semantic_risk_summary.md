# Semantic Risk Summary: stage2_ext_008_obj_0

- Candidate: `selected` / `stage2_ext_008_obj_0`
- Trace dir: `/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_4obj/rq3_symmetric/traces/no_constraint_stage2_4obj/seed_0007/selected__stage2_ext_008_obj_0`
- Tight thresholds: `business >= -125.0` `cost >= -22.0`
- Audit verdict: `Green`

## Core Metrics

- Mean returns: `security=-152.4612` `business=-25.5482` `cost=-23.4001`
- Mean `critical_host_safety`: `0.0000`
- Env-run feasible rate: `0.2562`
- Per-env violation rate: `business=0.0000` `cost=0.7438`
- Critical breach: `ever=0.0000` `persistent=0.0000`
- Mean critical dwell steps: `0.0000`
- Mean `Op_Server0` impact count: `0.0000`

## Risk Tiers

- `Tier 0 Safe`: count=`1` rate=`0.0063`
- `Tier 1 Near-Miss`: count=`159` rate=`0.9938`
- `Tier 2 Transient Critical Breach`: count=`0` rate=`0.0000`
- `Tier 3 Persistent Critical Breach`: count=`0` rate=`0.0000`

## Questionable Defense Actions

- High-confidence events: `count=0` `env_run_rate=0.0000`
- Medium-confidence events: `count=89` `env_run_rate=0.2188`
- `Q4_user_focus_after_enterprise_foothold`: `events=85` `env_runs=32`
- `Q5_repeated_low_value_decoy_loop`: `events=4` `env_runs=4`

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