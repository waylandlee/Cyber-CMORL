# Critical Casebook

## Earliest Critical Breach

- Basic info: `episode_id=episode_000` `env_idx=0` `env_seed=11` `risk_tier=Tier 3 Persistent Critical Breach`
- Returns: `security=-460.7000` `business=-123.4450` `cost=-28.9900`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=12` `first_relevant_blue_response=7`

Key sequence:
- step 0: Blue `DecoyVsftpd` -> `Op_Host0`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 4: Blue `DecoyVsftpd` -> `Op_Host0`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `Restore` -> `Enterprise2`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-
- step 6: Blue `DecoyVsftpd` -> `Op_Host0`; Red `PrivilegeEscalate` -> `Enterprise1`; new=-; recovered=-; critical_after=-
- step 7: Blue `Restore` -> `Enterprise2`; Red `DiscoverRemoteSystems` -> `Enterprise`; new=-; recovered=-; critical_after=-
- step 8: Blue `Restore` -> `Enterprise2`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 11: Blue `DecoyVsftpd` -> `Op_Server0`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 12: Blue `Restore` -> `Enterprise0`; Red `ExploitRemoteService` -> `-`; new=Op_Server0; recovered=-; critical_after=Op_Server0
- step 13: Blue `Restore` -> `Enterprise2`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=Enterprise2; critical_after=Op_Server0
- step 14: Blue `DecoySmss` -> `Enterprise0`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 15: Blue `Restore` -> `Op_Server0`; Red `Impact` -> `Op_Server0`; new=-; recovered=Op_Server0; critical_after=-
- step 99: Blue `Restore` -> `Enterprise1`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0

Conclusion:
- 最终 `Op_Server0` 仍处于 critical compromised 状态，说明该 env-run 属于持久打穿而不是短暂失守。
- 红方真正完成突破的关键节点是 step 14 对 `Op_Server0` 的 `Impact`。
- critical hit 后蓝方首次 relevant response 的延迟为 `1` step。
- 蓝方最可疑的动作规则是：`Q2_user_action_during_critical_breach`，以及 `Q2_user_action_during_critical_breach`。

## Worst Business Return

- Basic info: `episode_id=episode_015` `env_idx=5` `env_seed=5026` `risk_tier=Tier 3 Persistent Critical Breach`
- Returns: `security=-538.8000` `business=-138.2575` `cost=-32.1400`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=12` `first_relevant_blue_response=7`

Key sequence:
- step 0: Blue `Restore` -> `Enterprise2`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 4: Blue `Remove` -> `User2`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `Remove` -> `Enterprise2`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-
- step 6: Blue `DecoyHarakaSMPT` -> `User2`; Red `PrivilegeEscalate` -> `Enterprise1`; new=-; recovered=-; critical_after=-
- step 7: Blue `Restore` -> `Enterprise2`; Red `DiscoverRemoteSystems` -> `Enterprise`; new=-; recovered=-; critical_after=-
- step 8: Blue `Restore` -> `Enterprise2`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 11: Blue `Restore` -> `Enterprise2`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=Enterprise2; critical_after=-
- step 12: Blue `Restore` -> `Enterprise2`; Red `ExploitRemoteService` -> `-`; new=Op_Server0; recovered=-; critical_after=Op_Server0
- step 13: Blue `DecoyVsftpd` -> `Op_Host0`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 14: Blue `DecoyVsftpd` -> `Op_Host0`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 15: Blue `Restore` -> `Op_Server0`; Red `Impact` -> `Op_Server0`; new=-; recovered=Op_Server0; critical_after=-
- step 99: Blue `Restore` -> `Enterprise2`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0

Conclusion:
- 最终 `Op_Server0` 仍处于 critical compromised 状态，说明该 env-run 属于持久打穿而不是短暂失守。
- 红方真正完成突破的关键节点是 step 14 对 `Op_Server0` 的 `Impact`。
- critical hit 后蓝方首次 relevant response 的延迟为 `3` step。
- 蓝方最可疑的动作规则是：`Q2_user_action_during_critical_breach`，以及 `Q2_user_action_during_critical_breach`。

## Worst Security Return

- Basic info: `episode_id=episode_012` `env_idx=3` `env_seed=3023` `risk_tier=Tier 2 Transient Critical Breach`
- Returns: `security=-828.1000` `business=-94.6750` `cost=-28.3500`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=12` `first_relevant_blue_response=7`

Key sequence:
- step 0: Blue `Restore` -> `Enterprise1`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 4: Blue `Restore` -> `Enterprise2`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `Restore` -> `Enterprise2`; Red `ExploitRemoteService` -> `-`; new=Enterprise0; recovered=-; critical_after=-
- step 6: Blue `DecoySmss` -> `User4`; Red `PrivilegeEscalate` -> `Enterprise0`; new=-; recovered=-; critical_after=-
- step 7: Blue `Restore` -> `Enterprise2`; Red `DiscoverRemoteSystems` -> `Enterprise`; new=-; recovered=-; critical_after=-
- step 8: Blue `DecoyFemitter` -> `Enterprise1`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 11: Blue `Restore` -> `Enterprise2`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=Enterprise2; critical_after=-
- step 12: Blue `Analyse` -> `Enterprise2`; Red `ExploitRemoteService` -> `-`; new=Op_Server0; recovered=-; critical_after=Op_Server0
- step 13: Blue `DecoySSHD` -> `User2`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 14: Blue `DecoySmss` -> `Enterprise0`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 15: Blue `DecoySSHD` -> `User1`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 99: Blue `DecoyTomcat` -> `User2`; Red `ExploitRemoteService` -> `-`; new=Enterprise2; recovered=-; critical_after=-

Conclusion:
- 曾经发生 critical breach，但最终没有维持到结束，属于短暂打穿后部分恢复。
- 红方真正完成突破的关键节点是 step 14 对 `Op_Server0` 的 `Impact`。
- critical hit 后蓝方首次 relevant response 的延迟为 `2` step。
- 蓝方最可疑的动作规则是：`Q2_user_action_during_critical_breach`，以及 `Q2_user_action_during_critical_breach`。

## Max Critical Dwell

- Basic info: `episode_id=episode_002` `env_idx=3` `env_seed=3013` `risk_tier=Tier 3 Persistent Critical Breach`
- Returns: `security=-453.7500` `business=-128.9350` `cost=-27.3000`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=16` `first_relevant_blue_response=6`

Key sequence:
- step 0: Blue `Restore` -> `Enterprise2`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 4: Blue `Restore` -> `Enterprise2`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `Restore` -> `Op_Server0`; Red `ExploitRemoteService` -> `-`; new=Enterprise0; recovered=-; critical_after=-
- step 6: Blue `Restore` -> `Enterprise2`; Red `PrivilegeEscalate` -> `Enterprise0`; new=-; recovered=-; critical_after=-
- step 7: Blue `DecoyVsftpd` -> `Op_Host0`; Red `DiscoverRemoteSystems` -> `Enterprise`; new=-; recovered=-; critical_after=-
- step 15: Blue `DecoyHarakaSMPT` -> `Enterprise1`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 16: Blue `Restore` -> `Enterprise2`; Red `ExploitRemoteService` -> `-`; new=Op_Server0; recovered=Enterprise2; critical_after=Op_Server0
- step 17: Blue `Restore` -> `Enterprise2`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 18: Blue `DecoySmss` -> `User2`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 19: Blue `Restore` -> `Enterprise2`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 99: Blue `DecoySmss` -> `Op_Host1`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0

Conclusion:
- 最终 `Op_Server0` 仍处于 critical compromised 状态，说明该 env-run 属于持久打穿而不是短暂失守。
- 红方真正完成突破的关键节点是 step 18 对 `Op_Server0` 的 `Impact`。
- critical hit 后蓝方首次 relevant response 的延迟为 `1` step。
- 蓝方最可疑的动作规则是：`Q2_user_action_during_critical_breach`，以及 `Q2_user_action_during_critical_breach`。

## Best Tier 0 Safe Sample

No matching env-run was available for this case.

## Critical-Step Action Summary

### Critical-step top action families

- `decoy`: `4850` critical-present steps
- `restore`: `3217` critical-present steps
- `remove`: `563` critical-present steps
- `analyse`: `414` critical-present steps
- `other`: `64` critical-present steps

### Critical-step recovery counts

- `Restore -> Enterprise2`: `399` recovery steps
- `Restore -> Enterprise1`: `55` recovery steps
- `Restore -> Enterprise0`: `54` recovery steps
- `Restore -> User1`: `5` recovery steps
- `Restore -> User4`: `4` recovery steps

### Critical-step no-recovery top actions

- `Restore -> Enterprise2`: `1727` no-recovery steps
- `DecoyVsftpd -> Op_Host0`: `1286` no-recovery steps
- `DecoyHarakaSMPT -> User2`: `416` no-recovery steps
- `Restore -> Enterprise0`: `342` no-recovery steps
- `DecoyFemitter -> Enterprise0`: `278` no-recovery steps

## Pre-critical containment summary

### Pre-critical top action families

- `restore`: `1809` pre-critical steps
- `decoy`: `1569` pre-critical steps
- `remove`: `183` pre-critical steps
- `analyse`: `138` pre-critical steps
- `other`: `26` pre-critical steps

### Pre-critical compromised-target recovery counts

- `Restore -> Enterprise2`: `685` containment steps
- `Restore -> Op_Server0`: `317` containment steps
- `Restore -> Enterprise0`: `33` containment steps
- `Restore -> Enterprise1`: `25` containment steps
- `Analyse -> Enterprise2`: `25` containment steps

### Pre-critical no-containment top actions

- `DecoyVsftpd -> Op_Host0`: `422` no-containment steps
- `Restore -> Op_Server0`: `230` no-containment steps
- `Restore -> Enterprise2`: `214` no-containment steps
- `DecoyHarakaSMPT -> User2`: `138` no-containment steps
- `Restore -> Enterprise0`: `111` no-containment steps
