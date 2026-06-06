from xiangqi_sifu.coach.mistake_detector import MistakeThresholds, detect_mistakes
from xiangqi_sifu.engine.analysis import Evaluation
from xiangqi_sifu.parsers.base import ParsedMove


def test_detect_mistakes_classifies_red_eval_loss():
    moves = [
        ParsedMove(iccs="H2-E2", uci="h2e2", move_number=1, side="red"),
    ]
    evaluations = [
        Evaluation(ply=0, fen="start", red_score_cp=120, best_move="h0g2"),
        Evaluation(ply=1, fen="after", red_score_cp=-80, best_move="b9c7"),
    ]

    mistakes = detect_mistakes(moves, evaluations, MistakeThresholds())

    assert len(mistakes) == 1
    assert mistakes[0].severity == "mistake"
    assert mistakes[0].eval_loss_cp == 200
    assert mistakes[0].best_move == "h0g2"


def test_detect_mistakes_uses_black_perspective_for_black_moves():
    moves = [
        ParsedMove(iccs="H2-E2", uci="h2e2", move_number=1, side="red"),
        ParsedMove(iccs="B9-C7", uci="b9c7", move_number=1, side="black"),
    ]
    evaluations = [
        Evaluation(ply=0, fen="start", red_score_cp=0, best_move="h2e2"),
        Evaluation(ply=1, fen="after-red", red_score_cp=-50, best_move="b9a7"),
        Evaluation(ply=2, fen="after-black", red_score_cp=290, best_move="h0g2"),
    ]

    mistakes = detect_mistakes(moves, evaluations, MistakeThresholds())

    assert len(mistakes) == 1
    assert mistakes[0].side == "black"
    assert mistakes[0].severity == "blunder"
    assert mistakes[0].eval_loss_cp == 340


def test_detect_mistakes_suppresses_when_best_move_matches_played_move():
    moves = [
        ParsedMove(iccs="H2-E2", uci="h2e2", move_number=1, side="red"),
    ]
    evaluations = [
        Evaluation(ply=0, fen="start", red_score_cp=300, best_move="h2e2"),
        Evaluation(ply=1, fen="after", red_score_cp=20, best_move="b9c7"),
    ]

    mistakes = detect_mistakes(moves, evaluations, MistakeThresholds())

    assert mistakes == []
