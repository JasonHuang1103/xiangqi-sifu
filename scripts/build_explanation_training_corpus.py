from __future__ import annotations

import argparse
import json
from pathlib import Path

from xiangqi_sifu.cli import _build_engine
from xiangqi_sifu.coach.explanation import build_explanation_samples
from xiangqi_sifu.coach.mistake_detector import MistakeThresholds, detect_mistakes
from xiangqi_sifu.engine.analysis import analyze_game
from xiangqi_sifu.parsers.pgn_parser import PgnParser
from xiangqi_sifu.parsers.wxf_bulk_parser import iter_game_texts
from xiangqi_sifu.training.dataset import build_sft_record
from xiangqi_sifu.training.lora_config import DEFAULT_BASE_MODEL_ID
from xiangqi_sifu.training.sources import DEFAULT_TRAINING_PGNS


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    sources = tuple(args.source or DEFAULT_TRAINING_PGNS)
    if args.dry_run:
        _print_dry_run(sources, args)
        return 0

    engine = _build_engine(args)
    parser = PgnParser()
    games_seen = 0
    records_written = 0
    errors = 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with args.output.open("w", encoding="utf-8") as output_file:
            for source in sources:
                source_records_written = 0
                for source_game_id, raw_game in enumerate(iter_game_texts(source), start=1):
                    if args.max_games_per_source is not None and source_game_id > args.max_games_per_source:
                        break
                    if args.max_records is not None and records_written >= args.max_records:
                        break
                    if (
                        args.max_records_per_source is not None
                        and source_records_written >= args.max_records_per_source
                    ):
                        break
                    games_seen += 1
                    try:
                        game = parser.parse_text(raw_game)
                        analysis = analyze_game(game, engine)
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
                    except Exception:
                        errors += 1
                        if not args.skip_errors:
                            raise
                        continue

                    for sample in samples:
                        if args.max_records is not None and records_written >= args.max_records:
                            break
                        if (
                            args.max_records_per_source is not None
                            and source_records_written >= args.max_records_per_source
                        ):
                            break
                        records_written += 1
                        source_records_written += 1
                        record = build_sft_record(
                            sample,
                            base_model=args.base_model,
                            record_id=_record_id(source, source_game_id, sample.ply),
                            source_name=source.name,
                            game_id=source_game_id,
                        )
                        output_file.write(json.dumps(record, ensure_ascii=False) + "\n")
    finally:
        close = getattr(engine, "close", None)
        if close is not None:
            close()

    print(f"Sources: {len(sources)}")
    print(f"Games analyzed: {games_seen}")
    print(f"Training records written: {records_written}")
    print(f"Errors skipped: {errors}")
    print(f"Wrote {args.output}")
    return 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build explanation SFT JSONL from the raw Xiangqi .pgns databases.",
    )
    parser.add_argument(
        "--source",
        type=Path,
        action="append",
        help="Raw .pgns source. Defaults to both files in data/raw.",
    )
    parser.add_argument("--output", type=Path, default=Path("data/training/explanations/train.jsonl"))
    parser.add_argument("--base-model", default=DEFAULT_BASE_MODEL_ID)
    parser.add_argument("--engine", default="mock")
    parser.add_argument("--depth", type=int, default=8)
    parser.add_argument("--movetime-ms", type=int)
    parser.add_argument("--max-games-per-source", type=int)
    parser.add_argument("--max-records", type=int)
    parser.add_argument("--max-records-per-source", type=int)
    parser.add_argument("--skip-errors", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--inaccuracy-cp", type=int, default=80)
    parser.add_argument("--mistake-cp", type=int, default=150)
    parser.add_argument("--blunder-cp", type=int, default=300)
    return parser.parse_args(argv)


def _print_dry_run(sources: tuple[Path, ...], args: argparse.Namespace) -> None:
    print("Training corpus sources:")
    for source in sources:
        print(f"- {source}")
    print(f"Output: {args.output}")
    print(f"Base model: {args.base_model}")
    if args.max_records_per_source is not None:
        print(f"Max records per source: {args.max_records_per_source}")
    print("No engine analysis started. No training data written.")


def _record_id(source: Path, game_id: int, ply: int) -> str:
    return f"{source.stem}-g{game_id:06d}-ply-{ply}"


if __name__ == "__main__":
    raise SystemExit(main())
