# Pikafish Engine

Pikafish is an external UCI engine. The backend should launch it as a subprocess
and communicate through standard input/output; do not import engine code into
the Python package.

Run 1 uses `MockEngine` for deterministic tests and dry runs. Run 2 adds the
real subprocess adapter in `xiangqi_sifu.engine.pikafish.PikafishEngine`.

Expected local binary path for this workspace:

```text
engines/pikafish-2026-01-02/MacOS/pikafish-apple-silicon
```

Set it with:

```bash
export XIANGQI_SIFU_ENGINE_PATH=engines/pikafish-2026-01-02/MacOS/pikafish-apple-silicon
```

Analyze with the real engine:

```bash
PYTHONPATH=src python3 -m xiangqi_sifu.cli analyze data/examples/simple_game.txt \
  --engine engines/pikafish-2026-01-02/MacOS/pikafish-apple-silicon \
  --db data/processed/xiangqi_sifu.db \
  --report data/processed/pikafish_report.md \
  --depth 8
```

The adapter sends:

```text
uci
isready
position fen <fen>
go depth <n>
```

It reads `score cp`, `score mate`, `pv`, and `bestmove`, then converts scores
to red-centric values before mistake detection.
