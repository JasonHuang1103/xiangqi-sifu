import { useState } from "react";

import type { AnalysisView, AnalyzedPosition, CoachMessage, GameView } from "../app/types";
import { AnalysisRibbon } from "./AnalysisRibbon";
import { CoachPanel } from "./CoachPanel";
import { EvaluationChart } from "./EvaluationChart";
import { XiangqiBoard } from "./XiangqiBoard";

interface WorkspaceProps {
  title: string;
  game: GameView;
  analysis?: AnalysisView | null;
  messages?: CoachMessage[];
  onExit: () => void;
  onMove?: (uci: string) => void;
  onAsk?: (question: string) => Promise<void> | void;
  selectedPly?: number;
  onNavigate?: (ply: number) => void;
  positions?: AnalyzedPosition[];
  selectedSquare?: string | null;
  legalTargets?: string[];
  onSquareClick?: (square: string) => void;
  toolbarActions?: { label: string; onClick: () => void; disabled?: boolean; active?: boolean }[];
  notice?: string | null;
}


export function Workspace({ title, game, analysis = null, messages = [], onExit, onAsk, selectedPly = game.moves.length, onNavigate, positions, selectedSquare, legalTargets = [], onSquareClick, toolbarActions = [], notice }: WorkspaceProps) {
  const [analysisVisible, setAnalysisVisible] = useState(Boolean(analysis));
  const [flipped, setFlipped] = useState(false);
  const selectedPosition = positions?.find((position) => position.ply === selectedPly);
  const selectedMove = selectedPly > 0
    ? selectedPosition?.played_move ?? game.moves.find((move) => move.ply === selectedPly)?.uci ?? null
    : null;
  return (
    <main className="workspace-shell">
      <header className="workspace-topbar">
        <button className="brand brand-button" type="button" onClick={onExit}><span className="brand-seal" aria-hidden="true">師</span><span>XIANGQI SIFU</span></button>
        <div className="workspace-mode"><span className="active">Analyze</span><span>Play</span></div>
        <div className="engine-ready"><span /> Pikafish ready</div>
      </header>
      <div className="workspace-grid">
        <nav className="workspace-nav" aria-label="Workspace navigation">
          <p>WORKSPACE</p><button className="active" type="button"><span>局</span>Position</button><button type="button"><span>譜</span>Game review</button><button type="button"><span>戰</span>Play Sifu</button>
          <p>LIBRARY</p><button type="button"><span>時</span>Sessions</button><button type="button"><span>書</span>Patterns</button>
        </nav>
        <section className="board-workspace">
          <header className="board-heading"><div><p className="section-kicker">{game.mode === "friend" ? "FRIENDLY MATCH" : game.mode === "sifu" ? "CHALLENGE SIFU" : "POSITION ANALYSIS"}</p><h1>{title}</h1><p className="board-notice" role="status" aria-hidden={!notice}>{notice || "\u00a0"}</p></div><div className="board-tools"><button type="button" onClick={() => setFlipped((value) => !value)}>Flip</button>{analysis && <button type="button" className={analysisVisible ? "active" : ""} onClick={() => setAnalysisVisible((value) => !value)}>{analysisVisible ? "Analysis on" : "Analysis off"}</button>}{toolbarActions.map((action) => <button type="button" key={action.label} onClick={action.onClick} disabled={action.disabled} className={action.active ? "active" : ""}>{action.label}</button>)}<button type="button" onClick={onExit}>New</button></div></header>
          <div data-testid="analysis-slot" className={`analysis-slot ${analysis && analysisVisible ? "" : "analysis-slot-hidden"}`} aria-hidden={!analysis || !analysisVisible}>
            {analysis && <AnalysisRibbon analysis={analysis} />}
          </div>
          <div className="board-stage"><div className="turn-label"><span className={game.side_to_move} /> {game.status === "completed" ? `GAME OVER · ${game.result ?? "DRAW"}` : `${game.side_to_move.toUpperCase()} TO MOVE`}</div><XiangqiBoard pieces={game.pieces} bestMove={analysis?.bestMove} lastMove={selectedMove} showAnalysis={analysisVisible} flipped={flipped} selectedSquare={selectedSquare} legalTargets={legalTargets} onSquareClick={onSquareClick} /></div>
          <div>{positions && positions.length > 1 && onNavigate && <EvaluationChart positions={positions} selectedPly={selectedPly} onSelect={onNavigate} />}<footer className="move-footer"><button type="button" aria-label="First move" onClick={() => onNavigate?.(0)} disabled={!onNavigate || selectedPly === 0}>|‹</button><button type="button" aria-label="Previous move" onClick={() => onNavigate?.(selectedPly - 1)} disabled={!onNavigate || selectedPly === 0}>‹</button><div className="move-track"><i style={{ width: `${game.moves.length ? Math.round(selectedPly / game.moves.length * 100) : 0}%` }} /></div><span>{selectedPly} / {game.moves.length} moves</span><button type="button" aria-label="Next move" onClick={() => onNavigate?.(selectedPly + 1)} disabled={!onNavigate || selectedPly >= game.moves.length}>›</button><button type="button" aria-label="Last move" onClick={() => onNavigate?.(game.moves.length)} disabled={!onNavigate || selectedPly >= game.moves.length}>›|</button></footer></div>
        </section>
        <CoachPanel messages={messages} onSend={onAsk} />
      </div>
    </main>
  );
}
