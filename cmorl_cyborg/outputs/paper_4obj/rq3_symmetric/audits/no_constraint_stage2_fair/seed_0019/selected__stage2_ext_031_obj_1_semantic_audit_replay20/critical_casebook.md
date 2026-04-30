# Critical Casebook

## Earliest Critical Breach

- Basic info: `episode_id=episode_001` `env_idx=0` `env_seed=20` `risk_tier=Tier 3 Persistent Critical Breach`
- Returns: `security=-1345.1000` `business=-132.0800` `cost=-21.0400`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=12` `first_relevant_blue_response=9`

Key sequence:
- step 0: Blue `DecoyHarakaSMPT` -> `Enterprise0`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 4: Blue `DecoySSHD` -> `User3`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `Restore` -> `Enterprise2`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-
- step 6: Blue `DecoyVsftpd` -> `Op_Host0`; Red `PrivilegeEscalate` -> `Enterprise1`; new=-; recovered=-; critical_after=-
- step 8: Blue `DecoyVsftpd` -> `Op_Host2`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 9: Blue `Restore` -> `Enterprise2`; Red `ExploitRemoteService` -> `-`; new=Enterprise2; recovered=-; critical_after=-
- step 10: Blue `DecoyHarakaSMPT` -> `Enterprise0`; Red `PrivilegeEscalate` -> `Enterprise2`; new=-; recovered=-; critical_after=-
- step 11: Blue `DecoySSHD` -> `Enterprise2`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 12: Blue `DecoyHarakaSMPT` -> `Enterprise0`; Red `ExploitRemoteService` -> `-`; new=Op_Server0; recovered=-; critical_after=Op_Server0
- step 13: Blue `Restore` -> `Enterprise2`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=Enterprise2; critical_after=Op_Server0
- step 14: Blue `DecoyApache` -> `Enterprise0`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 99: Blue `Restore` -> `Op_Host0`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0

Conclusion:
- 最终 `Op_Server0` 仍处于 critical compromised 状态，说明该 env-run 属于持久打穿而不是短暂失守。
- 红方真正完成突破的关键节点是 step 14 对 `Op_Server0` 的 `Impact`。
- critical hit 后蓝方首次 relevant response 的延迟为 `1` step。
- 蓝方最可疑的动作规则是：`Q2_user_action_during_critical_breach`，以及 `Q4_user_focus_after_enterprise_foothold`。

## Worst Business Return

- Basic info: `episode_id=episode_008` `env_idx=3` `env_seed=3027` `risk_tier=Tier 3 Persistent Critical Breach`
- Returns: `security=-695.7000` `business=-154.7900` `cost=-21.4700`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=12` `first_relevant_blue_response=15`

Key sequence:
- step 0: Blue `DecoySvchost` -> `Op_Host0`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 4: Blue `Restore` -> `Enterprise2`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `Restore` -> `User1`; Red `ExploitRemoteService` -> `-`; new=Enterprise0; recovered=-; critical_after=-
- step 6: Blue `DecoySmss` -> `Defender`; Red `PrivilegeEscalate` -> `Enterprise0`; new=-; recovered=-; critical_after=-
- step 11: Blue `DecoyFemitter` -> `Defender`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 12: Blue `Restore` -> `User1`; Red `ExploitRemoteService` -> `-`; new=Op_Server0; recovered=-; critical_after=Op_Server0
- step 13: Blue `DecoyVsftpd` -> `User3`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 14: Blue `DecoySSHD` -> `User4`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 15: Blue `DecoyApache` -> `Enterprise0`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 16: Blue `DecoyTomcat` -> `Op_Host2`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 99: Blue `DecoyHarakaSMPT` -> `User3`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0

Conclusion:
- 最终 `Op_Server0` 仍处于 critical compromised 状态，说明该 env-run 属于持久打穿而不是短暂失守。
- 红方真正完成突破的关键节点是 step 14 对 `Op_Server0` 的 `Impact`。
- critical hit 后蓝方首次 relevant response 的延迟为 `3` step。
- 蓝方最可疑的动作规则是：`Q4_user_focus_after_enterprise_foothold`，以及 `Q2_user_action_during_critical_breach`。

## Worst Security Return

- Basic info: `episode_id=episode_004` `env_idx=3` `env_seed=3023` `risk_tier=Tier 3 Persistent Critical Breach`
- Returns: `security=-1433.0500` `business=-152.0400` `cost=-19.9500`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=12` `first_relevant_blue_response=9`

Key sequence:
- step 0: Blue `DecoySSHD` -> `User3`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 4: Blue `Restore` -> `Enterprise2`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `DecoyVsftpd` -> `Defender`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-
- step 6: Blue `DecoyHarakaSMPT` -> `User4`; Red `PrivilegeEscalate` -> `Enterprise1`; new=-; recovered=-; critical_after=-
- step 8: Blue `Sleep` -> `-`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 9: Blue `DecoyVsftpd` -> `Enterprise1`; Red `ExploitRemoteService` -> `-`; new=Enterprise2; recovered=-; critical_after=-
- step 10: Blue `DecoySvchost` -> `User0`; Red `PrivilegeEscalate` -> `Enterprise2`; new=-; recovered=-; critical_after=-
- step 11: Blue `DecoyTomcat` -> `Enterprise1`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 12: Blue `Remove` -> `User0`; Red `ExploitRemoteService` -> `-`; new=Op_Server0; recovered=-; critical_after=Op_Server0
- step 13: Blue `DecoyVsftpd` -> `User3`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 14: Blue `Analyse` -> `User4`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 99: Blue `Analyse` -> `User3`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0

Conclusion:
- 最终 `Op_Server0` 仍处于 critical compromised 状态，说明该 env-run 属于持久打穿而不是短暂失守。
- 红方真正完成突破的关键节点是 step 14 对 `Op_Server0` 的 `Impact`。
- critical hit 后蓝方首次 relevant response 的延迟为 `6` step。
- 蓝方最可疑的动作规则是：`Q3_missed_immediate_response_to_critical_hit`，以及 `Q4_user_focus_after_enterprise_foothold`。

## Max Critical Dwell

- Basic info: `episode_id=episode_002` `env_idx=0` `env_seed=21` `risk_tier=Tier 3 Persistent Critical Breach`
- Returns: `security=-1318.6000` `business=-128.4575` `cost=-20.4800`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=12` `first_relevant_blue_response=7`

Key sequence:
- step 0: Blue `DecoySSHD` -> `Defender`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 4: Blue `DecoySSHD` -> `Op_Server0`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `Restore` -> `User0`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-
- step 6: Blue `DecoyVsftpd` -> `Op_Host2`; Red `PrivilegeEscalate` -> `Enterprise1`; new=-; recovered=-; critical_after=-
- step 7: Blue `DecoyApache` -> `Enterprise0`; Red `DiscoverRemoteSystems` -> `Enterprise`; new=-; recovered=-; critical_after=-
- step 8: Blue `DecoyApache` -> `Enterprise0`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 11: Blue `DecoySvchost` -> `User4`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 12: Blue `DecoySmss` -> `User2`; Red `ExploitRemoteService` -> `-`; new=Op_Server0; recovered=-; critical_after=Op_Server0
- step 13: Blue `Restore` -> `Enterprise2`; Red `PrivilegeEscalate` -> `Op_Server0`; new=-; recovered=Enterprise2; critical_after=Op_Server0
- step 14: Blue `DecoyTomcat` -> `Defender`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 15: Blue `Restore` -> `Enterprise2`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0
- step 99: Blue `Restore` -> `User1`; Red `Impact` -> `Op_Server0`; new=-; recovered=-; critical_after=Op_Server0

Conclusion:
- 最终 `Op_Server0` 仍处于 critical compromised 状态，说明该 env-run 属于持久打穿而不是短暂失守。
- 红方真正完成突破的关键节点是 step 14 对 `Op_Server0` 的 `Impact`。
- critical hit 后蓝方首次 relevant response 的延迟为 `1` step。
- 蓝方最可疑的动作规则是：`Q2_user_action_during_critical_breach`，以及 `Q2_user_action_during_critical_breach`。

## Best Tier 0 Safe Sample

- Basic info: `episode_id=episode_002` `env_idx=1` `env_seed=1021` `risk_tier=Tier 0 Safe`
- Returns: `security=-103.0000` `business=-17.8125` `cost=-21.4600`
- Key times: `enterprise_foothold_step=None` `first_critical_hit_step=None` `first_relevant_blue_response=None`

Key sequence:
- step 0: Blue `DecoySSHD` -> `User3`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 1: Blue `DecoyVsftpd` -> `User3`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 2: Blue `DecoySmss` -> `Op_Host1`; Red `ExploitRemoteService` -> `-`; new=User3; recovered=-; critical_after=-
- step 3: Blue `DecoyHarakaSMPT` -> `Enterprise0`; Red `PrivilegeEscalate` -> `User3`; new=-; recovered=-; critical_after=-
- step 4: Blue `DecoyApache` -> `User1`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `DecoySSHD` -> `User3`; Red `ExploitRemoteService` -> `-`; new=-; recovered=-; critical_after=-
- step 6: Blue `DecoyVsftpd` -> `Op_Host2`; Red `ExploitRemoteService` -> `-`; new=-; recovered=-; critical_after=-
- step 99: Blue `DecoyVsftpd` -> `Op_Host0`; Red `ExploitRemoteService` -> `-`; new=-; recovered=-; critical_after=-

Conclusion:
- 没有发生 critical breach，但红方已经沿关键路径形成显著推进。

## Critical-Step Action Summary

### Critical-step top action families

- `decoy`: `8615` critical-present steps
- `restore`: `1991` critical-present steps
- `analyse`: `1247` critical-present steps
- `remove`: `610` critical-present steps
- `other`: `300` critical-present steps

### Critical-step recovery counts

- `Restore -> Enterprise2`: `156` recovery steps
- `Restore -> Enterprise1`: `36` recovery steps
- `Restore -> User1`: `17` recovery steps
- `Restore -> User3`: `4` recovery steps
- `Restore -> User2`: `1` recovery steps

### Critical-step no-recovery top actions

- `DecoySSHD -> User3`: `946` no-recovery steps
- `Restore -> Enterprise2`: `893` no-recovery steps
- `Analyse -> User2`: `740` no-recovery steps
- `DecoyVsftpd -> User3`: `654` no-recovery steps
- `DecoyHarakaSMPT -> Enterprise0`: `595` no-recovery steps

## Pre-critical containment summary

### Pre-critical top action families

- `decoy`: `936` pre-critical steps
- `restore`: `330` pre-critical steps
- `analyse`: `147` pre-critical steps
- `remove`: `57` pre-critical steps
- `other`: `31` pre-critical steps

### Pre-critical compromised-target recovery counts

- `Restore -> Op_Server0`: `92` containment steps
- `Restore -> Enterprise2`: `51` containment steps
- `Restore -> Enterprise1`: `4` containment steps
- `Analyse -> Enterprise1`: `2` containment steps
- `Remove -> Enterprise2`: `1` containment steps

### Pre-critical no-containment top actions

- `DecoySSHD -> User3`: `99` no-containment steps
- `Analyse -> User2`: `84` no-containment steps
- `Restore -> Enterprise2`: `71` no-containment steps
- `DecoyVsftpd -> User3`: `65` no-containment steps
- `DecoyHarakaSMPT -> Enterprise0`: `63` no-containment steps
