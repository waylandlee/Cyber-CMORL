# Semantic Risk Summary: stage2_ext_005_obj_0

- Candidate: `objective_selected` / `stage2_ext_005_obj_0`
- Trace dir: `/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/critical_safe_v2_1_4obj_analysis/baseline/seed_0007/trace/ours_stage2_fair/seed_0007/objective_selected__stage2_ext_005_obj_0`
- Tight thresholds: `business >= -125.0` `cost >= -22.0`
- Audit verdict: `Red`

## Core Metrics

- Mean returns: `security=-513.6059` `business=-116.6947` `cost=-24.4253`
- Env-run feasible rate: `0.0000`
- Per-env violation rate: `business=0.3125` `cost=0.9938`
- Critical breach: `ever=1.0000` `persistent=0.7750`
- Mean critical dwell steps: `67.2125`
- Mean `Op_Server0` impact count: `63.1125`

## Risk Tiers

- `Tier 0 Safe`: count=`0` rate=`0.0000`
- `Tier 1 Near-Miss`: count=`0` rate=`0.0000`
- `Tier 2 Transient Critical Breach`: count=`36` rate=`0.2250`
- `Tier 3 Persistent Critical Breach`: count=`124` rate=`0.7750`

## Questionable Defense Actions

- High-confidence events: `count=2736` `env_run_rate=1.0000`
- Medium-confidence events: `count=339` `env_run_rate=0.8375`
- `Q1_sleep_during_critical_breach`: `events=126` `env_runs=88`
- `Q2_user_action_during_critical_breach`: `events=2598` `env_runs=160`
- `Q3_missed_immediate_response_to_critical_hit`: `events=12` `env_runs=12`
- `Q4_user_focus_after_enterprise_foothold`: `events=220` `env_runs=103`
- `Q5_repeated_low_value_decoy_loop`: `events=119` `env_runs=111`