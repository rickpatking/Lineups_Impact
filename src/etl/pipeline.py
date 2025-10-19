import lineup_tracker
import nba_data_extractor
import database_loader
import pandas as pd
from sqlalchemy import create_engine

def process_single_game(game_id, engine):
    pbp_df = nba_data_extractor.get_game_playbyplay(game_id)
    teams = pbp_df['teamId'].unique()[1:]
    clean_pbp = lineup_tracker.clean_data(pbp_df)
    all_stints = []
    for team in teams:
        clean_subs = lineup_tracker.clean_subs_pbp(pbp_df, team)
        lineups = lineup_tracker.get_lineups(clean_pbp, clean_subs, team)
        stints = lineup_tracker.get_stints(clean_pbp, lineups[0], lineups[1], team)
        stints = stints[stints['duration_secs'] != 0].copy()
        all_stints.append(stints)
    all_stints =  pd.concat(all_stints)

    database_loader.load_playbyplay(engine, clean_pbp)
    database_loader.load_lineup_stints(engine, all_stints)
    return True # to say that everything worked

def process_season(connection_str, season='2024-25'):
    engine = create_engine(connection_str)
    games = nba_data_extractor.get_season_games(season)
    game_ids = games['GAME_ID'].unique()

    loaded_games = database_loader.get_loaded_games(engine)
    unprocessed_games = [game for game in game_ids if game not in loaded_games]

    for game_id in unprocessed_games:
        try:
            process_single_game(game_id, connection_str)
        except Exception as e:
            print(e)