-- Active: 1760807926261@@127.0.0.1@5432@nba_analysis
-- Active: 1760716511493@@127.0.0.1@5432
CREATE TABLE IF NOT EXISTS teams (
    team_id INT PRIMARY KEY,
    team_name VARCHAR(3),
    abbreviation VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS players (
    player_id INT PRIMARY KEY,
    player_name VARCHAR(80),
    position VARCHAR(10),
    height INT,
    weight INT
);

CREATE TABLE IF NOT EXISTS games(
    game_id INT PRIMARY KEY,
    home_team_id INT,
    away_team_id INT,
    home_score INT,
    away_score INT,

    FOREIGN KEY (home_team_id) REFERENCES teams(team_id),
    FOREIGN KEY (away_team_id) REFERENCES teams(team_id)
);

CREATE TABLE IF NOT EXISTS play_by_play(
    event_id SERIAL PRIMARY KEY,
    game_id INT,
    action_id INT,
    period INT,
    clock VARCHAR(15),
    seconds_left_in_game INT,
    seconds_into_game INT,
    player_id INT,
    player_name VARCHAR(80),
    team_id INT,
    description VARCHAR(200),
    action_type VARCHAR(80),
    action_subtype VARCHAR(80),
    shot_value INT,
    shot_result VARCHAR(10),

    FOREIGN KEY (game_id) REFERENCES games(game_id),
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

CREATE TABLE IF NOT EXISTS lineup_stints(
    stint_id SERIAL PRIMARY KEY,
    game_id INT,
    team_id INT,
    start_num INT,
    end_num INT,
    duration_secs INT,
    player1_id INT,
    player2_id INT,
    player3_id INT,
    player4_id INT,
    player5_id INT,
    lineup_hash VARCHAR(100),

    FOREIGN KEY (game_id) REFERENCES games(game_id)
);

-- CREATE INDEX IF NOT EXISTS idx_pvp_game ON play_by_play(game_id);
-- CREATE INDEX IF NOT EXISTS idx_pvp_event ON play_by_play(game_id, action_id);
-- CREATE INDEX IF NOT EXISTS idx_stints_game ON lineup_stints(game_id);
-- CREATE INDEX IF NOT EXISTS idx_stints_lineup ON lineup_stints(lineup_hash);

-- CREATE MATERIALIZED VIEW active_lineups

-- CREATE MATERIALIZED VIEW possession_stats