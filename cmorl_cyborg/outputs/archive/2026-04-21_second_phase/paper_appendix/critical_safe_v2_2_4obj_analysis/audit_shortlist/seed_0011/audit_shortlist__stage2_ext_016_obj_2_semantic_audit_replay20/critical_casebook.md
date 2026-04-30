# Critical Casebook

## Earliest Critical Breach

- Basic info: `episode_id=episode_000` `env_idx=0` `env_seed=11` `risk_tier=Tier 2 Transient Critical Breach`
- Returns: `security=-243.1000` `business=-58.1975` `cost=-24.0400`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=12` `first_relevant_blue_response=6`

Key sequence:
- step 0: Blue `Analyse` -> `User1`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 4: Blue `DecoyTomcat` -> `User1`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `Analyse` -> `User1`; Red `ExploitRemoteService` -> `-`; new=Enterprise0; recovered=-; critical_after=-
- step 6: Blue `DecoyVsftpd` -> `Op_Server0`; Red `PrivilegeEscalate` -> `Enterprise0`; new=-; recovered=-; critical_after=-
- step 7: Blue `Restore` -> `Enterprise2`; Red `DiscoverRemoteSystems` -> `Enterprise`; new=-; recovered=-; critical_after=-
- step 11: Blue `DecoyVsftpd` -> `Op_Server0`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 12: Blue `Restore` -> `Enterprise0`; Red `ExploitRemoteService` -> `-`; new=Op_Server0; recovered=Enterprise0; critical_after=Op_Server0
- step 13: Blue `Restore` -> `Op_Server0`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=Op_Server0; critical_after=-
- step 99: Blue `DecoyApache` -> `Op_Server0`; Red `ExploitRemoteService` -> `-`; new=-; recovered=-; critical_after=-

Conclusion:
- 曾经发生 critical breach，但最终没有维持到结束，属于短暂打穿后部分恢复。
- 红方的关键推进节点是首先在 `Enterprise0` 建立 foothold。
- critical hit 后蓝方首次 relevant response 的延迟为 `1` step。

## Worst Business Return

- Basic info: `episode_id=episode_000` `env_idx=2` `env_seed=2011` `risk_tier=Tier 2 Transient Critical Breach`
- Returns: `security=-583.1500` `business=-143.2325` `cost=-32.2500`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=30` `first_relevant_blue_response=6`

Key sequence:
- step 0: Blue `DecoyTomcat` -> `User1`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 4: Blue `Analyse` -> `User1`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `Analyse` -> `User1`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-
- step 6: Blue `Restore` -> `Enterprise2`; Red `PrivilegeEscalate` -> `Enterprise1`; new=-; recovered=-; critical_after=-
- step 7: Blue `Remove` -> `Op_Host2`; Red `DiscoverRemoteSystems` -> `Enterprise`; new=-; recovered=-; critical_after=-
- step 29: Blue `DecoySmss` -> `Enterprise0`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 30: Blue `Restore` -> `Enterprise2`; Red `ExploitRemoteService` -> `-`; new=Op_Server0; recovered=Enterprise2; critical_after=Op_Server0
- step 31: Blue `Restore` -> `Op_Server0`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=Op_Server0; critical_after=-
- step 99: Blue `Restore` -> `Op_Server0`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=Op_Server0; critical_after=-

Conclusion:
- 曾经发生 critical breach，但最终没有维持到结束，属于短暂打穿后部分恢复。
- 红方的关键推进节点是首先在 `Enterprise1` 建立 foothold。
- critical hit 后蓝方首次 relevant response 的延迟为 `1` step。

## Worst Security Return

- Basic info: `episode_id=episode_001` `env_idx=6` `env_seed=6012` `risk_tier=Tier 2 Transient Critical Breach`
- Returns: `security=-567.1000` `business=-139.2275` `cost=-32.6300`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=28` `first_relevant_blue_response=6`

Key sequence:
- step 0: Blue `Analyse` -> `User1`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 4: Blue `Analyse` -> `User1`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `Analyse` -> `User1`; Red `ExploitRemoteService` -> `-`; new=Enterprise0; recovered=-; critical_after=-
- step 6: Blue `DecoyVsftpd` -> `Op_Server0`; Red `PrivilegeEscalate` -> `Enterprise0`; new=-; recovered=-; critical_after=-
- step 7: Blue `Restore` -> `Enterprise2`; Red `DiscoverRemoteSystems` -> `Enterprise`; new=-; recovered=-; critical_after=-
- step 27: Blue `Restore` -> `Enterprise2`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=Enterprise2; critical_after=-
- step 28: Blue `DecoyVsftpd` -> `Op_Server0`; Red `ExploitRemoteService` -> `-`; new=Op_Server0; recovered=-; critical_after=Op_Server0
- step 29: Blue `Restore` -> `Op_Server0`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=Op_Server0; critical_after=-
- step 99: Blue `Restore` -> `Enterprise2`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=Enterprise2; critical_after=-

Conclusion:
- 曾经发生 critical breach，但最终没有维持到结束，属于短暂打穿后部分恢复。
- 红方的关键推进节点是首先在 `Enterprise0` 建立 foothold。
- critical hit 后蓝方首次 relevant response 的延迟为 `1` step。

## Max Critical Dwell

- Basic info: `episode_id=episode_009` `env_idx=3` `env_seed=3020` `risk_tier=Tier 2 Transient Critical Breach`
- Returns: `security=-468.9000` `business=-110.1075` `cost=-30.0900`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=46` `first_relevant_blue_response=7`

Key sequence:
- step 0: Blue `Analyse` -> `User1`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 4: Blue `Analyse` -> `User3`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `Analyse` -> `User1`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-
- step 6: Blue `DecoyHarakaSMPT` -> `Op_Host2`; Red `PrivilegeEscalate` -> `Enterprise1`; new=-; recovered=-; critical_after=-
- step 7: Blue `Restore` -> `Enterprise2`; Red `DiscoverRemoteSystems` -> `Enterprise`; new=-; recovered=-; critical_after=-
- step 8: Blue `DecoyApache` -> `Op_Server0`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 45: Blue `Restore` -> `Enterprise2`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=Enterprise2; critical_after=-
- step 46: Blue `DecoySmss` -> `Enterprise0`; Red `ExploitRemoteService` -> `-`; new=Op_Server0; recovered=-; critical_after=Op_Server0
- step 47: Blue `Restore` -> `Op_Server0`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=Op_Server0; critical_after=-
- step 99: Blue `DecoyTomcat` -> `Op_Host0`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-

Conclusion:
- 曾经发生 critical breach，但最终没有维持到结束，属于短暂打穿后部分恢复。
- 红方的关键推进节点是首先在 `Enterprise1` 建立 foothold。
- critical hit 后蓝方首次 relevant response 的延迟为 `1` step。

## Best Tier 0 Safe Sample

No matching env-run was available for this case.

## Critical-Step Action Summary

### Critical-step top action families

- `decoy`: `112` critical-present steps
- `restore`: `104` critical-present steps
- `remove`: `2` critical-present steps
- `analyse`: `1` critical-present steps

### Critical-step recovery counts

- `Restore -> Enterprise2`: `14` recovery steps
- `Restore -> Enterprise0`: `3` recovery steps
- `Restore -> Enterprise1`: `1` recovery steps

### Critical-step no-recovery top actions

- `Restore -> Enterprise2`: `72` no-recovery steps
- `DecoyVsftpd -> Op_Server0`: `34` no-recovery steps
- `DecoyApache -> Op_Server0`: `27` no-recovery steps
- `DecoySmss -> Enterprise0`: `22` no-recovery steps
- `DecoyTomcat -> Op_Host0`: `10` no-recovery steps
