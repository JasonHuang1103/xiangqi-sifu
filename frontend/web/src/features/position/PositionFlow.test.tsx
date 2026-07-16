import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

import { PositionFlow } from "./PositionFlow";


test("validates an editable FEN before opening analysis", async () => {
  const onOpen = vi.fn();
  vi.stubGlobal("fetch", vi.fn()
    .mockResolvedValueOnce(new Response(JSON.stringify({
      fen: "4k4/9/9/9/9/9/9/9/9/4K4 w - - 0 1",
      pieces: { e9: "k", e0: "K" },
      active_color: "w",
      valid: true,
      issues: [],
    }), { status: 200, headers: { "Content-Type": "application/json" } }))
    .mockResolvedValueOnce(new Response(JSON.stringify({
      fen: "4k4/9/9/9/9/9/9/9/9/4K4 w - - 0 1",
      lines: [{ best_move: "e0e1", red_score_cp: 42, mate_score: null, pv: ["e0e1"], estimated_red_win_rate: 0.5436 }],
    }), { status: 200, headers: { "Content-Type": "application/json" } })));

  render(<PositionFlow onBack={() => undefined} onOpen={onOpen} />);
  fireEvent.change(screen.getByLabelText("Position FEN"), { target: { value: "4k4/9/9/9/9/9/9/9/9/4K4 w - - 0 1" } });
  fireEvent.click(screen.getByRole("button", { name: "Confirm and analyze" }));

  await waitFor(() => expect(onOpen).toHaveBeenCalledWith(expect.objectContaining({
    title: "Position study",
    analysis: expect.objectContaining({ bestMove: "e0e1" }),
  })));
});
