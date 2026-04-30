# Critical Casebook

## Earliest Critical Breach

- Basic info: `episode_id=episode_001` `env_idx=0` `env_seed=20` `risk_tier=Tier 3 Persistent Critical Breach`
- Returns: `security=-382.4500` `business=-112.1625` `cost=-24.8400`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=12` `first_relevant_blue_response=6`

Key sequence:
- step 0: Blue `Restore` -> `Op_Server0`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 4: Blue `DecoyFemitter` -> `Enterprise2`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `Restore` -> `Enterprise2`; Red `ExploitRemoteService` -> `-`; new=Enterprise0; recovered=-; critical_after=-
- step 6: Blue `DecoyFemitter` -> `Enterprise2`; Red `PrivilegeEscalate` -> `Enterprise0`; new=-; recovered=-; critical_after=-
- step 7: Blue `Restore` -> `Enterprise2`; Red `DiscoverRemoteSystems` -> `Enterprise`; new=-; recovered=-; critical_after=-
- step 11: Blue `DecoyFemitter` -> `Enterprise2`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 12: Blue `DecoyVsftpd` -> `Enterprise1`; Red `ExploitRemoteService` -> `-`; new=Op_Server0; recovered=-; critical_after=Op_Server0
- step 13: Blue `Restore` -> `Enterprise2`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=Enterprise2; critical_after=Op_Server0
- step 14: Blue `DecoyFemitter` -> `Enterprise2`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 15: Blue `Restore` -> `Enterprise1`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 99: Blue `DecoySmss` -> `User0`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0

Conclusion:
- 最终 `Op_Server0` 仍处于 critical compromised 状态，说明该 env-run 属于持久打穿而不是短暂失守。
- 红方真正完成突破的关键节点是 step 14 对 `Op_Server0` 的 `Impact`。
- critical hit 后蓝方首次 relevant response 的延迟为 `1` step。
- 蓝方最可疑的动作规则是：`Q2_user_action_during_critical_breach`，以及 `Q4_user_focus_after_enterprise_foothold`。

## Worst Business Return

- Basic info: `episode_id=episode_019` `env_idx=4` `env_seed=4038` `risk_tier=Tier 2 Transient Critical Breach`
- Returns: `security=-484.2000` `business=-127.0075` `cost=-24.9000`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=14` `first_relevant_blue_response=6`

Key sequence:
- step 0: Blue `Restore` -> `Enterprise0`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 4: Blue `Restore` -> `Enterprise0`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `Remove` -> `Op_Host0`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-
- step 6: Blue `Restore` -> `Enterprise1`; Red `PrivilegeEscalate` -> `Enterprise1`; new=-; recovered=Enterprise1; critical_after=-
- step 7: Blue `DecoySmss` -> `User0`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-
- step 13: Blue `DecoySvchost` -> `Enterprise1`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 14: Blue `Analyse` -> `Op_Host1`; Red `ExploitRemoteService` -> `-`; new=Op_Server0; recovered=-; critical_after=Op_Server0
- step 15: Blue `DecoySvchost` -> `Enterprise1`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 16: Blue `Remove` -> `User2`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 17: Blue `DecoySvchost` -> `Enterprise1`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 99: Blue `Restore` -> `Enterprise0`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=-; critical_after=-

Conclusion:
- 曾经发生 critical breach，但最终没有维持到结束，属于短暂打穿后部分恢复。
- 红方真正完成突破的关键节点是 step 16 对 `Op_Server0` 的 `Impact`。
- critical hit 后蓝方首次 relevant response 的延迟为 `1` step。
- 蓝方最可疑的动作规则是：`Q2_user_action_during_critical_breach`，以及 `Q2_user_action_during_critical_breach`。

## Worst Security Return

- Basic info: `episode_id=episode_012` `env_idx=3` `env_seed=3031` `risk_tier=Tier 2 Transient Critical Breach`
- Returns: `security=-808.1500` `business=-111.7275` `cost=-24.5100`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=17` `first_relevant_blue_response=6`

Key sequence:
- step 0: Blue `Restore` -> `Enterprise2`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 4: Blue `Restore` -> `Op_Host2`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `Restore` -> `Op_Host2`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-
- step 6: Blue `DecoyFemitter` -> `Enterprise2`; Red `PrivilegeEscalate` -> `Enterprise1`; new=-; recovered=-; critical_after=-
- step 7: Blue `DecoyFemitter` -> `Enterprise2`; Red `DiscoverRemoteSystems` -> `Enterprise`; new=-; recovered=-; critical_after=-
- step 16: Blue `Analyse` -> `Op_Host1`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 17: Blue `Restore` -> `Enterprise2`; Red `ExploitRemoteService` -> `-`; new=Op_Server0; recovered=Enterprise2; critical_after=Op_Server0
- step 18: Blue `Restore` -> `User2`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=User2; critical_after=Op_Server0
- step 19: Blue `Analyse` -> `Op_Host1`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 20: Blue `DecoyFemitter` -> `Enterprise2`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 99: Blue `DecoyFemitter` -> `Enterprise2`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-

Conclusion:
- 曾经发生 critical breach，但最终没有维持到结束，属于短暂打穿后部分恢复。
- 红方真正完成突破的关键节点是 step 19 对 `Op_Server0` 的 `Impact`。
- critical hit 后蓝方首次 relevant response 的延迟为 `3` step。
- 蓝方最可疑的动作规则是：`Q2_user_action_during_critical_breach`，以及 `Q2_user_action_during_critical_breach`。

## Max Critical Dwell

- Basic info: `episode_id=episode_002` `env_idx=3` `env_seed=3021` `risk_tier=Tier 3 Persistent Critical Breach`
- Returns: `security=-422.5000` `business=-125.5325` `cost=-25.1600`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=14` `first_relevant_blue_response=6`

Key sequence:
- step 0: Blue `Restore` -> `Enterprise0`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 4: Blue `DecoySmss` -> `User0`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `Remove` -> `Enterprise2`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-
- step 6: Blue `Restore` -> `Enterprise1`; Red `PrivilegeEscalate` -> `Enterprise1`; new=-; recovered=Enterprise1; critical_after=-
- step 7: Blue `Restore` -> `Op_Server0`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-
- step 13: Blue `DecoyApache` -> `Enterprise1`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 14: Blue `DecoyFemitter` -> `Enterprise2`; Red `ExploitRemoteService` -> `-`; new=Op_Server0; recovered=-; critical_after=Op_Server0
- step 15: Blue `DecoyFemitter` -> `Enterprise2`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 16: Blue `Restore` -> `Enterprise0`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 17: Blue `Remove` -> `Enterprise2`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 99: Blue `Monitor` -> `-`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0

Conclusion:
- 最终 `Op_Server0` 仍处于 critical compromised 状态，说明该 env-run 属于持久打穿而不是短暂失守。
- 红方真正完成突破的关键节点是 step 16 对 `Op_Server0` 的 `Impact`。
- critical hit 后蓝方首次 relevant response 的延迟为 `1` step。
- 蓝方最可疑的动作规则是：`Q2_user_action_during_critical_breach`，以及 `Q2_user_action_during_critical_breach`。

## Best Tier 0 Safe Sample

No matching env-run was available for this case.
