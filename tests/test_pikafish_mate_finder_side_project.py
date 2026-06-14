import json

from PIL import Image, ImageDraw

from side_projects.pikafish_mate_finder.mate_finder.mate_search import find_forced_mate
from side_projects.pikafish_mate_finder.scripts.find_mate import main as find_mate_main


START_FEN = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"


def test_find_forced_mate_reports_mate_score_from_uci(tmp_path):
    engine = _write_fake_engine(tmp_path, "info depth 1 score mate 3 pv h2e2 b9c7 h0g2\nbestmove h2e2\n")

    result = find_forced_mate(
        START_FEN,
        engine_path=engine,
        depth=1,
        command_timeout=5,
    )

    assert result.forced_mate_found is True
    assert result.mate_score == 3
    assert result.best_move == "h2e2"
    assert result.pv == ("h2e2", "b9c7", "h0g2")


def test_find_mate_cli_accepts_png_as_only_position_input(tmp_path, capsys):
    engine = _write_fake_engine(tmp_path, "info depth 1 score mate 3 pv h2e2 b9c7 h0g2\nbestmove h2e2\n")
    templates_dir = _write_templates(tmp_path)
    image_path = tmp_path / "board.png"
    _write_board_image(image_path, _starting_pieces(), templates_dir)

    exit_code = find_mate_main(
        [
            "--image",
            str(image_path),
            "--templates",
            str(templates_dir),
            "--board-rect",
            "10,10,160,180",
            "--engine",
            str(engine),
            "--depth",
            "1",
        ]
    )

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert output["fen"] == START_FEN
    assert output["forced_mate_found"] is True
    assert output["mate_score"] == 3
    assert output["pv"] == ["h2e2", "b9c7", "h0g2"]


def test_find_mate_cli_does_not_claim_mate_for_cp_score(tmp_path, capsys):
    engine = _write_fake_engine(tmp_path, "info depth 1 score cp 120 pv h2e2 b9c7\nbestmove h2e2\n")
    templates_dir = _write_templates(tmp_path)
    image_path = tmp_path / "board.png"
    _write_board_image(image_path, _starting_pieces(), templates_dir)

    exit_code = find_mate_main(
        [
            "--image",
            str(image_path),
            "--templates",
            str(templates_dir),
            "--board-rect",
            "10,10,160,180",
            "--engine",
            str(engine),
            "--depth",
            "1",
        ]
    )

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert output["forced_mate_found"] is False
    assert output["cp_score"] == 120
    assert output["message"] == "No forced mate found at this search setting."


def _write_fake_engine(tmp_path, analysis_output):
    path = tmp_path / "fake_engine.py"
    path.write_text(
        "import sys\n"
        f"analysis_output = {analysis_output!r}\n"
        "for line in sys.stdin:\n"
        "    command = line.strip()\n"
        "    if command == 'uci':\n"
        "        print('id name FakePikafish', flush=True)\n"
        "        print('uciok', flush=True)\n"
        "    elif command == 'isready':\n"
        "        print('readyok', flush=True)\n"
        "    elif command.startswith('go'):\n"
        "        print(analysis_output, end='', flush=True)\n"
        "    elif command == 'quit':\n"
        "        break\n",
        encoding="utf-8",
    )
    return path


def _write_templates(tmp_path):
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    manifest = {}
    for piece in "rnbakcpRNBAKCP":
        filename = f"{ord(piece)}.png"
        manifest[piece] = filename
        image = Image.new("RGB", (16, 16), "white")
        draw = ImageDraw.Draw(image)
        draw.ellipse((1, 1, 14, 14), fill=("red" if piece.isupper() else "black"))
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


def _starting_pieces():
    return {
        "a9": "r",
        "b9": "n",
        "c9": "b",
        "d9": "a",
        "e9": "k",
        "f9": "a",
        "g9": "b",
        "h9": "n",
        "i9": "r",
        "b7": "c",
        "h7": "c",
        "a6": "p",
        "c6": "p",
        "e6": "p",
        "g6": "p",
        "i6": "p",
        "a3": "P",
        "c3": "P",
        "e3": "P",
        "g3": "P",
        "i3": "P",
        "b2": "C",
        "h2": "C",
        "a0": "R",
        "b0": "N",
        "c0": "B",
        "d0": "A",
        "e0": "K",
        "f0": "A",
        "g0": "B",
        "h0": "N",
        "i0": "R",
    }
