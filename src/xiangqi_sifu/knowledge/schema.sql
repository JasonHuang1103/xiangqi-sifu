create table if not exists kb_games (
    id integer primary key autoincrement,
    corpus_name text not null,
    source_file text not null,
    source_game_id integer not null,
    event text,
    red text,
    black text,
    result text,
    starting_fen text not null,
    move_count integer not null,
    metadata_json text not null,
    unique (corpus_name, source_file, source_game_id)
);

create table if not exists kb_positions (
    fen text primary key,
    side_to_move text not null,
    occurrence_count integer not null default 0
);

create table if not exists kb_moves (
    fen text not null references kb_positions(fen) on delete cascade,
    move_uci text not null,
    move_iccs text not null,
    side text not null,
    play_count integer not null default 0,
    red_wins integer not null default 0,
    black_wins integer not null default 0,
    draws integer not null default 0,
    sample_game_id integer references kb_games(id) on delete set null,
    sample_ply integer,
    primary key (fen, move_uci)
);

create table if not exists kb_examples (
    id integer primary key autoincrement,
    fen text not null references kb_positions(fen) on delete cascade,
    move_uci text not null,
    game_id integer not null references kb_games(id) on delete cascade,
    ply integer not null,
    unique (fen, move_uci, game_id, ply)
);

create index if not exists idx_kb_moves_fen_count on kb_moves(fen, play_count desc);
create index if not exists idx_kb_examples_lookup on kb_examples(fen, move_uci);
