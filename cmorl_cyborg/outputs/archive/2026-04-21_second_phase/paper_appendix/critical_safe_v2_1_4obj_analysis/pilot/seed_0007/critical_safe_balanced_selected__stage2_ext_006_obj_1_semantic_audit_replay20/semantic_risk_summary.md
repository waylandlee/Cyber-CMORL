# Semantic Risk Summary: stage2_ext_006_obj_1

- Candidate: `critical_safe_balanced_selected` / `stage2_ext_006_obj_1`
- Trace dir: `/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/critical_safe_v2_1_4obj_analysis/pilot/seed_0007/trace/ours_stage2_fair_critical_safe_v2_1_4obj/seed_0007/critical_safe_balanced_selected__stage2_ext_006_obj_1`
- Tight thresholds: `business >= -125.0` `cost >= -22.0`
- Audit verdict: `Red`

## Core Metrics

- Mean returns: `security=-920.6069` `business=-110.2868` `cost=-22.5270`
- Mean `critical_host_safety`: `-0.7364`
- Env-run feasible rate: `0.1437`
- Per-env violation rate: `business=0.2812` `cost=0.7875`
- Critical breach: `ever=0.8562` `persistent=0.8250`
- Mean critical dwell steps: `55.7938`
- Mean `Op_Server0` impact count: `54.0688`

## Risk Tiers

- `Tier 0 Safe`: count=`0` rate=`0.0000`
- `Tier 1 Near-Miss`: count=`23` rate=`0.1437`
- `Tier 2 Transient Critical Breach`: count=`5` rate=`0.0312`
- `Tier 3 Persistent Critical Breach`: count=`132` rate=`0.8250`

## Questionable Defense Actions

- High-confidence events: `count=3242` `env_run_rate=0.8562`
- Medium-confidence events: `count=1018` `env_run_rate=1.0000`
- `Q1_sleep_during_critical_breach`: `events=3` `env_runs=3`
- `Q2_user_action_during_critical_breach`: `events=3228` `env_runs=137`
- `Q3_missed_immediate_response_to_critical_hit`: `events=11` `env_runs=11`
- `Q4_user_focus_after_enterprise_foothold`: `events=741` `env_runs=156`
- `Q5_repeated_low_value_decoy_loop`: `events=277` `env_runs=155`