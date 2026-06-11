from __future__ import annotations

import argparse
import json
from pathlib import Path

from xiangqi_sifu.config import DEFAULT_START_FEN
from xiangqi_sifu.knowledge.repository import KnowledgeBaseRepository


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    repo = KnowledgeBaseRepository(args.db)
    result = {
        "position": repo.get_position_summary(args.fen),
        "moves": repo.get_position_moves(args.fen, limit=args.limit),
        "examples": repo.get_representative_games(
            args.fen,
            args.move,
            limit=args.example_limit,
        ),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Query the Phase 3A position/move knowledge base.",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=Path("data/processed/xiangqi_sifu_knowledge.db"),
    )
    parser.add_argument("--fen", default=DEFAULT_START_FEN)
    parser.add_argument("--move", help="Optional UCI move filter for representative games.")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--example-limit", type=int, default=5)
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(main())
