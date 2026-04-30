## selected (stage2_ext_005_obj_0)

| candidate_label | policy_id | step_idx | blue_action_mode | blue_target_mode | red_action_mode | red_target_mode | newly_compromised_top_hosts | recovered_top_hosts | op_server0_compromised_rate | enterprise2_compromised_rate | impact_rate | restore_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| selected | stage2_ext_005_obj_0 | 0 | Restore | Enterprise1 | DiscoverRemoteSystems | User |  |  | 0.0 | 0.0 | 0.0 | 0.2562 |
| selected | stage2_ext_005_obj_0 | 1 | Restore | Enterprise1 | DiscoverNetworkServices |  |  |  | 0.0 | 0.0 | 0.0 | 0.2313 |
| selected | stage2_ext_005_obj_0 | 2 | Restore | Enterprise2 | ExploitRemoteService |  | User2(48), User4(41), User1(37) |  | 0.0 | 0.0 | 0.0 | 0.2125 |
| selected | stage2_ext_005_obj_0 | 3 | Remove | Enterprise2 | PrivilegeEscalate | User2 | User2(1) |  | 0.0 | 0.0 | 0.0 | 0.1562 |
| selected | stage2_ext_005_obj_0 | 4 | Restore | Enterprise2 | DiscoverNetworkServices | User2 |  |  | 0.0 | 0.0 | 0.0 | 0.225 |
| selected | stage2_ext_005_obj_0 | 5 | DecoySSHD | Enterprise1 | ExploitRemoteService |  | Enterprise1(84), Enterprise0(68) |  | 0.0 | 0.0 | 0.0 | 0.1938 |
| selected | stage2_ext_005_obj_0 | 6 | DecoyFemitter | Enterprise1 | PrivilegeEscalate | Enterprise1 | User2(1), Enterprise1(1) | Enterprise1(15), User2(1), Enterprise0(1) | 0.0 | 0.0 | 0.0 | 0.1875 |
| selected | stage2_ext_005_obj_0 | 7 | DecoySSHD | Enterprise2 | DiscoverRemoteSystems | Enterprise | Enterprise1(15), Enterprise0(1) | Enterprise1(3), Enterprise0(2) | 0.0 | 0.0 | 0.0 | 0.1625 |
| selected | stage2_ext_005_obj_0 | 8 | Remove | Enterprise1 | DiscoverNetworkServices | Enterprise1 |  | Enterprise1(7), Enterprise0(2), User3(1) | 0.0 | 0.0 | 0.0 | 0.15 |
| selected | stage2_ext_005_obj_0 | 9 | Restore | Enterprise2 | ExploitRemoteService | Enterprise | Enterprise2(78), Enterprise1(5), Enterprise0(3) | Enterprise1(4), User2(2), Enterprise0(1) | 0.0 | 0.4875 | 0.0 | 0.2 |
| selected | stage2_ext_005_obj_0 | 10 | Remove | Enterprise1 | PrivilegeEscalate | Enterprise2 | Enterprise1(3), Enterprise0(2) | Enterprise2(4), Enterprise1(3), User3(1) | 0.0 | 0.4625 | 0.0 | 0.1875 |
| selected | stage2_ext_005_obj_0 | 11 | Restore | Enterprise1 | DiscoverNetworkServices | Enterprise1 | Enterprise2(9), Enterprise1(2) | Enterprise1(10), Enterprise2(6), Enterprise0(2) | 0.0 | 0.4813 | 0.0 | 0.2812 |
| selected | stage2_ext_005_obj_0 | 12 | Restore | Enterprise1 | ExploitRemoteService | Enterprise | Op_Server0(67), Enterprise1(6) | Enterprise0(4), Enterprise2(2), User2(2) | 0.4188 | 0.4688 | 0.0 | 0.2687 |
| selected | stage2_ext_005_obj_0 | 13 | Remove | Enterprise1 | PrivilegeEscalate | Op_Server0 | Enterprise2(4) | Enterprise2(7), Enterprise1(6), Op_Server0(1) | 0.4125 | 0.45 | 0.0 | 0.1688 |
| selected | stage2_ext_005_obj_0 | 14 | Remove | Enterprise1 | ExploitRemoteService | Op_Server0 | Enterprise2(20), Op_Server0(9), Enterprise1(5) | Enterprise1(5), Op_Server0(4), Enterprise2(3) | 0.4437 | 0.5563 | 0.4125 | 0.1938 |
| selected | stage2_ext_005_obj_0 | 15 | Restore | Enterprise1 | Impact | Op_Server0 | Enterprise0(1), Enterprise2(1) | Enterprise1(5), Enterprise0(2), User2(1) | 0.4375 | 0.5563 | 0.3875 | 0.25 |
| selected | stage2_ext_005_obj_0 | 16 | Restore | Enterprise1 | Impact | Op_Server0 | Op_Server0(12), Enterprise2(6), Enterprise1(1) | Enterprise2(7), Op_Server0(4), Enterprise1(3) | 0.4875 | 0.55 | 0.4375 | 0.275 |
| selected | stage2_ext_005_obj_0 | 17 | Remove | Enterprise2 | Impact | Op_Server0 | Op_Server0(19), Enterprise0(2), Enterprise1(1) | Enterprise2(6), Op_Server0(5), Enterprise1(3) | 0.575 | 0.5125 | 0.4125 | 0.2188 |
| selected | stage2_ext_005_obj_0 | 18 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Op_Server0(5), Enterprise2(1), Enterprise1(1) | Op_Server0(5), Enterprise1(2), Enterprise2(1) | 0.575 | 0.5125 | 0.4562 | 0.175 |
| selected | stage2_ext_005_obj_0 | 19 | Restore | Enterprise2 | Impact | Op_Server0 | Enterprise2(17), Op_Server0(9), Enterprise1(1) | Enterprise2(6), Enterprise0(5), Op_Server0(2) | 0.6188 | 0.5813 | 0.5437 | 0.2375 |
| selected | stage2_ext_005_obj_0 | 20 | Restore | Enterprise1 | Impact | Op_Server0 | Op_Server0(4), Enterprise2(2), Enterprise0(2) | Op_Server0(8), Enterprise2(4), Enterprise1(3) | 0.5938 | 0.5687 | 0.5625 | 0.225 |
| selected | stage2_ext_005_obj_0 | 21 | Restore | Enterprise2 | Impact | Op_Server0 | Enterprise2(3), Op_Server0(2) | Enterprise2(6), Enterprise1(6), Op_Server0(5) | 0.575 | 0.55 | 0.5687 | 0.1938 |
| selected | stage2_ext_005_obj_0 | 22 | Restore | Enterprise2 | Impact | Op_Server0 | Op_Server0(21), Enterprise2(2), Enterprise1(1) | Enterprise2(11), Enterprise1(3), Op_Server0(3) | 0.6875 | 0.4938 | 0.5625 | 0.25 |
| selected | stage2_ext_005_obj_0 | 23 | Restore | Enterprise2 | Impact | Op_Server0 | Enterprise2(8), Op_Server0(4), Enterprise1(1) | Enterprise2(5), Enterprise1(3), Enterprise0(2) | 0.7063 | 0.5125 | 0.5563 | 0.2437 |
| selected | stage2_ext_005_obj_0 | 24 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Enterprise2(8), Op_Server0(5), Enterprise1(1) | Enterprise2(4), Enterprise1(3), Op_Server0(2) | 0.725 | 0.5375 | 0.6813 | 0.1562 |
| selected | stage2_ext_005_obj_0 | 25 | Remove | Enterprise1 | Impact | Op_Server0 | Op_Server0(2), Enterprise0(1) | Enterprise1(3), Op_Server0(3), Enterprise2(2) | 0.7188 | 0.525 | 0.6937 | 0.15 |
| selected | stage2_ext_005_obj_0 | 26 | Remove | Enterprise1 | Impact | Op_Server0 | Op_Server0(8), Enterprise1(2), Enterprise2(2) | Op_Server0(4), Enterprise1(4), Enterprise2(3) | 0.7438 | 0.5188 | 0.7063 | 0.1688 |
| selected | stage2_ext_005_obj_0 | 27 | Restore | Enterprise1 | Impact | Op_Server0 | Op_Server0(9), Enterprise1(2), Enterprise2(1) | Enterprise2(7), Enterprise1(4), Op_Server0(3) | 0.7812 | 0.4813 | 0.6937 | 0.2375 |
| selected | stage2_ext_005_obj_0 | 28 | Restore | Enterprise1 | Impact | Op_Server0 | Enterprise2(2), Op_Server0(2), Enterprise1(1) | Op_Server0(7), Enterprise2(4), Enterprise1(2) | 0.75 | 0.4688 | 0.725 | 0.2437 |
| selected | stage2_ext_005_obj_0 | 29 | Restore | Enterprise2 | Impact | Op_Server0 | Enterprise2(5), Op_Server0(4), User2(1) | Enterprise2(7), Op_Server0(4), Enterprise1(3) | 0.75 | 0.4562 | 0.7375 | 0.25 |
| selected | stage2_ext_005_obj_0 | 30 | Restore | Enterprise2 | Impact | Op_Server0 | Op_Server0(6), Enterprise2(2), Enterprise1(1) | Op_Server0(4), Enterprise1(2), Enterprise2(2) | 0.7625 | 0.4562 | 0.725 | 0.2188 |
| selected | stage2_ext_005_obj_0 | 31 | Restore | Enterprise1 | Impact | Op_Server0 | Enterprise2(7), Op_Server0(5), Enterprise1(2) | Op_Server0(5), Enterprise1(1), Enterprise2(1) | 0.7625 | 0.4938 | 0.725 | 0.2188 |
| selected | stage2_ext_005_obj_0 | 32 | DecoySSHD | Enterprise2 | Impact | Op_Server0 | Op_Server0(6), Enterprise2(1) | Enterprise2(7), Op_Server0(4), Enterprise1(2) | 0.775 | 0.4562 | 0.7312 | 0.2 |
| selected | stage2_ext_005_obj_0 | 33 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Op_Server0(6), Enterprise2(4) | Enterprise2(3), Enterprise1(3), Op_Server0(3) | 0.7937 | 0.4625 | 0.7375 | 0.1437 |
| selected | stage2_ext_005_obj_0 | 34 | Restore | Enterprise1 | Impact | Op_Server0 | Op_Server0(10), Enterprise2(3), Enterprise1(1) | Enterprise2(6), Op_Server0(4), Enterprise0(1) | 0.8313 | 0.4437 | 0.7562 | 0.25 |
| selected | stage2_ext_005_obj_0 | 35 | Remove | Enterprise1 | Impact | Op_Server0 | Op_Server0(4), Enterprise2(1) | Op_Server0(8), Enterprise2(5), Enterprise0(1) | 0.8063 | 0.4188 | 0.7688 | 0.1875 |
| selected | stage2_ext_005_obj_0 | 36 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Op_Server0(6) | Enterprise2(4), Op_Server0(2), Enterprise1(1) | 0.8313 | 0.3937 | 0.7812 | 0.175 |
| selected | stage2_ext_005_obj_0 | 37 | Remove | Enterprise1 | Impact | Op_Server0 | Op_Server0(8), Enterprise2(1) | Op_Server0(8), Enterprise2(4), Enterprise1(2) | 0.8313 | 0.375 | 0.7937 | 0.1688 |
| selected | stage2_ext_005_obj_0 | 38 | DecoySSHD | Enterprise1 | Impact | Op_Server0 | Enterprise2(4), Enterprise1(2), Op_Server0(1) | Op_Server0(4), Enterprise2(3), User2(1) | 0.8125 | 0.3812 | 0.7812 | 0.1625 |
| selected | stage2_ext_005_obj_0 | 39 | Restore | Enterprise1 | Impact | Op_Server0 | Op_Server0(6), Enterprise2(1), Enterprise1(1) | Op_Server0(8), Enterprise1(3), Enterprise2(3) | 0.8 | 0.3688 | 0.8063 | 0.25 |
| selected | stage2_ext_005_obj_0 | 40 | Restore | Enterprise1 | Impact | Op_Server0 | Op_Server0(3), Enterprise1(1), Enterprise2(1) | Enterprise2(5), Enterprise1(4), Op_Server0(4) | 0.7937 | 0.3438 | 0.7625 | 0.2437 |
| selected | stage2_ext_005_obj_0 | 41 | Remove | Enterprise1 | Impact | Op_Server0 | Op_Server0(10), Enterprise2(2), Enterprise1(1) | Op_Server0(5), Enterprise0(2), Enterprise2(1) | 0.825 | 0.35 | 0.775 | 0.2 |
| selected | stage2_ext_005_obj_0 | 42 | Restore | Enterprise2 | Impact | Op_Server0 | Op_Server0(3), Enterprise2(2), Enterprise0(1) | Op_Server0(5), Enterprise1(3), Enterprise0(3) | 0.8125 | 0.35 | 0.7625 | 0.2188 |
| selected | stage2_ext_005_obj_0 | 43 | DecoySSHD | Enterprise1 | Impact | Op_Server0 | Op_Server0(5), Enterprise1(2), Enterprise2(2) | Op_Server0(4), Enterprise0(2), Enterprise2(2) | 0.8187 | 0.35 | 0.7937 | 0.1625 |
| selected | stage2_ext_005_obj_0 | 44 | Restore | Enterprise1 | Impact | Op_Server0 | Op_Server0(4), Enterprise2(3) | Op_Server0(4), Enterprise1(3), User3(1) | 0.8187 | 0.3625 | 0.7875 | 0.2313 |
| selected | stage2_ext_005_obj_0 | 45 | Restore | Enterprise1 | Impact | Op_Server0 | Op_Server0(4), Enterprise1(3), Enterprise2(1) | Op_Server0(4), Enterprise1(3), Enterprise2(2) | 0.8187 | 0.3563 | 0.7937 | 0.1812 |
| selected | stage2_ext_005_obj_0 | 46 | Restore | Enterprise1 | Impact | Op_Server0 | Op_Server0(6), Enterprise1(2), Enterprise2(1) | Op_Server0(5), Enterprise2(1), User2(1) | 0.825 | 0.3563 | 0.7937 | 0.2062 |
| selected | stage2_ext_005_obj_0 | 47 | Restore | Enterprise2 | Impact | Op_Server0 | Op_Server0(5), Enterprise1(1) | Enterprise2(4), Op_Server0(3) | 0.8375 | 0.3312 | 0.7875 | 0.2 |
| selected | stage2_ext_005_obj_0 | 48 | Remove | Enterprise1 | Impact | Op_Server0 | Op_Server0(4), Enterprise2(1), Enterprise1(1) | Enterprise2(4), Op_Server0(3), User2(2) | 0.8438 | 0.3125 | 0.8063 | 0.2062 |
| selected | stage2_ext_005_obj_0 | 49 | DecoyFemitter | Enterprise1 | Impact | Op_Server0 | Enterprise2(5), Op_Server0(1) | Op_Server0(4), Enterprise1(3), Enterprise2(3) | 0.825 | 0.325 | 0.8187 | 0.175 |
| selected | stage2_ext_005_obj_0 | 50 | Restore | Enterprise1 | Impact | Op_Server0 | Enterprise2(4), Op_Server0(2), Enterprise1(1) | Op_Server0(7), Enterprise2(2), Enterprise1(1) | 0.7937 | 0.3375 | 0.8187 | 0.2188 |
| selected | stage2_ext_005_obj_0 | 51 | Restore | Enterprise1 | Impact | Op_Server0 | Op_Server0(4), Enterprise2(2) | Enterprise2(6), Op_Server0(5), Enterprise0(2) | 0.7875 | 0.3125 | 0.7812 | 0.225 |
| selected | stage2_ext_005_obj_0 | 52 | Remove | Enterprise1 | Impact | Op_Server0 | Op_Server0(7), Enterprise0(2), Enterprise2(1) | Enterprise2(3), Enterprise1(2) | 0.8313 | 0.3 | 0.7625 | 0.1562 |
| selected | stage2_ext_005_obj_0 | 53 | Remove | Enterprise1 | Impact | Op_Server0 | Op_Server0(4), Enterprise2(3) | Op_Server0(7), Enterprise1(2), Enterprise2(2) | 0.8125 | 0.3063 | 0.7875 | 0.2 |
| selected | stage2_ext_005_obj_0 | 54 | Remove | Enterprise1 | Impact | Op_Server0 | Enterprise2(4), Enterprise1(2), Op_Server0(2) | Enterprise1(4), Enterprise2(2), Op_Server0(1) | 0.8187 | 0.3187 | 0.7875 | 0.2062 |
| selected | stage2_ext_005_obj_0 | 55 | Remove | Enterprise1 | Impact | Op_Server0 | Op_Server0(3), Enterprise0(1), Enterprise1(1) | Enterprise2(4), Op_Server0(3), Enterprise0(1) | 0.8187 | 0.2938 | 0.8063 | 0.1625 |
| selected | stage2_ext_005_obj_0 | 56 | Remove | Enterprise1 | Impact | Op_Server0 | Enterprise2(4), Op_Server0(4), Enterprise1(1) | Enterprise2(5), Op_Server0(4), User2(1) | 0.8187 | 0.2875 | 0.8 | 0.2 |
| selected | stage2_ext_005_obj_0 | 57 | Restore | Enterprise1 | Impact | Op_Server0 | Op_Server0(5), Enterprise1(1), Enterprise0(1) | Enterprise2(5), Op_Server0(4), Enterprise1(1) | 0.825 | 0.2562 | 0.7937 | 0.2313 |
| selected | stage2_ext_005_obj_0 | 58 | Remove | Enterprise1 | Impact | Op_Server0 | Enterprise2(3), Op_Server0(2) | Op_Server0(7), Enterprise2(2) | 0.7937 | 0.2625 | 0.7937 | 0.1688 |
| selected | stage2_ext_005_obj_0 | 59 | Restore | Enterprise2 | Impact | Op_Server0 | Op_Server0(7), Enterprise2(3) | Enterprise2(4), Op_Server0(3), Enterprise1(1) | 0.8187 | 0.2562 | 0.7812 | 0.2313 |
| selected | stage2_ext_005_obj_0 | 60 | Remove | Enterprise1 | Impact | Op_Server0 | Op_Server0(4), Enterprise2(1), Enterprise0(1) | Op_Server0(6), Enterprise2(1) | 0.8063 | 0.2562 | 0.775 | 0.1812 |
| selected | stage2_ext_005_obj_0 | 61 | Restore | Enterprise1 | Impact | Op_Server0 | Enterprise2(5), Op_Server0(4) | Op_Server0(9), Enterprise2(3), Enterprise1(1) | 0.775 | 0.2687 | 0.7812 | 0.2313 |
| selected | stage2_ext_005_obj_0 | 62 | Restore | Enterprise1 | Impact | Op_Server0 | Op_Server0(3), Enterprise1(1), Enterprise2(1) | Op_Server0(6), Enterprise0(2), Enterprise2(2) | 0.7562 | 0.2625 | 0.75 | 0.225 |
| selected | stage2_ext_005_obj_0 | 63 | DecoyFemitter | Enterprise2 | Impact | Op_Server0 | Enterprise2(7), Op_Server0(5), Enterprise1(1) | Op_Server0(3), Enterprise1(2), Enterprise2(1) | 0.7688 | 0.3 | 0.7375 | 0.1938 |
| selected | stage2_ext_005_obj_0 | 64 | Remove | Enterprise1 | Impact | Op_Server0 | Op_Server0(9), Enterprise2(4) | Op_Server0(4), Enterprise1(2), Enterprise0(1) | 0.8 | 0.3187 | 0.7375 | 0.1875 |
| selected | stage2_ext_005_obj_0 | 65 | Remove | Enterprise1 | Impact | Op_Server0 | Enterprise1(2), Enterprise0(1), Enterprise2(1) | Op_Server0(3), Enterprise2(2) | 0.7875 | 0.3125 | 0.7438 | 0.2 |
| selected | stage2_ext_005_obj_0 | 66 | Remove | Enterprise1 | Impact | Op_Server0 | Op_Server0(8), Enterprise2(3), Enterprise0(1) | Enterprise2(3), Op_Server0(3), Enterprise1(1) | 0.8187 | 0.3125 | 0.7812 | 0.1938 |
| selected | stage2_ext_005_obj_0 | 67 | Restore | Enterprise1 | Impact | Op_Server0 | Enterprise2(3), Op_Server0(3) | Op_Server0(7), Enterprise2(2), Enterprise1(1) | 0.7937 | 0.3187 | 0.7688 | 0.2313 |
| selected | stage2_ext_005_obj_0 | 68 | Remove | Enterprise1 | Impact | Op_Server0 | Op_Server0(4), Enterprise2(4), Enterprise1(1) | Op_Server0(5), Enterprise2(4), Enterprise0(1) | 0.7875 | 0.3187 | 0.775 | 0.2313 |
| selected | stage2_ext_005_obj_0 | 69 | Restore | Enterprise1 | Impact | Op_Server0 | Op_Server0(8), Enterprise2(2) | Enterprise2(4), Op_Server0(2), Enterprise0(1) | 0.825 | 0.3063 | 0.7625 | 0.225 |
| selected | stage2_ext_005_obj_0 | 70 | Restore | Enterprise1 | Impact | Op_Server0 | Op_Server0(6), Enterprise2(3) | Op_Server0(4), Enterprise2(3), Enterprise1(1) | 0.8375 | 0.3063 | 0.775 | 0.225 |
| selected | stage2_ext_005_obj_0 | 71 | Restore | Enterprise2 | Impact | Op_Server0 | Op_Server0(5), Enterprise2(3), Enterprise0(1) | Op_Server0(11), Enterprise2(1) | 0.8 | 0.3187 | 0.8 | 0.2125 |
| selected | stage2_ext_005_obj_0 | 72 | Remove | Enterprise1 | Impact | Op_Server0 | Op_Server0(3), Enterprise2(1), Enterprise1(1) | Enterprise2(5), Op_Server0(2) | 0.8063 | 0.2938 | 0.7688 | 0.175 |
| selected | stage2_ext_005_obj_0 | 73 | Restore | Enterprise1 | Impact | Op_Server0 | Op_Server0(9), Enterprise2(2) | Op_Server0(4), Enterprise2(3), Enterprise0(1) | 0.8375 | 0.2875 | 0.7875 | 0.2562 |
| selected | stage2_ext_005_obj_0 | 74 | Restore | Enterprise1 | Impact | Op_Server0 | Enterprise2(5), Op_Server0(4), Enterprise1(1) | Op_Server0(7), Enterprise0(1), Enterprise2(1) | 0.8187 | 0.3125 | 0.7812 | 0.2375 |
| selected | stage2_ext_005_obj_0 | 75 | Restore | Enterprise1 | Impact | Op_Server0 | Op_Server0(3), Enterprise2(1), Enterprise0(1) | Op_Server0(4), Enterprise0(1), Enterprise2(1) | 0.8125 | 0.3125 | 0.7937 | 0.2125 |
| selected | stage2_ext_005_obj_0 | 76 | Restore | Enterprise2 | Impact | Op_Server0 | Op_Server0(4), Enterprise2(2) | Op_Server0(5), Enterprise2(2), Enterprise0(2) | 0.8063 | 0.3125 | 0.7937 | 0.2625 |
| selected | stage2_ext_005_obj_0 | 77 | DecoySSHD | Enterprise1 | Impact | Op_Server0 | Op_Server0(7), Enterprise2(7), Enterprise0(1) | Op_Server0(2), Enterprise2(1) | 0.8375 | 0.35 | 0.7812 | 0.2 |
| selected | stage2_ext_005_obj_0 | 78 | Restore | Enterprise1 | Impact | Op_Server0 | Op_Server0(2), Enterprise2(2) | Op_Server0(7), Enterprise2(1), Enterprise1(1) | 0.8063 | 0.3563 | 0.7937 | 0.2375 |
| selected | stage2_ext_005_obj_0 | 79 | Restore | Enterprise2 | Impact | Op_Server0 | Enterprise2(4), Op_Server0(3) | Op_Server0(7), Enterprise0(2), Enterprise2(1) | 0.7812 | 0.375 | 0.7937 | 0.2062 |
| selected | stage2_ext_005_obj_0 | 80 | Remove | Enterprise1 | Impact | Op_Server0 | Op_Server0(11), Enterprise2(1) | Op_Server0(4), Enterprise2(2), Enterprise1(1) | 0.825 | 0.3688 | 0.7625 | 0.1875 |
| selected | stage2_ext_005_obj_0 | 81 | Remove | Enterprise1 | Impact | Op_Server0 | Op_Server0(8), Enterprise2(2), Enterprise0(1) | Op_Server0(7), Enterprise2(3), Enterprise0(1) | 0.8313 | 0.3625 | 0.7562 | 0.1812 |
| selected | stage2_ext_005_obj_0 | 82 | DecoySSHD | Enterprise1 | Impact | Op_Server0 | Op_Server0(5), Enterprise2(1) | Enterprise2(3), Op_Server0(1) | 0.8562 | 0.35 | 0.7812 | 0.175 |
| selected | stage2_ext_005_obj_0 | 83 | Restore | Enterprise1 | Impact | Op_Server0 | Op_Server0(4), Enterprise2(4), Enterprise1(1) | Op_Server0(9), Enterprise2(3) | 0.825 | 0.3563 | 0.825 | 0.2812 |
| selected | stage2_ext_005_obj_0 | 84 | Remove | Enterprise1 | Impact | Op_Server0 | Enterprise2(6), Op_Server0(2), Enterprise1(1) | Op_Server0(7), Enterprise2(4), Enterprise1(2) | 0.7937 | 0.3688 | 0.8 | 0.1812 |
| selected | stage2_ext_005_obj_0 | 85 | Restore | Enterprise1 | Impact | Op_Server0 | Op_Server0(5), Enterprise2(2), Enterprise1(1) | Op_Server0(8), Enterprise2(4), Enterprise1(1) | 0.775 | 0.3563 | 0.7812 | 0.2062 |
| selected | stage2_ext_005_obj_0 | 86 | Remove | Enterprise1 | Impact | Op_Server0 | Enterprise2(4), Op_Server0(3) | Op_Server0(8), Enterprise2(3), Enterprise0(1) | 0.7438 | 0.3625 | 0.7438 | 0.2188 |
| selected | stage2_ext_005_obj_0 | 87 | Restore | Enterprise1 | Impact | Op_Server0 | Enterprise2(7), Op_Server0(5), Enterprise1(2) | Enterprise2(7), Op_Server0(2), User2(1) | 0.7625 | 0.3625 | 0.725 | 0.225 |
| selected | stage2_ext_005_obj_0 | 88 | Restore | Enterprise1 | Impact | Op_Server0 | Enterprise2(7), Op_Server0(5), Enterprise0(1) | Op_Server0(5), Enterprise2(4), Enterprise1(2) | 0.7625 | 0.3812 | 0.7312 | 0.2375 |
| selected | stage2_ext_005_obj_0 | 89 | Restore | Enterprise1 | Impact | Op_Server0 | Enterprise2(4), Op_Server0(4), Enterprise1(2) | Op_Server0(6), Enterprise2(3), Enterprise1(1) | 0.75 | 0.3875 | 0.7312 | 0.2562 |
| selected | stage2_ext_005_obj_0 | 90 | Remove | Enterprise1 | Impact | Op_Server0 | Op_Server0(10), Enterprise2(1), Enterprise0(1) | Op_Server0(5), Enterprise2(3), Enterprise1(2) | 0.7812 | 0.375 | 0.725 | 0.2 |
| selected | stage2_ext_005_obj_0 | 91 | Restore | Enterprise2 | Impact | Op_Server0 | Op_Server0(8), Enterprise2(4), Enterprise1(1) | Op_Server0(6), Enterprise2(5) | 0.7937 | 0.3688 | 0.7188 | 0.2313 |
| selected | stage2_ext_005_obj_0 | 92 | Restore | Enterprise1 | Impact | Op_Server0 | Op_Server0(5), Enterprise2(4), Enterprise1(1) | Enterprise2(4), Op_Server0(4) | 0.8 | 0.3688 | 0.7438 | 0.2437 |
| selected | stage2_ext_005_obj_0 | 93 | Restore | Enterprise1 | Impact | Op_Server0 | Enterprise2(4), Op_Server0(4) | Op_Server0(8), Enterprise2(3), Enterprise1(2) | 0.775 | 0.375 | 0.7688 | 0.2313 |
| selected | stage2_ext_005_obj_0 | 94 | Restore | Enterprise1 | Impact | Op_Server0 | Op_Server0(4), Enterprise2(2), Enterprise1(1) | Op_Server0(6), Enterprise2(4), Enterprise0(2) | 0.7625 | 0.3625 | 0.75 | 0.2313 |
| selected | stage2_ext_005_obj_0 | 95 | Remove | Enterprise1 | Impact | Op_Server0 | Op_Server0(12), Enterprise2(3), Enterprise0(1) | Op_Server0(7), Enterprise2(1) | 0.7937 | 0.375 | 0.7375 | 0.2062 |
| selected | stage2_ext_005_obj_0 | 96 | Remove | Enterprise1 | Impact | Op_Server0 | Op_Server0(5), Enterprise2(2), Enterprise1(1) | Op_Server0(6), Enterprise2(2), User3(1) | 0.7875 | 0.375 | 0.7188 | 0.2 |
| selected | stage2_ext_005_obj_0 | 97 | Restore | Enterprise1 | Impact | Op_Server0 | Op_Server0(7), Enterprise2(3) | Op_Server0(6), Enterprise1(2), Enterprise2(2) | 0.7937 | 0.3812 | 0.7562 | 0.2812 |
| selected | stage2_ext_005_obj_0 | 98 | Restore | Enterprise1 | Impact | Op_Server0 | Enterprise2(6), Op_Server0(5) | Enterprise2(8), Enterprise0(2), Op_Server0(1) | 0.8187 | 0.3688 | 0.75 | 0.2313 |
| selected | stage2_ext_005_obj_0 | 99 | Remove | Enterprise1 | Impact | Op_Server0 | Enterprise2(5), Op_Server0(2), Enterprise1(1) | Op_Server0(9), User2(2) | 0.775 | 0.4 | 0.7875 | 0.1688 |
