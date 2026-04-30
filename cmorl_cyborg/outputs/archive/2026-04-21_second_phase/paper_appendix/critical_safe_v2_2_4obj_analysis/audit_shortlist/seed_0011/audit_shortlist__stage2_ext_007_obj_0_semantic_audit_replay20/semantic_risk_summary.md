# Semantic Risk Summary: stage2_ext_007_obj_0

- Candidate: `audit_shortlist` / `stage2_ext_007_obj_0`
- Trace dir: `/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/critical_safe_v2_2_4obj_analysis/audit_shortlist/seed_0011/trace/ours_stage2_fair_critical_safe_v2_2_4obj/seed_0011/audit_shortlist__stage2_ext_007_obj_0`
- Tight thresholds: `business >= -125.0` `cost >= -22.0`
- Audit verdict: `Red`

## Core Metrics

- Mean returns: `security=-580.4494` `business=-112.9071` `cost=-21.6420`
- Mean `critical_host_safety`: `-0.9837`
- Env-run feasible rate: `0.4875`
- Per-env violation rate: `business=0.3125` `cost=0.2875`
- Critical breach: `ever=0.9000` `persistent=0.6875`
- Mean critical dwell steps: `45.2250`
- Mean `Op_Server0` impact count: `42.8625`

## Risk Tiers

- `Tier 0 Safe`: count=`0` rate=`0.0000`
- `Tier 1 Near-Miss`: count=`8` rate=`0.1000`
- `Tier 2 Transient Critical Breach`: count=`17` rate=`0.2125`
- `Tier 3 Persistent Critical Breach`: count=`55` rate=`0.6875`

## Questionable Defense Actions

- High-confidence events: `count=0` `env_run_rate=0.0000`
- Medium-confidence events: `count=10` `env_run_rate=0.1125`
- `Q4_user_focus_after_enterprise_foothold`: `events=10` `env_runs=9`