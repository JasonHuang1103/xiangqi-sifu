from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from xiangqi_sifu.coach.mistake_detector import Mistake
from xiangqi_sifu.engine.analysis import AnalysisResult


class AnalysisRepository:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def save_analysis(self, analysis: AnalysisResult, mistakes: list[Mistake]) -> int:
        game = analysis.game
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("pragma foreign_keys = on")
            game_cursor = conn.execute(
                """
                insert into games (event, red, black, result, starting_fen, metadata_json)
                values (?, ?, ?, ?, ?, ?)
                """,
                (
                    game.metadata.get("Event"),
                    game.red,
                    game.black,
                    game.result,
                    game.starting_fen,
                    json.dumps(game.metadata, ensure_ascii=False),
                ),
            )
            game_id = int(game_cursor.lastrowid)

            conn.executemany(
                """
                insert into positions (game_id, ply, fen, side_to_move, move_uci, move_iccs)
                values (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        game_id,
                        position.ply,
                        position.fen,
                        position.side_to_move,
                        position.move_uci,
                        position.move_iccs,
                    )
                    for position in analysis.positions
                ],
            )
            conn.executemany(
                """
                insert into moves (game_id, ply, move_number, side, iccs, uci)
                values (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        game_id,
                        index + 1,
                        move.move_number,
                        move.side,
                        move.iccs,
                        move.uci,
                    )
                    for index, move in enumerate(game.moves)
                ],
            )
            conn.executemany(
                """
                insert into evaluations (game_id, ply, fen, red_score_cp, mate_score, best_move, pv_json)
                values (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        game_id,
                        evaluation.ply,
                        evaluation.fen,
                        evaluation.red_score_cp,
                        evaluation.mate_score,
                        evaluation.best_move,
                        json.dumps(list(evaluation.pv)),
                    )
                    for evaluation in analysis.evaluations
                ],
            )
            conn.executemany(
                """
                insert into mistakes (
                    game_id, ply, move_number, side, played_move, best_move, severity,
                    eval_before_cp, eval_after_cp, eval_loss_cp
                )
                values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        game_id,
                        mistake.ply,
                        mistake.move_number,
                        mistake.side,
                        mistake.played_move,
                        mistake.best_move,
                        mistake.severity,
                        mistake.eval_before_cp,
                        mistake.eval_after_cp,
                        mistake.eval_loss_cp,
                    )
                    for mistake in mistakes
                ],
            )
            return game_id

    def _initialize(self) -> None:
        schema_path = Path(__file__).with_name("schema.sql")
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("pragma foreign_keys = on")
            conn.executescript(schema_path.read_text(encoding="utf-8"))
