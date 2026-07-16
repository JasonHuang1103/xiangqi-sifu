import { useState } from "react";

export interface NewGameSettings {
  mode: "friend" | "sifu";
  human_side?: "w" | "b";
  ai_level?: number;
  adaptive?: boolean;
  red_name?: string;
  black_name?: string;
}


export function NewGameDialog({ mode, busy, onCancel, onStart }: { mode: "friend" | "sifu"; busy: boolean; onCancel: () => void; onStart: (settings: NewGameSettings) => void }) {
  const [redName, setRedName] = useState("Red");
  const [blackName, setBlackName] = useState("Black");
  const [side, setSide] = useState<"w" | "b" | "random">("w");
  const [level, setLevel] = useState("5");
  const title = mode === "friend" ? "Play a Friend" : "Challenge Sifu";
  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    if (mode === "friend") onStart({ mode, red_name: redName.trim() || "Red", black_name: blackName.trim() || "Black" });
    else {
      const humanSide = side === "random" ? (Math.random() < .5 ? "w" : "b") : side;
      onStart({ mode, human_side: humanSide, adaptive: level === "adaptive", ai_level: level === "adaptive" ? undefined : Number(level) });
    }
  };
  return (
    <div className="dialog-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) onCancel(); }}>
      <section className="new-game-dialog" role="dialog" aria-modal="true" aria-labelledby="new-game-dialog-title">
        <p className="section-kicker">NEW GAME</p><h2 id="new-game-dialog-title">{title}</h2>
        <p>{mode === "friend" ? "Two players, one board. The complete game is saved locally." : "Choose your side and how firmly Sifu should play."}</p>
        <form onSubmit={submit}>
          {mode === "friend" ? <div className="dialog-fields"><label>Red player<input value={redName} onChange={(event) => setRedName(event.target.value)} /></label><label>Black player<input value={blackName} onChange={(event) => setBlackName(event.target.value)} /></label></div> : <><fieldset><legend>Your side</legend><label><input type="radio" name="side" checked={side === "w"} onChange={() => setSide("w")} /> Red</label><label><input type="radio" name="side" checked={side === "b"} onChange={() => setSide("b")} /> Black</label><label><input type="radio" name="side" checked={side === "random"} onChange={() => setSide("random")} /> Surprise me</label></fieldset><label className="dialog-level">Sifu strength<select value={level} onChange={(event) => setLevel(event.target.value)}><option value="adaptive">Adaptive</option>{Array.from({ length: 10 }, (_, index) => <option key={index + 1} value={index + 1}>Level {index + 1}</option>)}</select><small>{level === "adaptive" ? "Adjusts one step at a time from your saved results." : "Higher levels stay closer to Pikafish's first choice."}</small></label></>}
          <div className="dialog-actions"><button type="button" onClick={onCancel}>Cancel</button><button className="primary-button" type="submit" disabled={busy}>{busy ? "Preparing…" : title}</button></div>
        </form>
      </section>
    </div>
  );
}
