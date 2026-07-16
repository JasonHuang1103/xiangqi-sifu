import type { PieceMap } from "../app/types";

const files = "abcdefghi";
const glyphs: Record<string, string> = {
  R: "俥", N: "傌", B: "相", A: "仕", K: "帥", C: "炮", P: "兵",
  r: "車", n: "馬", b: "象", a: "士", k: "將", c: "砲", p: "卒",
};

interface XiangqiBoardProps {
  pieces: PieceMap;
  bestMove?: string | null;
  showAnalysis?: boolean;
  flipped?: boolean;
  selectedSquare?: string | null;
  legalTargets?: string[];
  onSquareClick?: (square: string) => void;
}

function point(square: string, flipped: boolean) {
  const rawFile = files.indexOf(square[0]);
  const rawRank = Number(square[1]);
  const file = flipped ? 8 - rawFile : rawFile;
  const rank = flipped ? 9 - rawRank : rawRank;
  return { x: 40 + file * 40, y: 40 + (9 - rank) * 40 };
}


export function XiangqiBoard({
  pieces,
  bestMove = null,
  showAnalysis = false,
  flipped = false,
  selectedSquare = null,
  legalTargets = [],
  onSquareClick,
}: XiangqiBoardProps) {
  const arrow = bestMove && bestMove.length === 4
    ? { from: point(bestMove.slice(0, 2), flipped), to: point(bestMove.slice(2), flipped) }
    : null;
  return (
    <div className="board-frame">
      <svg className="xiangqi-board" viewBox="0 0 400 440" role="img" aria-label="Xiangqi board">
        <defs>
          <marker id="best-arrowhead" markerWidth="4" markerHeight="4" refX="3.5" refY="2" orient="auto">
            <path d="M0,0 L4,2 L0,4 z" className="best-arrow-head" />
          </marker>
        </defs>
        <rect className="board-surface" x="12" y="12" width="376" height="416" rx="8" />
        <g className="board-grid-lines">
          <rect x="40" y="40" width="320" height="360" />
          {Array.from({ length: 8 }, (_, index) => <line key={`h-${index}`} x1="40" y1={80 + index * 40} x2="360" y2={80 + index * 40} />)}
          {Array.from({ length: 7 }, (_, index) => {
            const x = 80 + index * 40;
            return <g key={`v-${index}`}><line x1={x} y1="40" x2={x} y2="200" /><line x1={x} y1="240" x2={x} y2="400" /></g>;
          })}
          <line x1="160" y1="40" x2="240" y2="120" /><line x1="240" y1="40" x2="160" y2="120" />
          <line x1="160" y1="320" x2="240" y2="400" /><line x1="240" y1="320" x2="160" y2="400" />
        </g>
        <text className="river-label" x="105" y="226">楚 河</text>
        <text className="river-label" x="267" y="226">漢 界</text>
        {legalTargets.map((square) => {
          const target = point(square, flipped);
          return <circle key={`target-${square}`} className="legal-target" cx={target.x} cy={target.y} r="7" />;
        })}
        {Object.entries(pieces).map(([square, piece]) => {
          const position = point(square, flipped);
          return (
            <g
              key={square}
              className={`board-piece ${piece === piece.toUpperCase() ? "red-piece" : "black-piece"} ${selectedSquare === square ? "selected-piece" : ""}`}
              transform={`translate(${position.x} ${position.y})`}
              onClick={() => onSquareClick?.(square)}
            >
              <circle r="17" />
              <text y="1">{glyphs[piece] ?? piece}</text>
            </g>
          );
        })}
        {showAnalysis && arrow && (
          <g className="analysis-overlay">
            <circle className="best-target" cx={arrow.to.x} cy={arrow.to.y} r="21" />
            <line className="best-arrow" x1={arrow.from.x} y1={arrow.from.y} x2={arrow.to.x} y2={arrow.to.y} markerEnd="url(#best-arrowhead)" />
          </g>
        )}
        {Array.from({ length: 9 }, (_, index) => (
          <text className="file-label" key={index} x={40 + index * 40} y="421">{flipped ? index + 1 : 9 - index}</text>
        ))}
      </svg>
    </div>
  );
}
