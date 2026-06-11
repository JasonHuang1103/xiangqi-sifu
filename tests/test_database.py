import sqlite3

from xiangqi_sifu.coach.mistake_detector import Mistake
from xiangqi_sifu.coach.explanation import (
    ExplanationCandidate,
    ExplanationSample,
    VerifiedExplanation,
)
from xiangqi_sifu.database.repository import AnalysisRepository
from xiangqi_sifu.engine.analysis import AnalysisResult, Evaluation
from xiangqi_sifu.parsers.base import GameRecord, ParsedMove


def test_repository_saves_game_analysis_to_sqlite(tmp_path):
    db_path = tmp_path / "xiangqi_sifu.db"
    game = GameRecord(
        metadata={"Event": "Sample"},
        starting_fen="start",
        moves=[ParsedMove(iccs="H2-E2", uci="h2e2", move_number=1, side="red")],
        red="Red",
        black="Black",
        result="1-0",
    )
    analysis = AnalysisResult(
        game=game,
        positions=[],
        evaluations=[
            Evaluation(ply=0, fen="start", red_score_cp=120, best_move="h0g2"),
            Evaluation(ply=1, fen="after", red_score_cp=-80, best_move="b9c7"),
        ],
    )
    mistakes = [
        Mistake(
            ply=1,
            move_number=1,
            side="red",
            played_move="h2e2",
            best_move="h0g2",
            severity="mistake",
            eval_before_cp=120,
            eval_after_cp=-80,
            eval_loss_cp=200,
        )
    ]

    game_id = AnalysisRepository(db_path).save_analysis(analysis, mistakes)

    with sqlite3.connect(db_path) as conn:
        assert conn.execute("select count(*) from games").fetchone()[0] == 1
        assert conn.execute("select count(*) from moves").fetchone()[0] == 1
        assert conn.execute("select count(*) from evaluations").fetchone()[0] == 2
        assert conn.execute("select severity from mistakes where game_id = ?", (game_id,)).fetchone()[0] == "mistake"


def test_repository_saves_verified_explanations_to_sqlite(tmp_path):
    db_path = tmp_path / "xiangqi_sifu.db"
    game = GameRecord(
        metadata={"Event": "Sample"},
        starting_fen="start",
        moves=[ParsedMove(iccs="H2-E2", uci="h2e2", move_number=1, side="red")],
    )
    analysis = AnalysisResult(
        game=game,
        positions=[],
        evaluations=[
            Evaluation(ply=0, fen="start", red_score_cp=120, best_move="h0g2"),
            Evaluation(ply=1, fen="after", red_score_cp=-80, best_move="b9c7"),
        ],
    )
    mistakes = [
        Mistake(
            ply=1,
            move_number=1,
            side="red",
            played_move="h2e2",
            best_move="h0g2",
            severity="mistake",
            eval_before_cp=120,
            eval_after_cp=-80,
            eval_loss_cp=200,
        )
    ]
    verified = [
        VerifiedExplanation(
            sample=ExplanationSample(
                ply=1,
                move_number=1,
                side="red",
                severity="mistake",
                fen="start",
                played_move="h2e2",
                best_move="h0g2",
                pv_best=("h0g2", "b9c7"),
                pv_played=("b9c7",),
                eval_before_cp=120,
                eval_after_cp=-80,
                eval_delta_cp=-200,
                eval_loss_cp=200,
            ),
            candidate=ExplanationCandidate(
                provider="static",
                text="Pikafish prefers h0g2 because the played move lost 200 cp.",
            ),
            status="PASS",
            confidence="Medium",
            notes=("best move checked",),
        )
    ]

    game_id = AnalysisRepository(db_path).save_analysis(
        analysis,
        mistakes,
        verified_explanations=verified,
    )

    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            """
            select ply, provider, status, confidence, explanation_text, notes_json
            from explanations
            where game_id = ?
            """,
            (game_id,),
        ).fetchone()

    assert row[0] == 1
    assert row[1] == "static"
    assert row[2] == "PASS"
    assert row[3] == "Medium"
    assert "h0g2" in row[4]
    assert row[5] == '["best move checked"]'
