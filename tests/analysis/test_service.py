import pytest

from xiangqi_sifu.analysis.service import estimated_red_win_rate, move_impact


def test_win_rate_is_monotonic_centered_and_symmetric():
    losing = estimated_red_win_rate(-300)
    equal = estimated_red_win_rate(0)
    winning = estimated_red_win_rate(300)

    assert losing < equal < winning
    assert equal == 0.5
    assert losing + winning == pytest.approx(1.0, abs=0.0001)


def test_mate_has_no_centipawn_win_rate():
    assert estimated_red_win_rate(None) is None


def test_move_impact_is_adjusted_for_side_that_moved():
    red_loss = move_impact(before_red_cp=100, after_red_cp=20, side="red")
    black_loss = move_impact(before_red_cp=20, after_red_cp=100, side="black")

    assert red_loss.score_change_cp == -80
    assert red_loss.mover_loss_cp == 80
    assert red_loss.classification == "inaccuracy"
    assert black_loss.score_change_cp == -80
    assert black_loss.mover_loss_cp == 80
    assert black_loss.classification == "inaccuracy"


def test_move_impact_does_not_report_negative_loss_for_improvement():
    impact = move_impact(before_red_cp=0, after_red_cp=120, side="red")

    assert impact.score_change_cp == 120
    assert impact.mover_loss_cp == 0
    assert impact.classification == "best"
