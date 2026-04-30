# Semantic Risk Summary: stage2_ext_002_obj_0

- Candidate: `semantic_balanced` / `stage2_ext_002_obj_0`
- Trace dir: `/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/semantic_repair_traces/phase1_selection_only/semantic_balanced/ours_stage2_fair/seed_0011/semantic_balanced__stage2_ext_002_obj_0`
- Tight thresholds: `business >= -125.0` `cost >= -22.0`
- Audit verdict: `Red`

## Core Metrics

- Mean returns: `security=-423.6333` `business=-108.1429` `cost=-28.0167`
- Env-run feasible rate: `0.0000`
- Per-env violation rate: `business=0.0833` `cost=1.0000`
- Critical breach: `ever=1.0000` `persistent=0.5000`
- Mean critical dwell steps: `55.2500`
- Mean `Op_Server0` impact count: `50.0000`

## Risk Tiers

- `Tier 0 Safe`: count=`0` rate=`0.0000`
- `Tier 1 Near-Miss`: count=`0` rate=`0.0000`
- `Tier 2 Transient Critical Breach`: count=`12` rate=`0.5000`
- `Tier 3 Persistent Critical Breach`: count=`12` rate=`0.5000`

## Questionable Defense Actions

- High-confidence events: `count=245` `env_run_rate=1.0000`
- Medium-confidence events: `count=20` `env_run_rate=0.5417`
- `Q1_sleep_during_critical_breach`: `events=5` `env_runs=4`
- `Q2_user_action_during_critical_breach`: `events=239` `env_runs=24`
- `Q3_missed_immediate_response_to_critical_hit`: `events=1` `env_runs=1`
- `Q4_user_focus_after_enterprise_foothold`: `events=14` `env_runs=10`
- `Q5_repeated_low_value_decoy_loop`: `events=6` `env_runs=6`

## Audit Comparison

| Audit | env-runs | feasible_rate | ever_critical | persistent_critical | high_conf_env_rate | verdict |
| --- | --- | --- | --- | --- | --- | --- |
| 3-episode audit | 24 | 0.0000 | 1.0000 | 0.5000 | 1.0000 | Red |
| 20-episode confirmatory audit | 160 | 0.0000 | 1.0000 | 0.6062 | 1.0000 | Red |

## Final Diagnosis

- `constraint-feasible but semantically fragile`