# Critical Casebook

## Earliest Critical Breach

No matching env-run was available for this case.

## Worst Business Return

- Basic info: `episode_id=episode_006` `env_idx=4` `env_seed=4025` `risk_tier=Tier 1 Near-Miss`
- Returns: `security=-172.6000` `business=-30.0850` `cost=-28.2900`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=None` `first_relevant_blue_response=6`

Key sequence:
- step 0: Blue `DecoyVsftpd` -> `Enterprise0`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 1: Blue `DecoyVsftpd` -> `Enterprise0`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 2: Blue `DecoyFemitter` -> `User4`; Red `ExploitRemoteService` -> `-`; new=User1; recovered=-; critical_after=-
- step 4: Blue `DecoyVsftpd` -> `Enterprise0`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `DecoyVsftpd` -> `Enterprise0`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-
- step 6: Blue `Restore` -> `Enterprise1`; Red `PrivilegeEscalate` -> `Enterprise1`; new=-; recovered=Enterprise1; critical_after=-
- step 7: Blue `DecoyVsftpd` -> `Enterprise0`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-
- step 99: Blue `DecoySvchost` -> `Enterprise2`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-

Conclusion:
- 没有发生 critical breach，但红方已经沿关键路径形成显著推进。
- 红方的关键推进节点是首先在 `Enterprise1` 建立 foothold。

## Worst Security Return

- Basic info: `episode_id=episode_008` `env_idx=5` `env_seed=5027` `risk_tier=Tier 1 Near-Miss`
- Returns: `security=-172.6000` `business=-29.7550` `cost=-28.0500`
- Key times: `enterprise_foothold_step=5` `first_critical_hit_step=None` `first_relevant_blue_response=6`

Key sequence:
- step 0: Blue `Analyse` -> `User0`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 1: Blue `DecoyVsftpd` -> `Enterprise0`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 2: Blue `Restore` -> `User0`; Red `ExploitRemoteService` -> `-`; new=User1; recovered=-; critical_after=-
- step 4: Blue `Analyse` -> `User2`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 5: Blue `Restore` -> `Op_Host1`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-
- step 6: Blue `Restore` -> `Enterprise1`; Red `PrivilegeEscalate` -> `Enterprise1`; new=-; recovered=Enterprise1; critical_after=-
- step 7: Blue `Analyse` -> `User2`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-
- step 99: Blue `Analyse` -> `User2`; Red `ExploitRemoteService` -> `-`; new=Enterprise1; recovered=-; critical_after=-

Conclusion:
- 没有发生 critical breach，但红方已经沿关键路径形成显著推进。
- 红方的关键推进节点是首先在 `Enterprise1` 建立 foothold。

## Max Critical Dwell

- Basic info: `episode_id=episode_000` `env_idx=0` `env_seed=19` `risk_tier=Tier 1 Near-Miss`
- Returns: `security=-140.0000` `business=-23.0500` `cost=-22.8800`
- Key times: `enterprise_foothold_step=17` `first_critical_hit_step=None` `first_relevant_blue_response=18`

Key sequence:
- step 0: Blue `Remove` -> `User2`; Red `DiscoverRemoteSystems` -> `User`; new=-; recovered=-; critical_after=-
- step 1: Blue `DecoyVsftpd` -> `Enterprise0`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 2: Blue `DecoySmss` -> `User0`; Red `ExploitRemoteService` -> `-`; new=User3; recovered=-; critical_after=-
- step 16: Blue `DecoyVsftpd` -> `Enterprise0`; Red `DiscoverNetworkServices` -> `-`; new=-; recovered=-; critical_after=-
- step 17: Blue `DecoyVsftpd` -> `Enterprise0`; Red `ExploitRemoteService` -> `-`; new=Enterprise0; recovered=-; critical_after=-
- step 18: Blue `Restore` -> `Enterprise0`; Red `PrivilegeEscalate` -> `Enterprise0`; new=-; recovered=Enterprise0; critical_after=-
- step 19: Blue `Analyse` -> `User0`; Red `ExploitRemoteService` -> `-`; new=Enterprise0; recovered=-; critical_after=-
- step 99: Blue `DecoyVsftpd` -> `Enterprise0`; Red `ExploitRemoteService` -> `-`; new=Enterprise0; recovered=-; critical_after=-

Conclusion:
- 没有发生 critical breach，但红方已经沿关键路径形成显著推进。
- 红方的关键推进节点是首先在 `Enterprise0` 建立 foothold。

## Best Tier 0 Safe Sample

No matching env-run was available for this case.

## Critical-Step Action Summary

### Critical-step top action families

- No critical-present steps were observed.

### Critical-step recovery counts

- No recovery steps were observed while `critical_present=1`.

### Critical-step no-recovery top actions

- All critical-present steps included a recovery event.

## Pre-critical containment summary

### Pre-critical top action families

- `restore`: `4945` pre-critical steps

### Pre-critical compromised-target recovery counts

- `Restore -> Enterprise1`: `3852` containment steps
- `Restore -> Enterprise0`: `1093` containment steps

### Pre-critical no-containment top actions

- All pre-critical steps focused on compromised Enterprise/Operational targets.
