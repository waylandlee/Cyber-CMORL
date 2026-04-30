# Semantic Risk Summary: stage2_ext_001_obj_2

- Candidate: `critical_safe_balanced` / `stage2_ext_001_obj_2`
- Trace dir: `/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/semantic_repair_analysis/phase1_selection_only/critical_safe_balanced/seed_0011/critical_safe_balanced__stage2_ext_001_obj_2_semantic_audit_replay20/replay_trace/ours_stage2_fair/seed_0011/critical_safe_balanced__stage2_ext_001_obj_2`
- Tight thresholds: `business >= -125.0` `cost >= -22.0`
- Audit verdict: `Red`

## Core Metrics

- Mean returns: `security=-521.1256` `business=-132.7915` `cost=-24.6449`
- Env-run feasible rate: `0.0000`
- Per-env violation rate: `business=0.8562` `cost=1.0000`
- Critical breach: `ever=1.0000` `persistent=0.8250`
- Mean critical dwell steps: `71.7062`
- Mean `Op_Server0` impact count: `64.1625`

## Risk Tiers

- `Tier 0 Safe`: count=`0` rate=`0.0000`
- `Tier 1 Near-Miss`: count=`0` rate=`0.0000`
- `Tier 2 Transient Critical Breach`: count=`28` rate=`0.1750`
- `Tier 3 Persistent Critical Breach`: count=`132` rate=`0.8250`

## Questionable Defense Actions

- High-confidence events: `count=4442` `env_run_rate=1.0000`
- Medium-confidence events: `count=1055` `env_run_rate=1.0000`
- `Q1_sleep_during_critical_breach`: `events=1` `env_runs=1`
- `Q2_user_action_during_critical_breach`: `events=4401` `env_runs=160`
- `Q3_missed_immediate_response_to_critical_hit`: `events=40` `env_runs=40`
- `Q4_user_focus_after_enterprise_foothold`: `events=809` `env_runs=156`
- `Q5_repeated_low_value_decoy_loop`: `events=246` `env_runs=154`

## Audit Comparison

| Audit | env-runs | feasible_rate | ever_critical | persistent_critical | high_conf_env_rate | verdict |
| --- | --- | --- | --- | --- | --- | --- |
| 20-episode audit | 160 | 0.0000 | 1.0000 | 0.8250 | 1.0000 | Red |
| 3-episode confirmatory audit | 24 | 0.0000 | 1.0000 | 0.8750 | 1.0000 | Red |

## Final Diagnosis

- `constraint-feasible but semantically fragile`