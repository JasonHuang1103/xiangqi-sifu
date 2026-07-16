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
  expect(screen.getByRole("complementary", { name: "Ask Sifu" })).toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: "Analysis on" }));

  expect(screen.queryByText("+1.3")).not.toBeInTheDocument();
  expect(screen.getByRole("complementary", { name: "Ask Sifu" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Analysis off" })).toBeInTheDocument();
});
