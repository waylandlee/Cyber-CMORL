# Semantic Risk Summary: stage2_ext_006_obj_0

- Candidate: `gate_selected` / `stage2_ext_006_obj_0`
- Trace dir: `/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/critical_safe_v2_1_4obj_analysis/pilot/seed_0011/trace/ours_stage2_fair_critical_safe_v2_1_4obj/seed_0011/gate_selected__stage2_ext_006_obj_0`
- Tight thresholds: `business >= -125.0` `cost >= -22.0`
- Audit verdict: `Red`

## Core Metrics

- Mean returns: `security=-1000.3794` `business=-124.2477` `cost=-21.3580`
- Mean `critical_host_safety`: `-0.6764`
- Env-run feasible rate: `0.3625`
- Per-env violation rate: `business=0.5813` `cost=0.1625`
- Critical breach: `ever=0.7812` `persistent=0.7812`
- Mean critical dwell steps: `53.6812`
- Mean `Op_Server0` impact count: `52.1125`

## Risk Tiers

- `Tier 0 Safe`: count=`0` rate=`0.0000`
- `Tier 1 Near-Miss`: count=`35` rate=`0.2188`
- `Tier 2 Transient Critical Breach`: count=`0` rate=`0.0000`
- `Tier 3 Persistent Critical Breach`: count=`125` rate=`0.7812`

## Questionable Defense Actions

- High-confidence events: `count=2820` `env_run_rate=0.7812`
- Medium-confidence events: `count=523` `env_run_rate=0.9062`
- `Q1_sleep_during_critical_breach`: `events=67` `env_runs=47`
- `Q2_user_action_during_critical_breach`: `events=2730` `env_runs=125`
- `Q3_missed_immediate_response_to_critical_hit`: `events=23` `env_runs=23`
- `Q4_user_focus_after_enterprise_foothold`: `events=510` `env_runs=145`
- `Q5_repeated_low_value_decoy_loop`: `events=13` `env_runs=13`