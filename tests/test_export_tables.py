from __future__ import annotations

import json

from cmorl_minicage.export_tables import _table_b_rows


def test_table_b_rows_uses_aggregated_selected_policy_ids(tmp_path) -> None:
    payload_path = tmp_path / "aggregated.json"
    payload_path.write_text(
        json.dumps(
            {
                "method_name": "ours_stage2_v2_4",
                "selected_policy_ids": [
                    "stage2_ext_008_obj_0",
                    "stage2_ext_005_obj_1",
                    "stage2_ext_005_obj_2",
                ],
                "security_return": -170.57,
                "business_return": -27.87,
                "cost_return": -20.64,
                "feasible_rate": 0.6667,
                "mean_violation": 0.4066,
                "final_critical_compromised_hosts": 0.0,
                "critical_impact_count": 0.0,
                "high_disruption_action_rate": 0.4748,
            }
        ),
        encoding="utf-8",
    )

    rows = _table_b_rows([str(payload_path)])

    assert len(rows) == 1
    assert rows[0]["method_name"] == "ours_stage2_v2_4"
    assert (
        rows[0]["selected_policy_id"]
        == "stage2_ext_008_obj_0; stage2_ext_005_obj_1; stage2_ext_005_obj_2"
    )
