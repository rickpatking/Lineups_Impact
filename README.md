# NBA Lineup Impact Analysis

A data pipeline and analytics system for analyzing NBA lineup performance using play-by-play data and rotation tracking.

**Power BI Dashboard**: [View Dashboard](https://uflorida-my.sharepoint.com/:u:/r/personal/patrickking_ufl_edu/Documents/nba_lineups_analysis.pbix?csf=1&web=1&e=Pe0jQu)

## Project Overview

This project extracts NBA game data from the official NBA API, tracks which 5-player lineups are on the court during each possession, calculates advanced statistics (offensive/defensive/net rating, plus/minus), and visualizes the results in Power BI to identify the most effective lineup combinations.

## Technology Stack

- **Python 3.11**: Data extraction and transformation
- **PostgreSQL**: Data storage and aggregation
- **NBA API**: Official NBA statistics (nba_api library)
- **Power BI Desktop**: Data visualization
- **SQLAlchemy**: Database connection and ORM

## Database Schema

### Core Tables

**teams**: NBA team information (30 teams)
- `team_id`, `team_name`, `abbreviation`

**players**: Player roster data
- `player_id`, `player_name`, `position`, `height`, `weight`

**games**: Game metadata
- `game_id`, `home_team_id`, `away_team_id`, `home_score`, `away_score`

**play_by_play**: Every action in every game
- `game_id`, `action_id`, `period`, `player_id`, `team_id`, `action_type`, `shot_value`, etc.

**lineup_stints**: Continuous periods where 5 players are on court together
- `game_id`, `team_id`, `start_num`, `end_num`, `duration_secs`
- `player1_id`, `player2_id`, `player3_id`, `player4_id`, `player5_id`
- `lineup_hash`: Sorted player IDs for consistent identification

### Views

**lineup_stint_stats**: Per-stint statistics
- Joins play-by-play data with lineup stints
- Calculates points scored/allowed, possessions, ratings per stint

**lineup_aggregated_stats**: Aggregated across all games
- Groups by lineup_hash to show total performance
- `games_played`, `total_minutes`, `avg_net_rating`, `total_plus_minus`

**player_impact_stats**: Individual player performance across all stints

**game_lineup_summary**: Lineup performance broken down by game

## ETL Pipeline

### Data Flow

1. **Extract**: Fetch game data from NBA API
   - Season schedule
   - Play-by-play events
   - Game rotation (player substitutions)
   - Player information

2. **Transform**: Process raw data
   - Calculate time metrics (seconds into game)
   - Track lineup changes via rotation data
   - Identify stint boundaries using action IDs
   - Sort player IDs to create consistent lineup_hash

3. **Load**: Insert into PostgreSQL
   - Deduplicate existing records
   - Handle foreign key constraints
   - Rate limit API calls to avoid blocking

### Running the Pipeline

```bash
# Load 2024-25 season data
python scripts/run_etl.py --season 2024-25

# Load a specific game
python scripts/run_etl.py --game-id 0042400407
```

The pipeline automatically:
- Skips already-loaded games
- Handles API rate limiting (600ms delays)
- Retries failed requests
- Logs progress to `logs/etl_pipeline.log`

## Key Statistics Calculated

**Offensive Rating**: Points scored per 100 possessions
**Defensive Rating**: Points allowed per 100 possessions
**Net Rating**: Offensive rating - Defensive rating
**Plus/Minus**: Point differential while lineup is on court
**Possessions**: Estimated from field goal attempts

Ratings are calculated from aggregated totals (not averaged per stint) for statistical accuracy.

## Power BI Dashboard

### Connection Setup

1. Open Power BI Desktop
2. Get Data > PostgreSQL database
3. Server: `localhost:5432`, Database: `nba_analysis`
4. Import views: `lineup_aggregated_stats`, `lineup_stint_stats`, `player_impact_stats`, `game_lineup_summary`
5. Import tables: `players`, `teams`

### Key Visualizations

**Lineup Efficiency vs Usage (Scatter Chart)**
- X-axis: Total minutes played
- Y-axis: Average net rating
- Size: Games played together
- Identifies high-performing lineups with significant playing time

**Top Lineups Table**
- Shows player names, statistics, games played
- Conditional formatting on net rating and plus/minus
- Filterable by team, minimum minutes, minimum games

**Offensive vs Defensive Rating (Scatter)**
- Four-quadrant analysis
- Reference lines at league averages
- Identifies defensive specialists vs offensive powerhouses

**Plus/Minus Bar Chart**
- Top 15 lineups by total plus/minus
- Color-coded by team

### DAX Measures

Created calculated columns for player name lookups:
```dax
Player1Name = LOOKUPVALUE(players[player_name], players[player_id], lineup_aggregated_stats[player1_id])
LineupNames = [Player1Name] & ", " & [Player2Name] & ", " & [Player3Name] & ", " & [Player4Name] & ", " & [Player5Name]
```

## Project Structure

```
Lineups_Impact/
├── src/
│   ├── etl/
│   │   ├── pipeline.py              # Main ETL orchestration
│   │   ├── lineup_tracker.py        # Lineup extraction logic
│   │   ├── nba_data_extractor.py    # NBA API wrappers
│   │   └── database_loader.py       # PostgreSQL loading functions
│   └── utils/
│       └── db_connection.py         # Database connection manager
├── sql/
│   ├── schema/
│   │   └── 01_create_tables.sql     # Table definitions
│   └── views/
│       └── lineup_performance.sql   # Analytical views
├── scripts/
│   ├── run_etl.py                   # CLI entry point
│   ├── fix_missing_players.py       # Backfill missing players
│   ├── check_views.py               # Validate view calculations
│   └── force_recreate_views.py      # Rebuild views after schema changes
├── logs/                            # ETL execution logs
└── docs/
    └── PowerBI_Setup_Guide.md       # Detailed Power BI instructions
```

## Key Challenges Solved

### 1. Duplicate Lineup Bug
**Problem**: Same lineup_hash appeared for both opposing teams in a game.
**Cause**: `get_lineups()` function always used first dataframe from rotation API (contains both teams).
**Solution**: Iterate through both dataframes and select the one matching the requested team_id.

### 2. Lineup Hash Inconsistency
**Problem**: Same 5 players created different lineup_hashes due to different ordering.
**Cause**: Lineup hash created from unsorted player list.
**Solution**: Sort player IDs before creating hash: `sorted(lineup)`.

### 3. Inflated Net Ratings
**Problem**: Net ratings showed 50-100 when plus/minus was near 0.
**Cause**: SQL views joined on `seconds_into_game` but stint boundaries used `action_id`.
**Solution**: Changed join condition to use `action_id` ranges.

### 4. Division by Zero in Power BI
**Problem**: OLE DB errors when loading views.
**Cause**: Power BI evaluated divisions even when CASE statements should prevent them.
**Solution**: Used `NULLIF()` for all division operations.

### 5. Missing Players in Database
**Problem**: Some lineups showed blank names (4 commas).
**Cause**: Players not loaded during initial ETL run (API failures for two-way contract players).
**Solution**: Created `fix_missing_players.py` to backfill missing player records.

## Configuration

Create a `.env` file with PostgreSQL credentials:
```
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=nba_analysis
```

## Data Volume

- **2024-25 Season**: ~2,170 games (when complete)
- **Current Load**: 872 games (as of project snapshot)
- **Processing Time**: ~3-6 hours for full season (due to API rate limiting)
- **Database Size**: ~500MB for full season with all play-by-play data

## Future Enhancements

- Automated daily updates during NBA season
- Historical season comparison (2023-24, 2022-23, etc.)
- Player on/off court impact analysis
- Lineup recommendation engine based on opponent
- Rest days and back-to-back game adjustments
- Playoff vs regular season performance splits

## References

- NBA API Documentation: [nba_api on GitHub](https://github.com/swar/nba_api)
- Basketball Reference: [NBA Statistics](https://www.basketball-reference.com/)
- Power BI Documentation: [Microsoft Power BI](https://docs.microsoft.com/en-us/power-bi/)

## License

This project is for educational and analytical purposes. NBA data is property of the NBA.

## Author

Patrick King
University of Florida
