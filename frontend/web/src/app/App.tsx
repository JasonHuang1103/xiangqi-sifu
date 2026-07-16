import { useState } from "react";

import { analyzePosition, askCoach, createCoachThread, createGame } from "./api";
import type { CoachMessage, GameView, StudySession } from "./types";
import { Launchpad } from "../components/Launchpad";
import { Workspace } from "../components/Workspace";
import { LibraryFlow } from "../features/library/LibraryFlow";
import { PositionFlow } from "../features/position/PositionFlow";
import { ReviewFlow } from "../features/review/ReviewFlow";
import { sessionFromPositions } from "../features/study";

type Intake = "position" | "record" | "library";

export function App() {
  const [game, setGame] = useState<GameView | null>(null);
  const [intake, setIntake] = useState<Intake | null>(null);
  const [study, setStudy] = useState<StudySession | null>(null);
  const [messages, setMessages] = useState<CoachMessage[]>([]);
  const [threadId, setThreadId] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const choose = async (activity: "friend" | "sifu" | Intake) => {
    setError(null);
    if (activity === "position" || activity === "record" || activity === "library") {
      setIntake(activity);
      return;
    }
    setBusy(true);
    try {
      const created = await createGame(activity === "friend" ? { mode: "friend" } : { mode: "sifu", human_side: "w", ai_level: 5 });
      setGame(created);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The local service did not respond.");
    } finally {
      setBusy(false);
    }
  };

  const openStudy = (session: StudySession) => {
    setStudy(session);
    setMessages([]);
    setThreadId(null);
  };

  const closeWorkspace = () => {
    setGame(null);
    setStudy(null);
    setIntake(null);
    setMessages([]);
    setThreadId(null);
  };

  const ask = async (question: string) => {
    if (!study) return;
    setMessages((current) => [...current, { role: "user", content: question }]);
    try {
      let activeThread = threadId;
      if (activeThread === null) {
        const created = await createCoachThread({
          fen: study.game.current_fen,
          side_to_move: study.game.side_to_move,
          best_move: study.analysis.bestMove,
          red_score_cp: study.analysis.redScoreCp,
          mate_score: study.analysis.mateScore ?? null,
          pv: study.analysis.pv,
          selected_ply: study.selectedPly ?? 0,
        });
        activeThread = created.id;
        setThreadId(activeThread);
      }
      const response = await askCoach(activeThread, question);
      setMessages(response.messages.map((message) => ({ role: message.role, content: message.content })));
    } catch (caught) {
      setMessages((current) => [...current, { role: "assistant", content: caught instanceof Error ? caught.message : "Sifu could not answer." }]);
    }
  };

  const navigateStudy = async (ply: number) => {
    if (!study?.positions) return;
    const bounded = Math.max(0, Math.min(study.positions.length - 1, ply));
    const moves = study.game.moves.map((move) => move.uci);
    let positions = study.positions;
    setStudy(sessionFromPositions(study.title, study.source, positions, moves, bounded));
    setMessages([]);
    setThreadId(null);
    if (positions[bounded].lines.length === 0) {
      try {
        const result = await analyzePosition(positions[bounded].fen);
        positions = positions.map((position, index) => index === bounded ? { ...position, lines: result.lines } : position);
        setStudy(sessionFromPositions(study.title, study.source, positions, moves, bounded));
      } catch {
        // The board remains navigable even if a single engine request is interrupted.
      }
    }
  };

  if (game) {
    return <Workspace title={game.mode === "friend" ? "Friendly Match" : "Challenge Sifu"} game={game} onExit={closeWorkspace} />;
  }
  if (study) return <Workspace title={study.title} game={study.game} analysis={study.analysis} messages={messages} onAsk={ask} onExit={closeWorkspace} selectedPly={study.selectedPly} onNavigate={(ply) => void navigateStudy(ply)} positions={study.positions} />;
  if (intake) {
    if (intake === "position") return <PositionFlow onBack={() => setIntake(null)} onOpen={openStudy} />;
    if (intake === "record") return <ReviewFlow onBack={() => setIntake(null)} onOpen={openStudy} />;
    return <LibraryFlow onBack={() => setIntake(null)} onOpen={openStudy} />;
  }
  return <Launchpad onChoose={choose} busy={busy} error={error} />;
}
