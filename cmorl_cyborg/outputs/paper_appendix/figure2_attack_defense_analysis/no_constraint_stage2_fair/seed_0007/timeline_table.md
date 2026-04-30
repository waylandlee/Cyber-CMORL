## selected (stage2_ext_022_obj_1)

| candidate_label | policy_id | step_idx | blue_action_mode | blue_target_mode | red_action_mode | red_target_mode | newly_compromised_top_hosts | recovered_top_hosts | op_server0_compromised_rate | enterprise2_compromised_rate | impact_rate | restore_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| selected | stage2_ext_022_obj_1 | 0 | Analyse | Op_Server0 | DiscoverRemoteSystems | User |  |  | 0.0 | 0.0 | 0.0 | 0.0417 |
| selected | stage2_ext_022_obj_1 | 1 | DecoySvchost | Enterprise1 | DiscoverNetworkServices |  |  |  | 0.0 | 0.0 | 0.0 | 0.125 |
| selected | stage2_ext_022_obj_1 | 2 | DecoySvchost | Enterprise1 | ExploitRemoteService |  | User1(9), User2(7), User4(5) |  | 0.0 | 0.0 | 0.0 | 0.1667 |
| selected | stage2_ext_022_obj_1 | 3 | DecoyTomcat | Op_Host1 | PrivilegeEscalate | User1 |  |  | 0.0 | 0.0 | 0.0 | 0.0833 |
| selected | stage2_ext_022_obj_1 | 4 | Sleep | Enterprise0 | DiscoverNetworkServices |  |  |  | 0.0 | 0.0 | 0.0 | 0.0417 |
| selected | stage2_ext_022_obj_1 | 5 | Restore | Op_Server0 | ExploitRemoteService |  | Enterprise1(16), Enterprise0(7) | User1(1) | 0.0 | 0.0 | 0.0 | 0.1667 |
| selected | stage2_ext_022_obj_1 | 6 | Restore | Enterprise2 | PrivilegeEscalate | Enterprise1 |  | Enterprise1(1) | 0.0 | 0.0 | 0.0 | 0.2083 |
| selected | stage2_ext_022_obj_1 | 7 | Sleep | Enterprise2 | DiscoverRemoteSystems | Enterprise | Enterprise1(1) | Enterprise1(1) | 0.0 | 0.0 | 0.0 | 0.0417 |
| selected | stage2_ext_022_obj_1 | 8 | DecoyTomcat | Defender | DiscoverNetworkServices | Enterprise1 |  | Enterprise1(3) | 0.0 | 0.0 | 0.0 | 0.1667 |
| selected | stage2_ext_022_obj_1 | 9 | DecoySvchost | User2 | ExploitRemoteService | Enterprise | Enterprise2(16) | User2(1) | 0.0 | 0.6667 | 0.0 | 0.0833 |
| selected | stage2_ext_022_obj_1 | 10 | DecoyTomcat | Defender | PrivilegeEscalate | Enterprise2 | Enterprise1(1) | Enterprise2(1) | 0.0 | 0.625 | 0.0 | 0.1667 |
| selected | stage2_ext_022_obj_1 | 11 | DecoySvchost | Enterprise0 | DiscoverNetworkServices | Enterprise1 | Enterprise2(2) |  | 0.0 | 0.7083 | 0.0 | 0.0833 |
| selected | stage2_ext_022_obj_1 | 12 | DecoyTomcat | Op_Server0 | ExploitRemoteService | Enterprise | Op_Server0(12) | Enterprise1(1) | 0.5 | 0.7083 | 0.0 | 0.125 |
| selected | stage2_ext_022_obj_1 | 13 | Sleep | User3 | PrivilegeEscalate | Op_Server0 |  | Enterprise2(1), Enterprise1(1) | 0.5 | 0.6667 | 0.0 | 0.1667 |
| selected | stage2_ext_022_obj_1 | 14 | Restore | Enterprise1 | Impact | Op_Server0 | Enterprise2(2), Op_Server0(1) | Enterprise2(1), Enterprise1(1) | 0.5417 | 0.7083 | 0.5 | 0.25 |
| selected | stage2_ext_022_obj_1 | 15 | Sleep | Enterprise0 | Impact | Op_Server0 | Enterprise2(1), Enterprise1(1) |  | 0.5417 | 0.75 | 0.5 | 0.0417 |
| selected | stage2_ext_022_obj_1 | 16 | Sleep | Enterprise2 | Impact | Op_Server0 | Op_Server0(2) | Enterprise2(2) | 0.625 | 0.6667 | 0.5417 | 0.125 |
| selected | stage2_ext_022_obj_1 | 17 | Restore | Enterprise2 | Impact | Op_Server0 |  | Enterprise2(2), Enterprise1(1) | 0.625 | 0.5833 | 0.5417 | 0.2083 |
| selected | stage2_ext_022_obj_1 | 18 | Sleep | Op_Host0 | Impact | Op_Server0 |  |  | 0.625 | 0.5833 | 0.625 | 0.0417 |
| selected | stage2_ext_022_obj_1 | 19 | Sleep | Enterprise2 | Impact | Op_Server0 | Enterprise2(2), Enterprise1(1) | Enterprise2(2) | 0.625 | 0.5833 | 0.625 | 0.1667 |
| selected | stage2_ext_022_obj_1 | 20 | DecoyTomcat | Enterprise0 | Impact | Op_Server0 |  |  | 0.625 | 0.5833 | 0.625 | 0.0417 |
| selected | stage2_ext_022_obj_1 | 21 | Restore | User2 | Impact | Op_Server0 |  | Enterprise1(1) | 0.625 | 0.5833 | 0.625 | 0.25 |
| selected | stage2_ext_022_obj_1 | 22 | DecoyTomcat | Op_Server0 | Impact | Op_Server0 | Op_Server0(2) |  | 0.7083 | 0.5833 | 0.625 | 0.2083 |
| selected | stage2_ext_022_obj_1 | 23 | DecoyTomcat | Op_Server0 | Impact | Op_Server0 |  | Op_Server0(1) | 0.6667 | 0.5833 | 0.625 | 0.0833 |
| selected | stage2_ext_022_obj_1 | 24 | DecoySvchost | Enterprise1 | Impact | Op_Server0 | Enterprise2(1) | Enterprise1(2) | 0.6667 | 0.625 | 0.6667 | 0.125 |
| selected | stage2_ext_022_obj_1 | 25 | Sleep | User3 | Impact | Op_Server0 | Op_Server0(1) |  | 0.7083 | 0.625 | 0.6667 | 0.0 |
| selected | stage2_ext_022_obj_1 | 26 | Sleep | User2 | Impact | Op_Server0 |  | User2(1) | 0.7083 | 0.625 | 0.6667 | 0.125 |
| selected | stage2_ext_022_obj_1 | 27 | DecoyTomcat | Enterprise2 | Impact | Op_Server0 |  | Enterprise2(1) | 0.7083 | 0.5833 | 0.7083 | 0.0417 |
| selected | stage2_ext_022_obj_1 | 28 | Analyse | User2 | Impact | Op_Server0 |  | User2(1), Enterprise1(1) | 0.7083 | 0.5833 | 0.7083 | 0.125 |
| selected | stage2_ext_022_obj_1 | 29 | Restore | Defender | Impact | Op_Server0 | Enterprise2(1) | Enterprise2(1), Op_Server0(1) | 0.6667 | 0.5833 | 0.7083 | 0.25 |
| selected | stage2_ext_022_obj_1 | 30 | Sleep | User0 | Impact | Op_Server0 |  |  | 0.6667 | 0.5833 | 0.6667 | 0.125 |
| selected | stage2_ext_022_obj_1 | 31 | DecoySvchost | Enterprise0 | Impact | Op_Server0 | Op_Server0(1) |  | 0.7083 | 0.5833 | 0.6667 | 0.0833 |
| selected | stage2_ext_022_obj_1 | 32 | DecoySSHD | User4 | Impact | Op_Server0 | Op_Server0(1) | Enterprise1(1) | 0.75 | 0.5833 | 0.6667 | 0.0833 |
| selected | stage2_ext_022_obj_1 | 33 | Sleep | Enterprise2 | Impact | Op_Server0 |  | User1(1), Enterprise2(1) | 0.75 | 0.5417 | 0.7083 | 0.1667 |
| selected | stage2_ext_022_obj_1 | 34 | Sleep | Op_Server0 | Impact | Op_Server0 | Enterprise2(1) | Enterprise2(1), User1(1) | 0.75 | 0.5417 | 0.75 | 0.1667 |
| selected | stage2_ext_022_obj_1 | 35 | DecoySvchost | Op_Host1 | Impact | Op_Server0 |  |  | 0.75 | 0.5417 | 0.75 | 0.0833 |
| selected | stage2_ext_022_obj_1 | 36 | Sleep | User2 | Impact | Op_Server0 | Op_Server0(1) | Enterprise2(1) | 0.7917 | 0.5 | 0.75 | 0.1667 |
| selected | stage2_ext_022_obj_1 | 37 | DecoySvchost | Enterprise0 | Impact | Op_Server0 | Enterprise0(1), Enterprise2(1) | Enterprise1(1) | 0.7917 | 0.5417 | 0.75 | 0.125 |
| selected | stage2_ext_022_obj_1 | 38 | DecoySSHD | Enterprise2 | Impact | Op_Server0 |  |  | 0.7917 | 0.5417 | 0.7917 | 0.125 |
| selected | stage2_ext_022_obj_1 | 39 | DecoyTomcat | Op_Server0 | Impact | Op_Server0 |  | User4(1), User2(1) | 0.7917 | 0.5417 | 0.7917 | 0.1667 |
| selected | stage2_ext_022_obj_1 | 40 | DecoySvchost | Enterprise0 | Impact | Op_Server0 |  | User1(1) | 0.7917 | 0.5417 | 0.7917 | 0.0833 |
| selected | stage2_ext_022_obj_1 | 41 | Restore | Defender | Impact | Op_Server0 | Enterprise2(1) | Enterprise2(2) | 0.7917 | 0.5 | 0.7917 | 0.2083 |
| selected | stage2_ext_022_obj_1 | 42 | Sleep | Enterprise1 | Impact | Op_Server0 |  |  | 0.7917 | 0.5 | 0.7917 | 0.1667 |
| selected | stage2_ext_022_obj_1 | 43 | DecoyTomcat | Op_Server0 | Impact | Op_Server0 | Enterprise2(1) | User4(1), Enterprise1(1) | 0.7917 | 0.5417 | 0.7917 | 0.125 |
| selected | stage2_ext_022_obj_1 | 44 | Sleep | User2 | Impact | Op_Server0 | Op_Server0(1) | User2(1) | 0.8333 | 0.5417 | 0.7917 | 0.1667 |
| selected | stage2_ext_022_obj_1 | 45 | DecoySvchost | Defender | Impact | Op_Server0 |  |  | 0.8333 | 0.5417 | 0.7917 | 0.0833 |
| selected | stage2_ext_022_obj_1 | 46 | DecoyTomcat | Op_Server0 | Impact | Op_Server0 | Op_Server0(1) |  | 0.875 | 0.5417 | 0.8333 | 0.0833 |
| selected | stage2_ext_022_obj_1 | 47 | Restore | User3 | Impact | Op_Server0 |  | Enterprise1(1), Enterprise2(1) | 0.875 | 0.5 | 0.8333 | 0.2083 |
| selected | stage2_ext_022_obj_1 | 48 | Sleep | Enterprise2 | Impact | Op_Server0 |  |  | 0.875 | 0.5 | 0.875 | 0.125 |
| selected | stage2_ext_022_obj_1 | 49 | DecoyTomcat | Op_Server0 | Impact | Op_Server0 | Enterprise2(1) |  | 0.875 | 0.5417 | 0.875 | 0.0833 |
| selected | stage2_ext_022_obj_1 | 50 | DecoySSHD | Enterprise2 | Impact | Op_Server0 |  |  | 0.875 | 0.5417 | 0.875 | 0.0833 |
| selected | stage2_ext_022_obj_1 | 51 | DecoyTomcat | Enterprise1 | Impact | Op_Server0 |  | Enterprise1(1) | 0.875 | 0.5417 | 0.875 | 0.2083 |
| selected | stage2_ext_022_obj_1 | 52 | Sleep | Op_Host2 | Impact | Op_Server0 |  | Enterprise2(1) | 0.875 | 0.5 | 0.875 | 0.0833 |
| selected | stage2_ext_022_obj_1 | 53 | Sleep | Op_Host1 | Impact | Op_Server0 |  | Enterprise1(1) | 0.875 | 0.5 | 0.875 | 0.0417 |
| selected | stage2_ext_022_obj_1 | 54 | Sleep | User2 | Impact | Op_Server0 |  |  | 0.875 | 0.5 | 0.875 | 0.0833 |
| selected | stage2_ext_022_obj_1 | 55 | Sleep | User0 | Impact | Op_Server0 |  |  | 0.875 | 0.5 | 0.875 | 0.0833 |
| selected | stage2_ext_022_obj_1 | 56 | DecoySvchost | User0 | Impact | Op_Server0 |  | Enterprise2(1) | 0.875 | 0.4583 | 0.875 | 0.125 |
| selected | stage2_ext_022_obj_1 | 57 | DecoyTomcat | Defender | Impact | Op_Server0 |  |  | 0.875 | 0.4583 | 0.875 | 0.0417 |
| selected | stage2_ext_022_obj_1 | 58 | Sleep | Enterprise2 | Impact | Op_Server0 |  |  | 0.875 | 0.4583 | 0.875 | 0.0833 |
| selected | stage2_ext_022_obj_1 | 59 | Remove | User4 | Impact | Op_Server0 |  | Enterprise2(1) | 0.875 | 0.4167 | 0.875 | 0.2083 |
| selected | stage2_ext_022_obj_1 | 60 | DecoyTomcat | Enterprise2 | Impact | Op_Server0 |  |  | 0.875 | 0.4167 | 0.875 | 0.1667 |
| selected | stage2_ext_022_obj_1 | 61 | DecoySvchost | Enterprise0 | Impact | Op_Server0 |  |  | 0.875 | 0.4167 | 0.875 | 0.0 |
| selected | stage2_ext_022_obj_1 | 62 | Analyse | Enterprise2 | Impact | Op_Server0 |  | Op_Server0(1) | 0.8333 | 0.4167 | 0.875 | 0.125 |
| selected | stage2_ext_022_obj_1 | 63 | DecoyTomcat | Op_Server0 | Impact | Op_Server0 |  |  | 0.8333 | 0.4167 | 0.8333 | 0.0 |
| selected | stage2_ext_022_obj_1 | 64 | DecoySSHD | Enterprise2 | Impact | Op_Server0 | Op_Server0(1) | Enterprise1(1) | 0.875 | 0.4167 | 0.8333 | 0.125 |
| selected | stage2_ext_022_obj_1 | 65 | Sleep | User2 | Impact | Op_Server0 |  |  | 0.875 | 0.4167 | 0.8333 | 0.1667 |
| selected | stage2_ext_022_obj_1 | 66 | Sleep | Op_Host1 | Impact | Op_Server0 | Op_Server0(1) |  | 0.9167 | 0.4167 | 0.875 | 0.1667 |
| selected | stage2_ext_022_obj_1 | 67 | Sleep | Enterprise1 | Impact | Op_Server0 |  |  | 0.9167 | 0.4167 | 0.875 | 0.0833 |
| selected | stage2_ext_022_obj_1 | 68 | Restore | Enterprise1 | Impact | Op_Server0 |  | Enterprise2(1) | 0.9167 | 0.375 | 0.9167 | 0.2083 |
| selected | stage2_ext_022_obj_1 | 69 | Restore | User0 | Impact | Op_Server0 |  | User1(1) | 0.9167 | 0.375 | 0.9167 | 0.2083 |
| selected | stage2_ext_022_obj_1 | 70 | Sleep | User4 | Impact | Op_Server0 |  |  | 0.9167 | 0.375 | 0.9167 | 0.0833 |
| selected | stage2_ext_022_obj_1 | 71 | DecoySvchost | Op_Server0 | Impact | Op_Server0 |  |  | 0.9167 | 0.375 | 0.9167 | 0.1667 |
| selected | stage2_ext_022_obj_1 | 72 | Analyse | Op_Host2 | Impact | Op_Server0 |  |  | 0.9167 | 0.375 | 0.9167 | 0.0833 |
| selected | stage2_ext_022_obj_1 | 73 | DecoyTomcat | Enterprise0 | Impact | Op_Server0 |  | Enterprise2(1) | 0.9167 | 0.3333 | 0.9167 | 0.1667 |
| selected | stage2_ext_022_obj_1 | 74 | Restore | Enterprise1 | Impact | Op_Server0 | Op_Server0(1) |  | 0.9583 | 0.3333 | 0.9167 | 0.2083 |
| selected | stage2_ext_022_obj_1 | 75 | Analyse | Enterprise0 | Impact | Op_Server0 |  | Enterprise2(1) | 0.9583 | 0.2917 | 0.9167 | 0.1667 |
| selected | stage2_ext_022_obj_1 | 76 | Restore | User2 | Impact | Op_Server0 | Op_Server0(1) |  | 1.0 | 0.2917 | 0.9583 | 0.2083 |
| selected | stage2_ext_022_obj_1 | 77 | Restore | Enterprise2 | Impact | Op_Server0 |  | Enterprise2(1) | 1.0 | 0.25 | 0.9583 | 0.25 |
| selected | stage2_ext_022_obj_1 | 78 | DecoyTomcat | Enterprise0 | Impact | Op_Server0 |  |  | 1.0 | 0.25 | 1.0 | 0.0417 |
| selected | stage2_ext_022_obj_1 | 79 | Analyse | Enterprise0 | Impact | Op_Server0 |  | Enterprise2(1) | 1.0 | 0.2083 | 1.0 | 0.2083 |
| selected | stage2_ext_022_obj_1 | 80 | Sleep | User2 | Impact | Op_Server0 |  |  | 1.0 | 0.2083 | 1.0 | 0.2083 |
| selected | stage2_ext_022_obj_1 | 81 | Sleep | User2 | Impact | Op_Server0 |  | User3(1) | 1.0 | 0.2083 | 1.0 | 0.0417 |
| selected | stage2_ext_022_obj_1 | 82 | DecoySSHD | Defender | Impact | Op_Server0 |  |  | 1.0 | 0.2083 | 1.0 | 0.0833 |
| selected | stage2_ext_022_obj_1 | 83 | DecoySvchost | Enterprise2 | Impact | Op_Server0 |  |  | 1.0 | 0.2083 | 1.0 | 0.125 |
| selected | stage2_ext_022_obj_1 | 84 | Sleep | Enterprise2 | Impact | Op_Server0 |  |  | 1.0 | 0.2083 | 1.0 | 0.125 |
| selected | stage2_ext_022_obj_1 | 85 | DecoyTomcat | User2 | Impact | Op_Server0 |  |  | 1.0 | 0.2083 | 1.0 | 0.125 |
| selected | stage2_ext_022_obj_1 | 86 | Restore | Op_Server0 | Impact | Op_Server0 |  | Enterprise2(1) | 1.0 | 0.1667 | 1.0 | 0.25 |
| selected | stage2_ext_022_obj_1 | 87 | DecoySvchost | User3 | Impact | Op_Server0 |  |  | 1.0 | 0.1667 | 1.0 | 0.125 |
| selected | stage2_ext_022_obj_1 | 88 | DecoySvchost | Enterprise2 | Impact | Op_Server0 |  | Enterprise2(1), User2(1) | 1.0 | 0.125 | 1.0 | 0.125 |
| selected | stage2_ext_022_obj_1 | 89 | DecoySvchost | Enterprise2 | Impact | Op_Server0 |  |  | 1.0 | 0.125 | 1.0 | 0.125 |
| selected | stage2_ext_022_obj_1 | 90 | Sleep | Enterprise2 | Impact | Op_Server0 |  |  | 1.0 | 0.125 | 1.0 | 0.0417 |
| selected | stage2_ext_022_obj_1 | 91 | Restore | Enterprise2 | Impact | Op_Server0 |  | Enterprise2(1) | 1.0 | 0.0833 | 1.0 | 0.25 |
| selected | stage2_ext_022_obj_1 | 92 | DecoyTomcat | Op_Server0 | Impact | Op_Server0 |  |  | 1.0 | 0.0833 | 1.0 | 0.0417 |
| selected | stage2_ext_022_obj_1 | 93 | Sleep | User4 | Impact | Op_Server0 |  |  | 1.0 | 0.0833 | 1.0 | 0.0417 |
| selected | stage2_ext_022_obj_1 | 94 | DecoySvchost | Enterprise1 | Impact | Op_Server0 |  |  | 1.0 | 0.0833 | 1.0 | 0.125 |
| selected | stage2_ext_022_obj_1 | 95 | DecoyVsftpd | User0 | Impact | Op_Server0 |  |  | 1.0 | 0.0833 | 1.0 | 0.0417 |
| selected | stage2_ext_022_obj_1 | 96 | Restore | Enterprise2 | Impact | Op_Server0 |  |  | 1.0 | 0.0833 | 1.0 | 0.25 |
| selected | stage2_ext_022_obj_1 | 97 | DecoySvchost | User3 | Impact | Op_Server0 |  |  | 1.0 | 0.0833 | 1.0 | 0.1667 |
| selected | stage2_ext_022_obj_1 | 98 | Sleep | User3 | Impact | Op_Server0 |  |  | 1.0 | 0.0833 | 1.0 | 0.125 |
| selected | stage2_ext_022_obj_1 | 99 | Analyse | Enterprise1 | Impact | Op_Server0 |  |  | 1.0 | 0.0833 | 1.0 | 0.125 |
