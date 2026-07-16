from __future__ import annotations

from dataclasses import dataclass

from xiangqi_sifu.board.rules import BoardState, PositionStatus, apply_legal_move, position_status


@dataclass(frozen=True)
class GameState:
    board: BoardState
    moves: tuple[str, ...]
    position_fens: tuple[str, ...]

    @classmethod
    def start(cls, board: BoardState) -> "GameState":
        return cls(board=board, moves=(), position_fens=(board.to_fen(),))

    def push(self, move_uci: str) -> "GameState":
        next_board = apply_legal_move(self.board, move_uci)
        return GameState(
            board=next_board,
            moves=(*self.moves, move_uci.lower()),
            position_fens=(*self.position_fens, next_board.to_fen()),
        )

    def repetition_count(self, board: BoardState | None = None) -> int:
        target = (board or self.board).to_fen().split(" ", 4)[0:2]
        key = " ".join(target)
        return sum(
            1
            for fen in self.position_fens
            if " ".join(fen.split(" ", 4)[0:2]) == key
        )

    @property
    def status(self) -> PositionStatus:
        return position_status(self.board, repetitions=self.repetition_count())
