CREATE TABLE teams (
    team_id INT PRIMARY KEY,
    team_name VARCHAR(3),
    abbreviation VARCHAR(100)
);

CREATE TABLE players (
    player_id INT PRIMARY KEY,
    player_name VARCHAR(80),
    position VARCHAR(5),
    height INT,
    weight INT
);

CREATE TABLE games(
    game_id INT PRIMARY KEY,
    date DATE,
    home_team_id INT,
    away_team_id INT,
    home_score INT,
    away_score INT,

    FOREIGN KEY (home_team_id) REFERENCES teams(team_id),
    FOREIGN KEY (away_team_id) REFERENCES teams(team_id)
);

CREATE TABLE play_by_play(
    event_id SERIAL PRIMARY KEY,
    game_id INT,
    action_id INT,
    actionNumber INT,
    period INT,
    clock VARCHAR(15),
    seconds_left INT,
    player_id,
    player_name,
    team_id,
    description VARCHAR(200),
    action_type VARCHAR(80),
    action_subtype CVARHAR(80),
    shot_value INT,
    shot_result VARCHAR(10),

    FOREIGN KEY (game_id) REFERENCES games(game_id),
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

CREATE TABLE substitutions(
    -- actionType == 'Substitution'
);

-- CREATE MATERIALIZED VIEW active_lineups

-- CREATE MATERIALIZED VIEW possession_stats