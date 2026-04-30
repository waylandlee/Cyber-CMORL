# Semantic Risk Summary: stage1_pref_000_ckpt_191

- Candidate: `deployment_like` / `stage1_pref_000_ckpt_191`
- Trace dir: `/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/figure2_attack_defense_traces/ours_stage2_fair/seed_0007/deployment_like__stage1_pref_000_ckpt_191`
- Tight thresholds: `business >= -125.0` `cost >= -22.0`
- Audit verdict: `Red`

## Core Metrics

- Mean returns: `security=-395.5708` `business=-105.3407` `cost=-30.5108`
- Env-run feasible rate: `0.0000`
- Per-env violation rate: `business=0.1667` `cost=1.0000`
- Critical breach: `ever=1.0000` `persistent=0.2917`
- Mean critical dwell steps: `44.2917`
- Mean `Op_Server0` impact count: `37.2500`

## Risk Tiers

- `Tier 0 Safe`: count=`0` rate=`0.0000`
- `Tier 1 Near-Miss`: count=`0` rate=`0.0000`
- `Tier 2 Transient Critical Breach`: count=`17` rate=`0.7083`
- `Tier 3 Persistent Critical Breach`: count=`7` rate=`0.2917`

## Questionable Defense Actions

- High-confidence events: `count=254` `env_run_rate=1.0000`
- Medium-confidence events: `count=49` `env_run_rate=0.7083`
- `Q1_sleep_during_critical_breach`: `events=1` `env_runs=1`
- `Q2_user_action_during_critical_breach`: `events=253` `env_runs=24`
- `Q4_user_focus_after_enterprise_foothold`: `events=39` `env_runs=15`
- `Q5_repeated_low_value_decoy_loop`: `events=10` `env_runs=10`

## Audit Comparison

| Audit | env-runs | feasible_rate | ever_critical | persistent_critical | high_conf_env_rate | verdict |
| --- | --- | --- | --- | --- | --- | --- |
| 3-episode audit | 24 | 0.0000 | 1.0000 | 0.2917 | 1.0000 | Red |
| 20-episode confirmatory audit | 160 | 0.0000 | 1.0000 | 0.4562 | 1.0000 | Red |

## Final Diagnosis

- `constraint-feasible but semantically fragile`