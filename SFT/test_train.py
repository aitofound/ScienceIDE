"""Regression checks for supervision, split provenance and distributed coverage."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import train


class SFTTests(unittest.TestCase):
    def row(self):
        return dict(prompt=[dict(role="user", content="Fix the function"),
                            dict(role="assistant", content="Earlier attempt")],
                    completion=[dict(role="assistant", content="Failed action", loss=False),
                                dict(role="user", content="Failure report"),
                                dict(role="assistant", content="Recovery")])

    def test_prompt_and_failed_action_stay_masked(self):
        original = self.row()
        before = copy.deepcopy(original)
        converted = train.normalize_row(original)
        self.assertEqual([m["loss"] for m in converted["messages"]], [False] * 4 + [True])
        self.assertEqual(original, before)

    def test_tool_call_loss_and_schema(self):
        row = self.row()
        row["tools"] = [dict(type="function", function=dict(name="exec", parameters={}))]
        row["completion"].insert(0, dict(role="assistant", content="", loss=False,
            tool_calls=[dict(function=dict(name="exec", arguments='{"input":"hello"}'))]))
        result = train.normalize_row(row)
        action = result["messages"][2]
        self.assertEqual(action["role"], "tool_call")
        self.assertFalse(action["loss"])
        self.assertEqual(json.loads(action["content"])["arguments"], {"input": "hello"})
        row["tools"] = []
        with self.assertRaisesRegex(ValueError, "schema"):
            train.normalize_row(row)

    def test_reject_supervised_observation(self):
        row = self.row()
        row["completion"][1]["loss"] = True
        with self.assertRaisesRegex(ValueError, "Only assistant"):
            train.normalize_row(row)

    def test_reject_empty_supervision(self):
        row = self.row()
        row["completion"][-1]["loss"] = False
        with self.assertRaisesRegex(ValueError, "No supervised"):
            train.normalize_row(row)

    def test_boolean_loss_is_not_a_string(self):
        row = self.row()
        row["completion"][-1]["loss"] = "false"
        with self.assertRaisesRegex(ValueError, "boolean"):
            train.normalize_row(row)

    def test_trailing_observation_is_preserved_without_supervision(self):
        row = self.row()
        row["completion"].append(dict(role="tool_response", content="Final observation"))
        result = train.normalize_row(row)
        self.assertEqual(result["messages"][-1], dict(
            role="tool_response", content="Final observation", loss=False))
        self.assertTrue(result["messages"][-2]["loss"])

    def test_distributed_padding_covers_tail_even_below_world_size(self):
        for count in (1, 3, 7, 64, 65):
            for world in (1, 4, 8):
                padded = train.distributed_order(list(range(count)), world)
                ranks = [padded[r::world] for r in range(world)]
                self.assertEqual(len({len(r) for r in ranks}), 1)
                self.assertEqual(set(padded), set(range(count)))

    def test_sidecar_supports_both_historical_formats(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "train.jsonl"
            audit = path.with_suffix(".audit.jsonl")
            for indexed in (False, True):
                rows = [dict(status="kept", task_name="a"),
                        dict(status="overlength", task_name="skipped"),
                        dict(status="kept", task_name="b")]
                if indexed:
                    rows[0]["output_line"], rows[2]["output_line"] = 1, 2
                audit.write_text("".join(json.dumps(r) + "\n" for r in rows))
                self.assertEqual(train.task_sidecar(path), {1: "a", 2: "b"})

    def args(self, extra=()):
        return train.parse_args(["train", "--model", "/path/to/model",
            "--data-dir", "prepared", "--output-dir", "outputs/test", *extra])

    def report(self):
        return dict(max_length=4096, splits={"train": dict(max_tokens=4000)})

    def test_batch_math_uses_data_parallel_width(self):
        args = self.args(["--sequence-parallel-size", "4", "--deepspeed", "zero3"])
        _, values = train.build_training_args(args, self.report(), 32, 8)
        self.assertEqual(values["gradient_accumulation_steps"], 8)
        self.assertFalse(values["use_logits_to_keep"])
        self.assertEqual(values["enable_thinking"], args.enable_thinking)

    def test_invalid_batch_and_missing_parallel_backend(self):
        for extra in (["--global-batch-size", "7"], ["--sequence-parallel-size", "4"]):
            with self.assertRaises(ValueError):
                train.build_training_args(self.args(extra), self.report(), 8, 8)

    def test_model_type_and_template_are_optional_and_unrestricted(self):
        args = self.args()
        self.assertIsNone(args.model_type)
        self.assertIsNone(args.template)
        cli, values = train.build_training_args(args, self.report(), 1, 1)
        self.assertNotIn("--model_type", cli)
        self.assertNotIn("--template", cli)
        args = self.args(["--model-type", "custom_architecture", "--template", "custom_chat"])
        _, values = train.build_training_args(args, self.report(), 1, 1)
        self.assertEqual(values["model_type"], "custom_architecture")
        self.assertEqual(values["template"], "custom_chat")

    def test_template_and_freeze_options_are_explicit(self):
        args = self.args(["--enable-thinking", "--no-add-non-thinking-prefix",
                          "--no-freeze-vit", "--no-freeze-aligner"])
        _, values = train.build_training_args(args, self.report(), 1, 1)
        for key, value in train.template_options(args).items():
            self.assertEqual(values[key], value)
        self.assertTrue(values["enable_thinking"])
        self.assertFalse(values["add_non_thinking_prefix"])
        self.assertFalse(values["freeze_vit"])
        self.assertFalse(values["freeze_aligner"])

    def test_sequence_parallel_checks_capabilities(self):
        train.validate_sequence_parallel({"text_config": {"num_key_value_heads": 8,
            "layer_types": ["full_attention", "sliding_attention"]}}, 4)
        for config in ({"num_key_value_heads": 3}, {"num_key_value_heads": 8,
                "layer_types": ["full_attention", "linear_attention"]}):
            with self.assertRaises(ValueError):
                train.validate_sequence_parallel(config, 4)

    def test_shorter_context_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "shorter"):
            train.build_training_args(self.args(["--max-length", "2048"]), self.report(), 1, 1)

    def test_smoke_ends_with_checkpoint_and_optional_eval(self):
        _, values = train.build_training_args(self.args(["--max-steps", "2"]), self.report(), 1, 1)
        self.assertEqual(values["save_steps"], 2)
        self.assertEqual(values["eval_strategy"], "no")
        self.assertEqual(values["split_dataset_ratio"], 0)

    def test_examples_have_disjoint_tasks(self):
        base = Path(__file__).parent / "sample_data"
        tasks = []
        for split in ("train", "validation"):
            rows = list(train.read_jsonl(base / f"{split}.jsonl"))
            tasks.append({r["task_name"] for _, r in rows})
            for _, row in rows:
                train.normalize_row(row)
        self.assertFalse(tasks[0] & tasks[1])

    def test_prepare_rejects_overlap_before_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.jsonl"
            source.write_text(json.dumps(dict(task_name="shared", **self.row())) + "\n")
            args = train.parse_args(["prepare", "--model", "unused", "--train-file", str(source),
                "--validation-file", str(source), "--output-dir", str(root / "prepared")])
            with patch.object(train, "runtime_setup"), patch.object(train, "check_mask"), \
                    patch.object(train, "load_template", return_value=(None, None, {})):
                with self.assertRaisesRegex(ValueError, "overlap"):
                    train.prepare(args)
            self.assertFalse(args.output_dir.exists())

    def test_prepare_never_silently_truncates(self):
        class Template:
            def encode(self, row):
                length = 20 if "long" in row["messages"][-1]["content"] else 5
                return dict(input_ids=[1] * length, labels=[-100] * (length - 2) + [1, 2])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.jsonl"
            rows = [dict(task_name=name, messages=[dict(role="user", content="input"),
                    dict(role="assistant", content=name)]) for name in ("short", "long")]
            source.write_text("".join(json.dumps(r) + "\n" for r in rows))
            for drop in (False, True):
                args = train.parse_args(["prepare", "--model", "unused", "--train-file", str(source),
                    "--max-length", "10", "--output-dir", str(root / str(drop))] +
                    (["--drop-overlength"] if drop else []))
                with patch.object(train, "runtime_setup"), patch.object(train, "check_mask"), \
                        patch.object(train, "load_template", return_value=(Template(), None, {})), \
                        patch("builtins.print"):
                    if drop:
                        train.prepare(args)
                        report = json.loads((args.output_dir / "report.json").read_text())
                        self.assertEqual(report["splits"]["train"]["examples"], 1)
                        self.assertEqual(report["splits"]["train"]["excluded_overlength"], 1)
                    else:
                        with self.assertRaisesRegex(ValueError, "tokens"):
                            train.prepare(args)
                        self.assertFalse((args.output_dir / "report.json").exists())


if __name__ == "__main__":
    unittest.main()
