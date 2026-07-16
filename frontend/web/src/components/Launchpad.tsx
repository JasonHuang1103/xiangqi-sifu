import type { GameView } from "../app/types";

type Activity = "friend" | "sifu" | "position" | "record" | "library";

interface LaunchpadProps {
  onChoose: (activity: Activity) => void;
  busy?: boolean;
  error?: string | null;
  savedGames?: GameView[];
  onResume?: (game: GameView) => void;
}

const studyActions: Array<{ id: Activity; eyebrow: string; title: string; description: string }> = [
  {
    id: "position",
    eyebrow: "POSITION",
    title: "Analyze a Position",
    description: "Bring a screenshot, FEN, or arrange the pieces yourself.",
  },
  {
    id: "record",
    eyebrow: "REVIEW",
    title: "Review a Record",
    description: "Open PGN, PGNS, or ICCS and study every turning point.",
  },
  {
    id: "library",
    eyebrow: "ARCHIVE",
    title: "Tournament Library",
    description: "Search 141,511 master games from the local collection.",
  },
];


export function Launchpad({ onChoose, busy = false, error = null, savedGames = [], onResume }: LaunchpadProps) {
  return (
    <main className="launchpad">
      <header className="launch-header">
        <a className="brand" href="#" aria-label="Xiangqi Sifu home">
          <span className="brand-seal" aria-hidden="true">師</span>
          <span>XIANGQI SIFU</span>
        </a>
        <div className="local-status"><span aria-hidden="true" /> Local-first · private by design</div>
      </header>

      <section className="launch-hero" aria-labelledby="launch-title">
        <p className="section-kicker">YOUR PERSONAL XIANGQI MASTER</p>
        <h1 id="launch-title">Every position<br />has a lesson.</h1>
        <p className="hero-copy">
          Play, review, and understand your games with local engine analysis and a coach that stays grounded in the board.
        </p>
      </section>

      <section className="launch-section" aria-labelledby="new-game-title">
        <div className="section-heading">
          <div><p className="section-kicker">NEW GAME</p><h2 id="new-game-title">Take your seat</h2></div>
          <p>Start from the traditional position. Every move is saved as you play.</p>
        </div>
        <div className="play-actions">
          <button className="launch-action launch-action-primary" aria-label="Play a Friend" onClick={() => onChoose("friend")} disabled={busy}>
            <span className="action-icon" aria-hidden="true">友</span>
            <span><strong>Play a Friend</strong><small>Local, same-device match</small></span>
            <span className="action-arrow" aria-hidden="true">↗</span>
          </button>
          <button className="launch-action launch-action-sifu" aria-label="Challenge Sifu" onClick={() => onChoose("sifu")} disabled={busy}>
            <span className="action-icon" aria-hidden="true">將</span>
            <span><strong>Challenge Sifu</strong><small>Adjustable and adaptive AI</small></span>
            <span className="action-arrow" aria-hidden="true">↗</span>
          </button>
        </div>
      </section>

      <section className="launch-section study-section" aria-labelledby="study-title">
        <div className="section-heading">
          <div><p className="section-kicker">STUDY</p><h2 id="study-title">Enter the study</h2></div>
          <p>No board appears until you choose or load a game.</p>
        </div>
        <div className="study-actions">
          {studyActions.map((action) => (
            <button key={action.id} className="study-action" aria-label={action.title} onClick={() => onChoose(action.id)} disabled={busy}>
              <span className="study-eyebrow">{action.eyebrow}</span>
              <strong>{action.title}</strong>
              <small>{action.description}</small>
              <span className="study-link">Open <span aria-hidden="true">→</span></span>
            </button>
          ))}
        </div>
      </section>
      {savedGames.length > 0 && <section className="launch-section sessions-section" aria-labelledby="sessions-title"><div className="section-heading"><div><p className="section-kicker">PERSONAL DATABASE</p><h2 id="sessions-title">Your recent games</h2></div><p>Saved separately from the tournament library. Active games can be continued exactly where you left them.</p></div><div className="session-list">{savedGames.slice(0, 6).map((game) => <button type="button" key={game.id} onClick={() => onResume?.(game)}><span><strong>{game.mode === "sifu" ? `Challenge Sifu · Level ${game.ai_level}` : `${game.red_name || "Red"} — ${game.black_name || "Black"}`}</strong><small>{game.moves.length} moves · {game.status === "active" ? "In progress" : `${game.result} · ${game.termination}`}</small></span><b>{game.status === "active" ? "Continue →" : "Open →"}</b></button>)}</div></section>}
      {busy && <p className="launch-notice" role="status">Preparing the board…</p>}
      {error && <p className="launch-error" role="alert">{error}</p>}
    </main>
  );
}
