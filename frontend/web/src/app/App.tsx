import { useState } from "react";

import { createGame } from "./api";
import type { GameView } from "./types";
import { Launchpad } from "../components/Launchpad";
import { Workspace } from "../components/Workspace";

type Intake = "position" | "record" | "library";

const intakeCopy: Record<Intake, { eyebrow: string; title: string; body: string }> = {
  position: { eyebrow: "ANALYZE", title: "Bring a position into the study", body: "Upload a digital board screenshot, paste FEN, or set the board manually." },
  record: { eyebrow: "REVIEW", title: "Open a game record", body: "Choose PGN, PGNS, or paste ICCS moves to begin." },
  library: { eyebrow: "TOURNAMENT LIBRARY", title: "Learn from master games", body: "Search the local tournament archive by player, event, or result." },
};


export function App() {
  const [game, setGame] = useState<GameView | null>(null);
  const [intake, setIntake] = useState<Intake | null>(null);
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

  if (game) {
    return <Workspace title={game.mode === "friend" ? "Friendly Match" : "Challenge Sifu"} game={game} onExit={() => setGame(null)} />;
  }
  if (intake) {
    const copy = intakeCopy[intake];
    return <main className="intake-page"><header className="launch-header"><button className="brand brand-button" type="button" onClick={() => setIntake(null)}><span className="brand-seal">師</span> XIANGQI SIFU</button></header><section className="intake-card"><p className="section-kicker">{copy.eyebrow}</p><h1>{copy.title}</h1><p>{copy.body}</p><button type="button" className="text-button" onClick={() => setIntake(null)}>← Back to the studio</button></section></main>;
  }
  return <Launchpad onChoose={choose} busy={busy} error={error} />;
}
