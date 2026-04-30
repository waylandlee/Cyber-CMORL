# Semantic Risk Summary: stage2_ext_016_obj_2

- Candidate: `audit_shortlist` / `stage2_ext_016_obj_2`
- Trace dir: `/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/critical_safe_v2_2_4obj_analysis/audit_shortlist/seed_0011/trace/ours_stage2_fair_critical_safe_v2_2_4obj/seed_0011/audit_shortlist__stage2_ext_016_obj_2`
- Tight thresholds: `business >= -125.0` `cost >= -22.0`
- Audit verdict: `Red`

## Core Metrics

- Mean returns: `security=-272.9837` `business=-62.1869` `cost=-26.0289`
- Mean `critical_host_safety`: `-1.1855`
- Env-run feasible rate: `0.0000`
- Per-env violation rate: `business=0.0250` `cost=1.0000`
- Critical breach: `ever=0.6375` `persistent=0.0000`
- Mean critical dwell steps: `2.7375`
- Mean `Op_Server0` impact count: `0.0000`

## Risk Tiers

- `Tier 0 Safe`: count=`0` rate=`0.0000`
- `Tier 1 Near-Miss`: count=`29` rate=`0.3625`
- `Tier 2 Transient Critical Breach`: count=`51` rate=`0.6375`
- `Tier 3 Persistent Critical Breach`: count=`0` rate=`0.0000`

## Questionable Defense Actions

- High-confidence events: `count=0` `env_run_rate=0.0000`
- Medium-confidence events: `count=29` `env_run_rate=0.2375`
- `Q4_user_focus_after_enterprise_foothold`: `events=16` `env_runs=6`
- `Q5_repeated_low_value_decoy_loop`: `events=13` `env_runs=13`

## Critical Action Families

- `restore`: `step_rate=0.4749` `env_run_rate=0.5686`
- `remove`: `step_rate=0.0091` `env_run_rate=0.0392`
- `analyse`: `step_rate=0.0046` `env_run_rate=0.0196`
- `decoy`: `step_rate=0.5114` `env_run_rate=0.8039`
- `other`: `step_rate=0.0000` `env_run_rate=0.0000`