from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from xiangqi_sifu.coach.mistake_detector import MistakeThresholds, detect_mistakes
from xiangqi_sifu.coach.report import build_move_impact_rows, render_markdown_report
from xiangqi_sifu.database.repository import AnalysisRepository
from xiangqi_sifu.engine.analysis import MockEngine, analyze_game
from xiangqi_sifu.engine.pikafish import PikafishEngine
from xiangqi_sifu.parsers.pgn_parser import PgnParser
from xiangqi_sifu.parsers.simple_move_parser import SimpleMoveParser


@dataclass(frozen=True)
class ReviewViewModel:
    game_id: int
    move_rows: list[dict[str, Any]]
    eval_rows: list[dict[str, Any]]
    impact_rows: list[dict[str, Any]]
    mistake_rows: list[dict[str, Any]]
    report_markdown: str


def decode_uploaded_bytes(raw: bytes) -> str:
    return raw.decode("utf-8-sig")


def run_review_from_text(
    game_text: str,
    *,
    engine_value: str,
    db_path: str | Path,
    depth: int,
    movetime_ms: int | None = None,
    thresholds: MistakeThresholds | None = None,
) -> ReviewViewModel:
    game = _parse_game_text(game_text)
    engine = _build_engine(engine_value, depth=depth, movetime_ms=movetime_ms)
    try:
        analysis = analyze_game(game, engine)
    finally:
        close = getattr(engine, "close", None)
        if close is not None:
            close()

    mistakes = detect_mistakes(game.moves, analysis.evaluations, thresholds or MistakeThresholds())
    game_id = AnalysisRepository(db_path).save_analysis(analysis, mistakes)
    report = render_markdown_report(analysis, mistakes)
    impact_rows = build_move_impact_rows(analysis)
    return ReviewViewModel(
        game_id=game_id,
        move_rows=[
            {
                "move": move.move_number,
                "side": move.side,
                "played": move.uci,
                "iccs": move.iccs,
            }
            for move in game.moves
        ],
        eval_rows=[
            {
                "ply": evaluation.ply,
                "red_score_cp": evaluation.red_score_cp,
                "best_move": evaluation.best_move,
            }
            for evaluation in analysis.evaluations
        ],
        impact_rows=impact_rows,
        mistake_rows=[
            {
                "move": mistake.move_number,
                "side": mistake.side,
                "played": mistake.played_move,
                "severity": mistake.severity,
                "eval_before": mistake.eval_before_cp,
                "eval_after": mistake.eval_after_cp,
                "loss": mistake.eval_loss_cp,
                "best_move": mistake.best_move,
            }
            for mistake in mistakes
        ],
        report_markdown=f"<!-- saved_game_id: {game_id} -->\n\n{report}",
    )


def main() -> None:
    import streamlit as st

    st.set_page_config(page_title="Xiangqi Sifu", page_icon="XS", layout="wide")
    st.title("Xiangqi Sifu")
    st.caption("Phase 1 personal game review: upload one game, analyze positions, and review engine-backed mistakes.")

    with st.sidebar:
        st.header("Analysis Settings")
        engine_value = st.text_input(
            "Engine",
            value="mock",
            help="Use 'mock' for a fast dry run, or enter a Pikafish binary path.",
        )
        db_path = st.text_input("SQLite DB", value="data/processed/xiangqi_sifu.db")
        depth = st.number_input("Depth", min_value=1, max_value=30, value=8, step=1)
        movetime_ms = st.number_input(
            "Movetime ms",
            min_value=0,
            value=0,
            step=100,
            help="Leave at 0 to use depth.",
        )
        inaccuracy_cp = st.number_input("Inaccuracy cp", min_value=1, value=80, step=10)
        mistake_cp = st.number_input("Mistake cp", min_value=1, value=150, step=10)
        blunder_cp = st.number_input("Blunder cp", min_value=1, value=300, step=10)

    uploaded_file = st.file_uploader("Upload a Xiangqi game", type=["txt", "pgn", "pgns"])
    sample_text = Path("data/examples/simple_game.txt").read_text(encoding="utf-8")
    game_text = st.text_area(
        "Game text",
        value=sample_text,
        height=160,
        help="Paste ICCS coordinate moves or PGN-like text with ICCS moves.",
    )
    if uploaded_file is not None:
        game_text = decode_uploaded_bytes(uploaded_file.getvalue())
        st.text_area("Uploaded game preview", value=game_text, height=160, disabled=True)

    if st.button("Analyze Game", type="primary"):
        if not game_text.strip():
            st.error("Upload or paste a game before running analysis.")
            return
        with st.spinner("Analyzing game..."):
            review = run_review_from_text(
                game_text,
                engine_value=engine_value.strip() or "mock",
                db_path=db_path,
                depth=int(depth),
                movetime_ms=int(movetime_ms) if int(movetime_ms) > 0 else None,
                thresholds=MistakeThresholds(
                    inaccuracy_cp=int(inaccuracy_cp),
                    mistake_cp=int(mistake_cp),
                    blunder_cp=int(blunder_cp),
                ),
            )
        _render_review(st, review)


def _parse_game_text(game_text: str):
    if "[Game" in game_text or "[FEN" in game_text:
        return PgnParser().parse_text(game_text)
    return SimpleMoveParser().parse_text(game_text)


def _build_engine(engine_value: str, *, depth: int, movetime_ms: int | None):
    if engine_value == "mock":
        return MockEngine()
    return PikafishEngine(engine_value, depth=depth, movetime_ms=movetime_ms)


def _render_review(st, review: ReviewViewModel) -> None:
    st.success(f"Analysis saved as game #{review.game_id}.")
    metrics = st.columns(3)
    metrics[0].metric("Moves", len(review.move_rows))
    metrics[1].metric("Evaluations", len(review.eval_rows))
    metrics[2].metric("Mistakes", len(review.mistake_rows))

    tab_moves, tab_eval, tab_impact, tab_mistakes, tab_report = st.tabs(
        ["Move List", "Position Eval", "Move Impact", "Mistakes", "Markdown Report"]
    )
    with tab_moves:
        st.dataframe(review.move_rows, use_container_width=True, hide_index=True)
    with tab_eval:
        st.caption("Position eval is the current board evaluation from Red's perspective, not the per-move change.")
        st.line_chart(review.eval_rows, x="ply", y="red_score_cp")
        st.dataframe(review.eval_rows, use_container_width=True, hide_index=True)
    with tab_impact:
        st.caption("Move impact compares the eval before and after each move. Mover loss is adjusted for the side that moved.")
        st.dataframe(review.impact_rows, use_container_width=True, hide_index=True)
    with tab_mistakes:
        if review.mistake_rows:
            st.dataframe(review.mistake_rows, use_container_width=True, hide_index=True)
        else:
            st.info("No moves crossed the configured mistake thresholds.")
    with tab_report:
        st.markdown(review.report_markdown)
        st.download_button(
            "Download Markdown Report",
            data=review.report_markdown,
            file_name="xiangqi_sifu_report.md",
            mime="text/markdown",
        )


if __name__ == "__main__":
    main()
