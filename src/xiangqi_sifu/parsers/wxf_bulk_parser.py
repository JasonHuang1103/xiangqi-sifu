from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from xiangqi_sifu.parsers.base import GameRecord
from xiangqi_sifu.parsers.pgn_parser import PgnParser

GAME_DELIMITER = '[Game "Chinese Chess"]'


@dataclass(frozen=True)
class ImportSummary:
    source_path: Path
    output_dir: Path
    output_path: Path
    manifest_path: Path
    game_count: int


def iter_game_texts(source_path: str | Path) -> Iterator[str]:
    current_lines: list[str] = []
    with Path(source_path).open("r", encoding="utf-8-sig", errors="replace") as source:
        for line in source:
            if line.startswith(GAME_DELIMITER):
                if current_lines:
                    yield "".join(current_lines).strip() + "\n"
                    current_lines = []
            if current_lines or line.startswith(GAME_DELIMITER):
                current_lines.append(line)
    if current_lines:
        yield "".join(current_lines).strip() + "\n"


def write_games_jsonl(
    source_path: str | Path,
    output_dir: str | Path,
    *,
    limit: int | None = None,
) -> ImportSummary:
    source = Path(source_path)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    output_path = destination / "games.jsonl"
    manifest_path = destination / "manifest.json"
    parser = PgnParser()

    game_count = 0
    with output_path.open("w", encoding="utf-8") as output:
        for raw_game in iter_game_texts(source):
            if limit is not None and game_count >= limit:
                break
            game_count += 1
            game = parser.parse_text(raw_game)
            output.write(json.dumps(_to_record(game_count, game), ensure_ascii=False))
            output.write("\n")

    manifest = {
        "source_file": str(source),
        "output_file": str(output_path),
        "game_count": game_count,
        "format": "jsonl",
        "delimiter": GAME_DELIMITER,
        "schema_version": 1,
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return ImportSummary(
        source_path=source,
        output_dir=destination,
        output_path=output_path,
        manifest_path=manifest_path,
        game_count=game_count,
    )


def _to_record(game_id: int, game: GameRecord) -> dict:
    return {
        "schema_version": 1,
        "game_id": game_id,
        "metadata": game.metadata,
        "red": game.red,
        "black": game.black,
        "result": game.result,
        "starting_fen": game.starting_fen,
        "move_count": len(game.moves),
        "moves": [
            {
                "ply": index + 1,
                "move_number": move.move_number,
                "side": move.side,
                "iccs": move.iccs,
                "uci": move.uci,
            }
            for index, move in enumerate(game.moves)
        ],
    }
