# Critical Casebook

## Earliest Critical Breach

No matching env-run was available for this case.

## Worst Business Return

- Basic info: `episode_id=episode_004` `env_idx=4` `env_seed=4023` `risk_tier=Tier 1 Near-Miss`
- Returns: `security=-170.6000` `business=-27.7925` `cost=-20.0900`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=None` `first_relevant_blue_response=6`

Key sequence:
- step 0: Blue `Monitor` -> `-`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 1: Blue `Monitor` -> `-`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 2: Blue `Monitor` -> `-`; Red `ExploitRemoteService` -> `-`; new=User1; recovered=-; critical_after=-
- step 4: Blue `Monitor` -> `-`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `Remove` -> `User3`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-
- step 6: Blue `Restore` -> `Enterprise1`; Red `PrivilegeEscalate` -> `Enterprise1`; new=-; recovered=Enterprise1; critical_after=-
- step 7: Blue `Monitor` -> `-`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-
- step 99: Blue `Monitor` -> `-`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-

Conclusion:
- 没有发生 critical breach，但红方已经沿关键路径形成显著推进。
- 红方的关键推进节点是首先在 `Enterprise1` 建立 foothold。

## Worst Security Return

- Basic info: `episode_id=episode_000` `env_idx=0` `env_seed=19` `risk_tier=Tier 1 Near-Miss`
- Returns: `security=-170.6000` `business=-27.7750` `cost=-19.8600`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=None` `first_relevant_blue_response=6`

Key sequence:
- step 0: Blue `Monitor` -> `-`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 1: Blue `Monitor` -> `-`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 2: Blue `Monitor` -> `-`; Red `ExploitRemoteService` -> `-`; new=User2; recovered=-; critical_after=-
- step 4: Blue `Monitor` -> `-`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `Monitor` -> `-`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-
- step 6: Blue `Restore` -> `Enterprise1`; Red `PrivilegeEscalate` -> `Enterprise1`; new=-; recovered=Enterprise1; critical_after=-
- step 7: Blue `Monitor` -> `-`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-
- step 99: Blue `Monitor` -> `-`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-

Conclusion:
- 没有发生 critical breach，但红方已经沿关键路径形成显著推进。
- 红方的关键推进节点是首先在 `Enterprise1` 建立 foothold。

## Max Critical Dwell

- Basic info: `episode_id=episode_001` `env_idx=0` `env_seed=20` `risk_tier=Tier 1 Near-Miss`
- Returns: `security=-170.6000` `business=-27.7750` `cost=-19.8600`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=None` `first_relevant_blue_response=6`

Key sequence:
- step 0: Blue `Monitor` -> `-`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 1: Blue `Monitor` -> `-`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 2: Blue `Monitor` -> `-`; Red `ExploitRemoteService` -> `-`; new=User2; recovered=-; critical_after=-
- step 4: Blue `Monitor` -> `-`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `Monitor` -> `-`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-
- step 6: Blue `Restore` -> `Enterprise1`; Red `PrivilegeEscalate` -> `Enterprise1`; new=-; recovered=Enterprise1; critical_after=-
- step 7: Blue `Monitor` -> `-`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-
- step 99: Blue `Monitor` -> `-`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-

Conclusion:
- 没有发生 critical breach，但红方已经沿关键路径形成显著推进。
- 红方的关键推进节点是首先在 `Enterprise1` 建立 foothold。

## Best Tier 0 Safe Sample

No matching env-run was available for this case.

## Critical-Step Action Summary

### Critical-step top action families

- No critical-present steps were observed.

### Critical-step recovery counts

- No recovery steps were observed while `critical_present=1`.

### Critical-step no-recovery top actions

- All critical-present steps included a recovery event.

## Pre-critical containment summary

### Pre-critical top action families

- `restore`: `3760` pre-critical steps

### Pre-critical compromised-target recovery counts

- `Restore -> Enterprise0`: `1927` containment steps
- `Restore -> Enterprise1`: `1833` containment steps

### Pre-critical no-containment top actions

- All pre-critical steps focused on compromised Enterprise/Operational targets.
