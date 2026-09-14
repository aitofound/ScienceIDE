"""
Classify Harbor failures after LiteLLM strips transport metadata.
"""

from __future__ import annotations

from psrl.utils.agent.exceptions import AgentExceptionClassifier
from psrl.workers.agent_loop.loops.utils import TerminateReason


class HarborExceptionClassifier(AgentExceptionClassifier):
    """
    Map Harbor/terminus-2 failures onto PSRL terminate reasons.

    Used by `ScienceIDEAgentLoop` and by `scienceide_rl/eval` so training and
    evaluation classify identically.
    """

    # Timeout classes share a base, so names and ordering distinguish setup from runtime expiry.
    TYPE_MARKERS = (
        # The container or agent never started, so no turn was ever produced.
        ("AgentSetupTimeout", TerminateReason.ROLLOUT_ERROR),
        ("EnvironmentStartTimeout", TerminateReason.ROLLOUT_ERROR),
        ("SandboxBuildFailed", TerminateReason.ROLLOUT_ERROR),
        # The agent ran and used up its externally enforced wall-clock budget. The
        # turns it produced are valid on-policy data, so this is a truncation.
        ("AgentTimeout", TerminateReason.AGENT_TIMEOUT),
        # Grading timed out after the agent finished. The trajectory is still good, it
        # just scores 0 because no verifier reward arrived.
        ("VerifierTimeout", TerminateReason.VERIFIER_ERROR),
    )

    # Message markers for failures flattened into a bare `BadRequestError`.
    MESSAGE_MARKERS = (
        # SMG aborts are identified by sentinel body because headers are unavailable.
        ("Request aborted by PS Manager", TerminateReason.ABORTED),
        # Harbor's own wording for the externally enforced agent budget, which arrives
        # as text when `exception_type` is unavailable.
        ("Agent execution timed out", TerminateReason.AGENT_TIMEOUT),
        # An in-container command exceeded its own timeout during setup. Observed on a
        # session that produced zero turns, so it is infrastructure, not policy.
        ("Command timed out", TerminateReason.ROLLOUT_ERROR),
        # `Job.run` returned no trial at all, so nothing ran.
        ("no_trials", TerminateReason.ROLLOUT_ERROR),
    )
    # A vLLM context overflow relayed by litellm is handled by the base class, which
    # falls back to `is_prompt_overflow` and returns MAX_RESPONSE_LENGTH_EXCEEDED.


__all__ = ["HarborExceptionClassifier"]
