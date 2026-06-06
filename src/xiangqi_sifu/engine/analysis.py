from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from xiangqi_sifu.board.fen import generate_positions
from xiangqi_sifu.board.representation import Position
from xiangqi_sifu.parsers.base import GameRecord


@dataclass(frozen=True)
class Evaluation:
    ply: int
    fen: str
    red_score_cp: int | None
    best_move: str | None = None
    mate_score: int | None = None
    pv: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class AnalysisResult:
    game: GameRecord
    positions: list[Position]
    evaluations: list[Evaluation]


class Engine(Protocol):
    def analyze(self, position: Position) -> Evaluation:
        ...


class MockEngine:
    """Deterministic engine for tests and Run 1 CLI demos."""

    def __init__(
        self,
        scores: list[int] | None = None,
        best_moves: list[str | None] | None = None,
    ) -> None:
        self.scores = scores or []
        self.best_moves = best_moves or []
        self.analyzed_fens: list[str] = []

    def analyze(self, position: Position) -> Evaluation:
        self.analyzed_fens.append(position.fen)
        index = position.ply
        score = self.scores[index] if index < len(self.scores) else 0
        best_move = self.best_moves[index] if index < len(self.best_moves) else None
        return Evaluation(
            ply=position.ply,
            fen=position.fen,
            red_score_cp=score,
            best_move=best_move,
        )


def analyze_game(game: GameRecord, engine: Engine) -> AnalysisResult:
    positions = generate_positions(game.starting_fen, [move.uci for move in game.moves])
    evaluations = [engine.analyze(position) for position in positions]
    return AnalysisResult(game=game, positions=positions, evaluations=evaluations)
