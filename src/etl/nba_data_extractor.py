import pandas as pd
from nba_api.stats.endpoints import playbyplayv3, leaguegamefinder, commonteamroster, boxscoretraditionalv3, commonplayerinfo
from nba_api.stats.static import teams, players

def get_season_games(season='2023-24'):
    try:
        gamefinder = leaguegamefinder.LeagueGameFinder(season_nullable=season)
        games_df = gamefinder.get_data_frames()[0]
        print(f'Successfully got games for {season}')
        return games_df
    except Exception as e:
        print(e)
        return None
    
def get_game_playbyplay(game_id, max_retries=3):
    import time
    for attempt in range(max_retries):
        try:
            pbpfinder = playbyplayv3.PlayByPlayV3(game_id)
            pbp_df = pbpfinder.get_data_frames()[0]
            print(f'Successfully got pbp data for {game_id}')
            return pbp_df
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 15 * (2 ** attempt)  # Exponential backoff: 15s, 30s, 60s
                print(f'Timeout getting pbp for {game_id}, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})')
                time.sleep(wait_time)
            else:
                print(f'Failed to get pbp data for {game_id} after {max_retries} attempts: {e}')
                return None
    
def get_teams():
    teams_list = teams.get_teams()
    teams_df = pd.DataFrame(teams_list)
    print(f'Got all nba teams')
    return teams_df
    
def get_active_players():
    players_list = players.get_active_players()
    players_df = pd.DataFrame(players_list)
    print(f'Got all active players')
    return players_df

def pbp_cleaner(pbp):
    pbp = pbp.copy()
    pbp = pbp.rename(columns={'gameId': 'game_id',
                              'actionId': 'action_id',
                              'personId': 'player_id',
                              'playerNameI': 'player_name',
                              'teamId': 'team_id',
                              'actionType': 'action_type',
                              'subType': 'action_subtype',
                              'shotValue': 'shot_value',
                              'shotResult': 'shot_result'})

    # Select only columns that exist in the database schema
    columns_to_keep = [
        'game_id', 'action_id', 'period', 'clock',
        'seconds_left_in_game', 'seconds_into_game',
        'player_id', 'player_name', 'team_id', 'description',
        'action_type', 'action_subtype', 'shot_value', 'shot_result'
    ]

    # Only keep columns that exist in the dataframe
    columns_to_keep = [col for col in columns_to_keep if col in pbp.columns]
    pbp = pbp[columns_to_keep]

    return pbp

def get_game_info(game_id):
    game_data = boxscoretraditionalv3.BoxScoreTraditionalV3(game_id)
    game_data = game_data.get_data_frames()[2]
    game_df = pd.DataFrame({'game_id': [game_id],
                            'home_team_id': [game_data['teamId'][0]],
                            'away_team_id': [game_data['teamId'][1]],
                            'home_score': [game_data['points'][0]],
                            'away_score': [game_data['points'][1]]
                            })
    return game_df

def get_player_info(player_id):
    try:
        player_data = commonplayerinfo.CommonPlayerInfo(player_id)
        player_data = player_data.get_data_frames()[0]

        # Check if we got any data back
        if len(player_data) == 0:
            raise ValueError(f"No player data found for player_id {player_id}")

        # Handle empty strings for weight (convert to None for NULL in database)
        weight = player_data['WEIGHT'][0]
        if weight == '' or pd.isna(weight):
            weight = None

        # Handle empty strings for height
        height = player_data['HEIGHT'][0]
        if height == '' or pd.isna(height):
            height = None

        player_df = pd.DataFrame({'player_id': [player_id],
                                'player_name': [player_data['PLAYER_SLUG'][0]],
                                'position': [player_data['POSITION'][0]],
                                'height': [height],
                                'weight': [weight]
                                })
        return player_df
    except Exception as e:
        raise ValueError(f"Failed to get player info for player_id {player_id}: {str(e)}")