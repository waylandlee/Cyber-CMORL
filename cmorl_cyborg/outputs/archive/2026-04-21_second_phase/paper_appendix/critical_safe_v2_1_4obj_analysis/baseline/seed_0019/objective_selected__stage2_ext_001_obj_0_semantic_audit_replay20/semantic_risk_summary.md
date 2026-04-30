# Semantic Risk Summary: stage2_ext_001_obj_0

- Candidate: `objective_selected` / `stage2_ext_001_obj_0`
- Trace dir: `/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/critical_safe_v2_1_4obj_analysis/baseline/seed_0019/trace/ours_stage2_fair/seed_0019/objective_selected__stage2_ext_001_obj_0`
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