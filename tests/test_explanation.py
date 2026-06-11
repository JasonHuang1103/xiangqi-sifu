import sys
import types

from xiangqi_sifu.coach.explanation import (
    ExplanationCandidate,
    LoraExplanationProvider,
    StaticExplanationProvider,
    build_explanation_samples,
    build_xiangqi_r1_prompt,
    verify_explanation,
)
from xiangqi_sifu.coach.mistake_detector import Mistake
from xiangqi_sifu.engine.analysis import AnalysisResult, Evaluation
from xiangqi_sifu.parsers.base import GameRecord, ParsedMove


def test_build_explanation_sample_contains_engine_ground_truth():
    analysis = _sample_analysis()
    mistake = _sample_mistake()

    samples = build_explanation_samples(analysis, [mistake])

    assert len(samples) == 1
    sample = samples[0]
    assert sample.fen == "fen-before"
    assert sample.played_move == "h2e2"
    assert sample.best_move == "h0g2"
    assert sample.pv_best == ("h0g2", "b9c7")
    assert sample.pv_played == ("b9c7", "h9g7")
    assert sample.eval_delta_cp == -200
    assert sample.eval_loss_cp == 200


def test_xiangqi_r1_prompt_asks_for_explanation_not_move_selection():
    sample = build_explanation_samples(_sample_analysis(), [_sample_mistake()])[0]

    prompt = build_xiangqi_r1_prompt(sample)

    assert "fen-before" in prompt
    assert "h2e2" in prompt
    assert "h0g2" in prompt
    assert "不要重新选择最佳走法" in prompt
    assert "为什么 Pikafish 的推荐更好" in prompt


def test_verify_explanation_passes_grounded_candidate():
    sample = build_explanation_samples(_sample_analysis(), [_sample_mistake()])[0]
    candidate = ExplanationCandidate(
        provider="test",
        text="Pikafish prefers h0g2. The played move h2e2 lost 200 cp, so the engine line is more stable.",
    )

    verified = verify_explanation(sample, candidate)

    assert verified.status == "PASS"
    assert verified.confidence == "Medium"


def test_static_provider_returns_verified_explanation_text():
    sample = build_explanation_samples(_sample_analysis(), [_sample_mistake()])[0]

    candidate = StaticExplanationProvider().explain(sample)

    assert candidate.provider == "static"
    assert "h0g2" in candidate.text
    assert "200 cp" in candidate.text


def test_lora_explanation_provider_is_lazy_and_configurable():
    provider = LoraExplanationProvider(
        model_path="Qwen/Qwen3.5-2B",
        lora_path="models/xiangqi-sifu-qwen35-2b-lora",
        model_family="qwen3_5_image_text_to_text",
        max_new_tokens=128,
    )

    assert provider.model_path == "Qwen/Qwen3.5-2B"
    assert provider.lora_path == "models/xiangqi-sifu-qwen35-2b-lora"
    assert provider.model_family == "qwen3_5_image_text_to_text"
    assert provider.max_new_tokens == 128


def test_lora_explanation_provider_uses_text_only_tokenizer(monkeypatch):
    class FakeInputs(dict):
        @property
        def input_ids(self):
            return self["input_ids"]

        def to(self, device):
            self["device"] = device
            return self

    class FakeTokenizer:
        def apply_chat_template(self, messages, *, tokenize, add_generation_prompt):
            assert tokenize is False
            assert add_generation_prompt is True
            return messages[0]["content"]

        def __call__(self, text, *, return_tensors):
            assert return_tensors == "pt"
            return FakeInputs(input_ids=[[1, 2, 3]])

        def batch_decode(self, generated_ids, *, skip_special_tokens):
            assert generated_ids == [[4, 5]]
            assert skip_special_tokens is True
            return ["Pikafish 推荐 h0g2，因为这比实战走法少损失 200 cp。"]

    class FakeModel:
        device = "mps:0"

        def generate(self, **kwargs):
            assert kwargs["max_new_tokens"] == 32
            assert kwargs["do_sample"] is False
            return [[1, 2, 3, 4, 5]]

        def eval(self):
            return None

    class AutoProcessor:
        @staticmethod
        def from_pretrained(*args, **kwargs):
            raise AssertionError("text-only LoRA inference must not load AutoProcessor")

    class AutoModelForImageTextToText:
        @staticmethod
        def from_pretrained(*args, **kwargs):
            return FakeModel()

    class AutoModelForCausalLM:
        @staticmethod
        def from_pretrained(*args, **kwargs):
            return FakeModel()

    class AutoTokenizer:
        @staticmethod
        def from_pretrained(*args, **kwargs):
            return FakeTokenizer()

    class PeftModel:
        @staticmethod
        def from_pretrained(model, *, model_id, adapter_name):
            assert model_id == "adapter"
            assert adapter_name == "default"
            return model

    monkeypatch.setitem(sys.modules, "peft", types.SimpleNamespace(PeftModel=PeftModel))
    monkeypatch.setitem(
        sys.modules,
        "transformers",
        types.SimpleNamespace(
            AutoModelForCausalLM=AutoModelForCausalLM,
            AutoModelForImageTextToText=AutoModelForImageTextToText,
            AutoProcessor=AutoProcessor,
            AutoTokenizer=AutoTokenizer,
        ),
    )
    provider = LoraExplanationProvider(
        model_path="base",
        lora_path="adapter",
        model_family="qwen3_5_image_text_to_text",
        max_new_tokens=32,
    )
    sample = build_explanation_samples(_sample_analysis(), [_sample_mistake()])[0]

    candidate = provider.explain(sample)

    assert candidate.provider == "lora"
    assert "h0g2" in candidate.text


def _sample_analysis() -> AnalysisResult:
    game = GameRecord(
        metadata={"Event": "Sample"},
        starting_fen="fen-before",
        moves=[ParsedMove(iccs="H2-E2", uci="h2e2", move_number=1, side="red")],
    )
    return AnalysisResult(
        game=game,
        positions=[],
        evaluations=[
            Evaluation(
                ply=0,
                fen="fen-before",
                red_score_cp=120,
                best_move="h0g2",
                pv=("h0g2", "b9c7"),
            ),
            Evaluation(
                ply=1,
                fen="fen-after",
                red_score_cp=-80,
                best_move="b9c7",
                pv=("b9c7", "h9g7"),
            ),
        ],
    )


def _sample_mistake() -> Mistake:
    return Mistake(
        ply=1,
        move_number=1,
        side="red",
        played_move="h2e2",
        best_move="h0g2",
        severity="mistake",
        eval_before_cp=120,
        eval_after_cp=-80,
        eval_loss_cp=200,
    )
