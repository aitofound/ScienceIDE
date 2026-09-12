"""
Resolve the source line of each injected defect, and cache it per environment.

`_build_hint` needs a line number for the strongest hint level, and not every env
records one. `authoring/provenance.json` stores the defect as a literal `old` text
block, so locating that block in the pinned upstream file gives the line exactly.

A recorded `candidate.meta.line` always wins and is never written to the cache, so the
cache holds only the lines the env itself is missing. Output goes to
`envs/<env>/factory/DEFECT_LINES.json` to keep `build_dataset.py` offline. Re-run this
only when the task bank changes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path
from typing import Any

psrl_logger = logging.getLogger(__file__)
psrl_logger.setLevel(os.getenv("PSRL_LOGGING_LEVEL", "INFO"))
if not psrl_logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    psrl_logger.addHandler(_handler)
    psrl_logger.propagate = False

CACHE_NAME = "DEFECT_LINES.json"

# Where each env's pinned source comes from, preferring a bundled archive that needs
# no network. A sha256 mismatch means the env moved and this table is stale.
_SOURCES: dict[str, dict[str, Any]] = {
    "mitgcm-biogeo": {
        "bundled": "env/source/mitgcm-853761d8f46926cd8042d6e0ad252050561fd6fa.tar.gz",
        "sha256": "7fc8abfc7bd58bc4c5a40c20213f8e3f2fb377c889a7ed0e3ddbfe1fe4358586",
    },
    "athena-gr": {
        "url": (
            "https://github.com/PrincetonUniversity/athena/archive/823614c90b594472747a0ac2a699e4a454f300d2.tar.gz"
        ),
        "sha256": "226e81620cbcabbbeff81b2989312c13163db64667aca1a1b3778aab9921ebfe",
    },
    # Pins a commit and skips the digest check, because codeload tarballs are not
    # byte-stable. The commit guarantees the contents, which is all a lookup needs.
    "laps": {
        "url": "https://github.com/chenshihelio/LAPS/archive/a625806931a82ba3342f35906955e6806081d219.tar.gz",
        "sha256": None,
        "commit": "a625806931a82ba3342f35906955e6806081d219",
    },
}


def _sha256(path: Path) -> str:
    """Return the hex sha256 of a file, read in chunks to bound memory."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _fetch(url: str, dest: Path, expected_sha256: str | None) -> None:
    """
    Download `url` to `dest` and verify its digest when one is pinned.

    The digest check is the whole point where a digest exists: a truncated transfer
    produced a 966 KB file that extracted without error and would have yielded wrong
    line numbers silently. A None digest means the env pins a commit instead, so the
    URL itself already names immutable content and only emptiness is worth checking.

    Args:
        url (str): Source archive URL.
        dest (Path): Where to write the archive.
        expected_sha256 (str | None): Digest the archive must have, or None to skip.

    Raises:
        RuntimeError: If the download fails or the digest does not match.
    """
    psrl_logger.info(f"Fetching {url}")
    result = subprocess.run(
        ["curl", "-fsSL", "--retry", "3", "--retry-delay", "2", "--max-time", "600", "-o", str(dest), url],
        capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Download failed for {url}: {result.stderr.decode(errors='replace')[:400]}")
    if expected_sha256 is None:
        if dest.stat().st_size == 0:
            raise RuntimeError(f"Downloaded an empty archive from {url}.")
        psrl_logger.info(f"No digest pinned for {url}. Relying on the commit in the URL.")
        return
    actual = _sha256(dest)
    if actual != expected_sha256:
        raise RuntimeError(f"Digest mismatch for {url}. Expected {expected_sha256}, got {actual}.")


def _extract_root(archive: Path, workdir: Path) -> Path:
    """
    Extract `archive` and return the single top-level directory inside it.

    Args:
        archive (Path): Source tarball.
        workdir (Path): Directory to extract into.

    Returns:
        Path: The extracted source root.

    Raises:
        RuntimeError: If the archive does not hold exactly one top-level directory.
    """
    with tarfile.open(archive) as tar:
        tar.extractall(workdir, filter="data")
    entries = [p for p in workdir.iterdir() if p.is_dir()]
    if len(entries) != 1:
        raise RuntimeError(f"Expected one top-level directory in {archive.name}, found {len(entries)}.")
    return entries[0]


def _resolve_one(source_root: Path, defect_file: str, old_text: str) -> tuple[int | None, str]:
    """
    Find the 1-based line where `old_text` begins in `defect_file`.

    Args:
        source_root (Path): Extracted upstream source root.
        defect_file (str): Repository-relative path from the provenance row.
        old_text (str): The pre-defect text block, matched literally.

    Returns:
        tuple[int | None, str]: The line number and a status string. The line is None
            for every status other than `ok`, so a caller cannot mistake a failed
            lookup for line 1.
    """
    path = source_root / defect_file
    if not path.exists():
        return None, "file_missing"
    text = path.read_text(encoding="utf-8", errors="replace")
    occurrences = text.count(old_text)
    if occurrences == 0:
        return None, "no_match"
    if occurrences > 1:
        # An ambiguous block cannot name one line honestly.
        return None, f"ambiguous_{occurrences}"
    return text[: text.index(old_text)].count("\n") + 1, "ok"


def _iter_provenance(env_dir: Path):
    """Yield (task_name, provenance row) for every task that has one."""
    for path in sorted((env_dir / "tasks").glob("**/authoring/provenance.json")):
        yield path.parent.parent.name, json.loads(path.read_text(encoding="utf-8"))


def resolve_env(repo: Path, env: str, allow_network: bool = True) -> dict[str, Any]:
    """
    Resolve every injected defect's line for one environment and write the cache.

    Args:
        repo (Path): sciaccel-rl repository root.
        env (str): Environment directory name under `envs/`.
        allow_network (bool): Whether a remote fetch is permitted when the env ships
            no bundled archive.

    Returns:
        dict[str, Any]: The cache written to `factory/DEFECT_LINES.json`.
    """
    if env not in _SOURCES:
        raise ValueError(f"No pinned source known for env {env!r}. Add it to _SOURCES.")
    spec = _SOURCES[env]
    env_dir = repo / "envs" / env

    workdir = Path(tempfile.mkdtemp(prefix=f"defectlines-{env}-"))
    try:
        bundled = spec.get("bundled")
        if bundled and (env_dir / bundled).exists():
            archive = env_dir / bundled
            actual = _sha256(archive)
            if actual != spec["sha256"]:
                raise RuntimeError(f"Bundled archive digest mismatch for {env}. Got {actual}.")
            psrl_logger.info(f"Using bundled source archive: {archive.name}")
        else:
            if not allow_network:
                raise RuntimeError(f"Env {env!r} needs a network fetch but allow_network is False.")
            archive = workdir / "source.tar.gz"
            _fetch(spec["url"], archive, spec["sha256"])
        source_root = _extract_root(archive, workdir / "src")

        lines: dict[str, int] = {}
        statuses: dict[str, str] = {}
        agreements = disagreements = 0
        for task_name, row in _iter_provenance(env_dir):
            candidate = row.get("candidate") or {}
            edits = (candidate.get("break") or {}).get("edits") or []
            if not edits:
                statuses[task_name] = "no_edits"
                continue
            edit = edits[0]
            defect_file = edit.get("file")
            old_text = edit.get("old")
            if not defect_file or old_text is None:
                statuses[task_name] = "no_edit_fields"
                continue
            line, status = _resolve_one(source_root, defect_file, old_text)
            statuses[task_name] = status
            if line is None:
                continue
            # Cross-check against the env's own record where it has one. This is what
            # makes the method trustworthy for the envs that record nothing.
            recorded = (candidate.get("meta") or {}).get("line")
            if recorded is None:
                lines[task_name] = line
                continue
            # A recorded line wins and is never cached, because `_build_hint` reads
            # `meta.line` first and a second value could only disagree.
            span = old_text.count("\n")
            if line == int(recorded) or line + span == int(recorded):
                agreements += 1
            else:
                # A constant offset across every task in one file means the build
                # patches that file, so the recorded line is the navigable one.
                disagreements += 1
                psrl_logger.info(
                    f"Line offset for {task_name}: upstream {line} (span {span}) "
                    f"vs recorded {recorded}. Keeping the recorded line."
                )

        cache = {
            "env": env,
            "source_sha256": spec["sha256"],
            # Only tasks whose provenance records no line. A task with a recorded line
            # is deliberately absent, so the cache can never contradict it.
            "resolved": lines,
            "statuses": statuses,
            "cross_check": {"agree": agreements, "offset": disagreements},
        }
        out = env_dir / "factory" / CACHE_NAME
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(cache, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        unresolved = {k: v for k, v in statuses.items() if v != "ok"}
        psrl_logger.info(
            f"{env}: cached {len(lines)} newly resolved lines of {len(statuses)} tasks. "
            f"Cross-check agree={agreements} offset={disagreements}. Wrote {out}."
        )
        if unresolved:
            psrl_logger.info(f"{env}: unresolved statuses: {sorted(set(unresolved.values()))}")
        # A task that ends up with neither a recorded nor a resolved line degrades to a
        # file-only hint, which is correct behaviour rather than a failure. Only report.
        if agreements == 0 and disagreements == 0 and lines:
            psrl_logger.warning(
                f"{env}: no task carried a recorded line, so nothing cross-validated the "
                f"{len(lines)} resolved lines. Spot check a few before training on them."
            )
        return cache
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Resolve defect line numbers from pinned upstream source.")
    parser.add_argument("--repo", required=True, help="Path to the sciaccel-rl repo root.")
    parser.add_argument(
        "--env",
        action="append",
        required=True,
        help="Environment directory name under envs/. Repeat for several.",
    )
    parser.add_argument("--no-network", action="store_true", help="Fail rather than fetch a remote archive.")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    for env in args.env:
        resolve_env(repo, env, allow_network=not args.no_network)


if __name__ == "__main__":
    main()
