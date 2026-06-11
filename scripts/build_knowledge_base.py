from __future__ import annotations

import argparse
from pathlib import Path

from xiangqi_sifu.knowledge.builder import build_knowledge_base


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    summary = build_knowledge_base(
        args.games_jsonl,
        args.db,
        corpus_name=args.corpus_name,
        max_games=args.max_games,
        max_examples_per_move=args.max_examples_per_move,
    )
    print(f"Games seen: {summary.games_seen}")
    print(f"Games indexed: {summary.games_indexed}")
    print(f"Games skipped: {summary.games_skipped}")
    print(f"Positions indexed: {summary.positions_indexed}")
    print(f"Wrote knowledge base: {args.db}")
    return 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the Phase 3A position/move knowledge base from normalized game JSONL.",
    )
    parser.add_argument(
        "games_jsonl",
        nargs="+",
        type=Path,
        help="One or more processed games.jsonl files.",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=Path("data/processed/xiangqi_sifu_knowledge.db"),
        help="Output SQLite knowledge-base path.",
    )
    parser.add_argument("--corpus-name", default="public")
    parser.add_argument("--max-games", type=int, help="Optional build limit for smoke tests.")
    parser.add_argument("--max-examples-per-move", type=int, default=3)
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(main())
