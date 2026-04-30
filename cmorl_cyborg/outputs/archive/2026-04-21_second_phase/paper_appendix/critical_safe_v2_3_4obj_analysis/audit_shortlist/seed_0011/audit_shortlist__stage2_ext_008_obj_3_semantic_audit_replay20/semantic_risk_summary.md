# Semantic Risk Summary: stage2_ext_008_obj_3

- Candidate: `audit_shortlist` / `stage2_ext_008_obj_3`
- Trace dir: `/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/critical_safe_v2_3_4obj_analysis/audit_shortlist/seed_0011/trace/ours_stage2_fair_critical_safe_v2_3_4obj/seed_0011/audit_shortlist__stage2_ext_008_obj_3`
- Tight thresholds: `business >= -125.0` `cost >= -22.0`
- Audit verdict: `Red`

## Core Metrics

- Mean returns: `security=-375.6481` `business=-87.9820` `cost=-21.8349`
- Mean `critical_host_safety`: `-2.2696`
- Env-run feasible rate: `0.7250`
- Per-env violation rate: `business=0.1000` `cost=0.2750`
- Critical breach: `ever=0.8250` `persistent=0.0000`
- Mean critical dwell steps: `5.5250`
- Mean `Op_Server0` impact count: `0.0000`

## Risk Tiers

- `Tier 0 Safe`: count=`0` rate=`0.0000`
- `Tier 1 Near-Miss`: count=`14` rate=`0.1750`
- `Tier 2 Transient Critical Breach`: count=`66` rate=`0.8250`
- `Tier 3 Persistent Critical Breach`: count=`0` rate=`0.0000`

## Questionable Defense Actions

- High-confidence events: `count=0` `env_run_rate=0.0000`
- Medium-confidence events: `count=0` `env_run_rate=0.0000`
- No questionable defense actions were detected under the configured rules.

## Critical Action Families

- `restore`: `step_rate=0.0566` `env_run_rate=0.2576`
- `remove`: `step_rate=0.0679` `env_run_rate=0.2879`
- `analyse`: `step_rate=0.0769` `env_run_rate=0.3030`
- `decoy`: `step_rate=0.7986` `env_run_rate=0.8636`
- `other`: `step_rate=0.0000` `env_run_rate=0.0000`