from __future__ import annotations

import argparse
import json
from pathlib import Path

from xiangqi_sifu.vision.board_detector import manual_board_rectangle
from xiangqi_sifu.vision.image_recognizer import recognize_board_from_image
from xiangqi_sifu.vision.move_from_screenshots import infer_move_from_piece_maps
from xiangqi_sifu.vision.piece_classifier import load_labelled_board


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    before, after = _load_boards(args)
    inference = infer_move_from_piece_maps(before.pieces, after.pieces)
    output = {
        "move_uci": inference.move_uci,
        "move_iccs": inference.move_iccs,
        "confidence": inference.confidence,
        "changed_squares": list(inference.changed_squares),
        "before_fen": before.to_fen(),
        "after_fen": after.to_fen(),
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Infer a Xiangqi move from before/after screenshots or verified board labels.",
    )
    parser.add_argument("--before-labels", type=Path)
    parser.add_argument("--after-labels", type=Path)
    parser.add_argument("--before-image", type=Path)
    parser.add_argument("--after-image", type=Path)
    parser.add_argument("--templates", type=Path)
    parser.add_argument("--board-rect")
    parser.add_argument("--before-active-color", default="w", choices=["w", "b"])
    parser.add_argument("--after-active-color", default="b", choices=["w", "b"])
    parser.add_argument("--threshold", type=float, default=0.92)
    parser.add_argument("--crop-scale", type=float, default=0.8)
    return parser.parse_args(argv)


def _load_boards(args: argparse.Namespace):
    if args.before_labels is not None and args.after_labels is not None:
        return load_labelled_board(args.before_labels), load_labelled_board(args.after_labels)
    if (
        args.before_image is None
        or args.after_image is None
        or args.templates is None
        or args.board_rect is None
    ):
        raise SystemExit(
            "image mode requires --before-image, --after-image, --templates, and --board-rect"
        )
    rectangle = manual_board_rectangle(args.board_rect)
    if rectangle is None:
        raise SystemExit("--board-rect is required for image mode")
    before = recognize_board_from_image(
        args.before_image,
        template_dir=args.templates,
        board_rect=rectangle,
        active_color=args.before_active_color,
        threshold=args.threshold,
        crop_scale=args.crop_scale,
    )
    after = recognize_board_from_image(
        args.after_image,
        template_dir=args.templates,
        board_rect=rectangle,
        active_color=args.after_active_color,
        threshold=args.threshold,
        crop_scale=args.crop_scale,
    )
    return before, after


if __name__ == "__main__":
    raise SystemExit(main())
