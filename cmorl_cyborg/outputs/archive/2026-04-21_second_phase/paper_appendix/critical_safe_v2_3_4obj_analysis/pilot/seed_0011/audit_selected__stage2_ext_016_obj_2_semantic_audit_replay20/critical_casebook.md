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

- Basic info: `episode_id=episode_010` `env_idx=7` `env_seed=7021` `risk_tier=Tier 2 Transient Critical Breach`
- Returns: `security=-494.2500` `business=-118.9525` `cost=-31.9600`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=26` `first_relevant_blue_response=6`

Key sequence:
- step 0: Blue `DecoyHarakaSMPT` -> `Defender`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 4: Blue `DecoyVsftpd` -> `User0`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `Restore` -> `Enterprise1`; Red `ExploitRemoteService` -> `-`; new=Enterprise0; recovered=-; critical_after=-
- step 6: Blue `DecoyVsftpd` -> `Op_Server0`; Red `PrivilegeEscalate` -> `Enterprise0`; new=-; recovered=-; critical_after=-
- step 7: Blue `Restore` -> `Enterprise2`; Red `DiscoverRemoteSystems` -> `Enterprise`; new=-; recovered=-; critical_after=-
- step 25: Blue `DecoySmss` -> `Enterprise0`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 26: Blue `DecoyVsftpd` -> `Op_Server0`; Red `ExploitRemoteService` -> `-`; new=Op_Server0; recovered=-; critical_after=Op_Server0
- step 27: Blue `Restore` -> `Op_Server0`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=Op_Server0; critical_after=-
- step 99: Blue `Analyse` -> `User1`; Red `ExploitRemoteService` -> `-`; new=Enterprise2; recovered=-; critical_after=-

Conclusion:
- 曾经发生 critical breach，但最终没有维持到结束，属于短暂打穿后部分恢复。
- 红方的关键推进节点是首先在 `Enterprise0` 建立 foothold。
- critical hit 后蓝方首次 relevant response 的延迟为 `1` step。

## Best Tier 0 Safe Sample

No matching env-run was available for this case.

## Critical-Step Action Summary

### Critical-step top action families

- `decoy`: `168` critical-present steps
- `restore`: `150` critical-present steps
- `remove`: `4` critical-present steps
- `analyse`: `1` critical-present steps

### Critical-step recovery counts

- `Restore -> Enterprise2`: `20` recovery steps
- `Restore -> Enterprise0`: `3` recovery steps
- `Restore -> Enterprise1`: `2` recovery steps

### Critical-step no-recovery top actions

- `Restore -> Enterprise2`: `89` no-recovery steps
- `DecoyVsftpd -> Op_Server0`: `49` no-recovery steps
- `DecoyApache -> Op_Server0`: `43` no-recovery steps
- `DecoySmss -> Enterprise0`: `30` no-recovery steps
- `Restore -> Enterprise1`: `21` no-recovery steps

## Pre-critical containment summary

### Pre-critical top action families

- `restore`: `6064` pre-critical steps
- `decoy`: `6055` pre-critical steps
- `analyse`: `1731` pre-critical steps
- `remove`: `115` pre-critical steps

### Pre-critical compromised-target recovery counts

- `Restore -> Enterprise2`: `3924` containment steps
- `Restore -> Op_Server0`: `323` containment steps
- `Restore -> Enterprise1`: `93` containment steps
- `Restore -> Enterprise0`: `85` containment steps
- `Remove -> Enterprise2`: `10` containment steps

### Pre-critical no-containment top actions

- `DecoyVsftpd -> Op_Server0`: `1575` no-containment steps
- `Analyse -> User1`: `1410` no-containment steps
- `DecoyApache -> Op_Server0`: `1032` no-containment steps
- `DecoySmss -> Enterprise0`: `906` no-containment steps
- `Restore -> Enterprise2`: `683` no-containment steps
