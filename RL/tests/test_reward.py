"""Tests for the scienceide_rl reward function."""


class TestComputeScore:
    """Test compute_score extracts verifier reward correctly."""

    def test_laps_cpu_reward_key(self):
        from scienceide_rl.reward import compute_score

        result = compute_score(
            data_source="scienceide_rl",
            solution_str="",
            ground_truth=None,
            extra_info={
                "reward_key": "reward",
                "harbor_rewards": {"reward": 0.75, "equivalence_pass": 0, "speedup": 0.0},
                "task_name": "scienceide/laps-cpu",
            },
        )
        assert result["score"] == 0.75
        assert result["reward_extra_info"]["reward_key"] == "reward"
        assert result["reward_extra_info"]["task_name"] == "scienceide/laps-cpu"

    def test_laps_cuda_reward_gpu_key(self):
        from scienceide_rl.reward import compute_score

        result = compute_score(
            data_source="scienceide_rl",
            solution_str="",
            ground_truth=None,
            extra_info={
                "reward_key": "reward_gpu",
                "harbor_rewards": {"reward": 1.0, "reward_gpu": 0.0, "gpu_active": 0},
                "task_name": "scienceide/laps-cuda",
            },
        )
        assert result["score"] == 0.0

    def test_missing_harbor_rewards_returns_zero(self):
        from scienceide_rl.reward import compute_score

        result = compute_score(
            data_source="scienceide_rl",
            solution_str="",
            ground_truth=None,
            extra_info={"reward_key": "reward"},
        )
        assert result["score"] == 0.0

    def test_missing_reward_key_defaults_to_reward(self):
        from scienceide_rl.reward import compute_score

        result = compute_score(
            data_source="scienceide_rl",
            solution_str="",
            ground_truth=None,
            extra_info={
                "harbor_rewards": {"reward": 0.6},
            },
        )
        assert result["score"] == 0.6

    def test_full_pass_returns_one(self):
        from scienceide_rl.reward import compute_score

        result = compute_score(
            data_source="scienceide_rl",
            solution_str="",
            ground_truth=None,
            extra_info={
                "reward_key": "reward",
                "harbor_rewards": {
                    "reward": 1.0,
                    "equivalence_pass": 1,
                    "speedup": 1.2,
                    "check_aw_2d_256": 1.0,
                    "check_aw_2d_512": 1.0,
                    "check_aw_128": 1.0,
                },
                "task_name": "scienceide/laps-cpu",
            },
        )
        assert result["score"] == 1.0
        assert result["reward_extra_info"]["all_rewards"]["equivalence_pass"] == 1
