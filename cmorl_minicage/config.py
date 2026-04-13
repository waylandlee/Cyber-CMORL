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
    beta_mode: str = "fixed"
    beta_min: float = 0.88
    beta_max: float = 0.98
    schedule_weights: dict[str, float] = field(
        default_factory=lambda: {
            "crowding": 0.25,
            "expansion": 0.35,
            "low_risk": 0.20,
            "progress": 0.20,
        }
    )
    gamma: float = 0.995
    gae_lambda: float = 0.95
    eps: float = 1e-8


@dataclass
class SelectionConfig:
    mode: str = "crowding"
    score_weights: dict[str, float] = field(
        default_factory=lambda: {
            "crowding": 0.30,
            "expansion": 0.30,
            "low_risk": 0.20,
            "coverage": 0.20,
            "semantic_low_risk": 0.0,
        }
    )
    utility_tolerance: float = 0.02
    coverage_mode: str = "static"
    keep_extremes: bool = True
    semantic_eval_episodes: int = 0
    semantic_metric_weights: dict[str, float] = field(
        default_factory=lambda: {
            "high_disruption_action_rate": 0.50,
            "final_critical_compromised_hosts": 0.30,
            "critical_impact_count": 0.20,
        }
    )


@dataclass
class Stage1Config:
    seed: int = 7
    total_timesteps: int = 1024
    num_policies: int = 6
    preference_strategy: str = "dirichlet_extremes"
    preference_step: float = 0.5
    preference_dirichlet_alpha: float = 1.0
    explicit_preferences: list[list[float]] = field(default_factory=list)
    save_interval_updates: int = 0
    reseed_mode: str = "shared"
    independent_env_per_preference: bool = False
    preference_seed_stride: int = 1000
    env_seed_stride: int = 1000
    stage1_protocol_name: str = "legacy"
    parallel_workers: int = 1
    parallel_backend: str = "process"
    merge_order: str = "preference_index"
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
    max_consecutive_constraint_failures: int = 1
    extension_mode: str = "constrained"
    constraint_tolerance: float = 1e-6
    total_timesteps_per_update: int = 512
    semantic_penalty_coef: float = 0.0
    semantic_penalty_weights: dict[str, float] = field(
        default_factory=lambda: {
            "high_disruption_action_count": 0.50,
            "final_critical_compromised_hosts": 0.30,
            "critical_impact_count": 0.20,
        }
    )
    output_dir: str = "cmorl_minicage/outputs/stage2"
    env: EnvConfig = field(default_factory=lambda: EnvConfig(seed=19))
    model: ModelConfig = field(default_factory=ModelConfig)
    rollout: RolloutConfig = field(default_factory=RolloutConfig)
    eval: EvalConfig = field(default_factory=EvalConfig)
    selection: SelectionConfig = field(default_factory=SelectionConfig)
    ipo: IPOHyperConfig = field(default_factory=IPOHyperConfig)
    archive_mode: str = "single"
    num_cons_parents: int = 3
    num_uc_parents: int = 3
    route_mode: str = "exclusive"
    cons_operator_mode: str = "original"
    uc_operator_mode: str = "adacs_dcs"
    cons_risk_mode: str = "none"
    cvar_alpha: float = 0.25
    cvar_metric: str = "final_critical_compromised_hosts"
    cvar_penalty_coef: float = 0.25
    cvar_metric_weights: dict[str, float] = field(
        default_factory=lambda: {
            "final_critical_compromised_hosts": 1.0,
            "mean_violation": 1.0,
            "high_disruption_excess": 0.5,
        }
    )
    cons_risk_objective_mode: str = "none"
    cons_risk_penalty_coef: float = 0.5
    cons_thresholds: dict[str, float] = field(
        default_factory=lambda: {
            "violation": 0.5,
            "high_disruption": 1.0,
            "cost_margin": 0.0,
            "cost_delta_tolerance": 3.0,
            "final_critical_near": 0.25,
        }
    )
    uc_thresholds: dict[str, float] = field(
        default_factory=lambda: {
            "delta_eu": 0.001,
            "delta_coverage": 0.01,
            "novelty": 5.0,
            "spread_gain": 5.0,
        }
    )
    selector_mode_default: str = "strict"
    selector_penalty_weights: dict[str, float] = field(
        default_factory=lambda: {
            "violation": 1.0,
            "high_disruption": 1.0,
            "final_critical": 1.0,
        }
    )


@dataclass
class EvaluateConfig:
    buffer_path: str = ""
    output_path: str = ""
    preference_step: float | None = None
    selector_mode: str = "union"
    archive_source: str = "union"
    strict_require_tight: bool = False
    hybrid_penalty_weights: dict[str, float] = field(
        default_factory=lambda: {
            "mean_violation": 1.0,
            "high_disruption_rate": 1.0,
            "final_critical_compromised": 1.0,
        }
    )
    reference_strategy: str = "data_min_margin"
    reference_margin: float = 1.0
    reference_point: list[float] = field(default_factory=list)
    hv_max_exact_points: int = 18
    hv_mc_samples: int = 50000


@dataclass
class ConditionedEvaluateConfig:
    input_path: str = ""
    input_kind: str = "run_metadata"
    output_path: str = ""
    preference_step: float | None = None
    reference_strategy: str = "data_min_margin"
    reference_margin: float = 1.0
    reference_point: list[float] = field(default_factory=list)
    hv_max_exact_points: int = 18
    hv_mc_samples: int = 50000
    eval_episodes: int = 3


@dataclass
class ConstraintEvaluateConfig:
    method_name: str = ""
    input_kind: str = "buffer"
    input_path: str = ""
    selection_source: str = "pareto"
    selection_policy: str = "objective"
    security_margin: float = 120.0
    feasible_rate_tolerance: float = 0.10
    mean_violation_tolerance: float = 0.50
    semantic_metric_weights: dict[str, float] = field(
        default_factory=lambda: {
            "high_disruption_action_rate": 0.50,
            "final_critical_compromised_hosts": 0.30,
            "critical_impact_count": 0.20,
        }
    )
    thresholds_path: str = ""
    output_path: str = ""
    eval_episodes: int = 5


@dataclass
class PreferenceConditionedPPOConfig:
    seed: int = 7
    total_timesteps: int = 98304
    output_dir: str = "cmorl_minicage/outputs/paper_table_a/pref_conditioned_ppo"
    preference_strategy: str = "dirichlet"
    preference_step: float = 0.1
    preference_dirichlet_alpha: float = 1.0
    explicit_preferences: list[list[float]] = field(default_factory=list)
    clip_param: float = 0.2
    ppo_epochs: int = 4
    num_mini_batch: int = 4
    value_loss_coef: float = 0.5
    entropy_coef: float = 0.01
    learning_rate: float = 3e-4
    max_grad_norm: float = 0.5
    gamma: float = 0.995
    gae_lambda: float = 0.95
    env: EnvConfig = field(default_factory=EnvConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    rollout: RolloutConfig = field(default_factory=RolloutConfig)
    eval: EvalConfig = field(default_factory=EvalConfig)


@dataclass
class LagrangianPPOConfig:
    seed: int = 23
    total_timesteps: int = 98304
    output_dir: str = "cmorl_minicage/outputs/paper_table_b/lagrangian_ppo"
    stage1_buffer: str = ""
    thresholds_path: str = ""
    dual_lr: float = 0.05
    clip_param: float = 0.2
    ppo_epochs: int = 4
    num_mini_batch: int = 4
    value_loss_coef: float = 0.5
    entropy_coef: float = 0.01
    learning_rate: float = 3e-4
    max_grad_norm: float = 0.5
    gamma: float = 0.995
    gae_lambda: float = 0.95
    env: EnvConfig = field(default_factory=lambda: EnvConfig(seed=23))
    model: ModelConfig = field(default_factory=ModelConfig)
    rollout: RolloutConfig = field(default_factory=RolloutConfig)
    eval: EvalConfig = field(default_factory=EvalConfig)


@dataclass
class PCNConfig:
    seed: int = 29
    total_timesteps: int = 98304
    output_dir: str = "cmorl_minicage/outputs/paper_appendix/pcn"
    archive_sources: list[str] = field(default_factory=list)
    archive_episodes_per_source: int = 2
    batch_size: int = 256
    learning_rate: float = 3e-4
    num_epochs: int = 10
    hidden_size: int = 128
    eval_preferences_path: str = ""
    env: EnvConfig = field(default_factory=lambda: EnvConfig(seed=29))
    model: ModelConfig = field(default_factory=ModelConfig)
    eval: EvalConfig = field(default_factory=EvalConfig)


@dataclass
class CompareSuiteConfig:
    output_dir: str = "cmorl_minicage/outputs/paper_table_a"
    entries: list[dict[str, Any]] = field(default_factory=list)
    preference_step: float | None = 0.1
    reference_strategy: str = "data_min_range"
    reference_margin: float = 0.25
    reference_point: list[float] = field(default_factory=list)
    hv_max_exact_points: int = 18
    hv_mc_samples: int = 100000


@dataclass
class ExportTablesConfig:
    compare_summary_path: str = ""
    constraint_metrics_paths: list[str] = field(default_factory=list)
    appendix_metrics_paths: list[str] = field(default_factory=list)
    output_dir: str = "cmorl_minicage/outputs/paper_tables"


T = TypeVar("T")

CONFIG_DIR = Path(__file__).resolve().parent / "configs"
DEFAULT_STAGE1_CONFIG = CONFIG_DIR / "stage1.yaml"
DEFAULT_STAGE2_CONFIG = CONFIG_DIR / "stage2.yaml"
DEFAULT_EVALUATE_CONFIG = CONFIG_DIR / "evaluate.yaml"
DEFAULT_CONDITIONED_EVALUATE_CONFIG = CONFIG_DIR / "paper" / "evaluate_main_table_a.yaml"
DEFAULT_CONSTRAINT_EVALUATE_CONFIG = CONFIG_DIR / "paper" / "evaluate_main_table_b.yaml"


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


def load_conditioned_evaluate_config(
    path: str | Path | None = None,
) -> ConditionedEvaluateConfig:
    config = ConditionedEvaluateConfig()
    if path is None:
        return config
    return _merge_dataclass(config, _load_yaml(path))


def load_constraint_evaluate_config(
    path: str | Path | None = None,
) -> ConstraintEvaluateConfig:
    config = ConstraintEvaluateConfig()
    if path is None:
        return config
    return _merge_dataclass(config, _load_yaml(path))


def load_preference_conditioned_ppo_config(
    path: str | Path | None = None,
) -> PreferenceConditionedPPOConfig:
    config = PreferenceConditionedPPOConfig()
    if path is None:
        return config
    return _merge_dataclass(config, _load_yaml(path))


def load_lagrangian_ppo_config(path: str | Path | None = None) -> LagrangianPPOConfig:
    config = LagrangianPPOConfig()
    if path is None:
        return config
    return _merge_dataclass(config, _load_yaml(path))


def load_pcn_config(path: str | Path | None = None) -> PCNConfig:
    config = PCNConfig()
    if path is None:
        return config
    return _merge_dataclass(config, _load_yaml(path))


def load_compare_suite_config(path: str | Path | None = None) -> CompareSuiteConfig:
    config = CompareSuiteConfig()
    if path is None:
        return config
    return _merge_dataclass(config, _load_yaml(path))


def load_export_tables_config(path: str | Path | None = None) -> ExportTablesConfig:
    config = ExportTablesConfig()
    if path is None:
        return config
    return _merge_dataclass(config, _load_yaml(path))
