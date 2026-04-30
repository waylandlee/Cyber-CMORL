# Semantic Risk Summary: stage2_ext_016_obj_2

- Candidate: `audit_selected` / `stage2_ext_016_obj_2`
- Trace dir: `/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/critical_safe_v2_3_4obj_analysis/pilot/seed_0011/trace/ours_stage2_fair_critical_safe_v2_3_4obj/seed_0011/audit_selected__stage2_ext_016_obj_2`
- Tight thresholds: `business >= -125.0` `cost >= -22.0`
- Audit verdict: `Red`

## Core Metrics

- Mean returns: `security=-265.6550` `business=-60.1603` `cost=-25.8791`
- Mean `critical_host_safety`: `-0.8748`
- Env-run feasible rate: `0.0000`
- Per-env violation rate: `business=0.0125` `cost=1.0000`
- Critical breach: `ever=0.5687` `persistent=0.0000`
- Mean critical dwell steps: `2.0187`
- Mean `Op_Server0` impact count: `0.0000`

## Risk Tiers

- `Tier 0 Safe`: count=`0` rate=`0.0000`
- `Tier 1 Near-Miss`: count=`69` rate=`0.4313`
- `Tier 2 Transient Critical Breach`: count=`91` rate=`0.5687`
- `Tier 3 Persistent Critical Breach`: count=`0` rate=`0.0000`

## Questionable Defense Actions

- High-confidence events: `count=0` `env_run_rate=0.0000`
- Medium-confidence events: `count=85` `env_run_rate=0.2437`
- `Q4_user_focus_after_enterprise_foothold`: `events=55` `env_runs=13`
- `Q5_repeated_low_value_decoy_loop`: `events=30` `env_runs=28`

## Critical Action Families

- `restore`: `step_rate=0.4644` `env_run_rate=0.5934`
- `remove`: `step_rate=0.0124` `env_run_rate=0.0440`
- `analyse`: `step_rate=0.0031` `env_run_rate=0.0110`
- `decoy`: `step_rate=0.5201` `env_run_rate=0.7692`
- `other`: `step_rate=0.0000` `env_run_rate=0.0000`

## Pre-Critical Containment

- `restore`: `step_rate=0.4342` `env_run_rate=1.0000`
- `remove`: `step_rate=0.0082` `env_run_rate=0.5250`
- `analyse`: `step_rate=0.1240` `env_run_rate=1.0000`
- `decoy`: `step_rate=0.4336` `env_run_rate=1.0000`
- `other`: `step_rate=0.0000` `env_run_rate=0.0000`
- `compromised_target_focus`: `step_rate=0.3378` `env_run_rate=1.0000`