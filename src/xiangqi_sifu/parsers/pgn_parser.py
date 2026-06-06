from __future__ import annotations

import re
from pathlib import Path

from xiangqi_sifu.config import DEFAULT_START_FEN
from xiangqi_sifu.parsers.base import GameRecord
from xiangqi_sifu.parsers.simple_move_parser import _parse_move_tokens

TAG_RE = re.compile(r'^\[([^ ]+) "(.*)"\]$', re.MULTILINE)


class PgnParser:
    def parse_text(self, text: str) -> GameRecord:
        metadata = dict(TAG_RE.findall(text))
        body = TAG_RE.sub("", text)
        moves = _parse_move_tokens(body)
        return GameRecord(
            metadata=metadata,
            starting_fen=metadata.get("FEN", DEFAULT_START_FEN),
            moves=moves,
            red=metadata.get("Red"),
            black=metadata.get("Black"),
            result=metadata.get("Result"),
        )

    def parse_file(self, path: str | Path) -> GameRecord:
        return self.parse_text(Path(path).read_text(encoding="utf-8"))
