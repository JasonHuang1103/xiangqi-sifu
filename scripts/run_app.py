#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
import threading
import webbrowser
from pathlib import Path

import uvicorn

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from xiangqi_sifu.api.main import create_app  # noqa: E402


def resolve_engine_path(explicit: str | None = None) -> Path | None:
    configured = explicit or os.environ.get("XIANGQI_SIFU_ENGINE_PATH")
    candidates = [
        Path(configured).expanduser() if configured else None,
        ROOT / "engines/pikafish-2026-01-02/MacOS/pikafish-apple-silicon",
    ]
    return next((path.resolve() for path in candidates if path is not None and path.is_file()), None)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the local Xiangqi Sifu desktop-style web app.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--data-dir", default=str(ROOT / "data/processed"))
    parser.add_argument("--engine")
    parser.add_argument("--frontend-dir", default=str(ROOT / "frontend/web/dist"))
    parser.add_argument("--no-open", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    frontend = Path(args.frontend_dir)
    if not (frontend / "index.html").is_file():
        raise SystemExit("The web client is not built. Run: cd frontend/web && npm install && npm run build")
    engine = resolve_engine_path(args.engine)
    application = create_app(
        data_dir=Path(args.data_dir),
        engine_path=engine,
        frontend_dir=frontend,
    )
    url = f"http://{args.host}:{args.port}"
    if not args.no_open:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    print(f"Xiangqi Sifu is ready at {url}")
    print(f"Personal games: {Path(args.data_dir) / 'personal.db'}")
    print(f"Pikafish: {engine or 'not found (analysis disabled)'}")
    uvicorn.run(application, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
