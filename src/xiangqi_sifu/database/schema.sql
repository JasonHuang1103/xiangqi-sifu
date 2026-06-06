create table if not exists games (
    id integer primary key autoincrement,
    event text,
    red text,
    black text,
    result text,
    starting_fen text not null,
    metadata_json text not null,
    created_at text not null default current_timestamp
);

create table if not exists positions (
    id integer primary key autoincrement,
    game_id integer not null references games(id) on delete cascade,
    ply integer not null,
    fen text not null,
    side_to_move text not null,
    move_uci text,
    move_iccs text
);

create table if not exists moves (
    id integer primary key autoincrement,
    game_id integer not null references games(id) on delete cascade,
    ply integer not null,
    move_number integer not null,
    side text not null,
    iccs text not null,
    uci text not null
);

create table if not exists evaluations (
    id integer primary key autoincrement,
    game_id integer not null references games(id) on delete cascade,
    ply integer not null,
    fen text not null,
    red_score_cp integer,
    mate_score integer,
    best_move text,
    pv_json text not null
);

create table if not exists mistakes (
    id integer primary key autoincrement,
    game_id integer not null references games(id) on delete cascade,
    ply integer not null,
    move_number integer not null,
    side text not null,
    played_move text not null,
    best_move text,
    severity text not null,
    eval_before_cp integer not null,
    eval_after_cp integer not null,
    eval_loss_cp integer not null
);
