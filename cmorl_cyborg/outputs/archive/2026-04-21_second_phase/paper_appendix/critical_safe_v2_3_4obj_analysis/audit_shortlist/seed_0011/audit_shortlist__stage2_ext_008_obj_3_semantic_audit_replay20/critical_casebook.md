# Critical Casebook

## Earliest Critical Breach

- Basic info: `episode_id=episode_001` `env_idx=1` `env_seed=1012` `risk_tier=Tier 2 Transient Critical Breach`
- Returns: `security=-324.4500` `business=-77.3925` `cost=-20.6700`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=12` `first_relevant_blue_response=6`

Key sequence:
- step 0: Blue `DecoySSHD` -> `Op_Host2`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 4: Blue `Remove` -> `User0`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `DecoyHarakaSMPT` -> `Enterprise2`; Red `ExploitRemoteService` -> `-`; new=Enterprise0; recovered=-; critical_after=-
- step 6: Blue `DecoyVsftpd` -> `Op_Server0`; Red `PrivilegeEscalate` -> `Enterprise0`; new=-; recovered=-; critical_after=-
- step 7: Blue `DecoyHarakaSMPT` -> `Enterprise0`; Red `DiscoverRemoteSystems` -> `Enterprise`; new=-; recovered=-; critical_after=-
- step 11: Blue `Restore` -> `Enterprise2`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=Enterprise2; critical_after=-
- step 12: Blue `DecoyTomcat` -> `Op_Server0`; Red `ExploitRemoteService` -> `-`; new=Op_Server0; recovered=-; critical_after=Op_Server0
- step 13: Blue `Restore` -> `Op_Server0`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=Op_Server0; critical_after=-
- step 99: Blue `DecoyVsftpd` -> `Enterprise2`; Red `ExploitRemoteService` -> `-`; new=-; recovered=-; critical_after=-

Conclusion:
- 曾经发生 critical breach，但最终没有维持到结束，属于短暂打穿后部分恢复。
- 红方的关键推进节点是首先在 `Enterprise0` 建立 foothold。
- critical hit 后蓝方首次 relevant response 的延迟为 `1` step。

## Worst Business Return

- Basic info: `episode_id=episode_008` `env_idx=4` `env_seed=4019` `risk_tier=Tier 2 Transient Critical Breach`
- Returns: `security=-710.2500` `business=-190.4350` `cost=-27.8100`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=12` `first_relevant_blue_response=9`

Key sequence:
- step 0: Blue `DecoyFemitter` -> `User4`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 4: Blue `Analyse` -> `Enterprise0`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `Remove` -> `User3`; Red `ExploitRemoteService` -> `-`; new=Enterprise0; recovered=-; critical_after=-
- step 6: Blue `DecoySSHD` -> `Defender`; Red `PrivilegeEscalate` -> `Enterprise0`; new=-; recovered=-; critical_after=-
- step 8: Blue `DecoySSHD` -> `Defender`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 9: Blue `Analyse` -> `Enterprise0`; Red `ExploitRemoteService` -> `-`; new=Enterprise2; recovered=-; critical_after=-
- step 10: Blue `DecoyFemitter` -> `Enterprise2`; Red `PrivilegeEscalate` -> `Enterprise2`; new=-; recovered=-; critical_after=-
- step 11: Blue `Analyse` -> `Op_Host2`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 12: Blue `DecoyTomcat` -> `Op_Server0`; Red `ExploitRemoteService` -> `-`; new=Op_Server0; recovered=-; critical_after=Op_Server0
- step 13: Blue `Restore` -> `Op_Server0`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=Op_Server0; critical_after=-
- step 99: Blue `Restore` -> `Op_Server0`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=Op_Server0; critical_after=-

Conclusion:
- 曾经发生 critical breach，但最终没有维持到结束，属于短暂打穿后部分恢复。
- 红方的关键推进节点是首先在 `Enterprise0` 建立 foothold。
- critical hit 后蓝方首次 relevant response 的延迟为 `1` step。

## Worst Security Return

- Basic info: `episode_id=episode_002` `env_idx=3` `env_seed=3013` `risk_tier=Tier 2 Transient Critical Breach`
- Returns: `security=-607.8500` `business=-153.4275` `cost=-26.0700`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=36` `first_relevant_blue_response=6`

Key sequence:
- step 0: Blue `DecoyTomcat` -> `Op_Server0`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 4: Blue `Remove` -> `User2`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `Restore` -> `User4`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-
- step 6: Blue `DecoyApache` -> `Enterprise1`; Red `PrivilegeEscalate` -> `Enterprise1`; new=-; recovered=-; critical_after=-
- step 7: Blue `DecoySmss` -> `Op_Host2`; Red `DiscoverRemoteSystems` -> `Enterprise`; new=-; recovered=-; critical_after=-
- step 35: Blue `Restore` -> `Enterprise2`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=Enterprise2; critical_after=-
- step 36: Blue `DecoyTomcat` -> `Op_Server0`; Red `ExploitRemoteService` -> `-`; new=Op_Server0; recovered=-; critical_after=Op_Server0
- step 37: Blue `Restore` -> `Op_Server0`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=Op_Server0; critical_after=-
- step 99: Blue `Restore` -> `Op_Server0`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=Op_Server0; critical_after=-

Conclusion:
- 曾经发生 critical breach，但最终没有维持到结束，属于短暂打穿后部分恢复。
- 红方的关键推进节点是首先在 `Enterprise1` 建立 foothold。
- critical hit 后蓝方首次 relevant response 的延迟为 `1` step。

## Max Critical Dwell

- Basic info: `episode_id=episode_002` `env_idx=0` `env_seed=13` `risk_tier=Tier 2 Transient Critical Breach`
- Returns: `security=-573.1500` `business=-157.0075` `cost=-27.1100`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=28` `first_relevant_blue_response=6`

Key sequence:
- step 0: Blue `DecoyFemitter` -> `User4`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 4: Blue `Restore` -> `Enterprise2`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `DecoyTomcat` -> `Enterprise1`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-
- step 6: Blue `DecoyVsftpd` -> `Op_Server0`; Red `PrivilegeEscalate` -> `Enterprise1`; new=-; recovered=-; critical_after=-
- step 7: Blue `DecoyTomcat` -> `Op_Server0`; Red `DiscoverRemoteSystems` -> `Enterprise`; new=-; recovered=-; critical_after=-
- step 27: Blue `DecoySSHD` -> `Defender`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 28: Blue `DecoyTomcat` -> `Op_Server0`; Red `ExploitRemoteService` -> `-`; new=Op_Server0; recovered=-; critical_after=Op_Server0
- step 29: Blue `Restore` -> `Op_Server0`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=Op_Server0; critical_after=-
- step 99: Blue `Restore` -> `Op_Server0`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=Op_Server0; critical_after=-

Conclusion:
- 曾经发生 critical breach，但最终没有维持到结束，属于短暂打穿后部分恢复。
- 红方的关键推进节点是首先在 `Enterprise1` 建立 foothold。
- critical hit 后蓝方首次 relevant response 的延迟为 `1` step。

## Best Tier 0 Safe Sample

No matching env-run was available for this case.

## Critical-Step Action Summary

### Critical-step top action families

- `decoy`: `353` critical-present steps
- `analyse`: `34` critical-present steps
- `remove`: `30` critical-present steps
- `restore`: `25` critical-present steps

### Critical-step recovery counts

- `Restore -> Enterprise2`: `4` recovery steps
- `Restore -> Enterprise1`: `3` recovery steps
- `Restore -> Enterprise0`: `1` recovery steps

### Critical-step no-recovery top actions

- `DecoyApache -> Op_Server0`: `99` no-recovery steps
- `DecoyTomcat -> Op_Server0`: `66` no-recovery steps
- `DecoyVsftpd -> Op_Server0`: `38` no-recovery steps
- `Analyse -> Enterprise0`: `28` no-recovery steps
- `DecoySSHD -> Defender`: `25` no-recovery steps
