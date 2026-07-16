import { useState } from "react";

import type { AnalysisView, CoachMessage, GameView } from "../app/types";
import { AnalysisRibbon } from "./AnalysisRibbon";
import { CoachPanel } from "./CoachPanel";
import { XiangqiBoard } from "./XiangqiBoard";

interface WorkspaceProps {
  title: string;
  game: GameView;
  analysis?: AnalysisView | null;
  messages?: CoachMessage[];
  onExit: () => void;
  onMove?: (uci: string) => void;
  onAsk?: (question: string) => Promise<void> | void;
}


export function Workspace({ title, game, analysis = null, messages = [], onExit, onAsk }: WorkspaceProps) {
  const [analysisVisible, setAnalysisVisible] = useState(Boolean(analysis));
  const [flipped, setFlipped] = useState(false);
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
          <header className="board-heading"><div><p className="section-kicker">{game.mode === "friend" ? "FRIENDLY MATCH" : "POSITION ANALYSIS"}</p><h1>{title}</h1></div><div className="board-tools"><button type="button" onClick={() => setFlipped((value) => !value)}>Flip</button>{analysis && <button type="button" className={analysisVisible ? "active" : ""} onClick={() => setAnalysisVisible((value) => !value)}>{analysisVisible ? "Analysis on" : "Analysis off"}</button>}<button type="button">Edit</button><button type="button" onClick={onExit}>New</button></div></header>
          {analysis && analysisVisible && <AnalysisRibbon analysis={analysis} />}
          <div className="board-stage"><div className="turn-label"><span className={game.side_to_move} /> {game.side_to_move.toUpperCase()} TO MOVE</div><XiangqiBoard pieces={game.pieces} bestMove={analysis?.bestMove} showAnalysis={analysisVisible} flipped={flipped} /></div>
          <footer className="move-footer"><button type="button" aria-label="First move">|‹</button><button type="button" aria-label="Previous move">‹</button><div className="move-track"><i style={{ width: `${Math.min(100, game.moves.length * 4)}%` }} /></div><span>{game.moves.length} moves</span><button type="button" aria-label="Next move">›</button><button type="button" aria-label="Last move">›|</button></footer>
        </section>
        <CoachPanel messages={messages} onSend={onAsk} />
      </div>
    </main>
  );
}
