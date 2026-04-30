# Semantic Risk Summary: stage1_pref_005_ckpt_191

- Candidate: `semantic_balanced_selected` / `stage1_pref_005_ckpt_191`
- Trace dir: `/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/semantic_repair_analysis/phase2_gate/seed_0011/semantic_balanced_selected__stage1_pref_005_ckpt_191_semantic_audit_replay20/replay_trace/ours_stage2_fair_semantic_gate/seed_0011/semantic_balanced_selected__stage1_pref_005_ckpt_191`
- Tight thresholds: `business >= -125.0` `cost >= -22.0`
- Audit verdict: `Red`

## Core Metrics

- Mean returns: `security=-679.8737` `business=-135.7822` `cost=-19.2044`
- Env-run feasible rate: `0.2437`
- Per-env violation rate: `business=0.7562` `cost=0.0125`
- Critical breach: `ever=1.0000` `persistent=0.8875`
- Mean critical dwell steps: `77.3937`
- Mean `Op_Server0` impact count: `73.7062`

## Risk Tiers

- `Tier 0 Safe`: count=`0` rate=`0.0000`
- `Tier 1 Near-Miss`: count=`0` rate=`0.0000`
- `Tier 2 Transient Critical Breach`: count=`18` rate=`0.1125`
- `Tier 3 Persistent Critical Breach`: count=`142` rate=`0.8875`

## Questionable Defense Actions

- High-confidence events: `count=913` `env_run_rate=0.9938`
- Medium-confidence events: `count=7` `env_run_rate=0.0437`
- `Q2_user_action_during_critical_breach`: `events=910` `env_runs=159`
- `Q3_missed_immediate_response_to_critical_hit`: `events=3` `env_runs=3`
- `Q4_user_focus_after_enterprise_foothold`: `events=6` `env_runs=6`
- `Q5_repeated_low_value_decoy_loop`: `events=1` `env_runs=1`

## Audit Comparison

| Audit | env-runs | feasible_rate | ever_critical | persistent_critical | high_conf_env_rate | verdict |
| --- | --- | --- | --- | --- | --- | --- |
| 20-episode audit | 160 | 0.2437 | 1.0000 | 0.8875 | 0.9938 | Red |
| 3-episode confirmatory audit | 24 | 0.2500 | 1.0000 | 0.9167 | 0.9583 | Red |

## Final Diagnosis

- `constraint-feasible but semantically fragile`