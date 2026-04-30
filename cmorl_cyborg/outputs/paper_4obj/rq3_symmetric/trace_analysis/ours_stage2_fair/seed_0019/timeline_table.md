## selected (stage2_ext_001_obj_0)

| candidate_label | policy_id | step_idx | blue_action_mode | blue_target_mode | red_action_mode | red_target_mode | newly_compromised_top_hosts | recovered_top_hosts | op_server0_compromised_rate | enterprise2_compromised_rate | impact_rate | restore_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| selected | stage2_ext_001_obj_0 | 0 | DecoyVsftpd | User3 | DiscoverRemoteSystems | User |  |  | 0.0 | 0.0 | 0.0 | 0.1187 |
| selected | stage2_ext_001_obj_0 | 1 | DecoyVsftpd | User3 | DiscoverNetworkServices |  |  |  | 0.0 | 0.0 | 0.0 | 0.0813 |
| selected | stage2_ext_001_obj_0 | 2 | DecoyVsftpd | User3 | ExploitRemoteService |  | User3(45), User2(45), User4(38) |  | 0.0 | 0.0 | 0.0 | 0.125 |
| selected | stage2_ext_001_obj_0 | 3 | DecoyVsftpd | User3 | PrivilegeEscalate | User3 |  |  | 0.0 | 0.0 | 0.0 | 0.1062 |
| selected | stage2_ext_001_obj_0 | 4 | DecoyVsftpd | User3 | DiscoverNetworkServices |  |  |  | 0.0 | 0.0 | 0.0 | 0.1375 |
| selected | stage2_ext_001_obj_0 | 5 | DecoyVsftpd | User3 | ExploitRemoteService |  | Enterprise1(77), Enterprise0(67) | User2(1) | 0.0 | 0.0 | 0.0 | 0.1187 |
| selected | stage2_ext_001_obj_0 | 6 | DecoyVsftpd | Enterprise0 | PrivilegeEscalate | Enterprise1 |  | Enterprise0(7) | 0.0 | 0.0 | 0.0 | 0.1437 |
| selected | stage2_ext_001_obj_0 | 7 | DecoyVsftpd | User3 | DiscoverRemoteSystems | Enterprise | Enterprise0(6) | Enterprise0(6), Enterprise1(1) | 0.0 | 0.0 | 0.0 | 0.1625 |
| selected | stage2_ext_001_obj_0 | 8 | DecoyVsftpd | User3 | DiscoverNetworkServices | Enterprise0 |  | Enterprise0(2) | 0.0 | 0.0 | 0.0 | 0.0875 |
| selected | stage2_ext_001_obj_0 | 9 | DecoyVsftpd | User3 | ExploitRemoteService | Enterprise | Enterprise2(87), Enterprise0(3) | Enterprise0(3) | 0.0 | 0.5437 | 0.0 | 0.1062 |
| selected | stage2_ext_001_obj_0 | 10 | DecoyVsftpd | User3 | PrivilegeEscalate | Enterprise2 |  | Enterprise0(3), Enterprise2(2) | 0.0 | 0.5312 | 0.0 | 0.1313 |
| selected | stage2_ext_001_obj_0 | 11 | DecoyVsftpd | User3 | DiscoverNetworkServices | Enterprise1 | Enterprise2(3), Enterprise0(2) | Enterprise2(2), Enterprise0(2) | 0.0 | 0.5375 | 0.0 | 0.0938 |
| selected | stage2_ext_001_obj_0 | 12 | DecoyVsftpd | User3 | ExploitRemoteService | Enterprise | Op_Server0(37), Enterprise0(1) | Enterprise0(3), Enterprise2(1), User3(1) | 0.2313 | 0.5312 | 0.0 | 0.1187 |
| selected | stage2_ext_001_obj_0 | 13 | DecoyVsftpd | Op_Server0 | ExploitRemoteService | Op_Server0 | Enterprise0(5), Enterprise2(4) | Enterprise0(4), Enterprise2(2), Op_Server0(1) | 0.225 | 0.5437 | 0.0 | 0.125 |
| selected | stage2_ext_001_obj_0 | 14 | DecoyVsftpd | User3 | ExploitRemoteService | Enterprise2 | Enterprise2(17), Enterprise0(3), Op_Server0(1) | Enterprise0(5), Op_Server0(1), User1(1) | 0.225 | 0.65 | 0.225 | 0.1313 |
| selected | stage2_ext_001_obj_0 | 15 | DecoyVsftpd | Enterprise0 | PrivilegeEscalate | Op_Server0 | Enterprise0(3) | Enterprise0(3), Op_Server0(2), Enterprise2(1) | 0.2125 | 0.6438 | 0.2188 | 0.15 |
| selected | stage2_ext_001_obj_0 | 16 | Restore | User3 | ExploitRemoteService | Op_Server0 | Op_Server0(11), Enterprise2(2) | Enterprise0(4), Enterprise2(1) | 0.2812 | 0.65 | 0.2125 | 0.1938 |
| selected | stage2_ext_001_obj_0 | 17 | DecoyVsftpd | User3 | ExploitRemoteService | Op_Server0 | Op_Server0(10), Enterprise0(5), Enterprise2(2) | Enterprise0(4), Enterprise2(2), User2(1) | 0.3438 | 0.65 | 0.2125 | 0.1 |
| selected | stage2_ext_001_obj_0 | 18 | DecoyVsftpd | User3 | Impact | Op_Server0 | Enterprise2(3), Enterprise0(2), Op_Server0(2) | Enterprise0(5), Enterprise2(3), Op_Server0(1) | 0.35 | 0.65 | 0.2812 | 0.1187 |
| selected | stage2_ext_001_obj_0 | 19 | DecoyVsftpd | Enterprise0 | Impact | Op_Server0 | Enterprise2(8), Enterprise0(6), Op_Server0(2) | Enterprise2(2), Enterprise0(2) | 0.3625 | 0.6875 | 0.3375 | 0.1313 |
| selected | stage2_ext_001_obj_0 | 20 | DecoyVsftpd | User3 | Impact | Op_Server0 | Op_Server0(10), Enterprise0(3) | Enterprise0(3), Enterprise2(2) | 0.425 | 0.675 | 0.35 | 0.1125 |
| selected | stage2_ext_001_obj_0 | 21 | DecoyVsftpd | Op_Server0 | Impact | Op_Server0 | Enterprise0(6), Enterprise2(1), Op_Server0(1) | Enterprise0(3), Op_Server0(2), Enterprise2(1) | 0.4188 | 0.675 | 0.3625 | 0.125 |
| selected | stage2_ext_001_obj_0 | 22 | DecoyVsftpd | Enterprise0 | Impact | Op_Server0 | Op_Server0(6), Enterprise0(1) | Enterprise0(4), Enterprise2(1) | 0.4562 | 0.6687 | 0.4125 | 0.125 |
| selected | stage2_ext_001_obj_0 | 23 | DecoyVsftpd | User3 | Impact | Op_Server0 | Enterprise2(3), Enterprise0(1), Op_Server0(1) | Enterprise0(4), Enterprise2(2) | 0.4625 | 0.675 | 0.4188 | 0.125 |
| selected | stage2_ext_001_obj_0 | 24 | DecoyVsftpd | User3 | Impact | Op_Server0 | Op_Server0(7), Enterprise2(6), Enterprise0(2) | Enterprise0(5), Enterprise2(2), Op_Server0(2) | 0.4938 | 0.7 | 0.4562 | 0.1187 |
| selected | stage2_ext_001_obj_0 | 25 | DecoyVsftpd | Op_Server0 | Impact | Op_Server0 | Enterprise0(5), Enterprise2(2), Op_Server0(2) | Enterprise2(2), Op_Server0(1), Enterprise0(1) | 0.5 | 0.7 | 0.45 | 0.1062 |
| selected | stage2_ext_001_obj_0 | 26 | DecoyVsftpd | Op_Server0 | Impact | Op_Server0 | Op_Server0(2), Enterprise2(2), Enterprise0(1) | Enterprise2(4), Enterprise0(3) | 0.5125 | 0.6875 | 0.4875 | 0.1187 |
| selected | stage2_ext_001_obj_0 | 27 | DecoyVsftpd | Enterprise0 | Impact | Op_Server0 | Enterprise0(3) | Enterprise0(5), Enterprise2(1) | 0.5125 | 0.6813 | 0.5 | 0.1375 |
| selected | stage2_ext_001_obj_0 | 28 | DecoyVsftpd | Enterprise0 | Impact | Op_Server0 | Op_Server0(6), Enterprise0(4), Enterprise2(1) | Enterprise0(2), Enterprise2(1), Op_Server0(1) | 0.5437 | 0.6813 | 0.5125 | 0.1 |
| selected | stage2_ext_001_obj_0 | 29 | DecoyVsftpd | User3 | Impact | Op_Server0 | Enterprise2(6), Op_Server0(2), Enterprise0(1) | Enterprise0(9), Enterprise2(2) | 0.5563 | 0.7063 | 0.5062 | 0.1688 |
| selected | stage2_ext_001_obj_0 | 30 | DecoyVsftpd | User3 | Impact | Op_Server0 | Enterprise0(5), Enterprise2(1) | Enterprise0(3), User2(1), Op_Server0(1) | 0.55 | 0.7125 | 0.5437 | 0.0938 |
| selected | stage2_ext_001_obj_0 | 31 | DecoyVsftpd | User3 | Impact | Op_Server0 | Op_Server0(2), Enterprise0(2), Enterprise2(1) | Enterprise2(3), Op_Server0(2), Enterprise0(2) | 0.55 | 0.7 | 0.55 | 0.1062 |
| selected | stage2_ext_001_obj_0 | 32 | DecoyVsftpd | User3 | Impact | Op_Server0 | Op_Server0(5), Enterprise2(2), Enterprise0(1) | Enterprise0(7), Enterprise2(4), Op_Server0(1) | 0.575 | 0.6875 | 0.5375 | 0.125 |
| selected | stage2_ext_001_obj_0 | 33 | DecoyVsftpd | Op_Server0 | Impact | Op_Server0 | Enterprise2(3), Op_Server0(2), Enterprise0(1) | Enterprise0(4), Enterprise2(1), Op_Server0(1) | 0.5813 | 0.7 | 0.5437 | 0.1562 |
| selected | stage2_ext_001_obj_0 | 34 | DecoyVsftpd | Enterprise0 | Impact | Op_Server0 | Enterprise2(6), Enterprise0(5), Op_Server0(2) | Enterprise0(7), Enterprise2(6), Op_Server0(2) | 0.5813 | 0.7 | 0.5687 | 0.175 |
| selected | stage2_ext_001_obj_0 | 35 | DecoyVsftpd | User3 | Impact | Op_Server0 | Enterprise0(3), Op_Server0(3) | Enterprise0(4), Op_Server0(1), Enterprise2(1) | 0.5938 | 0.6937 | 0.5687 | 0.1062 |
| selected | stage2_ext_001_obj_0 | 36 | DecoyVsftpd | User3 | Impact | Op_Server0 | Op_Server0(5), Enterprise0(2), Enterprise2(1) | Enterprise0(2), Enterprise2(2), Op_Server0(1) | 0.6188 | 0.6875 | 0.575 | 0.1125 |
| selected | stage2_ext_001_obj_0 | 37 | DecoyVsftpd | Op_Server0 | Impact | Op_Server0 | Op_Server0(7), Enterprise0(3) | Op_Server0(5), Enterprise0(2), Enterprise2(1) | 0.6312 | 0.6813 | 0.5875 | 0.1125 |
| selected | stage2_ext_001_obj_0 | 38 | DecoyVsftpd | User3 | Impact | Op_Server0 | Enterprise2(3), Enterprise0(1), Op_Server0(1) | Enterprise0(5), Op_Server0(2), User2(1) | 0.625 | 0.6937 | 0.5875 | 0.1375 |
| selected | stage2_ext_001_obj_0 | 39 | DecoyVsftpd | User3 | Impact | Op_Server0 | Enterprise0(6), Op_Server0(3), Enterprise2(2) | Op_Server0(4), Enterprise2(3), Enterprise0(1) | 0.6188 | 0.6875 | 0.6188 | 0.1 |
| selected | stage2_ext_001_obj_0 | 40 | DecoyVsftpd | User3 | Impact | Op_Server0 | Enterprise2(4), Op_Server0(2), Enterprise0(1) | Enterprise2(2), Enterprise0(2) | 0.6312 | 0.7 | 0.6 | 0.0813 |
| selected | stage2_ext_001_obj_0 | 41 | DecoyVsftpd | User3 | Impact | Op_Server0 | Op_Server0(5), Enterprise0(2) | Enterprise2(5), Op_Server0(1), Enterprise0(1) | 0.6562 | 0.6687 | 0.6188 | 0.1313 |
| selected | stage2_ext_001_obj_0 | 42 | DecoyVsftpd | User3 | Impact | Op_Server0 | Enterprise2(3), Enterprise0(2), Op_Server0(1) | Enterprise0(3), Enterprise2(1), Op_Server0(1) | 0.6562 | 0.6813 | 0.625 | 0.1187 |
| selected | stage2_ext_001_obj_0 | 43 | DecoyVsftpd | User3 | Impact | Op_Server0 | Enterprise2(3), Op_Server0(3), Enterprise0(1) | Enterprise2(3), User1(1), Enterprise0(1) | 0.675 | 0.6813 | 0.65 | 0.0938 |
| selected | stage2_ext_001_obj_0 | 44 | DecoyVsftpd | User3 | Impact | Op_Server0 | Enterprise2(2), Enterprise0(1) | Op_Server0(1) | 0.6687 | 0.6937 | 0.6562 | 0.1 |
| selected | stage2_ext_001_obj_0 | 45 | DecoyVsftpd | Enterprise0 | Impact | Op_Server0 | Op_Server0(2) | Op_Server0(4), Enterprise2(2) | 0.6562 | 0.6813 | 0.6687 | 0.1812 |
| selected | stage2_ext_001_obj_0 | 46 | DecoyVsftpd | User3 | Impact | Op_Server0 | Op_Server0(1) | Enterprise2(5), Enterprise0(1), Op_Server0(1) | 0.6562 | 0.65 | 0.6438 | 0.0938 |
| selected | stage2_ext_001_obj_0 | 47 | DecoyVsftpd | User3 | Impact | Op_Server0 | Op_Server0(2), Enterprise2(1), Enterprise0(1) | Op_Server0(3), Enterprise2(2) | 0.65 | 0.6438 | 0.65 | 0.1125 |
| selected | stage2_ext_001_obj_0 | 48 | DecoyVsftpd | User3 | Impact | Op_Server0 | Enterprise2(7), Op_Server0(3) | Enterprise2(2), Enterprise0(1) | 0.6687 | 0.675 | 0.6375 | 0.0875 |
| selected | stage2_ext_001_obj_0 | 49 | DecoyVsftpd | User3 | Impact | Op_Server0 | Op_Server0(2), Enterprise2(1) | Op_Server0(2), Enterprise0(2) | 0.6687 | 0.6813 | 0.65 | 0.0938 |
| selected | stage2_ext_001_obj_0 | 50 | DecoyVsftpd | User3 | Impact | Op_Server0 | Op_Server0(4), Enterprise2(1) | Enterprise0(4), Enterprise2(3), Enterprise1(1) | 0.6937 | 0.6687 | 0.6562 | 0.1625 |
| selected | stage2_ext_001_obj_0 | 51 | DecoyVsftpd | User3 | Impact | Op_Server0 | Op_Server0(3), Enterprise2(1) | Enterprise0(2), Enterprise2(1), Op_Server0(1) | 0.7063 | 0.6687 | 0.6687 | 0.1062 |
| selected | stage2_ext_001_obj_0 | 52 | DecoyVsftpd | Enterprise0 | Impact | Op_Server0 | Enterprise2(3), Enterprise0(1) | Enterprise0(2), Enterprise2(1) | 0.7063 | 0.6813 | 0.6875 | 0.125 |
| selected | stage2_ext_001_obj_0 | 53 | DecoyVsftpd | User3 | Impact | Op_Server0 | Op_Server0(4), Enterprise0(1), Enterprise2(1) | Enterprise2(3), Enterprise0(2), User2(1) | 0.7312 | 0.6687 | 0.7063 | 0.1313 |
| selected | stage2_ext_001_obj_0 | 54 | DecoyVsftpd | User3 | Impact | Op_Server0 | Enterprise0(2), Enterprise2(1) | Op_Server0(2), Enterprise2(2), Enterprise0(1) | 0.7188 | 0.6625 | 0.7063 | 0.0813 |
| selected | stage2_ext_001_obj_0 | 55 | DecoyVsftpd | User3 | Impact | Op_Server0 | Op_Server0(4), Enterprise2(1), Enterprise0(1) | Op_Server0(3), Enterprise2(1), Enterprise0(1) | 0.725 | 0.6625 | 0.7188 | 0.1313 |
| selected | stage2_ext_001_obj_0 | 56 | DecoyVsftpd | User3 | Impact | Op_Server0 | Enterprise0(1), Enterprise2(1), Op_Server0(1) | Enterprise2(5), Op_Server0(1) | 0.725 | 0.6375 | 0.7 | 0.125 |
| selected | stage2_ext_001_obj_0 | 57 | DecoyVsftpd | User3 | Impact | Op_Server0 | Enterprise2(2), Enterprise0(1) | Op_Server0(3), Enterprise2(2), Enterprise0(2) | 0.7063 | 0.6375 | 0.7188 | 0.1187 |
| selected | stage2_ext_001_obj_0 | 58 | DecoyVsftpd | User3 | Impact | Op_Server0 | Enterprise2(3), Op_Server0(2), Enterprise0(1) | Enterprise2(2), Op_Server0(2), Enterprise0(1) | 0.7063 | 0.6438 | 0.7063 | 0.1125 |
| selected | stage2_ext_001_obj_0 | 59 | DecoyVsftpd | User3 | Impact | Op_Server0 | Enterprise0(1), Op_Server0(1), Enterprise2(1) | Enterprise0(3), Enterprise2(3), Op_Server0(1) | 0.7063 | 0.6312 | 0.6937 | 0.175 |
| selected | stage2_ext_001_obj_0 | 60 | DecoyVsftpd | User3 | Impact | Op_Server0 | Op_Server0(5), Enterprise2(3) | Enterprise2(3) | 0.7375 | 0.6312 | 0.7 | 0.0875 |
| selected | stage2_ext_001_obj_0 | 61 | DecoyVsftpd | User3 | Impact | Op_Server0 | Op_Server0(3), Enterprise2(1) | Enterprise2(5), Enterprise0(1) | 0.7562 | 0.6062 | 0.7063 | 0.125 |
| selected | stage2_ext_001_obj_0 | 62 | DecoyVsftpd | Enterprise2 | Impact | Op_Server0 | Enterprise2(4), Op_Server0(1) | Enterprise2(4), Op_Server0(2), Enterprise0(2) | 0.75 | 0.6062 | 0.7375 | 0.125 |
| selected | stage2_ext_001_obj_0 | 63 | DecoyVsftpd | User3 | Impact | Op_Server0 | Op_Server0(5), Enterprise2(1), Enterprise0(1) | Op_Server0(3), Enterprise2(1) | 0.7625 | 0.6062 | 0.7438 | 0.1375 |
| selected | stage2_ext_001_obj_0 | 64 | DecoyVsftpd | User3 | Impact | Op_Server0 | Enterprise2(3), Op_Server0(1) | Enterprise2(2), Op_Server0(1) | 0.7625 | 0.6125 | 0.7312 | 0.0938 |
| selected | stage2_ext_001_obj_0 | 65 | DecoyVsftpd | User3 | Impact | Op_Server0 | Op_Server0(7), Enterprise2(2) | Enterprise2(2), Enterprise0(1) | 0.8063 | 0.6125 | 0.7562 | 0.1125 |
| selected | stage2_ext_001_obj_0 | 66 | DecoyVsftpd | User3 | Impact | Op_Server0 | Op_Server0(1) | Enterprise2(2), User2(1), User1(1) | 0.8125 | 0.6 | 0.7625 | 0.0563 |
| selected | stage2_ext_001_obj_0 | 67 | DecoyVsftpd | User3 | Impact | Op_Server0 | Op_Server0(2), Enterprise0(1) | Op_Server0(4), Enterprise2(2), Enterprise0(1) | 0.8 | 0.5875 | 0.8063 | 0.1437 |
| selected | stage2_ext_001_obj_0 | 68 | DecoyVsftpd | User3 | Impact | Op_Server0 | Op_Server0(2), Enterprise0(1), Enterprise2(1) | Enterprise0(3), Enterprise2(3), User2(1) | 0.8125 | 0.575 | 0.7875 | 0.1562 |
| selected | stage2_ext_001_obj_0 | 69 | DecoyVsftpd | User3 | Impact | Op_Server0 | Op_Server0(3), Enterprise0(1), Enterprise2(1) | Enterprise2(3), Enterprise0(2), Op_Server0(2) | 0.8187 | 0.5625 | 0.8 | 0.125 |
| selected | stage2_ext_001_obj_0 | 70 | DecoyVsftpd | User3 | Impact | Op_Server0 | Enterprise2(1), Op_Server0(1) | Op_Server0(2), Enterprise2(2), Enterprise0(1) | 0.8125 | 0.5563 | 0.8 | 0.1187 |
| selected | stage2_ext_001_obj_0 | 71 | DecoyVsftpd | User3 | Impact | Op_Server0 | Op_Server0(1) | Enterprise2(1), Op_Server0(1), Enterprise0(1) | 0.8125 | 0.55 | 0.8063 | 0.1625 |
| selected | stage2_ext_001_obj_0 | 72 | DecoyVsftpd | User3 | Impact | Op_Server0 | Op_Server0(2), Enterprise0(1) |  | 0.825 | 0.55 | 0.8063 | 0.0813 |
| selected | stage2_ext_001_obj_0 | 73 | DecoyVsftpd | User3 | Impact | Op_Server0 | Op_Server0(4), Enterprise2(1) | Enterprise2(3), Enterprise0(1), User2(1) | 0.85 | 0.5375 | 0.8125 | 0.0813 |
| selected | stage2_ext_001_obj_0 | 74 | DecoyVsftpd | User3 | Impact | Op_Server0 | Enterprise0(1), Op_Server0(1) | Enterprise2(2), Op_Server0(2) | 0.8438 | 0.525 | 0.825 | 0.1062 |
| selected | stage2_ext_001_obj_0 | 75 | DecoyVsftpd | User3 | Impact | Op_Server0 | Op_Server0(1) | Enterprise2(4), Op_Server0(3), Enterprise0(2) | 0.8313 | 0.5 | 0.8375 | 0.1125 |
| selected | stage2_ext_001_obj_0 | 76 | DecoyVsftpd | User3 | Impact | Op_Server0 | Enterprise2(3), Op_Server0(3), Enterprise0(1) | Enterprise2(3), Enterprise0(1) | 0.85 | 0.5 | 0.825 | 0.1062 |
| selected | stage2_ext_001_obj_0 | 77 | DecoyVsftpd | User3 | Impact | Op_Server0 | Op_Server0(3), Enterprise0(1) | Enterprise2(3), Op_Server0(2) | 0.8562 | 0.4813 | 0.8313 | 0.1062 |
| selected | stage2_ext_001_obj_0 | 78 | DecoyVsftpd | User3 | Impact | Op_Server0 | Enterprise2(3), Enterprise0(1) | Op_Server0(2), Enterprise2(1) | 0.8438 | 0.4938 | 0.8375 | 0.1187 |
| selected | stage2_ext_001_obj_0 | 79 | DecoyVsftpd | Enterprise0 | Impact | Op_Server0 | Op_Server0(2), Enterprise0(1) | Enterprise0(1), Op_Server0(1) | 0.85 | 0.4938 | 0.8438 | 0.15 |
| selected | stage2_ext_001_obj_0 | 80 | DecoyVsftpd | User3 | Impact | Op_Server0 | Op_Server0(3), Enterprise2(2) | Op_Server0(2), Enterprise1(1) | 0.8562 | 0.5062 | 0.8375 | 0.1688 |
| selected | stage2_ext_001_obj_0 | 81 | DecoyVsftpd | Enterprise0 | Impact | Op_Server0 | Op_Server0(4) | Enterprise2(3), Enterprise0(2), Op_Server0(2) | 0.8688 | 0.4875 | 0.8375 | 0.1437 |
| selected | stage2_ext_001_obj_0 | 82 | DecoyVsftpd | User3 | Impact | Op_Server0 |  | Enterprise2(3), Enterprise0(1) | 0.8688 | 0.4688 | 0.8438 | 0.125 |
| selected | stage2_ext_001_obj_0 | 83 | DecoyVsftpd | User3 | Impact | Op_Server0 | Enterprise2(3), Op_Server0(3), Enterprise0(1) | Enterprise2(2) | 0.8875 | 0.475 | 0.8688 | 0.1375 |
| selected | stage2_ext_001_obj_0 | 84 | DecoyVsftpd | User3 | Impact | Op_Server0 |  | Op_Server0(3), Enterprise2(1) | 0.8688 | 0.4688 | 0.8688 | 0.0938 |
| selected | stage2_ext_001_obj_0 | 85 | DecoyVsftpd | User3 | Impact | Op_Server0 | Enterprise2(2) | Op_Server0(3), Enterprise2(2), Enterprise0(1) | 0.85 | 0.4688 | 0.8688 | 0.175 |
| selected | stage2_ext_001_obj_0 | 86 | DecoyVsftpd | User3 | Impact | Op_Server0 | Op_Server0(2), Enterprise2(1) | Op_Server0(2) | 0.85 | 0.475 | 0.85 | 0.0813 |
| selected | stage2_ext_001_obj_0 | 87 | DecoyVsftpd | User3 | Impact | Op_Server0 | Op_Server0(2) | Enterprise2(3), Enterprise0(1), User2(1) | 0.8625 | 0.4562 | 0.8375 | 0.1688 |
| selected | stage2_ext_001_obj_0 | 88 | DecoyVsftpd | User3 | Impact | Op_Server0 | Op_Server0(2), Enterprise0(1), Enterprise2(1) | Enterprise2(3), Op_Server0(2), Enterprise0(1) | 0.8625 | 0.4437 | 0.85 | 0.1313 |
| selected | stage2_ext_001_obj_0 | 89 | DecoyVsftpd | Enterprise0 | Impact | Op_Server0 | Op_Server0(2), Enterprise2(1), Enterprise0(1) | Enterprise0(3), Enterprise2(3), Op_Server0(1) | 0.8688 | 0.4313 | 0.85 | 0.1688 |
| selected | stage2_ext_001_obj_0 | 90 | DecoyVsftpd | User3 | Impact | Op_Server0 | Op_Server0(2) | Op_Server0(4), Enterprise2(1) | 0.8562 | 0.425 | 0.8562 | 0.1625 |
| selected | stage2_ext_001_obj_0 | 91 | DecoyVsftpd | User3 | Impact | Op_Server0 | Op_Server0(3), Enterprise0(1), Enterprise2(1) | Enterprise0(1), Enterprise2(1), Op_Server0(1) | 0.8688 | 0.425 | 0.8438 | 0.0688 |
| selected | stage2_ext_001_obj_0 | 92 | DecoyVsftpd | User3 | Impact | Op_Server0 | Op_Server0(4), Enterprise2(1) | Enterprise2(1) | 0.8938 | 0.425 | 0.85 | 0.1125 |
| selected | stage2_ext_001_obj_0 | 93 | DecoyVsftpd | User3 | Impact | Op_Server0 | Enterprise2(1), Op_Server0(1) | Enterprise2(2), Op_Server0(2), Enterprise0(1) | 0.8875 | 0.4188 | 0.8688 | 0.1437 |
| selected | stage2_ext_001_obj_0 | 94 | DecoyVsftpd | User3 | Impact | Op_Server0 | Enterprise0(1) | Enterprise2(2), Op_Server0(1), User1(1) | 0.8812 | 0.4062 | 0.8812 | 0.1187 |
| selected | stage2_ext_001_obj_0 | 95 | DecoyVsftpd | User3 | Impact | Op_Server0 | Op_Server0(3) | Op_Server0(3), Enterprise0(1) | 0.8812 | 0.4062 | 0.8812 | 0.1062 |
| selected | stage2_ext_001_obj_0 | 96 | DecoyVsftpd | User3 | Impact | Op_Server0 | Op_Server0(4), Enterprise0(1) | Enterprise2(2), Op_Server0(1), Enterprise1(1) | 0.9 | 0.3937 | 0.8625 | 0.1125 |
| selected | stage2_ext_001_obj_0 | 97 | DecoyVsftpd | User3 | Impact | Op_Server0 |  | User1(1), Op_Server0(1) | 0.8938 | 0.3937 | 0.875 | 0.1187 |
| selected | stage2_ext_001_obj_0 | 98 | DecoyVsftpd | User3 | Impact | Op_Server0 | Enterprise2(1) | Op_Server0(3), Enterprise2(2), Enterprise0(1) | 0.875 | 0.3875 | 0.8938 | 0.1062 |
| selected | stage2_ext_001_obj_0 | 99 | DecoyVsftpd | Enterprise2 | Impact | Op_Server0 | Enterprise0(2), Enterprise2(1) | Enterprise2(2) | 0.875 | 0.3812 | 0.875 | 0.1062 |
