# Semantic Risk Summary: stage1_pref_003_ckpt_191

- Candidate: `critical_safe_balanced_selected` / `stage1_pref_003_ckpt_191`
- Trace dir: `/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/critical_safe_v2_1_4obj_analysis/pilot/seed_0011/trace/ours_stage2_fair_critical_safe_v2_1_4obj/seed_0011/critical_safe_balanced_selected__stage1_pref_003_ckpt_191`
- Tight thresholds: `business >= -125.0` `cost >= -22.0`
- Audit verdict: `Red`

## Core Metrics

- Mean returns: `security=-1025.3672` `business=-129.4241` `cost=-20.2023`
- Mean `critical_host_safety`: `-0.6527`
- Env-run feasible rate: `0.4188`
- Per-env violation rate: `business=0.5813` `cost=0.0000`
- Critical breach: `ever=0.7562` `persistent=0.7562`
- Mean critical dwell steps: `52.5438`
- Mean `Op_Server0` impact count: `51.0312`

## Risk Tiers

- `Tier 0 Safe`: count=`0` rate=`0.0000`
- `Tier 1 Near-Miss`: count=`39` rate=`0.2437`
- `Tier 2 Transient Critical Breach`: count=`0` rate=`0.0000`
- `Tier 3 Persistent Critical Breach`: count=`121` rate=`0.7562`

## Questionable Defense Actions

- High-confidence events: `count=2941` `env_run_rate=0.7562`
- Medium-confidence events: `count=611` `env_run_rate=0.9250`
- `Q1_sleep_during_critical_breach`: `events=46` `env_runs=37`
- `Q2_user_action_during_critical_breach`: `events=2863` `env_runs=120`
- `Q3_missed_immediate_response_to_critical_hit`: `events=32` `env_runs=32`
- `Q4_user_focus_after_enterprise_foothold`: `events=594` `env_runs=147`
- `Q5_repeated_low_value_decoy_loop`: `events=17` `env_runs=17`