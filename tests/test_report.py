from xiangqi_sifu.coach.mistake_detector import Mistake
from xiangqi_sifu.coach.explanation import (
    ExplanationCandidate,
    StaticExplanationProvider,
    VerifiedExplanation,
    build_explanation_samples,
)
from xiangqi_sifu.coach.report import render_markdown_report
from xiangqi_sifu.engine.analysis import AnalysisResult, Evaluation
from xiangqi_sifu.parsers.base import GameRecord, ParsedMove


def test_report_includes_metadata_eval_timeline_and_mistake_summary():
    game = GameRecord(
        metadata={"Event": "Sample"},
        starting_fen="start",
        moves=[ParsedMove(iccs="H2-E2", uci="h2e2", move_number=1, side="red")],
        red="Red Player",
        black="Black Player",
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

    markdown = render_markdown_report(analysis, mistakes)

    assert "# Xiangqi Sifu Review" in markdown
    assert "Red Player vs Black Player" in markdown
    assert "## Position Eval Data" in markdown
    assert "## Move Impact Data" in markdown
    assert "| 1 | red | h2e2 | +120 | -80 | -200 | 200 | h0g2 |" in markdown
    assert "| 1 | red | h2e2 | mistake | +120 | -80 | 200 | h0g2 |" in markdown
    assert "Likely reason:" in markdown
    assert '"ply": 1' in markdown


def test_report_can_include_verified_explanations():
    game = GameRecord(
        metadata={"Event": "Sample"},
        starting_fen="start",
        moves=[ParsedMove(iccs="H2-E2", uci="h2e2", move_number=1, side="red")],
    )
    analysis = AnalysisResult(
        game=game,
        positions=[],
        evaluations=[
            Evaluation(
                ply=0,
                fen="start",
                red_score_cp=120,
                best_move="h0g2",
                pv=("h0g2", "b9c7"),
            ),
            Evaluation(
                ply=1,
                fen="after",
                red_score_cp=-80,
                best_move="b9c7",
                pv=("b9c7",),
            ),
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

    markdown = render_markdown_report(
        analysis,
        mistakes,
        explanation_provider=StaticExplanationProvider(),
    )

    assert "## Verified Explanations" in markdown
    assert "Confidence: Medium" in markdown
    assert "Pikafish prefers `h0g2`" in markdown


def test_report_can_render_precomputed_verified_explanations():
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
    sample = build_explanation_samples(analysis, mistakes)[0]
    verified = [
        VerifiedExplanation(
            sample=sample,
            candidate=ExplanationCandidate(
                provider="test",
                text="Pikafish prefers h0g2 because h2e2 lost 200 cp.",
            ),
            status="PASS",
            confidence="Medium",
        )
    ]

    markdown = render_markdown_report(
        analysis,
        mistakes,
        verified_explanations=verified,
    )

    assert "## Verified Explanations" in markdown
    assert "Pikafish prefers h0g2" in markdown
    assert "Status: PASS" in markdown
