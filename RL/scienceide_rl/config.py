"""
SciAccel-RL Runtime Configuration for PSRL.

Dataclass-based config for the Harbor-based SciAccel integration. Controls
Harbor Job parameters and episode timeouts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from omegaconf import OmegaConf


@dataclass
class HarborConfig:
    """
    Harbor Job execution settings.
    """

    jobs_dir: str = "/tmp/sciaccel_jobs"
    agent_name: str = "terminus-2"
    override_gpus: int | None = None
    gpu_compose_override: str = ""
    # Byte cap on one terminal observation. Harbor hardcodes 10000, so a lower value
    # needs the `agent.py` subclass that `agent_name` must point at.
    max_observation_bytes: int = 10000
    # Raise the task container memory above the `task.toml` declaration. A verifier whose
    # solver dies mid-run can hang instead of failing cleanly. Zero keeps the task's value.
    memory_mb_override: int = 0
    # Harbor containers are invisible to Ray scheduling, so nothing else bounds this.
    # Teardown is asynchronous, so an episode's containers outlive it.
    max_concurrent_episodes: int = 8


@dataclass
class SciAccelRuntimeConfig:
    """
    Top-level config for the SciAccel-RL PSRL integration.
    """

    harbor: HarborConfig = field(default_factory=HarborConfig)
    # Harbor enforces this external agent budget.
    # PSRL `wait_for` only provides a longer backstop.
    task_timeout_sec: float = 3600.0
    # Verifier budget. Only used to size that backstop, so it must be >= the task's
    # own `[verifier] timeout_sec` or the outer guard can pre-empt grading.
    verifier_timeout_sec: float = 900.0


def build_runtime_config(yaml_kwargs: dict[str, Any]) -> SciAccelRuntimeConfig:
    """
    Build config by merging YAML kwargs onto the structured schema.
    """
    raw = OmegaConf.to_container(OmegaConf.create(yaml_kwargs), resolve=True)
    if not isinstance(raw, dict):
        raw = {}
    raw.pop("name", None)
    raw.pop("_target_", None)

    schema = OmegaConf.structured(SciAccelRuntimeConfig)
    merged = OmegaConf.merge(schema, OmegaConf.create(raw))
    return OmegaConf.to_object(merged)
