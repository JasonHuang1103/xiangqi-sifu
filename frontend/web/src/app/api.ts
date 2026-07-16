import type { AnalyzedPosition, GameView, InspectedGame, PositionAnalysisResponse, ReferenceGameSummary } from "./types";


async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  if (!(init?.body instanceof FormData)) headers.set("Content-Type", "application/json");
  const response = await fetch(path, {
    ...init,
    headers,
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: unknown } | null;
    throw new Error(typeof body?.detail === "string" ? body.detail : `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}


export function createGame(input: {
  mode: "friend" | "sifu";
  human_side?: "w" | "b";
  ai_level?: number;
  adaptive?: boolean;
  red_name?: string;
  black_name?: string;
}): Promise<GameView> {
  return request<GameView>("/api/play/games", {
    method: "POST",
    body: JSON.stringify(input),
  });
}


export function playMove(gameId: number, uci: string): Promise<GameView> {
  return request<GameView>(`/api/play/games/${gameId}/moves`, {
    method: "POST",
    body: JSON.stringify({ uci }),
  });
}


export function requestAiMove(gameId: number): Promise<GameView> {
  return request<GameView>(`/api/play/games/${gameId}/ai-move`, { method: "POST" });
}

export function undoGame(gameId: number): Promise<GameView> {
  return request<GameView>(`/api/play/games/${gameId}/undo`, { method: "POST" });
}

export function resignGame(gameId: number, side?: "w" | "b"): Promise<GameView> {
  return request<GameView>(`/api/play/games/${gameId}/resign`, { method: "POST", body: JSON.stringify({ side }) });
}

export function listPersonalGames(): Promise<GameView[]> {
  return request<GameView[]>("/api/personal/games");
}

export interface PositionValidation {
  fen: string;
  pieces: Record<string, string>;
  active_color: "w" | "b";
  valid: boolean;
  issues: { code: string; message: string; squares: string[] }[];
}

export function validatePosition(fen: string): Promise<PositionValidation> {
  return request<PositionValidation>("/api/positions/validate", { method: "POST", body: JSON.stringify({ fen }) });
}

export function recognizePosition(image: File, activeColor: "w" | "b"): Promise<PositionValidation & { requires_confirmation: boolean; confidence_by_square: Record<string, number>; validation: { valid: boolean; issues: PositionValidation["issues"] } }> {
  const body = new FormData();
  body.append("image", image);
  body.append("profile", "scholars-studio");
  body.append("active_color", activeColor);
  return request("/api/positions/recognize", { method: "POST", body });
}

export function analyzePosition(fen: string, multipv = 3): Promise<PositionAnalysisResponse> {
  return request<PositionAnalysisResponse>("/api/analysis/positions", { method: "POST", body: JSON.stringify({ fen, multipv }) });
}

export function inspectRecord(text: string): Promise<{ total_games: number; requires_selection: boolean; games: InspectedGame[] }> {
  return request("/api/records/inspect", { method: "POST", body: JSON.stringify({ text, offset: 0, limit: 200 }) });
}

export function analyzeGame(startingFen: string, moves: string[]): Promise<{ starting_fen: string; moves: string[]; positions: AnalyzedPosition[] }> {
  return request("/api/analysis/games", { method: "POST", body: JSON.stringify({ starting_fen: startingFen, moves, multipv: 3, selected_ply: 0 }) });
}

export function searchReferenceGames(query = ""): Promise<{ total: number; games: ReferenceGameSummary[] }> {
  return request(`/api/reference/games?query=${encodeURIComponent(query)}&limit=50`);
}

export function getReferenceGame(id: number): Promise<{ summary: ReferenceGameSummary; record: { starting_fen: string; moves: { uci: string }[] } }> {
  return request(`/api/reference/games/${id}`);
}

export function createCoachThread(context: Record<string, unknown>): Promise<{ id: number }> {
  return request("/api/coach/threads", { method: "POST", body: JSON.stringify(context) });
}

export function askCoach(threadId: number, question: string): Promise<{ reply: { text: string }; messages: { role: "user" | "assistant"; content: string }[] }> {
  return request(`/api/coach/threads/${threadId}/messages`, { method: "POST", body: JSON.stringify({ question }) });
}
