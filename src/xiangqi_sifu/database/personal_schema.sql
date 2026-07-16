PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS profile (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    display_name TEXT,
    adaptive_level INTEGER NOT NULL DEFAULT 5 CHECK (adaptive_level BETWEEN 1 AND 10),
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mode TEXT NOT NULL CHECK (mode IN ('friend', 'sifu', 'upload', 'reference')),
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'completed')),
    starting_fen TEXT NOT NULL,
    current_fen TEXT NOT NULL,
    human_side TEXT CHECK (human_side IN ('w', 'b')),
    ai_level INTEGER CHECK (ai_level BETWEEN 1 AND 10),
    ai_adaptive INTEGER NOT NULL DEFAULT 0 CHECK (ai_adaptive IN (0, 1)),
    red_name TEXT,
    black_name TEXT,
    result TEXT,
    termination TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS moves (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    ply INTEGER NOT NULL,
    uci TEXT NOT NULL,
    resulting_fen TEXT NOT NULL,
    retracted INTEGER NOT NULL DEFAULT 0 CHECK (retracted IN (0, 1)),
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS moves_game_active_idx
ON moves(game_id, retracted, ply);

CREATE TABLE IF NOT EXISTS game_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    payload_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS analysis_jobs (
    id TEXT PRIMARY KEY,
    game_id INTEGER REFERENCES games(id) ON DELETE CASCADE,
    status TEXT NOT NULL CHECK (status IN ('queued', 'running', 'completed', 'failed', 'cancelled')),
    completed_positions INTEGER NOT NULL DEFAULT 0,
    total_positions INTEGER NOT NULL,
    error TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL REFERENCES analysis_jobs(id) ON DELETE CASCADE,
    ply INTEGER NOT NULL,
    fen TEXT NOT NULL,
    red_score_cp INTEGER,
    mate_score INTEGER,
    best_move TEXT,
    lines_json TEXT NOT NULL DEFAULT '[]',
    UNIQUE(job_id, ply)
);

CREATE TABLE IF NOT EXISTS coach_threads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER REFERENCES games(id) ON DELETE CASCADE,
    context_fen TEXT NOT NULL,
    context_json TEXT NOT NULL DEFAULT '{}',
    selected_ply INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS coach_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    thread_id INTEGER NOT NULL REFERENCES coach_threads(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    provider TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS recognitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT,
    source_width INTEGER NOT NULL,
    source_height INTEGER NOT NULL,
    recognized_fen TEXT NOT NULL,
    confirmed_fen TEXT,
    confidence_json TEXT NOT NULL,
    corrections_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);

PRAGMA user_version = 3;
