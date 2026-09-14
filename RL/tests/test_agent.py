"""Tests for the scienceide_rl terminus-2 subclass with a tighter observation cap."""

from scienceide_rl.agent import HARBOR_DEFAULT_MAX_OBS_BYTES, TruncatingTerminus2
from harbor.agents.terminus_2 import Terminus2


def _agent(max_bytes: int) -> TruncatingTerminus2:
    """
    Build an instance without running terminus-2's constructor.

    The real constructor reaches for a live model connection and a logs
    directory, neither of which the truncation logic touches.
    """
    agent = object.__new__(TruncatingTerminus2)
    agent._max_observation_bytes = max_bytes
    return agent


class TestTruncatingTerminus2:
    """Test the observation byte cap."""

    def test_resolves_through_harbor_import_path(self):
        # Harbor treats an agent name containing ':' as an import path.
        from harbor.utils.import_path import import_class

        assert import_class("scienceide_rl.agent:TruncatingTerminus2", label="agent") is TruncatingTerminus2

    def test_long_output_is_truncated_to_the_cap(self):
        out = _agent(4096)._limit_output_length("x" * 30000)
        # The banner and its newlines sit outside the byte budget.
        assert len(out) < 4096 + 200
        assert "interior bytes omitted" in out

    def test_short_output_passes_through_unchanged(self):
        text = "y" * 100
        assert _agent(4096)._limit_output_length(text) == text

    def test_explicit_max_bytes_overrides_the_default(self):
        out = _agent(4096)._limit_output_length("x" * 30000, 1000)
        assert len(out) < 1000 + 200

    def test_cap_is_lower_than_the_harbor_default(self):
        # The subclass only earns its place by tightening the default.
        assert HARBOR_DEFAULT_MAX_OBS_BYTES == 10000

    def test_keeps_the_head_and_the_tail(self):
        out = _agent(4096)._limit_output_length("A" * 15000 + "ZZZ")
        assert out.startswith("A")
        assert out.endswith("ZZZ")


class TestOverflowIsTerminal:
    """Test that a context overflow ends the episode instead of retrying."""

    OVERFLOW = (
        "litellm.BadRequestError: OpenAIException - The prompt (length 69801) "
        "is longer than the maximum model length of 67584."
    )

    def _query(self, side_effect):
        """Call the subclass `_query_llm` with a patched parent implementation."""
        import asyncio
        from unittest.mock import AsyncMock, patch

        agent = _agent(4096)
        with patch.object(Terminus2, "_query_llm", new=AsyncMock(side_effect=side_effect)):
            return asyncio.run(TruncatingTerminus2._query_llm(agent))

    def test_overflow_raises_the_terminal_exception(self):
        import pytest
        from scienceide_rl.agent import ContextWindowExhausted

        # Retrying cannot help: the transcript only grows. One run logged 5040
        # rejections, the same request repeated 1733 times, burning the agent budget.
        with pytest.raises(ContextWindowExhausted):
            self._query(Exception(self.OVERFLOW))

    def test_the_message_survives_for_downstream_classification(self):
        from scienceide_rl.agent import ContextWindowExhausted
        from psrl.utils.agent.overflow import is_prompt_overflow

        # `ScienceIDEAgentLoop` re-classifies the message to decide whether to train the
        # partial trajectory, so wrapping must not lose the vLLM wording.
        try:
            self._query(Exception(self.OVERFLOW))
        except ContextWindowExhausted as exc:
            assert is_prompt_overflow(exc)

    def test_unrelated_errors_propagate_unchanged(self):
        import pytest

        with pytest.raises(RuntimeError, match="boom"):
            self._query(RuntimeError("boom"))

    def test_a_successful_query_passes_through(self):
        import asyncio
        from unittest.mock import AsyncMock, patch

        agent = _agent(4096)
        with patch.object(Terminus2, "_query_llm", new=AsyncMock(return_value="ok")):
            assert asyncio.run(TruncatingTerminus2._query_llm(agent)) == "ok"


class TestEpisodeConcurrencyGate:
    """Test the per-worker cap on concurrent Harbor episodes."""

    def test_gate_never_exceeds_its_limit(self):
        # Without this cap admission allowed ~256 concurrent requests and one node
        # reached 182 containers, which wedged its Docker daemon and stalled training.
        import asyncio

        import scienceide_rl.agent_loop as al

        al._episode_gate = None
        al._episode_gate_limit = 0
        state = {"live": 0, "peak": 0}
        limit = 4

        async def one():
            gate = await al._acquire_episode_slot(limit)
            try:
                state["live"] += 1
                state["peak"] = max(state["peak"], state["live"])
                await asyncio.sleep(0.01)
                state["live"] -= 1
            finally:
                gate.release()

        async def drive():
            await asyncio.gather(*[one() for _ in range(40)])

        asyncio.run(drive())
        assert state["peak"] <= limit
        assert state["live"] == 0

    def test_gate_is_rebuilt_when_the_limit_changes(self):
        import asyncio

        import scienceide_rl.agent_loop as al

        al._episode_gate = None
        al._episode_gate_limit = 0

        async def probe(limit):
            gate = await al._acquire_episode_slot(limit)
            gate.release()
            return al._episode_gate_limit

        assert asyncio.run(probe(2)) == 2
        assert asyncio.run(probe(7)) == 7
