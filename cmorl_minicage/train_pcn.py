from __future__ import annotations

import argparse
import uuid
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

from cmorl_minicage.config import load_pcn_config
from cmorl_minicage.datasets import build_trajectory_archive
from cmorl_minicage.env import MiniCageMORLEnv
from cmorl_minicage.models import PCNPolicy
from cmorl_minicage.utils import ensure_dir, save_json, set_seed


def _prepare_batches(transitions: list[dict], batch_size: int) -> list[list[dict]]:
    batches: list[list[dict]] = []
    for start in range(0, len(transitions), batch_size):
        batch = transitions[start : start + batch_size]
        if batch:
            batches.append(batch)
    return batches


def train_pcn(config) -> Path:
    if not config.archive_sources:
        raise ValueError("archive_sources must not be empty")
    set_seed(config.seed)
    run_dir = ensure_dir(Path(config.output_dir) / f"run_{uuid.uuid4().hex[:8]}")
    archive_path = run_dir / "trajectory_archive.json"
    archive_payload = build_trajectory_archive(
        list(config.archive_sources),
        output_path=archive_path,
        episodes_per_source=config.archive_episodes_per_source,
    )
    transitions = list(archive_payload.get("transitions", []))
    if not transitions:
        raise ValueError("trajectory archive is empty")

    env = MiniCageMORLEnv(
        num_envs=config.env.num_envs,
        red_policy=config.env.red_policy,
        remove_bugs=config.env.remove_bugs,
        max_steps=config.env.max_episode_steps,
        seed=config.env.seed,
    )
    obs_dim = len(transitions[0]["obs"])
    command_dim = len(transitions[0]["return_to_go_vec"])
    action_dim = env.action_dim
    device = torch.device("cpu")
    model = PCNPolicy(
        obs_dim=obs_dim,
        command_dim=command_dim,
        action_dim=action_dim,
        hidden_sizes=(config.hidden_size, config.hidden_size),
    ).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    rng = np.random.default_rng(config.seed)
    training_log: list[dict[str, float]] = []

    for epoch_idx in range(config.num_epochs):
        rng.shuffle(transitions)
        batches = _prepare_batches(transitions, config.batch_size)
        epoch_loss = 0.0
        epoch_count = 0
        for batch in batches:
            obs = torch.as_tensor(
                [entry["obs"] for entry in batch], dtype=torch.float32, device=device
            )
            desired_return = torch.as_tensor(
                [entry["return_to_go_vec"] for entry in batch],
                dtype=torch.float32,
                device=device,
            )
            horizon = torch.as_tensor(
                [
                    [float(entry["remaining_horizon"]) / max(float(config.env.max_episode_steps), 1.0)]
                    for entry in batch
                ],
                dtype=torch.float32,
                device=device,
            )
            actions = torch.as_tensor(
                [entry["action"] for entry in batch], dtype=torch.long, device=device
            )
            logits = model(obs, desired_return, horizon)
            loss = F.cross_entropy(logits, actions)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            epoch_loss += float(loss.item())
            epoch_count += 1
        training_log.append(
            {
                "epoch_index": epoch_idx,
                "loss": epoch_loss / max(epoch_count, 1),
            }
        )

    checkpoint_path = run_dir / "policy_final.pt"
    torch.save(model.state_dict(), checkpoint_path)

    command_library_path = run_dir / "command_library.json"
    command_returns = np.unique(
        np.asarray(archive_payload.get("command_returns", []), dtype=np.float32), axis=0
    )
    save_json(
        command_library_path,
        {
            "schema_version": "0.1.0",
            "command_returns": command_returns.tolist(),
        },
    )

    metadata_path = run_dir / "conditioned_run_metadata.json"
    save_json(
        metadata_path,
        {
            "schema_version": "0.1.0",
            "method_name": "pcn",
            "model_type": "pcn",
            "policy_id": "pcn_final",
            "checkpoint_path": str(checkpoint_path),
            "command_library_path": str(command_library_path),
            "env": {
                "num_envs": config.env.num_envs,
                "red_policy": config.env.red_policy,
                "remove_bugs": config.env.remove_bugs,
                "max_episode_steps": config.env.max_episode_steps,
                "seed": config.env.seed,
            },
            "model": {
                "hidden_size": config.hidden_size,
                "obj_dim": config.model.obj_dim,
            },
            "evaluation": {
                "eval_episodes": config.eval.eval_episodes,
                "preference_step": config.eval.preference_step,
            },
            "training": {
                "seed": config.seed,
                "total_timesteps": config.total_timesteps,
                "num_epochs": config.num_epochs,
                "batch_size": config.batch_size,
                "learning_rate": config.learning_rate,
                "archive_sources": list(config.archive_sources),
                "archive_episodes_per_source": config.archive_episodes_per_source,
            },
        },
    )
    save_json(run_dir / "training_summary.json", training_log)
    return metadata_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a PCN-lite policy on MiniCAGE.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()

    config = load_pcn_config(args.config)
    if args.output_dir is not None:
        config.output_dir = args.output_dir
    metadata_path = train_pcn(config)
    print(metadata_path)


if __name__ == "__main__":
    main()
