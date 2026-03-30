from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from cmorl_minicage.utils import load_json, save_json


SCHEMA_VERSION = "0.3.0"


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
    metadata = {
        "schema_version": SCHEMA_VERSION,
        "stage": stage,
        "env": asdict(env_config),
        "model": asdict(model_config),
        "rollout": asdict(rollout_config),
        "optimizer": asdict(optimizer_config),
        "evaluation": asdict(eval_config),
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
) -> None:
    save_json(
        path,
        {
            "schema_version": SCHEMA_VERSION,
            "metadata": metadata,
            "records": records,
            "pareto_front": pareto_front,
        },
    )


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
    return payload
