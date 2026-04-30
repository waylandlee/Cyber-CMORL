# Critical Casebook

## Earliest Critical Breach

- Basic info: `episode_id=episode_001` `env_idx=0` `env_seed=12` `risk_tier=Tier 3 Persistent Critical Breach`
- Returns: `security=-1506.0500` `business=-172.8725` `cost=-21.6200`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=12` `first_relevant_blue_response=9`

Key sequence:
- step 0: Blue `DecoyFemitter` -> `Enterprise2`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 4: Blue `DecoyFemitter` -> `Enterprise1`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `DecoyFemitter` -> `Defender`; Red `ExploitRemoteService` -> `-`; new=Enterprise0; recovered=-; critical_after=-
- step 6: Blue `DecoyTomcat` -> `User3`; Red `PrivilegeEscalate` -> `Enterprise0`; new=-; recovered=-; critical_after=-
- step 8: Blue `DecoySSHD` -> `User2`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 9: Blue `Remove` -> `Enterprise1`; Red `ExploitRemoteService` -> `-`; new=Enterprise2; recovered=-; critical_after=-
- step 10: Blue `DecoySvchost` -> `User2`; Red `PrivilegeEscalate` -> `Enterprise2`; new=-; recovered=-; critical_after=-
- step 11: Blue `DecoySvchost` -> `User3`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 12: Blue `DecoyApache` -> `Op_Server0`; Red `ExploitRemoteService` -> `-`; new=Op_Server0; recovered=-; critical_after=Op_Server0
- step 13: Blue `DecoySSHD` -> `User1`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 14: Blue `DecoyApache` -> `Op_Host2`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 99: Blue `DecoyApache` -> `Op_Server0`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0

Conclusion:
- 最终 `Op_Server0` 仍处于 critical compromised 状态，说明该 env-run 属于持久打穿而不是短暂失守。
- 红方真正完成突破的关键节点是 step 14 对 `Op_Server0` 的 `Impact`。
- critical hit 后蓝方首次 relevant response 的延迟为 `3` step。
- 蓝方最可疑的动作规则是：`Q2_user_action_during_critical_breach`，以及 `Q2_user_action_during_critical_breach`。

## Worst Business Return

- Basic info: `episode_id=episode_018` `env_idx=6` `env_seed=6029` `risk_tier=Tier 3 Persistent Critical Breach`
- Returns: `security=-1504.0500` `business=-174.1225` `cost=-21.4000`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=12` `first_relevant_blue_response=7`

Key sequence:
- step 0: Blue `DecoySmss` -> `Enterprise0`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 4: Blue `DecoyVsftpd` -> `Enterprise2`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `DecoySvchost` -> `Defender`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-
- step 6: Blue `DecoyTomcat` -> `User0`; Red `PrivilegeEscalate` -> `Enterprise1`; new=-; recovered=-; critical_after=-
- step 7: Blue `Remove` -> `Op_Server0`; Red `DiscoverRemoteSystems` -> `Enterprise`; new=-; recovered=-; critical_after=-
- step 8: Blue `DecoyTomcat` -> `Enterprise2`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 11: Blue `DecoySmss` -> `Defender`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 12: Blue `Restore` -> `User3`; Red `ExploitRemoteService` -> `-`; new=Op_Server0; recovered=-; critical_after=Op_Server0
- step 13: Blue `Restore` -> `Op_Host2`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 14: Blue `DecoyTomcat` -> `User0`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 15: Blue `Analyse` -> `Op_Host0`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 99: Blue `DecoyFemitter` -> `Enterprise2`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0

Conclusion:
- 最终 `Op_Server0` 仍处于 critical compromised 状态，说明该 env-run 属于持久打穿而不是短暂失守。
- 红方真正完成突破的关键节点是 step 14 对 `Op_Server0` 的 `Impact`。
- critical hit 后蓝方首次 relevant response 的延迟为 `4` step。
- 蓝方最可疑的动作规则是：`Q3_missed_immediate_response_to_critical_hit`，以及 `Q2_user_action_during_critical_breach`。

## Worst Security Return

- Basic info: `episode_id=episode_005` `env_idx=7` `env_seed=7016` `risk_tier=Tier 3 Persistent Critical Breach`
- Returns: `security=-1510.0500` `business=-173.8000` `cost=-23.0900`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=12` `first_relevant_blue_response=12`

Key sequence:
- step 0: Blue `DecoyVsftpd` -> `User2`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 4: Blue `DecoySSHD` -> `User2`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `DecoySmss` -> `Enterprise0`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-
- step 6: Blue `DecoySvchost` -> `User1`; Red `PrivilegeEscalate` -> `Enterprise1`; new=-; recovered=-; critical_after=-
- step 11: Blue `DecoyFemitter` -> `User4`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 12: Blue `DecoyFemitter` -> `Enterprise2`; Red `ExploitRemoteService` -> `-`; new=Op_Server0; recovered=-; critical_after=Op_Server0
- step 13: Blue `DecoyTomcat` -> `Op_Host0`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 14: Blue `DecoyTomcat` -> `Enterprise2`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 15: Blue `DecoySvchost` -> `User4`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 99: Blue `DecoyFemitter` -> `Enterprise2`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0

Conclusion:
- 最终 `Op_Server0` 仍处于 critical compromised 状态，说明该 env-run 属于持久打穿而不是短暂失守。
- 红方真正完成突破的关键节点是 step 14 对 `Op_Server0` 的 `Impact`。
- critical hit 后蓝方首次 relevant response 的延迟为 `2` step。
- 蓝方最可疑的动作规则是：`Q2_user_action_during_critical_breach`，以及 `Q2_user_action_during_critical_breach`。

## Max Critical Dwell

- Basic info: `episode_id=episode_003` `env_idx=0` `env_seed=14` `risk_tier=Tier 3 Persistent Critical Breach`
- Returns: `security=-1405.8500` `business=-158.6025` `cost=-21.2900`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=12` `first_relevant_blue_response=8`

Key sequence:
- step 0: Blue `DecoySmss` -> `Op_Host0`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 4: Blue `DecoySvchost` -> `Op_Host2`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `DecoySSHD` -> `Defender`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-
- step 6: Blue `DecoySvchost` -> `User3`; Red `PrivilegeEscalate` -> `Enterprise1`; new=-; recovered=-; critical_after=-
- step 7: Blue `Restore` -> `Op_Host0`; Red `DiscoverRemoteSystems` -> `Enterprise`; new=-; recovered=-; critical_after=-
- step 8: Blue `DecoyFemitter` -> `Enterprise2`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 9: Blue `DecoyHarakaSMPT` -> `Op_Host1`; Red `ExploitRemoteService` -> `-`; new=Enterprise2; recovered=-; critical_after=-
- step 11: Blue `Remove` -> `Enterprise1`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 12: Blue `DecoySvchost` -> `Op_Host0`; Red `ExploitRemoteService` -> `-`; new=Op_Server0; recovered=-; critical_after=Op_Server0
- step 13: Blue `DecoySmss` -> `Enterprise0`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 14: Blue `Analyse` -> `Op_Host0`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 99: Blue `DecoyHarakaSMPT` -> `Op_Server0`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0

Conclusion:
- 最终 `Op_Server0` 仍处于 critical compromised 状态，说明该 env-run 属于持久打穿而不是短暂失守。
- 红方真正完成突破的关键节点是 step 14 对 `Op_Server0` 的 `Impact`。
- critical hit 后蓝方首次 relevant response 的延迟为 `1` step。
- 蓝方最可疑的动作规则是：`Q2_user_action_during_critical_breach`，以及 `Q2_user_action_during_critical_breach`。

## Best Tier 0 Safe Sample

No matching env-run was available for this case.
