# Semantic Risk Summary: stage1_pref_005_ckpt_191

- Candidate: `semantic_aware` / `stage1_pref_005_ckpt_191`
- Trace dir: `/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/semantic_repair_traces/phase1_selection_only/semantic_aware/ours_stage2_fair/seed_0011/semantic_aware__stage1_pref_005_ckpt_191`
- Tight thresholds: `business >= -125.0` `cost >= -22.0`
- Audit verdict: `Red`

## Core Metrics

- Mean returns: `security=-652.5792` `business=-133.9834` `cost=-19.3150`
- Env-run feasible rate: `0.2500`
- Per-env violation rate: `business=0.7500` `cost=0.0417`
- Critical breach: `ever=1.0000` `persistent=0.9167`
- Mean critical dwell steps: `74.0417`
- Mean `Op_Server0` impact count: `70.2917`

## Risk Tiers

- `Tier 0 Safe`: count=`0` rate=`0.0000`
- `Tier 1 Near-Miss`: count=`0` rate=`0.0000`
- `Tier 2 Transient Critical Breach`: count=`2` rate=`0.0833`
- `Tier 3 Persistent Critical Breach`: count=`22` rate=`0.9167`

## Questionable Defense Actions

- High-confidence events: `count=123` `env_run_rate=0.9583`
- Medium-confidence events: `count=0` `env_run_rate=0.0000`
- `Q2_user_action_during_critical_breach`: `events=123` `env_runs=23`

## Audit Comparison

| Audit | env-runs | feasible_rate | ever_critical | persistent_critical | high_conf_env_rate | verdict |
| --- | --- | --- | --- | --- | --- | --- |
| 3-episode audit | 24 | 0.2500 | 1.0000 | 0.9167 | 0.9583 | Red |
| 20-episode confirmatory audit | 160 | 0.2437 | 1.0000 | 0.8875 | 0.9938 | Red |

## Final Diagnosis

- `constraint-feasible but semantically fragile`