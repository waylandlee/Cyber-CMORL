# Semantic Risk Summary: stage1_pref_000_ckpt_191

- Candidate: `semantic_balanced` / `stage1_pref_000_ckpt_191`
- Trace dir: `/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/semantic_repair_analysis/phase1_selection_only/semantic_balanced/seed_0007/semantic_balanced__stage1_pref_000_ckpt_191_semantic_audit_replay20/replay_trace/ours_stage2_fair/seed_0007/semantic_balanced__stage1_pref_000_ckpt_191`
- Tight thresholds: `business >= -125.0` `cost >= -22.0`
- Audit verdict: `Red`

## Core Metrics

- Mean returns: `security=-404.3903` `business=-108.1466` `cost=-30.8043`
- Env-run feasible rate: `0.0000`
- Per-env violation rate: `business=0.2437` `cost=1.0000`
- Critical breach: `ever=1.0000` `persistent=0.4562`
- Mean critical dwell steps: `46.9062`
- Mean `Op_Server0` impact count: `39.2313`

## Risk Tiers

- `Tier 0 Safe`: count=`0` rate=`0.0000`
- `Tier 1 Near-Miss`: count=`0` rate=`0.0000`
- `Tier 2 Transient Critical Breach`: count=`87` rate=`0.5437`
- `Tier 3 Persistent Critical Breach`: count=`73` rate=`0.4562`

## Questionable Defense Actions

- High-confidence events: `count=1693` `env_run_rate=1.0000`
- Medium-confidence events: `count=239` `env_run_rate=0.7125`
- `Q1_sleep_during_critical_breach`: `events=6` `env_runs=6`
- `Q2_user_action_during_critical_breach`: `events=1683` `env_runs=160`
- `Q3_missed_immediate_response_to_critical_hit`: `events=4` `env_runs=4`
- `Q4_user_focus_after_enterprise_foothold`: `events=178` `env_runs=97`
- `Q5_repeated_low_value_decoy_loop`: `events=61` `env_runs=57`

## Audit Comparison

| Audit | env-runs | feasible_rate | ever_critical | persistent_critical | high_conf_env_rate | verdict |
| --- | --- | --- | --- | --- | --- | --- |
| 20-episode audit | 160 | 0.0000 | 1.0000 | 0.4562 | 1.0000 | Red |
| 3-episode confirmatory audit | 24 | 0.0000 | 1.0000 | 0.2917 | 1.0000 | Red |

## Final Diagnosis

- `constraint-feasible but semantically fragile`