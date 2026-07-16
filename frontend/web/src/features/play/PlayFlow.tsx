import { useEffect, useRef, useState } from "react";

import { analyzePosition, playMove, requestAiMove, resignGame, undoGame } from "../../app/api";
import type { AnalysisView, GameView } from "../../app/types";
import { Workspace } from "../../components/Workspace";


export function PlayFlow({ initialGame, onExit, onReview }: { initialGame: GameView; onExit: () => void; onReview: (game: GameView) => void }) {
  const [game, setGame] = useState(initialGame);
  const [selected, setSelected] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisView | null>(null);
  const openingReplyRequested = useRef(false);
  const humanColor = game.human_side === "b" ? "black" : "red";
  const aiTurn = game.mode === "sifu" && game.side_to_move !== humanColor;

  const askAiToMove = async (current: GameView) => {
    setBusy(true);
    try { setGame(await requestAiMove(current.id)); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "Sifu could not move."); }
    finally { setBusy(false); }
  };
  useEffect(() => {
    if (game.status === "active" && aiTurn && game.moves.length === 0 && !openingReplyRequested.current) {
      openingReplyRequested.current = true;
      void askAiToMove(game);
    }
  }, []);

  const clickSquare = async (square: string) => {
    if (busy || game.status !== "active" || aiTurn) return;
    const move = selected ? `${selected}${square}` : "";
    if (selected && game.legal_moves.includes(move)) {
      setBusy(true); setError(null); setSelected(null); setAnalysis(null);
      try {
        const moved = await playMove(game.id, move);
        setGame(moved);
        const movedHumanColor = moved.human_side === "b" ? "black" : "red";
        if (moved.mode === "sifu" && moved.status === "active" && moved.side_to_move !== movedHumanColor) await askAiToMove(moved);
      } catch (caught) { setError(caught instanceof Error ? caught.message : "That move was not accepted."); setBusy(false); }
      finally { setBusy(false); }
      return;
    }
    const piece = game.pieces[square];
    const ownsPiece = piece && (game.side_to_move === "red" ? piece === piece.toUpperCase() : piece === piece.toLowerCase());
    setSelected(ownsPiece && game.legal_moves.some((candidate) => candidate.startsWith(square)) ? square : null);
  };
  const targets = selected ? game.legal_moves.filter((move) => move.startsWith(selected)).map((move) => move.slice(2)) : [];

  const hint = async () => {
    setBusy(true); setError(null);
    try {
      const result = await analyzePosition(game.current_fen);
      const line = result.lines[0];
      setAnalysis({ redScoreCp: line?.red_score_cp ?? null, redWinRate: line?.estimated_red_win_rate ?? null, bestMove: line?.best_move ?? null, scoreChangeCp: null, pv: line?.pv ?? [], mateScore: line?.mate_score ?? null });
    } catch (caught) { setError(caught instanceof Error ? caught.message : "A hint is unavailable."); }
    finally { setBusy(false); }
  };
  const undo = async () => { setBusy(true); setError(null); try { setGame(await undoGame(game.id)); setSelected(null); setAnalysis(null); } catch (caught) { setError(caught instanceof Error ? caught.message : "Nothing to undo."); } finally { setBusy(false); } };
  const resign = async () => { setBusy(true); setError(null); try { setGame(await resignGame(game.id)); } catch (caught) { setError(caught instanceof Error ? caught.message : "The game could not be resigned."); } finally { setBusy(false); } };

  const label = game.mode === "friend" ? `${game.red_name || "Red"} — ${game.black_name || "Black"}` : `Level ${game.ai_level}${game.ai_adaptive ? " · Adaptive" : ""}`;
  return <Workspace title={label} game={game} analysis={analysis} onExit={onExit} selectedSquare={selected} legalTargets={targets} onSquareClick={(square) => void clickSquare(square)} notice={error || (busy ? (aiTurn ? "Sifu is considering the position…" : "Saving the move…") : null)} toolbarActions={game.status === "completed" ? [{ label: "Review game", onClick: () => onReview(game) }] : [{ label: "Hint", onClick: () => void hint(), disabled: busy }, { label: "Undo", onClick: () => void undo(), disabled: busy || game.moves.length === 0 }, { label: "Resign", onClick: () => void resign(), disabled: busy }]} />;
}
