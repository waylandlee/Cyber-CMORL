# Semantic Risk Summary: stage1_pref_003_ckpt_096

- Candidate: `critical_safe_balanced_selected` / `stage1_pref_003_ckpt_096`
- Trace dir: `/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/critical_safe_v2_4obj_analysis/pilot/seed_0011/trace/ours_stage2_fair_critical_safe_v2_4obj/seed_0011/critical_safe_balanced_selected__stage1_pref_003_ckpt_096`
- Tight thresholds: `business >= -125.0` `cost >= -22.0`
- Audit verdict: `Red`

## Core Metrics

- Mean returns: `security=-1016.7075` `business=-127.9743` `cost=-20.1990`
- Mean `critical_host_safety`: `-0.7436`
- Env-run feasible rate: `0.4000`
- Per-env violation rate: `business=0.6000` `cost=0.0063`
- Critical breach: `ever=0.7937` `persistent=0.7937`
- Mean critical dwell steps: `54.0312`
- Mean `Op_Server0` impact count: `52.4438`

## Risk Tiers

- `Tier 0 Safe`: count=`0` rate=`0.0000`
- `Tier 1 Near-Miss`: count=`33` rate=`0.2062`
- `Tier 2 Transient Critical Breach`: count=`0` rate=`0.0000`
- `Tier 3 Persistent Critical Breach`: count=`127` rate=`0.7937`

## Questionable Defense Actions

- High-confidence events: `count=2913` `env_run_rate=0.7875`
- Medium-confidence events: `count=538` `env_run_rate=0.8938`
- `Q1_sleep_during_critical_breach`: `events=63` `env_runs=51`
- `Q2_user_action_during_critical_breach`: `events=2815` `env_runs=126`
- `Q3_missed_immediate_response_to_critical_hit`: `events=35` `env_runs=35`
- `Q4_user_focus_after_enterprise_foothold`: `events=515` `env_runs=143`
- `Q5_repeated_low_value_decoy_loop`: `events=23` `env_runs=22`