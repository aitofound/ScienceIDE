#!/usr/bin/env python3
"""Standalone tool-trajectory LoRA SFT: prepare, then train with ms-swift.

No imports from the parent repository; run this file with Python or torchrun.
Only preparation and training live here. Raw rollout collection stays upstream.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib
from importlib.metadata import PackageNotFoundError, version
import json
import math
import os
from pathlib import Path
import sys
import typing


ASSISTANT_ROLES = {"assistant", "tool_call"}
ROLES = ASSISTANT_ROLES | {"system", "user", "tool", "tool_response"}
STACK = ("ms-swift", "transformers", "torch", "peft", "datasets", "accelerate")


def template_options(args) -> dict:
    return dict(enable_thinking=args.enable_thinking,
                add_non_thinking_prefix=args.add_non_thinking_prefix)


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_jsonl(path: Path):
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                raise ValueError(f"{path}:{line_number}: blank JSONL row")
            try:
                row = json.loads(line)
                if not isinstance(row, dict):
                    raise ValueError("row must be an object")
            except ValueError as exc:
                raise ValueError(f"{path}:{line_number}: {exc}") from exc
            yield line_number, row


def normalize_row(row: dict) -> dict:
    """Keep explicit loss=False, including failed actions retained as history."""
    has_sections = "prompt" in row or "completion" in row
    if "messages" in row and has_sections:
        raise ValueError("Use messages OR prompt/completion, not both")
    sections = [("messages", row.get("messages"))] if not has_sections else [
        ("prompt", row.get("prompt")), ("completion", row.get("completion"))]
    tools = row.get("tools") or []
    if isinstance(tools, str):
        tools = json.loads(tools)
    if not isinstance(tools, list):
        raise ValueError("tools must be a list or a JSON-encoded list")
    names = set()
    for tool in tools:
        function = tool.get("function", tool)
        if not isinstance(function.get("name"), str):
            raise ValueError("Each tool must have a function name")
        names.add(function["name"])
    messages = []
    for section, items in sections:
        if not isinstance(items, list) or not items:
            raise ValueError(f"{section} must be a nonempty list")
        for original in items:
            message = copy.deepcopy(original)
            role = message.get("role")
            if role not in ROLES:
                raise ValueError(f"Unsupported role: {role}")
            if "loss_scale" in message:
                raise ValueError("This script accepts boolean loss flags, not loss_scale")
            loss = message.get("loss", role in ASSISTANT_ROLES)
            if not isinstance(loss, bool):
                raise ValueError("loss must be a JSON boolean")
            if "loss" in message and loss and role not in ASSISTANT_ROLES:
                raise ValueError("Only assistant/tool_call messages can have loss=true")
            loss = loss and section != "prompt" and role in ASSISTANT_ROLES
            content = message.get("content") or ""
            calls = message.get("tool_calls")
            if calls:
                if role != "assistant" or not isinstance(calls, list):
                    raise ValueError("tool_calls must be a list on an assistant message")
                if content:
                    if not isinstance(content, str):
                        raise ValueError("Only text messages are supported")
                    messages.append(dict(role="assistant", content=content, loss=loss))
                for call in calls:
                    function = copy.deepcopy(call.get("function", call))
                    arguments = function.get("arguments", {})
                    if isinstance(arguments, str):
                        arguments = json.loads(arguments)
                    messages.append(dict(role="tool_call", loss=loss, content=json.dumps(
                        dict(name=function["name"], arguments=arguments), ensure_ascii=False)))
            else:
                role = "tool_response" if role == "tool" else role
                if isinstance(content, dict) and role in {"tool_call", "tool_response"}:
                    content = json.dumps(content, ensure_ascii=False)
                if not isinstance(content, str):
                    raise ValueError("Only text messages are supported")
                messages.append(dict(role=role, content=content, loss=loss))
    for message in messages:
        if message["role"] == "tool_call":
            call = json.loads(message["content"])
            if call.get("name") not in names:
                raise ValueError(f"Tool call has no matching schema: {call.get('name')}")
    if not any(m["loss"] and m["content"] for m in messages):
        raise ValueError("No supervised assistant target remains")
    return dict(messages=messages, tools=json.dumps(tools, ensure_ascii=False))


def task_sidecar(path: Path) -> dict[int, str]:
    """Read both historical sequential audits and repaired output_line audits."""
    sidecar = path.with_suffix(".audit.jsonl")
    if not sidecar.exists():
        return {}
    result = {}
    for _, row in read_jsonl(sidecar):
        if row.get("status") != "kept":
            continue
        line = row.get("output_line", len(result) + 1)
        task = row.get("task_name")
        if not isinstance(line, int) or line < 1 or line in result or not task:
            raise ValueError(f"Invalid task audit: {sidecar}")
        result[line] = task
    return result


def runtime_setup() -> None:
    os.environ.setdefault("USE_HF", "1")
    os.environ.setdefault("USE_HUB_KERNELS", "NO")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    # DeepSpeed 0.19.6 uses list[int], which torch 2.6's inferencer cannot spell.
    # Import with an equivalent annotation entry, then restore the original table.
    try:
        needs_fix = version("torch").split("+")[0] == "2.6.0" and version("deepspeed") == "0.19.6"
    except PackageNotFoundError:
        needs_fix = False
    if needs_fix:
        import torch
        schema = importlib.import_module("torch._library.infer_schema")
        added = list[int] not in schema.SUPPORTED_PARAM_TYPES
        if added:
            schema.SUPPORTED_PARAM_TYPES[list[int]] = schema.SUPPORTED_PARAM_TYPES[typing.List[int]]
        # This DeepSpeed release imports GPU-only Triton inference kernels even
        # for CPU tokenization. Make only that import treat Triton as unavailable.
        cpu_only = not torch.cuda.is_available()
        triton_present = "triton" in sys.modules
        saved_triton = sys.modules.get("triton")
        if cpu_only:
            sys.modules["triton"] = None
        try:
            importlib.import_module("deepspeed")
        finally:
            if cpu_only:
                if triton_present:
                    sys.modules["triton"] = saved_triton
                else:
                    sys.modules.pop("triton", None)
            if added:
                schema.SUPPORTED_PARAM_TYPES.pop(list[int], None)
    if version("ms-swift") != "4.5.3":
        raise ValueError("This script targets ms-swift==4.5.3; install requirements.txt")


def load_template(args):
    from swift.model import get_model_processor
    from swift.template import get_template
    _, processor = get_model_processor(args.model, model_type=args.model_type,
                                      revision=args.revision, load_model=False, use_hf=True)
    template = get_template(processor, template_type=args.template,
                            max_length=1_000_000_000, loss_scale="default", **template_options(args))
    template.set_mode("train")
    tokenizer = getattr(processor, "tokenizer", processor)
    # Hash actual tokenizer/config files, so changing a local path or Hub branch
    # cannot silently change the encoding after preparation.
    model_dir = Path(processor.model_info.model_dir)
    files = {str(p.relative_to(model_dir)): sha256(p)
             for p in sorted(model_dir.rglob("*"))
             if p.is_file() and (p.name in {"config.json", "tokenizer.json", "tokenizer_config.json",
                                           "special_tokens_map.json", "added_tokens.json",
                                           "vocab.json", "vocab.txt", "merges.txt", "tokenizer.model"}
                                 or p.suffix == ".jinja")}
    identity = dict(model_type=processor.model_info.model_type,
                    template=template.template_meta.template_type,
                    template_options=template_options(args), files=files,
                    versions={name: version(name) for name in STACK})
    return template, tokenizer, identity


def check_mask(template, tokenizer) -> None:
    """Exercise both ordinary messages and native tool-call masks."""
    tool = dict(type="function", function=dict(name="mask_probe_tool", description="Mask probe",
                parameters=dict(type="object", properties={"command": {"type": "string"}})))
    row = dict(tools=[tool], messages=[
        dict(role="system", content="MASK_SYSTEM_SENTINEL", loss=False),
        dict(role="user", content="MASK_USER_SENTINEL", loss=False),
        dict(role="assistant", content="MASK_HISTORY_SENTINEL", loss=False),
        dict(role="tool_call", content=json.dumps(dict(name="mask_probe_tool", arguments={
            "command": "MASK_BAD_ACTION_SENTINEL"})), loss=False),
        dict(role="tool_response", content="MASK_OBSERVATION_SENTINEL", loss=False),
        dict(role="tool_call", content=json.dumps(dict(name="mask_probe_tool", arguments={
            "command": "GOOD_RECOVERY_TARGET_SENTINEL"})), loss=True),
        dict(role="tool_response", content="MASK_SECOND_OBSERVATION_SENTINEL", loss=False),
        dict(role="assistant", content="GOOD_FINAL_TARGET_SENTINEL", loss=True)])
    # Exercise the same dataset preprocessor used by training, too.
    from swift.dataset import MessagesPreprocessor
    processed = MessagesPreprocessor().preprocess(normalize_row(row))
    encoded = template.encode(processed)
    target = tokenizer.decode([x for x in encoded["labels"] if x != -100])
    if "MASK_" in target or any(marker not in target for marker in (
            "GOOD_RECOVERY_TARGET_SENTINEL", "GOOD_FINAL_TARGET_SENTINEL")):
        raise ValueError("Template/dataset preprocessor did not preserve assistant-only loss")


def prepare(args) -> None:
    if args.output_dir.exists():
        raise ValueError("Preparation output already exists; choose a new --output-dir")
    runtime_setup()
    template, tokenizer, identity = load_template(args)
    check_mask(template, tokenizer)
    sources = {"train": args.train_file}
    if args.validation_file:
        sources["validation"] = args.validation_file
    # Check task overlap before tokenization, including any overlength rows.
    data, task_sets, inputs = {}, {}, {}
    for split, path in sources.items():
        audit = task_sidecar(path)
        rows, tasks = [], set()
        inputs[split] = dict(sha256=sha256(path), filename=path.name)
        if path.with_suffix(".audit.jsonl").exists():
            inputs[split]["audit_sha256"] = sha256(path.with_suffix(".audit.jsonl"))
        for line, row in read_jsonl(path):
            task = row.get("task_name") or audit.get(line)
            if not isinstance(task, str) or not task.strip():
                raise ValueError(f"{path}:{line}: need task_name or a matching .audit.jsonl")
            if line in audit and audit[line] != task:
                raise ValueError(f"{path}:{line}: task_name disagrees with audit")
            try:
                rows.append((line, task, normalize_row(row)))
            except (ValueError, KeyError, TypeError) as exc:
                raise ValueError(f"{path}:{line}: {exc}") from exc
            tasks.add(task)
        if not rows or (audit and set(audit) != set(range(1, len(rows) + 1))):
            raise ValueError(f"Empty data or incomplete audit: {path}")
        data[split], task_sets[split] = rows, tasks
    overlap = task_sets["train"] & task_sets.get("validation", set())
    if overlap:
        raise ValueError(f"Train/validation task overlap: {sorted(overlap)[:5]}")
    args.output_dir.mkdir(parents=True)
    report = dict(format_version=2, encoding=identity, inputs=inputs,
                  max_length=args.max_length, mask_check_passed=True,
                  train_validation_task_overlap=0, splits={})
    for split, rows in data.items():
        lengths, supervised, excluded = [], 0, 0
        destination = args.output_dir / f"{split}.jsonl"
        with destination.open("w", encoding="utf-8") as output, (
                args.output_dir / f"{split}.audit.jsonl").open("w", encoding="utf-8") as audit:
            for line, task, row in rows:
                encoded = template.encode(copy.deepcopy(row))
                tokens = len(encoded["input_ids"])
                targets = sum(x != -100 for x in encoded["labels"])
                if not targets:
                    raise ValueError(f"{split}:{line}: encoded target is empty")
                too_long = tokens > args.max_length
                if too_long and not args.drop_overlength:
                    raise ValueError(f"{split}:{line}: {tokens} tokens > {args.max_length}; "
                                     "raise --max-length or explicitly use --drop-overlength")
                record = dict(source_line=line, task_name=task, tokens=tokens,
                              supervised_tokens=targets, status="overlength" if too_long else "kept")
                if too_long:
                    excluded += 1
                else:
                    output.write(json.dumps(row, ensure_ascii=False) + "\n")
                    lengths.append(tokens)
                    supervised += targets
                    record["output_line"] = len(lengths)
                audit.write(json.dumps(record, ensure_ascii=False) + "\n")
        if not lengths:
            raise ValueError(f"No {split} rows remain")
        report["splits"][split] = dict(examples=len(lengths), excluded_overlength=excluded,
            tokens=sum(lengths), supervised_tokens=supervised, max_tokens=max(lengths),
            sha256=sha256(destination))
    # The report is the completion marker; a partial directory cannot be trained.
    write_json(args.output_dir / "report.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


def distributed_order(indices, world_size):
    if world_size < 1 or not indices:
        raise ValueError("Need nonempty indices and a positive world size")
    return list(indices) + [indices[i % len(indices)] for i in range((-len(indices)) % world_size)]


def patch_sampler() -> None:
    """ms-swift 4.5.3 otherwise floors the data length before shuffling."""
    import torch
    from swift.dataloader.shard import BatchSamplerShard
    if getattr(BatchSamplerShard, "_sft_patched", False):
        return
    original_init = BatchSamplerShard.__init__

    def initialize(self, total_samples, *args, **kwargs):
        original_init(self, total_samples, *args, **kwargs)
        self._sft_samples = total_samples
        self.total_samples = math.ceil(total_samples / self.world_size)

    def iterate(self):
        generator = torch.Generator().manual_seed(self.curr_seed)
        if self.shuffle and self.group_by_length:
            from transformers.trainer_pt_utils import get_length_grouped_indices
            indices = get_length_grouped_indices(self.lengths, self.batch_size * self.world_size,
                                                generator=generator)
        elif self.shuffle:
            indices = torch.randperm(self._sft_samples, generator=generator).tolist()
        else:
            indices = list(range(self._sft_samples))
        indices = distributed_order(indices, self.world_size)[self.rank::self.world_size]
        for start in range(0, len(indices), self.batch_size):
            batch = indices[start:start + self.batch_size]
            if len(batch) == self.batch_size or not self.drop_last:
                yield batch

    BatchSamplerShard.__init__ = initialize
    BatchSamplerShard.__iter__ = iterate
    BatchSamplerShard._sft_patched = True


def validate_sequence_parallel(config, size):
    text_config = config.get("text_config", config)
    layer_types = text_config.get("layer_types", [])
    if any(layer not in {"full_attention", "sliding_attention"} for layer in layer_types):
        raise ValueError("Sequence parallelism requires supported attention layers")
    heads = text_config.get("num_key_value_heads", text_config.get("num_attention_heads", 0))
    if not heads or heads % size:
        raise ValueError("Sequence parallel size must divide the model's KV head count")


def build_training_args(args, report, world_size, local_world_size):
    sp = args.sequence_parallel_size
    if world_size % sp or local_world_size % sp:
        raise ValueError("Sequence parallel size must divide world size and GPUs per node")
    if sp > 1 and not args.deepspeed:
        raise ValueError("Sequence parallelism requires DeepSpeed in this script")
    dp = world_size // sp
    divisor = dp * args.batch_size
    if args.global_batch_size % divisor:
        raise ValueError("Global batch must be divisible by (world_size / SP) * batch_size")
    max_length = args.max_length or report["max_length"]
    if max_length < max(s["max_tokens"] for s in report["splits"].values()):
        raise ValueError("Training context is shorter than prepared examples")
    values = dict(model=args.model,
        tuner_type="lora", lora_rank=args.lora_rank, lora_alpha=args.lora_alpha,
        lora_dropout=0.05, target_modules="all-linear", torch_dtype=args.dtype,
        attn_impl="sdpa", use_liger_kernel=args.liger, loss_scale="default",
        dataset=str((args.data_dir / "train.jsonl").resolve()), split_dataset_ratio=0,
        strict=True, truncation_strategy="delete", max_length=max_length,
        packing=False, padding_free=False, per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=args.global_batch_size // divisor,
        gradient_checkpointing=True, gradient_checkpointing_kwargs='{"use_reentrant": false}',
        ddp_find_unused_parameters=False, dataloader_drop_last=False,
        learning_rate=args.learning_rate, num_train_epochs=args.epochs,
        max_steps=args.max_steps, warmup_ratio=0 if args.max_steps > 0 else 0.03,
        lr_scheduler_type="cosine", max_grad_norm=1, dataset_num_proc=1,
        dataloader_num_workers=0, dataloader_persistent_workers=False,
        eval_strategy="epoch" if "validation" in report["splits"] else "no",
        save_strategy="epoch", save_total_limit=3, logging_steps=1,
        logging_nan_inf_filter=False, prediction_loss_only=True,
        report_to=args.report_to, seed=args.seed, add_version=False,
        output_dir=str(args.output_dir.resolve()))
    if "validation" in report["splits"]:
        values["val_dataset"] = str((args.data_dir / "validation.jsonl").resolve())
    for name in ("model_type", "template"):
        if getattr(args, name) is not None:
            values[name] = getattr(args, name)
    values.update(template_options(args), freeze_vit=args.freeze_vit, freeze_aligner=args.freeze_aligner)
    if args.max_steps > 0:
        values.update(save_strategy="steps", save_steps=args.max_steps,
                      eval_strategy="steps" if "validation" in report["splits"] else "no",
                      eval_steps=args.max_steps)
    if args.revision:
        values["model_revision"] = args.revision
    if args.deepspeed:
        values["deepspeed"] = args.deepspeed
    if sp > 1:
        values.update(sequence_parallel_size=sp, use_logits_to_keep=False)
    if args.resume_from_checkpoint:
        values["resume_from_checkpoint"] = str(args.resume_from_checkpoint.resolve())
    cli = []
    for key, value in values.items():
        cli.extend([f"--{key}", str(value).lower() if isinstance(value, bool) else str(value)])
    return cli, values


def train(args) -> None:
    report = json.loads((args.data_dir / "report.json").read_text(encoding="utf-8"))
    if report.get("format_version") != 2 or not report.get("mask_check_passed"):
        raise ValueError("Run this script's prepare command first")
    for name in ("model_type", "template"):
        prepared_value = report["encoding"][name]
        if getattr(args, name) is not None and getattr(args, name) != prepared_value:
            raise ValueError("Model type/template differ from preparation")
        setattr(args, name, prepared_value)
    if report["encoding"]["template_options"] != template_options(args):
        raise ValueError("Template options differ from preparation")
    for split, info in report["splits"].items():
        if sha256(args.data_dir / f"{split}.jsonl") != info["sha256"]:
            raise ValueError(f"Prepared {split} data changed; prepare again")
    world = int(os.environ.get("WORLD_SIZE", "1"))
    local_world = int(os.environ.get("LOCAL_WORLD_SIZE", str(world)))
    if world < 1 or local_world < 1:
        raise ValueError("Invalid distributed world size")
    cli, values = build_training_args(args, report, world, local_world)
    rank = int(os.environ.get("RANK", "0"))
    if args.dry_run:
        if rank == 0:
            print(json.dumps(dict(world_size=world, swift_arguments=values), indent=2))
        return
    runtime_setup()
    import torch
    cpu_only = not torch.cuda.is_available()
    if cpu_only:
        # Accelerate requires an explicit CPU flag to recognize torchrun CPU DDP.
        values["use_cpu"] = True
        cli.extend(["--use_cpu", "true"])
    template, tokenizer, identity = load_template(args)
    if identity != report["encoding"]:
        raise ValueError("Tokenizer/config/dependency versions differ; prepare with this model/environment")
    check_mask(template, tokenizer)
    del template, tokenizer
    if args.sequence_parallel_size > 1:
        config_path = Path(args.model) / "config.json"
        if config_path.is_file():
            config = json.loads(config_path.read_text())
        else:
            from transformers import AutoConfig
            config = AutoConfig.from_pretrained(args.model, revision=args.revision).to_dict()
        validate_sequence_parallel(config, args.sequence_parallel_size)
        os.environ.setdefault("CELOSS_PARALLEL_SIZE", "2048")
    patch_sampler()
    # Initialize once and share the output check before any rank writes files.
    # Accelerate/Swift reuse this process group when constructing the trainer.
    from accelerate import PartialState
    import torch.distributed as dist
    state = PartialState(cpu=cpu_only)
    config = dict(swift_arguments={k: v for k, v in values.items() if k != "resume_from_checkpoint"},
                  world_size=world, data_report_sha256=sha256(args.data_dir / "report.json"))
    error = [None]
    if state.is_main_process:
        try:
            config_path = args.output_dir / "sft_config.json"
            if args.resume_from_checkpoint:
                checkpoint = args.resume_from_checkpoint.resolve()
                if checkpoint.parent != args.output_dir.resolve() or not (checkpoint / "trainer_state.json").is_file():
                    raise ValueError("Resume requires a checkpoint-* directory inside --output-dir")
                if json.loads(config_path.read_text()) != config:
                    raise ValueError("Resume configuration/data differ from the original run")
            else:
                if args.output_dir.exists() and any(args.output_dir.iterdir()):
                    raise ValueError("Output is nonempty; choose a new output or explicitly resume")
                args.output_dir.mkdir(parents=True, exist_ok=True)
                write_json(config_path, config)
        except (ValueError, OSError) as exc:
            error[0] = str(exc)
    if dist.is_initialized():
        dist.broadcast_object_list(error, src=0)
    if error[0]:
        raise ValueError(error[0])
    from swift.pipelines import sft_main
    # Swift owns model, optimizer, evaluation and checkpoint writes.
    result = sft_main(cli)
    if rank == 0:
        write_json(args.output_dir / "sft_run.json", dict(
            world_size=world, swift_arguments=values, data_report_sha256=sha256(args.data_dir / "report.json"),
            versions={name: version(name) for name in STACK}, result=result))


def positive(value: str) -> int:
    result = int(value)
    if result < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return result


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("prepare", "train"):
        p = sub.add_parser(command)
        p.add_argument("--model", required=True, help="Hugging Face model ID or local directory")
        p.add_argument("--revision", help="Pin the model/tokenizer to a Hub commit")
        p.add_argument("--model-type", help="Optional ms-swift model type; inferred from model metadata")
        p.add_argument("--template", help="Optional ms-swift template; inferred from model metadata")
        p.add_argument("--enable-thinking", action=argparse.BooleanOptionalAction, default=False)
        p.add_argument("--add-non-thinking-prefix", action=argparse.BooleanOptionalAction, default=True)
        p.add_argument("--output-dir", type=Path, required=True)
        p.add_argument("--max-length", type=positive, default=4096 if command == "prepare" else None)
        if command == "prepare":
            p.add_argument("--train-file", type=Path, required=True)
            p.add_argument("--validation-file", type=Path)
            p.add_argument("--drop-overlength", action="store_true",
                           help="Exclude whole overlength examples and record them in the audit")
        else:
            p.add_argument("--data-dir", type=Path, required=True)
            p.add_argument("--epochs", type=positive, default=3)
            p.add_argument("--batch-size", type=positive, default=1)
            p.add_argument("--global-batch-size", type=positive, default=64)
            p.add_argument("--learning-rate", type=float, default=2e-5)
            p.add_argument("--lora-rank", type=positive, default=32)
            p.add_argument("--lora-alpha", type=positive, default=64)
            p.add_argument("--freeze-vit", action=argparse.BooleanOptionalAction, default=True)
            p.add_argument("--freeze-aligner", action=argparse.BooleanOptionalAction, default=True)
            p.add_argument("--max-steps", type=int, default=-1, help="Positive value for a smoke run")
            p.add_argument("--dtype", choices=("bfloat16", "float32"), default="bfloat16")
            p.add_argument("--liger", action=argparse.BooleanOptionalAction, default=True)
            p.add_argument("--deepspeed", help="zero2, zero3, or a DeepSpeed JSON file")
            p.add_argument("--sequence-parallel-size", type=positive, default=1)
            p.add_argument("--resume-from-checkpoint", type=Path)
            p.add_argument("--report-to", choices=("none", "tensorboard"), default="none")
            p.add_argument("--seed", type=int, default=42)
            p.add_argument("--dry-run", action="store_true", help="Check data/batch and print config; no model load")
    args = parser.parse_args(argv)
    if args.command == "train":
        if not math.isfinite(args.learning_rate) or args.learning_rate <= 0:
            parser.error("--learning-rate must be finite and positive")
        if args.max_steps != -1 and args.max_steps < 1:
            parser.error("--max-steps must be -1 or positive")
    return args


def main(argv=None) -> None:
    args = parse_args(argv)
    try:
        (prepare if args.command == "prepare" else train)(args)
    except (ValueError, OSError, ImportError, PackageNotFoundError) as exc:
        raise SystemExit(f"Error: {exc}") from exc


if __name__ == "__main__":
    main()
