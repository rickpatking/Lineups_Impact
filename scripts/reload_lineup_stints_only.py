import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.db_connection import create_db_engine
from src.etl.lineup_tracker import clean_data, get_lineups, get_stints
from src.etl.database_loader import load_lineup_stints
import pandas as pd
import logging
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/lineup_reload.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

engine = create_db_engine()

print("="*70)
print("RELOADING LINEUP STINTS FOR ALL GAMES")
print("="*70)

# Get all games from play_by_play table (these are already loaded)
logger.info("Getting list of all loaded games...")
games_query = "SELECT DISTINCT game_id FROM play_by_play ORDER BY game_id"
game_ids = pd.read_sql(games_query, engine)['game_id'].astype(str).str.zfill(10).tolist()

logger.info(f"Found {len(game_ids)} games to process")
print(f"\nFound {len(game_ids)} games with play-by-play data")
print("Will regenerate lineup stints for all games using fixed code...\n")

games_processed = 0
games_failed = 0

for i, game_id in enumerate(game_ids):
    try:
        # Rate limiting: pause every 10 games
        if i > 0 and i % 10 == 0:
            logger.info(f"Processed {i} games, taking 30 second break...")
            time.sleep(30)

        logger.info(f"[{i+1}/{len(game_ids)}] Processing game {game_id}")

        # Get play-by-play data from database
        pbp_query = f"SELECT * FROM play_by_play WHERE game_id = '{game_id}'"
        pbp_df = pd.read_sql(pbp_query, engine)

        if len(pbp_df) == 0:
            logger.warning(f"No play-by-play data found for game {game_id}")
            games_failed += 1
            continue

        # Get unique teams (skip team_id 0 which is neutral)
        teams = pbp_df['team_id'].unique()
        teams = [t for t in teams if t != 0]

        if len(teams) < 2:
            logger.warning(f"Game {game_id} has fewer than 2 teams: {teams}")
            games_failed += 1
            continue

        # Process lineups for each team
        all_stints = []
        for team_id in teams:
            try:
                # Get lineups using the FIXED get_lineups function
                lineups = get_lineups(game_id, team_id)
                time.sleep(0.6)  # Brief delay for API rate limiting

                # Generate stints
                stints = get_stints(pbp_df, lineups, team_id)
                stints = stints[stints['duration_secs'] != 0].copy()
                all_stints.append(stints)

                logger.info(f"  Team {team_id}: {len(stints)} stints")

            except Exception as e:
                logger.error(f"  Failed to process team {team_id}: {type(e).__name__}: {str(e)}")
                raise

        if len(all_stints) > 0:
            all_stints_df = pd.concat(all_stints)

            # Load to database
            load_lineup_stints(engine, all_stints_df)
            games_processed += 1
            logger.info(f"  Loaded {len(all_stints_df)} total stints for game {game_id}")
        else:
            logger.warning(f"No stints generated for game {game_id}")
            games_failed += 1

        time.sleep(0.6)  # Brief delay between games

    except Exception as e:
        logger.error(f"Failed to process game {game_id}: {type(e).__name__}: {str(e)}")
        games_failed += 1
        continue

print("\n" + "="*70)
print("RELOAD COMPLETE!")
print("="*70)
print(f"Successfully processed: {games_processed} games")
print(f"Failed: {games_failed} games")
print("\nNext steps:")
print("1. Run: python scripts/check_views.py")
print("2. Verify Power BI dashboards work correctly")
print("3. Check that lineups now show more than 2 games played together")
print("="*70)

engine.dispose()
