import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

import { ReviewFlow } from "./ReviewFlow";


test("requires selecting a game from a multi-game record", async () => {
  const onOpen = vi.fn();
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({
    total_games: 2,
    offset: 0,
    limit: 50,
    requires_selection: true,
    games: [
      { index: 0, event: "Final", red: "Lin", black: "Chen", result: "1-0", move_count: 1, starting_fen: "start-a", moves: ["h2e2"] },
      { index: 1, event: "Final", red: "Wu", black: "Li", result: "0-1", move_count: 1, starting_fen: "start-b", moves: ["c3c4"] },
    ],
  }), { status: 200, headers: { "Content-Type": "application/json" } })));

  render(<ReviewFlow onBack={() => undefined} onOpen={onOpen} />);
  fireEvent.change(screen.getByLabelText("Game record"), { target: { value: "two games" } });
  fireEvent.click(screen.getByRole("button", { name: "Inspect record" }));

  expect(await screen.findByText("Lin — Chen")).toBeInTheDocument();
  expect(screen.getByText("Wu — Li")).toBeInTheDocument();
  expect(onOpen).not.toHaveBeenCalled();
});
