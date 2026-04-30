# Semantic Risk Summary: stage2_ext_011_obj_0

- Candidate: `semantic_aware` / `stage2_ext_011_obj_0`
- Trace dir: `/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/semantic_repair_traces/phase1_selection_only/semantic_aware/ours_stage2_fair/seed_0007/semantic_aware__stage2_ext_011_obj_0`
- Tight thresholds: `business >= -125.0` `cost >= -22.0`
- Audit verdict: `Red`

## Core Metrics

- Mean returns: `security=-573.2333` `business=-139.4144` `cost=-19.2779`
- Env-run feasible rate: `0.2917`
- Per-env violation rate: `business=0.7083` `cost=0.0000`
- Critical breach: `ever=1.0000` `persistent=0.7917`
- Mean critical dwell steps: `58.4583`
- Mean `Op_Server0` impact count: `53.2917`

## Risk Tiers

- `Tier 0 Safe`: count=`0` rate=`0.0000`
- `Tier 1 Near-Miss`: count=`0` rate=`0.0000`
- `Tier 2 Transient Critical Breach`: count=`5` rate=`0.2083`
- `Tier 3 Persistent Critical Breach`: count=`19` rate=`0.7917`

## Questionable Defense Actions

- High-confidence events: `count=385` `env_run_rate=1.0000`
- Medium-confidence events: `count=40` `env_run_rate=0.7500`
- `Q1_sleep_during_critical_breach`: `events=4` `env_runs=4`
- `Q2_user_action_during_critical_breach`: `events=379` `env_runs=24`
- `Q3_missed_immediate_response_to_critical_hit`: `events=2` `env_runs=2`
- `Q4_user_focus_after_enterprise_foothold`: `events=40` `env_runs=18`

## Audit Comparison

| Audit | env-runs | feasible_rate | ever_critical | persistent_critical | high_conf_env_rate | verdict |
| --- | --- | --- | --- | --- | --- | --- |
| 3-episode audit | 24 | 0.2917 | 1.0000 | 0.7917 | 1.0000 | Red |
| 20-episode confirmatory audit | 160 | 0.1875 | 0.9938 | 0.8875 | 0.9875 | Red |

## Final Diagnosis

- `constraint-feasible but semantically fragile`