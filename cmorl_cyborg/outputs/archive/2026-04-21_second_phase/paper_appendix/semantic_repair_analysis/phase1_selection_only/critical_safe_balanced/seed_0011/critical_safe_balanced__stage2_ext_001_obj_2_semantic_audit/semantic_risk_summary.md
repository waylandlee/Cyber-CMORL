# Semantic Risk Summary: stage2_ext_001_obj_2

- Candidate: `critical_safe_balanced` / `stage2_ext_001_obj_2`
- Trace dir: `/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/semantic_repair_traces/phase1_selection_only/critical_safe_balanced/ours_stage2_fair/seed_0011/critical_safe_balanced__stage2_ext_001_obj_2`
- Tight thresholds: `business >= -125.0` `cost >= -22.0`
- Audit verdict: `Red`

## Core Metrics

- Mean returns: `security=-550.4396` `business=-133.2491` `cost=-24.6500`
- Env-run feasible rate: `0.0000`
- Per-env violation rate: `business=0.8750` `cost=1.0000`
- Critical breach: `ever=1.0000` `persistent=0.8750`
- Mean critical dwell steps: `71.0000`
- Mean `Op_Server0` impact count: `62.9583`

## Risk Tiers

- `Tier 0 Safe`: count=`0` rate=`0.0000`
- `Tier 1 Near-Miss`: count=`0` rate=`0.0000`
- `Tier 2 Transient Critical Breach`: count=`3` rate=`0.1250`
- `Tier 3 Persistent Critical Breach`: count=`21` rate=`0.8750`

## Questionable Defense Actions

- High-confidence events: `count=651` `env_run_rate=1.0000`
- Medium-confidence events: `count=156` `env_run_rate=1.0000`
- `Q2_user_action_during_critical_breach`: `events=645` `env_runs=24`
- `Q3_missed_immediate_response_to_critical_hit`: `events=6` `env_runs=6`
- `Q4_user_focus_after_enterprise_foothold`: `events=116` `env_runs=22`
- `Q5_repeated_low_value_decoy_loop`: `events=40` `env_runs=24`

## Audit Comparison

| Audit | env-runs | feasible_rate | ever_critical | persistent_critical | high_conf_env_rate | verdict |
| --- | --- | --- | --- | --- | --- | --- |
| 3-episode audit | 24 | 0.0000 | 1.0000 | 0.8750 | 1.0000 | Red |
| 20-episode confirmatory audit | 160 | 0.0000 | 1.0000 | 0.8250 | 1.0000 | Red |

## Final Diagnosis

- `constraint-feasible but semantically fragile`