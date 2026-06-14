from __future__ import annotations

import argparse
import json
from pathlib import Path

from xiangqi_sifu.vision.board_detector import ensure_image_path, manual_board_rectangle
from xiangqi_sifu.vision.image_recognizer import recognize_board_from_image
from xiangqi_sifu.vision.piece_classifier import load_labelled_board


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    rectangle = manual_board_rectangle(args.board_rect)
    if args.labels is not None:
        labelled_board = load_labelled_board(args.labels)
        source = "labels"
    else:
        if args.image is None or args.templates is None or rectangle is None:
            raise SystemExit("--image mode requires --image, --templates, and --board-rect")
        ensure_image_path(args.image)
        labelled_board = recognize_board_from_image(
            args.image,
            template_dir=args.templates,
            board_rect=rectangle,
            active_color=args.active_color,
            threshold=args.threshold,
            crop_scale=args.crop_scale,
        )
        source = "image"

    output = {
        "fen": labelled_board.to_fen(),
        "source": source,
        "confidence": labelled_board.confidence,
        "piece_count": len(labelled_board.pieces),
        "uncertain_squares": labelled_board.uncertain_squares,
    }
    if args.image is not None:
        output["image"] = str(args.image)
    if rectangle is not None:
        output["board_rect"] = {
            "x": rectangle.x,
            "y": rectangle.y,
            "width": rectangle.width,
            "height": rectangle.height,
        }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert a Xiangqi board screenshot or verified labels into FEN.",
    )
    parser.add_argument("--image", type=Path, help="Optional source screenshot path.")
    parser.add_argument(
        "--labels",
        type=Path,
        help="JSON label file containing active_color and pieces.",
    )
    parser.add_argument("--templates", type=Path, help="Template manifest directory for image mode.")
    parser.add_argument(
        "--board-rect",
        help="Manual board rectangle in x,y,width,height format for image mode.",
    )
    parser.add_argument("--active-color", default="w", choices=["w", "b"])
    parser.add_argument("--threshold", type=float, default=0.92)
    parser.add_argument("--crop-scale", type=float, default=0.8)
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(main())
