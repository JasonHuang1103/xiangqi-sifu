# Xiangqi Sifu Standalone App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a polished local-first Xiangqi application for screenshot/record analysis, grounded coaching chat, and persisted human or adjustable-AI play.

**Architecture:** A React/TypeScript/Vite client talks to a localhost FastAPI server. The Python server owns authoritative rules, Pikafish, vision, coaching, and two physically separate SQLite repositories; React owns the Scholar's Studio launchpad and interactive workspace.

**Tech Stack:** Python 3.11, FastAPI, Pydantic, SQLite, Pillow/NumPy, Pikafish UCI, React 19, TypeScript, Vite, Vitest, Testing Library, Playwright.

## Global Constraints

- All normal flows run locally without an account, internet connection, or cloud API.
- The launch screen contains no board before the user starts or loads an activity.
- Launch actions are named **Play a Friend**, **Challenge Sifu**, **Analyze a Position**, **Review a Record**, and **Tournament Library**.
- Chat remains in a permanent right-hand workspace column; analysis meta toggles independently above the board.
- `personal.db` accepts user writes; `reference.db` is read-only during application use.
- Pikafish is the tactical source of truth; the language model never invents engine metadata.
- No model-training job is started.
- Existing unrelated code and user-owned files are not refactored or deleted.

---

## File Map

### Python server

- `src/xiangqi_sifu/board/rules.py` — authoritative move generation and position status.
- `src/xiangqi_sifu/board/game.py` — persisted game state transitions and repetition tracking.
- `src/xiangqi_sifu/engine/pikafish.py` — UCI MultiPV analysis and option handling.
- `src/xiangqi_sifu/analysis/models.py` — serializable score, line, and move-impact models.
- `src/xiangqi_sifu/analysis/service.py` — position/game analysis orchestration.
- `src/xiangqi_sifu/database/personal.py` — personal schema and repository.
- `src/xiangqi_sifu/database/reference.py` — read-only tournament queries.
- `src/xiangqi_sifu/vision/service.py` — image recognition result and board validation.
- `src/xiangqi_sifu/coach/chat.py` — grounded chat service and deterministic fallback.
- `src/xiangqi_sifu/api/models.py` — API request/response models.
- `src/xiangqi_sifu/api/dependencies.py` — configured services and database paths.
- `src/xiangqi_sifu/api/routes/*.py` — health, analysis, records, play, library, and coach routes.
- `src/xiangqi_sifu/api/main.py` — FastAPI app factory and production static mount.
- `scripts/run_app.py` — one-command local launcher.

### React client

- `frontend/web/package.json` — scripts and pinned dependencies.
- `frontend/web/src/app/App.tsx` — activity routing and restoration.
- `frontend/web/src/app/api.ts` — typed API client.
- `frontend/web/src/app/types.ts` — shared client models.
- `frontend/web/src/components/Launchpad.tsx` — five launch actions and dialogs.
- `frontend/web/src/components/XiangqiBoard.tsx` — grid, pieces, overlays, and editing.
- `frontend/web/src/components/AnalysisRibbon.tsx` — toggleable independent meta.
- `frontend/web/src/components/CoachPanel.tsx` — persistent right-hand chat.
- `frontend/web/src/features/position/PositionFlow.tsx` — screenshot/FEN confirmation and analysis.
- `frontend/web/src/features/review/ReviewFlow.tsx` — record selection and move review.
- `frontend/web/src/features/play/PlayFlow.tsx` — friend/Sifu play.
- `frontend/web/src/styles/*.css` — Scholar's Studio tokens and responsive layout.

---

### Task 1: Reproducible Toolchain and API Bootstrap

**Files:**
- Modify: `pyproject.toml`
- Create: `src/xiangqi_sifu/api/models.py`
- Modify: `src/xiangqi_sifu/api/main.py`
- Create: `tests/api/test_health.py`
- Create: `frontend/web/package.json`
- Create: `frontend/web/tsconfig.json`
- Create: `frontend/web/vite.config.ts`
- Create: `frontend/web/index.html`
- Create: `frontend/web/src/main.tsx`

**Interfaces:**
- Produces: `create_app() -> FastAPI`
- Produces: `GET /api/health -> {status, engine_available, personal_db, reference_db}`

- [ ] **Step 1: Repair the local Python environment without using training dependencies**

Run:

```bash
uv venv .venv --python /opt/homebrew/bin/python3.11
uv pip install --python .venv/bin/python -e '.[dev,app,vision]'
```

Expected: `.venv/bin/python` exists and imports `fastapi`, `pydantic`, `PIL`, and `numpy`.

- [ ] **Step 2: Write the failing health API test**

```python
from fastapi.testclient import TestClient
from xiangqi_sifu.api.main import create_app


def test_health_describes_local_runtime(tmp_path):
    client = TestClient(create_app(data_dir=tmp_path, engine_path=None))
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "engine_available": False,
        "personal_db": str(tmp_path / "personal.db"),
        "reference_db": str(tmp_path / "reference.db"),
    }
```

- [ ] **Step 3: Run the test and confirm the missing app factory failure**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest tests/api/test_health.py -q`

Expected: FAIL because `create_app` does not exist.

- [ ] **Step 4: Add application dependencies and the minimal app factory**

Add `app = ["fastapi>=0.116,<1", "uvicorn[standard]>=0.35,<1", "python-multipart>=0.0.20,<1"]` to `pyproject.toml`. Implement `create_app(data_dir: Path, engine_path: Path | None)` and return the exact response asserted above.

- [ ] **Step 5: Verify backend bootstrap and scaffold the frontend**

Run the targeted test, then install the pinned React/Vite/Vitest dependencies and run `npm run build` from `frontend/web`.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml src/xiangqi_sifu/api tests/api frontend/web
git commit -m "build: add local API and React toolchains"
```

### Task 2: Authoritative Xiangqi Rules

**Files:**
- Create: `src/xiangqi_sifu/board/rules.py`
- Create: `src/xiangqi_sifu/board/game.py`
- Create: `tests/board/test_rules.py`
- Create: `tests/board/test_game_state.py`

**Interfaces:**
- Produces: `BoardState.from_fen(fen: str) -> BoardState`
- Produces: `BoardState.to_fen() -> str`
- Produces: `legal_moves(state: BoardState) -> tuple[str, ...]`
- Produces: `apply_legal_move(state: BoardState, move: str) -> BoardState`
- Produces: `position_status(state: BoardState, repetitions: int = 1) -> PositionStatus`

- [ ] **Step 1: Write failing tests for each piece's movement restrictions**

Tests must cover palace bounds, flying generals, advisor diagonals, elephant eyes/river, horse legs, rook blockers, cannon screens, and soldier river behavior using minimal FEN fixtures and exact UCI move membership assertions.

- [ ] **Step 2: Verify all new rule tests fail for the missing module**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest tests/board/test_rules.py -q`

Expected: collection failure for `xiangqi_sifu.board.rules`.

- [ ] **Step 3: Implement immutable board parsing and pseudo-legal generation**

Use a `BoardState(board: tuple[tuple[str | None, ...], ...], active_color: str, halfmove_clock: int, fullmove_number: int)` dataclass and explicit piece generators. Do not add a third-party chess-rules dependency.

- [ ] **Step 4: Write failing self-check and terminal-state tests**

Assert a pinned piece cannot expose its general, facing generals are check, checkmate has no legal moves while checked, stalemate has no legal moves while not checked, and repetition count 3 yields a draw status.

- [ ] **Step 5: Implement legal filtering and `GameState` transitions**

`apply_legal_move` rejects moves absent from `legal_moves`. `GameState.push` appends the move/FEN and increments repetition counts without mutating previous states.

- [ ] **Step 6: Run board tests and existing FEN/parser tests**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest tests/board tests/test_fen.py tests/test_parser.py -q`

- [ ] **Step 7: Commit**

```bash
git add src/xiangqi_sifu/board tests/board
git commit -m "feat: implement legal Xiangqi game rules"
```

### Task 3: Personal Persistence and Played Games

**Files:**
- Create: `src/xiangqi_sifu/database/personal.py`
- Create: `src/xiangqi_sifu/database/personal_schema.sql`
- Create: `tests/database/test_personal.py`

**Interfaces:**
- Produces: `PersonalRepository.create_game(mode, human_side, ai_level, player_names) -> StoredGame`
- Produces: `PersonalRepository.append_move(game_id, uci, resulting_fen) -> StoredGame`
- Produces: `PersonalRepository.finish_game(game_id, result, termination) -> StoredGame`
- Produces: `PersonalRepository.list_games() -> list[StoredGame]`

- [ ] **Step 1: Write a failing autosave and isolation test**

Create a game, append `h2e2`, reopen the repository, and assert the move remains. Create a sentinel `reference.db`, perform personal writes, and assert its bytes do not change.

- [ ] **Step 2: Implement the schema and transactional repository**

Use tables `profile`, `games`, `game_events`, `moves`, `analysis_jobs`, `evaluations`, `coach_threads`, `coach_messages`, and `recognitions`. Apply schema versioning with `PRAGMA user_version`.

- [ ] **Step 3: Add tests for undo events, finish metadata, and in-progress restoration**

Undo records an event and marks the latest move retracted; it does not erase audit history. Listing sorts active games before completed games and then by `updated_at DESC`.

- [ ] **Step 4: Verify repository tests and commit**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest tests/database/test_personal.py -q`

Commit message: `feat: persist personal games and sessions`.

### Task 4: Pikafish MultiPV and Analysis Semantics

**Files:**
- Modify: `src/xiangqi_sifu/engine/pikafish.py`
- Create: `src/xiangqi_sifu/analysis/models.py`
- Create: `src/xiangqi_sifu/analysis/service.py`
- Modify: `tests/test_pikafish.py`
- Create: `tests/analysis/test_service.py`

**Interfaces:**
- Produces: `PikafishEngine.analyze_lines(position, multipv=3) -> tuple[EngineLine, ...]`
- Produces: `estimated_red_win_rate(score_cp: int) -> float`
- Produces: `move_impact(before, after, side) -> MoveImpact`

- [ ] **Step 1: Write failing UCI parsing tests for MultiPV, depth, nodes, and mate**

Feed interleaved `info depth 14 multipv 1 ...` and `multipv 2 ...` lines and assert stable ordering, Red-perspective normalization, and distinct mate fields.

- [ ] **Step 2: Implement the minimal MultiPV parser and engine option command**

Send `setoption name MultiPV value N` before `go`, retain the final line for each `multipv`, and preserve the existing `analyze` interface by returning line one.

- [ ] **Step 3: Write failing win-rate and mover-impact tests**

Assert `rate(-300) < rate(0) < rate(300)`, `rate(0) == 0.5`, symmetry within rounding, and Black mover loss reverses Red-score deltas.

- [ ] **Step 4: Implement score semantics and bounded analysis orchestration**

Use `1 / (1 + exp(-score_cp / 240))`, rounded to four decimals and clamped to `[0.01, 0.99]`. Mate positions return no estimated win rate.

- [ ] **Step 5: Verify with the local Pikafish binary at depth 4**

Run unit tests, then a one-position integration command against `engines/pikafish-2026-01-02/MacOS/pikafish-apple-silicon` and assert at least one legal best move.

- [ ] **Step 6: Commit**

Commit message: `feat: add MultiPV analysis metadata`.

### Task 5: Record Inspection and Reference Library

**Files:**
- Modify: `src/xiangqi_sifu/parsers/pgn_parser.py`
- Create: `src/xiangqi_sifu/records/service.py`
- Create: `src/xiangqi_sifu/database/reference.py`
- Create: `tests/records/test_inspection.py`
- Create: `tests/database/test_reference.py`
- Modify: `scripts/build_knowledge_base.py`

**Interfaces:**
- Produces: `inspect_record(text, offset=0, limit=50) -> RecordInspection`
- Produces: `ReferenceRepository.search_games(query, offset, limit) -> GamePage`
- Produces: `ReferenceRepository.get_game(game_id) -> GameRecord`

- [ ] **Step 1: Write failing single/multi-game inspection tests**

Assert a single game returns one summary, a two-game `.pgns` returns two summaries with offsets, and an invalid token response includes game index and token text.

- [ ] **Step 2: Implement bounded metadata inspection**

Reuse `WxfBulkParser` boundaries. Parse only the requested page and retain byte offsets so selecting a game does not load a 100 MB source into browser state.

- [ ] **Step 3: Write failing read-only reference tests**

Open a fixture database with SQLite URI `mode=ro`, search by Red/Black/Event, load a game, and assert write attempts fail.

- [ ] **Step 4: Implement reference queries and builder compatibility**

Reuse the current knowledge database when its schema supports the required fields; add a migration-free derived view/table only in the explicit builder command.

- [ ] **Step 5: Verify against bounded slices of both supplied corpora**

Inspect the first three games from each `.pgns`, then query the existing knowledge database without rebuilding it.

- [ ] **Step 6: Commit**

Commit message: `feat: add record picker and tournament library`.

### Task 6: Screenshot Recognition and Position Validation

**Files:**
- Create: `src/xiangqi_sifu/vision/service.py`
- Modify: `src/xiangqi_sifu/vision/board_detector.py`
- Modify: `src/xiangqi_sifu/vision/image_recognizer.py`
- Create: `tests/vision/test_service.py`

**Interfaces:**
- Produces: `recognize_image(image, profile, active_color) -> RecognitionResult`
- Produces: `validate_piece_map(pieces, active_color) -> ValidationResult`

- [ ] **Step 1: Write a failing app-board screenshot round-trip test**

Render the standard Scholar's Studio board fixture to PNG, recognize it with the bundled profile, and assert its FEN equals `DEFAULT_START_FEN` with 32 pieces and confidence values for occupied squares.

- [ ] **Step 2: Implement a bundled profile and automatic board bounds fallback**

Detect the dominant rectangular grid region for screenshots with margins, then use the existing 90-intersection recognizer. Ship generated templates matching the app's piece glyph treatment and keep external profile loading explicit.

- [ ] **Step 3: Write failing validation tests**

Assert missing generals, general outside palace, excessive piece count, and facing generals return square-addressed issues; a valid start position returns none.

- [ ] **Step 4: Implement validation and confidence serialization**

Recognition never starts analysis. It returns `requires_confirmation=True` plus the original dimensions, board rectangle, orientation, FEN, piece map, confidence map, and issues.

- [ ] **Step 5: Verify vision tests and commit**

Commit message: `feat: recognize and confirm board screenshots`.

### Task 7: Grounded Coach and API Vertical Slices

**Files:**
- Create: `src/xiangqi_sifu/coach/chat.py`
- Create: `src/xiangqi_sifu/api/dependencies.py`
- Create: `src/xiangqi_sifu/api/routes/analysis.py`
- Create: `src/xiangqi_sifu/api/routes/records.py`
- Create: `src/xiangqi_sifu/api/routes/play.py`
- Create: `src/xiangqi_sifu/api/routes/library.py`
- Create: `src/xiangqi_sifu/api/routes/coach.py`
- Modify: `src/xiangqi_sifu/api/main.py`
- Create: `tests/coach/test_chat.py`
- Create: `tests/api/test_flows.py`

**Interfaces:**
- Produces all `/api` routes listed in the design specification.
- Produces: `CoachService.reply(context: CoachContext, question: str) -> CoachReply`

- [ ] **Step 1: Write failing deterministic coach grounding tests**

Given best move `h0g2`, score `+130`, and question "why?", assert the fallback names `h0g2`, labels the advantage for Red, and never names an unavailable tactical motif.

- [ ] **Step 2: Implement bounded coach context and verification**

The local LoRA provider is attempted only when configured. Failed loading falls back deterministically. Reject candidate text that contradicts the best move or score direction.

- [ ] **Step 3: Write failing API flow tests**

Cover position validation/analysis, record inspection, new friend game plus move autosave, Sifu AI move, reference search, and coach message persistence using temporary databases and a fake engine.

- [ ] **Step 4: Implement typed routes and dependencies**

Routes translate domain exceptions into `422`, engine availability into `503`, missing records into `404`, and cancellation into a persisted job state.

- [ ] **Step 5: Run the complete Python suite and commit**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q`

Commit message: `feat: expose local coaching and game APIs`.

### Task 8: Scholar's Studio React Shell

**Files:**
- Create: `frontend/web/src/app/types.ts`
- Create: `frontend/web/src/app/api.ts`
- Create: `frontend/web/src/app/App.tsx`
- Create: `frontend/web/src/components/Launchpad.tsx`
- Create: `frontend/web/src/components/Workspace.tsx`
- Create: `frontend/web/src/components/XiangqiBoard.tsx`
- Create: `frontend/web/src/components/AnalysisRibbon.tsx`
- Create: `frontend/web/src/components/CoachPanel.tsx`
- Create: `frontend/web/src/styles/tokens.css`
- Create: `frontend/web/src/styles/app.css`
- Create: `frontend/web/src/app/App.test.tsx`

**Interfaces:**
- Consumes typed `/api/bootstrap`, play, analysis, and coach responses.
- Produces launchpad-to-workspace activity state.

- [ ] **Step 1: Write a failing launchpad test**

Render `App`, assert all five accepted action names, and assert no element with accessible name `Xiangqi board` exists.

- [ ] **Step 2: Implement the launchpad and activity transition shell**

Use semantic buttons and dialogs. The board mounts only after a successful activity creation/load response.

- [ ] **Step 3: Write failing workspace hierarchy tests**

Assert `Ask Sifu` remains mounted after clicking `Analysis on`, while score, win rate, arrow overlay, and analysis ribbon disappear.

- [ ] **Step 4: Implement the board and independent panels**

Render the 9×10 SVG grid, river gap, palace diagonals, coordinates, Chinese pieces, legal-target markers, last move, and compact best-move arrow. Preserve chat as a sibling grid column.

- [ ] **Step 5: Add Scholar's Studio tokens and responsive CSS**

Use warm paper, wood, jade, and cinnabar tokens; visible focus states; minimum 44px touch targets; and no horizontal scrolling at 1280px or 768px.

- [ ] **Step 6: Run frontend tests/build and commit**

Run: `npm test -- --run && npm run build` from `frontend/web`.

Commit message: `feat: build Scholar's Studio application shell`.

### Task 9: Position and Record Review UI

**Files:**
- Create: `frontend/web/src/features/position/PositionFlow.tsx`
- Create: `frontend/web/src/features/position/PositionFlow.test.tsx`
- Create: `frontend/web/src/features/review/ReviewFlow.tsx`
- Create: `frontend/web/src/features/review/ReviewFlow.test.tsx`
- Create: `frontend/web/src/components/EvaluationChart.tsx`

**Interfaces:**
- Consumes recognition, validation, record inspection, job, and coach APIs.
- Produces confirmed position/game workspace contexts.

- [ ] **Step 1: Write failing screenshot confirmation tests**

Upload an image fixture, assert low-confidence squares are marked, change one piece, choose active side, confirm, and assert analysis starts only after confirmation.

- [ ] **Step 2: Implement screenshot/FEN/manual setup flow**

Keep the source image visible beside the editable board until confirmation. Surface server validation issues by square.

- [ ] **Step 3: Write failing multi-game and synchronized review tests**

Upload two games, select the second, analyze, click a mistake row, and assert board ply, chart selection, analysis ribbon, and chat context all use that ply.

- [ ] **Step 4: Implement record picker, review navigation, and chart**

Use first/previous/next/last controls, clickable move list, directly labeled evaluation line, and a cancelable progress state.

- [ ] **Step 5: Verify frontend tests/build and commit**

Commit message: `feat: add position and record coaching workflows`.

### Task 10: Play a Friend and Challenge Sifu UI

**Files:**
- Create: `frontend/web/src/features/play/PlayFlow.tsx`
- Create: `frontend/web/src/features/play/NewGameDialog.tsx`
- Create: `frontend/web/src/features/play/PlayFlow.test.tsx`
- Modify: `src/xiangqi_sifu/api/routes/play.py`
- Create: `tests/api/test_play_strength.py`

**Interfaces:**
- Consumes persisted game and legal-move APIs.
- Produces new-game setup, live play, resume, resign, undo, and post-game review transition.

- [ ] **Step 1: Write failing friend-game persistence UI test**

Start **Play a Friend**, move `h2e2`, remount using the persisted active-game response, and assert the cannon remains on `e2`.

- [ ] **Step 2: Implement friend play with server-authoritative moves**

Client highlights returned legal moves, sends the selected UCI move, and replaces local state with the server response.

- [ ] **Step 3: Write failing AI strength tests**

With fixed MultiPV lines, assert level 10 chooses rank 1, level 1 may choose a legal candidate inside its configured loss band, and adaptive changes by no more than one level after a game.

- [ ] **Step 4: Implement deterministic difficulty bands and adaptive profile update**

Seed candidate choice with game ID and ply for reproducible tests. Never choose outside the engine's MultiPV candidates or return an illegal move.

- [ ] **Step 5: Implement Challenge Sifu controls and post-game review action**

Support side choice, random side, levels 1–10, Adaptive, hint reveal, resign, undo, restart, and **Review this game**.

- [ ] **Step 6: Verify backend/frontend tests and commit**

Commit message: `feat: add persisted friend and Sifu play`.

### Task 11: Launcher, Production Integration, and End-to-End Verification

**Files:**
- Create: `scripts/run_app.py`
- Modify: `src/xiangqi_sifu/api/main.py`
- Modify: `README.md`
- Modify: `.env.example`
- Create: `frontend/web/playwright.config.ts`
- Create: `frontend/web/e2e/app.spec.ts`

**Interfaces:**
- Produces: `PYTHONPATH=src .venv/bin/python scripts/run_app.py`

- [ ] **Step 1: Write a failing launcher smoke test**

Start on an ephemeral loopback port with temporary data paths, wait for `/api/health`, and assert `/` returns the production React shell.

- [ ] **Step 2: Implement static mount and launcher**

Build frontend assets first. The launcher resolves the bundled Pikafish path, creates personal storage, opens the browser unless `--no-open`, and shuts down cleanly on interruption.

- [ ] **Step 3: Add Playwright end-to-end tests**

Cover launchpad board absence, friend-game persistence across reload, Sifu legal reply, screenshot confirmation/analysis/chat, multi-game selection/review/chat, analysis toggle with persistent chat, and read-only tournament search.

- [ ] **Step 4: Run fresh complete verification**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q
cd frontend/web && npm test -- --run
cd frontend/web && npm run build
cd frontend/web && npm run e2e
```

Expected: all commands exit 0 with no failing tests.

- [ ] **Step 5: Run manual browser visual QA**

Inspect launchpad, 1280px workspace, 768px stacked layout, board grid, arrow size, permanent chat, analysis toggle, screenshot editor, record review, and both play modes. Fix any clipping, overlap, illegible contrast, or broken interaction and rerun affected checks.

- [ ] **Step 6: Update documentation and commit**

Document prerequisites, one-command launch, database locations, reference indexing, model fallback, supported screenshot scope, and test commands.

Commit message: `docs: ship standalone Xiangqi Sifu app`.

---

## Plan Self-Review

- Every requirement in the approved design maps to at least one task.
- Personal/reference database isolation is tested in Tasks 3, 5, 7, and 11.
- The launchpad board-absence requirement is tested in Tasks 8 and 11.
- Persistent chat and independent analysis visibility are tested in Tasks 8 and 11.
- Screenshot, record, tournament, friend play, and Sifu play each have backend, frontend, and end-to-end coverage.
- Model training is absent from all execution steps.
