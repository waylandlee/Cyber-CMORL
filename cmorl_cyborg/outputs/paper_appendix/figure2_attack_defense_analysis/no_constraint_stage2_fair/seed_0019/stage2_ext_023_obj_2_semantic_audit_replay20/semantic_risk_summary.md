# Semantic Risk Summary: stage2_ext_023_obj_2

- Candidate: `closest_candidate` / `stage2_ext_023_obj_2`
- Trace dir: `/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_appendix/figure2_attack_defense_analysis/no_constraint_stage2_fair/seed_0019/stage2_ext_023_obj_2_semantic_audit_replay20/replay_trace/no_constraint_stage2_fair/seed_0019/closest_candidate__stage2_ext_023_obj_2`
- Tight thresholds: `business >= -125.0` `cost >= -22.0`
- Audit verdict: `Red`

## Core Metrics

- Mean returns: `security=-947.0541` `business=-121.1175` `cost=-15.6081`
- Env-run feasible rate: `0.4313`
- Per-env violation rate: `business=0.5687` `cost=0.0000`
- Critical breach: `ever=0.7625` `persistent=0.7625`
- Mean critical dwell steps: `48.8125`
- Mean `Op_Server0` impact count: `47.2687`

## Risk Tiers

- `Tier 0 Safe`: count=`0` rate=`0.0000`
- `Tier 1 Near-Miss`: count=`38` rate=`0.2375`
- `Tier 2 Transient Critical Breach`: count=`0` rate=`0.0000`
- `Tier 3 Persistent Critical Breach`: count=`122` rate=`0.7625`

## Questionable Defense Actions

- High-confidence events: `count=4420` `env_run_rate=0.7562`
- Medium-confidence events: `count=2853` `env_run_rate=1.0000`
- `Q1_sleep_during_critical_breach`: `events=3` `env_runs=3`
- `Q2_user_action_during_critical_breach`: `events=4380` `env_runs=119`
- `Q3_missed_immediate_response_to_critical_hit`: `events=37` `env_runs=37`
- `Q4_user_focus_after_enterprise_foothold`: `events=2709` `env_runs=160`
- `Q5_repeated_low_value_decoy_loop`: `events=144` `env_runs=119`

## Audit Comparison

| Audit | env-runs | feasible_rate | ever_critical | persistent_critical | high_conf_env_rate | verdict |
| --- | --- | --- | --- | --- | --- | --- |
| 20-episode audit | 160 | 0.4313 | 0.7625 | 0.7625 | 0.7562 | Red |
| 3-episode confirmatory audit | 24 | 0.5833 | 0.6250 | 0.6250 | 0.6250 | Red |

## Final Diagnosis

- `constraint-feasible but semantically fragile`