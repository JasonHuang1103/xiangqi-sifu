from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from xiangqi_sifu.coach.explanation import ExplanationSample, build_xiangqi_r1_prompt
from xiangqi_sifu.training.lora_config import DEFAULT_BASE_MODEL_ID

SYSTEM_PROMPT = (
    "你是 Xiangqi-Sifu 的象棋复盘教练。你必须基于 Pikafish 引擎给出的事实解释，"
    "不要重新选择最佳走法，也不要编造没有评估分数或 PV 支持的战术结论。"
)


def build_sft_record(
    sample: ExplanationSample,
    *,
    explanation_text: str | None = None,
    base_model: str = DEFAULT_BASE_MODEL_ID,
    record_id: str | None = None,
    source_name: str | None = None,
    game_id: int | None = None,
) -> dict[str, Any]:
    assistant_text = explanation_text or build_conservative_target(sample)
    metadata = {
        "base_model": base_model,
        "ply": sample.ply,
        "move_number": sample.move_number,
        "side": sample.side,
        "severity": sample.severity,
        "fen": sample.fen,
        "played_move": sample.played_move,
        "best_move": sample.best_move,
        "eval_before_cp": sample.eval_before_cp,
        "eval_after_cp": sample.eval_after_cp,
        "eval_delta_cp": sample.eval_delta_cp,
        "eval_loss_cp": sample.eval_loss_cp,
        "pv_best": list(sample.pv_best),
        "pv_played": list(sample.pv_played),
    }
    if source_name is not None:
        metadata["source_name"] = source_name
    if game_id is not None:
        metadata["game_id"] = game_id
    return {
        "id": record_id or f"game-unknown-ply-{sample.ply}",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_xiangqi_r1_prompt(sample)},
            {"role": "assistant", "content": assistant_text},
        ],
        "metadata": metadata,
    }


def build_conservative_target(sample: ExplanationSample) -> str:
    best_move = sample.best_move or "Pikafish 的推荐走法"
    loss = f"{sample.eval_loss_cp} cp" if sample.eval_loss_cp is not None else "明显评估损失"
    pv_hint = _format_pv(sample.pv_best)
    shift = _format_position_shift(sample.eval_before_cp, sample.eval_after_cp)
    return (
        f"原因：实战走法 `{sample.played_move}` 后，{shift}，"
        f"走棋方损失 {loss}。这说明实战线比引擎推荐线更难接受。\n"
        f"更好走法：Pikafish 推荐 `{best_move}`"
        f"{'，参考变化：' + pv_hint if pv_hint else ''}；"
        "这条线保留了更好的局面评估。\n"
        "信心：中。"
    )


def write_jsonl(records: Iterable[dict[str, Any]], path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as output_file:
        for record in records:
            output_file.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as input_file:
        for line in input_file:
            stripped = line.strip()
            if stripped:
                records.append(json.loads(stripped))
    return records


def split_train_validation(
    records: list[dict[str, Any]],
    *,
    validation_count: int,
    balance_by_metadata_key: str | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if validation_count < 0:
        raise ValueError("validation_count must be non-negative")
    validation_indexes = (
        _balanced_validation_indexes(records, validation_count, balance_by_metadata_key)
        if balance_by_metadata_key
        else set(range(min(validation_count, len(records))))
    )
    validation = []
    train = []
    for index, record in enumerate(records):
        if index in validation_indexes:
            validation.append(_with_review_status(record, "pending_human_review"))
        else:
            train.append(record)
    return train, validation


def _format_pv(pv: tuple[str, ...]) -> str:
    return " ".join(pv)


def _format_position_shift(before_cp: int | None, after_cp: int | None) -> str:
    before = _score_label(before_cp)
    after = _score_label(after_cp)
    if before == after:
        return f"局势仍是{after}，但评估明显下降"
    return f"局势从{before}转为{after}"


def _score_label(score: int | None) -> str:
    if score is None:
        return "引擎未给出明确判断"
    if score >= 800:
        return "红方大优"
    if score >= 100:
        return "红方略优"
    if score <= -800:
        return "黑方大优"
    if score <= -100:
        return "黑方略优"
    return "双方接近均势"


def _with_review_status(record: dict[str, Any], status: str) -> dict[str, Any]:
    copied = dict(record)
    metadata = dict(copied.get("metadata", {}))
    metadata["review_status"] = status
    copied["metadata"] = metadata
    return copied


def _balanced_validation_indexes(
    records: list[dict[str, Any]],
    validation_count: int,
    metadata_key: str,
) -> set[int]:
    groups: dict[Any, list[int]] = {}
    for index, record in enumerate(records):
        key = record.get("metadata", {}).get(metadata_key)
        groups.setdefault(key, []).append(index)

    selected: set[int] = set()
    group_indexes = list(groups.values())
    while len(selected) < validation_count:
        added = False
        for indexes in group_indexes:
            if indexes and len(selected) < validation_count:
                selected.add(indexes.pop(0))
                added = True
        if not added:
            break
    return selected
