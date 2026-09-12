#!/usr/bin/env python3
"""Plot key RL training metrics from a PSRL log file."""

from __future__ import annotations

import argparse
import math
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

METRICS = (
    ("critic/rewards/mean", "Reward"),
    ("response_length/mean", "Response Length"),
    ("actor/entropy", "Entropy"),
    ("rollout_corr/kl", "Train–Inference KL"),
)
PURPLE = "#7C3AED"
NUMBER = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
STEP_RE = re.compile(r"\bstep:(\d+)\b")
ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
METRIC_RES = {name: re.compile(rf"(?:^|\s|-\s){re.escape(name)}:({NUMBER})(?=\s|$)") for name, _ in METRICS}


def parse_log(path: Path) -> dict[str, list[tuple[int, float]]]:
    """Extract requested metrics, retaining the last value for duplicate steps."""
    by_metric: dict[str, dict[int, float]] = {name: {} for name, _ in METRICS}

    with path.open("r", encoding="utf-8", errors="replace") as log_file:
        for raw_line in log_file:
            line = ANSI_RE.sub("", raw_line)
            step_match = STEP_RE.search(line)
            if step_match is None:
                continue

            step = int(step_match.group(1))
            for name, _ in METRICS:
                value_match = METRIC_RES[name].search(line)
                if value_match is None:
                    continue
                value = float(value_match.group(1))
                if math.isfinite(value):
                    by_metric[name][step] = value

    return {name: sorted(values.items()) for name, values in by_metric.items()}


def plot_metrics(data: dict[str, list[tuple[int, float]]], output: Path) -> None:
    """Draw four metrics in one horizontal row and save the figure."""
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, axes = plt.subplots(1, 4, figsize=(21, 4.4), sharex=True)

    for ax, (name, title) in zip(axes, METRICS):
        points = data[name]
        if not points:
            ax.text(
                0.5,
                0.5,
                "No data",
                ha="center",
                va="center",
                transform=ax.transAxes,
                color="#6B7280",
                fontsize=18,
            )
        else:
            steps, values = zip(*points)
            ax.plot(steps, values, color=PURPLE, linewidth=2.2)

        ax.set_title(title, fontsize=26, fontweight="bold", pad=8)
        ax.set_xlabel("Step", fontsize=24)
        ax.xaxis.set_label_coords(0.5, -0.07)
        ax.tick_params(axis="both", labelsize=20, pad=1, length=3)
        ax.grid(True, color="#E5E7EB", linewidth=0.8)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    fig.tight_layout(w_pad=2.0)

    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=220, bbox_inches="tight", facecolor="white", pad_inches=0.05)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot Reward, Response Length, Entropy, and train-inference KL.")
    parser.add_argument("log_file", type=Path, help="path to the training log")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="output image path (default: <log_name>_training_curves.svg)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.log_file.is_file():
        raise SystemExit(f"Log file not found: {args.log_file}")

    output = args.output or args.log_file.with_name(f"{args.log_file.stem}_training_curves.svg")
    data = parse_log(args.log_file)
    missing = [name for name, _ in METRICS if not data[name]]
    if missing:
        raise SystemExit(f"Metrics not found in log: {', '.join(missing)}")

    plot_metrics(data, output)
    counts = ", ".join(f"{name}={len(data[name])}" for name, _ in METRICS)
    print(f"Parsed points: {counts}")
    print(f"Saved figure to: {output}")


if __name__ == "__main__":
    main()
