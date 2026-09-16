# SFT

> Code: [github.com/aitofound/ScienceIDE](https://github.com/aitofound/ScienceIDE) · Models: [ScienceIDE Model Series](https://huggingface.co/collections/AItonomy/scienceide-model-series) · Project page: [aitonomy.org/projects/scienceide](https://aitonomy.org/projects/scienceide)

Standalone tool-trajectory LoRA SFT, with all training logic in **`train.py`**.
Pass the model through `--model`. ms-swift identifies the model type and chat template from
model metadata; you can also set them explicitly with `--model-type` and `--template`.
The code is not tied to a specific model or model family. Available models, templates,
and acceleration kernels depend on the installed ms-swift version and its dependencies.

Workflow: JSONL trajectories → data and label checks → LoRA training → adapter checkpoint.
You can copy this entire directory into another repository. It does not depend on Python
modules, experiment paths, or cluster addresses from the original repository.

## Files

| File | Purpose |
| --- | --- |
| `train.py` | Data preparation with `prepare` and training with `train`; the complete Python training implementation |
| `requirements.txt` | Core dependency versions |
| `zero3.json` | Optional DeepSpeed ZeRO-3 configuration |
| `sample_data/*.jsonl` | 4 manually written training samples and 2 validation samples, for workflow checks only |
| `test_train.py` | Regression checks for labels, task splits, general parameters, and distributed sampling |

## Installation

Run all commands below from this directory using Python 3.11. Install a PyTorch build
compatible with your driver first. The following example installs dependencies for CUDA 12.4:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install torch==2.6.0 torchvision==0.21.0 \
  --index-url https://download.pytorch.org/whl/cu124
DS_BUILD_OPS=0 python -m pip install -r requirements.txt
python -m pip check
```

Liger reduces GPU memory use when computing loss for long sequences. Use `--no-liger`
if the model does not support the kernel. Install any additional architecture dependencies
required by your chosen model. For example, if it requires linear attention kernels,
you can install `flash-linear-attention==0.4.2`.

The script includes a fix for distributed sampling of trailing samples in ms-swift 4.5.3
and import compatibility handling for PyTorch 2.6 / DeepSpeed 0.19.6 within the running
process. It does not modify installed package files. Recheck these behaviors after upgrading dependencies.

## Minimal Example

Replace `MODEL_PATH` with a local model directory, or pass a Hugging Face model ID.
For a remote model, use `--revision` to pin a commit. Use the same revision for preparation and training.

```bash
export MODEL_PATH=/path/to/model

# Load only the tokenizer/config to check and convert data; do not load training weights.
CUDA_VISIBLE_DEVICES='' python train.py prepare \
  --model "$MODEL_PATH" \
  --train-file sample_data/train.jsonl \
  --validation-file sample_data/validation.jsonl \
  --max-length 4096 --output-dir data/sft

# Check data hashes and batch settings, then print training arguments; no model loading or training.
python train.py train --model "$MODEL_PATH" --data-dir data/sft \
  --global-batch-size 2 --max-steps 2 --output-dir outputs/smoke --dry-run

# Run two optimization steps on one GPU, run validation, and save checkpoint-2.
CUDA_VISIBLE_DEVICES=0 python train.py train \
  --model "$MODEL_PATH" --data-dir data/sft \
  --global-batch-size 2 --max-steps 2 --output-dir outputs/smoke
```

If automatic detection does not apply, add `--model-type "$MODEL_TYPE" --template "$CHAT_TEMPLATE"`
to the preparation command. Set these variables to the ms-swift registered types for the chosen model.
By default, training reuses the model type and template resolved during data preparation.

Thinking mode is disabled and the non-thinking prefix is enabled by default. Adjust these settings
with `--enable-thinking` and `--no-add-non-thinking-prefix`. Keep them consistent between
preparation and training. For multimodal models, the vision encoder and alignment module are
frozen by default; adjust this with `--no-freeze-vit` and `--no-freeze-aligner`.
The exact behavior of these options depends on the model and template implementations.

The output is a LoRA adapter in `outputs/smoke/checkpoint-2/`, which requires the original
base model to use. The checkpoint also saves optimizer/scheduler state. `sft_config.json`
saves the launch configuration, and `sft_run.json` is written after training returns successfully.
Add `--report-to tensorboard` to record local training curves.

4096 is the default length for the short-context example. Real trajectories are often longer:
prepare the data again for the target model, then choose the context length and parallelism
settings based on GPU capacity. A smoke run with a few samples does not reflect the GPU memory
requirements of the full dataset.

## Using Your Own Training Data

The input contains one JSON object per line. Two structures are supported; raw ATIF files are not accepted:

```json
{"task_name":"task-a","prompt":[{"role":"user","content":"Fix the function."}],"completion":[{"role":"assistant","content":"The fix is ..."}],"tools":[]}
```

```json
{"task_name":"task-b","messages":[{"role":"user","content":"Fix the function.","loss":false},{"role":"assistant","content":"An earlier failed attempt.","loss":false},{"role":"user","content":"The test still fails.","loss":false},{"role":"assistant","content":"The corrected implementation.","loss":true}],"tools":[]}
```

- The entire `prompt` is excluded from supervision. Within `completion`, only assistant/tool_call messages are supervised, with explicit `loss=false` preserved.
- In `messages`, assistant/tool_call messages are supervised by default when `loss` is omitted. Explicitly mark historical context windows or failed actions.
- system/user/tool/tool_response messages do not contribute to loss. Explicitly setting `loss=true` on these messages raises an error.
- Native OpenAI `assistant.tool_calls` are converted to ms-swift `tool_call` messages. `tools` can be an array or a JSON string.
- Tool calls must have matching schemas. Only text messages are supported. A segment may end with tool feedback,
  but it must contain at least one valid assistant/tool_call supervision target.
- `task_name` is used to check for leakage across splits. Keep all segments/attempts for the same task in one split.
  If older message data lacks this field, place `train.audit.jsonl` and `validation.audit.jsonl`
  beside the corresponding data files. The script reads task mappings from records with `status=kept`.

```bash
python train.py prepare --model "$MODEL_PATH" \
  --train-file /path/to/train.jsonl --validation-file /path/to/validation.jsonl \
  --max-length 32768 --output-dir data/trajectories
```

Preparation uses the actual template to count tokens for each sample, checks that supervision
targets are nonempty, and uses synthetic sentinels to verify that the data preprocessor and
template preserve the loss mask. Overlength samples raise an error by default. Only an explicit
`--drop-overlength` excludes whole samples and records them in the audit; tool calls are not truncated.
Overlapping tasks raise an error. The script does not randomly split data or read the test split.
A directory from a failed preparation has no `report.json` and cannot be used for training;
choose a new directory when retrying.

The current preparation report format is v2. It records the resolved model type, template,
and template options. Run `prepare` again for data prepared with an older format.
The script preserves the input supervision flags. It does not automatically judge whether
trajectories succeeded or execute tool commands again. Perform verifier filtering, protocol
conversion, and failed-action annotation when generating the input data.

## Integration Scope and Validation

Training uses ms-swift throughout, preserving assistant/completion supervision, task split checks,
actual token audits, LoRA parameters, distributed batch calculations, and compatibility handling
from the original workflow. Raw trajectory collection, specialized data repairs, experiment
scheduling, and benchmark evaluation remain upstream. This script implements SFT and does not
include an online RL optimizer.

```bash
python -m unittest discover -s . -p 'test_*.py' -v
```

18 standard-library regression tests cover supervision flags, split leakage, overlength handling,
general model parameters, and distributed configurations. A local small model with random weights
is used to check the actual template, CPU optimization, validation, and checkpoint saving.
Multi-node GPU, NCCL/ZeRO-3, and different model architectures require validation in their
corresponding environments. Workflow checks do not establish actual capability improvements.
