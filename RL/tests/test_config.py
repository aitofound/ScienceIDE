"""Tests for sciaccel_rl config dataclass and factory."""


class TestSciAccelRuntimeConfig:
    """Test config construction and merging."""

    def test_default_config(self):
        from scienceide_rl.config import SciAccelRuntimeConfig

        cfg = SciAccelRuntimeConfig()
        assert cfg.harbor.agent_name == "terminus-2"
        assert cfg.task_timeout_sec == 3600.0
        assert cfg.harbor.override_gpus is None

    def test_build_runtime_config_from_yaml_kwargs(self):
        from scienceide_rl.config import build_runtime_config

        cfg = build_runtime_config(
            {
                "harbor": {"agent_name": "custom-agent", "jobs_dir": "/tmp/custom"},
                "task_timeout_sec": 7200.0,
            }
        )
        assert cfg.harbor.agent_name == "custom-agent"
        assert cfg.harbor.jobs_dir == "/tmp/custom"
        assert cfg.task_timeout_sec == 7200.0
        # Defaults preserved for unset fields
        assert cfg.harbor.override_gpus is None

    def test_build_runtime_config_strips_meta_keys(self):
        from scienceide_rl.config import build_runtime_config

        cfg = build_runtime_config({"name": "sciaccel", "_target_": "foo.bar"})
        assert cfg.harbor.agent_name == "terminus-2"
