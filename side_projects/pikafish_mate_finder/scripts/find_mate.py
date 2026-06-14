from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from side_projects.pikafish_mate_finder.mate_finder.mate_search import find_forced_mate
    from side_projects.pikafish_mate_finder.mate_finder.report import (
        result_to_dict,
        write_json,
        write_markdown,
    )
    from side_projects.pikafish_mate_finder.mate_finder.vision import (
        BoardRectangle,
        screenshot_to_fen,
    )
except ImportError:  # pragma: no cover - supports moving this project out of the repo.
    from mate_finder.mate_search import find_forced_mate
    from mate_finder.report import result_to_dict, write_json, write_markdown
    from mate_finder.vision import BoardRectangle, screenshot_to_fen


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    fen, confidence, piece_count = screenshot_to_fen(
        args.image,
        template_dir=args.templates,
        board_rect=BoardRectangle.parse(args.board_rect),
        active_color=args.active_color,
        threshold=args.threshold,
        crop_scale=args.crop_scale,
    )
    result = find_forced_mate(
        fen,
        engine_path=args.engine,
        depth=args.depth,
        movetime_ms=args.movetime_ms,
        command_timeout=args.command_timeout,
    )
    data = result_to_dict(
        result,
        image=str(args.image),
        confidence=confidence,
        piece_count=piece_count,
    )
    if args.output is not None:
        write_json(args.output, data)
    if args.markdown_output is not None:
        write_markdown(args.markdown_output, data)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Find a Pikafish forced mate line from a Xiangqi board screenshot.",
    )
    parser.add_argument("--image", type=Path, required=True, help="Board screenshot .png/.jpg.")
    parser.add_argument("--templates", type=Path, required=True, help="Template manifest directory.")
    parser.add_argument("--board-rect", required=True, help="Manual rectangle: x,y,width,height.")
    parser.add_argument("--engine", type=Path, required=True, help="Pikafish UCI binary path.")
    parser.add_argument("--active-color", default="w", choices=["w", "b"])
    parser.add_argument("--threshold", type=float, default=0.92)
    parser.add_argument("--crop-scale", type=float, default=0.8)
    parser.add_argument("--depth", type=int, default=12)
    parser.add_argument("--movetime-ms", type=int)
    parser.add_argument("--command-timeout", type=float, default=30.0)
    parser.add_argument("--output", type=Path, help="Optional JSON output path.")
    parser.add_argument("--markdown-output", type=Path, help="Optional Markdown output path.")
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(main())
