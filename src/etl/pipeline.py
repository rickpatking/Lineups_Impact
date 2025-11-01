from src.etl.lineup_tracker import clean_subs_pbp, clean_data, get_lineups, get_stints
from src.etl.nba_data_extractor import get_game_playbyplay, get_season_games, pbp_cleaner, get_game_info, get_player_info, get_teams
from src.etl.database_loader import get_loaded_games, load_playbyplay, load_lineup_stints, load_games, get_loaded_players, load_players, load_teams, get_loaded_teams
import pandas as pd
from sqlalchemy import create_engine
import logging
import time

logger = logging.getLogger(__name__)

def process_single_game(game_id, engine):
    try:
        logger.info(f"Processing game {game_id}")

        loaded_games = get_loaded_games(engine)
        if game_id in loaded_games:
            logger.info(f"Game {game_id} already loaded, skipping")
            return False

        pbp_df = get_game_playbyplay(game_id)
        if pbp_df is None:
            logger.error(f"Failed to get play-by-play data for game {game_id}")
            return False

        time.sleep(1)  # Brief delay after getting play-by-play
        teams = pbp_df['teamId'].unique()[1:]
        clean_pbp = clean_data(pbp_df)
        all_stints = []
        for team in teams:
            try:
                lineups = get_lineups(game_id, team)
                time.sleep(1)  # Brief delay after each lineup request
                stints = get_stints(clean_pbp, lineups, team)
                stints = stints[stints['duration_secs'] != 0].copy()
                # get seconds into the game too for pbp
                all_stints.append(stints)
            except Exception as e:
                logger.error(f"Failed to process lineups for team {team} in game {game_id}: {type(e).__name__}: {str(e)}")
                raise
        all_stints =  pd.concat(all_stints)

        clean_pbp = pbp_cleaner(clean_pbp)
        time.sleep(1)  # Brief delay before getting game info
        game_df = get_game_info(game_id)

        # Load teams if not already loaded (teams don't change)
        loaded_teams = get_loaded_teams(engine)
        if len(loaded_teams) == 0:
            logger.info("Loading NBA teams data...")
            teams_df = get_teams()
            # Rename columns to match database schema
            teams_df = teams_df.rename(columns={'id': 'team_id', 'full_name': 'team_name', 'abbreviation': 'abbreviation'})
            teams_df = teams_df[['team_id', 'abbreviation', 'team_name']]  # Select only needed columns
            load_teams(engine, teams_df)
            logger.info(f"Loaded {len(teams_df)} teams")

        loaded_players = get_loaded_players(engine)
        players = clean_pbp['player_id'].unique() #error around here
        players = [player for player in players if pd.notna(player) and player != 0 and player not in loaded_players and not (player >= 1610612000 and player <= 1610613000)]
        if players:
            player_data = []
            for player in players:
                try:
                    player_df = get_player_info(player)
                    player_data.append(player_df)
                    time.sleep(0.6)  # Rate limiting: ~100 requests per minute
                except Exception as e:
                    logger.warning(f"Skipping player {player} due to error: {type(e).__name__}: {str(e)}")
                    continue  # Skip this player but continue with others
            if player_data:
                players_df = pd.concat(player_data, ignore_index=True)
                load_players(engine, players_df)
        load_games(engine, game_df)
        load_playbyplay(engine, clean_pbp)
        load_lineup_stints(engine, all_stints)
        logger.info(f"Processing game {game_id} was a success")
        return True # to say that everything worked
    except Exception as e:
        logger.error(f"Failed to process game {game_id}: {type(e).__name__}: {str(e)}", exc_info=True)
        return False

def process_season(season, engine, batch_size=10):
    games = get_season_games(season)
    game_ids = games['GAME_ID'].unique()

    loaded_games = get_loaded_games(engine)
    unprocessed_games = [game for game in game_ids if game not in loaded_games]

    logger.info(f"Found {len(unprocessed_games)} unprocessed games")

    games_processed = 0
    for i, game_id in enumerate(unprocessed_games):
        # After every batch_size games, take a longer break
        if i > 0 and i % batch_size == 0:
            logger.info(f"Processed {i} games, taking a 60 second break to avoid rate limiting...")
            time.sleep(60)

        time.sleep(5)  # Increased delay between games to avoid rate limiting
        try:
            success = process_single_game(game_id, engine)
            if success:
                games_processed += 1
                logger.info(f"Progress: {games_processed}/{len(unprocessed_games)} games completed")
            else:
                logger.warning(f"Failed to process game {game_id}, will retry on next run")
                # Continue to next game instead of stopping entire season
                continue
        except Exception as e:
            logger.error(f"Unexpected error processing game {game_id}: {e}")
            continue  # Continue with other games

    logger.info(f"Season processing complete: {games_processed}/{len(unprocessed_games)} games loaded successfully")
    return True