import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { Workspace } from "./Workspace";
import type { GameView } from "../app/types";


const game: GameView = {
  id: 1,
  mode: "friend",
  status: "active",
  starting_fen: "start",
  current_fen: "position",
  human_side: null,
  ai_level: null,
  ai_adaptive: false,
  red_name: "Red",
  black_name: "Black",
  result: null,
  termination: null,
  side_to_move: "red",
  pieces: { e0: "K", e9: "k", h2: "C" },
  legal_moves: ["h2e2"],
  moves: [],
};


test("analysis toggle never removes the coaching panel", async () => {
  const user = userEvent.setup();
  render(
    <Workspace
      title="Central Cannon"
      game={game}
      analysis={{
        redScoreCp: 130,
        redWinRate: 0.62,
        bestMove: "h2e2",
        scoreChangeCp: 40,
        pv: ["h2e2", "b9c7"],
      }}
      onExit={() => undefined}
    />,
  );

  expect(screen.getByText("+1.3")).toBeInTheDocument();
  expect(screen.getByTestId("analysis-slot")).toBeInTheDocument();
  expect(screen.getByRole("complementary", { name: "Ask Sifu" })).toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: "Analysis on" }));

  expect(screen.getByTestId("analysis-slot")).toHaveClass("analysis-slot-hidden");
  expect(screen.getByTestId("analysis-slot")).toHaveAttribute("aria-hidden", "true");
  expect(screen.getByText("+1.3")).toBeInTheDocument();
  expect(screen.getByRole("complementary", { name: "Ask Sifu" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Analysis off" })).toBeInTheDocument();
});


test("review navigation traces the move that produced the selected position", () => {
  render(
    <Workspace
      title="Central Cannon"
      game={{
        ...game,
        pieces: { e0: "K", e9: "k", e2: "C" },
        moves: [
          { id: 1, ply: 1, uci: "h2e2", resulting_fen: "after-one" },
          { id: 2, ply: 2, uci: "h7e7", resulting_fen: "after-two" },
        ],
      }}
      selectedPly={1}
      positions={[
        { ply: 0, fen: "start", played_move: null, lines: [] },
        { ply: 1, fen: "after-one", played_move: "h2e2", lines: [] },
        { ply: 2, fen: "after-two", played_move: "h7e7", lines: [] },
      ]}
      onNavigate={() => undefined}
      onExit={() => undefined}
    />,
  );

  expect(screen.getByTestId("last-move-origin-h2")).toBeInTheDocument();
  expect(screen.getByTestId("last-move-destination-e2")).toBeInTheDocument();
});
