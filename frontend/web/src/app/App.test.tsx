import { render, screen } from "@testing-library/react";

import { App } from "./App";


test("launchpad offers every activity without mounting a board", () => {
  render(<App />);

  expect(screen.getByRole("button", { name: "Play a Friend" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Challenge Sifu" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Analyze a Position" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Review a Record" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Tournament Library" })).toBeInTheDocument();
  expect(screen.queryByRole("img", { name: "Xiangqi board" })).not.toBeInTheDocument();
});
