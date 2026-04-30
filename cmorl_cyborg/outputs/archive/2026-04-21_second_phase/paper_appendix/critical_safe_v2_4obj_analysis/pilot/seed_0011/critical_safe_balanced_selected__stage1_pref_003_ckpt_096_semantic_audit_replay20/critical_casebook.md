# Critical Casebook

## Earliest Critical Breach

- Basic info: `episode_id=episode_001` `env_idx=0` `env_seed=12` `risk_tier=Tier 3 Persistent Critical Breach`
- Returns: `security=-1391.4500` `business=-157.6475` `cost=-20.1500`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=12` `first_relevant_blue_response=9`

Key sequence:
- step 0: Blue `DecoySSHD` -> `Enterprise2`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 4: Blue `DecoyFemitter` -> `Enterprise1`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `DecoyFemitter` -> `Defender`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-
- step 6: Blue `DecoyTomcat` -> `User3`; Red `PrivilegeEscalate` -> `Enterprise1`; new=-; recovered=-; critical_after=-
- step 8: Blue `DecoySSHD` -> `User2`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 9: Blue `Remove` -> `Enterprise1`; Red `ExploitRemoteService` -> `-`; new=Enterprise2; recovered=-; critical_after=-
- step 10: Blue `DecoySvchost` -> `User2`; Red `PrivilegeEscalate` -> `Enterprise2`; new=-; recovered=-; critical_after=-
- step 11: Blue `DecoySvchost` -> `User3`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 12: Blue `DecoyApache` -> `Op_Server0`; Red `ExploitRemoteService` -> `-`; new=Op_Server0; recovered=-; critical_after=Op_Server0
- step 13: Blue `DecoySSHD` -> `User1`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 14: Blue `DecoySmss` -> `Defender`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 99: Blue `DecoySSHD` -> `Op_Host1`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0

Conclusion:
- 最终 `Op_Server0` 仍处于 critical compromised 状态，说明该 env-run 属于持久打穿而不是短暂失守。
- 红方真正完成突破的关键节点是 step 14 对 `Op_Server0` 的 `Impact`。
- critical hit 后蓝方首次 relevant response 的延迟为 `3` step。
- 蓝方最可疑的动作规则是：`Q2_user_action_during_critical_breach`，以及 `Q2_user_action_during_critical_breach`。

## Worst Business Return

- Basic info: `episode_id=episode_008` `env_idx=4` `env_seed=4019` `risk_tier=Tier 3 Persistent Critical Breach`
- Returns: `security=-1504.0500` `business=-174.3300` `cost=-20.5700`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=12` `first_relevant_blue_response=12`

Key sequence:
- step 0: Blue `DecoyVsftpd` -> `User4`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 4: Blue `DecoySvchost` -> `Op_Host1`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `DecoyFemitter` -> `Op_Host0`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-
- step 6: Blue `DecoyTomcat` -> `User3`; Red `PrivilegeEscalate` -> `Enterprise1`; new=-; recovered=-; critical_after=-
- step 11: Blue `DecoySmss` -> `User0`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 12: Blue `DecoyTomcat` -> `Op_Server0`; Red `ExploitRemoteService` -> `-`; new=Op_Server0; recovered=-; critical_after=Op_Server0
- step 13: Blue `Analyse` -> `User1`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 14: Blue `Remove` -> `Op_Server0`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 15: Blue `DecoyApache` -> `Op_Server0`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 99: Blue `Remove` -> `Op_Host1`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0

Conclusion:
- 最终 `Op_Server0` 仍处于 critical compromised 状态，说明该 env-run 属于持久打穿而不是短暂失守。
- 红方真正完成突破的关键节点是 step 14 对 `Op_Server0` 的 `Impact`。
- critical hit 后蓝方首次 relevant response 的延迟为 `2` step。
- 蓝方最可疑的动作规则是：`Q4_user_focus_after_enterprise_foothold`，以及 `Q4_user_focus_after_enterprise_foothold`。

## Worst Security Return

- Basic info: `episode_id=episode_019` `env_idx=7` `env_seed=7030` `risk_tier=Tier 3 Persistent Critical Breach`
- Returns: `security=-1503.0500` `business=-173.5275` `cost=-20.9500`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=12` `first_relevant_blue_response=9`

Key sequence:
- step 0: Blue `Analyse` -> `User2`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 4: Blue `DecoyVsftpd` -> `Defender`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `DecoyTomcat` -> `Op_Server0`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-
- step 6: Blue `Restore` -> `User1`; Red `PrivilegeEscalate` -> `Enterprise1`; new=-; recovered=-; critical_after=-
- step 8: Blue `Remove` -> `User1`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 9: Blue `DecoyTomcat` -> `Op_Server0`; Red `ExploitRemoteService` -> `-`; new=Enterprise2; recovered=-; critical_after=-
- step 10: Blue `Analyse` -> `User2`; Red `PrivilegeEscalate` -> `Enterprise2`; new=-; recovered=-; critical_after=-
- step 11: Blue `DecoyVsftpd` -> `User4`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 12: Blue `Remove` -> `User0`; Red `ExploitRemoteService` -> `-`; new=Op_Server0; recovered=-; critical_after=Op_Server0
- step 13: Blue `DecoyFemitter` -> `Enterprise1`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 14: Blue `DecoyHarakaSMPT` -> `Op_Host2`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 99: Blue `Remove` -> `Enterprise1`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0

Conclusion:
- 最终 `Op_Server0` 仍处于 critical compromised 状态，说明该 env-run 属于持久打穿而不是短暂失守。
- 红方真正完成突破的关键节点是 step 14 对 `Op_Server0` 的 `Impact`。
- critical hit 后蓝方首次 relevant response 的延迟为 `1` step。
- 蓝方最可疑的动作规则是：`Q4_user_focus_after_enterprise_foothold`，以及 `Q2_user_action_during_critical_breach`。

## Max Critical Dwell

- Basic info: `episode_id=episode_010` `env_idx=0` `env_seed=21` `risk_tier=Tier 3 Persistent Critical Breach`
- Returns: `security=-1378.3500` `business=-155.3325` `cost=-19.7700`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=12` `first_relevant_blue_response=7`

Key sequence:
- step 0: Blue `DecoySSHD` -> `User2`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 4: Blue `DecoySSHD` -> `Op_Server0`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `Restore` -> `User0`; Red `ExploitRemoteService` -> `-`; new=Enterprise0; recovered=-; critical_after=-
- step 6: Blue `DecoyVsftpd` -> `Op_Host2`; Red `PrivilegeEscalate` -> `Enterprise0`; new=-; recovered=-; critical_after=-
- step 7: Blue `DecoyApache` -> `Enterprise0`; Red `DiscoverRemoteSystems` -> `Enterprise`; new=-; recovered=-; critical_after=-
- step 8: Blue `DecoySvchost` -> `User1`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 11: Blue `DecoySvchost` -> `User4`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 12: Blue `DecoySmss` -> `User2`; Red `ExploitRemoteService` -> `-`; new=Op_Server0; recovered=-; critical_after=Op_Server0
- step 13: Blue `DecoyHarakaSMPT` -> `User1`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 14: Blue `DecoyApache` -> `Op_Server0`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 15: Blue `DecoyApache` -> `User3`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 99: Blue `DecoyTomcat` -> `Op_Server0`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0

Conclusion:
- 最终 `Op_Server0` 仍处于 critical compromised 状态，说明该 env-run 属于持久打穿而不是短暂失守。
- 红方真正完成突破的关键节点是 step 14 对 `Op_Server0` 的 `Impact`。
- critical hit 后蓝方首次 relevant response 的延迟为 `2` step。
- 蓝方最可疑的动作规则是：`Q4_user_focus_after_enterprise_foothold`，以及 `Q2_user_action_during_critical_breach`。

## Best Tier 0 Safe Sample

No matching env-run was available for this case.
