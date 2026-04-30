# Semantic Risk Summary: stage2_ext_002_obj_0

- Candidate: `selected` / `stage2_ext_002_obj_0`
- Trace dir: `/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_ablation/objective_3obj_vs_4obj/semantic_comparison/traces/ours_stage2/seed_0011/selected__stage2_ext_002_obj_0`
- Tight thresholds: `business >= -125.0` `cost >= -22.0`
- Audit verdict: `Red`

## Core Metrics

- Mean returns: `security=-411.4356` `business=-108.5491` `cost=-27.8101`
- Env-run feasible rate: `0.0000`
- Per-env violation rate: `business=0.0813` `cost=1.0000`
- Critical breach: `ever=1.0000` `persistent=0.6062`
- Mean critical dwell steps: `56.9250`
- Mean `Op_Server0` impact count: `51.6187`

## Risk Tiers

- `Tier 0 Safe`: count=`0` rate=`0.0000`
- `Tier 1 Near-Miss`: count=`0` rate=`0.0000`
- `Tier 2 Transient Critical Breach`: count=`63` rate=`0.3937`
- `Tier 3 Persistent Critical Breach`: count=`97` rate=`0.6062`

## Questionable Defense Actions

- High-confidence events: `count=1966` `env_run_rate=1.0000`
- Medium-confidence events: `count=153` `env_run_rate=0.5500`
- `Q1_sleep_during_critical_breach`: `events=59` `env_runs=50`
- `Q2_user_action_during_critical_breach`: `events=1893` `env_runs=160`
- `Q3_missed_immediate_response_to_critical_hit`: `events=14` `env_runs=14`
- `Q4_user_focus_after_enterprise_foothold`: `events=130` `env_runs=74`
- `Q5_repeated_low_value_decoy_loop`: `events=23` `env_runs=23`

## Critical Action Families

- `restore`: `step_rate=0.3532` `env_run_rate=1.0000`
- `remove`: `step_rate=0.0618` `env_run_rate=0.9500`
- `analyse`: `step_rate=0.0455` `env_run_rate=0.9250`
- `decoy`: `step_rate=0.5325` `env_run_rate=1.0000`
- `other`: `step_rate=0.0070` `env_run_rate=0.3375`

## Pre-Critical Containment

- `restore`: `step_rate=0.4856` `env_run_rate=1.0000`
- `remove`: `step_rate=0.0491` `env_run_rate=0.6875`
- `analyse`: `step_rate=0.0370` `env_run_rate=0.5563`
- `decoy`: `step_rate=0.4212` `env_run_rate=1.0000`
- `other`: `step_rate=0.0070` `env_run_rate=0.1437`
- `compromised_target_focus`: `step_rate=0.3170` `env_run_rate=0.9938`