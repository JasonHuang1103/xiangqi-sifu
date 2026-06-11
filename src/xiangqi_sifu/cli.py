from __future__ import annotations

import argparse
from pathlib import Path

from xiangqi_sifu.coach.explanation import (
    StaticExplanationProvider,
    XiangqiR1LocalProvider,
    build_verified_explanations,
)
from xiangqi_sifu.coach.mistake_detector import MistakeThresholds, detect_mistakes
from xiangqi_sifu.coach.report import render_markdown_report
from xiangqi_sifu.config import load_config
from xiangqi_sifu.database.repository import AnalysisRepository
from xiangqi_sifu.engine.analysis import MockEngine, analyze_game
from xiangqi_sifu.engine.pikafish import PikafishEngine
from xiangqi_sifu.parsers.pgn_parser import PgnParser
from xiangqi_sifu.parsers.simple_move_parser import SimpleMoveParser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "analyze":
        return analyze_command(args)
    parser.print_help()
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="xiangqi-sifu")
    subparsers = parser.add_subparsers(dest="command")

    analyze = subparsers.add_parser("analyze", help="Analyze one Xiangqi game")
    analyze.add_argument("game_path", type=Path)
    analyze.add_argument("--engine", help="Pikafish binary path, or 'mock' for deterministic dry runs")
    analyze.add_argument("--db", type=Path, default=Path("xiangqi_sifu.db"))
    analyze.add_argument("--report", type=Path, help="Optional Markdown report output path")
    analyze.add_argument("--depth", type=int, default=8, help="Search depth for real Pikafish analysis")
    analyze.add_argument("--movetime-ms", type=int, help="Optional movetime per position; overrides depth")
    analyze.add_argument(
        "--explain",
        choices=["none", "mock", "xiangqi-r1"],
        default="none",
        help="Optional explanation provider for mistake summaries",
    )
    analyze.add_argument("--xiangqi-r1-model", help="Base model path/name for local Xiangqi-R1 inference")
    analyze.add_argument("--xiangqi-r1-lora", help="LoRA adapter path for local Xiangqi-R1 inference")
    analyze.add_argument("--inaccuracy-cp", type=int, default=80)
    analyze.add_argument("--mistake-cp", type=int, default=150)
    analyze.add_argument("--blunder-cp", type=int, default=300)
    return parser


def analyze_command(args: argparse.Namespace) -> int:
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
    explanation_provider = _build_explanation_provider(args)
    verified_explanations = (
        build_verified_explanations(analysis, mistakes, explanation_provider)
        if explanation_provider is not None
        else None
    )
    game_id = AnalysisRepository(args.db).save_analysis(
        analysis,
        mistakes,
        verified_explanations=verified_explanations,
    )
    report = render_markdown_report(
        analysis,
        mistakes,
        verified_explanations=verified_explanations,
    )
    report = f"<!-- saved_game_id: {game_id} -->\n\n{report}"

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(report, encoding="utf-8")
    else:
        print(report)
    return 0


def _parse_game(path: Path):
    text = path.read_text(encoding="utf-8")
    if "[Game" in text or "[FEN" in text:
        return PgnParser().parse_text(text)
    return SimpleMoveParser().parse_text(text)


def _build_engine(args: argparse.Namespace):
    config = load_config()
    engine_arg = args.engine or (str(config.engine_path) if config.engine_path else "mock")
    if engine_arg == "mock":
        return MockEngine()
    return PikafishEngine(
        engine_arg,
        depth=args.depth,
        movetime_ms=args.movetime_ms,
    )


def _build_explanation_provider(args: argparse.Namespace):
    if args.explain == "none":
        return None
    if args.explain == "mock":
        return StaticExplanationProvider()
    if args.explain == "xiangqi-r1":
        if not args.xiangqi_r1_model or not args.xiangqi_r1_lora:
            raise SystemExit(
                "--explain xiangqi-r1 requires --xiangqi-r1-model and --xiangqi-r1-lora"
            )
        return XiangqiR1LocalProvider(
            model_path=args.xiangqi_r1_model,
            lora_path=args.xiangqi_r1_lora,
        )
    raise ValueError(f"Unsupported explanation provider: {args.explain!r}")


if __name__ == "__main__":
    raise SystemExit(main())
