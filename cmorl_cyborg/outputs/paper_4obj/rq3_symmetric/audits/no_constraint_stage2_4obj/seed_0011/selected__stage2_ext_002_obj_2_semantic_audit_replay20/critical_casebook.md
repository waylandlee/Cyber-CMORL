# Critical Casebook

## Earliest Critical Breach

No matching env-run was available for this case.

## Worst Business Return

- Basic info: `episode_id=episode_018` `env_idx=7` `env_seed=7029` `risk_tier=Tier 1 Near-Miss`
- Returns: `security=-170.6000` `business=-30.0575` `cost=-29.0400`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=None` `first_relevant_blue_response=6`

Key sequence:
- step 0: Blue `DecoyApache` -> `Enterprise0`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 1: Blue `DecoyTomcat` -> `User4`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 2: Blue `DecoyTomcat` -> `User4`; Red `ExploitRemoteService` -> `-`; new=User2; recovered=-; critical_after=-
- step 4: Blue `Analyse` -> `Op_Host1`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `DecoyApache` -> `Enterprise0`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-
- step 6: Blue `Restore` -> `Enterprise1`; Red `PrivilegeEscalate` -> `Enterprise1`; new=-; recovered=Enterprise1; critical_after=-
- step 7: Blue `DecoyFemitter` -> `Enterprise1`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-
- step 99: Blue `DecoyApache` -> `Enterprise0`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-

Conclusion:
- 没有发生 critical breach，但红方已经沿关键路径形成显著推进。
- 红方的关键推进节点是首先在 `Enterprise1` 建立 foothold。
- 蓝方最可疑的动作规则是：`Q5_repeated_low_value_decoy_loop`。

## Worst Security Return

- Basic info: `episode_id=episode_015` `env_idx=4` `env_seed=4026` `risk_tier=Tier 1 Near-Miss`
- Returns: `security=-174.6000` `business=-29.5175` `cost=-29.4800`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=None` `first_relevant_blue_response=6`

Key sequence:
- step 0: Blue `DecoyHarakaSMPT` -> `Enterprise0`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 1: Blue `DecoyTomcat` -> `User4`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 2: Blue `Analyse` -> `Enterprise2`; Red `ExploitRemoteService` -> `-`; new=User2; recovered=-; critical_after=-
- step 4: Blue `DecoyApache` -> `Enterprise0`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `DecoyHarakaSMPT` -> `Enterprise0`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-
- step 6: Blue `Restore` -> `Enterprise1`; Red `PrivilegeEscalate` -> `Enterprise1`; new=-; recovered=Enterprise1; critical_after=-
- step 7: Blue `Restore` -> `User1`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-
- step 99: Blue `DecoyApache` -> `Enterprise0`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-

Conclusion:
- 没有发生 critical breach，但红方已经沿关键路径形成显著推进。
- 红方的关键推进节点是首先在 `Enterprise1` 建立 foothold。
- 蓝方最可疑的动作规则是：`Q5_repeated_low_value_decoy_loop`，以及 `Q5_repeated_low_value_decoy_loop`。

## Max Critical Dwell

- Basic info: `episode_id=episode_000` `env_idx=0` `env_seed=11` `risk_tier=Tier 1 Near-Miss`
- Returns: `security=-96.1000` `business=-14.3175` `cost=-19.0800`
- Key times: `enterprise_foothold_step=25` `first_critical_hit_step=None` `first_relevant_blue_response=26`

Key sequence:
- step 0: Blue `Analyse` -> `Enterprise2`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 1: Blue `DecoyApache` -> `Enterprise0`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 2: Blue `DecoyTomcat` -> `User4`; Red `ExploitRemoteService` -> `-`; new=User4; recovered=-; critical_after=-
- step 24: Blue `DecoyApache` -> `Enterprise0`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 25: Blue `Analyse` -> `Op_Host1`; Red `ExploitRemoteService` -> `-`; new=Enterprise0; recovered=-; critical_after=-
- step 26: Blue `Restore` -> `Enterprise0`; Red `PrivilegeEscalate` -> `Enterprise0`; new=-; recovered=Enterprise0; critical_after=-
- step 27: Blue `Analyse` -> `Op_Host1`; Red `ExploitRemoteService` -> `-`; new=-; recovered=-; critical_after=-
- step 99: Blue `DecoyHarakaSMPT` -> `Enterprise0`; Red `ExploitRemoteService` -> `-`; new=-; recovered=-; critical_after=-

Conclusion:
- 没有发生 critical breach，但红方已经沿关键路径形成显著推进。
- 红方的关键推进节点是首先在 `Enterprise0` 建立 foothold。
- 蓝方最可疑的动作规则是：`Q5_repeated_low_value_decoy_loop`，以及 `Q4_user_focus_after_enterprise_foothold`。

## Best Tier 0 Safe Sample

- Basic info: `episode_id=episode_019` `env_idx=5` `env_seed=5030` `risk_tier=Tier 0 Safe`
- Returns: `security=-89.0000` `business=-13.7825` `cost=-19.2800`
- Key times: `enterprise_foothold_step=None` `first_critical_hit_step=None` `first_relevant_blue_response=None`

Key sequence:
- step 0: Blue `DecoyHarakaSMPT` -> `Enterprise0`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 1: Blue `DecoyApache` -> `Enterprise0`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 2: Blue `DecoyHarakaSMPT` -> `Enterprise0`; Red `ExploitRemoteService` -> `-`; new=User4; recovered=-; critical_after=-
- step 3: Blue `DecoyHarakaSMPT` -> `User1`; Red `PrivilegeEscalate` -> `User4`; new=-; recovered=-; critical_after=-
- step 4: Blue `DecoyTomcat` -> `User4`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `DecoyHarakaSMPT` -> `Enterprise0`; Red `ExploitRemoteService` -> `-`; new=-; recovered=-; critical_after=-
- step 6: Blue `Analyse` -> `Op_Host1`; Red `ExploitRemoteService` -> `-`; new=-; recovered=-; critical_after=-
- step 99: Blue `DecoyApache` -> `Enterprise0`; Red `PrivilegeEscalate` -> `User4`; new=-; recovered=-; critical_after=-

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

- `restore`: `4614` pre-critical steps

### Pre-critical compromised-target recovery counts

- `Restore -> Enterprise1`: `3916` containment steps
- `Restore -> Enterprise0`: `698` containment steps

### Pre-critical no-containment top actions

- All pre-critical steps focused on compromised Enterprise/Operational targets.
