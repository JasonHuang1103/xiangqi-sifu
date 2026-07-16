import { useState } from "react";

import { analyzeGame, inspectRecord } from "../../app/api";
import type { InspectedGame, StudySession } from "../../app/types";
import { sessionFromPositions } from "../study";

interface ReviewFlowProps {
  onBack: () => void;
  onOpen: (session: StudySession) => void;
}


export function ReviewFlow({ onBack, onOpen }: ReviewFlowProps) {
  const [text, setText] = useState("");
  const [games, setGames] = useState<InspectedGame[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const readFile = async (file?: File) => {
    if (file) setText(await file.text());
  };

  const open = async (game: InspectedGame) => {
    setBusy(true);
    setError(null);
    try {
      const result = await analyzeGame(game.starting_fen, game.moves);
      const names = [game.red, game.black].filter(Boolean).join(" — ");
      onOpen(sessionFromPositions(names || game.event || "Imported game", "upload", result.positions, game.moves));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The selected game could not be analyzed.");
    } finally {
      setBusy(false);
    }
  };

  const inspect = async () => {
    setBusy(true);
    setError(null);
    try {
      const result = await inspectRecord(text);
      setGames(result.games);
      if (!result.requires_selection && result.games[0]) await open(result.games[0]);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The record could not be read.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="intake-page">
      <header className="launch-header"><button className="brand brand-button" type="button" onClick={onBack}><span className="brand-seal">師</span> XIANGQI SIFU</button><span className="local-status"><span /> PGN · PGNS · ICCS</span></header>
      <section className="intake-layout">
        <div className="intake-intro"><p className="section-kicker">REVIEW A RECORD</p><h1>Revisit every<br />turning point.</h1><p>Import one game or an entire PGNS file. Multi-game records remain separate until you choose the game to study.</p><button type="button" className="text-button" onClick={onBack}>← Back to the studio</button></div>
        <div className="intake-form">
          <label className="drop-zone"><strong>Choose a record file</strong><span>.pgn, .pgns, or a text record in ICCS notation</span><input type="file" accept=".pgn,.pgns,.txt" onChange={(event) => void readFile(event.target.files?.[0])} /></label>
          <div className="form-divider"><span>OR PASTE THE RECORD</span></div>
          <label className="field-label" htmlFor="game-record">Game record</label>
          <textarea id="game-record" rows={9} value={text} onChange={(event) => setText(event.target.value)} placeholder={'[Event "Club championship"]\n1. H2-E2 B9-C7'} />
          {error && <p className="form-error" role="alert">{error}</p>}
          <button className="primary-button" type="button" disabled={busy || !text.trim()} onClick={() => void inspect()}>{busy ? "Reading record…" : "Inspect record"}</button>
          {games.length > 1 && <div className="record-picker"><p className="field-label">CHOOSE A GAME</p>{games.map((game) => <button type="button" key={game.index} onClick={() => void open(game)}><span><strong>{game.red || "Unknown Red"} — {game.black || "Unknown Black"}</strong><small>{game.event || "Recorded game"} · {game.move_count} moves</small></span><b>{game.result || "*"}</b></button>)}</div>}
        </div>
      </section>
    </main>
  );
}
