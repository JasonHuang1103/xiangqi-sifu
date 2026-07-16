import { render, screen } from "@testing-library/react";

import { XiangqiBoard } from "./XiangqiBoard";


test("shows a muted trace at both ends of the latest move", () => {
  render(
    <XiangqiBoard
      pieces={{ e0: "K", e9: "k", e2: "C" }}
      lastMove="h2e2"
    />,
  );

  expect(screen.getByTestId("last-move-origin-h2")).toBeInTheDocument();
  expect(screen.getByTestId("last-move-destination-e2")).toBeInTheDocument();
});
