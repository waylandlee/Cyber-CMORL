from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from cmorl_minicage.utils import load_json, save_json


SCHEMA_VERSION = "0.4.3"


def buffer_metadata(
    *,
    stage: str,
    env_config,
    model_config,
    rollout_config,
    optimizer_config,
    eval_config,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    def _serialise_config(value: Any) -> Any:
        return asdict(value) if hasattr(value, "__dataclass_fields__") else value

    metadata = {
        "schema_version": SCHEMA_VERSION,
        "stage": stage,
        "env": _serialise_config(env_config),
        "model": _serialise_config(model_config),
        "rollout": _serialise_config(rollout_config),
        "optimizer": _serialise_config(optimizer_config),
        "evaluation": _serialise_config(eval_config),
    }
    if extra:
        metadata.update(extra)
    return metadata


def policy_record(
    *,
    policy_id: str,
    checkpoint_path: str,
    objective_vector,
    stage: str,
    source: str,
    preference=None,
    parent_policy_id=None,
    target_objective=None,
    base_objective_vector=None,
    update_index=None,
    archive_role: str | None = None,
    operator_source: str | None = None,
    feasible_flag: bool | None = None,
    near_feasible_flag: bool | None = None,
    tight_feasible_flag: bool | None = None,
    business_return: float | None = None,
    cost_return: float | None = None,
    security_return: float | None = None,
    mean_violation: float | None = None,
    critical_impact_count: float | None = None,
    final_critical_compromised: float | None = None,
    high_disruption_rate: float | None = None,
    delta_hv: float | None = None,
    delta_eu: float | None = None,
    delta_coverage: float | None = None,
    novelty_score: float | None = None,
    assignment_diversity_gain: float | None = None,
    spread_gain: float | None = None,
    notes: dict[str, Any] | None = None,
) -> dict[str, Any]:
    record = {
        "policy_id": policy_id,
        "checkpoint_path": checkpoint_path,
        "preference": preference,
        "objective_vector": list(map(float, objective_vector)),
        "stage": stage,
        "source": source,
        "parent_policy_id": parent_policy_id,
        "target_objective": target_objective,
        "base_objective_vector": base_objective_vector,
        "update_index": update_index,
        "archive_role": archive_role,
        "operator_source": operator_source,
        "feasible_flag": feasible_flag,
        "near_feasible_flag": near_feasible_flag,
        "tight_feasible_flag": tight_feasible_flag,
        "business_return": business_return,
        "cost_return": cost_return,
        "security_return": security_return,
        "mean_violation": mean_violation,
        "critical_impact_count": critical_impact_count,
        "final_critical_compromised": final_critical_compromised,
        "high_disruption_rate": high_disruption_rate,
        "delta_hv": delta_hv,
        "delta_eu": delta_eu,
        "delta_coverage": delta_coverage,
        "novelty_score": novelty_score,
        "assignment_diversity_gain": assignment_diversity_gain,
        "spread_gain": spread_gain,
    }
    if notes:
        record["notes"] = notes
    return record


def save_policy_buffer(
    path: str | Path,
    *,
    metadata: dict[str, Any],
    records: list[dict[str, Any]],
    pareto_front: list[dict[str, Any]],
    cons_records: list[dict[str, Any]] | None = None,
    uc_records: list[dict[str, Any]] | None = None,
    union_front: list[dict[str, Any]] | None = None,
) -> None:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "metadata": metadata,
        "records": records,
        "pareto_front": pareto_front,
    }
    if cons_records is not None:
        payload["cons_records"] = cons_records
    if uc_records is not None:
        payload["uc_records"] = uc_records
    if union_front is not None:
        payload["union_front"] = union_front
    save_json(path, payload)


def load_policy_buffer(path: str | Path) -> dict[str, Any]:
    payload = load_json(path)
    if "metadata" not in payload:
        payload = {
            "schema_version": "0.1.0",
            "metadata": {
                "schema_version": "0.1.0",
                "stage": payload.get("stage", "unknown"),
                "config": payload.get("config", {}),
            },
            "records": payload.get("records", []),
            "pareto_front": payload.get("pareto_front", []),
        }
    payload.setdefault("schema_version", payload.get("metadata", {}).get("schema_version", "0.1.0"))
    payload.setdefault("records", [])
    payload.setdefault("pareto_front", [])
    payload.setdefault("cons_records", [])
    payload.setdefault("uc_records", [])
    payload.setdefault("union_front", [])
    return payload
