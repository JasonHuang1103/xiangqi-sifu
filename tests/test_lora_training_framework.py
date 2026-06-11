import json
import types

from scripts.train_lora import (
    _run_training,
    main as train_lora_main,
    should_use_bf16_training,
)
from scripts.build_explanation_training_corpus import main as build_corpus_main
from scripts.evaluate_explanation_benchmark import main as evaluate_benchmark_main
from scripts.export_lora_adapter import main as export_adapter_main
from scripts.split_explanation_training_data import main as split_training_main
from xiangqi_sifu.coach.explanation import ExplanationSample
from xiangqi_sifu.training.evaluation import evaluate_explanation_records
from xiangqi_sifu.training.dataset import (
    build_conservative_target,
    build_sft_record,
    read_jsonl,
    split_train_validation,
    write_jsonl,
)
from xiangqi_sifu.training.lora_config import (
    DEFAULT_BASE_MODEL_ID,
    LoraTrainingConfig,
)
from xiangqi_sifu.training.sources import DEFAULT_TRAINING_PGNS


def test_prompt_template_file_documents_training_contract():
    text = open("prompts/explanation_sft_prompt.md", encoding="utf-8").read()

    assert "Pikafish" in text
    assert "不要重新选择最佳走法" in text
    assert "FEN" in text
    assert "PV(best)" in text
    assert "信心" in text
    assert "复盘重点" not in text


def test_default_training_sources_are_the_two_raw_pgns():
    assert [path.as_posix() for path in DEFAULT_TRAINING_PGNS] == [
        "data/raw/WXF-41743games.pgns",
        "data/raw/dpxq-99813games.pgns",
    ]


def test_default_lora_config_targets_qwen35_2b_without_training_enabled():
    config = LoraTrainingConfig()

    assert DEFAULT_BASE_MODEL_ID == "Qwen/Qwen3.5-2B"
    assert config.base_model_id == "Qwen/Qwen3.5-2B"
    assert config.model_family == "qwen3_5_image_text_to_text"
    assert config.target_modules == "all-linear"
    assert config.output_dir.as_posix() == "models/xiangqi-sifu-qwen35-2b-lora"


def test_lora_config_loads_from_json(tmp_path):
    path = tmp_path / "lora.json"
    path.write_text(
        json.dumps(
            {
                "base_model_id": "Qwen/Qwen3.5-2B",
                "dataset_path": "data/training/explanations/train.jsonl",
                "num_train_epochs": 2,
                "learning_rate": 0.0002,
            }
        ),
        encoding="utf-8",
    )

    config = LoraTrainingConfig.from_json_file(path)

    assert config.dataset_path.as_posix() == "data/training/explanations/train.jsonl"
    assert config.num_train_epochs == 2
    assert config.learning_rate == 0.0002


def test_build_sft_record_uses_engine_ground_truth_and_cautious_target():
    record = build_sft_record(_sample())

    assert record["messages"][0]["role"] == "system"
    assert record["messages"][1]["role"] == "user"
    assert record["messages"][2]["role"] == "assistant"
    assert "fen-before" in record["messages"][1]["content"]
    assert "h0g2" in record["messages"][1]["content"]
    assert "实战走法" in record["messages"][1]["content"]
    assert "Pikafish 推荐 `h0g2`" in record["messages"][2]["content"]
    assert "200 cp" in record["messages"][2]["content"]
    assert record["metadata"]["base_model"] == "Qwen/Qwen3.5-2B"
    assert record["metadata"]["severity"] == "mistake"


def test_conservative_target_is_more_than_numeric_restatement():
    target = build_conservative_target(_sample())

    assert "局势从红方略优转为双方接近均势" in target
    assert "参考变化：h0g2 b9c7" in target
    assert "复盘重点" not in target
    assert "不要只记住分数" not in target


def test_build_sft_record_can_include_corpus_source_metadata():
    record = build_sft_record(
        _sample(),
        record_id="wxf-000001-ply-17",
        source_name="WXF-41743games.pgns",
        game_id=1,
    )

    assert record["id"] == "wxf-000001-ply-17"
    assert record["metadata"]["source_name"] == "WXF-41743games.pgns"
    assert record["metadata"]["game_id"] == 1


def test_training_jsonl_roundtrip(tmp_path):
    output = tmp_path / "train.jsonl"
    record = build_sft_record(_sample())

    write_jsonl([record], output)

    assert read_jsonl(output) == [record]


def test_split_train_validation_is_deterministic():
    records = [
        build_sft_record(_sample(), record_id=f"sample-{index}")
        for index in range(5)
    ]

    train, validation = split_train_validation(records, validation_count=2)

    assert [record["id"] for record in validation] == ["sample-0", "sample-1"]
    assert [record["id"] for record in train] == ["sample-2", "sample-3", "sample-4"]


def test_split_train_validation_can_balance_by_source():
    records = [
        build_sft_record(_sample(), record_id="a-0", source_name="a.pgns"),
        build_sft_record(_sample(), record_id="a-1", source_name="a.pgns"),
        build_sft_record(_sample(), record_id="b-0", source_name="b.pgns"),
        build_sft_record(_sample(), record_id="b-1", source_name="b.pgns"),
    ]

    train, validation = split_train_validation(
        records,
        validation_count=2,
        balance_by_metadata_key="source_name",
    )

    assert [record["id"] for record in validation] == ["a-0", "b-0"]
    assert [record["id"] for record in train] == ["a-1", "b-1"]


def test_split_training_script_writes_review_validation_set(tmp_path):
    source = tmp_path / "records.jsonl"
    train = tmp_path / "train.jsonl"
    validation = tmp_path / "validation.jsonl"
    records = [
        build_sft_record(_sample(), record_id=f"sample-{index}")
        for index in range(3)
    ]
    write_jsonl(records, source)

    exit_code = split_training_main(
        [
            "--source",
            str(source),
            "--train-output",
            str(train),
            "--validation-output",
            str(validation),
            "--validation-count",
            "1",
        ]
    )

    assert exit_code == 0
    assert len(read_jsonl(train)) == 2
    assert len(read_jsonl(validation)) == 1
    assert read_jsonl(validation)[0]["metadata"]["review_status"] == "pending_human_review"


def test_train_lora_dry_run_validates_dataset_without_starting_training(tmp_path, capsys):
    dataset_path = tmp_path / "train.jsonl"
    write_jsonl([build_sft_record(_sample())], dataset_path)

    exit_code = train_lora_main(["--dataset", str(dataset_path), "--dry-run"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Qwen/Qwen3.5-2B" in captured.out
    assert "Training will not start" in captured.out


def test_train_lora_dry_run_accepts_bounded_max_steps(tmp_path, capsys):
    dataset_path = tmp_path / "train.jsonl"
    write_jsonl([build_sft_record(_sample())], dataset_path)

    exit_code = train_lora_main(
        ["--dataset", str(dataset_path), "--max-steps", "1", "--dry-run"]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert '"max_steps": 1' in captured.out


def test_bf16_training_is_disabled_without_accelerator_support():
    class FakeTorch:
        class cuda:
            @staticmethod
            def is_available():
                return False

        class backends:
            class mps:
                @staticmethod
                def is_available():
                    return False

    assert should_use_bf16_training(FakeTorch, requested=True) is False


def test_train_lora_uses_text_only_model_loading(monkeypatch, tmp_path):
    class FakeDataset:
        column_names = ["messages"]

        def __init__(self, records):
            self.records = records

        @classmethod
        def from_list(cls, records):
            return cls(records)

        def map(self, func, *, batched, remove_columns):
            assert batched is False
            assert remove_columns == self.column_names
            return [func(record) for record in self.records]

    class FakeTokenizer:
        eos_token = "<eos>"
        eos_token_id = 1
        pad_token = None
        pad_token_id = None

        def apply_chat_template(self, messages, *, tokenize, add_generation_prompt):
            assert tokenize is False
            assert add_generation_prompt is True
            return messages[0]["content"][0]["text"]

        def __call__(self, text, *, add_special_tokens):
            assert add_special_tokens is False
            return {"input_ids": [2, 3], "attention_mask": [1, 1]}

        def save_pretrained(self, output_dir):
            (tmp_path / "tokenizer_saved").write_text(str(output_dir), encoding="utf-8")

    class FakeModel:
        config = types.SimpleNamespace(use_cache=True)

        def enable_input_require_grads(self):
            return None

        def save_pretrained(self, output_dir):
            (tmp_path / "model_saved").write_text(str(output_dir), encoding="utf-8")

    class AutoProcessor:
        @staticmethod
        def from_pretrained(*args, **kwargs):
            raise AssertionError("text-only Qwen training must not load AutoProcessor")

    class AutoTokenizer:
        @staticmethod
        def from_pretrained(*args, **kwargs):
            return FakeTokenizer()

    class AutoModelForCausalLM:
        @staticmethod
        def from_pretrained(*args, **kwargs):
            return FakeModel()

    class FakeTrainer:
        def __init__(self, *, model, args, train_dataset, data_collator):
            self.model = model

        def train(self):
            return None

    fake_torch = types.SimpleNamespace(
        bfloat16="bf16",
        float16="fp16",
        cuda=types.SimpleNamespace(is_available=lambda: False),
        backends=types.SimpleNamespace(
            mps=types.SimpleNamespace(is_available=lambda: False)
        ),
    )
    fake_transformers = types.SimpleNamespace(
        AutoModelForCausalLM=AutoModelForCausalLM,
        AutoProcessor=AutoProcessor,
        AutoTokenizer=AutoTokenizer,
        Trainer=FakeTrainer,
        TrainingArguments=lambda **kwargs: kwargs,
        default_data_collator=object(),
    )
    fake_peft = types.SimpleNamespace(
        LoraConfig=lambda **kwargs: kwargs,
        TaskType=types.SimpleNamespace(CAUSAL_LM="CAUSAL_LM"),
        get_peft_model=lambda model, config: model,
    )
    fake_datasets = types.SimpleNamespace(Dataset=FakeDataset)
    monkeypatch.setitem(__import__("sys").modules, "torch", fake_torch)
    monkeypatch.setitem(__import__("sys").modules, "transformers", fake_transformers)
    monkeypatch.setitem(__import__("sys").modules, "peft", fake_peft)
    monkeypatch.setitem(__import__("sys").modules, "datasets", fake_datasets)

    _run_training(
        LoraTrainingConfig(
            base_model_id="models/base/Qwen3.5-2B",
            output_dir=tmp_path / "adapter",
            max_length=8,
            max_steps=1,
        ),
        [build_sft_record(_sample())],
    )

    assert (tmp_path / "model_saved").exists()
    assert (tmp_path / "tokenizer_saved").exists()


def test_train_lora_does_not_use_device_map_auto_on_mps(monkeypatch, tmp_path):
    captured_model_kwargs = {}

    class FakeDataset:
        column_names = ["messages"]

        @classmethod
        def from_list(cls, records):
            return cls()

        def map(self, func, *, batched, remove_columns):
            return [func(build_sft_record(_sample()))]

    class FakeTokenizer:
        eos_token = "<eos>"
        eos_token_id = 1
        pad_token = None
        pad_token_id = None

        def apply_chat_template(self, messages, *, tokenize, add_generation_prompt):
            return messages[0]["content"][0]["text"]

        def __call__(self, text, *, add_special_tokens):
            return {"input_ids": [2, 3], "attention_mask": [1, 1]}

        def save_pretrained(self, output_dir):
            return None

    class FakeModel:
        config = types.SimpleNamespace(use_cache=True)

        def enable_input_require_grads(self):
            return None

        def save_pretrained(self, output_dir):
            return None

    class AutoTokenizer:
        @staticmethod
        def from_pretrained(*args, **kwargs):
            return FakeTokenizer()

    class AutoModelForCausalLM:
        @staticmethod
        def from_pretrained(*args, **kwargs):
            captured_model_kwargs.update(kwargs)
            return FakeModel()

    class FakeTrainer:
        def __init__(self, *, model, args, train_dataset, data_collator):
            self.model = model

        def train(self):
            return None

    fake_torch = types.SimpleNamespace(
        bfloat16="bf16",
        float16="fp16",
        cuda=types.SimpleNamespace(is_available=lambda: False),
        backends=types.SimpleNamespace(
            mps=types.SimpleNamespace(is_available=lambda: True)
        ),
    )
    fake_transformers = types.SimpleNamespace(
        AutoModelForCausalLM=AutoModelForCausalLM,
        AutoTokenizer=AutoTokenizer,
        Trainer=FakeTrainer,
        TrainingArguments=lambda **kwargs: kwargs,
        default_data_collator=object(),
    )
    fake_peft = types.SimpleNamespace(
        LoraConfig=lambda **kwargs: kwargs,
        TaskType=types.SimpleNamespace(CAUSAL_LM="CAUSAL_LM"),
        get_peft_model=lambda model, config: model,
    )
    monkeypatch.setitem(__import__("sys").modules, "torch", fake_torch)
    monkeypatch.setitem(__import__("sys").modules, "transformers", fake_transformers)
    monkeypatch.setitem(__import__("sys").modules, "peft", fake_peft)
    monkeypatch.setitem(
        __import__("sys").modules, "datasets", types.SimpleNamespace(Dataset=FakeDataset)
    )

    _run_training(
        LoraTrainingConfig(
            base_model_id="models/base/Qwen3.5-2B",
            output_dir=tmp_path / "adapter",
            max_length=8,
            max_steps=1,
        ),
        [build_sft_record(_sample())],
    )

    assert captured_model_kwargs.get("device_map") is None


def test_evaluate_explanation_records_scores_grounded_targets():
    summary = evaluate_explanation_records([build_sft_record(_sample())])

    assert summary["record_count"] == 1
    assert summary["pass_count"] == 1
    assert summary["format_validity_rate"] == 1.0
    assert summary["best_move_consistency_rate"] == 1.0
    assert summary["eval_loss_consistency_rate"] == 1.0


def test_evaluate_benchmark_script_writes_summary_json(tmp_path):
    dataset_path = tmp_path / "validation.jsonl"
    output_path = tmp_path / "benchmark.json"
    write_jsonl([build_sft_record(_sample())], dataset_path)

    exit_code = evaluate_benchmark_main(
        ["--dataset", str(dataset_path), "--output", str(output_path)]
    )

    result = json.loads(output_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert result["summary"]["record_count"] == 1
    assert result["records"][0]["status"] == "PASS"


def test_export_lora_adapter_requires_adapter_checkpoint(tmp_path):
    adapter_dir = tmp_path / "adapter"
    adapter_dir.mkdir()
    (adapter_dir / "adapter_config.json").write_text("{}", encoding="utf-8")

    exit_code = export_adapter_main(["--adapter-dir", str(adapter_dir)])

    assert exit_code == 2


def test_export_lora_adapter_writes_manifest_and_model_card(tmp_path):
    adapter_dir = tmp_path / "adapter"
    adapter_dir.mkdir()
    (adapter_dir / "adapter_config.json").write_text("{}", encoding="utf-8")
    (adapter_dir / "adapter_model.safetensors").write_bytes(b"fake")

    exit_code = export_adapter_main(
        [
            "--adapter-dir",
            str(adapter_dir),
            "--base-model",
            "Qwen/Qwen3.5-2B",
            "--training-records",
            "450",
            "--validation-records",
            "50",
        ]
    )

    manifest = json.loads(
        (adapter_dir / "xiangqi_sifu_adapter_manifest.json").read_text(encoding="utf-8")
    )
    assert exit_code == 0
    assert manifest["base_model_id"] == "Qwen/Qwen3.5-2B"
    assert manifest["adapter_type"] == "peft_lora"
    assert manifest["compatible_provider"] == "LoraExplanationProvider"
    assert (adapter_dir / "README.md").exists()


def test_build_training_corpus_dry_run_uses_both_raw_pgns(capsys):
    exit_code = build_corpus_main(["--dry-run"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "data/raw/WXF-41743games.pgns" in captured.out
    assert "data/raw/dpxq-99813games.pgns" in captured.out
    assert "No engine analysis started" in captured.out


def test_build_training_corpus_accepts_max_records_per_source(capsys):
    exit_code = build_corpus_main(["--dry-run", "--max-records-per-source", "250"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Max records per source: 250" in captured.out


def _sample() -> ExplanationSample:
    return ExplanationSample(
        ply=17,
        move_number=9,
        side="red",
        severity="mistake",
        fen="fen-before",
        played_move="h2e2",
        best_move="h0g2",
        pv_best=("h0g2", "b9c7"),
        pv_played=("b9c7", "h9g7"),
        eval_before_cp=120,
        eval_after_cp=-80,
        eval_delta_cp=-200,
        eval_loss_cp=200,
    )
