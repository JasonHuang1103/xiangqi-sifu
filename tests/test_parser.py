from xiangqi_sifu.parsers.pgn_parser import PgnParser
from xiangqi_sifu.parsers.simple_move_parser import SimpleMoveParser


def test_simple_move_parser_normalizes_iccs_and_uci_moves():
    text = "H2-E2 b9c7\nH0-G2"

    game = SimpleMoveParser().parse_text(text)

    assert game.moves[0].iccs == "H2-E2"
    assert game.moves[0].uci == "h2e2"
    assert game.moves[1].iccs == "B9-C7"
    assert game.moves[2].move_number == 2
    assert game.moves[2].side == "red"


def test_pgn_parser_reads_metadata_fen_and_moves():
    text = """[Game "Chinese Chess"]
[Event "Sample Event"]
[Red "Red Player"]
[Black "Black Player"]
[Result "1-0"]
[FEN "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"]
[Format "ICCS"]
1. H2-E2 B9-C7
2. H0-G2
1-0
"""

    game = PgnParser().parse_text(text)

    assert game.metadata["Event"] == "Sample Event"
    assert game.red == "Red Player"
    assert game.black == "Black Player"
    assert game.result == "1-0"
    assert game.starting_fen.startswith("rnbakabnr/9")
    assert [move.iccs for move in game.moves] == ["H2-E2", "B9-C7", "H0-G2"]
