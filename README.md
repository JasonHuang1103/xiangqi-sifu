# Xiangqi Sifu

Xiangqi Sifu is a fully local-first Xiangqi desktop-style web app. It combines a legal playable board, bundled Pikafish analysis, tournament records, and a grounded coaching chat in the **Scholar's Studio** interface.

No account or network service is required during normal use. Personal games are saved only on the local machine.

## What is included

- **Play a Friend** — a same-device match with legal-move highlighting, autosave, undo, resign, resume, and post-game review.
- **Challenge Sifu** — play Red, Black, or a random side at levels 1–10 or Adaptive strength. Sifu's moves always come from legal Pikafish MultiPV candidates.
- **Analyze a Position** — paste FEN or upload a supported digital-board screenshot, confirm/correct the FEN, then inspect score, win-rate estimate, best move, principal variation, and follow-up coaching.
- **Review a Record** — open `.pgn`, `.pgns`, or ICCS text, select a game from multi-game files, and navigate synchronized board, evaluation, metadata, and chat contexts.
- **Tournament Library** — search 141,511 locally indexed master games from the two supplied corpora.

The initial screen intentionally contains no board. A board appears only after starting or loading an activity.

## Quick start

Requirements: Python 3.11+, Node.js 20+, and macOS Apple Silicon for the bundled Pikafish binary. Other platforms can provide a compatible Pikafish binary through `--engine` or `XIANGQI_SIFU_ENGINE_PATH`.

```bash
python3.11 -m venv .venv
.venv/bin/pip install -e ".[app,vision,dev]"
cd frontend/web
npm install
npm run build
cd ../..
.venv/bin/python scripts/run_app.py
```

The launcher opens `http://127.0.0.1:8765`. To run without opening the system browser:

```bash
.venv/bin/python scripts/run_app.py --no-open
```

Useful options:

```text
--host 127.0.0.1
--port 8765
--data-dir data/processed
--engine /path/to/pikafish
--frontend-dir frontend/web/dist
```

## Local data and privacy

- Personal matches, undo audit events, recognition confirmations, and coach threads live in `data/processed/personal.db`.
- Tournament data is queried read-only from `data/processed/xiangqi_sifu_knowledge.db` (or `data/processed/reference.db` when present).
- The two stores are physically separate. Playing or chatting never mutates the tournament database.
- The raw supplied corpora remain at `data/raw/WXF-41743games.pgns` and `data/raw/dpxq-99813games.pgns`.

To keep a different personal history, launch with another `--data-dir`.

## Analysis and coaching

Pikafish is the tactical source of truth. Scores use Red's perspective, win-rate is an explicit estimate derived from centipawns, and mate scores are shown separately. Long game records are reconstructed immediately and analyzed one selected ply at a time so the review workspace remains responsive.

The current coach is a deterministic local fallback grounded in the exact FEN, engine best move, score, and principal variation. The repository contains optional LoRA preparation/export infrastructure, but this application does **not** start model training. A future local fine-tuned explanation model can replace the fallback without changing the board or engine contracts.

Screenshot recognition currently supports screenshots rendered in the Scholar's Studio digital-board profile. Every recognition result requires confirmation through an editable FEN before analysis; arbitrary camera photos are not claimed as supported yet.

## Development

Run the API and Vite development server separately:

```bash
PYTHONPATH=src .venv/bin/python -c 'from pathlib import Path; import uvicorn; from xiangqi_sifu.api.main import create_app; uvicorn.run(create_app(engine_path=Path("engines/pikafish-2026-01-02/MacOS/pikafish-apple-silicon")), host="127.0.0.1", port=8000)'
cd frontend/web && npm run dev
```

Verification:

```bash
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q
cd frontend/web && npm test -- --run
cd frontend/web && npm run build
```

The Python suite covers rules, persistence isolation, MultiPV parsing, recognition, record/library access, coaching, adaptive strength, API flows, and production static serving. The React suite covers launch invariants, setup dialogs, position/record intake, workspace layout, and legal click-to-move interaction.

## Rebuilding the tournament index

The checked-in processed data can be used directly. To rebuild from the two `.pgns` files:

```bash
PYTHONPATH=src .venv/bin/python scripts/import_games.py --source data/raw/WXF-41743games.pgns --output-dir data/processed/wxf_41743games
PYTHONPATH=src .venv/bin/python scripts/import_games.py --source data/raw/dpxq-99813games.pgns --output-dir data/processed/dpxq_99813games
PYTHONPATH=src .venv/bin/python scripts/build_knowledge_base.py
```
