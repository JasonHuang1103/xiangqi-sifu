import json

from PIL import Image, ImageDraw

from scripts.compare_screenshots import main as compare_main
from scripts.screenshot_to_fen import main as screenshot_main
from xiangqi_sifu.config import DEFAULT_START_FEN
from xiangqi_sifu.vision.fen_from_image import fen_to_piece_map, fen_from_piece_map
from xiangqi_sifu.vision.grid_mapper import BoardRectangle
from xiangqi_sifu.vision.move_from_screenshots import infer_move_from_fens
from xiangqi_sifu.vision.orientation import resolve_orientation


def test_board_rectangle_maps_90_xiangqi_intersections():
    points = BoardRectangle(x=10, y=20, width=160, height=180).grid_points()

    assert len(points) == 90
    assert points[0].square == "a9"
    assert points[0].x == 10
    assert points[0].y == 20
    assert points[-1].square == "i0"
    assert points[-1].x == 170
    assert points[-1].y == 200


def test_fen_from_piece_map_round_trips_default_position():
    pieces = fen_to_piece_map(DEFAULT_START_FEN)

    fen = fen_from_piece_map(pieces, active_color="w")

    assert fen == DEFAULT_START_FEN


def test_resolve_orientation_uses_kings():
    pieces = fen_to_piece_map(DEFAULT_START_FEN)

    orientation = resolve_orientation(pieces)

    assert orientation == "red_bottom"


def test_infer_move_from_before_after_fens():
    before = DEFAULT_START_FEN
    after = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C2C4/9/RNBAKABNR b - - 0 1"

    result = infer_move_from_fens(before, after)

    assert result.move_uci == "h2e2"
    assert result.move_iccs == "H2-E2"
    assert result.confidence == 1.0
    assert result.changed_squares == ("e2", "h2")


def test_screenshot_to_fen_cli_reads_verified_labels(tmp_path, capsys):
    labels_path = tmp_path / "labels.json"
    labels_path.write_text(
        json.dumps(
            {
                "active_color": "w",
                "pieces": fen_to_piece_map(DEFAULT_START_FEN),
                "confidence": {"a9": 0.9},
            }
        ),
        encoding="utf-8",
    )

    exit_code = screenshot_main(["--labels", str(labels_path)])

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert output["fen"] == DEFAULT_START_FEN
    assert output["confidence"] == 0.9
    assert output["uncertain_squares"] == []


def test_compare_screenshots_cli_infers_move_from_label_files(tmp_path, capsys):
    before_path = tmp_path / "before.json"
    after_path = tmp_path / "after.json"
    before_path.write_text(
        json.dumps({"active_color": "w", "pieces": fen_to_piece_map(DEFAULT_START_FEN)}),
        encoding="utf-8",
    )
    after_path.write_text(
        json.dumps(
            {
                "active_color": "b",
                "pieces": fen_to_piece_map(
                    "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C2C4/9/RNBAKABNR b - - 0 1"
                ),
            }
        ),
        encoding="utf-8",
    )

    exit_code = compare_main(["--before-labels", str(before_path), "--after-labels", str(after_path)])

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert output["move_uci"] == "h2e2"
    assert output["move_iccs"] == "H2-E2"


def test_screenshot_to_fen_cli_reads_png_with_templates(tmp_path, capsys):
    templates_dir = _write_templates(tmp_path)
    image_path = tmp_path / "board.png"
    _write_board_image(image_path, fen_to_piece_map(DEFAULT_START_FEN), templates_dir)

    exit_code = screenshot_main(
        [
            "--image",
            str(image_path),
            "--templates",
            str(templates_dir),
            "--board-rect",
            "10,10,160,180",
            "--active-color",
            "w",
            "--threshold",
            "0.95",
        ]
    )

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert output["fen"] == DEFAULT_START_FEN
    assert output["source"] == "image"
    assert output["piece_count"] == 32


def test_compare_screenshots_cli_infers_move_from_pngs(tmp_path, capsys):
    templates_dir = _write_templates(tmp_path)
    before_path = tmp_path / "before.png"
    after_path = tmp_path / "after.png"
    _write_board_image(before_path, fen_to_piece_map(DEFAULT_START_FEN), templates_dir)
    _write_board_image(
        after_path,
        fen_to_piece_map(
            "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C2C4/9/RNBAKABNR b - - 0 1"
        ),
        templates_dir,
    )

    exit_code = compare_main(
        [
            "--before-image",
            str(before_path),
            "--after-image",
            str(after_path),
            "--templates",
            str(templates_dir),
            "--board-rect",
            "10,10,160,180",
            "--before-active-color",
            "w",
            "--after-active-color",
            "b",
            "--threshold",
            "0.95",
        ]
    )

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert output["move_uci"] == "h2e2"
    assert output["before_fen"] == DEFAULT_START_FEN


def _write_templates(tmp_path):
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    manifest = {}
    for piece in "rnbakcpRNBAKCP":
        filename = f"{ord(piece)}.png"
        manifest[piece] = filename
        image = Image.new("RGB", (16, 16), "white")
        draw = ImageDraw.Draw(image)
        color = "red" if piece.isupper() else "black"
        draw.ellipse((1, 1, 14, 14), fill=color)
        draw.text((5, 4), piece.upper(), fill="white")
        image.save(templates_dir / filename)
    (templates_dir / "manifest.json").write_text(
        json.dumps({"templates": manifest}),
        encoding="utf-8",
    )
    return templates_dir


def _write_board_image(path, pieces, templates_dir):
    image = Image.new("RGB", (180, 200), "white")
    draw = ImageDraw.Draw(image)
    for file_index in range(9):
        x = 10 + file_index * 20
        draw.line((x, 10, x, 190), fill="gray")
    for row_index in range(10):
        y = 10 + row_index * 20
        draw.line((10, y, 170, y), fill="gray")
    for square, piece in pieces.items():
        file_index = "abcdefghi".index(square[0])
        rank = int(square[1])
        center_x = 10 + file_index * 20
        center_y = 10 + (9 - rank) * 20
        template = Image.open(templates_dir / f"{ord(piece)}.png").convert("RGB")
        image.paste(template, (center_x - 8, center_y - 8))
    image.save(path)
