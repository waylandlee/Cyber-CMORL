## selected (stage2_ext_008_obj_0)

| candidate_label | policy_id | step_idx | blue_action_mode | blue_target_mode | red_action_mode | red_target_mode | newly_compromised_top_hosts | recovered_top_hosts | op_server0_compromised_rate | enterprise2_compromised_rate | impact_rate | restore_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| selected | stage2_ext_008_obj_0 | 0 | DecoyApache | Enterprise0 | DiscoverRemoteSystems | User |  |  | 0.0 | 0.0 | 0.0 | 0.0625 |
| selected | stage2_ext_008_obj_0 | 1 | DecoyApache | Enterprise0 | DiscoverNetworkServices |  |  |  | 0.0 | 0.0 | 0.0 | 0.0625 |
| selected | stage2_ext_008_obj_0 | 2 | Sleep | User1 | ExploitRemoteService |  | User1(46), User4(41), User3(38) |  | 0.0 | 0.0 | 0.0 | 0.0563 |
| selected | stage2_ext_008_obj_0 | 3 | Analyse | Enterprise0 | PrivilegeEscalate | User1 |  | User4(1) | 0.0 | 0.0 | 0.0 | 0.0563 |
| selected | stage2_ext_008_obj_0 | 4 | DecoyApache | Enterprise0 | DiscoverNetworkServices |  | User4(1) | User4(1) | 0.0 | 0.0 | 0.0 | 0.0375 |
| selected | stage2_ext_008_obj_0 | 5 | DecoyApache | User1 | ExploitRemoteService | User4 | Enterprise1(81), Enterprise0(21) | User4(2) | 0.0 | 0.0 | 0.0 | 0.0625 |
| selected | stage2_ext_008_obj_0 | 6 | Restore | Enterprise1 | PrivilegeEscalate | Enterprise1 | User4(3) | Enterprise1(81), Enterprise0(21) | 0.0 | 0.0 | 0.0 | 0.6562 |
| selected | stage2_ext_008_obj_0 | 7 | Sleep | Enterprise0 | ExploitRemoteService | User4 | Enterprise1(81), Enterprise0(16) | User4(3) | 0.0 | 0.0 | 0.0 | 0.0625 |
| selected | stage2_ext_008_obj_0 | 8 | Restore | Enterprise1 | PrivilegeEscalate | Enterprise1 | User4(2) | Enterprise1(81), Enterprise0(16), User4(2) | 0.0 | 0.0 | 0.0 | 0.6375 |
| selected | stage2_ext_008_obj_0 | 9 | Sleep | Enterprise0 | ExploitRemoteService | User4 | Enterprise1(81), Enterprise0(33) | User4(2) | 0.0 | 0.0 | 0.0 | 0.05 |
| selected | stage2_ext_008_obj_0 | 10 | Restore | Enterprise1 | PrivilegeEscalate | Enterprise1 | User4(2) | Enterprise1(81), Enterprise0(33) | 0.0 | 0.0 | 0.0 | 0.7375 |
| selected | stage2_ext_008_obj_0 | 11 | DecoyApache | Enterprise0 | ExploitRemoteService | User3 | Enterprise1(81), Enterprise0(18) | User4(1) | 0.0 | 0.0 | 0.0 | 0.0375 |
| selected | stage2_ext_008_obj_0 | 12 | Restore | Enterprise1 | PrivilegeEscalate | Enterprise1 | User4(1) | Enterprise1(81), Enterprise0(18) | 0.0 | 0.0 | 0.0 | 0.6312 |
| selected | stage2_ext_008_obj_0 | 13 | DecoyApache | Enterprise0 | ExploitRemoteService | User4 | Enterprise1(81), Enterprise0(26) | User4(2) | 0.0 | 0.0 | 0.0 | 0.0625 |
| selected | stage2_ext_008_obj_0 | 14 | Restore | Enterprise1 | PrivilegeEscalate | Enterprise1 | User4(1) | Enterprise1(81), Enterprise0(26), User4(2) | 0.0 | 0.0 | 0.0 | 0.6875 |
| selected | stage2_ext_008_obj_0 | 15 | Sleep | Enterprise0 | ExploitRemoteService | User3 | Enterprise1(81), Enterprise0(31) | User4(3) | 0.0 | 0.0 | 0.0 | 0.05 |
| selected | stage2_ext_008_obj_0 | 16 | Restore | Enterprise1 | PrivilegeEscalate | Enterprise1 | User4(5) | Enterprise1(81), Enterprise0(31), User4(3) | 0.0 | 0.0 | 0.0 | 0.75 |
| selected | stage2_ext_008_obj_0 | 17 | DecoyApache | Enterprise0 | ExploitRemoteService | User4 | Enterprise1(81), Enterprise0(26) | User4(2) | 0.0 | 0.0 | 0.0 | 0.075 |
| selected | stage2_ext_008_obj_0 | 18 | Restore | Enterprise1 | PrivilegeEscalate | Enterprise1 | User4(6) | Enterprise1(81), Enterprise0(26) | 0.0 | 0.0 | 0.0 | 0.6937 |
| selected | stage2_ext_008_obj_0 | 19 | DecoyApache | Enterprise0 | ExploitRemoteService | User4 | Enterprise1(81), Enterprise0(28) | User4(1) | 0.0 | 0.0 | 0.0 | 0.1 |
| selected | stage2_ext_008_obj_0 | 20 | Restore | Enterprise1 | PrivilegeEscalate | Enterprise1 | User4(1) | Enterprise1(81), Enterprise0(28), User4(1) | 0.0 | 0.0 | 0.0 | 0.7 |
| selected | stage2_ext_008_obj_0 | 21 | Sleep | Enterprise0 | ExploitRemoteService | User4 | Enterprise1(81), Enterprise0(32) | User4(2) | 0.0 | 0.0 | 0.0 | 0.0437 |
| selected | stage2_ext_008_obj_0 | 22 | Restore | Enterprise1 | PrivilegeEscalate | Enterprise1 | User4(1) | Enterprise1(81), Enterprise0(32) | 0.0 | 0.0 | 0.0 | 0.7312 |
| selected | stage2_ext_008_obj_0 | 23 | Sleep | Enterprise0 | ExploitRemoteService | User4 | Enterprise1(81), Enterprise0(30) | User4(3) | 0.0 | 0.0 | 0.0 | 0.0625 |
| selected | stage2_ext_008_obj_0 | 24 | Restore | Enterprise1 | PrivilegeEscalate | Enterprise1 | User4(4) | Enterprise1(81), Enterprise0(30), User4(2) | 0.0 | 0.0 | 0.0 | 0.7375 |
| selected | stage2_ext_008_obj_0 | 25 | DecoyApache | Enterprise0 | ExploitRemoteService | User4 | Enterprise1(81), Enterprise0(34) |  | 0.0 | 0.0 | 0.0 | 0.0437 |
| selected | stage2_ext_008_obj_0 | 26 | Restore | Enterprise1 | PrivilegeEscalate | Enterprise1 | User4(2) | Enterprise1(81), Enterprise0(34) | 0.0 | 0.0 | 0.0 | 0.7188 |
| selected | stage2_ext_008_obj_0 | 27 | Sleep | Enterprise0 | ExploitRemoteService | User3 | Enterprise1(81), Enterprise0(33) | User4(5) | 0.0 | 0.0 | 0.0 | 0.0688 |
| selected | stage2_ext_008_obj_0 | 28 | Restore | Enterprise1 | PrivilegeEscalate | Enterprise1 | User4(4) | Enterprise1(81), Enterprise0(33), User4(1) | 0.0 | 0.0 | 0.0 | 0.7312 |
| selected | stage2_ext_008_obj_0 | 29 | Sleep | Enterprise0 | ExploitRemoteService | User4 | Enterprise1(81), Enterprise0(35) | User4(1) | 0.0 | 0.0 | 0.0 | 0.0375 |
| selected | stage2_ext_008_obj_0 | 30 | Restore | Enterprise1 | PrivilegeEscalate | Enterprise1 | User4(1) | Enterprise1(81), Enterprise0(35), User4(1) | 0.0 | 0.0 | 0.0 | 0.7312 |
| selected | stage2_ext_008_obj_0 | 31 | DecoyApache | Enterprise0 | ExploitRemoteService | User3 | Enterprise1(81), Enterprise0(36) | User4(2) | 0.0 | 0.0 | 0.0 | 0.0938 |
| selected | stage2_ext_008_obj_0 | 32 | Restore | Enterprise1 | PrivilegeEscalate | Enterprise1 | User4(1) | Enterprise1(81), Enterprise0(36) | 0.0 | 0.0 | 0.0 | 0.7438 |
| selected | stage2_ext_008_obj_0 | 33 | DecoyApache | Enterprise0 | ExploitRemoteService | User4 | Enterprise1(81), Enterprise0(37) | User4(3) | 0.0 | 0.0 | 0.0 | 0.075 |
| selected | stage2_ext_008_obj_0 | 34 | Restore | Enterprise1 | PrivilegeEscalate | Enterprise1 | User4(2) | Enterprise1(81), Enterprise0(37) | 0.0 | 0.0 | 0.0 | 0.7688 |
| selected | stage2_ext_008_obj_0 | 35 | Sleep | Enterprise0 | ExploitRemoteService | User3 | Enterprise1(81), Enterprise0(40) | User2(1) | 0.0 | 0.0 | 0.0 | 0.0437 |
| selected | stage2_ext_008_obj_0 | 36 | Restore | Enterprise1 | PrivilegeEscalate | Enterprise1 |  | Enterprise1(81), Enterprise0(40) | 0.0 | 0.0 | 0.0 | 0.7688 |
| selected | stage2_ext_008_obj_0 | 37 | Sleep | Enterprise0 | ExploitRemoteService | User4 | Enterprise1(81), Enterprise0(36) |  | 0.0 | 0.0 | 0.0 | 0.0312 |
| selected | stage2_ext_008_obj_0 | 38 | Restore | Enterprise1 | PrivilegeEscalate | Enterprise1 |  | Enterprise1(81), Enterprise0(36), User4(2) | 0.0 | 0.0 | 0.0 | 0.7562 |
| selected | stage2_ext_008_obj_0 | 39 | Sleep | Enterprise0 | ExploitRemoteService | User3 | Enterprise1(81), Enterprise0(39) |  | 0.0 | 0.0 | 0.0 | 0.0375 |
| selected | stage2_ext_008_obj_0 | 40 | Restore | Enterprise1 | PrivilegeEscalate | Enterprise1 | User4(1) | Enterprise1(81), Enterprise0(39), User4(1) | 0.0 | 0.0 | 0.0 | 0.7562 |
| selected | stage2_ext_008_obj_0 | 41 | DecoyApache | Enterprise0 | ExploitRemoteService | User4 | Enterprise1(81), Enterprise0(42) | User4(2) | 0.0 | 0.0 | 0.0 | 0.05 |
| selected | stage2_ext_008_obj_0 | 42 | Restore | Enterprise1 | PrivilegeEscalate | Enterprise1 | User4(3) | Enterprise1(81), Enterprise0(42) | 0.0 | 0.0 | 0.0 | 0.7688 |
| selected | stage2_ext_008_obj_0 | 43 | DecoyApache | Enterprise0 | ExploitRemoteService | User3 | Enterprise1(81), Enterprise0(41) | User4(2) | 0.0 | 0.0 | 0.0 | 0.075 |
| selected | stage2_ext_008_obj_0 | 44 | Restore | Enterprise1 | PrivilegeEscalate | Enterprise1 | User4(1) | Enterprise1(81), Enterprise0(41) | 0.0 | 0.0 | 0.0 | 0.7688 |
| selected | stage2_ext_008_obj_0 | 45 | DecoyApache | Enterprise0 | ExploitRemoteService | User4 | Enterprise1(81), Enterprise0(50) | User4(2) | 0.0 | 0.0 | 0.0 | 0.0437 |
| selected | stage2_ext_008_obj_0 | 46 | Restore | Enterprise1 | PrivilegeEscalate | Enterprise1 |  | Enterprise1(81), Enterprise0(50) | 0.0 | 0.0 | 0.0 | 0.8375 |
| selected | stage2_ext_008_obj_0 | 47 | Sleep | Enterprise0 | ExploitRemoteService | User3 | Enterprise1(81), Enterprise0(50) | User4(1) | 0.0 | 0.0 | 0.0 | 0.0938 |
| selected | stage2_ext_008_obj_0 | 48 | Restore | Enterprise1 | PrivilegeEscalate | Enterprise1 |  | Enterprise1(81), Enterprise0(50) | 0.0 | 0.0 | 0.0 | 0.8313 |
| selected | stage2_ext_008_obj_0 | 49 | Sleep | Enterprise0 | ExploitRemoteService | User4 | Enterprise1(81), Enterprise0(47) |  | 0.0 | 0.0 | 0.0 | 0.0625 |
| selected | stage2_ext_008_obj_0 | 50 | Restore | Enterprise1 | PrivilegeEscalate | Enterprise1 |  | Enterprise1(81), Enterprise0(47) | 0.0 | 0.0 | 0.0 | 0.8187 |
| selected | stage2_ext_008_obj_0 | 51 | Sleep | User1 | ExploitRemoteService | User3 | Enterprise1(81), Enterprise0(49) |  | 0.0 | 0.0 | 0.0 | 0.0625 |
| selected | stage2_ext_008_obj_0 | 52 | Restore | Enterprise1 | PrivilegeEscalate | Enterprise1 |  | Enterprise1(81), Enterprise0(49) | 0.0 | 0.0 | 0.0 | 0.8125 |
| selected | stage2_ext_008_obj_0 | 53 | Sleep | Enterprise0 | ExploitRemoteService | User4 | Enterprise1(81), Enterprise0(49) | User4(1) | 0.0 | 0.0 | 0.0 | 0.0563 |
| selected | stage2_ext_008_obj_0 | 54 | Restore | Enterprise1 | PrivilegeEscalate | Enterprise1 |  | Enterprise1(81), Enterprise0(49) | 0.0 | 0.0 | 0.0 | 0.825 |
| selected | stage2_ext_008_obj_0 | 55 | DecoyApache | Enterprise0 | ExploitRemoteService | User3 | Enterprise1(81), Enterprise0(50) |  | 0.0 | 0.0 | 0.0 | 0.0 |
| selected | stage2_ext_008_obj_0 | 56 | Restore | Enterprise1 | PrivilegeEscalate | Enterprise1 |  | Enterprise1(81), Enterprise0(50) | 0.0 | 0.0 | 0.0 | 0.825 |
| selected | stage2_ext_008_obj_0 | 57 | Sleep | Enterprise0 | ExploitRemoteService | User3 | Enterprise1(81), Enterprise0(57) | User4(1) | 0.0 | 0.0 | 0.0 | 0.0625 |
| selected | stage2_ext_008_obj_0 | 58 | Restore | Enterprise1 | PrivilegeEscalate | Enterprise1 | User4(1) | Enterprise1(81), Enterprise0(57) | 0.0 | 0.0 | 0.0 | 0.8625 |
| selected | stage2_ext_008_obj_0 | 59 | DecoyApache | Enterprise0 | ExploitRemoteService | User3 | Enterprise1(81), Enterprise0(57) | User4(2) | 0.0 | 0.0 | 0.0 | 0.1 |
| selected | stage2_ext_008_obj_0 | 60 | Restore | Enterprise1 | PrivilegeEscalate | Enterprise1 |  | Enterprise1(81), Enterprise0(57) | 0.0 | 0.0 | 0.0 | 0.875 |
| selected | stage2_ext_008_obj_0 | 61 | Sleep | Enterprise0 | ExploitRemoteService | User4 | Enterprise1(81), Enterprise0(53) | User4(2) | 0.0 | 0.0 | 0.0 | 0.0625 |
| selected | stage2_ext_008_obj_0 | 62 | Restore | Enterprise1 | PrivilegeEscalate | Enterprise1 |  | Enterprise1(81), Enterprise0(53) | 0.0 | 0.0 | 0.0 | 0.8375 |
| selected | stage2_ext_008_obj_0 | 63 | DecoyApache | Enterprise0 | ExploitRemoteService | User3 | Enterprise1(81), Enterprise0(55) |  | 0.0 | 0.0 | 0.0 | 0.0375 |
| selected | stage2_ext_008_obj_0 | 64 | Restore | Enterprise1 | PrivilegeEscalate | Enterprise1 |  | Enterprise1(81), Enterprise0(55), User4(1) | 0.0 | 0.0 | 0.0 | 0.8625 |
| selected | stage2_ext_008_obj_0 | 65 | DecoyApache | Enterprise0 | ExploitRemoteService | User4 | Enterprise1(81), Enterprise0(54) | User4(1) | 0.0 | 0.0 | 0.0 | 0.0813 |
| selected | stage2_ext_008_obj_0 | 66 | Restore | Enterprise1 | PrivilegeEscalate | Enterprise1 | User4(2) | Enterprise1(81), Enterprise0(54), User4(2) | 0.0 | 0.0 | 0.0 | 0.8625 |
| selected | stage2_ext_008_obj_0 | 67 | DecoyApache | Enterprise0 | ExploitRemoteService | User3 | Enterprise1(81), Enterprise0(54) |  | 0.0 | 0.0 | 0.0 | 0.05 |
| selected | stage2_ext_008_obj_0 | 68 | Restore | Enterprise1 | PrivilegeEscalate | Enterprise1 | User4(1) | Enterprise1(81), Enterprise0(54), User4(1) | 0.0 | 0.0 | 0.0 | 0.8625 |
| selected | stage2_ext_008_obj_0 | 69 | DecoyApache | Enterprise0 | ExploitRemoteService | User4 | Enterprise1(81), Enterprise0(58) |  | 0.0 | 0.0 | 0.0 | 0.0688 |
| selected | stage2_ext_008_obj_0 | 70 | Restore | Enterprise1 | PrivilegeEscalate | Enterprise1 | User4(1) | Enterprise1(81), Enterprise0(58) | 0.0 | 0.0 | 0.0 | 0.875 |
| selected | stage2_ext_008_obj_0 | 71 | DecoyApache | Enterprise0 | ExploitRemoteService | User3 | Enterprise1(81), Enterprise0(58) |  | 0.0 | 0.0 | 0.0 | 0.05 |
| selected | stage2_ext_008_obj_0 | 72 | Restore | Enterprise1 | PrivilegeEscalate | Enterprise1 | User4(1) | Enterprise1(81), Enterprise0(58) | 0.0 | 0.0 | 0.0 | 0.9 |
| selected | stage2_ext_008_obj_0 | 73 | Sleep | Enterprise0 | ExploitRemoteService | User4 | Enterprise1(81), Enterprise0(59) | User4(1) | 0.0 | 0.0 | 0.0 | 0.075 |
| selected | stage2_ext_008_obj_0 | 74 | Restore | Enterprise1 | PrivilegeEscalate | Enterprise1 |  | Enterprise1(81), Enterprise0(59) | 0.0 | 0.0 | 0.0 | 0.875 |
| selected | stage2_ext_008_obj_0 | 75 | DecoyApache | Enterprise0 | ExploitRemoteService | User3 | Enterprise1(81), Enterprise0(58) | User4(4) | 0.0 | 0.0 | 0.0 | 0.0813 |
| selected | stage2_ext_008_obj_0 | 76 | Restore | Enterprise1 | PrivilegeEscalate | Enterprise1 | User4(3) | Enterprise1(81), Enterprise0(58) | 0.0 | 0.0 | 0.0 | 0.875 |
| selected | stage2_ext_008_obj_0 | 77 | DecoyApache | Enterprise0 | ExploitRemoteService | User4 | Enterprise1(81), Enterprise0(57) |  | 0.0 | 0.0 | 0.0 | 0.0688 |
| selected | stage2_ext_008_obj_0 | 78 | Restore | Enterprise1 | PrivilegeEscalate | Enterprise1 |  | Enterprise1(81), Enterprise0(57), User4(1) | 0.0 | 0.0 | 0.0 | 0.8688 |
| selected | stage2_ext_008_obj_0 | 79 | DecoyApache | Enterprise0 | ExploitRemoteService | User3 | Enterprise1(81), Enterprise0(57) | User4(1) | 0.0 | 0.0 | 0.0 | 0.0563 |
| selected | stage2_ext_008_obj_0 | 80 | Restore | Enterprise1 | PrivilegeEscalate | Enterprise1 | User4(2) | Enterprise1(81), Enterprise0(57) | 0.0 | 0.0 | 0.0 | 0.8625 |
| selected | stage2_ext_008_obj_0 | 81 | DecoyApache | User1 | ExploitRemoteService | User4 | Enterprise1(81), Enterprise0(57) | User4(2) | 0.0 | 0.0 | 0.0 | 0.0375 |
| selected | stage2_ext_008_obj_0 | 82 | Restore | Enterprise1 | PrivilegeEscalate | Enterprise1 | User4(1) | Enterprise1(81), Enterprise0(57) | 0.0 | 0.0 | 0.0 | 0.875 |
| selected | stage2_ext_008_obj_0 | 83 | Sleep | Enterprise0 | ExploitRemoteService | User3 | Enterprise1(81), Enterprise0(59) |  | 0.0 | 0.0 | 0.0 | 0.0437 |
| selected | stage2_ext_008_obj_0 | 84 | Restore | Enterprise1 | PrivilegeEscalate | Enterprise1 |  | Enterprise1(81), Enterprise0(59) | 0.0 | 0.0 | 0.0 | 0.8812 |
| selected | stage2_ext_008_obj_0 | 85 | DecoyApache | Enterprise0 | ExploitRemoteService | User4 | Enterprise1(81), Enterprise0(59) |  | 0.0 | 0.0 | 0.0 | 0.075 |
| selected | stage2_ext_008_obj_0 | 86 | Restore | Enterprise1 | PrivilegeEscalate | Enterprise1 | User4(1) | Enterprise1(81), Enterprise0(59) | 0.0 | 0.0 | 0.0 | 0.8812 |
| selected | stage2_ext_008_obj_0 | 87 | Sleep | User1 | ExploitRemoteService | User3 | Enterprise1(81), Enterprise0(59) | User4(1) | 0.0 | 0.0 | 0.0 | 0.0437 |
| selected | stage2_ext_008_obj_0 | 88 | Restore | Enterprise1 | PrivilegeEscalate | Enterprise1 |  | Enterprise1(81), Enterprise0(59) | 0.0 | 0.0 | 0.0 | 0.875 |
| selected | stage2_ext_008_obj_0 | 89 | DecoyApache | Enterprise0 | ExploitRemoteService | User4 | Enterprise1(81), Enterprise0(58) | User4(2) | 0.0 | 0.0 | 0.0 | 0.0625 |
| selected | stage2_ext_008_obj_0 | 90 | Restore | Enterprise1 | PrivilegeEscalate | Enterprise1 | User4(3) | Enterprise1(81), Enterprise0(58) | 0.0 | 0.0 | 0.0 | 0.8688 |
| selected | stage2_ext_008_obj_0 | 91 | DecoyApache | Enterprise0 | ExploitRemoteService | User4 | Enterprise1(81), Enterprise0(60) |  | 0.0 | 0.0 | 0.0 | 0.05 |
| selected | stage2_ext_008_obj_0 | 92 | Restore | Enterprise1 | PrivilegeEscalate | Enterprise1 |  | Enterprise1(81), Enterprise0(60) | 0.0 | 0.0 | 0.0 | 0.8875 |
| selected | stage2_ext_008_obj_0 | 93 | Sleep | Enterprise0 | ExploitRemoteService | User4 | Enterprise1(81), Enterprise0(62) | User4(1) | 0.0 | 0.0 | 0.0 | 0.0437 |
| selected | stage2_ext_008_obj_0 | 94 | Restore | Enterprise1 | PrivilegeEscalate | Enterprise1 |  | Enterprise1(81), Enterprise0(62) | 0.0 | 0.0 | 0.0 | 0.9 |
| selected | stage2_ext_008_obj_0 | 95 | Sleep | User1 | ExploitRemoteService | User4 | Enterprise1(81), Enterprise0(61) | User4(3) | 0.0 | 0.0 | 0.0 | 0.0688 |
| selected | stage2_ext_008_obj_0 | 96 | Restore | Enterprise1 | PrivilegeEscalate | Enterprise1 | User4(3) | Enterprise1(81), Enterprise0(61) | 0.0 | 0.0 | 0.0 | 0.8875 |
| selected | stage2_ext_008_obj_0 | 97 | DecoyApache | Enterprise0 | ExploitRemoteService | User4 | Enterprise1(81), Enterprise0(62) | User4(1) | 0.0 | 0.0 | 0.0 | 0.0563 |
| selected | stage2_ext_008_obj_0 | 98 | Restore | Enterprise1 | PrivilegeEscalate | Enterprise1 | User4(1) | Enterprise1(81), Enterprise0(62) | 0.0 | 0.0 | 0.0 | 0.8938 |
| selected | stage2_ext_008_obj_0 | 99 | Sleep | Enterprise0 | ExploitRemoteService | User3 | Enterprise1(81), Enterprise0(63) |  | 0.0 | 0.0 | 0.0 | 0.025 |
