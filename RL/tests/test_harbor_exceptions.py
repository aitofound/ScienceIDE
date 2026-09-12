"""
Harbor failure classification, anchored to strings observed in real training logs.

The cascade this guards against: PSManager aborts a group's siblings, SMG answers
their in-flight turns with `request_aborted`, litellm re-raises it as a bare
`BadRequestError`, and classifying that as `ROLLOUT_ERROR` makes the manager abort the
group a second time. One slow episode then discards seven healthy trajectories.
"""

from scienceide_rl.exceptions import HarborExceptionClassifier
from psrl.utils.agent.exceptions import AgentExceptionClassifier, is_prompt_overflow
from psrl.utils.common.http_utils import (
    PromptOverflowError,
    RequestAbortedByGatewayError,
)
from psrl.workers.agent_loop.loops.utils import TerminateReason

CLASSIFIER = HarborExceptionClassifier()

# Verbatim from outputs/.../GRPO-sciaccel-laps-cpu-8B.log.
OVERFLOW_MSG = (
    "litellm.BadRequestError: OpenAIException - The prompt (length 32958) "
    "is longer than the maximum model length of 32768."
)
ABORT_MSG = "litellm.BadRequestError: OpenAIException - Request aborted by PS Manager"
AGENT_TIMEOUT_MSG = "Agent execution timed out after 1200.0 seconds"
SETUP_TIMEOUT_MSG = "Command timed out after 120 seconds"


def test_budget_failures_keep_their_data():
    """A budget that ran out still yields trainable turns."""
    for message, exc_type in [
        (OVERFLOW_MSG, None),
        (AGENT_TIMEOUT_MSG, "AgentTimeoutError"),
        ("verifier timed out", "VerifierTimeoutError"),
    ]:
        reason = CLASSIFIER.classify(message, exc_type=exc_type)
        assert reason is not None, message
        assert reason.is_successful, (
            f"Message={message!r}, reason={reason!r}: Classification would discard usable turns."
        )
        assert not reason.needs_manager_retry(), (
            f"Message={message!r}, reason={reason!r}: Classification would terminate the group."
        )


def test_timeout_and_verifier_have_distinct_reasons():
    """A clock timeout is not a turn cap, and a grading failure is neither."""
    assert CLASSIFIER.classify(AGENT_TIMEOUT_MSG, exc_type="AgentTimeoutError") is TerminateReason.AGENT_TIMEOUT
    assert CLASSIFIER.classify("x", exc_type="VerifierTimeoutError") is TerminateReason.VERIFIER_ERROR
    # Neither may be reported as MAX_TURNS_EXCEEDED, which means the turn cap was hit.
    assert TerminateReason.AGENT_TIMEOUT is not TerminateReason.MAX_TURNS_EXCEEDED
    assert TerminateReason.VERIFIER_ERROR is not TerminateReason.MAX_TURNS_EXCEEDED


def test_agent_timeout_keeps_data_without_retrying():
    """Re-running an episode whose turns were accepted would duplicate them."""
    reason = TerminateReason.AGENT_TIMEOUT
    assert reason.is_successful
    assert not reason.is_timeout, "is_timeout feeds needs_worker_retry, so data would double-count"
    assert not reason.needs_worker_retry()
    assert not reason.needs_manager_retry()


def test_verifier_error_is_trainable_and_not_an_error_class():
    reason = TerminateReason.VERIFIER_ERROR
    assert reason.is_successful
    assert not reason.is_error
    assert not reason.needs_worker_retry()
    assert not reason.needs_manager_retry()


def test_overflow_maps_to_max_response_length():
    assert CLASSIFIER.classify(OVERFLOW_MSG) is TerminateReason.MAX_RESPONSE_LENGTH_EXCEEDED


def test_deliberate_abort_never_retries_the_group():
    """The regression guard for the sibling-abort cascade."""
    reason = CLASSIFIER.classify(ABORT_MSG)
    assert reason is TerminateReason.ABORTED
    assert not reason.needs_manager_retry()
    assert not reason.is_successful


def test_setup_failures_are_faults_not_truncations():
    """Nothing ran, so there is no partial trajectory worth keeping."""
    for message, exc_type in [
        (SETUP_TIMEOUT_MSG, None),
        ("setup timed out", "AgentSetupTimeoutError"),
        ("environment did not start", "EnvironmentStartTimeoutError"),
        ("no_trials", "NoTrialsError"),
    ]:
        reason = CLASSIFIER.classify(message, exc_type=exc_type)
        assert reason is TerminateReason.ROLLOUT_ERROR, f"{message} -> {reason}"


def test_agent_setup_timeout_is_not_shadowed_by_agent_timeout():
    """`AgentSetupTimeout` contains `AgentTimeout`, so marker order matters."""
    assert CLASSIFIER.classify("x", exc_type="AgentSetupTimeoutError") is TerminateReason.ROLLOUT_ERROR
    assert CLASSIFIER.classify("x", exc_type="AgentTimeoutError") is TerminateReason.AGENT_TIMEOUT


def test_a_discarded_train_slot_always_refills_the_group():
    """A train entry needs every slot, so discarding one must request a refill.

    `AgentLoopManager` occupies the buffer entry only once all `alg_rollout_n`
    trajectories arrive, and `PSManager.abort_requests` clears the entry when fewer
    remain. Any reason that reaches the worker without usable data must therefore
    either be `ABORTED` (PSManager already cleared the entry) or satisfy
    `needs_manager_retry()`.

    This holds for every member, not just the ones Harbor produces: `worker.py` sets
    `output = None` for anything satisfying `needs_worker_retry()`, so a reason that
    discards data without refilling would leak the group.
    """
    for reason in TerminateReason:
        if reason.is_successful or reason is TerminateReason.ABORTED:
            continue
        assert reason.needs_manager_retry(), (
            f"{reason.value} yields no data but never refills the group, so its siblings would wait forever"
        )
    assert not TerminateReason.ABORTED.needs_manager_retry()


def test_data_bearing_reasons_never_refill_the_group():
    """The converse: a usable trajectory must not trigger a group teardown."""
    for reason in TerminateReason:
        if not reason.is_successful:
            continue
        assert not reason.needs_manager_retry(), f"{reason.value} discards its own data"
        assert not reason.needs_worker_retry(), f"{reason.value} would be re-run after its turns were already accepted"


def test_exception_type_beats_message_text():
    """Harbor's class name is the reliable signal when both are present."""
    assert CLASSIFIER.classify("some unrelated wording", exc_type="AgentTimeoutError") is TerminateReason.AGENT_TIMEOUT


def test_unrecognised_failure_returns_none():
    """`None` keeps 'unknown' distinguishable from 'definitely a fault'."""
    assert CLASSIFIER.classify("something nobody has seen before") is None
    assert CLASSIFIER.classify(None) is None
    assert CLASSIFIER.classify("") is None


def test_psrl_sentinel_types_classify_without_text_matching():
    """The base class handles our own sentinels for every harness."""
    base = AgentExceptionClassifier()
    assert base.classify(RequestAbortedByGatewayError(request_id="r", message="m")) is TerminateReason.ABORTED
    assert base.classify(PromptOverflowError("too long")) is TerminateReason.MAX_RESPONSE_LENGTH_EXCEEDED


def test_base_classifier_has_no_harness_knowledge():
    """Harbor markers must live in the subclass, not leak into shared code."""
    base = AgentExceptionClassifier()
    assert base.classify(ABORT_MSG) is None
    assert base.classify(AGENT_TIMEOUT_MSG) is None
    # But the shared vLLM overflow detector is genuinely harness-independent.
    assert base.classify(OVERFLOW_MSG) is TerminateReason.MAX_RESPONSE_LENGTH_EXCEEDED


def test_is_prompt_overflow_accepts_text_or_exception():
    assert is_prompt_overflow(OVERFLOW_MSG)
    assert is_prompt_overflow(ValueError(OVERFLOW_MSG))
    assert not is_prompt_overflow("connection reset by peer")
