from __future__ import annotations

import re
import subprocess
import sys
import time
from pathlib import Path

from xiangqi_sifu.analysis.models import EngineLine
from xiangqi_sifu.board.representation import Position
from xiangqi_sifu.engine.analysis import Evaluation

SCORE_CP_RE = re.compile(r"\bscore cp (-?\d+)")
SCORE_MATE_RE = re.compile(r"\bscore mate (-?\d+)")
PV_RE = re.compile(r"\bpv\s+(.+)$")
DEPTH_RE = re.compile(r"\bdepth (\d+)")
NODES_RE = re.compile(r"\bnodes (\d+)")
MULTIPV_RE = re.compile(r"\bmultipv (\d+)")


class UciProtocolError(RuntimeError):
    pass


class PikafishEngine:
    def __init__(
        self,
        binary_path: str | Path,
        *,
        depth: int = 8,
        movetime_ms: int | None = None,
        working_directory: str | Path | None = None,
        startup_timeout: float = 5.0,
        command_timeout: float = 30.0,
    ) -> None:
        self.binary_path = Path(binary_path).expanduser().resolve()
        self.depth = depth
        self.movetime_ms = movetime_ms
        self.working_directory = (
            Path(working_directory).expanduser().resolve()
            if working_directory is not None
            else _default_working_directory(self.binary_path)
        )
        self.startup_timeout = startup_timeout
        self.command_timeout = command_timeout
        self._process: subprocess.Popen[str] | None = None

    def analyze(self, position: Position) -> Evaluation:
        lines = self.analyze_lines(position, multipv=1)
        line = lines[0] if lines else EngineLine(1, None, None, None)
        return Evaluation(
            ply=position.ply,
            fen=position.fen,
            red_score_cp=line.red_score_cp,
            mate_score=line.mate_score,
            best_move=line.best_move,
            pv=line.pv,
            depth=line.depth,
            nodes=line.nodes,
        )

    def analyze_lines(self, position: Position, *, multipv: int = 3) -> tuple[EngineLine, ...]:
        if multipv < 1:
            raise ValueError("multipv must be at least 1")
        self._ensure_started()
        self._send(f"setoption name MultiPV value {multipv}")
        self._send(f"position fen {position.fen}")
        self._send(_go_command(self.depth, self.movetime_ms))
        lines = self._read_until("bestmove", self.command_timeout)
        red_to_move = position.side_to_move == "red"
        return _parse_engine_lines(lines, red_to_move=red_to_move)

    def close(self) -> None:
        process = self._process
        self._process = None
        if process is None:
            return
        if process.poll() is None:
            try:
                process.stdin.write("quit\n")
                process.stdin.flush()
                process.wait(timeout=2)
            except Exception:
                process.kill()
                process.wait(timeout=2)

    def __enter__(self) -> "PikafishEngine":
        self._ensure_started()
        return self

    def __exit__(self, *_exc_info) -> None:
        self.close()

    def _ensure_started(self) -> None:
        if self._process is not None and self._process.poll() is None:
            return
        if not self.binary_path.exists():
            raise FileNotFoundError(f"Pikafish binary not found: {self.binary_path}")
        self._process = subprocess.Popen(
            _command_for_binary(self.binary_path),
            cwd=str(self.working_directory),
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

    def _send(self, command: str) -> None:
        if self._process is None or self._process.stdin is None:
            raise UciProtocolError("Pikafish process is not running")
        self._process.stdin.write(f"{command}\n")
        self._process.stdin.flush()

    def _read_until(self, marker: str, timeout: float) -> list[str]:
        if self._process is None or self._process.stdout is None:
            raise UciProtocolError("Pikafish process is not running")

        deadline = time.monotonic() + timeout
        lines: list[str] = []
        while True:
            if self._process.poll() is not None:
                raise UciProtocolError(f"Pikafish exited before {marker!r}: {lines}")
            if time.monotonic() > deadline:
                raise TimeoutError(f"Timed out waiting for {marker!r}: {lines}")
            line = self._process.stdout.readline()
            if not line:
                time.sleep(0.01)
                continue
            stripped = line.strip()
            lines.append(stripped)
            if stripped.startswith(marker) or stripped == marker:
                return lines


def _default_working_directory(binary_path: Path) -> Path:
    if binary_path.parent.name in {"MacOS", "Linux", "Windows", "Android"}:
        return binary_path.parent.parent
    return binary_path.parent


def _command_for_binary(binary_path: Path) -> list[str]:
    if binary_path.suffix == ".py":
        return [sys.executable, str(binary_path)]
    return [str(binary_path)]


def _go_command(depth: int, movetime_ms: int | None) -> str:
    if movetime_ms is not None:
        return f"go movetime {movetime_ms}"
    return f"go depth {depth}"


def _parse_engine_lines(lines: list[str], *, red_to_move: bool) -> tuple[EngineLine, ...]:
    parsed: dict[int, EngineLine] = {}
    final_best_move: str | None = None
    for line in lines:
        if line.startswith("bestmove"):
            parts = line.split()
            final_best_move = parts[1] if len(parts) > 1 and parts[1] != "(none)" else None
            continue
        cp_match = SCORE_CP_RE.search(line)
        mate_match = SCORE_MATE_RE.search(line)
        pv_match = PV_RE.search(line)
        if cp_match is None and mate_match is None:
            continue
        multipv_match = MULTIPV_RE.search(line)
        depth_match = DEPTH_RE.search(line)
        nodes_match = NODES_RE.search(line)
        index = int(multipv_match.group(1)) if multipv_match else 1
        pv = tuple(pv_match.group(1).split()) if pv_match else ()
        parsed[index] = EngineLine(
            multipv=index,
            red_score_cp=(
                _to_red_score(int(cp_match.group(1)), red_to_move) if cp_match else None
            ),
            mate_score=(
                _to_red_score(int(mate_match.group(1)), red_to_move) if mate_match else None
            ),
            best_move=pv[0] if pv else None,
            pv=pv,
            depth=int(depth_match.group(1)) if depth_match else None,
            nodes=int(nodes_match.group(1)) if nodes_match else None,
        )

    if 1 in parsed and final_best_move is not None:
        first = parsed[1]
        parsed[1] = EngineLine(
            multipv=first.multipv,
            red_score_cp=first.red_score_cp,
            mate_score=first.mate_score,
            best_move=final_best_move,
            pv=first.pv,
            depth=first.depth,
            nodes=first.nodes,
        )
    if not parsed and final_best_move is not None:
        parsed[1] = EngineLine(1, None, None, final_best_move)
    return tuple(parsed[index] for index in sorted(parsed))


def _to_red_score(score: int | None, red_to_move: bool) -> int | None:
    if score is None:
        return None
    return score if red_to_move else -score
