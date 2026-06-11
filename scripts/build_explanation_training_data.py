from __future__ import annotations

import argparse
from pathlib import Path

from xiangqi_sifu.cli import _build_engine, _parse_game
from xiangqi_sifu.coach.explanation import build_explanation_samples
from xiangqi_sifu.coach.mistake_detector import MistakeThresholds, detect_mistakes
from xiangqi_sifu.engine.analysis import analyze_game
from xiangqi_sifu.training.dataset import build_sft_record, write_jsonl
from xiangqi_sifu.training.lora_config import DEFAULT_BASE_MODEL_ID


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    game = _parse_game(args.game_path)
    engine = _build_engine(args)
    try:
        analysis = analyze_game(game, engine)
    finally:
        close = getattr(engine, "close", None)
        if close is not None:
            close()

    mistakes = detect_mistakes(
        game.moves,
        analysis.evaluations,
        MistakeThresholds(
            inaccuracy_cp=args.inaccuracy_cp,
            mistake_cp=args.mistake_cp,
            blunder_cp=args.blunder_cp,
        ),
    )
    samples = build_explanation_samples(analysis, mistakes)
    if args.limit is not None:
        samples = samples[: args.limit]
    records = [
        build_sft_record(sample, base_model=args.base_model)
        for sample in samples
    ]
    write_jsonl(records, args.output)
    print(f"Wrote {len(records)} explanation training records to {args.output}")
    return 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build Xiangqi-Sifu explanation SFT JSONL from one analyzed game.",
    )
    parser.add_argument("game_path", type=Path)
    parser.add_argument("--output", type=Path, default=Path("data/training/explanations/train.jsonl"))
    parser.add_argument("--base-model", default=DEFAULT_BASE_MODEL_ID)
    parser.add_argument("--engine", default="mock")
    parser.add_argument("--depth", type=int, default=8)
    parser.add_argument("--movetime-ms", type=int)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--inaccuracy-cp", type=int, default=80)
    parser.add_argument("--mistake-cp", type=int, default=150)
    parser.add_argument("--blunder-cp", type=int, default=300)
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(main())
