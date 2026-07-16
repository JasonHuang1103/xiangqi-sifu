import type { AnalyzedPosition } from "../app/types";


export function EvaluationChart({ positions, selectedPly, onSelect }: { positions: AnalyzedPosition[]; selectedPly: number; onSelect: (ply: number) => void }) {
  const known = positions.map((position) => position.lines[0]?.red_score_cp ?? null);
  return (
    <section className="evaluation-chart" aria-label="Game evaluation by move">
      <span>BLACK</span>
      <div className="evaluation-track">
        <i />
        {known.map((score, ply) => score === null ? null : <button key={ply} type="button" aria-label={`Move ${ply}: ${score} centipawns`} className={ply === selectedPly ? "active" : ""} style={{ left: `${positions.length > 1 ? ply / (positions.length - 1) * 100 : 0}%`, top: `${50 - Math.max(-400, Math.min(400, score)) / 10}%` }} onClick={() => onSelect(ply)} />)}
      </div>
      <span>RED</span>
    </section>
  );
}
