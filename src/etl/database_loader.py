from sqlalchemy import text
import pandas as pd

def load_teams(engine, teams_df):
    from sqlalchemy.exc import IntegrityError
    try:
        teams_df.to_sql('teams', engine, if_exists='append', index=False, method='multi')
    except IntegrityError:
        # Some teams already exist in database, skip the duplicates
        pass

def load_players(engine, players_df):
    from sqlalchemy.exc import IntegrityError
    try:
        players_df.to_sql('players', engine, if_exists='append', index=False, method='multi')
    except IntegrityError:
        # Some players already exist in database, skip the duplicates
        pass

def load_games(engine, games_df):
    from sqlalchemy.exc import IntegrityError
    try:
        games_df.to_sql('games', engine, if_exists='append', index=False, method='multi')
    except IntegrityError:
        # Game already exists in database, skip the duplicate
        pass

def load_playbyplay(engine, pbp_df):
    from sqlalchemy.exc import IntegrityError
    try:
        pbp_df.to_sql('play_by_play', engine, if_exists='append', index=False, method='multi', chunksize=1000)
    except IntegrityError:
        # Some play-by-play records already exist in database, skip the duplicates
        pass

def load_lineup_stints(engine, stints_df):
    from sqlalchemy.exc import IntegrityError
    try:
        stints_df.to_sql('lineup_stints', engine, if_exists='append', index=False, method='multi', chunksize=1000)
    except IntegrityError:
        # Some lineup stints already exist in database, skip the duplicates
        pass

def check_game_exists(engine, game_id):
    with engine.connect() as conn:
        query = text("SELECT COUNT(*) FROM play_by_play WHERE game_id = :game_id")
        result = conn.execute(query, {'game_id': game_id})
        count = result.scalar()
        return count > 0
    
def get_loaded_games(engine):
    query = "SELECT DISTINCT game_id FROM play_by_play ORDER BY game_id"
    # Convert to string to match NBA API format (with leading zeros)
    return pd.read_sql(query, engine)['game_id'].astype(str).str.zfill(10).tolist()

def get_loaded_players(engine):
    query = "SELECT DISTINCT player_id FROM players ORDER BY player_id"
    return pd.read_sql(query, engine)['player_id'].tolist()

def get_loaded_teams(engine):
    query = "SELECT DISTINCT team_id FROM teams ORDER BY team_id"
    result = pd.read_sql(query, engine)
    if len(result) == 0:
        return []
    return result['team_id'].tolist()