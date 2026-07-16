# Board Stability and Readability Implementation Plan

**Goal:** Add persistent last-move trace markers, keep the board at an invariant position while surrounding UI changes, and improve small-text readability without changing the Scholar's Studio visual direction.

**Scope:** Frontend React components, focused CSS, component tests, and the existing Playwright workflow. No engine, persistence, or API changes are required.

## 1. Establish regression coverage

- Add component tests for origin and destination trace markers.
- Add workspace tests proving the contextual move comes from the live game or selected review ply.
- Update the analysis-toggle test to require a persistent analysis layout slot.
- Verify the new tests fail for the intended missing behavior before implementation.

## 2. Implement last-move trace

- Derive the contextual last move in `Workspace`.
- Pass it into `XiangqiBoard`.
- Render a muted gray origin footprint and a gray destination halo while preserving selection and legal-target styling.
- Verify component tests pass.

## 3. Stabilize board geometry

- Keep the analysis row mounted at a fixed responsive height and hide only its content.
- Keep a reserved notice/status line in the board header.
- Anchor the board to the top-center of its stage so footer or chart changes cannot recenter it.
- Add a Playwright geometry assertion comparing board coordinates before and after toggling analysis.

## 4. Improve typography

- Raise undersized navigation, control, metadata, coach, launch, and archive text to the approved targeted scale.
- Preserve display headings and board-piece glyph sizes.
- Check desktop and compact layouts for overflow or wrapping regressions.

## 5. Verify and deliver

- Run frontend unit tests, production build, and focused Playwright tests.
- Reload the local app and manually verify move trace, analysis-toggle stability, and readable typography at representative viewports.
- Review the diff for unrelated changes and commit only the implementation files.
