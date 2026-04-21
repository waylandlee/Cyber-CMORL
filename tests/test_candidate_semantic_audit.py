from __future__ import annotations

import csv
import json
from pathlib import Path

from cmorl_cyborg.export_candidate_semantic_audit import export_candidate_semantic_audit


TRACE_DIR = (
    Path(__file__).resolve().parents[1]
    / "cmorl_cyborg"
    / "outputs"
    / "paper_appendix"
    / "figure2_attack_defense_traces"
    / "no_constraint_stage2_fair"
    / "seed_0019"
    / "closest_candidate__stage2_ext_023_obj_2"
)


def test_export_candidate_semantic_audit_smoke(tmp_path: Path) -> None:
    output_dir = tmp_path / "semantic_audit"

    result = export_candidate_semantic_audit(
        trace_dir=TRACE_DIR,
        output_dir=output_dir,
    )

    assert set(result.keys()) == {"stage_a"}
    summary = result["stage_a"]
    assert summary["policy_id"] == "stage2_ext_023_obj_2"
    assert summary["total_env_runs"] == 24
    assert summary["risk_label"] == "Red"

    env_run_table = output_dir / "env_run_risk_table.csv"
    questionable_table = output_dir / "questionable_defense_actions.csv"
    summary_json = output_dir / "risk_tier_summary.json"
    casebook = output_dir / "critical_casebook.md"
    summary_md = output_dir / "semantic_risk_summary.md"
    heatmap = output_dir / "critical_path_heatmap.png"

    for path in (
        env_run_table,
        questionable_table,
        summary_json,
        casebook,
        summary_md,
        heatmap,
    ):
        assert path.exists(), path

    with env_run_table.open(encoding="utf-8") as handle:
        env_run_rows = list(csv.DictReader(handle))
    assert len(env_run_rows) == 24
    assert {row["policy_id"] for row in env_run_rows} == {"stage2_ext_023_obj_2"}

    with questionable_table.open(encoding="utf-8") as handle:
        questionable_rows = list(csv.DictReader(handle))
    assert all(row["policy_id"] == "stage2_ext_023_obj_2" for row in questionable_rows)

    summary_payload = json.loads(summary_json.read_text(encoding="utf-8"))
    assert summary_payload["total_env_runs"] == 24
    assert sum(summary_payload["tier_counts"].values()) == 24
    assert summary_payload["risk_label"] == "Red"

    summary_text = summary_md.read_text(encoding="utf-8")
    assert "stage2_ext_023_obj_2" in summary_text
    assert "`Red`" in summary_text
