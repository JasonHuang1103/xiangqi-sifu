# Xiangqi Sifu Standalone App Design

**Date:** 2026-07-16

## Product Goal

Build a local-first desktop-style web application that combines three complete Xiangqi workflows:

1. Analyze a position reconstructed from a flat digital board screenshot, FEN, or manual setup.
2. Review a single game or a selected game from a `.pgn`/`.pgns` record with move-by-move engine analysis.
3. Start and play a new local human match or an adjustable-strength game against Sifu.

Pikafish is the tactical authority. The local explanation model converts verified engine facts into coaching language but never supplies moves, scores, or win rates on its own.

## Product Principles

- Everything required for normal use runs on the user's machine.
- No account, internet connection, or cloud API is required.
- A board is not shown on the launch screen. The board workspace opens only after the user starts or loads an activity.
- Engine output, estimates, historical statistics, and language-model explanations are labeled distinctly.
- Incorrect screenshot recognition is recoverable through an explicit confirmation and correction step.
- Personal games and conversations are stored separately from the supplied tournament corpus.
- Training does not run as part of this implementation.

## Launch Screen

The initial interface is a calm Scholar's Studio launchpad with five actions:

- **Play a Friend** — start a fresh same-device two-player game.
- **Challenge Sifu** — select side and difficulty, then start a fresh game against the local engine.
- **Analyze a Position** — upload a screenshot, paste FEN, or arrange a position manually.
- **Review a Record** — upload or paste `.pgn`, `.pgns`, or ICCS text.
- **Tournament Library** — search and select a game indexed from the supplied tournament corpora.

The launch screen does not show an empty board, a selected game, or a game overview. Once an action produces a position or game, the application transitions into the board workspace.

## Visual System

The accepted visual direction is **Scholar's Studio**:

- Warm paper and aged-wood surfaces.
- Jade for positive/active analysis state.
- Cinnabar for Red, primary emphasis, and the Sifu seal.
- A restrained editorial type hierarchy.
- A real 9×10 Xiangqi grid with river break, palace diagonals, coordinates, and Chinese piece glyphs.
- A compact green best-move arrow with a small arrowhead.

The desktop workspace contains:

- Context navigation on the left.
- The active board and move navigation in the center.
- Coaching chat in a permanent, independent right-hand column.
- Analysis meta in a ribbon above the board.

The **Analysis on/off** button sits beside **Flip**. It toggles the analysis ribbon, evaluation overlays, best-move arrow, and engine hints. It never hides, covers, or displaces the right-hand chat.

On narrow screens the layout stacks in this order: board controls, analysis ribbon, board, chat. The first-class target is a desktop browser on macOS Apple Silicon.

## Local Architecture

### Client

A React + TypeScript + Vite application owns presentation and interaction:

- Launchpad and new-game dialogs.
- Xiangqi board rendering and direct piece manipulation.
- Screenshot confirmation editor.
- Record picker, move timeline, evaluation chart, and mistake navigation.
- Play controls and local game state presentation.
- Persistent context-aware chat.

The client receives domain state from the API and does not reproduce engine analysis or authoritative legality rules.

### Server

A FastAPI application on localhost owns:

- Xiangqi legality and game-state transitions.
- Pikafish process lifecycle and analysis jobs.
- Record parsing and normalization.
- Screenshot recognition orchestration.
- Personal and reference repositories.
- Coach context construction and response verification.
- Static serving of the built React application in production mode.

A single launcher starts the API, selects an available loopback port, and opens the local app. Development mode runs Vite and FastAPI separately.

### Domain Boundaries

- `board`: FEN, legal moves, checks, terminal states, and notation.
- `engine`: Pikafish UCI process, MultiPV, score normalization, and cancellation.
- `analysis`: position/game orchestration, win-rate estimates, move deltas, and classifications.
- `vision`: board detection, recognition profiles, confidence, and FEN reconstruction.
- `coach`: grounded context, provider selection, verification, and deterministic fallback.
- `personal`: played/imported sessions, player profile, analysis, and chat storage.
- `reference`: read-only tournament indexing and retrieval.
- `api`: typed request/response models and job lifecycle.

## Source of Truth and Analysis Semantics

Pikafish supplies:

- Centipawn score or mate score.
- Best move.
- Requested MultiPV candidate lines.
- Principal variations.
- Search depth and node count when available.

Scores are normalized to Red's perspective in storage and converted to the selected side's perspective in the UI.

Win rate is a monotonic estimate derived from normalized score. It is labeled **Estimated win rate** and never displayed for forced-mate positions, where a mate label is used instead.

For each played move:

- `score_before` is the engine score before the move.
- `score_after` is the score after the move.
- `mover_loss` is adjusted for the side that moved.
- `score_change` shows the signed change for the mover.
- Classification uses configurable inaccuracy, mistake, and blunder thresholds.

The UI never substitutes database result frequency for the engine evaluation.

## Position Analysis Flow

1. The user chooses **Analyze a Position**.
2. The user uploads a PNG/JPEG/WebP screenshot, pastes FEN, or enters manual setup.
3. Screenshot input is passed through a local recognizer profile.
4. The server returns a board rectangle, orientation guess, piece map, confidence per square, and reconstructed FEN.
5. The client shows the original image beside an editable board. Low-confidence squares are highlighted.
6. The user confirms orientation and side to move and corrects any pieces.
7. The server validates kings, piece counts, palace constraints, and flying-general legality.
8. Pikafish analyzes the confirmed position with MultiPV.
9. The workspace shows score, estimated win rate, best move, alternatives, PV, and arrow overlay.
10. Chat is grounded in the confirmed FEN and most recent analysis.

The bundled recognizer must correctly recognize screenshots produced by Xiangqi Sifu's own board. External digital board styles use configurable recognizer profiles and always retain the manual-correction path.

## Record Review Flow

1. The user chooses **Review a Record** or selects a game from **Tournament Library**.
2. Single-game records open directly. Multi-game `.pgns` files first open a searchable, paginated game selector.
3. Parsing returns metadata, normalized ICCS/UCI moves, starting FEN, and a precise error location for invalid input.
4. The user starts an analysis job and may cancel it.
5. The job evaluates every position and persists incremental progress.
6. The workspace opens at move zero and supports previous, next, first, last, and direct move selection.
7. The evaluation chart and mistake list stay synchronized with the board.
8. Selecting a move updates the analysis ribbon and coaching context.
9. Follow-up questions such as "Why was this move bad?" reference the selected ply.

Uploaded user records are stored in the personal database with `origin = upload`. Tournament records remain in the reference database and only their personal analysis/session metadata is stored personally.

## Tournament Corpus

The two supplied sources are:

- `data/raw/WXF-41743games.pgns`
- `data/raw/dpxq-99813games.pgns`

They are indexed into a read-only reference database containing normalized game metadata, moves, position hashes, move frequencies, result frequencies, and representative games.

The corpus supports:

- Tournament Library search.
- Opening and similar-position retrieval.
- Historical move/result context in coaching.
- Future dataset generation and fine-tuning.

No training job is started. Historical frequency is supporting context, not tactical truth.

## Play Flows

### Play a Friend

- Start from the standard position.
- Optional player names and clock-free play.
- Same-device alternating turns.
- Legal destinations are highlighted after selection.
- Undo requires one explicit action and is recorded in the session event log.
- Resign, restart, and return to launch are available.

### Challenge Sifu

- Choose Red, Black, or random side.
- Choose a manual level from 1 through 10 or **Adaptive**.
- Pikafish supplies MultiPV candidates.
- Difficulty controls thinking time and the permitted evaluation-loss band when selecting among plausible candidates.
- Low levels make coherent, non-random inaccuracies; high levels converge on the engine's first choice.
- Adaptive mode updates a local skill estimate after completed games using result and move-quality evidence, then changes at most one displayed level between games.
- Hints are opt-in and analysis is hidden by default during live play.
- The completed game can be opened immediately in the review workspace.

### Rules and Terminal States

The authoritative server implements:

- General palace movement and flying-general capture/check.
- Advisor palace movement.
- Elephant river restriction and blocked eye.
- Horse blocked leg.
- Rook sliding movement.
- Cannon screen capture.
- Soldier forward movement and post-river lateral movement.
- Self-check rejection.
- Check, checkmate, stalemate, resignation, repetition, and no-progress draw tracking.

All accepted moves are validated by the server even if the client pre-highlights legal destinations.

## Persistence

### `personal.db`

Stores:

- Player profile and adaptive skill estimate.
- Played games and game events.
- Imported user records.
- Positions and moves.
- Analysis jobs and per-ply evaluations.
- Coaching threads and messages.
- Screenshot recognition results and user corrections.

Every accepted move is committed immediately. An interrupted in-progress game can be resumed.

Completed games store mode, players, human side, AI level, result, termination reason, timestamps, starting FEN, and complete move history. Games can be exported to PGN-compatible text.

### `reference.db`

Stores the derived tournament index. Application play never writes to this database. Rebuilding it is an explicit offline command.

## Coach Behavior

The chat request includes only structured, relevant context:

- Current FEN and side to move.
- Selected ply and played move when reviewing a game.
- Engine score, mate state, best move, alternatives, and PVs.
- Move delta and classification.
- Relevant historical examples when available.
- Prior messages from the current thread within a bounded context window.

The provider order is:

1. Existing local Qwen3.5-2B + Xiangqi Sifu LoRA adapter when configured and loadable.
2. Deterministic grounded explanation provider.

The verifier rejects or sanitizes answers that contradict the supplied best move, score direction, mate state, or move delta. The deterministic provider always remains available, so chat never becomes an empty surface because a model is missing.

## API Surface

The API uses `/api` routes and JSON unless noted otherwise:

- `GET /api/health`
- `GET /api/bootstrap`
- `POST /api/positions/recognize` (multipart image)
- `POST /api/positions/validate`
- `POST /api/analysis/positions`
- `POST /api/records/inspect`
- `POST /api/analysis/games`
- `GET /api/jobs/{job_id}`
- `DELETE /api/jobs/{job_id}`
- `GET /api/reference/games`
- `GET /api/reference/games/{game_id}`
- `GET /api/personal/games`
- `GET /api/personal/games/{game_id}`
- `POST /api/play/games`
- `POST /api/play/games/{game_id}/moves`
- `POST /api/play/games/{game_id}/ai-move`
- `POST /api/play/games/{game_id}/resign`
- `POST /api/play/games/{game_id}/undo`
- `POST /api/coach/threads`
- `POST /api/coach/threads/{thread_id}/messages`

Analysis jobs expose progress through polling first. The schema permits later migration to server-sent events without changing analysis records.

## Error and Recovery Design

- Missing Pikafish binary: launchpad shows a local setup action and affected actions remain disabled with an explanation.
- Engine crash/timeout: job becomes failed, partial results remain stored, and retry is available.
- Low-confidence screenshot: correction mode is mandatory; no silent auto-analysis.
- Invalid position: affected squares and rule violations are shown before analysis.
- Invalid record: source line/token and the first illegal or unsupported move are shown.
- Oversized multi-game upload: metadata inspection remains bounded and the user selects games before analysis.
- Model unavailable: deterministic coach is used automatically.
- Database migration failure: startup stops before writes and reports the exact database path.
- Browser refresh: active personal game, selected ply, and current thread are restored from persisted state.

## Testing Strategy

### Python

- Unit tests for every Xiangqi piece rule and self-check rejection.
- Position status tests for check, checkmate, stalemate, flying generals, and repetition.
- Pikafish protocol tests for MultiPV, score normalization, mate, timeout, and cancellation.
- Parser tests for single and multi-game records plus error locations.
- Repository migration and separation tests for `personal.db` and `reference.db`.
- Coach grounding and verifier tests.
- Vision round-trip tests using screenshots rendered from the app board.
- API integration tests for each vertical flow.

### TypeScript

- Board coordinate/orientation rendering tests.
- Launchpad transition tests verifying no board exists before an activity is chosen.
- Screenshot correction interaction tests.
- Analysis toggle tests verifying chat remains mounted.
- Record navigation and chart synchronization tests.
- Play and persistence client-flow tests.

### End to End

- Start **Play a Friend**, make legal moves, reload, resume, and finish.
- Start **Challenge Sifu** at two levels and receive legal AI moves.
- Upload an app-rendered board screenshot, confirm FEN, analyze, and ask a question.
- Upload a multi-game record, select one game, analyze it, navigate a mistake, and ask a question.
- Search the tournament library without writing to `reference.db`.

## Acceptance Criteria

The implementation is complete only when all of the following are verified locally:

- The launchpad contains the five named actions and no board before selection.
- Screenshot, record, tournament-library, Play a Friend, and Challenge Sifu flows open the correct workspace.
- A confirmed screenshot position produces real Pikafish metadata and a grounded chat answer.
- A selected record produces move-by-move analysis, navigation, and contextual chat.
- Both play modes enforce legal Xiangqi and persist every accepted move to `personal.db`.
- Personal writes do not modify `reference.db`.
- Analysis meta toggles independently while chat remains visible on the right.
- Manual and adaptive AI levels produce legal moves and distinct strength behavior.
- Automated backend and frontend tests pass.
- The production frontend builds without errors.
- Browser-based end-to-end smoke tests pass against the local launcher.

## Explicit Non-Goals

- No cloud account, synchronization, or multiplayer networking.
- No physical-board photo recognition in this release.
- No new LoRA or vision-model training run.
- No mobile-native packaging.
- No engine claims sourced from the language model.
