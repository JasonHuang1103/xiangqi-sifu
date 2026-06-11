from __future__ import annotations

from statistics import mean
from typing import Any

from xiangqi_sifu.coach.explanation import (
    ExplanationCandidate,
    ExplanationSample,
    verify_explanation,
)


REQUIRED_PREFIXES = ("原因：", "更好走法：", "信心：")


def evaluate_explanation_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    results = [evaluate_explanation_record(record) for record in records]
    return {
        "record_count": len(results),
        "pass_count": sum(1 for result in results if result["status"] == "PASS"),
        "needs_review_count": sum(
            1 for result in results if result["status"] == "NEEDS_REVIEW"
        ),
        "fail_count": sum(1 for result in results if result["status"] == "FAIL"),
        "format_validity_rate": _rate(results, "format_valid"),
        "best_move_consistency_rate": _rate(results, "best_move_consistent"),
        "eval_loss_consistency_rate": _rate(results, "eval_loss_consistent"),
        "records": results,
    }


def evaluate_explanation_record(record: dict[str, Any]) -> dict[str, Any]:
    sample = _sample_from_record(record)
    text = _assistant_text(record)
    candidate = ExplanationCandidate(provider="benchmark", text=text)
    verified = verify_explanation(sample, candidate)
    return {
        "id": record.get("id"),
        "status": verified.status,
        "confidence": verified.confidence,
        "format_valid": _has_required_format(text),
        "best_move_consistent": _mentions_value(text, sample.best_move),
        "eval_loss_consistent": _mentions_value(
            text,
            f"{sample.eval_loss_cp} cp" if sample.eval_loss_cp is not None else None,
        ),
        "notes": list(verified.notes),
    }


def _sample_from_record(record: dict[str, Any]) -> ExplanationSample:
    metadata = record.get("metadata", {})
    return ExplanationSample(
        ply=int(metadata.get("ply", 0)),
        move_number=int(metadata.get("move_number", 0)),
        side=str(metadata.get("side", "")),
        severity=str(metadata.get("severity", "")),
        fen=str(metadata.get("fen", "")),
        played_move=str(metadata.get("played_move", "")),
        best_move=metadata.get("best_move"),
        pv_best=tuple(metadata.get("pv_best", ())),
        pv_played=tuple(metadata.get("pv_played", ())),
        eval_before_cp=metadata.get("eval_before_cp"),
        eval_after_cp=metadata.get("eval_after_cp"),
        eval_delta_cp=metadata.get("eval_delta_cp"),
        eval_loss_cp=metadata.get("eval_loss_cp"),
    )


def _assistant_text(record: dict[str, Any]) -> str:
    for message in reversed(record.get("messages", [])):
        if message.get("role") == "assistant":
            return str(message.get("content", ""))
    return ""


def _has_required_format(text: str) -> bool:
    return all(prefix in text for prefix in REQUIRED_PREFIXES)


def _mentions_value(text: str, value: str | None) -> bool:
    return bool(value) and value in text


def _rate(results: list[dict[str, Any]], key: str) -> float:
    if not results:
        return 0.0
    return mean(1.0 if result[key] else 0.0 for result in results)
