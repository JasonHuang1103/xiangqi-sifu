export type PieceMap = Record<string, string>;

export interface MoveView {
  id: number;
  ply: number;
  uci: string;
  resulting_fen: string;
}

export interface GameView {
  id: number;
  mode: "friend" | "sifu" | "upload" | "reference";
  status: "active" | "completed";
  starting_fen: string;
  current_fen: string;
  human_side: "w" | "b" | null;
  ai_level: number | null;
  red_name: string | null;
  black_name: string | null;
  result: string | null;
  termination: string | null;
  side_to_move: "red" | "black";
  pieces: PieceMap;
  legal_moves: string[];
  moves: MoveView[];
}

export interface AnalysisView {
  redScoreCp: number | null;
  redWinRate: number | null;
  bestMove: string | null;
  scoreChangeCp: number | null;
  pv: string[];
  mateScore?: number | null;
}

export interface CoachMessage {
  role: "user" | "assistant";
  content: string;
}
