"""Tests for scienceide_rl Harbor runner."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch


class TestHarborEpisodeResult:
    """Test the result dataclass."""

    def test_construction(self):
        from scienceide_rl.runner import HarborEpisodeResult

        result = HarborEpisodeResult(
            task_name="scienceide/laps-cpu",
            reward=0.75,
            rewards={"reward": 0.75, "equivalence_pass": 0},
        )
        assert result.task_name == "scienceide/laps-cpu"
        assert result.reward == 0.75
        assert result.exception is None

    def test_failed_episode(self):
        from scienceide_rl.runner import HarborEpisodeResult

        result = HarborEpisodeResult(
            task_name="scienceide/laps-cpu",
            reward=0.0,
            rewards={},
            exception="container_timeout",
        )
        assert result.reward == 0.0
        assert result.exception == "container_timeout"


class TestRunHarborEpisode:
    """Test run_harbor_episode with mocked Harbor API."""

    def test_successful_episode(self):
        from scienceide_rl.config import ScienceIDERuntimeConfig
        from scienceide_rl.runner import HarborEpisodeResult, run_harbor_episode

        mock_trial_result = MagicMock()
        mock_trial_result.task_name = "scienceide/laps-cpu"
        mock_trial_result.trial_name = "trial-001"
        mock_trial_result.verifier_result = MagicMock()
        mock_trial_result.verifier_result.rewards = {"reward": 0.85, "equivalence_pass": 0}
        mock_trial_result.exception_info = None

        mock_job_result = MagicMock()
        mock_job_result.trial_results = [mock_trial_result]

        mock_job = AsyncMock()
        mock_job.run = AsyncMock(return_value=mock_job_result)

        config = ScienceIDERuntimeConfig()

        with (
            patch("scienceide_rl.runner.Job") as mock_job_cls,
            patch("scienceide_rl.runner.force_remove_compose_project", return_value=[]),
            patch("scienceide_rl.runner.force_remove_compose_images", return_value=0),
            patch("scienceide_rl.runner.prune_dangling_images", return_value=False),
        ):
            mock_job_cls.create = AsyncMock(return_value=mock_job)
            result = asyncio.run(
                run_harbor_episode(
                    task_path="/path/to/tasks/laps-cpu",
                    model_base_url="http://10.0.0.1:8000/sessions/abc/v1",
                    model_name="Qwen/Qwen3-8B",
                    config=config,
                )
            )
            job_config = mock_job_cls.create.await_args.args[0]

        assert isinstance(result, HarborEpisodeResult)
        assert result.reward == 0.85
        assert result.rewards["reward"] == 0.85
        assert result.exception is None
        assert job_config.agents[0].kwargs["record_terminal_session"] is False

    def _run_with_hint(self, hint):
        """
        Run one mocked episode and return the JobConfig Harbor was handed.
        """
        from scienceide_rl.config import ScienceIDERuntimeConfig
        from scienceide_rl.runner import run_harbor_episode

        mock_trial_result = MagicMock()
        mock_trial_result.task_name = "scienceide/laps-repair-bounds-2d-mhdrhs-l264"
        mock_trial_result.verifier_result = MagicMock()
        mock_trial_result.verifier_result.rewards = {"reward_repair": 1.0}
        mock_trial_result.exception_info = None

        mock_job_result = MagicMock()
        mock_job_result.trial_results = [mock_trial_result]

        mock_job = AsyncMock()
        mock_job.run = AsyncMock(return_value=mock_job_result)

        with (
            patch("scienceide_rl.runner.Job") as mock_job_cls,
            patch("scienceide_rl.runner.force_remove_compose_project", return_value=[]),
            patch("scienceide_rl.runner.force_remove_compose_images", return_value=0),
            patch("scienceide_rl.runner.prune_dangling_images", return_value=False),
        ):
            mock_job_cls.create = AsyncMock(return_value=mock_job)
            asyncio.run(
                run_harbor_episode(
                    task_path="/path/to/tasks/laps-repair-bounds-2d-mhdrhs-l264",
                    model_base_url="http://10.0.0.1:8000/sessions/abc/v1",
                    model_name="Qwen/Qwen3.5-4B",
                    config=ScienceIDERuntimeConfig(),
                    hint=hint,
                )
            )
            return mock_job_cls.create.await_args.args[0]

    def test_hint_reaches_harbor_as_extra_instructions(self):
        # Harbor re-reads `instruction.md` from disk, so this is the only delivery path.
        hint = "## Where to look\n\nsrc_compressible/2D/mhdrhs.f90"
        job_config = self._run_with_hint(hint)
        assert job_config.extra_instructions == [hint]

    def test_empty_hint_leaves_the_job_config_untouched(self):
        # The unhinted level must stay a true control.
        job_config = self._run_with_hint("")
        assert job_config.extra_instructions == []


class TestEpisodeContainerCleanup:
    """Test that every exit path reclaims the episode's Docker containers."""

    SESSION = "sess-ABC-123"

    def _run(self, job_run):
        """Run one episode with a patched Job, returning the cleanup mock and job config."""
        from scienceide_rl.config import ScienceIDERuntimeConfig
        from scienceide_rl.runner import run_harbor_episode

        job = AsyncMock()
        job.run = job_run
        with (
            patch("scienceide_rl.runner.Job") as mock_job_cls,
            patch("scienceide_rl.runner.force_remove_compose_project", return_value=["cid1"]) as mock_rm,
            patch("scienceide_rl.runner.force_remove_compose_images", return_value=0),
            patch("scienceide_rl.runner.prune_dangling_images", return_value=False),
        ):
            mock_job_cls.create = AsyncMock(return_value=job)
            asyncio.run(
                run_harbor_episode(
                    task_path="/t",
                    model_base_url="u",
                    model_name="m",
                    config=ScienceIDERuntimeConfig(),
                    session_id=self.SESSION,
                    regrade_unverified=False,
                )
            )
            return mock_rm, mock_job_cls.create.await_args.args[0]

    def test_cleanup_runs_on_the_success_path(self):
        mock_rm, _ = self._run(AsyncMock(return_value=self._ok_result()))
        mock_rm.assert_called_once_with(self.SESSION)

    def test_cleanup_runs_when_the_job_times_out(self):
        # Cancelling the coroutine does not stop the containers, which is what wedged
        # the rollout pipeline: the verifier kept running `sleep infinity` for hours.
        mock_rm, _ = self._run(AsyncMock(side_effect=asyncio.TimeoutError()))
        mock_rm.assert_called_once_with(self.SESSION)

    def test_cleanup_runs_when_the_job_raises(self):
        mock_rm, _ = self._run(AsyncMock(side_effect=RuntimeError("boom")))
        mock_rm.assert_called_once_with(self.SESSION)

    @staticmethod
    def _ok_result():
        tr = MagicMock()
        tr.task_name = "t"
        tr.verifier_result = MagicMock()
        tr.verifier_result.rewards = {"reward": 1.0}
        tr.exception_info = None
        result = MagicMock()
        result.trial_results = [tr]
        return result


class TestDanglingImagePrune:
    """Test the throttled dangling-image prune that runs after each episode."""

    def setup_method(self):
        import psrl.utils.common.docker_utils as du

        du._LAST_PRUNE_MONOTONIC = 0.0

    def test_prune_is_throttled_after_the_first_call(self):
        # Listing the image store is the expensive operation being defended against,
        # so this must not run once per episode.
        import psrl.utils.common.docker_utils as du

        with patch("psrl.utils.common.docker_utils.subprocess.run") as run:
            run.return_value = MagicMock(stdout=b"")
            assert du.prune_dangling_images() is True
            assert du.prune_dangling_images() is False
            assert du.prune_dangling_images() is False
            assert run.call_count == 1

    def test_prune_only_lists_dangling_images(self):
        # Tagged task images must survive so the next episode skips a cold rebuild.
        import psrl.utils.common.docker_utils as du

        with patch("psrl.utils.common.docker_utils.subprocess.run") as run:
            run.return_value = MagicMock(stdout=b"")
            du.prune_dangling_images()
            assert run.call_args.args[0] == ["docker", "images", "-f", "dangling=true", "-q"]

    def test_prune_removes_by_id_in_batches(self):
        # `docker image prune -f` was measured removing 0 of 5816 images over 25 minutes
        # on a degraded daemon, while batched `rmi -f` cleared them in under 3 minutes.
        import psrl.utils.common.docker_utils as du

        remaining = {f"id{i}" for i in range(450)}
        deleted: set[str] = set()

        def fake_run(cmd, **kwargs):
            if cmd[:2] == ["docker", "images"]:
                return MagicMock(stdout=("\n".join(sorted(remaining))).encode())
            if cmd[:3] == ["docker", "rmi", "-f"]:
                for image_id in cmd[3:]:
                    remaining.discard(image_id)
                    deleted.add(image_id)
            return MagicMock(stdout=b"")

        with patch("psrl.utils.common.docker_utils.subprocess.run", side_effect=fake_run):
            assert du.prune_dangling_images() is True
        # All 450 removed, in batches rather than one oversized argument list.
        assert len(deleted) == 450
        assert not remaining

    def test_an_undeletable_image_does_not_spin_the_loop(self):
        # An image held by a live container can only be untagged, so it keeps reappearing
        # in the listing. Without tracking attempts this would loop until the deadline.
        import psrl.utils.common.docker_utils as du

        def fake_run(cmd, **kwargs):
            if cmd[:2] == ["docker", "images"]:
                return MagicMock(stdout=b"stuck_id\n")
            return MagicMock(stdout=b"")

        with patch("psrl.utils.common.docker_utils.subprocess.run", side_effect=fake_run) as run:
            assert du.prune_dangling_images() is True
        assert run.call_count <= 4

    def test_a_prune_failure_never_propagates(self):
        # A cleanup problem must not take down a rollout.
        import psrl.utils.common.docker_utils as du

        with patch("psrl.utils.common.docker_utils.subprocess.run", side_effect=OSError("boom")):
            assert du.prune_dangling_images() is False

    def test_per_episode_images_are_selected_by_compose_project(self):
        # These images are TAGGED, so a dangling sweep never reaches them. They must be
        # matched by the project prefix Compose derives image names from.
        from psrl.utils.common.docker_utils import force_remove_compose_images

        with patch("psrl.utils.common.docker_utils.subprocess.run") as run:
            run.return_value = MagicMock(stdout=b"sess-abc-main:latest\n")
            assert force_remove_compose_images("sess-ABC") == 1
            listing = run.call_args_list[0].args[0]
            assert "reference=sess-abc-*" in listing
            assert run.call_args_list[1].args[0][:3] == ["docker", "rmi", "-f"]

    def test_empty_session_id_removes_no_images(self):
        from psrl.utils.common.docker_utils import force_remove_compose_images

        assert force_remove_compose_images("") == 0

    def test_episode_cleanup_invokes_the_prune(self):
        from scienceide_rl.config import ScienceIDERuntimeConfig
        from scienceide_rl.runner import run_harbor_episode

        tr = MagicMock()
        tr.task_name = "t"
        tr.verifier_result = MagicMock()
        tr.verifier_result.rewards = {"reward": 1.0}
        tr.exception_info = None
        result = MagicMock()
        result.trial_results = [tr]
        job = AsyncMock()
        job.run = AsyncMock(return_value=result)

        with (
            patch("scienceide_rl.runner.Job") as mock_job_cls,
            patch("scienceide_rl.runner.force_remove_compose_project", return_value=[]),
            patch("scienceide_rl.runner.prune_dangling_images") as mock_prune,
        ):
            mock_job_cls.create = AsyncMock(return_value=job)
            asyncio.run(
                run_harbor_episode(
                    task_path="/t",
                    model_base_url="u",
                    model_name="m",
                    config=ScienceIDERuntimeConfig(),
                    session_id="s",
                    regrade_unverified=False,
                )
            )
        mock_prune.assert_called_once()


class TestContextBudget:
    """Test the window advertised to terminus-2 against the served window."""

    def _kwargs(self, max_model_len):
        from scienceide_rl.config import ScienceIDERuntimeConfig
        from scienceide_rl.runner import run_harbor_episode

        tr = MagicMock()
        tr.task_name = "t"
        tr.verifier_result = MagicMock()
        tr.verifier_result.rewards = {"reward": 1.0}
        tr.exception_info = None
        result = MagicMock()
        result.trial_results = [tr]
        job = AsyncMock()
        job.run = AsyncMock(return_value=result)

        # Every cleanup call must be patched: unpatched ones shell out to a real
        # `docker`, which makes the unit test depend on daemon responsiveness.
        with (
            patch("scienceide_rl.runner.Job") as mock_job_cls,
            patch("scienceide_rl.runner.force_remove_compose_project", return_value=[]),
            patch("scienceide_rl.runner.force_remove_compose_images", return_value=0),
            patch("scienceide_rl.runner.prune_dangling_images", return_value=False),
        ):
            mock_job_cls.create = AsyncMock(return_value=job)
            asyncio.run(
                run_harbor_episode(
                    task_path="/t",
                    model_base_url="u",
                    model_name="m",
                    config=ScienceIDERuntimeConfig(),
                    max_model_len=max_model_len,
                    regrade_unverified=False,
                )
            )
            return mock_job_cls.create.await_args.args[0].agents[0].kwargs

    def test_advertised_window_is_below_the_served_window(self):
        # Equal windows let terminus-2 build a prompt vLLM rejects with a 400, because it
        # counts tokens with litellm's estimator rather than the served tokenizer.
        from scienceide_rl.runner import _CONTEXT_SAFETY_MARGIN

        served = 67584
        advertised = self._kwargs(served)["model_info"]["max_input_tokens"]
        assert advertised == served - _CONTEXT_SAFETY_MARGIN
        assert advertised < served

    def test_advertised_window_never_goes_nonpositive(self):
        # A tiny window must not produce a negative or zero budget.
        assert self._kwargs(512)["model_info"]["max_input_tokens"] >= 1024


class TestComposeProjectName:
    """Test the Compose project name used as the cleanup key."""

    def test_matches_harbors_own_sanitizer(self):
        # A drifting copy would make cleanup silently target nothing.
        from harbor.environments.docker.docker import _sanitize_docker_compose_project_name as harbor_fn
        from psrl.utils.common.docker_utils import sanitize_compose_project_name

        for name in ("01a056bc-0280-7662-b62f-92edb30e7285", "ABC_def-123", "_leading", "9x", "A.B:C/D", "-dash"):
            assert sanitize_compose_project_name(name) == harbor_fn(name)

    def test_empty_session_id_is_a_no_op(self):
        from psrl.utils.common.docker_utils import force_remove_compose_project

        assert force_remove_compose_project("") == []

    def test_episode_with_exception(self):
        from scienceide_rl.config import ScienceIDERuntimeConfig
        from scienceide_rl.runner import run_harbor_episode

        mock_trial_result = MagicMock()
        mock_trial_result.task_name = "scienceide/laps-cpu"
        mock_trial_result.trial_name = "trial-001"
        mock_trial_result.verifier_result = None
        mock_trial_result.exception_info = MagicMock()
        mock_trial_result.exception_info.exception_message = "build_failed"

        mock_job_result = MagicMock()
        mock_job_result.trial_results = [mock_trial_result]

        mock_job = AsyncMock()
        mock_job.run = AsyncMock(return_value=mock_job_result)

        config = ScienceIDERuntimeConfig()

        with (
            patch("scienceide_rl.runner.Job") as mock_job_cls,
            patch("scienceide_rl.runner.force_remove_compose_project", return_value=[]),
            patch("scienceide_rl.runner.force_remove_compose_images", return_value=0),
            patch("scienceide_rl.runner.prune_dangling_images", return_value=False),
        ):
            mock_job_cls.create = AsyncMock(return_value=mock_job)
            result = asyncio.run(
                run_harbor_episode(
                    task_path="/path/to/tasks/laps-cpu",
                    model_base_url="http://10.0.0.1:8000/sessions/abc/v1",
                    model_name="Qwen/Qwen3-8B",
                    config=config,
                )
            )

        assert result.reward == 0.0
        assert result.exception == "build_failed"
