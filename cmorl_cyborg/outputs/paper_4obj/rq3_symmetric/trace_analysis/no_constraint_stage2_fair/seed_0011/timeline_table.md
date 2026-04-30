## selected (stage2_ext_022_obj_1)

| candidate_label | policy_id | step_idx | blue_action_mode | blue_target_mode | red_action_mode | red_target_mode | newly_compromised_top_hosts | recovered_top_hosts | op_server0_compromised_rate | enterprise2_compromised_rate | impact_rate | restore_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| selected | stage2_ext_022_obj_1 | 0 | DecoyFemitter | Enterprise2 | DiscoverRemoteSystems | User |  |  | 0.0 | 0.0 | 0.0 | 0.125 |
| selected | stage2_ext_022_obj_1 | 1 | DecoyFemitter | Enterprise2 | DiscoverNetworkServices |  |  |  | 0.0 | 0.0 | 0.0 | 0.1187 |
| selected | stage2_ext_022_obj_1 | 2 | DecoyFemitter | Enterprise2 | ExploitRemoteService |  | User2(41), User1(40), User3(39) |  | 0.0 | 0.0 | 0.0 | 0.1 |
| selected | stage2_ext_022_obj_1 | 3 | DecoyFemitter | Enterprise2 | PrivilegeEscalate | User2 |  |  | 0.0 | 0.0 | 0.0 | 0.1313 |
| selected | stage2_ext_022_obj_1 | 4 | DecoyFemitter | Enterprise2 | DiscoverNetworkServices |  |  | User3(1), User4(1) | 0.0 | 0.0 | 0.0 | 0.1313 |
| selected | stage2_ext_022_obj_1 | 5 | Restore | Enterprise2 | ExploitRemoteService |  | Enterprise1(81), Enterprise0(60), User2(1) |  | 0.0 | 0.0 | 0.0 | 0.1625 |
| selected | stage2_ext_022_obj_1 | 6 | DecoyFemitter | Enterprise2 | PrivilegeEscalate | Enterprise1 | User4(1) | User4(3), Enterprise1(1), Enterprise0(1) | 0.0 | 0.0 | 0.0 | 0.175 |
| selected | stage2_ext_022_obj_1 | 7 | DecoyFemitter | Enterprise2 | DiscoverRemoteSystems | Enterprise | Enterprise1(1), Enterprise0(1) | Enterprise0(2) | 0.0 | 0.0 | 0.0 | 0.1562 |
| selected | stage2_ext_022_obj_1 | 8 | DecoyHarakaSMPT | Enterprise2 | DiscoverNetworkServices | Enterprise1 | Enterprise1(1) | User4(1), Enterprise0(1) | 0.0 | 0.0 | 0.0 | 0.1062 |
| selected | stage2_ext_022_obj_1 | 9 | DecoyFemitter | Enterprise2 | ExploitRemoteService | Enterprise | Enterprise2(74), Enterprise0(2) |  | 0.0 | 0.4625 | 0.0 | 0.1 |
| selected | stage2_ext_022_obj_1 | 10 | DecoyHarakaSMPT | Enterprise2 | ExploitRemoteService | Enterprise2 | Enterprise0(2) | Enterprise2(3), Enterprise0(2), User4(1) | 0.0 | 0.4437 | 0.0 | 0.1187 |
| selected | stage2_ext_022_obj_1 | 11 | Restore | Enterprise2 | PrivilegeEscalate | Enterprise1 | Enterprise2(3) | Enterprise2(6) | 0.0 | 0.425 | 0.0 | 0.1562 |
| selected | stage2_ext_022_obj_1 | 12 | DecoyFemitter | Enterprise2 | ExploitRemoteService | Enterprise | Op_Server0(33), User2(1), Enterprise2(1) | Enterprise2(4), Enterprise0(1) | 0.2062 | 0.4062 | 0.0 | 0.15 |
| selected | stage2_ext_022_obj_1 | 13 | DecoyApache | Enterprise2 | DiscoverNetworkServices | Op_Server0 | Enterprise0(4), Enterprise2(4) | Enterprise2(4), Enterprise0(3), Op_Server0(1) | 0.2 | 0.4062 | 0.0 | 0.1562 |
| selected | stage2_ext_022_obj_1 | 14 | DecoyFemitter | Enterprise2 | ExploitRemoteService | Op_Server0 | Enterprise2(23), Op_Server0(3), Enterprise0(1) | Op_Server0(2), Enterprise0(1), Enterprise1(1) | 0.2062 | 0.55 | 0.2 | 0.075 |
| selected | stage2_ext_022_obj_1 | 15 | DecoyHarakaSMPT | Enterprise0 | PrivilegeEscalate | Op_Server0 | Enterprise1(3) | Enterprise0(4), User4(1), Op_Server0(1) | 0.2 | 0.55 | 0.1875 | 0.1313 |
| selected | stage2_ext_022_obj_1 | 16 | Restore | Enterprise2 | PrivilegeEscalate | Op_Server0 | Op_Server0(8) | Enterprise0(5), Enterprise2(3) | 0.25 | 0.5312 | 0.2 | 0.2062 |
| selected | stage2_ext_022_obj_1 | 17 | DecoyHarakaSMPT | Enterprise2 | ExploitRemoteService | Op_Server0 | Op_Server0(11), Enterprise0(7), Enterprise2(1) | Enterprise2(5), Op_Server0(2), User4(1) | 0.3063 | 0.5062 | 0.2 | 0.1938 |
| selected | stage2_ext_022_obj_1 | 18 | DecoyFemitter | Enterprise2 | PrivilegeEscalate | Op_Server0 | Enterprise2(4) | Enterprise2(4), Op_Server0(2) | 0.2938 | 0.5062 | 0.2375 | 0.1 |
| selected | stage2_ext_022_obj_1 | 19 | DecoyFemitter | Enterprise2 | ExploitRemoteService | Op_Server0 | Enterprise2(18), Op_Server0(3), Enterprise0(1) | Enterprise2(6), Op_Server0(1), Enterprise0(1) | 0.3063 | 0.5813 | 0.2938 | 0.1437 |
| selected | stage2_ext_022_obj_1 | 20 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Op_Server0(12), Enterprise2(2), Enterprise0(1) | Enterprise2(3), Op_Server0(1), Enterprise0(1) | 0.375 | 0.575 | 0.2875 | 0.1062 |
| selected | stage2_ext_022_obj_1 | 21 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Enterprise2(5), Op_Server0(4), Enterprise0(2) | Enterprise2(3), Enterprise1(1) | 0.4 | 0.5875 | 0.3 | 0.1 |
| selected | stage2_ext_022_obj_1 | 22 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Op_Server0(8), Enterprise2(1) | Enterprise2(9), Enterprise1(1), User3(1) | 0.45 | 0.5375 | 0.375 | 0.1125 |
| selected | stage2_ext_022_obj_1 | 23 | DecoyHarakaSMPT | Enterprise2 | Impact | Op_Server0 | Enterprise2(4) | Enterprise2(6), User2(1), Enterprise1(1) | 0.45 | 0.525 | 0.4 | 0.1187 |
| selected | stage2_ext_022_obj_1 | 24 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Enterprise2(11), Op_Server0(4), Enterprise0(1) | Enterprise2(6), Op_Server0(1) | 0.4688 | 0.5563 | 0.45 | 0.1375 |
| selected | stage2_ext_022_obj_1 | 25 | DecoyHarakaSMPT | Enterprise2 | Impact | Op_Server0 | Op_Server0(2), Enterprise2(1) | Enterprise2(7), Op_Server0(4), Enterprise1(1) | 0.4562 | 0.5188 | 0.4437 | 0.1625 |
| selected | stage2_ext_022_obj_1 | 26 | DecoyHarakaSMPT | Enterprise2 | Impact | Op_Server0 | Op_Server0(5), Enterprise2(2) | Enterprise2(5), Enterprise0(1) | 0.4875 | 0.5 | 0.4437 | 0.1 |
| selected | stage2_ext_022_obj_1 | 27 | DecoyApache | Enterprise2 | Impact | Op_Server0 | Op_Server0(5), Enterprise2(2) | Enterprise2(5), Enterprise0(2), Enterprise1(1) | 0.5188 | 0.4813 | 0.4562 | 0.1375 |
| selected | stage2_ext_022_obj_1 | 28 | DecoyHarakaSMPT | Enterprise2 | Impact | Op_Server0 | Enterprise2(5), Op_Server0(3) | Enterprise2(4), Op_Server0(3), Enterprise1(1) | 0.5188 | 0.4875 | 0.4875 | 0.1313 |
| selected | stage2_ext_022_obj_1 | 29 | DecoyHarakaSMPT | Enterprise2 | Impact | Op_Server0 | Enterprise2(4), Enterprise0(3), Op_Server0(2) | Enterprise2(3), User4(2), Op_Server0(1) | 0.525 | 0.4938 | 0.5 | 0.1187 |
| selected | stage2_ext_022_obj_1 | 30 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Op_Server0(5), Enterprise2(3), Enterprise1(2) | Enterprise2(4), Enterprise0(2), User2(1) | 0.55 | 0.4875 | 0.5125 | 0.1437 |
| selected | stage2_ext_022_obj_1 | 31 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Enterprise2(5), Op_Server0(4) | Enterprise2(3), Enterprise1(1), Op_Server0(1) | 0.5687 | 0.5 | 0.5188 | 0.125 |
| selected | stage2_ext_022_obj_1 | 32 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Op_Server0(3), Enterprise2(1) | Enterprise2(8), Op_Server0(3), Enterprise0(1) | 0.5687 | 0.4562 | 0.5437 | 0.15 |
| selected | stage2_ext_022_obj_1 | 33 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Enterprise0(1) | Enterprise2(3), Op_Server0(3), Enterprise0(2) | 0.55 | 0.4375 | 0.55 | 0.1187 |
| selected | stage2_ext_022_obj_1 | 34 | Restore | Enterprise2 | Impact | Op_Server0 | Op_Server0(6), Enterprise2(2) | Enterprise2(4), Op_Server0(2), User1(1) | 0.575 | 0.425 | 0.55 | 0.1812 |
| selected | stage2_ext_022_obj_1 | 35 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Enterprise2(3), Op_Server0(3), User4(1) | Enterprise2(4), Op_Server0(2), Enterprise0(1) | 0.5813 | 0.4188 | 0.5375 | 0.1562 |
| selected | stage2_ext_022_obj_1 | 36 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Op_Server0(2), Enterprise2(1) | Enterprise2(6), Enterprise1(1), Enterprise0(1) | 0.5938 | 0.3875 | 0.5625 | 0.1 |
| selected | stage2_ext_022_obj_1 | 37 | DecoyHarakaSMPT | Enterprise2 | Impact | Op_Server0 | Enterprise0(2), Op_Server0(1), Enterprise2(1) | Op_Server0(5), Enterprise2(2), Enterprise1(1) | 0.5687 | 0.3812 | 0.5813 | 0.0938 |
| selected | stage2_ext_022_obj_1 | 38 | Restore | Enterprise2 | Impact | Op_Server0 | Enterprise2(6), Enterprise0(1) | Op_Server0(3), Enterprise2(2), Enterprise1(1) | 0.55 | 0.4062 | 0.5625 | 0.1938 |
| selected | stage2_ext_022_obj_1 | 39 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Enterprise2(6), Op_Server0(5) | Enterprise2(4), Op_Server0(4), Enterprise1(2) | 0.5563 | 0.4188 | 0.55 | 0.1562 |
| selected | stage2_ext_022_obj_1 | 40 | DecoyHarakaSMPT | Enterprise2 | Impact | Op_Server0 | Enterprise2(3), Op_Server0(3) | Enterprise2(2), Op_Server0(1), Enterprise1(1) | 0.5687 | 0.425 | 0.525 | 0.1125 |
| selected | stage2_ext_022_obj_1 | 41 | DecoyHarakaSMPT | Enterprise2 | Impact | Op_Server0 | Op_Server0(7), Enterprise2(4), Enterprise0(1) | Op_Server0(3), Enterprise0(2), Enterprise2(2) | 0.5938 | 0.4375 | 0.55 | 0.1375 |
| selected | stage2_ext_022_obj_1 | 42 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Enterprise2(4), Op_Server0(3) | Enterprise2(4), Enterprise0(2), Op_Server0(2) | 0.6 | 0.4375 | 0.55 | 0.1313 |
| selected | stage2_ext_022_obj_1 | 43 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Op_Server0(4), Enterprise2(2) | Enterprise2(3), Op_Server0(2), User1(1) | 0.6125 | 0.4313 | 0.5813 | 0.1125 |
| selected | stage2_ext_022_obj_1 | 44 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Enterprise2(3), Op_Server0(3) | Enterprise0(2), Enterprise2(2), Op_Server0(1) | 0.625 | 0.4375 | 0.5875 | 0.125 |
| selected | stage2_ext_022_obj_1 | 45 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Op_Server0(5), Enterprise2(3) | Enterprise2(2), Op_Server0(2), Enterprise0(1) | 0.6438 | 0.4437 | 0.6062 | 0.0688 |
| selected | stage2_ext_022_obj_1 | 46 | DecoyHarakaSMPT | Enterprise2 | Impact | Op_Server0 | Op_Server0(3), Enterprise2(2), Enterprise1(1) | Enterprise2(5), Op_Server0(2), User3(1) | 0.65 | 0.425 | 0.6125 | 0.1375 |
| selected | stage2_ext_022_obj_1 | 47 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Op_Server0(5), Enterprise2(5) | Enterprise2(4), Op_Server0(2), User4(1) | 0.6687 | 0.4313 | 0.6312 | 0.1562 |
| selected | stage2_ext_022_obj_1 | 48 | DecoyApache | Enterprise2 | Impact | Op_Server0 | Op_Server0(3), Enterprise2(2), User4(1) | Op_Server0(2), User1(1), User2(1) | 0.675 | 0.4375 | 0.6375 | 0.1 |
| selected | stage2_ext_022_obj_1 | 49 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Op_Server0(4), Enterprise0(1) | Enterprise2(6), Op_Server0(2), Enterprise1(2) | 0.6875 | 0.4 | 0.6562 | 0.1562 |
| selected | stage2_ext_022_obj_1 | 50 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Enterprise2(4), Op_Server0(3) | Op_Server0(3), Enterprise2(1), Enterprise1(1) | 0.6875 | 0.4188 | 0.6625 | 0.125 |
| selected | stage2_ext_022_obj_1 | 51 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Op_Server0(3), Enterprise2(1) | Enterprise2(6), Enterprise0(2), Op_Server0(2) | 0.6937 | 0.3875 | 0.6687 | 0.1125 |
| selected | stage2_ext_022_obj_1 | 52 | DecoyHarakaSMPT | Enterprise2 | Impact | Op_Server0 | Enterprise2(5), Op_Server0(2) | Enterprise2(2), Op_Server0(1), Enterprise1(1) | 0.7 | 0.4062 | 0.675 | 0.0875 |
| selected | stage2_ext_022_obj_1 | 53 | DecoyHarakaSMPT | Enterprise2 | Impact | Op_Server0 | Enterprise2(5) | Enterprise2(3), Op_Server0(1), Enterprise1(1) | 0.6937 | 0.4188 | 0.6875 | 0.1 |
| selected | stage2_ext_022_obj_1 | 54 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Enterprise2(4), Op_Server0(2) | Enterprise2(2), Enterprise0(1), Op_Server0(1) | 0.7 | 0.4313 | 0.6937 | 0.1125 |
| selected | stage2_ext_022_obj_1 | 55 | DecoyHarakaSMPT | Enterprise2 | Impact | Op_Server0 | Op_Server0(2), Enterprise0(1) | Enterprise0(1), Op_Server0(1), Enterprise2(1) | 0.7063 | 0.425 | 0.6875 | 0.0813 |
| selected | stage2_ext_022_obj_1 | 56 | DecoyApache | Enterprise2 | Impact | Op_Server0 | Op_Server0(4), Enterprise0(2), Enterprise2(2) | Enterprise2(5), Op_Server0(1) | 0.725 | 0.4062 | 0.6937 | 0.1062 |
| selected | stage2_ext_022_obj_1 | 57 | DecoyHarakaSMPT | Enterprise2 | Impact | Op_Server0 | Op_Server0(6) | Enterprise2(5), Op_Server0(3), Enterprise1(2) | 0.7438 | 0.375 | 0.7 | 0.1437 |
| selected | stage2_ext_022_obj_1 | 58 | DecoyHarakaSMPT | Enterprise2 | Impact | Op_Server0 | Op_Server0(2), Enterprise2(2) | Op_Server0(2), Enterprise2(1) | 0.7438 | 0.3812 | 0.7063 | 0.1437 |
| selected | stage2_ext_022_obj_1 | 59 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Op_Server0(3), Enterprise2(1) | Enterprise2(3), Op_Server0(3), Enterprise0(2) | 0.7438 | 0.3688 | 0.7312 | 0.1313 |
| selected | stage2_ext_022_obj_1 | 60 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Enterprise2(4), Op_Server0(2), Enterprise0(1) | Op_Server0(4), Enterprise2(2), User2(1) | 0.7312 | 0.3812 | 0.725 | 0.125 |
| selected | stage2_ext_022_obj_1 | 61 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Op_Server0(3) | Op_Server0(5), Enterprise2(3), User4(1) | 0.7188 | 0.3625 | 0.7188 | 0.1688 |
| selected | stage2_ext_022_obj_1 | 62 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Op_Server0(4), Enterprise2(3) | Op_Server0(3), Enterprise2(3), Enterprise0(1) | 0.725 | 0.3625 | 0.7 | 0.1187 |
| selected | stage2_ext_022_obj_1 | 63 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Op_Server0(5), Enterprise2(2) | Op_Server0(2), Enterprise2(1), Enterprise1(1) | 0.7438 | 0.3688 | 0.7 | 0.1125 |
| selected | stage2_ext_022_obj_1 | 64 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Enterprise2(3) | Enterprise2(4), Op_Server0(3), Enterprise1(2) | 0.725 | 0.3625 | 0.7125 | 0.1437 |
| selected | stage2_ext_022_obj_1 | 65 | DecoyApache | Enterprise2 | Impact | Op_Server0 | Enterprise2(3), Op_Server0(1) | Enterprise2(3), Op_Server0(2), User3(1) | 0.7188 | 0.3625 | 0.725 | 0.1375 |
| selected | stage2_ext_022_obj_1 | 66 | DecoyHarakaSMPT | Enterprise2 | Impact | Op_Server0 | Enterprise2(3), Op_Server0(2), Enterprise1(1) | Enterprise2(7), Op_Server0(2), User2(1) | 0.7188 | 0.3375 | 0.7125 | 0.1375 |
| selected | stage2_ext_022_obj_1 | 67 | DecoyApache | User2 | Impact | Op_Server0 | Enterprise2(4), Op_Server0(3), Enterprise0(2) | Op_Server0(3), Enterprise2(2), Enterprise1(1) | 0.7188 | 0.35 | 0.7063 | 0.1 |
| selected | stage2_ext_022_obj_1 | 68 | DecoyApache | Enterprise2 | Impact | Op_Server0 | Op_Server0(3), Enterprise2(3) | Enterprise0(2), Enterprise2(2), Op_Server0(1) | 0.7312 | 0.3563 | 0.7 | 0.1313 |
| selected | stage2_ext_022_obj_1 | 69 | DecoyHarakaSMPT | Enterprise2 | Impact | Op_Server0 | Op_Server0(4), Enterprise2(2) | Op_Server0(4), Enterprise2(2), Enterprise0(1) | 0.7312 | 0.3563 | 0.7125 | 0.1437 |
| selected | stage2_ext_022_obj_1 | 70 | DecoyHarakaSMPT | Enterprise2 | Impact | Op_Server0 | Op_Server0(4), Enterprise2(3) | Op_Server0(4), Enterprise0(2), Enterprise2(2) | 0.7312 | 0.3625 | 0.7063 | 0.1313 |
| selected | stage2_ext_022_obj_1 | 71 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Op_Server0(5), User4(1) | Op_Server0(4), Enterprise2(3), Enterprise0(1) | 0.7375 | 0.3438 | 0.7063 | 0.1437 |
| selected | stage2_ext_022_obj_1 | 72 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Op_Server0(3), Enterprise2(1) | Enterprise2(5), Enterprise1(1), Enterprise0(1) | 0.7562 | 0.3187 | 0.7063 | 0.1062 |
| selected | stage2_ext_022_obj_1 | 73 | Restore | Enterprise2 | Impact | Op_Server0 | Op_Server0(3), Enterprise2(3), Enterprise0(1) | Op_Server0(4), Enterprise2(1), Enterprise0(1) | 0.75 | 0.3312 | 0.7375 | 0.15 |
| selected | stage2_ext_022_obj_1 | 74 | Restore | Enterprise2 | Impact | Op_Server0 | Enterprise2(2), Op_Server0(1) | Op_Server0(7), Enterprise2(2), Enterprise0(1) | 0.7125 | 0.3312 | 0.7312 | 0.175 |
| selected | stage2_ext_022_obj_1 | 75 | Restore | Enterprise2 | Impact | Op_Server0 | Op_Server0(6), Enterprise2(1) | Enterprise2(6), Op_Server0(4), Enterprise1(2) | 0.725 | 0.3 | 0.7063 | 0.1625 |
| selected | stage2_ext_022_obj_1 | 76 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Op_Server0(7), Enterprise2(3) | Op_Server0(3), Enterprise2(2), Enterprise0(2) | 0.75 | 0.3063 | 0.6875 | 0.15 |
| selected | stage2_ext_022_obj_1 | 77 | DecoyHarakaSMPT | Enterprise2 | Impact | Op_Server0 | Op_Server0(5), Enterprise2(4) | Enterprise1(2), Enterprise2(2), Enterprise0(1) | 0.775 | 0.3187 | 0.7063 | 0.0938 |
| selected | stage2_ext_022_obj_1 | 78 | DecoyHarakaSMPT | Enterprise2 | Impact | Op_Server0 | Enterprise2(2), Op_Server0(1), Enterprise0(1) | Op_Server0(4), Enterprise1(1), Enterprise0(1) | 0.7562 | 0.3312 | 0.7438 | 0.1125 |
| selected | stage2_ext_022_obj_1 | 79 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Enterprise2(2), Op_Server0(2) | Op_Server0(5), Enterprise2(3), Enterprise0(2) | 0.7375 | 0.325 | 0.75 | 0.1437 |
| selected | stage2_ext_022_obj_1 | 80 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Op_Server0(4), Enterprise2(1) | Op_Server0(4), Enterprise0(2), Enterprise1(1) | 0.7375 | 0.3312 | 0.725 | 0.1187 |
| selected | stage2_ext_022_obj_1 | 81 | DecoyApache | Op_Server0 | Impact | Op_Server0 | Op_Server0(7), Enterprise2(3), Enterprise0(1) | Op_Server0(2), Enterprise0(2), Enterprise2(1) | 0.7688 | 0.3438 | 0.7125 | 0.125 |
| selected | stage2_ext_022_obj_1 | 82 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Enterprise2(3), Op_Server0(1), Enterprise0(1) | Enterprise2(3), Enterprise0(1), Op_Server0(1) | 0.7688 | 0.3438 | 0.725 | 0.125 |
| selected | stage2_ext_022_obj_1 | 83 | DecoyHarakaSMPT | Enterprise2 | Impact | Op_Server0 | Enterprise2(4), Op_Server0(2) | Enterprise2(5), Op_Server0(4) | 0.7562 | 0.3375 | 0.7625 | 0.1375 |
| selected | stage2_ext_022_obj_1 | 84 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Op_Server0(1), Enterprise0(1), Enterprise2(1) | Op_Server0(5), Enterprise2(2) | 0.7312 | 0.3312 | 0.7438 | 0.125 |
| selected | stage2_ext_022_obj_1 | 85 | DecoyHarakaSMPT | Enterprise2 | Impact | Op_Server0 | Enterprise2(4), Op_Server0(2), Enterprise0(1) | Enterprise2(3), Op_Server0(2) | 0.7312 | 0.3375 | 0.725 | 0.1 |
| selected | stage2_ext_022_obj_1 | 86 | DecoyHarakaSMPT | Enterprise2 | Impact | Op_Server0 | Op_Server0(5), Enterprise2(3) | Enterprise2(3), Op_Server0(2) | 0.75 | 0.3375 | 0.7188 | 0.1375 |
| selected | stage2_ext_022_obj_1 | 87 | DecoyHarakaSMPT | Enterprise2 | Impact | Op_Server0 | Op_Server0(4), Enterprise2(3), Enterprise0(2) | Enterprise2(4), Op_Server0(1) | 0.7688 | 0.3312 | 0.7188 | 0.15 |
| selected | stage2_ext_022_obj_1 | 88 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Op_Server0(5), Enterprise2(1) | Op_Server0(3), Enterprise2(2), Enterprise1(1) | 0.7812 | 0.325 | 0.7438 | 0.125 |
| selected | stage2_ext_022_obj_1 | 89 | Restore | Enterprise2 | Impact | Op_Server0 | Op_Server0(3), Enterprise2(1) | Enterprise2(3), Op_Server0(3), Enterprise0(2) | 0.7812 | 0.3125 | 0.75 | 0.1688 |
| selected | stage2_ext_022_obj_1 | 90 | DecoyApache | Enterprise2 | Impact | Op_Server0 | Op_Server0(3), Enterprise2(2), Enterprise1(1) | Op_Server0(5), Enterprise2(4) | 0.7688 | 0.3 | 0.7625 | 0.1375 |
| selected | stage2_ext_022_obj_1 | 91 | DecoyHarakaSMPT | Enterprise2 | Impact | Op_Server0 | Enterprise2(5), Op_Server0(1) | Op_Server0(1), User4(1), Enterprise2(1) | 0.7688 | 0.325 | 0.75 | 0.1062 |
| selected | stage2_ext_022_obj_1 | 92 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Enterprise2(4), Op_Server0(3), User4(1) | Enterprise2(2), User2(1), Enterprise1(1) | 0.7812 | 0.3375 | 0.7625 | 0.1125 |
| selected | stage2_ext_022_obj_1 | 93 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Op_Server0(4), Enterprise0(1), Enterprise2(1) | Op_Server0(4), Enterprise2(4), Enterprise0(3) | 0.7812 | 0.3187 | 0.7625 | 0.1313 |
| selected | stage2_ext_022_obj_1 | 94 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Op_Server0(7), Enterprise2(1), Enterprise0(1) | Op_Server0(6), Enterprise2(1) | 0.7875 | 0.3187 | 0.7562 | 0.1313 |
| selected | stage2_ext_022_obj_1 | 95 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Op_Server0(7), Enterprise2(1) | Enterprise2(4), Op_Server0(2), Enterprise1(1) | 0.8187 | 0.3 | 0.7438 | 0.15 |
| selected | stage2_ext_022_obj_1 | 96 | DecoyHarakaSMPT | Enterprise2 | Impact | Op_Server0 | Op_Server0(7), Enterprise2(3) | Op_Server0(5), Enterprise2(1), User2(1) | 0.8313 | 0.3125 | 0.775 | 0.1187 |
| selected | stage2_ext_022_obj_1 | 97 | Restore | Enterprise2 | Impact | Op_Server0 | Enterprise2(4), Op_Server0(2) | Enterprise2(4), Op_Server0(4), User1(1) | 0.8187 | 0.3125 | 0.7875 | 0.1688 |
| selected | stage2_ext_022_obj_1 | 98 | DecoyApache | Enterprise2 | Impact | Op_Server0 | Enterprise2(3), Op_Server0(3) | Enterprise2(2), Enterprise1(1), Op_Server0(1) | 0.8313 | 0.3187 | 0.8063 | 0.1062 |
| selected | stage2_ext_022_obj_1 | 99 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Enterprise2(4), Op_Server0(1) | Op_Server0(4), Enterprise2(2), Enterprise1(2) | 0.8125 | 0.3312 | 0.8125 | 0.1062 |
