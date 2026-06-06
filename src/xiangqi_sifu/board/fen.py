from __future__ import annotations

from dataclasses import dataclass

from xiangqi_sifu.board.move import normalize_move
from xiangqi_sifu.board.representation import Position

FILES = "abcdefghi"


@dataclass(frozen=True)
class FenBoard:
    board: tuple[tuple[str | None, ...], ...]
    active_color: str
    castling: str = "-"
    en_passant: str = "-"
    halfmove_clock: int = 0
    fullmove_number: int = 1

    @classmethod
    def from_fen(cls, fen: str) -> "FenBoard":
        fields = fen.split()
        if len(fields) != 6:
            raise ValueError(f"Expected 6-field FEN, got {len(fields)} fields: {fen!r}")
        rows = fields[0].split("/")
        if len(rows) != 10:
            raise ValueError(f"Expected 10 Xiangqi board rows in FEN: {fen!r}")

        parsed_rows: list[tuple[str | None, ...]] = []
        for row in rows:
            cells: list[str | None] = []
            for char in row:
                if char.isdigit():
                    cells.extend([None] * int(char))
                else:
                    cells.append(char)
            if len(cells) != 9:
                raise ValueError(f"Expected 9 files in FEN row {row!r}")
            parsed_rows.append(tuple(cells))

        return cls(
            board=tuple(parsed_rows),
            active_color=fields[1],
            castling=fields[2],
            en_passant=fields[3],
            halfmove_clock=int(fields[4]),
            fullmove_number=int(fields[5]),
        )

    def piece_at(self, square: str) -> str | None:
        row, col = _square_to_index(square)
        return self.board[row][col]

    def apply_uci_move(self, move_uci: str) -> "FenBoard":
        move = normalize_move(move_uci)
        from_row, from_col = _square_to_index(move.from_square)
        to_row, to_col = _square_to_index(move.to_square)
        piece = self.board[from_row][from_col]
        if piece is None:
            raise ValueError(f"No piece on {move.from_square} for move {move_uci!r}")

        rows = [list(row) for row in self.board]
        rows[from_row][from_col] = None
        rows[to_row][to_col] = piece
        next_color = "b" if self.active_color == "w" else "w"
        next_fullmove = self.fullmove_number + (1 if self.active_color == "b" else 0)
        return FenBoard(
            board=tuple(tuple(row) for row in rows),
            active_color=next_color,
            castling=self.castling,
            en_passant=self.en_passant,
            halfmove_clock=0,
            fullmove_number=next_fullmove,
        )

    def to_fen(self) -> str:
        rows = []
        for row in self.board:
            empty = 0
            encoded = []
            for piece in row:
                if piece is None:
                    empty += 1
                else:
                    if empty:
                        encoded.append(str(empty))
                        empty = 0
                    encoded.append(piece)
            if empty:
                encoded.append(str(empty))
            rows.append("".join(encoded))
        return (
            f"{'/'.join(rows)} {self.active_color} {self.castling} "
            f"{self.en_passant} {self.halfmove_clock} {self.fullmove_number}"
        )


def generate_positions(starting_fen: str, moves: list[str]) -> list[Position]:
    board = FenBoard.from_fen(starting_fen)
    positions = [
        Position(ply=0, fen=board.to_fen(), side_to_move=_side_name(board.active_color)),
    ]
    for ply, raw_move in enumerate(moves, start=1):
        move = normalize_move(raw_move)
        board = board.apply_uci_move(move.uci)
        positions.append(
            Position(
                ply=ply,
                fen=board.to_fen(),
                side_to_move=_side_name(board.active_color),
                move_uci=move.uci,
                move_iccs=move.iccs,
            )
        )
    return positions


def _square_to_index(square: str) -> tuple[int, int]:
    if len(square) != 2 or square[0] not in FILES or square[1] not in "0123456789":
        raise ValueError(f"Invalid Xiangqi coordinate: {square!r}")
    col = FILES.index(square[0])
    row = 9 - int(square[1])
    return row, col


def _side_name(active_color: str) -> str:
    return "red" if active_color == "w" else "black"
