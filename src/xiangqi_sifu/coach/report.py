from __future__ import annotations

import json

from xiangqi_sifu.coach.explanation import explain_mistake
from xiangqi_sifu.coach.mistake_detector import Mistake
from xiangqi_sifu.engine.analysis import AnalysisResult
from xiangqi_sifu.parsers.base import ParsedMove


def render_markdown_report(analysis: AnalysisResult, mistakes: list[Mistake]) -> str:
    game = analysis.game
    title = _game_title(game.red, game.black)
    lines = [
        "# Xiangqi Sifu Review",
        "",
        f"**Game:** {title}",
        f"**Result:** {game.result or '-'}",
        "",
        "## Move List",
        "",
        "| Move | Side | Played |",
        "|---:|---|---|",
    ]
    for move in game.moves:
        lines.append(f"| {move.move_number} | {move.side} | {move.uci} |")

    timeline = [
        {"ply": evaluation.ply, "red_score_cp": evaluation.red_score_cp}
        for evaluation in analysis.evaluations
    ]
    impact_rows = build_move_impact_rows(analysis)
    lines.extend(
        [
            "",
            "## Position Eval Data",
            "",
            "`red_score_cp` is the current board evaluation from Red's perspective. Positive values favor Red; negative values favor Black. It is not a per-move delta.",
            "",
            "```json",
            json.dumps(timeline, indent=2),
            "```",
            "",
            "## Move Impact Data",
            "",
            "| Move | Side | Played | Eval Before | Eval After | Red Delta | Mover Loss | Best Move |",
            "|---:|---|---|---:|---:|---:|---:|---|",
        ]
    )
    for row in impact_rows:
        lines.append(
            "| "
            f"{row['move']} | {row['side']} | {row['played']} | "
            f"{_format_nullable_cp(row['eval_before_cp'])} | "
            f"{_format_nullable_cp(row['eval_after_cp'])} | "
            f"{_format_nullable_cp(row['red_delta_cp'])} | "
            f"{row['mover_loss_cp']} | {row['best_move'] or '-'} |"
        )

    lines.extend(
        [
            "",
            "## Mistake Timeline",
            "",
            "| Move | Side | Played | Severity | Eval Before | Eval After | Loss | Best Move |",
            "|---:|---|---|---|---:|---:|---:|---|",
        ]
    )
    for mistake in mistakes:
        lines.append(
            "| "
            f"{mistake.move_number} | {mistake.side} | {mistake.played_move} | "
            f"{mistake.severity} | {_format_cp(mistake.eval_before_cp)} | "
            f"{_format_cp(mistake.eval_after_cp)} | {mistake.eval_loss_cp} | "
            f"{mistake.best_move or '-'} |"
        )
    if not mistakes:
        lines.append("| - | - | - | - | - | - | - | - |")

    lines.extend(["", "## Explanation Stubs", ""])
    if mistakes:
        for mistake in mistakes:
            lines.append(
                f"- Move {mistake.move_number}: `{mistake.played_move}` was likely a "
                f"{mistake.severity}. Engine eval changed from "
                f"{_format_cp(mistake.eval_before_cp)} to {_format_cp(mistake.eval_after_cp)}. "
                f"Best move: `{mistake.best_move or '-'}`. {explain_mistake(mistake)}"
            )
    else:
        lines.append("- No mistakes crossed the configured threshold.")
    lines.append("")
    return "\n".join(lines)


def build_move_impact_rows(analysis: AnalysisResult) -> list[dict[str, object]]:
    rows = []
    for index, move in enumerate(analysis.game.moves):
        before = analysis.evaluations[index] if index < len(analysis.evaluations) else None
        after = analysis.evaluations[index + 1] if index + 1 < len(analysis.evaluations) else None
        before_score = before.red_score_cp if before is not None else None
        after_score = after.red_score_cp if after is not None else None
        red_delta = _nullable_delta(before_score, after_score)
        rows.append(
            {
                "ply": index + 1,
                "move": move.move_number,
                "side": move.side,
                "played": move.uci,
                "iccs": move.iccs,
                "eval_before_cp": before_score,
                "eval_after_cp": after_score,
                "red_delta_cp": red_delta,
                "mover_loss_cp": _mover_loss(move, red_delta),
                "best_move": before.best_move if before is not None else None,
            }
        )
    return rows


def _game_title(red: str | None, black: str | None) -> str:
    return f"{red or 'Red'} vs {black or 'Black'}"


def _format_cp(score: int) -> str:
    return f"+{score}" if score > 0 else str(score)


def _format_nullable_cp(score: int | None) -> str:
    return "-" if score is None else _format_cp(score)


def _nullable_delta(before_score: int | None, after_score: int | None) -> int | None:
    if before_score is None or after_score is None:
        return None
    return after_score - before_score


def _mover_loss(move: ParsedMove, red_delta: int | None) -> int | None:
    if red_delta is None:
        return None
    if move.side == "red":
        return max(0, -red_delta)
    if move.side == "black":
        return max(0, red_delta)
    return None
