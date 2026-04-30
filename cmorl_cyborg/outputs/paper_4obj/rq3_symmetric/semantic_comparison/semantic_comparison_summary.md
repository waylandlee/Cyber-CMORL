# RQ3 Semantic Comparison Summary

- Left method: `Constraint-Aware Stage-2` (`ours_stage2_v2_4`)
- Right method: `Unconstrained Stage-2` (`no_constraint_stage2_4obj`)

| seed | left_policy_id | right_policy_id | left_ever | right_ever | delta_ever | left_persistent | right_persistent | delta_persistent | left_tier1 | right_tier1 | delta_tier1 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 7 | stage2_ext_008_obj_0 | stage2_ext_008_obj_0 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.9938 | 0.0062 |
| 11 | stage2_ext_005_obj_1 | stage2_ext_002_obj_2 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.9750 | 0.0250 |
| 19 | stage2_ext_005_obj_2 | stage2_ext_009_obj_1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 1.0000 | 0.0000 |

## Aggregate

- `Constraint-Aware Stage-2 ever_critical_breach_rate = 0.0000`
- `Unconstrained Stage-2 ever_critical_breach_rate = 0.0000`
- `delta ever_critical_breach_rate = 0.0000`
- `Constraint-Aware Stage-2 persistent_critical_breach_rate = 0.0000`
- `Unconstrained Stage-2 persistent_critical_breach_rate = 0.0000`
- `delta persistent_critical_breach_rate = 0.0000`
- `Constraint-Aware Stage-2 Tier 1 Near-Miss = 1.0000`
- `Unconstrained Stage-2 Tier 1 Near-Miss = 0.9896`
- `delta Tier 1 Near-Miss = 0.0104`
- `Constraint-Aware Stage-2 precritical restore step rate = 1.0000`
- `Unconstrained Stage-2 precritical restore step rate = 1.0000`
- `delta precritical restore step rate = 0.0000`
- `Constraint-Aware Stage-2 precritical decoy step rate = 0.0000`
- `Unconstrained Stage-2 precritical decoy step rate = 0.0000`
- `delta precritical decoy step rate = 0.0000`