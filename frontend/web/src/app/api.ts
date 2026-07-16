import type { GameView } from "./types";


async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
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
