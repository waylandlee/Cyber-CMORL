# Semantic Risk Summary: stage2_ext_018_obj_3

- Candidate: `audit_shortlist` / `stage2_ext_018_obj_3`
- Trace dir: `/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/critical_safe_v2_2_4obj_analysis/audit_shortlist/seed_0011/trace/ours_stage2_fair_critical_safe_v2_2_4obj/seed_0011/audit_shortlist__stage2_ext_018_obj_3`
- Tight thresholds: `business >= -125.0` `cost >= -22.0`
- Audit verdict: `Red`

## Core Metrics

- Mean returns: `security=-933.3462` `business=-116.2688` `cost=-21.3356`
- Mean `critical_host_safety`: `-0.6438`
- Env-run feasible rate: `0.4875`
- Per-env violation rate: `business=0.4750` `cost=0.0750`
- Critical breach: `ever=0.7500` `persistent=0.7375`
- Mean critical dwell steps: `51.8625`
- Mean `Op_Server0` impact count: `50.3750`

## Risk Tiers

- `Tier 0 Safe`: count=`0` rate=`0.0000`
- `Tier 1 Near-Miss`: count=`20` rate=`0.2500`
- `Tier 2 Transient Critical Breach`: count=`1` rate=`0.0125`
- `Tier 3 Persistent Critical Breach`: count=`59` rate=`0.7375`

## Questionable Defense Actions

- High-confidence events: `count=0` `env_run_rate=0.0000`
- Medium-confidence events: `count=0` `env_run_rate=0.0000`
- No questionable defense actions were detected under the configured rules.