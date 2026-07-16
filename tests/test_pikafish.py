import os
import sys

from xiangqi_sifu.board.representation import Position
from xiangqi_sifu.engine.analysis import MockEngine, analyze_game
from xiangqi_sifu.engine.pikafish import PikafishEngine
from xiangqi_sifu.parsers.simple_move_parser import SimpleMoveParser


START_FEN = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"


def test_mock_engine_drives_analysis_without_pikafish_binary():
    game = SimpleMoveParser(starting_fen=START_FEN).parse_text("H2-E2 B9-C7")
    engine = MockEngine(
        scores=[100, 40, 120],
        best_moves=["h2e2", "b9c7", "h0g2"],
    )

    analysis = analyze_game(game, engine)

    assert [item.red_score_cp for item in analysis.evaluations] == [100, 40, 120]
    assert analysis.evaluations[0].best_move == "h2e2"
    assert analysis.positions[2].move_uci == "b9c7"
    assert engine.analyzed_fens == [position.fen for position in analysis.positions]


def test_pikafish_engine_speaks_uci_and_parses_analysis(tmp_path):
    fake_engine = _write_fake_uci_engine(tmp_path, score_cp=42, best_move="h2e2")
    position = Position(ply=0, fen=START_FEN, side_to_move="red")

    engine = PikafishEngine(fake_engine, depth=6)
    try:
        evaluation = engine.analyze(position)
    finally:
        engine.close()

    assert evaluation.ply == 0
    assert evaluation.red_score_cp == 42
    assert evaluation.best_move == "h2e2"
    assert evaluation.pv == ("h2e2", "b9c7")


def test_pikafish_engine_converts_black_to_move_score_to_red_perspective(tmp_path):
    fake_engine = _write_fake_uci_engine(tmp_path, score_cp=75, best_move="b9c7")
    fen = START_FEN.replace(" w ", " b ")
    position = Position(ply=1, fen=fen, side_to_move="black")

    engine = PikafishEngine(fake_engine, depth=6)
    try:
        evaluation = engine.analyze(position)
    finally:
        engine.close()

    assert evaluation.red_score_cp == -75
    assert evaluation.best_move == "b9c7"


def test_pikafish_engine_returns_ordered_multipv_metadata(tmp_path):
    fake_engine = _write_fake_multipv_engine(tmp_path)
    position = Position(ply=0, fen=START_FEN, side_to_move="red")

    engine = PikafishEngine(fake_engine, depth=12)
    try:
        lines = engine.analyze_lines(position, multipv=3)
    finally:
        engine.close()

    assert [line.multipv for line in lines] == [1, 2, 3]
    assert [line.best_move for line in lines] == ["h2e2", "h0g2", "b2e2"]
    assert [line.red_score_cp for line in lines] == [80, 45, None]
    assert lines[2].mate_score == 5
    assert lines[0].depth == 12
    assert lines[0].nodes == 1200
    assert lines[0].pv == ("h2e2", "b9c7")


def _write_fake_uci_engine(tmp_path, score_cp, best_move):
    script = tmp_path / "fake_uci_engine.py"
    script.write_text(
        f"""#!{sys.executable}
import sys

for raw in sys.stdin:
    command = raw.strip()
    if command == "uci":
        print("id name Fake Pikafish")
        print("id author tests")
        print("uciok")
        sys.stdout.flush()
    elif command == "isready":
        print("readyok")
        sys.stdout.flush()
    elif command.startswith("go "):
        print("info depth 1 score cp {score_cp} pv h2e2 b9c7")
        print("bestmove {best_move}")
        sys.stdout.flush()
    elif command == "quit":
        break
""",
        encoding="utf-8",
    )
    script.chmod(script.stat().st_mode | os.X_OK)
    return script


def _write_fake_multipv_engine(tmp_path):
    script = tmp_path / "fake_multipv_engine.py"
    script.write_text(
        f"""#!{sys.executable}
import sys

for raw in sys.stdin:
    command = raw.strip()
    if command == "uci":
        print("id name Fake MultiPV Pikafish")
        print("option name MultiPV type spin default 1 min 1 max 10")
        print("uciok")
        sys.stdout.flush()
    elif command == "isready":
        print("readyok")
        sys.stdout.flush()
    elif command.startswith("go "):
        print("info depth 10 multipv 1 score cp 70 nodes 900 pv h2e2 b9c7")
        print("info depth 12 multipv 2 score cp 45 nodes 1100 pv h0g2 b9c7")
        print("info depth 12 multipv 1 score cp 80 nodes 1200 pv h2e2 b9c7")
        print("info depth 12 multipv 3 score mate 5 nodes 1000 pv b2e2 b9c7")
        print("bestmove h2e2")
        sys.stdout.flush()
    elif command == "quit":
        break
""",
        encoding="utf-8",
    )
    script.chmod(script.stat().st_mode | os.X_OK)
    return script
