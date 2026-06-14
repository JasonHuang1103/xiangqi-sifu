from __future__ import annotations

import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

SCORE_CP_RE = re.compile(r"\bscore cp (-?\d+)")
SCORE_MATE_RE = re.compile(r"\bscore mate (-?\d+)")
PV_RE = re.compile(r"\bpv\s+(.+)$")


@dataclass(frozen=True)
class MateSearchResult:
    fen: str
    forced_mate_found: bool
    mate_score: int | None
    cp_score: int | None
    best_move: str | None
    pv: tuple[str, ...]
    message: str


def find_forced_mate(
    fen: str,
    *,
    engine_path: str | Path,
    depth: int = 12,
    movetime_ms: int | None = None,
    startup_timeout: float = 5.0,
    command_timeout: float = 30.0,
) -> MateSearchResult:
    with _UciEngine(
        engine_path,
        startup_timeout=startup_timeout,
        command_timeout=command_timeout,
    ) as engine:
        lines = engine.analyze(fen, depth=depth, movetime_ms=movetime_ms)
    mate_score, cp_score, best_move, pv = _parse_analysis(lines)
    forced = mate_score is not None
    return MateSearchResult(
        fen=fen,
        forced_mate_found=forced,
        mate_score=mate_score,
        cp_score=cp_score,
        best_move=best_move,
        pv=tuple(pv),
        message=(
            f"Pikafish found a forced mate score: mate {mate_score}."
            if forced
            else "No forced mate found at this search setting."
        ),
    )


class _UciEngine:
    def __init__(
        self,
        engine_path: str | Path,
        *,
        startup_timeout: float,
        command_timeout: float,
    ) -> None:
        self.engine_path = Path(engine_path).expanduser().resolve()
        self.startup_timeout = startup_timeout
        self.command_timeout = command_timeout
        self.process: subprocess.Popen[str] | None = None

    def __enter__(self) -> "_UciEngine":
        if not self.engine_path.exists():
            raise FileNotFoundError(f"Pikafish binary not found: {self.engine_path}")
        self.process = subprocess.Popen(
            _command_for_path(self.engine_path),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self._send("uci")
        self._read_until("uciok", self.startup_timeout)
        self._send("isready")
        self._read_until("readyok", self.startup_timeout)
        return self

    def __exit__(self, *_exc_info) -> None:
        if self.process is None:
            return
        if self.process.poll() is None:
            try:
                self._send("quit")
                self.process.wait(timeout=2)
            except Exception:
                self.process.kill()
                self.process.wait(timeout=2)

    def analyze(self, fen: str, *, depth: int, movetime_ms: int | None) -> list[str]:
        self._send(f"position fen {fen}")
        self._send(f"go movetime {movetime_ms}" if movetime_ms is not None else f"go depth {depth}")
        return self._read_until("bestmove", self.command_timeout)

    def _send(self, command: str) -> None:
        if self.process is None or self.process.stdin is None:
            raise RuntimeError("UCI process is not running")
        self.process.stdin.write(f"{command}\n")
        self.process.stdin.flush()

    def _read_until(self, marker: str, timeout: float) -> list[str]:
        if self.process is None or self.process.stdout is None:
            raise RuntimeError("UCI process is not running")
        deadline = time.monotonic() + timeout
        lines: list[str] = []
        while True:
            if self.process.poll() is not None:
                raise RuntimeError(f"UCI process exited before {marker!r}: {lines}")
            if time.monotonic() > deadline:
                raise TimeoutError(f"Timed out waiting for {marker!r}: {lines}")
            line = self.process.stdout.readline()
            if not line:
                time.sleep(0.01)
                continue
            stripped = line.strip()
            lines.append(stripped)
            if stripped.startswith(marker) or stripped == marker:
                return lines


def _parse_analysis(lines: list[str]) -> tuple[int | None, int | None, str | None, list[str]]:
    mate_score: int | None = None
    cp_score: int | None = None
    best_move: str | None = None
    pv: list[str] = []
    for line in lines:
        cp_match = SCORE_CP_RE.search(line)
        mate_match = SCORE_MATE_RE.search(line)
        pv_match = PV_RE.search(line)
        if cp_match:
            cp_score = int(cp_match.group(1))
            mate_score = None
        if mate_match:
            mate_score = int(mate_match.group(1))
            cp_score = None
        if pv_match:
            pv = pv_match.group(1).split()
        if line.startswith("bestmove"):
            parts = line.split()
            best_move = parts[1] if len(parts) > 1 else None
    return mate_score, cp_score, best_move, pv


def _command_for_path(path: Path) -> list[str]:
    if path.suffix == ".py":
        return [sys.executable, str(path)]
    return [str(path)]
