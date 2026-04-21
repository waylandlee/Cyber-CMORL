from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import numpy as np


SHIELD_MODE_DISABLED = "disabled"
SHIELD_MODE_CRITICAL_PATH_HARD = "critical_path_hard"
SHIELD_MODE_CRITICAL_RECOVERY_PRIORITY = "critical_recovery_priority"
SHIELD_MODE_PRE_CRITICAL_CONTAINMENT_PRIORITY = (
    "pre_critical_containment_priority"
)

SHIELD_LEVEL_NONE = "none"
SHIELD_LEVEL_ENTERPRISE_ALERT = "enterprise_alert"
SHIELD_LEVEL_PRE_CRITICAL_CONTAINMENT = "pre_critical_containment"
SHIELD_LEVEL_CRITICAL = "critical"

SHIELD_RESPONSE_TIER_NONE = "none"
SHIELD_RESPONSE_TIER_ENTERPRISE_ALERT = "enterprise_alert"
SHIELD_RESPONSE_TIER_CRITICAL_RESTORE_ON_CRITICAL = "critical_restore_on_critical"
SHIELD_RESPONSE_TIER_CRITICAL_REMOVE_ON_CRITICAL = "critical_remove_on_critical"
SHIELD_RESPONSE_TIER_CRITICAL_ANALYSE_ON_CRITICAL = "critical_analyse_on_critical"
SHIELD_RESPONSE_TIER_CRITICAL_RESTORE_ON_ENTERPRISE_OPERATIONAL = (
    "critical_restore_on_enterprise_operational"
)
SHIELD_RESPONSE_TIER_CRITICAL_REMOVE_ON_ENTERPRISE_OPERATIONAL = (
    "critical_remove_on_enterprise_operational"
)
SHIELD_RESPONSE_TIER_CRITICAL_ANALYSE_ON_ENTERPRISE_OPERATIONAL = (
    "critical_analyse_on_enterprise_operational"
)
SHIELD_RESPONSE_TIER_CRITICAL_PATH_GENERAL = "critical_path_general"
SHIELD_RESPONSE_TIER_PRECRITICAL_RESTORE_ON_ENTERPRISE_OPERATIONAL_COMPROMISED = (
    "precritical_restore_on_enterprise_operational_compromised"
)
SHIELD_RESPONSE_TIER_PRECRITICAL_REMOVE_ON_ENTERPRISE_OPERATIONAL_COMPROMISED = (
    "precritical_remove_on_enterprise_operational_compromised"
)
SHIELD_RESPONSE_TIER_PRECRITICAL_ANALYSE_ON_ENTERPRISE_OPERATIONAL_COMPROMISED = (
    "precritical_analyse_on_enterprise_operational_compromised"
)
SHIELD_RESPONSE_TIER_PRECRITICAL_GENERAL_ENTERPRISE_OPERATIONAL = (
    "precritical_general_enterprise_operational"
)
SHIELD_RESPONSE_TIER_FALLBACK_NATIVE = "fallback_native"

ACTION_FAMILY_RESTORE = "restore"
ACTION_FAMILY_REMOVE = "remove"
ACTION_FAMILY_ANALYSE = "analyse"
ACTION_FAMILY_DECOY = "decoy"
ACTION_FAMILY_OTHER = "other"
ACTION_FAMILY_SLEEP = "sleep"

CRITICAL_RESPONSE_SHIELD_MODES = {
    SHIELD_MODE_CRITICAL_PATH_HARD,
    SHIELD_MODE_CRITICAL_RECOVERY_PRIORITY,
    SHIELD_MODE_PRE_CRITICAL_CONTAINMENT_PRIORITY,
}


@dataclass
class CriticalResponseShieldConfig:
    mode: str = SHIELD_MODE_DISABLED


def normalize_shield_mode(mode: str | CriticalResponseShieldConfig | None) -> str:
    if isinstance(mode, CriticalResponseShieldConfig):
        mode = mode.mode
    return str(mode or SHIELD_MODE_DISABLED).lower()


def shield_enabled(mode: str | CriticalResponseShieldConfig | None) -> bool:
    return normalize_shield_mode(mode) in CRITICAL_RESPONSE_SHIELD_MODES


def action_family_from_name(name: Any) -> str:
    action_name = str(name or "")
    if action_name == "Restore":
        return ACTION_FAMILY_RESTORE
    if action_name == "Remove":
        return ACTION_FAMILY_REMOVE
    if action_name == "Analyse":
        return ACTION_FAMILY_ANALYSE
    if action_name.startswith("Decoy"):
        return ACTION_FAMILY_DECOY
    if action_name == "Sleep":
        return ACTION_FAMILY_SLEEP
    return ACTION_FAMILY_OTHER


def default_policy_action_mask(env: Any) -> np.ndarray:
    if hasattr(env, "current_action_mask"):
        mask = np.asarray(env.current_action_mask(), dtype=np.float32)
        return mask.reshape(int(env.num_envs), int(env.action_dim))
    if hasattr(env, "sim") and hasattr(env.sim, "get_mask"):
        state = getattr(env.sim, "state", None)
        current_decoys = getattr(env.sim, "current_decoys", None)
        mask_payload = env.sim.get_mask(state, current_decoys)
        blue_mask = mask_payload.get("Blue", mask_payload)
        mask = np.asarray(blue_mask, dtype=np.float32)
        return mask.reshape(int(env.num_envs), int(env.action_dim))
    return np.ones((int(env.num_envs), int(env.action_dim)), dtype=np.float32)


def record_policy_mask_stats(env: Any, blocked_probability_mass: Any) -> None:
    if not hasattr(env, "set_last_policy_mask_stats"):
        return
    if blocked_probability_mass is None:
        return
    values = np.asarray(blocked_probability_mass, dtype=np.float32).reshape(int(env.num_envs))
    env.set_last_policy_mask_stats(blocked_probability_mass=values)


def shield_diagnostics_with_policy_stats(
    diagnostics: dict[str, Any],
    *,
    blocked_probability_mass: Iterable[float] | None = None,
) -> dict[str, Any]:
    payload = dict(diagnostics)
    values = (
        np.zeros(len(payload.get("shield_level", [])), dtype=np.float32)
        if blocked_probability_mass is None
        else np.asarray(list(blocked_probability_mass), dtype=np.float32)
    )
    payload["shield_blocked_probability_mass"] = values.astype(np.float32).tolist()
    return payload


def build_shielded_action_mask(
    *,
    native_mask: np.ndarray,
    action_catalog: list[dict[str, Any]],
    critical_present: np.ndarray,
    enterprise_foothold_present: np.ndarray,
    mode: str | CriticalResponseShieldConfig | None = SHIELD_MODE_CRITICAL_PATH_HARD,
    critical_compromised_target_mask: np.ndarray | None = None,
    enterprise_operational_compromised_target_mask: np.ndarray | None = None,
) -> tuple[np.ndarray, dict[str, Any]]:
    native = np.asarray(native_mask, dtype=np.float32)
    if native.ndim != 2:
        raise ValueError(f"native_mask must be 2D, got shape {native.shape}")
    num_envs, action_dim = native.shape
    if len(action_catalog) != action_dim:
        raise ValueError(
            f"action_catalog length {len(action_catalog)} does not match action_dim {action_dim}"
        )

    allowed = native > 0.0
    shield_active_flag = np.zeros(num_envs, dtype=np.int32)
    shield_level: list[str] = [SHIELD_LEVEL_NONE for _ in range(num_envs)]
    shield_response_tier: list[str] = [
        SHIELD_RESPONSE_TIER_NONE for _ in range(num_envs)
    ]
    shield_fallback_flag = np.zeros(num_envs, dtype=np.int32)
    shield_allowed_action_count = allowed.sum(axis=1).astype(np.int32)
    normalized_mode = normalize_shield_mode(mode)

    critical_path_targets = np.asarray(
        [bool(entry.get("_shield_is_critical_path_target", False)) for entry in action_catalog],
        dtype=bool,
    )
    non_user_non_sleep_targets = np.asarray(
        [bool(entry.get("_shield_is_non_user_non_sleep", False)) for entry in action_catalog],
        dtype=bool,
    )
    enterprise_operational_targets = np.asarray(
        [
            bool(entry.get("_shield_is_enterprise_operational_non_sleep", False))
            for entry in action_catalog
        ],
        dtype=bool,
    )
    restore_targets = np.asarray(
        [
            str(entry.get("_shield_action_family", ACTION_FAMILY_OTHER))
            == ACTION_FAMILY_RESTORE
            for entry in action_catalog
        ],
        dtype=bool,
    )
    remove_targets = np.asarray(
        [
            str(entry.get("_shield_action_family", ACTION_FAMILY_OTHER))
            == ACTION_FAMILY_REMOVE
            for entry in action_catalog
        ],
        dtype=bool,
    )
    analyse_targets = np.asarray(
        [
            str(entry.get("_shield_action_family", ACTION_FAMILY_OTHER))
            == ACTION_FAMILY_ANALYSE
            for entry in action_catalog
        ],
        dtype=bool,
    )

    critical_present = np.asarray(critical_present, dtype=bool).reshape(num_envs)
    enterprise_foothold_present = np.asarray(
        enterprise_foothold_present,
        dtype=bool,
    ).reshape(num_envs)
    if critical_compromised_target_mask is None:
        critical_compromised_target_mask = np.zeros(
            (num_envs, action_dim),
            dtype=bool,
        )
    if enterprise_operational_compromised_target_mask is None:
        enterprise_operational_compromised_target_mask = np.zeros(
            (num_envs, action_dim),
            dtype=bool,
        )
    critical_compromised_target_mask = np.asarray(
        critical_compromised_target_mask,
        dtype=bool,
    ).reshape(num_envs, action_dim)
    enterprise_operational_compromised_target_mask = np.asarray(
        enterprise_operational_compromised_target_mask,
        dtype=bool,
    ).reshape(num_envs, action_dim)

    for env_idx in range(num_envs):
        row_native = allowed[env_idx]
        row_allowed = row_native.copy()
        row_response_tier = SHIELD_RESPONSE_TIER_NONE

        if critical_present[env_idx]:
            shield_active_flag[env_idx] = 1
            shield_level[env_idx] = SHIELD_LEVEL_CRITICAL
            if normalized_mode in {
                SHIELD_MODE_CRITICAL_RECOVERY_PRIORITY,
                SHIELD_MODE_PRE_CRITICAL_CONTAINMENT_PRIORITY,
            }:
                critical_target_mask = critical_compromised_target_mask[env_idx]
                enterprise_operational_target_mask = (
                    enterprise_operational_compromised_target_mask[env_idx]
                )
                critical_recovery_tiers = (
                    (
                        SHIELD_RESPONSE_TIER_CRITICAL_RESTORE_ON_CRITICAL,
                        np.logical_and.reduce(
                            (row_native, restore_targets, critical_target_mask)
                        ),
                    ),
                    (
                        SHIELD_RESPONSE_TIER_CRITICAL_REMOVE_ON_CRITICAL,
                        np.logical_and.reduce(
                            (row_native, remove_targets, critical_target_mask)
                        ),
                    ),
                    (
                        SHIELD_RESPONSE_TIER_CRITICAL_ANALYSE_ON_CRITICAL,
                        np.logical_and.reduce(
                            (row_native, analyse_targets, critical_target_mask)
                        ),
                    ),
                    (
                        SHIELD_RESPONSE_TIER_CRITICAL_RESTORE_ON_ENTERPRISE_OPERATIONAL,
                        np.logical_and.reduce(
                            (
                                row_native,
                                restore_targets,
                                enterprise_operational_target_mask,
                            )
                        ),
                    ),
                    (
                        SHIELD_RESPONSE_TIER_CRITICAL_REMOVE_ON_ENTERPRISE_OPERATIONAL,
                        np.logical_and.reduce(
                            (
                                row_native,
                                remove_targets,
                                enterprise_operational_target_mask,
                            )
                        ),
                    ),
                    (
                        SHIELD_RESPONSE_TIER_CRITICAL_ANALYSE_ON_ENTERPRISE_OPERATIONAL,
                        np.logical_and.reduce(
                            (
                                row_native,
                                analyse_targets,
                                enterprise_operational_target_mask,
                            )
                        ),
                    ),
                )
                for response_tier, candidate_mask in critical_recovery_tiers:
                    if np.any(candidate_mask):
                        row_allowed = candidate_mask
                        row_response_tier = response_tier
                        break
            if row_response_tier == SHIELD_RESPONSE_TIER_NONE:
                primary = np.logical_and(row_native, critical_path_targets)
                secondary = np.logical_and(row_native, non_user_non_sleep_targets)
                if np.any(primary):
                    row_allowed = primary
                    row_response_tier = SHIELD_RESPONSE_TIER_CRITICAL_PATH_GENERAL
                elif np.any(secondary):
                    row_allowed = secondary
                    row_response_tier = SHIELD_RESPONSE_TIER_CRITICAL_PATH_GENERAL
                else:
                    shield_fallback_flag[env_idx] = 1
                    row_response_tier = SHIELD_RESPONSE_TIER_FALLBACK_NATIVE
        elif enterprise_foothold_present[env_idx]:
            shield_active_flag[env_idx] = 1
            if normalized_mode == SHIELD_MODE_PRE_CRITICAL_CONTAINMENT_PRIORITY:
                shield_level[env_idx] = SHIELD_LEVEL_PRE_CRITICAL_CONTAINMENT
                enterprise_operational_target_mask = (
                    enterprise_operational_compromised_target_mask[env_idx]
                )
                precritical_containment_tiers = (
                    (
                        SHIELD_RESPONSE_TIER_PRECRITICAL_RESTORE_ON_ENTERPRISE_OPERATIONAL_COMPROMISED,
                        np.logical_and.reduce(
                            (
                                row_native,
                                restore_targets,
                                enterprise_operational_target_mask,
                            )
                        ),
                    ),
                    (
                        SHIELD_RESPONSE_TIER_PRECRITICAL_REMOVE_ON_ENTERPRISE_OPERATIONAL_COMPROMISED,
                        np.logical_and.reduce(
                            (
                                row_native,
                                remove_targets,
                                enterprise_operational_target_mask,
                            )
                        ),
                    ),
                    (
                        SHIELD_RESPONSE_TIER_PRECRITICAL_ANALYSE_ON_ENTERPRISE_OPERATIONAL_COMPROMISED,
                        np.logical_and.reduce(
                            (
                                row_native,
                                analyse_targets,
                                enterprise_operational_target_mask,
                            )
                        ),
                    ),
                )
                for response_tier, candidate_mask in precritical_containment_tiers:
                    if np.any(candidate_mask):
                        row_allowed = candidate_mask
                        row_response_tier = response_tier
                        break
                if row_response_tier == SHIELD_RESPONSE_TIER_NONE:
                    primary = np.logical_and(row_native, enterprise_operational_targets)
                    if np.any(primary):
                        row_allowed = primary
                        row_response_tier = (
                            SHIELD_RESPONSE_TIER_PRECRITICAL_GENERAL_ENTERPRISE_OPERATIONAL
                        )
                    else:
                        shield_fallback_flag[env_idx] = 1
                        row_response_tier = SHIELD_RESPONSE_TIER_FALLBACK_NATIVE
            else:
                shield_level[env_idx] = SHIELD_LEVEL_ENTERPRISE_ALERT
                primary = np.logical_and(row_native, enterprise_operational_targets)
                if np.any(primary):
                    row_allowed = primary
                    row_response_tier = SHIELD_RESPONSE_TIER_ENTERPRISE_ALERT
                else:
                    shield_fallback_flag[env_idx] = 1
                    row_response_tier = SHIELD_RESPONSE_TIER_FALLBACK_NATIVE

        if not np.any(row_allowed):
            row_allowed = row_native
            if shield_active_flag[env_idx]:
                shield_fallback_flag[env_idx] = 1
                row_response_tier = SHIELD_RESPONSE_TIER_FALLBACK_NATIVE

        allowed[env_idx] = row_allowed
        shield_allowed_action_count[env_idx] = int(np.sum(row_allowed))
        shield_response_tier[env_idx] = row_response_tier

    diagnostics = {
        "shield_active_flag": shield_active_flag.astype(np.int32).tolist(),
        "shield_level": list(shield_level),
        "shield_response_tier": list(shield_response_tier),
        "shield_fallback_flag": shield_fallback_flag.astype(np.int32).tolist(),
        "shield_allowed_action_count": shield_allowed_action_count.astype(np.int32).tolist(),
        "shield_blocked_probability_mass": np.zeros(num_envs, dtype=np.float32).tolist(),
    }
    return allowed.astype(np.float32), diagnostics
