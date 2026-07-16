from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class CoachContext:
    fen: str
    side_to_move: str
    best_move: str | None
    red_score_cp: int | None
    mate_score: int | None
    pv: tuple[str, ...] = field(default_factory=tuple)
    selected_ply: int | None = None
    played_move: str | None = None
    mover_loss_cp: int | None = None


@dataclass(frozen=True)
class CoachReply:
    text: str
    provider: str
    grounded: bool


class ChatProvider(Protocol):
    def reply(self, context: CoachContext, question: str) -> CoachReply:
        ...


class CoachService:
    def __init__(self, provider: ChatProvider | None = None) -> None:
        self.provider = provider

    def reply(self, context: CoachContext, question: str) -> CoachReply:
        if not question.strip():
            raise ValueError("Coach question cannot be empty")
        if self.provider is not None:
            try:
                candidate = self.provider.reply(context, question)
                if _is_grounded(candidate.text, context):
                    return CoachReply(candidate.text.strip(), candidate.provider, True)
            except Exception:
                pass
        return CoachReply(_deterministic_text(context), "deterministic", True)


def _deterministic_text(context: CoachContext) -> str:
    best_move = context.best_move or "no legal engine move"
    parts = [f"Pikafish's first choice is `{best_move}`."]
    if context.mate_score is not None:
        side = "Red" if context.mate_score > 0 else "Black"
        parts.append(f"The engine reports a forced mate for {side} in {abs(context.mate_score)}.")
    elif context.red_score_cp is not None:
        if context.red_score_cp > 0:
            parts.append(f"The current score favors Red by {context.red_score_cp} cp.")
        elif context.red_score_cp < 0:
            parts.append(f"The current score favors Black by {abs(context.red_score_cp)} cp.")
        else:
            parts.append("The current engine score is equal at 0 cp.")
    if context.played_move and context.mover_loss_cp is not None:
        parts.append(
            f"The played move `{context.played_move}` gave up {context.mover_loss_cp} cp for the mover."
        )
    if context.pv:
        parts.append(f"A concrete line to study is `{' '.join(context.pv)}`.")
    parts.append(
        "This explanation stays with the engine evidence; a deeper tactical label needs support from the shown line."
    )
    return " ".join(parts)


def _is_grounded(text: str, context: CoachContext) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    if context.best_move and context.best_move not in stripped:
        return False
    lowered = stripped.lower()
    if context.mate_score is None and ("forced mate" in lowered or "checkmate" in lowered):
        return False
    return True
