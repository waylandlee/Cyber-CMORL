# Semantic Risk Summary: stage2_ext_005_obj_2

- Candidate: `audit_shortlist` / `stage2_ext_005_obj_2`
- Trace dir: `/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/critical_safe_v2_4_4obj_analysis/audit_shortlist/seed_0019/trace/ours_stage2_fair_critical_safe_v2_4_4obj/seed_0019/audit_shortlist__stage2_ext_005_obj_2`
- Tight thresholds: `business >= -125.0` `cost >= -22.0`
- Audit verdict: `Green`

## Core Metrics

- Mean returns: `security=-170.6000` `business=-27.7752` `cost=-19.8629`
- Mean `critical_host_safety`: `0.0000`
- Env-run feasible rate: `1.0000`
- Per-env violation rate: `business=0.0000` `cost=0.0000`
- Critical breach: `ever=0.0000` `persistent=0.0000`
- Mean critical dwell steps: `0.0000`
- Mean `Op_Server0` impact count: `0.0000`

## Risk Tiers

- `Tier 0 Safe`: count=`0` rate=`0.0000`
- `Tier 1 Near-Miss`: count=`80` rate=`1.0000`
- `Tier 2 Transient Critical Breach`: count=`0` rate=`0.0000`
- `Tier 3 Persistent Critical Breach`: count=`0` rate=`0.0000`

## Questionable Defense Actions

- High-confidence events: `count=0` `env_run_rate=0.0000`
- Medium-confidence events: `count=0` `env_run_rate=0.0000`
- No questionable defense actions were detected under the configured rules.

## Critical Action Families

- `restore`: `step_rate=0.0000` `env_run_rate=0.0000`
- `remove`: `step_rate=0.0000` `env_run_rate=0.0000`
- `analyse`: `step_rate=0.0000` `env_run_rate=0.0000`
- `decoy`: `step_rate=0.0000` `env_run_rate=0.0000`
- `other`: `step_rate=0.0000` `env_run_rate=0.0000`

## Pre-Critical Containment

- `restore`: `step_rate=1.0000` `env_run_rate=1.0000`
- `remove`: `step_rate=0.0000` `env_run_rate=0.0000`
- `analyse`: `step_rate=0.0000` `env_run_rate=0.0000`
- `decoy`: `step_rate=0.0000` `env_run_rate=0.0000`
- `other`: `step_rate=0.0000` `env_run_rate=0.0000`
- `compromised_target_focus`: `step_rate=1.0000` `env_run_rate=1.0000`