## closest_candidate (stage2_ext_023_obj_2)

| candidate_label | policy_id | step_idx | blue_action_mode | blue_target_mode | red_action_mode | red_target_mode | newly_compromised_top_hosts | recovered_top_hosts | op_server0_compromised_rate | enterprise2_compromised_rate | impact_rate | restore_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| closest_candidate | stage2_ext_023_obj_2 | 0 | Analyse | User2 | DiscoverRemoteSystems | User |  |  | 0.0 | 0.0 | 0.0 | 0.0417 |
| closest_candidate | stage2_ext_023_obj_2 | 1 | Analyse | Enterprise2 | DiscoverNetworkServices |  |  |  | 0.0 | 0.0 | 0.0 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 2 | Analyse | User3 | ExploitRemoteService |  | User3(10), User4(5), User1(5) |  | 0.0 | 0.0 | 0.0 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 3 | Analyse | User2 | PrivilegeEscalate | User3 | User1(1) | User2(1) | 0.0 | 0.0 | 0.0 | 0.0417 |
| closest_candidate | stage2_ext_023_obj_2 | 4 | Analyse | User2 | DiscoverNetworkServices | User1 | User2(1) |  | 0.0 | 0.0 | 0.0 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 5 | DecoyTomcat | User0 | ExploitRemoteService | User2 | Enterprise0(13), Enterprise1(7) |  | 0.0 | 0.0 | 0.0 | 0.0417 |
| closest_candidate | stage2_ext_023_obj_2 | 6 | DecoyTomcat | Enterprise2 | PrivilegeEscalate | Enterprise0 | Enterprise1(1) |  | 0.0 | 0.0 | 0.0 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 7 | Analyse | User2 | DiscoverRemoteSystems | Enterprise | Enterprise1(1) |  | 0.0 | 0.0 | 0.0 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 8 | Analyse | User2 | DiscoverNetworkServices | Enterprise1 |  |  | 0.0 | 0.0 | 0.0 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 9 | Analyse | User2 | ExploitRemoteService | Enterprise | Enterprise2(8), Enterprise0(1) |  | 0.0 | 0.3333 | 0.0 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 10 | Analyse | User2 | ExploitRemoteService | Enterprise2 | Enterprise2(1) |  | 0.0 | 0.375 | 0.0 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 11 | Analyse | User0 | PrivilegeEscalate | Enterprise0 | Enterprise2(1) |  | 0.0 | 0.4167 | 0.0 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 12 | Analyse | User2 | DiscoverRemoteSystems | Enterprise | Op_Server0(5) |  | 0.2083 | 0.4167 | 0.0 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 13 | Analyse | User2 | DiscoverNetworkServices | Op_Server0 |  | Enterprise2(1) | 0.2083 | 0.375 | 0.0 | 0.0417 |
| closest_candidate | stage2_ext_023_obj_2 | 14 | Analyse | Enterprise2 | ExploitRemoteService | Op_Server0 | Enterprise2(3), Op_Server0(1) |  | 0.25 | 0.5 | 0.2083 | 0.0417 |
| closest_candidate | stage2_ext_023_obj_2 | 15 | Analyse | User2 | ExploitRemoteService | Op_Server0 |  |  | 0.25 | 0.5 | 0.2083 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 16 | Analyse | Enterprise2 | PrivilegeEscalate | Op_Server0 | Op_Server0(1) |  | 0.2917 | 0.5 | 0.25 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 17 | Analyse | User3 | DiscoverRemoteSystems | Enterprise | Op_Server0(1), Enterprise0(1) |  | 0.3333 | 0.5 | 0.25 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 18 | Analyse | User2 | DiscoverNetworkServices | Op_Server0 |  |  | 0.3333 | 0.5 | 0.2917 | 0.0417 |
| closest_candidate | stage2_ext_023_obj_2 | 19 | Analyse | User2 | ExploitRemoteService | Op_Server0 | Enterprise2(2) |  | 0.3333 | 0.5833 | 0.3333 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 20 | Analyse | User2 | ExploitRemoteService | Op_Server0 | Op_Server0(1) |  | 0.375 | 0.5833 | 0.3333 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 21 | Analyse | User2 | PrivilegeEscalate | Op_Server0 |  | Op_Server0(1) | 0.3333 | 0.5833 | 0.3333 | 0.0417 |
| closest_candidate | stage2_ext_023_obj_2 | 22 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Op_Server0(1) |  | 0.375 | 0.5833 | 0.3333 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 23 | Analyse | User2 | DiscoverNetworkServices | Op_Server0 | Op_Server0(1) |  | 0.4167 | 0.5833 | 0.3333 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 24 | Analyse | Enterprise2 | ExploitRemoteService | Op_Server0 | Enterprise2(1) |  | 0.4167 | 0.625 | 0.375 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 25 | Analyse | Enterprise2 | Impact | Op_Server0 |  |  | 0.4167 | 0.625 | 0.4167 | 0.0417 |
| closest_candidate | stage2_ext_023_obj_2 | 26 | Analyse | Op_Server0 | Impact | Op_Server0 |  |  | 0.4167 | 0.625 | 0.4167 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 27 | Analyse | Enterprise2 | Impact | Op_Server0 |  |  | 0.4167 | 0.625 | 0.4167 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 28 | Analyse | User2 | Impact | Op_Server0 |  |  | 0.4167 | 0.625 | 0.4167 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 29 | Analyse | User3 | ExploitRemoteService | Op_Server0 |  |  | 0.4167 | 0.625 | 0.4167 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 30 | DecoyTomcat | User2 | Impact | Op_Server0 |  | Enterprise0(1) | 0.4167 | 0.625 | 0.4167 | 0.0417 |
| closest_candidate | stage2_ext_023_obj_2 | 31 | Analyse | User2 | Impact | Op_Server0 |  |  | 0.4167 | 0.625 | 0.4167 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 32 | Analyse | User2 | Impact | Op_Server0 |  |  | 0.4167 | 0.625 | 0.4167 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 33 | Analyse | Enterprise2 | Impact | Op_Server0 |  |  | 0.4167 | 0.625 | 0.4167 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 34 | Analyse | User2 | Impact | Op_Server0 | Enterprise2(2) |  | 0.4167 | 0.7083 | 0.4167 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 35 | Analyse | User2 | Impact | Op_Server0 |  |  | 0.4167 | 0.7083 | 0.4167 | 0.0417 |
| closest_candidate | stage2_ext_023_obj_2 | 36 | Analyse | Op_Server0 | Impact | Op_Server0 |  |  | 0.4167 | 0.7083 | 0.4167 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 37 | DecoyVsftpd | Op_Server0 | Impact | Op_Server0 |  |  | 0.4167 | 0.7083 | 0.4167 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 38 | Analyse | User2 | Impact | Op_Server0 |  |  | 0.4167 | 0.7083 | 0.4167 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 39 | Analyse | User2 | Impact | Op_Server0 | Enterprise2(1) |  | 0.4167 | 0.75 | 0.4167 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 40 | Analyse | Enterprise2 | Impact | Op_Server0 | Op_Server0(1) |  | 0.4583 | 0.75 | 0.4167 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 41 | Analyse | User2 | Impact | Op_Server0 |  | Enterprise2(1) | 0.4583 | 0.7083 | 0.4167 | 0.0417 |
| closest_candidate | stage2_ext_023_obj_2 | 42 | Analyse | User2 | Impact | Op_Server0 |  |  | 0.4583 | 0.7083 | 0.4583 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 43 | Analyse | User2 | Impact | Op_Server0 |  |  | 0.4583 | 0.7083 | 0.4583 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 44 | Analyse | User2 | Impact | Op_Server0 | Enterprise2(1) |  | 0.4583 | 0.75 | 0.4583 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 45 | Analyse | User2 | Impact | Op_Server0 |  |  | 0.4583 | 0.75 | 0.4583 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 46 | Analyse | Enterprise2 | Impact | Op_Server0 |  |  | 0.4583 | 0.75 | 0.4583 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 47 | Analyse | User2 | Impact | Op_Server0 |  |  | 0.4583 | 0.75 | 0.4583 | 0.0417 |
| closest_candidate | stage2_ext_023_obj_2 | 48 | Analyse | User2 | Impact | Op_Server0 |  |  | 0.4583 | 0.75 | 0.4583 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 49 | DecoyTomcat | User3 | Impact | Op_Server0 |  |  | 0.4583 | 0.75 | 0.4583 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 50 | Analyse | User3 | Impact | Op_Server0 |  | Enterprise0(1) | 0.4583 | 0.75 | 0.4583 | 0.0417 |
| closest_candidate | stage2_ext_023_obj_2 | 51 | Analyse | User2 | Impact | Op_Server0 |  |  | 0.4583 | 0.75 | 0.4583 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 52 | Analyse | Enterprise2 | Impact | Op_Server0 |  | Enterprise0(1) | 0.4583 | 0.75 | 0.4583 | 0.0417 |
| closest_candidate | stage2_ext_023_obj_2 | 53 | Analyse | User3 | Impact | Op_Server0 |  |  | 0.4583 | 0.75 | 0.4583 | 0.0417 |
| closest_candidate | stage2_ext_023_obj_2 | 54 | Analyse | Enterprise2 | Impact | Op_Server0 |  | Enterprise0(1) | 0.4583 | 0.75 | 0.4583 | 0.0417 |
| closest_candidate | stage2_ext_023_obj_2 | 55 | Analyse | User2 | Impact | Op_Server0 | Enterprise0(1) |  | 0.4583 | 0.75 | 0.4583 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 56 | Analyse | User2 | Impact | Op_Server0 | Op_Server0(1) |  | 0.5 | 0.75 | 0.4583 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 57 | Analyse | User3 | Impact | Op_Server0 |  |  | 0.5 | 0.75 | 0.4583 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 58 | Analyse | User2 | Impact | Op_Server0 |  |  | 0.5 | 0.75 | 0.5 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 59 | Analyse | User2 | Impact | Op_Server0 |  |  | 0.5 | 0.75 | 0.5 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 60 | Analyse | User2 | Impact | Op_Server0 |  |  | 0.5 | 0.75 | 0.5 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 61 | Analyse | User2 | Impact | Op_Server0 |  |  | 0.5 | 0.75 | 0.5 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 62 | Analyse | User2 | Impact | Op_Server0 |  |  | 0.5 | 0.75 | 0.5 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 63 | Analyse | User2 | Impact | Op_Server0 |  |  | 0.5 | 0.75 | 0.5 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 64 | Analyse | User2 | Impact | Op_Server0 | Enterprise2(2) |  | 0.5 | 0.8333 | 0.5 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 65 | DecoyVsftpd | User2 | Impact | Op_Server0 |  | Enterprise2(1) | 0.5 | 0.7917 | 0.5 | 0.0417 |
| closest_candidate | stage2_ext_023_obj_2 | 66 | Analyse | Enterprise2 | Impact | Op_Server0 |  |  | 0.5 | 0.7917 | 0.5 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 67 | Analyse | User3 | Impact | Op_Server0 |  |  | 0.5 | 0.7917 | 0.5 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 68 | Analyse | User3 | Impact | Op_Server0 |  |  | 0.5 | 0.7917 | 0.5 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 69 | Analyse | User2 | Impact | Op_Server0 |  |  | 0.5 | 0.7917 | 0.5 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 70 | Analyse | User2 | Impact | Op_Server0 |  |  | 0.5 | 0.7917 | 0.5 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 71 | Analyse | User3 | Impact | Op_Server0 |  |  | 0.5 | 0.7917 | 0.5 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 72 | Analyse | Op_Server0 | Impact | Op_Server0 |  | Enterprise0(1) | 0.5 | 0.7917 | 0.5 | 0.0417 |
| closest_candidate | stage2_ext_023_obj_2 | 73 | Analyse | User2 | Impact | Op_Server0 | Op_Server0(1) |  | 0.5417 | 0.7917 | 0.5 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 74 | Analyse | User2 | Impact | Op_Server0 |  |  | 0.5417 | 0.7917 | 0.5 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 75 | Analyse | User2 | Impact | Op_Server0 |  |  | 0.5417 | 0.7917 | 0.5417 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 76 | Analyse | User2 | Impact | Op_Server0 |  |  | 0.5417 | 0.7917 | 0.5417 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 77 | Analyse | User2 | Impact | Op_Server0 |  |  | 0.5417 | 0.7917 | 0.5417 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 78 | Analyse | User2 | Impact | Op_Server0 |  |  | 0.5417 | 0.7917 | 0.5417 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 79 | Analyse | User2 | Impact | Op_Server0 |  | Enterprise0(1) | 0.5417 | 0.7917 | 0.5417 | 0.0417 |
| closest_candidate | stage2_ext_023_obj_2 | 80 | Analyse | Enterprise2 | Impact | Op_Server0 |  |  | 0.5417 | 0.7917 | 0.5417 | 0.0417 |
| closest_candidate | stage2_ext_023_obj_2 | 81 | Analyse | User2 | Impact | Op_Server0 | Op_Server0(1) |  | 0.5833 | 0.7917 | 0.5417 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 82 | Analyse | User2 | Impact | Op_Server0 |  |  | 0.5833 | 0.7917 | 0.5417 | 0.0417 |
| closest_candidate | stage2_ext_023_obj_2 | 83 | Analyse | User2 | Impact | Op_Server0 |  |  | 0.5833 | 0.7917 | 0.5833 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 84 | Analyse | User2 | Impact | Op_Server0 |  |  | 0.5833 | 0.7917 | 0.5833 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 85 | Analyse | User2 | Impact | Op_Server0 |  |  | 0.5833 | 0.7917 | 0.5833 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 86 | Analyse | User2 | Impact | Op_Server0 |  |  | 0.5833 | 0.7917 | 0.5833 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 87 | Analyse | User1 | Impact | Op_Server0 |  |  | 0.5833 | 0.7917 | 0.5833 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 88 | Analyse | Enterprise2 | Impact | Op_Server0 | Op_Server0(1) |  | 0.625 | 0.7917 | 0.5833 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 89 | Analyse | Op_Server0 | Impact | Op_Server0 |  |  | 0.625 | 0.7917 | 0.5833 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 90 | Analyse | User2 | Impact | Op_Server0 |  |  | 0.625 | 0.7917 | 0.625 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 91 | Analyse | User2 | Impact | Op_Server0 |  |  | 0.625 | 0.7917 | 0.625 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 92 | Analyse | User2 | Impact | Op_Server0 |  |  | 0.625 | 0.7917 | 0.625 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 93 | DecoyTomcat | User4 | Impact | Op_Server0 |  |  | 0.625 | 0.7917 | 0.625 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 94 | Analyse | User3 | Impact | Op_Server0 |  |  | 0.625 | 0.7917 | 0.625 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 95 | Analyse | User2 | Impact | Op_Server0 |  |  | 0.625 | 0.7917 | 0.625 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 96 | Analyse | User3 | Impact | Op_Server0 |  |  | 0.625 | 0.7917 | 0.625 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 97 | Analyse | User2 | Impact | Op_Server0 |  |  | 0.625 | 0.7917 | 0.625 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 98 | Analyse | Enterprise2 | Impact | Op_Server0 |  |  | 0.625 | 0.7917 | 0.625 | 0.0 |
| closest_candidate | stage2_ext_023_obj_2 | 99 | Analyse | User2 | Impact | Op_Server0 |  |  | 0.625 | 0.7917 | 0.625 | 0.0 |
