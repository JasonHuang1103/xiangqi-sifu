from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from xiangqi_sifu.api.dependencies import Services, get_services
from xiangqi_sifu.api.models import CoachMessageRequest, CoachThreadRequest
from xiangqi_sifu.api.serializers import coach_thread_dict
from xiangqi_sifu.coach.chat import CoachContext

router = APIRouter(prefix="/api")


@router.post("/coach/threads")
def create_thread(
    request: CoachThreadRequest,
    services: Services = Depends(get_services),
) -> dict:
    context = request.model_dump()
    thread = services.personal.create_coach_thread(
        context_fen=request.fen,
        context=context,
        game_id=request.game_id,
        selected_ply=request.selected_ply,
    )
    return coach_thread_dict(thread)


@router.post("/coach/threads/{thread_id}/messages")
def add_message(
    thread_id: int,
    request: CoachMessageRequest,
    services: Services = Depends(get_services),
) -> dict:
    try:
        thread = services.personal.append_coach_message(
            thread_id, role="user", content=request.question
        )
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    context = CoachContext(
        fen=thread.context["fen"],
        side_to_move=thread.context["side_to_move"],
        best_move=thread.context.get("best_move"),
        red_score_cp=thread.context.get("red_score_cp"),
        mate_score=thread.context.get("mate_score"),
        pv=tuple(thread.context.get("pv") or ()),
        selected_ply=thread.context.get("selected_ply"),
        played_move=thread.context.get("played_move"),
        mover_loss_cp=thread.context.get("mover_loss_cp"),
    )
    reply = services.coach.reply(context, request.question)
    thread = services.personal.append_coach_message(
        thread_id,
        role="assistant",
        content=reply.text,
        provider=reply.provider,
    )
    return {"reply": {"text": reply.text, "provider": reply.provider}, **coach_thread_dict(thread)}
