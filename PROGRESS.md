# Xiangqi Sifu — Project Progress

Last updated: 2026-07-19

This file is the durable development ledger for Xiangqi Sifu. It records what the project is, why major decisions were made, what has shipped, what remains intentionally incomplete, and how each implementation phase was verified.

## How to maintain this ledger

Every future code, design, data, architecture, or plan change must update this file as part of the same work.

1. Before implementation, add the intended scope to **Active work**.
2. Update that entry whenever the plan, assumptions, or design direction changes.
3. Before committing, move completed work into the chronological log with the outcome, important decisions, affected areas, and verification performed.
4. Keep entries concise enough to scan, but specific enough that someone outside the project can understand why the change exists.
5. Do not record secrets, local credentials, generated personal game data, or large raw outputs here.

## Current product snapshot

Xiangqi Sifu is a fully local-first, desktop-style web application with a React interface and local Python API. Its current product surface includes:

- A board-free launchpad that only opens the game workspace after the user starts or loads an activity.
- **Play a Friend**, a same-device legal Xiangqi match with autosave, undo, resign, resume, last-move tracing, and post-game review.
- **Challenge Sifu**, a Pikafish-backed opponent with levels 1–10, side selection, and adaptive strength.
- **Analyze a Position**, accepting FEN or supported Scholar's Studio board screenshots, followed by editable confirmation, engine metadata, and grounded coaching chat.
- **Review a Record**, accepting `.pgn`, `.pgns`, and ICCS text with multi-game selection and synchronized move/evaluation navigation.
- A local **Tournament Library** indexing 141,511 master games from the two supplied PGNS corpora.
- A persistent right-side coaching panel grounded in the exact position and engine result.
- A separate personal SQLite database for played games, sessions, recognition confirmations, undo events, and coach threads.
- The **Scholar's Studio** visual system: parchment, cinnabar, jade, traditional board grid, Chinese piece glyphs, and responsive desktop-style layout.

## Architecture at a glance

| Area | Current implementation |
| --- | --- |
| Application shell | React 19, TypeScript, Vite |
| Local service | FastAPI served by the local launcher |
| Xiangqi rules | In-repository legal move generation and state handling |
| Engine | Bundled/local Pikafish subprocess with MultiPV support |
| Analysis metadata | Red-perspective score, mate score, estimated win rate, best move, PV, and score change |
| Coaching | Deterministic local fallback grounded in FEN and engine output |
| Personal storage | `data/processed/personal.db` |
| Tournament storage | Read-only local knowledge/reference database |
| Screenshot recognition | Scholar's Studio digital-board profile with mandatory editable FEN confirmation |
| Testing | Pytest, Vitest/Testing Library, and Playwright |

## Durable product decisions

| Date | Decision | Reason / consequence |
| --- | --- | --- |
| 2026-07-16 | Treat “standalone” as a fully local-first desktop-style web app. | Normal use requires no account or hosted service; user data stays local. |
| 2026-07-16 | Use the Scholar's Studio direction. | Establishes the parchment/cinnabar/jade visual language while retaining a standard gridded Xiangqi board. |
| 2026-07-16 | Keep the coaching chat permanently on the right side of the workspace. | Analysis metadata must occupy the board column and never overlap the coach. |
| 2026-07-16 | Start on a board-free launchpad. | The workspace appears only after a screenshot, FEN, record, library game, or new match is selected. |
| 2026-07-16 | Name play modes **Play a Friend** and **Challenge Sifu**. | Avoids trivial PvP/PvC terminology and supports the coaching theme. |
| 2026-07-16 | Store personal games separately from tournament records. | Protects the read-only corpus and makes all played games resumable without contaminating reference data. |
| 2026-07-16 | Use existing models only as placeholders; do not start training. | Training infrastructure may be prepared, but compute-heavy fine-tuning requires a later explicit decision and resources. |
| 2026-07-17 | Reserve stable analysis and notice space, and top-anchor the board. | Moving pieces or toggling analysis must not shift the board. |
| 2026-07-17 | Show the last move with a muted gray origin footprint and destination halo. | Gives persistent move context without competing with green selection and analysis indicators. |

## Active work

No implementation is currently in progress.

## Known limitations and deferred work

- The coaching language model is still a deterministic grounded fallback. Optional LoRA tooling exists, but no new training run should start without explicit approval and suitable compute.
- Screenshot recognition is intentionally limited to the supported digital-board profile. Arbitrary photographs and unknown board themes are not yet claimed as supported.
- The bundled Pikafish binary targets macOS Apple Silicon. Other platforms must provide a compatible binary.
- The app is local-first and desktop-style; native desktop packaging is not yet part of the shipped workflow.

## Verification baseline

Last full verification on 2026-07-17:

- Python: `107 passed` using `.venv/bin/python -m pytest -q`.
- React component tests: `8 passed` using `npm test -- --run`.
- Production frontend build: passed using `npm run build`.
- Playwright workflows: `3 passed` using `npm run e2e`.
- Manual browser inspection: desktop and short-window layouts, last-move trace, right-side coach, and analysis visibility were checked.

## Chronological development log

### 2026-07-19 — Established the project progress ledger

- Added this `PROGRESS.md` as the shared record for product evolution, decisions, implementation status, limitations, and verification.
- Added repository-level agent instructions requiring future code and plan changes to update this ledger along the way.
- Linked the ledger from the main README so contributors and outside readers can find it immediately.
- Reconstructed the history below from the complete Git commit history and current shipped behavior.

### 2026-07-17 — Stabilized board feedback and readability

Commits: `0655f9ab`, `b54f6f63`, `cecf4cc5`

- Specified and planned a stable board layout with a persistent analysis slot and reserved status line.
- Added gray last-move trace markers for the origin and destination in live play and selected review plies.
- Made the workspace fit the application viewport and scale the board without document scrolling in shorter windows.
- Prevented board-coordinate changes after a move or analysis toggle; kept the coach fixed on the right.
- Increased undersized navigation, metadata, archive, form, toolbar, and coach typography while retaining the established display hierarchy.
- Added component and Playwright regressions for move traces, persistent analysis layout, board coordinates, compact layout, and short-window fit.

### 2026-07-16 — Shipped the standalone Scholar's Studio application

Commits: `88a3f29f` through `4800e7df`

#### Product definition and implementation plan

- Reframed the earlier analysis prototype as a complete local-first Xiangqi application.
- Captured the product requirements, Scholar's Studio design, architecture, delivery phases, testing strategy, and explicit non-goal of starting model training.

#### Local application toolchains

- Added the FastAPI application factory and health endpoint.
- Added the React/TypeScript/Vite frontend with Vitest and Testing Library.
- Added the production launcher and static frontend serving.

#### Legal Xiangqi rules

- Implemented legal move generation for all piece types, palace and river constraints, cannon screens, horse legs, elephant eyes, flying generals, check detection, and terminal state handling.
- Added game-state reconstruction and focused rule coverage.

#### Personal persistence

- Added a dedicated personal SQLite schema and repository.
- Persisted matches, moves, undo audit events, study sessions, screenshot confirmations, and coach messages.
- Kept personal storage physically separate from the tournament/reference database.

#### Engine analysis and metadata

- Expanded the Pikafish adapter to support MultiPV output.
- Added normalized Red-perspective centipawn and mate scores, best move, principal variations, and explicit estimated win rates.
- Added the analysis service and engine parsing tests.

#### Records and tournament library

- Added PGN/PGNS/ICCS inspection with explicit multi-game selection.
- Added read-only tournament database access and local search.
- Exposed the two supplied PGNS corpora through the indexed 141,511-game library.

#### Screenshot recognition

- Added board calibration, grid sampling, piece classification, orientation handling, confidence reporting, and FEN generation for the supported Scholar's Studio digital-board profile.
- Required editable FEN confirmation before analysis and recorded corrections locally.

#### Local APIs and grounded coaching

- Added routes for analysis, records, library search, coaching, and playable games.
- Added legal friend/Sifu move endpoints, AI move selection, undo, resign, adaptive strength, and serialized game state.
- Added deterministic local coaching grounded in the current FEN, engine score, best move, and PV.

#### Scholar's Studio interface

- Built the board-free launchpad, intake flows, searchable library, analysis workspace, playable board, metadata ribbon, evaluation chart, and fixed right-side coaching panel.
- Added the traditional Xiangqi grid, Chinese glyphs, smaller green analysis arrowhead, Flip and Analysis controls, and responsive desktop-style layout.
- Added **Play a Friend** and **Challenge Sifu** setup and persisted resume flows.

#### Production delivery

- Added the single local launcher, quick-start documentation, environment configuration, static-serving tests, and Playwright user journeys.
- Documented data isolation, engine configuration, current coaching behavior, screenshot limits, and tournament-index rebuild steps.

### 2026-06-14 — Added the initial vision phase and mate-finder side project

Commit: `5348eef2`

- Added the first screenshot-to-FEN pipeline, orientation and grid helpers, sample labels, comparison utilities, and vision tests.
- Added a separate Pikafish forced-mate finder with reporting and screenshot support.
- Expanded the earlier roadmap and usage documentation.

### 2026-06-11 — Added knowledge and optional LoRA preparation

Commit: `82abdbf9`

- Added knowledge-base construction and query infrastructure for the supplied game records.
- Added explanation dataset generation, splitting, evaluation, training configuration, dry-run safeguards, and adapter export tooling.
- Selected `Qwen/Qwen3.5-2B` as the placeholder base for optional LoRA work.
- Kept heavyweight training dependencies optional and prevented training from starting without an explicit flag.

### 2026-06-06 — Built the original analysis MVP

Commit: `3320a5da`

- Added ICCS/PGN-like parsing, FEN reconstruction, Pikafish/mock analysis, mistake detection, SQLite storage, Markdown reporting, CLI commands, and a Streamlit prototype.
- Added the initial automated tests and sample games.
- This phase was intentionally a review pipeline rather than a fully legal playable application.

### 2026-06-04 — Repository created

Commit: `957272ec`

- Created the Xiangqi Sifu repository and initial README.
