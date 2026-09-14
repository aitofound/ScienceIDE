"""
Evaluate task-bank tasks through Harbor against OpenAI-compatible endpoints.

The evaluator selects each task's reward key and writes trial records plus summaries.
"""

from __future__ import annotations

import argparse
import asyncio
import fnmatch
import json
import logging
import os
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

import pandas as pd
from harbor.job import Job
from harbor.models.job.config import AgentConfig, JobConfig, SourceJobConfig
from harbor.models.trial.config import TaskConfig
from psrl.utils.agent.exceptions import is_prompt_overflow

psrl_logger = logging.getLogger(__file__)
psrl_logger.setLevel(os.getenv("PSRL_LOGGING_LEVEL", "INFO"))
if not psrl_logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    psrl_logger.addHandler(_handler)
    psrl_logger.propagate = False

# Anchor agents execute without a model endpoint.
# Oracle applies the reference solution while nop does nothing.
_ANCHOR_AGENTS = ("oracle", "nop")

# Path to the GPU device passthrough overlay, reused from the training config so
# the CUDA task sees the same devices in eval as in training.
_GPU_COMPOSE_OVERRIDE = Path(__file__).resolve().parents[1] / "config" / "gpu-compose-override.yaml"

# Redirect apt to an internal mirror on hosts without direct internet access.
_APT_MIRROR_OVERRIDE = Path(__file__).resolve().parents[1] / "config" / "apt-mirror-override.yaml"

# The shipped override carries a placeholder URL, which would fail the build several
# layers in with a DNS error rather than at the point the mistake was made.
_APT_MIRROR_PLACEHOLDER = "your-apt-mirror.example.com"


def _require_usable_apt_mirror() -> None:
    """
    Refuse to run with the unedited apt mirror placeholder.

    Raises:
        SystemExit: If the override file is missing or still holds the placeholder.
    """
    if not _APT_MIRROR_OVERRIDE.is_file():
        raise SystemExit(f"--apt-mirror needs {_APT_MIRROR_OVERRIDE}, which is missing.")
    if _APT_MIRROR_PLACEHOLDER in _APT_MIRROR_OVERRIDE.read_text(encoding="utf-8"):
        raise SystemExit(
            f"--apt-mirror was passed but {_APT_MIRROR_OVERRIDE} still holds the "
            f"placeholder URL. Replace it with a reachable mirror, or drop the flag "
            f"to build against the upstream Debian mirrors."
        )


def _load_tasks(
    dataset: str,
    categories: list[str] | None,
    families: list[str] | None,
    task_glob: str,
    per_family: int,
    limit: int,
) -> list[dict[str, Any]]:
    """
    Load and filter task rows from a Parquet built by `build_dataset`.

    Args:
        dataset (str): Path to `all.parquet` (or train/val).
        categories (list[str] | None): Keep only these taxonomy categories.
        families (list[str] | None): Keep only these families.
        task_glob (str): `fnmatch` pattern on the full task name. Empty keeps all.
        per_family (int): Keep at most this many tasks per (category, family, tree)
            group, taken in sorted name order. 0 disables the cap.
        limit (int): Keep at most this many tasks overall. 0 disables the cap.

    Returns:
        list[dict[str, Any]]: Task rows, each with `task_name` and `extra_info`.
    """
    df = pd.read_parquet(dataset)
    if categories:
        df = df[df["category"].isin(categories)]
    if families:
        df = df[df["family"].isin(families)]
    if task_glob:
        df = df[df["task_name"].map(lambda name: fnmatch.fnmatch(name, task_glob))]
    df = df.sort_values("task_name").reset_index(drop=True)

    if per_family > 0:
        df = (
            df.groupby(["category", "family", "tree"], sort=True, group_keys=False)
            .head(per_family)
            .reset_index(drop=True)
        )
    if limit > 0:
        df = df.head(limit).reset_index(drop=True)

    return [
        {
            "task_name": row["task_name"],
            "category": row["category"],
            "family": row["family"],
            "tree": row["tree"],
            "floor": float(row["floor"]),
            "extra_info": dict(row["extra_info"]),
        }
        for _, row in df.iterrows()
    ]


def _build_agent_config(
    agent: str,
    served_model_name: str,
    api_base: str,
    temperature: float,
    max_model_len: int,
    max_output_tokens: int,
    max_turns: int | None,
    llm_timeout: int,
) -> AgentConfig:
    """
    Build the Harbor agent config for either an anchor agent or terminus-2.

    Anchors take no model endpoint. The terminus-2 branch drops the training-only
    `collect_rollout_details` and points `api_base` at the vLLM server.

    Args:
        agent (str): Harbor agent name.
        served_model_name (str): The `model` field clients send, i.e. vLLM's
            `--served-model-name`.
        api_base (str): OpenAI-compatible base URL, including `/v1`.
        temperature (float): Sampling temperature.
        max_model_len (int): Context window, forwarded to terminus-2 as its token
            budget so it stops before vLLM rejects the request.
        max_output_tokens (int): Per-turn generation cap.
        max_turns (int | None): Episode cap. None leaves terminus-2 unbounded.
        llm_timeout (int): Per-request timeout in seconds.

    Returns:
        AgentConfig: Config for a single-agent Harbor job.
    """
    if agent in _ANCHOR_AGENTS:
        return AgentConfig(name=agent)

    return AgentConfig(
        name=agent,
        model_name=f"openai/{served_model_name}",
        env={"OPENAI_API_KEY": "EMPTY"},
        kwargs={
            "api_base": api_base,
            # Terminus-2's proactive summarization rewrites the transcript, which
            # destroys the turn structure the eval is trying to measure.
            "enable_summarize": False,
            # Bound turns so the verifier can grade work before context exhaustion.
            "max_turns": max_turns,
            "suppress_max_turns_warning": True,
            "temperature": temperature,
            # Keep the per-turn output budget below the full context window.
            "model_info": {
                "max_input_tokens": max_model_len,
                "max_output_tokens": max_output_tokens,
                "max_turns": max_turns,
                "input_cost_per_token": 0.0,
                "output_cost_per_token": 0.0,
            },
            "llm_kwargs": {
                "timeout": llm_timeout,
                "max_retries": 0,
            },
        },
    )


def _classify_exception(message: str | None, exc_type: str | None = None) -> str:
    """
    Bucket a trial exception so model failures stay separable from harness failures.

    Exception types are authoritative when Harbor records an empty message.

    Args:
        message (str | None): The trial's exception message, if any.
        exc_type (str | None): The exception class name Harbor recorded.

    Returns:
        str: One of `ok`, `prompt_overflow`, `timeout`, or `other`.
    """
    if not message and not exc_type:
        return "ok"

    type_name = (exc_type or "").lower()
    if "contextlengthexceeded" in type_name or "outputlengthexceeded" in type_name:
        return "prompt_overflow"
    if "timeout" in type_name:
        return "timeout"

    if message:
        if is_prompt_overflow(Exception(message)):
            return "prompt_overflow"
        lowered = message.lower()
        if "timeout" in lowered or "timed out" in lowered:
            return "timeout"
    return "other"


async def _run_batch(
    batch: list[dict[str, Any]],
    agent_config: AgentConfig,
    jobs_dir: Path,
    job_name: str,
    n_attempts: int,
    n_concurrent: int,
    timeout_multiplier: float,
    build_timeout_multiplier: float,
    apt_mirror: bool,
) -> list[dict[str, Any]]:
    """
    Run one Harbor Job over a batch of tasks and shape the per-trial records.

    Args:
        batch (list[dict[str, Any]]): Task rows from `_load_tasks`.
        agent_config (AgentConfig): Output of `_build_agent_config`.
        jobs_dir (Path): Root for Harbor job directories.
        job_name (str): Subdirectory name for this batch.
        n_attempts (int): Attempts per task.
        n_concurrent (int): Concurrent trials.
        timeout_multiplier (float): Scales the task-declared agent timeout.
        build_timeout_multiplier (float): Scales the task-declared environment
            build timeout.
        apt_mirror (bool): Whether to inject the apt mirror redirect overlay.

    Returns:
        list[dict[str, Any]]: One record per trial, score already resolved
            against each task's own reward key.
    """
    by_name = {row["extra_info"]["task_name"]: row for row in batch}
    needs_gpu = any(int(row["extra_info"].get("gpus", 0)) > 0 for row in batch)

    compose_overlays: list[Path] = []
    if apt_mirror and _APT_MIRROR_OVERRIDE.is_file():
        compose_overlays.append(_APT_MIRROR_OVERRIDE)
    if needs_gpu and _GPU_COMPOSE_OVERRIDE.is_file():
        compose_overlays.append(_GPU_COMPOSE_OVERRIDE)

    environment: dict[str, Any] = {}
    if compose_overlays:
        environment["extra_docker_compose"] = compose_overlays

    # NOTE(lhy): Harbor re-reads `instruction.md`, so `extra_instructions` is the only
    # path that delivers the hint. It is job-level rather than per-task, so a mixed
    # batch would hand every task the first task's hint.
    hints = {row["extra_info"].get("hint", "") for row in batch}
    if len(hints) > 1:
        raise ValueError(
            f"_run_batch received {len(batch)} tasks with differing hints. "
            "`extra_instructions` is job-level, so a mixed batch would deliver the "
            "wrong hint. Dispatch one task per job, or move the hint per task."
        )
    hint = next(iter(hints), "")

    job_config = JobConfig(
        job_name=job_name,
        jobs_dir=jobs_dir,
        tasks=[TaskConfig(path=row["extra_info"]["task_path"]) for row in batch],
        agents=[agent_config],
        n_attempts=n_attempts,
        n_concurrent_trials=n_concurrent,
        timeout_multiplier=timeout_multiplier,
        environment_build_timeout_multiplier=build_timeout_multiplier,
        quiet=True,
        **({"extra_instructions": [hint]} if hint else {}),
        **({"environment": environment} if environment else {}),
    )
    job = await Job.create(job_config)
    result = await job.run()

    records: list[dict[str, Any]] = []
    for trial in result.trial_results:
        rewards = (
            dict(trial.verifier_result.rewards) if trial.verifier_result and trial.verifier_result.rewards else {}
        )
        row = by_name.get(trial.task_name, {})
        extra_info = row.get("extra_info", {})
        reward_key = extra_info.get("reward_key", "reward")
        exception = trial.exception_info.exception_message if trial.exception_info else None
        exception_type = trial.exception_info.exception_type if trial.exception_info else None
        error_class = _classify_exception(exception, exception_type)

        # An empty reward dictionary means the verifier produced no measurement.
        if not rewards and error_class == "ok":
            error_class = "no_reward"

        # `n_episodes` is the Terminus turn counter.
        agent = trial.agent_result
        agent_meta = (agent.metadata or {}) if agent else {}
        n_input = agent.n_input_tokens if agent else None
        n_output = agent.n_output_tokens if agent else None

        records.append(
            {
                "task_name": trial.task_name,
                "trial_name": trial.trial_name,
                "category": row.get("category", ""),
                "family": row.get("family", ""),
                "tree": row.get("tree", ""),
                "reward_key": reward_key,
                # The score is the task's own training signal, NOT raw `reward`:
                # for repair and implementation the latter is lifted by the floor.
                "score": float(rewards.get(reward_key, 0.0)),
                "raw_reward": float(rewards.get("reward", 0.0)),
                "equivalence_pass": int(rewards.get("equivalence_pass", 0)),
                # Solved on the strict all-checks gate. A trial can earn partial
                # credit without passing, so these are different questions.
                "success": int(rewards.get("equivalence_pass", 0)) == 1,
                "n_turns": agent_meta.get("n_episodes"),
                "n_input_tokens": n_input,
                "n_output_tokens": n_output,
                "n_total_tokens": (n_input + n_output if n_input is not None and n_output is not None else None),
                "agent_seconds": _phase_seconds(trial.agent_execution),
                "env_setup_seconds": _phase_seconds(trial.environment_setup),
                "verifier_seconds": _phase_seconds(trial.verifier),
                "total_seconds": (
                    round((trial.finished_at - trial.started_at).total_seconds(), 1)
                    if trial.started_at and trial.finished_at
                    else None
                ),
                **_trajectory_lengths(trial.trial_uri),
                "floor_reported": rewards.get("floor"),
                "floor_expected": row.get("floor"),
                "rewards": rewards,
                "trial_uri": trial.trial_uri,
                "exception": exception,
                "exception_type": exception_type,
                "error_class": error_class,
            }
        )
    return records


def _trial_dir(trial_uri: str) -> Path:
    """Resolve a Harbor trial URI to a local directory.

    Harbor reports trial locations as `file://` URIs. Passing one straight to
    `Path()` yields the literal relative path `file:/path/to/trial`, which never
    exists, so every derived measurement silently came back None instead of
    failing loudly.

    Args:
        trial_uri (str): Trial location, either a file:// URI or a plain path.

    Returns:
        Path: The trial directory on disk.
    """
    parsed = urlparse(trial_uri)
    if parsed.scheme == "file":
        return Path(unquote(parsed.path))
    return Path(trial_uri)


def _trajectory_lengths(trial_uri: str | None) -> dict[str, int | None]:
    """
    Break a trial's transcript into its three contributing parts.

    The token counters Harbor reports are cumulative across turns: a multi-turn
    agent resends the whole transcript every turn, so `n_input_tokens` grows
    quadratically in turn count and is NOT the length of the trajectory. These
    are the one-time sizes instead, measured in characters off the recorded
    trajectory:

    - `prompt_chars`: the opening instruction, sent once.
    - `agent_chars`: everything the model emitted, summed over turns.
    - `env_chars`: everything the container emitted back, i.e. the tmux pane.
    - `traj_chars`: the three added up, the real conversation length.

    Args:
        trial_uri (str | None): Harbor trial directory.

    Returns:
        dict[str, int | None]: The four sizes, each None when unavailable.
    """
    empty = {"prompt_chars": None, "agent_chars": None, "env_chars": None, "traj_chars": None}
    if not trial_uri:
        return empty
    agent_dir = _trial_dir(trial_uri) / "agent"
    traj_path = agent_dir / "trajectory.json"
    if not traj_path.is_file():
        return empty

    try:
        steps = json.loads(traj_path.read_text()).get("steps", [])
    except (json.JSONDecodeError, OSError):
        return empty

    prompt_chars = 0
    agent_chars = 0
    for step in steps:
        message = step.get("message")
        if not isinstance(message, str):
            continue
        if step.get("source") == "agent":
            agent_chars += len(message)
        else:
            prompt_chars += len(message)

    pane = agent_dir / "terminus_2.pane"
    env_chars = pane.stat().st_size if pane.is_file() else 0

    return {
        "prompt_chars": prompt_chars,
        "agent_chars": agent_chars,
        "env_chars": env_chars,
        "traj_chars": prompt_chars + agent_chars + env_chars,
    }


def _phase_seconds(phase: Any) -> float | None:
    """
    Elapsed wall seconds of a Harbor `TimingInfo`, or None if unfinished.

    Args:
        phase (Any): A `TimingInfo` with `started_at` and `finished_at`.

    Returns:
        float | None: Seconds between the two stamps, rounded.
    """
    if phase is None:
        return None
    start, finish = getattr(phase, "started_at", None), getattr(phase, "finished_at", None)
    if start is None or finish is None:
        return None
    return round((finish - start).total_seconds(), 1)


def _aggregate(records: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Aggregate per-trial records into overall, per-category, and per-group metrics.

    `pass_rate` counts trials whose `equivalence_pass` is 1, which is the source
    benchmark's unchanged strict gate. `score` is the mean of the per-category
    training signal.

    Args:
        records (list[dict[str, Any]]): Per-trial records.

    Returns:
        dict[str, Any]: The `summary.json` payload minus the config block.
    """

    def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
        n = len(rows)
        if n == 0:
            return {"n_trials": 0}
        # pass@k over attempts of the same task: a task counts as solved if any
        # attempt cleared the strict gate.
        by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            by_task[row["task_name"]].append(row)
        solved = sum(1 for trials in by_task.values() if any(t["equivalence_pass"] == 1 for t in trials))

        def mean_of(key: str) -> float | None:
            """Mean over trials that reported the field, or None if none did."""
            vals = [r[key] for r in rows if r.get(key) is not None]
            return round(sum(vals) / len(vals), 1) if vals else None

        return {
            "n_trials": n,
            "n_tasks": len(by_task),
            "mean_score": round(sum(r["score"] for r in rows) / n, 6),
            "mean_raw_reward": round(sum(r["raw_reward"] for r in rows) / n, 6),
            "pass_rate": round(sum(r["equivalence_pass"] for r in rows) / n, 6),
            "pass_any_rate": round(solved / len(by_task), 6),
            "n_success": sum(1 for r in rows if r.get("success")),
            "mean_turns": mean_of("n_turns"),
            "mean_total_tokens": mean_of("n_total_tokens"),
            "mean_traj_chars": mean_of("traj_chars"),
            "mean_prompt_chars": mean_of("prompt_chars"),
            "mean_agent_chars": mean_of("agent_chars"),
            "mean_env_chars": mean_of("env_chars"),
            "mean_output_tokens": mean_of("n_output_tokens"),
            "mean_agent_seconds": mean_of("agent_seconds"),
            "mean_total_seconds": mean_of("total_seconds"),
            "n_errors": sum(1 for r in rows if r["error_class"] != "ok"),
            # Trials whose verifier was skipped by an agent-side exception and whose
            # score came from the artifact regrade pass instead of the live run.
            "n_regraded": sum(1 for r in rows if r.get("regraded")),
            # The measurement gap: no rewards even after regrading, i.e. nothing was
            # delivered to grade. These are true zeros, not lost measurements.
            "n_unmeasured": sum(1 for r in rows if not r.get("rewards")),
        }

    by_category: dict[str, Any] = {}
    for category in sorted({r["category"] for r in records}):
        by_category[category] = summarize([r for r in records if r["category"] == category])

    by_family: dict[str, Any] = {}
    keys = sorted({(r["category"], r["family"], r["tree"]) for r in records})
    for category, family, tree in keys:
        rows = [r for r in records if (r["category"], r["family"], r["tree"]) == (category, family, tree)]
        by_family[f"{category}/{family}/{tree}"] = summarize(rows)

    # Floor drift is a data-integrity check: the verifier measures the floor in
    # situ at image build time, and it should match what the dataset recorded.
    floor_mismatch = [
        {
            "task_name": r["task_name"],
            "reported": r["floor_reported"],
            "expected": r["floor_expected"],
        }
        for r in records
        if (
            r["floor_reported"] is not None
            and r["floor_expected"] is not None
            and abs(float(r["floor_reported"]) - float(r["floor_expected"])) > 1e-6
        )
    ]

    return {
        "overall": summarize(records),
        "by_category": by_category,
        "by_family": by_family,
        "errors": dict(Counter(r["error_class"] for r in records if r["error_class"] != "ok")),
        "floor_mismatch": floor_mismatch,
    }


async def _run_queue(
    tasks: list[dict[str, Any]],
    agent_configs: list[AgentConfig],
    jobs_dir: Path,
    max_per_instance: int,
    n_attempts: int,
    timeout_multiplier: float,
    build_timeout_multiplier: float,
    apt_mirror: bool,
    on_record: Any,
) -> list[dict[str, Any]]:
    """
    Drain a task queue across every endpoint, keeping all slots busy.

    Each endpoint gets `max_per_instance` workers, and every worker runs one task
    at a time as its own Harbor Job. A worker takes the next queued task the
    moment its current one finishes, so a slow task never blocks the others and
    utilisation stays flat until the queue runs dry. Batching by contrast idles
    a whole cohort waiting for its slowest member, and one unhostable task fails
    the entire Job it shares.

    Args:
        tasks (list[dict[str, Any]]): Task rows to run.
        agent_configs (list[AgentConfig]): One config per model endpoint.
        jobs_dir (Path): Root for Harbor job directories.
        max_per_instance (int): Concurrent tasks per endpoint.
        n_attempts (int): Attempts per task.
        timeout_multiplier (float): Scales task-declared agent timeouts.
        build_timeout_multiplier (float): Scales task-declared build timeouts.
        apt_mirror (bool): Whether to inject the apt mirror overlay.
        on_record (Any): Called with each finished record, for incremental
            persistence. Invoked from the event loop, so it must not block long.

    Returns:
        list[dict[str, Any]]: One record per trial, order not significant.
    """
    queue: asyncio.Queue[tuple[int, dict[str, Any]]] = asyncio.Queue()
    for index, task in enumerate(tasks):
        queue.put_nowait((index, task))

    records: list[dict[str, Any]] = []
    total = len(tasks)

    async def worker(endpoint_index: int, slot: int) -> None:
        agent_config = agent_configs[endpoint_index]
        while True:
            try:
                index, task = queue.get_nowait()
            except asyncio.QueueEmpty:
                return
            label = task["task_name"].replace("scienceide/", "")
            try:
                got = await _run_batch(
                    batch=[task],
                    agent_config=agent_config,
                    jobs_dir=jobs_dir,
                    job_name=f"task_{index:03d}",
                    n_attempts=n_attempts,
                    n_concurrent=n_attempts,
                    timeout_multiplier=timeout_multiplier,
                    build_timeout_multiplier=build_timeout_multiplier,
                    apt_mirror=apt_mirror,
                )
            except Exception as exc:
                # Job-level failure: record it against the task rather than
                # dropping the task from the denominator.
                psrl_logger.exception(f"[{label}] job raised:")
                got = [_failure_record(task, exc)]

            for record in got:
                records.append(record)
                on_record(record)
            psrl_logger.info(
                f"[{len(records)}/{total}] {label}: score={got[0]['score'] if got else 0.0:.3f} "
                f"turns={got[0].get('n_turns') if got else None} "
                f"err={got[0]['error_class'] if got else 'unknown'} "
                f"(ep{endpoint_index} slot{slot})"
            )
            queue.task_done()

    workers = [
        asyncio.create_task(worker(endpoint_index, slot))
        for endpoint_index in range(len(agent_configs))
        for slot in range(max_per_instance)
    ]
    await asyncio.gather(*workers)
    return records


async def _regrade_unverified(
    records: list[dict[str, Any]],
    tasks: list[dict[str, Any]],
    jobs_dir: Path,
    n_concurrent: int,
    build_timeout_multiplier: float,
) -> int:
    """
    Grade trials whose verifier never ran, from the artifacts they left behind.

    Harbor's trial body is a bare sequence (`harbor/trial/single_step.py`):
    `_run_agent()` then `_collect_artifacts()` then `_run_verifier()`, with no
    try/except between them. So any agent-side exception, usually a context overflow,
    skips verification entirely and the trial reports an empty
    reward dict. In the Qwen3.5-9B baseline that was 44 of 144 trials: not scored
    zero, but never measured at all.

    The recovery path still runs though: `_recover_outputs()` collects artifacts
    even on failure, so whatever the agent copied to `/logs/artifacts` before dying
    survives on disk. Harbor can grade exactly that, with no agent and no live
    container, via a `regrade` source job. LAPS tasks qualify because they declare
    `[verifier] environment_mode = "separate"`, i.e. the verifier reads
    `/logs/artifacts` rather than needing the agent's container alive.

    This turns "the harness lost the measurement" into a real ladder score. An
    episode that delivered and then overflowed on a later turn gets the partial
    credit it earned instead of a false zero, which matters most for RL, where a
    false zero is an incorrect label rather than merely a missing datapoint.

    Every unverified trial is regraded, including ones that delivered nothing. An
    earlier version skipped those to avoid spending a verifier build confirming a zero,
    which was a false economy: `rewards == {}` and a graded 0.0 are different facts,
    and only the graded result carries `floor` (0.0 for restore tasks, 0.5 for repair)
    that `reward_repair` normalizes against. Measured cost of grading an empty artifact
    dir: 31 s.

    Records are mutated in place: `score`, `raw_reward`, `equivalence_pass`,
    `rewards`, and `error_class` are filled in, and `regraded` is set to True so the
    two populations stay distinguishable in `results.jsonl`.

    Args:
        records (list[dict[str, Any]]): Trial records, mutated in place.
        tasks (list[dict[str, Any]]): Task rows, for `task_path` and `reward_key`.
        jobs_dir (Path): Where the original Job directories live.
        n_concurrent (int): Concurrent regrade trials.
        build_timeout_multiplier (float): Scales the verifier image build timeout.

    Returns:
        int: How many records were successfully regraded.
    """
    by_name = {row["task_name"]: row for row in tasks}
    pending: list[dict[str, Any]] = []
    for record in records:
        if record.get("rewards") or not record.get("trial_uri"):
            continue
        if by_name.get(record["task_name"]):
            pending.append(record)

    if not pending:
        return 0

    psrl_logger.info(f"Regrading unverified trials. Count: {len(pending)}...")

    n_regraded = 0
    for record in pending:
        row = by_name[record["task_name"]]
        source_dir = _trial_dir(record["trial_uri"]).parent
        config = JobConfig(
            jobs_dir=jobs_dir / "regrade",
            job_name=f"regrade_{Path(source_dir).name}",
            tasks=[TaskConfig(path=row["extra_info"]["task_path"])],
            source_jobs=[SourceJobConfig(action="regrade", type="local", path=source_dir.resolve())],
            n_concurrent_trials=n_concurrent,
            environment_build_timeout_multiplier=build_timeout_multiplier,
            quiet=True,
        )
        try:
            job = await Job.create(config)
            result = await job.run()
        except Exception as e:
            psrl_logger.warning(f"Regrade failed for {record['task_name']}: {e}.")
            continue

        for trial in result.trial_results or []:
            rewards = (
                dict(trial.verifier_result.rewards) if trial.verifier_result and trial.verifier_result.rewards else {}
            )
            if not rewards:
                continue
            reward_key = row["extra_info"].get("reward_key", "reward")
            record["rewards"] = rewards
            record["score"] = float(rewards.get(reward_key, 0.0))
            record["raw_reward"] = float(rewards.get("reward", 0.0))
            record["equivalence_pass"] = rewards.get("equivalence_pass")
            record["floor_reported"] = rewards.get("floor")
            record["success"] = rewards.get("equivalence_pass") == 1
            # Keep the original error_class: how the episode ended is still true, and
            # overwriting it would erase the fact that the agent hit the window.
            record["regraded"] = True
            n_regraded += 1

    psrl_logger.info(f"Regraded {n_regraded}/{len(pending)} trial(s).")
    return n_regraded


def _failure_record(task: dict[str, Any], exc: Exception) -> dict[str, Any]:
    """
    Build a zero-scored record for a task whose Job never produced a trial.

    Args:
        task (dict[str, Any]): The task row that failed.
        exc (Exception): The raised error.

    Returns:
        dict[str, Any]: A record shaped like a real trial result.
    """
    return {
        "task_name": task["extra_info"]["task_name"],
        "trial_name": "",
        "category": task["category"],
        "family": task["family"],
        "tree": task["tree"],
        "reward_key": task["extra_info"]["reward_key"],
        "score": 0.0,
        "raw_reward": 0.0,
        "equivalence_pass": 0,
        "success": False,
        "n_turns": None,
        "n_input_tokens": None,
        "n_output_tokens": None,
        "n_total_tokens": None,
        "agent_seconds": None,
        "env_setup_seconds": None,
        "verifier_seconds": None,
        "total_seconds": None,
        "prompt_chars": None,
        "agent_chars": None,
        "env_chars": None,
        "traj_chars": None,
        "floor_reported": None,
        "floor_expected": task["floor"],
        "rewards": {},
        "trial_uri": None,
        "exception": f"{type(exc).__name__}: {exc}",
        "exception_type": type(exc).__name__,
        "error_class": _classify_exception(str(exc), type(exc).__name__),
    }


def run_eval(
    *,
    dataset: str,
    output_dir: Path,
    agent: str,
    served_model_name: str,
    api_base: str,
    categories: list[str] | None,
    families: list[str] | None,
    task_glob: str,
    per_family: int,
    limit: int,
    n_attempts: int,
    n_concurrent: int,
    max_per_instance: int,
    temperature: float,
    max_model_len: int,
    max_output_tokens: int,
    max_turns: int | None,
    llm_timeout: int,
    timeout_multiplier: float,
    build_timeout_multiplier: float,
    apt_mirror: bool,
    skip_gpu_tasks: bool,
    regrade_unverified: bool = True,
) -> dict[str, Any]:
    """
    Orchestrate the full evaluation run and write the artefacts.

    Tasks are run in batches rather than as one giant Job so `results.jsonl`
    grows as work completes. A multi-hour run that dies partway still leaves
    every finished trial on disk.

    Args:
        dataset (str): Path to a v2 Parquet.
        output_dir (Path): Root output directory.
        agent (str): Harbor agent name (`oracle`, `nop`, `terminus-2`, ...).
        served_model_name (str): vLLM `--served-model-name`. Unused for anchors.
        api_base (str): OpenAI-compatible base URL. Unused for anchors.
        categories (list[str] | None): Category filter.
        families (list[str] | None): Family filter.
        task_glob (str): Task-name glob filter.
        per_family (int): Cap per (category, family, tree) group.
        limit (int): Overall task cap.
        n_attempts (int): Attempts per task.
        n_concurrent (int): Retained for reporting. Concurrency is set by
            `max_per_instance` times the endpoint count.
        max_per_instance (int): Concurrent tasks per model endpoint.
        temperature (float): Sampling temperature.
        max_model_len (int): Context window advertised to terminus-2.
        max_output_tokens (int): Per-turn generation cap sent as max_tokens.
        max_turns (int | None): Episode cap per trial. None means unbounded.
        llm_timeout (int): Per-request LLM timeout in seconds.
        timeout_multiplier (float): Scales task-declared timeouts.
        build_timeout_multiplier (float): Scales the task-declared environment
            build timeout. Raise it when image builds must fetch through a slow
            proxy.
        apt_mirror (bool): Whether to redirect apt to the internal Debian mirror
            during image builds. See `config/apt-mirror-override.yaml`.
        skip_gpu_tasks (bool): Drop tasks declaring `gpus > 0` instead of letting
            them fail on a provider without GPU support.
        regrade_unverified (bool): After the main pass, grade trials whose verifier
            never ran but which left `.dat` artifacts behind. An agent-side exception
            skips Harbor's verifier entirely, so those trials carry no measurement.
            Regrading recovers the ladder score from delivered artifacts.

    Returns:
        dict[str, Any]: The summary payload written to `summary.json`.
    """
    tasks = _load_tasks(dataset, categories, families, task_glob, per_family, limit)
    if not tasks:
        raise ValueError(f"No tasks matched the filters against dataset {dataset!r}.")

    if agent not in _ANCHOR_AGENTS and not served_model_name:
        raise ValueError(f"Agent {agent!r} needs --served-model-name and --api-base.")

    output_dir.mkdir(parents=True, exist_ok=True)
    results_path = output_dir / "results.jsonl"
    results_path.unlink(missing_ok=True)
    jobs_dir = output_dir / "jobs"

    endpoints = [b.strip() for b in api_base.split(",") if b.strip()]
    agent_configs = [
        _build_agent_config(
            agent=agent,
            served_model_name=served_model_name,
            api_base=endpoint,
            temperature=temperature,
            max_model_len=max_model_len,
            max_output_tokens=max_output_tokens,
            max_turns=max_turns,
            llm_timeout=llm_timeout,
        )
        for endpoint in endpoints
    ]

    # Drop GPU tasks when the local Docker provider cannot allocate GPUs.
    gpu_tasks = [t for t in tasks if int(t["extra_info"].get("gpus", 0)) > 0]
    if gpu_tasks and skip_gpu_tasks:
        psrl_logger.warning(
            f"Skipping GPU tasks unsupported by local Docker. Count: {len(gpu_tasks)}. "
            f"Tasks: {[t['task_name'] for t in gpu_tasks]!r}."
        )
        tasks = [t for t in tasks if int(t["extra_info"].get("gpus", 0)) == 0]

    slots = max_per_instance * len(agent_configs)
    psrl_logger.info(
        f"Evaluating tasks={len(tasks)} with agent={agent!r}, attempts={n_attempts}, "
        f"endpoints={len(endpoints)}, slots_per_endpoint={max_per_instance}, total_slots={slots}. "
        f"Endpoint URLs: {endpoints!r}."
    )

    t_start = time.monotonic()
    results_file = open(results_path, "a", encoding="utf-8")

    def persist(record: dict[str, Any]) -> None:
        """Append a finished record so a long run survives an interruption."""
        results_file.write(json.dumps(record, default=str) + "\n")
        results_file.flush()

    try:
        records = asyncio.run(
            _run_queue(
                tasks=tasks,
                agent_configs=agent_configs,
                jobs_dir=jobs_dir,
                max_per_instance=max_per_instance,
                n_attempts=n_attempts,
                timeout_multiplier=timeout_multiplier,
                build_timeout_multiplier=build_timeout_multiplier,
                apt_mirror=apt_mirror,
                on_record=persist,
            )
        )
    finally:
        results_file.close()

    if regrade_unverified and agent not in _ANCHOR_AGENTS:
        n_regraded = asyncio.run(
            _regrade_unverified(
                records=records,
                tasks=tasks,
                jobs_dir=jobs_dir,
                n_concurrent=n_concurrent,
                build_timeout_multiplier=build_timeout_multiplier,
            )
        )
        if n_regraded:
            # Rewrite live results after regrading to keep one row per task.
            with results_path.open("w", encoding="utf-8") as fh:
                for record in records:
                    fh.write(json.dumps(record) + "\n")

    summary = _aggregate(records)
    summary["config"] = {
        "dataset": dataset,
        "agent": agent,
        "served_model_name": served_model_name if agent not in _ANCHOR_AGENTS else "",
        "api_base": api_base if agent not in _ANCHOR_AGENTS else "",
        "n_endpoints": len(endpoints) if agent not in _ANCHOR_AGENTS else 0,
        "n_attempts": n_attempts,
        "n_concurrent": n_concurrent,
        "max_per_instance": max_per_instance,
        "slots_in_flight": slots,
        "temperature": temperature,
        "max_model_len": max_model_len,
        "max_output_tokens": max_output_tokens,
        "timeout_multiplier": timeout_multiplier,
        "build_timeout_multiplier": build_timeout_multiplier,
        "apt_mirror": apt_mirror,
        "skip_gpu_tasks": skip_gpu_tasks,
        "regrade_unverified": regrade_unverified,
        "filters": {
            "categories": categories,
            "families": families,
            "task_glob": task_glob,
            "per_family": per_family,
            "limit": limit,
        },
        "elapsed_s": round(time.monotonic() - t_start, 1),
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    _print_summary(summary, output_dir)
    return summary


def summarize_progress(records: list[dict[str, Any]]) -> str:
    """
    Render a one-line progress note for a finished batch.

    Args:
        records (list[dict[str, Any]]): Records from one batch.

    Returns:
        str: Human-readable mean score and error count.
    """
    if not records:
        return "no trials"
    mean = sum(r["score"] for r in records) / len(records)
    errors = sum(1 for r in records if r["error_class"] != "ok")
    return f"{len(records)} trials, mean score {mean:.4f}, {errors} errors"


def _print_summary(summary: dict[str, Any], output_dir: Path) -> None:
    """
    Print the summary tables to stdout.

    Args:
        summary (dict[str, Any]): Output of `_aggregate` plus the config block.
        output_dir (Path): Where the artefacts were written.
    """
    overall = summary["overall"]
    print("\n=== ScienceIDE RL evaluation complete ===")
    print(f"Trials  : {overall['n_trials']} over {overall['n_tasks']} tasks ({overall['n_errors']} errors)")
    print(f"Score   : {overall['mean_score']:.4f}  (raw reward {overall['mean_raw_reward']:.4f})")
    print(f"Pass    : {overall['pass_rate']:.2%} of trials, {overall['pass_any_rate']:.2%} of tasks")
    print(
        f"Effort  : {overall['mean_turns']} turns, {overall['mean_agent_seconds']}s agent, "
        f"{overall['mean_total_seconds']}s total (per trial, mean)"
    )
    print(
        f"Traj    : {overall['mean_traj_chars']} chars = {overall['mean_prompt_chars']} prompt "
        f"+ {overall['mean_agent_chars']} model + {overall['mean_env_chars']} env"
    )
    print(
        f"Tokens  : {overall['mean_total_tokens']} billed (cumulative over turns, "
        f"grows quadratically and does not represent trajectory length)"
    )

    print("\n--- by category ---")
    for name, stats in summary["by_category"].items():
        print(
            f"  {name:16s} n={stats['n_trials']:4d}  score={stats['mean_score']:.4f}  "
            f"raw={stats['mean_raw_reward']:.4f}  pass={stats['pass_rate']:.2%}  "
            f"turns={stats['mean_turns']}  tok={stats['mean_total_tokens']}  "
            f"{stats['mean_total_seconds']}s"
        )

    print("\n--- by family ---")
    for name, stats in summary["by_family"].items():
        print(
            f"  {name:34s} n={stats['n_trials']:4d}  score={stats['mean_score']:.4f}  "
            f"pass={stats['pass_rate']:.2%}  turns={stats['mean_turns']}  "
            f"tok={stats['mean_total_tokens']}  {stats['mean_total_seconds']}s  "
            f"err={stats['n_errors']}"
        )

    if summary["errors"]:
        print(f"\n--- errors --- {summary['errors']}")
    if summary["floor_mismatch"]:
        print(f"\n--- WARNING: floor drift on {len(summary['floor_mismatch'])} trials ---")
        for item in summary["floor_mismatch"][:5]:
            print(f"  {item['task_name']}: reported {item['reported']}, dataset {item['expected']}")

    print(f"\nOutput  : {output_dir}")


def main() -> None:
    """
    CLI entry point.
    """
    parser = argparse.ArgumentParser(description="Evaluate a model on ScienceIDE RL tasks.")
    parser.add_argument(
        "--dataset",
        default="scienceide_rl/data/v2/all.parquet",
        help="Path to a v2 Parquet built by build_dataset_v2.",
    )
    parser.add_argument("--output-dir", required=True, help="Output directory.")
    parser.add_argument(
        "--agent",
        default="terminus-2",
        help="Harbor agent name. oracle and nop are the anchors and need no model.",
    )
    parser.add_argument(
        "--served-model-name",
        default="",
        help="The model name the endpoint serves, i.e. vLLM --served-model-name.",
    )
    parser.add_argument(
        "--api-base",
        default="http://localhost:8000/v1",
        help=(
            "OpenAI-compatible base URL(s), including /v1. Comma-separate several "
            "to spread batches round-robin over independent servers, e.g. "
            "http://127.0.0.1:8000/v1,http://127.0.0.1:8001/v1"
        ),
    )
    parser.add_argument("--categories", nargs="+", default=None, help="Category filter.")
    parser.add_argument("--families", nargs="+", default=None, help="Family filter.")
    parser.add_argument("--task-glob", default="", help="Glob on the full task name.")
    parser.add_argument(
        "--per-family",
        type=int,
        default=0,
        help="Cap tasks per (category, family, tree) group. 0 disables.",
    )
    parser.add_argument("--limit", type=int, default=0, help="Overall task cap. 0 disables.")
    parser.add_argument("-k", "--n-attempts", type=int, default=1, help="Attempts per task.")
    parser.add_argument("-n", "--n-concurrent", type=int, default=4, help="Concurrent trials.")
    parser.add_argument(
        "--max-per-instance",
        type=int,
        default=32,
        help=(
            "Concurrent tasks per model endpoint. Total in flight is this times the "
            "number of --api-base endpoints. Each task runs as its own Harbor Job and "
            "a finished slot immediately takes the next queued task."
        ),
    )
    parser.add_argument("--temperature", type=float, default=1.0, help="Sampling temperature.")
    parser.add_argument(
        "--max-model-len",
        type=int,
        default=40960,
        help="Context window advertised to terminus-2.",
    )
    parser.add_argument(
        "--max-output-tokens",
        type=int,
        default=8192,
        help=(
            "Advisory per-turn output budget recorded in terminus-2's model_info. On "
            "the litellm chat path this is METADATA ONLY: nothing sends it as a "
            "per-request max_tokens, so it does not bound generation. Only the Responses "
            "API and cost accounting read it. Generation is bounded by the server's "
            "--max-model-len."
        ),
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=0,
        help=(
            "Cap agent turns per trial; 0 leaves terminus-2 unbounded (its default is "
            "1000000). Each turn resends the full transcript, so an uncapped run tends "
            "to exhaust the context window and die ungraded. A cap ends the loop "
            "cleanly and the verifier still scores what was delivered."
        ),
    )
    parser.add_argument("--llm-timeout", type=int, default=900, help="Per-request LLM timeout.")
    parser.add_argument(
        "--timeout-multiplier",
        type=float,
        default=1.0,
        help="Scales the task-declared agent timeout. Lower it to shorten smoke runs.",
    )
    parser.add_argument(
        "--build-timeout-multiplier",
        type=float,
        default=2.0,
        help=(
            "Scales the task-declared environment build timeout. Default 2.0 for "
            "headroom on the first cold build; the tasks themselves declare 3600s."
        ),
    )
    parser.add_argument(
        "--apt-mirror",
        dest="apt_mirror",
        action="store_true",
        help=(
            "Redirect apt to a local Debian mirror during image builds, using the URL in "
            "`config/apt-mirror-override.yaml`. Edit that file to point at your own mirror "
            "first. Worth doing only where the route to deb.debian.org is slow."
        ),
    )
    parser.set_defaults(apt_mirror=False)
    parser.add_argument(
        "--skip-gpu-tasks",
        action="store_true",
        help=(
            "Drop tasks that declare gpus > 0. Harbor's local Docker provider "
            "rejects them, so on such a host they can only ever be errors."
        ),
    )
    parser.add_argument(
        "--no-regrade",
        dest="regrade_unverified",
        action="store_false",
        help=(
            "Skip the post-pass that grades trials whose verifier never ran. An "
            "agent-side exception (usually a context overflow) makes Harbor skip "
            "verification entirely, leaving no measurement. The post-pass re-verifies "
            "Qwen3.5-9B baseline. The post-pass re-verifies those from the artifacts "
            "they delivered, with no agent and no GPU (~50s each). Only trials that "
            "actually delivered .dat files are regraded."
        ),
    )
    args = parser.parse_args()

    # Fail here rather than several Docker layers into every task's build.
    if args.apt_mirror:
        _require_usable_apt_mirror()

    run_eval(
        dataset=args.dataset,
        output_dir=Path(args.output_dir),
        agent=args.agent,
        served_model_name=args.served_model_name,
        api_base=args.api_base,
        categories=args.categories,
        families=args.families,
        task_glob=args.task_glob,
        per_family=args.per_family,
        limit=args.limit,
        n_attempts=args.n_attempts,
        n_concurrent=args.n_concurrent,
        max_per_instance=args.max_per_instance,
        temperature=args.temperature,
        max_model_len=args.max_model_len,
        max_output_tokens=args.max_output_tokens,
        max_turns=args.max_turns or None,
        llm_timeout=args.llm_timeout,
        timeout_multiplier=args.timeout_multiplier,
        build_timeout_multiplier=args.build_timeout_multiplier,
        apt_mirror=args.apt_mirror,
        skip_gpu_tasks=args.skip_gpu_tasks,
        regrade_unverified=args.regrade_unverified,
    )


if __name__ == "__main__":
    main()
