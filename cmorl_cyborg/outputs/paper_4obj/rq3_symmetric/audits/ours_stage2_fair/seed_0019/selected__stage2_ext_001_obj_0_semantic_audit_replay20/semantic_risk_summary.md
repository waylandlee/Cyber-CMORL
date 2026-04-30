# Semantic Risk Summary: stage2_ext_001_obj_0

- Candidate: `selected` / `stage2_ext_001_obj_0`
- Trace dir: `/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_4obj/rq3_symmetric/traces/ours_stage2_fair/seed_0019/selected__stage2_ext_001_obj_0`
- Tight thresholds: `business >= -125.0` `cost >= -22.0`
- Audit verdict: `Red`

## Core Metrics

- Mean returns: `security=-724.7875` `business=-119.0766` `cost=-22.3668`
- Env-run feasible rate: `0.1562`
- Per-env violation rate: `business=0.5000` `cost=0.7000`
- Critical breach: `ever=0.9625` `persistent=0.8750`
- Mean critical dwell steps: `60.4000`
- Mean `Op_Server0` impact count: `57.9438`

## Risk Tiers

- `Tier 0 Safe`: count=`0` rate=`0.0000`
- `Tier 1 Near-Miss`: count=`6` rate=`0.0375`
- `Tier 2 Transient Critical Breach`: count=`14` rate=`0.0875`
- `Tier 3 Persistent Critical Breach`: count=`140` rate=`0.8750`

## Questionable Defense Actions

- High-confidence events: `count=3924` `env_run_rate=0.9500`
- Medium-confidence events: `count=1165` `env_run_rate=0.9875`
- `Q1_sleep_during_critical_breach`: `events=42` `env_runs=38`
- `Q2_user_action_during_critical_breach`: `events=3863` `env_runs=152`
- `Q3_missed_immediate_response_to_critical_hit`: `events=19` `env_runs=19`
- `Q4_user_focus_after_enterprise_foothold`: `events=969` `env_runs=153`
- `Q5_repeated_low_value_decoy_loop`: `events=196` `env_runs=146`

## Critical Action Families

- `restore`: `step_rate=0.1099` `env_run_rate=0.9740`
- `remove`: `step_rate=0.0767` `env_run_rate=0.9740`
- `analyse`: `step_rate=0.0291` `env_run_rate=0.8052`
- `decoy`: `step_rate=0.7798` `env_run_rate=0.9935`
- `other`: `step_rate=0.0046` `env_run_rate=0.2597`

## Pre-Critical Containment

- `restore`: `step_rate=0.1443` `env_run_rate=0.9688`
- `remove`: `step_rate=0.0746` `env_run_rate=0.7188`
- `analyse`: `step_rate=0.0305` `env_run_rate=0.5500`
- `decoy`: `step_rate=0.7465` `env_run_rate=1.0000`
- `other`: `step_rate=0.0041` `env_run_rate=0.1250`
- `compromised_target_focus`: `step_rate=0.1832` `env_run_rate=0.9625`