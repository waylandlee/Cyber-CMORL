## selected (stage2_ext_022_obj_1)

| candidate_label | policy_id | step_idx | blue_action_mode | blue_target_mode | red_action_mode | red_target_mode | newly_compromised_top_hosts | recovered_top_hosts | op_server0_compromised_rate | enterprise2_compromised_rate | impact_rate | restore_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| selected | stage2_ext_022_obj_1 | 0 | DecoyFemitter | Enterprise2 | DiscoverRemoteSystems | User |  |  | 0.0 | 0.0 | 0.0 | 0.1667 |
| selected | stage2_ext_022_obj_1 | 1 | Restore | Enterprise0 | DiscoverNetworkServices |  |  |  | 0.0 | 0.0 | 0.0 | 0.25 |
| selected | stage2_ext_022_obj_1 | 2 | DecoySSHD | User0 | ExploitRemoteService |  | User2(8), User4(7), User3(6) |  | 0.0 | 0.0 | 0.0 | 0.125 |
| selected | stage2_ext_022_obj_1 | 3 | DecoyFemitter | Enterprise2 | PrivilegeEscalate | User2 |  |  | 0.0 | 0.0 | 0.0 | 0.0833 |
| selected | stage2_ext_022_obj_1 | 4 | Analyse | Enterprise2 | DiscoverNetworkServices |  |  |  | 0.0 | 0.0 | 0.0 | 0.25 |
| selected | stage2_ext_022_obj_1 | 5 | DecoyFemitter | Enterprise2 | ExploitRemoteService |  | Enterprise1(11), Enterprise0(9) |  | 0.0 | 0.0 | 0.0 | 0.1667 |
| selected | stage2_ext_022_obj_1 | 6 | DecoyFemitter | Enterprise2 | PrivilegeEscalate | Enterprise1 |  |  | 0.0 | 0.0 | 0.0 | 0.1667 |
| selected | stage2_ext_022_obj_1 | 7 | DecoyHarakaSMPT | Enterprise0 | DiscoverRemoteSystems | Enterprise |  |  | 0.0 | 0.0 | 0.0 | 0.0833 |
| selected | stage2_ext_022_obj_1 | 8 | DecoySSHD | Enterprise1 | DiscoverNetworkServices |  |  | User4(1) | 0.0 | 0.0 | 0.0 | 0.125 |
| selected | stage2_ext_022_obj_1 | 9 | DecoyHarakaSMPT | Enterprise2 | ExploitRemoteService |  | Enterprise2(13), Enterprise0(2) |  | 0.0 | 0.5417 | 0.0 | 0.125 |
| selected | stage2_ext_022_obj_1 | 10 | DecoyHarakaSMPT | User2 | PrivilegeEscalate | Enterprise2 |  | User4(1) | 0.0 | 0.5417 | 0.0 | 0.0417 |
| selected | stage2_ext_022_obj_1 | 11 | DecoyApache | Op_Server0 | DiscoverNetworkServices | Enterprise0 |  |  | 0.0 | 0.5417 | 0.0 | 0.125 |
| selected | stage2_ext_022_obj_1 | 12 | Restore | Enterprise2 | ExploitRemoteService | Enterprise | Op_Server0(6) | Enterprise2(2), Enterprise0(1) | 0.25 | 0.4583 | 0.0 | 0.2917 |
| selected | stage2_ext_022_obj_1 | 13 | Restore | Enterprise2 | ExploitRemoteService | Op_Server0 | Enterprise0(1), Enterprise2(1) | Enterprise0(1) | 0.25 | 0.5 | 0.0 | 0.2083 |
| selected | stage2_ext_022_obj_1 | 14 | DecoyFemitter | Enterprise2 | ExploitRemoteService | Enterprise2 | Enterprise2(4) |  | 0.25 | 0.6667 | 0.25 | 0.0 |
| selected | stage2_ext_022_obj_1 | 15 | DecoyHarakaSMPT | Enterprise0 | PrivilegeEscalate | Op_Server0 |  |  | 0.25 | 0.6667 | 0.25 | 0.0833 |
| selected | stage2_ext_022_obj_1 | 16 | DecoyHarakaSMPT | Enterprise1 | ExploitRemoteService | Op_Server0 | Op_Server0(2) | Enterprise2(1) | 0.3333 | 0.625 | 0.25 | 0.125 |
| selected | stage2_ext_022_obj_1 | 17 | DecoyHarakaSMPT | User1 | ExploitRemoteService | Op_Server0 | Op_Server0(2) | Enterprise2(1) | 0.4167 | 0.5833 | 0.25 | 0.2083 |
| selected | stage2_ext_022_obj_1 | 18 | Analyse | Enterprise2 | Impact | Op_Server0 | Enterprise2(1) | Op_Server0(1), Enterprise2(1) | 0.375 | 0.5833 | 0.3333 | 0.1667 |
| selected | stage2_ext_022_obj_1 | 19 | Restore | Enterprise2 | Impact | Op_Server0 | Enterprise2(2) | Enterprise2(1) | 0.375 | 0.625 | 0.375 | 0.1667 |
| selected | stage2_ext_022_obj_1 | 20 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Op_Server0(3), Enterprise2(1) | Enterprise2(1) | 0.5 | 0.625 | 0.375 | 0.1667 |
| selected | stage2_ext_022_obj_1 | 21 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 |  | Enterprise2(1) | 0.5 | 0.5833 | 0.375 | 0.0833 |
| selected | stage2_ext_022_obj_1 | 22 | Analyse | User2 | Impact | Op_Server0 | Op_Server0(2), Enterprise2(1) | Enterprise2(2) | 0.5833 | 0.5417 | 0.5 | 0.125 |
| selected | stage2_ext_022_obj_1 | 23 | DecoyFemitter | Op_Server0 | Impact | Op_Server0 |  |  | 0.5833 | 0.5417 | 0.5 | 0.0833 |
| selected | stage2_ext_022_obj_1 | 24 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 |  |  | 0.5833 | 0.5417 | 0.5833 | 0.0417 |
| selected | stage2_ext_022_obj_1 | 25 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Op_Server0(1) | Op_Server0(1), Enterprise1(1), Enterprise2(1) | 0.5833 | 0.5 | 0.5833 | 0.125 |
| selected | stage2_ext_022_obj_1 | 26 | DecoyHarakaSMPT | Enterprise2 | Impact | Op_Server0 |  |  | 0.5833 | 0.5 | 0.5417 | 0.0417 |
| selected | stage2_ext_022_obj_1 | 27 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 |  | Enterprise2(1) | 0.5833 | 0.4583 | 0.5833 | 0.0833 |
| selected | stage2_ext_022_obj_1 | 28 | Restore | Enterprise2 | Impact | Op_Server0 | Op_Server0(1) | Op_Server0(1), Enterprise2(1) | 0.5833 | 0.4167 | 0.5833 | 0.2083 |
| selected | stage2_ext_022_obj_1 | 29 | DecoyHarakaSMPT | Enterprise0 | Impact | Op_Server0 | Enterprise0(1), Enterprise2(1) |  | 0.5833 | 0.4583 | 0.5417 | 0.0833 |
| selected | stage2_ext_022_obj_1 | 30 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Op_Server0(1), Enterprise2(1) | Enterprise2(1) | 0.625 | 0.4583 | 0.5833 | 0.125 |
| selected | stage2_ext_022_obj_1 | 31 | DecoyHarakaSMPT | Enterprise2 | Impact | Op_Server0 | Op_Server0(1), Enterprise2(1) | Enterprise2(1) | 0.6667 | 0.4583 | 0.5833 | 0.0417 |
| selected | stage2_ext_022_obj_1 | 32 | Analyse | Enterprise2 | Impact | Op_Server0 | Op_Server0(1) | Enterprise2(2), Enterprise0(1) | 0.7083 | 0.375 | 0.625 | 0.125 |
| selected | stage2_ext_022_obj_1 | 33 | DecoyFemitter | User2 | Impact | Op_Server0 | Enterprise0(1) |  | 0.7083 | 0.375 | 0.6667 | 0.0833 |
| selected | stage2_ext_022_obj_1 | 34 | Restore | Enterprise2 | Impact | Op_Server0 | Op_Server0(1) |  | 0.75 | 0.375 | 0.7083 | 0.25 |
| selected | stage2_ext_022_obj_1 | 35 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 |  | Enterprise0(1), Enterprise2(1) | 0.75 | 0.3333 | 0.7083 | 0.2083 |
| selected | stage2_ext_022_obj_1 | 36 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 |  | Enterprise1(1) | 0.75 | 0.3333 | 0.75 | 0.0417 |
| selected | stage2_ext_022_obj_1 | 37 | DecoyHarakaSMPT | Enterprise0 | Impact | Op_Server0 |  | Op_Server0(2) | 0.6667 | 0.3333 | 0.75 | 0.125 |
| selected | stage2_ext_022_obj_1 | 38 | DecoyHarakaSMPT | Enterprise0 | Impact | Op_Server0 | Enterprise2(1) | Enterprise1(1) | 0.6667 | 0.375 | 0.6667 | 0.2083 |
| selected | stage2_ext_022_obj_1 | 39 | DecoyApache | Enterprise2 | Impact | Op_Server0 | Op_Server0(1) | Enterprise2(2) | 0.7083 | 0.2917 | 0.6667 | 0.125 |
| selected | stage2_ext_022_obj_1 | 40 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Enterprise2(1), Op_Server0(1) | Op_Server0(1) | 0.7083 | 0.3333 | 0.6667 | 0.0417 |
| selected | stage2_ext_022_obj_1 | 41 | DecoyHarakaSMPT | Enterprise2 | Impact | Op_Server0 |  |  | 0.7083 | 0.3333 | 0.6667 | 0.0 |
| selected | stage2_ext_022_obj_1 | 42 | DecoySSHD | Enterprise1 | Impact | Op_Server0 |  | Enterprise2(1) | 0.7083 | 0.2917 | 0.7083 | 0.125 |
| selected | stage2_ext_022_obj_1 | 43 | DecoySSHD | User0 | Impact | Op_Server0 | Op_Server0(1), Enterprise2(1) |  | 0.75 | 0.3333 | 0.7083 | 0.0833 |
| selected | stage2_ext_022_obj_1 | 44 | DecoySSHD | Enterprise2 | Impact | Op_Server0 |  |  | 0.75 | 0.3333 | 0.7083 | 0.1667 |
| selected | stage2_ext_022_obj_1 | 45 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Enterprise2(1), Op_Server0(1) |  | 0.7917 | 0.375 | 0.75 | 0.0833 |
| selected | stage2_ext_022_obj_1 | 46 | DecoyApache | Enterprise2 | Impact | Op_Server0 | Op_Server0(2) | Enterprise2(1), Op_Server0(1) | 0.8333 | 0.3333 | 0.75 | 0.1667 |
| selected | stage2_ext_022_obj_1 | 47 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 |  |  | 0.8333 | 0.3333 | 0.75 | 0.0833 |
| selected | stage2_ext_022_obj_1 | 48 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Op_Server0(1) |  | 0.875 | 0.3333 | 0.8333 | 0.0417 |
| selected | stage2_ext_022_obj_1 | 49 | Restore | Enterprise2 | Impact | Op_Server0 |  |  | 0.875 | 0.3333 | 0.8333 | 0.1667 |
| selected | stage2_ext_022_obj_1 | 50 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 |  | Op_Server0(1) | 0.8333 | 0.3333 | 0.875 | 0.0833 |
| selected | stage2_ext_022_obj_1 | 51 | DecoyHarakaSMPT | Enterprise2 | Impact | Op_Server0 |  | Enterprise2(1) | 0.8333 | 0.2917 | 0.8333 | 0.125 |
| selected | stage2_ext_022_obj_1 | 52 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Op_Server0(1) |  | 0.875 | 0.2917 | 0.8333 | 0.0833 |
| selected | stage2_ext_022_obj_1 | 53 | Analyse | Op_Server0 | Impact | Op_Server0 |  |  | 0.875 | 0.2917 | 0.8333 | 0.0417 |
| selected | stage2_ext_022_obj_1 | 54 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 |  | Enterprise2(1) | 0.875 | 0.25 | 0.875 | 0.125 |
| selected | stage2_ext_022_obj_1 | 55 | DecoyHarakaSMPT | Enterprise0 | Impact | Op_Server0 |  |  | 0.875 | 0.25 | 0.875 | 0.0833 |
| selected | stage2_ext_022_obj_1 | 56 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 |  | Enterprise2(1) | 0.875 | 0.2083 | 0.875 | 0.0833 |
| selected | stage2_ext_022_obj_1 | 57 | DecoyHarakaSMPT | Defender | Impact | Op_Server0 |  |  | 0.875 | 0.2083 | 0.875 | 0.0417 |
| selected | stage2_ext_022_obj_1 | 58 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 |  |  | 0.875 | 0.2083 | 0.875 | 0.1667 |
| selected | stage2_ext_022_obj_1 | 59 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Op_Server0(1) | User4(1), Enterprise2(1), Op_Server0(1) | 0.875 | 0.1667 | 0.875 | 0.1667 |
| selected | stage2_ext_022_obj_1 | 60 | DecoyHarakaSMPT | User2 | Impact | Op_Server0 |  | Enterprise2(1), Op_Server0(1), User2(1) | 0.8333 | 0.125 | 0.8333 | 0.2083 |
| selected | stage2_ext_022_obj_1 | 61 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 |  | Op_Server0(2) | 0.75 | 0.125 | 0.8333 | 0.2083 |
| selected | stage2_ext_022_obj_1 | 62 | Analyse | Op_Server0 | Impact | Op_Server0 | Op_Server0(1), Enterprise2(1) |  | 0.7917 | 0.1667 | 0.75 | 0.0833 |
| selected | stage2_ext_022_obj_1 | 63 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 |  |  | 0.7917 | 0.1667 | 0.75 | 0.125 |
| selected | stage2_ext_022_obj_1 | 64 | DecoyApache | Enterprise2 | Impact | Op_Server0 | Enterprise2(1) | Enterprise2(1) | 0.7917 | 0.1667 | 0.7917 | 0.1667 |
| selected | stage2_ext_022_obj_1 | 65 | DecoyHarakaSMPT | Enterprise2 | Impact | Op_Server0 |  |  | 0.7917 | 0.1667 | 0.7917 | 0.1667 |
| selected | stage2_ext_022_obj_1 | 66 | DecoyHarakaSMPT | Enterprise0 | Impact | Op_Server0 | Enterprise2(1) |  | 0.7917 | 0.2083 | 0.7917 | 0.0417 |
| selected | stage2_ext_022_obj_1 | 67 | DecoyHarakaSMPT | Enterprise2 | Impact | Op_Server0 | Op_Server0(1) |  | 0.8333 | 0.2083 | 0.7917 | 0.125 |
| selected | stage2_ext_022_obj_1 | 68 | DecoyHarakaSMPT | User3 | Impact | Op_Server0 |  |  | 0.8333 | 0.2083 | 0.7917 | 0.125 |
| selected | stage2_ext_022_obj_1 | 69 | DecoyApache | Defender | Impact | Op_Server0 |  | Op_Server0(1) | 0.7917 | 0.2083 | 0.8333 | 0.0833 |
| selected | stage2_ext_022_obj_1 | 70 | DecoyHarakaSMPT | Enterprise0 | Impact | Op_Server0 |  | Enterprise0(1), Op_Server0(1) | 0.75 | 0.2083 | 0.7917 | 0.125 |
| selected | stage2_ext_022_obj_1 | 71 | Analyse | Op_Host2 | Impact | Op_Server0 | Op_Server0(1) | Op_Server0(2) | 0.7083 | 0.2083 | 0.75 | 0.0833 |
| selected | stage2_ext_022_obj_1 | 72 | Analyse | Enterprise2 | Impact | Op_Server0 | Op_Server0(1) |  | 0.75 | 0.2083 | 0.6667 | 0.0833 |
| selected | stage2_ext_022_obj_1 | 73 | DecoyHarakaSMPT | User2 | Impact | Op_Server0 | Op_Server0(2), Enterprise0(1) | Op_Server0(1), Enterprise2(1) | 0.7917 | 0.1667 | 0.7083 | 0.2083 |
| selected | stage2_ext_022_obj_1 | 74 | Restore | Enterprise2 | Impact | Op_Server0 |  | Op_Server0(2) | 0.7083 | 0.1667 | 0.7083 | 0.25 |
| selected | stage2_ext_022_obj_1 | 75 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Op_Server0(1) | Enterprise1(1), Enterprise2(1) | 0.75 | 0.125 | 0.7083 | 0.125 |
| selected | stage2_ext_022_obj_1 | 76 | Restore | Enterprise2 | Impact | Op_Server0 |  | Op_Server0(2) | 0.6667 | 0.125 | 0.7083 | 0.3333 |
| selected | stage2_ext_022_obj_1 | 77 | DecoyHarakaSMPT | User3 | Impact | Op_Server0 | Enterprise2(2) | Enterprise0(1) | 0.6667 | 0.2083 | 0.6667 | 0.0833 |
| selected | stage2_ext_022_obj_1 | 78 | DecoySSHD | Op_Host0 | Impact | Op_Server0 | Op_Server0(1) | Op_Server0(1) | 0.6667 | 0.2083 | 0.6667 | 0.0417 |
| selected | stage2_ext_022_obj_1 | 79 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Enterprise2(1) | Enterprise1(1), Op_Server0(1) | 0.625 | 0.25 | 0.625 | 0.0833 |
| selected | stage2_ext_022_obj_1 | 80 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Op_Server0(2) | Op_Server0(1) | 0.6667 | 0.25 | 0.625 | 0.125 |
| selected | stage2_ext_022_obj_1 | 81 | DecoySSHD | Enterprise1 | Impact | Op_Server0 | Op_Server0(2), Enterprise2(1) |  | 0.75 | 0.2917 | 0.5833 | 0.1667 |
| selected | stage2_ext_022_obj_1 | 82 | DecoySvchost | Enterprise2 | Impact | Op_Server0 | Op_Server0(1), Enterprise2(1) | Enterprise2(1) | 0.7917 | 0.2917 | 0.6667 | 0.1667 |
| selected | stage2_ext_022_obj_1 | 83 | Restore | User0 | Impact | Op_Server0 | Enterprise2(1) | Op_Server0(2), Enterprise2(2) | 0.7083 | 0.25 | 0.75 | 0.25 |
| selected | stage2_ext_022_obj_1 | 84 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Op_Server0(1) |  | 0.75 | 0.25 | 0.7083 | 0.125 |
| selected | stage2_ext_022_obj_1 | 85 | DecoyApache | Op_Server0 | Impact | Op_Server0 | Enterprise0(1), Op_Server0(1) | Op_Server0(1) | 0.75 | 0.25 | 0.7083 | 0.1667 |
| selected | stage2_ext_022_obj_1 | 86 | Restore | Enterprise2 | Impact | Op_Server0 | Enterprise2(1), Op_Server0(1) | Enterprise2(2) | 0.7917 | 0.2083 | 0.7083 | 0.25 |
| selected | stage2_ext_022_obj_1 | 87 | DecoyVsftpd | Enterprise2 | Impact | Op_Server0 | Enterprise2(1), Enterprise0(1) |  | 0.7917 | 0.25 | 0.75 | 0.125 |
| selected | stage2_ext_022_obj_1 | 88 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 |  |  | 0.7917 | 0.25 | 0.7917 | 0.125 |
| selected | stage2_ext_022_obj_1 | 89 | Restore | Enterprise2 | Impact | Op_Server0 | Op_Server0(1) | Enterprise0(1) | 0.8333 | 0.25 | 0.7917 | 0.25 |
| selected | stage2_ext_022_obj_1 | 90 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Op_Server0(1) |  | 0.875 | 0.25 | 0.7917 | 0.0417 |
| selected | stage2_ext_022_obj_1 | 91 | DecoyHarakaSMPT | Enterprise2 | Impact | Op_Server0 |  | Op_Server0(1), User4(1) | 0.8333 | 0.25 | 0.8333 | 0.0833 |
| selected | stage2_ext_022_obj_1 | 92 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | User4(1) |  | 0.8333 | 0.25 | 0.8333 | 0.0833 |
| selected | stage2_ext_022_obj_1 | 93 | Analyse | User0 | Impact | Op_Server0 | Op_Server0(1) | Enterprise0(1) | 0.875 | 0.25 | 0.8333 | 0.0417 |
| selected | stage2_ext_022_obj_1 | 94 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 |  | Op_Server0(2), Enterprise2(1) | 0.7917 | 0.2083 | 0.8333 | 0.2083 |
| selected | stage2_ext_022_obj_1 | 95 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 |  | Op_Server0(1) | 0.75 | 0.2083 | 0.7917 | 0.0417 |
| selected | stage2_ext_022_obj_1 | 96 | DecoyHarakaSMPT | Enterprise2 | Impact | Op_Server0 | Op_Server0(2), Enterprise2(1) |  | 0.8333 | 0.25 | 0.75 | 0.0417 |
| selected | stage2_ext_022_obj_1 | 97 | DecoyHarakaSMPT | Enterprise2 | Impact | Op_Server0 |  | Enterprise2(2) | 0.8333 | 0.1667 | 0.75 | 0.125 |
| selected | stage2_ext_022_obj_1 | 98 | Restore | Enterprise1 | Impact | Op_Server0 | Enterprise2(2) |  | 0.8333 | 0.25 | 0.8333 | 0.1667 |
| selected | stage2_ext_022_obj_1 | 99 | DecoyVsftpd | Enterprise0 | Impact | Op_Server0 |  |  | 0.8333 | 0.25 | 0.8333 | 0.125 |
