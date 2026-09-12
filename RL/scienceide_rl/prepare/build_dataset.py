"""
Build stratified SciAccel-RL datasets from taxonomy metadata.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd
import tomllib

psrl_logger = logging.getLogger(__file__)
psrl_logger.setLevel(os.getenv("PSRL_LOGGING_LEVEL", "INFO"))
if not psrl_logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    psrl_logger.addHandler(_handler)
    psrl_logger.propagate = False

# Map each category to its verifier training reward.
_CATEGORY_REWARD_KEYS = {
    "repair": "reward_repair",
    "implementation": "reward_repair",
    "acceleration": "reward",
}

# The CUDA acceleration task uses its telemetry-gated reward.
_TASK_REWARD_KEY_OVERRIDES = {
    "laps-accel-cuda": "reward_gpu",
}

# The two acceleration tasks predate the taxonomy and carry no
# `[metadata.taxonomy]` section, so their group labels are assigned here.
_ACCELERATION_FAMILY = "accel"
_ACCELERATION_TREE = "both"

DATA_SOURCE = "sciaccel_rl"

# Localization hint strength, from strongest to none.
# `L3` reproduces the unhinted instruction, so it is the control.
HINT_LEVELS = ("L1", "L2", "L3")

# Injected and semantic defects both localize to a real file, so both are hinted.
# Excised routines are not: their instruction already names the file and subroutine.
_HINTED_SOURCES = frozenset({"inject", "semantic", "semantic-gr-sol"})

# Tokens the hint may add. The builder refuses a hint wider than this so a prompt
# cannot silently cross `data.max_prompt_length` under `data.truncation=error`.
_HINT_CHAR_BUDGET = 400


def _resolve_tasks_root(repo: Path, env: str) -> Path:
    """
    Return the compiled task tree Harbor can actually run.

    An env ships authored task sources under `envs/<env>/tasks`, which carry the
    instruction and provenance but no `environment/` directory. Harbor builds its
    image from that directory, so pointing a dataset at an authored source fails at
    trial start with `unable to prepare context: path .../environment not found`.
    `utils/harbor/to_harbor.py` compiles the sources into `build/<env>`, adding
    `environment/`, `tests/`, and `solution/` while keeping `authoring/provenance.json`.

    Every env compiles the same way, so the compiled tree is the only runnable one and
    a missing `build/<env>/index.jsonl` is an error rather than a fallback.

    Args:
        repo (Path): sciaccel-rl repository root.
        env (str): Environment directory name under `envs/`.

    Returns:
        Path: Directory holding the category subdirectories.
    """
    compiled = repo / "build" / env
    if not (compiled / "index.jsonl").exists():
        raise FileNotFoundError(
            f"No compiled task tree at {compiled}. Compile the env first:\n"
            f"    python utils/harbor/to_harbor.py --env envs/{env} --apt-mirror <url>"
        )
    psrl_logger.info(f"Using compiled task tree: {compiled!s}")
    return compiled


def _load_canonical_rows(repo: Path, env: str) -> dict[str, dict[str, Any]]:
    """
    Load every task's `authoring/provenance.json`, indexed by task directory name.

    This is the per-task canonical row. Some envs also ship an aggregated `tasks.jsonl`,
    but the per-task file is the format every env has, so reading it keeps one code path.

    Hand-authored tasks have no provenance file and are simply absent, which `_build_row`
    already tolerates.

    Args:
        repo (Path): sciaccel-rl repository root.
        env (str): Environment directory name under `envs/`.

    Returns:
        dict[str, dict[str, Any]]: Task directory name to canonical row.
    """
    tasks_root = _resolve_tasks_root(repo, env)

    rows: dict[str, dict[str, Any]] = {}
    for path in sorted(tasks_root.glob("**/authoring/provenance.json")):
        task_name = path.parent.parent.name
        rows[task_name] = json.loads(path.read_text(encoding="utf-8"))
    if not rows:
        raise FileNotFoundError(f"No authoring/provenance.json found under {tasks_root}")
    psrl_logger.info(f"Loaded canonical rows from {tasks_root!s}. Count: {len(rows)}.")
    return rows


def _discover_task_dirs(
    repo: Path,
    env: str,
    categories: list[str] | None,
    difficulty: str | None = None,
) -> list[tuple[str, Path]]:
    """
    Find every compiled task directory, as (category, path) pairs.

    A compiled task directory is one containing a `task.toml`. Planned-but-empty
    category directories hold only a `.gitkeep` and are skipped.

    Every env nests a difficulty tier between the category and the task
    (`repair/easy/<task>`), so recursing for `task.toml` finds them without the
    caller having to know an env's depth.

    Args:
        repo (Path): sciaccel-rl repository root.
        env (str): Environment directory name under `envs/`.
        categories (list[str] | None): Categories to include. None means every
            category that has at least one compiled task.
        difficulty (str | None): Keep only tasks whose `metadata.taxonomy.difficulty`
            matches. None keeps every tier.

    Returns:
        list[tuple[str, Path]]: Sorted (category, task_dir) pairs.
    """
    tasks_root = _resolve_tasks_root(repo, env)

    found: list[tuple[str, Path]] = []
    skipped_by_difficulty = 0
    for category_dir in sorted(p for p in tasks_root.iterdir() if p.is_dir()):
        category = category_dir.name
        if categories is not None and category not in categories:
            continue
        task_dirs = sorted(p.parent for p in category_dir.glob("**/task.toml"))
        if difficulty is not None:
            kept = []
            for task_dir in task_dirs:
                manifest = tomllib.loads((task_dir / "task.toml").read_text(encoding="utf-8"))
                tier = manifest.get("metadata", {}).get("taxonomy", {}).get("difficulty")
                if tier == difficulty:
                    kept.append(task_dir)
                else:
                    skipped_by_difficulty += 1
            task_dirs = kept
        if not task_dirs:
            psrl_logger.info(f"No compiled tasks in category={category!r}. Skipping.")
            continue
        found.extend((category, task_dir) for task_dir in task_dirs)

    if difficulty is not None:
        psrl_logger.info(f"Difficulty filter {difficulty!r} kept {len(found)}, skipped {skipped_by_difficulty}.")
        if not found:
            raise ValueError(
                f"No tasks in env {env!r} declare difficulty={difficulty!r}. "
                f"Envs whose tasks carry no difficulty field must run without the filter."
            )

    if categories is not None:
        missing = set(categories) - {category for category, _ in found}
        if missing:
            raise ValueError(f"Requested categories have no compiled tasks: {sorted(missing)}.")
    return found


def _build_hint(
    canonical: dict[str, Any],
    level: str,
    task_name: str = "",
    resolved_lines: dict[str, int] | None = None,
) -> str:
    """
    Write the localization hint for one task, or an empty string for no hint.

    Every packaged defect is confined to one or two files, so naming them removes the
    repository search without giving away the repair itself. The material comes from
    the canonical row: `candidate.meta.file` (with `candidate.meta.files` when the
    edit spans more than one), a one line `candidate.note` describing the defect
    class, and a line number.

    The line number has two sources. Envs that record `candidate.meta.line` are used
    directly. For the rest, `resolved_lines` supplies a value located by matching the
    provenance `old` text against the pinned upstream source, which
    `resolve_defect_lines.py` produces and cross-validates. Where neither is
    available, `L1` degrades to `L2` rather than inventing a line.

    Both injected and semantic defects are hinted. A semantic defect substitutes one
    calibrated constant for another, so its file is as real a localization target as
    an injected one, and withholding the hint would silently make part of the bank a
    different task. Excised routines are still excluded: their instruction already
    names the file and subroutine, so a location hint tells them nothing.

    Args:
        canonical (dict[str, Any]): One row from `_load_canonical_rows`.
        level (str): One of `HINT_LEVELS`.
        task_name (str): Task directory name, used to look up `resolved_lines`.
        resolved_lines (dict[str, int] | None): Task name to line number, from the
            env's `factory/DEFECT_LINES.json`.

    Returns:
        str: A markdown section to append to the instruction, or an empty string.
    """
    if level == "L3":
        return ""

    candidate = canonical.get("candidate") or {}
    if candidate.get("source") not in _HINTED_SOURCES:
        return ""

    meta = candidate.get("meta") or {}
    note = (candidate.get("note") or "").strip()
    # `files` is authoritative when present, because a multi-file defect that names
    # only `file` would send the model looking in one of two places.
    defect_files = [str(f) for f in (meta.get("files") or []) if f]
    if not defect_files:
        single = meta.get("file")
        defect_files = [str(single)] if single else []
    if not defect_files or not note:
        return ""

    line = meta.get("line")
    if line is None and resolved_lines is not None:
        line = resolved_lines.get(task_name)
    # A line locates a point, so it is only meaningful for a single-file defect.
    if level == "L1" and line is not None and len(defect_files) == 1:
        location = f"{defect_files[0]}, line {line}"
        confined = "The defect is a single edit confined to:"
    elif len(defect_files) == 1:
        location = defect_files[0]
        confined = "The defect is a single edit confined to:"
    else:
        location = "\n    ".join(defect_files)
        confined = "The same change was made in each of these files:"
        # Naming the shared directory stays inside the budget and localizes just as
        # well, because every file under it received the same edit.
        if len(location) > _HINT_CHAR_BUDGET // 2:
            common = os.path.commonpath(defect_files)
            if common and common not in (".", "/"):
                location = f"{common}/ (all {len(defect_files)} files below it)"
                confined = "The same change was made in every solver file under:"

    # The closing clause must not claim single-file scope for a multi-file defect, or
    # the hint actively misleads the model into stopping after the first fix.
    closing = "No other file has been modified." if len(defect_files) == 1 else "Nothing outside them has changed."
    hint = f"## Where to look\n\n{confined}\n\n    {location}\n\nThe change made there: {note}. {closing}"

    if len(hint) > _HINT_CHAR_BUDGET:
        raise ValueError(
            f"Hint for task {canonical.get('task')!r} is {len(hint)} chars, over the "
            f"{_HINT_CHAR_BUDGET} budget. Widen _HINT_CHAR_BUDGET only after checking "
            f"data.max_prompt_length, because data.truncation is error."
        )
    return hint


def _build_row(
    category: str,
    task_dir: Path,
    canonical_rows: dict[str, dict[str, Any]],
    hint_level: str,
    resolved_lines: dict[str, int] | None = None,
) -> dict[str, Any]:
    """
    Build one dataset row from a compiled task directory.

    Args:
        category (str): Taxonomy category, from the parent directory name.
        task_dir (Path): Compiled task directory containing `task.toml`.
        canonical_rows (dict[str, dict[str, Any]]): Output of
            `_load_canonical_rows`, keyed by unprefixed task name.
        hint_level (str): One of `HINT_LEVELS`, selecting the hint strength.
        resolved_lines (dict[str, int] | None): Task name to line number, from
            `_load_resolved_lines`.

    Returns:
        dict[str, Any]: One row for the output Parquet.
    """
    manifest = tomllib.loads((task_dir / "task.toml").read_text(encoding="utf-8"))
    instruction = (task_dir / "instruction.md").read_text(encoding="utf-8").strip()

    taxonomy = manifest.get("metadata", {}).get("taxonomy", {})
    environment = manifest.get("environment", {})
    task_name = manifest["task"]["name"]
    canonical = canonical_rows.get(task_dir.name, {})
    hint = _build_hint(canonical, hint_level, task_name=task_dir.name, resolved_lines=resolved_lines)

    # Manifest and directory categories must agree.
    manifest_category = taxonomy.get("category")
    if manifest_category is not None and manifest_category != category:
        raise ValueError(
            f"Task {task_dir.name!r} sits under category {category!r} but its manifest "
            f"declares {manifest_category!r}. Recompile the task tree."
        )

    reward_key = _TASK_REWARD_KEY_OVERRIDES.get(task_dir.name)
    if reward_key is None:
        if category not in _CATEGORY_REWARD_KEYS:
            raise ValueError(
                f"No reward key known for category {category!r} (task {task_dir.name!r}). "
                f"Add it to _CATEGORY_REWARD_KEYS."
            )
        reward_key = _CATEGORY_REWARD_KEYS[category]

    # Prefer the funnel's in-situ measured floor over the manifest's
    # `floor_native_estimate`, which the task factory documents as advisory.
    floor = float(canonical.get("funnel", {}).get("floor", taxonomy.get("floor_native_estimate", 0.0)))

    # Resolve checks from canonical data, manifest metadata, then the checks directory.
    checks = list(canonical.get("checks") or taxonomy.get("affected_checks") or [])
    if not checks:
        checks_dir = task_dir / "environment" / "checks"
        checks = sorted(p.name for p in checks_dir.iterdir() if p.is_dir()) if checks_dir.is_dir() else []

    family = taxonomy.get("family", _ACCELERATION_FAMILY if category == "acceleration" else "")
    tree = taxonomy.get("tree", _ACCELERATION_TREE if category == "acceleration" else "")

    extra_info = {
        "task_path": str(task_dir.resolve()),
        "reward_key": reward_key,
        "task_name": task_name,
        # Harbor appends this to the on-disk instruction via `extra_instructions`.
        # This field, not `prompt`, is what actually reaches the model.
        "hint": hint,
        "hint_level": hint_level,
        "timeout_sec": float(manifest.get("agent", {}).get("timeout_sec", 3600.0)),
        "gpus": int(environment.get("gpus", 0)),
        "category": category,
        "family": family,
        "tree": tree,
        "mode": taxonomy.get("mode", ""),
        "floor": floor,
        "checks": checks,
        "network_mode": environment.get("network_mode", ""),
    }

    # Harbor re-reads `instruction.md` and appends the hint itself, so this column is a
    # record of the delivered prompt rather than the delivery path.
    prompt_content = f"{instruction}\n\n{hint}" if hint else instruction

    return {
        "prompt": [{"role": "user", "content": prompt_content}],
        "data_source": DATA_SOURCE,
        # Harbor supplies verifier reward while the schema still requires ground truth.
        "reward_model": {"style": "rule", "ground_truth": ""},
        "task_name": task_name,
        "category": category,
        "family": family,
        "tree": tree,
        "floor": floor,
        "extra_info": extra_info,
    }


def _interleave_categories(df: pd.DataFrame, seed: int = 20260828) -> pd.DataFrame:
    """
    Shuffle rows so no contiguous run of the frame is one category.

    `_discover_task_dirs` walks category directories in order, so the frame arrives
    grouped and a sequential sampler would spend its first steps inside one category.
    Shuffling here makes the artifact correct without relying on `data.shuffle`.

    Args:
        df (pd.DataFrame): The category-ordered frame.
        seed (int): Fixed so the row order is reproducible.

    Returns:
        pd.DataFrame: The same rows in interleaved order.
    """
    return df.sample(frac=1.0, random_state=seed).reset_index(drop=True)


def _stratified_val_names(df: pd.DataFrame, per_group: int, max_fraction: float = 0.25) -> list[str]:
    """
    Pick validation tasks by taking the first `per_group` of every group.

    Grouping is by (category, family, tree), which is the sampling unit the
    sciaccel-rl README prescribes: same-family tasks share a debugging shape, so
    uniform sampling over-weights the large families (57 of 99 repair tasks are
    sign flips). Selection is by sorted task name so the split is reproducible
    without a random seed.

    Args:
        df (pd.DataFrame): The full dataset.
        per_group (int): Tasks to take from each group.
        max_fraction (float): Upper bound on the validation share. One per group is only
            proportionate when groups are large, and an env with many singleton groups
            would otherwise hold out most of the bank.

    Returns:
        list[str]: Sorted validation task names.
    """
    groups = [(k, sorted(g["task_name"])) for k, g in df.groupby(["category", "family", "tree"], sort=True)]
    picked = {k: names[:per_group] for k, names in groups}
    candidates = sum(len(v) for v in picked.values())

    budget = max(1, int(len(df) * max_fraction))
    total = candidates
    if total > budget:
        # Largest groups give up their slot first, because they keep representation
        # either way. The group key breaks ties, so the split needs no seed.
        for key, _ in sorted(groups, key=lambda kv: (-len(kv[1]), kv[0])):
            if total <= budget:
                break
            total -= len(picked[key])
            picked[key] = []
        psrl_logger.info(
            f"Validation capped at {max_fraction:.0%} of {len(df)} tasks: "
            f"kept {total} of {candidates} one-per-group candidates."
        )

    return sorted(name for names in picked.values() for name in names)


def _build_stats(df: pd.DataFrame) -> dict[str, Any]:
    """
    Summarize task counts and floor ranges per group, for curriculum planning.

    Args:
        df (pd.DataFrame): The full dataset.

    Returns:
        dict[str, Any]: Totals plus per-category and per-group breakdowns.
    """
    by_group: dict[str, dict[str, Any]] = {}
    for (category, family, tree), group in df.groupby(["category", "family", "tree"], sort=True):
        floors = group["floor"].tolist()
        by_group[f"{category}/{family}/{tree}"] = {
            "n_tasks": len(group),
            "floor_min": round(min(floors), 6),
            "floor_max": round(max(floors), 6),
            "floor_mean": round(sum(floors) / len(floors), 6),
            "reward_key": sorted({row["reward_key"] for row in group["extra_info"]}),
        }

    return {
        "n_tasks": len(df),
        "n_hinted": int(sum(1 for row in df["extra_info"] if row.get("hint"))),
        "by_category": {k: int(v) for k, v in df["category"].value_counts().sort_index().items()},
        "by_reward_key": {
            k: int(v)
            for k, v in pd.Series([row["reward_key"] for row in df["extra_info"]]).value_counts().sort_index().items()
        },
        "by_group": by_group,
    }


def _load_resolved_lines(repo: Path, env: str) -> dict[str, int]:
    """
    Load `factory/DEFECT_LINES.json`, or return empty when the env has none.

    Only envs whose provenance omits `candidate.meta.line` need this. Absence is
    normal rather than an error, so a missing cache degrades `L1` to a file-only hint
    instead of failing the build.

    Args:
        repo (Path): sciaccel-rl repository root.
        env (str): Environment directory name under `envs/`.

    Returns:
        dict[str, int]: Task directory name to 1-based line number.
    """
    path = repo / "envs" / env / "factory" / "DEFECT_LINES.json"
    if not path.exists():
        psrl_logger.info(f"No resolved line cache at {path!s}. L1 falls back to file-only where needed.")
        return {}
    cache = json.loads(path.read_text(encoding="utf-8"))
    resolved = {str(k): int(v) for k, v in (cache.get("resolved") or {}).items()}
    psrl_logger.info(f"Loaded {len(resolved)} resolved defect lines from {path!s}.")
    return resolved


def build_datasets(
    repo_path: str,
    out_dir: str,
    env: str,
    categories: list[str] | None = None,
    val_per_group: int = 1,
    hint_level: str = "L3",
    difficulty: str | None = None,
) -> dict[str, Any]:
    """
    Build the train split for one hint level, plus the shared unhinted eval set.

    Train and eval are built from separate row passes. The eval set is always unhinted
    so scores stay comparable across levels, while the train split carries whichever
    hint `hint_level` asks for. The split itself is chosen on the unhinted frame, so
    every level trains and scores on exactly the same task partition.

    Writes into `out_dir` as:

        train/<level>.parquet: hinted train split
        eval/<level>.parquet: hinted eval split, in-distribution, absent for L3
        eval/unhinted.parquet: unhinted eval split, shared by every level
        all/<level>.parquet: every task at this level, unsplit
        stats/<level>.json: per-group counts and floor ranges
        split.json: the train and eval partition, and how it was chosen

    Args:
        repo_path (str): Path to the sciaccel-rl repository root.
        out_dir (str): Directory to write the artefacts into.
        env (str): Environment directory name under `envs/`.
        categories (list[str] | None): Categories to include. None means every
            category with at least one compiled task.
        val_per_group (int): Tasks to hold out per (category, family, tree) group.
        hint_level (str): One of `HINT_LEVELS`. `L3` reproduces the unhinted bank.
        difficulty (str | None): Keep only this `metadata.taxonomy.difficulty` tier.
            None keeps every tier.

    Returns:
        dict[str, Any]: The stats dict also written to `stats.json`.
    """
    if hint_level not in HINT_LEVELS:
        raise ValueError(f"Unknown hint_level {hint_level!r}. Choose one of {list(HINT_LEVELS)}.")

    repo = Path(repo_path).resolve()
    canonical_rows = _load_canonical_rows(repo, env)
    resolved_lines = _load_resolved_lines(repo, env)
    task_dirs = _discover_task_dirs(repo, env, categories, difficulty)
    psrl_logger.info(f"Discovered compiled tasks under {repo / 'envs' / env / 'tasks'!s}. Count: {len(task_dirs)}.")

    counts: dict[str, int] = defaultdict(int)
    rows: list[dict[str, Any]] = []
    plain_rows: list[dict[str, Any]] = []
    for category, task_dir in task_dirs:
        rows.append(_build_row(category, task_dir, canonical_rows, hint_level, resolved_lines))
        plain_rows.append(_build_row(category, task_dir, canonical_rows, "L3", resolved_lines))
        counts[category] += 1

    df = pd.DataFrame(rows)
    plain_df = pd.DataFrame(plain_rows)
    if df["task_name"].duplicated().any():
        duplicates = sorted(df.loc[df["task_name"].duplicated(), "task_name"])
        raise ValueError(f"Duplicate task names in the dataset: {duplicates}.")

    val_names = _stratified_val_names(plain_df, val_per_group)
    val_df = plain_df[plain_df["task_name"].isin(val_names)].reset_index(drop=True)
    # Interleave only the train split. Validation runs whole, so its order is moot.
    train_df = _interleave_categories(df[~df["task_name"].isin(val_names)])

    out = Path(out_dir)
    for role in ("train", "eval", "all", "stats"):
        (out / role).mkdir(parents=True, exist_ok=True)

    # One file per role per hint level. The role is the directory, so a training
    # script names a split by path rather than by decoding a filename prefix.
    df.to_parquet(out / "all" / f"{hint_level}.parquet", index=False)
    train_df.to_parquet(out / "train" / f"{hint_level}.parquet", index=False)
    # Unhinted, so it measures unaided localization. Shared by every level, which makes
    # rewriting it on each pass idempotent.
    val_df.to_parquet(out / "eval" / "unhinted.parquet", index=False)
    # Hinted eval on the same partition, because a hint-trained model sees a different
    # task in `eval/unhinted.parquet`. `L3` would only duplicate that file.
    if hint_level != "L3":
        hinted_val_df = df[df["task_name"].isin(val_names)].reset_index(drop=True)
        hinted_val_df.to_parquet(out / "eval" / f"{hint_level}.parquet", index=False)

    (out / "split.json").write_text(
        json.dumps(
            {
                "env": env,
                "categories": sorted(counts),
                "difficulty": difficulty,
                "val_per_group": val_per_group,
                "group_key": ["category", "family", "tree"],
                "val": val_names,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    stats = _build_stats(df)
    stats["repo"] = str(repo)
    stats["env"] = env
    stats["hint_level"] = hint_level
    stats["n_train"] = len(train_df)
    stats["n_val"] = len(val_df)
    (out / "stats" / f"{hint_level}.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")

    psrl_logger.info(
        f"Wrote {hint_level} dataset under {out!s}. Total tasks: {len(df)}. "
        f"Hinted: {stats['n_hinted']}. Train: {len(train_df)}. Eval: {len(val_df)}. "
        f"Categories: {dict(counts)!r}."
    )
    return stats


def main() -> None:
    """
    CLI entry point.
    """
    parser = argparse.ArgumentParser(description="Build SciAccel-RL datasets.")
    parser.add_argument("--repo", required=True, help="Path to the sciaccel-rl repo root.")
    parser.add_argument("--out-dir", required=True, help="Directory for the output artefacts.")
    parser.add_argument("--env", required=True, help="Environment directory name under envs/.")
    parser.add_argument(
        "--categories",
        nargs="+",
        default=None,
        help="Taxonomy categories to include. Defaults to every non-empty category.",
    )
    parser.add_argument(
        "--val-per-group",
        type=int,
        default=1,
        help="Tasks held out per (category, family, tree) group.",
    )
    parser.add_argument(
        "--hint-level",
        choices=list(HINT_LEVELS) + ["all"],
        default="all",
        help="Localization hint strength for the train split. 'all' builds every level.",
    )
    parser.add_argument(
        "--difficulty",
        default=None,
        help="Keep only this metadata.taxonomy.difficulty tier, e.g. 'easy'. Omit to keep every tier.",
    )
    args = parser.parse_args()

    levels = list(HINT_LEVELS) if args.hint_level == "all" else [args.hint_level]
    stats = {}
    for level in levels:
        stats = build_datasets(
            repo_path=args.repo,
            out_dir=args.out_dir,
            env=args.env,
            categories=args.categories,
            val_per_group=args.val_per_group,
            hint_level=level,
            difficulty=args.difficulty,
        )
        print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
