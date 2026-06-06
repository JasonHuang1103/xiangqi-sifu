from __future__ import annotations

import re
from pathlib import Path

from xiangqi_sifu.board.move import normalize_move
from xiangqi_sifu.config import DEFAULT_START_FEN
from xiangqi_sifu.parsers.base import GameRecord, ParsedMove

MOVE_TOKEN_RE = re.compile(r"\b(?:[A-I][0-9]-[A-I][0-9]|[a-i][0-9][a-i][0-9])\b", re.IGNORECASE)


class SimpleMoveParser:
    def __init__(self, starting_fen: str = DEFAULT_START_FEN) -> None:
        self.starting_fen = starting_fen

    def parse_text(self, text: str) -> GameRecord:
        moves = _parse_move_tokens(text)
        return GameRecord(starting_fen=self.starting_fen, moves=moves)

    def parse_file(self, path: str | Path) -> GameRecord:
        return self.parse_text(Path(path).read_text(encoding="utf-8"))


def _parse_move_tokens(text: str) -> list[ParsedMove]:
    parsed_moves = []
    for ply, token in enumerate(MOVE_TOKEN_RE.findall(text)):
        move = normalize_move(token)
        parsed_moves.append(
            ParsedMove(
                iccs=move.iccs,
                uci=move.uci,
                move_number=(ply // 2) + 1,
                side="red" if ply % 2 == 0 else "black",
            )
        )
    return parsed_moves
