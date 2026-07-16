from xiangqi_sifu.coach.chat import CoachContext, CoachService


def test_deterministic_coach_names_engine_move_and_score_direction():
    service = CoachService()
    context = CoachContext(
        fen="position",
        side_to_move="red",
        best_move="h0g2",
        red_score_cp=130,
        mate_score=None,
        pv=("h0g2", "b9c7"),
    )

    reply = service.reply(context, "Why is this move best?")

    assert reply.provider == "deterministic"
    assert reply.grounded is True
    assert "h0g2" in reply.text
    assert "Red" in reply.text
    assert "130 cp" in reply.text


def test_deterministic_coach_uses_mate_language_only_with_mate_score():
    service = CoachService()
    normal = CoachContext("position", "black", "b9c7", -40, None, ("b9c7",))
    mate = CoachContext("position", "red", "e0e9", None, 3, ("e0e9",))

    assert "forced mate" not in service.reply(normal, "What happens?").text.lower()
    assert "forced mate" in service.reply(mate, "What happens?").text.lower()
