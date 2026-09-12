"""Tests for the SciAccelAgentLoop registration and basic contract."""


class TestSciAccelAgentLoopRegistration:
    """Test the agent loop is properly registered."""

    def test_registered_in_agent_loop_registry(self):
        import scienceide_rl.agent_loop  # noqa: F401
        from psrl.workers.agent_loop.loops.utils import AGENT_LOOP_REGISTRY

        assert "sciaccel" in AGENT_LOOP_REGISTRY
        target = AGENT_LOOP_REGISTRY["sciaccel"]["_target_"]
        assert "SciAccelAgentLoop" in target

    def test_config_loading(self):
        from scienceide_rl.config import SciAccelRuntimeConfig, build_runtime_config

        cfg = build_runtime_config(
            {
                "harbor": {"agent_name": "terminus-2"},
                "task_timeout_sec": 7200.0,
            }
        )
        assert isinstance(cfg, SciAccelRuntimeConfig)
        assert cfg.task_timeout_sec == 7200.0
