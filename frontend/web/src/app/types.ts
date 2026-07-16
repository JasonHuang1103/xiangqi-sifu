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

export interface EngineLineView {
  best_move: string | null;
  red_score_cp: number;
  mate_score: number | null;
  pv: string[];
  estimated_red_win_rate: number | null;
}

export interface PositionAnalysisResponse {
  fen: string;
  lines: EngineLineView[];
}

export interface AnalyzedPosition {
  ply: number;
  fen: string;
  played_move: string | null;
  lines: EngineLineView[];
}

export interface StudySession {
  title: string;
  source: "position" | "upload" | "reference";
  game: GameView;
  analysis: AnalysisView;
  positions?: AnalyzedPosition[];
  selectedPly?: number;
}

export interface InspectedGame {
  index: number;
  event: string | null;
  red: string | null;
  black: string | null;
  result: string | null;
  move_count: number;
  starting_fen: string;
  moves: string[];
}

export interface ReferenceGameSummary {
  id: number;
  corpus_name: string;
  source_game_id: number;
  event: string | null;
  red: string | null;
  black: string | null;
  result: string | null;
  move_count: number;
}
