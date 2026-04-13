from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

import numpy as np
import torch

from cmorl_minicage.algorithms.selection import crowding_distance, nondominated_filter
from cmorl_minicage.evaluate_constraints import compute_shared_thresholds
from cmorl_minicage.models import ActorCritic


ARCHIVE_RULE_VERSION = "b_fix_v1"


def _objective_array(records: Sequence[dict]) -> np.ndarray:
    if not records:
        return np.zeros((0, 0), dtype=np.float32)
    return np.asarray([record["objective_vector"] for record in records], dtype=np.float32)


def _as_float(value, default: float | None = None) -> float | None:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_bool(value) -> bool:
    return bool(value) if value is not None else False


def _dedupe_by_policy_id(records: Sequence[dict]) -> list[dict]:
    by_id: dict[str, dict] = {}
    for record in records:
        by_id.setdefault(str(record["policy_id"]), dict(record))
    return list(by_id.values())


def _constraint_violation_from_record(record: dict) -> float | None:
    notes = record.get("notes") or {}
    margins = notes.get("last_constraint_margins")
    if margins is None:
        return None
    values = np.asarray(margins, dtype=np.float32)
    if values.size == 0:
        return None
    return float(np.mean(np.maximum(0.0, -values)))


def _repo_root_from_path(path: str | Path) -> Path:
    path = Path(path).resolve()
    for candidate in (path, *path.parents):
        if (candidate / "cmorl_minicage").exists():
            return candidate
    raise ValueError(f"Could not infer repository root from {path}")


def _resolve_checkpoint_path(anchor: str | Path, checkpoint_path: str | Path) -> Path:
    checkpoint = Path(checkpoint_path)
    if checkpoint.is_absolute():
        return checkpoint
    return (_repo_root_from_path(anchor) / checkpoint).resolve()


def _is_seed_record(record: dict) -> bool:
    return str(record.get("stage") or "").lower() == "stage1" or record.get(
        "base_objective_vector"
    ) is None


def _metric(record: dict, *keys: str, default: float | None = None) -> float | None:
    for key in keys:
        value = record.get(key)
        if value is not None:
            return _as_float(value, default)
    return default


def _semantic_metrics_for_record(
    record: dict,
    metadata: dict[str, Any],
    buffer_anchor: str | Path,
    *,
    eval_episodes: int,
) -> dict[str, float]:
    if eval_episodes <= 0 or not record.get("checkpoint_path"):
        return {}

    env_config = metadata.get("env", {})
    model_config = metadata.get("model", {})
    env_class = _env_class_from_metadata(metadata)
    env_kwargs = {
        "num_envs": int(env_config.get("num_envs", 8)),
        "red_policy": env_config.get("red_policy", "bline"),
        "remove_bugs": bool(env_config.get("remove_bugs", True)),
        "max_steps": int(env_config.get("max_episode_steps", 100)),
        "seed": int(env_config.get("seed", 7)),
    }
    if env_class.__name__ == "CybORGMORLEnv":
        env_kwargs.update(
            {
                "scenario_name": env_config.get("scenario_name", "Scenario2"),
                "scenario_profile": env_config.get("scenario_profile", ""),
                "gym_wrapper_name": env_config.get("gym_wrapper_name", "ChallengeWrapper"),
                "blue_agent_name": env_config.get("blue_agent_name", "Blue"),
                "red_agent_name": env_config.get("red_agent_name", "Red"),
                "obs_mode": env_config.get("obs_mode", "vector"),
                "state_mode": env_config.get("state_mode", "true"),
            }
        )
    env = env_class(**env_kwargs)
    actor_critic = ActorCritic(
        obs_dim=env.obs_dim,
        action_dim=env.action_dim,
        obj_dim=int(model_config.get("obj_dim", 3)),
        hidden_sizes=(
            int(model_config.get("hidden_size", 128)),
            int(model_config.get("hidden_size", 128)),
        ),
    ).to(torch.device("cpu"))
    checkpoint = torch.load(
        _resolve_checkpoint_path(buffer_anchor, record["checkpoint_path"]),
        map_location="cpu",
        weights_only=True,
    )
    actor_critic.load_state_dict(checkpoint)
    actor_critic.eval()

    totals = {
        "final_critical_compromised_hosts": [],
        "critical_impact_count": [],
        "high_disruption_action_count": [],
        "total_action_count": [],
    }
    base_seed = int(env_config.get("seed", 7))
    with torch.no_grad():
        for episode_idx in range(max(int(eval_episodes), 1)):
            env.seed = base_seed + episode_idx
            obs, _ = env.reset()
            done = np.zeros(env.num_envs, dtype=bool)
            episode_semantics = {
                "critical_impact_count": np.zeros(env.num_envs, dtype=np.float64),
                "high_disruption_action_count": np.zeros(env.num_envs, dtype=np.float64),
                "total_action_count": np.zeros(env.num_envs, dtype=np.float64),
            }
            final_critical = np.zeros(env.num_envs, dtype=np.float64)

            while not np.all(done):
                obs_tensor = torch.as_tensor(obs, dtype=torch.float32)
                actions = (
                    actor_critic.act(obs_tensor)
                    .actions.cpu()
                    .numpy()
                    .reshape(env.num_envs, 1)
                )
                obs, _, done, _, info = env.step(actions)
                semantic_info = info["semantic_info"]
                final_critical = np.asarray(
                    semantic_info["final_critical_compromised_hosts"],
                    dtype=np.float64,
                )
                for key in episode_semantics:
                    episode_semantics[key] += np.asarray(
                        semantic_info[key], dtype=np.float64
                    )

            totals["final_critical_compromised_hosts"].extend(final_critical.tolist())
            for key in episode_semantics:
                totals[key].extend(episode_semantics[key].tolist())

    total_action_sum = max(float(np.sum(totals["total_action_count"])), 1.0)
    return {
        "final_critical_compromised_hosts": float(
            np.mean(totals["final_critical_compromised_hosts"])
        ),
        "critical_impact_count": float(np.mean(totals["critical_impact_count"])),
        "high_disruption_action_rate": float(
            np.sum(totals["high_disruption_action_count"]) / total_action_sum
        ),
    }


def _env_class_from_metadata(metadata: dict[str, Any]):
    env_config = metadata.get("env", {})
    if "scenario_name" in env_config or "gym_wrapper_name" in env_config:
        from cmorl_cyborg.env import CybORGMORLEnv

        return CybORGMORLEnv
    from cmorl_minicage.env import MiniCageMORLEnv

    return MiniCageMORLEnv


def _record_lookup(records: Sequence[dict]) -> dict[str, dict]:
    return {str(record["policy_id"]): record for record in records}


class DualArchiveManager:
    def __init__(
        self,
        *,
        cons_thresholds: dict[str, float] | None = None,
        uc_thresholds: dict[str, float] | None = None,
        selector_penalty_weights: dict[str, float] | None = None,
        preferences: Sequence[Sequence[float]] | None = None,
        utility_tolerance: float = 0.02,
        seed_uc_size: int = 0,
        route_mode: str = "exclusive",
        metadata: dict[str, Any] | None = None,
        buffer_path: str | Path | None = None,
        semantic_eval_episodes: int = 0,
        archive_seed_thresholds: dict[str, float] | None = None,
        archive_rule_version: str = ARCHIVE_RULE_VERSION,
    ) -> None:
        self.cons_thresholds = dict(cons_thresholds or {})
        self.uc_thresholds = dict(uc_thresholds or {})
        self.selector_penalty_weights = dict(selector_penalty_weights or {})
        self.preferences = [list(map(float, pref)) for pref in (preferences or [])]
        self.utility_tolerance = float(utility_tolerance)
        self.seed_uc_size = max(int(seed_uc_size), 0)
        self.route_mode = route_mode
        self.metadata = dict(metadata or {})
        self.buffer_path = Path(buffer_path).resolve() if buffer_path else None
        self.semantic_eval_episodes = max(int(semantic_eval_episodes), 0)
        self.archive_seed_thresholds = dict(archive_seed_thresholds or {})
        self.archive_rule_version = archive_rule_version
        self.cons_records: list[dict] = []
        self.uc_records: list[dict] = []
        self.union_records: list[dict] = []
        self.union_front: list[dict] = []
        self._semantic_cache: dict[str, dict[str, float]] = {}

    def seed_from_stage1(self, records: Sequence[dict]) -> None:
        pareto = nondominated_filter(records)
        annotated = [self.annotate_record(record, pareto) for record in pareto]
        self.cons_records = [
            dict(record, archive_role="cons") for record in annotated
        ]
        uc_seed = sorted(
            annotated,
            key=lambda record: (
                -self._uc_score(record),
                str(record["policy_id"]),
            ),
        )[: self.seed_uc_size]
        self.uc_records = [dict(record, archive_role="uc") for record in uc_seed]
        self.refresh_union_front()

    def annotate_record(
        self,
        record: dict,
        reference_records: Sequence[dict] | None = None,
    ) -> dict:
        annotated = dict(record)
        notes = dict(annotated.get("notes") or {})
        objectives = np.asarray(annotated["objective_vector"], dtype=np.float32)
        if objectives.size >= 1 and annotated.get("security_return") is None:
            annotated["security_return"] = float(objectives[0])
        if objectives.size >= 2 and annotated.get("business_return") is None:
            annotated["business_return"] = float(objectives[1])
        if objectives.size >= 3 and annotated.get("cost_return") is None:
            annotated["cost_return"] = float(objectives[2])

        if (
            annotated.get("high_disruption_action_rate") is None
            or annotated.get("final_critical_compromised_hosts") is None
            or annotated.get("critical_impact_count") is None
        ):
            semantic_metrics = self._semantic_metrics(annotated)
            if semantic_metrics:
                annotated.setdefault(
                    "high_disruption_action_rate",
                    semantic_metrics["high_disruption_action_rate"],
                )
                annotated.setdefault(
                    "final_critical_compromised_hosts",
                    semantic_metrics["final_critical_compromised_hosts"],
                )
                annotated.setdefault(
                    "critical_impact_count",
                    semantic_metrics["critical_impact_count"],
                )

        if annotated.get("high_disruption_rate") is None:
            annotated["high_disruption_rate"] = _metric(
                annotated, "high_disruption_action_rate", default=None
            )
        if annotated.get("high_disruption_action_rate") is None:
            annotated["high_disruption_action_rate"] = _metric(
                annotated, "high_disruption_rate", default=None
            )
        if annotated.get("final_critical_compromised") is None:
            annotated["final_critical_compromised"] = _metric(
                annotated, "final_critical_compromised_hosts", default=None
            )
        if annotated.get("final_critical_compromised_hosts") is None:
            annotated["final_critical_compromised_hosts"] = _metric(
                annotated, "final_critical_compromised", default=None
            )

        violation = _constraint_violation_from_record(annotated)
        if violation is not None:
            annotated["mean_violation"] = violation
        elif annotated.get("mean_violation") is None and _is_seed_record(annotated):
            thresholds = self.ensure_archive_seed_thresholds()
            business_return = _metric(annotated, "business_return", default=None)
            cost_return = _metric(annotated, "cost_return", default=None)
            if thresholds and business_return is not None and cost_return is not None:
                heuristic_violation = max(
                    0.0, float(thresholds["d_business"]) - float(business_return)
                ) + max(0.0, float(thresholds["d_cost"]) - float(cost_return))
                annotated["mean_violation"] = float(heuristic_violation)
                notes["heuristic_mean_violation"] = float(heuristic_violation)

        references = list(reference_records) if reference_records is not None else list(self.union_records)
        references = [
            ref for ref in references if ref.get("policy_id") != annotated.get("policy_id")
        ]
        if annotated.get("delta_eu") is None:
            annotated["delta_eu"] = self._delta_expected_utility(annotated, references)
        if annotated.get("delta_coverage") is None:
            annotated["delta_coverage"] = self._delta_coverage(annotated, references)
        if annotated.get("novelty_score") is None:
            annotated["novelty_score"] = self._novelty_score(annotated, references)
        if annotated.get("spread_gain") is None:
            annotated["spread_gain"] = float(annotated.get("novelty_score") or 0.0)
        if annotated.get("assignment_diversity_gain") is None:
            annotated["assignment_diversity_gain"] = float(
                annotated.get("delta_coverage") or 0.0
            )

        strict_state = self._strict_state(annotated)
        annotated["strict_candidate_eligible"] = strict_state["eligible"]
        annotated["strict_ineligibility_reason"] = strict_state["ineligibility_reason"]
        annotated["base_cost_return"] = strict_state["base_cost_return"]
        annotated["relative_cost_ok"] = strict_state["relative_cost_ok"]
        annotated["relative_cost_margin"] = strict_state["relative_cost_margin"]
        annotated["feasible_flag"] = strict_state["tight_feasible_flag"]
        annotated["near_feasible_flag"] = strict_state["near_feasible_flag"]
        annotated["tight_feasible_flag"] = strict_state["tight_feasible_flag"]
        notes["archive_rule_version"] = self.archive_rule_version
        if self.archive_seed_thresholds:
            notes["archive_seed_thresholds"] = dict(self.archive_seed_thresholds)
        annotated["notes"] = notes
        return annotated

    def is_cons_candidate(self, record: dict) -> bool:
        return self.cons_decision(record)[0]

    def is_uc_candidate(self, record: dict) -> bool:
        return self.uc_decision(record)[0]

    def cons_decision(self, record: dict) -> tuple[bool, str]:
        if not _as_bool(record.get("strict_candidate_eligible")):
            if record.get("relative_cost_ok") is False:
                return False, "rejected_cost_gate"
            return False, "rejected_feasibility"
        if record.get("relative_cost_ok") is False:
            return False, "rejected_cost_gate"
        if _as_bool(record.get("tight_feasible_flag")) or _as_bool(
            record.get("near_feasible_flag")
        ):
            return True, "accepted_cons"
        return False, "rejected_feasibility"

    def uc_decision(self, record: dict) -> tuple[bool, str]:
        checks = (
            ("delta_eu", "delta_eu"),
            ("delta_coverage", "delta_coverage"),
            ("novelty_score", "novelty"),
            ("spread_gain", "spread_gain"),
        )
        for record_key, threshold_key in checks:
            value = _as_float(record.get(record_key), 0.0) or 0.0
            threshold = float(self.uc_thresholds.get(threshold_key, 0.0))
            if value >= threshold:
                return True, "accepted_uc"
        return False, "rejected_no_material_uc_gain"

    def _route_fail_components(self, record: dict) -> list[str]:
        components: list[str] = []
        violation = _metric(record, "mean_violation", default=None)
        final_critical = _metric(
            record,
            "final_critical_compromised_hosts",
            "final_critical_compromised",
            default=None,
        )
        disruption = _metric(
            record, "high_disruption_action_rate", "high_disruption_rate", default=None
        )

        ineligibility_reason = str(record.get("strict_ineligibility_reason") or "")
        if ineligibility_reason.startswith("missing_"):
            components.append("missing_semantics")

        if record.get("relative_cost_ok") is False:
            components.append("cost")
        if violation is not None and float(violation) > float(
            self.cons_thresholds.get("violation", 0.5)
        ):
            components.append("violation")
        if final_critical is not None and float(final_critical) > float(
            self.cons_thresholds.get("final_critical_near", 0.25)
        ):
            components.append("final_critical")
        if disruption is not None and float(disruption) > float(
            self.cons_thresholds.get("high_disruption", 1.0)
        ):
            components.append("disruption")
        return components

    def _route_fail_primary(self, record: dict, components: Sequence[str]) -> str | None:
        if not components:
            return None

        violation_thr = max(float(self.cons_thresholds.get("violation", 0.5)), 1e-6)
        final_critical_thr = max(
            float(self.cons_thresholds.get("final_critical_near", 0.25)), 1e-6
        )
        disruption_thr = max(
            float(self.cons_thresholds.get("high_disruption", 1.0)), 1e-6
        )
        cost_delta_tolerance = max(
            float(self.cons_thresholds.get("cost_delta_tolerance", 3.0)), 1e-6
        )

        violation = _metric(record, "mean_violation", default=None)
        final_critical = _metric(
            record,
            "final_critical_compromised_hosts",
            "final_critical_compromised",
            default=None,
        )
        disruption = _metric(
            record, "high_disruption_action_rate", "high_disruption_rate", default=None
        )
        relative_cost_margin = _as_float(record.get("relative_cost_margin"), 0.0) or 0.0

        score_by_component = {
            "violation": (
                max(0.0, float(violation) - violation_thr) / violation_thr
                if violation is not None
                else 0.0
            ),
            "final_critical": (
                max(0.0, float(final_critical) - final_critical_thr) / final_critical_thr
                if final_critical is not None
                else 0.0
            ),
            "disruption": (
                max(0.0, float(disruption) - disruption_thr) / disruption_thr
                if disruption is not None
                else 0.0
            ),
            "cost": max(0.0, -relative_cost_margin) / cost_delta_tolerance,
            "missing_semantics": 0.0,
        }
        tie_break_order = {
            "final_critical": 0,
            "violation": 1,
            "cost": 2,
            "disruption": 3,
            "missing_semantics": 4,
        }
        return sorted(
            components,
            key=lambda component: (
                -float(score_by_component.get(component, 0.0)),
                tie_break_order.get(component, 99),
            ),
        )[0]

    def preview_route(self, record: dict) -> dict:
        if self.route_mode != "exclusive":
            raise ValueError(f"Unsupported route_mode: {self.route_mode}")
        routed = self.annotate_record(record)
        cons_candidate, cons_reason = self.cons_decision(routed)
        uc_candidate, uc_reason = self.uc_decision(routed)
        route_decision = (
            cons_reason
            if cons_candidate
            else uc_reason
            if uc_candidate
            else cons_reason
            if cons_reason == "rejected_cost_gate"
            else uc_reason
            if uc_reason == "rejected_no_material_uc_gain"
            else cons_reason
        )
        archive_role = "cons" if cons_candidate else "uc" if uc_candidate else None
        routed["archive_role"] = archive_role
        components = [] if cons_candidate else self._route_fail_components(routed)
        return {
            "accepted": bool(cons_candidate or uc_candidate),
            "archive_role": archive_role,
            "route_decision": route_decision,
            "record": routed,
            "cons_reason": cons_reason,
            "uc_reason": uc_reason,
            "route_fail_components_all": components,
            "route_fail_primary": self._route_fail_primary(routed, components),
        }

    def insert_preview(self, preview_result: dict) -> dict:
        archive_role = preview_result.get("archive_role")
        routed = preview_result["record"]
        routed["archive_role"] = archive_role
        if archive_role == "cons":
            self.cons_records.append(routed)
            self.refresh_union_front()
        elif archive_role == "uc":
            self.uc_records.append(routed)
            self.refresh_union_front()
        return preview_result

    def route_and_insert(self, record: dict) -> dict:
        preview_result = self.preview_route(record)
        return self.insert_preview(preview_result)

    def select_cons_parents(self, n: int) -> list[dict]:
        candidates = self.cons_records or self.union_records
        return self._select_by_score(candidates, n, self._cons_score)

    def select_uc_parents(self, n: int) -> list[dict]:
        candidates = self.uc_records or self.union_records or self.cons_records
        return self._select_by_score(candidates, n, self._uc_score)

    def refresh_union_front(self) -> list[dict]:
        self.union_records = _dedupe_by_policy_id([*self.cons_records, *self.uc_records])
        self.union_front = nondominated_filter(self.union_records)
        return self.union_front

    def select_strict_policy(self, preference: Sequence[float]) -> dict:
        candidates = [
            record
            for record in self.cons_records
            if _as_bool(record.get("tight_feasible_flag"))
            or _as_bool(record.get("near_feasible_flag"))
        ]
        if not candidates:
            raise ValueError("No strict feasible policy candidates are available")
        return self._select_plain(preference, candidates)

    def select_hybrid_policy(self, preference: Sequence[float]) -> dict:
        try:
            selected = self.select_strict_policy(preference)
            selected["selector_mode"] = "hybrid_strict"
            return selected
        except ValueError:
            candidates = self.union_records or [*self.cons_records, *self.uc_records]
            if not candidates:
                raise ValueError("No hybrid policy candidates are available") from None
            selected = self._select_penalized(preference, candidates)
            selected["selector_mode"] = "hybrid_fallback"
            return selected

    def child_diagnostics(self, record: dict) -> dict:
        return {
            "policy_id": record.get("policy_id"),
            "archive_role": record.get("archive_role"),
            "operator_source": record.get("operator_source"),
            "delta_eu": record.get("delta_eu"),
            "delta_coverage": record.get("delta_coverage"),
            "spread_gain": record.get("spread_gain"),
            "near_feasible_flag": record.get("near_feasible_flag"),
            "tight_feasible_flag": record.get("tight_feasible_flag"),
            "high_disruption_rate": record.get("high_disruption_rate"),
            "high_disruption_action_rate": record.get("high_disruption_action_rate"),
            "mean_violation": record.get("mean_violation"),
            "final_critical_compromised_hosts": record.get(
                "final_critical_compromised_hosts"
            ),
            "strict_candidate_eligible": record.get("strict_candidate_eligible"),
            "relative_cost_ok": record.get("relative_cost_ok"),
        }

    def _select_by_score(
        self,
        records: Sequence[dict],
        n: int,
        scorer,
    ) -> list[dict]:
        if n <= 0 or not records:
            return []
        pareto = nondominated_filter(records)
        scored = [(float(scorer(record)), str(record["policy_id"]), record) for record in pareto]
        scored.sort(key=lambda item: (-item[0], item[1]))
        return [dict(record) for _, _, record in scored[:n]]

    def _cons_score(self, record: dict) -> float:
        feasible_score = 0.0
        if _as_bool(record.get("tight_feasible_flag")):
            feasible_score = 1.0
        elif _as_bool(record.get("near_feasible_flag")):
            feasible_score = 0.5
        elif _as_bool(record.get("feasible_flag")):
            feasible_score = 0.25
        cost_margin = _as_float(record.get("relative_cost_margin"), 0.0) or 0.0
        violation = _as_float(record.get("mean_violation"), 0.0) or 0.0
        disruption = _metric(
            record, "high_disruption_action_rate", "high_disruption_rate", default=0.0
        ) or 0.0
        crowding = self._crowding_by_id(self.cons_records).get(str(record["policy_id"]), 0.0)
        return feasible_score + cost_margin - violation - disruption + crowding

    def _uc_score(self, record: dict) -> float:
        return float(
            (_as_float(record.get("novelty_score"), 0.0) or 0.0)
            + (_as_float(record.get("delta_eu"), 0.0) or 0.0)
            + (_as_float(record.get("delta_coverage"), 0.0) or 0.0)
            + (_as_float(record.get("spread_gain"), 0.0) or 0.0)
            + (_as_float(record.get("assignment_diversity_gain"), 0.0) or 0.0)
        )

    def _crowding_by_id(self, records: Sequence[dict]) -> dict[str, float]:
        pareto = nondominated_filter(records)
        distances = crowding_distance(pareto)
        result: dict[str, float] = {}
        for index, record in enumerate(pareto):
            value = float(distances[index]) if distances.size else 0.0
            result[str(record["policy_id"])] = 1.0 if not np.isfinite(value) else value
        return result

    def _delta_expected_utility(self, record: dict, references: Sequence[dict]) -> float:
        if not self.preferences:
            return 0.0
        weights = np.asarray(self.preferences, dtype=np.float32)
        point = np.asarray(record["objective_vector"], dtype=np.float32)
        child_utilities = point @ weights.T
        if not references:
            return float(np.mean(child_utilities))
        ref_points = _objective_array(references)
        ref_utilities = ref_points @ weights.T
        best_before = np.max(ref_utilities, axis=0)
        return float(np.mean(np.maximum(0.0, child_utilities - best_before)))

    def _delta_coverage(self, record: dict, references: Sequence[dict]) -> float:
        if not self.preferences:
            return 0.0
        weights = np.asarray(self.preferences, dtype=np.float32)
        point = np.asarray(record["objective_vector"], dtype=np.float32)
        child_utilities = point @ weights.T
        if not references:
            return 1.0
        ref_points = _objective_array(references)
        best_before = np.max(ref_points @ weights.T, axis=0)
        return float(np.mean(child_utilities > best_before + self.utility_tolerance))

    def _novelty_score(self, record: dict, references: Sequence[dict]) -> float:
        if not references:
            return 1.0
        point = np.asarray(record["objective_vector"], dtype=np.float32)
        ref_points = _objective_array(references)
        distances = np.linalg.norm(ref_points - point[None, :], axis=1)
        scale = max(float(np.sqrt(max(point.size, 1))), 1.0)
        return float(np.min(distances) / scale)

    def _select_plain(self, preference: Sequence[float], policy_set: Sequence[dict]) -> dict:
        weights = np.asarray(preference, dtype=np.float32)
        best_record = None
        best_utility = -np.inf
        for record in policy_set:
            utility = float(weights @ np.asarray(record["objective_vector"], dtype=np.float32))
            if utility > best_utility:
                best_utility = utility
                best_record = record
        if best_record is None:
            raise ValueError("policy_set must not be empty")
        selected = dict(best_record)
        selected["preference"] = weights.tolist()
        selected["utility"] = float(best_utility)
        return selected

    def _select_penalized(self, preference: Sequence[float], policy_set: Sequence[dict]) -> dict:
        weights = np.asarray(preference, dtype=np.float32)
        best_record = None
        best_score = -np.inf
        best_utility = -np.inf
        for record in policy_set:
            utility = float(weights @ np.asarray(record["objective_vector"], dtype=np.float32))
            penalty = (
                float(self.selector_penalty_weights.get("violation", 1.0))
                * (_as_float(record.get("mean_violation"), 0.0) or 0.0)
                + float(self.selector_penalty_weights.get("high_disruption", 1.0))
                * (
                    _metric(
                        record,
                        "high_disruption_action_rate",
                        "high_disruption_rate",
                        default=0.0,
                    )
                    or 0.0
                )
                + float(self.selector_penalty_weights.get("final_critical", 1.0))
                * (
                    _metric(
                        record,
                        "final_critical_compromised_hosts",
                        "final_critical_compromised",
                        default=0.0,
                    )
                    or 0.0
                )
            )
            score = utility - penalty
            if score > best_score:
                best_score = score
                best_utility = utility
                best_record = record
        if best_record is None:
            raise ValueError("policy_set must not be empty")
        selected = dict(best_record)
        selected["preference"] = weights.tolist()
        selected["utility"] = float(best_utility)
        selected["penalized_utility"] = float(best_score)
        return selected

    def ensure_archive_seed_thresholds(self) -> dict[str, float]:
        if self.archive_seed_thresholds:
            return dict(self.archive_seed_thresholds)
        stage1_buffer = self._stage1_buffer_path()
        if stage1_buffer is None:
            return {}
        self.archive_seed_thresholds = compute_shared_thresholds([stage1_buffer])
        return dict(self.archive_seed_thresholds)

    def _stage1_buffer_path(self) -> Path | None:
        raw_path = self.metadata.get("stage1_buffer")
        if raw_path:
            return Path(raw_path).resolve()
        if self.buffer_path is not None and self.metadata.get("stage") == "stage1":
            return self.buffer_path
        return None

    def _semantic_metrics(self, record: dict) -> dict[str, float]:
        policy_id = str(record.get("policy_id"))
        if policy_id in self._semantic_cache:
            return dict(self._semantic_cache[policy_id])
        if self.semantic_eval_episodes <= 0 or self.buffer_path is None:
            return {}
        metrics = _semantic_metrics_for_record(
            record,
            self.metadata,
            self.buffer_path,
            eval_episodes=self.semantic_eval_episodes,
        )
        self._semantic_cache[policy_id] = dict(metrics)
        return dict(metrics)

    def _strict_state(self, record: dict) -> dict[str, Any]:
        violation = _metric(record, "mean_violation", default=None)
        high_disruption = _metric(
            record, "high_disruption_action_rate", "high_disruption_rate", default=None
        )
        final_critical = _metric(
            record,
            "final_critical_compromised_hosts",
            "final_critical_compromised",
            default=None,
        )
        is_seed = _is_seed_record(record)
        base_cost_return = None
        if not is_seed:
            base_vector = record.get("base_objective_vector")
            if base_vector is not None:
                base_array = np.asarray(base_vector, dtype=np.float32)
                if base_array.size >= 3:
                    base_cost_return = float(base_array[2])
        cost_return = _metric(record, "cost_return", default=None)
        cost_delta_tolerance = float(self.cons_thresholds.get("cost_delta_tolerance", 3.0))
        relative_cost_ok = True
        relative_cost_margin = 0.0
        if not is_seed:
            if cost_return is None or base_cost_return is None:
                relative_cost_ok = False
            else:
                relative_cost_margin = float(cost_return) - (
                    float(base_cost_return) - cost_delta_tolerance
                )
                relative_cost_ok = bool(relative_cost_margin >= 0.0)

        eligible = (
            violation is not None
            and high_disruption is not None
            and final_critical is not None
            and (is_seed or base_cost_return is not None)
            and (is_seed or cost_return is not None)
        )
        ineligibility_reason = None
        if not eligible:
            if violation is None:
                ineligibility_reason = "missing_mean_violation"
            elif high_disruption is None:
                ineligibility_reason = "missing_high_disruption"
            elif final_critical is None:
                ineligibility_reason = "missing_final_critical"
            elif not is_seed and base_cost_return is None:
                ineligibility_reason = "missing_base_cost_return"
            elif not is_seed and cost_return is None:
                ineligibility_reason = "missing_cost_return"

        tight = False
        near = False
        if eligible:
            disruption_ok = bool(
                float(high_disruption)
                <= float(self.cons_thresholds.get("high_disruption", 1.0))
            )
            tight = bool(
                float(violation) <= 0.0
                and relative_cost_ok
                and float(final_critical) <= 0.0
                and disruption_ok
            )
            near = bool(
                float(violation) <= float(self.cons_thresholds.get("violation", 0.5))
                and relative_cost_ok
                and float(final_critical)
                <= float(self.cons_thresholds.get("final_critical_near", 0.25))
                and disruption_ok
            )

        return {
            "eligible": bool(eligible),
            "ineligibility_reason": ineligibility_reason,
            "base_cost_return": base_cost_return,
            "relative_cost_ok": bool(relative_cost_ok),
            "relative_cost_margin": float(relative_cost_margin),
            "tight_feasible_flag": bool(tight),
            "near_feasible_flag": bool(near),
        }


def normalized_archive_sets(
    payload: dict,
    *,
    buffer_path: str | Path | None = None,
    cons_thresholds: dict[str, float] | None = None,
    uc_thresholds: dict[str, float] | None = None,
    selector_penalty_weights: dict[str, float] | None = None,
    preferences: Sequence[Sequence[float]] | None = None,
    utility_tolerance: float = 0.02,
    seed_uc_size: int | None = None,
    route_mode: str = "exclusive",
    semantic_eval_episodes: int | None = None,
) -> dict[str, Any]:
    metadata = dict(payload.get("metadata", {}))
    if semantic_eval_episodes is None:
        semantic_eval_episodes = int(
            metadata.get("evaluation", {}).get("eval_episodes", 1)
        )
    manager = DualArchiveManager(
        cons_thresholds=cons_thresholds,
        uc_thresholds=uc_thresholds,
        selector_penalty_weights=selector_penalty_weights,
        preferences=preferences,
        utility_tolerance=utility_tolerance,
        seed_uc_size=(
            max(int(seed_uc_size), 0)
            if seed_uc_size is not None
            else max(len(payload.get("uc_records", [])), 0)
        ),
        route_mode=route_mode,
        metadata=metadata,
        buffer_path=buffer_path,
        semantic_eval_episodes=semantic_eval_episodes,
        archive_seed_thresholds=metadata.get("archive_seed_thresholds", {}),
        archive_rule_version=str(
            metadata.get("archive_rule_version", ARCHIVE_RULE_VERSION)
        ),
    )

    raw_records = list(payload.get("records", []))
    records = [manager.annotate_record(record, raw_records) for record in raw_records]
    record_lookup = _record_lookup(records)

    raw_cons = list(payload.get("cons_records", []))
    if not raw_cons:
        raw_cons = [
            record
            for record in records
            if record.get("archive_role") == "cons" or _is_seed_record(record)
        ]
    cons_records = [
        dict(
            manager.annotate_record(
                record_lookup.get(str(record["policy_id"]), record),
                records,
            ),
            archive_role="cons",
        )
        for record in raw_cons
    ]

    raw_uc = list(payload.get("uc_records", []))
    if not raw_uc:
        raw_uc = [record for record in records if record.get("archive_role") == "uc"]
    uc_records = [
        dict(
            manager.annotate_record(
                record_lookup.get(str(record["policy_id"]), record),
                records,
            ),
            archive_role="uc",
        )
        for record in raw_uc
    ]

    if cons_records or uc_records:
        union_records = _dedupe_by_policy_id([*cons_records, *uc_records])
    else:
        union_records = records
    union_records = [manager.annotate_record(record, union_records) for record in union_records]

    raw_union_front = list(payload.get("union_front", []))
    if raw_union_front:
        union_front = [
            manager.annotate_record(
                record_lookup.get(str(record["policy_id"]), record),
                union_records,
            )
            for record in raw_union_front
        ]
    else:
        union_front = nondominated_filter(union_records)

    raw_pareto = list(payload.get("pareto_front", []))
    if raw_pareto:
        pareto_front = [
            manager.annotate_record(
                record_lookup.get(str(record["policy_id"]), record),
                records,
            )
            for record in raw_pareto
        ]
    else:
        pareto_front = nondominated_filter(records)

    manager.cons_records = cons_records
    manager.uc_records = uc_records
    manager.union_records = union_records
    manager.union_front = nondominated_filter(union_records)
    return {
        "records": records,
        "pareto": pareto_front,
        "cons": cons_records,
        "uc": uc_records,
        "union": union_records,
        "union_front": union_front,
        "manager": manager,
    }
