import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

import type { GameView } from "../../app/types";
import { PlayFlow } from "./PlayFlow";

const game: GameView = {
  id: 7,
  mode: "friend",
  status: "active",
  starting_fen: "start",
  current_fen: "start",
  human_side: null,
  ai_level: null,
  ai_adaptive: false,
  red_name: "Mei",
  black_name: "Lin",
  result: null,
  termination: null,
  side_to_move: "red",
  pieces: { h2: "C", e0: "K", e9: "k" },
  legal_moves: ["h2e2"],
  moves: [],
};


test("plays a highlighted server-authoritative move", async () => {
  const moved = { ...game, side_to_move: "black" as const, pieces: { e2: "C", e0: "K", e9: "k" }, legal_moves: [], moves: [{ id: 1, ply: 1, uci: "h2e2", resulting_fen: "after" }] };
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify(moved), { status: 200, headers: { "Content-Type": "application/json" } })));

  render(<PlayFlow initialGame={game} onExit={() => undefined} onReview={() => undefined} />);
  fireEvent.click(screen.getByTestId("square-h2"));
  fireEvent.click(screen.getByTestId("square-e2"));

  await waitFor(() => expect(screen.getByText("BLACK TO MOVE")).toBeInTheDocument());
  expect(fetch).toHaveBeenCalledWith("/api/play/games/7/moves", expect.objectContaining({ method: "POST" }));
  expect(screen.getByTestId("last-move-origin-h2")).toBeInTheDocument();
  expect(screen.getByTestId("last-move-destination-e2")).toBeInTheDocument();
});
