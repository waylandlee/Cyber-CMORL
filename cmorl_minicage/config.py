from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields, is_dataclass
from pathlib import Path
from typing import Any, TypeVar

import yaml

from .shield import CriticalResponseShieldConfig


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
    critical_host_safety_enabled: bool = False
    critical_host_safety_mode: str = "v2_legacy"


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
    pool_mode: str = "pareto"
    near_frontier_quota: int = 6
    strict_frontier_quota: int = 4
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
    semantic_score_mode: str = "legacy"
    semantic_thresholds_path: str = ""
    semantic_support_score_weights: dict[str, float] = field(
        default_factory=lambda: {
            "mean_violation": 0.40,
            "high_disruption": 0.30,
            "business": 0.20,
            "cost": 0.10,
        }
    )
    semantic_metric_weights: dict[str, float] = field(
        default_factory=lambda: {
            "high_disruption_action_rate": 0.50,
            "final_critical_compromised_hosts": 0.30,
            "critical_impact_count": 0.20,
        }
    )


@dataclass
class DeployabilityGateConfig:
    mode: str = "disabled"
    min_strict_margin_improvement: float = 0.25
    min_mean_violation_reduction: float = 0.25
    min_high_disruption_reduction: float = 0.01
    max_business_regression: float = 8.0
    max_cost_regression: float = 4.0
    max_final_critical_increase: float = 0.10
    max_ever_critical_breach_increase: float = 0.0
    max_persistent_critical_breach_increase: float = 0.05
    max_critical_hit_latency_score_drop: float = 0.05
    max_mean_critical_dwell_steps_increase: float = 3.0
    max_user_action_during_critical_breach_rate_increase: float = 0.02
    min_ever_critical_breach_reduction: float = 0.05
    min_persistent_critical_breach_reduction: float = 0.10
    min_critical_hit_latency_score_improvement: float = 0.10


@dataclass
class DeployabilityTargetConfig:
    mode: str = "disabled"
    reference_shell: str = "S0"
    min_target_score_improvement: float = 0.02
    min_target_excess_reduction: float = 0.02
    max_business_regression: float = 8.0
    max_cost_regression: float = 4.0
    max_final_critical_increase: float = 0.15
    max_ever_critical_breach_increase: float = 0.0
    max_persistent_critical_breach_increase: float = 0.05
    max_critical_hit_latency_score_drop: float = 0.05
    max_mean_critical_dwell_steps_increase: float = 3.0
    max_user_action_during_critical_breach_rate_increase: float = 0.02
    min_ever_critical_breach_reduction: float = 0.05
    min_persistent_critical_breach_reduction: float = 0.10
    min_critical_hit_latency_score_improvement: float = 0.10
    weights: dict[str, float] = field(
        default_factory=lambda: {
            "mean_violation": 0.55,
            "high_disruption": 0.30,
            "business": 0.10,
            "cost": 0.05,
        }
    )


@dataclass
class TailAcceptanceConfig:
    mode: str = "disabled"
    tail_eval_episodes: int = 16
    tail_alpha: float = 0.25
    business_guardrail: float = 8.0
    cost_guardrail: float = 4.0
    persistent_non_regression: bool = True
    dwell_slack: float = 5.0


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
    shield: CriticalResponseShieldConfig = field(
        default_factory=CriticalResponseShieldConfig
    )
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
    semantic_penalty_coef: float = 0.20
    semantic_penalty_weights: dict[str, float] = field(
        default_factory=lambda: {
            "critical_hit_event": 0.40,
            "critical_present": 0.25,
            "critical_path_compromise_count": 0.15,
            "user_action_during_critical_breach": 0.10,
            "sleep_during_critical_breach": 0.05,
            "user_action_after_enterprise_foothold": 0.05,
        }
    )
    output_dir: str = "cmorl_minicage/outputs/stage2"
    env: EnvConfig = field(default_factory=lambda: EnvConfig(seed=19))
    model: ModelConfig = field(default_factory=ModelConfig)
    shield: CriticalResponseShieldConfig = field(
        default_factory=CriticalResponseShieldConfig
    )
    rollout: RolloutConfig = field(default_factory=RolloutConfig)
    eval: EvalConfig = field(default_factory=EvalConfig)
    selection: SelectionConfig = field(default_factory=SelectionConfig)
    deployability_gate: DeployabilityGateConfig = field(
        default_factory=DeployabilityGateConfig
    )
    deployability_target: DeployabilityTargetConfig = field(
        default_factory=DeployabilityTargetConfig
    )
    tail_acceptance: TailAcceptanceConfig = field(
        default_factory=TailAcceptanceConfig
    )
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
class AssignmentDiagnosticsConfig:
    buffer_path: str = ""
    source_set: str = "pareto"
    thresholds_path: str = ""
    output_dir: str = "cmorl_minicage/outputs/assignment_diag"
    run_label: str = "tight_strict_seed0007"
    preference_step: float = 0.1
    eval_episodes: int = 5
    profile_name: str = "tight_strict_seed0007"
    mean_violation_max: float = 0.50
    final_critical_max: float = 0.25
    high_disruption_max: float = 0.50
    utility_floor_ratio: float = 0.10
    risk_penalty_weights: dict[str, float] = field(
        default_factory=lambda: {
            "business": 1.0,
            "cost": 1.0,
            "mean_violation": 2.0,
            "final_critical": 2.0,
            "high_disruption": 1.0,
        }
    )
    run_strict_level_on_supply: bool = True
    strict_level_output_dir: str = "cmorl_minicage/outputs/strict_level_diag"


@dataclass
class StrictLevelDiagnosticsConfig:
    candidate_cache_path: str = ""
    thresholds_path: str = ""
    output_dir: str = "cmorl_minicage/outputs/strict_level_diag"
    run_label: str = "tight_strict_seed0007"
    profile_name: str = "tight_strict_seed0007"
    high_disruption_max: float = 0.50
    levels: list[dict[str, Any]] = field(
        default_factory=lambda: [
            {
                "name": "L0",
                "final_critical_max": 1.00,
                "mean_violation_max": 1.25,
            },
            {
                "name": "L1",
                "final_critical_max": 0.95,
                "mean_violation_max": 1.00,
            },
            {
                "name": "L2",
                "final_critical_max": 0.75,
                "mean_violation_max": 0.75,
            },
            {
                "name": "L3",
                "final_critical_max": 0.50,
                "mean_violation_max": 0.60,
            },
            {
                "name": "STRICT",
                "final_critical_max": 0.25,
                "mean_violation_max": 0.50,
            },
        ]
    )


@dataclass
class MetricsSanityConfig:
    assignment_summary_path: str = ""
    candidate_cache_path: str = ""
    buffer_path: str = ""
    thresholds_path: str = ""
    output_dir: str = "cmorl_minicage/outputs/metrics_sanity"
    run_label: str = "tight_strict_seed0007"
    eval_episodes: int = 5


@dataclass
class SupportShellDiagnosticsConfig:
    assignment_summary_path: str = ""
    candidate_cache_path: str = ""
    thresholds_path: str = ""
    output_dir: str = "cmorl_minicage/outputs/support_shell_diag"
    run_label: str = "tight_strict_seed0007"
    profile_name: str = "tight_strict_seed0007"
    strict_mean_violation_max: float = 0.50
    strict_final_critical_max: float = 0.25
    strict_high_disruption_max: float = 0.50


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
DEFAULT_ASSIGNMENT_DIAGNOSTICS_CONFIG = (
    CONFIG_DIR / "diagnostics" / "assignment_diag.yaml"
)
DEFAULT_STRICT_LEVEL_DIAGNOSTICS_CONFIG = (
    CONFIG_DIR / "diagnostics" / "strict_level_diag.yaml"
)
DEFAULT_METRICS_SANITY_CONFIG = CONFIG_DIR / "diagnostics" / "metrics_sanity.yaml"
DEFAULT_SUPPORT_SHELL_DIAGNOSTICS_CONFIG = (
    CONFIG_DIR / "diagnostics" / "support_shell_diag.yaml"
)


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


def load_assignment_diagnostics_config(
    path: str | Path | None = None,
) -> AssignmentDiagnosticsConfig:
    config = AssignmentDiagnosticsConfig()
    if path is None:
        return config
    return _merge_dataclass(config, _load_yaml(path))


def load_strict_level_diagnostics_config(
    path: str | Path | None = None,
) -> StrictLevelDiagnosticsConfig:
    config = StrictLevelDiagnosticsConfig()
    if path is None:
        return config
    return _merge_dataclass(config, _load_yaml(path))


def load_metrics_sanity_config(
    path: str | Path | None = None,
) -> MetricsSanityConfig:
    config = MetricsSanityConfig()
    if path is None:
        return config
    return _merge_dataclass(config, _load_yaml(path))


def load_support_shell_diagnostics_config(
    path: str | Path | None = None,
) -> SupportShellDiagnosticsConfig:
    config = SupportShellDiagnosticsConfig()
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
