from __future__ import annotations

from collections.abc import Mapping

from xiangqi_sifu.board.fen import FenBoard

FILES = "abcdefghi"
VALID_PIECES = set("rnbakcpRNBAKCP")


def fen_to_piece_map(fen: str) -> dict[str, str]:
    board = FenBoard.from_fen(fen)
    pieces: dict[str, str] = {}
    for row_index, row in enumerate(board.board):
        rank = 9 - row_index
        for file_index, piece in enumerate(row):
            if piece is not None:
                pieces[f"{FILES[file_index]}{rank}"] = piece
    return pieces


def fen_from_piece_map(
    pieces: Mapping[str, str],
    *,
    active_color: str = "w",
    halfmove_clock: int = 0,
    fullmove_number: int = 1,
) -> str:
    rows: list[str] = []
    for rank in range(9, -1, -1):
        empty = 0
        encoded: list[str] = []
        for file_name in FILES:
            piece = pieces.get(f"{file_name}{rank}")
            if piece is None:
                empty += 1
                continue
            _validate_piece(piece)
            if empty:
                encoded.append(str(empty))
                empty = 0
            encoded.append(piece)
        if empty:
            encoded.append(str(empty))
        rows.append("".join(encoded))

    fen = f"{'/'.join(rows)} {active_color} - - {halfmove_clock} {fullmove_number}"
    FenBoard.from_fen(fen)
    return fen


def _validate_piece(piece: str) -> None:
    if len(piece) != 1 or piece not in VALID_PIECES:
        raise ValueError(f"Unsupported Xiangqi FEN piece: {piece!r}")
