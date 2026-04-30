# Semantic Risk Summary: stage2_ext_000_obj_0

- Candidate: `semantic_balanced` / `stage2_ext_000_obj_0`
- Trace dir: `/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/semantic_repair_traces/phase1_selection_only/semantic_balanced/ours_stage2_fair/seed_0019/semantic_balanced__stage2_ext_000_obj_0`
- Tight thresholds: `business >= -125.0` `cost >= -22.0`
- Audit verdict: `Red`

## Core Metrics

- Mean returns: `security=-374.9312` `business=-105.3086` `cost=-26.8704`
- Env-run feasible rate: `0.0000`
- Per-env violation rate: `business=0.0417` `cost=1.0000`
- Critical breach: `ever=1.0000` `persistent=0.8333`
- Mean critical dwell steps: `55.6250`
- Mean `Op_Server0` impact count: `50.6250`

## Risk Tiers

- `Tier 0 Safe`: count=`0` rate=`0.0000`
- `Tier 1 Near-Miss`: count=`0` rate=`0.0000`
- `Tier 2 Transient Critical Breach`: count=`4` rate=`0.1667`
- `Tier 3 Persistent Critical Breach`: count=`20` rate=`0.8333`

## Questionable Defense Actions

- High-confidence events: `count=166` `env_run_rate=1.0000`
- Medium-confidence events: `count=13` `env_run_rate=0.3750`
- `Q2_user_action_during_critical_breach`: `events=164` `env_runs=24`
- `Q3_missed_immediate_response_to_critical_hit`: `events=2` `env_runs=2`
- `Q4_user_focus_after_enterprise_foothold`: `events=6` `env_runs=4`
- `Q5_repeated_low_value_decoy_loop`: `events=7` `env_runs=7`

## Audit Comparison

| Audit | env-runs | feasible_rate | ever_critical | persistent_critical | high_conf_env_rate | verdict |
| --- | --- | --- | --- | --- | --- | --- |
| 3-episode audit | 24 | 0.0000 | 1.0000 | 0.8333 | 1.0000 | Red |
| 20-episode confirmatory audit | 160 | 0.0000 | 1.0000 | 0.6375 | 0.9938 | Red |

## Final Diagnosis

- `constraint-feasible but semantically fragile`