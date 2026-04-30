from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import pytest
import yaml

from cmorl_cyborg.config import (
    load_lagrangian_ppo_config,
    load_preference_conditioned_ppo_config,
    load_stage1_config,
    load_stage2_config,
)
from cmorl_cyborg.export_figure2_attack_defense_trace import (
    select_figure2_replay_candidates,
)
from cmorl_cyborg.export_rq3_symmetric_analysis import (
    AuditArtifact,
    _collect_artifact_completeness,
    _collect_metric_consistency,
    _collect_phase_sanity,
)
from cmorl_cyborg.export_rq4_objective_ablation import (
    _build_matched_deployment,
    _build_projected_set_quality,
)
from cmorl_cyborg.export_rq4_ablation_summary import export_rq4_ablation_summary
from cmorl_cyborg.export_attacker_shift_summary_4obj import (
    export_attacker_shift_summary_4obj,
)
from cmorl_cyborg.export_per_seed_main_results_4obj import (
    export_per_seed_main_results_4obj,
)
from cmorl_cyborg.export_raw_vs_acceptable_assignment_4obj import (
    ACCEPTABLE_RULE,
    RAW_RULE,
    export_raw_vs_acceptable_assignment_4obj,
)
from cmorl_cyborg.export_threshold_sensitivity_4obj import (
    export_threshold_sensitivity_4obj,
)
from cmorl_cyborg.export_zero_event_confidence_bounds_4obj import (
    clopper_pearson_zero_upper,
    export_zero_event_confidence_bounds_4obj,
)
from cmorl_cyborg.export_semantic_risk_summary import (
    build_method_comparison_semantic_summary,
    build_semantic_risk_summary,
)
from cmorl_cyborg.train_lagrangian_ppo import _scalar_advantages, _update_lambdas
from cmorl_cyborg.main_table_b import generate_main_table_b
from cmorl_minicage.algorithms.selection import nondominated_filter
from cmorl_minicage.evaluate import expected_utility
from cmorl_minicage.baselines import run_weighted_sum_baseline
from cmorl_minicage.utils import load_json, save_json, simplex_grid
import numpy as np
import torch


def test_weighted_sum_and_no_constraint_4obj_configs_load() -> None:
    stage1 = load_stage1_config(
        "cmorl_cyborg/configs/paper/weighted_sum_main_4obj.yaml"
    )
    stage2 = load_stage2_config(
        "cmorl_cyborg/configs/paper/no_constraint_stage2_main_4obj.yaml"
    )

    assert stage1.model.obj_dim == 4
    assert stage1.model.critical_host_safety_enabled is True
    assert len(stage1.explicit_preferences) == 10
    assert stage2.model.obj_dim == 4
    assert stage2.extension_mode == "unconstrained"
    assert stage2.shield.mode == "pre_critical_containment_priority"


def test_preference_conditioned_ppo_4obj_configs_load() -> None:
    for seed in (7, 11, 19):
        config = load_preference_conditioned_ppo_config(
            f"cmorl_cyborg/configs/paper/pref_cond_ppo_main_4obj_seed_{seed:04d}.yaml"
        )
        assert config.seed == seed
        assert config.env.seed == seed
        assert config.env.scenario_name == "Scenario2"
        assert config.env.red_policy == "bline"
        assert config.env.max_episode_steps == 100
        assert config.model.obj_dim == 4
        assert config.model.critical_host_safety_enabled is True
        assert config.model.critical_host_safety_mode == "v2_1_dense_persistent"
        assert config.eval.eval_episodes == 3
        assert config.eval.preference_step == 0.1
        assert config.output_dir.endswith(f"seed_{seed:04d}")


def test_lagrangian_ppo_4obj_configs_load() -> None:
    for seed in (7, 11, 19):
        config = load_lagrangian_ppo_config(
            f"cmorl_cyborg/configs/paper/lagrangian_ppo_main_4obj_seed_{seed:04d}.yaml"
        )
        assert config.seed == seed
        assert config.env.seed == seed
        assert config.env.scenario_name == "Scenario2"
        assert config.env.red_policy == "bline"
        assert config.env.max_episode_steps == 100
        assert config.model.obj_dim == 4
        assert config.model.critical_host_safety_enabled is True
        assert config.model.critical_host_safety_mode == "v2_1_dense_persistent"
        assert config.eval.eval_episodes == 3
        assert config.thresholds_path.endswith("paper_4obj/table_b/shared_thresholds.json")
        assert config.output_dir.endswith(f"seed_{seed:04d}")


def test_lagrangian_ppo_4obj_scalar_advantages_use_security_and_critical() -> None:
    advantages = torch.tensor(
        [
            [[1.0, 10.0, 100.0, 1000.0]],
            [[2.0, 20.0, 200.0, 2000.0]],
        ],
        dtype=torch.float32,
    )
    lambdas = np.asarray([0.5, 0.25], dtype=np.float32)
    scalar = _scalar_advantages(advantages, lambdas)
    expected = torch.tensor(
        [[1.0 + 0.5 * 10.0 + 0.25 * 100.0 + 1000.0], [2.0 + 0.5 * 20.0 + 0.25 * 200.0 + 2000.0]],
        dtype=torch.float32,
    )
    assert torch.allclose(scalar, expected)


def test_lagrangian_ppo_lambda_update_only_uses_business_and_cost() -> None:
    lambdas = np.asarray([0.1, 0.2], dtype=np.float32)
    updated = _update_lambdas(
        lambdas,
        dual_lr=0.5,
        thresholds={"d_business": -10.0, "d_cost": -20.0},
        rollout_return=np.asarray([-1.0, -12.0, -25.0, 999.0], dtype=np.float32),
    )
    assert np.allclose(updated, np.asarray([0.1 + 0.5 * 2.0, 0.2 + 0.5 * 5.0], dtype=np.float32))


def test_weighted_sum_baseline_uses_config_explicit_preferences_by_default(
    monkeypatch,
) -> None:
    stage1 = load_stage1_config(
        "cmorl_cyborg/configs/paper/weighted_sum_main_4obj.yaml"
    )
    captured: dict[str, object] = {}

    def _fake_run_learning_baseline(stage1_config, evaluate_config, *, explicit_preferences, output_dir):
        captured["preferences"] = explicit_preferences
        captured["output_dir"] = output_dir
        return Path("buffer.json"), Path("metrics.json")

    monkeypatch.setattr(
        "cmorl_minicage.baselines._run_learning_baseline",
        _fake_run_learning_baseline,
    )

    run_weighted_sum_baseline(stage1, object(), "tmp-output")

    assert captured["preferences"] == stage1.explicit_preferences


def test_main_table_4obj_configs_have_expected_entry_counts() -> None:
    compare_config = yaml.safe_load(
        Path("cmorl_cyborg/configs/paper/compare_suite_main_4obj.yaml").read_text(
            encoding="utf-8"
        )
    )
    table_b_config = yaml.safe_load(
        Path("cmorl_cyborg/configs/paper/table_b_suite_main_4obj.yaml").read_text(
            encoding="utf-8"
        )
    )

    assert len(compare_config["entries"]) == 12
    assert len(table_b_config["entries"]) == 15
    assert sorted({entry["method_name"] for entry in compare_config["entries"]}) == [
        "ours_stage2_v2_4",
        "preference_conditioned_ppo_4obj",
        "stage1_only_4obj",
        "weighted_sum_4obj",
    ]
    assert sorted({entry["method_name"] for entry in table_b_config["entries"]}) == [
        "lagrangian_ppo_4obj",
        "no_constraint_stage2_4obj",
        "ours_stage2_v2_4",
        "stage1_only_4obj",
        "weighted_sum_4obj",
    ]
    ours_entries = [
        entry
        for entry in table_b_config["entries"]
        if entry["method_name"] == "ours_stage2_v2_4"
    ]
    assert len(ours_entries) == 3
    assert all(entry["input_kind"] == "single_policy" for entry in ours_entries)
    lagrangian_entries = [
        entry
        for entry in table_b_config["entries"]
        if entry["method_name"] == "lagrangian_ppo_4obj"
    ]
    assert len(lagrangian_entries) == 3
    assert all(entry["input_kind"] == "single_policy" for entry in lagrangian_entries)
    pref_cond_entries = [
        entry
        for entry in compare_config["entries"]
        if entry["method_name"] == "preference_conditioned_ppo_4obj"
    ]
    assert len(pref_cond_entries) == 3
    assert all(entry["artifact_kind"] == "conditioned_points" for entry in pref_cond_entries)
    assert all(
        str(entry["artifact_path"]).endswith("evaluated_points.json")
        for entry in pref_cond_entries
    )


def test_export_per_seed_main_results_4obj_exports_expected_rows(
    tmp_path: Path,
) -> None:
    outputs = export_per_seed_main_results_4obj(
        output_root=tmp_path / "exports",
        paper_table_dir=tmp_path / "paper_tables",
    )

    archive_payload = load_json(outputs["archive_quality_json"])
    assignment_payload = load_json(outputs["operational_assignment_json"])
    verification_payload = load_json(outputs["verification_summary_json"])

    archive_records = archive_payload["records"]
    assignment_records = assignment_payload["records"]

    assert len(archive_records) == 12
    assert len(assignment_records) == 15
    assert sorted({int(row["seed"]) for row in archive_records}) == [7, 11, 19]
    assert sorted({int(row["seed"]) for row in assignment_records}) == [7, 11, 19]
    assert verification_payload["all_match"] is True
    assert verification_payload["archive_quality"]["all_match"] is True
    assert verification_payload["operational_assignment"]["all_match"] is True
    assert all(item["num_records"] == 3 for item in verification_payload["archive_quality"]["comparisons"])
    assert all(
        item["hypervolume"]["matches"] and item["expected_utility"]["matches"]
        for item in verification_payload["archive_quality"]["comparisons"]
    )
    assert all(item["num_records"] == 3 for item in verification_payload["operational_assignment"]["comparisons"])
    assert all(
        item["feasible_rate"]["matches"]
        and item["mean_violation"]["matches"]
        and item["critical_impact_count"]["matches"]
        and item["final_critical_compromised_hosts"]["matches"]
        for item in verification_payload["operational_assignment"]["comparisons"]
    )

    archive_tex = Path(outputs["archive_quality_tex"]).read_text(encoding="utf-8")
    assignment_tex = Path(outputs["operational_assignment_tex"]).read_text(encoding="utf-8")
    assert "selected_policy_id" not in archive_tex
    assert "selected_policy_id" not in assignment_tex
    assert "0007" in archive_tex and "0011" in archive_tex and "0019" in archive_tex
    assert "0007" in assignment_tex and "0011" in assignment_tex and "0019" in assignment_tex

    selected_policy_id = str(assignment_records[0]["selected_policy_id"])
    assert selected_policy_id
    assert selected_policy_id not in assignment_tex

    paper_archive_tex = Path(outputs["paper_archive_quality_tex"]).read_text(encoding="utf-8")
    paper_assignment_tex = Path(outputs["paper_operational_assignment_tex"]).read_text(
        encoding="utf-8"
    )
    assert paper_archive_tex == archive_tex
    assert paper_assignment_tex == assignment_tex


def test_export_per_seed_main_results_4obj_raises_on_missing_archive_seed(
    tmp_path: Path,
) -> None:
    table_a_summary = load_json(
        "cmorl_cyborg/outputs/paper_4obj/table_a/table_a_summary.json"
    )
    table_b_summary_path = Path(
        "cmorl_cyborg/outputs/paper_4obj/table_b/table_b_summary.json"
    ).resolve()

    table_a_summary["per_run"] = [
        row
        for row in table_a_summary["per_run"]
        if not (
            str(row.get("method_name")) == "ours_stage2_v2_4"
            and int(row.get("seed", -1)) == 7
        )
    ]
    broken_table_a = tmp_path / "table_a_summary_missing_seed.json"
    save_json(broken_table_a, table_a_summary)

    with pytest.raises(ValueError, match="Expected exactly one archive-quality row"):
        export_per_seed_main_results_4obj(
            table_a_summary_path=broken_table_a,
            table_b_summary_path=table_b_summary_path,
            output_root=tmp_path / "exports",
            paper_table_dir=tmp_path / "paper_tables",
        )


def test_export_per_seed_main_results_4obj_raises_on_missing_constraint_metrics(
    tmp_path: Path,
) -> None:
    table_a_summary_path = Path(
        "cmorl_cyborg/outputs/paper_4obj/table_a/table_a_summary.json"
    ).resolve()
    table_b_summary = load_json(
        "cmorl_cyborg/outputs/paper_4obj/table_b/table_b_summary.json"
    )

    broken_output_path = tmp_path / "missing" / "constraint_metrics.json"
    table_b_summary["per_run_records"][0]["output_path"] = str(broken_output_path)
    broken_table_b = tmp_path / "table_b_summary_missing_metrics.json"
    save_json(broken_table_b, table_b_summary)

    with pytest.raises(FileNotFoundError, match="Missing constraint metrics"):
        export_per_seed_main_results_4obj(
            table_a_summary_path=table_a_summary_path,
            table_b_summary_path=broken_table_b,
            output_root=tmp_path / "exports",
            paper_table_dir=tmp_path / "paper_tables",
        )


def _raw_vs_records() -> list[dict[str, object]]:
    return [
        {
            "policy_id": "bad_security",
            "checkpoint_path": "bad_security.pt",
            "objective_vector": [10.0, -1.0, 2.0, 0.0],
            "stage": "stage2",
            "source": "synthetic",
        },
        {
            "policy_id": "bad_cost",
            "checkpoint_path": "bad_cost.pt",
            "objective_vector": [7.0, -0.5, 4.0, 0.0],
            "stage": "stage2",
            "source": "synthetic",
        },
        {
            "policy_id": "good_balanced",
            "checkpoint_path": "good_balanced.pt",
            "objective_vector": [1.0, 1.0, 1.0, 0.0],
            "stage": "stage2",
            "source": "synthetic",
        },
        {
            "policy_id": "good_critical",
            "checkpoint_path": "good_critical.pt",
            "objective_vector": [0.0, 0.5, 0.5, 5.0],
            "stage": "stage2",
            "source": "synthetic",
        },
    ]


def _write_raw_vs_fixture(
    tmp_path: Path,
    *,
    records_by_seed: dict[int, list[dict[str, object]]] | None = None,
    seeds: tuple[int, ...] = (7, 11, 19),
    preference_step: float = 0.5,
) -> tuple[Path, Path]:
    records_by_seed = records_by_seed or {
        seed: _raw_vs_records()
        for seed in seeds
    }
    preferences = simplex_grid(preference_step, 4)
    per_run = []
    for seed in seeds:
        records = [dict(record) for record in records_by_seed[seed]]
        pareto = nondominated_filter(records)
        buffer_path = tmp_path / f"seed_{seed:04d}" / "solution_buffer.json"
        save_json(
            buffer_path,
            {
                "schema_version": "0.3.0",
                "metadata": {
                    "schema_version": "0.3.0",
                    "stage": "stage2",
                    "model": {"obj_dim": 4, "hidden_size": 8},
                    "env": {"scenario_name": "Scenario2"},
                },
                "records": records,
                "pareto_front": pareto,
            },
        )
        per_run.append(
            {
                "method_name": "ours_stage2_v2_4",
                "display_group": "Ours Stage2 V2.4",
                "seed": seed,
                "artifact_kind": "buffer",
                "artifact_path": str(buffer_path),
                "expected_utility": expected_utility(pareto, preferences),
                "num_pareto_records": len(pareto),
            }
        )
    table_a_summary_path = tmp_path / "table_a_summary.json"
    save_json(
        table_a_summary_path,
        {
            "schema_version": "0.1.0",
            "per_run": per_run,
            "method_summary": [],
        },
    )
    thresholds_path = tmp_path / "shared_thresholds.json"
    save_json(thresholds_path, {"d_business": 0.0, "d_cost": 0.0})
    return table_a_summary_path, thresholds_path


def _raw_vs_fake_metrics(**kwargs) -> dict[str, float]:
    policy_id = str(kwargs["policy_id"])
    if policy_id.startswith("bad"):
        return {
            "feasible_rate": 0.0,
            "mean_violation": 5.0,
            "critical_impact_count": 2.0,
            "final_critical_compromised_hosts": 1.0,
        }
    return {
        "feasible_rate": 1.0,
        "mean_violation": 0.0,
        "critical_impact_count": 0.0,
        "final_critical_compromised_hosts": 0.0,
    }


def test_export_raw_vs_acceptable_assignment_4obj_filters_raw_pareto_choices(
    tmp_path: Path,
) -> None:
    table_a_summary_path, thresholds_path = _write_raw_vs_fixture(tmp_path)

    outputs = export_raw_vs_acceptable_assignment_4obj(
        table_a_summary_path=table_a_summary_path,
        thresholds_path=thresholds_path,
        output_root=tmp_path / "exports",
        paper_table_dir=tmp_path / "paper_tables",
        preference_step=0.5,
        metric_provider=_raw_vs_fake_metrics,
    )

    summary = load_json(outputs["raw_vs_acceptable_summary_json"])
    logs = load_json(outputs["preference_assignment_log_json"])["records"]
    verification = load_json(outputs["verification_summary_json"])
    rows = {row["rule"]: row for row in summary["records"]}

    assert sorted({int(row["seed"]) for row in logs}) == [7, 11, 19]
    assert rows[ACCEPTABLE_RULE]["feasible_assignment_rate"] == pytest.approx(1.0)
    assert rows[RAW_RULE]["feasible_assignment_rate"] < rows[ACCEPTABLE_RULE]["feasible_assignment_rate"]
    assert rows[RAW_RULE]["mean_violation"] > rows[ACCEPTABLE_RULE]["mean_violation"]
    assert rows[RAW_RULE]["critical_impact_count"] > rows[ACCEPTABLE_RULE]["critical_impact_count"]
    assert any(
        row["rule"] == RAW_RULE
        and row["selected_policy_id"].startswith("bad")
        and row["is_acceptable"] is False
        for row in logs
    )
    assert all(
        row["is_acceptable"] is True
        for row in logs
        if row["rule"] == ACCEPTABLE_RULE and row["is_assigned"] is True
    )
    assert verification["all_match"] is True
    assert verification["raw_table_a_alignment"]["all_match"] is True

    assignment_csv = Path(outputs["preference_assignment_log_csv"]).read_text(encoding="utf-8")
    summary_tex = Path(outputs["paper_raw_vs_acceptable_tex"]).read_text(encoding="utf-8")
    assert "selected_policy_id" in assignment_csv
    assert "selected_policy_id" not in summary_tex
    assert r"\caption{Raw Pareto assignment versus acceptable Pareto assignment" in summary_tex
    assert r"\label{tab:app-raw-vs-acceptable-assignment}" in summary_tex
    assert "Feasible Assign. Rate" in summary_tex


def test_export_raw_vs_acceptable_assignment_4obj_marks_empty_acceptable_set_infeasible(
    tmp_path: Path,
) -> None:
    records = [
        {
            "policy_id": "bad_only",
            "checkpoint_path": "bad_only.pt",
            "objective_vector": [5.0, -1.0, 2.0, 0.0],
            "stage": "stage2",
            "source": "synthetic",
        }
    ]
    table_a_summary_path, thresholds_path = _write_raw_vs_fixture(
        tmp_path,
        records_by_seed={7: records, 11: records, 19: records},
    )

    outputs = export_raw_vs_acceptable_assignment_4obj(
        table_a_summary_path=table_a_summary_path,
        thresholds_path=thresholds_path,
        output_root=tmp_path / "exports",
        paper_table_dir=tmp_path / "paper_tables",
        preference_step=0.5,
        metric_provider=_raw_vs_fake_metrics,
    )

    per_seed = load_json(outputs["raw_vs_acceptable_per_seed_json"])["records"]
    acceptable_rows = [row for row in per_seed if row["rule"] == ACCEPTABLE_RULE]
    assert all(row["num_assigned_preferences"] == 0 for row in acceptable_rows)
    assert all(row["num_infeasible_preferences"] > 0 for row in acceptable_rows)
    assert all(row["feasible_assignment_rate"] == 0.0 for row in acceptable_rows)


def test_export_raw_vs_acceptable_assignment_4obj_raises_on_missing_seed(
    tmp_path: Path,
) -> None:
    table_a_summary_path, thresholds_path = _write_raw_vs_fixture(
        tmp_path,
        seeds=(7, 11),
    )

    with pytest.raises(ValueError, match="Expected exactly one ours_stage2_v2_4 Table A row"):
        export_raw_vs_acceptable_assignment_4obj(
            table_a_summary_path=table_a_summary_path,
            thresholds_path=thresholds_path,
            output_root=tmp_path / "exports",
            paper_table_dir=tmp_path / "paper_tables",
            preference_step=0.5,
            metric_provider=_raw_vs_fake_metrics,
        )


def test_export_raw_vs_acceptable_assignment_4obj_raises_on_missing_checkpoint(
    tmp_path: Path,
) -> None:
    records = _raw_vs_records()
    records[0] = {**records[0], "checkpoint_path": ""}
    table_a_summary_path, thresholds_path = _write_raw_vs_fixture(
        tmp_path,
        records_by_seed={7: records, 11: _raw_vs_records(), 19: _raw_vs_records()},
    )

    with pytest.raises(ValueError, match="missing checkpoint_path"):
        export_raw_vs_acceptable_assignment_4obj(
            table_a_summary_path=table_a_summary_path,
            thresholds_path=thresholds_path,
            output_root=tmp_path / "exports",
            paper_table_dir=tmp_path / "paper_tables",
            preference_step=0.5,
            metric_provider=_raw_vs_fake_metrics,
        )


def test_export_raw_vs_acceptable_assignment_4obj_raises_on_missing_replay_metric(
    tmp_path: Path,
) -> None:
    table_a_summary_path, thresholds_path = _write_raw_vs_fixture(tmp_path)

    def _broken_metrics(**kwargs) -> dict[str, float]:
        return {
            "feasible_rate": 1.0,
            "critical_impact_count": 0.0,
            "final_critical_compromised_hosts": 0.0,
        }

    with pytest.raises(ValueError, match="missing fields"):
        export_raw_vs_acceptable_assignment_4obj(
            table_a_summary_path=table_a_summary_path,
            thresholds_path=thresholds_path,
            output_root=tmp_path / "exports",
            paper_table_dir=tmp_path / "paper_tables",
            preference_step=0.5,
            metric_provider=_broken_metrics,
        )


def _threshold_archive_records(prefix: str) -> list[dict[str, object]]:
    return [
        {
            "policy_id": f"{prefix}_high_security",
            "checkpoint_path": f"{prefix}_high_security.pt",
            "objective_vector": [6.0, -6.0, -6.0, 0.0],
            "stage": "stage2",
            "source": "synthetic",
        },
        {
            "policy_id": f"{prefix}_balanced",
            "checkpoint_path": f"{prefix}_balanced.pt",
            "objective_vector": [5.0, -2.0, -2.0, 0.0],
            "stage": "stage2",
            "source": "synthetic",
        },
        {
            "policy_id": f"{prefix}_safe",
            "checkpoint_path": f"{prefix}_safe.pt",
            "objective_vector": [4.0, 1.0, 1.0, 0.0],
            "stage": "stage2",
            "source": "synthetic",
        },
    ]


def _write_threshold_sensitivity_fixture(tmp_path: Path) -> dict[str, Path]:
    seeds = (7, 11, 19)
    compare_entries = []
    table_b_entries = []
    threshold_source_paths = []

    threshold_vectors = [
        (-5.0, -5.0),
        (-3.0, -3.0),
        (-1.0, -1.0),
        (1.0, 1.0),
        (3.0, 3.0),
    ]
    grouped_threshold_vectors = (
        threshold_vectors[:2],
        threshold_vectors[2:4],
        threshold_vectors[4:],
    )
    for seed, vectors in zip(seeds, grouped_threshold_vectors, strict=True):
        buffer_path = tmp_path / "thresholds" / f"seed_{seed:04d}" / "solution_buffer.json"
        threshold_records = [
            {
                "policy_id": f"threshold_seed_{seed:04d}_{index}",
                "checkpoint_path": f"threshold_{seed:04d}_{index}.pt",
                "objective_vector": [0.0, business, cost, 0.0],
                "stage": "stage1",
                "source": "synthetic",
            }
            for index, (business, cost) in enumerate(vectors)
        ]
        save_json(
            buffer_path,
            {
                "schema_version": "0.3.0",
                "metadata": {"model": {"obj_dim": 4}},
                "records": threshold_records,
                "pareto_front": threshold_records,
            },
        )
        threshold_source_paths.append(buffer_path)

    business_values = np.asarray([value[0] for value in threshold_vectors], dtype=np.float64)
    cost_values = np.asarray([value[1] for value in threshold_vectors], dtype=np.float64)
    official_thresholds_path = tmp_path / "official_shared_thresholds.json"
    save_json(
        official_thresholds_path,
        {
            "d_business": float(np.quantile(business_values, 0.25)),
            "d_cost": float(np.quantile(cost_values, 0.25)),
        },
    )

    for seed in seeds:
        ours_buffer = tmp_path / "ours" / f"seed_{seed:04d}" / "solution_buffer.json"
        stage1_buffer = tmp_path / "stage1" / f"seed_{seed:04d}" / "solution_buffer.json"
        weighted_buffer = tmp_path / "weighted_sum" / f"seed_{seed:04d}" / "solution_buffer.json"
        no_constraint_buffer = (
            tmp_path / "no_constraint" / f"seed_{seed:04d}" / "solution_buffer.json"
        )
        lagrangian_metadata = (
            tmp_path / "lagrangian" / f"seed_{seed:04d}" / "run_metadata.json"
        )

        for path, prefix in (
            (ours_buffer, f"ours_{seed}"),
            (stage1_buffer, f"stage1_{seed}"),
            (weighted_buffer, f"weighted_{seed}"),
            (no_constraint_buffer, f"no_constraint_{seed}"),
        ):
            records = _threshold_archive_records(prefix)
            save_json(
                path,
                {
                    "schema_version": "0.3.0",
                    "metadata": {"model": {"obj_dim": 4}},
                    "records": records,
                    "pareto_front": records,
                },
            )

        save_json(
            lagrangian_metadata,
            {
                "method_name": "lagrangian_ppo_4obj",
                "policy_id": f"lagrangian_seed_{seed:04d}",
                "checkpoint_path": f"lagrangian_seed_{seed:04d}.pt",
                "final_objective_vector": [5.5, -3.0, -3.0, 0.0],
            },
        )

        compare_entries.extend(
            [
                {
                    "method_name": "ours_stage2_v2_4",
                    "artifact_kind": "buffer",
                    "artifact_path": str(ours_buffer),
                    "display_group": "DA-CPSL",
                    "seed": seed,
                },
                {
                    "method_name": "stage1_only_4obj",
                    "artifact_kind": "buffer",
                    "artifact_path": str(stage1_buffer),
                    "display_group": "Stage-1 Only",
                    "seed": seed,
                },
                {
                    "method_name": "weighted_sum_4obj",
                    "artifact_kind": "buffer",
                    "artifact_path": str(weighted_buffer),
                    "display_group": "Weighted-Sum",
                    "seed": seed,
                },
            ]
        )
        table_b_entries.extend(
            [
                {
                    "method_name": "ours_stage2_v2_4",
                    "seed": seed,
                    "input_kind": "single_policy",
                    "input_path": str(
                        tmp_path / "ours_selected" / f"seed_{seed:04d}" / "run_metadata.json"
                    ),
                },
                {
                    "method_name": "stage1_only_4obj",
                    "seed": seed,
                    "input_kind": "buffer",
                    "input_path": str(stage1_buffer),
                },
                {
                    "method_name": "weighted_sum_4obj",
                    "seed": seed,
                    "input_kind": "buffer",
                    "input_path": str(weighted_buffer),
                },
                {
                    "method_name": "lagrangian_ppo_4obj",
                    "seed": seed,
                    "input_kind": "single_policy",
                    "input_path": str(lagrangian_metadata),
                },
                {
                    "method_name": "no_constraint_stage2_4obj",
                    "seed": seed,
                    "input_kind": "buffer",
                    "input_path": str(no_constraint_buffer),
                },
            ]
        )

    compare_config_path = tmp_path / "compare_suite_main_4obj.yaml"
    compare_config_path.write_text(
        yaml.safe_dump(
            {
                "output_dir": str(tmp_path / "table_a"),
                "entries": compare_entries,
                "preference_step": 0.1,
            }
        ),
        encoding="utf-8",
    )
    table_b_config_path = tmp_path / "table_b_suite_main_4obj.yaml"
    table_b_config_path.write_text(
        yaml.safe_dump(
            {
                "output_dir": str(tmp_path / "table_b"),
                "table_output_dir": str(tmp_path / "tables"),
                "shared_thresholds_path": str(official_thresholds_path),
                "threshold_buffer_sources": [{"path": str(path)} for path in threshold_source_paths],
                "entries": table_b_entries,
            }
        ),
        encoding="utf-8",
    )
    table_a_summary_path = tmp_path / "table_a_summary.json"
    save_json(table_a_summary_path, {"schema_version": "0.1.0", "per_run": [], "method_summary": []})
    return {
        "compare_config_path": compare_config_path,
        "table_b_config_path": table_b_config_path,
        "table_a_summary_path": table_a_summary_path,
        "official_thresholds_path": official_thresholds_path,
    }


def test_export_threshold_sensitivity_4obj_exports_expected_rows(
    tmp_path: Path,
) -> None:
    outputs = export_threshold_sensitivity_4obj(
        output_root=tmp_path / "exports",
        paper_table_dir=tmp_path / "paper_tables",
    )

    profiles = load_json(outputs["threshold_profiles_json"])
    assignment_log = load_json(outputs["assignment_log_json"])["records"]
    per_seed = load_json(outputs["per_seed_json"])["records"]
    summary = load_json(outputs["summary_json"])["records"]
    verification = load_json(outputs["verification_summary_json"])
    official_thresholds = load_json(
        "cmorl_cyborg/outputs/paper_4obj/table_b/shared_thresholds.json"
    )

    assert sorted(profiles.keys()) == ["default", "looser", "stricter"]
    assert profiles["looser"]["d_business"] <= profiles["default"]["d_business"]
    assert profiles["default"]["d_business"] <= profiles["stricter"]["d_business"]
    assert profiles["looser"]["d_cost"] <= profiles["default"]["d_cost"]
    assert profiles["default"]["d_cost"] <= profiles["stricter"]["d_cost"]
    assert profiles["default"]["d_business"] == official_thresholds["d_business"]
    assert profiles["default"]["d_cost"] == official_thresholds["d_cost"]

    assert len(assignment_log) == 12870
    assert len(per_seed) == 45
    assert len(summary) == 15
    assert sorted({int(row["seed"]) for row in assignment_log}) == [7, 11, 19]
    assert sorted({str(row["threshold_profile"]) for row in summary}) == [
        "default",
        "looser",
        "stricter",
    ]
    assert verification["all_match"] is True
    assert verification["default_threshold_alignment"]["matches"] is True
    assert verification["row_counts"]["assignment_log_rows"]["matches"] is True
    assert verification["row_counts"]["per_seed_rows"]["matches"] is True
    assert verification["row_counts"]["summary_rows"]["matches"] is True
    assert verification["method_coverage"]["matches"] is True
    assert verification["seed_coverage"]["matches"] is True
    assert verification["profile_coverage"]["matches"] is True

    assignment_csv = Path(outputs["assignment_log_csv"]).read_text(encoding="utf-8")
    summary_tex = Path(outputs["paper_tex"]).read_text(encoding="utf-8")
    assert "selected_policy_id" in assignment_csv
    assert "selected_policy_id" not in summary_tex
    assert r"\caption{Operational-threshold sensitivity" in summary_tex
    assert "Threshold Profile" in summary_tex
    assert "Feasible Assign. Rate" in summary_tex


def test_export_threshold_sensitivity_4obj_monotonic_under_synthetic_thresholds(
    tmp_path: Path,
) -> None:
    fixture = _write_threshold_sensitivity_fixture(tmp_path)

    outputs = export_threshold_sensitivity_4obj(
        compare_config_path=fixture["compare_config_path"],
        table_b_config_path=fixture["table_b_config_path"],
        table_a_summary_path=fixture["table_a_summary_path"],
        official_thresholds_path=fixture["official_thresholds_path"],
        output_root=tmp_path / "exports",
        paper_table_dir=tmp_path / "paper_tables",
    )

    per_seed_rows = load_json(outputs["per_seed_json"])["records"]
    by_method_seed = {}
    for row in per_seed_rows:
        by_method_seed.setdefault((str(row["method_name"]), int(row["seed"])), {})[
            str(row["threshold_profile"])
        ] = row

    for rows_by_profile in by_method_seed.values():
        looser = rows_by_profile["looser"]
        default = rows_by_profile["default"]
        stricter = rows_by_profile["stricter"]
        assert looser["feasible_assignment_rate"] >= default["feasible_assignment_rate"]
        assert default["feasible_assignment_rate"] >= stricter["feasible_assignment_rate"]
        assert looser["mean_violation"] <= default["mean_violation"]
        assert default["mean_violation"] <= stricter["mean_violation"]


def test_export_threshold_sensitivity_4obj_raises_on_missing_archive_method(
    tmp_path: Path,
) -> None:
    fixture = _write_threshold_sensitivity_fixture(tmp_path)
    compare_config = yaml.safe_load(fixture["compare_config_path"].read_text(encoding="utf-8"))
    compare_config["entries"] = [
        row
        for row in compare_config["entries"]
        if not (
            str(row["method_name"]) == "ours_stage2_v2_4"
            and int(row["seed"]) == 7
        )
    ]
    fixture["compare_config_path"].write_text(
        yaml.safe_dump(compare_config),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Missing compare-config archive entry"):
        export_threshold_sensitivity_4obj(
            compare_config_path=fixture["compare_config_path"],
            table_b_config_path=fixture["table_b_config_path"],
            table_a_summary_path=fixture["table_a_summary_path"],
            official_thresholds_path=fixture["official_thresholds_path"],
            output_root=tmp_path / "exports",
            paper_table_dir=tmp_path / "paper_tables",
        )


def test_export_threshold_sensitivity_4obj_raises_on_missing_seed(
    tmp_path: Path,
) -> None:
    fixture = _write_threshold_sensitivity_fixture(tmp_path)
    table_b_config = yaml.safe_load(fixture["table_b_config_path"].read_text(encoding="utf-8"))
    table_b_config["entries"] = [
        row
        for row in table_b_config["entries"]
        if not (
            str(row["method_name"]) == "lagrangian_ppo_4obj"
            and int(row["seed"]) == 19
        )
    ]
    fixture["table_b_config_path"].write_text(
        yaml.safe_dump(table_b_config),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Missing Table-B single-policy entry"):
        export_threshold_sensitivity_4obj(
            compare_config_path=fixture["compare_config_path"],
            table_b_config_path=fixture["table_b_config_path"],
            table_a_summary_path=fixture["table_a_summary_path"],
            official_thresholds_path=fixture["official_thresholds_path"],
            output_root=tmp_path / "exports",
            paper_table_dir=tmp_path / "paper_tables",
        )


def test_export_threshold_sensitivity_4obj_raises_on_missing_artifact_path(
    tmp_path: Path,
) -> None:
    fixture = _write_threshold_sensitivity_fixture(tmp_path)
    compare_config = yaml.safe_load(fixture["compare_config_path"].read_text(encoding="utf-8"))
    for row in compare_config["entries"]:
        if str(row["method_name"]) == "stage1_only_4obj" and int(row["seed"]) == 11:
            row["artifact_path"] = str(tmp_path / "missing" / "stage1_seed_0011.json")
            break
    fixture["compare_config_path"].write_text(
        yaml.safe_dump(compare_config),
        encoding="utf-8",
    )

    with pytest.raises(FileNotFoundError, match="Missing archive artifact"):
        export_threshold_sensitivity_4obj(
            compare_config_path=fixture["compare_config_path"],
            table_b_config_path=fixture["table_b_config_path"],
            table_a_summary_path=fixture["table_a_summary_path"],
            official_thresholds_path=fixture["official_thresholds_path"],
            output_root=tmp_path / "exports",
            paper_table_dir=tmp_path / "paper_tables",
        )


def test_export_threshold_sensitivity_4obj_raises_on_missing_objective_vector(
    tmp_path: Path,
) -> None:
    fixture = _write_threshold_sensitivity_fixture(tmp_path)
    ours_seed7_buffer = tmp_path / "ours" / "seed_0007" / "solution_buffer.json"
    payload = load_json(ours_seed7_buffer)
    payload["records"][0].pop("objective_vector")
    save_json(ours_seed7_buffer, payload)

    with pytest.raises(ValueError, match="4-objective vector"):
        export_threshold_sensitivity_4obj(
            compare_config_path=fixture["compare_config_path"],
            table_b_config_path=fixture["table_b_config_path"],
            table_a_summary_path=fixture["table_a_summary_path"],
            official_thresholds_path=fixture["official_thresholds_path"],
            output_root=tmp_path / "exports",
            paper_table_dir=tmp_path / "paper_tables",
        )


def _write_broken_zero_event_table_b_summary(
    tmp_path: Path,
    mutator,
) -> Path:
    summary = load_json("cmorl_cyborg/outputs/paper_4obj/table_b/table_b_summary.json")
    target_index = next(
        index
        for index, row in enumerate(summary["per_run_records"])
        if str(row["method_name"]) == "ours_stage2_v2_4" and int(row["seed"]) == 7
    )
    target_row = dict(summary["per_run_records"][target_index])
    metrics = load_json(target_row["output_path"])
    mutator(metrics)
    broken_metrics_path = tmp_path / "broken" / "constraint_metrics.json"
    save_json(broken_metrics_path, metrics)
    target_row["output_path"] = str(broken_metrics_path)
    summary["per_run_records"][target_index] = target_row
    broken_summary_path = tmp_path / "table_b_summary.json"
    save_json(broken_summary_path, summary)
    return broken_summary_path


def test_zero_event_confidence_bound_closed_forms() -> None:
    assert clopper_pearson_zero_upper(40, 0.05) == pytest.approx(0.0722, abs=5e-5)
    assert clopper_pearson_zero_upper(120, 0.05) == pytest.approx(0.0247, abs=5e-5)


def test_export_zero_event_confidence_bounds_4obj_exports_expected_rows(
    tmp_path: Path,
) -> None:
    outputs = export_zero_event_confidence_bounds_4obj(
        output_root=tmp_path / "exports",
        paper_table_dir=tmp_path / "paper_tables",
    )

    per_seed = load_json(outputs["zero_event_bounds_per_seed_json"])["records"]
    summary = load_json(outputs["zero_event_bounds_summary_json"])["records"]
    verification = load_json(outputs["verification_summary_json"])

    assert len(per_seed) == 60
    assert len(summary) == 20
    assert sorted({int(row["seed"]) for row in per_seed}) == [7, 11, 19]
    assert all(
        values == [120]
        for values in verification["episodes_by_method"].values()
    )
    assert verification["all_match"] is True
    assert verification["row_count_checks"]["per_seed_rows"]["matches"] is True
    assert verification["row_count_checks"]["summary_rows"]["matches"] is True
    assert verification["method_coverage"]["matches"] is True
    assert verification["seed_coverage"]["matches"] is True
    assert verification["zero_bound_applicability"]["zero_summary_rows"] == 12

    zero_rows = [row for row in summary if row["bound_applicable"] is True]
    assert len(zero_rows) == 12
    assert all(int(row["observed_count"]) == 0 for row in zero_rows)
    assert all(
        row["clopper_pearson_upper"] == pytest.approx(0.024655401055656334)
        for row in zero_rows
    )
    ours_ever = next(
        row
        for row in summary
        if row["method_name"] == "ours_stage2_v2_4"
        and row["event_key"] == "ever_critical_breach"
    )
    assert ours_ever["total_episodes"] == 120
    assert ours_ever["observed_count"] == 0
    assert ours_ever["bound_applicable"] is True
    weighted_ever = next(
        row
        for row in summary
        if row["method_name"] == "weighted_sum_4obj"
        and row["event_key"] == "ever_critical_breach"
    )
    assert weighted_ever["observed_count"] > 0
    assert weighted_ever["bound_applicable"] is False
    assert weighted_ever["clopper_pearson_upper"] is None

    tex = Path(outputs["paper_zero_event_bounds_tex"]).read_text(encoding="utf-8")
    assert r"\caption{Zero-observed critical-event confidence bounds" in tex
    assert r"\label{tab:app-zero-event-confidence-bounds}" in tex
    assert "Observed Events / Episodes" in tex
    assert "selected_policy_id" not in tex
    assert "constraint_metrics" not in tex
    assert ".pt" not in tex


def test_export_zero_event_confidence_bounds_raises_on_missing_episode_count(
    tmp_path: Path,
) -> None:
    table_b_summary_path = _write_broken_zero_event_table_b_summary(
        tmp_path,
        lambda metrics: metrics.pop("semantic_eval_episodes"),
    )

    with pytest.raises(ValueError, match="Missing semantic_eval_episodes"):
        export_zero_event_confidence_bounds_4obj(
            table_b_summary_path=table_b_summary_path,
            output_root=tmp_path / "exports",
            paper_table_dir=tmp_path / "paper_tables",
        )


def test_export_zero_event_confidence_bounds_raises_on_missing_event_metric(
    tmp_path: Path,
) -> None:
    table_b_summary_path = _write_broken_zero_event_table_b_summary(
        tmp_path,
        lambda metrics: metrics.pop("ever_critical_breach_rate"),
    )

    with pytest.raises(ValueError, match="Missing event metric ever_critical_breach_rate"):
        export_zero_event_confidence_bounds_4obj(
            table_b_summary_path=table_b_summary_path,
            output_root=tmp_path / "exports",
            paper_table_dir=tmp_path / "paper_tables",
        )


def test_export_zero_event_confidence_bounds_raises_on_fractional_count(
    tmp_path: Path,
) -> None:
    def _break_rate(metrics):
        metrics["ever_critical_breach_rate"] = 0.123

    table_b_summary_path = _write_broken_zero_event_table_b_summary(
        tmp_path,
        _break_rate,
    )

    with pytest.raises(ValueError, match="Could not reconstruct integer observed count"):
        export_zero_event_confidence_bounds_4obj(
            table_b_summary_path=table_b_summary_path,
            output_root=tmp_path / "exports",
            paper_table_dir=tmp_path / "paper_tables",
        )


def test_generate_main_table_b_supports_precomputed_metrics(
    tmp_path: Path, monkeypatch
) -> None:
    metrics_a = tmp_path / "metrics_seed7.json"
    metrics_b = tmp_path / "metrics_seed11.json"
    save_json(
        metrics_a,
        {
            "method_name": "ours_stage2_v2_4",
            "selected_policy_id": "policy_a",
            "security_return": -100.0,
            "business_return": -20.0,
            "cost_return": -10.0,
            "feasible_rate": 1.0,
            "mean_violation": 0.0,
            "final_critical_compromised_hosts": 0.0,
            "critical_impact_count": 0.0,
            "high_disruption_action_rate": 0.2,
        },
    )
    save_json(
        metrics_b,
        {
            "method_name": "ours_stage2_v2_4",
            "selected_policy_id": "policy_b",
            "security_return": -200.0,
            "business_return": -30.0,
            "cost_return": -20.0,
            "feasible_rate": 0.5,
            "mean_violation": 0.8,
            "final_critical_compromised_hosts": 0.0,
            "critical_impact_count": 0.0,
            "high_disruption_action_rate": 0.4,
        },
    )
    dummy_threshold_source = tmp_path / "threshold_buffer.json"
    dummy_threshold_source.write_text("{}", encoding="utf-8")

    config_path = tmp_path / "table_b.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "output_dir": str(tmp_path / "table_b"),
                "table_output_dir": str(tmp_path / "tables"),
                "shared_thresholds_path": str(tmp_path / "thresholds.json"),
                "threshold_buffer_sources": [{"path": str(dummy_threshold_source)}],
                "entries": [
                    {
                        "method_name": "ours_stage2_v2_4",
                        "seed": 7,
                        "input_kind": "precomputed_metrics",
                        "input_path": str(metrics_a),
                    },
                    {
                        "method_name": "ours_stage2_v2_4",
                        "seed": 11,
                        "input_kind": "precomputed_metrics",
                        "input_path": str(metrics_b),
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    def _fake_thresholds(paths: list[str], output_path: str | Path) -> dict[str, float]:
        save_json(output_path, {"d_business": -125.0})
        return {"d_business": -125.0}

    def _should_not_run(*args, **kwargs):  # pragma: no cover
        raise AssertionError("evaluate_constraints should not run for precomputed metrics")

    monkeypatch.setattr("cmorl_cyborg.main_table_b.compute_shared_thresholds", _fake_thresholds)
    monkeypatch.setattr("cmorl_cyborg.main_table_b.evaluate_constraints", _should_not_run)

    summary_path = generate_main_table_b(config_path)

    summary = load_json(summary_path)
    assert len(summary["aggregated_paths"]) == 1
    aggregate = load_json(summary["aggregated_paths"][0])
    assert aggregate["method_name"] == "ours_stage2_v2_4"
    assert aggregate["selected_policy_ids"] == ["policy_a", "policy_b"]
    assert aggregate["security_return"] == -150.0
    assert aggregate["business_return"] == -25.0
    assert aggregate["feasible_rate"] == 0.75


def test_generate_main_table_b_supports_single_policy_entries(
    tmp_path: Path, monkeypatch
) -> None:
    metadata_a = tmp_path / "policy_seed7.json"
    metadata_b = tmp_path / "policy_seed11.json"
    save_json(
        metadata_a,
        {
            "method_name": "ours_stage2_v2_4",
            "policy_id": "policy_a",
            "checkpoint_path": str(tmp_path / "policy_a.pt"),
            "final_objective_vector": [-10.0, -20.0, -30.0, 0.0],
            "env": {"num_envs": 8},
            "model": {"obj_dim": 4},
            "shield": {"mode": "pre_critical_containment_priority"},
        },
    )
    save_json(
        metadata_b,
        {
            "method_name": "ours_stage2_v2_4",
            "policy_id": "policy_b",
            "checkpoint_path": str(tmp_path / "policy_b.pt"),
            "final_objective_vector": [-11.0, -21.0, -31.0, 0.0],
            "env": {"num_envs": 8},
            "model": {"obj_dim": 4},
            "shield": {"mode": "pre_critical_containment_priority"},
        },
    )
    dummy_threshold_source = tmp_path / "threshold_buffer.json"
    dummy_threshold_source.write_text("{}", encoding="utf-8")

    config_path = tmp_path / "table_b_single_policy.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "output_dir": str(tmp_path / "table_b"),
                "table_output_dir": str(tmp_path / "tables"),
                "shared_thresholds_path": str(tmp_path / "thresholds.json"),
                "threshold_buffer_sources": [{"path": str(dummy_threshold_source)}],
                "entries": [
                    {
                        "method_name": "ours_stage2_v2_4",
                        "seed": 7,
                        "input_kind": "single_policy",
                        "input_path": str(metadata_a),
                    },
                    {
                        "method_name": "ours_stage2_v2_4",
                        "seed": 11,
                        "input_kind": "single_policy",
                        "input_path": str(metadata_b),
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    def _fake_thresholds(paths: list[str], output_path: str | Path) -> dict[str, float]:
        save_json(output_path, {"d_business": -125.0, "d_cost": -22.0})
        return {"d_business": -125.0, "d_cost": -22.0}

    calls: list[dict[str, object]] = []

    def _fake_evaluate_constraints(**kwargs):
        calls.append(dict(kwargs))
        input_path = Path(str(kwargs["input_path"]))
        metadata = load_json(input_path)
        offset = 0.0 if metadata["policy_id"] == "policy_a" else 10.0
        return {
            "method_name": kwargs["method_name"],
            "selected_policy_id": metadata["policy_id"],
            "security_return": -100.0 - offset,
            "business_return": -20.0 - offset,
            "cost_return": -10.0 - offset,
            "feasible_rate": 1.0 - (offset / 20.0),
            "mean_violation": offset / 10.0,
            "final_critical_compromised_hosts": 0.0,
            "critical_impact_count": 0.0,
            "high_disruption_action_rate": 0.25 + (offset / 100.0),
        }

    monkeypatch.setattr("cmorl_cyborg.main_table_b.compute_shared_thresholds", _fake_thresholds)
    monkeypatch.setattr("cmorl_cyborg.main_table_b.evaluate_constraints", _fake_evaluate_constraints)

    summary_path = generate_main_table_b(config_path)

    assert len(calls) == 2
    assert all(call["input_kind"] == "single_policy" for call in calls)
    assert all(call["selection_source"] == "pareto" for call in calls)
    aggregate = load_json(load_json(summary_path)["aggregated_paths"][0])
    assert aggregate["selected_policy_ids"] == ["policy_a", "policy_b"]
    assert aggregate["security_return"] == -105.0
    assert aggregate["business_return"] == -25.0
    assert aggregate["feasible_rate"] == 0.75


def test_build_semantic_risk_summary_aggregates_selected_and_baseline(tmp_path: Path) -> None:
    selected_a = tmp_path / "selected_a.json"
    baseline_a = tmp_path / "baseline_a.json"
    selected_b = tmp_path / "selected_b.json"
    baseline_b = tmp_path / "baseline_b.json"

    def _payload(*, ever: float, persistent: float, q4: float, tier1: float, restore: float, decoy: float, focus: float) -> dict[str, object]:
        return {
            "ever_critical_breach_rate": ever,
            "persistent_critical_breach_rate": persistent,
            "mean_critical_dwell_steps": 1.0,
            "high_confidence_env_run_rate": 0.0,
            "questionable_rule_env_run_rates": {
                "Q4_user_focus_after_enterprise_foothold": q4,
            },
            "tier_rates": {
                "Tier 0 Safe": 0.0,
                "Tier 1 Near-Miss": tier1,
                "Tier 2 Transient Critical Breach": 0.0,
                "Tier 3 Persistent Critical Breach": persistent,
            },
            "precritical_action_family_step_rates": {
                "restore": restore,
                "remove": 0.0,
                "analyse": 0.0,
                "decoy": decoy,
                "other": 0.0,
            },
            "precritical_compromised_target_focus_step_rate": focus,
        }

    save_json(selected_a, _payload(ever=0.0, persistent=0.0, q4=0.0, tier1=1.0, restore=1.0, decoy=0.0, focus=1.0))
    save_json(baseline_a, _payload(ever=1.0, persistent=0.8, q4=0.6, tier1=0.2, restore=0.2, decoy=0.5, focus=0.3))
    save_json(selected_b, _payload(ever=0.1, persistent=0.0, q4=0.1, tier1=0.9, restore=0.8, decoy=0.1, focus=0.9))
    save_json(baseline_b, _payload(ever=0.9, persistent=0.7, q4=0.5, tier1=0.3, restore=0.3, decoy=0.4, focus=0.4))

    final_a = tmp_path / "seed_0007_final_summary.json"
    final_b = tmp_path / "seed_0011_final_summary.json"
    save_json(
        final_a,
        {
            "seed": 7,
            "final_selected_policy_id": "policy_a",
            "baseline_policy_id": "baseline_a",
            "selected_risk_summary_path": str(selected_a),
            "baseline_risk_summary_path": str(baseline_a),
        },
    )
    save_json(
        final_b,
        {
            "seed": 11,
            "final_selected_policy_id": "policy_b",
            "baseline_policy_id": "baseline_b",
            "selected_risk_summary_path": str(selected_b),
            "baseline_risk_summary_path": str(baseline_b),
        },
    )

    output_path = build_semantic_risk_summary(
        [final_a, final_b],
        output_dir=tmp_path / "semantic",
    )

    aggregate = load_json(output_path)
    assert aggregate["selected"]["ever_critical_breach_rate"] == 0.05
    assert aggregate["baseline"]["ever_critical_breach_rate"] == 0.95
    assert aggregate["delta"]["ever_critical_breach_rate"] == -0.9
    assert aggregate["selected"]["precritical_action_family_step_rates.restore"] == 0.9
    assert aggregate["baseline"]["precritical_action_family_step_rates.decoy"] == 0.45
    assert (tmp_path / "semantic" / "semantic_risk_seedwise.csv").exists()
    assert (tmp_path / "semantic" / "semantic_risk_summary.md").exists()


def test_selected_only_trace_export_mode_keeps_only_selected_candidate() -> None:
    tight_summary = {"selected_policy_id": "policy_selected"}
    reevaluated_summary = {
        "closest_candidate_policy_id": "policy_closest",
        "candidate_rows": [
            {
                "policy_id": "policy_best_feasible",
                "is_reevaluated_feasible": True,
                "reevaluated_security_return": -10.0,
            }
        ],
    }

    selected_only = select_figure2_replay_candidates(
        "no_constraint_stage2_fair",
        tight_summary,
        reevaluated_summary,
        selection_mode="selected_only",
    )
    default_mode = select_figure2_replay_candidates(
        "no_constraint_stage2_fair",
        tight_summary,
        reevaluated_summary,
    )

    assert [(item.candidate_label, item.policy_id) for item in selected_only] == [
        ("selected", "policy_selected")
    ]
    assert [item.policy_id for item in default_mode] == [
        "policy_selected",
        "policy_closest",
        "policy_best_feasible",
    ]


def test_build_method_comparison_semantic_summary(tmp_path: Path) -> None:
    left_a = tmp_path / "left_seed7.json"
    right_a = tmp_path / "right_seed7.json"
    left_b = tmp_path / "left_seed11.json"
    right_b = tmp_path / "right_seed11.json"

    def _payload(*, ever: float, persistent: float, q4: float, tier1: float, restore: float, decoy: float, focus: float) -> dict[str, object]:
        return {
            "ever_critical_breach_rate": ever,
            "persistent_critical_breach_rate": persistent,
            "mean_critical_dwell_steps": ever * 10.0,
            "high_confidence_env_run_rate": ever,
            "questionable_rule_env_run_rates": {
                "Q2_user_action_during_critical_breach": ever,
                "Q3_missed_immediate_response_to_critical_hit": persistent,
                "Q4_user_focus_after_enterprise_foothold": q4,
                "Q5_repeated_low_value_decoy_loop": decoy,
            },
            "tier_rates": {
                "Tier 0 Safe": 0.0,
                "Tier 1 Near-Miss": tier1,
                "Tier 2 Transient Critical Breach": max(0.0, 1.0 - tier1 - persistent),
                "Tier 3 Persistent Critical Breach": persistent,
            },
            "precritical_action_family_step_rates": {
                "restore": restore,
                "remove": 0.0,
                "analyse": 0.0,
                "decoy": decoy,
                "other": 0.0,
            },
            "precritical_compromised_target_focus_step_rate": focus,
        }

    save_json(left_a, _payload(ever=0.0, persistent=0.0, q4=0.0, tier1=1.0, restore=1.0, decoy=0.0, focus=1.0))
    save_json(right_a, _payload(ever=1.0, persistent=0.8, q4=0.7, tier1=0.1, restore=0.2, decoy=0.6, focus=0.3))
    save_json(left_b, _payload(ever=0.1, persistent=0.0, q4=0.1, tier1=0.9, restore=0.8, decoy=0.1, focus=0.9))
    save_json(right_b, _payload(ever=0.9, persistent=0.7, q4=0.6, tier1=0.2, restore=0.3, decoy=0.5, focus=0.4))

    compare_a = tmp_path / "seed_0007_compare.json"
    compare_b = tmp_path / "seed_0011_compare.json"
    save_json(
        compare_a,
        {
            "seed": 7,
            "left_method_name": "ours_stage2_fair",
            "left_display_name": "Constraint-Aware Stage-2",
            "left_policy_id": "ours_policy_a",
            "left_risk_summary_path": str(left_a),
            "right_method_name": "no_constraint_stage2_fair",
            "right_display_name": "Unconstrained Stage-2",
            "right_policy_id": "no_constraint_policy_a",
            "right_risk_summary_path": str(right_a),
        },
    )
    save_json(
        compare_b,
        {
            "seed": 11,
            "left_method_name": "ours_stage2_fair",
            "left_display_name": "Constraint-Aware Stage-2",
            "left_policy_id": "ours_policy_b",
            "left_risk_summary_path": str(left_b),
            "right_method_name": "no_constraint_stage2_fair",
            "right_display_name": "Unconstrained Stage-2",
            "right_policy_id": "no_constraint_policy_b",
            "right_risk_summary_path": str(right_b),
        },
    )

    output_path = build_method_comparison_semantic_summary(
        [compare_a, compare_b],
        output_dir=tmp_path / "rq3",
        left_method_name="ours_stage2_fair",
        left_display_name="Constraint-Aware Stage-2",
        right_method_name="no_constraint_stage2_fair",
        right_display_name="Unconstrained Stage-2",
    )

    aggregate = load_json(output_path)
    assert aggregate["left"]["ever_critical_breach_rate"] == 0.05
    assert aggregate["right"]["ever_critical_breach_rate"] == 0.95
    assert aggregate["delta_left_minus_right"]["ever_critical_breach_rate"] == -0.9
    assert aggregate["left"]["precritical_action_family_step_rates.restore"] == 0.9
    assert aggregate["right"]["precritical_action_family_step_rates.decoy"] == 0.55
    assert (tmp_path / "rq3" / "semantic_comparison_seedwise.csv").exists()
    assert (tmp_path / "rq3" / "semantic_comparison_summary.md").exists()


def test_rq3_verification_helpers(tmp_path: Path) -> None:
    trace_dir = tmp_path / "traces" / "ours_stage2_v2_4" / "seed_0007" / "selected__policy_a"
    audit_dir = tmp_path / "audits" / "ours_stage2_v2_4" / "seed_0007" / "selected__policy_a_semantic_audit_replay2"
    analysis_dir = tmp_path / "trace_analysis" / "ours_stage2_v2_4" / "seed_0007"
    trace_dir.mkdir(parents=True, exist_ok=True)
    audit_dir.mkdir(parents=True, exist_ok=True)
    analysis_dir.mkdir(parents=True, exist_ok=True)

    save_json(trace_dir / "trace_manifest.json", {"policy_id": "policy_a"})
    save_json(trace_dir / "episode_summaries.json", {"episodes": 2})
    save_json(trace_dir / "topology_snapshot.json", {"scenario_name": "Scenario2"})
    (trace_dir / "episode_000.jsonl").write_text('{"step_idx": 0}\n', encoding="utf-8")
    (trace_dir / "episode_001.jsonl").write_text('{"step_idx": 1}\n', encoding="utf-8")

    save_json(audit_dir / "risk_tier_summary.json", {"ever_critical_breach_rate": 0.0})
    (audit_dir / "critical_casebook.md").write_text("# casebook\n", encoding="utf-8")
    (audit_dir / "questionable_defense_actions.csv").write_text("step_idx\n", encoding="utf-8")
    (audit_dir / "critical_path_heatmap.png").write_bytes(b"png")

    (analysis_dir / "timeline_table.csv").write_text("step_idx\n", encoding="utf-8")
    (analysis_dir / "timeline_table.md").write_text("# timeline\n", encoding="utf-8")
    (analysis_dir / "host_level_summary.csv").write_text("hostname\n", encoding="utf-8")
    (analysis_dir / "host_attack_defense_heatmap.png").write_bytes(b"png")

    artifact = AuditArtifact(
        method_name="ours_stage2_v2_4",
        display_name="Constraint-Aware Stage-2",
        seed=7,
        policy_id="policy_a",
        trace_dir=trace_dir,
        audit_dir=audit_dir,
        risk_summary_path=audit_dir / "risk_tier_summary.json",
        trace_analysis_dir=analysis_dir,
    )

    completeness_rows = _collect_artifact_completeness([artifact], eval_episodes=2)
    assert completeness_rows[0]["episode_file_count_ok"] is True
    assert completeness_rows[0]["all_required_present"] is True

    phase_summary = {
        "seed_rows": [
            {
                "method_name": "ours_stage2_v2_4",
                "seed": 7,
                "phase_name": "foothold",
                "total_phase_steps": 1,
                "action_rate.restore": 0.0,
                "action_rate.decoy": 0.0,
                "action_rate.analyse": 1.0,
                "action_rate.remove": 0.0,
                "action_rate.sleep": 0.0,
                "action_rate.other": 0.0,
                "target_rate.critical_path_host": 0.0,
                "target_rate.compromised_enterprise_or_operational_host": 0.0,
                "target_rate.user_host": 1.0,
                "target_rate.non_compromised_host": 0.0,
                "target_rate.no_target_or_other": 0.0,
            },
            {
                "method_name": "ours_stage2_v2_4",
                "seed": 7,
                "phase_name": "precritical",
                "total_phase_steps": 1,
                "action_rate.restore": 1.0,
                "action_rate.decoy": 0.0,
                "action_rate.analyse": 0.0,
                "action_rate.remove": 0.0,
                "action_rate.sleep": 0.0,
                "action_rate.other": 0.0,
                "target_rate.critical_path_host": 1.0,
                "target_rate.compromised_enterprise_or_operational_host": 0.0,
                "target_rate.user_host": 0.0,
                "target_rate.non_compromised_host": 0.0,
                "target_rate.no_target_or_other": 0.0,
            },
            {
                "method_name": "ours_stage2_v2_4",
                "seed": 7,
                "phase_name": "critical_present",
                "total_phase_steps": 0,
                "action_rate.restore": 0.0,
                "action_rate.decoy": 0.0,
                "action_rate.analyse": 0.0,
                "action_rate.remove": 0.0,
                "action_rate.sleep": 0.0,
                "action_rate.other": 0.0,
                "target_rate.critical_path_host": 0.0,
                "target_rate.compromised_enterprise_or_operational_host": 0.0,
                "target_rate.user_host": 0.0,
                "target_rate.non_compromised_host": 0.0,
                "target_rate.no_target_or_other": 0.0,
            },
        ]
    }
    phase_rows = _collect_phase_sanity([artifact], phase_summary)
    assert phase_rows[0]["phase_total_matches_trace"] is True
    assert phase_rows[0]["all_phase_checks_ok"] is True


def test_metric_consistency_helper_matches_built_semantic_summary(tmp_path: Path) -> None:
    left = tmp_path / "left.json"
    right = tmp_path / "right.json"
    payload = {
        "ever_critical_breach_rate": 0.0,
        "persistent_critical_breach_rate": 0.0,
        "mean_critical_dwell_steps": 0.0,
        "high_confidence_env_run_rate": 0.0,
        "questionable_rule_env_run_rates": {
            "Q2_user_action_during_critical_breach": 0.0,
            "Q3_missed_immediate_response_to_critical_hit": 0.0,
            "Q4_user_focus_after_enterprise_foothold": 0.1,
            "Q5_repeated_low_value_decoy_loop": 0.0,
        },
        "tier_rates": {
            "Tier 0 Safe": 0.0,
            "Tier 1 Near-Miss": 1.0,
            "Tier 2 Transient Critical Breach": 0.0,
            "Tier 3 Persistent Critical Breach": 0.0,
        },
        "precritical_action_family_step_rates": {
            "restore": 1.0,
            "remove": 0.0,
            "analyse": 0.0,
            "decoy": 0.0,
            "other": 0.0,
        },
        "precritical_compromised_target_focus_step_rate": 1.0,
    }
    save_json(left, payload)
    save_json(right, payload)

    compare = tmp_path / "seed_0007_compare.json"
    save_json(
        compare,
        {
            "seed": 7,
            "left_method_name": "ours_stage2_v2_4",
            "left_display_name": "Constraint-Aware Stage-2",
            "left_policy_id": "policy_left",
            "left_risk_summary_path": str(left),
            "right_method_name": "no_constraint_stage2_4obj",
            "right_display_name": "Unconstrained Stage-2",
            "right_policy_id": "policy_right",
            "right_risk_summary_path": str(right),
        },
    )

    semantic_root = tmp_path / "semantic"
    build_method_comparison_semantic_summary(
        [compare],
        output_dir=semantic_root,
        left_method_name="ours_stage2_v2_4",
        left_display_name="Constraint-Aware Stage-2",
        right_method_name="no_constraint_stage2_4obj",
        right_display_name="Unconstrained Stage-2",
    )
    consistency = _collect_metric_consistency(semantic_root)
    assert consistency["all_metrics_match"] is True


def test_export_rq4_ablation_summary_uses_current_paper_4obj_sources(tmp_path: Path) -> None:
    table_a_summary = tmp_path / "table_a_summary.json"
    save_json(
        table_a_summary,
        {
            "method_summary": [
                {
                    "method_name": "ours_stage2_v2_4",
                    "hypervolume": {"mean": 22_910_000.0, "std": 10.0},
                    "expected_utility": {"mean": -41.92, "std": 0.1},
                    "coverage_ratio": {"mean": 0.6048, "std": 0.01},
                    "unique_assigned_policies": {"mean": 3.3333, "std": 0.2},
                },
                {
                    "method_name": "stage1_only_4obj",
                    "hypervolume": {"mean": 22_170_000.0, "std": 9.0},
                    "expected_utility": {"mean": -44.88, "std": 0.2},
                    "coverage_ratio": {"mean": 0.8056, "std": 0.02},
                    "unique_assigned_policies": {"mean": 2.3333, "std": 0.3},
                },
            ]
        },
    )
    ours_path = tmp_path / "ours.json"
    stage1_path = tmp_path / "stage1.json"
    no_constraint_path = tmp_path / "no_constraint.json"
    save_json(
        ours_path,
        {
            "method_name": "ours_stage2_v2_4",
            "feasible_rate": 0.6417,
            "feasible_rate_std": 0.1,
            "mean_violation": 0.0942,
            "mean_violation_std": 0.01,
            "high_disruption_action_rate": 0.4748,
            "high_disruption_action_rate_std": 0.02,
        },
    )
    save_json(
        stage1_path,
        {
            "method_name": "stage1_only_4obj",
            "feasible_rate": 0.3083,
            "feasible_rate_std": 0.2,
            "mean_violation": 1.9770,
            "mean_violation_std": 0.4,
            "high_disruption_action_rate": 0.7317,
            "high_disruption_action_rate_std": 0.03,
        },
    )
    save_json(
        no_constraint_path,
        {
            "method_name": "no_constraint_stage2_4obj",
            "feasible_rate": 0.4583,
            "feasible_rate_std": 0.2,
            "mean_violation": 2.1274,
            "mean_violation_std": 0.4,
            "high_disruption_action_rate": 0.7942,
            "high_disruption_action_rate_std": 0.03,
        },
    )

    semantic_path = tmp_path / "semantic_comparison.json"
    save_json(
        semantic_path,
        {
            "left_method_name": "ours_stage2_v2_4",
            "left_display_name": "Constraint-Aware Stage-2",
            "right_method_name": "no_constraint_stage2_4obj",
            "right_display_name": "Unconstrained Stage-2",
            "left": {
                "ever_critical_breach_rate": 0.0,
                "persistent_critical_breach_rate": 0.0,
                "Q4_user_focus_after_enterprise_foothold": 0.0021,
                "Q5_repeated_low_value_decoy_loop": 0.0,
            },
            "right": {
                "ever_critical_breach_rate": 0.0,
                "persistent_critical_breach_rate": 0.0,
                "Q4_user_focus_after_enterprise_foothold": 0.3375,
                "Q5_repeated_low_value_decoy_loop": 0.2542,
            },
        },
    )

    objective_panel_path = tmp_path / "objective_ablation_summary.json"
    save_json(
        objective_panel_path,
        {
            "panel_key": "objective_3obj_vs_4obj",
            "panel_title": "C. 3obj vs. 4obj",
            "left_method_name": "ours_stage2",
            "left_display_name": "3-Objective Stage-2",
            "right_method_name": "ours_stage2_v2_4",
            "right_display_name": "4-Objective Stage-2",
                "rows": [
                    {
                        "metric_key": "projected_hypervolume_3d",
                        "metric_label": "Projected 3D Hypervolume",
                        "metric_source": "objective_ablation",
                    "left_method_name": "ours_stage2",
                    "left_display_name": "3-Objective Stage-2",
                    "left_mean": 2_500_000.0,
                    "left_std": 10.0,
                    "right_method_name": "ours_stage2_v2_4",
                    "right_display_name": "4-Objective Stage-2",
                    "right_mean": 5_500_000.0,
                        "right_std": 20.0,
                        "delta_right_minus_left": 3_000_000.0,
                    },
                    {
                        "metric_key": "projected_expected_utility_3d",
                        "metric_label": "Projected 3D Expected Utility",
                        "metric_source": "objective_ablation",
                        "left_method_name": "ours_stage2",
                        "left_display_name": "3-Objective Stage-2",
                        "left_mean": -175.40,
                        "left_std": 1.0,
                        "right_method_name": "ours_stage2_v2_4",
                        "right_display_name": "4-Objective Stage-2",
                        "right_mean": -55.92,
                        "right_std": 2.0,
                        "delta_right_minus_left": 119.48,
                    },
                    {
                        "metric_key": "feasible_rate",
                        "metric_label": "Feasible Rate",
                        "metric_source": "objective_ablation",
                        "left_method_name": "ours_stage2",
                        "left_display_name": "3-Objective Stage-2",
                        "left_mean": 0.0,
                        "left_std": 0.0,
                        "right_method_name": "ours_stage2_v2_4",
                        "right_display_name": "4-Objective Stage-2",
                        "right_mean": 0.64,
                        "right_std": 0.1,
                        "delta_right_minus_left": 0.64,
                    },
                    {
                        "metric_key": "mean_violation",
                        "metric_label": "Mean Violation",
                        "metric_source": "objective_ablation",
                        "left_method_name": "ours_stage2",
                        "left_display_name": "3-Objective Stage-2",
                        "left_mean": 86.22,
                        "left_std": 1.0,
                        "right_method_name": "ours_stage2_v2_4",
                        "right_display_name": "4-Objective Stage-2",
                        "right_mean": 0.09,
                        "right_std": 0.01,
                        "delta_right_minus_left": -86.13,
                    },
                    {
                        "metric_key": "ever_critical_breach_rate",
                        "metric_label": "Ever Critical Breach",
                        "metric_source": "objective_ablation",
                        "left_method_name": "ours_stage2",
                        "left_display_name": "3-Objective Stage-2",
                        "left_mean": 0.99,
                        "left_std": None,
                        "right_method_name": "ours_stage2_v2_4",
                        "right_display_name": "4-Objective Stage-2",
                        "right_mean": 0.00,
                        "right_std": None,
                        "delta_right_minus_left": -0.99,
                    },
                    {
                        "metric_key": "persistent_critical_breach_rate",
                        "metric_label": "Persistent Critical Breach",
                        "metric_source": "objective_ablation",
                        "left_method_name": "ours_stage2",
                        "left_display_name": "3-Objective Stage-2",
                        "left_mean": 0.65,
                        "left_std": None,
                        "right_method_name": "ours_stage2_v2_4",
                        "right_display_name": "4-Objective Stage-2",
                        "right_mean": 0.00,
                        "right_std": None,
                        "delta_right_minus_left": -0.65,
                    },
                    {
                        "metric_key": "Q4_user_focus_after_enterprise_foothold",
                        "metric_label": "Post-Foothold Drift (Q4)",
                        "metric_source": "objective_ablation",
                        "left_method_name": "ours_stage2",
                    "left_display_name": "3-Objective Stage-2",
                    "left_mean": 0.4000,
                    "left_std": None,
                    "right_method_name": "ours_stage2_v2_4",
                    "right_display_name": "4-Objective Stage-2",
                        "right_mean": 0.0021,
                        "right_std": None,
                        "delta_right_minus_left": -0.3979,
                    },
                    {
                        "metric_key": "Q5_repeated_low_value_decoy_loop",
                        "metric_label": "Repeated Low-Value Decoy Loop (Q5)",
                        "metric_source": "objective_ablation",
                        "left_method_name": "ours_stage2",
                        "left_display_name": "3-Objective Stage-2",
                        "left_mean": 0.47,
                        "left_std": None,
                        "right_method_name": "ours_stage2_v2_4",
                        "right_display_name": "4-Objective Stage-2",
                        "right_mean": 0.00,
                        "right_std": None,
                        "delta_right_minus_left": -0.47,
                    },
                ],
            },
        )

    outputs = export_rq4_ablation_summary(
        output_root=tmp_path / "rq4",
        table_a_summary_path=table_a_summary,
        semantic_comparison_path=semantic_path,
        paper_table_path=tmp_path / "paper" / "rq4_ablation_summary.tex",
        objective_ablation_summary_path=objective_panel_path,
        deployment_paths={
            "ours_stage2_v2_4": ours_path,
            "stage1_only_4obj": stage1_path,
            "no_constraint_stage2_4obj": no_constraint_path,
        },
    )

    summary = load_json(outputs["summary_json"])
    assert summary["panels"][0]["rows"][0]["metric_key"] == "hypervolume"
    assert summary["panels"][0]["rows"][0]["left_mean"] == 22_170_000.0
    assert [row["metric_key"] for row in summary["panels"][0]["rows"]] == [
        "hypervolume",
        "expected_utility",
        "feasible_rate",
        "mean_violation",
    ]
    assert summary["panels"][0]["rows"][2]["right_mean"] == 0.6417
    assert [row["metric_key"] for row in summary["panels"][1]["rows"]] == [
        "feasible_rate",
        "mean_violation",
        "Q4_user_focus_after_enterprise_foothold",
        "Q5_repeated_low_value_decoy_loop",
    ]
    assert summary["panels"][2]["panel_key"] == "objective_3obj_vs_4obj"
    assert summary["panels"][2]["rows"][0]["metric_key"] == "projected_hypervolume_3d"
    deltas = load_json(outputs["deltas_json"])
    assert deltas["stage2_vs_stage1"]["feasible_rate"] == pytest.approx(0.3334)
    assert deltas["constraint_aware_vs_unconstrained"]["Q5_repeated_low_value_decoy_loop"] == pytest.approx(
        -0.2542
    )
    assert deltas["objective_3obj_vs_4obj"]["projected_hypervolume_3d"] == pytest.approx(3_000_000.0)
    tex = Path(outputs["paper_table_path"]).read_text(encoding="utf-8")
    assert "A. Stage-1 vs. Constraint-Aware" in tex
    assert "B. Unconstrained vs. Constraint-Aware" in tex
    assert "C. 3obj vs. 4obj" in tex


def test_build_projected_set_quality_projects_4obj_into_shared_3d_space(
    tmp_path: Path,
) -> None:
    left_metrics = tmp_path / "left_seed_0007.json"
    right_metrics = tmp_path / "right_seed_0007.json"
    save_json(
        left_metrics,
        {
            "pareto_front": [
                {"policy_id": "l_a", "objective_vector": [-10.0, -20.0, -30.0]},
                {"policy_id": "l_b", "objective_vector": [-12.0, -18.0, -25.0]},
            ]
        },
    )
    save_json(
        right_metrics,
        {
            "pareto_front": [
                {"policy_id": "r_a", "objective_vector": [-9.0, -19.0, -29.0, 0.0]},
                {"policy_id": "r_b", "objective_vector": [-11.0, -17.0, -24.0, 0.2]},
            ]
        },
    )

    outputs = _build_projected_set_quality(
        output_root=tmp_path / "objective",
        left_metrics_paths={7: left_metrics},
        right_metrics_paths={7: right_metrics},
        paper_table_path=tmp_path / "paper" / "rq4_objective_projected_set_quality.tex",
    )

    payload = load_json(outputs["summary_json"])
    assert payload["projected_dimensions"] == ["security", "business", "cost"]
    assert len(payload["reference_point"]) == 3
    assert payload["preference_count"] > 0
    assert all(
        len(record["objective_vector"]) == 3
        for record in load_json(left_metrics)["pareto_front"]
    )
    row_lookup = {
        row["method_name"]: row
        for row in payload["method_summary"]
    }
    assert row_lookup["ours_stage2"]["projected_hypervolume_3d"]["mean"] > 0.0
    assert row_lookup["ours_stage2_v2_4"]["projected_expected_utility_3d"]["mean"] != 0.0
    assert (tmp_path / "objective" / "verification" / "projected_set_quality_sanity.json").exists()


def test_build_matched_deployment_reuses_4obj_thresholds_for_3obj_selection(
    tmp_path: Path,
    monkeypatch,
) -> None:
    left_buffer = tmp_path / "ours_stage2_seed_0007.json"
    save_json(left_buffer, {"records": []})

    right_input = tmp_path / "ours_stage2_v2_4_seed_0007.json"
    right_output = tmp_path / "ours_stage2_v2_4_seed_0007_metrics.json"
    save_json(right_input, {"policy_id": "stage2_ext_008_obj_0"})
    save_json(
        right_output,
        {
            "method_name": "ours_stage2_v2_4",
            "selected_policy_id": "stage2_ext_008_obj_0",
            "feasible_rate": 0.6,
            "mean_violation": 0.1,
            "security_return": -170.0,
            "business_return": -28.0,
            "cost_return": -21.0,
            "high_disruption_action_rate": 0.47,
        },
    )

    table_b_summary = tmp_path / "table_b_summary.json"
    save_json(
        table_b_summary,
        {
            "per_run_records": [
                {
                    "method_name": "ours_stage2_v2_4",
                    "seed": 7,
                    "input_kind": "single_policy",
                    "input_path": str(right_input),
                    "output_path": str(right_output),
                }
            ]
        },
    )
    thresholds_path = tmp_path / "shared_thresholds.json"
    save_json(thresholds_path, {"d_business": -27.0, "d_cost": -24.0})

    calls: list[dict[str, object]] = []

    def _fake_evaluate_constraints(**kwargs):
        calls.append(dict(kwargs))
        return {
            "method_name": kwargs["method_name"],
            "selected_policy_id": "stage1_pref_000_ckpt_191",
            "feasible_rate": 0.0,
            "mean_violation": 86.2,
            "security_return": -497.3,
            "business_return": -110.8,
            "cost_return": -27.0,
            "high_disruption_action_rate": 0.97,
            "final_critical_compromised_hosts": 0.6,
            "critical_impact_count": 4.55,
        }

    monkeypatch.setattr(
        "cmorl_cyborg.export_rq4_objective_ablation.evaluate_constraints",
        _fake_evaluate_constraints,
    )

    outputs = _build_matched_deployment(
        output_root=tmp_path / "objective",
        left_buffer_paths={7: left_buffer},
        table_b_summary_path=table_b_summary,
        thresholds_path=thresholds_path,
        deployment_eval_episodes=5,
    )

    assert len(calls) == 1
    assert calls[0]["method_name"] == "ours_stage2"
    assert Path(str(calls[0]["thresholds_path"])).resolve() == thresholds_path.resolve()
    payload = load_json(outputs["summary_json"])
    assert payload["thresholds_source_path"] == str(thresholds_path.resolve())
    assert payload["per_seed_records"][0]["selected_policy_id"] == "stage1_pref_000_ckpt_191"
    protocol = load_json(tmp_path / "objective" / "verification" / "protocol_match.json")
    assert protocol["rows"][0]["uses_4obj_thresholds"] is True


def test_export_attacker_shift_summary_4obj_uses_paper_4obj_buffers(
    tmp_path: Path, monkeypatch
) -> None:
    buffer_a = tmp_path / "ours_seed7.json"
    buffer_b = tmp_path / "stage1_seed7.json"
    buffer_c = tmp_path / "no_constraint_seed7.json"
    for path in (buffer_a, buffer_b, buffer_c):
        save_json(
            path,
            {
                "metadata": {
                    "env": {
                        "red_policy": "bline",
                        "seed": 7,
                    }
                }
            },
        )

    table_a_summary = tmp_path / "table_a_summary.json"
    save_json(
        table_a_summary,
        {
            "per_run": [
                {
                    "method_name": "ours_stage2_v2_4",
                    "seed": 7,
                    "artifact_path": str(buffer_a),
                },
                {
                    "method_name": "stage1_only_4obj",
                    "seed": 7,
                    "artifact_path": str(buffer_b),
                },
            ]
        },
    )
    table_b_summary = tmp_path / "table_b_summary.json"
    save_json(
        table_b_summary,
        {
            "per_run_records": [
                {
                    "method_name": "no_constraint_stage2_4obj",
                    "seed": 7,
                    "input_kind": "buffer",
                    "input_path": str(buffer_c),
                }
            ]
        },
    )
    thresholds = tmp_path / "shared_thresholds.json"
    save_json(thresholds, {"d_business": -1.0, "d_cost": -2.0})

    calls: list[dict[str, object]] = []

    def _fake_evaluate_constraints(**kwargs):
        calls.append(kwargs)
        return {
            "method_name": kwargs["method_name"],
            "selected_policy_id": f"{kwargs['method_name']}_selected",
            "security_return": -10.0,
            "business_return": -3.0,
            "cost_return": -2.0,
            "feasible_rate": 0.5,
            "mean_violation": 1.0,
            "final_critical_compromised_hosts": 0.0,
            "critical_impact_count": 0.0,
            "high_disruption_action_rate": 0.25,
            "thresholds": {"d_business": -1.0, "d_cost": -2.0},
        }

    monkeypatch.setattr(
        "cmorl_cyborg.export_attacker_shift_summary_4obj.evaluate_constraints",
        _fake_evaluate_constraints,
    )

    outputs = export_attacker_shift_summary_4obj(
        red_policy="meander",
        methods=("ours_stage2_v2_4", "stage1_only_4obj", "no_constraint_stage2_4obj"),
        seeds=(7,),
        eval_episodes=5,
        table_a_summary_path=table_a_summary,
        table_b_summary_path=table_b_summary,
        shared_thresholds_path=thresholds,
        output_dir=tmp_path / "attacker_shift_meander",
    )

    assert len(calls) == 3
    assert all(call["selection_source"] == "pareto" for call in calls)
    assert all(str(call["thresholds_path"]).endswith("shared_thresholds.json") for call in calls)
    shifted_payload = load_json(
        tmp_path
        / "attacker_shift_meander"
        / "tmp_inputs"
        / "ours_stage2_v2_4"
        / "seed_0007"
        / "solution_buffer.json"
    )
    assert shifted_payload["metadata"]["env"]["red_policy"] == "meander"

    summary = load_json(outputs["summary_json"])
    assert summary["train_red_policy"] == "bline"
    assert summary["eval_red_policy"] == "meander"
    assert summary["seeds"] == [7]
    assert len(summary["aggregated_paths"]) == 3
    assert Path(outputs["status_path"]).exists()
