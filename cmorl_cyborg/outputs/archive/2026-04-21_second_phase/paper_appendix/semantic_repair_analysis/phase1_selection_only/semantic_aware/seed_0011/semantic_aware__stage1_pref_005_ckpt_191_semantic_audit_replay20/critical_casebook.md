# Critical Casebook

## Earliest Critical Breach

- Basic info: `episode_id=episode_001` `env_idx=0` `env_seed=12` `risk_tier=Tier 3 Persistent Critical Breach`
- Returns: `security=-599.9500` `business=-138.4275` `cost=-21.4300`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=12` `first_relevant_blue_response=6`

Key sequence:
- step 0: Blue `Restore` -> `Enterprise1`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 4: Blue `Restore` -> `Enterprise1`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `DecoyVsftpd` -> `Op_Host2`; Red `ExploitRemoteService` -> `-`; new=Enterprise0; recovered=-; critical_after=-
- step 6: Blue `Analyse` -> `Enterprise1`; Red `PrivilegeEscalate` -> `Enterprise0`; new=-; recovered=-; critical_after=-
- step 7: Blue `Analyse` -> `Enterprise1`; Red `DiscoverRemoteSystems` -> `Enterprise`; new=-; recovered=-; critical_after=-
- step 11: Blue `Restore` -> `Enterprise1`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 12: Blue `Analyse` -> `Enterprise1`; Red `ExploitRemoteService` -> `-`; new=Op_Server0; recovered=-; critical_after=Op_Server0
- step 13: Blue `Analyse` -> `Enterprise1`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 14: Blue `Analyse` -> `Enterprise1`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 15: Blue `Analyse` -> `Enterprise1`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 99: Blue `Restore` -> `Enterprise1`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0

Conclusion:
- 最终 `Op_Server0` 仍处于 critical compromised 状态，说明该 env-run 属于持久打穿而不是短暂失守。
- 红方真正完成突破的关键节点是 step 14 对 `Op_Server0` 的 `Impact`。
- critical hit 后蓝方首次 relevant response 的延迟为 `1` step。
- 蓝方最可疑的动作规则是：`Q2_user_action_during_critical_breach`，以及 `Q2_user_action_during_critical_breach`。

## Worst Business Return

- Basic info: `episode_id=episode_006` `env_idx=7` `env_seed=7017` `risk_tier=Tier 3 Persistent Critical Breach`
- Returns: `security=-1228.2500` `business=-173.6925` `cost=-21.1000`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=12` `first_relevant_blue_response=7`

Key sequence:
- step 0: Blue `Remove` -> `Op_Host0`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 4: Blue `DecoyHarakaSMPT` -> `User3`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `Analyse` -> `Enterprise1`; Red `ExploitRemoteService` -> `-`; new=Enterprise0; recovered=-; critical_after=-
- step 6: Blue `Remove` -> `Op_Host0`; Red `PrivilegeEscalate` -> `Enterprise0`; new=-; recovered=-; critical_after=-
- step 7: Blue `Analyse` -> `Enterprise1`; Red `DiscoverRemoteSystems` -> `Enterprise`; new=-; recovered=-; critical_after=-
- step 8: Blue `DecoyTomcat` -> `Op_Host2`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 11: Blue `DecoySSHD` -> `Op_Server0`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 12: Blue `Restore` -> `Enterprise1`; Red `ExploitRemoteService` -> `-`; new=Op_Server0; recovered=-; critical_after=Op_Server0
- step 13: Blue `DecoyHarakaSMPT` -> `Op_Server0`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 14: Blue `Restore` -> `Enterprise1`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 15: Blue `Restore` -> `Enterprise1`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 99: Blue `Analyse` -> `Enterprise1`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0

Conclusion:
- 最终 `Op_Server0` 仍处于 critical compromised 状态，说明该 env-run 属于持久打穿而不是短暂失守。
- 红方真正完成突破的关键节点是 step 14 对 `Op_Server0` 的 `Impact`。
- critical hit 后蓝方首次 relevant response 的延迟为 `1` step。
- 蓝方最可疑的动作规则是：`Q2_user_action_during_critical_breach`，以及 `Q2_user_action_during_critical_breach`。

## Worst Security Return

- Basic info: `episode_id=episode_003` `env_idx=0` `env_seed=14` `risk_tier=Tier 3 Persistent Critical Breach`
- Returns: `security=-1450.2500` `business=-167.7050` `cost=-20.1600`
- Key times: `enterprise_foothold_step=9` `first_critical_hit_step=16` `first_relevant_blue_response=11`

Key sequence:
- step 0: Blue `Analyse` -> `Enterprise1`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 8: Blue `Analyse` -> `Enterprise1`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 9: Blue `DecoyHarakaSMPT` -> `Op_Host1`; Red `ExploitRemoteService` -> `-`; new=Enterprise0; recovered=-; critical_after=-
- step 10: Blue `Remove` -> `Op_Host0`; Red `PrivilegeEscalate` -> `Enterprise0`; new=-; recovered=-; critical_after=-
- step 11: Blue `Analyse` -> `Enterprise1`; Red `DiscoverRemoteSystems` -> `Enterprise`; new=-; recovered=-; critical_after=-
- step 12: Blue `Analyse` -> `Enterprise1`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 15: Blue `Analyse` -> `Enterprise1`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 16: Blue `DecoyHarakaSMPT` -> `Op_Server0`; Red `ExploitRemoteService` -> `-`; new=Op_Server0; recovered=-; critical_after=Op_Server0
- step 17: Blue `DecoyHarakaSMPT` -> `User3`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 18: Blue `Analyse` -> `Defender`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 19: Blue `Analyse` -> `Enterprise1`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 99: Blue `DecoyTomcat` -> `Op_Host2`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0

Conclusion:
- 最终 `Op_Server0` 仍处于 critical compromised 状态，说明该 env-run 属于持久打穿而不是短暂失守。
- 红方真正完成突破的关键节点是 step 18 对 `Op_Server0` 的 `Impact`。
- critical hit 后蓝方首次 relevant response 的延迟为 `3` step。
- 蓝方最可疑的动作规则是：`Q2_user_action_during_critical_breach`，以及 `Q2_user_action_during_critical_breach`。

## Max Critical Dwell

- Basic info: `episode_id=episode_005` `env_idx=0` `env_seed=16` `risk_tier=Tier 3 Persistent Critical Breach`
- Returns: `security=-528.6500` `business=-145.9975` `cost=-17.9800`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=12` `first_relevant_blue_response=6`

Key sequence:
- step 0: Blue `Analyse` -> `Enterprise1`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 4: Blue `Analyse` -> `Enterprise1`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `Analyse` -> `Enterprise1`; Red `ExploitRemoteService` -> `-`; new=Enterprise0; recovered=-; critical_after=-
- step 6: Blue `Analyse` -> `Enterprise1`; Red `PrivilegeEscalate` -> `Enterprise0`; new=-; recovered=-; critical_after=-
- step 7: Blue `Restore` -> `User0`; Red `DiscoverRemoteSystems` -> `Enterprise`; new=-; recovered=-; critical_after=-
- step 11: Blue `Restore` -> `Op_Server0`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 12: Blue `DecoySSHD` -> `Op_Server0`; Red `ExploitRemoteService` -> `-`; new=Op_Server0; recovered=-; critical_after=Op_Server0
- step 13: Blue `Analyse` -> `Enterprise1`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 14: Blue `Analyse` -> `Enterprise1`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 15: Blue `DecoySSHD` -> `Op_Server0`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 99: Blue `Analyse` -> `Enterprise1`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0

Conclusion:
- 最终 `Op_Server0` 仍处于 critical compromised 状态，说明该 env-run 属于持久打穿而不是短暂失守。
- 红方真正完成突破的关键节点是 step 14 对 `Op_Server0` 的 `Impact`。
- critical hit 后蓝方首次 relevant response 的延迟为 `1` step。
- 蓝方最可疑的动作规则是：`Q2_user_action_during_critical_breach`，以及 `Q2_user_action_during_critical_breach`。

## Best Tier 0 Safe Sample

No matching env-run was available for this case.
