import type { AnalysisView } from "../app/types";


function score(value: number | null) {
  if (value === null) return "—";
  const normalized = Math.abs(value) < 5 ? 0 : value / 100;
  return `${normalized > 0 ? "+" : ""}${normalized.toFixed(1)}`;
}


export function AnalysisRibbon({ analysis }: { analysis: AnalysisView }) {
  const redRate = analysis.redWinRate === null ? null : Math.round(analysis.redWinRate * 100);
  return (
    <section className="analysis-ribbon" aria-label="Position analysis">
      <div className="analysis-cell"><span>CURRENT SCORE</span><strong>{score(analysis.redScoreCp)}</strong></div>
      <div className="analysis-cell"><span>LAST MOVE</span><strong className={(analysis.scoreChangeCp ?? 0) >= 0 ? "positive" : "negative"}>{score(analysis.scoreChangeCp)}</strong></div>
      <div className="analysis-cell"><span>BEST MOVE</span><strong>{analysis.bestMove ?? "—"}</strong></div>
      <div className="analysis-cell win-cell">
        <span>ESTIMATED WIN RATE</span>
        {redRate === null ? <strong>—</strong> : <div className="win-balance"><strong>{redRate}%</strong><div><i style={{ width: `${redRate}%` }} /></div><strong>{100 - redRate}%</strong></div>}
      </div>
    </section>
  );
}
