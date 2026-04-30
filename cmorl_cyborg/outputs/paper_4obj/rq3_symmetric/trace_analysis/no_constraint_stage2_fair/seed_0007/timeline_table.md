## selected (stage2_ext_022_obj_1)

| candidate_label | policy_id | step_idx | blue_action_mode | blue_target_mode | red_action_mode | red_target_mode | newly_compromised_top_hosts | recovered_top_hosts | op_server0_compromised_rate | enterprise2_compromised_rate | impact_rate | restore_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| selected | stage2_ext_022_obj_1 | 0 | Restore | Enterprise0 | DiscoverRemoteSystems | User |  |  | 0.0 | 0.0 | 0.0 | 0.1688 |
| selected | stage2_ext_022_obj_1 | 1 | DecoySvchost | Enterprise2 | DiscoverNetworkServices |  |  |  | 0.0 | 0.0 | 0.0 | 0.1313 |
| selected | stage2_ext_022_obj_1 | 2 | Restore | Enterprise1 | ExploitRemoteService |  | User2(50), User1(41), User3(39) |  | 0.0 | 0.0 | 0.0 | 0.1688 |
| selected | stage2_ext_022_obj_1 | 3 | DecoyTomcat | Enterprise2 | PrivilegeEscalate | User2 | User1(1) | User2(2) | 0.0 | 0.0 | 0.0 | 0.1313 |
| selected | stage2_ext_022_obj_1 | 4 | Sleep | Enterprise2 | DiscoverNetworkServices | User1 | User2(2) | User2(1) | 0.0 | 0.0 | 0.0 | 0.125 |
| selected | stage2_ext_022_obj_1 | 5 | Sleep | Op_Server0 | ExploitRemoteService | User2 | Enterprise1(89), Enterprise0(61) | User1(1), User2(1), User4(1) | 0.0 | 0.0 | 0.0 | 0.1437 |
| selected | stage2_ext_022_obj_1 | 6 | Sleep | Enterprise2 | PrivilegeEscalate | Enterprise1 | Enterprise1(1) | Enterprise1(5), Enterprise0(1), User2(1) | 0.0 | 0.0 | 0.0 | 0.1375 |
| selected | stage2_ext_022_obj_1 | 7 | Sleep | Enterprise2 | DiscoverRemoteSystems | Enterprise | Enterprise1(7), Enterprise0(1) | Enterprise1(4), User2(2) | 0.0 | 0.0 | 0.0 | 0.1437 |
| selected | stage2_ext_022_obj_1 | 8 | Sleep | Enterprise0 | DiscoverNetworkServices | Enterprise1 |  | Enterprise1(5) | 0.0 | 0.0 | 0.0 | 0.0938 |
| selected | stage2_ext_022_obj_1 | 9 | Sleep | Enterprise0 | ExploitRemoteService | Enterprise | Enterprise2(123) | User2(3), User4(1) | 0.0 | 0.7688 | 0.0 | 0.1313 |
| selected | stage2_ext_022_obj_1 | 10 | Sleep | Enterprise0 | PrivilegeEscalate | Enterprise2 | Enterprise1(1), Enterprise2(1) | Enterprise2(5), Enterprise1(3), User2(1) | 0.0 | 0.7438 | 0.0 | 0.1313 |
| selected | stage2_ext_022_obj_1 | 11 | DecoySvchost | Enterprise2 | DiscoverNetworkServices | Enterprise1 | Enterprise2(12) | Enterprise1(6), Enterprise2(4) | 0.0 | 0.7937 | 0.0 | 0.1437 |
| selected | stage2_ext_022_obj_1 | 12 | Sleep | Defender | ExploitRemoteService | Enterprise | Op_Server0(73), Enterprise1(1) | Enterprise2(5), Enterprise1(2), User2(2) | 0.4562 | 0.7625 | 0.0 | 0.1375 |
| selected | stage2_ext_022_obj_1 | 13 | DecoyTomcat | Enterprise0 | PrivilegeEscalate | Op_Server0 | Enterprise0(1), Enterprise2(1), Op_Server0(1) | Enterprise2(6), Enterprise1(4), User2(1) | 0.4625 | 0.7312 | 0.0 | 0.1187 |
| selected | stage2_ext_022_obj_1 | 14 | Sleep | Enterprise2 | Impact | Op_Server0 | Enterprise2(7), Op_Server0(5) | Enterprise1(5), Enterprise2(4), User1(1) | 0.4875 | 0.75 | 0.4562 | 0.1437 |
| selected | stage2_ext_022_obj_1 | 15 | Sleep | Enterprise0 | Impact | Op_Server0 | Enterprise2(3), Enterprise1(1) | Enterprise2(2), User2(1), Enterprise1(1) | 0.4875 | 0.7562 | 0.4562 | 0.1187 |
| selected | stage2_ext_022_obj_1 | 16 | Restore | User2 | Impact | Op_Server0 | Op_Server0(13), Enterprise2(2), Enterprise1(1) | Enterprise2(5), User2(4), Enterprise1(2) | 0.5687 | 0.7375 | 0.4875 | 0.1688 |
| selected | stage2_ext_022_obj_1 | 17 | DecoySvchost | Enterprise0 | Impact | Op_Server0 | Enterprise2(4), Op_Server0(1) | Enterprise2(5), Enterprise1(2), User2(2) | 0.575 | 0.7312 | 0.4875 | 0.1375 |
| selected | stage2_ext_022_obj_1 | 18 | Sleep | Enterprise0 | Impact | Op_Server0 | Op_Server0(2), Enterprise2(1) | Enterprise2(4), Enterprise1(3) | 0.5875 | 0.7125 | 0.5687 | 0.1125 |
| selected | stage2_ext_022_obj_1 | 19 | Sleep | Enterprise2 | Impact | Op_Server0 | Enterprise2(4), Enterprise1(3) | Enterprise2(6), User3(1), Enterprise1(1) | 0.5875 | 0.7 | 0.575 | 0.1375 |
| selected | stage2_ext_022_obj_1 | 20 | Restore | Enterprise0 | Impact | Op_Server0 | Op_Server0(6), Enterprise2(1) | Enterprise2(5), Enterprise1(3), User2(1) | 0.625 | 0.675 | 0.5875 | 0.1812 |
| selected | stage2_ext_022_obj_1 | 21 | Restore | Enterprise2 | Impact | Op_Server0 | Enterprise0(1), Enterprise1(1), Enterprise2(1) | Enterprise1(6), Enterprise2(2), User1(1) | 0.6188 | 0.6687 | 0.5875 | 0.1875 |
| selected | stage2_ext_022_obj_1 | 22 | DecoySvchost | Enterprise2 | Impact | Op_Server0 | Op_Server0(5), User3(1), Enterprise1(1) | Enterprise2(3), User2(2), Enterprise1(2) | 0.65 | 0.65 | 0.6188 | 0.1437 |
| selected | stage2_ext_022_obj_1 | 23 | DecoyTomcat | Enterprise2 | Impact | Op_Server0 | Enterprise2(2), Op_Server0(1) | Enterprise1(2), Enterprise2(2), Op_Server0(1) | 0.65 | 0.65 | 0.6188 | 0.1187 |
| selected | stage2_ext_022_obj_1 | 24 | Sleep | Enterprise0 | Impact | Op_Server0 | Op_Server0(6), Enterprise2(4) | Enterprise2(5), Enterprise1(3), User2(2) | 0.6875 | 0.6438 | 0.6438 | 0.15 |
| selected | stage2_ext_022_obj_1 | 25 | Sleep | Enterprise0 | Impact | Op_Server0 | Enterprise2(3), Op_Server0(2), Enterprise0(1) | User2(2), Enterprise1(2), Enterprise2(1) | 0.7 | 0.6562 | 0.65 | 0.0875 |
| selected | stage2_ext_022_obj_1 | 26 | DecoySvchost | Enterprise0 | Impact | Op_Server0 | Enterprise2(2), Op_Server0(2) | User2(2), Enterprise2(2) | 0.7125 | 0.6562 | 0.6875 | 0.1375 |
| selected | stage2_ext_022_obj_1 | 27 | Restore | User2 | Impact | Op_Server0 | Op_Server0(1) | Enterprise2(5), Enterprise1(3) | 0.7188 | 0.625 | 0.7 | 0.1688 |
| selected | stage2_ext_022_obj_1 | 28 | Sleep | User2 | Impact | Op_Server0 | Op_Server0(3), Enterprise2(1) | Enterprise1(4), Enterprise2(4), User2(1) | 0.7375 | 0.6062 | 0.7125 | 0.1375 |
| selected | stage2_ext_022_obj_1 | 29 | Restore | Enterprise2 | Impact | Op_Server0 | Enterprise2(4), Op_Server0(2), Enterprise0(1) | Enterprise2(4), Enterprise1(2), Op_Server0(1) | 0.7438 | 0.6062 | 0.7188 | 0.1437 |
| selected | stage2_ext_022_obj_1 | 30 | Sleep | Enterprise0 | Impact | Op_Server0 | Op_Server0(1) | Enterprise2(3), Enterprise1(3), User2(2) | 0.75 | 0.5875 | 0.7312 | 0.1375 |
| selected | stage2_ext_022_obj_1 | 31 | Sleep | Enterprise0 | Impact | Op_Server0 | Op_Server0(2), Enterprise2(1), Enterprise1(1) | Enterprise2(3), Enterprise1(1) | 0.7625 | 0.575 | 0.7438 | 0.1375 |
| selected | stage2_ext_022_obj_1 | 32 | Restore | Enterprise2 | Impact | Op_Server0 | Op_Server0(2), Enterprise2(2) | Enterprise2(4), Enterprise1(2) | 0.775 | 0.5625 | 0.75 | 0.1562 |
| selected | stage2_ext_022_obj_1 | 33 | Sleep | Enterprise0 | Impact | Op_Server0 | Enterprise2(1) | Enterprise2(4), User1(1) | 0.775 | 0.5437 | 0.7625 | 0.15 |
| selected | stage2_ext_022_obj_1 | 34 | Restore | Enterprise2 | Impact | Op_Server0 | Enterprise2(1), Enterprise1(1) | Enterprise2(4), User1(2), Enterprise1(2) | 0.775 | 0.525 | 0.775 | 0.2 |
| selected | stage2_ext_022_obj_1 | 35 | Sleep | Enterprise0 | Impact | Op_Server0 | Enterprise2(1) | Enterprise1(2), User1(1) | 0.775 | 0.5312 | 0.775 | 0.1375 |
| selected | stage2_ext_022_obj_1 | 36 | Sleep | Enterprise0 | Impact | Op_Server0 | Op_Server0(3) | Enterprise2(4) | 0.7937 | 0.5062 | 0.775 | 0.1187 |
| selected | stage2_ext_022_obj_1 | 37 | Sleep | User2 | Impact | Op_Server0 | Enterprise2(2), Enterprise0(1) | Enterprise1(3), Enterprise2(2) | 0.7937 | 0.5062 | 0.775 | 0.0938 |
| selected | stage2_ext_022_obj_1 | 38 | Restore | Enterprise2 | Impact | Op_Server0 | Enterprise2(1) | User1(1) | 0.7937 | 0.5125 | 0.7937 | 0.1688 |
| selected | stage2_ext_022_obj_1 | 39 | Sleep | Enterprise0 | Impact | Op_Server0 | Enterprise1(1), Enterprise2(1), Op_Server0(1) | Enterprise2(3), User2(2), User4(1) | 0.8 | 0.5 | 0.7937 | 0.1375 |
| selected | stage2_ext_022_obj_1 | 40 | Sleep | Defender | Impact | Op_Server0 | Op_Server0(1) | User2(3), Enterprise2(2), User1(1) | 0.8063 | 0.4875 | 0.7937 | 0.15 |
| selected | stage2_ext_022_obj_1 | 41 | Restore | Enterprise2 | Impact | Op_Server0 | Enterprise2(1) | Enterprise2(3) | 0.8063 | 0.475 | 0.8 | 0.1688 |
| selected | stage2_ext_022_obj_1 | 42 | Sleep | User2 | Impact | Op_Server0 |  | Enterprise1(1) | 0.8063 | 0.475 | 0.8063 | 0.1187 |
| selected | stage2_ext_022_obj_1 | 43 | Sleep | Op_Server0 | Impact | Op_Server0 | Enterprise2(1) | Enterprise2(2), User4(1), Enterprise1(1) | 0.8063 | 0.4688 | 0.8063 | 0.075 |
| selected | stage2_ext_022_obj_1 | 44 | Sleep | Enterprise0 | Impact | Op_Server0 | Op_Server0(3) | Enterprise2(2), Enterprise1(2), User2(1) | 0.8187 | 0.4562 | 0.8063 | 0.1437 |
| selected | stage2_ext_022_obj_1 | 45 | Sleep | Enterprise0 | Impact | Op_Server0 |  | Enterprise2(2), Enterprise1(1) | 0.8187 | 0.4437 | 0.8 | 0.1125 |
| selected | stage2_ext_022_obj_1 | 46 | DecoyTomcat | User2 | Impact | Op_Server0 | Op_Server0(3), Enterprise1(1) | Enterprise2(3), Enterprise1(1), User2(1) | 0.8375 | 0.425 | 0.8187 | 0.1187 |
| selected | stage2_ext_022_obj_1 | 47 | Sleep | Enterprise0 | Impact | Op_Server0 | Enterprise2(1) | Enterprise2(6), Enterprise1(1), Op_Server0(1) | 0.8313 | 0.3937 | 0.8187 | 0.125 |
| selected | stage2_ext_022_obj_1 | 48 | Restore | Enterprise2 | Impact | Op_Server0 | Enterprise2(1) | Enterprise1(1), Enterprise2(1) | 0.8313 | 0.3937 | 0.8313 | 0.15 |
| selected | stage2_ext_022_obj_1 | 49 | Sleep | Enterprise0 | Impact | Op_Server0 | Enterprise2(3) | Enterprise1(2), User1(1), User4(1) | 0.8313 | 0.4062 | 0.8313 | 0.1437 |
| selected | stage2_ext_022_obj_1 | 50 | Sleep | Enterprise2 | Impact | Op_Server0 | Enterprise2(2) | Enterprise2(3), Enterprise1(2) | 0.8313 | 0.4 | 0.8313 | 0.1187 |
| selected | stage2_ext_022_obj_1 | 51 | Sleep | Enterprise2 | Impact | Op_Server0 |  | Enterprise2(4), Enterprise1(1) | 0.8313 | 0.375 | 0.8313 | 0.125 |
| selected | stage2_ext_022_obj_1 | 52 | Sleep | Enterprise2 | Impact | Op_Server0 | Op_Server0(2) | Enterprise2(5), Enterprise1(2), Enterprise0(1) | 0.8438 | 0.3438 | 0.8313 | 0.1187 |
| selected | stage2_ext_022_obj_1 | 53 | Sleep | User3 | Impact | Op_Server0 | Enterprise2(1), Op_Server0(1) | Enterprise1(2), Enterprise2(1) | 0.85 | 0.3438 | 0.8313 | 0.0875 |
| selected | stage2_ext_022_obj_1 | 54 | Restore | User2 | Impact | Op_Server0 | Enterprise2(2) | Enterprise0(2) | 0.85 | 0.3563 | 0.8438 | 0.1375 |
| selected | stage2_ext_022_obj_1 | 55 | Sleep | Enterprise0 | Impact | Op_Server0 | Op_Server0(1) | Enterprise1(1), User1(1), User2(1) | 0.8562 | 0.3563 | 0.85 | 0.1375 |
| selected | stage2_ext_022_obj_1 | 56 | Sleep | Enterprise0 | Impact | Op_Server0 | Op_Server0(1) | Enterprise2(2), User1(1), Op_Server0(1) | 0.8562 | 0.3438 | 0.85 | 0.1187 |
| selected | stage2_ext_022_obj_1 | 57 | DecoyTomcat | Enterprise0 | Impact | Op_Server0 | Enterprise1(1), Op_Server0(1) | Enterprise2(2), User1(1), Enterprise1(1) | 0.8625 | 0.3312 | 0.85 | 0.1 |
| selected | stage2_ext_022_obj_1 | 58 | Sleep | Enterprise2 | Impact | Op_Server0 | Op_Server0(1) | Enterprise2(2) | 0.8688 | 0.3187 | 0.8562 | 0.1125 |
| selected | stage2_ext_022_obj_1 | 59 | Restore | Enterprise2 | Impact | Op_Server0 | Enterprise2(1) | Enterprise2(2), User1(1), Enterprise1(1) | 0.8688 | 0.3125 | 0.8625 | 0.1875 |
| selected | stage2_ext_022_obj_1 | 60 | Sleep | Enterprise2 | Impact | Op_Server0 | Op_Server0(2) | Enterprise2(2), User3(1) | 0.8812 | 0.3 | 0.8688 | 0.1125 |
| selected | stage2_ext_022_obj_1 | 61 | DecoySvchost | Enterprise0 | Impact | Op_Server0 |  | Enterprise2(2), Enterprise1(1) | 0.8812 | 0.2875 | 0.8688 | 0.1187 |
| selected | stage2_ext_022_obj_1 | 62 | Restore | Enterprise0 | Impact | Op_Server0 | Enterprise2(1), Op_Server0(1) | Op_Server0(1), Enterprise2(1) | 0.8812 | 0.2875 | 0.8812 | 0.1375 |
| selected | stage2_ext_022_obj_1 | 63 | DecoyTomcat | Enterprise0 | Impact | Op_Server0 | Enterprise2(1) | Enterprise1(2), User3(1) | 0.8812 | 0.2938 | 0.875 | 0.1313 |
| selected | stage2_ext_022_obj_1 | 64 | Restore | Enterprise2 | Impact | Op_Server0 | Op_Server0(2), Enterprise1(1) | Enterprise1(2), User1(2), Enterprise2(1) | 0.8938 | 0.2875 | 0.8812 | 0.2 |
| selected | stage2_ext_022_obj_1 | 65 | Sleep | Enterprise0 | Impact | Op_Server0 | Op_Server0(2), Enterprise0(1) | Enterprise2(3), User4(1) | 0.9062 | 0.2687 | 0.8812 | 0.15 |
| selected | stage2_ext_022_obj_1 | 66 | Sleep | Enterprise0 | Impact | Op_Server0 | Op_Server0(3) | Enterprise1(1) | 0.925 | 0.2687 | 0.8938 | 0.1437 |
| selected | stage2_ext_022_obj_1 | 67 | DecoyTomcat | Enterprise0 | Impact | Op_Server0 | Enterprise2(1) | Enterprise1(1) | 0.925 | 0.275 | 0.9062 | 0.1062 |
| selected | stage2_ext_022_obj_1 | 68 | Restore | Enterprise2 | Impact | Op_Server0 |  | Enterprise2(1), Enterprise0(1), User2(1) | 0.925 | 0.2687 | 0.925 | 0.1938 |
| selected | stage2_ext_022_obj_1 | 69 | DecoyTomcat | Enterprise0 | Impact | Op_Server0 | Enterprise1(1) | User1(2), Enterprise2(2), User3(1) | 0.925 | 0.2562 | 0.925 | 0.1437 |
| selected | stage2_ext_022_obj_1 | 70 | Sleep | Enterprise2 | Impact | Op_Server0 |  | Enterprise2(1) | 0.925 | 0.25 | 0.925 | 0.15 |
| selected | stage2_ext_022_obj_1 | 71 | Sleep | Enterprise0 | Impact | Op_Server0 | User3(1) | Enterprise2(2), Op_Server0(1) | 0.9187 | 0.2375 | 0.925 | 0.1313 |
| selected | stage2_ext_022_obj_1 | 72 | Sleep | Enterprise2 | Impact | Op_Server0 | Op_Server0(1) | Enterprise2(1) | 0.925 | 0.2313 | 0.9187 | 0.1375 |
| selected | stage2_ext_022_obj_1 | 73 | Sleep | Enterprise0 | Impact | Op_Server0 |  | Enterprise2(1), Enterprise0(1), Enterprise1(1) | 0.925 | 0.225 | 0.9187 | 0.1625 |
| selected | stage2_ext_022_obj_1 | 74 | Restore | Defender | Impact | Op_Server0 | Op_Server0(2), Enterprise2(2) | User3(1) | 0.9375 | 0.2375 | 0.925 | 0.1875 |
| selected | stage2_ext_022_obj_1 | 75 | DecoyTomcat | User2 | Impact | Op_Server0 |  | Enterprise2(1), Op_Server0(1) | 0.9313 | 0.2313 | 0.925 | 0.1437 |
| selected | stage2_ext_022_obj_1 | 76 | Restore | User2 | Impact | Op_Server0 | Op_Server0(1) | User2(1) | 0.9375 | 0.2313 | 0.9313 | 0.175 |
| selected | stage2_ext_022_obj_1 | 77 | Restore | Enterprise2 | Impact | Op_Server0 | Op_Server0(2), Enterprise0(1) | Enterprise2(1) | 0.95 | 0.225 | 0.9313 | 0.1938 |
| selected | stage2_ext_022_obj_1 | 78 | Sleep | Enterprise2 | Impact | Op_Server0 | Enterprise2(1) | Enterprise2(2), Op_Server0(1) | 0.9437 | 0.2188 | 0.9375 | 0.125 |
| selected | stage2_ext_022_obj_1 | 79 | DecoySvchost | User2 | Impact | Op_Server0 | Op_Server0(1) | Enterprise2(2) | 0.95 | 0.2062 | 0.9437 | 0.1125 |
| selected | stage2_ext_022_obj_1 | 80 | Sleep | User2 | Impact | Op_Server0 |  | User4(1), Enterprise0(1) | 0.95 | 0.2062 | 0.9437 | 0.15 |
| selected | stage2_ext_022_obj_1 | 81 | Sleep | Op_Server0 | Impact | Op_Server0 | Enterprise2(1) | Enterprise2(3), User3(1), Enterprise1(1) | 0.95 | 0.1938 | 0.95 | 0.125 |
| selected | stage2_ext_022_obj_1 | 82 | DecoyTomcat | Enterprise0 | Impact | Op_Server0 | Enterprise2(1) |  | 0.95 | 0.2 | 0.95 | 0.1437 |
| selected | stage2_ext_022_obj_1 | 83 | Restore | Enterprise2 | Impact | Op_Server0 | Enterprise1(1), Op_Server0(1) | Enterprise2(3) | 0.9563 | 0.1812 | 0.95 | 0.1875 |
| selected | stage2_ext_022_obj_1 | 84 | Restore | Enterprise2 | Impact | Op_Server0 |  | Enterprise2(1) | 0.9563 | 0.175 | 0.95 | 0.1313 |
| selected | stage2_ext_022_obj_1 | 85 | DecoyTomcat | User3 | Impact | Op_Server0 | Op_Server0(1) | Enterprise2(2), Op_Server0(1) | 0.9563 | 0.1625 | 0.9563 | 0.1313 |
| selected | stage2_ext_022_obj_1 | 86 | DecoyTomcat | Enterprise2 | Impact | Op_Server0 |  | Enterprise2(3), User1(1) | 0.9563 | 0.1437 | 0.95 | 0.175 |
| selected | stage2_ext_022_obj_1 | 87 | Sleep | Enterprise2 | Impact | Op_Server0 | Op_Server0(1) | Enterprise2(2) | 0.9625 | 0.1313 | 0.9563 | 0.1 |
| selected | stage2_ext_022_obj_1 | 88 | Restore | Enterprise0 | Impact | Op_Server0 |  | Enterprise2(1), User2(1) | 0.9625 | 0.125 | 0.9563 | 0.1688 |
| selected | stage2_ext_022_obj_1 | 89 | Sleep | Enterprise2 | Impact | Op_Server0 | Enterprise2(1) | Enterprise2(1) | 0.9625 | 0.125 | 0.9625 | 0.15 |
| selected | stage2_ext_022_obj_1 | 90 | DecoySvchost | User2 | Impact | Op_Server0 |  | Enterprise2(1), Op_Server0(1) | 0.9563 | 0.1187 | 0.9625 | 0.1437 |
| selected | stage2_ext_022_obj_1 | 91 | DecoyTomcat | Enterprise2 | Impact | Op_Server0 |  | Enterprise2(1) | 0.9563 | 0.1125 | 0.9563 | 0.1187 |
| selected | stage2_ext_022_obj_1 | 92 | Sleep | Enterprise0 | Impact | Op_Server0 | Enterprise2(1) | Enterprise0(1) | 0.9563 | 0.1187 | 0.9563 | 0.15 |
| selected | stage2_ext_022_obj_1 | 93 | DecoySvchost | Defender | Impact | Op_Server0 | Op_Server0(1), Enterprise2(1) | Enterprise2(1) | 0.9625 | 0.1187 | 0.9563 | 0.0938 |
| selected | stage2_ext_022_obj_1 | 94 | Sleep | Enterprise2 | Impact | Op_Server0 |  |  | 0.9625 | 0.1187 | 0.9563 | 0.1125 |
| selected | stage2_ext_022_obj_1 | 95 | Sleep | Enterprise0 | Impact | Op_Server0 |  |  | 0.9625 | 0.1187 | 0.9625 | 0.1062 |
| selected | stage2_ext_022_obj_1 | 96 | Sleep | Enterprise2 | Impact | Op_Server0 | Op_Server0(1) |  | 0.9688 | 0.1187 | 0.9625 | 0.1375 |
| selected | stage2_ext_022_obj_1 | 97 | Restore | Enterprise0 | Impact | Op_Server0 |  | Op_Server0(1) | 0.9625 | 0.1187 | 0.9625 | 0.1625 |
| selected | stage2_ext_022_obj_1 | 98 | Restore | Enterprise0 | Impact | Op_Server0 | Enterprise2(1) | Enterprise2(2) | 0.9625 | 0.1125 | 0.9625 | 0.1562 |
| selected | stage2_ext_022_obj_1 | 99 | DecoyTomcat | User3 | Impact | Op_Server0 | Op_Server0(1) | Enterprise2(1) | 0.9688 | 0.1062 | 0.9625 | 0.075 |
