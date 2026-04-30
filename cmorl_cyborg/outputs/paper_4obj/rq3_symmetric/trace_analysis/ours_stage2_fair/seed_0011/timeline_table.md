## selected (stage2_ext_016_obj_0)

| candidate_label | policy_id | step_idx | blue_action_mode | blue_target_mode | red_action_mode | red_target_mode | newly_compromised_top_hosts | recovered_top_hosts | op_server0_compromised_rate | enterprise2_compromised_rate | impact_rate | restore_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| selected | stage2_ext_016_obj_0 | 0 | Restore | Op_Server0 | DiscoverRemoteSystems | User |  |  | 0.0 | 0.0 | 0.0 | 0.1875 |
| selected | stage2_ext_016_obj_0 | 1 | DecoySmss | Op_Server0 | DiscoverNetworkServices |  |  |  | 0.0 | 0.0 | 0.0 | 0.1688 |
| selected | stage2_ext_016_obj_0 | 2 | DecoySmss | Op_Server0 | ExploitRemoteService |  | User3(43), User2(40), User1(37) |  | 0.0 | 0.0 | 0.0 | 0.15 |
| selected | stage2_ext_016_obj_0 | 3 | DecoyVsftpd | Enterprise2 | PrivilegeEscalate | User3 |  |  | 0.0 | 0.0 | 0.0 | 0.175 |
| selected | stage2_ext_016_obj_0 | 4 | Restore | Op_Server0 | DiscoverNetworkServices |  | User4(1) | User4(1) | 0.0 | 0.0 | 0.0 | 0.1562 |
| selected | stage2_ext_016_obj_0 | 5 | Restore | Enterprise2 | ExploitRemoteService | User4 | Enterprise1(77), Enterprise0(74), User3(1) | User4(1) | 0.0 | 0.0 | 0.0 | 0.2062 |
| selected | stage2_ext_016_obj_0 | 6 | DecoySmss | Enterprise2 | PrivilegeEscalate | Enterprise1 |  | Enterprise0(3), Enterprise1(2) | 0.0 | 0.0 | 0.0 | 0.1625 |
| selected | stage2_ext_016_obj_0 | 7 | Restore | Op_Server0 | DiscoverRemoteSystems | Enterprise | Enterprise0(4), Enterprise1(2) | Enterprise0(4), User1(2) | 0.0 | 0.0 | 0.0 | 0.2062 |
| selected | stage2_ext_016_obj_0 | 8 | Restore | Op_Server0 | DiscoverNetworkServices | Enterprise0 | Enterprise0(1), Enterprise1(1) | Enterprise0(4) | 0.0 | 0.0 | 0.0 | 0.1625 |
| selected | stage2_ext_016_obj_0 | 9 | Restore | Enterprise2 | ExploitRemoteService | Enterprise | Enterprise2(145), User4(1), User2(1) |  | 0.0 | 0.9062 | 0.0 | 0.1625 |
| selected | stage2_ext_016_obj_0 | 10 | Restore | Enterprise2 | PrivilegeEscalate | Enterprise2 | User2(2) | Enterprise2(9), Enterprise0(3) | 0.0 | 0.85 | 0.0 | 0.1562 |
| selected | stage2_ext_016_obj_0 | 11 | Restore | Op_Server0 | DiscoverNetworkServices | User2 | Enterprise2(15) | Enterprise2(9), Enterprise0(3), Enterprise1(1) | 0.0 | 0.8875 | 0.0 | 0.1812 |
| selected | stage2_ext_016_obj_0 | 12 | Restore | Enterprise2 | ExploitRemoteService | Enterprise2 | Op_Server0(74), Enterprise2(2), Enterprise0(1) | Enterprise2(10), Enterprise0(1) | 0.4625 | 0.8375 | 0.0 | 0.1812 |
| selected | stage2_ext_016_obj_0 | 13 | Restore | Enterprise2 | PrivilegeEscalate | Op_Server0 | Enterprise2(9), Enterprise1(2), Enterprise0(1) | Enterprise2(7), Enterprise0(5), Op_Server0(1) | 0.4562 | 0.85 | 0.0 | 0.2125 |
| selected | stage2_ext_016_obj_0 | 14 | Restore | Op_Server0 | Impact | Op_Server0 | Op_Server0(8), Enterprise2(1), Enterprise1(1) | Enterprise2(9), Enterprise0(4), Op_Server0(3) | 0.4875 | 0.8 | 0.4562 | 0.2062 |
| selected | stage2_ext_016_obj_0 | 15 | Restore | Op_Server0 | Impact | Op_Server0 | Enterprise2(3), Op_Server0(1) | Enterprise0(4), Op_Server0(4), Enterprise2(2) | 0.4688 | 0.8063 | 0.4375 | 0.225 |
| selected | stage2_ext_016_obj_0 | 16 | Restore | Op_Server0 | Impact | Op_Server0 | Op_Server0(25), Enterprise2(2) | Enterprise2(9), Enterprise0(5), Op_Server0(5) | 0.5938 | 0.7625 | 0.4625 | 0.225 |
| selected | stage2_ext_016_obj_0 | 17 | Restore | Op_Server0 | Impact | Op_Server0 | Enterprise2(6), Op_Server0(4) | Op_Server0(7), Enterprise2(5), Enterprise0(1) | 0.575 | 0.7688 | 0.4375 | 0.2062 |
| selected | stage2_ext_016_obj_0 | 18 | DecoyVsftpd | Enterprise2 | Impact | Op_Server0 | Op_Server0(8), Enterprise2(1) | Enterprise2(6), Op_Server0(4), User2(1) | 0.6 | 0.7375 | 0.55 | 0.1562 |
| selected | stage2_ext_016_obj_0 | 19 | Restore | Op_Server0 | Impact | Op_Server0 | Op_Server0(8), Enterprise2(3) | Enterprise2(7), Op_Server0(5), Enterprise0(4) | 0.6188 | 0.7125 | 0.55 | 0.1875 |
| selected | stage2_ext_016_obj_0 | 20 | Restore | Enterprise2 | Impact | Op_Server0 | Op_Server0(13) | Enterprise2(10), Op_Server0(8), Enterprise0(1) | 0.65 | 0.65 | 0.5687 | 0.1812 |
| selected | stage2_ext_016_obj_0 | 21 | Restore | Op_Server0 | Impact | Op_Server0 | Op_Server0(7), Enterprise2(6) | Enterprise2(6), Op_Server0(4), Enterprise1(1) | 0.6687 | 0.65 | 0.5687 | 0.1688 |
| selected | stage2_ext_016_obj_0 | 22 | Restore | Enterprise2 | Impact | Op_Server0 | Op_Server0(11) | Enterprise2(12), Op_Server0(2), Enterprise0(2) | 0.725 | 0.575 | 0.625 | 0.1625 |
| selected | stage2_ext_016_obj_0 | 23 | Restore | Op_Server0 | Impact | Op_Server0 | Enterprise2(6), Op_Server0(3) | Enterprise2(6), Enterprise0(3), Op_Server0(1) | 0.7375 | 0.575 | 0.6562 | 0.1688 |
| selected | stage2_ext_016_obj_0 | 24 | Restore | Op_Server0 | Impact | Op_Server0 | Op_Server0(7) | Op_Server0(5), Enterprise2(4), Enterprise0(2) | 0.75 | 0.55 | 0.7188 | 0.175 |
| selected | stage2_ext_016_obj_0 | 25 | Restore | Op_Server0 | Impact | Op_Server0 | Enterprise2(4), Op_Server0(2) | Op_Server0(10), Enterprise2(6), Enterprise1(1) | 0.7 | 0.5375 | 0.7063 | 0.2188 |
| selected | stage2_ext_016_obj_0 | 26 | DecoySmss | Enterprise2 | Impact | Op_Server0 | Op_Server0(4) | Enterprise2(6), Op_Server0(3), User1(1) | 0.7063 | 0.5 | 0.6875 | 0.1375 |
| selected | stage2_ext_016_obj_0 | 27 | Restore | Op_Server0 | Impact | Op_Server0 | Op_Server0(8), Enterprise2(6) | Enterprise2(6), Op_Server0(4), Enterprise0(3) | 0.7312 | 0.5 | 0.6813 | 0.2313 |
| selected | stage2_ext_016_obj_0 | 28 | DecoyVsftpd | Enterprise2 | Impact | Op_Server0 | Op_Server0(6), Enterprise2(1) | Enterprise2(6), Op_Server0(4), Enterprise0(2) | 0.7438 | 0.4688 | 0.6813 | 0.175 |
| selected | stage2_ext_016_obj_0 | 29 | Restore | Op_Server0 | Impact | Op_Server0 | Enterprise2(6), Op_Server0(1) | Enterprise0(2), Op_Server0(2), Enterprise2(1) | 0.7375 | 0.5 | 0.7063 | 0.2062 |
| selected | stage2_ext_016_obj_0 | 30 | Restore | Enterprise2 | Impact | Op_Server0 | Op_Server0(7), Enterprise2(2) | Enterprise2(10), Op_Server0(3), Enterprise0(1) | 0.7625 | 0.45 | 0.7312 | 0.2062 |
| selected | stage2_ext_016_obj_0 | 31 | Restore | Enterprise2 | Impact | Op_Server0 | Enterprise2(6), Op_Server0(5) | Op_Server0(6), Enterprise2(3), User1(1) | 0.7562 | 0.4688 | 0.7188 | 0.2188 |
| selected | stage2_ext_016_obj_0 | 32 | Restore | Enterprise2 | Impact | Op_Server0 | Op_Server0(10) | Enterprise2(6), Op_Server0(5), Enterprise0(1) | 0.7875 | 0.4313 | 0.725 | 0.1812 |
| selected | stage2_ext_016_obj_0 | 33 | DecoySmss | Op_Server0 | Impact | Op_Server0 | Op_Server0(6), Enterprise2(2), Enterprise0(1) | Op_Server0(7), Enterprise2(6), Enterprise1(1) | 0.7812 | 0.4062 | 0.725 | 0.1625 |
| selected | stage2_ext_016_obj_0 | 34 | Restore | Op_Server0 | Impact | Op_Server0 | Op_Server0(4), Enterprise2(2) | Op_Server0(6), Enterprise2(4), Enterprise1(3) | 0.7688 | 0.3937 | 0.7438 | 0.2313 |
| selected | stage2_ext_016_obj_0 | 35 | Restore | Enterprise2 | Impact | Op_Server0 | Enterprise2(5), Op_Server0(4) | Op_Server0(6), Enterprise2(4), Enterprise1(1) | 0.7562 | 0.4 | 0.7438 | 0.1875 |
| selected | stage2_ext_016_obj_0 | 36 | Restore | Op_Server0 | Impact | Op_Server0 | Op_Server0(7), Enterprise2(3) | Op_Server0(6), Enterprise2(3), User4(1) | 0.7625 | 0.4 | 0.7312 | 0.1688 |
| selected | stage2_ext_016_obj_0 | 37 | DecoyVsftpd | Op_Server0 | Impact | Op_Server0 | Op_Server0(7), Enterprise2(2) | Op_Server0(8), Enterprise2(1) | 0.7562 | 0.4062 | 0.7188 | 0.1313 |
| selected | stage2_ext_016_obj_0 | 38 | Restore | Op_Server0 | Impact | Op_Server0 | Op_Server0(7), Enterprise2(2) | Op_Server0(8), Enterprise2(4), Enterprise1(1) | 0.75 | 0.3937 | 0.7125 | 0.2437 |
| selected | stage2_ext_016_obj_0 | 39 | Restore | Enterprise2 | Impact | Op_Server0 | Op_Server0(7), Enterprise2(4) | Op_Server0(9), Enterprise2(8) | 0.7375 | 0.3688 | 0.7063 | 0.2062 |
| selected | stage2_ext_016_obj_0 | 40 | DecoySmss | Enterprise2 | Impact | Op_Server0 | Op_Server0(8), Enterprise2(3) | Op_Server0(2), Enterprise0(1), Enterprise2(1) | 0.775 | 0.3812 | 0.6937 | 0.1562 |
| selected | stage2_ext_016_obj_0 | 41 | Restore | Op_Server0 | Impact | Op_Server0 | Op_Server0(5), Enterprise2(3) | Op_Server0(7), Enterprise2(4), Enterprise0(1) | 0.7625 | 0.375 | 0.725 | 0.1562 |
| selected | stage2_ext_016_obj_0 | 42 | Restore | Enterprise2 | Impact | Op_Server0 | Op_Server0(8), Enterprise2(5) | Enterprise2(5), Op_Server0(4), Enterprise1(2) | 0.7875 | 0.375 | 0.7312 | 0.2188 |
| selected | stage2_ext_016_obj_0 | 43 | Restore | Op_Server0 | Impact | Op_Server0 | Op_Server0(5), Enterprise2(2) | Enterprise2(5), Op_Server0(4), User1(1) | 0.7937 | 0.3563 | 0.7375 | 0.175 |
| selected | stage2_ext_016_obj_0 | 44 | DecoyVsftpd | Op_Server0 | Impact | Op_Server0 | Op_Server0(6), Enterprise2(5) | Op_Server0(5), Enterprise2(4), Enterprise0(2) | 0.8 | 0.3625 | 0.7625 | 0.1625 |
| selected | stage2_ext_016_obj_0 | 45 | DecoySmss | Op_Server0 | Impact | Op_Server0 | Enterprise2(4), Op_Server0(4) | Enterprise2(5), Op_Server0(2), Enterprise0(1) | 0.8125 | 0.3563 | 0.7625 | 0.1625 |
| selected | stage2_ext_016_obj_0 | 46 | DecoySmss | User4 | Impact | Op_Server0 | Op_Server0(6), Enterprise2(1) | Op_Server0(3), Enterprise1(1) | 0.8313 | 0.3625 | 0.7875 | 0.15 |
| selected | stage2_ext_016_obj_0 | 47 | Restore | Op_Server0 | Impact | Op_Server0 | Op_Server0(5), Enterprise2(2) | Enterprise2(8), Op_Server0(7), Enterprise1(1) | 0.8187 | 0.325 | 0.7937 | 0.2 |
| selected | stage2_ext_016_obj_0 | 48 | DecoySmss | Enterprise2 | Impact | Op_Server0 | Op_Server0(5), Enterprise2(1) | Op_Server0(3), Enterprise2(3), User1(1) | 0.8313 | 0.3125 | 0.7875 | 0.15 |
| selected | stage2_ext_016_obj_0 | 49 | DecoyVsftpd | Enterprise2 | Impact | Op_Server0 | Op_Server0(6), Enterprise2(5) | Enterprise2(2), Enterprise0(1), Op_Server0(1) | 0.8625 | 0.3312 | 0.8 | 0.1125 |
| selected | stage2_ext_016_obj_0 | 50 | Restore | Op_Server0 | Impact | Op_Server0 | Op_Server0(3), Enterprise2(1) | Op_Server0(16), Enterprise2(2) | 0.7812 | 0.325 | 0.825 | 0.2437 |
| selected | stage2_ext_016_obj_0 | 51 | DecoySmss | Enterprise2 | Impact | Op_Server0 | Op_Server0(4), Enterprise2(1) | Op_Server0(4), Enterprise2(3), User4(1) | 0.7812 | 0.3125 | 0.7625 | 0.1812 |
| selected | stage2_ext_016_obj_0 | 52 | Remove | Op_Server0 | Impact | Op_Server0 | Op_Server0(13) | Op_Server0(6), Enterprise2(3), Enterprise0(1) | 0.825 | 0.2938 | 0.7562 | 0.1688 |
| selected | stage2_ext_016_obj_0 | 53 | Restore | Op_Server0 | Impact | Op_Server0 | Op_Server0(5), Enterprise2(5) | Op_Server0(5), Enterprise2(4), Enterprise1(1) | 0.825 | 0.3 | 0.7438 | 0.1812 |
| selected | stage2_ext_016_obj_0 | 54 | DecoyVsftpd | Op_Server0 | Impact | Op_Server0 | Op_Server0(6), Enterprise2(1) | Op_Server0(3), Enterprise2(2) | 0.8438 | 0.2938 | 0.7937 | 0.1125 |
| selected | stage2_ext_016_obj_0 | 55 | Restore | Enterprise2 | Impact | Op_Server0 | Enterprise2(2), Op_Server0(2) | Op_Server0(3), Enterprise2(1) | 0.8375 | 0.3 | 0.8063 | 0.1625 |
| selected | stage2_ext_016_obj_0 | 56 | Restore | Op_Server0 | Impact | Op_Server0 | Op_Server0(7), Enterprise2(3), Enterprise1(1) | Op_Server0(5), Enterprise2(2), Enterprise0(1) | 0.85 | 0.3063 | 0.825 | 0.1625 |
| selected | stage2_ext_016_obj_0 | 57 | Restore | Op_Server0 | Impact | Op_Server0 | Op_Server0(2), Enterprise2(1) | Op_Server0(5), Enterprise2(3), Enterprise1(1) | 0.8313 | 0.2938 | 0.8063 | 0.1562 |
| selected | stage2_ext_016_obj_0 | 58 | Restore | Enterprise2 | Impact | Op_Server0 | Op_Server0(3), Enterprise2(3) | Enterprise2(5), Op_Server0(4), Enterprise0(1) | 0.825 | 0.2812 | 0.8187 | 0.1562 |
| selected | stage2_ext_016_obj_0 | 59 | Restore | Op_Server0 | Impact | Op_Server0 | Enterprise2(4), Op_Server0(4) | Op_Server0(6), Enterprise2(3), Enterprise0(2) | 0.8125 | 0.2875 | 0.8063 | 0.1938 |
| selected | stage2_ext_016_obj_0 | 60 | DecoySmss | Op_Server0 | Impact | Op_Server0 | Enterprise2(5), Op_Server0(4) | Op_Server0(3), User2(1) | 0.8187 | 0.3187 | 0.7875 | 0.1375 |
| selected | stage2_ext_016_obj_0 | 61 | Restore | Enterprise2 | Impact | Op_Server0 | Op_Server0(5), Enterprise2(1) | Op_Server0(7), Enterprise0(1) | 0.8063 | 0.325 | 0.7937 | 0.225 |
| selected | stage2_ext_016_obj_0 | 62 | Restore | Enterprise2 | Impact | Op_Server0 | Op_Server0(8), Enterprise2(3) | Op_Server0(8), Enterprise2(4) | 0.8063 | 0.3187 | 0.775 | 0.2062 |
| selected | stage2_ext_016_obj_0 | 63 | Restore | Enterprise2 | Impact | Op_Server0 | Op_Server0(4), Enterprise2(2) | Op_Server0(4), Enterprise2(2), Enterprise1(1) | 0.8063 | 0.3187 | 0.7562 | 0.1688 |
| selected | stage2_ext_016_obj_0 | 64 | Restore | Op_Server0 | Impact | Op_Server0 | Enterprise2(5), Op_Server0(4) | Enterprise2(6), Op_Server0(3), Enterprise0(1) | 0.8125 | 0.3125 | 0.7812 | 0.1938 |
| selected | stage2_ext_016_obj_0 | 65 | Restore | Op_Server0 | Impact | Op_Server0 | Op_Server0(6), Enterprise2(4) | Enterprise2(3), Op_Server0(3), User4(1) | 0.8313 | 0.3187 | 0.7875 | 0.1938 |
| selected | stage2_ext_016_obj_0 | 66 | Restore | Op_Server0 | Impact | Op_Server0 | Op_Server0(3), Enterprise2(3) | Op_Server0(8), Enterprise2(4) | 0.8 | 0.3125 | 0.7937 | 0.2062 |
| selected | stage2_ext_016_obj_0 | 67 | DecoySmss | Op_Server0 | Impact | Op_Server0 | Op_Server0(6), Enterprise2(3) | Op_Server0(9), Enterprise2(2) | 0.7812 | 0.3187 | 0.7812 | 0.1688 |
| selected | stage2_ext_016_obj_0 | 68 | Restore | Op_Server0 | Impact | Op_Server0 | Op_Server0(10), Enterprise2(2) | Op_Server0(5), Enterprise2(2), User4(1) | 0.8125 | 0.3187 | 0.7438 | 0.1875 |
| selected | stage2_ext_016_obj_0 | 69 | Restore | Op_Server0 | Impact | Op_Server0 | Op_Server0(7), Enterprise2(4) | Op_Server0(3), Enterprise2(2), Enterprise1(1) | 0.8375 | 0.3312 | 0.75 | 0.1688 |
| selected | stage2_ext_016_obj_0 | 70 | DecoyVsftpd | Op_Server0 | Impact | Op_Server0 | Op_Server0(6), Enterprise2(4) | Op_Server0(6), Enterprise1(1), User1(1) | 0.8375 | 0.3563 | 0.7937 | 0.1625 |
| selected | stage2_ext_016_obj_0 | 71 | Restore | Enterprise2 | Impact | Op_Server0 | Op_Server0(2), Enterprise2(2) | Op_Server0(6), Enterprise2(5), Enterprise0(1) | 0.8125 | 0.3375 | 0.8 | 0.2188 |
| selected | stage2_ext_016_obj_0 | 72 | Restore | Enterprise2 | Impact | Op_Server0 | Op_Server0(4), Enterprise2(3) | Enterprise2(7), Enterprise1(1), Op_Server0(1) | 0.8313 | 0.3125 | 0.8 | 0.2062 |
| selected | stage2_ext_016_obj_0 | 73 | Restore | Op_Server0 | Impact | Op_Server0 | Op_Server0(7), Enterprise2(6) | Op_Server0(9), User2(2), Enterprise2(2) | 0.8187 | 0.3375 | 0.8063 | 0.2 |
| selected | stage2_ext_016_obj_0 | 74 | Restore | Op_Server0 | Impact | Op_Server0 | Enterprise2(3), Op_Server0(2) | Op_Server0(7), Enterprise2(2), Enterprise0(1) | 0.7875 | 0.3438 | 0.775 | 0.1812 |
| selected | stage2_ext_016_obj_0 | 75 | Restore | Op_Server0 | Impact | Op_Server0 | Op_Server0(6) | Op_Server0(9), Enterprise2(4) | 0.7688 | 0.3187 | 0.775 | 0.2 |
| selected | stage2_ext_016_obj_0 | 76 | Restore | Op_Server0 | Impact | Op_Server0 | Op_Server0(9), Enterprise2(6) | Enterprise2(7), Op_Server0(4) | 0.8 | 0.3125 | 0.7312 | 0.2188 |
| selected | stage2_ext_016_obj_0 | 77 | DecoySmss | Op_Server0 | Impact | Op_Server0 | Enterprise2(4), Op_Server0(4) | Op_Server0(3), Enterprise2(2), Enterprise1(1) | 0.8063 | 0.325 | 0.7438 | 0.0938 |
| selected | stage2_ext_016_obj_0 | 78 | Restore | Enterprise2 | Impact | Op_Server0 | Enterprise2(7), Op_Server0(1) | Op_Server0(7), Enterprise2(3), Enterprise1(1) | 0.7688 | 0.35 | 0.7812 | 0.175 |
| selected | stage2_ext_016_obj_0 | 79 | Restore | Op_Server0 | Impact | Op_Server0 | Op_Server0(7), Enterprise2(3) | Op_Server0(5) | 0.7812 | 0.3688 | 0.7625 | 0.1875 |
| selected | stage2_ext_016_obj_0 | 80 | DecoySmss | Op_Server0 | Impact | Op_Server0 | Op_Server0(7), Enterprise2(1) | Op_Server0(4), User4(1), Enterprise2(1) | 0.8 | 0.3688 | 0.7375 | 0.1625 |
| selected | stage2_ext_016_obj_0 | 81 | Restore | Op_Server0 | Impact | Op_Server0 | Op_Server0(11), Enterprise2(4) | Op_Server0(5), Enterprise2(4), Enterprise1(1) | 0.8375 | 0.3688 | 0.7562 | 0.175 |
| selected | stage2_ext_016_obj_0 | 82 | Restore | Enterprise2 | Impact | Op_Server0 | Enterprise2(3), Op_Server0(2) | Op_Server0(6), Enterprise2(6), Enterprise1(1) | 0.8125 | 0.35 | 0.7688 | 0.2 |
| selected | stage2_ext_016_obj_0 | 83 | Restore | Op_Server0 | Impact | Op_Server0 | Enterprise2(4), Op_Server0(2) | Enterprise2(5), Op_Server0(5), Enterprise0(1) | 0.7937 | 0.3438 | 0.8 | 0.2313 |
| selected | stage2_ext_016_obj_0 | 84 | DecoySmss | Enterprise2 | Impact | Op_Server0 | Enterprise2(4), Op_Server0(2) | Op_Server0(6) | 0.7688 | 0.3688 | 0.7812 | 0.1375 |
| selected | stage2_ext_016_obj_0 | 85 | DecoyVsftpd | Op_Server0 | Impact | Op_Server0 | Enterprise2(5), Op_Server0(2) | Enterprise2(3), Op_Server0(2), Enterprise0(1) | 0.7688 | 0.3812 | 0.7562 | 0.1375 |
| selected | stage2_ext_016_obj_0 | 86 | Restore | Op_Server0 | Impact | Op_Server0 | Op_Server0(8), Enterprise2(5) | Op_Server0(7), Enterprise2(3), Enterprise0(1) | 0.775 | 0.3937 | 0.7562 | 0.175 |
| selected | stage2_ext_016_obj_0 | 87 | Restore | Enterprise2 | Impact | Op_Server0 | Enterprise2(4), Op_Server0(4) | Enterprise2(7), Op_Server0(2) | 0.7875 | 0.375 | 0.725 | 0.2062 |
| selected | stage2_ext_016_obj_0 | 88 | DecoyVsftpd | Op_Server0 | Impact | Op_Server0 | Op_Server0(5), Enterprise2(3) | Op_Server0(7), Enterprise2(2) | 0.775 | 0.3812 | 0.7625 | 0.175 |
| selected | stage2_ext_016_obj_0 | 89 | Restore | Enterprise2 | Impact | Op_Server0 | Op_Server0(6), Enterprise2(4) | Enterprise2(8), Op_Server0(4) | 0.7875 | 0.3563 | 0.7438 | 0.2062 |
| selected | stage2_ext_016_obj_0 | 90 | Restore | Op_Server0 | Impact | Op_Server0 | Op_Server0(5), Enterprise2(3) | Op_Server0(9), Enterprise2(2) | 0.7625 | 0.3625 | 0.75 | 0.2125 |
| selected | stage2_ext_016_obj_0 | 91 | DecoySmss | Enterprise2 | Impact | Op_Server0 | Op_Server0(7), Enterprise2(2) | Op_Server0(4), Enterprise2(3), User4(1) | 0.7812 | 0.3563 | 0.7312 | 0.175 |
| selected | stage2_ext_016_obj_0 | 92 | DecoyVsftpd | Op_Server0 | Impact | Op_Server0 | Op_Server0(7), Enterprise2(2) | Enterprise2(5), Op_Server0(5), Enterprise1(2) | 0.7937 | 0.3375 | 0.7375 | 0.1625 |
| selected | stage2_ext_016_obj_0 | 93 | Restore | Enterprise2 | Impact | Op_Server0 | Op_Server0(6), Enterprise2(5) | Op_Server0(5), Enterprise2(2) | 0.8 | 0.3563 | 0.75 | 0.1875 |
| selected | stage2_ext_016_obj_0 | 94 | Remove | Op_Server0 | Impact | Op_Server0 | Op_Server0(8), Enterprise2(3) | Op_Server0(6), Enterprise2(2) | 0.8125 | 0.3625 | 0.7625 | 0.1375 |
| selected | stage2_ext_016_obj_0 | 95 | DecoyVsftpd | Op_Server0 | Impact | Op_Server0 | Op_Server0(4), Enterprise2(1) | Op_Server0(6), Enterprise2(3) | 0.8 | 0.35 | 0.7625 | 0.175 |
| selected | stage2_ext_016_obj_0 | 96 | Restore | Op_Server0 | Impact | Op_Server0 | Op_Server0(10), Enterprise2(5) | Op_Server0(8), Enterprise2(3), User4(1) | 0.8125 | 0.3625 | 0.775 | 0.1812 |
| selected | stage2_ext_016_obj_0 | 97 | Restore | Op_Server0 | Impact | Op_Server0 | Op_Server0(5), Enterprise2(5) | Op_Server0(5), Enterprise2(5), User1(3) | 0.8125 | 0.3625 | 0.75 | 0.2188 |
| selected | stage2_ext_016_obj_0 | 98 | Restore | Op_Server0 | Impact | Op_Server0 | Op_Server0(6), Enterprise2(1) | Enterprise2(6), Op_Server0(5) | 0.8187 | 0.3312 | 0.7812 | 0.1812 |
| selected | stage2_ext_016_obj_0 | 99 | Restore | Op_Server0 | Impact | Op_Server0 | Op_Server0(5), Enterprise2(4) | Op_Server0(9), Enterprise2(5) | 0.7937 | 0.325 | 0.7812 | 0.1875 |
