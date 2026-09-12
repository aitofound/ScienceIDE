"""Tests for the SciAccel-RL dataset preparation script."""

import os
import tempfile
from pathlib import Path

import pytest

# The task bank lives outside this repo, so these tests are opt-in. Set
# SCIACCEL_RL_REPO to a checkout with compiled envs, or they skip.
SCIACCEL_RL_REPO = os.environ.get("SCIACCEL_RL_REPO", "")

# Every env compiles and builds identically, so one env exercises the whole path.
ENV = os.environ.get("SCIACCEL_RL_ENV", "laps")

_HAS_COMPILED_ENV = bool(SCIACCEL_RL_REPO) and (Path(SCIACCEL_RL_REPO) / "build" / ENV / "index.jsonl").exists()
_SKIP_REASON = f"set SCIACCEL_RL_REPO to a checkout with a compiled build/{ENV}"


@pytest.fixture(scope="module")
def canonical_rows():
    """
    Index each task's canonical row by task directory name.

    Read from the per-task `authoring/provenance.json` rather than an aggregated
    `tasks.jsonl`, because the per-task file is the format every env has.
    """
    import json

    root = Path(SCIACCEL_RL_REPO) / "build" / ENV
    return {
        path.parent.parent.name: json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(root.glob("**/authoring/provenance.json"))
    }


@pytest.fixture(scope="module")
def hint_datasets():
    """
    Build every hint level once into a shared temporary directory.
    """
    import pandas as pd
    from scienceide_rl.prepare.build_dataset import HINT_LEVELS, build_datasets

    with tempfile.TemporaryDirectory() as tmpdir:
        frames = {}
        for level in HINT_LEVELS:
            build_datasets(
                repo_path=SCIACCEL_RL_REPO,
                out_dir=tmpdir,
                env=ENV,
                categories=["repair", "implementation"],
                hint_level=level,
                difficulty="easy",
            )
            frames[level] = pd.read_parquet(Path(tmpdir) / "all" / f"{level}.parquet")
            frames[f"{level}_train"] = pd.read_parquet(Path(tmpdir) / "train" / f"{level}.parquet")
        frames["val"] = pd.read_parquet(Path(tmpdir) / "eval" / "unhinted.parquet")
        yield frames


@pytest.fixture(scope="module")
def hint_train_frames(hint_datasets):
    """
    Expose the train splits under their bare level names.
    """
    return {level: hint_datasets[f"{level}_train"] for level in ("L1", "L2", "L3")}


@pytest.mark.skipif(not _HAS_COMPILED_ENV, reason=_SKIP_REASON)
class TestTasksRoot:
    """Test that only a compiled task tree is accepted."""

    def test_uncompiled_env_is_rejected(self):
        # Pointing a dataset at authored sources yields tasks with no `environment/`,
        # and every episode then dies inside Harbor with `unable to prepare context`.
        from scienceide_rl.prepare.build_dataset import _resolve_tasks_root

        with pytest.raises(FileNotFoundError, match="No compiled task tree"):
            _resolve_tasks_root(Path(SCIACCEL_RL_REPO), "no-such-env")

    def test_compiled_tree_is_used(self):
        from scienceide_rl.prepare.build_dataset import _resolve_tasks_root

        root = _resolve_tasks_root(Path(SCIACCEL_RL_REPO), ENV)
        assert root == Path(SCIACCEL_RL_REPO) / "build" / ENV


@pytest.mark.skipif(not _HAS_COMPILED_ENV, reason=_SKIP_REASON)
class TestDatasetSchema:
    """Test the columns the trainer and reward loop rely on."""

    def test_prompt_is_chat_format(self, hint_datasets):
        prompt = list(hint_datasets["L3"].iloc[0]["prompt"])
        assert isinstance(prompt, list)
        assert prompt[0]["role"] == "user"
        assert prompt[0]["content"]

    def test_required_columns_are_present(self, hint_datasets):
        df = hint_datasets["L3"]
        for column in ("prompt", "extra_info", "data_source", "reward_model"):
            assert column in df.columns

    def test_every_row_carries_a_runnable_task_path(self, hint_datasets):
        # `task_path` is what Harbor builds from, so a path with no `environment/`
        # is a dataset that cannot run.
        for row in hint_datasets["L3"]["extra_info"]:
            assert (Path(row["task_path"]) / "environment").is_dir()

    def test_repair_rows_use_the_floor_normalized_reward(self, hint_datasets):
        # Raw `reward` is inflated to the floor by delivering the unfixed build.
        df = hint_datasets["L3"]
        repair = df[df["category"] == "repair"]
        assert len(repair) > 0
        assert {row["reward_key"] for row in repair["extra_info"]} == {"reward_repair"}


@pytest.mark.skipif(not _HAS_COMPILED_ENV, reason=_SKIP_REASON)
class TestHintLevels:
    """Test the localization hint appended to repair task instructions."""

    def test_l3_carries_no_hint(self, hint_datasets):
        df = hint_datasets["L3"]
        assert len(df) > 0
        assert all(not row["hint"] for row in df["extra_info"])

    def test_only_repair_tasks_are_hinted(self, hint_datasets):
        # An excised routine already names its file and subroutine, so a location
        # hint tells it nothing.
        for level in ("L1", "L2"):
            df = hint_datasets[level]
            hinted = {r["task_name"] for _, r in df.iterrows() if r["extra_info"]["hint"]}
            assert len(hinted) > 0
            assert set(df[df["task_name"].isin(hinted)]["category"]) == {"repair"}

    def test_hint_names_the_golden_patch_file(self, hint_datasets, canonical_rows):
        # A hint pointing anywhere but the edited file would teach the wrong search.
        for level in ("L1", "L2"):
            for _, row in hint_datasets[level].iterrows():
                hint = row["extra_info"]["hint"]
                if not hint:
                    continue
                canonical = canonical_rows[Path(row["extra_info"]["task_path"]).name]
                assert canonical["candidate"]["fix"]["edits"][0]["file"] in hint

    def test_l1_carries_the_line_and_l2_does_not(self, hint_datasets, canonical_rows):
        for _, row in hint_datasets["L1"].iterrows():
            hint = row["extra_info"]["hint"]
            if not hint:
                continue
            canonical = canonical_rows[Path(row["extra_info"]["task_path"]).name]
            line = (canonical["candidate"].get("meta") or {}).get("line")
            if line is not None:
                assert f"line {line}" in hint
        assert all("line " not in row["hint"] for row in hint_datasets["L2"]["extra_info"])

    def test_prompt_column_mirrors_the_hint(self, hint_datasets):
        # The column is documentation, because Harbor delivers the hint itself.
        for _, row in hint_datasets["L1"].iterrows():
            hint = row["extra_info"]["hint"]
            if hint:
                assert row["prompt"][0]["content"].endswith(hint)

    def test_validation_is_unhinted_at_every_level(self, hint_datasets):
        assert all(not row["hint"] for row in hint_datasets["val"]["extra_info"])

    def test_hinted_validation_exists_for_hinted_levels(self, hint_datasets):
        # Each hinted level also ships an in-distribution eval split, because
        # `eval/unhinted.parquet` measures a task a hint-trained model never saw.
        for level in ("L1", "L2"):
            assert any(row["hint"] for row in hint_datasets[level]["extra_info"])

    def test_hint_level_is_recorded_on_every_row(self, hint_datasets):
        for level in ("L1", "L2", "L3"):
            assert all(row["hint_level"] == level for row in hint_datasets[level]["extra_info"])

    def test_unknown_level_is_rejected(self):
        from scienceide_rl.prepare.build_dataset import build_datasets

        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValueError, match="Unknown hint_level"):
                build_datasets(
                    repo_path=SCIACCEL_RL_REPO,
                    out_dir=tmpdir,
                    env=ENV,
                    hint_level="L9",
                )

    def test_train_split_interleaves_categories(self, hint_train_frames):
        # The bank is grouped by category on disk. A sequential sampler over that
        # order spent the first two steps entirely on unhinted restore tasks.
        df = hint_train_frames["L1"]
        assert len(set(df["category"])) > 1
        assert len(set(df["category"].iloc[: min(16, len(df))])) > 1

    def test_repair_only_build_is_fully_hinted(self):
        # The default training set. Excised routine tasks are excluded because a
        # location hint cannot help restore a whole subroutine body.
        import pandas as pd
        from scienceide_rl.prepare.build_dataset import build_datasets

        with tempfile.TemporaryDirectory() as tmpdir:
            build_datasets(
                repo_path=SCIACCEL_RL_REPO,
                out_dir=tmpdir,
                env=ENV,
                categories=["repair"],
                hint_level="L1",
                difficulty="easy",
            )
            train = pd.read_parquet(Path(tmpdir) / "train" / "L1.parquet")
            val = pd.read_parquet(Path(tmpdir) / "eval" / "unhinted.parquet")

        assert set(train["category"]) == {"repair"}
        assert all(row["hint"] for row in train["extra_info"])
        # Validation stays unhinted so it measures the task as it really ships.
        assert all(not row["hint"] for row in val["extra_info"])


@pytest.mark.skipif(not _HAS_COMPILED_ENV, reason=_SKIP_REASON)
class TestOutputLayout:
    """Test the on-disk artefact layout the launch scripts address by path."""

    def test_roles_are_separate_directories(self):
        from scienceide_rl.prepare.build_dataset import HINT_LEVELS, build_datasets

        with tempfile.TemporaryDirectory() as tmpdir:
            for level in HINT_LEVELS:
                build_datasets(
                    repo_path=SCIACCEL_RL_REPO,
                    out_dir=tmpdir,
                    env=ENV,
                    categories=["repair"],
                    hint_level=level,
                    difficulty="easy",
                )
            root = Path(tmpdir)
            expected = {
                "split.json",
                "eval/unhinted.parquet",
                *(f"{role}/{lvl}.parquet" for role in ("train", "all") for lvl in HINT_LEVELS),
                *(f"stats/{lvl}.json" for lvl in HINT_LEVELS),
                # L3 is the unhinted control, so its hinted eval split would only
                # duplicate `eval/unhinted.parquet`.
                *(f"eval/{lvl}.parquet" for lvl in ("L1", "L2")),
            }
            found = {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()}
            assert found == expected


@pytest.mark.skipif(not _HAS_COMPILED_ENV, reason=_SKIP_REASON)
class TestSplits:
    """Test the train and validation partition."""

    def test_train_and_val_are_disjoint(self, hint_datasets, hint_train_frames):
        train = set(hint_train_frames["L1"]["task_name"])
        val = set(hint_datasets["val"]["task_name"])
        assert train & val == set()

    def test_split_is_identical_across_hint_levels(self, hint_train_frames):
        # The split is chosen on the unhinted frame, so every level trains and
        # validates on exactly the same task partition.
        splits = [set(hint_train_frames[level]["task_name"]) for level in ("L1", "L2", "L3")]
        assert splits[0] == splits[1] == splits[2]

    def test_validation_is_capped(self, hint_datasets):
        # One per group is only proportionate when groups are large: an uncapped rule
        # held out 51 of 123 tasks on mitgcm-atmos.
        total = len(hint_datasets["L3"])
        assert len(hint_datasets["val"]) <= max(1, int(total * 0.25))
