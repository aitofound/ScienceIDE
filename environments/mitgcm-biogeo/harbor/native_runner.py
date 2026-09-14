#!/usr/bin/env python3
"""Build and run frozen single-process MITgcm deck profiles in images."""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "factory"))


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    build.add_argument("source")
    build.add_argument("cases")
    build.add_argument("builds")
    build.add_argument("checks", nargs="+")
    build.add_argument("--jobs", type=int, default=4)
    run = sub.add_parser("run")
    run.add_argument("builds")
    run.add_argument("cases")
    run.add_argument("out")
    run.add_argument("checks", nargs="+")
    run.add_argument("--timeout", type=float, default=120.0)
    args = parser.parse_args()
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import runtime_lib
    if args.command == "build":
        for check in args.checks:
            result = runtime_lib.build_profile(
                args.source, os.path.join(args.cases, check),
                os.path.join(args.builds, check), args.jobs)
            print(check, result)
            if result["exit"] != 0:
                return 1
        return 0
    for check in args.checks:
        status = runtime_lib.run_profile(
            os.path.join(args.builds, check, "mitgcmuv"),
            os.path.join(args.cases, check), os.path.join(args.out, check),
            args.timeout)
        print(check, status)
        if status["status"] != "ok":
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
