# Critical Casebook

## Earliest Critical Breach

- Basic info: `episode_id=episode_001` `env_idx=0` `env_seed=12` `risk_tier=Tier 2 Transient Critical Breach`
- Returns: `security=-403.9000` `business=-110.2800` `cost=-23.5500`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=12` `first_relevant_blue_response=12`

Key sequence:
- step 0: Blue `DecoySSHD` -> `Enterprise2`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 4: Blue `DecoySmss` -> `Enterprise1`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `Restore` -> `Enterprise2`; Red `ExploitRemoteService` -> `-`; new=Enterprise0; recovered=-; critical_after=-
- step 6: Blue `DecoyFemitter` -> `User2`; Red `PrivilegeEscalate` -> `Enterprise0`; new=-; recovered=-; critical_after=-
- step 11: Blue `DecoySvchost` -> `User3`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 12: Blue `Analyse` -> `Enterprise2`; Red `ExploitRemoteService` -> `-`; new=Op_Server0; recovered=-; critical_after=Op_Server0
- step 13: Blue `Restore` -> `Enterprise0`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=Enterprise0; critical_after=Op_Server0
- step 14: Blue `DecoyApache` -> `Op_Host2`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 15: Blue `DecoySvchost` -> `Defender`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 99: Blue `Restore` -> `Op_Server0`; Red `ExploitRemoteService` -> `-`; new=Enterprise2; recovered=-; critical_after=-

Conclusion:
- 曾经发生 critical breach，但最终没有维持到结束，属于短暂打穿后部分恢复。
- 红方真正完成突破的关键节点是 step 14 对 `Op_Server0` 的 `Impact`。
- critical hit 后蓝方首次 relevant response 的延迟为 `1` step。
- 蓝方最可疑的动作规则是：`Q2_user_action_during_critical_breach`，以及 `Q2_user_action_during_critical_breach`。

## Worst Business Return

- Basic info: `episode_id=episode_013` `env_idx=0` `env_seed=24` `risk_tier=Tier 3 Persistent Critical Breach`
- Returns: `security=-645.0000` `business=-170.1950` `cost=-22.3500`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=14` `first_relevant_blue_response=7`

Key sequence:
- step 0: Blue `Remove` -> `Op_Server0`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 4: Blue `Sleep` -> `-`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `Analyse` -> `Enterprise2`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-
- step 6: Blue `DecoySmss` -> `User4`; Red `PrivilegeEscalate` -> `Enterprise1`; new=-; recovered=-; critical_after=-
- step 7: Blue `DecoySmss` -> `Enterprise0`; Red `DiscoverRemoteSystems` -> `Enterprise`; new=-; recovered=-; critical_after=-
- step 8: Blue `DecoyFemitter` -> `Op_Server0`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 13: Blue `Remove` -> `Enterprise1`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 14: Blue `DecoySmss` -> `Op_Host1`; Red `ExploitRemoteService` -> `-`; new=Op_Server0; recovered=-; critical_after=Op_Server0
- step 15: Blue `DecoyTomcat` -> `User2`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 16: Blue `DecoyVsftpd` -> `User0`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 17: Blue `DecoyVsftpd` -> `Enterprise2`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 99: Blue `DecoyVsftpd` -> `Enterprise1`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0

Conclusion:
- 最终 `Op_Server0` 仍处于 critical compromised 状态，说明该 env-run 属于持久打穿而不是短暂失守。
- 红方真正完成突破的关键节点是 step 16 对 `Op_Server0` 的 `Impact`。
- critical hit 后蓝方首次 relevant response 的延迟为 `3` step。
- 蓝方最可疑的动作规则是：`Q2_user_action_during_critical_breach`，以及 `Q2_user_action_during_critical_breach`。

## Worst Security Return

- Basic info: `episode_id=episode_008` `env_idx=4` `env_seed=4019` `risk_tier=Tier 3 Persistent Critical Breach`
- Returns: `security=-1238.4500` `business=-121.0050` `cost=-23.7500`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=12` `first_relevant_blue_response=6`

Key sequence:
- step 0: Blue `DecoyVsftpd` -> `User4`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 4: Blue `DecoySmss` -> `Enterprise1`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `Remove` -> `User3`; Red `ExploitRemoteService` -> `-`; new=Enterprise0; recovered=-; critical_after=-
- step 6: Blue `Restore` -> `Enterprise2`; Red `PrivilegeEscalate` -> `Enterprise0`; new=-; recovered=-; critical_after=-
- step 7: Blue `Restore` -> `Enterprise2`; Red `DiscoverRemoteSystems` -> `Enterprise`; new=-; recovered=-; critical_after=-
- step 11: Blue `DecoySmss` -> `User0`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 12: Blue `DecoyTomcat` -> `Op_Server0`; Red `ExploitRemoteService` -> `-`; new=Op_Server0; recovered=-; critical_after=Op_Server0
- step 13: Blue `Remove` -> `Op_Host2`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 14: Blue `Remove` -> `Defender`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 15: Blue `DecoyApache` -> `Op_Server0`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 99: Blue `Remove` -> `Op_Host1`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0

Conclusion:
- 最终 `Op_Server0` 仍处于 critical compromised 状态，说明该 env-run 属于持久打穿而不是短暂失守。
- 红方真正完成突破的关键节点是 step 14 对 `Op_Server0` 的 `Impact`。
- critical hit 后蓝方首次 relevant response 的延迟为 `3` step。
- 蓝方最可疑的动作规则是：`Q2_user_action_during_critical_breach`，以及 `Q2_user_action_during_critical_breach`。

## Max Critical Dwell

- Basic info: `episode_id=episode_008` `env_idx=0` `env_seed=19` `risk_tier=Tier 3 Persistent Critical Breach`
- Returns: `security=-384.2500` `business=-122.1050` `cost=-20.9800`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=12` `first_relevant_blue_response=9`

Key sequence:
- step 0: Blue `Remove` -> `Op_Host0`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 4: Blue `DecoyVsftpd` -> `Op_Server0`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `Remove` -> `Op_Host1`; Red `ExploitRemoteService` -> `-`; new=Enterprise0; recovered=-; critical_after=-
- step 6: Blue `DecoySSHD` -> `Op_Host0`; Red `PrivilegeEscalate` -> `Enterprise0`; new=-; recovered=-; critical_after=-
- step 8: Blue `DecoySmss` -> `User4`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 9: Blue `Analyse` -> `Enterprise2`; Red `ExploitRemoteService` -> `-`; new=Enterprise2; recovered=-; critical_after=-
- step 10: Blue `Monitor` -> `-`; Red `PrivilegeEscalate` -> `Enterprise2`; new=-; recovered=-; critical_after=-
- step 11: Blue `Restore` -> `Op_Server0`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 12: Blue `DecoySmss` -> `Op_Host1`; Red `ExploitRemoteService` -> `-`; new=Op_Server0; recovered=-; critical_after=Op_Server0
- step 13: Blue `DecoyVsftpd` -> `Enterprise1`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 14: Blue `DecoyHarakaSMPT` -> `Op_Server0`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 99: Blue `Analyse` -> `Op_Host1`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0

Conclusion:
- 最终 `Op_Server0` 仍处于 critical compromised 状态，说明该 env-run 属于持久打穿而不是短暂失守。
- 红方真正完成突破的关键节点是 step 14 对 `Op_Server0` 的 `Impact`。
- critical hit 后蓝方首次 relevant response 的延迟为 `1` step。
- 蓝方最可疑的动作规则是：`Q2_user_action_during_critical_breach`，以及 `Q2_user_action_during_critical_breach`。

## Best Tier 0 Safe Sample

No matching env-run was available for this case.

## Critical-Step Action Summary

### Critical-step top action families

- `decoy`: `6782` critical-present steps
- `restore`: `1572` critical-present steps
- `remove`: `1238` critical-present steps
- `analyse`: `827` critical-present steps
- `other`: `355` critical-present steps

### Critical-step recovery counts

- `Restore -> Enterprise2`: `239` recovery steps
- `Restore -> Enterprise0`: `50` recovery steps
- `Restore -> Enterprise1`: `32` recovery steps
- `Restore -> User4`: `9` recovery steps
- `Restore -> User1`: `8` recovery steps

### Critical-step no-recovery top actions

- `DecoyVsftpd -> Op_Server0`: `528` no-recovery steps
- `Restore -> Enterprise0`: `490` no-recovery steps
- `DecoySmss -> User4`: `476` no-recovery steps
- `Restore -> Enterprise2`: `468` no-recovery steps
- `DecoySmss -> Enterprise1`: `383` no-recovery steps
