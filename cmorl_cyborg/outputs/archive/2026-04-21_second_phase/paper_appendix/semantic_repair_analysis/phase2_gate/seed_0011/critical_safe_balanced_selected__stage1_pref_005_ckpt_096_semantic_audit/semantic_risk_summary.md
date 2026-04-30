# Semantic Risk Summary: stage1_pref_005_ckpt_096

- Candidate: `critical_safe_balanced_selected` / `stage1_pref_005_ckpt_096`
- Trace dir: `/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/semantic_repair_traces/phase2_gate/ours_stage2_fair_critical_safe_v1/seed_0011/critical_safe_balanced_selected__stage1_pref_005_ckpt_096`
- Tight thresholds: `business >= -125.0` `cost >= -22.0`
- Audit verdict: `Red`

## Core Metrics

- Mean returns: `security=-522.3875` `business=-132.5596` `cost=-25.4588`
- Env-run feasible rate: `0.0000`
- Per-env violation rate: `business=0.8750` `cost=1.0000`
- Critical breach: `ever=1.0000` `persistent=0.9167`
- Mean critical dwell steps: `68.7083`
- Mean `Op_Server0` impact count: `58.6667`

## Risk Tiers

- `Tier 0 Safe`: count=`0` rate=`0.0000`
- `Tier 1 Near-Miss`: count=`0` rate=`0.0000`
- `Tier 2 Transient Critical Breach`: count=`2` rate=`0.0833`
- `Tier 3 Persistent Critical Breach`: count=`22` rate=`0.9167`

## Questionable Defense Actions

- High-confidence events: `count=478` `env_run_rate=1.0000`
- Medium-confidence events: `count=70` `env_run_rate=0.9167`
- `Q2_user_action_during_critical_breach`: `events=477` `env_runs=24`
- `Q3_missed_immediate_response_to_critical_hit`: `events=1` `env_runs=1`
- `Q4_user_focus_after_enterprise_foothold`: `events=50` `env_runs=19`
- `Q5_repeated_low_value_decoy_loop`: `events=20` `env_runs=20`

## Audit Comparison

| Audit | env-runs | feasible_rate | ever_critical | persistent_critical | high_conf_env_rate | verdict |
| --- | --- | --- | --- | --- | --- | --- |
| 3-episode audit | 24 | 0.0000 | 1.0000 | 0.9167 | 1.0000 | Red |
| 20-episode confirmatory audit | 160 | 0.0000 | 1.0000 | 0.8375 | 1.0000 | Red |

## Final Diagnosis

- `constraint-feasible but semantically fragile`