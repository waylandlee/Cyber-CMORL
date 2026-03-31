from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields, is_dataclass
from pathlib import Path
from typing import Any, TypeVar

import yaml


@dataclass
class EnvConfig:
    num_envs: int = 8
    red_policy: str = "bline"
    remove_bugs: bool = True
    max_episode_steps: int = 100
    seed: int = 7


@dataclass
class ModelConfig:
    hidden_size: int = 128
    obj_dim: int = 3


@dataclass
class RolloutConfig:
    num_steps: int = 64


@dataclass
class EvalConfig:
    eval_episodes: int = 3
    preference_step: float | None = None


@dataclass
class IPOHyperConfig:
    clip_param: float = 0.2
    ppo_epochs: int = 4
    num_mini_batch: int = 4
    value_loss_coef: float = 0.5
    entropy_coef: float = 0.01
    learning_rate: float = 3e-4
    max_grad_norm: float = 0.5
    barrier_coef: float = 20.0
    beta: float = 0.9
    gamma: float = 0.995
    gae_lambda: float = 0.95
    eps: float = 1e-8


@dataclass
class Stage1Config:
    seed: int = 7
    total_timesteps: int = 1024
    num_policies: int = 6
    preference_strategy: str = "dirichlet_extremes"
    preference_step: float = 0.5
    preference_dirichlet_alpha: float = 1.0
    save_interval_updates: int = 0
    output_dir: str = "cmorl_minicage/outputs/stage1"
    env: EnvConfig = field(default_factory=EnvConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    rollout: RolloutConfig = field(default_factory=RolloutConfig)
    eval: EvalConfig = field(default_factory=EvalConfig)


@dataclass
class Stage2Config:
    seed: int = 19
    stage1_buffer: str = ""
    num_extension_policies: int = 6
    extension_rounds: int = 2
    constrained_updates: int = 2
    constraint_tolerance: float = 1e-6
    total_timesteps_per_update: int = 512
    output_dir: str = "cmorl_minicage/outputs/stage2"
    env: EnvConfig = field(default_factory=lambda: EnvConfig(seed=19))
    model: ModelConfig = field(default_factory=ModelConfig)
    rollout: RolloutConfig = field(default_factory=RolloutConfig)
    eval: EvalConfig = field(default_factory=EvalConfig)
    ipo: IPOHyperConfig = field(default_factory=IPOHyperConfig)


@dataclass
class EvaluateConfig:
    buffer_path: str = ""
    output_path: str = ""
    preference_step: float | None = None
    reference_strategy: str = "data_min_margin"
    reference_margin: float = 1.0
    reference_point: list[float] = field(default_factory=list)
    hv_max_exact_points: int = 18
    hv_mc_samples: int = 50000


T = TypeVar("T")

CONFIG_DIR = Path(__file__).resolve().parent / "configs"
DEFAULT_STAGE1_CONFIG = CONFIG_DIR / "stage1.yaml"
DEFAULT_STAGE2_CONFIG = CONFIG_DIR / "stage2.yaml"
DEFAULT_EVALUATE_CONFIG = CONFIG_DIR / "evaluate.yaml"


def _merge_dataclass(instance: T, overrides: dict[str, Any]) -> T:
    for field_info in fields(instance):
        name = field_info.name
        if name not in overrides:
            continue
        current = getattr(instance, name)
        incoming = overrides[name]
        if is_dataclass(current) and isinstance(incoming, dict):
            _merge_dataclass(current, incoming)
        else:
            setattr(instance, name, incoming)
    return instance


def _load_yaml(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"Config file must contain a mapping: {path}")
    return payload


def save_config_template(path: str | Path, config: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(asdict(config), handle, sort_keys=False, allow_unicode=True)


def load_stage1_config(path: str | Path | None = None) -> Stage1Config:
    config = Stage1Config()
    if path is None:
        return config
    return _merge_dataclass(config, _load_yaml(path))


def load_stage2_config(path: str | Path | None = None) -> Stage2Config:
    config = Stage2Config()
    if path is None:
        return config
    return _merge_dataclass(config, _load_yaml(path))


def load_evaluate_config(path: str | Path | None = None) -> EvaluateConfig:
    config = EvaluateConfig()
    if path is None:
        return config
    return _merge_dataclass(config, _load_yaml(path))
