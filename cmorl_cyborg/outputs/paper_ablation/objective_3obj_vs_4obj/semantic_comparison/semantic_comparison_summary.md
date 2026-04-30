# RQ3 Semantic Comparison Summary

- Left method: `3-Objective Stage-2` (`ours_stage2`)
- Right method: `4-Objective Stage-2` (`ours_stage2_v2_4`)

| seed | left_policy_id | right_policy_id | left_ever | right_ever | delta_ever | left_persistent | right_persistent | delta_persistent | left_tier1 | right_tier1 | delta_tier1 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 7 | stage1_pref_000_ckpt_191 | stage2_ext_008_obj_0 | 1.0000 | 0.0000 | 1.0000 | 0.4562 | 0.0000 | 0.4562 | 0.0000 | 1.0000 | -1.0000 |
| 11 | stage2_ext_002_obj_0 | stage2_ext_005_obj_1 | 1.0000 | 0.0000 | 1.0000 | 0.6062 | 0.0000 | 0.6062 | 0.0000 | 1.0000 | -1.0000 |
| 19 | stage2_ext_001_obj_0 | stage2_ext_005_obj_2 | 0.9625 | 0.0000 | 0.9625 | 0.8750 | 0.0000 | 0.8750 | 0.0375 | 1.0000 | -0.9625 |

## Aggregate

- `3-Objective Stage-2 ever_critical_breach_rate = 0.9875`
- `4-Objective Stage-2 ever_critical_breach_rate = 0.0000`
- `delta ever_critical_breach_rate = 0.9875`
- `3-Objective Stage-2 persistent_critical_breach_rate = 0.6458`
- `4-Objective Stage-2 persistent_critical_breach_rate = 0.0000`
- `delta persistent_critical_breach_rate = 0.6458`
- `3-Objective Stage-2 Tier 1 Near-Miss = 0.0125`
- `4-Objective Stage-2 Tier 1 Near-Miss = 1.0000`
- `delta Tier 1 Near-Miss = -0.9875`
- `3-Objective Stage-2 precritical restore step rate = 0.4126`
- `4-Objective Stage-2 precritical restore step rate = 1.0000`
- `delta precritical restore step rate = -0.5874`
- `3-Objective Stage-2 precritical decoy step rate = 0.4895`
- `4-Objective Stage-2 precritical decoy step rate = 0.0000`
- `delta precritical decoy step rate = 0.4895`