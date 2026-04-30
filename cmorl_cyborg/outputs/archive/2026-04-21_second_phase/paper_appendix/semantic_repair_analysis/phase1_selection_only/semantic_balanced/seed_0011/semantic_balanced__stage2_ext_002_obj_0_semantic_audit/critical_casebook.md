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

## Worst Security Return

- Basic info: `episode_id=episode_000` `env_idx=4` `env_seed=4011` `risk_tier=Tier 2 Transient Critical Breach`
- Returns: `security=-654.5500` `business=-119.6650` `cost=-27.3700`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=12` `first_relevant_blue_response=7`

Key sequence:
- step 0: Blue `Restore` -> `Enterprise2`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 4: Blue `Restore` -> `Enterprise2`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `DecoyFemitter` -> `Enterprise0`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-
- step 6: Blue `Analyse` -> `User2`; Red `PrivilegeEscalate` -> `Enterprise1`; new=-; recovered=-; critical_after=-
- step 7: Blue `DecoySmss` -> `Enterprise0`; Red `DiscoverRemoteSystems` -> `Enterprise`; new=-; recovered=-; critical_after=-
- step 8: Blue `Restore` -> `Enterprise2`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 11: Blue `Restore` -> `Enterprise2`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=Enterprise2; critical_after=-
- step 12: Blue `DecoyHarakaSMPT` -> `User1`; Red `ExploitRemoteService` -> `-`; new=Op_Server0; recovered=-; critical_after=Op_Server0
- step 13: Blue `Restore` -> `Enterprise2`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 14: Blue `Restore` -> `Enterprise2`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 15: Blue `DecoyApache` -> `Op_Host0`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 99: Blue `Restore` -> `Enterprise2`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=Enterprise2; critical_after=-

Conclusion:
- 曾经发生 critical breach，但最终没有维持到结束，属于短暂打穿后部分恢复。
- 红方真正完成突破的关键节点是 step 14 对 `Op_Server0` 的 `Impact`。
- critical hit 后蓝方首次 relevant response 的延迟为 `1` step。
- 蓝方最可疑的动作规则是：`Q2_user_action_during_critical_breach`，以及 `Q2_user_action_during_critical_breach`。

## Max Critical Dwell

- Basic info: `episode_id=episode_001` `env_idx=4` `env_seed=4012` `risk_tier=Tier 3 Persistent Critical Breach`
- Returns: `security=-444.9000` `business=-122.3750` `cost=-29.4700`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=12` `first_relevant_blue_response=6`

Key sequence:
- step 0: Blue `Restore` -> `Enterprise2`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 4: Blue `DecoyVsftpd` -> `Op_Host0`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `Restore` -> `Enterprise2`; Red `ExploitRemoteService` -> `-`; new=Enterprise0; recovered=-; critical_after=-
- step 6: Blue `Restore` -> `Enterprise2`; Red `PrivilegeEscalate` -> `Enterprise0`; new=-; recovered=-; critical_after=-
- step 7: Blue `DecoyHarakaSMPT` -> `User2`; Red `DiscoverRemoteSystems` -> `Enterprise`; new=-; recovered=-; critical_after=-
- step 11: Blue `Restore` -> `Op_Server0`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 12: Blue `DecoyVsftpd` -> `Op_Host0`; Red `ExploitRemoteService` -> `-`; new=Op_Server0; recovered=-; critical_after=Op_Server0
- step 13: Blue `DecoySmss` -> `Enterprise0`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 14: Blue `Restore` -> `Enterprise2`; Red `Impact` -> `Op_Server0`; new=-; recovered=Enterprise2; critical_after=Op_Server0
- step 15: Blue `Restore` -> `Enterprise2`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 99: Blue `DecoyVsftpd` -> `Op_Host0`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0

Conclusion:
- 最终 `Op_Server0` 仍处于 critical compromised 状态，说明该 env-run 属于持久打穿而不是短暂失守。
- 红方真正完成突破的关键节点是 step 14 对 `Op_Server0` 的 `Impact`。
- critical hit 后蓝方首次 relevant response 的延迟为 `1` step。
- 蓝方最可疑的动作规则是：`Q2_user_action_during_critical_breach`，以及 `Q2_user_action_during_critical_breach`。

## Best Tier 0 Safe Sample

No matching env-run was available for this case.
