# ScienceIDE

An environment for AI agents that do scientific computing work: reading real
simulation codebases, changing them, and being graded on whether the science
still comes out right.

## Components

| Component | What it does |
|---|---|
| [`RL/`](RL/) | Reinforcement learning on scientific-computing repair tasks |

## RL

[`RL/`](RL/) trains a model to fix injected defects in real scientific
simulation codebases (LAPS, MITgcm, Athena++). Each task is a containerized
[Harbor](https://github.com/laude-institute/harbor) episode: the agent is given
a repository and an instruction, it edits source, and a verifier recompiles the
code and compares numerical output against reference frames.

The reward is earned by making a simulation numerically correct again rather
than by matching a reference diff, which makes the task hard to game. Published
results, the task taxonomy, and the full training recipe are in
[`RL/README.md`](RL/README.md).

### Training backend: PSRL

The RL component does not implement its own trainer. It runs on
**[PSRL](https://github.com/psrl-project/psrl)**, a modified
[veRL](https://github.com/volcengine/verl) that decouples rollout, reward, and
training behind a Parameter Server so generation and training proceed
asynchronously with bounded model-version staleness.

PSRL is what makes this recipe practical. Attaching a black-box agent harness,
one that runs in its own container and is reached over an OpenAI-compatible
endpoint, took no changes inside the framework: ScienceIDE supplies one agent
loop and one reward function, registered through config. PSRL contributes the
session-scoped API and trajectory collection, async GRPO, RDMA weight sync, and
vLLM fleet serving.

Install PSRL first, then the RL package. See
[`RL/README.md`](RL/README.md#install).
