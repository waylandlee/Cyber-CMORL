## selected (stage2_ext_031_obj_1)

| candidate_label | policy_id | step_idx | blue_action_mode | blue_target_mode | red_action_mode | red_target_mode | newly_compromised_top_hosts | recovered_top_hosts | op_server0_compromised_rate | enterprise2_compromised_rate | impact_rate | restore_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| selected | stage2_ext_031_obj_1 | 0 | DecoySSHD | User3 | DiscoverRemoteSystems | User |  |  | 0.0 | 0.0 | 0.0 | 0.1875 |
| selected | stage2_ext_031_obj_1 | 1 | DecoyVsftpd | User3 | DiscoverNetworkServices |  |  |  | 0.0 | 0.0 | 0.0 | 0.1187 |
| selected | stage2_ext_031_obj_1 | 2 | Restore | User3 | ExploitRemoteService |  | User3(45), User2(44), User4(38) |  | 0.0 | 0.0 | 0.0 | 0.1625 |
| selected | stage2_ext_031_obj_1 | 3 | Analyse | User3 | PrivilegeEscalate | User3 | User3(2) | User1(2) | 0.0 | 0.0 | 0.0 | 0.1562 |
| selected | stage2_ext_031_obj_1 | 4 | Restore | User3 | DiscoverNetworkServices | User3 | User1(2) | User1(1) | 0.0 | 0.0 | 0.0 | 0.1938 |
| selected | stage2_ext_031_obj_1 | 5 | Restore | Enterprise2 | ExploitRemoteService | User1 | Enterprise1(69), Enterprise0(57) | User1(2) | 0.0 | 0.0 | 0.0 | 0.2437 |
| selected | stage2_ext_031_obj_1 | 6 | Restore | Enterprise2 | PrivilegeEscalate | Enterprise1 | Enterprise0(1) | User1(1) | 0.0 | 0.0 | 0.0 | 0.175 |
| selected | stage2_ext_031_obj_1 | 7 | Restore | Enterprise0 | DiscoverRemoteSystems | Enterprise | Enterprise1(2) | User1(2), Enterprise1(1) | 0.0 | 0.0 | 0.0 | 0.2 |
| selected | stage2_ext_031_obj_1 | 8 | DecoySSHD | User3 | DiscoverNetworkServices | Enterprise1 |  | User1(2), Enterprise1(1) | 0.0 | 0.0 | 0.0 | 0.1562 |
| selected | stage2_ext_031_obj_1 | 9 | DecoySSHD | User3 | ExploitRemoteService | Enterprise | Enterprise2(126), Enterprise0(7) | User1(1) | 0.0 | 0.7875 | 0.0 | 0.1437 |
| selected | stage2_ext_031_obj_1 | 10 | DecoyVsftpd | User3 | PrivilegeEscalate | Enterprise2 | Enterprise2(1) | Enterprise2(6) | 0.0 | 0.7562 | 0.0 | 0.1187 |
| selected | stage2_ext_031_obj_1 | 11 | Restore | User3 | DiscoverNetworkServices | User3 | Enterprise2(8), User3(1) | Enterprise2(9), Enterprise1(1) | 0.0 | 0.75 | 0.0 | 0.1875 |
| selected | stage2_ext_031_obj_1 | 12 | Restore | User3 | ExploitRemoteService | Enterprise2 | Op_Server0(108) | Enterprise2(8), Enterprise1(1), User3(1) | 0.675 | 0.7 | 0.0 | 0.2125 |
| selected | stage2_ext_031_obj_1 | 13 | Restore | Enterprise2 | PrivilegeEscalate | Op_Server0 | Enterprise2(9), Enterprise1(1), Enterprise0(1) | Enterprise2(14), Enterprise1(1), User1(1) | 0.6813 | 0.6687 | 0.0 | 0.1938 |
| selected | stage2_ext_031_obj_1 | 14 | DecoySSHD | User3 | Impact | Op_Server0 | Op_Server0(6) | Enterprise2(6), Enterprise1(1), Op_Server0(1) | 0.7125 | 0.6312 | 0.675 | 0.1375 |
| selected | stage2_ext_031_obj_1 | 15 | Restore | User3 | Impact | Op_Server0 | Enterprise2(1), Enterprise0(1) | Enterprise2(6), User1(3) | 0.7125 | 0.6 | 0.675 | 0.15 |
| selected | stage2_ext_031_obj_1 | 16 | Restore | User3 | Impact | Op_Server0 | Op_Server0(10), User1(1) | Enterprise2(5), Op_Server0(2) | 0.7625 | 0.5687 | 0.7125 | 0.1812 |
| selected | stage2_ext_031_obj_1 | 17 | Restore | Enterprise2 | Impact | Op_Server0 | Enterprise0(4), Enterprise2(2) | Enterprise2(9) | 0.7625 | 0.525 | 0.7 | 0.1688 |
| selected | stage2_ext_031_obj_1 | 18 | DecoySSHD | User3 | Impact | Op_Server0 | Op_Server0(3) | Enterprise2(5) | 0.7812 | 0.4938 | 0.7625 | 0.1313 |
| selected | stage2_ext_031_obj_1 | 19 | DecoySSHD | User3 | Impact | Op_Server0 | Enterprise2(2) | Enterprise2(3), User1(1), Op_Server0(1) | 0.775 | 0.4875 | 0.7625 | 0.1125 |
| selected | stage2_ext_031_obj_1 | 20 | Restore | User3 | Impact | Op_Server0 | Op_Server0(5) | Enterprise2(7), User1(1) | 0.8063 | 0.4437 | 0.775 | 0.1625 |
| selected | stage2_ext_031_obj_1 | 21 | Restore | User3 | Impact | Op_Server0 | Enterprise2(4), Enterprise0(3), Op_Server0(1) | Enterprise2(6), Op_Server0(3) | 0.7937 | 0.4313 | 0.775 | 0.2 |
| selected | stage2_ext_031_obj_1 | 22 | Restore | Enterprise2 | Impact | Op_Server0 | Op_Server0(1) | Enterprise2(8), Op_Server0(1) | 0.7937 | 0.3812 | 0.7875 | 0.1688 |
| selected | stage2_ext_031_obj_1 | 23 | DecoySSHD | User3 | Impact | Op_Server0 | Op_Server0(3), Enterprise2(2) | Enterprise2(3), Enterprise1(1) | 0.8125 | 0.375 | 0.7875 | 0.1313 |
| selected | stage2_ext_031_obj_1 | 24 | Restore | Enterprise2 | Impact | Op_Server0 | Op_Server0(7) | Enterprise2(10), Op_Server0(2), User1(1) | 0.8438 | 0.3125 | 0.7937 | 0.2 |
| selected | stage2_ext_031_obj_1 | 25 | Restore | User3 | Impact | Op_Server0 | Enterprise2(4), Enterprise0(3), Enterprise1(1) | Enterprise2(6), Op_Server0(3), Enterprise1(1) | 0.825 | 0.3 | 0.8 | 0.1938 |
| selected | stage2_ext_031_obj_1 | 26 | Restore | Enterprise2 | Impact | Op_Server0 | Op_Server0(3) | Enterprise2(6), Op_Server0(1) | 0.8375 | 0.2625 | 0.825 | 0.15 |
| selected | stage2_ext_031_obj_1 | 27 | Restore | User3 | Impact | Op_Server0 | Op_Server0(3), Enterprise2(1), Enterprise1(1) | Enterprise2(3), User1(2) | 0.8562 | 0.25 | 0.8187 | 0.1562 |
| selected | stage2_ext_031_obj_1 | 28 | DecoyHarakaSMPT | User3 | Impact | Op_Server0 | Op_Server0(4), Enterprise0(1) | Enterprise2(2), Enterprise1(1), Op_Server0(1) | 0.875 | 0.2375 | 0.8375 | 0.1437 |
| selected | stage2_ext_031_obj_1 | 29 | DecoySSHD | User3 | Impact | Op_Server0 | Enterprise2(5), Enterprise0(2) | Enterprise2(5), User1(2) | 0.875 | 0.2375 | 0.85 | 0.1562 |
| selected | stage2_ext_031_obj_1 | 30 | DecoySSHD | User3 | Impact | Op_Server0 | Op_Server0(1) | Op_Server0(1), Enterprise2(1), User1(1) | 0.875 | 0.2313 | 0.875 | 0.0875 |
| selected | stage2_ext_031_obj_1 | 31 | Restore | User3 | Impact | Op_Server0 | Enterprise2(2) | Op_Server0(5), Enterprise2(5), Enterprise1(1) | 0.8438 | 0.2125 | 0.8688 | 0.2188 |
| selected | stage2_ext_031_obj_1 | 32 | DecoySSHD | User3 | Impact | Op_Server0 | Op_Server0(6), Enterprise2(1) | Enterprise2(3), Op_Server0(3) | 0.8625 | 0.2 | 0.8438 | 0.175 |
| selected | stage2_ext_031_obj_1 | 33 | DecoyVsftpd | User3 | Impact | Op_Server0 | Op_Server0(3), Enterprise2(3) | Enterprise2(2), Op_Server0(1) | 0.875 | 0.2062 | 0.825 | 0.1313 |
| selected | stage2_ext_031_obj_1 | 34 | DecoySSHD | User3 | Impact | Op_Server0 | Op_Server0(2), Enterprise2(1) | Enterprise2(3), User1(1), Op_Server0(1) | 0.8812 | 0.1938 | 0.8562 | 0.1688 |
| selected | stage2_ext_031_obj_1 | 35 | DecoySSHD | User3 | Impact | Op_Server0 | Op_Server0(2), Enterprise2(2) | Op_Server0(2), Enterprise2(1), Enterprise1(1) | 0.8812 | 0.2 | 0.8688 | 0.15 |
| selected | stage2_ext_031_obj_1 | 36 | Restore | User3 | Impact | Op_Server0 | Op_Server0(3) | Enterprise2(3), Op_Server0(1), Enterprise1(1) | 0.8938 | 0.1812 | 0.8688 | 0.1625 |
| selected | stage2_ext_031_obj_1 | 37 | Restore | User3 | Impact | Op_Server0 | Op_Server0(3), Enterprise0(1) | Op_Server0(4), Enterprise1(1), User3(1) | 0.8875 | 0.175 | 0.875 | 0.1625 |
| selected | stage2_ext_031_obj_1 | 38 | Restore | User3 | Impact | Op_Server0 | Op_Server0(4), Enterprise2(1) | Enterprise2(2), User2(1), Enterprise1(1) | 0.9125 | 0.1688 | 0.8688 | 0.1875 |
| selected | stage2_ext_031_obj_1 | 39 | DecoySSHD | User3 | Impact | Op_Server0 | Op_Server0(4) | Op_Server0(2), Enterprise1(1) | 0.925 | 0.1688 | 0.8875 | 0.1437 |
| selected | stage2_ext_031_obj_1 | 40 | DecoySSHD | User3 | Impact | Op_Server0 | Op_Server0(1) | Op_Server0(2) | 0.9187 | 0.1688 | 0.9 | 0.1313 |
| selected | stage2_ext_031_obj_1 | 41 | Restore | User3 | Impact | Op_Server0 | Op_Server0(3), Enterprise2(1) | Op_Server0(3), Enterprise2(2), User1(1) | 0.9187 | 0.1625 | 0.9125 | 0.1875 |
| selected | stage2_ext_031_obj_1 | 42 | DecoySSHD | User3 | Impact | Op_Server0 |  |  | 0.9187 | 0.1625 | 0.9 | 0.1187 |
| selected | stage2_ext_031_obj_1 | 43 | DecoySSHD | User3 | Impact | Op_Server0 | Op_Server0(2), Enterprise2(1) | Enterprise2(6), Op_Server0(1) | 0.925 | 0.1313 | 0.9187 | 0.1812 |
| selected | stage2_ext_031_obj_1 | 44 | DecoySSHD | User3 | Impact | Op_Server0 | Op_Server0(1), Enterprise2(1) | Enterprise2(2), Op_Server0(2) | 0.9187 | 0.125 | 0.9125 | 0.1625 |
| selected | stage2_ext_031_obj_1 | 45 | Restore | User3 | Impact | Op_Server0 | Op_Server0(1) | Op_Server0(5), Enterprise2(3) | 0.8938 | 0.1062 | 0.9125 | 0.1812 |
| selected | stage2_ext_031_obj_1 | 46 | Restore | User3 | Impact | Op_Server0 | Op_Server0(3) | Enterprise1(1) | 0.9125 | 0.1062 | 0.8875 | 0.1625 |
| selected | stage2_ext_031_obj_1 | 47 | DecoySSHD | User3 | Impact | Op_Server0 | Op_Server0(3), Enterprise2(1) | Op_Server0(4), Enterprise2(1), Enterprise1(1) | 0.9062 | 0.1062 | 0.8938 | 0.1812 |
| selected | stage2_ext_031_obj_1 | 48 | DecoyVsftpd | User2 | Impact | Op_Server0 | Enterprise2(2) | Enterprise2(1), Op_Server0(1), User1(1) | 0.9 | 0.1125 | 0.8875 | 0.1062 |
| selected | stage2_ext_031_obj_1 | 49 | DecoySSHD | User3 | Impact | Op_Server0 | Op_Server0(2), Enterprise2(1), Enterprise0(1) | Enterprise2(2), Enterprise1(1), Op_Server0(1) | 0.9062 | 0.1062 | 0.9 | 0.1562 |
| selected | stage2_ext_031_obj_1 | 50 | Restore | User3 | Impact | Op_Server0 | Op_Server0(3), Enterprise2(2) | Enterprise2(1), Op_Server0(1), Enterprise1(1) | 0.9187 | 0.1125 | 0.8938 | 0.1625 |
| selected | stage2_ext_031_obj_1 | 51 | DecoyVsftpd | User2 | Impact | Op_Server0 | Op_Server0(3) | Op_Server0(1), Enterprise2(1) | 0.9313 | 0.1062 | 0.9 | 0.1375 |
| selected | stage2_ext_031_obj_1 | 52 | Restore | User3 | Impact | Op_Server0 | Enterprise2(1) |  | 0.9313 | 0.1125 | 0.9125 | 0.1688 |
| selected | stage2_ext_031_obj_1 | 53 | Restore | User3 | Impact | Op_Server0 | Enterprise2(2), Enterprise0(1) | Enterprise2(2), Op_Server0(1), User1(1) | 0.925 | 0.1125 | 0.9313 | 0.1812 |
| selected | stage2_ext_031_obj_1 | 54 | DecoySSHD | Enterprise2 | Impact | Op_Server0 | Enterprise2(2) | Op_Server0(2), Enterprise2(1) | 0.9125 | 0.1187 | 0.925 | 0.125 |
| selected | stage2_ext_031_obj_1 | 55 | Restore | Enterprise2 | Impact | Op_Server0 | Op_Server0(2) | Enterprise1(1), Enterprise2(1), Op_Server0(1) | 0.9187 | 0.1125 | 0.9125 | 0.1938 |
| selected | stage2_ext_031_obj_1 | 56 | Restore | User3 | Impact | Op_Server0 | Op_Server0(5) | Enterprise2(2), Op_Server0(2), Enterprise1(1) | 0.9375 | 0.1 | 0.9062 | 0.1688 |
| selected | stage2_ext_031_obj_1 | 57 | DecoySSHD | User3 | Impact | Op_Server0 | Op_Server0(3), Enterprise2(1), Enterprise0(1) | Op_Server0(3), Enterprise2(1) | 0.9375 | 0.1 | 0.9062 | 0.1313 |
| selected | stage2_ext_031_obj_1 | 58 | Restore | User3 | Impact | Op_Server0 | Op_Server0(1) | Op_Server0(2), Enterprise2(1) | 0.9313 | 0.0938 | 0.9187 | 0.1812 |
| selected | stage2_ext_031_obj_1 | 59 | Restore | User3 | Impact | Op_Server0 | Op_Server0(3), Enterprise2(1) | Op_Server0(2) | 0.9375 | 0.1 | 0.925 | 0.1688 |
| selected | stage2_ext_031_obj_1 | 60 | Restore | User3 | Impact | Op_Server0 | Op_Server0(3) | Op_Server0(2), Enterprise2(1) | 0.9437 | 0.0938 | 0.9187 | 0.175 |
| selected | stage2_ext_031_obj_1 | 61 | DecoySSHD | User3 | Impact | Op_Server0 | Op_Server0(2), Enterprise2(1) | Enterprise2(2), Enterprise1(1), Op_Server0(1) | 0.95 | 0.0875 | 0.925 | 0.1688 |
| selected | stage2_ext_031_obj_1 | 62 | Restore | User3 | Impact | Op_Server0 | Op_Server0(3) | Op_Server0(2), Enterprise2(1) | 0.9563 | 0.0813 | 0.9375 | 0.175 |
| selected | stage2_ext_031_obj_1 | 63 | Restore | Enterprise2 | Impact | Op_Server0 | Op_Server0(1) | Op_Server0(1), Enterprise2(1) | 0.9563 | 0.075 | 0.9375 | 0.1688 |
| selected | stage2_ext_031_obj_1 | 64 | Restore | Enterprise2 | Impact | Op_Server0 | Op_Server0(3) | Op_Server0(2), Enterprise2(1) | 0.9625 | 0.0688 | 0.95 | 0.1625 |
| selected | stage2_ext_031_obj_1 | 65 | DecoySSHD | User3 | Impact | Op_Server0 |  | Enterprise2(2), Enterprise1(1), User1(1) | 0.9625 | 0.0563 | 0.9437 | 0.15 |
| selected | stage2_ext_031_obj_1 | 66 | Restore | User3 | Impact | Op_Server0 | Op_Server0(2), Enterprise2(1) | Enterprise1(1), Enterprise2(1), User3(1) | 0.975 | 0.0563 | 0.9625 | 0.1812 |
| selected | stage2_ext_031_obj_1 | 67 | DecoyVsftpd | User3 | Impact | Op_Server0 |  |  | 0.975 | 0.0563 | 0.9625 | 0.15 |
| selected | stage2_ext_031_obj_1 | 68 | Restore | User3 | Impact | Op_Server0 |  | Op_Server0(1) | 0.9688 | 0.0563 | 0.975 | 0.2062 |
| selected | stage2_ext_031_obj_1 | 69 | Restore | User3 | Impact | Op_Server0 | Op_Server0(1) | Op_Server0(4), Enterprise2(1) | 0.95 | 0.05 | 0.9688 | 0.1938 |
| selected | stage2_ext_031_obj_1 | 70 | Restore | User3 | Impact | Op_Server0 | Op_Server0(1) | Op_Server0(1) | 0.95 | 0.05 | 0.9437 | 0.1437 |
| selected | stage2_ext_031_obj_1 | 71 | Restore | User3 | Impact | Op_Server0 | Op_Server0(3) | Enterprise2(2), Op_Server0(1) | 0.9625 | 0.0375 | 0.9437 | 0.1875 |
| selected | stage2_ext_031_obj_1 | 72 | DecoySSHD | Enterprise2 | Impact | Op_Server0 | Op_Server0(1), Enterprise2(1) | Enterprise2(1) | 0.9688 | 0.0375 | 0.9437 | 0.1812 |
| selected | stage2_ext_031_obj_1 | 73 | DecoySSHD | User3 | Impact | Op_Server0 | Op_Server0(1) | Enterprise1(1), Enterprise2(1), Op_Server0(1) | 0.9688 | 0.0312 | 0.9625 | 0.1375 |
| selected | stage2_ext_031_obj_1 | 74 | Restore | User3 | Impact | Op_Server0 |  | Op_Server0(2), Enterprise1(1) | 0.9563 | 0.0312 | 0.9625 | 0.2313 |
| selected | stage2_ext_031_obj_1 | 75 | Restore | User3 | Impact | Op_Server0 | Op_Server0(1) | Op_Server0(3) | 0.9437 | 0.0312 | 0.9563 | 0.1562 |
| selected | stage2_ext_031_obj_1 | 76 | Restore | User3 | Impact | Op_Server0 | Op_Server0(2), Enterprise2(1) |  | 0.9563 | 0.0375 | 0.9375 | 0.1875 |
| selected | stage2_ext_031_obj_1 | 77 | Restore | User3 | Impact | Op_Server0 | Op_Server0(2) | Enterprise1(3) | 0.9688 | 0.0375 | 0.9437 | 0.1812 |
| selected | stage2_ext_031_obj_1 | 78 | Restore | User3 | Impact | Op_Server0 | Enterprise2(1) | Enterprise1(2), Op_Server0(1), Enterprise2(1) | 0.9625 | 0.0375 | 0.9563 | 0.1688 |
| selected | stage2_ext_031_obj_1 | 79 | Restore | User3 | Impact | Op_Server0 | Op_Server0(1) | Enterprise2(2), Enterprise1(1) | 0.9688 | 0.025 | 0.9625 | 0.1562 |
| selected | stage2_ext_031_obj_1 | 80 | DecoySSHD | User3 | Impact | Op_Server0 |  | Op_Server0(1), Enterprise1(1) | 0.9625 | 0.025 | 0.9625 | 0.1062 |
| selected | stage2_ext_031_obj_1 | 81 | Restore | Enterprise2 | Impact | Op_Server0 | Enterprise2(1), Op_Server0(1) | Op_Server0(2) | 0.9563 | 0.0312 | 0.9625 | 0.1625 |
| selected | stage2_ext_031_obj_1 | 82 | DecoySSHD | User3 | Impact | Op_Server0 |  |  | 0.9563 | 0.0312 | 0.95 | 0.1187 |
| selected | stage2_ext_031_obj_1 | 83 | DecoySSHD | User3 | Impact | Op_Server0 | Enterprise2(1), Op_Server0(1) |  | 0.9625 | 0.0375 | 0.9563 | 0.1187 |
| selected | stage2_ext_031_obj_1 | 84 | Restore | User3 | Impact | Op_Server0 | Op_Server0(1), Enterprise2(1) | Op_Server0(2), Enterprise2(1) | 0.9563 | 0.0375 | 0.9563 | 0.1938 |
| selected | stage2_ext_031_obj_1 | 85 | Restore | User3 | Impact | Op_Server0 | Enterprise2(1) | Op_Server0(2), Enterprise2(1), Enterprise1(1) | 0.9437 | 0.0375 | 0.95 | 0.1812 |
| selected | stage2_ext_031_obj_1 | 86 | Restore | User3 | Impact | Op_Server0 |  |  | 0.9437 | 0.0375 | 0.9437 | 0.1875 |
| selected | stage2_ext_031_obj_1 | 87 | Restore | Enterprise2 | Impact | Op_Server0 | Op_Server0(3), Enterprise2(2) | Enterprise2(2) | 0.9625 | 0.0375 | 0.9437 | 0.2188 |
| selected | stage2_ext_031_obj_1 | 88 | DecoySSHD | User3 | Impact | Op_Server0 |  | Op_Server0(2), Enterprise1(1) | 0.95 | 0.0375 | 0.9437 | 0.1313 |
| selected | stage2_ext_031_obj_1 | 89 | Restore | User3 | Impact | Op_Server0 | Enterprise2(1) | Enterprise1(1), Op_Server0(1), Enterprise2(1) | 0.9437 | 0.0375 | 0.95 | 0.1938 |
| selected | stage2_ext_031_obj_1 | 90 | DecoySSHD | User3 | Impact | Op_Server0 | Op_Server0(4) | Op_Server0(1), Enterprise2(1) | 0.9625 | 0.0312 | 0.9437 | 0.1562 |
| selected | stage2_ext_031_obj_1 | 91 | Restore | User3 | Impact | Op_Server0 | Op_Server0(1), Enterprise2(1) | Op_Server0(1) | 0.9625 | 0.0375 | 0.9375 | 0.1625 |
| selected | stage2_ext_031_obj_1 | 92 | Restore | User3 | Impact | Op_Server0 | Op_Server0(2) | Op_Server0(1), User1(1) | 0.9688 | 0.0375 | 0.9563 | 0.1688 |
| selected | stage2_ext_031_obj_1 | 93 | Restore | User3 | Impact | Op_Server0 |  |  | 0.9688 | 0.0375 | 0.9563 | 0.1688 |
| selected | stage2_ext_031_obj_1 | 94 | Restore | User3 | Impact | Op_Server0 | Enterprise2(1), Op_Server0(1) | Op_Server0(2), Enterprise1(1) | 0.9625 | 0.0437 | 0.9688 | 0.1688 |
| selected | stage2_ext_031_obj_1 | 95 | DecoySSHD | User3 | Impact | Op_Server0 | Enterprise2(1) | Op_Server0(2) | 0.95 | 0.05 | 0.9563 | 0.1313 |
| selected | stage2_ext_031_obj_1 | 96 | DecoyVsftpd | User3 | Impact | Op_Server0 | Op_Server0(1) |  | 0.9563 | 0.05 | 0.95 | 0.1313 |
| selected | stage2_ext_031_obj_1 | 97 | DecoySSHD | User3 | Impact | Op_Server0 | Enterprise2(1), Op_Server0(1) | Op_Server0(1), Enterprise2(1) | 0.9563 | 0.05 | 0.95 | 0.1812 |
| selected | stage2_ext_031_obj_1 | 98 | Restore | Enterprise2 | Impact | Op_Server0 | Enterprise2(2), Op_Server0(1) | Op_Server0(1) | 0.9563 | 0.0625 | 0.95 | 0.1688 |
| selected | stage2_ext_031_obj_1 | 99 | Restore | User3 | Impact | Op_Server0 | Op_Server0(1) | Enterprise1(1), Enterprise2(1) | 0.9625 | 0.0563 | 0.95 | 0.15 |
