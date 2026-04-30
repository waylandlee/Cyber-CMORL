# Critical Casebook

## Earliest Critical Breach

No matching env-run was available for this case.

## Worst Business Return

- Basic info: `episode_id=episode_016` `env_idx=4` `env_seed=4023` `risk_tier=Tier 1 Near-Miss`
- Returns: `security=-171.6000` `business=-30.0975` `cost=-25.5800`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=None` `first_relevant_blue_response=6`

Key sequence:
- step 0: Blue `DecoyHarakaSMPT` -> `Enterprise1`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 1: Blue `Sleep` -> `-`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 2: Blue `DecoyApache` -> `Enterprise0`; Red `ExploitRemoteService` -> `-`; new=User1; recovered=-; critical_after=-
- step 4: Blue `Sleep` -> `-`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `Remove` -> `User3`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-
- step 6: Blue `Restore` -> `Enterprise1`; Red `PrivilegeEscalate` -> `Enterprise1`; new=-; recovered=Enterprise1; critical_after=-
- step 7: Blue `DecoySmss` -> `User1`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-
- step 99: Blue `DecoySSHD` -> `User4`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-

Conclusion:
- 没有发生 critical breach，但红方已经沿关键路径形成显著推进。
- 红方的关键推进节点是首先在 `Enterprise1` 建立 foothold。

## Worst Security Return

- Basic info: `episode_id=episode_010` `env_idx=5` `env_seed=5017` `risk_tier=Tier 1 Near-Miss`
- Returns: `security=-179.6000` `business=-29.4075` `cost=-26.8800`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=None` `first_relevant_blue_response=6`

Key sequence:
- step 0: Blue `Restore` -> `User4`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 1: Blue `DecoySSHD` -> `User4`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 2: Blue `Analyse` -> `Enterprise2`; Red `ExploitRemoteService` -> `-`; new=User3; recovered=-; critical_after=-
- step 4: Blue `Analyse` -> `User1`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `Sleep` -> `-`; Red `ExploitRemoteService` -> `-`; new=Enterprise0; recovered=-; critical_after=-
- step 6: Blue `Restore` -> `Enterprise0`; Red `PrivilegeEscalate` -> `Enterprise0`; new=-; recovered=Enterprise0; critical_after=-
- step 7: Blue `Restore` -> `Defender`; Red `ExploitRemoteService` -> `-`; new=Enterprise0; recovered=-; critical_after=-
- step 99: Blue `Analyse` -> `Enterprise2`; Red `ExploitRemoteService` -> `-`; new=Enterprise0; recovered=-; critical_after=-

Conclusion:
- 没有发生 critical breach，但红方已经沿关键路径形成显著推进。
- 红方的关键推进节点是首先在 `Enterprise0` 建立 foothold。

## Max Critical Dwell

- Basic info: `episode_id=episode_000` `env_idx=0` `env_seed=7` `risk_tier=Tier 1 Near-Miss`
- Returns: `security=-101.5000` `business=-14.2875` `cost=-13.9400`
- Key times: `enterprise_foothold_step=21` `first_critical_hit_step=None` `first_relevant_blue_response=22`

Key sequence:
- step 0: Blue `DecoyApache` -> `Enterprise0`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 1: Blue `DecoyApache` -> `Enterprise0`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 2: Blue `Sleep` -> `-`; Red `ExploitRemoteService` -> `-`; new=User3; recovered=-; critical_after=-
- step 20: Blue `Remove` -> `User2`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 21: Blue `Sleep` -> `-`; Red `ExploitRemoteService` -> `-`; new=Enterprise0; recovered=-; critical_after=-
- step 22: Blue `Restore` -> `Enterprise0`; Red `PrivilegeEscalate` -> `Enterprise0`; new=-; recovered=Enterprise0; critical_after=-
- step 23: Blue `Analyse` -> `Enterprise1`; Red `ExploitRemoteService` -> `-`; new=Enterprise0; recovered=-; critical_after=-
- step 99: Blue `Sleep` -> `-`; Red `ExploitRemoteService` -> `-`; new=-; recovered=-; critical_after=-

Conclusion:
- 没有发生 critical breach，但红方已经沿关键路径形成显著推进。
- 红方的关键推进节点是首先在 `Enterprise0` 建立 foothold。
- 蓝方最可疑的动作规则是：`Q4_user_focus_after_enterprise_foothold`，以及 `Q4_user_focus_after_enterprise_foothold`。

## Best Tier 0 Safe Sample

- Basic info: `episode_id=episode_006` `env_idx=0` `env_seed=13` `risk_tier=Tier 0 Safe`
- Returns: `security=-97.0000` `business=-13.6150` `cost=-14.7800`
- Key times: `enterprise_foothold_step=None` `first_critical_hit_step=None` `first_relevant_blue_response=None`

Key sequence:
- step 0: Blue `DecoyApache` -> `Enterprise0`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 1: Blue `DecoySSHD` -> `Op_Host1`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 2: Blue `DecoyApache` -> `Enterprise0`; Red `ExploitRemoteService` -> `-`; new=User3; recovered=-; critical_after=-
- step 3: Blue `DecoyApache` -> `Enterprise0`; Red `PrivilegeEscalate` -> `User3`; new=-; recovered=-; critical_after=-
- step 4: Blue `Analyse` -> `User1`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `DecoyApache` -> `Enterprise0`; Red `ExploitRemoteService` -> `-`; new=-; recovered=-; critical_after=-
- step 6: Blue `Sleep` -> `-`; Red `ExploitRemoteService` -> `-`; new=-; recovered=-; critical_after=-
- step 99: Blue `DecoySmss` -> `Enterprise1`; Red `PrivilegeEscalate` -> `User3`; new=-; recovered=-; critical_after=-

Conclusion:
- 没有发生 critical breach，但红方已经沿关键路径形成显著推进。

## Critical-Step Action Summary

### Critical-step top action families

- No critical-present steps were observed.

### Critical-step recovery counts

- No recovery steps were observed while `critical_present=1`.

### Critical-step no-recovery top actions

- All critical-present steps included a recovery event.

## Pre-critical containment summary

### Pre-critical top action families

- `restore`: `5950` pre-critical steps

### Pre-critical compromised-target recovery counts

- `Restore -> Enterprise1`: `3807` containment steps
- `Restore -> Enterprise0`: `2143` containment steps

### Pre-critical no-containment top actions

- All pre-critical steps focused on compromised Enterprise/Operational targets.
