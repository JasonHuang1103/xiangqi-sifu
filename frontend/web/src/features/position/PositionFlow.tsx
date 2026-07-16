import { useState } from "react";

import { analyzePosition, recognizePosition, validatePosition } from "../../app/api";
import type { StudySession } from "../../app/types";
import { sessionFromPositions, START_FEN } from "../study";

interface PositionFlowProps {
  onBack: () => void;
  onOpen: (session: StudySession) => void;
}


export function PositionFlow({ onBack, onOpen }: PositionFlowProps) {
  const [fen, setFen] = useState(START_FEN);
  const [activeColor, setActiveColor] = useState<"w" | "b">("w");
  const [preview, setPreview] = useState<string | null>(null);
  const [notice, setNotice] = useState("Paste a FEN or upload a Scholar's Studio board screenshot.");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const upload = async (file?: File) => {
    if (!file) return;
    setPreview(URL.createObjectURL(file));
    setBusy(true);
    setError(null);
    try {
      const recognition = await recognizePosition(file, activeColor);
      setFen(recognition.fen);
      setNotice("Recognition complete. Check the editable FEN before analysis.");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The board could not be recognized.");
    } finally {
      setBusy(false);
    }
  };

  const analyze = async () => {
    setBusy(true);
    setError(null);
    try {
      const validation = await validatePosition(fen.trim());
      if (!validation.valid) {
        setError(validation.issues.map((issue) => issue.message).join(" "));
        return;
      }
      const result = await analyzePosition(validation.fen);
      const linePosition = { ply: 0, fen: result.fen, played_move: null, lines: result.lines };
      onOpen(sessionFromPositions("Position study", "position", [linePosition], []));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Analysis could not be started.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="intake-page">
      <header className="launch-header"><button className="brand brand-button" type="button" onClick={onBack}><span className="brand-seal">師</span> XIANGQI SIFU</button><span className="local-status"><span /> Local recognition</span></header>
      <section className="intake-layout">
        <div className="intake-intro"><p className="section-kicker">ANALYZE A POSITION</p><h1>Bring the board<br />into the study.</h1><p>Start from a screenshot or an exact FEN. You always confirm the position before Pikafish begins.</p><button type="button" className="text-button" onClick={onBack}>← Back to the studio</button></div>
        <form className="intake-form" onSubmit={(event) => { event.preventDefault(); void analyze(); }}>
          <label className={`drop-zone ${preview ? "with-preview" : ""}`}>{preview && <img src={preview} alt="Uploaded board to confirm" />}<span><strong>{busy ? "Reading the board…" : "Upload a board screenshot"}</strong><small>PNG, JPEG, or WEBP · Scholar's Studio digital board</small><input type="file" accept="image/png,image/jpeg,image/webp" onChange={(event) => void upload(event.target.files?.[0])} disabled={busy} /></span></label>
          <div className="form-divider"><span>OR ENTER EXACT POSITION</span></div>
          <label className="field-label" htmlFor="position-fen">Position FEN</label>
          <textarea id="position-fen" rows={4} value={fen} onChange={(event) => setFen(event.target.value)} />
          <div className="inline-fields"><label><span>Side to move</span><select value={activeColor} onChange={(event) => { const value = event.target.value as "w" | "b"; setActiveColor(value); setFen((current) => { const parts = current.trim().split(/\s+/); if (parts.length >= 2) parts[1] = value; return parts.join(" "); }); }}><option value="w">Red</option><option value="b">Black</option></select></label><p>{notice}</p></div>
          {error && <p className="form-error" role="alert">{error}</p>}
          <button className="primary-button" type="submit" disabled={busy}>{busy ? "Preparing…" : "Confirm and analyze"}</button>
        </form>
      </section>
    </main>
  );
}
