# Critical Casebook

## Earliest Critical Breach

- Basic info: `episode_id=episode_001` `env_idx=0` `env_seed=12` `risk_tier=Tier 3 Persistent Critical Breach`
- Returns: `security=-1418.4500` `business=-160.2025` `cost=-20.0900`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=12` `first_relevant_blue_response=15`

Key sequence:
- step 0: Blue `DecoySSHD` -> `Enterprise2`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 4: Blue `DecoySSHD` -> `Op_Host2`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `DecoyHarakaSMPT` -> `Enterprise2`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-
- step 6: Blue `DecoyTomcat` -> `User3`; Red `PrivilegeEscalate` -> `Enterprise1`; new=-; recovered=-; critical_after=-
- step 11: Blue `DecoySvchost` -> `User3`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 12: Blue `Analyse` -> `Op_Host1`; Red `ExploitRemoteService` -> `-`; new=Op_Server0; recovered=-; critical_after=Op_Server0
- step 13: Blue `DecoySSHD` -> `User1`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 14: Blue `DecoySvchost` -> `Op_Host0`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 15: Blue `DecoyFemitter` -> `Enterprise2`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 16: Blue `DecoyHarakaSMPT` -> `Op_Server0`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 99: Blue `DecoySSHD` -> `User4`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0

Conclusion:
- 最终 `Op_Server0` 仍处于 critical compromised 状态，说明该 env-run 属于持久打穿而不是短暂失守。
- 红方真正完成突破的关键节点是 step 14 对 `Op_Server0` 的 `Impact`。
- critical hit 后蓝方首次 relevant response 的延迟为 `3` step。
- 蓝方最可疑的动作规则是：`Q2_user_action_during_critical_breach`，以及 `Q2_user_action_during_critical_breach`。

## Worst Business Return

- Basic info: `episode_id=episode_012` `env_idx=4` `env_seed=4023` `risk_tier=Tier 3 Persistent Critical Breach`
- Returns: `security=-1500.0500` `business=-174.5550` `cost=-20.6000`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=12` `first_relevant_blue_response=6`

Key sequence:
- step 0: Blue `DecoyHarakaSMPT` -> `Enterprise1`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 4: Blue `Remove` -> `Op_Server0`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `Remove` -> `User3`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-
- step 6: Blue `DecoyFemitter` -> `Enterprise0`; Red `PrivilegeEscalate` -> `Enterprise1`; new=-; recovered=-; critical_after=-
- step 7: Blue `DecoySmss` -> `User1`; Red `DiscoverRemoteSystems` -> `Enterprise`; new=-; recovered=-; critical_after=-
- step 11: Blue `DecoySvchost` -> `Op_Host0`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 12: Blue `DecoyHarakaSMPT` -> `Enterprise2`; Red `ExploitRemoteService` -> `-`; new=Op_Server0; recovered=-; critical_after=Op_Server0
- step 13: Blue `DecoyApache` -> `Enterprise1`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 14: Blue `Sleep` -> `-`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 15: Blue `Analyse` -> `Op_Server0`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 99: Blue `DecoySSHD` -> `User4`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0

Conclusion:
- 最终 `Op_Server0` 仍处于 critical compromised 状态，说明该 env-run 属于持久打穿而不是短暂失守。
- 红方真正完成突破的关键节点是 step 14 对 `Op_Server0` 的 `Impact`。
- critical hit 后蓝方首次 relevant response 的延迟为 `1` step。
- 蓝方最可疑的动作规则是：`Q1_sleep_during_critical_breach`，以及 `Q2_user_action_during_critical_breach`。

## Worst Security Return

- Basic info: `episode_id=episode_005` `env_idx=3` `env_seed=3016` `risk_tier=Tier 3 Persistent Critical Breach`
- Returns: `security=-1505.0500` `business=-173.2525` `cost=-21.5900`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=12` `first_relevant_blue_response=6`

Key sequence:
- step 0: Blue `Restore` -> `Op_Host1`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 4: Blue `DecoySSHD` -> `User4`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `DecoySSHD` -> `User3`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-
- step 6: Blue `DecoySSHD` -> `Op_Server0`; Red `PrivilegeEscalate` -> `Enterprise1`; new=-; recovered=-; critical_after=-
- step 7: Blue `DecoyFemitter` -> `User0`; Red `DiscoverRemoteSystems` -> `Enterprise`; new=-; recovered=-; critical_after=-
- step 11: Blue `DecoyFemitter` -> `Op_Host1`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 12: Blue `DecoySmss` -> `User3`; Red `ExploitRemoteService` -> `-`; new=Op_Server0; recovered=-; critical_after=Op_Server0
- step 13: Blue `DecoyHarakaSMPT` -> `User4`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 14: Blue `DecoyHarakaSMPT` -> `Op_Host2`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 15: Blue `DecoySmss` -> `User0`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 99: Blue `DecoySvchost` -> `Op_Host2`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0

Conclusion:
- 最终 `Op_Server0` 仍处于 critical compromised 状态，说明该 env-run 属于持久打穿而不是短暂失守。
- 红方真正完成突破的关键节点是 step 14 对 `Op_Server0` 的 `Impact`。
- critical hit 后蓝方首次 relevant response 的延迟为 `10` step。
- 蓝方最可疑的动作规则是：`Q3_missed_immediate_response_to_critical_hit`，以及 `Q2_user_action_during_critical_breach`。

## Max Critical Dwell

- Basic info: `episode_id=episode_010` `env_idx=0` `env_seed=21` `risk_tier=Tier 3 Persistent Critical Breach`
- Returns: `security=-1499.0500` `business=-171.7400` `cost=-19.9300`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=12` `first_relevant_blue_response=13`

Key sequence:
- step 0: Blue `DecoySSHD` -> `User2`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 4: Blue `DecoySSHD` -> `Op_Server0`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `Restore` -> `User0`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-
- step 6: Blue `DecoyApache` -> `User2`; Red `PrivilegeEscalate` -> `Enterprise1`; new=-; recovered=-; critical_after=-
- step 11: Blue `DecoySvchost` -> `User4`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 12: Blue `DecoySmss` -> `User2`; Red `ExploitRemoteService` -> `-`; new=Op_Server0; recovered=-; critical_after=Op_Server0
- step 13: Blue `DecoyFemitter` -> `Enterprise0`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 14: Blue `DecoyApache` -> `Op_Server0`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 15: Blue `DecoyApache` -> `User3`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 99: Blue `DecoyTomcat` -> `Op_Server0`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0

Conclusion:
- 最终 `Op_Server0` 仍处于 critical compromised 状态，说明该 env-run 属于持久打穿而不是短暂失守。
- 红方真正完成突破的关键节点是 step 14 对 `Op_Server0` 的 `Impact`。
- critical hit 后蓝方首次 relevant response 的延迟为 `1` step。
- 蓝方最可疑的动作规则是：`Q4_user_focus_after_enterprise_foothold`，以及 `Q4_user_focus_after_enterprise_foothold`。

## Best Tier 0 Safe Sample

No matching env-run was available for this case.
