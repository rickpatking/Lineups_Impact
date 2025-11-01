-- ============================================================================
-- LINEUP PERFORMANCE VIEWS FOR POWER BI ANALYSIS
-- ============================================================================
-- This file creates SQL views that calculate advanced basketball metrics
-- for lineup analysis in Power BI or Tableau
-- ============================================================================

-- ----------------------------------------------------------------------------
-- VIEW 1: lineup_stint_stats
-- ----------------------------------------------------------------------------
-- PURPOSE: Calculate points scored and allowed for each lineup stint
--
-- HOW IT WORKS:
-- 1. For each lineup stint (period where same 5 players are on court)
-- 2. Join with play-by-play data to get all events during that stint
-- 3. Calculate points scored (shots made by the lineup's team)
-- 4. Calculate points allowed (shots made by opponent)
-- 5. Calculate possessions (estimated using a standard NBA formula)
--
-- WHY: This is the foundation for all lineup analysis. We need to know
-- how many points a lineup scores vs allows to measure their effectiveness.
-- ----------------------------------------------------------------------------

DROP VIEW IF EXISTS lineup_stint_stats CASCADE;

CREATE VIEW lineup_stint_stats AS
WITH stint_events AS (
    -- Step 1: Match each lineup stint with all play-by-play events that happened during it
    -- We use seconds_into_game to determine if an event happened during a stint
    SELECT
        ls.stint_id,
        ls.game_id,
        ls.team_id,
        ls.start_num,
        ls.end_num,
        ls.duration_secs,
        ls.player1_id,
        ls.player2_id,
        ls.player3_id,
        ls.player4_id,
        ls.player5_id,
        ls.lineup_hash,
        pbp.action_id,
        pbp.period,
        pbp.seconds_into_game,
        pbp.team_id AS event_team_id,
        pbp.action_type,
        pbp.shot_value,
        pbp.shot_result,
        -- Determine if this event was by the lineup's team or opponent
        CASE
            WHEN pbp.team_id = ls.team_id THEN 'offense'
            ELSE 'defense'
        END AS event_context

    FROM lineup_stints ls
    INNER JOIN play_by_play pbp
        ON ls.game_id = pbp.game_id
        -- Event must occur during this stint's time period
        AND pbp.seconds_into_game >= ls.start_num
        AND pbp.seconds_into_game <= ls.end_num
),

stint_scoring AS (
    -- Step 2: Calculate points scored and allowed for each stint
    SELECT
        stint_id,
        game_id,
        team_id,
        duration_secs,
        lineup_hash,
        player1_id,
        player2_id,
        player3_id,
        player4_id,
        player5_id,
        -- Points scored: sum shot values where team made a shot
        COALESCE(SUM(
            CASE
                WHEN event_context = 'offense'
                    AND shot_result = 'Made'
                    AND shot_value IS NOT NULL
                THEN shot_value
                ELSE 0
            END
        ), 0) AS points_scored,
        -- Points allowed: sum shot values where opponent made a shot
        COALESCE(SUM(
            CASE
                WHEN event_context = 'defense'
                    AND shot_result = 'Made'
                    AND shot_value IS NOT NULL
                THEN shot_value
                ELSE 0
            END
        ), 0) AS points_allowed,
        -- Count offensive possessions (estimated)
        -- In NBA stats, possessions ≈ FGA + 0.4*FTA - OReb + Turnovers
        -- We'll use a simplified version: field goal attempts + free throws/2
        COALESCE(SUM(
            CASE
                WHEN event_context = 'offense'
                    AND action_type IN ('Made Shot', 'Missed Shot')
                THEN 1
                ELSE 0
            END
        ), 0) AS field_goal_attempts,
        -- Count total offensive events (for possessions estimate)
        COUNT(CASE WHEN event_context = 'offense' THEN 1 END) AS offensive_events,
        -- Count total defensive events
        COUNT(CASE WHEN event_context = 'defense' THEN 1 END) AS defensive_events

    FROM stint_events
    GROUP BY
        stint_id, game_id, team_id, duration_secs, lineup_hash,
        player1_id, player2_id, player3_id, player4_id, player5_id
)
-- Step 3: Calculate advanced metrics for each stint
SELECT
    stint_id,
    game_id,
    team_id,
    lineup_hash,
    player1_id,
    player2_id,
    player3_id,
    player4_id,
    player5_id,
    duration_secs,
    -- Basic counting stats
    points_scored,
    points_allowed,
    points_scored - points_allowed AS plus_minus,
    -- Estimated possessions (simplified formula)
    -- Using field goal attempts as proxy for possessions
    GREATEST(field_goal_attempts, 1) AS possessions,
    -- Per-minute metrics (convert seconds to minutes)
    CASE
        WHEN duration_secs > 0
        THEN ROUND((points_scored::DECIMAL / duration_secs) * 60, 2)
        ELSE 0
    END AS points_per_minute,

    CASE
        WHEN duration_secs > 0
        THEN ROUND((points_allowed::DECIMAL / duration_secs) * 60, 2)
        ELSE 0
    END AS points_allowed_per_minute,
    -- Per-100-possession metrics (standard NBA efficiency metric)
    CASE
        WHEN field_goal_attempts > 0
        THEN ROUND((points_scored::DECIMAL / field_goal_attempts) * 100, 2)
        ELSE 0
    END AS offensive_rating,

    CASE
        WHEN field_goal_attempts > 0
        THEN ROUND((points_allowed::DECIMAL / field_goal_attempts) * 100, 2)
        ELSE 0
    END AS defensive_rating,
    -- Net rating (offensive rating - defensive rating)
    CASE
        WHEN field_goal_attempts > 0
        THEN ROUND(
            ((points_scored::DECIMAL / field_goal_attempts) * 100) -
            ((points_allowed::DECIMAL / field_goal_attempts) * 100),
            2
        )
        ELSE 0
    END AS net_rating

FROM stint_scoring;


-- ----------------------------------------------------------------------------
-- VIEW 2: lineup_aggregated_stats
-- ----------------------------------------------------------------------------
-- PURPOSE: Aggregate stats across ALL stints for each unique lineup
--
-- HOW IT WORKS:
-- 1. Group all stints by the same 5 players (using lineup_hash)
-- 2. Sum up total minutes, points scored, points allowed
-- 3. Calculate overall efficiency metrics for that lineup
--
-- WHY: Power BI will use this to show "Which lineups are most effective?"
-- For example: "The Curry-Thompson-Green-Wiggins-Looney lineup has played
-- 45 minutes with a +15.3 net rating"
-- ----------------------------------------------------------------------------

DROP VIEW IF EXISTS lineup_aggregated_stats CASCADE;

CREATE VIEW lineup_aggregated_stats AS
SELECT
    lineup_hash,
    team_id,
    player1_id,
    player2_id,
    player3_id,
    player4_id,
    player5_id,
    -- Aggregate across all games
    COUNT(DISTINCT game_id) AS games_played,
    COUNT(stint_id) AS total_stints,
    SUM(duration_secs) AS total_seconds,
    ROUND(SUM(duration_secs)::DECIMAL / 60, 2) AS total_minutes,
    -- Cumulative scoring
    SUM(points_scored) AS total_points_scored,
    SUM(points_allowed) AS total_points_allowed,
    SUM(points_scored - points_allowed) AS total_plus_minus,
    -- Average per-stint metrics
    ROUND(AVG(points_scored), 2) AS avg_points_per_stint,
    ROUND(AVG(points_allowed), 2) AS avg_points_allowed_per_stint,
    ROUND(AVG(plus_minus), 2) AS avg_plus_minus_per_stint,
    -- Overall efficiency (per 100 possessions)
    ROUND(AVG(offensive_rating), 2) AS avg_offensive_rating,
    ROUND(AVG(defensive_rating), 2) AS avg_defensive_rating,
    ROUND(AVG(net_rating), 2) AS avg_net_rating,
    -- Per-minute metrics
    CASE
        WHEN SUM(duration_secs) > 0
        THEN ROUND((SUM(points_scored)::DECIMAL / SUM(duration_secs)) * 60, 2)
        ELSE 0
    END AS overall_points_per_minute,

    CASE
        WHEN SUM(duration_secs) > 0
        THEN ROUND((SUM(points_allowed)::DECIMAL / SUM(duration_secs)) * 60, 2)
        ELSE 0
    END AS overall_points_allowed_per_minute

FROM lineup_stint_stats
GROUP BY
    lineup_hash, team_id,
    player1_id, player2_id, player3_id, player4_id, player5_id;


-- ----------------------------------------------------------------------------
-- VIEW 3: player_impact_stats
-- ----------------------------------------------------------------------------
-- PURPOSE: Calculate individual player impact using On/Off court analysis
--
-- HOW IT WORKS:
-- 1. For each player, find all stints where they were ON the court
-- 2. Calculate team performance with player ON
-- 3. Compare to team performance with player OFF
-- 4. The difference shows that player's impact
--
-- WHY: Answers "How much better is the team when Player X is playing?"
-- This is one of the most valuable metrics in modern NBA analysis
-- ----------------------------------------------------------------------------

DROP VIEW IF EXISTS player_impact_stats CASCADE;

CREATE VIEW player_impact_stats AS
WITH player_on_court AS (
    -- Find all stints where each player was on the court
    SELECT
        player_id,
        team_id,
        stint_id,
        game_id,
        duration_secs,
        points_scored,
        points_allowed,
        plus_minus,
        offensive_rating,
        defensive_rating,
        net_rating
    FROM (
        -- Union all 5 player columns into one player_id column
        SELECT player1_id AS player_id, team_id, stint_id, game_id,
               duration_secs, points_scored, points_allowed, plus_minus,
               offensive_rating, defensive_rating, net_rating
        FROM lineup_stint_stats
        UNION ALL
        SELECT player2_id, team_id, stint_id, game_id,
               duration_secs, points_scored, points_allowed, plus_minus,
               offensive_rating, defensive_rating, net_rating
        FROM lineup_stint_stats
        UNION ALL
        SELECT player3_id, team_id, stint_id, game_id,
               duration_secs, points_scored, points_allowed, plus_minus,
               offensive_rating, defensive_rating, net_rating
        FROM lineup_stint_stats
        UNION ALL
        SELECT player4_id, team_id, stint_id, game_id,
               duration_secs, points_scored, points_allowed, plus_minus,
               offensive_rating, defensive_rating, net_rating
        FROM lineup_stint_stats
        UNION ALL
        SELECT player5_id, team_id, stint_id, game_id,
               duration_secs, points_scored, points_allowed, plus_minus,
               offensive_rating, defensive_rating, net_rating
        FROM lineup_stint_stats
    ) AS all_player_stints
)
SELECT
    p.player_id,
    p.player_name,
    p.position,
    poc.team_id,
    -- Time on court
    COUNT(DISTINCT poc.game_id) AS games_played,
    COUNT(poc.stint_id) AS stints_played,
    SUM(poc.duration_secs) AS total_seconds,
    ROUND(SUM(poc.duration_secs)::DECIMAL / 60, 2) AS total_minutes,
    -- Team performance with player ON court
    SUM(poc.points_scored) AS on_court_points_scored,
    SUM(poc.points_allowed) AS on_court_points_allowed,
    SUM(poc.plus_minus) AS on_court_plus_minus,
    -- Average per-stint impact
    ROUND(AVG(poc.plus_minus), 2) AS avg_plus_minus_per_stint,
    ROUND(AVG(poc.offensive_rating), 2) AS avg_offensive_rating,
    ROUND(AVG(poc.defensive_rating), 2) AS avg_defensive_rating,
    ROUND(AVG(poc.net_rating), 2) AS avg_net_rating,
    -- Per-48-minutes metrics (standard NBA comparison)
    CASE
        WHEN SUM(poc.duration_secs) > 0
        THEN ROUND((SUM(poc.plus_minus)::DECIMAL / SUM(poc.duration_secs)) * 2880, 2)
        ELSE 0
    END AS plus_minus_per_48min

FROM player_on_court poc
INNER JOIN players p ON poc.player_id = p.player_id
GROUP BY p.player_id, p.player_name, p.position, poc.team_id;


-- ----------------------------------------------------------------------------
-- VIEW 4: game_lineup_summary
-- ----------------------------------------------------------------------------
-- PURPOSE: Show which lineups were used in each game and their performance
--
-- HOW IT WORKS:
-- 1. Group lineup stints by game
-- 2. Show all lineups used in that game
-- 3. Include game outcome (win/loss) for context
--
-- WHY: Helps answer "Which lineups did we use in wins vs losses?"
-- Coaches can see if certain lineups correlate with winning
-- ----------------------------------------------------------------------------

DROP VIEW IF EXISTS game_lineup_summary CASCADE;

CREATE VIEW game_lineup_summary AS
SELECT
    lss.game_id,
    g.home_team_id,
    g.away_team_id,
    g.home_score,
    g.away_score,
    lss.team_id,
    lss.lineup_hash,
    -- Determine if this team won or lost
    CASE
        WHEN lss.team_id = g.home_team_id THEN
            CASE WHEN g.home_score > g.away_score THEN 'W' ELSE 'L' END
        WHEN lss.team_id = g.away_team_id THEN
            CASE WHEN g.away_score > g.home_score THEN 'W' ELSE 'L' END
        ELSE NULL
    END AS game_result,
    -- Lineup stats for this game
    SUM(lss.duration_secs) AS minutes_played_in_game,
    SUM(lss.points_scored) AS points_scored_in_game,
    SUM(lss.points_allowed) AS points_allowed_in_game,
    SUM(lss.plus_minus) AS plus_minus_in_game,
    ROUND(AVG(lss.net_rating), 2) AS avg_net_rating_in_game

FROM lineup_stint_stats lss
INNER JOIN games g ON lss.game_id = g.game_id
GROUP BY
    lss.game_id, g.home_team_id, g.away_team_id,
    g.home_score, g.away_score, lss.team_id, lss.lineup_hash;


-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================
-- These indexes speed up queries when Power BI requests data
-- Think of them like a book's index - helps find data faster
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_pbp_game_time
    ON play_by_play(game_id, seconds_into_game);

CREATE INDEX IF NOT EXISTS idx_pbp_scoring
    ON play_by_play(game_id, team_id, shot_result)
    WHERE shot_result = 'Made';

CREATE INDEX IF NOT EXISTS idx_stints_game_team
    ON lineup_stints(game_id, team_id);

CREATE INDEX IF NOT EXISTS idx_stints_lineup
    ON lineup_stints(lineup_hash);

-- ============================================================================
-- USAGE NOTES
-- ============================================================================
--
-- To create these views in your database, run:
--   psql -U your_username -d nba_analysis -f sql/views/lineup_performance.sql
--
-- Or from Python:
--   from src.utils.db_connection import create_db_engine
--   engine = create_db_engine()
--   with open('sql/views/lineup_performance.sql', 'r') as f:
--       engine.execute(f.read())
--
-- In Power BI, these views will appear as regular tables that you can use
-- ============================================================================
