import { useEffect, useState } from "react";

import { analyzeGame, getReferenceGame, searchReferenceGames } from "../../app/api";
import type { ReferenceGameSummary, StudySession } from "../../app/types";
import { sessionFromPositions } from "../study";

interface LibraryFlowProps {
  onBack: () => void;
  onOpen: (session: StudySession) => void;
}


export function LibraryFlow({ onBack, onOpen }: LibraryFlowProps) {
  const [query, setQuery] = useState("");
  const [games, setGames] = useState<ReferenceGameSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const search = async (value = query) => {
    setBusy(true);
    setError(null);
    try {
      const result = await searchReferenceGames(value);
      setGames(result.games);
      setTotal(result.total);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The archive could not be opened.");
    } finally {
      setBusy(false);
    }
  };
  useEffect(() => { void search(""); }, []);

  const open = async (summary: ReferenceGameSummary) => {
    setBusy(true);
    try {
      const detail = await getReferenceGame(summary.id);
      const moves = detail.record.moves.map((move) => move.uci);
      const result = await analyzeGame(detail.record.starting_fen, moves);
      onOpen(sessionFromPositions(`${summary.red || "Red"} — ${summary.black || "Black"}`, "reference", result.positions, moves));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The master game could not be opened.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="library-page">
      <header className="launch-header"><button className="brand brand-button" type="button" onClick={onBack}><span className="brand-seal">師</span> XIANGQI SIFU</button><span className="local-status"><span /> Read-only archive</span></header>
      <section className="library-heading"><p className="section-kicker">TOURNAMENT LIBRARY</p><h1>Study the masters.</h1><p>{total.toLocaleString()} tournament games, kept apart from your personal game history.</p><form onSubmit={(event) => { event.preventDefault(); void search(); }}><label className="sr-only" htmlFor="library-search">Search tournament games</label><input id="library-search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Player, event, or result" /><button type="submit">Search</button></form></section>
      {error && <p className="form-error library-error" role="alert">{error}</p>}
      <section className="library-list" aria-busy={busy}>{games.map((game) => <button type="button" key={game.id} onClick={() => void open(game)}><span className="library-corpus">{game.corpus_name}</span><span><strong>{game.red || "Unknown Red"}</strong><i>versus</i><strong>{game.black || "Unknown Black"}</strong></span><small>{game.event || "Tournament game"} · {game.move_count} moves</small><b>{game.result || "*"}</b></button>)}{busy && <p className="library-loading">Opening the archive…</p>}</section>
      <button type="button" className="text-button library-back" onClick={onBack}>← Back to the studio</button>
    </main>
  );
}
