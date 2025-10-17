CREATE TABLE teams (
    team_id INT
    team_name CHAR(80)
    abbreviation CHAR(80)
);

CREATE TABLE player (
    player_id INT
    player_name CHAR(80)
    position CHAR(80)
    height CHAR(80)
    weight CHAR(80)
);

CREATE TABLE games(
    game_id INT
    date CHAR(80)
    home_team CHAR(80)
    away_team CHAR(80)
    home_score INT
    away_score INT
);

CREATE TABLE play_by_play(
    game_id INT
    action_id INT
    actionNumber INT
    period INT
    description CHAR(200)
    actionType CHAR(80)
    subType CHAR(80)
    shotValue INT
    shotResult CHAR(80)
);

CREATE TABLE substitutions(
    -- actionType == 'Substitution'
);

-- CREATE MATERIALIZED VIEW active_lineups

-- CREATE MATERIALIZED VIEW possession_stats