# Critical Casebook

## Earliest Critical Breach

- Basic info: `episode_id=episode_005` `env_idx=0` `env_seed=12` `risk_tier=Tier 2 Transient Critical Breach`
- Returns: `security=-1007.9500` `business=-115.3500` `cost=-23.0300`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=12` `first_relevant_blue_response=9`

Key sequence:
- step 0: Blue `DecoyTomcat` -> `User3`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 4: Blue `DecoyTomcat` -> `Enterprise1`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `Restore` -> `Enterprise2`; Red `ExploitRemoteService` -> `-`; new=Enterprise0; recovered=-; critical_after=-
- step 6: Blue `DecoyTomcat` -> `User3`; Red `PrivilegeEscalate` -> `Enterprise0`; new=-; recovered=-; critical_after=-
- step 8: Blue `DecoyHarakaSMPT` -> `User1`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 9: Blue `DecoyHarakaSMPT` -> `Op_Server0`; Red `ExploitRemoteService` -> `-`; new=Enterprise2; recovered=-; critical_after=-
- step 10: Blue `DecoyApache` -> `User2`; Red `PrivilegeEscalate` -> `Enterprise2`; new=-; recovered=-; critical_after=-
- step 11: Blue `DecoySvchost` -> `User3`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 12: Blue `DecoyApache` -> `Op_Server0`; Red `ExploitRemoteService` -> `-`; new=Op_Server0; recovered=-; critical_after=Op_Server0
- step 13: Blue `Restore` -> `Enterprise2`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=Enterprise2; critical_after=Op_Server0
- step 14: Blue `DecoySmss` -> `Enterprise2`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 99: Blue `DecoyHarakaSMPT` -> `User1`; Red `ExploitRemoteService` -> `-`; new=-; recovered=-; critical_after=-

Conclusion:
- 曾经发生 critical breach，但最终没有维持到结束，属于短暂打穿后部分恢复。
- 红方真正完成突破的关键节点是 step 14 对 `Op_Server0` 的 `Impact`。
- critical hit 后蓝方首次 relevant response 的延迟为 `1` step。
- 蓝方最可疑的动作规则是：`Q4_user_focus_after_enterprise_foothold`，以及 `Q2_user_action_during_critical_breach`。

## Worst Business Return

- Basic info: `episode_id=episode_000` `env_idx=7` `env_seed=7007` `risk_tier=Tier 3 Persistent Critical Breach`
- Returns: `security=-1299.5500` `business=-152.2225` `cost=-20.9800`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=26` `first_relevant_blue_response=6`

Key sequence:
- step 0: Blue `Remove` -> `User0`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 4: Blue `Remove` -> `User0`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `DecoyApache` -> `User2`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-
- step 6: Blue `DecoyHarakaSMPT` -> `Op_Server0`; Red `PrivilegeEscalate` -> `Enterprise1`; new=-; recovered=-; critical_after=-
- step 7: Blue `DecoyVsftpd` -> `Op_Server0`; Red `DiscoverRemoteSystems` -> `Enterprise`; new=-; recovered=-; critical_after=-
- step 25: Blue `DecoyVsftpd` -> `Op_Server0`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 26: Blue `DecoyApache` -> `User2`; Red `ExploitRemoteService` -> `-`; new=Op_Server0; recovered=-; critical_after=Op_Server0
- step 27: Blue `DecoySmss` -> `Enterprise2`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 28: Blue `DecoySmss` -> `Op_Host0`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 29: Blue `DecoySSHD` -> `User4`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 99: Blue `DecoyHarakaSMPT` -> `Op_Host0`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0

Conclusion:
- 最终 `Op_Server0` 仍处于 critical compromised 状态，说明该 env-run 属于持久打穿而不是短暂失守。
- 红方真正完成突破的关键节点是 step 28 对 `Op_Server0` 的 `Impact`。
- critical hit 后蓝方首次 relevant response 的延迟为 `1` step。
- 蓝方最可疑的动作规则是：`Q4_user_focus_after_enterprise_foothold`，以及 `Q5_repeated_low_value_decoy_loop`。

## Worst Security Return

- Basic info: `episode_id=episode_005` `env_idx=7` `env_seed=7012` `risk_tier=Tier 3 Persistent Critical Breach`
- Returns: `security=-1381.2500` `business=-142.5500` `cost=-22.2600`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=12` `first_relevant_blue_response=8`

Key sequence:
- step 0: Blue `DecoySmss` -> `Enterprise2`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 4: Blue `DecoySmss` -> `Enterprise2`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `DecoyTomcat` -> `User2`; Red `ExploitRemoteService` -> `-`; new=Enterprise0; recovered=-; critical_after=-
- step 6: Blue `DecoyApache` -> `User2`; Red `PrivilegeEscalate` -> `Enterprise0`; new=-; recovered=-; critical_after=-
- step 7: Blue `DecoySmss` -> `Op_Host0`; Red `DiscoverRemoteSystems` -> `Enterprise`; new=-; recovered=-; critical_after=-
- step 8: Blue `DecoySmss` -> `Enterprise2`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 9: Blue `Restore` -> `Enterprise2`; Red `ExploitRemoteService` -> `-`; new=Enterprise2; recovered=-; critical_after=-
- step 11: Blue `Analyse` -> `User1`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 12: Blue `DecoyApache` -> `User2`; Red `ExploitRemoteService` -> `-`; new=Op_Server0; recovered=-; critical_after=Op_Server0
- step 13: Blue `DecoyTomcat` -> `Enterprise1`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 14: Blue `DecoyVsftpd` -> `Op_Server0`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 99: Blue `DecoyApache` -> `User4`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0

Conclusion:
- 最终 `Op_Server0` 仍处于 critical compromised 状态，说明该 env-run 属于持久打穿而不是短暂失守。
- 红方真正完成突破的关键节点是 step 14 对 `Op_Server0` 的 `Impact`。
- critical hit 后蓝方首次 relevant response 的延迟为 `1` step。
- 蓝方最可疑的动作规则是：`Q5_repeated_low_value_decoy_loop`，以及 `Q4_user_focus_after_enterprise_foothold`。

## Max Critical Dwell

- Basic info: `episode_id=episode_013` `env_idx=0` `env_seed=20` `risk_tier=Tier 3 Persistent Critical Breach`
- Returns: `security=-1267.5000` `business=-125.2550` `cost=-22.8900`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=12` `first_relevant_blue_response=6`

Key sequence:
- step 0: Blue `DecoyHarakaSMPT` -> `Op_Server0`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 4: Blue `DecoyHarakaSMPT` -> `User1`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `Restore` -> `Enterprise2`; Red `ExploitRemoteService` -> `-`; new=Enterprise0; recovered=-; critical_after=-
- step 6: Blue `DecoyHarakaSMPT` -> `Op_Server0`; Red `PrivilegeEscalate` -> `Enterprise0`; new=-; recovered=-; critical_after=-
- step 7: Blue `Restore` -> `Enterprise2`; Red `DiscoverRemoteSystems` -> `Enterprise`; new=-; recovered=-; critical_after=-
- step 11: Blue `DecoyHarakaSMPT` -> `User1`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 12: Blue `DecoyApache` -> `Op_Server0`; Red `ExploitRemoteService` -> `-`; new=Op_Server0; recovered=-; critical_after=Op_Server0
- step 13: Blue `Restore` -> `Enterprise2`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=Enterprise2; critical_after=Op_Server0
- step 14: Blue `DecoyHarakaSMPT` -> `Op_Host0`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 15: Blue `DecoySvchost` -> `User1`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 99: Blue `DecoyHarakaSMPT` -> `User1`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0

Conclusion:
- 最终 `Op_Server0` 仍处于 critical compromised 状态，说明该 env-run 属于持久打穿而不是短暂失守。
- 红方真正完成突破的关键节点是 step 14 对 `Op_Server0` 的 `Impact`。
- critical hit 后蓝方首次 relevant response 的延迟为 `1` step。
- 蓝方最可疑的动作规则是：`Q2_user_action_during_critical_breach`，以及 `Q2_user_action_during_critical_breach`。

## Best Tier 0 Safe Sample

No matching env-run was available for this case.
