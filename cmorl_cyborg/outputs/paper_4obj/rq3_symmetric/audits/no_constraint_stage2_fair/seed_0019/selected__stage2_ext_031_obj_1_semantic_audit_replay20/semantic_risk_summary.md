# Semantic Risk Summary: stage2_ext_031_obj_1

- Candidate: `selected` / `stage2_ext_031_obj_1`
- Trace dir: `/home/waylandlee/CMORL2/Cyber-CMORL/cmorl_cyborg/outputs/paper_4obj/rq3_symmetric/traces/no_constraint_stage2_fair/seed_0019/selected__stage2_ext_031_obj_1`
- Tight thresholds: `business >= -125.0` `cost >= -22.0`
- Audit verdict: `Red`

## Core Metrics

- Mean returns: `security=-948.3031` `business=-125.7047` `cost=-21.8896`
- Env-run feasible rate: `0.1875`
- Per-env violation rate: `business=0.7063` `cost=0.4313`
- Critical breach: `ever=0.9875` `persistent=0.9625`
- Mean critical dwell steps: `79.7687`
- Mean `Op_Server0` impact count: `77.1625`

## Risk Tiers

- `Tier 0 Safe`: count=`2` rate=`0.0125`
- `Tier 1 Near-Miss`: count=`0` rate=`0.0000`
- `Tier 2 Transient Critical Breach`: count=`4` rate=`0.0250`
- `Tier 3 Persistent Critical Breach`: count=`154` rate=`0.9625`

## Questionable Defense Actions

- High-confidence events: `count=5677` `env_run_rate=0.9875`
- Medium-confidence events: `count=1169` `env_run_rate=0.9750`
- `Q1_sleep_during_critical_breach`: `events=296` `env_runs=133`
- `Q2_user_action_during_critical_breach`: `events=5333` `env_runs=158`
- `Q3_missed_immediate_response_to_critical_hit`: `events=48` `env_runs=48`
- `Q4_user_focus_after_enterprise_foothold`: `events=1040` `env_runs=156`
- `Q5_repeated_low_value_decoy_loop`: `events=129` `env_runs=102`

## Critical Action Families

- `restore`: `step_rate=0.1560` `env_run_rate=1.0000`
- `remove`: `step_rate=0.0478` `env_run_rate=0.9937`
- `analyse`: `step_rate=0.0977` `env_run_rate=1.0000`
- `decoy`: `step_rate=0.6750` `env_run_rate=1.0000`
- `other`: `step_rate=0.0235` `env_run_rate=0.8544`

## Pre-Critical Containment

- `restore`: `step_rate=0.2199` `env_run_rate=0.7911`
- `remove`: `step_rate=0.0380` `env_run_rate=0.2848`
- `analyse`: `step_rate=0.0979` `env_run_rate=0.5759`
- `decoy`: `step_rate=0.6236` `env_run_rate=0.9937`
- `other`: `step_rate=0.0207` `env_run_rate=0.1709`
- `compromised_target_focus`: `step_rate=0.1865` `env_run_rate=0.7215`