from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import torch

from cmorl_minicage.buffer import load_policy_buffer
from cmorl_minicage.evaluate_constraints import _resolve_path
from cmorl_minicage.models import ActorCritic
from cmorl_minicage.shield import default_policy_action_mask, record_policy_mask_stats
from cmorl_minicage.utils import ensure_dir, save_json

from .compat import repo_root
from .env import CybORGMORLEnv
from .topology import topology_snapshot


FIGURE2_CONTEXT = "Figure 2 tight fair-compare"
TRACE_SCHEMA_VERSION = "figure2_attack_defense_trace.v1"
DEFAULT_METHODS = ("ours_stage2_fair", "no_constraint_stage2_fair")
DEFAULT_SEEDS = (7, 11, 19)
DEFAULT_EVAL_EPISODES = 3
DEFAULT_TIGHT_THRESHOLDS = {
    "d_business": -125.0,
    "d_cost": -22.0,
}


@dataclass(frozen=True)
class Figure2ReplayCandidate:
    policy_id: str
    candidate_label: str
    candidate_aliases: tuple[str, ...]


def default_output_root() -> Path:
    return (
        Path(__file__).resolve().parent
        / "outputs"
        / "paper_appendix"
        / "figure2_attack_defense_traces"
    )


def _tight_summary_path(method_name: str, seed: int) -> Path:
    return (
        Path(__file__).resolve().parent
        / "outputs"
        / "fair_compare_eval"
        / "tight_feasible_set_summary"
        / method_name
        / f"seed_{seed:04d}.json"
    )


def _reevaluated_summary_path(method_name: str, seed: int) -> Path:
    return (
        Path(__file__).resolve().parent
        / "outputs"
        / "fair_compare_eval"
        / "reevaluated_tight_feasible_set_summary"
        / method_name
        / f"seed_{seed:04d}.json"
    )


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _repo_root_candidates(path: str | Path | None) -> list[Path]:
    if path is None:
        return []
    probe = Path(path)
    candidates: list[Path] = []
    for candidate in (probe if probe.is_dir() else probe.parent, *probe.parents):
        if any((candidate / marker).exists() for marker in ("cmorl_cyborg", "cmorl_minicage", "paper")):
            candidates.append(candidate.resolve())
    deduped: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
    return deduped


def _repo_relative_candidates(path: str | Path) -> list[Path]:
    probe = Path(path)
    candidates: list[Path] = []
    for marker in ("cmorl_cyborg", "cmorl_minicage", "paper", "Debugged_CybORG"):
        if marker not in probe.parts:
            continue
        subpath = Path(*probe.parts[probe.parts.index(marker) :])
        candidates.append((repo_root() / subpath).resolve())
    return candidates


def resolve_artifact_path(
    raw_path: str | Path,
    *,
    anchor_path: str | Path | None = None,
) -> Path:
    path = Path(raw_path)
    candidates: list[Path] = []
    if path.is_absolute():
        candidates.append(path)
        candidates.extend(_repo_relative_candidates(path))
    else:
        if anchor_path is not None:
            try:
                candidates.append(_resolve_path(anchor_path, path))
            except Exception:
                pass
        candidates.append((repo_root() / path).resolve())
        for candidate_root in _repo_root_candidates(anchor_path):
            candidates.append((candidate_root / path).resolve())

    deduped: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
        if candidate.exists():
            return candidate
    if deduped:
        return deduped[0]
    raise FileNotFoundError(f"Could not resolve artifact path: {raw_path}")


def select_figure2_replay_candidates(
    method_name: str,
    tight_summary: dict[str, Any],
    reevaluated_summary: dict[str, Any],
) -> list[Figure2ReplayCandidate]:
    requested: list[tuple[str, str]] = []

    def add_candidate(label: str, policy_id: Any) -> None:
        if policy_id is None:
            return
        requested.append((label, str(policy_id)))

    add_candidate("selected", tight_summary.get("selected_policy_id"))
    add_candidate("closest_candidate", reevaluated_summary.get("closest_candidate_policy_id"))

    if method_name == "no_constraint_stage2_fair":
        feasible_rows = [
            row
            for row in reevaluated_summary.get("candidate_rows", [])
            if bool(row.get("is_reevaluated_feasible"))
        ]
        if feasible_rows:
            best_row = max(
                feasible_rows,
                key=lambda row: (
                    float(row.get("reevaluated_security_return", float("-inf"))),
                    str(row.get("policy_id", "")),
                ),
            )
            add_candidate("best_feasible_security", best_row.get("policy_id"))

    deduped: list[Figure2ReplayCandidate] = []
    by_policy: dict[str, int] = {}
    for label, policy_id in requested:
        if policy_id in by_policy:
            index = by_policy[policy_id]
            previous = deduped[index]
            deduped[index] = Figure2ReplayCandidate(
                policy_id=previous.policy_id,
                candidate_label=previous.candidate_label,
                candidate_aliases=previous.candidate_aliases + (label,),
            )
            continue
        by_policy[policy_id] = len(deduped)
        deduped.append(
            Figure2ReplayCandidate(
                policy_id=policy_id,
                candidate_label=label,
                candidate_aliases=(label,),
            )
        )
    return deduped


def _validate_tight_thresholds(payload: dict[str, Any]) -> dict[str, float]:
    threshold_block = (
        payload.get("tight_thresholds")
        or payload.get("thresholds")
        or {}
    )
    thresholds = {
        "d_business": float(payload.get("d_business", threshold_block.get("d_business"))),
        "d_cost": float(payload.get("d_cost", threshold_block.get("d_cost"))),
    }
    for key, expected in DEFAULT_TIGHT_THRESHOLDS.items():
        if not np.isclose(thresholds[key], expected):
            raise ValueError(
                f"Unexpected Figure 2 threshold for {key}: {thresholds[key]} != {expected}"
            )
    return thresholds


def _buffer_record_lookup(buffer_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for record in list(buffer_payload.get("records", [])) + list(buffer_payload.get("pareto_front", [])):
        policy_id = str(record.get("policy_id", ""))
        if policy_id and policy_id not in lookup:
            lookup[policy_id] = record
    return lookup


def _build_cyborg_env_from_metadata(metadata: dict[str, Any]) -> CybORGMORLEnv:
    env_config = metadata.get("env", {})
    model_config = metadata.get("model", {})
    return CybORGMORLEnv(
        num_envs=int(env_config.get("num_envs", 8)),
        red_policy=str(env_config.get("red_policy", "bline")),
        remove_bugs=bool(env_config.get("remove_bugs", True)),
        max_steps=int(env_config.get("max_episode_steps", 100)),
        seed=int(env_config.get("seed", 7)),
        scenario_name=str(env_config.get("scenario_name", "Scenario2")),
        scenario_profile=str(env_config.get("scenario_profile", "")),
        gym_wrapper_name=str(env_config.get("gym_wrapper_name", "ChallengeWrapper")),
        blue_agent_name=str(env_config.get("blue_agent_name", "Blue")),
        red_agent_name=str(env_config.get("red_agent_name", "Red")),
        obs_mode=str(env_config.get("obs_mode", "vector")),
        state_mode=str(env_config.get("state_mode", "true")),
        obj_dim=int(model_config.get("obj_dim", 3)),
        critical_host_safety_mode=str(
            model_config.get("critical_host_safety_mode", "v2_legacy")
        ),
        shield_mode=str(metadata.get("shield", {}).get("mode", "disabled")),
    )


def _load_actor_critic(checkpoint_path: Path, metadata: dict[str, Any]) -> ActorCritic:
    model_config = metadata.get("model", {})
    env = _build_cyborg_env_from_metadata(metadata)
    actor_critic = ActorCritic(
        obs_dim=env.obs_dim,
        action_dim=env.action_dim,
        obj_dim=int(model_config.get("obj_dim", 3)),
        hidden_sizes=(
            int(model_config.get("hidden_size", 128)),
            int(model_config.get("hidden_size", 128)),
        ),
    ).to(torch.device("cpu"))
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    actor_critic.load_state_dict(checkpoint)
    actor_critic.eval()
    return actor_critic


def _capture_rng_state() -> dict[str, Any]:
    return {
        "python": random.getstate(),
        "numpy": np.random.get_state(),
        "torch": torch.random.get_rng_state(),
    }


def _restore_rng_state(state: dict[str, Any]) -> None:
    random.setstate(state["python"])
    np.random.set_state(state["numpy"])
    torch.random.set_rng_state(state["torch"])


def _seed_eval_rng(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def _reward_terms_for_env(info: dict[str, Any], env_idx: int) -> dict[str, float]:
    def _value(key: str) -> float:
        field = info.get("reward_terms", {}).get(key, [0.0])
        if isinstance(field, list):
            if env_idx < len(field):
                return float(field[env_idx])
            return 0.0
        return float(field)

    reward_terms = {
        key: _value(key)
        for key in (
            "security",
            "business",
            "cost",
            "morl_scalar_reward",
            "cyborg_scalar_reward",
        )
    }
    if "critical_host_safety" in info.get("reward_terms", {}):
        reward_terms["critical_host_safety"] = _value("critical_host_safety")
    return reward_terms


def _semantic_info_for_env(info: dict[str, Any], env_idx: int) -> dict[str, float]:
    def _value(key: str) -> float:
        field = info.get("semantic_info", {}).get(key, [0.0])
        if isinstance(field, list):
            if env_idx < len(field):
                return float(field[env_idx])
            return 0.0
        return float(field)

    return {
        key: _value(key)
        for key in (
            "final_compromised_hosts",
            "final_critical_compromised_hosts",
            "persistent_critical_breach_rate",
            "critical_impact_count",
            "recovered_hosts",
            "analyse_count",
            "remove_count",
            "restore_count",
            "high_disruption_action_count",
            "total_action_count",
            "enterprise_foothold_present",
            "critical_present",
            "critical_hit_event",
            "critical_dwell_flag",
            "critical_path_compromise_count",
            "sleep_during_critical_breach",
            "user_action_during_critical_breach",
            "user_action_after_enterprise_foothold",
        )
    }


def _json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    raise TypeError(f"Unsupported JSON value: {type(value)!r}")


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, default=_json_default) + "\n")


def export_candidate_trace(
    *,
    method_name: str,
    seed: int,
    candidate: Figure2ReplayCandidate,
    buffer_path: str | Path,
    buffer_anchor_path: str | Path,
    record: dict[str, Any],
    metadata: dict[str, Any],
    output_root: str | Path,
    eval_episodes: int = DEFAULT_EVAL_EPISODES,
) -> Path:
    output_dir = ensure_dir(
        Path(output_root)
        / method_name
        / f"seed_{seed:04d}"
        / f"{candidate.candidate_label}__{candidate.policy_id}"
    )
    checkpoint_path = resolve_artifact_path(
        str(record.get("checkpoint_path", "")),
        anchor_path=buffer_anchor_path,
    )
    if not checkpoint_path.exists():
        raise FileNotFoundError(
            f"Checkpoint for {candidate.policy_id} was not found: {checkpoint_path}"
        )

    env = _build_cyborg_env_from_metadata(metadata)
    actor_critic = _load_actor_critic(checkpoint_path, metadata)
    topology = topology_snapshot(env.scenario_name, env.scenario_profile)
    action_catalog = env.action_catalog()

    manifest = {
        "trace_schema_version": TRACE_SCHEMA_VERSION,
        "figure_context": FIGURE2_CONTEXT,
        "method_name": method_name,
        "seed": int(seed),
        "policy_id": candidate.policy_id,
        "candidate_label": candidate.candidate_label,
        "candidate_aliases": list(candidate.candidate_aliases),
        "buffer_path": str(Path(buffer_path).resolve()),
        "buffer_anchor_path": str(buffer_anchor_path),
        "checkpoint_path": str(checkpoint_path.resolve()),
        "tight_thresholds": dict(DEFAULT_TIGHT_THRESHOLDS),
        "eval_episodes": int(eval_episodes),
        "shield": dict(metadata.get("shield", {})),
        "scenario_name": env.scenario_name,
        "scenario_profile": env.profile.profile_name,
        "red_policy": env.red_policy_name,
        "num_envs": int(env.num_envs),
    }
    save_json(output_dir / "trace_manifest.json", manifest)
    save_json(output_dir / "topology_snapshot.json", topology)
    save_json(output_dir / "action_catalog.json", action_catalog)

    episode_summaries: list[dict[str, Any]] = []
    base_seed = int(metadata.get("env", {}).get("seed", seed))
    rng_state = _capture_rng_state()
    try:
        with torch.no_grad():
            for episode_idx in range(max(int(eval_episodes), 1)):
                episode_seed = base_seed + episode_idx
                _seed_eval_rng(episode_seed)
                env.seed = episode_seed
                obs, reset_info = env.reset()
                finished = np.zeros(env.num_envs, dtype=bool)
                step_counts = np.zeros(env.num_envs, dtype=np.int32)
                returns = np.zeros((env.num_envs, env.obj_dim), dtype=np.float64)
                final_states = [dict(state) for state in reset_info.get("state_after", [])]
                rows: list[dict[str, Any]] = []

                while not np.all(finished):
                    obs_tensor = torch.as_tensor(obs, dtype=torch.float32)
                    action_mask = torch.as_tensor(
                        default_policy_action_mask(env),
                        dtype=torch.bool,
                    )
                    policy_output = actor_critic.act(
                        obs_tensor,
                        action_mask=action_mask,
                    )
                    record_policy_mask_stats(env, policy_output.blocked_probability_mass)
                    actions = policy_output.actions.cpu().numpy().reshape(
                        env.num_envs,
                        1,
                    )
                    active_before = np.logical_not(finished)
                    obs, reward_vec, done, truncated, info = env.step(actions)
                    returns += np.asarray(reward_vec, dtype=np.float64)

                    for env_idx in np.flatnonzero(active_before):
                        final_states[env_idx] = dict(info["state_after"][env_idx])
                        rows.append(
                            {
                                "episode_id": f"episode_{episode_idx:03d}",
                                "episode_seed": int(episode_seed),
                                "env_idx": int(env_idx),
                                "env_seed": int(episode_seed + env_idx * 1000),
                                "step_idx": int(step_counts[env_idx]),
                                "method_name": method_name,
                                "seed": int(seed),
                                "policy_id": candidate.policy_id,
                                "candidate_label": candidate.candidate_label,
                                "blue_action_index": int(actions[env_idx, 0]),
                                "blue_action": dict(info["blue_action_struct"][env_idx]),
                                "red_action": dict(info["red_action_struct"][env_idx]),
                                "reward_terms": _reward_terms_for_env(info, env_idx),
                                "semantic_info": _semantic_info_for_env(info, env_idx),
                                "state_before": dict(info["state_before"][env_idx]),
                                "state_after": dict(info["state_after"][env_idx]),
                                "newly_compromised_hosts": list(
                                    info["newly_compromised_hosts"][env_idx]
                                ),
                                "recovered_hosts": list(info["recovered_hosts"][env_idx]),
                                "critical_compromised_hosts": list(
                                    info["critical_compromised_hosts"][env_idx]
                                ),
                                "shield_active_flag": bool(
                                    info.get("shield_active_flag", [0])[env_idx]
                                ),
                                "shield_level": str(
                                    info.get("shield_level", ["none"])[env_idx]
                                ),
                                "shield_fallback_flag": bool(
                                    info.get("shield_fallback_flag", [0])[env_idx]
                                ),
                                "shield_blocked_probability_mass": float(
                                    info.get("shield_blocked_probability_mass", [0.0])[
                                        env_idx
                                    ]
                                ),
                                "shield_allowed_action_count": int(
                                    info.get(
                                        "shield_allowed_action_count",
                                        [env.action_dim],
                                    )[env_idx]
                                ),
                                "done": bool(done[env_idx]),
                                "truncated": bool(truncated[env_idx]),
                            }
                        )
                        step_counts[env_idx] += 1
                    finished |= np.asarray(done, dtype=bool) | np.asarray(truncated, dtype=bool)

                episode_path = output_dir / f"episode_{episode_idx:03d}.jsonl"
                _write_jsonl(episode_path, rows)
                episode_summaries.append(
                    {
                        "episode_id": f"episode_{episode_idx:03d}",
                        "episode_seed": int(episode_seed),
                        "num_trace_rows": int(len(rows)),
                        "env_summaries": [
                            {
                                "env_idx": int(env_idx),
                                "env_seed": int(episode_seed + env_idx * 1000),
                                "step_count": int(step_counts[env_idx]),
                                "return_vector": returns[env_idx].astype(np.float64).tolist(),
                                "final_state": final_states[env_idx],
                            }
                            for env_idx in range(env.num_envs)
                        ],
                    }
                )
    finally:
        _restore_rng_state(rng_state)

    save_json(output_dir / "episode_summaries.json", episode_summaries)
    return output_dir


def export_figure2_attack_defense_traces(
    *,
    methods: Iterable[str] = DEFAULT_METHODS,
    seeds: Iterable[int] = DEFAULT_SEEDS,
    output_root: str | Path = default_output_root(),
    eval_episodes: int = DEFAULT_EVAL_EPISODES,
) -> list[Path]:
    exported_dirs: list[Path] = []
    for method_name in methods:
        for seed in seeds:
            tight_summary = _load_json(_tight_summary_path(method_name, int(seed)))
            reevaluated_summary = _load_json(_reevaluated_summary_path(method_name, int(seed)))
            _validate_tight_thresholds(tight_summary)
            buffer_anchor = resolve_artifact_path(str(tight_summary["input_path"]))
            buffer_payload = load_policy_buffer(buffer_anchor)
            metadata = dict(buffer_payload.get("metadata", {}))
            record_lookup = _buffer_record_lookup(buffer_payload)
            candidates = select_figure2_replay_candidates(
                method_name,
                tight_summary,
                reevaluated_summary,
            )
            for candidate in candidates:
                if candidate.policy_id not in record_lookup:
                    raise KeyError(
                        f"Missing record for policy_id={candidate.policy_id} in {buffer_anchor}"
                    )
                exported_dirs.append(
                    export_candidate_trace(
                        method_name=method_name,
                        seed=int(seed),
                        candidate=candidate,
                        buffer_path=buffer_anchor,
                        buffer_anchor_path=tight_summary["input_path"],
                        record=record_lookup[candidate.policy_id],
                        metadata=metadata,
                        output_root=output_root,
                        eval_episodes=eval_episodes,
                    )
                )
    return exported_dirs


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export Figure 2 attack-defense traces via offline replay."
    )
    parser.add_argument("--methods", nargs="+", default=list(DEFAULT_METHODS))
    parser.add_argument("--seeds", nargs="+", type=int, default=list(DEFAULT_SEEDS))
    parser.add_argument("--eval-episodes", type=int, default=DEFAULT_EVAL_EPISODES)
    parser.add_argument("--output-root", default=str(default_output_root()))
    args = parser.parse_args()

    exported = export_figure2_attack_defense_traces(
        methods=args.methods,
        seeds=args.seeds,
        output_root=args.output_root,
        eval_episodes=args.eval_episodes,
    )
    print(f"Exported {len(exported)} candidate trace directories to {Path(args.output_root)}")


if __name__ == "__main__":
    main()
