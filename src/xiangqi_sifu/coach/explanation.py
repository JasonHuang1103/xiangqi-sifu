from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from xiangqi_sifu.coach.mistake_detector import Mistake
from xiangqi_sifu.engine.analysis import AnalysisResult


def explain_mistake(mistake: Mistake) -> str:
    return (
        "Likely reason: the move caused a large engine evaluation loss. "
        "Phase 1 does not infer a deep strategic theme yet."
    )


@dataclass(frozen=True)
class ExplanationSample:
    ply: int
    move_number: int
    side: str
    severity: str
    fen: str
    played_move: str
    best_move: str | None
    pv_best: tuple[str, ...] = field(default_factory=tuple)
    pv_played: tuple[str, ...] = field(default_factory=tuple)
    eval_before_cp: int | None = None
    eval_after_cp: int | None = None
    eval_delta_cp: int | None = None
    eval_loss_cp: int | None = None


@dataclass(frozen=True)
class ExplanationCandidate:
    provider: str
    text: str


@dataclass(frozen=True)
class VerifiedExplanation:
    sample: ExplanationSample
    candidate: ExplanationCandidate
    status: str
    confidence: str
    notes: tuple[str, ...] = field(default_factory=tuple)


class ExplanationProvider(Protocol):
    def explain(self, sample: ExplanationSample) -> ExplanationCandidate:
        ...


class StaticExplanationProvider:
    """Deterministic provider for tests and offline report demos."""

    def explain(self, sample: ExplanationSample) -> ExplanationCandidate:
        best_move = sample.best_move or "the engine move"
        loss = (
            f"{sample.eval_loss_cp} cp"
            if sample.eval_loss_cp is not None
            else "a measurable evaluation loss"
        )
        text = (
            f"Pikafish prefers `{best_move}`. The played move `{sample.played_move}` "
            f"lost {loss}, so the engine continuation should be reviewed before "
            "adding a deeper strategic label."
        )
        return ExplanationCandidate(provider="static", text=text)


def build_verified_explanations(
    analysis: AnalysisResult,
    mistakes: list[Mistake],
    provider: ExplanationProvider,
) -> list[VerifiedExplanation]:
    verified: list[VerifiedExplanation] = []
    for sample in build_explanation_samples(analysis, mistakes):
        candidate = provider.explain(sample)
        verified.append(verify_explanation(sample, candidate))
    return verified


def build_explanation_samples(
    analysis: AnalysisResult,
    mistakes: list[Mistake],
) -> list[ExplanationSample]:
    samples: list[ExplanationSample] = []
    for mistake in mistakes:
        before_index = mistake.ply - 1
        after_index = mistake.ply
        before = (
            analysis.evaluations[before_index]
            if 0 <= before_index < len(analysis.evaluations)
            else None
        )
        after = (
            analysis.evaluations[after_index]
            if 0 <= after_index < len(analysis.evaluations)
            else None
        )
        before_score = before.red_score_cp if before is not None else None
        after_score = after.red_score_cp if after is not None else None
        samples.append(
            ExplanationSample(
                ply=mistake.ply,
                move_number=mistake.move_number,
                side=mistake.side,
                severity=mistake.severity,
                fen=before.fen if before is not None else "",
                played_move=mistake.played_move,
                best_move=mistake.best_move,
                pv_best=before.pv if before is not None else (),
                pv_played=after.pv if after is not None else (),
                eval_before_cp=before_score,
                eval_after_cp=after_score,
                eval_delta_cp=_nullable_delta(before_score, after_score),
                eval_loss_cp=mistake.eval_loss_cp,
            )
        )
    return samples


def build_xiangqi_r1_prompt(sample: ExplanationSample) -> str:
    return (
        "你是一位中国象棋复盘教练。下面的最佳走法已经由 Pikafish 引擎给出，"
        "你的任务是解释为什么 Pikafish 的推荐更好。\n\n"
        "重要约束：不要重新选择最佳走法；不要声称没有由引擎分数或 PV 支持的战术事实。\n\n"
        f"FEN:\n{sample.fen}\n\n"
        f"走棋方: {sample.side}\n"
        f"实战走法: {sample.played_move}\n"
        f"Pikafish 推荐: {sample.best_move or '-'}\n"
        f"错误等级: {sample.severity}\n"
        f"走前评估: {_format_cp(sample.eval_before_cp)}\n"
        f"走后评估: {_format_cp(sample.eval_after_cp)}\n"
        f"评估变化: {_format_cp(sample.eval_delta_cp)}\n"
        f"走棋方损失: {_format_cp(sample.eval_loss_cp)}\n"
        f"PV(best): {_format_pv(sample.pv_best)}\n"
        f"PV(played): {_format_pv(sample.pv_played)}\n\n"
        "请输出三行：\n"
        "原因：用一到两句话解释实战走法的问题。\n"
        "更好走法：说明 Pikafish 推荐如何改善局面。\n"
        "信心：高/中/低。\n"
    )


def verify_explanation(
    sample: ExplanationSample,
    candidate: ExplanationCandidate,
) -> VerifiedExplanation:
    notes: list[str] = []
    text = candidate.text.strip()
    if not text:
        return VerifiedExplanation(sample, candidate, "FAIL", "Low", ("empty explanation",))

    lowered = text.lower()
    if "forced mate" in lowered or "checkmate" in lowered or "将死" in text:
        notes.append("mate claim needs explicit mate-score support")

    if sample.best_move and sample.best_move not in text:
        notes.append("best move not mentioned")

    if any("mate" in note for note in notes):
        status = "FAIL"
        confidence = "Low"
    elif notes:
        status = "NEEDS_REVIEW"
        confidence = "Low"
    else:
        status = "PASS"
        confidence = "Medium"
    return VerifiedExplanation(sample, candidate, status, confidence, tuple(notes))


class LoraExplanationProvider:
    """Lazy local Transformers/PEFT provider for Phase 1.5 adapters."""

    def __init__(
        self,
        model_path: str,
        lora_path: str,
        model_family: str = "qwen3_5_image_text_to_text",
        max_new_tokens: int = 512,
    ) -> None:
        self.model_path = model_path
        self.lora_path = lora_path
        self.model_family = model_family
        self.max_new_tokens = max_new_tokens
        self._model = None
        self._processor = None

    def explain(self, sample: ExplanationSample) -> ExplanationCandidate:
        model, tokenizer = self._load()
        prompt = build_xiangqi_r1_prompt(sample)
        messages = [{"role": "user", "content": prompt}]
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        model_inputs = tokenizer(text=[text], return_tensors="pt").to(model.device)
        generated_ids = model.generate(
            **model_inputs,
            max_new_tokens=self.max_new_tokens,
            do_sample=False,
        )
        generated_ids = [
            output_ids[len(input_ids) :]
            for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]
        response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        return ExplanationCandidate(provider="lora", text=response.strip())

    def _load(self):
        if self._model is not None and self._processor is not None:
            return self._model, self._processor
        try:
            from peft import PeftModel
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise RuntimeError(
                "LoRA explanation inference requires transformers and peft. "
                'Install dependencies with: pip install -e ".[training]"'
            ) from exc

        model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            device_map="auto",
            trust_remote_code=True,
        )
        tokenizer = AutoTokenizer.from_pretrained(self.model_path, trust_remote_code=True)
        self._model = PeftModel.from_pretrained(
            model,
            model_id=self.lora_path,
            adapter_name="default",
        )
        self._model.eval()
        self._processor = tokenizer
        return self._model, self._processor


class XiangqiR1LocalProvider(LoraExplanationProvider):
    """Backward-compatible name for local Xiangqi-R1-style LoRA inference."""


def _nullable_delta(before_score: int | None, after_score: int | None) -> int | None:
    if before_score is None or after_score is None:
        return None
    return after_score - before_score


def _format_cp(score: int | None) -> str:
    if score is None:
        return "-"
    return f"+{score}" if score > 0 else str(score)


def _format_pv(pv: tuple[str, ...]) -> str:
    return " ".join(pv) if pv else "-"
