from src.etl.lineup_tracker import clean_subs_pbp, clean_data, get_lineups, get_stints
from src.etl.nba_data_extractor import get_game_playbyplay, get_season_games, pbp_cleaner, get_game_info, get_player_info
from src.etl.database_loader import get_loaded_games, load_playbyplay, load_lineup_stints, load_games, get_loaded_players, load_players
import pandas as pd
from sqlalchemy import create_engine
import logging

logger = logging.getLogger(__name__)

def process_single_game(game_id, engine):
    try:
        logger.info(f"Processing game {game_id}")

        loaded_games = get_loaded_games(engine)
        if game_id in loaded_games:
            return False

        pbp_df = get_game_playbyplay(game_id)
        teams = pbp_df['teamId'].unique()[1:]
        clean_pbp = clean_data(pbp_df)
        all_stints = []
        for team in teams:
            clean_subs = clean_subs_pbp(pbp_df, team)
            lineups = get_lineups(clean_pbp, clean_subs, team)
            stints = get_stints(clean_pbp, lineups[0], lineups[1], team)
            stints = stints[stints['duration_secs'] != 0].copy()
            # get seconds into the game too for pbp
            all_stints.append(stints)
        all_stints =  pd.concat(all_stints)

        clean_pbp = pbp_cleaner(clean_pbp)
        game_df = get_game_info(game_id)

        loaded_players = get_loaded_players(engine)
        players = clean_pbp['personId'].unique()[1:]
        players = [player for player in players if player not in loaded_players]
        players_df = get_player_info(players[0])
        for player in players[1:]:
            players_df.loc[len(players_df)] = get_player_info(player)

        load_players(engine, players_df)
        load_games(engine, game_df)
        load_playbyplay(engine, clean_pbp)
        load_lineup_stints(engine, all_stints)
        logger.info(f"Processing game {game_id} was a success")
        return True # to say that everything worked
    except Exception as e:
        print(e)

def process_season(season, engine):
    games = get_season_games(season)
    game_ids = games['GAME_ID'].unique()

    loaded_games = get_loaded_games(engine)
    unprocessed_games = [game for game in game_ids if game not in loaded_games]

    for game_id in unprocessed_games:
        try:
            process_single_game(game_id, engine)
        except Exception as e:
            print(e)