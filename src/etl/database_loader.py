from sqlalchemy import text
import pandas as pd

def load_teams(engine, teams_df):
    teams_df.to_sql('teams', engine, if_exists='append', index=False, method='multi')

def load_players(engine, players_df):
    players_df.to_sql('players', engine, if_exists='append', index=False, method='multi')

def load_games(engine, games_df):
    games_df.to_sql('games', engine, if_exists='append', index=False, method='multi')

def load_playbyplay(engine, pbp_df):
    pbp_df.to_sql('play_by_play', engine, if_exists='append', index=False, method='multi', chunksize=1000)

def load_lineup_stints(engine, stints_df):
    stints_df.to_sql('lineup_stints', engine, if_exists='append', index=False, method='multi', chunksize=1000)

def check_game_exists(engine, game_id):
    with engine.connect() as conn:
        query = text("SELECT COUNT(*) FROM play_by_play WHERE game_id = :game_id")
        result = conn.execute(query, {'game_id': game_id})
        count = result.scalar()
        return count > 0
    
def get_loaded_games(engine):
    query = "SELECT DISTINCT game_id FROM play_by_play ORDER BY game_id"
    return pd.read_sql(query, engine)['game_id'].tolist()