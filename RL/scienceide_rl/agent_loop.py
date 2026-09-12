"""
Run SciAccel tasks through Harbor and return TITO training data.
"""

import asyncio
import json
import logging
import os
import threading

from scienceide_rl.config import SciAccelRuntimeConfig, build_runtime_config
from scienceide_rl.runner import HarborEpisodeResult, run_harbor_episode
from psrl.utils.agent.overflow import is_prompt_overflow
from psrl.utils.agent.thinking import MULTI_TRAJ, select_trajectories
from psrl.workers.agent_loop.context import AgentLoopContext
from psrl.workers.agent_loop.loops.session_agent_loop import SessionAgentLoop
from psrl.workers.agent_loop.loops.utils import TerminateReason, register
from psrl.workers.gen.utils import TokenOutput

psrl_logger = logging.getLogger("psrl.sciaccel_rl.agent_loop")
psrl_logger.setLevel(os.getenv("PSRL_LOGGING_LEVEL", "WARN"))

# Harbor drops SMG error headers, so classify request aborts by sentinel body text.
_ABORT_MARKER = "Request aborted by PS Manager"


class _HarborLoopThread:
    """
    A single dedicated thread running its own asyncio event loop for Harbor Jobs.

    Harbor uses `asyncio.subprocess` internally, and concurrent `asyncio.run()` from
    separate threads races on process spawn. One shared loop serializes that while
    still allowing concurrent Harbor I/O.
    """

    def __init__(self):
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None

    def _start(self):
        if self._thread is not None and self._thread.is_alive():
            return
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._loop.run_forever,
            daemon=True,
            name="sciaccel-harbor-loop",
        )
        self._thread.start()

    def run(self, coro) -> asyncio.Future:
        self._start()
        return asyncio.run_coroutine_threadsafe(coro, self._loop)


_harbor_loop = _HarborLoopThread()

# Admission gate on concurrent Harbor episodes, created lazily on the Harbor loop
# because an `asyncio.Semaphore` binds to the loop that first awaits it.
_episode_gate: asyncio.Semaphore | None = None
_episode_gate_limit = 0


async def _acquire_episode_slot(limit: int) -> asyncio.Semaphore:
    """
    Return the shared episode gate, building it on first use.

    Runs on the Harbor loop, so no lock is needed: that loop is single threaded and
    this coroutine does not await before the assignment.

    Args:
        limit (int): Maximum concurrent episodes for this worker.

    Returns:
        asyncio.Semaphore: The gate, already acquired by the caller.
    """
    global _episode_gate, _episode_gate_limit
    if _episode_gate is None or _episode_gate_limit != limit:
        _episode_gate = asyncio.Semaphore(limit)
        _episode_gate_limit = limit
        psrl_logger.info("Harbor episode concurrency capped at %d per worker.", limit)
    await _episode_gate.acquire()
    return _episode_gate


@register("sciaccel")
class SciAccelAgentLoop(SessionAgentLoop):
    """
    Harbor-based episode runner for SciAccel-RL tasks.

    Each call to `run()` launches one Harbor Job (agent + verifier containers)
    with the model endpoint pointed at this session's TITO URL, then assembles
    the training data from TITO and the reward from the verifier.
    """

    def __init__(
        self,
        context: AgentLoopContext,
        **kwargs,
    ):
        super().__init__(context=context)
        runtime_kwargs = {k: kwargs[k] for k in ("harbor", "task_timeout_sec", "verifier_timeout_sec") if k in kwargs}
        self.runtime_config: SciAccelRuntimeConfig = build_runtime_config(runtime_kwargs)

        # Chosen once here so the trajectory-retention policy applied below and the
        # `extra_body` the runner sends the gateway are read from the same place.
        self.thinking_template: str = context.config.psrl.agentic_rl.get("thinking_template", MULTI_TRAJ)

        multi_turn = context.config.gen_actor_rollout_ref.rollout.multi_turn
        if not getattr(multi_turn, "enable", False):
            raise ValueError("SciAccelAgentLoop requires rollout.multi_turn.enable=True.")

    async def run(
        self,
        request: dict,
    ) -> tuple[TokenOutput | list[TokenOutput] | None, TerminateReason]:
        """
        Run one SciAccel-RL episode through Harbor and collect TITO training data.
        """
        extra_info = request.get("extra_info", {})
        if isinstance(extra_info, str):
            try:
                extra_info = json.loads(extra_info)
            except (json.JSONDecodeError, TypeError):
                extra_info = {}

        task_path = extra_info.get("task_path", "")
        reward_key = extra_info.get("reward_key", "reward")
        hint = extra_info.get("hint", "")
        needs_gpu = int(extra_info.get("gpus", 0)) > 0
        uid = request.get("uid", "?")

        if not task_path:
            psrl_logger.error("[uid=%s] task_path missing from extra_info.", uid)
            return None, TerminateReason.ROLLOUT_ERROR

        session_id: str | None = None
        try:
            session_id = await self.create_session(request)
            model_base_url = self.session_api_url(session_id)
            model_name = self.model_config.path
            psrl_logger.info(
                "[uid=%s] Starting Harbor episode: session=%s, task=%s, model_url=%s",
                uid,
                session_id,
                task_path,
                model_base_url,
            )

            harbor_result = await self._run_harbor_in_thread(
                task_path,
                model_base_url,
                model_name,
                needs_gpu=needs_gpu,
                session_id=session_id,
                hint=hint,
            )

            if harbor_result.exception:
                psrl_logger.warning(
                    "[uid=%s] Harbor episode exception: %s (rewards=%s).",
                    uid,
                    harbor_result.exception,
                    harbor_result.rewards,
                )
            else:
                psrl_logger.info(
                    "[uid=%s] Harbor episode completed: reward=%.3f, rewards=%s.",
                    uid,
                    harbor_result.reward,
                    harbor_result.rewards,
                )

            # Preserve valid on-policy turns captured before a context overflow.
            overflowed = bool(harbor_result.exception and is_prompt_overflow(Exception(harbor_result.exception)))
            if overflowed:
                # Keep any verifier score produced before overflow.
                psrl_logger.info(
                    "[uid=%s] Episode hit context overflow, training partial trajectory (verifier rewards=%s).",
                    uid,
                    harbor_result.rewards or "none -> reward 0",
                )

            # Map the SMG abort sentinel to `ABORTED` to prevent redundant group retries.
            if harbor_result.exception and _ABORT_MARKER in harbor_result.exception:
                psrl_logger.info(
                    "[uid=%s] Episode aborted by PSManager, discarding without group retry.",
                    uid,
                )
                return None, TerminateReason.ABORTED

            # SMG may fork one TITO trajectory per turn when thinking is split from content.
            # Select with `thinking_template` before reward logic broadcasts the advantage.
            training_data = select_trajectories(self.thinking_template, await self.get_training_data(session_id))
            num_turns = sum(item["num_turns"] for item in training_data)
            num_tokens = sum(len(item.get("response_ids", [])) for item in training_data)
            psrl_logger.info(
                "[uid=%s] TITO data (%s): %d trajector%s, num_turns=%d, response_tokens=%d.",
                uid,
                self.thinking_template,
                len(training_data),
                "y" if len(training_data) == 1 else "ies",
                num_turns,
                num_tokens,
            )
            if num_turns == 0:
                # Training entries require every rollout slot.
                # Report zero turns as an error so the manager refills the whole group.
                psrl_logger.warning(
                    "[uid=%s] Zero turns in TITO session, failing the group for refill.",
                    uid,
                )
                return None, TerminateReason.ROLLOUT_ERROR

            outputs = [
                self.build_token_output(
                    item,
                    extra_fields={
                        # Empty verifier rewards already map to zero in `reward.py`.
                        "harbor_rewards": harbor_result.rewards,
                        "reward_key": reward_key,
                        "task_name": harbor_result.task_name,
                    },
                )
                for item in training_data
            ]

            # `compute_reward_score` scores the last trajectory and broadcasts the result
            # to the rest, so the episode-level verifier reward reaches every sibling.
            scored_output = await self.compute_reward_score(outputs if len(outputs) > 1 else outputs[0], **request)
            if scored_output is None:
                return None, TerminateReason.ABORTED

            terminate_reason = TerminateReason.FINISHED
            if overflowed or num_tokens >= int(self.rollout_config.response_length):
                terminate_reason = TerminateReason.MAX_RESPONSE_LENGTH_EXCEEDED
            elif num_turns >= self.max_turns:
                terminate_reason = TerminateReason.MAX_TURNS_EXCEEDED
            elif harbor_result.exception and not harbor_result.rewards:
                # NOTE(lhy): An infrastructure failure leaves the reward dict empty, which
                # `reward.py` cannot tell from a graded 0.0. Reporting FINISHED would split
                # siblings of one task 0.0 against 1.0 on container luck alone.
                terminate_reason = TerminateReason.VERIFIER_ERROR
                psrl_logger.warning(
                    "[uid=%s] Verifier produced no reward (%s), reporting verifier_error "
                    "so the ungraded trajectory does not train as a real zero.",
                    uid,
                    harbor_result.exception_type or "unknown",
                )

            psrl_logger.info(
                "[uid=%s] Episode done: terminate=%s, reward=%.3f.",
                uid,
                terminate_reason.value,
                harbor_result.reward,
            )
            return scored_output, terminate_reason

        except asyncio.TimeoutError:
            psrl_logger.warning("[uid=%s] Harbor Job timed out (session=%s).", uid, session_id)
            return await self._try_recover_partial(session_id, request, reward_key, uid)
        except Exception as exc:
            psrl_logger.error("[uid=%s] SciAccelAgentLoop error: %s", uid, exc)
            recovered = await self._try_recover_partial(session_id, request, reward_key, uid)
            if recovered[0] is not None:
                return recovered
            raise
        finally:
            if session_id is not None:
                await self.delete_session(session_id)

    async def _try_recover_partial(
        self,
        session_id: str | None,
        request: dict,
        reward_key: str,
        uid: str,
    ) -> tuple[TokenOutput | list[TokenOutput] | None, TerminateReason]:
        """
        Attempt to recover partial training data from TITO after timeout/error.

        Turns captured by TITO before the timeout are valid training data. No verifier
        score exists on this path, so the reward is 0.
        """
        if session_id is None:
            return None, TerminateReason.ROLLOUT_ERROR
        try:
            training_data = select_trajectories(self.thinking_template, await self.get_training_data(session_id))
            num_turns = sum(item["num_turns"] for item in training_data)
            psrl_logger.info(
                "[uid=%s] Recovering partial data: %d trajector%s, %d turns from TITO.",
                uid,
                len(training_data),
                "y" if len(training_data) == 1 else "ies",
                num_turns,
            )
            if num_turns == 0:
                # Nothing to recover. Report an error so the manager purges the group and
                # refills it, because a train entry needs all `alg_rollout_n` slots.
                return None, TerminateReason.ROLLOUT_ERROR

            outputs = [
                self.build_token_output(
                    item,
                    extra_fields={
                        "harbor_rewards": {},
                        "reward_key": reward_key,
                        "task_name": "sciaccel/timeout",
                    },
                )
                for item in training_data
            ]
            scored_output = await self.compute_reward_score(outputs if len(outputs) > 1 else outputs[0], **request)
            if scored_output is None:
                return None, TerminateReason.ABORTED
            # Mark recovered turns as agent timeout data so the manager keeps this valid slot.
            return scored_output, TerminateReason.AGENT_TIMEOUT
        except Exception as recover_exc:
            psrl_logger.warning("[uid=%s] Partial recovery failed: %s.", uid, recover_exc)
            return None, TerminateReason.ROLLOUT_ERROR

    async def _run_harbor_in_thread(
        self,
        task_path: str,
        model_base_url: str,
        model_name: str,
        *,
        needs_gpu: bool = False,
        session_id: str = "",
        hint: str = "",
    ) -> HarborEpisodeResult:
        """
        Run the Harbor Job on the dedicated Harbor event loop thread.

        All Harbor Jobs share one event loop to avoid `asyncio.subprocess` races. The
        episode is admitted through a semaphore released only after `run_harbor_episode`
        tears its containers down, so a waiting episode starts against a clean daemon.
        """
        limit = int(self.runtime_config.harbor.max_concurrent_episodes)

        async def _gated() -> HarborEpisodeResult:
            gate = await _acquire_episode_slot(limit)
            try:
                return await run_harbor_episode(
                    task_path=task_path,
                    model_base_url=model_base_url,
                    model_name=model_name,
                    config=self.runtime_config,
                    needs_gpu=needs_gpu,
                    session_id=session_id,
                    max_model_len=int(self.rollout_config.get("max_model_len", 40960)),
                    max_turns=self.max_turns,
                    actor_id=os.getenv("PSRL_ACTOR_ID", ""),
                    thinking_template=self.thinking_template,
                    hint=hint,
                )
            finally:
                gate.release()

        future = _harbor_loop.run(_gated())
        # Harbor owns the timeout budget. Another deadline could discard valid slow episodes.
        return await asyncio.wrap_future(future)
