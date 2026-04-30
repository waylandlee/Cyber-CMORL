# Semantic Risk Summary: stage2_ext_006_obj_0

- Candidate: `semantic_balanced_selected` / `stage2_ext_006_obj_0`
- Trace dir: `/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/semantic_repair_traces/phase3_target/ours_stage2_fair_semantic_target/seed_0011/semantic_balanced_selected__stage2_ext_006_obj_0`
- Tight thresholds: `business >= -125.0` `cost >= -22.0`
- Audit verdict: `Red`

## Core Metrics

- Mean returns: `security=-475.2417` `business=-126.8045` `cost=-27.4246`
- Env-run feasible rate: `0.0000`
- Per-env violation rate: `business=0.6250` `cost=1.0000`
- Critical breach: `ever=1.0000` `persistent=0.7500`
- Mean critical dwell steps: `60.5833`
- Mean `Op_Server0` impact count: `51.1667`

## Risk Tiers

- `Tier 0 Safe`: count=`0` rate=`0.0000`
- `Tier 1 Near-Miss`: count=`0` rate=`0.0000`
- `Tier 2 Transient Critical Breach`: count=`6` rate=`0.2500`
- `Tier 3 Persistent Critical Breach`: count=`18` rate=`0.7500`

## Questionable Defense Actions

- High-confidence events: `count=419` `env_run_rate=1.0000`
- Medium-confidence events: `count=57` `env_run_rate=0.8750`
- `Q1_sleep_during_critical_breach`: `events=5` `env_runs=4`
- `Q2_user_action_during_critical_breach`: `events=409` `env_runs=24`
- `Q3_missed_immediate_response_to_critical_hit`: `events=5` `env_runs=5`
- `Q4_user_focus_after_enterprise_foothold`: `events=43` `env_runs=19`
- `Q5_repeated_low_value_decoy_loop`: `events=14` `env_runs=12`

## Audit Comparison

| Audit | env-runs | feasible_rate | ever_critical | persistent_critical | high_conf_env_rate | verdict |
| --- | --- | --- | --- | --- | --- | --- |
| 3-episode audit | 24 | 0.0000 | 1.0000 | 0.7500 | 1.0000 | Red |
| 20-episode confirmatory audit | 160 | 0.0000 | 1.0000 | 0.7063 | 1.0000 | Red |

## Final Diagnosis

- `constraint-feasible but semantically fragile`