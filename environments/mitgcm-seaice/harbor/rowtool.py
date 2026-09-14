#!/usr/bin/env python3
"""Build one genmake2 profile or run one frozen single-process MITgcm row."""

import argparse
import json
import os
import sys

import runtime_lib


def row(case_dir):
    with open(os.path.join(case_dir, "row.json"), encoding="utf-8") as handle:
        return json.load(handle)


def representative(cases_dir, profile):
    matches = []
    for name in sorted(os.listdir(cases_dir)):
        case_dir = os.path.join(cases_dir, name)
        if os.path.isfile(os.path.join(case_dir, "row.json")) and \
                row(case_dir).get("build_profile") == profile:
            matches.append(case_dir)
    if not matches:
        raise RuntimeError(f"no vendored case represents build profile {profile}")
    return matches[0]


def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build")
    build.add_argument("source")
    build.add_argument("cases")
    build.add_argument("profile")
    build.add_argument("build_dir")
    build.add_argument("--jobs", type=int, default=4)
    build.add_argument("--strict", action="store_true")
    run = commands.add_parser("run")
    run.add_argument("builds")
    run.add_argument("case_dir")
    run.add_argument("out_dir")
    run.add_argument("--timeout", type=float, default=120.0)
    run.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    if args.command == "build":
        case_dir = representative(args.cases, args.profile)
        result = runtime_lib.build_profile(
            args.source, case_dir, args.build_dir, args.jobs)
        print(json.dumps({"profile": args.profile, **result}, sort_keys=True))
        return int(args.strict and result["exit"] != 0)

    fact = row(args.case_dir)
    binary = os.path.join(args.builds, fact["build_profile"], "mitgcmuv")
    status = runtime_lib.run_profile(
        binary, args.case_dir, args.out_dir,
        timeout=min(args.timeout, float(fact["timeout_sec"])))
    print(json.dumps(status, sort_keys=True))
    return int(args.strict and status["status"] != "ok")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc
