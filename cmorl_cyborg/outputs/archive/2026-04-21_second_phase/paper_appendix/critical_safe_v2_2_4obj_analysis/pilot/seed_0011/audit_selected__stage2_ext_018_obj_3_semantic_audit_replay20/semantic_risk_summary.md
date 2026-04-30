# Semantic Risk Summary: stage2_ext_018_obj_3

- Candidate: `audit_selected` / `stage2_ext_018_obj_3`
- Trace dir: `/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/critical_safe_v2_2_4obj_analysis/pilot/seed_0011/trace/ours_stage2_fair_critical_safe_v2_2_4obj/seed_0011/audit_selected__stage2_ext_018_obj_3`
- Tight thresholds: `business >= -125.0` `cost >= -22.0`
- Audit verdict: `Red`

## Core Metrics

- Mean returns: `security=-931.8856` `business=-116.5054` `cost=-21.4086`
- Mean `critical_host_safety`: `-0.6425`
- Env-run feasible rate: `0.4625`
- Per-env violation rate: `business=0.4562` `cost=0.1375`
- Critical breach: `ever=0.7500` `persistent=0.7438`
- Mean critical dwell steps: `51.2938`
- Mean `Op_Server0` impact count: `49.8000`

## Risk Tiers

- `Tier 0 Safe`: count=`0` rate=`0.0000`
- `Tier 1 Near-Miss`: count=`40` rate=`0.2500`
- `Tier 2 Transient Critical Breach`: count=`1` rate=`0.0063`
- `Tier 3 Persistent Critical Breach`: count=`119` rate=`0.7438`

## Questionable Defense Actions

- High-confidence events: `count=0` `env_run_rate=0.0000`
- Medium-confidence events: `count=0` `env_run_rate=0.0000`
- No questionable defense actions were detected under the configured rules.