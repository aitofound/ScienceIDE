"""
SciAccel-RL reward: extract the shaped reward from Harbor's verifier output.

The verifier (running in a separate Docker container) produces a reward.json
with shaped scores per check. This module just selects the appropriate key
(task-dependent) and passes it through as the training signal.
"""

from __future__ import annotations

import logging
import os
from typing import Any

psrl_logger = logging.getLogger("psrl.sciaccel_rl.reward")
psrl_logger.setLevel(os.getenv("PSRL_LOGGING_LEVEL", "WARN"))


def compute_score(
    data_source: str,
    solution_str: str,
    ground_truth: Any,
    extra_info: dict,
    **kwargs: Any,
) -> dict:
    """
    Score one SciAccel-RL trajectory.

    The shaped reward is computed by Harbor's verifier inside a separate
    container and delivered via `extra_info["harbor_rewards"]`. This function
    selects the task-appropriate reward key and returns it.

    Args:
        data_source: Dataset tag (`sciaccel_rl`).
        solution_str: Unused.
        ground_truth: Unused.
        extra_info: Per-row metadata containing `harbor_rewards` (dict from
            the verifier), `reward_key` (which key to train on), and
            `task_name`.

    Returns:
        Dict with `score` in [0, 1] and `reward_extra_info` diagnostics.
    """
    reward_key = extra_info.get("reward_key", "reward")
    harbor_rewards = extra_info.get("harbor_rewards") or {}
    task_name = extra_info.get("task_name", "")

    score = float(harbor_rewards.get(reward_key, 0.0))

    return {
        "score": score,
        "reward_extra_info": {
            "task_name": task_name,
            "reward_key": reward_key,
            "all_rewards": harbor_rewards,
        },
    }
