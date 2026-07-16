import type { AnalyzedPosition, AnalysisView, GameView, StudySession } from "../app/types";

export const START_FEN = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1";

export function piecesFromFen(fen: string) {
  const pieces: Record<string, string> = {};
  const rows = fen.split(" ")[0].split("/");
  rows.forEach((row, rowIndex) => {
    let file = 0;
    for (const token of row) {
      if (/\d/.test(token)) file += Number(token);
      else {
        pieces[`${"abcdefghi"[file]}${9 - rowIndex}`] = token;
        file += 1;
      }
    }
  });
  return pieces;
}

export function analysisFrom(position: AnalyzedPosition, previous?: AnalyzedPosition): AnalysisView {
  const line = position.lines[0];
  const previousScore = previous?.lines[0]?.red_score_cp;
  return {
    redScoreCp: line?.red_score_cp ?? null,
    redWinRate: line?.estimated_red_win_rate ?? null,
    bestMove: line?.best_move ?? null,
    scoreChangeCp: previousScore === undefined || !line ? null : line.red_score_cp - previousScore,
    pv: line?.pv ?? [],
    mateScore: line?.mate_score ?? null,
  };
}

export function sessionFromPositions(title: string, source: StudySession["source"], positions: AnalyzedPosition[], moves: string[], selectedPly = 0): StudySession {
  const position = positions[selectedPly];
  const active = position.fen.split(" ")[1] === "b" ? "black" : "red";
  const game: GameView = {
    id: 0,
    mode: source === "reference" ? "reference" : "upload",
    status: "completed",
    starting_fen: positions[0].fen,
    current_fen: position.fen,
    human_side: null,
    ai_level: null,
    ai_adaptive: false,
    red_name: null,
    black_name: null,
    result: null,
    termination: null,
    side_to_move: active,
    pieces: piecesFromFen(position.fen),
    legal_moves: [],
    moves: moves.map((uci, index) => ({ id: index + 1, ply: index + 1, uci, resulting_fen: positions[index + 1]?.fen ?? position.fen })),
  };
  return { title, source, game, analysis: analysisFrom(position, positions[selectedPly - 1]), positions, selectedPly };
}
