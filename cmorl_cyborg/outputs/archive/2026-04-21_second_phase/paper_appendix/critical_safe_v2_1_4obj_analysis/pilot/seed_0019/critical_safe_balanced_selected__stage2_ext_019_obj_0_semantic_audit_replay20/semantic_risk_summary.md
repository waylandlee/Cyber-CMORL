# Semantic Risk Summary: stage2_ext_019_obj_0

- Candidate: `critical_safe_balanced_selected` / `stage2_ext_019_obj_0`
- Trace dir: `/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/critical_safe_v2_1_4obj_analysis/pilot/seed_0019/trace/ours_stage2_fair_critical_safe_v2_1_4obj/seed_0019/critical_safe_balanced_selected__stage2_ext_019_obj_0`
- Tight thresholds: `business >= -125.0` `cost >= -22.0`
- Audit verdict: `Red`

## Core Metrics

- Mean returns: `security=-462.2744` `business=-128.1168` `cost=-25.8044`
- Mean `critical_host_safety`: `-4.8612`
- Env-run feasible rate: `0.0000`
- Per-env violation rate: `business=0.6438` `cost=1.0000`
- Critical breach: `ever=1.0000` `persistent=0.6188`
- Mean critical dwell steps: `54.2938`
- Mean `Op_Server0` impact count: `42.9375`

## Risk Tiers

- `Tier 0 Safe`: count=`0` rate=`0.0000`
- `Tier 1 Near-Miss`: count=`0` rate=`0.0000`
- `Tier 2 Transient Critical Breach`: count=`61` rate=`0.3812`
- `Tier 3 Persistent Critical Breach`: count=`99` rate=`0.6188`

## Questionable Defense Actions

- High-confidence events: `count=1694` `env_run_rate=1.0000`
- Medium-confidence events: `count=199` `env_run_rate=0.7063`
- `Q1_sleep_during_critical_breach`: `events=6` `env_runs=6`
- `Q2_user_action_during_critical_breach`: `events=1672` `env_runs=160`
- `Q3_missed_immediate_response_to_critical_hit`: `events=16` `env_runs=16`
- `Q4_user_focus_after_enterprise_foothold`: `events=109` `env_runs=72`
- `Q5_repeated_low_value_decoy_loop`: `events=90` `env_runs=90`