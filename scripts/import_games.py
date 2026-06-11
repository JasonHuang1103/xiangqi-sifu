from __future__ import annotations

import argparse
from pathlib import Path

from xiangqi_sifu.parsers.wxf_bulk_parser import write_games_jsonl


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Parse a Xiangqi .pgns corpus into one JSONL record per game.")
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("WXF-41743games.pgns"),
        help="Source .pgns file containing many games.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/processed/wxf_41743games"),
        help="Directory for games.jsonl and manifest.json.",
    )
    parser.add_argument("--limit", type=int, help="Optional maximum number of games to export.")
    args = parser.parse_args(argv)

    summary = write_games_jsonl(args.source, args.output_dir, limit=args.limit)
    print(f"Parsed {summary.game_count} games")
    print(f"Wrote {summary.output_path}")
    print(f"Wrote {summary.manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
