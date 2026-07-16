# Board Stability and Readability Design

## Objective

Refine the Scholar's Studio workspace so users can follow the latest move, the board never shifts when game or analysis state changes, and supporting text is comfortably readable without weakening the existing editorial hierarchy.

## Last-Move Trace

The board receives the current context's last move as a four-character UCI coordinate move.

- In live games, use the last persisted game move.
- In record review, use the move associated with the selected ply, not the final move of the record.
- Draw a muted gray footprint at the origin square.
- Draw a muted gray halo around the piece on the destination square.
- A currently selected piece keeps the stronger jade selection treatment above the gray trace.
- The trace follows board flipping through the existing square-to-point mapping.
- Positions with no prior move show no trace.

## Stable Board Geometry

The board's viewport position must remain unchanged when:

- analysis metadata is toggled;
- a hint first makes analysis available;
- a move is submitted, saved, or answered by Sifu;
- transient status or error text appears;
- move counters, evaluation points, or toolbar button states change.

The workspace will enforce this structurally:

- Always render a fixed-height analysis slot above the board. Hidden analysis retains the slot's geometry while removing its content from sight and interaction.
- Reserve a fixed status-line height in the heading so transient notices do not enlarge it.
- Align the board to the top-center of its stage instead of vertically recentering it within changing free space.
- Keep the evaluation chart and move navigation below the board, outside the board anchor.
- Preserve the permanent right-hand coach column and prevent the analysis slot from overlapping it.
- Use a taller fixed analysis slot at the compact breakpoint where metadata uses two rows.

## Typography

Increase undersized supporting text selectively rather than applying browser-scale zoom.

- Navigation and toolbar controls: 11 px, with primary labels at 12 px.
- Status, metadata labels, kickers, and form labels: 9 px, with input labels at 10 px.
- Descriptions, move controls, archive details, and secondary text: 11 px.
- Coach messages and compose controls: 11 px, with the coach header subtitle at 10 px.
- Preserve the existing large launch headings, workspace headings, board-piece glyphs, and editorial serif hierarchy.
- Maintain current colors and meet the existing contrast relationships.

## Tests and Verification

- Component test: live game passes the last persisted move to the board and exposes origin/destination trace nodes.
- Component test: review mode traces the selected ply's played move.
- Component test: analysis content toggles while its layout slot remains mounted.
- Browser measurement: board-frame `x`, `y`, width, and height are identical before and after analysis toggling.
- Browser measurement: board geometry is identical before, during, and after a legal move and Sifu reply.
- Visual QA at 1280×900 and 768×900 confirms readable typography, no overlap, and chat remains on the right.
- Run React component tests, production build, and focused Playwright end-to-end coverage.

## Scope

This pass changes only presentation and the derivation of last-move context. It does not change Xiangqi rules, API contracts, engine behavior, persistence schema, or game history.
